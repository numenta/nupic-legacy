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

"""Unit tests for BitmapArray Encoder."""

CL_VERBOSITY = 0

import cPickle as pickle
import unittest2 as unittest

import numpy

from nupic.encoders.bitmaparray import BitmapArrayEncoder



class BitmapArrayEncoderTest(unittest.TestCase):
  """Unit tests for BitmapArrayEncoder class."""


  def setUp(self):
    self.n = 25
    self.w = 1
    self.name = "foo"
    self._encoder = BitmapArrayEncoder


  def testInitialization(self):
    e = self._encoder(self.n, self.w, name=self.name)
    self.assertEqual(type(e), self._encoder)


  def testEncodeString(self):
    """Send array as csv string."""
    e = self._encoder(self.n, self.w, name=self.name)
    bitmap = "2,7,15,18,23"
    out = e.encode(bitmap)
    assert out.sum() == len(bitmap.split(','))*self.w

    x = e.decode(out)
    assert isinstance(x[0], dict)
    assert self.name in x[0]


  def testEncodeArray(self):
    """Send bitmap as array of indicies"""
    e = self._encoder(self.n, self.w, name=self.name)
    bitmap = [2,7,15,18,23]
    out = e.encode(bitmap)
    assert out.sum() == len(bitmap)*self.w

    x = e.decode(out)
    assert isinstance(x[0], dict)
    assert self.name in x[0]


  def testClosenessScores(self):
    """Compare two bitmaps for closeness"""
    e = self._encoder(self.n, self.w, name=self.name)

    """Identical => 1"""
    bitmap1 = [2,7,15,18,23]
    bitmap2 = [2,7,15,18,23]
    out1 = e.encode(bitmap1)
    out2 = e.encode(bitmap2)
    c = e.closenessScores(out1, out2)
    assert c[0] == 1.0

    """No overlap => 0"""
    bitmap1 = [2,7,15,18,23]
    bitmap2 = [3,9,14,19,24]
    out1 = e.encode(bitmap1)
    out2 = e.encode(bitmap2)
    c = e.closenessScores(out1, out2)
    assert c[0] == 0.0

    """Similar => 4 of 5 match"""
    bitmap1 = [2,7,15,18,23]
    bitmap2 = [2,7,17,18,23]
    out1 = e.encode(bitmap1)
    out2 = e.encode(bitmap2)
    c = e.closenessScores(out1, out2)
    assert c[0] == 0.8

    """Little => 1 of 5 match"""
    bitmap1 = [2,7,15,18,23]
    bitmap2 = [3,7,17,19,24]
    out1 = e.encode(bitmap1)
    out2 = e.encode(bitmap2)
    c = e.closenessScores(out1, out2)
    assert c[0] == 0.2

    """Extra active bit => off by 1 of 5"""
    bitmap1 = [2,7,15,18,23]
    bitmap2 = [2,7,11,15,18,23]
    out1 = e.encode(bitmap1)
    out2 = e.encode(bitmap2)
    c = e.closenessScores(out1, out2)
    assert c[0] == 0.8

    """Missing active bit => off by 1 of 5"""
    bitmap1 = [2,7,15,18,23]
    bitmap2 = [2,7,18,23]
    out1 = e.encode(bitmap1)
    out2 = e.encode(bitmap2)
    c = e.closenessScores(out1, out2)
    assert c[0] == 0.8


  def testRobustness(self):
    """Encode bitmaps with robustness (w) set"""
    self.w = 3
    self.n = self.n * self.w
    self.testEncodeString()
    self.testEncodeArray()
    self.testClosenessScores()


  def testSparsity(self):
    """Set sparsity nomalization"""
    self.n = 25
    self.w = 1
    self.onbits = 5
    e = self._encoder(self.n, self.w, self.onbits, self.name)
    bitmap = [2,7,15,18,23]
    out = e.encode(bitmap)
    assert out.sum() == self.onbits

    bitmap = [2]
    out = e.encode(bitmap)
    assert out.sum() == self.onbits

    bitmap = [0,1,2,3,7,15,18,23]
    out = e.encode(bitmap)
    assert out.sum() == self.onbits



if __name__ == '__main__':
  unittest.main()
