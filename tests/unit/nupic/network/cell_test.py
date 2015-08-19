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



class CellTest(unittest.TestCase):


  def testCreateSegment(self):
    cell1 = Cell()
    self.assertEqual(cell1.segments, set())

    segment1 = cell1.createSegment()
    self.assertEqual(segment1.cell, cell1)
    segment2 = cell1.createSegment()
    self.assertEqual(segment2.cell, cell1)

    self.assertEqual(cell1.segments, set([segment1, segment2]))


  def testDestroySegment(self):    
    cell1 = Cell()
    segment1 = cell1.createSegment()
    self.assertEqual(segment1.cell, cell1)
    segment2 = cell1.createSegment()
    self.assertEqual(segment2.cell, cell1)
    
    cell2 = Cell()
    synapse1 = segment1.createSynapse(presynapticCell=cell2, permanence=0.1173)
    self.assertEqual(synapse1.presynapticCell, cell2)
    self.assertEqual(synapse1.permanence, 0.1173)
    cell3 = Cell()
    synapse2 = segment1.createSynapse(presynapticCell=cell3, permanence=0.3253)
    self.assertEqual(synapse2.presynapticCell, cell3)
    self.assertEqual(synapse2.permanence, 0.3253)
    cell4 = Cell()
    synapse3 = segment2.createSynapse(presynapticCell=cell4, permanence=0.1284)
    self.assertEqual(synapse3.presynapticCell, cell4)
    self.assertEqual(synapse3.permanence, 0.1284)

    cell1.destroySegment(segment1)
    
    # TODO: self.assertFalse('segment1' in locals())
    # TODO: self.assertFalse('synapse1' in locals())
    # TODO: self.assertFalse('synapse2' in locals())
    
    self.assertEqual(cell2.postsynapticCellsSynapses, set([]))
    self.assertEqual(cell3.postsynapticCellsSynapses, set([]))
    self.assertEqual(cell4.postsynapticCellsSynapses, set([synapse3]))

    self.assertEqual(cell1.segments, set([segment2]))



if __name__ == '__main__':
  unittest.main()
