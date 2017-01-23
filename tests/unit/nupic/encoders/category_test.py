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

"""Unit tests for category encoder"""

import tempfile
import unittest

import numpy

from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
from nupic.encoders.base import defaultDtype
from nupic.encoders.category import CategoryEncoder, UNKNOWN

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.encoders.category_capnp import CategoryEncoderProto



class CategoryEncoderTest(unittest.TestCase):
  '''Unit tests for CategoryEncoder class'''


  def testCategoryEncoder(self):
    categories = ["ES", "GB", "US"]

    # forced: is not recommended, but is used here for readability.
    # see scalar.py
    e = CategoryEncoder(w=3, categoryList=categories, forced=True)
    output = e.encode("US")
    expected = numpy.array([0,0,0,0,0,0,0,0,0,1,1,1], dtype=defaultDtype)
    self.assertTrue(numpy.array_equal(output, expected))

    # Test reverse lookup
    decoded = e.decode(output)
    (fieldsDict, fieldNames) = decoded
    self.assertEqual(len(fieldNames), 1)
    self.assertEqual(len(fieldsDict), 1)
    self.assertEqual(fieldNames[0], fieldsDict.keys()[0])
    (ranges, desc) = fieldsDict.values()[0]
    self.assertEqual(desc, "US")
    self.assertEqual(len(ranges), 1)
    self.assertTrue(numpy.array_equal(ranges[0], [3, 3]))

    # Test topdown compute
    for v in categories:
      output = e.encode(v)
      topDown = e.topDownCompute(output)
      self.assertEqual(topDown.value, v)
      self.assertEqual(topDown.scalar, e.getScalars(v)[0])

      bucketIndices = e.getBucketIndices(v)
      topDown = e.getBucketInfo(bucketIndices)[0]
      self.assertEqual(topDown.value, v)
      self.assertEqual(topDown.scalar, e.getScalars(v)[0])
      self.assertTrue(numpy.array_equal(topDown.encoding, output))
      self.assertEqual(topDown.value, e.getBucketValues()[bucketIndices[0]])



    # ---------------------
    # unknown category
    output = e.encode("NA")
    expected = numpy.array([1,1,1,0,0,0,0,0,0,0,0,0], dtype=defaultDtype)
    self.assertTrue(numpy.array_equal(output, expected))

    # Test reverse lookup
    decoded = e.decode(output)
    (fieldsDict, fieldNames) = decoded
    self.assertEqual(len(fieldNames), 1)
    self.assertEqual(len(fieldsDict), 1)
    self.assertEqual(fieldNames[0], fieldsDict.keys()[0])
    (ranges, desc) = fieldsDict.values()[0]
    self.assertEqual(len(ranges), 1)
    self.assertTrue(numpy.array_equal(ranges[0], [0, 0]))

    # Test topdown compute
    topDown = e.topDownCompute(output)
    self.assertEqual(topDown.value, UNKNOWN)
    self.assertEqual(topDown.scalar, 0)


    # --------------------------------
    # ES
    output = e.encode("ES")
    expected = numpy.array([0,0,0,1,1,1,0,0,0,0,0,0], dtype=defaultDtype)
    self.assertTrue(numpy.array_equal(output, expected))

    # MISSING VALUE
    outputForMissing = e.encode(SENTINEL_VALUE_FOR_MISSING_DATA)
    self.assertEqual(sum(outputForMissing), 0)

    # Test reverse lookup
    decoded = e.decode(output)
    (fieldsDict, fieldNames) = decoded
    self.assertEqual(len(fieldNames), 1)
    self.assertEqual(len(fieldsDict), 1)
    self.assertEqual(fieldNames[0], fieldsDict.keys()[0])
    (ranges, desc) = fieldsDict.values()[0]
    self.assertEqual(len(ranges), 1)
    self.assertTrue(numpy.array_equal(ranges[0], [1, 1]))

    # Test topdown compute
    topDown = e.topDownCompute(output)
    self.assertEqual(topDown.value, "ES")
    self.assertEqual(topDown.scalar, e.getScalars("ES")[0])


    # --------------------------------
    # Multiple categories
    output.fill(1)

    # Test reverse lookup
    decoded = e.decode(output)
    (fieldsDict, fieldNames) = decoded
    self.assertEqual(len(fieldNames), 1)
    self.assertEqual(len(fieldsDict), 1)
    self.assertEqual(fieldNames[0], fieldsDict.keys()[0])
    (ranges, desc) = fieldsDict.values()[0]
    self.assertEqual(len(ranges), 1)
    self.assertTrue(numpy.array_equal(ranges[0], [0, 3]))


    # -------------------------------------------------------------
    # Test with width = 1
    categories = ["cat1", "cat2", "cat3", "cat4", "cat5"]
      # forced: is not recommended, but is used here for readability.
      # see scalar.py
    e = CategoryEncoder(w=1, categoryList=categories, forced=True)
    for cat in categories:
      output = e.encode(cat)
      topDown = e.topDownCompute(output)
      self.assertEqual(topDown.value, cat)
      self.assertEqual(topDown.scalar, e.getScalars(cat)[0])


    # -------------------------------------------------------------
    # Test with width = 9, removing some bits end the encoded output
    categories = ["cat%d" % (x) for x in range(1, 10)]
     # forced: is not recommended, but is used here for readability.
     # see scalar.py
    e = CategoryEncoder(w=9, categoryList=categories, forced=True)
    for cat in categories:
      output = e.encode(cat)
      topDown = e.topDownCompute(output)
      self.assertEqual(topDown.value, cat)
      self.assertEqual(topDown.scalar, e.getScalars(cat)[0])

      # Get rid of 1 bit on the left
      outputNZs = output.nonzero()[0]
      output[outputNZs[0]] = 0
      topDown = e.topDownCompute(output)
      self.assertEqual(topDown.value, cat)
      self.assertEqual(topDown.scalar, e.getScalars(cat)[0])

      # Get rid of 1 bit on the right
      output[outputNZs[0]] = 1
      output[outputNZs[-1]] = 0
      topDown = e.topDownCompute(output)
      self.assertEqual(topDown.value, cat)
      self.assertEqual(topDown.scalar, e.getScalars(cat)[0])

      # Get rid of 4 bits on the left
      output.fill(0)
      output[outputNZs[-5:]] = 1
      topDown = e.topDownCompute(output)
      self.assertEqual(topDown.value, cat)
      self.assertEqual(topDown.scalar, e.getScalars(cat)[0])

      # Get rid of 4 bits on the right
      output.fill(0)
      output[outputNZs[0:5]] = 1
      topDown = e.topDownCompute(output)
      self.assertEqual(topDown.value, cat)
      self.assertEqual(topDown.scalar, e.getScalars(cat)[0])


    # OR together the output of 2 different categories, we should not get
    #  back the mean, but rather one or the other
    output1 = e.encode("cat1")
    output2 = e.encode("cat9")
    output = output1 + output2
    topDown = e.topDownCompute(output)
    self.assertTrue(topDown.scalar == e.getScalars("cat1")[0] \
            or topDown.scalar == e.getScalars("cat9")[0])



  @unittest.skipUnless(
      capnp, "pycapnp is not installed, skipping serialization test.")
  def testReadWrite(self):
    categories = ["ES", "GB", "US"]

    # forced: is not recommended, but is used here for readability. see
    # scalar.py
    original = CategoryEncoder(w=3, categoryList=categories, forced=True)
    output = original.encode("US")
    target = numpy.array([0,0,0,0,0,0,0,0,0,1,1,1], dtype=defaultDtype)
    self.assertTrue(numpy.array_equal(output, target))

    decoded = original.decode(output)

    proto1 = CategoryEncoderProto.new_message()
    original.write(proto1)

    # Write the proto to a temp file and read it back into a new proto
    with tempfile.TemporaryFile() as f:
      proto1.write(f)
      f.seek(0)
      proto2 = CategoryEncoderProto.read(f)

    encoder = CategoryEncoder.read(proto2)

    self.assertIsInstance(encoder, CategoryEncoder)
    self.assertEqual(encoder.verbosity, original.verbosity)
    self.assertEqual(encoder.width, original.width)
    self.assertEqual(encoder.description, original.description)
    self.assertEqual(encoder.name, original.name)
    self.assertDictEqual(encoder.categoryToIndex, original.categoryToIndex)
    self.assertDictEqual(encoder.indexToCategory, original.indexToCategory)
    self.assertTrue(numpy.array_equal(encoder.encode("US"), output))
    self.assertEqual(original.decode(encoder.encode("US")),
                     encoder.decode(original.encode("US")))
    self.assertEqual(decoded, encoder.decode(output))



if __name__ == '__main__':
  unittest.main()
