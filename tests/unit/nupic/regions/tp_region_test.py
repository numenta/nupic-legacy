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
from pkg_resources import resource_filename

from nupic.regions.TPRegion import TPRegion
from nupic.regions.TPRegion_capnp import TemporalMemoryV1RegionProto



class TPRegionTest(unittest.TestCase):
  """Tests for TP region"""


  def testWriteRead(self):
    temporalParams = {
      'initialPerm': 0.21,
      'connectedPerm': 0.5,
      'minThreshold': 11,
      'newSynapseCount': 20,
      'permanenceInc': 0.1,
      'permanenceDec': 0.1,
      'permanenceMax': 1.0,
      'globalDecay': 0.0,
      'activationThreshold': 14,
      'doPooling': False,
      'segUpdateValidDuration': 5,
      'burnIn': 2,
      'collectStats': True,
      'seed': 1960,
      'verbosity': 0,
      'checkSynapseConsistency': False,
      'pamLength': 3,
      'maxInfBacktrack': 10,
      'maxLrnBacktrack': 5,
      'maxAge': 0,
      'maxSeqLength': 32,
      'maxSegmentsPerCell': 128,
      'maxSynapsesPerSegment': 32,
      'outputType': 'normal'}
    tpRegion1 = TPRegion(columnCount=2048, inputWidth=0, cellsPerColumn=32,
                         temporalImp='py', **temporalParams)
    tpRegion1.learningMode = True
    tpRegion1.inferenceMode = False

    with open(resource_filename(__name__, '../research/data/tp_input.csv'), 'r') as fin:
      records = []
      for bottomUpInStr in fin:
        bottomUpIn = numpy.array(eval('[' + bottomUpInStr.strip() + ']'),
                                 dtype='int32')
        records.append(bottomUpIn)

    i = 1
    numCells = tpRegion1.columnCount * tpRegion1.cellsPerColumn
    inputs = dict()
    outputs = dict()
    tpRegion1.initialize(None, None)
    for r in records[:150]:
      print i
      i += 1

      inputs['bottomUpIn'] = r
      outputs['bottomUpOut'] = numpy.zeros(numCells)
      tpRegion1.compute(inputs, outputs)

    proto1 = TemporalMemoryV1RegionProto.new_message()
    tpRegion1.write(proto1)

    # Write the proto to a temp file and read it back into a new proto
    with tempfile.TemporaryFile() as f:
      proto1.write(f)
      f.seek(0)
      proto2 = TemporalMemoryV1RegionProto.read(f)

    # Load the deserialized proto
    tpRegion2 = TPRegion.read(proto2)

    self.assertEqual(tpRegion1, tpRegion2)

    tpRegion1.learningMode = False
    tpRegion2.learningMode = False
    tpRegion1.inferenceMode = True
    tpRegion2.inferenceMode = True
    outputs1 = dict()
    outputs2 = dict()
    for r in records[151:160]:
      print i
      i += 1

      inputs['bottomUpIn'] = r
      outputs2['bottomUpOut'] = outputs1['bottomUpOut'] = numpy.zeros(numCells)
      tpRegion1.compute(inputs, outputs1)
      tpRegion2.compute(inputs, outputs2)
      self.assertEqual(outputs1, outputs2)


if __name__ == "__main__":
  unittest.main()
