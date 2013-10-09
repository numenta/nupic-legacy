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

"""Unit tests for PassThru Encoder."""

CL_VERBOSITY = 0

import cPickle as pickle
import unittest2 as unittest

import numpy

from nupic.encoders.passthru import PassThruEncoder



class PassThruEncoderTest(unittest.TestCase):
  """Unit tests for PassThruEncoder class."""


  def setUp(self):
    self.n = 9
    self.w = 1
    self.name = "foo"
    self._encoder = PassThruEncoder


  def testInitialization(self):
    e = self._encoder(self.n, self.w, name=self.name)
    self.assertIsInstance(e, self._encoder)


  def testEncodeArray(self):
    """Send bitmap as array"""
    e = self._encoder(self.n, self.w, name=self.name)
    bitmap = [0,0,0,1,0,0,0,0,0]
    out = e.encode(bitmap)
    self.assertEqual(out.sum(), sum(bitmap)*self.w)

    x = e.decode(out)
    self.assertIsInstance(x[0], dict)
    self.assertTrue(self.name in x[0])


  def testEncodeBitArray(self):
    """Send bitmap as numpy bit array"""
    e = self._encoder(self.n, self.w, name=self.name)
    bitmap = numpy.zeros(self.n, dtype=numpy.uint8)
    bitmap[3] = 1
    bitmap[5] = 1
    out = e.encode(bitmap)
    self.assertEqual(out.sum(), sum(bitmap)*self.w)


  def testClosenessScores(self):
    """Compare two bitmaps for closeness"""
    e = self._encoder(self.n, self.w, name=self.name)

    """Identical => 1"""
    bitmap1 = [0,0,0,1,1,1,0,0,0]
    bitmap2 = [0,0,0,1,1,1,0,0,0]
    out1 = e.encode(bitmap1)
    out2 = e.encode(bitmap2)
    c = e.closenessScores(out1, out2)
    self.assertEqual(c[0], 1.0)

    """No overlap => 0"""
    bitmap1 = [0,0,0,1,1,1,0,0,0]
    bitmap2 = [1,1,1,0,0,0,1,1,1]
    out1 = e.encode(bitmap1)
    out2 = e.encode(bitmap2)
    c = e.closenessScores(out1, out2)
    self.assertEqual(c[0], 0.0)

    """Similar => 4 of 5 match"""
    bitmap1 = [1,0,1,0,1,0,1,0,1]
    bitmap2 = [1,0,0,1,1,0,1,0,1]
    out1 = e.encode(bitmap1)
    out2 = e.encode(bitmap2)
    c = e.closenessScores(out1, out2)
    self.assertEqual(c[0], 0.8)

    """Little => 1 of 5 match"""
    bitmap1 = [1,0,0,1,1,0,1,0,1]
    bitmap2 = [0,1,1,1,0,1,0,1,0]
    out1 = e.encode(bitmap1)
    out2 = e.encode(bitmap2)
    c = e.closenessScores(out1, out2)
    self.assertEqual(c[0], 0.2)

    """Extra active bit => off by 1 of 5"""
    bitmap1 = [1,0,1,0,1,0,1,0,1]
    bitmap2 = [1,0,1,1,1,0,1,0,1]
    out1 = e.encode(bitmap1)
    out2 = e.encode(bitmap2)
    c = e.closenessScores(out1, out2)
    self.assertEqual(c[0], 0.8)

    """Missing active bit => off by 1 of 5"""
    bitmap1 = [1,0,1,0,1,0,1,0,1]
    bitmap2 = [1,0,0,0,1,0,1,0,1]
    out1 = e.encode(bitmap1)
    out2 = e.encode(bitmap2)
    c = e.closenessScores(out1, out2)
    self.assertEqual(c[0], 0.8)


  def testRobustness(self):
    """Encode bitmaps with robustness (w) set"""
    self.n = 27 
    self.w = 3
    self.testEncodeArray()
    self.testEncodeBitArray()
    self.testClosenessScores()


  def testSparsity(self):
    """Set sparsity nomalization"""
    self.n = 9 
    self.w = 1
    self.onbits = 3
    e = self._encoder(self.n, self.w, self.onbits, self.name)
    bitmap = [0,0,0,1,0,0,0,1,1]
    out = e.encode(bitmap)
    self.assertEqual(out.sum(), self.onbits)

    bitmap = [1,0,0,0,0,0,0,0,0]
    out = e.encode(bitmap)
    self.assertEqual(out.sum(), self.onbits)

    bitmap = [1,1,1,1,0,0,0,0,0]
    out = e.encode(bitmap)
    self.assertEqual(out.sum(), self.onbits)



if __name__ == '__main__':
  unittest.main()
