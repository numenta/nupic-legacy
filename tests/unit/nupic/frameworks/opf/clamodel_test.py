#!/usr/bin/env python
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

"""Unit tests for the clamodel module."""

import datetime
import unittest2 as unittest

from nupic.frameworks.opf.clamodel import CLAModel
from nupic.frameworks.opf.modelfactory import ModelFactory
from nupic.frameworks.opf.opfutils import ModelResult



class CLAModelTest(unittest.TestCase):
  """CLAModel unit tests."""


  def testRemoveUnlikelyPredictionsEmpty(self):
    result = CLAModel._removeUnlikelyPredictions({}, 0.01, 3)
    self.assertDictEqual(result, {})


  def testRemoveUnlikelyPredictionsSingleValues(self):
    result = CLAModel._removeUnlikelyPredictions({1: 0.1}, 0.01, 3)
    self.assertDictEqual(result, {1: 0.1})
    result = CLAModel._removeUnlikelyPredictions({1: 0.001}, 0.01, 3)
    self.assertDictEqual(result, {1: 0.001})


  def testRemoveUnlikelyPredictionsLikelihoodThresholds(self):
    result = CLAModel._removeUnlikelyPredictions({1: 0.1, 2: 0.001}, 0.01, 3)
    self.assertDictEqual(result, {1: 0.1})
    result = CLAModel._removeUnlikelyPredictions({1: 0.001, 2: 0.002}, 0.01, 3)
    self.assertDictEqual(result, {2: 0.002})
    result = CLAModel._removeUnlikelyPredictions({1: 0.002, 2: 0.001}, 0.01, 3)
    self.assertDictEqual(result, {1: 0.002})


  def testRemoveUnlikelyPredictionsMaxPredictions(self):
    result = CLAModel._removeUnlikelyPredictions({1: 0.1, 2: 0.2, 3: 0.3},
                                                 0.01, 3)
    self.assertDictEqual(result, {1: 0.1, 2: 0.2, 3: 0.3})
    result = CLAModel._removeUnlikelyPredictions(
        {1: 0.1, 2: 0.2, 3: 0.3, 4: 0.4}, 0.01, 3)
    self.assertDictEqual(result, {2: 0.2, 3: 0.3, 4: 0.4})


  def testRemoveUnlikelyPredictionsComplex(self):
    result = CLAModel._removeUnlikelyPredictions(
        {1: 0.1, 2: 0.2, 3: 0.3, 4: 0.004}, 0.01, 3)
    self.assertDictEqual(result, {1: 0.1, 2: 0.2, 3: 0.3})
    result = CLAModel._removeUnlikelyPredictions(
        {1: 0.1, 2: 0.2, 3: 0.3, 4: 0.4, 5: 0.005}, 0.01, 3)
    self.assertDictEqual(result, {2: 0.2, 3: 0.3, 4: 0.4})
    result = CLAModel._removeUnlikelyPredictions(
        {1: 0.1, 2: 0.2, 3: 0.3, 4: 0.004, 5: 0.005}, 0.01, 3)
    self.assertDictEqual(result, {1: 0.1, 2: 0.2, 3: 0.3})


  def testTemporalAnomalyModelFactory(self):
    """ Simple test to assert that ModelFactory.create() with a given specific
    Temporal Anomaly configuration will return a model that can return
    inferences
    """
    modelConfig = (
      {'aggregationInfo': {'days': 0,
                            'fields': [],
                            'hours': 0,
                            'microseconds': 0,
                            'milliseconds': 0,
                            'minutes': 0,
                            'months': 0,
                            'seconds': 0,
                            'weeks': 0,
                            'years': 0},
       'model': 'CLA',
       'modelParams': {'anomalyParams': {'anomalyCacheRecords': None,
                                           'autoDetectThreshold': None,
                                           'autoDetectWaitRecords': 5030},
                        'clEnable': False,
                        'clParams': {'alpha': 0.035828933612158,
                                      'clVerbosity': 0,
                                      'regionName': 'CLAClassifierRegion',
                                      'steps': '1'},
                        'inferenceType': 'TemporalAnomaly',
                        'sensorParams': {'encoders': {'c0_dayOfWeek': None,
                                                        'c0_timeOfDay': {'fieldname': 'c0',
                                                                          'name': 'c0',
                                                                          'timeOfDay': [21,
                                                                                         9.49122334747737],
                                                                          'type': 'DateEncoder'},
                                                        'c0_weekend': None,
                                                        'c1': {'fieldname': 'c1',
                                                                'name': 'c1',
                                                                'resolution': 0.8771929824561403,
                                                                'seed': 42,
                                                                'type': 'RandomDistributedScalarEncoder'}},
                                          'sensorAutoReset': None,
                                          'verbosity': 0},
                        'spEnable': True,
                        'spParams': {'potentialPct': 0.8,
                                      'columnCount': 2048,
                                      'globalInhibition': 1,
                                      'inputWidth': 0,
                                      'maxBoost': 1.0,
                                      'numActiveColumnsPerInhArea': 40,
                                      'seed': 1956,
                                      'spVerbosity': 0,
                                      'spatialImp': 'cpp',
                                      'synPermActiveInc': 0.0015,
                                      'synPermConnected': 0.1,
                                      'synPermInactiveDec': 0.0005,
                                      },
                        'tpEnable': True,
                        'tpParams': {'activationThreshold': 13,
                                      'cellsPerColumn': 32,
                                      'columnCount': 2048,
                                      'globalDecay': 0.0,
                                      'initialPerm': 0.21,
                                      'inputWidth': 2048,
                                      'maxAge': 0,
                                      'maxSegmentsPerCell': 128,
                                      'maxSynapsesPerSegment': 32,
                                      'minThreshold': 10,
                                      'newSynapseCount': 20,
                                      'outputType': 'normal',
                                      'pamLength': 3,
                                      'permanenceDec': 0.1,
                                      'permanenceInc': 0.1,
                                      'seed': 1960,
                                      'temporalImp': 'cpp',
                                      'verbosity': 0},
                        'trainSPNetOnlyIfRequested': False},
       'predictAheadTime': None,
       'version': 1}
    )

    inferenceArgs = {'inputPredictedField': 'auto',
                     'predictedField': 'c1',
                     'predictionSteps': [1]}

    data = [
      {'_category': [None],
       '_reset': 0,
       '_sequenceId': 0,
       '_timestamp': datetime.datetime(2013, 12, 5, 0, 0),
       '_timestampRecordIdx': None,
       'c0': datetime.datetime(2013, 12, 5, 0, 0),
       'c1': 5.0},
      {'_category': [None],
       '_reset': 0,
       '_sequenceId': 0,
       '_timestamp': datetime.datetime(2013, 12, 6, 0, 0),
       '_timestampRecordIdx': None,
       'c0': datetime.datetime(2013, 12, 6, 0, 0),
       'c1': 6.0},
      {'_category': [None],
       '_reset': 0,
       '_sequenceId': 0,
       '_timestamp': datetime.datetime(2013, 12, 7, 0, 0),
       '_timestampRecordIdx': None,
       'c0': datetime.datetime(2013, 12, 7, 0, 0),
       'c1': 7.0}
    ]

    model = ModelFactory.create(modelConfig=modelConfig)
    model.enableLearning()
    model.enableInference(inferenceArgs)

    for row in data:
      result = model.run(row)
      self.assertIsInstance(result, ModelResult)


if __name__ == "__main__":
  unittest.main()
