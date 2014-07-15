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

from nupic.research.TM import Connections, TM



class TMTest(unittest.TestCase):


  def testInit(self):
    pass



class ConnectionsTest(unittest.TestCase):


  def testInit(self):
    columnDimensions = [2048]
    cellsPerColumn = 32

    connections = Connections(columnDimensions, cellsPerColumn)
    self.assertEqual(connections.columnDimensions, columnDimensions)
    self.assertEqual(connections.cellsPerColumn, cellsPerColumn)


  def testInitInvalidParams(self):
    # Invalid columnDimensions
    args = [[], 32]
    self.assertRaises(ValueError, Connections, *args)

    # Invalid cellsPerColumn
    args = [[2048], 0]
    self.assertRaises(ValueError, Connections, *args)
    args = [[2048], -10]
    self.assertRaises(ValueError, Connections, *args)




if __name__ == '__main__':
  unittest.main()
