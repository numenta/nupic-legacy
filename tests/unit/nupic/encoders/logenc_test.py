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

"""Unit tests for logarithmic encoder"""

import numpy
import math
from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
from nupic.data.field_meta import FieldMetaType
import tempfile
import unittest

from nupic.encoders.logarithm import LogEncoder
from nupic.encoders.scalar import ScalarEncoder

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.encoders.logarithm_capnp import LogEncoderProto



class LogEncoderTest(unittest.TestCase):
  """Unit tests for LogEncoder class"""


  def testLogEncoder(self):
    # Create the encoder
    # use of forced=True is not recommended, but is used in the example for
    # readibility, see scalar.py
    le = LogEncoder(w=5,
                    resolution=0.1,
                    minval=1,
                    maxval=10000,
                    name="amount",
                    forced=True)

    # Verify we're setting the description properly
    self.assertEqual(le.getDescription(), [("amount", 0)])

    # Verify we're getting the correct field types
    types = le.getDecoderOutputFieldTypes()
    self.assertEqual(types[0], FieldMetaType.float)

    # Verify the encoder ends up with the correct width
    #
    # 10^0 -> 10^4 => 0 -> 4; With a resolution of 0.1
    # 41 possible values plus padding = 4 = width 45
    self.assertEqual(le.getWidth(), 45)

    # Verify we have the correct number of possible values
    self.assertEqual(len(le.getBucketValues()), 41)

    # Verify closeness calculations
    testTuples = [([1], [10000], 0.0),
                  ([1], [1000], 0.25),
                  ([1], [1], 1.0),
                  ([1], [-200], 1.0)]
    for tm in testTuples:
      expected = tm[0]
      actual = tm[1]
      expectedResult = tm[2]
      self.assertEqual(le.closenessScores(expected, actual),
                       expectedResult,
                       "exp: %s act: %s expR: %s" % (str(expected),
                                                     str(actual),
                                                     str(expectedResult)))

    # Verify a value of 1.0 is encoded as expected
    value = 1.0
    output = le.encode(value)

    # Our expected encoded representation of the value 1 is the first
    # w bits on in an array of len width.
    expected = [1, 1, 1, 1, 1] + 40 * [0]
    # Convert to numpy array
    expected = numpy.array(expected, dtype="uint8")

    self.assertTrue(numpy.array_equal(output, expected))

    # Test reverse lookup
    decoded = le.decode(output)
    (fieldsDict, _) = decoded
    self.assertEqual(len(fieldsDict), 1)
    (ranges, _) = fieldsDict.values()[0]
    self.assertEqual(len(ranges), 1)
    self.assertTrue(numpy.array_equal(ranges[0], [1, 1]))

    # Verify an input representing a missing value is handled properly
    mvOutput = le.encode(SENTINEL_VALUE_FOR_MISSING_DATA)
    self.assertEqual(sum(mvOutput), 0)

    # Test top-down for all values
    value = le.minval
    while value <= le.maxval:

      output = le.encode(value)
      topDown = le.topDownCompute(output)

      # Do the scaling by hand here.
      scaledVal = math.log10(value)

      # Find the range of values that would also produce this top down
      # output.
      minTopDown = math.pow(10, (scaledVal - le.encoder.resolution))
      maxTopDown = math.pow(10, (scaledVal + le.encoder.resolution))

      # Verify the range surrounds this scaled val
      self.assertGreaterEqual(topDown.value, minTopDown)
      self.assertLessEqual(topDown.value, maxTopDown)

      # Test bucket support
      bucketIndices = le.getBucketIndices(value)
      topDown = le.getBucketInfo(bucketIndices)[0]

      # Verify our reconstructed value is in the valid range
      self.assertGreaterEqual(topDown.value, minTopDown)
      self.assertLessEqual(topDown.value, maxTopDown)

      # Same for the scalar value
      self.assertGreaterEqual(topDown.scalar, minTopDown)
      self.assertLessEqual(topDown.scalar, maxTopDown)

      # That the encoding portion of our EncoderResult matched the result of
      # encode()
      self.assertTrue(numpy.array_equal(topDown.encoding, output))

      # Verify our reconstructed value is the same as the bucket value
      bucketValues = le.getBucketValues()
      self.assertEqual(topDown.value,
                       bucketValues[bucketIndices[0]])

      # Next value
      scaledVal += le.encoder.resolution / 4.0
      value = math.pow(10, scaledVal)

    # Verify next power of 10 encoding
    output = le.encode(100)
    # increase of 2 decades = 20 decibels
    # bit 0, 1 are padding; bit 3 is 1, ..., bit 22 is 20 (23rd bit)
    expected = 20 * [0] + [1, 1, 1, 1, 1] + 20 * [0]
    expected = numpy.array(expected, dtype="uint8")
    self.assertTrue(numpy.array_equal(output, expected))

    # Test reverse lookup
    decoded = le.decode(output)
    (fieldsDict, _) = decoded
    self.assertEqual(len(fieldsDict), 1)
    (ranges, _) = fieldsDict.values()[0]
    self.assertEqual(len(ranges), 1)
    self.assertTrue(numpy.array_equal(ranges[0], [100, 100]))

    # Verify next power of 10 encoding
    output = le.encode(10000)
    expected = 40 * [0] + [1, 1, 1, 1, 1]
    expected = numpy.array(expected, dtype="uint8")
    self.assertTrue(numpy.array_equal(output, expected))

    # Test reverse lookup
    decoded = le.decode(output)
    (fieldsDict, _) = decoded
    self.assertEqual(len(fieldsDict), 1)
    (ranges, _) = fieldsDict.values()[0]
    self.assertEqual(len(ranges), 1)
    self.assertTrue(numpy.array_equal(ranges[0], [10000, 10000]))


  def testGetBucketValues(self):
    """
    Verify that the values of buckets are as expected for given
    init params
    """

    # Create the encoder
    le = LogEncoder(w=5,
                    resolution=0.1,
                    minval=1,
                    maxval=10000,
                    name="amount",
		                forced=True)

    # Build our expected values
    inc = 0.1
    exp = 0
    expected = []
    # Incrementing to exactly 4.0 runs into fp issues
    while exp <= 4.0001:
      val = 10 ** exp
      expected.append(val)
      exp += inc

    expected = numpy.array(expected)
    actual = numpy.array(le.getBucketValues())

    numpy.testing.assert_almost_equal(expected, actual, 7)

  def testInitWithRadius(self):
    """
    Verifies you can use radius to specify a log encoder
    """

    # Create the encoder
    le = LogEncoder(w=1,
                    radius=1,
                    minval=1,
                    maxval=10000,
                    name="amount",
		                forced=True)


    self.assertEqual(le.encoder.n, 5)

    # Verify a a couple powers of 10 are encoded as expected
    value = 1.0
    output = le.encode(value)
    expected = [1, 0, 0, 0, 0]
    # Convert to numpy array
    expected = numpy.array(expected, dtype="uint8")
    self.assertTrue(numpy.array_equal(output, expected))

    value = 100.0
    output = le.encode(value)
    expected = [0, 0, 1, 0, 0]
    # Convert to numpy array
    expected = numpy.array(expected, dtype="uint8")
    self.assertTrue(numpy.array_equal(output, expected))


  def testInitWithN(self):
    """
    Verifies you can use N to specify a log encoder
    """
    # Create the encoder
    n = 100
    le = LogEncoder(n=n, forced=True)
    self.assertEqual(le.encoder.n, n)


  def testMinvalMaxVal(self):
    """
    Verifies unusual instances of minval and maxval are handled properly
    """

    self.assertRaises(ValueError, LogEncoder, n=100, minval=0, maxval=-100,
                      forced=True)
    self.assertRaises(ValueError, LogEncoder, n=100, minval=0, maxval=1e-07,
                      forced=True)

    le = LogEncoder(n=100, minval=42, maxval=1.3e12, forced=True)

    expectedRadius = 0.552141792732
    expectedResolution = 0.110428358546
    self.assertAlmostEqual(le.encoder.radius, expectedRadius)
    self.assertAlmostEqual(le.encoder.resolution, expectedResolution)


  @unittest.skipUnless(
      capnp, "pycapnp is not installed, skipping serialization test.")
  def testReadWrite(self):
    le = LogEncoder(w=5,
                    resolution=0.1,
                    minval=1,
                    maxval=10000,
                    name="amount",
                    forced=True)

    originalValue = le.encode(1.0)

    proto1 = LogEncoderProto.new_message()
    le.write(proto1)

    # Write the proto to a temp file and read it back into a new proto
    with tempfile.TemporaryFile() as f:
      proto1.write(f)
      f.seek(0)
      proto2 = LogEncoderProto.read(f)

    encoder = LogEncoder.read(proto2)

    self.assertIsInstance(encoder, LogEncoder)

    self.assertEqual(encoder.minScaledValue, le.minScaledValue)
    self.assertEqual(encoder.maxScaledValue, le.maxScaledValue)
    self.assertEqual(encoder.minval, le.minval)
    self.assertEqual(encoder.maxval, le.maxval)
    self.assertEqual(encoder.name, le.name)
    self.assertEqual(encoder.verbosity, le.verbosity)
    self.assertEqual(encoder.clipInput, le.clipInput)
    self.assertEqual(encoder.width, le.width)
    self.assertEqual(encoder.description, le.description)
    self.assertIsInstance(encoder.encoder, ScalarEncoder)
    self.assertTrue(numpy.array_equal(encoder.encode(1), originalValue))
    self.assertEqual(le.decode(encoder.encode(1)),
                     encoder.decode(le.encode(1)))

    # Feed in a new value and ensure the encodings match
    result1 = le.encode(10)
    result2 = encoder.encode(10)
    self.assertTrue(numpy.array_equal(result1, result2))



if __name__ == "__main__":
  unittest.main()
