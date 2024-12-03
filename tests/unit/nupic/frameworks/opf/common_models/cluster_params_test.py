# Copyright 2015 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""Unit tests for model selection via cluster params."""

import unittest
from nupic.support.unittesthelpers.testcasebase import TestCaseBase
from nupic.frameworks.opf.model_factory import ModelFactory
from nupic.frameworks.opf.htm_prediction_model import HTMPredictionModel
from nupic.frameworks.opf.common_models.cluster_params import (
  getScalarMetricWithTimeOfDayAnomalyParams)



class ClusterParamsTest(TestCaseBase):


  def testModelParams(self):
    """
    Test that clusterParams loads returns a valid dict that can be instantiated
    as a HTMPredictionModel.
    """
    params = getScalarMetricWithTimeOfDayAnomalyParams([0],
                                                       minVal=23.42,
                                                       maxVal=23.420001)

    encodersDict= (
      params['modelConfig']['modelParams']['sensorParams']['encoders'])

    model = ModelFactory.create(modelConfig=params['modelConfig'])
    self.assertIsInstance(model,
                          HTMPredictionModel,
                          "JSON returned cannot be used to create a model")

    # Ensure we have a time of day field
    self.assertIsNotNone(encodersDict['c0_timeOfDay'])

    # Ensure resolution doesn't get too low
    if encodersDict['c1']['type'] == 'RandomDistributedScalarEncoder':
      self.assertGreaterEqual(encodersDict['c1']['resolution'], 0.001,
                              "Resolution is too low")

    # Ensure tm_cpp returns correct json file
    params = getScalarMetricWithTimeOfDayAnomalyParams([0], tmImplementation="tm_cpp")
    self.assertEqual(params['modelConfig']['modelParams']['tmParams']['temporalImp'], "tm_cpp",
                     "Incorrect json for tm_cpp tmImplementation")

    # Ensure incorrect tmImplementation throws exception
    with self.assertRaises(ValueError):
        getScalarMetricWithTimeOfDayAnomalyParams([0], tmImplementation="")

if __name__ == '__main__':
  unittest.main()

