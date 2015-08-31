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

from nupic.research.connections import Connections

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.proto import ConnectionsProto_capnp



class ConnectionsTest(unittest.TestCase):


  def setUp(self):
    self.connections = Connections(2048 * 32)


  def testCreateSegment(self):
    connections = self.connections

    self.assertEqual(connections.segmentsForCell(0), set())

    self.assertEqual(connections.createSegment(0), 0)
    self.assertEqual(connections.createSegment(0), 1)
    self.assertEqual(connections.createSegment(10), 2)

    self.assertEqual(connections.cellForSegment(0), 0)
    self.assertEqual(connections.cellForSegment(2), 10)

    self.assertEqual(connections.segmentsForCell(0), set([0, 1]))


  def testDestroySegment(self):
    connections = self.connections

    self.assertEqual(connections.createSegment(0), 0)
    self.assertEqual(connections.createSegment(0), 1)
    self.assertEqual(connections.createSegment(10), 2)

    self.assertEqual(connections.createSynapse(0, 254, 0.1173), 0)
    self.assertEqual(connections.createSynapse(0, 477, 0.3253), 1)

    connections.destroySegment(0)

    args = [0]
    self.assertRaises(IndexError, connections.dataForSynapse, *args)
    args = [1]
    self.assertRaises(IndexError, connections.dataForSynapse, *args)

    args = [0]
    self.assertRaises(IndexError, connections.synapsesForSegment, *args)

    self.assertEqual(connections.synapsesForPresynapticCell(174), {})
    self.assertEqual(connections.synapsesForPresynapticCell(254), {})

    self.assertEqual(connections.segmentsForCell(0), set([1]))


  def testCreateSegmentInvalidCell(self):
    connections = self.connections

    try:
      connections.createSegment(65535)
    except IndexError:
      self.fail("IndexError raised unexpectedly")

    args = [65536]
    self.assertRaises(IndexError, connections.createSegment, *args)

    args = [-1]
    self.assertRaises(IndexError, connections.createSegment, *args)


  def testCellForSegmentInvalidSegment(self):
    connections = self.connections

    connections.createSegment(0)

    args = [1]
    self.assertRaises(KeyError, connections.cellForSegment, *args)


  def testSegmentsForCellInvalidCell(self):
    connections = self.connections

    args = [65536]
    self.assertRaises(IndexError, connections.segmentsForCell, *args)

    args = [-1]
    self.assertRaises(IndexError, connections.segmentsForCell, *args)


  def testCreateSynapse(self):
    connections = self.connections

    connections.createSegment(0)
    self.assertEqual(connections.synapsesForSegment(0), set())

    self.assertEqual(connections.createSynapse(0, 254, 0.1173), 0)
    self.assertEqual(connections.createSynapse(0, 477, 0.3253), 1)

    self.assertEqual(connections.dataForSynapse(0), (0, 254, 0.1173))

    self.assertEqual(connections.synapsesForSegment(0), set([0, 1]))

    self.assertEqual(connections.synapsesForPresynapticCell(174), {})
    self.assertEqual(connections.synapsesForPresynapticCell(254),
                     {0: (0, 254, 0.1173)})


  def testCreateSynapseInvalidParams(self):
    connections = self.connections

    connections.createSegment(0)

    # Invalid segment
    args = [1, 48, 0.124]
    self.assertRaises(IndexError, connections.createSynapse, *args)

    # Invalid permanence
    args = [0, 48, 1.124]
    self.assertRaises(ValueError, connections.createSynapse, *args)
    args = [0, 48, -0.124]
    self.assertRaises(ValueError, connections.createSynapse, *args)


  def testDestroySynapse(self):
    connections = self.connections

    connections.createSegment(0)
    self.assertEqual(connections.synapsesForSegment(0), set())

    self.assertEqual(connections.createSynapse(0, 254, 0.1173), 0)
    self.assertEqual(connections.createSynapse(0, 477, 0.3253), 1)

    connections.destroySynapse(0)

    args = [0]
    self.assertRaises(IndexError, connections.dataForSynapse, *args)

    self.assertEqual(connections.synapsesForSegment(0), set([1]))

    self.assertEqual(connections.synapsesForPresynapticCell(174), {})
    self.assertEqual(connections.synapsesForPresynapticCell(254), {})


  def testDataForSynapseInvalidSynapse(self):
    connections = self.connections

    connections.createSegment(0)
    connections.createSynapse(0, 834, 0.1284)

    args = [1]
    self.assertRaises(IndexError, connections.dataForSynapse, *args)


  def testSynapsesForSegmentInvalidSegment(self):
    connections = self.connections

    connections.createSegment(0)

    args = [1]
    self.assertRaises(IndexError, connections.synapsesForSegment, *args)


  def testUpdateSynapsePermanence(self):
    connections = self.connections

    connections.createSegment(0)
    connections.createSynapse(0, 483, 0.1284)

    connections.updateSynapsePermanence(0, 0.2496)
    self.assertEqual(connections.dataForSynapse(0), (0, 483, 0.2496))


  def testUpdateSynapsePermanenceInvalidParams(self):
    connections = self.connections

    connections.createSegment(0)
    connections.createSynapse(0, 483, 0.1284)

    # Invalid synapse
    args = [1, 0.4374]
    self.assertRaises(KeyError, connections.updateSynapsePermanence, *args)

    # Invalid permanence
    args = [0, 1.4374]
    self.assertRaises(ValueError, connections.updateSynapsePermanence, *args)
    args = [0, -0.4374]
    self.assertRaises(ValueError, connections.updateSynapsePermanence, *args)


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
