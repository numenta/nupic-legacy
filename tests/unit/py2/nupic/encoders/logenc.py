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

"""Unit tests for date encoder"""

import numpy
import math
#TODO howto not import * ??
from nupic.encoders.base import *
from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
import unittest2 as unittest

from nupic.encoders.logenc import LogEncoder


#########################################################################
class DateEncoderTest(unittest.TestCase):
  '''Unit tests for DateEncoder class'''


  ############################################################################
  def testLogEncoder(self):
      print "Testing LogEncoder...",

      l = LogEncoder(w=5, resolution=1, minval=1, maxval=10000, name="amount")
      assert l.getDescription() == [("amount", 0)]

      # -------------------------------------------------------------------
      # 10^0 -> 10^4 => 0 decibels -> 40 decibels;
      # 41 possible decibel values plus padding=4 = width 45
      assert l.getWidth() == 45
      value = 1.0
      output = l.encode(value)
      expected = [1, 1, 1, 1, 1] + 40 * [0]
      expected = numpy.array(expected, dtype='uint8')
      assert (output == expected).all()

      # Test reverse lookup
      decoded = l.decode(output)
      (fieldsDict, fieldNames) = decoded
      assert len(fieldsDict) == 1
      (ranges, desc) = fieldsDict.values()[0]
      print "decodedToStr of", ranges, "=>", l.decodedToStr(decoded)
      assert len(ranges) == 1 and numpy.array_equal(ranges[0], [1, 1])

      # MISSING VALUE
      mvOutput = l.encode(SENTINEL_VALUE_FOR_MISSING_DATA)
      assert sum(mvOutput) == 0

      # Test top-down
      value = l.minval
      while value <= l.maxval:
        output = l.encode(value)
        print "output of %f =>" % (value), output

        topDown = l.topDownCompute(output)
        print "topdown =>", topDown

        scaledVal = 10 * math.log10(value)
        minTopDown = math.pow(10, (scaledVal-l.encoder.resolution) / 10.0)
        maxTopDown = math.pow(10, (scaledVal+l.encoder.resolution) / 10.0)

        assert(topDown.value >= minTopDown and topDown.value <= maxTopDown)

        # Test bucket support
        bucketIndices = l.getBucketIndices(value)
        print "bucket index =>", bucketIndices[0]
        topDown = l.getBucketInfo(bucketIndices)[0]
        assert (topDown.value >= minTopDown and topDown.value <= maxTopDown)
        assert (topDown.scalar >= minTopDown and topDown.scalar <= maxTopDown)
        assert (topDown.encoding == output).all()
        assert (topDown.value == l.getBucketValues()[bucketIndices[0]])


        # Next value
        scaledVal += l.encoder.resolution/4
        value = math.pow(10, scaledVal / 10.0)


      # -------------------------------------------------------------------
      output = l.encode(100)
      # increase of 2 decades = 20 decibels
      # bit 0, 1 are padding; bit 3 is 1, ..., bit 22 is 20 (23rd bit)
      expected = 20 * [0] + [1, 1, 1, 1, 1] + 20 * [0]
      expected = numpy.array(expected, dtype='uint8')
      assert (output == expected).all()

      # Test reverse lookup
      decoded = l.decode(output)
      (fieldsDict, fieldNames) = decoded
      assert len(fieldsDict) == 1
      (ranges, desc) = fieldsDict.values()[0]
      assert len(ranges) == 1 and numpy.array_equal(ranges[0], [100, 100])
      print "decodedToStr of", ranges, "=>", l.decodedToStr(decoded)

      # -------------------------------------------------------------------
      output = l.encode(10000)
      expected = 40 * [0] + [1, 1, 1, 1, 1]
      expected = numpy.array(expected, dtype='uint8')
      assert (output == expected).all()

      # Test reverse lookup
      decoded = l.decode(output)
      (fieldsDict, fieldNames) = decoded
      assert len(fieldsDict) == 1
      (ranges, desc) = fieldsDict.values()[0]
      assert len(ranges) == 1 and numpy.array_equal(ranges[0], [10000, 10000])
      print "decodedToStr of", ranges, "=>", l.decodedToStr(decoded)


###########################################
if __name__ == '__main__':
  unittest.main()