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

""" @file clamodel.py

Encapsulation of CLAnetwork that implements the ModelBase.

"""

import copy
import math
import os
import json
import itertools
import logging
import traceback
from collections import deque
from operator import itemgetter

import numpy

from nupic.frameworks.opf.model import Model
from nupic.algorithms.anomaly import Anomaly
from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
from nupic.data.fieldmeta import FieldMetaSpecial, FieldMetaInfo
from nupic.encoders import MultiEncoder, DeltaEncoder
from nupic.engine import Network
from nupic.support.fshelpers import makeDirectoryFromAbsolutePath
from nupic.frameworks.opf.opfutils import (InferenceType,
                      InferenceElement,
                      SensorInput,
                      ClassifierInput,
                      initLogger)


DEFAULT_LIKELIHOOD_THRESHOLD = 0.0001
DEFAULT_MAX_PREDICTIONS_PER_STEP = 8

DEFAULT_ANOMALY_TRAINRECORDS = 4000
DEFAULT_ANOMALY_THRESHOLD = 1.1
DEFAULT_ANOMALY_CACHESIZE = 10000


def requireAnomalyModel(func):
  """
  Decorator for functions that require anomaly models.
  """
  def _decorator(self, *args, **kwargs):
    if not self.getInferenceType() == InferenceType.TemporalAnomaly:
      raise RuntimeError("Method required a TemporalAnomaly model.")
    if self._getAnomalyClassifier() is None:
      raise RuntimeError("Model does not support this command. Model must"
          "be an active anomalyDetector model.")
    return func(self, *args, **kwargs)
  return _decorator



class NetworkInfo(object):
  """ Data type used as return value type by
  CLAModel.__createCLANetwork()
  """

  def __init__(self, net, statsCollectors):
    """
    net:          The CLA Network instance
    statsCollectors:
                  Sequence of 0 or more CLAStatistic-based instances
    """
    self.net = net
    self.statsCollectors = statsCollectors
    return

  def __repr__(self):
    return "NetworkInfo(net=%r, statsCollectors=%r)" % (
              self.net, self.statsCollectors)



