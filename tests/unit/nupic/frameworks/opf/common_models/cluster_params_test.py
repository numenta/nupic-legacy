# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
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

"""Unit tests for model selection via cluster params."""

import unittest
from nupic.support.unittesthelpers.testcasebase import TestCaseBase
from nupic.frameworks.opf.modelfactory import ModelFactory
from nupic.frameworks.opf.clamodel import CLAModel
from nupic.frameworks.opf.common_models.cluster_params import (
  getScalarMetricWithTimeOfDayAnomalyParams)



class ClusterParamsTest(TestCaseBase):


  def testModelParams(self):
    """
    Test that clusterParams loads returns a valid dict that can be instantiated
    as a CLAModel.
    """
    params = getScalarMetricWithTimeOfDayAnomalyParams([0],
                                                       minVal=23.42,
                                                       maxVal=23.420001)

    encodersDict= (
      params['modelConfig']['modelParams']['sensorParams']['encoders'])

    model = ModelFactory.create(modelConfig=params['modelConfig'])
    self.assertIsInstance(model,
                          CLAModel,
                          "JSON returned cannot be used to create a model")

    # Ensure we have a time of day field
    self.assertIsNotNone(encodersDict['c0_timeOfDay'])

    # Ensure resolution doesn't get too low
    if encodersDict['c1']['type'] == 'RandomDistributedScalarEncoder':
      self.assertGreaterEqual(encodersDict['c1']['resolution'], 0.001,
                              "Resolution is too low")

    # Ensure tm_cpp returns correct json file
    params = getScalarMetricWithTimeOfDayAnomalyParams([0], tmImplementation="tm_cpp")
    self.assertEqual(params['modelConfig']['modelParams']['tpParams']['temporalImp'], "tm_cpp",
                     "Incorrect json for tm_cpp tmImplementation")

    # Ensure incorrect tmImplementation throws exception
    with self.assertRaises(ValueError):
        getScalarMetricWithTimeOfDayAnomalyParams([0], tmImplementation="")

if __name__ == '__main__':
  unittest.main()

