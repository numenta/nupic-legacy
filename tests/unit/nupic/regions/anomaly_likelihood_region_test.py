#!/usr/bin/env python
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

import tempfile
import unittest
import random

import numpy

from nupic.regions.AnomalyLikelihoodRegion import AnomalyLikelihoodRegion

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.regions.AnomalyRegion_capnp import AnomalyRegionProto



class AnomalyLikelihoodRegionTest(unittest.TestCase):
  """Tests for anomaly likelihood region"""


  @unittest.skipUnless(
      capnp, "pycapnp is not installed, skipping serialization test.")
  def testWriteRead(self):
    predictedColumns = [[0, 1 ,1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
                        [0, 1 ,1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
                        [0, 1 ,1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
                        [0, 1 ,1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
                        [0, 1 ,1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
                        [0, 1 ,1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
                        [0, 1 ,1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
                        [0, 1 ,1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
                        [0, 1 ,1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
                        [0, 1 ,1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]]
    activeColumns = [[0, 1 ,1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
                     [0, 1 ,1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
                     [0, 1 ,0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0],
                     [0, 0 ,0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0],
                     [1, 0 ,0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
                     [0, 0 ,0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
                     [0, 0 ,0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
                     [0, 1 ,1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
                     [0, 1 ,1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
                     [0, 1 ,1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0]]
    anomalyExpected = (1.0, 0.25, 1.0/3.0, 2.0/3.0, 1.0, 2.0/3.0, 1.0,
                       0.0, 0.25, 0.25)

    anomalyLikelihoodRegion1 = AnomalyLikelihoodRegion()
    inputs = AnomalyLikelihoodRegion.getSpec()['inputs']
    outputs = AnomalyLikelihoodRegion.getSpec()['outputs']
    for i in xrange(0, 6):
      inputs['rawAnomalyScore'] = random.random()
      inputs['value'] = random.random()
      anomalyLikelihoodRegion1.compute(inputs, outputs)
      score1 = outputs['anomalyLikelihood'][0]
      print score1
    # proto1 = AnomalyRegionProto.new_message()
    # anomalyRegion1.write(proto1)

    # # Write the proto to a temp file and read it back into a new proto
    # with tempfile.TemporaryFile() as f:
    #   proto1.write(f)
    #   f.seek(0)
    #   proto2 = AnomalyRegionProto.read(f)

    # # Load the deserialized proto
    # anomalyRegion2 = AnomalyRegion.read(proto2)

    # self.assertEqual(anomalyRegion1, anomalyRegion2)

    for i in xrange(6, 500):
      inputs['rawAnomalyScore'] = random.random()
      inputs['value'] = random.random()
      anomalyLikelihoodRegion1.compute(inputs, outputs)
      score1 = outputs['anomalyLikelihood'][0]
      # self.assertAlmostEqual(
      #     score1, anomalyExpected[i], places=5,
      #     msg="Anomaly score of %f doesn't match expected of %f" % (
      #         score1, anomalyExpected[i]))
      # self.assertAlmostEqual(
      #     score2, anomalyExpected[i], places=5,
      #     msg="Anomaly score of %f doesn't match expected of %f" % (
      #         score2, anomalyExpected[i]))
      print score1
    self.assertNotEqual(score1, .5)


if __name__ == "__main__":
  unittest.main()
