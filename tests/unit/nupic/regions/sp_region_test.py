#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
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

import tempfile
import unittest2 as unittest

import capnp
import numpy

from nupic.bindings.math import GetNTAReal
from nupic.regions.SPRegion import SPRegion
from nupic.regions.SPRegion_capnp import SpatialPoolerRegionProto



class SPRegionTest(unittest.TestCase):
  """Tests for SP region"""


  def testWriteRead(self):

    inputVector = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0,
                   1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0,
                   1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                   1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0,
                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    expectedOutput = [32, 223, 295, 307, 336, 381, 385, 428, 498, 543, 624,
                      672, 687, 731, 733, 751, 760, 790, 791, 797, 860, 955,
                      1024, 1037, 1184, 1303, 1347, 1454, 1475, 1483, 1494,
                      1497, 1580, 1671, 1701, 1774, 1787, 1830, 1868, 1878]

    spatialParams = {
      'inputDimensions': [1,188],
      'columnDimensions': [2048, 1],
      'potentialRadius': 94,
      'potentialPct': 0.5,
      'globalInhibition': 1,
      'localAreaDensity': -1.0,
      'numActiveColumnsPerInhArea': 40,
      'stimulusThreshold': 0,
      'synPermInactiveDec': 0.01,
      'synPermActiveInc': 0.1,
      'synPermConnected': 0.1,
      'minPctOverlapDutyCycles': 0.001,
      'minPctActiveDutyCycles': 0.001,
      'dutyCyclePeriod': 1000,
      'maxBoost': 10.0,
      'seed': 1956,
      'spVerbosity': 0}
    spRegion1 = SPRegion(columnCount=2048, inputWidth=188,
                         spatialImp='py', **spatialParams)
    spRegion1.learningMode = True

    inputs = dict()
    inputs['bottomUpIn'] = numpy.array(inputVector).astype(dtype=GetNTAReal())

    outputs = dict()
    outputs['bottomUpOut'] = numpy.zeros(2048)
    outputs['anomalyScore'] = numpy.array([])

    # Run a record through before serializing
    spRegion1.initialize(None, None)
    spRegion1.compute(inputs, outputs)

    proto1 = SpatialPoolerRegionProto.new_message()
    spRegion1.write(proto1)

    # Write the proto to a temp file and read it back into a new proto
    with tempfile.TemporaryFile() as f:
      proto1.write(f)
      f.seek(0)
      proto2 = SpatialPoolerRegionProto.read(f)

    # Load the deserialized proto
    spRegion2 = SPRegion.read(proto2)

    self.assertEqual(spRegion1, spRegion2)

    outputs1 = dict()
    outputs2 = dict()
    outputs2['bottomUpOut'] = outputs1['bottomUpOut'] = numpy.zeros(2048)
    outputs2['anomalyScore'] = outputs1['anomalyScore'] = numpy.array([])

    # Run a iteration through after serializing
    spRegion1.learningMode = False
    spRegion2.learningMode = False
    spRegion1.compute(inputs, outputs1)
    spRegion2.compute(inputs, outputs2)

    # Get only the active column indices
    returnedOutput = [i for i, v in enumerate(outputs2['bottomUpOut']) if v != 0]
    self.assertEqual(returnedOutput, expectedOutput)


if __name__ == "__main__":
  unittest.main()