class CLAModel(Model):

  __supportedInferenceKindSet = set((InferenceType.TemporalNextStep,
                                     InferenceType.TemporalClassification,
                                     InferenceType.NontemporalClassification,
                                     InferenceType.NontemporalAnomaly,
                                     InferenceType.TemporalAnomaly,
                                     InferenceType.TemporalMultiStep,
                                     InferenceType.NontemporalMultiStep))

  __myClassName = "CLAModel"


  def __init__(self,
      sensorParams,
      inferenceType=InferenceType.TemporalNextStep,
      predictedField=None,
      spEnable=True,
      spParams={},

      # TODO: We can't figure out what this is. Remove?
      trainSPNetOnlyIfRequested=False,
      tpEnable=True,
      tpParams={},
      clEnable=True,
      clParams={},
      anomalyParams={},
      minLikelihoodThreshold=DEFAULT_LIKELIHOOD_THRESHOLD,
      maxPredictionsPerStep=DEFAULT_MAX_PREDICTIONS_PER_STEP):
    """CLAModel constructor.

    Args:
      inferenceType: A value from the InferenceType enum class.
      predictedField: The field to predict for multistep prediction.
      sensorParams: A dictionary specifying the sensor parameters.
      spEnable: Whether or not to use a spatial pooler.
      spParams: A dictionary specifying the spatial pooler parameters. These
          are passed to the spatial pooler.
      trainSPNetOnlyIfRequested: If set, don't create an SP network unless the
          user requests SP metrics.
      tpEnable: Whether to use a temporal pooler.
      tpParams: A dictionary specifying the temporal pooler parameters. These
          are passed to the temporal pooler.
      clEnable: Whether to use the classifier. If false, the classifier will
          not be created and no predictions will be generated.
      clParams: A dictionary specifying the classifier parameters. These are
          are passed to the classifier.
      anomalyParams: Anomaly detection parameters
      minLikelihoodThreshold: The minimum likelihood value to include in
          inferences.  Currently only applies to multistep inferences.
      maxPredictionsPerStep: Maximum number of predictions to include for
          each step in inferences. The predictions with highest likelihood are
          included.
    """
    if not inferenceType in self.__supportedInferenceKindSet:
      raise ValueError("{0} received incompatible inference type: {1}"\
                       .format(self.__class__, inferenceType))

    # Call super class constructor
    super(CLAModel, self).__init__(inferenceType)

    # self.__restoringFromState is set to True by our __setstate__ method
    # and back to False at completion of our _deSerializeExtraData() method.
    self.__restoringFromState = False
    self.__restoringFromV1 = False

    # Intitialize logging
    self.__logger = initLogger(self)
    self.__logger.debug("Instantiating %s." % self.__myClassName)


    self._minLikelihoodThreshold = minLikelihoodThreshold
    self._maxPredictionsPerStep = maxPredictionsPerStep

    # set up learning parameters (note: these may be replaced via
    # enable/disable//SP/TP//Learning methods)
    self.__spLearningEnabled = bool(spEnable)
    self.__tpLearningEnabled = bool(tpEnable)

    # Explicitly exclude the TP if this type of inference doesn't require it
    if not InferenceType.isTemporal(self.getInferenceType()) \
       or self.getInferenceType() == InferenceType.NontemporalMultiStep:
      tpEnable = False

    self._netInfo = None
    self._hasSP = spEnable
    self._hasTP = tpEnable
    self._hasCL = clEnable

    self._classifierInputEncoder = None
    self._predictedFieldIdx = None
    self._predictedFieldName = None
    self._numFields = None
    # init anomaly
    windowSize = anomalyParams.get("slidingWindowSize", None)
    mode = anomalyParams.get("mode", "pure")
    anomalyThreshold = anomalyParams.get("autoDetectThreshold", None)
    self._anomalyInst = Anomaly(slidingWindowSize=windowSize, mode=mode,
                                binaryAnomalyThreshold=anomalyThreshold)

    # -----------------------------------------------------------------------
    # Create the network
    self._netInfo = self.__createCLANetwork(
        sensorParams, spEnable, spParams, tpEnable, tpParams, clEnable,
        clParams, anomalyParams)


    # Initialize Spatial Anomaly detection parameters
    if self.getInferenceType() == InferenceType.NontemporalAnomaly:
      self._getSPRegion().setParameter("anomalyMode", True)

    # Initialize Temporal Anomaly detection parameters
    if self.getInferenceType() == InferenceType.TemporalAnomaly:
      self._getTPRegion().setParameter("anomalyMode", True)
      self._prevPredictedColumns = numpy.array([])

    # -----------------------------------------------------------------------
    # This flag, if present tells us not to train the SP network unless
    #  the user specifically asks for the SP inference metric
    self.__trainSPNetOnlyIfRequested = trainSPNetOnlyIfRequested

    self.__numRunCalls = 0

    # Tracks whether finishedLearning() has been called
    self.__finishedLearning = False

    self.__logger.debug("Instantiated %s" % self.__class__.__name__)

    self._input = None

    return


  def getParameter(self, paramName):
    if paramName == '__numRunCalls':
      return self.__numRunCalls
    else:
      raise RuntimeError("'%s' parameter is not exposed by clamodel." % \
        (paramName))


  def resetSequenceStates(self):
    """ [virtual method override] Resets the model's sequence states. Normally
    called to force the delineation of a sequence, such as between OPF tasks.
    """

    if self._hasTP:
      # Reset TP's sequence states
      self._getTPRegion().executeCommand(['resetSequenceStates'])

      self.__logger.debug("CLAModel.resetSequenceStates(): reset temporal "
                         "pooler's sequence states")

      return


  def finishLearning(self):
    """ [virtual method override] Places the model in a permanent "finished
    learning" mode where it will not be able to learn from subsequent input
    records.

    NOTE: Upon completion of this command, learning may not be resumed on
    the given instance of the model (e.g., the implementation may optimize
    itself by pruning data structures that are necessary for learning)
    """
    assert not self.__finishedLearning

    if self._hasSP:
      # Finish SP learning
      self._getSPRegion().executeCommand(['finishLearning'])
      self.__logger.debug(
        "CLAModel.finishLearning(): finished SP learning")

    if self._hasTP:
      # Finish temporal network's TP learning
      self._getTPRegion().executeCommand(['finishLearning'])
      self.__logger.debug(
        "CLAModel.finishLearning(): finished TP learning")

    self.__spLearningEnabled = self.__tpLearningEnabled = False
    self.__finishedLearning = True
    return


  def setFieldStatistics(self,fieldStats):
    encoder = self._getEncoder()
    # Set the stats for the encoders. The first argument to setFieldStats
    # is the field name of the encoder. Since we are using a multiencoder
    # we leave it blank, the multiencoder will propagate the field names to the
    # underlying encoders
    encoder.setFieldStats('',fieldStats)


  def enableLearning(self):
    """[override] Turn Learning on for the current model """
    super(CLAModel, self).enableLearning()
    self.setEncoderLearning(True)


  def disableLearning(self):
    """[override] Turn Learning off for the current model """
    super(CLAModel, self).disableLearning()
    self.setEncoderLearning(False)


  def setEncoderLearning(self,learningEnabled):
    self._getEncoder().setLearning(learningEnabled)


  # Anomaly Accessor Methods
  @requireAnomalyModel
  def setAnomalyParameter(self, param, value):
    """
    Set a parameter of the anomaly classifier within this model.
    """
    self._getAnomalyClassifier().setParameter(param, value)


  @requireAnomalyModel
  def getAnomalyParameter(self, param):
    """
    Get a parameter of the anomaly classifier within this model.
    """
    return self._getAnomalyClassifier().getParameter(param)


  @requireAnomalyModel
  def anomalyRemoveLabels(self, start, end, labelFilter):
    """
    Remove labels from the anomaly classifier within this model.
    """
    self._getAnomalyClassifier().getSelf().removeLabels(start, end, labelFilter)


  @requireAnomalyModel
  def anomalyAddLabel(self, start, end, labelName):
    """
    Add labels from the anomaly classifier within this model.
    """
    self._getAnomalyClassifier().getSelf().addLabel(start, end, labelName)


  @requireAnomalyModel
  def anomalyGetLabels(self, start, end):
    """
    Get labels from the anomaly classifier within this model.
    """
    return self._getAnomalyClassifier().getSelf().getLabels(start, end)


  def run(self, inputRecord):
    """ run one iteration of this model.
            args:
                inputRecord is a record object formatted according to
                    nupic.data.RecordStream.getNextRecordDict() result format.

            return:
                An ModelResult class (see opfutils.py) The contents of
                ModelResult.inferences depends on the the specific inference
                type of this model, which can be queried by getInferenceType()
    """
    assert not self.__restoringFromState
    assert inputRecord

    results = super(CLAModel, self).run(inputRecord)

    self.__numRunCalls += 1

    if self.__logger.isEnabledFor(logging.DEBUG):
      self.__logger.debug("CLAModel.run() inputRecord=%s", (inputRecord))

    results.inferences = {}
    self._input = inputRecord

    # -------------------------------------------------------------------------
    # Turn learning on or off?
    if '_learning' in inputRecord:
      if inputRecord['_learning']:
        self.enableLearning()
      else:
        self.disableLearning()


    ###########################################################################
    # Predictions and Learning
    ###########################################################################
    self._sensorCompute(inputRecord)
    self._spCompute()
    self._tpCompute()

    results.sensorInput = self._getSensorInputRecord(inputRecord)

    inferences = {}

    # TODO: Reconstruction and temporal classification not used. Remove
    if self._isReconstructionModel():
      inferences = self._reconstructionCompute()
    elif self._isMultiStepModel():
      inferences = self._multiStepCompute(rawInput=inputRecord)
    # For temporal classification. Not used, and might not work anymore
    elif self._isClassificationModel():
      inferences = self._classificationCompute()

    results.inferences.update(inferences)

    inferences = self._anomalyCompute()
    results.inferences.update(inferences)

    # -----------------------------------------------------------------------
    # Store the index and name of the predictedField
    results.predictedFieldIdx = self._predictedFieldIdx
    results.predictedFieldName = self._predictedFieldName
    results.classifierInput = self._getClassifierInputRecord(inputRecord)

    # =========================================================================
    # output
    assert (not self.isInferenceEnabled() or results.inferences is not None), \
            "unexpected inferences: %r" %  results.inferences


    #self.__logger.setLevel(logging.DEBUG)
    if self.__logger.isEnabledFor(logging.DEBUG):
      self.__logger.debug("inputRecord: %r, results: %r" % (inputRecord,
                                                            results))

    return results


  def _getSensorInputRecord(self, inputRecord):
    """
    inputRecord - dict containing the input to the sensor

    Return a 'SensorInput' object, which represents the 'parsed'
    representation of the input record
    """
    sensor = self._getSensorRegion()
    dataRow = copy.deepcopy(sensor.getSelf().getOutputValues('sourceOut'))
    dataDict = copy.deepcopy(inputRecord)
    inputRecordEncodings = sensor.getSelf().getOutputValues('sourceEncodings')
    inputRecordCategory = int(sensor.getOutputData('categoryOut')[0])
    resetOut = sensor.getOutputData('resetOut')[0]

    return SensorInput(dataRow=dataRow,
                       dataDict=dataDict,
                       dataEncodings=inputRecordEncodings,
                       sequenceReset=resetOut,
                       category=inputRecordCategory)

  def _getClassifierInputRecord(self, inputRecord):
    """
    inputRecord - dict containing the input to the sensor

    Return a 'ClassifierInput' object, which contains the mapped
    bucket index for input Record
    """
    absoluteValue = None
    bucketIdx = None
    
    if self._predictedFieldName is not None and self._classifierInputEncoder is not None:
      absoluteValue = inputRecord[self._predictedFieldName]
      bucketIdx = self._classifierInputEncoder.getBucketIndices(absoluteValue)[0]

    return ClassifierInput(dataRow=absoluteValue,
                           bucketIndex=bucketIdx)

  def _sensorCompute(self, inputRecord):
    sensor = self._getSensorRegion()
    self._getDataSource().push(inputRecord)
    sensor.setParameter('topDownMode', False)
    sensor.prepareInputs()
    try:
      sensor.compute()
    except StopIteration as e:
      raise Exception("Unexpected StopIteration", e,
                      "ACTUAL TRACEBACK: %s" % traceback.format_exc())


  def _spCompute(self):
    sp = self._getSPRegion()
    if sp is None:
      return

    sp.setParameter('topDownMode', False)
    sp.setParameter('inferenceMode', self.isInferenceEnabled())
    sp.setParameter('learningMode', self.isLearningEnabled())
    sp.prepareInputs()
    sp.compute()


  def _tpCompute(self):
    tp = self._getTPRegion()
    if tp is None:
      return

    if (self.getInferenceType() == InferenceType.TemporalAnomaly or
        self._isReconstructionModel()):
      topDownCompute = True
    else:
      topDownCompute = False

    tp = self._getTPRegion()
    tp.setParameter('topDownMode', topDownCompute)
    tp.setParameter('inferenceMode', self.isInferenceEnabled())
    tp.setParameter('learningMode', self.isLearningEnabled())
    tp.prepareInputs()
    tp.compute()


  def _isReconstructionModel(self):
    inferenceType = self.getInferenceType()
    inferenceArgs = self.getInferenceArgs()

    if inferenceType == InferenceType.TemporalNextStep:
      return True

    if inferenceArgs:
      return inferenceArgs.get('useReconstruction', False)
    return False


  def _isMultiStepModel(self):
    return self.getInferenceType() in (InferenceType.NontemporalMultiStep,
                                       InferenceType.NontemporalClassification,
                                       InferenceType.TemporalMultiStep,
                                       InferenceType.TemporalAnomaly)


  def _isClassificationModel(self):
    return self.getInferenceType() in InferenceType.TemporalClassification


  def _multiStepCompute(self, rawInput):
    patternNZ = None
    if self._getTPRegion() is not None:
      tp = self._getTPRegion()
      tpOutput = tp.getSelf()._tfdr.infActiveState['t']
      patternNZ = tpOutput.reshape(-1).nonzero()[0]
    elif self._getSPRegion() is not None:
      sp = self._getSPRegion()
      spOutput = sp.getOutputData('bottomUpOut')
      patternNZ = spOutput.nonzero()[0]
    elif self._getSensorRegion() is not None:
      sensor = self._getSensorRegion()
      sensorOutput = sensor.getOutputData('dataOut')
      patternNZ = sensorOutput.nonzero()[0]
    else:
      raise RuntimeError("Attempted to make multistep prediction without"
                         "TP, SP, or Sensor regions")

    inputTSRecordIdx = rawInput.get('_timestampRecordIdx')
    return self._handleCLAClassifierMultiStep(
                                        patternNZ=patternNZ,
                                        inputTSRecordIdx=inputTSRecordIdx,
                                        rawInput=rawInput)


  def _classificationCompute(self):
    inference = {}
    classifier = self._getClassifierRegion()
    classifier.setParameter('inferenceMode', True)
    classifier.setParameter('learningMode', self.isLearningEnabled())
    classifier.prepareInputs()
    classifier.compute()

    # What we get out is the score for each category. The argmax is
    # then the index of the winning category
    classificationDist = classifier.getOutputData('categoriesOut')
    classification = classificationDist.argmax()
    probabilities = classifier.getOutputData('categoryProbabilitiesOut')
    numCategories = classifier.getParameter('activeOutputCount')
    classConfidences = dict(zip(xrange(numCategories), probabilities))

    inference[InferenceElement.classification] = classification
    inference[InferenceElement.classConfidences] = {0: classConfidences}

    return inference


  def _reconstructionCompute(self):
    if not self.isInferenceEnabled():
      return {}

    sp = self._getSPRegion()
    sensor = self._getSensorRegion()

    #--------------------------------------------------
    # SP Top-down flow
    sp.setParameter('topDownMode', True)
    sp.prepareInputs()
    sp.compute()

    #--------------------------------------------------
    # Sensor Top-down flow
    sensor.setParameter('topDownMode', True)
    sensor.prepareInputs()
    sensor.compute()

    # Need to call getOutputValues() instead of going through getOutputData()
    # because the return values may contain strings, which cannot be passed
    # through the Region.cpp code.

    # predictionRow is a list of values, one for each field. The value is
    #  in the same type as the original input to the encoder and may be a
    #  string for category fields for example.
    predictionRow = copy.copy(sensor.getSelf().getOutputValues('temporalTopDownOut'))
    predictionFieldEncodings = sensor.getSelf().getOutputValues('temporalTopDownEncodings')

    inferences =  {}
    inferences[InferenceElement.prediction] =  tuple(predictionRow)
    inferences[InferenceElement.encodings] = tuple(predictionFieldEncodings)

    return inferences


  def _anomalyCompute(self):
    """
    Compute Anomaly score, if required
    """
    inferenceType = self.getInferenceType()

    inferences = {}
    sp = self._getSPRegion()
    score = None
    if inferenceType == InferenceType.NontemporalAnomaly:
      score = sp.getOutputData("anomalyScore")[0] #TODO move from SP to Anomaly ?

    elif inferenceType == InferenceType.TemporalAnomaly:
      tp = self._getTPRegion()

      if sp is not None:
        activeColumns = sp.getOutputData("bottomUpOut").nonzero()[0]
      else:
        sensor = self._getSensorRegion()
        activeColumns = sensor.getOutputData('dataOut').nonzero()[0]

      if not self._predictedFieldName in self._input:
        raise ValueError(
          "Expected predicted field '%s' in input row, but was not found!" 
          % self._predictedFieldName
        )
      # Calculate the anomaly score using the active columns
      # and previous predicted columns.
      score = self._anomalyInst.compute(
                                   activeColumns,
                                   self._prevPredictedColumns,
                                   inputValue=self._input[self._predictedFieldName])

      # Store the predicted columns for the next timestep.
      predictedColumns = tp.getOutputData("topDownOut").nonzero()[0]
      self._prevPredictedColumns = copy.deepcopy(predictedColumns)

      # Calculate the classifier's output and use the result as the anomaly
      # label. Stores as string of results.

      # TODO: make labels work with non-SP models
      if sp is not None:
        self._getAnomalyClassifier().setParameter(
            "activeColumnCount", len(activeColumns))
        self._getAnomalyClassifier().prepareInputs()
        self._getAnomalyClassifier().compute()
        labels = self._getAnomalyClassifier().getSelf().getLabelResults()
        inferences[InferenceElement.anomalyLabel] = "%s" % labels

    inferences[InferenceElement.anomalyScore] = score
    return inferences


  def _handleCLAClassifierMultiStep(self, patternNZ,
                                    inputTSRecordIdx,
                                    rawInput):
    """ Handle the CLA Classifier compute logic when implementing multi-step
    prediction. This is where the patternNZ is associated with one of the
    other fields from the dataset 0 to N steps in the future. This method is
    used by each type of network (encoder only, SP only, SP +TP) to handle the
    compute logic through the CLA Classifier. It fills in the inference dict with
    the results of the compute.

    Parameters:
    -------------------------------------------------------------------
    patternNZ:  The input the CLA Classifier as a list of active input indices
    inputTSRecordIdx: The index of the record as computed from the timestamp
                  and aggregation interval. This normally increments by 1
                  each time unless there are missing records. If there is no
                  aggregation interval or timestamp in the data, this will be
                  None.
    rawInput:   The raw input to the sensor, as a dict.
    """
    inferenceArgs = self.getInferenceArgs()
    predictedFieldName = inferenceArgs.get('predictedField', None)
    if predictedFieldName is None:
      raise ValueError(
        "No predicted field was enabled! Did you call enableInference()?"
      )
    self._predictedFieldName = predictedFieldName

    classifier = self._getClassifierRegion()
    if not self._hasCL or classifier is None:
      # No classifier so return an empty dict for inferences.
      return {}

    sensor = self._getSensorRegion()
    minLikelihoodThreshold = self._minLikelihoodThreshold
    maxPredictionsPerStep = self._maxPredictionsPerStep
    needLearning = self.isLearningEnabled()
    inferences = {}

    # Get the classifier input encoder, if we don't have it already
    if self._classifierInputEncoder is None:
      if predictedFieldName is None:
        raise RuntimeError("This experiment description is missing "
              "the 'predictedField' in its config, which is required "
              "for multi-step prediction inference.")

      encoderList = sensor.getSelf().encoder.getEncoderList()
      self._numFields = len(encoderList)

      # This is getting index of predicted field if being fed to CLA.
      fieldNames = sensor.getSelf().encoder.getScalarNames()
      if predictedFieldName in fieldNames:
        self._predictedFieldIdx = fieldNames.index(predictedFieldName)
      else:
        # Predicted field was not fed into the network, only to the classifier
        self._predictedFieldIdx = None

      # In a multi-step model, the classifier input encoder is separate from
      #  the other encoders and always disabled from going into the bottom of
      # the network.
      if sensor.getSelf().disabledEncoder is not None:
        encoderList = sensor.getSelf().disabledEncoder.getEncoderList()
      else:
        encoderList = []
      if len(encoderList) >= 1:
        fieldNames = sensor.getSelf().disabledEncoder.getScalarNames()
        self._classifierInputEncoder = encoderList[fieldNames.index(
                                                        predictedFieldName)]
      else:
        # Legacy multi-step networks don't have a separate encoder for the
        #  classifier, so use the one that goes into the bottom of the network
        encoderList = sensor.getSelf().encoder.getEncoderList()
        self._classifierInputEncoder = encoderList[self._predictedFieldIdx]



    # Get the actual value and the bucket index for this sample. The
    # predicted field may not be enabled for input to the network, so we
    # explicitly encode it outside of the sensor
    # TODO: All this logic could be simpler if in the encoder itself
    if not predictedFieldName in rawInput:
      raise ValueError("Input row does not contain a value for the predicted "
                       "field configured for this model. Missing value for '%s'"
                       % predictedFieldName)
    absoluteValue = rawInput[predictedFieldName]
    bucketIdx = self._classifierInputEncoder.getBucketIndices(absoluteValue)[0]

    # Convert the absolute values to deltas if necessary
    # The bucket index should be handled correctly by the underlying delta encoder
    if isinstance(self._classifierInputEncoder, DeltaEncoder):
      # Make the delta before any values have been seen 0 so that we do not mess up the
      # range for the adaptive scalar encoder.
      if not hasattr(self,"_ms_prevVal"):
        self._ms_prevVal = absoluteValue
      prevValue = self._ms_prevVal
      self._ms_prevVal = absoluteValue
      actualValue = absoluteValue - prevValue
    else:
      actualValue = absoluteValue

    if isinstance(actualValue, float) and math.isnan(actualValue):
      actualValue = SENTINEL_VALUE_FOR_MISSING_DATA


    # Pass this information to the classifier's custom compute method
    # so that it can assign the current classification to possibly
    # multiple patterns from the past and current, and also provide
    # the expected classification for some time step(s) in the future.
    classifier.setParameter('inferenceMode', True)
    classifier.setParameter('learningMode', needLearning)
    classificationIn = {'bucketIdx': bucketIdx,
                        'actValue': actualValue}

    # Handle missing records
    if inputTSRecordIdx is not None:
      recordNum = inputTSRecordIdx
    else:
      recordNum = self.__numRunCalls
    clResults = classifier.getSelf().customCompute(recordNum=recordNum,
                                           patternNZ=patternNZ,
                                           classification=classificationIn)

    # ---------------------------------------------------------------
    # Get the prediction for every step ahead learned by the classifier
    predictionSteps = classifier.getParameter('steps')
    predictionSteps = [int(x) for x in predictionSteps.split(',')]

    # We will return the results in this dict. The top level keys
    # are the step number, the values are the relative likelihoods for
    # each classification value in that time step, represented as
    # another dict where the keys are the classification values and
    # the values are the relative likelihoods.
    inferences[InferenceElement.multiStepPredictions] = dict()
    inferences[InferenceElement.multiStepBestPredictions] = dict()
    inferences[InferenceElement.multiStepBucketLikelihoods] = dict()


    # ======================================================================
    # Plug in the predictions for each requested time step.
    for steps in predictionSteps:
      # From the clResults, compute the predicted actual value. The
      # CLAClassifier classifies the bucket index and returns a list of
      # relative likelihoods for each bucket. Let's find the max one
      # and then look up the actual value from that bucket index
      likelihoodsVec = clResults[steps]
      bucketValues = clResults['actualValues']

      # Create a dict of value:likelihood pairs. We can't simply use
      #  dict(zip(bucketValues, likelihoodsVec)) because there might be
      #  duplicate bucketValues (this happens early on in the model when
      #  it doesn't have actual values for each bucket so it returns
      #  multiple buckets with the same default actual value).
      likelihoodsDict = dict()
      bestActValue = None
      bestProb = None
      for (actValue, prob) in zip(bucketValues, likelihoodsVec):
        if actValue in likelihoodsDict:
          likelihoodsDict[actValue] += prob
        else:
          likelihoodsDict[actValue] = prob
        # Keep track of best
        if bestProb is None or likelihoodsDict[actValue] > bestProb:
          bestProb = likelihoodsDict[actValue]
          bestActValue = actValue


      # Remove entries with 0 likelihood or likelihood less than
      # minLikelihoodThreshold, but don't leave an empty dict.
      likelihoodsDict = CLAModel._removeUnlikelyPredictions(
          likelihoodsDict, minLikelihoodThreshold, maxPredictionsPerStep)

      # calculate likelihood for each bucket
      bucketLikelihood = {}
      for k in likelihoodsDict.keys():
        bucketLikelihood[self._classifierInputEncoder.getBucketIndices(k)[0]] = (
                                                                likelihoodsDict[k])

      # ---------------------------------------------------------------------
      # If we have a delta encoder, we have to shift our predicted output value
      #  by the sum of the deltas
      if isinstance(self._classifierInputEncoder, DeltaEncoder):
        # Get the prediction history for this number of timesteps.
        # The prediction history is a store of the previous best predicted values.
        # This is used to get the final shift from the current absolute value.
        if not hasattr(self, '_ms_predHistories'):
          self._ms_predHistories = dict()
        predHistories = self._ms_predHistories
        if not steps in predHistories:
          predHistories[steps] = deque()
        predHistory = predHistories[steps]

        # Find the sum of the deltas for the steps and use this to generate
        # an offset from the current absolute value
        sumDelta = sum(predHistory)
        offsetDict = dict()
        for (k, v) in likelihoodsDict.iteritems():
          if k is not None:
            # Reconstruct the absolute value based on the current actual value,
            # the best predicted values from the previous iterations,
            # and the current predicted delta
            offsetDict[absoluteValue+float(k)+sumDelta] = v

        # calculate likelihood for each bucket
        bucketLikelihoodOffset = {}
        for k in offsetDict.keys():
          bucketLikelihoodOffset[self._classifierInputEncoder.getBucketIndices(k)[0]] = (
                                                                            offsetDict[k])


        # Push the current best delta to the history buffer for reconstructing the final delta
        if bestActValue is not None:
          predHistory.append(bestActValue)
        # If we don't need any more values in the predictionHistory, pop off
        # the earliest one.
        if len(predHistory) >= steps:
          predHistory.popleft()

        # Provide the offsetDict as the return value
        if len(offsetDict)>0:
          inferences[InferenceElement.multiStepPredictions][steps] = offsetDict
          inferences[InferenceElement.multiStepBucketLikelihoods][steps] = bucketLikelihoodOffset
        else:
          inferences[InferenceElement.multiStepPredictions][steps] = likelihoodsDict
          inferences[InferenceElement.multiStepBucketLikelihoods][steps] = bucketLikelihood

        if bestActValue is None:
          inferences[InferenceElement.multiStepBestPredictions][steps] = None
        else:
          inferences[InferenceElement.multiStepBestPredictions][steps] = (
            absoluteValue + sumDelta + bestActValue)

      # ---------------------------------------------------------------------
      # Normal case, no delta encoder. Just plug in all our multi-step predictions
      #  with likelihoods as well as our best prediction
      else:
        # The multiStepPredictions element holds the probabilities for each
        #  bucket
        inferences[InferenceElement.multiStepPredictions][steps] = (
                                                      likelihoodsDict)
        inferences[InferenceElement.multiStepBestPredictions][steps] = (
                                                      bestActValue)
        inferences[InferenceElement.multiStepBucketLikelihoods][steps] = (
                                                      bucketLikelihood)


    return inferences


  @classmethod
  def _removeUnlikelyPredictions(cls, likelihoodsDict, minLikelihoodThreshold,
                                 maxPredictionsPerStep):
    """Remove entries with 0 likelihood or likelihood less than
    minLikelihoodThreshold, but don't leave an empty dict.
    """
    maxVal = (None, None)
    for (k, v) in likelihoodsDict.items():
      if len(likelihoodsDict) <= 1:
        break
      if maxVal[0] is None or v >= maxVal[1]:
        if maxVal[0] is not None and maxVal[1] < minLikelihoodThreshold:
          del likelihoodsDict[maxVal[0]]
        maxVal = (k, v)
      elif v < minLikelihoodThreshold:
        del likelihoodsDict[k]
    # Limit the number of predictions to include.
    likelihoodsDict = dict(sorted(likelihoodsDict.iteritems(),
                                  key=itemgetter(1),
                                  reverse=True)[:maxPredictionsPerStep])
    return likelihoodsDict


  def getRuntimeStats(self):
    """ [virtual method override] get runtime statistics specific to this
    model, i.e. activeCellOverlapAvg

        return:
            a dict where keys are statistic names and values are the stats
    """
    ret = {"numRunCalls" : self.__numRunCalls}

    #--------------------------------------------------
    # Query temporal network stats
    temporalStats = dict()
    if self._hasTP:
      for stat in self._netInfo.statsCollectors:
        sdict = stat.getStats()
        temporalStats.update(sdict)

    ret[InferenceType.getLabel(InferenceType.TemporalNextStep)] = temporalStats


    return ret


  def getFieldInfo(self, includeClassifierOnlyField=False):
    """ [virtual method override]
        Returns the sequence of FieldMetaInfo objects specifying this
        Model's output; note that this may be different than the list of
        FieldMetaInfo objects supplied at initialization (e.g., due to the
        transcoding of some input fields into meta-fields, such as datetime
        -> dayOfWeek, timeOfDay, etc.)

    Returns:    List of FieldMetaInfo objects (see description above)
    """

    encoder = self._getEncoder()

    fieldNames = encoder.getScalarNames()
    fieldTypes = encoder.getDecoderOutputFieldTypes()
    assert len(fieldNames) == len(fieldTypes)

    # Also include the classifierOnly field?
    encoder = self._getClassifierOnlyEncoder()
    if includeClassifierOnlyField and encoder is not None:
      addFieldNames = encoder.getScalarNames()
      addFieldTypes = encoder.getDecoderOutputFieldTypes()
      assert len(addFieldNames) == len(addFieldTypes)
      fieldNames = list(fieldNames) + addFieldNames
      fieldTypes = list(fieldTypes) + addFieldTypes

    fieldMetaList = map(FieldMetaInfo._make,
                        zip(fieldNames,
                            fieldTypes,
                            itertools.repeat(FieldMetaSpecial.none)))

    return tuple(fieldMetaList)


  def _getLogger(self):
    """ Get the logger for this object. This is a protected method that is used
    by the Model to access the logger created by the subclass

    return:
      A logging.Logger object. Should not be None
    """
    return self.__logger


  def _getSPRegion(self):
    """
    Returns reference to the network's SP region
    """
    return self._netInfo.net.regions.get('SP', None)


  def _getTPRegion(self):
    """
    Returns reference to the network's TP region
    """
    return self._netInfo.net.regions.get('TP', None)


  def _getSensorRegion(self):
    """
    Returns reference to the network's Sensor region
    """
    return self._netInfo.net.regions['sensor']


  def _getClassifierRegion(self):
    """
    Returns reference to the network's Classifier region
    """
    if (self._netInfo.net is not None and
        "Classifier" in self._netInfo.net.regions):
      return self._netInfo.net.regions["Classifier"]
    else:
      return None


  def _getAnomalyClassifier(self):
    return self._netInfo.net.regions.get("AnomalyClassifier", None)


  def _getEncoder(self):
    """
    Returns:  sensor region's encoder for the given network
    """
    return  self._getSensorRegion().getSelf().encoder

  def _getClassifierOnlyEncoder(self):
    """
    Returns:  sensor region's encoder that is sent only to the classifier,
                not to the bottom of the network
    """
    return  self._getSensorRegion().getSelf().disabledEncoder


  def _getDataSource(self):
    """
    Returns: data source that we installed in sensor region
    """
    return self._getSensorRegion().getSelf().dataSource


  def __createCLANetwork(self, sensorParams, spEnable, spParams, tpEnable,
                         tpParams, clEnable, clParams, anomalyParams):
    """ Create a CLA network and return it.

    description:  CLA Model description dictionary (TODO: define schema)
    Returns:      NetworkInfo instance;
    """

    #--------------------------------------------------
    # Create the network
    n = Network()


    #--------------------------------------------------
    # Add the Sensor
    n.addRegion("sensor", "py.RecordSensor", json.dumps(dict(verbosity=sensorParams['verbosity'])))
    sensor = n.regions['sensor'].getSelf()

    enabledEncoders = copy.deepcopy(sensorParams['encoders'])
    for name, params in enabledEncoders.items():
      if params is not None:
        classifierOnly = params.pop('classifierOnly', False)
        if classifierOnly:
          enabledEncoders.pop(name)

    # Disabled encoders are encoders that are fed to CLAClassifierRegion but not
    # SP or TP Regions. This is to handle the case where the predicted field
    # is not fed through the SP/TP. We typically just have one of these now.
    disabledEncoders = copy.deepcopy(sensorParams['encoders'])
    for name, params in disabledEncoders.items():
      if params is None:
        disabledEncoders.pop(name)
      else:
        classifierOnly = params.pop('classifierOnly', False)
        if not classifierOnly:
          disabledEncoders.pop(name)

    encoder = MultiEncoder(enabledEncoders)

    sensor.encoder = encoder
    sensor.disabledEncoder = MultiEncoder(disabledEncoders)
    sensor.dataSource = DataBuffer()

    prevRegion = "sensor"
    prevRegionWidth = encoder.getWidth()

    # SP is not enabled for spatial classification network
    if spEnable:
      spParams = spParams.copy()
      spParams['inputWidth'] = prevRegionWidth
      self.__logger.debug("Adding SPRegion; spParams: %r" % spParams)
      n.addRegion("SP", "py.SPRegion", json.dumps(spParams))

      # Link SP region
      n.link("sensor", "SP", "UniformLink", "")
      n.link("sensor", "SP", "UniformLink", "", srcOutput="resetOut",
             destInput="resetIn")

      n.link("SP", "sensor", "UniformLink", "", srcOutput="spatialTopDownOut",
             destInput="spatialTopDownIn")
      n.link("SP", "sensor", "UniformLink", "", srcOutput="temporalTopDownOut",
             destInput="temporalTopDownIn")

      prevRegion = "SP"
      prevRegionWidth = spParams['columnCount']

    if tpEnable:
      tpParams = tpParams.copy()
      if prevRegion == 'sensor':
        tpParams['inputWidth'] = tpParams['columnCount'] = prevRegionWidth
      else:
        assert tpParams['columnCount'] == prevRegionWidth
        tpParams['inputWidth'] = tpParams['columnCount']

      self.__logger.debug("Adding TPRegion; tpParams: %r" % tpParams)
      n.addRegion("TP", "py.TPRegion", json.dumps(tpParams))

      # Link TP region
      n.link(prevRegion, "TP", "UniformLink", "")
      if prevRegion != "sensor":
        n.link("TP", prevRegion, "UniformLink", "", srcOutput="topDownOut",
           destInput="topDownIn")
      else:
        n.link("TP", prevRegion, "UniformLink", "", srcOutput="topDownOut",
           destInput="temporalTopDownIn")
      n.link("sensor", "TP", "UniformLink", "", srcOutput="resetOut",
         destInput="resetIn")

      prevRegion = "TP"
      prevRegionWidth = tpParams['inputWidth']

    if clEnable and clParams is not None:
      clParams = clParams.copy()
      clRegionName = clParams.pop('regionName')
      self.__logger.debug("Adding %s; clParams: %r" % (clRegionName,
                                                      clParams))
      n.addRegion("Classifier", "py.%s" % str(clRegionName), json.dumps(clParams))

      n.link("sensor", "Classifier", "UniformLink", "", srcOutput="categoryOut",
             destInput="categoryIn")

      n.link(prevRegion, "Classifier", "UniformLink", "")

    if self.getInferenceType() == InferenceType.TemporalAnomaly:
      anomalyClParams = dict(
          trainRecords=anomalyParams.get('autoDetectWaitRecords', None),
          cacheSize=anomalyParams.get('anomalyCacheRecords', None)
      )
      self._addAnomalyClassifierRegion(n, anomalyClParams, spEnable, tpEnable)

    #--------------------------------------------------
    # NuPIC doesn't initialize the network until you try to run it
    # but users may want to access components in a setup callback
    n.initialize()

    return NetworkInfo(net=n, statsCollectors=[])


  def __getstate__(self):
    """
    Return serializable state.  This function will return a version of the
    __dict__ with data that shouldn't be pickled stripped out. In particular,
    the CLA Network is stripped out because it has it's own serialization
    mechanism)

    See also: _serializeExtraData()
    """

    # Remove ephemeral member variables from state
    state = self.__dict__.copy()

    state["_netInfo"] = NetworkInfo(net=None,
                        statsCollectors=self._netInfo.statsCollectors)


    for ephemeral in [self.__manglePrivateMemberName("__restoringFromState"),
                      self.__manglePrivateMemberName("__logger")]:
      state.pop(ephemeral)

    return state


  def __setstate__(self, state):
    """
    Set the state of ourself from a serialized state.

    See also: _deSerializeExtraData
    """

    self.__dict__.update(state)

    # Mark beginning of restoration.
    #
    # self.__restoringFromState will be reset to False upon completion of
    # object restoration in _deSerializeExtraData()
    self.__restoringFromState = True

    # set up logging
    self.__logger = initLogger(self)


    # =========================================================================
    # TODO: Temporary migration solution
    if not hasattr(self, "_Model__inferenceType"):
      self.__restoringFromV1 = True
      self._hasSP = True
      if self.__temporalNetInfo is not None:
        self._Model__inferenceType = InferenceType.TemporalNextStep
        self._netInfo = self.__temporalNetInfo
        self._hasTP = True
      else:
        raise RuntimeError("The Nontemporal inference type is not supported")

      self._Model__inferenceArgs = {}
      self._Model__learningEnabled = True
      self._Model__inferenceEnabled = True

      # Remove obsolete members
      self.__dict__.pop("_CLAModel__encoderNetInfo", None)
      self.__dict__.pop("_CLAModel__nonTemporalNetInfo", None)
      self.__dict__.pop("_CLAModel__temporalNetInfo", None)


    # -----------------------------------------------------------------------
    # Migrate from v2
    if not hasattr(self, "_netInfo"):
      self._hasSP = False
      self._hasTP = False
      if self.__encoderNetInfo is not None:
        self._netInfo = self.__encoderNetInfo
      elif self.__nonTemporalNetInfo is not None:
        self._netInfo = self.__nonTemporalNetInfo
        self._hasSP = True
      else:
        self._netInfo = self.__temporalNetInfo
        self._hasSP = True
        self._hasTP = True

      # Remove obsolete members
      self.__dict__.pop("_CLAModel__encoderNetInfo", None)
      self.__dict__.pop("_CLAModel__nonTemporalNetInfo", None)
      self.__dict__.pop("_CLAModel__temporalNetInfo", None)


    # -----------------------------------------------------------------------
    # Migrate from when Anomaly was not separate class
    if not hasattr(self, "_anomalyInst"):
      self._anomalyInst = Anomaly()


    # This gets filled in during the first infer because it can only be
    #  determined at run-time
    self._classifierInputEncoder = None

    if not hasattr(self, '_minLikelihoodThreshold'):
      self._minLikelihoodThreshold = DEFAULT_LIKELIHOOD_THRESHOLD

    if not hasattr(self, '_maxPredictionsPerStep'):
      self._maxPredictionsPerStep = DEFAULT_MAX_PREDICTIONS_PER_STEP

    if not hasattr(self, '_hasCL'):
      self._hasCL = (self._getClassifierRegion() is not None)

    self.__logger.debug("Restoring %s from state..." % self.__class__.__name__)


  def _serializeExtraData(self, extraDataDir):
    """ [virtual method override] This method is called during serialization
    with an external directory path that can be used to bypass pickle for saving
    large binary states.

    extraDataDir:
                  Model's extra data directory path
    """
    makeDirectoryFromAbsolutePath(extraDataDir)

    #--------------------------------------------------
    # Save the network
    outputDir = self.__getNetworkStateDirectory(extraDataDir=extraDataDir)

    self.__logger.debug("Serializing network...")

    self._netInfo.net.save(outputDir)

    self.__logger.debug("Finished serializing network")

    return


  def _deSerializeExtraData(self, extraDataDir):
    """ [virtual method override] This method is called during deserialization
    (after __setstate__) with an external directory path that can be used to
    bypass pickle for loading large binary states.

    extraDataDir:
                  Model's extra data directory path
    """
    assert self.__restoringFromState

    #--------------------------------------------------
    # Check to make sure that our Network member wasn't restored from
    # serialized data
    assert (self._netInfo.net is None), "Network was already unpickled"

    #--------------------------------------------------
    # Restore the network
    stateDir = self.__getNetworkStateDirectory(extraDataDir=extraDataDir)

    self.__logger.debug(
      "(%s) De-serializing network...", self)

    self._netInfo.net = Network(stateDir)

    self.__logger.debug(
      "(%s) Finished de-serializing network", self)


    # NuPIC doesn't initialize the network until you try to run it
    # but users may want to access components in a setup callback
    self._netInfo.net.initialize()


    # Used for backwards compatibility for anomaly classification models.
    # Previous versions used the CLAModelClassifierHelper class for utilizing
    # the KNN classifier. Current version uses KNNAnomalyClassifierRegion to
    # encapsulate all the classifier functionality.
    if self.getInferenceType() == InferenceType.TemporalAnomaly:
      classifierType = self._getAnomalyClassifier().getSelf().__class__.__name__
      if classifierType is 'KNNClassifierRegion':

        anomalyClParams = dict(
          trainRecords=self._classifier_helper._autoDetectWaitRecords,
          cacheSize=self._classifier_helper._history_length,
        )

        spEnable = (self._getSPRegion() is not None)
        tpEnable = True

        # Store original KNN region
        knnRegion = self._getAnomalyClassifier().getSelf()

        # Add new KNNAnomalyClassifierRegion
        self._addAnomalyClassifierRegion(self._netInfo.net, anomalyClParams,
                                         spEnable, tpEnable)

        # Restore state
        self._getAnomalyClassifier().getSelf()._iteration = self.__numRunCalls
        self._getAnomalyClassifier().getSelf()._recordsCache = (
            self._classifier_helper.saved_states)
        self._getAnomalyClassifier().getSelf().saved_categories = (
            self._classifier_helper.saved_categories)
        self._getAnomalyClassifier().getSelf()._knnclassifier = knnRegion

        # Set TP to output neccessary information
        self._getTPRegion().setParameter('anomalyMode', True)

        # Remove old classifier_helper
        del self._classifier_helper

        self._netInfo.net.initialize()

    #--------------------------------------------------
    # Mark end of restoration from state
    self.__restoringFromState = False

    self.__logger.debug("(%s) Finished restoring from state", self)

    return


  def _addAnomalyClassifierRegion(self, network, params, spEnable, tpEnable):
    """
    Attaches an 'AnomalyClassifier' region to the network. Will remove current
    'AnomalyClassifier' region if it exists.

    Parameters
    -----------
    network - network to add the AnomalyClassifier region
    params - parameters to pass to the region
    spEnable - True if network has an SP region
    tpEnable - True if network has a TP region; Currently requires True
    """

    allParams = copy.deepcopy(params)
    knnParams = dict(k=1,
                     distanceMethod='rawOverlap',
                     distanceNorm=1,
                     doBinarization=1,
                     replaceDuplicates=0,
                     maxStoredPatterns=1000)
    allParams.update(knnParams)

    # Set defaults if not set
    if allParams['trainRecords'] is None:
      allParams['trainRecords'] = DEFAULT_ANOMALY_TRAINRECORDS

    if allParams['cacheSize'] is None:
      allParams['cacheSize'] = DEFAULT_ANOMALY_CACHESIZE

    # Remove current instance if already created (used for deserializing)
    if self._netInfo is not None and self._netInfo.net is not None \
              and self._getAnomalyClassifier() is not None:
      self._netInfo.net.removeRegion('AnomalyClassifier')

    network.addRegion("AnomalyClassifier",
                      "py.KNNAnomalyClassifierRegion",
                      json.dumps(allParams))

    # Attach link to SP
    if spEnable:
      network.link("SP", "AnomalyClassifier", "UniformLink", "",
          srcOutput="bottomUpOut", destInput="spBottomUpOut")
    else:
      network.link("sensor", "AnomalyClassifier", "UniformLink", "",
          srcOutput="dataOut", destInput="spBottomUpOut")

    # Attach link to TP
    if tpEnable:
      network.link("TP", "AnomalyClassifier", "UniformLink", "",
              srcOutput="topDownOut", destInput="tpTopDownOut")
      network.link("TP", "AnomalyClassifier", "UniformLink", "",
              srcOutput="lrnActiveStateT", destInput="tpLrnActiveStateT")
    else:
      raise RuntimeError("TemporalAnomaly models require a TP region.")


  def __getNetworkStateDirectory(self, extraDataDir):
    """
    extraDataDir:
                  Model's extra data directory path
    Returns:      Absolute directory path for saving CLA Network
    """
    if self.__restoringFromV1:
      if self.getInferenceType() == InferenceType.TemporalNextStep:
        leafName = 'temporal'+ "-network.nta"
      else:
        leafName = 'nonTemporal'+ "-network.nta"
    else:
      leafName = InferenceType.getLabel(self.getInferenceType()) + "-network.nta"
    path = os.path.join(extraDataDir, leafName)
    path = os.path.abspath(path)
    return path


  def __manglePrivateMemberName(self, privateMemberName, skipCheck=False):
    """ Mangles the given mangled (private) member name; a mangled member name
    is one whose name begins with two or more underscores and ends with one
    or zero underscores.

    privateMemberName:
                  The private member name (e.g., "__logger")

    skipCheck:    Pass True to skip test for presence of the demangled member
                  in our instance.

    Returns:      The demangled member name (e.g., "_CLAModel__logger")
    """

    assert privateMemberName.startswith("__"), \
           "%r doesn't start with __" % privateMemberName
    assert not privateMemberName.startswith("___"), \
           "%r starts with ___" % privateMemberName
    assert not privateMemberName.endswith("__"), \
           "%r ends with more than one underscore" % privateMemberName

    realName = "_" + (self.__myClassName).lstrip("_") + privateMemberName

    if not skipCheck:
      # This will throw an exception if the member is missing
      getattr(self, realName)

    return realName



class DataBuffer(object):
  """
      A simple FIFO stack. Add data when it's available, and
      implement getNextRecordDict() so DataBuffer can be used as a DataSource
      in a CLA Network.

      Currently, DataBuffer requires the stack to contain 0 or 1 records.
      This requirement may change in the future, and is trivially supported
      by removing the assertions.
  """
  def __init__(self):
    self.stack = []

  def push(self, data):
    assert len(self.stack) == 0

    # Copy the data, because sensor's pre-encoding filters (e.g.,
    # AutoResetFilter) may modify it.  Our caller relies on the input record
    # remaining unmodified.
    data = data.__class__(data)

    self.stack.append(data)

  def getNextRecordDict(self):
    assert len(self.stack) > 0
    return self.stack.pop()




