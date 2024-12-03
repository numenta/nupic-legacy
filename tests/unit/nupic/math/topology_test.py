# Copyright 2016 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""Topology unit tests"""

import unittest

from nupic.math.topology import (coordinatesFromIndex,
                                 indexFromCoordinates,
                                 neighborhood,
                                 wrappingNeighborhood)

class TestTopology(unittest.TestCase):

  def testIndexFromCoordinates(self):
    self.assertEquals(0, indexFromCoordinates((0,), (100,)))
    self.assertEquals(50, indexFromCoordinates((50,), (100,)))
    self.assertEquals(99, indexFromCoordinates((99,), (100,)))

    self.assertEquals(0, indexFromCoordinates((0, 0), (100, 80)))
    self.assertEquals(10, indexFromCoordinates((0, 10), (100, 80)))
    self.assertEquals(80, indexFromCoordinates((1, 0), (100, 80)))
    self.assertEquals(90, indexFromCoordinates((1, 10), (100, 80)))

    self.assertEquals(0, indexFromCoordinates((0, 0, 0), (100, 10, 8)))
    self.assertEquals(7, indexFromCoordinates((0, 0, 7), (100, 10, 8)))
    self.assertEquals(8, indexFromCoordinates((0, 1, 0), (100, 10, 8)))
    self.assertEquals(80, indexFromCoordinates((1, 0, 0), (100, 10, 8)))
    self.assertEquals(88, indexFromCoordinates((1, 1, 0), (100, 10, 8)))
    self.assertEquals(89, indexFromCoordinates((1, 1, 1), (100, 10, 8)))


  def testCoordinatesFromIndex(self):
    self.assertEquals([0], coordinatesFromIndex(0, [100]));
    self.assertEquals([50], coordinatesFromIndex(50, [100]));
    self.assertEquals([99], coordinatesFromIndex(99, [100]));

    self.assertEquals([0, 0], coordinatesFromIndex(0, [100, 80]));
    self.assertEquals([0, 10], coordinatesFromIndex(10, [100, 80]));
    self.assertEquals([1, 0], coordinatesFromIndex(80, [100, 80]));
    self.assertEquals([1, 10], coordinatesFromIndex(90, [100, 80]));

    self.assertEquals([0, 0, 0], coordinatesFromIndex(0, [100, 10, 8]));
    self.assertEquals([0, 0, 7], coordinatesFromIndex(7, [100, 10, 8]));
    self.assertEquals([0, 1, 0], coordinatesFromIndex(8, [100, 10, 8]));
    self.assertEquals([1, 0, 0], coordinatesFromIndex(80, [100, 10, 8]));
    self.assertEquals([1, 1, 0], coordinatesFromIndex(88, [100, 10, 8]));
    self.assertEquals([1, 1, 1], coordinatesFromIndex(89, [100, 10, 8]));


  # ===========================================================================
  # NEIGHBORHOOD
  # ===========================================================================


  def expectNeighborhoodIndices(self, centerCoords, radius, dimensions, expected):
    centerIndex = indexFromCoordinates(centerCoords, dimensions)

    numIndices = 0

    for index, expectedIndex in zip(neighborhood(centerIndex, radius,
                                                 dimensions),
                                    expected):
      numIndices += 1
      self.assertEquals(index, expectedIndex)

    self.assertEquals(numIndices, len(expected))


  def expectNeighborhoodCoords(self, centerCoords, radius, dimensions, expected):
    centerIndex = indexFromCoordinates(centerCoords, dimensions)

    numIndices = 0

    for index, expectedIndex in zip(neighborhood(centerIndex, radius,
                                                 dimensions),
                                    expected):
      numIndices += 1
      self.assertEquals(index, indexFromCoordinates(expectedIndex, dimensions))

    self.assertEquals(numIndices, len(expected))


  def testNeighborhoodOfOrigin1D(self):
    self.expectNeighborhoodIndices(
      centerCoords = (0,),
      dimensions = (100,),
      radius = 2,
      expected = (0, 1, 2))


  def testNeighborhoodOfOrigin2D(self):
    self.expectNeighborhoodCoords(
      centerCoords = (0, 0),
      dimensions = (100, 80),
      radius = 2,
      expected = ((0, 0), (0, 1), (0, 2),
                  (1, 0), (1, 1), (1, 2),
                  (2, 0), (2, 1), (2, 2)))


  def testNeighborhoodOfOrigin3D(self):
    self.expectNeighborhoodCoords(
      centerCoords = (0, 0, 0),
      dimensions = (100, 80, 60),
      radius = 1,
      expected = ((0, 0, 0), (0, 0, 1),
                  (0, 1, 0), (0, 1, 1),
                  (1, 0, 0), (1, 0, 1),
                  (1, 1, 0), (1, 1, 1)))


  def testNeighborhoodInMiddle1D(self):
    self.expectNeighborhoodIndices(
      centerCoords = (50,),
      dimensions = (100,),
      radius = 1,
      expected = (49, 50, 51))


  def testNeighborhoodOfMiddle2D(self):
    self.expectNeighborhoodCoords(
      centerCoords = (50, 50),
      dimensions = (100, 80),
      radius = 1,
      expected = ((49, 49), (49, 50), (49, 51),
                  (50, 49), (50, 50), (50, 51),
                  (51, 49), (51, 50), (51, 51)))


  def testNeighborhoodOfEnd2D(self):
    self.expectNeighborhoodCoords(
      centerCoords = (99, 79),
      dimensions = (100, 80),
      radius = 2,
      expected = ((97, 77), (97, 78), (97, 79),
                  (98, 77), (98, 78), (98, 79),
                  (99, 77), (99, 78), (99, 79)))


  def testNeighborhoodWiderThanWorld(self):
    self.expectNeighborhoodCoords(
      centerCoords = (0, 0),
      dimensions = (3, 2),
      radius = 3,
      expected = ((0, 0), (0, 1),
                  (1, 0), (1, 1),
                  (2, 0), (2, 1)))


  def testNeighborhoodRadiusZero(self):
    self.expectNeighborhoodIndices(
      centerCoords = (0,),
      dimensions = (100,),
      radius = 0,
      expected = (0,))

    self.expectNeighborhoodCoords(
      centerCoords = (0, 0),
      dimensions = (100, 80),
      radius = 0,
      expected = ((0, 0),))

    self.expectNeighborhoodCoords(
      centerCoords = (0, 0, 0),
      dimensions = (100, 80, 60),
      radius = 0,
      expected = ((0, 0, 0),))


  def testNeighborhoodDimensionOne(self):
    self.expectNeighborhoodCoords(
      centerCoords = (5, 0),
      dimensions = (10, 1),
      radius = 1,
      expected = ((4, 0), (5, 0), (6, 0)))

    self.expectNeighborhoodCoords(
      centerCoords = (5, 0, 0),
      dimensions = (10, 1, 1),
      radius = 1,
      expected = ((4, 0, 0), (5, 0, 0), (6, 0, 0)))


  # ===========================================================================
  # WRAPPING NEIGHBORHOOD
  # ===========================================================================

  def expectWrappingNeighborhoodIndices(self, centerCoords, radius, dimensions,
                                        expected):
    centerIndex = indexFromCoordinates(centerCoords, dimensions)

    numIndices = 0

    for index, expectedIndex in zip(wrappingNeighborhood(centerIndex, radius,
                                                         dimensions),
                                    expected):
      numIndices += 1
      self.assertEquals(index, expectedIndex)

    self.assertEquals(numIndices, len(expected))


  def expectWrappingNeighborhoodCoords(self, centerCoords, radius, dimensions,
                                       expected):
    centerIndex = indexFromCoordinates(centerCoords, dimensions)

    numIndices = 0

    for index, expectedIndex in zip(wrappingNeighborhood(centerIndex, radius,
                                                         dimensions),
                                    expected):
      numIndices += 1
      self.assertEquals(index, indexFromCoordinates(expectedIndex, dimensions))

    self.assertEquals(numIndices, len(expected))


  def testWrappingNeighborhoodOfOrigin1D(self):
    self.expectWrappingNeighborhoodIndices(
      centerCoords = (0,),
      dimensions = (100,),
      radius = 1,
      expected = (99, 0, 1))


  def testWrappingNeighborhoodOfOrigin2D(self):
    self.expectWrappingNeighborhoodCoords(
      centerCoords = (0, 0),
      dimensions = (100, 80),
      radius = 1,
      expected = ((99, 79), (99, 0), (99, 1),
                  (0, 79), (0, 0), (0, 1),
                  (1, 79), (1, 0), (1, 1)))


  def testWrappingNeighborhoodOfOrigin3D(self):
    self.expectWrappingNeighborhoodCoords(
      centerCoords = (0, 0, 0),
      dimensions = (100, 80, 60),
      radius = 1,
      expected = ((99, 79, 59), (99, 79, 0), (99, 79, 1),
                  (99, 0, 59), (99, 0, 0), (99, 0, 1),
                  (99, 1, 59), (99, 1, 0), (99, 1, 1),
                  (0, 79, 59), (0, 79, 0), (0, 79, 1),
                  (0, 0, 59), (0, 0, 0), (0, 0, 1),
                  (0, 1, 59), (0, 1, 0), (0, 1, 1),
                  (1, 79, 59), (1, 79, 0), (1, 79, 1),
                  (1, 0, 59), (1, 0, 0), (1, 0, 1),
                  (1, 1, 59), (1, 1, 0), (1, 1, 1),))


  def testWrappingNeighborhoodInMiddle1D(self):
    self.expectWrappingNeighborhoodIndices(
      centerCoords = (50,),
      dimensions = (100,),
      radius = 1,
      expected = (49, 50, 51))


  def testWrappingNeighborhoodOfMiddle2D(self):
    self.expectWrappingNeighborhoodCoords(
      centerCoords = (50, 50),
      dimensions = (100, 80),
      radius = 1,
      expected = ((49, 49), (49, 50), (49, 51),
                  (50, 49), (50, 50), (50, 51),
                  (51, 49), (51, 50), (51, 51)))


  def testWrappingNeighborhoodOfEnd2D(self):
    self.expectWrappingNeighborhoodCoords(
      centerCoords = (99, 79),
      dimensions = (100, 80),
      radius = 1,
      expected = ((98, 78), (98, 79), (98, 0),
                  (99, 78), (99, 79), (99, 0),
                  (0, 78), (0, 79), (0, 0)))


  def testWrappingNeighborhoodWiderThanWorld(self):
    # The order is weird because it starts walking from {-3, -3} and avoids
    # walking the same point twice.
    self.expectWrappingNeighborhoodCoords(
      centerCoords = (0, 0),
      dimensions = (3, 2),
      radius = 3,
      expected = ((0, 1), (0, 0),
                  (1, 1), (1, 0),
                  (2, 1), (2, 0)))


  def testWrappingNeighborhoodRadiusZero(self):
    self.expectWrappingNeighborhoodIndices(
      centerCoords = (0,),
      dimensions = (100,),
      radius = 0,
      expected = (0,))

    self.expectWrappingNeighborhoodCoords(
      centerCoords = (0, 0),
      dimensions = (100, 80),
      radius = 0,
      expected = ((0, 0),))

    self.expectWrappingNeighborhoodCoords(
      centerCoords = (0, 0, 0),
      dimensions = (100, 80, 60),
      radius = 0,
      expected = ((0, 0, 0),))


  def testWrappingNeighborhoodDimensionOne(self):
    self.expectWrappingNeighborhoodCoords(
      centerCoords = (5, 0),
      dimensions = (10, 1),
      radius = 1,
      expected = ((4, 0), (5, 0), (6, 0)))

    self.expectWrappingNeighborhoodCoords(
      centerCoords = (5, 0, 0),
      dimensions = (10, 1, 1),
      radius = 1,
      expected = ((4, 0, 0), (5, 0, 0), (6, 0, 0)))
