# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

"""Module defining the OPF Model base class."""

import cPickle as pickle

import os
import shutil

from abc import ABCMeta, abstractmethod
from collections import namedtuple
import nupic.frameworks.opf.opfutils as opfutils

###############################################################

class Model(object):
  """
  This is the base class that all OPF Model implementations should subclass. It
  includes a number of virtual methods, to be overridden by subclasses, as well
  as some shared functionality for saving/loading models
  """

  __metaclass__ = ABCMeta

  def __init__(self, inferenceType):
    """ Model constructor.

    Args:
      inferenceType: An opfutils.InferenceType value that specifies the type
          of inference (i.e. TemporalNextStep, Classification, etc.).
    """
    self._numPredictions = 0
    self.__inferenceType =  inferenceType
    self.__learningEnabled = True
    self.__inferenceEnabled = True
    self.__inferenceArgs = {}

  def run(self, inputRecord):
    """ run one iteration of this model.
        args:
            inputRecord is a record object formatted according to
                nupic.data.FileSource.getNext() result format.

        return:
            An ModelResult namedtuple (see opfutils.py) The contents of
            ModelResult.inferences depends on the the specific inference type
            of this model, which can be queried by getInferenceType()
    """
    if hasattr(self, '_numPredictions'):
      predictionNumber = self._numPredictions
      self._numPredictions += 1
    else:
      predictionNumber = None
    result = opfutils.ModelResult(predictionNumber=predictionNumber,
                                  rawInput=inputRecord)
    return result

  @abstractmethod
  def finishLearning(self):
    """ Places the model in a permanent "finished learning" mode where it
    will not be able to learn from subsequent input records.

    NOTE: Upon completion of this command, learning may not be resumed on
    the given instance of the model (e.g., the implementation may optimize
    itself by pruning data structures that are necessary for learning)
    """

  @abstractmethod
  def resetSequenceStates(self):
    """ Signal that the input record is the start of a new sequence.
    """

  @abstractmethod
  def getFieldInfo(self, includeClassifierOnlyField=False):
    """
        Returns the sequence of nupic.data.FieldMetaInfo objects specifying the
        format of Model's output; note that this may be different than the list
        of FieldMetaInfo objects supplied at initialization (e.g., due to the
        transcoding of some input fields into meta-fields, such as datetime
        -> dayOfWeek, timeOfDay, etc.)
        
    Parameters:
      includeClassifierOnlyField - if True, any field which is only sent to the
         classifier (i.e. not sent in to the bottom of the network) is also
         included. 

    Returns:    List of FieldMetaInfo objects (see description above)
    """

  @abstractmethod
  def setFieldStatistics(self,fieldStats):
    """
    Propagates field statistics to the model in case some of its machinery
    needs it. 
    
    Parameters:
    
    fieldStats is a dict of dicts with first key being the fieldname and the 
    second key is min,max or other supported statistics.
    """

  @abstractmethod
  def getRuntimeStats(self):
    """ get runtime statistics specific to this model, i.e. activeCellOverlapAvg
        return:
            a dict where keys are statistic names and values are the stats
    """

  @abstractmethod
  def _getLogger(self):
    """ Get the logger for this object. This is a protected method that is used
    by the ModelBase to access the logger created by the subclass

    return:
      A logging.Logger object. Should not be None
    """

  ###############################################################################
  # Common learning/inference methods
  ###############################################################################

  def getInferenceType(self):
    """ Returns the InferenceType of this model. This is immutable"""
    return self.__inferenceType

  def enableLearning(self):
    """ Turn Learning on for the current model """
    self.__learningEnabled = True
    return

  def disableLearning(self):
    """ Turn Learning off for the current model """
    self.__learningEnabled = False
    return

  def isLearningEnabled(self):
    """ Return the Learning state of the current model (True/False) """
    return self.__learningEnabled

  def enableInference(self, inferenceArgs=None):
    """
    Enabled inference for this model.

    Parameters:
    -----------------------------------------------------------------------
      inferenceArgs:      A dictionary of arguments required for inference. These
                          depend on the InferenceType of the current model
    """
    self.__inferenceEnabled = True
    self.__inferenceArgs = inferenceArgs

  def getInferenceArgs(self):
    """
    Returns the dict of arguments for the current inference mode
    """
    return self.__inferenceArgs

  def disableInference(self):
    """Turn Inference off for the current model"""
    self.__inferenceEnabled = False

  def isInferenceEnabled(self):
    """Return the Inference state of the current model (True/False)"""
    return self.__inferenceEnabled

  ###############################################################################
  # Implementation of common save/load functionality
  ###############################################################################
  def save(self, saveModelDir):
    """ Save the model in the given directory

    Parameters:
    -----------------------------------------------------------------------
    saveModelDir:
                  Absolute directory path for saving the experiment.
                  If the directory already exists, it MUST contain a VALID
                  local checkpoint of a model.

    Returns: nothing
    """
    logger = self._getLogger()
    logger.debug("(%s) Creating local checkpoint in %r...",
                       self, saveModelDir)

    modelPickleFilePath = self._getModelPickleFilePath(saveModelDir)

    # Clean up old saved state, if any
    if os.path.exists(saveModelDir):
      if not os.path.isdir(saveModelDir):
        raise Exception(("Existing filesystem entry <%s> is not a model"
                         " checkpoint -- refusing to delete (not a directory)") \
                          % saveModelDir)
      if not os.path.isfile(modelPickleFilePath):
        raise Exception(("Existing filesystem entry <%s> is not a model"
                         " checkpoint -- refusing to delete"\
                         " (%s missing or not a file)") % \
                          (saveModelDir, modelPickleFilePath))

      shutil.rmtree(saveModelDir)

    # Create a new directory for saving state
    self.__makeDirectoryFromAbsolutePath(saveModelDir)

    with open(modelPickleFilePath, 'wb') as modelPickleFile:
      logger.debug("(%s) Pickling Model instance...", self)

      pickle.dump(self, modelPickleFile)

      logger.debug("(%s) Finished pickling Model instance", self)


    # Tell the model to save extra data, if any, that's too big for pickling
    self._serializeExtraData(extraDataDir=self._getModelExtraDataDir(saveModelDir))

    logger.debug("(%s) Finished creating local checkpoint", self)

    return

  def _serializeExtraData(self, extraDataDir):
    """This is a protected method that is called during serialization with an
    external directory path. It can be overridden by subclasses to bypass pickle
    for saving large binary states. This is called by ModelBase only

    extraDataDir:
                  Model's extra data directory path
    """
    pass

  @classmethod
  def load(cls, savedModelDir):
    """ Load saved model

    Parameters:
    -----------------------------------------------------------------------
    savedModelDir:
                  directory of where the experiment is to be or was saved

    Returns: the loaded model instance
    """
    logger = opfutils.initLogger(cls)
    logger.debug("Loading model from local checkpoint at %r...", savedModelDir)

    # Load the model
    modelPickleFilePath = Model._getModelPickleFilePath(savedModelDir)

    with open(modelPickleFilePath, 'rb') as modelPickleFile:
      logger.debug("Unpickling Model instance...")

      model = pickle.load(modelPickleFile)

      logger.debug("Finished unpickling Model instance")

    # Tell the model to load extra data, if any, that was too big for pickling
    model._deSerializeExtraData(
        extraDataDir=Model._getModelExtraDataDir(savedModelDir))

    logger.debug("Finished Loading model from local checkpoint")

    return model

  def _deSerializeExtraData(self, extraDataDir):
    """ This is a protected method that is called during deserialization
    (after __setstate__) with an external directory path. It can be overridden by
    subclasses to bypass pickle for loading large binary states. This is called
    by ModelBase only

    extraDataDir:
                  Model's extra data directory path
    """
    pass

  @staticmethod
  def _getModelPickleFilePath(saveModelDir):
    """
    saveModelDir:
                  directory of where the experiment is to be or was saved

    Returns:      the absolute path to the model's pickle file
    """
    path = os.path.join(saveModelDir, "model.pkl")
    path = os.path.abspath(path)
    return path

  @staticmethod
  def _getModelExtraDataDir(saveModelDir):
    """
    saveModelDir:
                  directory of where the experiment is to be or was saved

    Returns:      the absolute path to the directory for the model's own
                  "extra data" (i.e., data that's too big for pickling)
    """
    path = os.path.join(saveModelDir, "modelextradata")
    path = os.path.abspath(path)

    return path

  @staticmethod
  def __makeDirectoryFromAbsolutePath(absDirPath):
    """ Makes directory for the given directory path if it doesn't already exist
    in the filesystem.

    absDirPath:   absolute path of the directory to create.

    Returns:      nothing

    Exceptions:         OSError if directory creation fails
    """

    assert os.path.isabs(absDirPath)

    # Create the experiment directory
    # TODO Is default mode (0777) appropriate?
    try:
      os.makedirs(absDirPath)
    except OSError as e:
      if e.errno != os.errno.EEXIST:
        raise

    return
