#! /usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have an agreement
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

import unittest

import numpy

from nupic.bindings.math import GetNTAReal
from nupic.bindings.algorithms import SpatialPooler
# from nupic.research.spatial_pooler import SpatialPooler



realDType = GetNTAReal()



class SpatialPoolerTest(unittest.TestCase):
  """Unit Tests for C++ SpatialPooler class."""


  def testCalculateOverlap(self):
    sp = SpatialPooler(inputDimensions = [10],
                       columnDimensions = [5])

    permanences = [
      [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
      [0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
      [0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
      [0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
      [0, 0, 0, 0, 0, 0, 0, 0, 1, 1]
    ]
    inputVectors = [
      [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
      [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
      [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
      [1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
    ]
    expectedOverlaps = [
      [0,  0,  0,  0,  0],
      [10, 8,  6,  4,  2],
      [5,  4,  3,  2,  1],
      [5,  3,  1,  0,  0],
      [1,  1,  1,  1,  1]
    ]

    for column, permanence in enumerate(permanences):
      sp.setPermanence(column, numpy.array(permanence, dtype=realDType))

    for inputVector, expectedOverlap in zip(inputVectors, expectedOverlaps):
      inputVector = numpy.array(inputVector, dtype=realDType)
      overlap = set(sp._calculateOverlap(inputVector))
      expected = set(expectedOverlap)
      self.assertSetEqual(overlap, expected,
                          "Input: {0}\tExpected: {1}\tActual: {2}".format(
                            inputVector, expected, overlap))


  def testInhibitColumnsGlobal(self):
    sp = SpatialPooler(inputDimensions = [10],
                       columnDimensions = [10],
                       globalInhibition = True,
                       numActiveColumnsPerInhArea = 10)

    overlaps = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    expectedActive = set([5, 6, 7, 8, 9])

    active = sp._inhibitColumns(numpy.array(overlaps, dtype=realDType))
    active = set(active)

    self.assertSetEqual(active, expectedActive,
                        "Input: {0}\tExpected: {1}\tActual: {2}".format(
                          overlaps, expectedActive, active))



if __name__ == "__main__":
  unittest.main()
