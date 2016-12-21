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

import numpy as np
import tempfile
import unittest
from mock import patch

from nupic.encoders.base import defaultDtype
from nupic.encoders.coordinate import CoordinateEncoder

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.encoders.coordinate_capnp import CoordinateEncoderProto

# Disable warnings about accessing protected members
# pylint: disable=W0212



class CoordinateEncoderTest(unittest.TestCase):
  """Unit tests for CoordinateEncoder class"""

  def setUp(self):
    self.encoder = CoordinateEncoder(name="coordinate", n=33, w=3)


  def testInvalidW(self):
    # Even
    args = {"name": "coordinate",
            "n": 45,
            "w": 4}
    self.assertRaises(ValueError, CoordinateEncoder, **args)

    # 0
    args = {"name": "coordinate",
            "n": 45,
            "w": 0}
    self.assertRaises(ValueError, CoordinateEncoder, **args)

    # Negative
    args = {"name": "coordinate",
            "n": 45,
            "w": -2}
    self.assertRaises(ValueError, CoordinateEncoder, **args)


  def testInvalidN(self):
    # Too small
    args = {"name": "coordinate",
            "n": 11,
            "w": 3}
    self.assertRaises(ValueError, CoordinateEncoder, **args)


  def testHashCoordinate(self):
    h1 = self.encoder._hashCoordinate(np.array([0]))
    self.assertEqual(h1, 7415141576215061722)
    h2 = self.encoder._hashCoordinate(np.array([0, 1]))
    self.assertEqual(h2, 6909411824118942936)


  def testOrderForCoordinate(self):
    h1 = self.encoder._orderForCoordinate(np.array([2, 5, 10]))
    h2 = self.encoder._orderForCoordinate(np.array([2, 5, 11]))
    h3 = self.encoder._orderForCoordinate(np.array([2497477, -923478]))

    self.assertTrue(0 <= h1 and h1 < 1)
    self.assertTrue(0 <= h2 and h2 < 1)
    self.assertTrue(0 <= h3 and h3 < 1)

    self.assertTrue(h1 != h2)
    self.assertTrue(h2 != h3)


  def testBitForCoordinate(self):
    n = 1000
    b1 = self.encoder._bitForCoordinate(np.array([2, 5, 10]), n)
    b2 = self.encoder._bitForCoordinate(np.array([2, 5, 11]), n)
    b3 = self.encoder._bitForCoordinate(np.array([2497477, -923478]), n)

    self.assertTrue(0 <= b1 and b1 < n)
    self.assertTrue(0 <= b2 and b2 < n)
    self.assertTrue(0 <= b3 and b3 < n)

    self.assertTrue(b1 != b2)
    self.assertTrue(b2 != b3)

    # Small n
    n = 2
    b4 = self.encoder._bitForCoordinate(np.array([5, 10]), n)

    self.assertTrue(0 <= b4 < n)


  @patch.object(CoordinateEncoder, "_orderForCoordinate")
  def testTopWCoordinates(self, mockOrderForCoordinate):
    # Mock orderForCoordinate
    mockFn = lambda coordinate: np.sum(coordinate) / 5.0
    mockOrderForCoordinate.side_effect = mockFn

    coordinates = np.array([[1], [2], [3], [4], [5]])
    top = self.encoder._topWCoordinates(coordinates, 2).tolist()

    self.assertEqual(len(top), 2)
    self.assertIn([5], top)
    self.assertIn([4], top)


  def testNeighbors1D(self):
    coordinate = np.array([100])
    radius = 5
    neighbors = self.encoder._neighbors(coordinate, radius).tolist()

    self.assertEqual(len(neighbors), 11)
    self.assertIn([95], neighbors)
    self.assertIn([100], neighbors)
    self.assertIn([105], neighbors)


  def testNeighbors2D(self):
    coordinate = np.array([100, 200])
    radius = 5
    neighbors = self.encoder._neighbors(coordinate, radius).tolist()

    self.assertEqual(len(neighbors), 121)
    self.assertIn([95, 195], neighbors)
    self.assertIn([95, 205], neighbors)
    self.assertIn([100, 200], neighbors)
    self.assertIn([105, 195], neighbors)
    self.assertIn([105, 205], neighbors)


  def testNeighbors0Radius(self):
    coordinate = np.array([100, 200, 300])
    radius = 0
    neighbors = self.encoder._neighbors(coordinate, radius).tolist()

    self.assertEqual(len(neighbors), 1)
    self.assertIn([100, 200, 300], neighbors)


  def testEncodeIntoArray(self):
    n = 33
    w = 3
    encoder = CoordinateEncoder(name="coordinate", n=n, w=w)

    coordinate = np.array([100, 200])
    radius = 5
    output1 = encode(encoder, coordinate, radius)

    self.assertEqual(np.sum(output1), w)

    # Test that we get the same output for the same input
    output2 = encode(encoder, coordinate, radius)
    self.assertTrue(np.array_equal(output2, output1))


  def testEncodeSaturateArea(self):
    n = 1999
    w = 25
    encoder = CoordinateEncoder(name="coordinate", n=n, w=w)

    outputA = encode(encoder, np.array([0, 0]), 2)
    outputB = encode(encoder, np.array([0, 1]), 2)

    self.assertEqual(overlap(outputA, outputB), 0.8)


  def testEncodeRelativePositions(self):
    # As you get farther from a coordinate, the overlap should decrease
    overlaps = overlapsForRelativeAreas(999, 51, np.array([100, 200]), 10,
                                        dPosition=np.array([2, 2]),
                                        num=5)
    self.assertDecreasingOverlaps(overlaps)


  def testEncodeRelativeRadii(self):
    # As radius increases, the overlap should decrease
    overlaps = overlapsForRelativeAreas(999, 25, np.array([100, 200]), 5,
                                        dRadius=2,
                                        num=5)
    self.assertDecreasingOverlaps(overlaps)

    # As radius decreases, the overlap should decrease
    overlaps = overlapsForRelativeAreas(999, 51, np.array([100, 200]), 20,
                                        dRadius=-2,
                                        num=5)
    self.assertDecreasingOverlaps(overlaps)


  def testEncodeRelativePositionsAndRadii(self):
    # As radius increases and positions change, the overlap should decrease
    overlaps = overlapsForRelativeAreas(999, 25, np.array([100, 200]), 5,
                                        dPosition=np.array([1, 1]),
                                        dRadius=1,
                                        num=5)
    self.assertDecreasingOverlaps(overlaps)


  def testEncodeUnrelatedAreas(self):
    """
    assert unrelated areas don"t share bits
    (outside of chance collisions)
    """
    avgThreshold = 0.3

    maxThreshold = 0.12
    overlaps = overlapsForUnrelatedAreas(1499, 37, 5)
    self.assertLess(np.max(overlaps), maxThreshold)
    self.assertLess(np.average(overlaps), avgThreshold)

    maxThreshold = 0.12
    overlaps = overlapsForUnrelatedAreas(1499, 37, 10)
    self.assertLess(np.max(overlaps), maxThreshold)
    self.assertLess(np.average(overlaps), avgThreshold)

    maxThreshold = 0.17
    overlaps = overlapsForUnrelatedAreas(999, 25, 10)
    self.assertLess(np.max(overlaps), maxThreshold)
    self.assertLess(np.average(overlaps), avgThreshold)

    maxThreshold = 0.25
    overlaps = overlapsForUnrelatedAreas(499, 13, 10)
    self.assertLess(np.max(overlaps), maxThreshold)
    self.assertLess(np.average(overlaps), avgThreshold)


  def testEncodeAdjacentPositions(self, verbose=False):
    repetitions = 100
    n = 999
    w = 25
    radius = 10
    minThreshold = 0.75
    avgThreshold = 0.90
    allOverlaps = np.empty(repetitions)

    for i in range(repetitions):
      overlaps = overlapsForRelativeAreas(n, w,
                                          np.array([i * 10, i * 10]), radius,
                                          dPosition=np.array([0, 1]),
                                          num=1)
      allOverlaps[i] = overlaps[0]

    self.assertGreater(np.min(allOverlaps), minThreshold)
    self.assertGreater(np.average(allOverlaps), avgThreshold)

    if verbose:
      print ("===== Adjacent positions overlap "
             "(n = {0}, w = {1}, radius = {2}) ===").format(n, w, radius)
      print "Max: {0}".format(np.max(allOverlaps))
      print "Min: {0}".format(np.min(allOverlaps))
      print "Average: {0}".format(np.average(allOverlaps))


  def assertDecreasingOverlaps(self, overlaps):
    self.assertEqual((np.diff(overlaps) > 0).sum(), 0)


  @unittest.skipUnless(
      capnp, "pycapnp is not installed, skipping serialization test.")
  def testReadWrite(self):
    coordinate = np.array([100, 200])
    radius = 5
    output1 = encode(self.encoder, coordinate, radius)

    proto1 = CoordinateEncoderProto.new_message()
    self.encoder.write(proto1)

    # Write the proto to a temp file and read it back into a new proto
    with tempfile.TemporaryFile() as f:
      proto1.write(f)
      f.seek(0)
      proto2 = CoordinateEncoderProto.read(f)

    encoder = CoordinateEncoder.read(proto2)

    self.assertIsInstance(encoder, CoordinateEncoder)
    self.assertEqual(encoder.w, self.encoder.w)
    self.assertEqual(encoder.n, self.encoder.n)
    self.assertEqual(encoder.name, self.encoder.name)
    self.assertEqual(encoder.verbosity, self.encoder.verbosity)

    coordinate = np.array([100, 200])
    radius = 5
    output2 = encode(encoder, coordinate, radius)

    self.assertTrue(np.array_equal(output1, output2))


