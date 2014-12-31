#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
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

from cStringIO import StringIO
import sys
import unittest2 as unittest
import numpy

from nupic.encoders.base import defaultDtype
from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
from nupic.data.fieldmeta import FieldMetaType
from nupic.support.unittesthelpers.algorithm_test_helpers import getSeed
from nupic.encoders.random_distributed_scalar import (
  RandomDistributedScalarEncoder
  )

# Disable warnings about accessing protected members
# pylint: disable=W0212


def computeOverlap(x, y):
  """
  Given two binary arrays, compute their overlap. The overlap is the number
  of bits where x[i] and y[i] are both 1
  """
  return (x & y).sum()



def validateEncoder(enc, subsampling):
  """
  Given an encoder, calculate overlaps statistics and ensure everything is ok.
  We don't check every possible combination for speed reasons.
  """
  for i in range(enc.minIndex, enc.maxIndex+1, 1):
    for j in range(i+1, enc.maxIndex+1, subsampling):
      if not enc._overlapOK(i, j):
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
    enc = RandomDistributedScalarEncoder(name='enc', resolution=1.0, w=23,
                                         n=500, offset = 0.0)
    e0 = enc.encode(-0.1)
    
    self.assertEqual(e0.sum(), 23, "Number of on bits is incorrect")
    self.assertEqual(e0.size, 500, "Width of the vector is incorrect")
    self.assertEqual(enc.getBucketIndices(0.0)[0], enc._maxBuckets / 2,
                     "Offset doesn't correspond to middle bucket")
    self.assertEqual(len(enc.bucketMap), 1, "Number of buckets is not 1")

    # Encode with a number that is resolution away from offset. Now we should
    # have two buckets and this encoding should be one bit away from e0
    e1 = enc.encode(1.0)
    self.assertEqual(len(enc.bucketMap), 2, "Number of buckets is not 2")
    self.assertEqual(e1.sum(), 23, "Number of on bits is incorrect")
    self.assertEqual(e1.size, 500, "Width of the vector is incorrect")
    self.assertEqual(computeOverlap(e0, e1), 22,
                     "Overlap is not equal to w-1")

    # Encode with a number that is resolution*w away from offset. Now we should
    # have many buckets and this encoding should have very little overlap with
    # e0
    e25 = enc.encode(25.0)
    self.assertGreater(len(enc.bucketMap), 23, "Number of buckets is not 2")
    self.assertEqual(e25.sum(), 23, "Number of on bits is incorrect")
    self.assertEqual(e25.size, 500, "Width of the vector is incorrect")
    self.assertLess(computeOverlap(e0, e25), 4,
                     "Overlap is too high")
    
    # Test encoding consistency. The encodings for previous numbers
    # shouldn't change even though we have added additional buckets
    self.assertEqual((e0 == enc.encode(-0.1)).sum(), 500,
      "Encodings are not consistent - they have changed after new buckets "
      "have been created")
    self.assertEqual((e1 == enc.encode(1.0)).sum(), 500,
      "Encodings are not consistent - they have changed after new buckets "
      "have been created")


  def testMissingValues(self):
    """
    Test that missing values and NaN return all zero's.
    """
    enc = RandomDistributedScalarEncoder(name='enc', resolution=1.0)
    empty = enc.encode(SENTINEL_VALUE_FOR_MISSING_DATA)
    self.assertEqual(empty.sum(), 0)

    empty = enc.encode(float("nan"))
    self.assertEqual(empty.sum(), 0)


  def testResolution(self):
    """
    Test that numbers within the same resolution return the same encoding.
    Numbers outside the resolution should return different encodings.
    """
    enc = RandomDistributedScalarEncoder(name='enc', resolution=1.0)
    
    # Since 23.0 is the first encoded number, it will be the offset.
    # Since resolution is 1, 22.9 and 23.4 should have the same bucket index and
    # encoding.
    e23   = enc.encode(23.0)
    e23_1 = enc.encode(23.1)
    e22_9 = enc.encode(22.9)
    e24   = enc.encode(24.0)
    self.assertEqual(e23.sum(), enc.w)
    self.assertEqual((e23 == e23_1).sum(), enc.getWidth(),
      "Numbers within resolution don't have the same encoding")
    self.assertEqual((e23 == e22_9).sum(), enc.getWidth(),
      "Numbers within resolution don't have the same encoding")
    self.assertNotEqual((e23 == e24).sum(), enc.getWidth(),
      "Numbers outside resolution have the same encoding")

    e22_9 = enc.encode(22.5)
    self.assertNotEqual((e23 == e22_9).sum(), enc.getWidth(),
      "Numbers outside resolution have the same encoding")


  def testMapBucketIndexToNonZeroBits(self):
    """
    Test that mapBucketIndexToNonZeroBits works and that max buckets and
    clipping are handled properly.
    """
    enc = RandomDistributedScalarEncoder(resolution=1.0, w=11, n=150)
    # Set a low number of max buckets
    enc._initializeBucketMap(10, None)
    enc.encode(0.0)
    enc.encode(-7.0)
    enc.encode(7.0)
    
    self.assertEqual(len(enc.bucketMap), enc._maxBuckets,
      "_maxBuckets exceeded")
    self.assertTrue(
      (enc.mapBucketIndexToNonZeroBits(-1) == enc.bucketMap[0]).all(),
      "mapBucketIndexToNonZeroBits did not handle negative index")
    self.assertTrue(
      (enc.mapBucketIndexToNonZeroBits(1000) == enc.bucketMap[9]).all(),
      "mapBucketIndexToNonZeroBits did not handle negative index")

    e23 = enc.encode(23.0)
    e6  = enc.encode(6)
    self.assertEqual((e23 == e6).sum(), enc.getWidth(),
      "Values not clipped correctly during encoding")

    e_8 = enc.encode(-8)
    e_7  = enc.encode(-7)
    self.assertEqual((e_8 == e_7).sum(), enc.getWidth(),
      "Values not clipped correctly during encoding")
    
    self.assertEqual(enc.getBucketIndices(-8)[0], 0,
                "getBucketIndices returned negative bucket index")
    self.assertEqual(enc.getBucketIndices(23)[0], enc._maxBuckets-1,
                "getBucketIndices returned bucket index that is too large")


  def testParameterChecks(self):
    """
    Test that some bad construction parameters get handled.
    """
    # n must be >= 6*w
    with self.assertRaises(ValueError):
      RandomDistributedScalarEncoder(name='mv', resolution=1.0, n=int(5.9*21))

    # n must be an int
    with self.assertRaises(ValueError):
      RandomDistributedScalarEncoder(name='mv', resolution=1.0, n=5.9*21)

    # w can't be negative
    with self.assertRaises(ValueError):
      RandomDistributedScalarEncoder(name='mv', resolution=1.0, w=-1)

    # resolution can't be negative
    with self.assertRaises(ValueError):
      RandomDistributedScalarEncoder(name='mv', resolution=-2)

 
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
    enc = RandomDistributedScalarEncoder(resolution=1.0, w=11, n=150, seed=seed)
    enc.encode(0.0)
    enc.encode(-300.0)
    enc.encode(300.0)
    self.assertTrue(validateEncoder(enc, subsampling=3),
                    "Illegal overlap encountered in encoder")
  
  
  def testGetMethods(self):
    """
    Test that the getWidth, getDescription, and getDecoderOutputFieldTypes
    methods work.
    """
    enc = RandomDistributedScalarEncoder(name='theName', resolution=1.0, n=500)
    self.assertEqual(enc.getWidth(), 500,
                     "getWidth doesn't return the correct result")

    self.assertEqual(enc.getDescription(), [('theName', 0)],
                     "getDescription doesn't return the correct result")
  
    self.assertEqual(enc.getDecoderOutputFieldTypes(),
                (FieldMetaType.float, ),
                "getDecoderOutputFieldTypes doesn't return the correct result")
  
  
  def testOffset(self):
    """
    Test that offset is working properly
    """
    enc = RandomDistributedScalarEncoder(name='enc', resolution=1.0)
    enc.encode(23.0)
    self.assertEqual(enc._offset, 23.0,
              "Offset not specified and not initialized to first input")

    enc = RandomDistributedScalarEncoder(name='enc', resolution=1.0,
                                         offset=25.0)
    enc.encode(23.0)
    self.assertEqual(enc._offset, 25.0,
              "Offset not initialized to specified constructor parameter")
  
  
  def testSeed(self):
    """
    Test that initializing twice with the same seed returns identical encodings
    and different when not specified
    """
    enc1 = RandomDistributedScalarEncoder(name='enc', resolution=1.0, seed=42)
    enc2 = RandomDistributedScalarEncoder(name='enc', resolution=1.0, seed=42)
    enc3 = RandomDistributedScalarEncoder(name='enc', resolution=1.0, seed=-1)
    enc4 = RandomDistributedScalarEncoder(name='enc', resolution=1.0, seed=-1)
    
    e1 = enc1.encode(23.0)
    e2 = enc2.encode(23.0)
    e3 = enc3.encode(23.0)
    e4 = enc4.encode(23.0)
    
    self.assertEqual((e1 == e2).sum(), enc1.getWidth(),
        "Same seed gives rise to different encodings")

    self.assertNotEqual((e1 == e3).sum(), enc1.getWidth(),
        "Different seeds gives rise to same encodings")
  
    self.assertNotEqual((e3 == e4).sum(), enc1.getWidth(),
        "seeds of -1 give rise to same encodings")


  def testCountOverlapIndices(self):
    """
    Test that the internal method _countOverlapIndices works as expected.
    """
    # Create a fake set of encodings.
    enc = RandomDistributedScalarEncoder(name='enc', resolution=1.0, w=5,
                                         n=5*20)
    midIdx = enc._maxBuckets/2
    enc.bucketMap[midIdx-2] = numpy.array(range(3, 8))
    enc.bucketMap[midIdx-1] = numpy.array(range(4, 9))
    enc.bucketMap[midIdx]   = numpy.array(range(5, 10))
    enc.bucketMap[midIdx+1] = numpy.array(range(6, 11))
    enc.bucketMap[midIdx+2] = numpy.array(range(7, 12))
    enc.bucketMap[midIdx+3] = numpy.array(range(8, 13))
    enc.minIndex = midIdx - 2
    enc.maxIndex = midIdx + 3

    # Indices must exist
    with self.assertRaises(ValueError):
      enc._countOverlapIndices(midIdx-3, midIdx-2)
    with self.assertRaises(ValueError):
      enc._countOverlapIndices(midIdx-2, midIdx-3)

    # Test some overlaps
    self.assertEqual(enc._countOverlapIndices(midIdx-2, midIdx-2), 5,
                     "_countOverlapIndices didn't work")
    self.assertEqual(enc._countOverlapIndices(midIdx-1, midIdx-2), 4,
                     "_countOverlapIndices didn't work")
    self.assertEqual(enc._countOverlapIndices(midIdx+1, midIdx-2), 2,
                     "_countOverlapIndices didn't work")
    self.assertEqual(enc._countOverlapIndices(midIdx-2, midIdx+3), 0,
                     "_countOverlapIndices didn't work")


  def testOverlapOK(self):
    """
    Test that the internal method _overlapOK works as expected.
    """
    # Create a fake set of encodings.
    enc = RandomDistributedScalarEncoder(name='enc', resolution=1.0, w=5,
                                         n=5*20)
    midIdx = enc._maxBuckets/2
    enc.bucketMap[midIdx-3] = numpy.array(range(4, 9))  # Not ok with midIdx-1
    enc.bucketMap[midIdx-2] = numpy.array(range(3, 8))
    enc.bucketMap[midIdx-1] = numpy.array(range(4, 9))
    enc.bucketMap[midIdx]   = numpy.array(range(5, 10))
    enc.bucketMap[midIdx+1] = numpy.array(range(6, 11))
    enc.bucketMap[midIdx+2] = numpy.array(range(7, 12))
    enc.bucketMap[midIdx+3] = numpy.array(range(8, 13))
    enc.minIndex = midIdx - 3
    enc.maxIndex = midIdx + 3
    
    self.assertTrue(enc._overlapOK(midIdx, midIdx-1),
                    "_overlapOK didn't work")
    self.assertTrue(enc._overlapOK(midIdx-2, midIdx+3),
                    "_overlapOK didn't work")
    self.assertFalse(enc._overlapOK(midIdx-3, midIdx-1),
                    "_overlapOK didn't work")

    # We'll just use our own numbers
    self.assertTrue(enc._overlapOK(100, 50, 0),
                "_overlapOK didn't work for far values")
    self.assertTrue(enc._overlapOK(100, 50, enc._maxOverlap),
                "_overlapOK didn't work for far values")
    self.assertFalse(enc._overlapOK(100, 50, enc._maxOverlap+1),
                "_overlapOK didn't work for far values")
    self.assertTrue(enc._overlapOK(50, 50, 5),
                "_overlapOK didn't work for near values")
    self.assertTrue(enc._overlapOK(48, 50, 3),
                "_overlapOK didn't work for near values")
    self.assertTrue(enc._overlapOK(46, 50, 1),
                "_overlapOK didn't work for near values")
    self.assertTrue(enc._overlapOK(45, 50, enc._maxOverlap),
                "_overlapOK didn't work for near values")
    self.assertFalse(enc._overlapOK(48, 50, 4),
                "_overlapOK didn't work for near values")
    self.assertFalse(enc._overlapOK(48, 50, 2),
                "_overlapOK didn't work for near values")
    self.assertFalse(enc._overlapOK(46, 50, 2),
                "_overlapOK didn't work for near values")
    self.assertFalse(enc._overlapOK(50, 50, 6),
                "_overlapOK didn't work for near values")


  def testCountOverlap(self):
    """
    Test that the internal method _countOverlap works as expected.
    """
    enc = RandomDistributedScalarEncoder(name='enc', resolution=1.0, n=500)

    r1 = numpy.array([1, 2, 3, 4, 5, 6])
    r2 = numpy.array([1, 2, 3, 4, 5, 6])
    self.assertEqual(enc._countOverlap(r1, r2), 6,
                     "_countOverlap result is incorrect")

    r1 = numpy.array([1, 2, 3, 4, 5, 6])
    r2 = numpy.array([1, 2, 3, 4, 5, 7])
    self.assertEqual(enc._countOverlap(r1, r2), 5,
                     "_countOverlap result is incorrect")

    r1 = numpy.array([1, 2, 3, 4, 5, 6])
    r2 = numpy.array([6, 5, 4, 3, 2, 1])
    self.assertEqual(enc._countOverlap(r1, r2), 6,
                     "_countOverlap result is incorrect")

    r1 = numpy.array([1, 2, 8, 4, 5, 6])
    r2 = numpy.array([1, 2, 3, 4, 9, 6])
    self.assertEqual(enc._countOverlap(r1, r2), 4,
                     "_countOverlap result is incorrect")

    r1 = numpy.array([1, 2, 3, 4, 5, 6])
    r2 = numpy.array([1, 2, 3])
    self.assertEqual(enc._countOverlap(r1, r2), 3,
                     "_countOverlap result is incorrect")

    r1 = numpy.array([7, 8, 9, 10, 11, 12])
    r2 = numpy.array([1, 2, 3, 4, 5, 6])
    self.assertEqual(enc._countOverlap(r1, r2), 0,
                     "_countOverlap result is incorrect")


  def testVerbosity(self):
    """
    Test that nothing is printed out when verbosity=0
    """
    _stdout = sys.stdout
    sys.stdout = _stringio = StringIO()
    enc = RandomDistributedScalarEncoder(name='mv', resolution=1.0, verbosity=0)
    output = numpy.zeros(enc.getWidth(), dtype=defaultDtype)
    enc.encodeIntoArray(23.0, output)
    enc.getBucketIndices(23.0)
    sys.stdout = _stdout
    self.assertEqual(len(_stringio.getvalue()), 0,
                     "zero verbosity doesn't lead to zero output")


  def testEncodeInvalidInputType(self):
    encoder = RandomDistributedScalarEncoder(name='enc', resolution=1.0,
                                             verbosity=0)
    with self.assertRaises(TypeError):
      encoder.encode("String")



if __name__ == "__main__":
  unittest.main()
