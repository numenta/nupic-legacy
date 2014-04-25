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

"""Unit tests for VectorEncoder."""

CL_VERBOSITY = 0

import unittest2 as unittest

from nupic.encoders.vector import VectorEncoder, VectorEncoderOPF, SimpleVectorEncoder
from nupic.encoders.scalar import ScalarEncoder


class VectorEncoderTest(unittest.TestCase):
  """Unit tests for VectorEncoder class."""


  def setUp(self):
    self._tmp = None # to pass around values 

  def testInitialization(self):
    e = VectorEncoder(3, ScalarEncoder(21, 0, 10, n=200), name="vec")
    self.assertIsInstance(e, VectorEncoder)

  def testEncoding(self):
    s = ScalarEncoder(1,1,3,n=3, name='idx', forced=True)
    v = VectorEncoder(3, s, typeCastFn=float)

    data=[1,2,3]
    print "data=", data
    # encode
    enc = v.encode(data)
    print "encoded=", enc
    correct = [1,0,0,0,1,0,0,0,1]
    self.assertTrue((enc==correct).all(), "Did not encode correctly")

  def testDecoding(self):
    s = ScalarEncoder(1,1,3,n=3, name='idx', forced=True)
    v = VectorEncoder(3, s, typeCastFn=float)
    data=[1,2,3]
    enc = v.encode(data)

    #decode
    dec = v.decode(enc)
    print "decoded=", dec
    res= v.getData(dec)
    self.assertEqual(data, res, "Decoded data not equal to original")

  def testVectorEncoderOPFInstance(self):
    """calling VectorEncoder from OPF"""
    opfVect = VectorEncoderOPF(3, 1, 3, n=211, w=21, dataType="int")
    data=[1,2,3]
    enc=opfVect.encode(data)
    dec=opfVect.decode(enc)
    data2=opfVect.getData(dec)
    self.assertEqual(data, data2, "VectorEncoderOPF did not encode/decode correctly.")

  def testVectorEncoderOPFTypeCast(self):
    """for calling from OPF, use this to cast data type"""
    opfVect = VectorEncoderOPF(3, 1, 3, n=300, w=21, dataType="str")
    data=[1,2,3]
    enc=opfVect.encode(data)
    dec=opfVect.decode(enc)
    data2=opfVect.getData(dec)
    self.assertIsInstance(data2[0], str, "VectorEncoderOPF did not cast output to str(ing)")

    opfVect = VectorEncoderOPF(3, 1, 3, n=300, w=21, dataType="int")
    data=[1,2,3]
    enc=opfVect.encode(data)
    dec=opfVect.decode(enc)
    data2=opfVect.getData(dec)
    self.assertIsInstance(data2[0], int, "VectorEncoderOPF did not cast output to int")
 
  def testSimpleVectorEncoderInstance(self):
    """ simple demo version"""
    simpleVect = SimpleVectorEncoder()
    data=[1.0, 2.0, 3.0, 4.0, 5.0]
    enc=simpleVect.encode(data)
    dec=simpleVect.decode(enc)
    data2=simpleVect.getData(dec)
    self.assertEqual(data, data2, "Simple vector did not encode/decode correctly")

if __name__ == '__main__':
  unittest.main()
