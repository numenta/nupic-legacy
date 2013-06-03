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

from scalar import *
import numpy as np
import math

class AdaptiveScalarEncoder(ScalarEncoder):
  """
  This is an implementation of the scalar encoder that adapts the min and
  max of the scalar encoder dynamically. This is essential to the streaming
  model of the online prediction framework.

  Initialization of an adapive encoder using resolution or radius is not supported;
  it must be intitialized with n. This n is kept constant while the min and max of the
  encoder changes.
  The adaptive encoder must be have periodic set to false.
  The adaptive encoder my be initiliazed with a minval and maxvak or with 'None'
  for each of these. In the latter case, the min and max are set as the 1st and 99th
  percentile over a window of the past 100 records.

  Note: the sliding window may record duplicates of the values in the dataset,
  and therefore does not reflect the statistical distribution of the input data
  and may not be used to calculate the median, mean etc.
  """

  ############################################################################
  def __init__(self, w, minval=None, maxval=None, periodic=False, n=0, radius=0,
                resolution=0, name=None, verbosity=0, clipInput=True):
    """[ScalarEncoder class method override]"""
    self._learningEnabled = True
    if periodic:
      #Adaptive scalar encoders take non-periodic inputs only
      raise Exception('Adaptive scalar encoder does not encode periodic inputs')
    assert n!=0           #An adaptive encoder can only be intialized using n

    super(AdaptiveScalarEncoder, self).__init__(w=w, n=n, minval=minval, maxval=maxval,
                                clipInput=True, name=name, verbosity=verbosity)
    self.recordNum=0    #how many inputs have been sent to the encoder?
    self.slidingWindow = np.array([])
    self.windowSize = 300

  ############################################################################
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

  ############################################################################
  def setFieldStats(self, fieldName, fieldStats):
    #If the stats are not fully formed, ignore.
    if fieldStats[fieldName]['min'] == None or \
      fieldStats[fieldName]['max'] == None:
        return
    self.minval = fieldStats[fieldName]['min']
    self.maxval = fieldStats[fieldName]['max']
    if self.minval == self.maxval:
      self.maxval+=1
    self._setEncoderParams()

  ############################################################################
  def _setMinAndMax(self, input, learn):
    """
    Potentially change the minval and maxval using input.
    **The learn flag is currently not supported by cla regions.
    """

    if len(self.slidingWindow)>=self.windowSize:
      self.slidingWindow = np.delete(self.slidingWindow, 0)
    self.slidingWindow = np.append(self.slidingWindow, [input])

    if self.minval is None and self.maxval is None:
      self.minval = input
      self.maxval = input+1   #When the min and max and unspecified and only one record has been encoded
      self._setEncoderParams()

    elif learn:
      sorted = np.array(self.slidingWindow)
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

  ############################################################################
  def getBucketIndices(self, input, learn=None):
    """[ScalarEncoder class method override]"""

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

  ############################################################################
  def encodeIntoArray(self, input, output,learn=None):
    """[ScalarEncoder class method override]"""

    self.recordNum +=1
    if learn is None:
      learn = self._learningEnabled
    if input == SENTINEL_VALUE_FOR_MISSING_DATA:
        output[0:self.n] = 0
    elif not math.isnan(input):
      self._setMinAndMax(input, learn)

    super(AdaptiveScalarEncoder, self).encodeIntoArray(input, output)


  ############################################################################
  def getBucketInfo(self, buckets):
    """[ScalarEncoder class method override]"""

    if self.minval is None or self.maxval is None:
      return [EncoderResult(value=0, scalar=0,
                           encoding=numpy.zeros(self.n))]

    return super(AdaptiveScalarEncoder, self).getBucketInfo(buckets)

  ############################################################################
  def topDownCompute(self, encoded):
    """[ScalarEncoder class method override]"""

    if self.minval is None or self.maxval is None:
      return [EncoderResult(value=0, scalar=0,
                           encoding=numpy.zeros(self.n))]
    return super(AdaptiveScalarEncoder, self).topDownCompute(encoded)

  ############################################################################
  def dump(self):
    print "AdaptiveScalarEncoder:"
    print "  min: %f" % self.minval
    print "  max: %f" % self.maxval
    print "  w:   %d" % self.w
    print "  n:   %d" % self.n
    print "  resolution: %f" % self.resolution
    print "  radius:     %f" % self.radius
    print "  periodic: %s" % self.periodic
    print "  nInternal: %d" % self.nInternal
    print "  rangeInternal: %f" % self.rangeInternal
    print "  padding: %d" % self.padding


