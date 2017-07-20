# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013-2015, Numenta, Inc.  Unless you have an agreement
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

"""Unit tests for date encoder"""

import numpy
import itertools
import tempfile
from nupic.encoders.base import defaultDtype
from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
import unittest

from nupic.encoders.scalar import ScalarEncoder


try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.encoders.scalar_capnp import ScalarEncoderProto



class ScalarEncoderTest(unittest.TestCase):
  """Unit tests for ScalarEncoder class"""

  def setUp(self):
    # use of forced is not recommended, but used here for readability, see
    # scalar.py
    self._l = ScalarEncoder(name="scalar", n=14, w=3, minval=1, maxval=8,
                            periodic=True, forced=True)

  def testScalarEncoder(self):
    """Testing ScalarEncoder..."""

    # -------------------------------------------------------------------------
    # test missing values
    mv = ScalarEncoder(name="mv", n=14, w=3, minval=1, maxval=8,
                       periodic=False, forced=True)
    empty = mv.encode(SENTINEL_VALUE_FOR_MISSING_DATA)
    self.assertEqual(empty.sum(), 0)


  def testNaNs(self):
    """test NaNs"""
    mv = ScalarEncoder(name="mv", n=14, w=3, minval=1, maxval=8,
                       periodic=False, forced=True)
    empty = mv.encode(float("nan"))
    self.assertEqual(empty.sum(), 0)


  def testBottomUpEncodingPeriodicEncoder(self):
    """Test bottom-up encoding for a Periodic encoder"""
    l = ScalarEncoder(n=14, w=3, minval=1, maxval=8, periodic=True,
                      forced=True)
    self.assertEqual(l.getDescription(), [("[1:8]", 0)])
    l = ScalarEncoder(name="scalar", n=14, w=3, minval=1, maxval=8,
                      periodic=True, forced=True)
    self.assertEqual(l.getDescription(), [("scalar", 0)])
    self.assertTrue(numpy.array_equal(
      l.encode(3),
      numpy.array([0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                  dtype=defaultDtype)))
    self.assertTrue(numpy.array_equal(l.encode(3.1), l.encode(3)))
    self.assertTrue(numpy.array_equal(
      l.encode(3.5),
      numpy.array([0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
                  dtype=defaultDtype)))
    self.assertTrue(numpy.array_equal(l.encode(3.6), l.encode(3.5)))
    self.assertTrue(numpy.array_equal(l.encode(3.7), l.encode(3.5)))
    self.assertTrue(numpy.array_equal(
      l.encode(4),
      numpy.array([0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0],
                   dtype=defaultDtype)))

    self.assertTrue(numpy.array_equal(
      l.encode(1),
      numpy.array([1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                  dtype=defaultDtype)))
    self.assertTrue(numpy.array_equal(
      l.encode(1.5),
      numpy.array([1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                  dtype=defaultDtype)))
    self.assertTrue(numpy.array_equal(
      l.encode(7),
      numpy.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
                  dtype=defaultDtype)))
    self.assertTrue(numpy.array_equal(
      l.encode(7.5),
      numpy.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
                  dtype=defaultDtype)))

    self.assertEqual(l.resolution, 0.5)
    self.assertEqual(l.radius, 1.5)


  def testCreateResolution(self):
    """Test that we get the same encoder when we construct it using resolution
    instead of n
    """
    l = self._l
    d = l.__dict__
    l = ScalarEncoder(name="scalar", resolution=0.5, w=3, minval=1, maxval=8,
                      periodic=True, forced=True)
    self.assertEqual(l.__dict__, d)

    # Test that we get the same encoder when we construct it using radius
    #  instead of n
    l = ScalarEncoder(name="scalar", radius=1.5, w=3, minval=1, maxval=8,
                      periodic=True, forced=True)
    self.assertEqual(l.__dict__, d)



  def testDecodeAndResolution(self):
    """Test the input description generation, top-down compute, and bucket
    support on a periodic encoder
    """
    l = self._l
    v = l.minval
    while v < l.maxval:
      output = l.encode(v)
      decoded = l.decode(output)

      (fieldsDict, fieldNames) = decoded
      self.assertEqual(len(fieldsDict), 1)
      self.assertEqual(len(fieldNames), 1)
      self.assertEqual(fieldNames, fieldsDict.keys())
      (ranges, _) = fieldsDict.values()[0]
      self.assertEqual(len(ranges), 1)
      (rangeMin, rangeMax) = ranges[0]
      self.assertEqual(rangeMin, rangeMax)
      self.assertLess(abs(rangeMin - v), l.resolution)

      topDown = l.topDownCompute(output)[0]

      self.assertTrue(numpy.array_equal(topDown.encoding, output))
      self.assertLessEqual(abs(topDown.value - v), l.resolution / 2)

      # Test bucket support
      bucketIndices = l.getBucketIndices(v)
      topDown = l.getBucketInfo(bucketIndices)[0]
      self.assertLessEqual(abs(topDown.value - v), l.resolution / 2)
      self.assertEqual(topDown.value, l.getBucketValues()[bucketIndices[0]])
      self.assertEqual(topDown.scalar, topDown.value)
      self.assertTrue(numpy.array_equal(topDown.encoding, output))

      # Next value
      v += l.resolution / 4

    # -----------------------------------------------------------------------
    # Test the input description generation on a large number, periodic encoder
    l = ScalarEncoder(name='scalar', radius=1.5, w=3, minval=1, maxval=8,
                      periodic=True, forced=True)

    # Test with a "hole"
    decoded = l.decode(numpy.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0]))
    (fieldsDict, fieldNames) = decoded
    self.assertEqual(len(fieldsDict), 1)
    (ranges, _) = fieldsDict.values()[0]
    self.assertEqual(len(ranges), 1)
    self.assertTrue(numpy.array_equal(ranges[0], [7.5, 7.5]))

    # Test with something wider than w, and with a hole, and wrapped
    decoded = l.decode(numpy.array([1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0]))
    (fieldsDict, fieldNames) = decoded
    self.assertEqual(len(fieldsDict), 1)
    (ranges, _) = fieldsDict.values()[0]
    self.assertEqual(len(ranges), 2)
    self.assertTrue(numpy.array_equal(ranges[0], [7.5, 8]))
    self.assertTrue(numpy.array_equal(ranges[1], [1, 1]))

    # Test with something wider than w, no hole
    decoded = l.decode(numpy.array([1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]))
    (fieldsDict, fieldNames) = decoded
    self.assertEqual(len(fieldsDict), 1)
    (ranges, _) = fieldsDict.values()[0]
    self.assertEqual(len(ranges), 1)
    self.assertTrue(numpy.array_equal(ranges[0], [1.5, 2.5]))

    # Test with 2 ranges
    decoded = l.decode(numpy.array([1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0]))
    (fieldsDict, fieldNames) = decoded
    self.assertEqual(len(fieldsDict), 1)
    (ranges, _) = fieldsDict.values()[0]
    self.assertEqual(len(ranges), 2)
    self.assertTrue(numpy.array_equal(ranges[0], [1.5, 1.5]))
    self.assertTrue(numpy.array_equal(ranges[1], [5.5, 6.0]))

    # Test with 2 ranges, 1 of which is narrower than w
    decoded = l.decode(numpy.array([0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0]))
    (fieldsDict, fieldNames) = decoded
    self.assertEqual(len(fieldsDict), 1)
    (ranges, _) = fieldsDict.values()[0]
    self.assertTrue(len(ranges), 2)
    self.assertTrue(numpy.array_equal(ranges[0], [1.5, 1.5]))
    self.assertTrue(numpy.array_equal(ranges[1], [5.5, 6.0]))


  def testCloseness(self):
    """Test closenessScores for a periodic encoder"""
    encoder = ScalarEncoder(w=7, minval=0, maxval=7, radius=1, periodic=True,
                            name="day of week", forced=True)
    scores = encoder.closenessScores((2, 4, 7), (4, 2, 1), fractional=False)
    for actual, score in itertools.izip((2, 2, 1), scores):
      self.assertEqual(actual, score)


  def testNonPeriodicBottomUp(self):
    """Test Non-periodic encoder bottom-up"""
    l = ScalarEncoder(name="scalar", n=14, w=5, minval=1, maxval=10,
                      periodic=False, forced=True)
    self.assertTrue(numpy.array_equal(
      l.encode(1),
      numpy.array([1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                  dtype=defaultDtype)))
    self.assertTrue(numpy.array_equal(
      l.encode(2),
      numpy.array([0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                  dtype=defaultDtype)))
    self.assertTrue(numpy.array_equal(
      l.encode(10),
      numpy.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
                  dtype=defaultDtype)))

    # Test that we get the same encoder when we construct it using resolution
    #  instead of n
    d = l.__dict__
    l = ScalarEncoder(name="scalar", resolution=1, w=5, minval=1, maxval=10,
                       periodic=False, forced=True)
    self.assertEqual(l.__dict__, d)

    # Test that we get the same encoder when we construct it using radius
    #  instead of n
    l = ScalarEncoder(name="scalar", radius=5, w=5, minval=1, maxval=10,
                      periodic=False, forced=True)
    self.assertEqual(l.__dict__, d)

    # -------------------------------------------------------------------------
    # Test the input description generation and topDown decoding of a
    # non-periodic encoder
    v = l.minval
    while v < l.maxval:
      output = l.encode(v)
      decoded = l.decode(output)

      (fieldsDict, _) = decoded
      self.assertEqual(len(fieldsDict), 1)
      (ranges, _) = fieldsDict.values()[0]
      self.assertEqual(len(ranges), 1)
      (rangeMin, rangeMax) = ranges[0]
      self.assertEqual(rangeMin, rangeMax)
      self.assertLess(abs(rangeMin - v), l.resolution)

      topDown = l.topDownCompute(output)[0]
      self.assertTrue(numpy.array_equal(topDown.encoding, output))
      self.assertLessEqual(abs(topDown.value - v), l.resolution)

      # Test bucket support
      bucketIndices = l.getBucketIndices(v)
      topDown = l.getBucketInfo(bucketIndices)[0]
      self.assertLessEqual(abs(topDown.value - v), l.resolution / 2)
      self.assertEqual(topDown.scalar, topDown.value)
      self.assertTrue(numpy.array_equal(topDown.encoding, output))

      # Next value
      v += l.resolution / 4


    # Make sure we can fill in holes
    decoded = l.decode(numpy.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1]))
    (fieldsDict, _) = decoded
    self.assertEqual(len(fieldsDict), 1)
    (ranges, _) = fieldsDict.values()[0]
    self.assertEqual(len(ranges), 1)
    self.assertTrue(numpy.array_equal(ranges[0], [10, 10]))

    decoded = l.decode(numpy.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1]))
    (fieldsDict, _) = decoded
    self.assertEqual(len(fieldsDict), 1)
    (ranges, _) = fieldsDict.values()[0]
    self.assertEqual(len(ranges), 1)
    self.assertTrue(numpy.array_equal(ranges[0], [10, 10]))

    #Test min and max
    l = ScalarEncoder(name="scalar", n=14, w=3, minval=1, maxval=10,
                      periodic=False, forced=True)
    decoded = l.topDownCompute(
      numpy.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1]))[0]
    self.assertEqual(decoded.value, 10)
    decoded = l.topDownCompute(
      numpy.array([1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))[0]
    self.assertEqual(decoded.value, 1)

    #Make sure only the last and first encoding encodes to max and min, and
    #there is no value greater than max or min
    l = ScalarEncoder(name="scalar", n=140, w=3, minval=1, maxval=141,
                      periodic=False, forced=True)
    for i in range(137):
      iterlist = [0 for _ in range(140)]
      for j in range(i, i+3):
        iterlist[j] =1
      npar = numpy.array(iterlist)
      decoded = l.topDownCompute(npar)[0]
      self.assertLessEqual(decoded.value, 141)
      self.assertGreaterEqual(decoded.value, 1)
      self.assertTrue(decoded.value < 141 or i==137)
      self.assertTrue(decoded.value > 1 or i == 0)

    # -------------------------------------------------------------------------
    # Test the input description generation and top-down compute on a small
    # number non-periodic encoder
    l = ScalarEncoder(name="scalar", n=15, w=3, minval=.001, maxval=.002,
                      periodic=False, forced=True)
    v = l.minval
    while v < l.maxval:
      output = l.encode(v)
      decoded = l.decode(output)

      (fieldsDict, _) = decoded
      self.assertEqual(len(fieldsDict), 1)
      (ranges, _) = fieldsDict.values()[0]
      self.assertEqual(len(ranges), 1)
      (rangeMin, rangeMax) = ranges[0]
      self.assertEqual(rangeMin, rangeMax)
      self.assertLess(abs(rangeMin - v), l.resolution)

      topDown = l.topDownCompute(output)[0].value
      self.assertLessEqual(abs(topDown - v), l.resolution / 2)
      v += l.resolution / 4


    # -------------------------------------------------------------------------
    # Test the input description generation on a large number, non-periodic
    # encoder
    l = ScalarEncoder(name="scalar", n=15, w=3, minval=1, maxval=1000000000,
                      periodic=False, forced=True)
    v = l.minval
    while v < l.maxval:
      output = l.encode(v)
      decoded = l.decode(output)

      (fieldsDict, _) = decoded
      self.assertEqual(len(fieldsDict), 1)
      (ranges, _) = fieldsDict.values()[0]
      self.assertEqual(len(ranges), 1)
      (rangeMin, rangeMax) = ranges[0]
      self.assertEqual(rangeMin, rangeMax)
      self.assertLess(abs(rangeMin - v), l.resolution)

      topDown = l.topDownCompute(output)[0].value
      self.assertLessEqual(abs(topDown - v), l.resolution / 2)
      v += l.resolution / 4


  def testEncodeInvalidInputType(self):
    encoder = ScalarEncoder(name="enc", n=14, w=3, minval=1, maxval=8,
                            periodic=False, forced=True)
    with self.assertRaises(TypeError):
      encoder.encode("String")


  def testGetBucketInfoIntResolution(self):
    """Ensures that passing resolution as an int doesn't truncate values."""
    encoder = ScalarEncoder(w=3, resolution=1, minval=1, maxval=8,
                            periodic=True, forced=True)
    self.assertEqual(4.5,
                     encoder.topDownCompute(encoder.encode(4.5))[0].scalar)


  @unittest.skipUnless(
      capnp, "pycapnp is not installed, skipping serialization test.")
  def testReadWrite(self):
    """Test ScalarEncoder Cap'n Proto serialization implementation."""
    originalValue = self._l.encode(1)

    proto1 = ScalarEncoderProto.new_message()
    self._l.write(proto1)

    # Write the proto to a temp file and read it back into a new proto
    with tempfile.TemporaryFile() as f:
      proto1.write(f)
      f.seek(0)
      proto2 = ScalarEncoderProto.read(f)

    encoder = ScalarEncoder.read(proto2)

    self.assertIsInstance(encoder, ScalarEncoder)
    self.assertEqual(encoder.w, self._l.w)
    self.assertEqual(encoder.minval, self._l.minval)
    self.assertEqual(encoder.maxval, self._l.maxval)
    self.assertEqual(encoder.periodic, self._l.periodic)
    self.assertEqual(encoder.n, self._l.n)
    self.assertEqual(encoder.radius, self._l.radius)
    self.assertEqual(encoder.resolution, self._l.resolution)
    self.assertEqual(encoder.name, self._l.name)
    self.assertEqual(encoder.verbosity, self._l.verbosity)
    self.assertEqual(encoder.clipInput, self._l.clipInput)
    self.assertTrue(numpy.array_equal(encoder.encode(1), originalValue))
    self.assertEqual(self._l.decode(encoder.encode(1)),
                     encoder.decode(self._l.encode(1)))

    # Feed in a new value and ensure the encodings match
    result1 = self._l.encode(7)
    result2 = encoder.encode(7)
    self.assertTrue(numpy.array_equal(result1, result2))


  def testSettingNWithMaxvalMinvalNone(self):
    """Setting n when maxval/minval = None creates instance."""
    encoder = ScalarEncoder(3, None, None, name="scalar",
                            n=14, radius=0, resolution=0, forced=True)
    self.assertIsInstance(encoder, ScalarEncoder)


  def testSettingScalarAndResolution(self):
    """Setting both scalar and resolution not allowed."""
    with self.assertRaises(ValueError):
      ScalarEncoder(3, None, None, name="scalar", n=0, radius=None,
                    resolution=0.5, forced=True)


  def testSettingRadiusWithMaxvalMinvalNone(self):
    """If radius when maxval/minval = None creates instance."""
    encoder = ScalarEncoder(3, None, None, name="scalar",
                            n=0, radius=1.5, resolution=0, forced=True)
    self.assertIsInstance(encoder, ScalarEncoder)



if __name__ == "__main__":
  unittest.main()
