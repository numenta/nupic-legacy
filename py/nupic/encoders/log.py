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


from base import *
from scalar import ScalarEncoder

from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA

############################################################################
class LogEncoder(Encoder):
  """A Log encoder represents a floating point value on a logarithmic (decibel)
  scale.

  valueToEncode = 10 * log10(input)

  The default resolution (minimum difference in scaled values which is guaranteed
  to propduce different outputs) is 1 decibel. For example, the scaled values 10
  and 11 will be distinguishable in the output. In terms of the original input
  values, this means 10^1 (10) and 10^1.1 (12.5) will be distinguishable.

    resolution -- encoder resolution, in terms of scaled values. Default: 1 decibel
    minval -- must be greater than 0. Lower values are reset to this value
    maxval -- Higher values are reset to this value
  """

  ############################################################################
  def __init__(self, w = 5, resolution = 1.0, minval=0.10, maxval=10000,
                name="log", verbosity=0):

    self.encoders = None
    self.verbosity = verbosity
    self.minScaledValue = int(10 * math.log10(minval))
    self.maxScaledValue = int(math.ceil(10 * math.log10(maxval)))
    assert self.maxScaledValue > self.minScaledValue

    self.minval = 10 ** (self.minScaledValue / 10.0)
    self.maxval = 10 ** (self.maxScaledValue / 10.0)

    # Note: passing resolution=1 causes the test to topDownCompute
    # test to fail.  Fixed for now by always converting to float,
    # but should find the root cause.
    self.encoder = ScalarEncoder(w=w, minval = self.minScaledValue,
                    maxval=self.maxScaledValue,
                    periodic=False,
                    resolution=float(resolution))
    self.width = self.encoder.getWidth()
    self.description = [(name, 0)]
    self.name = name

    # This list is created by getBucketValues() the first time it is called,
    #  and re-created whenever our buckets would be re-arranged.
    self._bucketValues = None


  ############################################################################
  def getWidth(self):
    return self.width

  ############################################################################
  def getDescription(self):
    return self.description

  ############################################################################
  def _getScaledValue(self, input):
    """ Convert the input, which is in normal space, into log space
    """
    if input == SENTINEL_VALUE_FOR_MISSING_DATA:
      return None
    else:
      val = input
      if val < self.minval:
        val = self.minval
      elif val > self.maxval:
        val = self.maxval

      scaledVal = 10 * math.log10(val)
      return scaledVal

  ############################################################################
  def getBucketIndices(self, input):
    """ See the function description in base.py
    """

    # Get the scaled value
    scaledVal = self._getScaledValue(input)

    if scaledVal is None:
      return [None]
    else:
      return self.encoder.getBucketIndices(scaledVal)


  ############################################################################
  def encodeIntoArray(self, input, output):
    """ See the function description in base.py
    """

    # Get the scaled value
    scaledVal = self._getScaledValue(input)

    if scaledVal is None:
      output[0:] = 0
    else:
      self.encoder.encodeIntoArray(scaledVal, output)

      if self.verbosity >= 2:
        print "input:", input, "scaledVal:", scaledVal, "output:", output
        print "decoded:", self.decodedToStr(self.decode(output))


  ############################################################################
  def decode(self, encoded, parentFieldName=''):
    """ See the function description in base.py
    """

    # Get the scalar values from the underlying scalar encoder
    (fieldsDict, fieldNames) = self.encoder.decode(encoded)
    if len(fieldsDict) == 0:
      return (fieldsDict, fieldNames)

    # Expect only 1 field
    assert(len(fieldsDict) == 1)

    # Convert each range into normal space
    (inRanges, inDesc) = fieldsDict.values()[0]
    outRanges = []
    for (minV, maxV) in inRanges:
      outRanges.append((math.pow(10, minV / 10.0),
                        math.pow(10, maxV / 10.0)))


    # Generate a text description of the ranges
    desc = ""
    numRanges = len(outRanges)
    for i in xrange(numRanges):
      if outRanges[i][0] != outRanges[i][1]:
        desc += "%.2f-%.2f" % (outRanges[i][0], outRanges[i][1])
      else:
        desc += "%.2f" % (outRanges[i][0])
      if i < numRanges-1:
        desc += ", "

    # Return result
    if parentFieldName != '':
      fieldName = "%s.%s" % (parentFieldName, self.name)
    else:
      fieldName = self.name
    return ({fieldName: (outRanges, desc)}, [fieldName])


  ############################################################################
  def getBucketValues(self):
    """ See the function description in base.py """

    # Need to re-create?
    if self._bucketValues is None:
      scaledValues = self.encoder.getBucketValues()
      self._bucketValues = []
      for scaledValue in scaledValues:
        value = math.pow(10, scaledValue / 10.0)
        self._bucketValues.append(value)

    return self._bucketValues


  ############################################################################
  def getBucketInfo(self, buckets):
    """ See the function description in base.py
    """

    scaledResult = self.encoder.getBucketInfo(buckets)[0]
    scaledValue = scaledResult.value
    value = math.pow(10, scaledValue / 10.0)

    return [EncoderResult(value=value, scalar=value,
                         encoding = scaledResult.encoding)]

  ############################################################################
  def topDownCompute(self, encoded):
    """ See the function description in base.py
    """

    scaledResult = self.encoder.topDownCompute(encoded)[0]
    scaledValue = scaledResult.value
    value = math.pow(10, scaledValue / 10.0)

    return EncoderResult(value=value, scalar=value,
                         encoding = scaledResult.encoding)


  ############################################################################
  def closenessScores(self, expValues, actValues, fractional=True):
    """ See the function description in base.py
    """

    # Compute the percent error in log space
    if expValues[0] > 0:
      expValue = 10 * math.log10(expValues[0])
    else:
      expValue = self.minScaledValue

    if actValues  [0] > 0:
      actValue = 10 * math.log10(actValues[0])
    else:
      actValue = self.minScaledValue

    if fractional:
      err = abs(expValue - actValue)
      pctErr = err / (self.maxScaledValue - self.minScaledValue)
      pctErr = min(1.0, pctErr)
      closeness = 1.0 - pctErr
    else:
      err = abs(expValue - actValue)
      closeness = err

    #print "log::", "expValue:", expValues[0], "actValue:", actValues[0], \
    #      "closeness", closeness
    #import pdb; pdb.set_trace()
    return numpy.array([closeness])


