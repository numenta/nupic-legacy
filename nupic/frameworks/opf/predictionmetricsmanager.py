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

# This script implements PredictionMetricsManager, a helper class that handles
# pooling of multiple record and field prediction metrics calculators

import logging
import copy
import pprint
from collections import (namedtuple,
                         deque)

from nupic.data.inference_shifter import InferenceShifter
from nupic.frameworks.opf import metrics

from opfutils import InferenceType, InferenceElement



# MetricValueElement class
#
# Represents an individual metric value element in a list returned by
# PredictionMetricsManager.getMetrics()
#
# spec:           A MetricSpec value (a copy) that was used to construct
#                 the metric instance that generated the metric value
# value:          The metric value
MetricValueElement = namedtuple("MetricValueElement", ["spec", "value"])



class MetricsManager(object):
  """ This is a class to handle the computation of metrics properly. This class
  takes in an inferenceType, and it assumes that it is associcated with a single
  model """

  # Map from inference element to sensor input element. This helps us find the
  # appropriate ground truth field for a given inference element

  def __init__(self, metricSpecs, fieldInfo, inferenceType):
    """
    Constructs a Metrics Manager

    Parameters:
    -----------------------------------------------------------------------
    metricSpecs:    A sequence of MetricSpecs that specify which metrics should
                    be calculated

    inferenceType:  An opfutils.inferenceType value that specifies the inference
                    type of the associated model. This affects how metrics are
                    calculated. FOR EXAMPLE, temporal models save the inference
                    from the previous timestep to match it to the ground truth
                    value in the current timestep
    """

    self.__metricSpecs = []
    self.__metrics = []
    self.__metricLabels = []

    # Maps field names to indices. Useful for looking up input/predictions by
    # field name
    self.__fieldNameIndexMap = dict( [(info.name, i) \
                                      for i, info in enumerate(fieldInfo)] )

    self.__constructMetricsModules(metricSpecs)
    self.__currentGroundTruth = None
    self.__currentInference = None
    self.__currentResult = None

    self.__isTemporal = InferenceType.isTemporal(inferenceType)
    if self.__isTemporal:
      self.__inferenceShifter = InferenceShifter()


  def update(self, results):
    """
    Compute the new metrics values, given the next inference/ground-truth values

    Parameters:
    -----------------------------------------------------------------------
    results:  An opfutils.ModelResult object that was computed during the last
              iteration of the model

    Returns:  A dictionary where each key is the metric-name, and the values are
              it scalar value.

    """

    #print "\n\n---------------------------------------------------------------"
    #print "Model results: \nrawInput:%s \ninferences:%s" % \
    #      (pprint.pformat(results.rawInput), pprint.pformat(results.inferences))
          
    self._addResults(results)

    if  not self.__metricSpecs \
        or self.__currentInference is None:
      return {}

    metricResults = {}
    for metric, spec, label in zip(self.__metrics,
                                   self.__metricSpecs,
                                   self.__metricLabels):

      inferenceElement = spec.inferenceElement
      field = spec.field
      groundTruth = self._getGroundTruth(inferenceElement)
      inference = self._getInference(inferenceElement)
      rawRecord = self._getRawGroundTruth()
      result = self.__currentResult
      if field:
        if type(inference) in (list, tuple):
          if field in self.__fieldNameIndexMap:
            # NOTE: If the predicted field is not fed in at the bottom, we
            #  won't have it in our fieldNameIndexMap
            fieldIndex = self.__fieldNameIndexMap[field]
            inference = inference[fieldIndex]
          else:
            inference = None
        if groundTruth is not None:
          if type(groundTruth) in (list, tuple):
            if field in self.__fieldNameIndexMap:
              # NOTE: If the predicted field is not fed in at the bottom, we
              #  won't have it in our fieldNameIndexMap
              fieldIndex = self.__fieldNameIndexMap[field]
              groundTruth = groundTruth[fieldIndex]
            else:
              groundTruth = None
          else:
            # groundTruth could be a dict based off of field names
            groundTruth = groundTruth[field]

      metric.addInstance(groundTruth=groundTruth,
                         prediction=inference,
                         record=rawRecord,
                         result=result)

      metricResults[label] = metric.getMetric()['value']

    return metricResults


  def getMetrics(self):
    """ Gets the current metric values

    Returns: A dictionary where each key is the metric-name, and the values are
              it scalar value. Same as the output of update()
    """

    result = {}

    for metricObj, label in zip(self.__metrics, self.__metricLabels):
      value = metricObj.getMetric()
      result[label] = value['value']

    return result


  def getMetricDetails(self, metricLabel):
    """ Gets detailed info about a given metric, in addition to its value. This
    may including any statistics or auxilary data that are computed for a given
    metric

    Parameters:
    -----------------------------------------------------------------------
    metricLabel:   The string label of the given metric (see metrics.MetricSpec)

    Returns:  A dictionary of metric information, as returned by
              opf.metric.Metric.getMetric()
    """
    try:
      metricIndex = self.__metricLabels.index(metricLabel)
    except IndexError:
      return None

    return self.__metrics[metricIndex].getMetric()


  def getMetricLabels(self):
    """ Return the list of labels for the metrics that are being calculated"""
    return tuple(self.__metricLabels)


  def _addResults(self, results):
    """
    Stores the current model results in the manager's internal store

    Parameters:
    -----------------------------------------------------------------------
    results:  A ModelResults object that contains the current timestep's
              input/inferences
    """
    # -----------------------------------------------------------------------
    # If the model potentially has temporal inferences.
    if self.__isTemporal:
      shiftedInferences = self.__inferenceShifter.shift(results).inferences
      self.__currentResult = copy.deepcopy(results)
      self.__currentResult.inferences = shiftedInferences
      self.__currentInference = shiftedInferences

    # -----------------------------------------------------------------------
    # The current model has no temporal inferences.
    else:
      self.__currentResult = copy.deepcopy(results)
      self.__currentInference = copy.deepcopy(results.inferences)

    # -----------------------------------------------------------------------
    # Save the current ground-truth results
    self.__currentGroundTruth = copy.deepcopy(results)


  def _getGroundTruth(self, inferenceElement):
    """
    Get the actual value for this field

    Parameters:
    -----------------------------------------------------------------------
    sensorInputElement:       The inference element (part of the inference) that
                            is being used for this metric
    """
    sensorInputElement = InferenceElement.getInputElement(inferenceElement)
    if sensorInputElement is None:
      return None
    return getattr(self.__currentGroundTruth.sensorInput, sensorInputElement)


  def _getInference(self, inferenceElement):
    """
    Get what the inferred value for this field was

    Parameters:
    -----------------------------------------------------------------------
    inferenceElement:       The inference element (part of the inference) that
                            is being used for this metric
    """
    if self.__currentInference is not None:
      return self.__currentInference.get(inferenceElement, None)

    return None


  def _getRawGroundTruth(self):
    """
    Get what the inferred value for this field was

    Parameters:
    -----------------------------------------------------------------------
    inferenceElement:       The inference element (part of the inference) that
                            is being used for this metric
    """

    return self.__currentGroundTruth.rawInput


  def __constructMetricsModules(self, metricSpecs):
    """
    Creates the required metrics modules

    Parameters:
    -----------------------------------------------------------------------
    metricSpecs:
      A sequence of MetricSpec objects that specify which metric modules to
      instantiate
    """
    if not metricSpecs:
      return

    self.__metricSpecs = metricSpecs
    for spec in metricSpecs:
      if not InferenceElement.validate(spec.inferenceElement):
        raise ValueError("Invalid inference element for metric spec: %r" %spec)

      self.__metrics.append(metrics.getModule(spec))
      self.__metricLabels.append(spec.getLabel())



