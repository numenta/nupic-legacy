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

from nupic.network.region import Region



class RegionTest(unittest.TestCase):


  def setUp(self):
    self.region = Region()


  def testInitInvalidParams(self):
    # Invalid columnDimensions
    kwargs = {"columnDimensions": [], "numCellsPerColumn": 32}
    self.assertRaises(ValueError, Region, **kwargs)

    # Invalid numCellsPerColumn
    kwargs = {"columnDimensions": [2048], "numCellsPerColumn": 0}
    self.assertRaises(ValueError, Region, **kwargs)
    kwargs = {"columnDimensions": [2048], "numCellsPerColumn": -10}
    self.assertRaises(ValueError, Region, **kwargs)


  def testNumberOfColumns(self):
    region = Region(
      columnDimensions=[64, 64],
      numCellsPerColumn=32
    )
    self.assertEqual(region.numberOfColumns(), 64 * 64)


  def testNumberOfCells(self):
    region = Region(
      columnDimensions=[64, 64],
      numCellsPerColumn=32
    )
    self.assertEqual(region.numberOfCells(), 64 * 64 * 32)



if __name__ == '__main__':
  unittest.main()
