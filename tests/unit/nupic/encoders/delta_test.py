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

"""Unit tests for delta encoder"""

import numpy as np
import unittest

from nupic.encoders.delta import (DeltaEncoder,
                                  AdaptiveScalarEncoder)



class DeltaEncoderTest(unittest.TestCase):
  '''Unit tests for DeltaEncoder class'''


  def setUp(self):
    self._dencoder = DeltaEncoder(w=21, n=100, forced=True)
    self._adaptscalar = AdaptiveScalarEncoder(w=21, n=100, forced=True)


  def testDeltaEncoder(self):
      """simple delta reconstruction test"""
      for i in range(5):
        encarr =  self._dencoder.encodeIntoArray(i, np.zeros(100), learn=True)
      self._dencoder.setStateLock(True)
      for i in range(5, 7):
        encarr =  self._dencoder.encodeIntoArray(i, np.zeros(100), learn=True)
      res = self._dencoder.topDownCompute(encarr)
      self.assertEqual(res[0].value, 6)
      self.assertEqual(self._dencoder.topDownCompute(encarr)[0].value, res[0].value)
      self.assertEqual(self._dencoder.topDownCompute(encarr)[0].scalar, res[0].scalar)
      self.assertTrue((self._dencoder.topDownCompute(encarr)[0].encoding == res[0].encoding).all())


  def testEncodingVerification(self):
      """encoding verification test passed"""
      feedIn  = [1, 10, 4, 7, 9, 6, 3, 1]
      expectedOut = [0, 9, -6, 3, 2, -3, -3, -2]
      self._dencoder.setStateLock(False)
      #Check that the deltas are being returned correctly.
      for i in range(len(feedIn)):
        aseencode = np.zeros(100)
        self._adaptscalar.encodeIntoArray(expectedOut[i], aseencode, learn=True)
        delencode = np.zeros(100)
        self._dencoder.encodeIntoArray(feedIn[i], delencode, learn=True)
        self.assertTrue((delencode[0] == aseencode[0]).all())


  def testLockingState(self):
      """Check that locking the state works correctly"""
      feedIn  = [1, 10, 9, 7, 9, 6, 3, 1]
      expectedOut = [0, 9, -6, 3, 2, -3, -3, -2]
      for i in range(len(feedIn)):
        if i == 3:
          self._dencoder.setStateLock(True)

        aseencode = np.zeros(100)
        self._adaptscalar.encodeIntoArray(expectedOut[i], aseencode, learn=True)
        delencode = np.zeros(100)
        if i>=3:
          self._dencoder.encodeIntoArray(feedIn[i]-feedIn[2], delencode, learn=True)
        else:
          self._dencoder.encodeIntoArray(expectedOut[i], delencode, learn=True)

        self.assertTrue((delencode[0] == aseencode[0]).all())


  def testEncodeInvalidInputType(self):
    try:
      self._dencoder.encode("String")
    except TypeError as e:
      self.assertEqual(e.message, "Expected a scalar input but got input of type <type 'str'>")
    else:
      self.fail("Should have thrown TypeError during attempt to encode string with scalar encoder.")



if __name__ == "__main__":
  unittest.main()