def test():

  _testMetricsMgr()
  _testTemporalShift()
  _testMetricLabels()

  return



def _testMetricsMgr():
  print "*Testing Metrics Managers*..."
  from nupic.data.fieldmeta import (
    FieldMetaInfo,
    FieldMetaType,
    FieldMetaSpecial)

  from nupic.frameworks.opf.metrics import MetricSpec
  from nupic.frameworks.opf.opfutils import ModelResult, SensorInput
  onlineMetrics = (MetricSpec(metric="aae", inferenceElement='', \
                              field="consumption", params={}),)

  print "TESTING METRICS MANAGER (BASIC PLUMBING TEST)..."

  modelFieldMetaInfo = (
    FieldMetaInfo(name='temperature',
                  type=FieldMetaType.float,
                  special=FieldMetaSpecial.none),
    FieldMetaInfo(name='consumption',
              type=FieldMetaType.float,
              special=FieldMetaSpecial.none)
  )

  # -----------------------------------------------------------------------
  # Test to make sure that invalid InferenceElements are caught
  try:
    MetricsManager(
    metricSpecs=onlineMetrics,
    fieldInfo=modelFieldMetaInfo,
    inferenceType=InferenceType.TemporalNextStep)
  except ValueError:
    print "Caught bad inference element: PASS"


  print
  onlineMetrics = (MetricSpec(metric="aae",
                              inferenceElement=InferenceElement.prediction,
                              field="consumption", params={}),)

  temporalMetrics = MetricsManager(
    metricSpecs=onlineMetrics,
    fieldInfo=modelFieldMetaInfo,
    inferenceType=InferenceType.TemporalNextStep)



  inputs = [
    {
      'groundTruthRow' : [9, 7],

      'predictionsDict' : {
        InferenceType.TemporalNextStep: [12, 17]
      }
    },

    {
      'groundTruthRow' : [12, 17],

      'predictionsDict' : {
        InferenceType.TemporalNextStep: [14, 19]
      }
    },

    {
      'groundTruthRow' : [14, 20],

      'predictionsDict' : {
        InferenceType.TemporalNextStep: [16, 21]
      }
    },

    {
      'groundTruthRow' : [9, 7],

      'predictionsDict' : {
        InferenceType.TemporalNextStep:None
      }
    },
  ]


  for element in inputs:
    groundTruthRow=element['groundTruthRow']
    tPredictionRow=element['predictionsDict'][InferenceType.TemporalNextStep]

    result = ModelResult(sensorInput=SensorInput(dataRow=groundTruthRow,
                                                 dataEncodings=None,
                                                 sequenceReset=0,
                                                 category=None),
                         inferences={'prediction':tPredictionRow})

    temporalMetrics.update(result)

  assert temporalMetrics.getMetrics().values()[0] == 15.0 / 3.0, \
          "Expected %f, got %f" %(15.0/3.0,
                                  temporalMetrics.getMetrics().values()[0])
  print "ok"

  return



