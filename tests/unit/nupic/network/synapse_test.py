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



class SynapseTest(unittest.TestCase):
  

  def testSynapseSetPermanence(self):    
    cell1 = Cell()
    segment1 = cell1.createSegment()
    synapse = segment1.createSynapse(presynapticCell=Cell(), permanence=0.1284)

    # Invalid permanence
    args = [1.4374]
    self.assertRaises(ValueError, setattr, synapse, "permanence", *args)
    args = [-0.4374]
    self.assertRaises(ValueError, setattr, synapse, "permanence", *args)



if __name__ == '__main__':
  unittest.main()
