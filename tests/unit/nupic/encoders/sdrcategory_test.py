# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013-2015, Numenta, Inc.  Unless you have an agreement
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

"""Unit tests for SDR Category encoder"""

import numpy
from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
import tempfile
import unittest

from nupic.encoders.sdr_category import SDRCategoryEncoder


try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.encoders.sdr_category_capnp import SDRCategoryEncoderProto



class SDRCategoryEncoderTest(unittest.TestCase):
  """Unit tests for SDRCategory encoder class"""


  def testSDRCategoryEncoder(self):
    # make sure we have > 16 categories so that we have to grow our sdrs
    categories = ["ES", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8",
                  "S9","S10", "S11", "S12", "S13", "S14", "S15", "S16",
                  "S17", "S18", "S19", "GB", "US"]

    fieldWidth = 100
    bitsOn = 10

    s = SDRCategoryEncoder(n=fieldWidth, w=bitsOn, categoryList = categories,
                           name="foo", verbosity=0, forced=True)

    # internal check
    self.assertEqual(s.sdrs.shape, (32, fieldWidth))

    # ES
    es = s.encode("ES")
    self.assertEqual(es.sum(), bitsOn)
    self.assertEqual(es.shape, (fieldWidth,))
    self.assertEqual(es.sum(), bitsOn)

    x = s.decode(es)
    self.assertIsInstance(x[0], dict)
    self.assertTrue("foo" in x[0])
    self.assertEqual(x[0]["foo"][1], "ES")

    topDown = s.topDownCompute(es)
    self.assertEqual(topDown.value, "ES")
    self.assertEqual(topDown.scalar, 1)
    self.assertEqual(topDown.encoding.sum(), bitsOn)

    # ----------------------------------------------------------------------
    # Test topdown compute
    for v in categories:
      output = s.encode(v)
      topDown = s.topDownCompute(output)
      self.assertEqual(topDown.value, v)
      self.assertEqual(topDown.scalar, s.getScalars(v)[0])

      bucketIndices = s.getBucketIndices(v)
      topDown = s.getBucketInfo(bucketIndices)[0]
      self.assertEqual(topDown.value, v)
      self.assertEqual(topDown.scalar, s.getScalars(v)[0])
      self.assertTrue(numpy.array_equal(topDown.encoding, output))
      self.assertEqual(topDown.value, s.getBucketValues()[bucketIndices[0]])


    # Unknown
    unknown = s.encode("ASDFLKJLK")
    self.assertEqual(unknown.sum(), bitsOn)
    self.assertEqual(unknown.shape, (fieldWidth,))
    self.assertEqual(unknown.sum(), bitsOn)
    x = s.decode(unknown)
    self.assertEqual(x[0]["foo"][1], "<UNKNOWN>")

    topDown = s.topDownCompute(unknown)
    self.assertEqual(topDown.value, "<UNKNOWN>")
    self.assertEqual(topDown.scalar, 0)

    # US
    us = s.encode("US")
    self.assertEqual(us.sum(), bitsOn)
    self.assertEqual(us.shape, (fieldWidth,))
    self.assertEqual(us.sum(), bitsOn)
    x = s.decode(us)
    self.assertEqual(x[0]["foo"][1], "US")

    topDown = s.topDownCompute(us)
    self.assertEqual(topDown.value, "US")
    self.assertEqual(topDown.scalar, len(categories))
    self.assertEqual(topDown.encoding.sum(), bitsOn)

    # empty field
    empty = s.encode(SENTINEL_VALUE_FOR_MISSING_DATA)
    self.assertEqual(empty.sum(), 0)
    self.assertEqual(empty.shape, (fieldWidth,))
    self.assertEqual(empty.sum(), 0)

    # make sure it can still be decoded after a change
    bit =  s.random.getUInt32(s.getWidth()-1)
    us[bit] = 1 - us[bit]
    x = s.decode(us)
    self.assertEqual(x[0]["foo"][1], "US")


    # add two reps together
    newrep = ((us + unknown) > 0).astype(numpy.uint8)
    x = s.decode(newrep)
    name =x[0]["foo"][1]
    if name != "US <UNKNOWN>" and name != "<UNKNOWN> US":
      othercategory = name.replace("US", "")
      othercategory = othercategory.replace("<UNKNOWN>", "")
      othercategory = othercategory.replace(" ", "")
      otherencoded = s.encode(othercategory)
      raise RuntimeError("Decoding failure")

    # serialization
    # TODO: Remove pickle-based serialization tests -- issues #1419 and #1420
    import cPickle as pickle
    t = pickle.loads(pickle.dumps(s))
    self.assertTrue((t.encode("ES") == es).all())
    self.assertTrue((t.encode("GB") == s.encode("GB")).all())

    # Test autogrow
    s = SDRCategoryEncoder(n=fieldWidth, w=bitsOn, categoryList=None,
                           name="bar", forced=True)

    es = s.encode("ES")
    self.assertEqual(es.shape, (fieldWidth,))
    self.assertEqual(es.sum(), bitsOn)
    x = s.decode(es)
    self.assertIsInstance(x[0], dict)
    self.assertTrue("bar" in x[0])
    self.assertEqual(x[0]["bar"][1], "ES")


    us = s.encode("US")
    self.assertEqual(us.shape, (fieldWidth,))
    self.assertEqual(us.sum(), bitsOn)
    x = s.decode(us)
    self.assertEqual(x[0]["bar"][1], "US")

    es2 = s.encode("ES")
    self.assertTrue(numpy.array_equal(es2, es))

    us2 = s.encode("US")
    self.assertTrue(numpy.array_equal(us2, us))

    # make sure it can still be decoded after a change
    bit =  s.random.getUInt32(s.getWidth() - 1)
    us[bit] = 1 - us[bit]
    x = s.decode(us)
    self.assertEqual(x[0]["bar"][1], "US")

    # add two reps together
    newrep = ((us + es) > 0).astype(numpy.uint8)
    x = s.decode(newrep)
    name = x[0]["bar"][1]
    self.assertTrue(name == "US ES" or name == "ES US")

    # Catch duplicate categories
    caughtException = False
    newcategories = categories[:]
    self.assertTrue("ES" in newcategories)
    newcategories.append("ES")
    try:
      s = SDRCategoryEncoder(n=fieldWidth, w=bitsOn,
                             categoryList=newcategories, name="foo",
                             forced=True)
    except RuntimeError, e:
      caughtException = True
    finally:
      if not caughtException:
        raise RuntimeError("Did not catch duplicate category in constructor")

    # serialization for autogrow encoder
    gs = s.encode("GS")
    # TODO: Remove as part of issues #1419 and #1420
    t = pickle.loads(pickle.dumps(s))
    self.assertTrue(numpy.array_equal(t.encode("ES"), es))
    self.assertTrue(numpy.array_equal(t.encode("GS"), gs))

    # -----------------------------------------------------------------------


  def testAutogrow(self):
    """testing auto-grow"""
    fieldWidth = 100
    bitsOn = 10

    s = SDRCategoryEncoder(n=fieldWidth, w=bitsOn, name="foo", verbosity=2,
                           forced=True)

    encoded = numpy.zeros(fieldWidth)
    self.assertEqual(s.topDownCompute(encoded).value, "<UNKNOWN>")

    s.encodeIntoArray("catA", encoded)
    self.assertEqual(encoded.sum(), bitsOn)
    self.assertEqual(s.getScalars("catA"), 1)
    catA = encoded.copy()

    s.encodeIntoArray("catB", encoded)
    self.assertEqual(encoded.sum(), bitsOn)
    self.assertEqual(s.getScalars("catB"), 2)
    catB = encoded.copy()

    self.assertEqual(s.topDownCompute(catA).value, "catA")
    self.assertEqual(s.topDownCompute(catB).value, "catB")

    s.encodeIntoArray(SENTINEL_VALUE_FOR_MISSING_DATA, encoded)
    self.assertEqual(sum(encoded), 0)
    self.assertEqual(s.topDownCompute(encoded).value, "<UNKNOWN>")

    #Test Disabling Learning and autogrow
    s.setLearning(False)
    s.encodeIntoArray("catC", encoded)
    self.assertEqual(encoded.sum(), bitsOn)
    self.assertEqual(s.getScalars("catC"), 0)
    self.assertEqual(s.topDownCompute(encoded).value, "<UNKNOWN>")

    s.setLearning(True)
    s.encodeIntoArray("catC", encoded)
    self.assertEqual(encoded.sum(), bitsOn)
    self.assertEqual(s.getScalars("catC"), 3)
    self.assertEqual(s.topDownCompute(encoded).value, "catC")


  @unittest.skipUnless(
      capnp, "pycapnp is not installed, skipping serialization test.")
  def testReadWrite(self):
    categories = ["ES", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8",
                  "S9","S10", "S11", "S12", "S13", "S14", "S15", "S16",
                  "S17", "S18", "S19", "GB", "US"]

    fieldWidth = 100
    bitsOn = 10

    original = SDRCategoryEncoder(n=fieldWidth, w=bitsOn,
                                  categoryList=categories,
                                  name="foo", verbosity=0, forced=True)

    # internal check
    self.assertEqual(original.sdrs.shape, (32, fieldWidth))

    # ES
    es = original.encode("ES")
    self.assertEqual(es.sum(), bitsOn)
    self.assertEqual(es.shape, (fieldWidth,))
    self.assertEqual(es.sum(), bitsOn)

    decoded = original.decode(es)

    proto1 = SDRCategoryEncoderProto.new_message()
    original.write(proto1)

    # Write the proto to a temp file and read it back into a new proto
    with tempfile.TemporaryFile() as f:
      proto1.write(f)
      f.seek(0)
      proto2 = SDRCategoryEncoderProto.read(f)

    encoder = SDRCategoryEncoder.read(proto2)

    self.assertIsInstance(encoder, SDRCategoryEncoder)
    self.assertEqual(encoder.n, original.n)
    self.assertEqual(encoder.w, original.w)
    self.assertEqual(encoder.verbosity, original.verbosity)
    self.assertEqual(encoder.description, original.description)
    self.assertEqual(encoder.name, original.name)
    self.assertDictEqual(encoder.categoryToIndex, original.categoryToIndex)
    self.assertTrue(numpy.array_equal(encoder.encode("ES"), es))
    self.assertEqual(original.decode(encoder.encode("ES")),
                     encoder.decode(original.encode("ES")))
    self.assertEqual(decoded, encoder.decode(es))

    # Test autogrow serialization
    autogrow = SDRCategoryEncoder(n=fieldWidth, w=bitsOn, categoryList = None,
                                  name="bar", forced=True)

    es = autogrow.encode("ES")
    us = autogrow.encode("US")
    gs = autogrow.encode("GS")

    proto1 = SDRCategoryEncoderProto.new_message()
    autogrow.write(proto1)

    # Write the proto to a temp file and read it back into a new proto
    with tempfile.TemporaryFile() as f:
      proto1.write(f)
      f.seek(0)
      proto2 = SDRCategoryEncoderProto.read(f)

    t = SDRCategoryEncoder.read(proto2)

    self.assertTrue(numpy.array_equal(t.encode("ES"), es))
    self.assertTrue(numpy.array_equal(t.encode("US"), us))
    self.assertTrue(numpy.array_equal(t.encode("GS"), gs))



if __name__ == "__main__":
  unittest.main()
