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

"""Unit tests for BitmapArray Encoder."""

CL_VERBOSITY = 0

import cPickle as pickle
import unittest2 as unittest

import numpy

from nupic.encoders.sparse_pass_through_encoder import SparsePassThroughEncoder



class SparsePassThroughEncoderTest(unittest.TestCase):
  """Unit tests for SparsePassThroughEncoder class."""


  def setUp(self):
    self.n = 25
    self.name = "foo"
    self._encoder = SparsePassThroughEncoder


  def testEncodeArray(self):
    """Send bitmap as array of indicies"""
    e = self._encoder(self.n, name=self.name)
    bitmap = [2,7,15,18,23]
    out = e.encode(bitmap)
    self.assertEqual(out.sum(), len(bitmap))

    x = e.decode(out)
    self.assertIsInstance(x[0], dict)
    self.assertTrue(self.name in x[0])


  def testEncodeArrayInvalidW(self):
    """Send bitmap as array of indicies"""
    e = self._encoder(self.n, 3, name=self.name)
    with self.assertRaises(ValueError):
      e.encode([2])
    with self.assertRaises(ValueError):
      e.encode([2,7,15,18,23])


  def testClosenessScores(self):
    """Compare two bitmaps for closeness"""
    e = self._encoder(self.n, name=self.name)

    """Identical => 1"""
    bitmap1 = [2,7,15,18,23]
    bitmap2 = [2,7,15,18,23]
    out1 = e.encode(bitmap1)
    out2 = e.encode(bitmap2)
    c = e.closenessScores(out1, out2)
    self.assertEqual(c[0], 1.0)

    """No overlap => 0"""
    bitmap1 = [2,7,15,18,23]
    bitmap2 = [3,9,14,19,24]
    out1 = e.encode(bitmap1)
    out2 = e.encode(bitmap2)
    c = e.closenessScores(out1, out2)
    self.assertEqual(c[0], 0.0)

    """Similar => 4 of 5 match"""
    bitmap1 = [2,7,15,18,23]
    bitmap2 = [2,7,17,18,23]
    out1 = e.encode(bitmap1)
    out2 = e.encode(bitmap2)
    c = e.closenessScores(out1, out2)
    self.assertEqual(c[0], 0.8)

    """Little => 1 of 5 match"""
    bitmap1 = [2,7,15,18,23]
    bitmap2 = [3,7,17,19,24]
    out1 = e.encode(bitmap1)
    out2 = e.encode(bitmap2)
    c = e.closenessScores(out1, out2)
    self.assertEqual(c[0], 0.2)

    """Extra active bit => off by 1 of 5"""
    bitmap1 = [2,7,15,18,23]
    bitmap2 = [2,7,11,15,18,23]
    out1 = e.encode(bitmap1)
    out2 = e.encode(bitmap2)
    c = e.closenessScores(out1, out2)
    self.assertEqual(c[0], 0.8)

    """Missing active bit => off by 1 of 5"""
    bitmap1 = [2,7,15,18,23]
    bitmap2 = [2,7,18,23]
    out1 = e.encode(bitmap1)
    out2 = e.encode(bitmap2)
    c = e.closenessScores(out1, out2)
    self.assertEqual(c[0], 0.8)



if __name__ == "__main__":
  unittest.main()
