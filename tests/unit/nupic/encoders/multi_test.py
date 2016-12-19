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

"""Unit tests for multi- encoder"""

import numpy
import tempfile
import unittest2 as unittest

from nupic.encoders.multi import MultiEncoder
from nupic.encoders import ScalarEncoder, AdaptiveScalarEncoder, SDRCategoryEncoder
from nupic.data.dictutils import DictObj

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.encoders.multi_capnp import MultiEncoderProto



class MultiEncoderTest(unittest.TestCase):
  """Unit tests for MultiEncoder class"""


  def testMultiEncoder(self):
    """Testing MultiEncoder..."""

    e = MultiEncoder()

    # should be 7 bits wide
    # use of forced=True is not recommended, but here for readibility, see
    # scalar.py
    e.addEncoder("dow",
                 ScalarEncoder(w=3, resolution=1, minval=1, maxval=8,
                               periodic=True, name="day of week", forced=True))
    # sould be 14 bits wide
    e.addEncoder("myval",
                 ScalarEncoder(w=5, resolution=1, minval=1, maxval=10,
                               periodic=False, name="aux", forced=True))
    self.assertEqual(e.getWidth(), 21)
    self.assertEqual(e.getDescription(), [("day of week", 0), ("aux", 7)])

    d = DictObj(dow=3, myval=10)
    expected=numpy.array([0,1,1,1,0,0,0] + [0,0,0,0,0,0,0,0,0,1,1,1,1,1],
                         dtype="uint8")
    output = e.encode(d)
    self.assertTrue(numpy.array_equal(expected, output))

    # Check decoding
    decoded = e.decode(output)
    self.assertEqual(len(decoded), 2)
    (ranges, _) = decoded[0]["aux"]
    self.assertEqual(len(ranges), 1)
    self.assertTrue(numpy.array_equal(ranges[0], [10, 10]))
    (ranges, _) = decoded[0]["day of week"]
    self.assertTrue(len(ranges) == 1 and numpy.array_equal(ranges[0], [3, 3]))

    e.addEncoder("myCat",
                 SDRCategoryEncoder(n=7, w=3,
                                    categoryList=["run", "pass","kick"],
                                    forced=True))

    d = DictObj(dow=4, myval=6, myCat="pass")
    output = e.encode(d)
    topDownOut = e.topDownCompute(output)
    self.assertAlmostEqual(topDownOut[0].value, 4.5)
    self.assertEqual(topDownOut[1].value, 6.0)
    self.assertEqual(topDownOut[2].value, "pass")
    self.assertEqual(topDownOut[2].scalar, 2)
    self.assertEqual(topDownOut[2].encoding.sum(), 3)



  @unittest.skipUnless(
      capnp, "pycapnp is not installed, skipping serialization test.")
  def testReadWrite(self):
    original = MultiEncoder()
    original.addEncoder("dow",
                        ScalarEncoder(w=3, resolution=1, minval=1, maxval=8,
                                      periodic=True, name="day of week",
                                      forced=True))
    original.addEncoder("myval",
                        AdaptiveScalarEncoder(n=50, w=5, resolution=1, minval=1, maxval=10,
                                              periodic=False, name="aux", forced=True))
    originalValue = DictObj(dow=3, myval=10)
    output = original.encode(originalValue)

    proto1 = MultiEncoderProto.new_message()
    original.write(proto1)

    # Write the proto to a temp file and read it back into a new proto
    with tempfile.TemporaryFile() as f:
      proto1.write(f)
      f.seek(0)
      proto2 = MultiEncoderProto.read(f)

    encoder = MultiEncoder.read(proto2)

    self.assertIsInstance(encoder, MultiEncoder)
    self.assertEqual(encoder.name, original.name)
    self.assertEqual(encoder.width, original.width)
    self.assertTrue(numpy.array_equal(encoder.encode(originalValue), output))

    testObj1 = DictObj(dow=4, myval=9)
    self.assertEqual(original.decode(encoder.encode(testObj1)),
                     encoder.decode(original.encode(testObj1)))

    # Feed in a new value and ensure the encodings match
    testObj2 = DictObj(dow=5, myval=8)
    result1 = original.encode(testObj2)
    result2 = encoder.encode(testObj2)
    self.assertTrue(numpy.array_equal(result1, result2))



if __name__ == "__main__":
  unittest.main()
