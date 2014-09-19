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

import math
import sys

import numpy

from nupic.encoders.scalar import ScalarEncoder
from nupic.data.fieldmeta import FieldMetaType
from nupic.encoders.base import EncoderResult


class LogEncoder(ScalarEncoder):
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
               w=5, #TODO save is >=21
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
    lowLimit = sys.float_info.min
    hiLimit = sys.float_info.max

    # Limit minval as log10(0) is undefined.
    if minval < lowLimit:
      raise ValueError("log(0) is undefined, your specified minval= %r is below system \
          supported limit= %r" % (minval, lowLimit))

    if maxval > hiLimit:
      raise ValueError("Given maxvalue=%r is too high! Limit is %r" % (maxval, hiLimit))


    # Scale values for calculations within the class
    self.minScaledValue = math.log10(minval)
    self.maxScaledValue = math.log10(maxval)
    self.minvalRaw = minval # different than minval/maxval after super() call
    self.maxvalRaw = maxval
    self.resolutionRaw=resolution
    
    if not self.maxScaledValue > self.minScaledValue:
      raise ValueError("Max val must be larger, in log space, than min val.")
      
    super(LogEncoder, self).__init__(w=w,
                                 minval=self.minScaledValue,
                                 maxval=self.maxScaledValue,
                                 periodic=periodic,
                                 n=n,
                                 radius=radius,
                                 resolution=resolution,
				 name=name,
                                 verbosity=verbosity,
                                 clipInput=clipInput,
				 forced=forced)

    # This list is created by getBucketValues() the first time it is called,
    #  and re-created whenever our buckets would be re-arranged.
    self._bucketValues = None

  ############################################################################
  def getDecoderOutputFieldTypes(self):
    """
    Encoder class virtual method override
    """
    return (FieldMetaType.float, )

  ############################################################################
  def _getScaledValue(self, inpt):
    """
    Convert the input, which is in normal space, into log space
    """
    if inpt == self.SENTINEL_VALUE_FOR_MISSING_DATA:
      return None
    else:
      val = inpt
      if val < self.minvalRaw:
        val = self.minvalRaw
      elif val > self.maxvalRaw:
        val = self.maxvalRaw

      scaledVal = math.log10(val) #TODO do other log too
      return scaledVal

  ###########################################################################
  def _getDescaledValue(self, scaledInpt):
    """
    convert from log-space back to normal space
    """
    if scaledInpt == self.SENTINEL_VALUE_FOR_MISSING_DATA:
      return None

    val = scaledInpt
    if val < self.minval:
      val = self.minval
    elif val > self.maxval:
      val = self.maxval

    rawVal = math.pow(10, val) #TODO do other log too
    return rawVal


  ############################################################################
  def getBucketIndices(self, inpt):
    """
    See the function description in base.py
    """

    # Get the scaled value
    scaledVal = self._getScaledValue(inpt)

    return super(LogEncoder, self).getBucketIndices(scaledVal)

  ############################################################################
  def encodeIntoArray(self, inpt, output, learn=True):
    """
    See the function description in base.py
    """

    # Get the scaled value
    scaledVal = self._getScaledValue(inpt)

    if scaledVal is None:
      output[0:] = 0
    else:
      super(LogEncoder, self).encodeIntoArray(scaledVal, output, learn)

    for i in xrange(len(output)):
      output[i]=float(output[i])

      if self.verbosity >= 2:
        print "input:", inpt, "scaledVal:", scaledVal, "output:", output
        print "decoded:", self.decodedToStr(self.decode(output))

  ############################################################################
  def decode(self, encoded, parentFieldName=''):
    """
    See the function description in base.py
    """

    # Get the scalar values from the underlying scalar encoder
    (fieldsDict, fieldNames) = super(LogEncoder, self).decode(encoded)
    if len(fieldsDict) == 0:
      return (fieldsDict, fieldNames)

    # Expect only 1 field
    assert(len(fieldsDict) == 1)

    # Convert each range into normal space
    (inRanges, inDesc) = fieldsDict.values()[0]
    outRanges = []
    for (minV, maxV) in inRanges:
      outRanges.append((math.pow(10, minV), #TODO do other log too
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

  ############################################################################
  def getBucketValues(self):
    """
    See the function description in base.py
    """

    # Need to re-create?
    if self._bucketValues is None:
      scaledValues = super(LogEncoder, self).getBucketValues()
      self._bucketValues = []
      for scaledValue in scaledValues:
        value = scaledValue
        self._bucketValues.append(value)

    return self._bucketValues

  ############################################################################
  def getBucketInfo(self, buckets):
    """
    See the function description in base.py
    """

    scaledResult = super(LogEncoder, self).getBucketInfo(buckets)[0]
    scaledValue = scaledResult.value
    value = math.pow(10, scaledValue)

    return [EncoderResult(value=value, scalar=value,
                         encoding = scaledResult.encoding)]

  ############################################################################
  def topDownCompute(self, encoded):
    """
    See the function description in base.py
    """

    scaledResult = super(LogEncoder, self).topDownCompute(encoded)[0]
    scaledValue = scaledResult.value
    value = math.pow(10, scaledValue)

    return EncoderResult(value=value, scalar=value,
                         encoding = scaledResult.encoding)

  ############################################################################
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
