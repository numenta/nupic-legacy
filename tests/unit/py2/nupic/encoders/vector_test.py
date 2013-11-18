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

"""Unit tests for VectorEncoder."""

CL_VERBOSITY = 0

import unittest2 as unittest

from nupic.encoders.vector import VectorEncoder, VectorEncoderOPF, SimpleVectorEncoder
from nupic.encoders.scalar import ScalarEncoder


class VectorEncoderTest(unittest.TestCase):
  """Unit tests for VectorEncoder class."""


  def setUp(self):
    self.name = "vec"
    self._encoder = VectorEncoder
    self._subEnc = ScalarEncoder(5, 0, 10, n=20)


  def testInitialization(self):
    e = self._encoder(3, self._subEnc, name=self.name)
    self.assertIsInstance(e, VectorEncoder)

  def testEncoding(self):
    data=[1,2,3,4,5]
    e = self._encoder(len(data), self._subEnc, name=self.name)
    e.encode(data)

  def testDecoding(self):
    s = ScalarEncoder(1,1,3,n=3, name='idx')
    v = VectorEncoder(3, s, typeCastFn=float)

    data=[1,2,3]
    print "data=", data
    # encode
    enc = v.encode(data)
    print "encoded=", enc
    correct = [1,0,0,0,1,0,0,0,1]
    assert (enc==correct).all()

    #decode
    dec = v.decode(enc)
    print "decoded=", dec
    assert data==dec

  def testVectorEncoderOPFInstance(self):
    # for calling from OPF, use this:
    opfVect = VectorEncoderOPF(3, 1, 1, 3, n=3)
 
  def testSimpleVectorEncoderInstance(self):
    # demo version:
    simpleVect = SimpleVectorEncoder()


if __name__ == '__main__':
  unittest.main()
