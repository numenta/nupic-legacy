#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
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

import numpy
from nupic.encoders.base import defaultDtype
from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
import unittest2 as unittest

from nupic.encoders.random_distributed_scalar import (
  RandomDistributedScalarEncoder
  )


def computeOverlap(x, y):
  """
  Given two binary arrays, compute their overlap. The overlap is the number
  of bits where x[i] and y[i] are both 1
  """
  return ((x + y) == 2).sum()



class RandomDistributedScalarEncoderTest(unittest.TestCase):
  """
  Unit tests for RandomDistributedScalarEncoder class.
  """

  def testEncoding(self):
    """
    Test basic encoding functionality.
    """
    # Initialize with non-default parameters and encode with a number close to
    # the offset
    enc = RandomDistributedScalarEncoder(name='enc', s=1.0, w=23, n=500,
                                         offset = 0.0)
    e0 = enc.encode(-0.1)
    
    self.assertEqual(e0.sum(), 23, "Number of on bits is incorrect")
    self.assertEqual(e0.size, 500, "Width of the vector is incorrect")
    self.assertEqual(enc.getBucketIndices(0.0)[0], enc._maxBuckets / 2,
                     "Offset doesn't correspond to middle bucket")
    self.assertEqual(len(enc.bucketMap), 1, "Number of buckets is not 1")

    # Encode with a number that is s away from offset. Now we should have two
    # buckets and this encoding should be one bit away from e0
    e1 = enc.encode(1.0)
    self.assertEqual(len(enc.bucketMap), 2, "Number of buckets is not 2")
    self.assertEqual(e1.sum(), 23, "Number of on bits is incorrect")
    self.assertEqual(e1.size, 500, "Width of the vector is incorrect")
    self.assertEqual(computeOverlap(e0, e1), 22,
                     "Overlap is not equal to w-1")

    # Encode with a number that is s*w away from offset. Now we should have many
    # buckets and this encoding should have very little overlap with e0
    e25 = enc.encode(25.0)
    self.assertGreater(len(enc.bucketMap), 23, "Number of buckets is not 2")
    self.assertEqual(e25.sum(), 23, "Number of on bits is incorrect")
    self.assertEqual(e25.size, 500, "Width of the vector is incorrect")
    self.assertLess(computeOverlap(e0, e25), 4,
                     "Overlap is too high")


  def testMissingValues(self):
    """
    Test that missing values and NaN return all zero's.
    """
    enc = RandomDistributedScalarEncoder(name='enc', s=1.0)
    empty = enc.encode(SENTINEL_VALUE_FOR_MISSING_DATA)
    self.assertEqual(empty.sum(), 0)

    empty = enc.encode(float("nan"))
    self.assertEqual(empty.sum(), 0)


  def testResolution(self):
    """
    Test that numbers within the same resolution return the same encoding.
    Numbers outside the resolution should return different encodings.
    """
    enc = RandomDistributedScalarEncoder(name='enc', s=1.0)
    
    # Since 23.0 is the first encoded number, it will be the offset.
    # Since s is 1, 22.9 and 23.4 should have the same bucket index and
    # encoding.
    e23 = enc.encode(23.0)
    e23_1 = enc.encode(23.1)
    e22_9 = enc.encode(22.9)
    e24 = enc.encode(24.0)
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


  def testMaxBuckets(self):
    """
    Test that max buckets are handled properly.
    """
    pass


  def testEncodingConsistency(self):
    """
    Test that encodings for old values don't change once we generate new
    buckets.
    """
    pass
  
  
  def testParameterChecks(self):
    """
    Test that some bad construction parameters get handled.
    """
    # n must be >= 6*w
    with self.assertRaises(ValueError):
      RandomDistributedScalarEncoder(name='mv', s=1.0, n=int(5.9*21))

    # n must be an int
    with self.assertRaises(ValueError):
      RandomDistributedScalarEncoder(name='mv', s=1.0, n=5.9*21)

    # w can't be negative
    with self.assertRaises(ValueError):
      RandomDistributedScalarEncoder(name='mv', s=1.0, w=-1)

    # s can't be negative
    with self.assertRaises(ValueError):
      RandomDistributedScalarEncoder(name='mv', s=-2)

 
  def testStatistics(self):
    """
    Check that the statistics for the encodings are within reasonable range.
    """
    pass
  
  
  def testGetWidth(self):
    """
    Test that the getWidth() method works.
    """
    enc = RandomDistributedScalarEncoder(name='enc', s=1.0, n=500)
    self.assertEqual(enc.getWidth(), 500,
                     "getWidth doesn't return the correct result")
  
  
  def testOffset(self):
    """
    Test that offset is working properly
    """
    enc = RandomDistributedScalarEncoder(name='enc', s=1.0)
    enc.encode(23.0)
    self.assertEqual(enc._offset, 23.0,
              "Offset not specified and not initialized to first input")

    enc = RandomDistributedScalarEncoder(name='enc', s=1.0, offset=25.0)
    enc.encode(23.0)
    self.assertEqual(enc._offset, 25.0,
              "Offset not initialized to specified constructor parameter")
  
  
  def testSeed(self):
    """
    Test that initializing twice with the same seed returns identical encodings
    and different when not specified
    """
    enc1 = RandomDistributedScalarEncoder(name='enc', s=1.0, seed=42)
    enc2 = RandomDistributedScalarEncoder(name='enc', s=1.0, seed=42)
    enc3 = RandomDistributedScalarEncoder(name='enc', s=1.0, seed=-1)
    enc4 = RandomDistributedScalarEncoder(name='enc', s=1.0, seed=-1)
    
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


  def testRepresentationOK(self):
    """
    Test that the internal method _newRepresentationOK works as expected.
    """
    pass
  
  
  def testNewRepresentation(self):
    """
    Test that the internal method _newRepresentation works as expected.
    """
    pass


  def testCountOverlapIndices(self):
    """
    Test that the internal method _countOverlapIndices works as expected.
    """
    pass


  def testCountOverlap(self):
    """
    Test that the internal method _countOverlap works as expected.
    """
    pass


  def testVerbosity(self):
    """
    Test that nothing is printed out when verbosity=0
    """
    _stdout = sys.stdout
    sys.stdout = _stringio = StringIO()
    enc = RandomDistributedScalarEncoder(name='mv', s=1.0, verbosity=0)
    output = numpy.zeros(enc.getWidth(), dtype=defaultDtype)
    enc.encodeIntoArray(23.0, output)
    enc.getBucketIndices(23.0)
    sys.stdout = _stdout
    self.assertEqual(len(_stringio.getvalue()), 0,
                     "zero verbosity doesn't lead to zero output")
    
    
###########################################
if __name__ == '__main__':
  unittest.main()
