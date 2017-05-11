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
import numpy as np

from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
from nupic.encoders.scalar import ScalarEncoder
from nupic.utils import MovingAverage



class AdaptiveScalarEncoder(ScalarEncoder):
  """
  This is an implementation of the scalar encoder that adapts the min and
  max of the scalar encoder dynamically. This is essential to the streaming
  model of the online prediction framework.

  Initialization of an adapive encoder using resolution or radius is not supported;
  it must be intitialized with n. This n is kept constant while the min and max of the
  encoder changes.

  The adaptive encoder must be have periodic set to false.

  The adaptive encoder may be initialized with a minval and maxval or with `None`
  for each of these. In the latter case, the min and max are set as the 1st and 99th
  percentile over a window of the past 100 records.

  **Note:** the sliding window may record duplicates of the values in the dataset,
  and therefore does not reflect the statistical distribution of the input data
  and may not be used to calculate the median, mean etc.

  For params, see :class:`~.nupic.encoders.scalar.ScalarEncoder`.

  :raises: Exception if input is periodic.

  """


  def __init__(self, w, minval=None, maxval=None, periodic=False, n=0, radius=0,
                resolution=0, name=None, verbosity=0, clipInput=True, forced=False):
    self._learningEnabled = True
    if periodic:
      #Adaptive scalar encoders take non-periodic inputs only
      raise Exception('Adaptive scalar encoder does not encode periodic inputs')
    assert n!=0           #An adaptive encoder can only be intialized using n

    super(AdaptiveScalarEncoder, self).__init__(w=w, n=n, minval=minval, maxval=maxval,
                                clipInput=True, name=name, verbosity=verbosity, forced=forced)
    self.recordNum=0    #how many inputs have been sent to the encoder?
    self.slidingWindow = MovingAverage(300)


  def _setEncoderParams(self):
    """
    Set the radius, resolution and range. These values are updated when minval
    and/or maxval change.
    """

    self.rangeInternal = float(self.maxval - self.minval)

    self.resolution = float(self.rangeInternal) / (self.n - self.w)
    self.radius = self.w * self.resolution
    self.range = self.rangeInternal + self.resolution

    # nInternal represents the output area excluding the possible padding on each side
    self.nInternal = self.n - 2 * self.padding

    # Invalidate the bucket values cache so that they get recomputed
    self._bucketValues = None


  def setFieldStats(self, fieldName, fieldStats):
    """
    TODO: document
    """
    #If the stats are not fully formed, ignore.
    if fieldStats[fieldName]['min'] == None or \
      fieldStats[fieldName]['max'] == None:
        return
    self.minval = fieldStats[fieldName]['min']
    self.maxval = fieldStats[fieldName]['max']
    if self.minval == self.maxval:
      self.maxval+=1
    self._setEncoderParams()


  def _setMinAndMax(self, input, learn):
    """
    Potentially change the minval and maxval using input.
    **The learn flag is currently not supported by cla regions.**
    """

    self.slidingWindow.next(input)

    if self.minval is None and self.maxval is None:
      self.minval = input
      self.maxval = input+1   #When the min and max and unspecified and only one record has been encoded
      self._setEncoderParams()

    elif learn:
      sorted = self.slidingWindow.getSlidingWindow()
      sorted.sort()

      minOverWindow = sorted[0]
      maxOverWindow = sorted[len(sorted)-1]

      if minOverWindow < self.minval:
        #initialBump = abs(self.minval-minOverWindow)*(1-(min(self.recordNum, 200.0)/200.0))*2      #decrement minval more aggressively in the beginning
        if self.verbosity >= 2:
          print "Input %s=%.2f smaller than minval %.2f. Adjusting minval to %.2f"\
                          % (self.name, input, self.minval, minOverWindow)
        self.minval = minOverWindow       #-initialBump
        self._setEncoderParams()

      if maxOverWindow > self.maxval:
        #initialBump = abs(self.maxval-maxOverWindow)*(1-(min(self.recordNum, 200.0)/200.0))*2     #decrement maxval more aggressively in the beginning
        if self.verbosity >= 2:
          print "Input %s=%.2f greater than maxval %.2f. Adjusting maxval to %.2f" \
                          % (self.name, input, self.maxval, maxOverWindow)
        self.maxval = maxOverWindow       #+initialBump
        self._setEncoderParams()


  def getBucketIndices(self, input, learn=None):
    """
    [overrides nupic.encoders.scalar.ScalarEncoder.getBucketIndices]
    """

    self.recordNum +=1
    if learn is None:
      learn = self._learningEnabled

    if type(input) is float and math.isnan(input):
      input = SENTINEL_VALUE_FOR_MISSING_DATA

    if input == SENTINEL_VALUE_FOR_MISSING_DATA:
      return [None]
    else:
      self._setMinAndMax(input, learn)
      return super(AdaptiveScalarEncoder, self).getBucketIndices(input)


  def encodeIntoArray(self, input, output,learn=None):
    """
    [overrides nupic.encoders.scalar.ScalarEncoder.encodeIntoArray]
    """

    self.recordNum +=1
    if learn is None:
      learn = self._learningEnabled
    if input == SENTINEL_VALUE_FOR_MISSING_DATA:
        output[0:self.n] = 0
    elif not math.isnan(input):
      self._setMinAndMax(input, learn)

    super(AdaptiveScalarEncoder, self).encodeIntoArray(input, output)

  def getBucketInfo(self, buckets):
    """
    [overrides nupic.encoders.scalar.ScalarEncoder.getBucketInfo]
    """

    if self.minval is None or self.maxval is None:
      return [EncoderResult(value=0, scalar=0,
                           encoding=numpy.zeros(self.n))]

    return super(AdaptiveScalarEncoder, self).getBucketInfo(buckets)


  def topDownCompute(self, encoded):
    """
    [overrides nupic.encoders.scalar.ScalarEncoder.topDownCompute]
    """

    if self.minval is None or self.maxval is None:
      return [EncoderResult(value=0, scalar=0,
                           encoding=numpy.zeros(self.n))]
    return super(AdaptiveScalarEncoder, self).topDownCompute(encoded)


  def __str__(self):
    string = "AdaptiveScalarEncoder:"
    string += "  min: {minval}".format(minval = self.minval)
    string += "  max: {maxval}".format(maxval = self.maxval)
    string += "  w:   {w}".format(w = self.w)
    string += "  n:   {n}".format(n = self.n)
    string += "  resolution: {resolution}".format(resolution = self.resolution)
    string += "  radius:     {radius}".format(radius = self.radius)
    string += "  periodic: {periodic}".format(periodic = self.periodic)
    string += "  nInternal: {nInternal}".format(nInternal = self.nInternal)
    string += "  rangeInternal: {rangeInternal}".format(rangeInternal = self.rangeInternal)
    string += "  padding: {padding}".format(padding = self.padding)
    return string

  @classmethod
  def read(cls, proto):
    encoder = super(AdaptiveScalarEncoder, cls).read(proto)
    encoder.recordNum = proto.recordNum
    encoder.slidingWindow = MovingAverage.read(proto.slidingWindow)
    return encoder


  def write(self, proto):
    super(AdaptiveScalarEncoder, self).write(proto)
    proto.recordNum = self.recordNum
    self.slidingWindow.write(proto.slidingWindow)
