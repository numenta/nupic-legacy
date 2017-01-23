# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
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

import tempfile
import unittest

import numpy

from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
from nupic.encoders.adaptivescalar import AdaptiveScalarEncoder
from nupic.encoders.base import defaultDtype

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.encoders.adaptivescalar_capnp import AdaptiveScalarEncoderProto



class AdaptiveScalarTest(unittest.TestCase):
  """Tests for AdaptiveScalarEncoder"""


  def setUp(self):
    # forced: it's strongly recommended to use w>=21, in the example we force
    # skip the check for readibility
    self._l = AdaptiveScalarEncoder(name="scalar", n=14, w=5, minval=1,
                                    maxval=10, periodic=False, forced=True)

  def testMissingValues(self):
    """missing values"""
    # forced: it's strongly recommended to use w>=21, in the example we force
    # skip the check for readib.
    mv = AdaptiveScalarEncoder(name="mv", n=14, w=3, minval=1, maxval=8,
                               periodic=False, forced=True)
    empty = mv.encode(SENTINEL_VALUE_FOR_MISSING_DATA)
    self.assertEqual(empty.sum(), 0)


  def testNonPeriodicEncoderMinMaxSpec(self):
    """Non-periodic encoder, min and max specified"""

    self.assertTrue(numpy.array_equal(
      self._l.encode(1),
      numpy.array([1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                  dtype=defaultDtype)))
    self.assertTrue(numpy.array_equal(
      self._l.encode(2),
      numpy.array([0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                  dtype=defaultDtype)))
    self.assertTrue(numpy.array_equal(
      self._l.encode(10),
      numpy.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
                  dtype=defaultDtype)))


  def testTopDownDecode(self):
    """Test the input description generation and topDown decoding"""
    l = self._l
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
      self.assertLessEqual(abs(topDown.value - v), l.resolution)

      # Test bucket support
      bucketIndices = l.getBucketIndices(v)
      topDown = l.getBucketInfo(bucketIndices)[0]
      self.assertLessEqual(abs(topDown.value - v), l.resolution / 2)
      self.assertEqual(topDown.value, l.getBucketValues()[bucketIndices[0]])
      self.assertEqual(topDown.scalar, topDown.value)
      self.assertTrue(numpy.array_equal(topDown.encoding, output))

      # Next value
      v += l.resolution / 4


  def testFillHoles(self):
    """Make sure we can fill in holes"""
    l=self._l
    decoded = l.decode(numpy.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1]))
    (fieldsDict, _) = decoded
    self.assertEqual(len(fieldsDict), 1)

    (ranges, _) = fieldsDict.values()[0]
    self.assertEqual(len(ranges), 1)
    self.assertSequenceEqual(ranges[0], [10, 10])

    decoded = l.decode(numpy.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1]))
    (fieldsDict, _) = decoded
    self.assertEqual(len(fieldsDict), 1)
    (ranges, _) = fieldsDict.values()[0]
    self.assertEqual(len(ranges), 1)
    self.assertSequenceEqual(ranges[0], [10, 10])


  def testNonPeriodicEncoderMinMaxNotSpec(self):
    """Non-periodic encoder, min and max not specified"""
    l = AdaptiveScalarEncoder(name="scalar", n=14, w=5, minval=None,
                              maxval=None, periodic=False, forced=True)

    def _verify(v, encoded, expV=None):
      if expV is None:
        expV = v

      self.assertTrue(numpy.array_equal(
        l.encode(v),
        numpy.array(encoded, dtype=defaultDtype)))
      self.assertLessEqual(
        abs(l.getBucketInfo(l.getBucketIndices(v))[0].value - expV),
        l.resolution/2)

    def _verifyNot(v, encoded):
      self.assertFalse(numpy.array_equal(
        l.encode(v), numpy.array(encoded, dtype=defaultDtype)))

    _verify(1, [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    _verify(2, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    _verify(10, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    _verify(3, [0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0])
    _verify(-9, [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    _verify(-8, [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    _verify(-7, [0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    _verify(-6, [0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    _verify(-5, [0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0])
    _verify(0, [0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0])
    _verify(8, [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0])
    _verify(8, [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0])
    _verify(10, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    _verify(11, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    _verify(12, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    _verify(13, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    _verify(14, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    _verify(15, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1])


    #"""Test switching learning off"""
    l = AdaptiveScalarEncoder(name="scalar", n=14, w=5, minval=1, maxval=10,
                              periodic=False, forced=True)
    _verify(1, [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    _verify(10, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    _verify(20, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    _verify(10, [0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0])

    l.setLearning(False)
    _verify(30, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1], expV=20)
    _verify(20, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    _verify(-10, [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0], expV=1)
    _verify(-1, [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0], expV=1)

    l.setLearning(True)
    _verify(30, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    _verifyNot(20, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    _verify(-10, [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    _verifyNot(-1, [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0])


  def testSetFieldStats(self):
    """Test setting the min and max using setFieldStats"""
    def _dumpParams(enc):
      return (enc.n, enc.w, enc.minval, enc.maxval, enc.resolution,
              enc._learningEnabled, enc.recordNum,
              enc.radius, enc.rangeInternal, enc.padding, enc.nInternal)
    sfs = AdaptiveScalarEncoder(name='scalar', n=14, w=5, minval=1, maxval=10,
                              periodic=False, forced=True)
    reg = AdaptiveScalarEncoder(name='scalar', n=14, w=5, minval=1, maxval=100,
                              periodic=False, forced=True)
    self.assertNotEqual(_dumpParams(sfs), _dumpParams(reg),
                        ("Params should not be equal, since the two encoders "
                         "were instantiated with different values."))
    # set the min and the max using sFS to 1,100 respectively.
    sfs.setFieldStats("this", {"this":{"min":1, "max":100}})

    #Now the parameters for both should be the same
    self.assertEqual(_dumpParams(sfs), _dumpParams(reg),
                     ("Params should now be equal, but they are not. sFS "
                      "should be equivalent to initialization."))


  @unittest.skipUnless(
      capnp, "pycapnp is not installed, skipping serialization test.")
  def testReadWrite(self):

    originalValue = self._l.encode(1)

    proto1 = AdaptiveScalarEncoderProto.new_message()
    self._l.write(proto1)

    # Write the proto to a temp file and read it back into a new proto
    with tempfile.TemporaryFile() as f:
      proto1.write(f)
      f.seek(0)
      proto2 = AdaptiveScalarEncoderProto.read(f)

    encoder = AdaptiveScalarEncoder.read(proto2)

    self.assertIsInstance(encoder, AdaptiveScalarEncoder)
    self.assertEqual(encoder.recordNum, self._l.recordNum)
    self.assertDictEqual(encoder.slidingWindow.__dict__,
                         self._l.slidingWindow.__dict__)
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



if __name__ == '__main__':
  unittest.main()