def encode(encoder, coordinate, radius):
  output = np.zeros(encoder.getWidth(), dtype=defaultDtype)
  encoder.encodeIntoArray((coordinate, radius), output)
  return output


def overlap(sdr1, sdr2):
  assert sdr1.size == sdr2.size
  return float((sdr1 & sdr2).sum()) / sdr1.sum()


def overlapsForRelativeAreas(n, w, initPosition, initRadius, dPosition=None,
                             dRadius=0, num=100, verbose=False):
  """
  Return overlaps between an encoding and other encodings relative to it

  :param n: the size of the encoder output
  :param w: the number of active bits in the encoder output
  :param initPosition: the position of the first encoding
  :param initRadius: the radius of the first encoding
  :param dPosition: the offset to apply to each subsequent position
  :param dRadius: the offset to apply to each subsequent radius
  :param num: the number of encodings to generate
  :param verbose: whether to print verbose output
  """
  encoder = CoordinateEncoder(name="coordinate", n=n, w=w)

  overlaps = np.empty(num)
  outputA = encode(encoder, np.array(initPosition), initRadius)

  for i in range(num):
    newPosition = initPosition if dPosition is None else (
      initPosition + (i + 1) * dPosition)
    newRadius = initRadius + (i + 1) * dRadius
    outputB = encode(encoder, newPosition, newRadius)
    overlaps[i] = overlap(outputA, outputB)

  if verbose:
    print
    print ("===== Relative encoding overlaps (n = {0}, w = {1}, "
                           "initPosition = {2}, initRadius = {3}, "
                           "dPosition = {4}, dRadius = {5}) =====").format(
      n, w, initPosition, initRadius, dPosition, dRadius)
    print "Average: {0}".format(np.average(overlaps))
    print "Max: {0}".format(np.max(overlaps))

  return overlaps


def overlapsForUnrelatedAreas(n, w, radius, repetitions=100, verbose=False):
  """
  Return overlaps between an encoding and other, unrelated encodings
  """
  return overlapsForRelativeAreas(n, w, np.array([0, 0]), radius,
                                  dPosition=np.array([0, radius * 10]),
                                  num=repetitions, verbose=verbose)



if __name__ == "__main__":
  unittest.main()
