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


class RandomDistributedScalarEncoderTest(unittest.TestCase):
  """
  Unit tests for RandomDistributedScalarEncoder class.
  """

  def testMissingValues(self):
      """
      Test that missing values and NaN return all zero's.
      """
      mv = RandomDistributedScalarEncoder(name='mv', s=1.0)
      empty = mv.encode(SENTINEL_VALUE_FOR_MISSING_DATA)
      self.assertEqual(empty.sum(), 0)

      empty = mv.encode(float("nan"))
      self.assertEqual(empty.sum(), 0)


  def testResolution(self):
    """
    Test that numbers within the same resolution return the same encoding
    """
    pass


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
      enc = RandomDistributedScalarEncoder(name='mv', s=1.0, n=int(5.9*21))

    # n must be an int
    with self.assertRaises(ValueError):
      enc = RandomDistributedScalarEncoder(name='mv', s=1.0, n=5.9*21)

    # w can't be negative
    with self.assertRaises(ValueError):
      enc = RandomDistributedScalarEncoder(name='mv', s=1.0, w=-1)

    # s can't be negative
    with self.assertRaises(ValueError):
      enc = RandomDistributedScalarEncoder(name='mv', s=-2)

 
  def testStatistics(self):
    """
    Check that the statistics for the encodings are within reasonable range.
    """
    pass
  
  
  def testGetWidth(self):
    """
    Test that the getWidth() method works.
    """
    pass
  
  
  def testSeed(self):
    """
    Test that initializing twice with the same seed returns identical encodings.
    """
    pass
  
  
  def testRepresnetationOK(self):
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
  
  
  def testEncoding(self):
    """
    Test basic encoding functionality.
    """
    pass


  def testVerbosity(self):
    """
    Test that nothing is printed out when verbosity=0
    """
    self._stdout = sys.stdout
    sys.stdout = self._stringio = StringIO()
    enc = RandomDistributedScalarEncoder(name='mv', s=1.0, verbosity=0)
    output = numpy.zeros(enc.getWidth(),dtype=defaultDtype)
    enc.encodeIntoArray(23.0, output)
    enc.getBucketIndices(23.0)
    sys.stdout = self._stdout
    self.assertEqual(len(self._stringio.getvalue()), 0,
                     "zero verbosity doesn't lead to zero output")
    
    
###########################################
if __name__ == '__main__':
  unittest.main()
