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

# This file contains utility functions that are used
# internally by the prediction framework. It should not be
# imported by description files. (see helpers.py)


import os
import inspect
import logging
import re
from collections import namedtuple

import nupic.data.json_helpers as jsonhelpers
from nupic.support.enum import Enum



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
  """
  The concept of InferenceElements is a key part of the OPF. A model's inference
  may have multiple parts to it. For example, a model may output both a
  prediction and an anomaly score. Models output their set of inferences as a
  dictionary that is keyed by the enumerated type InferenceElement. Each entry
  in an inference dictionary is considered a separate inference element, and is
  handled independently by the OPF.
  """

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
    """
    Get the sensor input element that corresponds to the given inference
    element. This is mainly used for metrics and prediction logging

    :param inferenceElement: (:class:`.InferenceElement`)
    :return: (string) name of sensor input element
    """
    return InferenceElement.__inferenceInputMap.get(inferenceElement, None)

  @staticmethod
  def isTemporal(inferenceElement):
    """
    .. note:: This should only be checked IF THE MODEL'S INFERENCE TYPE IS ALSO
       TEMPORAL. That is, a temporal model CAN have non-temporal inference
       elements, but a non-temporal model CANNOT have temporal inference
       elements.

    :param inferenceElement: (:class:`.InferenceElement`)
    :return: (bool) ``True`` if the inference from this time step is predicted
             the input for the NEXT time step.
    """
    if InferenceElement.__temporalInferenceElements is None:
      InferenceElement.__temporalInferenceElements = \
                                set([InferenceElement.prediction])

    return inferenceElement in InferenceElement.__temporalInferenceElements

  @staticmethod
  def getTemporalDelay(inferenceElement, key=None):
    """
    :param inferenceElement: (:class:`.InferenceElement`) value being delayed
    :param key: (string) If the inference is a dictionary type, this specifies
                key for the sub-inference that is being delayed.
    :return: (int) the number of records that elapse between when an inference
             is made and when the corresponding input record will appear. For
             example, a multistep prediction for 3 timesteps out will have a
             delay of 3.
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
                            InferenceElement.multiStepBestPredictions,
                            InferenceElement.multiStepBucketLikelihoods):
      return int(key)

    # -----------------------------------------------------------------------
    # default: return 0
    return 0

  @staticmethod
  def getMaxDelay(inferences):
    """
    :param inferences: (dict) where the keys are :class:`.InferenceElement` 
           objects.
    :return: (int) the maximum delay for the :class:`.InferenceElement` objects 
             in the inference dictionary.
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
  """
  Enum: one of the following:

  - ``TemporalNextStep``
  - ``TemporalClassification``
  - ``NontemporalClassification``
  - ``TemporalAnomaly``
  - ``NontemporalAnomaly``
  - ``TemporalMultiStep``
  - ``NontemporalMultiStep``
  """


  __temporalInferenceTypes = None

  @staticmethod
  def isTemporal(inferenceType):
    """
    :param inferenceType: (:class:`.InferenceType`)
    :return: (bool) `True` if the inference type is 'temporal', i.e. requires a
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




class SensorInput(object):
  """
  Represents the mapping of a given inputRecord by the sensor region's encoder.

  This represents the input record, as it appears right before it is encoded.
  This may differ from the raw input in that certain input fields (such as
  DateTime fields) may be split into multiple encoded fields.

  :param dataRow: A data row that is the sensor's ``sourceOut`` mapping of the
                  supplied inputRecord.

  :param dataEncodings: A list of the corresponding bit-array encodings of each
                  value in "dataRow"

  :param sequenceReset:  The sensor's "resetOut" signal (0 or 1) emitted by the
                  sensor's compute logic on the supplied inputRecord; provided
                  for analysis and diagnostics.

  :param dataDict: The raw encoded input to the sensor
  :param category: the categoryOut on the sensor region

  """

  __slots__ = (
    "dataRow", "dataDict", "dataEncodings", "sequenceReset", "category"
  )

  def __init__(self, dataRow=None, dataDict=None, dataEncodings=None,
               sequenceReset=None, category=None):
    self.dataRow = dataRow
    self.dataDict = dataDict
    self.dataEncodings = dataEncodings
    self.sequenceReset = sequenceReset
    self.category = category

  def __repr__(self):
    return "SensorInput("\
          "\tdataRow={0}\n"\
          "\tdataDict={1}\n"\
          "\tdataEncodings={2}\n"\
          "\tsequenceReset={3}\n"\
          "\tcategory={4}\n"\
          ")".format(self.dataRow,
                     self.dataDict,
                     self.dataEncodings,
                     self.sequenceReset,
                     self.category)

  def _asdict(self):
    return dict(dataRow=self.dataRow,
                dataDict=self.dataDict,
                dataEncodings=self.dataEncodings,
                sequenceReset=self.sequenceReset,
                category=self.category)



class ClassifierInput(object):
  """
  Represents the mapping of a given inputRecord by the classifier input encoder.

  :param dataRow: A data row that is the sensor's "sourceOut" mapping of the
                  supplied inputRecord. See :class:`.SensorInput` class for
                  additional details.
  :param bucketIndex: (int) the classifier input encoder's mapping of the
                  dataRow.
  """

  __slots__ = ("dataRow", "bucketIndex")

  def __init__(self, dataRow=None, bucketIndex=None):
    self.dataRow = dataRow
    self.bucketIndex = bucketIndex

  def __repr__(self):
    return "ClassifierInput("\
          "\tdataRow={0}\n"\
          "\tbucketIndex={1}\n"\
          ")".format(self.dataRow,
                     self.bucketIndex)

  def _asdict(self):
    return dict(dataRow=self.dataRow,
                bucketIndex=self.bucketIndex)


class ModelResult(object):
  """
  A structure that contains the input to a model and the resulting predictions
  as well as any related information related to the predictions.

  All params below are accesses as properties of the ModelResult object.

  :param predictionNumber: (int) This should start at 0 and increase with each
         new ModelResult.
  :param rawInput: (object) The input record, as input by the user. This is a
         dictionary-like object which has attributes whose names are the same as
         the input field names
  :param sensorInput: (:class:`~.SensorInput`) object that represents the input
         record
  :param inferences: (dict) Each key is a :class:`~.InferenceType` constant
         which corresponds to the type of prediction being made. Each value is
         a an element that corresponds to the actual prediction by the model,
         including auxillary information.
  :param metrics: (:class:`~nupic.frameworks.opf.metrics.MetricsIface`)
         The metrics corresponding to the most-recent prediction/ground truth
         pair
  :param predictedFieldIdx: (int) predicted field index
  :param predictedFieldName: (string) predicted field name
  :param classifierInput: (:class:`.ClassifierInput`) input from classifier
  """

  __slots__= ("predictionNumber", "rawInput", "sensorInput", "inferences",
              "metrics", "predictedFieldIdx", "predictedFieldName",
              "classifierInput")

  def __init__(self,
               predictionNumber=None,
               rawInput=None,
               sensorInput=None,
               inferences=None,
               metrics=None,
               predictedFieldIdx=None,
               predictedFieldName=None,
               classifierInput=None):
    self.predictionNumber = predictionNumber
    self.rawInput = rawInput
    self.sensorInput = sensorInput
    self.inferences = inferences
    self.metrics = metrics
    self.predictedFieldIdx = predictedFieldIdx
    self.predictedFieldName = predictedFieldName
    self.classifierInput = classifierInput

  def __repr__(self):
     return ("ModelResult("
             "\tpredictionNumber={0}\n"
             "\trawInput={1}\n"
             "\tsensorInput={2}\n"
             "\tinferences={3}\n"
             "\tmetrics={4}\n"
             "\tpredictedFieldIdx={5}\n"
             "\tpredictedFieldName={6}\n"
             "\tclassifierInput={7}\n"
             ")").format(self.predictionNumber,
                        self.rawInput,
                        self.sensorInput,
                        self.inferences,
                        self.metrics,
                        self.predictedFieldIdx,
                        self.predictedFieldName,
                        self.classifierInput)



def validateOpfJsonValue(value, opfJsonSchemaFilename):
  """
  Validate a python object against an OPF json schema file

  :param value: target python object to validate (typically a dictionary)
  :param opfJsonSchemaFilename: (string) OPF json schema filename containing the
         json schema object. (e.g., opfTaskControlSchema.json)
  :raises: jsonhelpers.ValidationError when value fails json validation
  """

  # Create a path by joining the filename with our local json schema root
  jsonSchemaPath = os.path.join(os.path.dirname(__file__),
                                "jsonschema",
                                opfJsonSchemaFilename)

  # Validate
  jsonhelpers.validate(value, schemaPath=jsonSchemaPath)

  return



def initLogger(obj):
  """
  Helper function to create a logger object for the current object with
  the standard Numenta prefix.

  :param obj: (object) to add a logger to
  """
  if inspect.isclass(obj):
    myClass = obj
  else:
    myClass = obj.__class__
  logger = logging.getLogger(".".join(
    ['com.numenta', myClass.__module__, myClass.__name__]))
  return logger



def matchPatterns(patterns, keys):
  """
  Returns a subset of the keys that match any of the given patterns

  :param patterns: (list) regular expressions to match
  :param keys: (list) keys to search for matches
  """
  results = []
  if patterns:
    for pattern in patterns:
      prog = re.compile(pattern)
      for key in keys:
        if prog.match(key):
          results.append(key)
  else:
    return None

  return results
