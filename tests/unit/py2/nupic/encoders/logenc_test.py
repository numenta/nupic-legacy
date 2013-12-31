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

"""Unit tests for logarithmic encoder"""

import numpy
import math
from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
import unittest2 as unittest

from nupic.encoders.logenc import LogEncoder


#########################################################################
class LogEncoderTest(unittest.TestCase):
  '''Unit tests for LogEncoder class'''


  ############################################################################
  def testLogEncoder(self):
      print "Testing LogEncoder...",

      # Create the encoder
      le = LogEncoder(w=5,
                     resolution=1,
                     minval=1,
                     maxval=10000,
                     name="amount")
      
      #######################################################################
      # Verify we're setting the description properly
      self.assertEqual(le.getDescription(), [("amount", 0)])

      #######################################################################
      # Verify the encoder ends up with the correct width
      #
      # 10^0 -> 10^4 => 0 decibels -> 40 decibels;
      # 41 possible decibel values plus padding = 4 = width 45
      self.assertEqual(le.getWidth(), 45)
      
      #######################################################################
      # Verify we have the correct number of possible values
      #
      # 10^0 -> 10^4 => 0 -> 40 decibels;
      # 41 possible decibel values plus padding = 4 = width 45
      self.assertEqual(len(le.getBucketValues()), 41)
      
      #######################################################################
      # Verify a value of 1.0 is encoded as expected
      value = 1.0
      output = le.encode(value)
      
      # Our expected encoded representation of the value 1 is the first
      # w bits on in an array of len width.
      expected = [1, 1, 1, 1, 1] + 40 * [0]
      # Convert to numpy array
      expected = numpy.array(expected, dtype='uint8')
      
      self.assertTrue((output == expected).all())

      #######################################################################
      # Test reverse lookup
      decoded = le.decode(output)
      (fieldsDict, fieldNames) = decoded
      self.assertEqual(len(fieldsDict), 1)
      (ranges, desc) = fieldsDict.values()[0]
      self.assertTrue(len(ranges) == 1 and numpy.array_equal(ranges[0], [1, 1]))

      #######################################################################
      # Verify an input representing a missing value is handled properly
      mvOutput = le.encode(SENTINEL_VALUE_FOR_MISSING_DATA)
      self.assertEqual(sum(mvOutput), 0)

      #######################################################################
      # Test top-down
      import pdb
      value = le.minval
      while value <= le.maxval:

        output = le.encode(value)
        topDown = le.topDownCompute(output)

        # Do the scaling by hand here.
        scaledVal = 10 * math.log10(value)
        # Find the range of values that would also produce this top down
        # output.
        minTopDown = math.pow(10, (scaledVal - le.encoder.resolution) / 10.0)
        maxTopDown = math.pow(10, (scaledVal + le.encoder.resolution) / 10.0)

        # Verify the range surrounds this scaled val
        self.assertTrue(topDown.value >= minTopDown and
                        topDown.value <= maxTopDown)

        # Test bucket support
        if value == le.maxval:
          bucketIndices = le.getBucketIndices(value+1)
          print bucketIndices
          pdb.set_trace()
        else:
          bucketIndices = le.getBucketIndices(value)
        topDown = le.getBucketInfo(bucketIndices)[0]
        
        # Verify our reconstructed value is in the valid range
        self.assertTrue(topDown.value >= minTopDown and
                        topDown.value <= maxTopDown)
        # Same for the scalar value
        self.assertTrue(topDown.scalar >= minTopDown and
                        topDown.scalar <= maxTopDown)
        # That the encoding portion of our EncoderResult matched the result of
        # encode()
        self.assertTrue((topDown.encoding == output).all())
        # Verify our reconstructed value is the same as the bucket value
        bucketValues = le.getBucketValues()
        self.assertEqual(topDown.value,
                         bucketValues[bucketIndices[0]])

        # Next value
        scaledVal += le.encoder.resolution / 4.0
        value = math.pow(10, scaledVal / 10.0)
        print value


      # -------------------------------------------------------------------
      output = le.encode(100)
      # increase of 2 decades = 20 decibels
      # bit 0, 1 are padding; bit 3 is 1, ..., bit 22 is 20 (23rd bit)
      expected = 20 * [0] + [1, 1, 1, 1, 1] + 20 * [0]
      expected = numpy.array(expected, dtype='uint8')
      self.assertTrue((output == expected).all())

      # Test reverse lookup
      decoded = le.decode(output)
      (fieldsDict, fieldNames) = decoded
      self.assertEqual(len(fieldsDict), 1)
      (ranges, desc) = fieldsDict.values()[0]
      self.assertTrue(len(ranges) == 1 and
                      numpy.array_equal(ranges[0], [100, 100]))
      print "decodedToStr of", ranges, "=>", le.decodedToStr(decoded)

      # -------------------------------------------------------------------
      output = le.encode(10000)
      expected = 40 * [0] + [1, 1, 1, 1, 1]
      expected = numpy.array(expected, dtype='uint8')
      self.assertTrue((output == expected).all())

      # Test reverse lookup
      decoded = le.decode(output)
      (fieldsDict, fieldNames) = decoded
      self.assertEqual(len(fieldsDict), 1)
      (ranges, desc) = fieldsDict.values()[0]
      self.assertTrue(len(ranges) == 1 and
                      numpy.array_equal(ranges[0], [10000, 10000]))
      print "decodedToStr of", ranges, "=>", le.decodedToStr(decoded)


###########################################
if __name__ == '__main__':
  unittest.main()
