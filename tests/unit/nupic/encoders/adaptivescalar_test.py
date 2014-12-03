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

import unittest2 as unittest
from nupic.encoders.base import defaultDtype
from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
import numpy

from nupic.encoders.adaptivescalar import AdaptiveScalarEncoder

############################################################################
class AdaptiveScalarTest(unittest.TestCase):
    """Tests for AdaptiveScalarEncoder"""


    def setUp(self):
      # forced: it's strongly recommended to use w>=21, in the example we force skip the check for readibility
      self._l = AdaptiveScalarEncoder(name='scalar', n=14, w=5, minval=1, maxval=10,
                                periodic=False, forced=True) 

    def testMissingValues(self):
      """missing values"""
      # forced: it's strongly recommended to use w>=21, in the example we force skip the check for readib.
      mv = AdaptiveScalarEncoder(name='mv', n=14, w=3, minval=1, maxval=8, periodic=False, forced=True)
      empty = mv.encode(SENTINEL_VALUE_FOR_MISSING_DATA)
      print "\nEncoded missing data \'None\' as %s" % empty
      self.assertEqual(empty.sum(), 0)

    def testNonPeriodicEncoderMinMaxSpec(self):
      """Non-periodic encoder, min and max specified"""
      
      self.assertTrue((self._l.encode(1) == numpy.array([1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                         dtype=defaultDtype)).all())
      self.assertTrue((self._l.encode(2) == numpy.array([0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                                         dtype=defaultDtype)).all())
      self.assertTrue((self._l.encode(10) == numpy.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
                                          dtype=defaultDtype)).all())

    def testTopDownDecode(self):
      """Test the input description generation and topDown decoding"""
      l=self._l
      v = l.minval
      print "\nTesting non-periodic encoder decoding, resolution of %f..." % \
              l.resolution
      while v < l.maxval:
        output = l.encode(v)
        decoded = l.decode(output)
        print "decoding", output, "(%f)=>" % v, l.decodedToStr(decoded)

        (fieldsDict, fieldNames) = decoded
        self.assertEqual(len(fieldsDict), 1)

        (ranges, desc) = fieldsDict.values()[0]
        self.assertEqual(len(ranges), 1)

        (rangeMin, rangeMax) = ranges[0]
        self.assertEqual(rangeMin, rangeMax)
        self.assertTrue(abs(rangeMin - v) < l.resolution)

        topDown = l.topDownCompute(output)[0]
        print "topdown =>", topDown
        self.assertTrue(abs(topDown.value - v) <= l.resolution)

        # Test bucket support
        bucketIndices = l.getBucketIndices(v)
        print "bucket index =>", bucketIndices[0]
        topDown = l.getBucketInfo(bucketIndices)[0]
        self.assertTrue(abs(topDown.value - v) <= l.resolution / 2)
        self.assertEqual(topDown.value, l.getBucketValues()[bucketIndices[0]])
        self.assertEqual(topDown.scalar, topDown.value)
        self.assertTrue((topDown.encoding == output).all())

        # Next value
        v += l.resolution / 4
    def testFillHoles(self):
      """Make sure we can fill in holes"""
      l=self._l
      decoded = l.decode(numpy.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1]))
      (fieldsDict, fieldNames) = decoded
      self.assertEqual(len(fieldsDict), 1)

      (ranges, desc) = fieldsDict.values()[0]
      self.assertEqual(len(ranges), 1)
      self.assertSequenceEqual(ranges[0], [10, 10])
      print "decodedToStr of", ranges, "=>", l.decodedToStr(decoded)

      decoded = l.decode(numpy.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1]))
      (fieldsDict, fieldNames) = decoded
      self.assertEqual(len(fieldsDict), 1)
      (ranges, desc) = fieldsDict.values()[0]
      self.assertEqual(len(ranges), 1)
      self.assertSequenceEqual(ranges[0], [10, 10])
      print "decodedToStr of", ranges, "=>", l.decodedToStr(decoded)

    def testNonPeriodicEncoderMinMaxNotSpec(self):
      """Non-periodic encoder, min and max not specified"""
      l = AdaptiveScalarEncoder(name='scalar', n=14, w=5, minval=None, maxval=None,
                                periodic=False, forced=True)
                                
      def _verify(v, encoded, expV=None):
        if expV is None:
          expV = v
        self.assertTrue((l.encode(v) == numpy.array(encoded, dtype=defaultDtype)).all())
        self.assertTrue(abs(l.getBucketInfo(l.getBucketIndices(v))[0].value - expV) <= \
                    l.resolution/2)

      def _verifyNot(v, encoded):
        self.assertFalse((l.encode(v) == numpy.array(encoded, dtype=defaultDtype)).all())

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
      l = AdaptiveScalarEncoder(name='scalar', n=14, w=5, minval=1, maxval=10,
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
      self.assertTrue(_dumpParams(sfs) != _dumpParams(reg), "Params should not be equal, "\
                "since the two encoders were instantiated with different values.")
      # set the min and the max using sFS to 1,100 respectively.
      sfs.setFieldStats('this',{"this":{"min":1,"max":100}})

      #Now the parameters for both should be the same
      self.assertEqual(_dumpParams(sfs), _dumpParams(reg), "Params should now be equal, "\
            "but they are not. sFS should be equivalent to initialization.")


################################################################################
if __name__ == '__main__':
  unittest.main()
