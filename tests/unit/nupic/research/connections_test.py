#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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
"""
TODO: Mock out all function calls.
TODO: Move all duplicate connections logic into shared function.
"""

import tempfile
import unittest

from nupic.research.connections import Connections, Segment

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.proto import ConnectionsProto_capnp

def setupSampleConnections(connections):

  # Cell with 1 segment.
  # Segment with:
  # - 1 connected synapse: active
  # - 2 matching synapses
  segment1_1 = connections.createSegment(10)
  connections.createSynapse(segment1_1, 150, .85)
  connections.createSynapse(segment1_1, 151, .15)

  # Cell with 2 segment.
  # Segment with:
  # - 2 connected synapse: 2 active
  # - 3 matching synapses: 3 active
  segment2_1 = connections.createSegment(20)
  connections.createSynapse(segment2_1, 80, .85)
  connections.createSynapse(segment2_1, 81, .85)
  synapse = connections.createSynapse(segment2_1, 82, .85)
  connections.updateSynapsePermanence(synapse, .15)


  # Segment with:
  # - 2 connected synapses: 1 active, 1 inactive
  # - 3 matching synapses: 2 active, 1 inactive
  # - 1 non-matching synapse: 1 active
  segment2_2 = connections.createSegment(20)
  connections.createSynapse(segment2_2, 50, .85)
  connections.createSynapse(segment2_2, 51, .85)
  connections.createSynapse(segment2_2, 52, .85)
  connections.createSynapse(segment2_2, 53, .85)

  segment3_1 = connections.createSegment(30)
  connections.createSynapse(segment3_1, 53, .05)


def computeSampleActivity(connections):
    inputVec = [50, 52, 53, 80, 81, 82, 150, 151]
    connections.computeActivity(input, .5, 2, .1, 1)

class ConnectionsTest(unittest.TestCase):

  def testCreateSegment(self):
    connections = Connections(1024)

    segment1 = connections.createSegment(10)
    self.assertEqual(segment1.idx, 0)
    self.assertEqual(segment1.cell, 10)

    segment2 = connections.createSegment(10)
    self.assertEqual(segment2.idx, 1)
    self.assertEqual(segment2.cell, 10)

    self.assertEqual(connections.segmentsForCell(10), [segment1, segment2])
  

  def testCreateSegmentReuse(self):
    connections = Connections(1024, 2)

    segment1 = connections.createSegment(42)
    connections.createSynapse(segment1, 1, .5)
    connections.createSynapse(segment1, 2, .5)

    connections.computeActivity([], .5, 2, .1, 1)
    connections.computeActivity([], .5, 2, .1, 1)
    connections.computeActivity([], .5, 2, .1, 1)

    segment2 = connections.createSegment(42)
    activeSegs, matchingSegs = connections.computeActivity([1, 2], .5, 2, .1, 1)
    self.assertEqual(1, len(activeSegs))
    self.assertEqual(segment1, activeSegs[0].segment)

    segment3 = connections.createSegment(42)
    self.assertEqual(segment2.idx, segment3.idx)

  
  def testSynapseReusue(self):
    ''' Creates a synapse over the synapses per segment limit, and verifies
        that the lowest permanence synapse is removed to make room for the new
        synapse.
    '''
    connections = Connections(1024, 1024, 2)
    segment = connections.createSegment(10)

    synapse1 = connections.createSynapse(segment, 50, .34)
    synapse2 = connections.createSynapse(segment, 51, .34)

    synapses = connections.synapsesForSegment(segment)
    self.assertEqual(synapses, [synapse1, synapse2])
    
    #Add an additional synapse to force it over the limit of num synapses
    #per segment.
    synapse3 = connections.createSynapse(segment, 52, .52)
    self.assertEqual(0, synapse3.idx)
    
    #ensure lower permanence synapse was removed
    synapses = connections.synapsesForSegment(segment)
    self.assertEqual(synapses, [synapse3, synapse2])

  
  def testDestroySegment(self):
    ''' Creates a segment, destroys it, and makes sure it got destroyed along with
        all of its synapses.
    '''
    connections = Connections(1024)

    segment1 = connections.createSegment(10)
    segment2 = connections.createSegment(20)
    segment3 = connections.createSegment(30)
    segment4 = connections.createSegment(40)

    syn1 = connections.createSynapse(segment2, 80, 0.85)
    syn2 = connections.createSynapse(segment2, 81, 0.85)
    syn3 = connections.createSynapse(segment2, 82, 0.15)
    
    self.assertEqual(4, connections.numSegments())
    self.assertEqual(3, connections.numSynapses())

    connections.destroySegment(segment2)

    self.assertEqual(3, connections.numSegments())
    self.assertEqual(0, connections.numSynapses())
    
    args = [segment2]
    self.assertRaises(ValueError, connections.synapsesForSegment, *args)

    active, matching = connections.computeActivity([80, 81, 82], .5, 2, .1, 1)
    self.assertEqual(len(active), 0)
    self.assertEqual(len(matching), 0)
    

  def testDestroySynapse(self):
    ''' Creates a segment, creates a number of synapses on it, destroys a synapse,
        and makes sure it got destroyed.
    '''
    connections = Connections(1024)

    segment = connections.createSegment(20)
    synapse1 = connections.createSynapse(segment, 80, .85)
    synapse2 = connections.createSynapse(segment, 81, .85)
    synapse3 = connections.createSynapse(segment, 82, .15)

    self.assertEqual(3, connections.numSynapses())

    connections.destroySynapse(synapse2)

    self.assertEqual(2, connections.numSynapses())
    self.assertEqual(connections.synapsesForSegment(segment), [synapse1,
                                                               synapse3])
    active, matching = connections.computeActivity([80, 81, 82], .5, 2, 0.0, 1)
    self.assertEqual(0, len(active))
    self.assertEqual(1, len(matching))
    self.assertEqual(2, matching[0].overlap)


  @unittest.skipUnless(
      capnp, "pycapnp is not installed, skipping serialization test.")
  def testWriteRead(self):
    c1 = Connections(1024)

    # Add data before serializing
    c1.createSegment(0)
    c1.createSynapse(0, 254, 0.1173)

    c1.createSegment(100)
    c1.createSynapse(1, 20, 0.3)

    c1.createSynapse(0, 40, 0.3)

    c1.createSegment(0)
    c1.createSynapse(2, 0, 0.5)
    c1.createSynapse(2, 1, 0.5)

    c1.createSegment(10)
    c1.createSynapse(3, 0, 0.5)
    c1.createSynapse(3, 1, 0.5)
    c1.destroySegment(3)

    proto1 = ConnectionsProto_capnp.ConnectionsProto.new_message()
    c1.write(proto1)

    # Write the proto to a temp file and read it back into a new proto
    with tempfile.TemporaryFile() as f:
      proto1.write(f)
      f.seek(0)
      proto2 = ConnectionsProto_capnp.ConnectionsProto.read(f)

    # Load the deserialized proto
    c2 = Connections.read(proto2)

    # Check that the two connections objects are functionally equal
    self.assertEqual(c1, c2)


if __name__ == '__main__':
  unittest.main()
