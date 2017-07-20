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

"""Unit tests for the htm_prediction_model module."""

import datetime
import unittest2 as unittest

from nupic.frameworks.opf.htm_prediction_model import HTMPredictionModel
from nupic.frameworks.opf.model_factory import ModelFactory
from nupic.frameworks.opf.opf_utils import ModelResult



class HTMPredictionModelTest(unittest.TestCase):
  """HTMPredictionModel unit tests."""


  def testRemoveUnlikelyPredictionsEmpty(self):
    result = HTMPredictionModel._removeUnlikelyPredictions({}, 0.01, 3)
    self.assertDictEqual(result, {})


  def testRemoveUnlikelyPredictionsSingleValues(self):
    result = HTMPredictionModel._removeUnlikelyPredictions({1: 0.1}, 0.01, 3)
    self.assertDictEqual(result, {1: 0.1})
    result = HTMPredictionModel._removeUnlikelyPredictions({1: 0.001}, 0.01, 3)
    self.assertDictEqual(result, {1: 0.001})


  def testRemoveUnlikelyPredictionsLikelihoodThresholds(self):
    result = HTMPredictionModel._removeUnlikelyPredictions({1: 0.1, 2: 0.001}, 0.01, 3)
    self.assertDictEqual(result, {1: 0.1})
    result = HTMPredictionModel._removeUnlikelyPredictions({1: 0.001, 2: 0.002}, 0.01, 3)
    self.assertDictEqual(result, {2: 0.002})
    result = HTMPredictionModel._removeUnlikelyPredictions({1: 0.002, 2: 0.001}, 0.01, 3)
    self.assertDictEqual(result, {1: 0.002})


  def testRemoveUnlikelyPredictionsMaxPredictions(self):
    result = HTMPredictionModel._removeUnlikelyPredictions({1: 0.1, 2: 0.2, 3: 0.3},
                                                           0.01, 3)
    self.assertDictEqual(result, {1: 0.1, 2: 0.2, 3: 0.3})
    result = HTMPredictionModel._removeUnlikelyPredictions(
        {1: 0.1, 2: 0.2, 3: 0.3, 4: 0.4}, 0.01, 3)
    self.assertDictEqual(result, {2: 0.2, 3: 0.3, 4: 0.4})


  def testRemoveUnlikelyPredictionsComplex(self):
    result = HTMPredictionModel._removeUnlikelyPredictions(
        {1: 0.1, 2: 0.2, 3: 0.3, 4: 0.004}, 0.01, 3)
    self.assertDictEqual(result, {1: 0.1, 2: 0.2, 3: 0.3})
    result = HTMPredictionModel._removeUnlikelyPredictions(
        {1: 0.1, 2: 0.2, 3: 0.3, 4: 0.4, 5: 0.005}, 0.01, 3)
    self.assertDictEqual(result, {2: 0.2, 3: 0.3, 4: 0.4})
    result = HTMPredictionModel._removeUnlikelyPredictions(
        {1: 0.1, 2: 0.2, 3: 0.3, 4: 0.004, 5: 0.005}, 0.01, 3)
    self.assertDictEqual(result, {1: 0.1, 2: 0.2, 3: 0.3})


  def testTemporalAnomalyModelFactory(self):
    """ Simple test to assert that ModelFactory.create() with a given specific
    Temporal Anomaly configuration will return a model that can return
    inferences
    """
    modelConfig = (
      {u'aggregationInfo': {u'days': 0,
                            u'fields': [],
                            u'hours': 0,
                            u'microseconds': 0,
                            u'milliseconds': 0,
                            u'minutes': 0,
                            u'months': 0,
                            u'seconds': 0,
                            u'weeks': 0,
                            u'years': 0},
       u'model': u'HTMPrediction',
       u'modelParams': {u'anomalyParams': {u'anomalyCacheRecords': None,
                                           u'autoDetectThreshold': None,
                                           u'autoDetectWaitRecords': 5030},
                        u'clEnable': False,
                        u'clParams': {u'alpha': 0.035828933612158,
                                      u'verbosity': 0,
                                      u'regionName': u'SDRClassifierRegion',
                                      u'steps': u'1'},
                        u'inferenceType': u'TemporalAnomaly',
                        u'sensorParams': {u'encoders': {u'c0_dayOfWeek': None,
                                                        u'c0_timeOfDay': {u'fieldname': u'c0',
                                                                          u'name': u'c0',
                                                                          u'timeOfDay': [21,
                                                                                         9.49122334747737],
                                                                          u'type': u'DateEncoder'},
                                                        u'c0_weekend': None,
                                                        u'c1': {u'fieldname': u'c1',
                                                                u'name': u'c1',
                                                                u'resolution': 0.8771929824561403,
                                                                u'seed': 42,
                                                                u'type': u'RandomDistributedScalarEncoder'}},
                                          u'sensorAutoReset': None,
                                          u'verbosity': 0},
                        u'spEnable': True,
                        u'spParams': {u'potentialPct': 0.8,
                                      u'columnCount': 2048,
                                      u'globalInhibition': 1,
                                      u'inputWidth': 0,
                                      u'boostStrength': 0.0,
                                      u'numActiveColumnsPerInhArea': 40,
                                      u'seed': 1956,
                                      u'spVerbosity': 0,
                                      u'spatialImp': u'cpp',
                                      u'synPermActiveInc': 0.0015,
                                      u'synPermConnected': 0.1,
                                      u'synPermInactiveDec': 0.0005,
                                      },
                        u'tmEnable': True,
                        u'tmParams': {u'activationThreshold': 13,
                                      u'cellsPerColumn': 32,
                                      u'columnCount': 2048,
                                      u'globalDecay': 0.0,
                                      u'initialPerm': 0.21,
                                      u'inputWidth': 2048,
                                      u'maxAge': 0,
                                      u'maxSegmentsPerCell': 128,
                                      u'maxSynapsesPerSegment': 32,
                                      u'minThreshold': 10,
                                      u'newSynapseCount': 20,
                                      u'outputType': u'normal',
                                      u'pamLength': 3,
                                      u'permanenceDec': 0.1,
                                      u'permanenceInc': 0.1,
                                      u'seed': 1960,
                                      u'temporalImp': u'cpp',
                                      u'verbosity': 0},
                        u'trainSPNetOnlyIfRequested': False},
       u'predictAheadTime': None,
       u'version': 1}
    )

    inferenceArgs = {u'inputPredictedField': u'auto',
                     u'predictedField': u'c1',
                     u'predictionSteps': [1]}

    data = [
      {'_category': [None],
       '_reset': 0,
       '_sequenceId': 0,
       '_timestamp': datetime.datetime(2013, 12, 5, 0, 0),
       '_timestampRecordIdx': None,
       u'c0': datetime.datetime(2013, 12, 5, 0, 0),
       u'c1': 5.0},
      {'_category': [None],
       '_reset': 0,
       '_sequenceId': 0,
       '_timestamp': datetime.datetime(2013, 12, 6, 0, 0),
       '_timestampRecordIdx': None,
       u'c0': datetime.datetime(2013, 12, 6, 0, 0),
       u'c1': 6.0},
      {'_category': [None],
       '_reset': 0,
       '_sequenceId': 0,
       '_timestamp': datetime.datetime(2013, 12, 7, 0, 0),
       '_timestampRecordIdx': None,
       u'c0': datetime.datetime(2013, 12, 7, 0, 0),
       u'c1': 7.0}
    ]

    model = ModelFactory.create(modelConfig=modelConfig)
    model.enableLearning()
    model.enableInference(inferenceArgs)

    for row in data:
      result = model.run(row)
      self.assertIsInstance(result, ModelResult)


if __name__ == "__main__":
  unittest.main()
