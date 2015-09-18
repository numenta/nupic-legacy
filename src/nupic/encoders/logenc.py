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

import math

import numpy
from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
from nupic.data.fieldmeta import FieldMetaType
from nupic.encoders.base import Encoder, EncoderResult
from nupic.encoders.scalar import ScalarEncoder


class LogEncoder(Encoder):
  """
  This class wraps the ScalarEncoder class.

  A Log encoder represents a floating point value on a logarithmic scale.

  valueToEncode = log10(input)

    w -- number of bits to set in output
    minval -- minimum input value. must be greater than 0. Lower values are
              reset to this value
    maxval -- maximum input value (input is strictly less if periodic == True)
    periodic -- If true, then the input value "wraps around" such that minval =
              maxval For a periodic value, the input must be strictly less than
              maxval, otherwise maxval is a true upper bound.

    Exactly one of n, radius, resolution must be set. "0" is a special
    value that means "not set".

    n -- number of bits in the representation (must be > w)
    radius -- inputs separated by more than this distance in log space will have
              non-overlapping representations
    resolution -- The minimum change in scaled value needed to produce a change
                  in encoding. This should be specified in log space. For
                  example, the scaled values 10 and 11 will be distinguishable
                  in the output. In terms of the original input values, this
                  means 10^1 (1) and 10^1.1 (1.25) will be distinguishable.
    name -- an optional string which will become part of the description
    verbosity -- level of debugging output you want the encoder to provide.
    clipInput -- if true, non-periodic inputs smaller than minval or greater
                  than maxval will be clipped to minval/maxval
    forced -- (default False), if True, skip some safety checks

  """

  def __init__(self,
               w=5,
               minval=1e-07,
               maxval=10000,
               periodic=False,
               n=0,
               radius=0,
               resolution=0,
               name="log",
               verbosity=0,
               clipInput=True,
               forced=False):

    # Lower bound for log encoding near machine precision limit
    lowLimit = 1e-07

    # Limit minval as log10(0) is undefined.
    if minval < lowLimit:
      minval = lowLimit

    # Check that minval is still lower than maxval
    if not minval < maxval:
      raise ValueError("Max val must be larger than min val or the lower limit "
                       "for this encoder %.7f" % lowLimit)

    self.encoders = None
    self.verbosity = verbosity

    # Scale values for calculations within the class
    self.minScaledValue = math.log10(minval)
    self.maxScaledValue = math.log10(maxval)

    if not self.maxScaledValue > self.minScaledValue:
      raise ValueError("Max val must be larger, in log space, than min val.")

    self.clipInput = clipInput
    self.minval = minval
    self.maxval = maxval

    self.encoder = ScalarEncoder(w=w,
                                 minval=self.minScaledValue,
                                 maxval=self.maxScaledValue,
                                 periodic=False,
                                 n=n,
                                 radius=radius,
                                 resolution=resolution,
                                 verbosity=self.verbosity,
                                 clipInput=self.clipInput,
				 forced=forced)
    self.width = self.encoder.getWidth()
    self.description = [(name, 0)]
    self.name = name

    # This list is created by getBucketValues() the first time it is called,
    #  and re-created whenever our buckets would be re-arranged.
    self._bucketValues = None


  def getWidth(self):
    return self.width


  def getDescription(self):
    return self.description


  def getDecoderOutputFieldTypes(self):
    """
    Encoder class virtual method override
    """
    return (FieldMetaType.float, )


  def _getScaledValue(self, inpt):
    """
    Convert the input, which is in normal space, into log space
    """
    if inpt == SENTINEL_VALUE_FOR_MISSING_DATA:
      return None
    else:
      val = inpt
      if val < self.minval:
        val = self.minval
      elif val > self.maxval:
        val = self.maxval

      scaledVal = math.log10(val)
      return scaledVal


  def getBucketIndices(self, inpt):
    """
    See the function description in base.py
    """

    # Get the scaled value
    scaledVal = self._getScaledValue(inpt)

    if scaledVal is None:
      return [None]
    else:
      return self.encoder.getBucketIndices(scaledVal)


  def encodeIntoArray(self, inpt, output):
    """
    See the function description in base.py
    """

    # Get the scaled value
    scaledVal = self._getScaledValue(inpt)

    if scaledVal is None:
      output[0:] = 0
    else:
      self.encoder.encodeIntoArray(scaledVal, output)

      if self.verbosity >= 2:
        print "input:", inpt, "scaledVal:", scaledVal, "output:", output
        print "decoded:", self.decodedToStr(self.decode(output))


  def decode(self, encoded, parentFieldName=''):
    """
    See the function description in base.py
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
      outRanges.append((math.pow(10, minV),
                        math.pow(10, maxV)))

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


  def getBucketValues(self):
    """
    See the function description in base.py
    """

    # Need to re-create?
    if self._bucketValues is None:
      scaledValues = self.encoder.getBucketValues()
      self._bucketValues = []
      for scaledValue in scaledValues:
        value = math.pow(10, scaledValue)
        self._bucketValues.append(value)

    return self._bucketValues


  def getBucketInfo(self, buckets):
    """
    See the function description in base.py
    """

    scaledResult = self.encoder.getBucketInfo(buckets)[0]
    scaledValue = scaledResult.value
    value = math.pow(10, scaledValue)

    return [EncoderResult(value=value, scalar=value,
                         encoding = scaledResult.encoding)]


  def topDownCompute(self, encoded):
    """
    See the function description in base.py
    """

    scaledResult = self.encoder.topDownCompute(encoded)[0]
    scaledValue = scaledResult.value
    value = math.pow(10, scaledValue)

    return EncoderResult(value=value, scalar=value,
                         encoding = scaledResult.encoding)


  def closenessScores(self, expValues, actValues, fractional=True):
    """
    See the function description in base.py
    """

    # Compute the percent error in log space
    if expValues[0] > 0:
      expValue = math.log10(expValues[0])
    else:
      expValue = self.minScaledValue

    if actValues  [0] > 0:
      actValue = math.log10(actValues[0])
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


  @classmethod
  def read(cls, proto):
    encoder = object.__new__(cls)
    encoder.verbosity = proto.verbosity
    encoder.minScaledValue = proto.minScaledValue
    encoder.maxScaledValue = proto.maxScaledValue
    encoder.clipInput = proto.clipInput
    encoder.minval = proto.minval
    encoder.maxval = proto.maxval
    encoder.encoder = ScalarEncoder.read(proto.encoder)
    encoder.name = proto.name
    encoder.width = encoder.encoder.getWidth()
    encoder.description = [(encoder.name, 0)]
    encoder._bucketValues = None
    return encoder


  def write(self, proto):
    proto.verbosity = self.verbosity
    proto.minScaledValue = self.minScaledValue
    proto.maxScaledValue = self.maxScaledValue
    proto.clipInput = self.clipInput
    proto.minval = self.minval
    proto.maxval = self.maxval
    self.encoder.write(proto.encoder)
    proto.name = self.name
