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

# This file contains utility functions that are used
# internally by the prediction framework. It should not be
# imported by description files. (see helpers.py)


from nupic.support.enum import Enum


# TODO: This file contains duplicates of 'InferenceElement', 'InferenceType',
# and 'ModelResult' copied from nupic.frameworks.opf
# Will want to change this in the future!

class InferenceElement(Enum(
              prediction="prediction",
              encodings="encodings",
              classification="classification",
              anomalyScore="anomalyScore",
              anomalyLabel="anomalyLabel",
              classConfidences="classConfidences",
              multiStepPredictions="multiStepPredictions",
              multiStepBestPredictions="multiStepBestPredictions",
              multiStepBucketLikelihoods="multiStepBucketLikelihoods",
              multiStepBucketValues="multiStepBucketValues",
              )):

  __inferenceInputMap = {
    "prediction":               "dataRow",
    "encodings":                "dataEncodings",
    "classification":           "category",
    "classConfidences":         "category",
    "multiStepPredictions":     "dataDict",
    "multiStepBestPredictions": "dataDict",
  }

  __temporalInferenceElements = None

  @staticmethod
  def getInputElement(inferenceElement):
    """ Get the sensor input element that corresponds to the given inference
    element. This is mainly used for metrics and prediction logging
    """
    return InferenceElement.__inferenceInputMap.get(inferenceElement, None)

  @staticmethod
  def isTemporal(inferenceElement):
    """ Returns True if the inference from this timestep is predicted the input
    for the NEXT timestep.

    NOTE: This should only be checked IF THE MODEL'S INFERENCE TYPE IS ALSO
    TEMPORAL. That is, a temporal model CAN have non-temporal inference elements,
    but a non-temporal model CANNOT have temporal inference elements
    """
    if InferenceElement.__temporalInferenceElements is None:
      InferenceElement.__temporalInferenceElements = \
                                set([InferenceElement.prediction])

    return inferenceElement in InferenceElement.__temporalInferenceElements

  @staticmethod
  def getTemporalDelay(inferenceElement, key=None):
    """ Returns the number of records that elapse between when an inference is
    made and when the corresponding input record will appear. For example, a
    multistep prediction for 3 timesteps out will have a delay of 3


    Parameters:
    -----------------------------------------------------------------------

    inferenceElement:   The InferenceElement value being delayed
    key:                If the inference is a dictionary type, this specifies
                        key for the sub-inference that is being delayed
    """
    # -----------------------------------------------------------------------
    # For next step prediction, we shift by 1
    if inferenceElement in (InferenceElement.prediction,
                            InferenceElement.encodings):
      return 1
    # -----------------------------------------------------------------------
    # For classification, anomaly scores, the inferences immediately succeed the
    # inputs
    if inferenceElement in (InferenceElement.anomalyScore,
                            InferenceElement.anomalyLabel,
                            InferenceElement.classification,
                            InferenceElement.classConfidences):
      return 0
    # -----------------------------------------------------------------------
    # For multistep prediction, the delay is based on the key in the inference
    # dictionary
    if inferenceElement in (InferenceElement.multiStepPredictions,
                            InferenceElement.multiStepBestPredictions):
      return int(key)

    # -----------------------------------------------------------------------
    # default: return 0
    return 0

  @staticmethod
  def getMaxDelay(inferences):
    """
    Returns the maximum delay for the InferenceElements in the inference
    dictionary

    Parameters:
    -----------------------------------------------------------------------
    inferences:   A dictionary where the keys are InferenceElements
    """
    maxDelay = 0
    for inferenceElement, inference in inferences.iteritems():
      if isinstance(inference, dict):
        for key in inference.iterkeys():
          maxDelay = max(InferenceElement.getTemporalDelay(inferenceElement,
                                                            key),
                         maxDelay)
      else:
        maxDelay = max(InferenceElement.getTemporalDelay(inferenceElement),
                       maxDelay)


    return maxDelay

class InferenceType(Enum("TemporalNextStep",
                         "TemporalClassification",
                         "NontemporalClassification",
                         "TemporalAnomaly",
                         "NontemporalAnomaly",
                         "TemporalMultiStep",
                         "NontemporalMultiStep")):


  __temporalInferenceTypes = None

  @staticmethod
  def isTemporal(inferenceType):
    """ Returns True if the inference type is 'temporal', i.e. requires a
    temporal memory in the network.
    """
    if InferenceType.__temporalInferenceTypes is None:
      InferenceType.__temporalInferenceTypes = \
                                set([InferenceType.TemporalNextStep,
                                     InferenceType.TemporalClassification,
                                     InferenceType.TemporalAnomaly,
                                     InferenceType.TemporalMultiStep,
                                     InferenceType.NontemporalMultiStep])

    return inferenceType in InferenceType.__temporalInferenceTypes



# ModelResult - A structure that contains the input to a model and the resulting
# predictions as well as any related information related to the predictions.
#
# predictionNumber: The prediction number. This should start at 0 and increase
#                   with each new ModelResult.
#
# rawInput: The input record, as input by the user. This is a dictionary-like
#           object which has attributes whose names are the same as the input
#            field names
#
# sensorInput: A SensorInput object that represents the input record, as it
#              appears right before it is encoded. This may differ from the raw
#              input in that certain input fields (such as DateTime fields) may
#              be split into multiple encoded fields
#
# inferences: A dictionary of inferences. Each key is a InferenceType constant
#              which corresponds to the type of prediction being made. Each value
#              is a ___ element that corresponds to the actual prediction by the
#              model, including auxillary information; TODO: fix description.
#
# metrics:    The metrics corresponding to the most-recent prediction/ground
#             truth pair

class ModelResult(object):

  __slots__= ("predictionNumber", "rawInput", "sensorInput", "inferences",
              "metrics", "predictedFieldIdx", "predictedFieldName")

  def __init__(self,
               predictionNumber=None,
               rawInput=None,
               sensorInput=None,
               inferences=None,
               metrics=None,
               predictedFieldIdx=None,
               predictedFieldName=None):
    self.predictionNumber = predictionNumber
    self.rawInput = rawInput
    self.sensorInput = sensorInput
    self.inferences = inferences
    self.metrics = metrics
    self.predictedFieldIdx = predictedFieldIdx
    self.predictedFieldName = predictedFieldName


  def __repr__(self):
     return ("ModelResult("
             "\tpredictionNumber={0}\n"
             "\trawInput={1}\n"
             "\tsensorInput={2}\n"
             "\tinferences={3}\n"
             "\tmetrics={4}\n"
             "\tpredictedFieldIdx={5}\n"
             "\tpredictedFieldName={6}\n"
             ")").format(self.predictionNumber,
                        self.rawInput,
                        self.sensorInput,
                        self.inferences,
                        self.metrics,
                        self.predictedFieldIdx,
                        self.predictedFieldName)