############################################################################
def testAdaptiveScalarEncoder():
  print "Testing AdaptiveScalarEncoder...",

  # test missing values
  mv = AdaptiveScalarEncoder(name='mv', n=14, w=3, minval=1, maxval=8, periodic=False)
  empty = mv.encode(SENTINEL_VALUE_FOR_MISSING_DATA)
  print "\nEncoded missing data \'None\' as %s" % empty
  assert empty.sum() == 0

  # ============================================================================
  # Non-periodic encoder, min and max specified
  l = AdaptiveScalarEncoder(name='scalar', n=14, w=5, minval=1, maxval=10,
                            periodic=False)
  assert (l.encode(1) == numpy.array([1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                     dtype=defaultDtype)).all()
  assert (l.encode(2) == numpy.array([0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                                     dtype=defaultDtype)).all()
  assert (l.encode(10) == numpy.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
                                      dtype=defaultDtype)).all()

  # -------------------------------------------------------------------------
  # Test the input description generation and topDown decoding
  v = l.minval
  print "\nTesting non-periodic encoder decoding, resolution of %f..." % \
          l.resolution
  while v < l.maxval:
    output = l.encode(v)
    decoded = l.decode(output)
    print "decoding", output, "(%f)=>" % v, l.decodedToStr(decoded)

    (fieldsDict, fieldNames) = decoded
    assert len(fieldsDict) == 1
    (ranges, desc) = fieldsDict.values()[0]
    assert len(ranges) == 1
    (rangeMin, rangeMax) = ranges[0]
    assert (rangeMin == rangeMax)
    assert abs(rangeMin - v) < l.resolution

    topDown = l.topDownCompute(output)[0]
    print "topdown =>", topDown
    assert abs(topDown.value - v) <= l.resolution

    # Test bucket support
    bucketIndices = l.getBucketIndices(v)
    print "bucket index =>", bucketIndices[0]
    topDown = l.getBucketInfo(bucketIndices)[0]
    assert abs(topDown.value - v) <= l.resolution / 2
    assert (topDown.value == l.getBucketValues()[bucketIndices[0]])
    assert topDown.scalar == topDown.value
    assert (topDown.encoding == output).all()

    # Next value
    v += l.resolution / 4

  # Make sure we can fill in holes
  decoded = l.decode(numpy.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1]))
  (fieldsDict, fieldNames) = decoded
  assert len(fieldsDict) == 1
  (ranges, desc) = fieldsDict.values()[0]
  assert len(ranges) == 1 and numpy.array_equal(ranges[0], [10, 10])
  print "decodedToStr of", ranges, "=>", l.decodedToStr(decoded)

  decoded = l.decode(numpy.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1]))
  (fieldsDict, fieldNames) = decoded
  assert len(fieldsDict) == 1
  (ranges, desc) = fieldsDict.values()[0]
  assert len(ranges) == 1 and numpy.array_equal(ranges[0], [10, 10])
  print "decodedToStr of", ranges, "=>", l.decodedToStr(decoded)


  def _dumpParams(enc):
    return (enc.n, enc.w, enc.minval, enc.maxval, enc.resolution,
              enc.windowSize, enc._learningEnabled, enc.recordNum,
              enc.radius, enc.rangeInternal, enc.padding, enc.nInternal)

  def _verify(v, encoded, expV=None):
    if expV is None:
      expV = v
    assert (l.encode(v) == numpy.array(encoded, dtype=defaultDtype)).all()
    assert abs(l.getBucketInfo(l.getBucketIndices(v))[0].value - expV) <= \
                  l.resolution/2

  def _verifyNot(v, encoded):
    assert not (l.encode(v) == numpy.array(encoded, dtype=defaultDtype)).all()

  # ============================================================================
  # Non-periodic encoder, min and max not specified
  l = AdaptiveScalarEncoder(name='scalar', n=14, w=5, minval=None, maxval=None,
                            periodic=False)
  _verify(1, [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
  _verify(2, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
  _verify(10, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
  _verify(3, [0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0])
  _verify(-9, [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
  _verify(-8, [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
  _verify(-7, [0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0])
  _verify(-6, [0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0])
  _verify(-5, [0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0])
  _verify(0, [0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0])
  _verify(8, [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0])
  _verify(8, [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0])
  _verify(10, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
  _verify(11, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
  _verify(12, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
  _verify(13, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
  _verify(14, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
  _verify(15, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1])



  #Test switching learning off
  l = AdaptiveScalarEncoder(name='scalar', n=14, w=5, minval=1, maxval=10,
                            periodic=False)
  _verify(1, [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
  _verify(10, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
  _verify(20, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
  _verify(10, [0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0])


  l.setLearning(False)
  _verify(30, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1], expV=20)
  _verify(20, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
  _verify(-10, [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0], expV=1)
  _verify(-1, [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0], expV=1)


  l.setLearning(True)
  _verify(30, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
  _verifyNot(20, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
  _verify(-10, [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
  _verifyNot(-1, [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0])

  #Test setting the min and max using setFieldStats

  print "passed"
  sfs = AdaptiveScalarEncoder(name='scalar', n=14, w=5, minval=1, maxval=10,
                            periodic=False)
  reg = AdaptiveScalarEncoder(name='scalar', n=14, w=5, minval=1, maxval=100,
                            periodic=False)
  assert _dumpParams(sfs) != _dumpParams(reg) , "Params should not be equal,"\
            "since the two encoders were instantiated with different values."
  # set the min and the max using sFS to 1,100 respectively.
  sfs.setFieldStats('this',{"this":{"min":1,"max":100}})

  #Now the parameters for both should be the same
  assert _dumpParams(sfs) == _dumpParams(reg) ,"Params should now be equal,"\
        "but they are not.sFS should be equivalent to initialization."




################################################################################
if __name__ == '__main__':

  # Run all tests
  testAdaptiveScalarEncoder()
