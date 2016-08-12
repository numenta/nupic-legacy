#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014-2016, Numenta, Inc.  Unless you have an agreement
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
import tempfile
import unittest

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.proto import ConnectionsProto_capnp

from nupic.research.connections import Connections, Segment


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
    activeSegs, _ = connections.computeActivity([1, 2], .5, 2, .1, 1)
    self.assertEqual(1, len(activeSegs))
    self.assertEqual(segment1, activeSegs[0].segment)

    segment3 = connections.createSegment(42)
    self.assertEqual(segment2.idx, segment3.idx)


  def testSynapseReuse(self):
    """ Creates a synapse over the synapses per segment limit, and verifies
        that the lowest permanence synapse is removed to make room for the new
        synapse.
    """
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
    """ Creates a segment, destroys it, and makes sure it got destroyed along
        with all of its synapses.
    """
    connections = Connections(1024)

    connections.createSegment(10)
    segment2 = connections.createSegment(20)
    connections.createSegment(30)
    connections.createSegment(40)

    connections.createSynapse(segment2, 80, 0.85)
    connections.createSynapse(segment2, 81, 0.85)
    connections.createSynapse(segment2, 82, 0.15)

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
    """ Creates a segment, creates a number of synapses on it, destroys a
        synapse, and makes sure it got destroyed.
    """
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


  def testPathsNotInvalidatedByOtherDestroys(self):
    """ Creates segments and synapses, then destroys segments and synapses on
        either side of them and verifies that existing Segment and Synapse
        instances still point to the same segment / synapse as before.
    """
    connections = Connections(1024)
    segment1 = connections.createSegment(11)
    connections.createSegment(12)
    segment3 = connections.createSegment(13)
    connections.createSegment(14)
    segment5 = connections.createSegment(15)

    synapse1 = connections.createSynapse(segment3, 201, .85)
    synapse2 = connections.createSynapse(segment3, 202, .85)
    synapse3 = connections.createSynapse(segment3, 203, .85)
    synapse4 = connections.createSynapse(segment3, 204, .85)
    synapse5 = connections.createSynapse(segment3, 205, .85)

    self.assertEqual(203, connections.dataForSynapse(synapse3).presynapticCell)
    connections.destroySynapse(synapse1)
    self.assertEqual(203, connections.dataForSynapse(synapse3).presynapticCell)
    connections.destroySynapse(synapse5)
    self.assertEqual(203, connections.dataForSynapse(synapse3).presynapticCell)

    connections.destroySegment(segment1)
    self.assertEqual(connections.synapsesForSegment(segment3),
                     [synapse2, synapse3, synapse4])
    connections.destroySegment(segment5)
    self.assertEqual(connections.synapsesForSegment(segment3),
                     [synapse2, synapse3, synapse4])
    self.assertEqual(203, connections.dataForSynapse(synapse3).presynapticCell)


  def testDestroySegmentWithDestroyedSynapses(self):
    """ Destroy a segment that has a destroyed synapse and a non-destroyed
        synapse. Make sure nothing gets double-destroyed.
    """
    connections = Connections(1024)

    segment1 = connections.createSegment(11)
    segment2 = connections.createSegment(12)

    connections.createSynapse(segment1, 101, .85)
    synapse2a = connections.createSynapse(segment2, 201, .85)
    connections.createSynapse(segment2, 202, .85)

    self.assertEqual(3, connections.numSynapses())

    connections.destroySynapse(synapse2a)

    self.assertEqual(2, connections.numSegments())
    self.assertEqual(2, connections.numSynapses())

    connections.destroySegment(segment2)

    self.assertEqual(1, connections.numSegments())
    self.assertEqual(1, connections.numSynapses())


  def testReuseSegmentWithDestroyedSynapses(self):
    """ Destroy a segment that has a destroyed synapse and a non-destroyed
        synapse. Create a new segment in the same place. Make sure its synapse
        count is correct.
    """
    connections = Connections(1024)

    segment = connections.createSegment(11)

    synapse1 = connections.createSynapse(segment, 201, .85)
    connections.createSynapse(segment, 202, .85)

    connections.destroySynapse(synapse1)

    self.assertEqual(1, connections.numSynapses(segment))

    connections.destroySegment(segment)

    reincarnated = connections.createSegment(11)

    self.assertEqual(0, connections.numSynapses(reincarnated))
    self.assertEqual(0, len(connections.synapsesForSegment(reincarnated)))


  def testDestroySegmentsThenReachLimit(self):
    """ Destroy some segments then verify that the maxSegmentsPerCell is still
        correctly applied.
    """
    connections = Connections(1024, 2, 2)

    segment1 = connections.createSegment(11)
    segment2 = connections.createSegment(11)

    self.assertEqual(2, connections.numSegments())
    connections.destroySegment(segment1)
    connections.destroySegment(segment2)
    self.assertEqual(0, connections.numSegments())

    connections.createSegment(11)
    self.assertEqual(1, connections.numSegments())
    connections.createSegment(11)
    self.assertEqual(2, connections.numSegments())
    segment3 = connections.createSegment(11)
    self.assertLess(segment3.idx, 2)
    self.assertEqual(2, connections.numSegments())


  def testDestroySynapsesThenReachLimit(self):
    """ Destroy some synapses then verify that the maxSynapsesPerSegment is
        still correctly applied.
    """
    connections = Connections(1024, 2, 2)

    segment = connections.createSegment(10)

    synapse1 = connections.createSynapse(segment, 201, .85)
    synapse2 = connections.createSynapse(segment, 202, .85)

    self.assertEqual(2, connections.numSynapses())
    connections.destroySynapse(synapse1)
    connections.destroySynapse(synapse2)
    self.assertEqual(0, connections.numSynapses())

    connections.createSynapse(segment, 201, .85)
    self.assertEqual(1, connections.numSynapses())
    connections.createSynapse(segment, 202, .90)
    self.assertEqual(2, connections.numSynapses())
    synapse3 = connections.createSynapse(segment, 203, .8)
    self.assertLess(synapse3.idx, 2)
    self.assertEqual(2, connections.numSynapses())


  def testReachSegmentLimitMultipleTimes(self):
    """ Hit the maxSynapsesPerSegment threshold multiple times. Make sure it
        works more than once.
    """
    connections = Connections(1024, 2, 2)

    segment = connections.createSegment(10)
    connections.createSynapse(segment, 201, .85)
    self.assertEqual(1, connections.numSynapses())
    connections.createSynapse(segment, 202, .9)
    self.assertEqual(2, connections.numSynapses())
    connections.createSynapse(segment, 203, .8)
    self.assertEqual(2, connections.numSynapses())
    synapse = connections.createSynapse(segment, 204, .8)
    self.assertLess(synapse.idx, 2)
    self.assertEqual(2, connections.numSynapses())


  def testUpdateSynapsePermanence(self):
    """ Creates a synapse and updates its permanence, and makes sure that its
        data was correctly updated.
    """
    connections = Connections(1024)
    segment = connections.createSegment(10)
    synapse = connections.createSynapse(segment, 50, .34)

    connections.updateSynapsePermanence(synapse, .21)

    synapseData = connections.dataForSynapse(synapse)
    self.assertAlmostEqual(synapseData.permanence, .21)


  def testComputeActivity(self):
    """ Creates a sample set of connections, and makes sure that computing the
        activity for a collection of cells with no activity returns the right
        activity data.
    """
    connections = Connections(1024)

    # Cell with 1 segment.
    # Segment with:
    # - 1 connected synapse: active
    # - 2 matching synapses
    segment1a = connections.createSegment(10)
    connections.createSynapse(segment1a, 150, .85)
    connections.createSynapse(segment1a, 151, .15)

    # Cell with 2 segment.
    # Segment with:
    # - 2 connected synapse: 2 active
    # - 3 matching synapses: 3 active
    segment2a = connections.createSegment(20)
    connections.createSynapse(segment2a, 80, .85)
    connections.createSynapse(segment2a, 81, .85)
    synapse = connections.createSynapse(segment2a, 82, .85)
    connections.updateSynapsePermanence(synapse, .15)


    # Segment with:
    # - 2 connected synapses: 1 active, 1 inactive
    # - 3 matching synapses: 2 active, 1 inactive
    # - 1 non-matching synapse: 1 active
    segment2b = connections.createSegment(20)
    connections.createSynapse(segment2b, 50, .85)
    connections.createSynapse(segment2b, 51, .85)
    connections.createSynapse(segment2b, 52, .15)
    connections.createSynapse(segment2b, 53, .05)

    # Cell with one segment.
    # Segment with:
    # - 1 non-matching synapse: 1 active
    segment3a = connections.createSegment(30)
    connections.createSynapse(segment3a, 53, .05)

    inputVec = [50, 52, 53, 80, 81, 82, 150, 151]
    active, matching = connections.computeActivity(inputVec, .5, 2, .1, 1)

    self.assertEqual(1, len(active))
    self.assertEqual(segment2a, active[0].segment)
    self.assertEqual(2, active[0].overlap)

    self.assertEqual(3, len(matching))
    self.assertEqual(segment1a, matching[0].segment)
    self.assertEqual(2, matching[0].overlap)
    self.assertEqual(segment2a, matching[1].segment)
    self.assertEqual(3, matching[1].overlap)
    self.assertEqual(segment2b, matching[2].segment)
    self.assertEqual(2, matching[2].overlap)


  @unittest.skipUnless(
    capnp, "pycapnp is not installed, skipping serialization test.")
  def testWriteRead(self):
    c1 = Connections(1024)

    # Add data before serializing
    s1 = c1.createSegment(0)
    c1.createSynapse(s1, 254, 0.1173)

    s2 = c1.createSegment(100)
    c1.createSynapse(s2, 20, 0.3)

    c1.createSynapse(s1, 40, 0.3)

    s3 = c1.createSegment(0)
    c1.createSynapse(s3, 0, 0.5)
    c1.createSynapse(s3, 1, 0.5)

    s4 = c1.createSegment(10)
    c1.createSynapse(s4, 0, 0.5)
    c1.createSynapse(s4, 1, 0.5)
    c1.destroySegment(s4)

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
