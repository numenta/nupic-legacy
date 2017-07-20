# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

"""Module defining the OPF Model base class."""

import cPickle as pickle
import json
import os
import shutil
from abc import ABCMeta, abstractmethod

from nupic.frameworks.opf.opf_utils import InferenceType
import nupic.frameworks.opf.opf_utils as opf_utils
from nupic.serializable import Serializable


class Model(Serializable):
  """ This is the base class that all OPF Model implementations should
  subclass.

  It includes a number of virtual methods, to be overridden by subclasses,
  as well as some shared functionality for saving/loading models

  :param inferenceType: (:class:`~nupic.frameworks.opf.opf_utils.InferenceType`)
         A value that specifies the type of inference.
  """

  __metaclass__ = ABCMeta

  def __init__(self, inferenceType=None, proto=None):
    """
    :param opf_utils.InferenceType inferenceType: mutually-exclusive with proto
                                                  arg
    :param proto: capnp ModelProto message reader for deserializing;
                  mutually-exclusive with the other constructor args.
    """
    assert inferenceType is not None and proto is None or (
      inferenceType is None and proto is not None), (
      "proto and other constructor args are mutually exclusive")

    if proto is None:
      self._numPredictions = 0
      self.__inferenceType =  inferenceType
      self.__learningEnabled = True
      self.__inferenceEnabled = True
      self.__inferenceArgs = {}
    else:
      self._numPredictions = proto.numPredictions
      inferenceType = str(proto.inferenceType)
      # upper-case first letter to be compatible with enum InferenceType naming
      inferenceType = inferenceType[:1].upper() + inferenceType[1:]
      self.__inferenceType = InferenceType.getValue(inferenceType)

      self.__learningEnabled = proto.learningEnabled
      self.__inferenceEnabled = proto.inferenceEnabled
      self.__inferenceArgs = json.loads(proto.inferenceArgs)

  def run(self, inputRecord):
    """
    Run one iteration of this model.

    :param inputRecord: (object)
           A record object formatted according to
           :meth:`~nupic.data.record_stream.RecordStreamIface.getNextRecord` or
           :meth:`~nupic.data.record_stream.RecordStreamIface.getNextRecordDict`
           result format.
    :returns: (:class:`~nupic.frameworks.opf.opf_utils.ModelResult`)
             An ModelResult namedtuple. The contents of ModelResult.inferences
             depends on the the specific inference type of this model, which
             can be queried by :meth:`.getInferenceType`.
    """
    # 0-based prediction index for ModelResult
    predictionNumber = self._numPredictions
    self._numPredictions += 1
    result = opf_utils.ModelResult(predictionNumber=predictionNumber,
                                   rawInput=inputRecord)
    return result

  @abstractmethod
  def finishLearning(self):
    """ Place the model in a permanent "finished learning" mode.
    In such a mode the model will not be able to learn from subsequent input
    records.

    .. note:: Upon completion of this command, learning may not be resumed on
       the given instance of the model (e.g., the implementation may optimize
       itself by pruning data structures that are necessary for learning).
    """

  @abstractmethod
  def resetSequenceStates(self):
    """
    Signal that the input record is the start of a new sequence. Normally called
    to force the delineation of a sequence, such as between OPF tasks.
    """

  @abstractmethod
  def getFieldInfo(self, includeClassifierOnlyField=False):
    """
    Return the sequence of :class:`~nupic.data.field_meta.FieldMetaInfo` objects
    specifying the format of Model's output.

    This may be different than the list of
    :class:`~nupic.data.field_meta.FieldMetaInfo` objects supplied at
    initialization (e.g., due to the transcoding of some input fields into
    meta-fields, such as datetime -> dayOfWeek, timeOfDay, etc.).

    :param includeClassifierOnlyField: (bool)
           If True, any field which is only sent to the classifier (i.e. not
           sent in to the bottom of the network) is also included
    :returns: (list) of :class:`~nupic.data.field_meta.FieldMetaInfo` objects.
    """

  @abstractmethod
  def setFieldStatistics(self, fieldStats):
    """ Propagate field statistics to the model in case some of its machinery
    needs it.

    :param fieldStats: (dict)
           A dict of dicts with first key being the fieldname and the second
           key is min,max or other supported statistics.
    """

  @abstractmethod
  def getRuntimeStats(self):
    """ Get runtime statistics specific to this model, i.e.
    ``activeCellOverlapAvg``.

    :returns: (dict) A {statistic names: stats} dictionary
    """

  @abstractmethod
  def _getLogger(self):
    """ Get the logger for this object.
    This is a protected method that is used by the ModelBase to access the
    logger created by the subclass.

    :returns: (Logger) A Logger object, it should not be None.
    """

  ###############################################################################
  # Common learning/inference methods
  ###############################################################################

  def getInferenceType(self):
    """ Return the InferenceType of this model.
    This is immutable.

    :returns: :class:`~nupic.frameworks.opf.opf_utils.InferenceType`
    """
    return self.__inferenceType

  def enableLearning(self):
    """ Turn Learning on for the current model. """
    self.__learningEnabled = True
    return

  def disableLearning(self):
    """ Turn Learning off for the current model. """
    self.__learningEnabled = False
    return

  def isLearningEnabled(self):
    """ Return the Learning state of the current model.

    :returns: (bool) The learning state
    """
    return self.__learningEnabled

  def enableInference(self, inferenceArgs=None):
    """ Enable inference for this model.

    :param inferenceArgs: (dict)
           A dictionary of arguments required for inference. These depend on
           the InferenceType of the current model
    """
    self.__inferenceEnabled = True
    self.__inferenceArgs = inferenceArgs

  def getInferenceArgs(self):
    """ Return the dict of arguments for the current inference mode.

    :returns: (dict) The arguments of the inference mode
    """
    return self.__inferenceArgs

  def disableInference(self):
    """ Turn Inference off for the current model. """
    self.__inferenceEnabled = False

  def isInferenceEnabled(self):
    """ Return the inference state of the current model.

    :returns: (bool) The inference state
    """
    return self.__inferenceEnabled

  @staticmethod
  def getSchema():
    """Return the pycapnp proto type that the class uses for serialization.

    This is used to convert the proto into the proper type before passing it
    into the read or write method of the subclass.
    """
    raise NotImplementedError()

  @staticmethod
  def _getModelCheckpointFilePath(checkpointDir):
    """ Return the absolute path of the model's checkpoint file.

    :param checkpointDir: (string)
           Directory of where the experiment is to be or was saved
    :returns: (string) An absolute path.
    """
    path = os.path.join(checkpointDir, "model.data")
    path = os.path.abspath(path)
    return path

  def writeToCheckpoint(self, checkpointDir):
    """Serializes model using capnproto and writes data to ``checkpointDir``"""
    proto = self.getSchema().new_message()

    self.write(proto)

    checkpointPath = self._getModelCheckpointFilePath(checkpointDir)

    # Clean up old saved state, if any
    if os.path.exists(checkpointDir):
      if not os.path.isdir(checkpointDir):
        raise Exception(("Existing filesystem entry <%s> is not a model"
                         " checkpoint -- refusing to delete (not a directory)") \
                          % checkpointDir)
      if not os.path.isfile(checkpointPath):
        raise Exception(("Existing filesystem entry <%s> is not a model"
                         " checkpoint -- refusing to delete"\
                         " (%s missing or not a file)") % \
                          (checkpointDir, checkpointPath))

      shutil.rmtree(checkpointDir)

    # Create a new directory for saving state
    self.__makeDirectoryFromAbsolutePath(checkpointDir)

    with open(checkpointPath, 'wb') as f:
      proto.write(f)

  @classmethod
  def readFromCheckpoint(cls, checkpointDir):
    """Deerializes model from checkpointDir using capnproto"""
    checkpointPath = cls._getModelCheckpointFilePath(checkpointDir)

    with open(checkpointPath, 'r') as f:
      proto = cls.getSchema().read(f)

    model = cls.read(proto)
    return model


  def writeBaseToProto(self, proto):
    """Save the state maintained by the Model base class

    :param proto: capnp ModelProto message builder
    """
    inferenceType = self.getInferenceType()
    # lower-case first letter to be compatible with capnproto enum naming
    inferenceType = inferenceType[:1].lower() + inferenceType[1:]
    proto.inferenceType = inferenceType

    proto.numPredictions = self._numPredictions

    proto.learningEnabled = self.__learningEnabled
    proto.inferenceEnabled = self.__inferenceEnabled
    proto.inferenceArgs = json.dumps(self.__inferenceArgs)


  def write(self, proto):
    """Write state to proto object.

    The type of proto is determined by :meth:`getSchema`.
    """
    raise NotImplementedError()


  @classmethod
  def read(cls, proto):
    """Read state from proto object.

    The type of proto is determined by :meth:`getSchema`.
    """
    raise NotImplementedError()

  ###############################################################################
  # Implementation of common save/load functionality
  ###############################################################################

  def save(self, saveModelDir):
    """ Save the model in the given directory.

    :param saveModelDir: (string)
         Absolute directory path for saving the model. This directory should
         only be used to store a saved model. If the directory does not exist,
         it will be created automatically and populated with model data. A
         pre-existing directory will only be accepted if it contains previously
         saved model data. If such a directory is given, the full contents of
         the directory will be deleted and replaced with current model data.
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
    """ Protected method that is called during serialization with an external
    directory path. It can be overridden by subclasses to bypass pickle for
    saving large binary states.
    This is called by ModelBase only.

    :param extraDataDir: (string) Model's extra data directory path
    """
    pass

  @classmethod
  def load(cls, savedModelDir):
    """ Load saved model.

    :param savedModelDir: (string)
           Directory of where the experiment is to be or was saved
    :returns: (:class:`Model`) The loaded model instance
    """
    logger = opf_utils.initLogger(cls)
    logger.debug("Loading model from local checkpoint at %r...", savedModelDir)

    # Load the model
    modelPickleFilePath = Model._getModelPickleFilePath(savedModelDir)

    with open(modelPickleFilePath, 'r') as modelPickleFile:
      logger.debug("Unpickling Model instance...")

      model = pickle.load(modelPickleFile)

      logger.debug("Finished unpickling Model instance")

    # Tell the model to load extra data, if any, that was too big for pickling
    model._deSerializeExtraData(
        extraDataDir=Model._getModelExtraDataDir(savedModelDir))

    logger.debug("Finished Loading model from local checkpoint")

    return model

  def _deSerializeExtraData(self, extraDataDir):
    """ Protected method that is called during deserialization
    (after __setstate__) with an external directory path.
    It can be overridden by subclasses to bypass pickle for loading large
    binary states.
    This is called by ModelBase only.

    :param extraDataDir: (string) Model's extra data directory path
    """
    pass

  @staticmethod
  def _getModelPickleFilePath(saveModelDir):
    """ Return the absolute path of the model's pickle file.

    :param saveModelDir: (string)
           Directory of where the experiment is to be or was saved
    :returns: (string) An absolute path.
    """
    path = os.path.join(saveModelDir, "model.pkl")
    path = os.path.abspath(path)
    return path

  @staticmethod
  def _getModelExtraDataDir(saveModelDir):
    """ Return the absolute path to the directory where the model's own
    "extra data" are stored (i.e., data that's too big for pickling).

    :param saveModelDir: (string)
           Directory of where the experiment is to be or was saved
    :returns: (string) An absolute path.
    """
    path = os.path.join(saveModelDir, "modelextradata")
    path = os.path.abspath(path)

    return path

  @staticmethod
  def __makeDirectoryFromAbsolutePath(absDirPath):
    """ Make directory for the given directory path if it doesn't already
    exist in the filesystem.

    :param absDirPath: (string) Absolute path of the directory to create
    @exception (Exception) OSError if directory creation fails
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
