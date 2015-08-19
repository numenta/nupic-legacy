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

from nupic.network.layer import Layer



class LayerTest(unittest.TestCase):


  def setUp(self):
    self.layer = Layer()


  def testInitInvalidParams(self):
    # Invalid columnDimensions
    kwargs = {"columnDimensions": [], "numCellsPerColumn": 32}
    self.assertRaises(ValueError, Layer, **kwargs)

    # Invalid numCellsPerColumn
    kwargs = {"columnDimensions": [2048], "numCellsPerColumn": 0}
    self.assertRaises(ValueError, Layer, **kwargs)
    kwargs = {"columnDimensions": [2048], "numCellsPerColumn": -10}
    self.assertRaises(ValueError, Layer, **kwargs)


  def testNumberOfColumns(self):
    layer = Layer(
      columnDimensions=[64, 64],
      numCellsPerColumn=32
    )
    self.assertEqual(layer.numberOfColumns(), 64 * 64)


  def testNumberOfCells(self):
    layer = Layer(
      columnDimensions=[64, 64],
      numCellsPerColumn=32
    )
    self.assertEqual(layer.numberOfCells(), 64 * 64 * 32)



if __name__ == '__main__':
  unittest.main()
