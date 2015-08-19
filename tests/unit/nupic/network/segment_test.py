#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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

import unittest

from nupic.network.cell import Cell
from nupic.network.segment import Segment
from nupic.network.synapse import Synapse



class SegmentTest(unittest.TestCase):


  def testCreateSynapse(self):    
    cell1 = Cell()
    segment1 = cell1.createSegment()
    self.assertEqual(segment1.synapses, set())
    
    cell2 = Cell()
    synapse1 = segment1.createSynapse(presynapticCell=cell2, permanence=0.1173)
    self.assertEqual(synapse1.presynapticCell, cell2)
    self.assertEqual(synapse1.permanence, 0.1173)
    cell3 = Cell()
    synapse2 = segment1.createSynapse(presynapticCell=cell3, permanence=0.3253)
    self.assertEqual(synapse2.presynapticCell, cell3)
    self.assertEqual(synapse2.permanence, 0.3253)

    self.assertEqual(segment1.synapses, set([synapse1, synapse2]))

    self.assertEqual(cell2.postsynapticCellsSynapses, set([synapse1]))
    self.assertEqual(cell3.postsynapticCellsSynapses, set([synapse2]))


  def testCreateSynapseInvalidParams(self):
    cell1 = Cell()
    segment1 = cell1.createSegment()

    # Invalid permanence
    args = [cell1, None, 1.124]
    self.assertRaises(ValueError, segment1.createSynapse, *args)
    args = [cell1, None, -0.124]
    self.assertRaises(ValueError, segment1.createSynapse, *args)


  def testDestroySynapse(self):
    cell1 = Cell()
    segment1 = cell1.createSegment()
    self.assertEqual(segment1.synapses, set())
    
    cell2 = Cell()
    synapse1 = segment1.createSynapse(presynapticCell=cell2, permanence=0.1173)
    self.assertEqual(synapse1.presynapticCell, cell2)
    self.assertEqual(synapse1.permanence, 0.1173)
    cell3 = Cell()
    synapse2 = segment1.createSynapse(presynapticCell=cell3, permanence=0.3253)
    self.assertEqual(synapse2.presynapticCell, cell3)
    self.assertEqual(synapse2.permanence, 0.3253)
    
    segment1.destroySynapse(synapse1)

    self.assertEqual(segment1.synapses, set([synapse2]))

    self.assertEqual(cell2.postsynapticCellsSynapses, set([]))
    self.assertEqual(cell3.postsynapticCellsSynapses, set([synapse2]))


  def testDestroyAllSynapses(self):
    cell1 = Cell()
    segment1 = cell1.createSegment()
    self.assertEqual(segment1.synapses, set())
    
    cell2 = Cell()
    synapse1 = segment1.createSynapse(presynapticCell=cell2, permanence=0.1173)
    self.assertEqual(synapse1.presynapticCell, cell2)
    self.assertEqual(synapse1.permanence, 0.1173)
    cell3 = Cell()
    synapse2 = segment1.createSynapse(presynapticCell=cell3, permanence=0.3253)
    self.assertEqual(synapse2.presynapticCell, cell3)
    self.assertEqual(synapse2.permanence, 0.3253)
    
    segment1.destroyAllSynapses()

    self.assertEqual(segment1.synapses, set([]))

    self.assertEqual(cell2.postsynapticCellsSynapses, set([]))
    self.assertEqual(cell3.postsynapticCellsSynapses, set([]))



if __name__ == '__main__':
  unittest.main()