############################################################################
def testLogEncoder():
  print "Testing LogEncoder...",

  l = LogEncoder(w=5, resolution=1, minval=1, maxval=10000, name="amount")
  assert l.getDescription() == [("amount", 0)]

  # -------------------------------------------------------------------
  # 10^0 -> 10^4 => 0 decibels -> 40 decibels;
  # 41 possible decibel values plus padding=4 = width 45
  assert l.getWidth() == 45
  value = 1.0
  output = l.encode(value)
  expected = [1, 1, 1, 1, 1] + 40 * [0]
  expected = numpy.array(expected, dtype='uint8')
  assert (output == expected).all()

  # Test reverse lookup
  decoded = l.decode(output)
  (fieldsDict, fieldNames) = decoded
  assert len(fieldsDict) == 1
  (ranges, desc) = fieldsDict.values()[0]
  print "decodedToStr of", ranges, "=>", l.decodedToStr(decoded)
  assert len(ranges) == 1 and numpy.array_equal(ranges[0], [1, 1])

  # MISSING VALUE
  mvOutput = l.encode(SENTINEL_VALUE_FOR_MISSING_DATA)
  assert sum(mvOutput) == 0

  # Test top-down
  value = l.minval
  while value <= l.maxval:
    output = l.encode(value)
    print "output of %f =>" % (value), output

    topDown = l.topDownCompute(output)
    print "topdown =>", topDown

    scaledVal = 10 * math.log10(value)
    minTopDown = math.pow(10, (scaledVal-l.encoder.resolution) / 10.0)
    maxTopDown = math.pow(10, (scaledVal+l.encoder.resolution) / 10.0)

    assert(topDown.value >= minTopDown and topDown.value <= maxTopDown)

    # Test bucket support
    bucketIndices = l.getBucketIndices(value)
    print "bucket index =>", bucketIndices[0]
    topDown = l.getBucketInfo(bucketIndices)[0]
    assert (topDown.value >= minTopDown and topDown.value <= maxTopDown)
    assert (topDown.scalar >= minTopDown and topDown.scalar <= maxTopDown)
    assert (topDown.encoding == output).all()
    assert (topDown.value == l.getBucketValues()[bucketIndices[0]])


    # Next value
    scaledVal += l.encoder.resolution/4
    value = math.pow(10, scaledVal / 10.0)


  # -------------------------------------------------------------------
  output = l.encode(100)
  # increase of 2 decades = 20 decibels
  # bit 0, 1 are padding; bit 3 is 1, ..., bit 22 is 20 (23rd bit)
  expected = 20 * [0] + [1, 1, 1, 1, 1] + 20 * [0]
  expected = numpy.array(expected, dtype='uint8')
  assert (output == expected).all()

  # Test reverse lookup
  decoded = l.decode(output)
  (fieldsDict, fieldNames) = decoded
  assert len(fieldsDict) == 1
  (ranges, desc) = fieldsDict.values()[0]
  assert len(ranges) == 1 and numpy.array_equal(ranges[0], [100, 100])
  print "decodedToStr of", ranges, "=>", l.decodedToStr(decoded)



  # -------------------------------------------------------------------
  output = l.encode(10000)
  expected = 40 * [0] + [1, 1, 1, 1, 1]
  expected = numpy.array(expected, dtype='uint8')
  assert (output == expected).all()

  # Test reverse lookup
  decoded = l.decode(output)
  (fieldsDict, fieldNames) = decoded
  assert len(fieldsDict) == 1
  (ranges, desc) = fieldsDict.values()[0]
  assert len(ranges) == 1 and numpy.array_equal(ranges[0], [10000, 10000])
  print "decodedToStr of", ranges, "=>", l.decodedToStr(decoded)


  print "passed."


################################################################################
if __name__=='__main__':

  # Run all tests
  testLogEncoder()