def _testTemporalShift():
  """ Test to see if the metrics manager correctly shifts records for multistep
  prediction cases
  """
  print "*Testing Multistep temporal shift*..."
  from nupic.data.fieldmeta import (
    FieldMetaInfo,
    FieldMetaType,
    FieldMetaSpecial)

  from nupic.frameworks.opf.metrics import MetricSpec
  from nupic.frameworks.opf.opfutils import ModelResult, SensorInput
  onlineMetrics = ()

  modelFieldMetaInfo = (
    FieldMetaInfo(name='consumption',
              type=FieldMetaType.float,
              special=FieldMetaSpecial.none),)

  mgr = MetricsManager(metricSpecs=onlineMetrics,
                       fieldInfo=modelFieldMetaInfo,
                       inferenceType=InferenceType.TemporalMultiStep)

  groundTruths = [{'consumption':i} for i in range(10)]
  oneStepInfs = reversed(range(10))
  threeStepInfs = range(5, 15)

  for iterNum, gt, os, ts in zip(xrange(10), groundTruths,
                              oneStepInfs, threeStepInfs):
    inferences = {InferenceElement.multiStepPredictions:{1: os, 3: ts}}
    sensorInput = SensorInput(dataDict = [gt])
    result = ModelResult(sensorInput=sensorInput, inferences=inferences)
    mgr.update(result)

    assert mgr._getGroundTruth(InferenceElement.multiStepPredictions)[0] == gt
    if iterNum < 1:
      #assert mgr._getInference(InferenceElement.multiStepPredictions) is None
      assert mgr._getInference(InferenceElement.multiStepPredictions)[1] is None
    else:
      prediction = mgr._getInference(InferenceElement.multiStepPredictions)[1]
      assert prediction == 10 - iterNum

    if iterNum < 3:
      inference = mgr._getInference(InferenceElement.multiStepPredictions)
      assert inference is None or inference[3] is None
    else:
      prediction = mgr._getInference(InferenceElement.multiStepPredictions)[3]
      assert prediction == iterNum + 2



def _testMetricLabels():
  print "\n*Testing Metric Label Generation*..."

  from nupic.frameworks.opf.metrics import MetricSpec

  testTuples = [
    (MetricSpec('rmse', InferenceElement.prediction, 'consumption'),
     "prediction:rmse:field=consumption"),
    (MetricSpec('rmse', InferenceElement.classification),
     "classification:rmse"),
    (MetricSpec('rmse', InferenceElement.encodings, 'pounds',
                params=dict(window=100)),
     "encodings:rmse:window=100:field=pounds"),
    (MetricSpec('aae', InferenceElement.prediction, 'pounds',
                params=dict(window=100, paramA = 10.2, paramB = 20)),
     "prediction:aae:paramA=10.2:paramB=20:window=100:field=pounds"),
    (MetricSpec('aae', InferenceElement.prediction,'pounds',
                params={'window':100, 'paramA':10.2, '1paramB':20}),
     "prediction:aae:1paramB=20:paramA=10.2:window=100:field=pounds"),
    (MetricSpec('aae', InferenceElement.prediction,'pounds',
                params=dict(window=100, paramA = 10.2, paramB =-20)),
     "prediction:aae:paramA=10.2:paramB=-20:window=100:field=pounds"),
    (MetricSpec('aae', InferenceElement.prediction, 'pounds',
                params=dict(window=100, paramA = 10.2, paramB ='square')),
     "prediction:aae:paramA=10.2:paramB='square':window=100:field=pounds"),
  ]

  for test in testTuples:
    try:
      assert test[0].getLabel() == test[1]
    except:
      print "Failed Creating label"
      print "Expected %s \t Got %s" % (test[1], test[0].getLabel())
      return

  print "ok"



if __name__ == "__main__":
  test()
