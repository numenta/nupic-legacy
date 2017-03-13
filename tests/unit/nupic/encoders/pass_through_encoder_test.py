# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

"""Unit tests for PassThru Encoder."""

CL_VERBOSITY = 0

import tempfile
import unittest2 as unittest

import numpy

from nupic.encoders import PassThroughEncoder

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.encoders.pass_through_capnp import PassThroughEncoderProto



class PassThroughEncoderTest(unittest.TestCase):
  """Unit tests for PassThroughEncoder class."""


  def setUp(self):
    self.n = 9
    self.name = "foo"
    self._encoder = PassThroughEncoder


  def testEncodeArray(self):
    """Send bitmap as array"""
    e = self._encoder(self.n, name=self.name)
    bitmap = [0,0,0,1,0,0,0,0,0]
    out = e.encode(bitmap)
    self.assertEqual(out.sum(), sum(bitmap))

    x = e.decode(out)
    self.assertIsInstance(x[0], dict)
    self.assertTrue(self.name in x[0])


  def testEncodeBitArray(self):
    """Send bitmap as numpy bit array"""
    e = self._encoder(self.n, name=self.name)
    bitmap = numpy.zeros(self.n, dtype=numpy.uint8)
    bitmap[3] = 1
    bitmap[5] = 1
    out = e.encode(bitmap)
    expectedSum = sum(bitmap)
    realSum = out.sum()
    self.assertEqual(realSum, expectedSum)


  def testClosenessScores(self):
    """Compare two bitmaps for closeness"""
    e = self._encoder(self.n, name=self.name)

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


  @unittest.skipUnless(
      capnp, "pycapnp is not installed, skipping serialization test.")
  def testReadWrite(self):
    original = self._encoder(self.n, name=self.name)
    originalValue = original.encode([1,0,1,0,1,0,1,0,1])

    proto1 = PassThroughEncoderProto.new_message()
    original.write(proto1)

    # Write the proto to a temp file and read it back into a new proto
    with tempfile.TemporaryFile() as f:
      proto1.write(f)
      f.seek(0)
      proto2 = PassThroughEncoderProto.read(f)

    encoder = PassThroughEncoder.read(proto2)

    self.assertIsInstance(encoder, PassThroughEncoder)
    self.assertEqual(encoder.name, original.name)
    self.assertEqual(encoder.verbosity, original.verbosity)
    self.assertEqual(encoder.w, original.w)
    self.assertEqual(encoder.n, original.n)
    self.assertEqual(encoder.description, original.description)
    self.assertTrue(numpy.array_equal(encoder.encode([1,0,1,0,1,0,1,0,1]),
                                      originalValue))
    self.assertEqual(original.decode(encoder.encode([1,0,1,0,1,0,1,0,1])),
                     encoder.decode(original.encode([1,0,1,0,1,0,1,0,1])))

    # Feed in a new value and ensure the encodings match
    result1 = original.encode([0,1,0,1,0,1,0,1,0])
    result2 = encoder.encode([0,1,0,1,0,1,0,1,0])
    self.assertTrue(numpy.array_equal(result1, result2))



if __name__ == "__main__":
  unittest.main()
