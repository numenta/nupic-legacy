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

from cStringIO import StringIO
import sys
import tempfile
import unittest2 as unittest
import numpy

from nupic.encoders.base import defaultDtype
from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
from nupic.data.field_meta import FieldMetaType
from nupic.support.unittesthelpers.algorithm_test_helpers import getSeed
from nupic.encoders import RandomDistributedScalarEncoder

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.encoders.random_distributed_scalar_capnp import (
    RandomDistributedScalarEncoderProto
  )



# Disable warnings about accessing protected members
# pylint: disable=W0212



def computeOverlap(x, y):
  """
  Given two binary arrays, compute their overlap. The overlap is the number
  of bits where x[i] and y[i] are both 1
  """
  return (x & y).sum()



def validateEncoder(encoder, subsampling):
  """
  Given an encoder, calculate overlaps statistics and ensure everything is ok.
  We don't check every possible combination for speed reasons.
  """
  for i in range(encoder.minIndex, encoder.maxIndex+1, 1):
    for j in range(i+1, encoder.maxIndex+1, subsampling):
      if not encoder._overlapOK(i, j):
        return False

  return True



class RandomDistributedScalarEncoderTest(unittest.TestCase):
  """
  Unit tests for RandomDistributedScalarEncoder class.
  """

  def testEncoding(self):
    """
    Test basic encoding functionality. Create encodings without crashing and
    check they contain the correct number of on and off bits. Check some
    encodings for expected overlap. Test that encodings for old values don't
    change once we generate new buckets.
    """
    # Initialize with non-default parameters and encode with a number close to
    # the offset
    encoder = RandomDistributedScalarEncoder(name="encoder", resolution=1.0,
                                             w=23, n=500, offset=0.0)
    e0 = encoder.encode(-0.1)

    self.assertEqual(e0.sum(), 23, "Number of on bits is incorrect")
    self.assertEqual(e0.size, 500, "Width of the vector is incorrect")
    self.assertEqual(encoder.getBucketIndices(0.0)[0], encoder._maxBuckets / 2,
                     "Offset doesn't correspond to middle bucket")
    self.assertEqual(len(encoder.bucketMap), 1, "Number of buckets is not 1")

    # Encode with a number that is resolution away from offset. Now we should
    # have two buckets and this encoding should be one bit away from e0
    e1 = encoder.encode(1.0)
    self.assertEqual(len(encoder.bucketMap), 2, "Number of buckets is not 2")
    self.assertEqual(e1.sum(), 23, "Number of on bits is incorrect")
    self.assertEqual(e1.size, 500, "Width of the vector is incorrect")
    self.assertEqual(computeOverlap(e0, e1), 22, "Overlap is not equal to w-1")

    # Encode with a number that is resolution*w away from offset. Now we should
    # have many buckets and this encoding should have very little overlap with
    # e0
    e25 = encoder.encode(25.0)
    self.assertGreater(len(encoder.bucketMap), 23,
                       "Number of buckets is not 2")
    self.assertEqual(e25.sum(), 23, "Number of on bits is incorrect")
    self.assertEqual(e25.size, 500, "Width of the vector is incorrect")
    self.assertLess(computeOverlap(e0, e25), 4, "Overlap is too high")

    # Test encoding consistency. The encodings for previous numbers
    # shouldn't change even though we have added additional buckets
    self.assertTrue(numpy.array_equal(e0, encoder.encode(-0.1)),
      "Encodings are not consistent - they have changed after new buckets "
      "have been created")
    self.assertTrue(numpy.array_equal(e1, encoder.encode(1.0)),
      "Encodings are not consistent - they have changed after new buckets "
      "have been created")



  def testMissingValues(self):
    """
    Test that missing values and NaN return all zero's.
    """
    encoder = RandomDistributedScalarEncoder(name="encoder", resolution=1.0)
    empty = encoder.encode(SENTINEL_VALUE_FOR_MISSING_DATA)
    self.assertEqual(empty.sum(), 0)

    empty = encoder.encode(float("nan"))
    self.assertEqual(empty.sum(), 0)


  def testResolution(self):
    """
    Test that numbers within the same resolution return the same encoding.
    Numbers outside the resolution should return different encodings.
    """
    encoder = RandomDistributedScalarEncoder(name="encoder", resolution=1.0)

    # Since 23.0 is the first encoded number, it will be the offset.
    # Since resolution is 1, 22.9 and 23.4 should have the same bucket index and
    # encoding.
    e23   = encoder.encode(23.0)
    e23p1 = encoder.encode(23.1)
    e22p9 = encoder.encode(22.9)
    e24   = encoder.encode(24.0)
    self.assertEqual(e23.sum(), encoder.w)
    self.assertEqual((e23 == e23p1).sum(), encoder.getWidth(),
      "Numbers within resolution don't have the same encoding")
    self.assertEqual((e23 == e22p9).sum(), encoder.getWidth(),
      "Numbers within resolution don't have the same encoding")
    self.assertNotEqual((e23 == e24).sum(), encoder.getWidth(),
      "Numbers outside resolution have the same encoding")

    e22p9 = encoder.encode(22.5)
    self.assertNotEqual((e23 == e22p9).sum(), encoder.getWidth(),
      "Numbers outside resolution have the same encoding")


  def testMapBucketIndexToNonZeroBits(self):
    """
    Test that mapBucketIndexToNonZeroBits works and that max buckets and
    clipping are handled properly.
    """
    encoder = RandomDistributedScalarEncoder(resolution=1.0, w=11, n=150)
    # Set a low number of max buckets
    encoder._initializeBucketMap(10, None)
    encoder.encode(0.0)
    encoder.encode(-7.0)
    encoder.encode(7.0)

    self.assertEqual(len(encoder.bucketMap), encoder._maxBuckets,
      "_maxBuckets exceeded")
    self.assertTrue(
      numpy.array_equal(encoder.mapBucketIndexToNonZeroBits(-1),
                        encoder.bucketMap[0]),
                        "mapBucketIndexToNonZeroBits did not handle negative"
                        " index")
    self.assertTrue(
      numpy.array_equal(encoder.mapBucketIndexToNonZeroBits(1000),
                        encoder.bucketMap[9]),
      "mapBucketIndexToNonZeroBits did not handle negative index")

    e23 = encoder.encode(23.0)
    e6  = encoder.encode(6)
    self.assertEqual((e23 == e6).sum(), encoder.getWidth(),
      "Values not clipped correctly during encoding")

    ep8 = encoder.encode(-8)
    ep7  = encoder.encode(-7)
    self.assertEqual((ep8 == ep7).sum(), encoder.getWidth(),
      "Values not clipped correctly during encoding")

    self.assertEqual(encoder.getBucketIndices(-8)[0], 0,
                     "getBucketIndices returned negative bucket index")
    self.assertEqual(encoder.getBucketIndices(23)[0], encoder._maxBuckets-1,
                     "getBucketIndices returned bucket index that is too"
                     " large")


  def testParameterChecks(self):
    """
    Test that some bad construction parameters get handled.
    """
    # n must be >= 6*w
    with self.assertRaises(ValueError):
      RandomDistributedScalarEncoder(name="mv", resolution=1.0, n=int(5.9*21))

    # n must be an int
    with self.assertRaises(ValueError):
      RandomDistributedScalarEncoder(name="mv", resolution=1.0, n=5.9*21)

    # w can't be negative
    with self.assertRaises(ValueError):
      RandomDistributedScalarEncoder(name="mv", resolution=1.0, w=-1)

    # resolution can't be negative
    with self.assertRaises(ValueError):
      RandomDistributedScalarEncoder(name="mv", resolution=-2)


  def testOverlapStatistics(self):
    """
    Check that the overlaps for the encodings are within the expected range.
    Here we ask the encoder to create a bunch of representations under somewhat
    stressful conditions, and then verify they are correct. We rely on the fact
    that the _overlapOK and _countOverlapIndices methods are working correctly.
    """
    seed = getSeed()

    # Generate about 600 encodings. Set n relatively low to increase
    # chance of false overlaps
    encoder = RandomDistributedScalarEncoder(resolution=1.0, w=11, n=150,
                                             seed=seed)
    encoder.encode(0.0)
    encoder.encode(-300.0)
    encoder.encode(300.0)
    self.assertTrue(validateEncoder(encoder, subsampling=3),
                    "Illegal overlap encountered in encoder")


  def testGetMethods(self):
    """
    Test that the getWidth, getDescription, and getDecoderOutputFieldTypes
    methods work.
    """
    encoder = RandomDistributedScalarEncoder(name="theName", resolution=1.0, n=500)
    self.assertEqual(encoder.getWidth(), 500,
                     "getWidth doesn't return the correct result")

    self.assertEqual(encoder.getDescription(), [("theName", 0)],
                     "getDescription doesn't return the correct result")

    self.assertEqual(encoder.getDecoderOutputFieldTypes(),
                     (FieldMetaType.float, ),
                     "getDecoderOutputFieldTypes doesn't return the correct"
                     " result")


  def testOffset(self):
    """
    Test that offset is working properly
    """
    encoder = RandomDistributedScalarEncoder(name="encoder", resolution=1.0)
    encoder.encode(23.0)
    self.assertEqual(encoder._offset, 23.0,
              "Offset not specified and not initialized to first input")

    encoder = RandomDistributedScalarEncoder(name="encoder", resolution=1.0,
                                             offset=25.0)
    encoder.encode(23.0)
    self.assertEqual(encoder._offset, 25.0,
                     "Offset not initialized to specified constructor"
                     " parameter")


  def testSeed(self):
    """
    Test that initializing twice with the same seed returns identical encodings
    and different when not specified
    """
    encoder1 = RandomDistributedScalarEncoder(name="encoder1", resolution=1.0,
                                              seed=42)
    encoder2 = RandomDistributedScalarEncoder(name="encoder2", resolution=1.0,
                                              seed=42)
    encoder3 = RandomDistributedScalarEncoder(name="encoder3", resolution=1.0,
                                              seed=-1)
    encoder4 = RandomDistributedScalarEncoder(name="encoder4", resolution=1.0,
                                              seed=-1)

    e1 = encoder1.encode(23.0)
    e2 = encoder2.encode(23.0)
    e3 = encoder3.encode(23.0)
    e4 = encoder4.encode(23.0)

    self.assertEqual((e1 == e2).sum(), encoder1.getWidth(),
        "Same seed gives rise to different encodings")

    self.assertNotEqual((e1 == e3).sum(), encoder1.getWidth(),
        "Different seeds gives rise to same encodings")

    self.assertNotEqual((e3 == e4).sum(), encoder1.getWidth(),
        "seeds of -1 give rise to same encodings")


  def testCountOverlapIndices(self):
    """
    Test that the internal method _countOverlapIndices works as expected.
    """
    # Create a fake set of encodings.
    encoder = RandomDistributedScalarEncoder(name="encoder", resolution=1.0,
                                             w=5, n=5*20)
    midIdx = encoder._maxBuckets/2
    encoder.bucketMap[midIdx-2] = numpy.array(range(3, 8))
    encoder.bucketMap[midIdx-1] = numpy.array(range(4, 9))
    encoder.bucketMap[midIdx]   = numpy.array(range(5, 10))
    encoder.bucketMap[midIdx+1] = numpy.array(range(6, 11))
    encoder.bucketMap[midIdx+2] = numpy.array(range(7, 12))
    encoder.bucketMap[midIdx+3] = numpy.array(range(8, 13))
    encoder.minIndex = midIdx - 2
    encoder.maxIndex = midIdx + 3

    # Indices must exist
    with self.assertRaises(ValueError):
      encoder._countOverlapIndices(midIdx-3, midIdx-2)
    with self.assertRaises(ValueError):
      encoder._countOverlapIndices(midIdx-2, midIdx-3)

    # Test some overlaps
    self.assertEqual(encoder._countOverlapIndices(midIdx-2, midIdx-2), 5,
                     "_countOverlapIndices didn't work")
    self.assertEqual(encoder._countOverlapIndices(midIdx-1, midIdx-2), 4,
                     "_countOverlapIndices didn't work")
    self.assertEqual(encoder._countOverlapIndices(midIdx+1, midIdx-2), 2,
                     "_countOverlapIndices didn't work")
    self.assertEqual(encoder._countOverlapIndices(midIdx-2, midIdx+3), 0,
                     "_countOverlapIndices didn't work")


  def testOverlapOK(self):
    """
    Test that the internal method _overlapOK works as expected.
    """
    # Create a fake set of encodings.
    encoder = RandomDistributedScalarEncoder(name="encoder", resolution=1.0,
                                             w=5, n=5*20)
    midIdx = encoder._maxBuckets/2
    encoder.bucketMap[midIdx-3] = numpy.array(range(4, 9)) # Not ok with
                                                           # midIdx-1
    encoder.bucketMap[midIdx-2] = numpy.array(range(3, 8))
    encoder.bucketMap[midIdx-1] = numpy.array(range(4, 9))
    encoder.bucketMap[midIdx]   = numpy.array(range(5, 10))
    encoder.bucketMap[midIdx+1] = numpy.array(range(6, 11))
    encoder.bucketMap[midIdx+2] = numpy.array(range(7, 12))
    encoder.bucketMap[midIdx+3] = numpy.array(range(8, 13))
    encoder.minIndex = midIdx - 3
    encoder.maxIndex = midIdx + 3

    self.assertTrue(encoder._overlapOK(midIdx, midIdx-1),
                    "_overlapOK didn't work")
    self.assertTrue(encoder._overlapOK(midIdx-2, midIdx+3),
                    "_overlapOK didn't work")
    self.assertFalse(encoder._overlapOK(midIdx-3, midIdx-1),
                    "_overlapOK didn't work")

    # We'll just use our own numbers
    self.assertTrue(encoder._overlapOK(100, 50, 0),
                    "_overlapOK didn't work for far values")
    self.assertTrue(encoder._overlapOK(100, 50, encoder._maxOverlap),
                    "_overlapOK didn't work for far values")
    self.assertFalse(encoder._overlapOK(100, 50, encoder._maxOverlap+1),
                     "_overlapOK didn't work for far values")
    self.assertTrue(encoder._overlapOK(50, 50, 5),
                    "_overlapOK didn't work for near values")
    self.assertTrue(encoder._overlapOK(48, 50, 3),
                    "_overlapOK didn't work for near values")
    self.assertTrue(encoder._overlapOK(46, 50, 1),
                    "_overlapOK didn't work for near values")
    self.assertTrue(encoder._overlapOK(45, 50, encoder._maxOverlap),
                    "_overlapOK didn't work for near values")
    self.assertFalse(encoder._overlapOK(48, 50, 4),
                     "_overlapOK didn't work for near values")
    self.assertFalse(encoder._overlapOK(48, 50, 2),
                     "_overlapOK didn't work for near values")
    self.assertFalse(encoder._overlapOK(46, 50, 2),
                     "_overlapOK didn't work for near values")
    self.assertFalse(encoder._overlapOK(50, 50, 6),
                     "_overlapOK didn't work for near values")


  def testCountOverlap(self):
    """
    Test that the internal method _countOverlap works as expected.
    """
    encoder = RandomDistributedScalarEncoder(name="encoder", resolution=1.0,
                                             n=500)

    r1 = numpy.array([1, 2, 3, 4, 5, 6])
    r2 = numpy.array([1, 2, 3, 4, 5, 6])
    self.assertEqual(encoder._countOverlap(r1, r2), 6,
                     "_countOverlap result is incorrect")

    r1 = numpy.array([1, 2, 3, 4, 5, 6])
    r2 = numpy.array([1, 2, 3, 4, 5, 7])
    self.assertEqual(encoder._countOverlap(r1, r2), 5,
                     "_countOverlap result is incorrect")

    r1 = numpy.array([1, 2, 3, 4, 5, 6])
    r2 = numpy.array([6, 5, 4, 3, 2, 1])
    self.assertEqual(encoder._countOverlap(r1, r2), 6,
                     "_countOverlap result is incorrect")

    r1 = numpy.array([1, 2, 8, 4, 5, 6])
    r2 = numpy.array([1, 2, 3, 4, 9, 6])
    self.assertEqual(encoder._countOverlap(r1, r2), 4,
                     "_countOverlap result is incorrect")

    r1 = numpy.array([1, 2, 3, 4, 5, 6])
    r2 = numpy.array([1, 2, 3])
    self.assertEqual(encoder._countOverlap(r1, r2), 3,
                     "_countOverlap result is incorrect")

    r1 = numpy.array([7, 8, 9, 10, 11, 12])
    r2 = numpy.array([1, 2, 3, 4, 5, 6])
    self.assertEqual(encoder._countOverlap(r1, r2), 0,
                     "_countOverlap result is incorrect")


  def testVerbosity(self):
    """
    Test that nothing is printed out when verbosity=0
    """
    _stdout = sys.stdout
    sys.stdout = _stringio = StringIO()
    encoder = RandomDistributedScalarEncoder(name="mv", resolution=1.0,
                                             verbosity=0)
    output = numpy.zeros(encoder.getWidth(), dtype=defaultDtype)
    encoder.encodeIntoArray(23.0, output)
    encoder.getBucketIndices(23.0)
    sys.stdout = _stdout
    self.assertEqual(len(_stringio.getvalue()), 0,
                     "zero verbosity doesn't lead to zero output")


  def testEncodeInvalidInputType(self):
    encoder = RandomDistributedScalarEncoder(name="encoder", resolution=1.0,
                                             verbosity=0)
    with self.assertRaises(TypeError):
      encoder.encode("String")


  @unittest.skipUnless(
      capnp, "pycapnp is not installed, skipping serialization test.")
  def testWriteRead(self):
    original = RandomDistributedScalarEncoder(
        name="encoder", resolution=1.0, w=23, n=500, offset=0.0)

    originalValue = original.encode(1)

    proto1 = RandomDistributedScalarEncoderProto.new_message()
    original.write(proto1)

    # Write the proto to a temp file and read it back into a new proto
    with tempfile.TemporaryFile() as f:
      proto1.write(f)
      f.seek(0)
      proto2 = RandomDistributedScalarEncoderProto.read(f)

    encoder = RandomDistributedScalarEncoder.read(proto2)

    self.assertIsInstance(encoder, RandomDistributedScalarEncoder)
    self.assertEqual(encoder.resolution, original.resolution)
    self.assertEqual(encoder.w, original.w)
    self.assertEqual(encoder.n, original.n)
    self.assertEqual(encoder.name, original.name)
    self.assertEqual(encoder.verbosity, original.verbosity)
    self.assertEqual(encoder.minIndex, original.minIndex)
    self.assertEqual(encoder.maxIndex, original.maxIndex)
    encodedFromOriginal = original.encode(1)
    encodedFromNew = encoder.encode(1)
    self.assertTrue(numpy.array_equal(encodedFromNew, originalValue))
    self.assertEqual(original.decode(encodedFromNew),
                     encoder.decode(encodedFromOriginal))
    self.assertEqual(original.random.getSeed(), encoder.random.getSeed())

    for key, value in original.bucketMap.items():
      self.assertTrue(numpy.array_equal(value, encoder.bucketMap[key]))



if __name__ == "__main__":
  unittest.main()
