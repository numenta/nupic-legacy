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

import math
import numbers

import numpy

from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
from nupic.data.fieldmeta import FieldMetaType
from nupic.bindings.math import SM32, GetNTAReal
from nupic.encoders.base import Encoder, EncoderResult



DEFAULT_RADIUS = 0
DEFAULT_RESOLUTION = 0



class ScalarEncoder(Encoder):
  """
  A scalar encoder encodes a numeric (floating point) value into an array
  of bits. The output is 0's except for a contiguous block of 1's. The
  location of this contiguous block varies continuously with the input value.

  The encoding is linear. If you want a nonlinear encoding, just transform
  the scalar (e.g. by applying a logarithm function) before encoding.
  It is not recommended to bin the data as a pre-processing step, e.g.
  "1" = $0 - $.20, "2" = $.21-$0.80, "3" = $.81-$1.20, etc. as this
  removes a lot of information and prevents nearby values from overlapping
  in the output. Instead, use a continuous transformation that scales
  the data (a piecewise transformation is fine).


  Parameters:
  -----------------------------------------------------------------------------
  w --        The number of bits that are set to encode a single value - the
                "width" of the output signal
              restriction: w must be odd to avoid centering problems.

  minval --   The minimum value of the input signal.

  maxval --   The upper bound of the input signal

  periodic -- If true, then the input value "wraps around" such that minval = maxval
              For a periodic value, the input must be strictly less than maxval,
              otherwise maxval is a true upper bound.

  There are three mutually exclusive parameters that determine the overall size of
  of the output. Only one of these should be specifed to the constructor:

  n      --      The number of bits in the output. Must be greater than or equal to w
  radius --      Two inputs separated by more than the radius have non-overlapping
                  representations. Two inputs separated by less than the radius will
                  in general overlap in at least some of their bits. You can think
                  of this as the radius of the input.
  resolution --  Two inputs separated by greater than, or equal to the resolution are guaranteed
                  to have different representations.

  Note: radius and resolution are specified w.r.t the input, not output. w is
  specified w.r.t. the output.

  Example:
  day of week.
  w = 3
  Minval = 1 (Monday)
  Maxval = 8 (Monday)
  periodic = true
  n = 14
  [equivalently: radius = 1.5 or resolution = 0.5]

  The following values would encode midnight -- the start of the day
  monday (1)   -> 11000000000001
  tuesday(2)   -> 01110000000000
  wednesday(3) -> 00011100000000
  ...
  sunday (7)   -> 10000000000011

  Since the resolution is 12 hours, we can also encode noon, as
  monday noon  -> 11100000000000
  monday midnt-> 01110000000000
  tuesday noon -> 00111000000000
  etc.


  It may not be natural to specify "n", especially with non-periodic
  data. For example, consider encoding an input with a range of 1-10
  (inclusive) using an output width of 5.  If you specify resolution =
  1, this means that inputs of 1 and 2 have different outputs, though
  they overlap, but 1 and 1.5 might not have different outputs.
  This leads to a 14-bit representation like this:

  1 ->  11111000000000  (14 bits total)
  2 ->  01111100000000
  ...
  10->  00000000011111
  [resolution = 1; n=14; radius = 5]

  You could specify resolution = 0.5, which gives
  1   -> 11111000... (22 bits total)
  1.5 -> 011111.....
  2.0 -> 0011111....
  [resolution = 0.5; n=22; radius=2.5]

  You could specify radius = 1, which gives
  1   -> 111110000000....  (50 bits total)
  2   -> 000001111100....
  3   -> 000000000011111...
  ...
  10  ->                           .....000011111
  [radius = 1; resolution = 0.2; n=50]


  An N/M encoding can also be used to encode a binary value,
  where we want more than one bit to represent each state.
  For example, we could have: w = 5, minval = 0, maxval = 1,
  radius = 1 (which is equivalent to n=10)
  0 -> 1111100000
  1 -> 0000011111


  Implementation details:
  --------------------------------------------------------------------------
  range = maxval - minval
  h = (w-1)/2  (half-width)
  resolution = radius / w
  n = w * range/radius (periodic)
  n = w * range/radius + 2 * h (non-periodic)

  """


  def __init__(self,
               w,
               minval,
               maxval,
               periodic=False,
               n=0,
               radius=DEFAULT_RADIUS,
               resolution=DEFAULT_RESOLUTION,
               name=None,
               verbosity=0,
               clipInput=False,
               forced=False):
    """

    w -- number of bits to set in output
    minval -- minimum input value
    maxval -- maximum input value (input is strictly less if periodic == True)

    Exactly one of n, radius, resolution must be set. "0" is a special
    value that means "not set".

    n -- number of bits in the representation (must be > w)
    radius -- inputs separated by more than, or equal to this distance will have non-overlapping
              representations
    resolution -- inputs separated by more than, or equal to this distance will have different
              representations

    name -- an optional string which will become part of the description

    clipInput -- if true, non-periodic inputs smaller than minval or greater
            than maxval will be clipped to minval/maxval

    forced -- if true, skip some safety checks (for compatibility reasons), default false

    See class documentation for more information.
    """

    assert isinstance(w, numbers.Integral)
    self.encoders = None
    self.verbosity = verbosity
    self.w = w
    if (w % 2 == 0):
      raise Exception("Width must be an odd number (%f)" % w)

    self.minval = minval
    self.maxval = maxval

    self.periodic = periodic
    self.clipInput = clipInput

    self.halfwidth = (w - 1) / 2

    # For non-periodic inputs, padding is the number of bits "outside" the range,
    # on each side. I.e. the representation of minval is centered on some bit, and
    # there are "padding" bits to the left of that centered bit; similarly with
    # bits to the right of the center bit of maxval
    if self.periodic:
      self.padding = 0
    else:
      self.padding = self.halfwidth

    if (minval is not None and maxval is not None):
      if (minval >= maxval):
        raise Exception("The encoder for %s is invalid. minval %s is greater than "
                      "or equal to maxval %s. minval must be strictly less "
                      "than maxval." % (name, minval, maxval))

      self.rangeInternal = float(self.maxval - self.minval)

    # There are three different ways of thinking about the representation. Handle
    # each case here.
    self._initEncoder(w, minval, maxval, n, radius, resolution)

    # nInternal represents the output area excluding the possible padding on each
    #  side
    if (minval is not None and maxval is not None):
      self.nInternal = self.n - 2 * self.padding

    # Our name
    if name is not None:
      self.name = name
    else:
      self.name = "[%s:%s]" % (self.minval, self.maxval)

    # This matrix is used for the topDownCompute. We build it the first time
    #  topDownCompute is called
    self._topDownMappingM = None
    self._topDownValues = None

    # This list is created by getBucketValues() the first time it is called,
    #  and re-created whenever our buckets would be re-arranged.
    self._bucketValues = None

    # checks for likely mistakes in encoder settings
    if not forced:
      self._checkReasonableSettings()


  def _initEncoder(self, w, minval, maxval, n, radius, resolution):
    """ (helper function)  There are three different ways of thinking about the representation.
     Handle each case here."""
    if n != 0:
      if (radius !=0 or resolution != 0):
        raise ValueError("Only one of n/radius/resolution can be specified for a ScalarEncoder")
      assert n > w
      self.n = n

      if (minval is not None and maxval is not None):
        if not self.periodic:
          self.resolution = float(self.rangeInternal) / (self.n - self.w)
        else:
          self.resolution = float(self.rangeInternal) / (self.n)

        self.radius = self.w * self.resolution

        if self.periodic:
          self.range = self.rangeInternal
        else:
          self.range = self.rangeInternal + self.resolution

    else:
      if radius != 0:
        if (resolution != 0):
          raise ValueError("Only one of radius/resolution can be specified for a ScalarEncoder")
        self.radius = radius
        self.resolution = float(self.radius) / w
      elif resolution != 0:
        self.resolution = float(resolution)
        self.radius = self.resolution * self.w
      else:
        raise Exception("One of n, radius, resolution must be specified for a ScalarEncoder")

      if (minval is not None and maxval is not None):
        if self.periodic:
          self.range = self.rangeInternal
        else:
          self.range = self.rangeInternal + self.resolution

        nfloat = self.w * (self.range / self.radius) + 2 * self.padding
        self.n = int(math.ceil(nfloat))


  def _checkReasonableSettings(self):
    """(helper function) check if the settings are reasonable for SP to work"""
    # checks for likely mistakes in encoder settings
    if self.w < 21:
      raise ValueError("Number of bits in the SDR (%d) must be greater than 2, and recommended >= 21 (use forced=True to override)"
                         % self.w)


  def getDecoderOutputFieldTypes(self):
    """ [Encoder class virtual method override]
    """
    return (FieldMetaType.float, )


  def getWidth(self):
    return self.n


  def _recalcParams(self):
    self.rangeInternal = float(self.maxval - self.minval)

    if not self.periodic:
      self.resolution = float(self.rangeInternal) / (self.n - self.w)
    else:
      self.resolution = float(self.rangeInternal) / (self.n)

    self.radius = self.w * self.resolution

    if self.periodic:
      self.range = self.rangeInternal
    else:
      self.range = self.rangeInternal + self.resolution

    name = "[%s:%s]" % (self.minval, self.maxval)


  def getDescription(self):
    return [(self.name, 0)]


  def _getFirstOnBit(self, input):
    """ Return the bit offset of the first bit to be set in the encoder output.
    For periodic encoders, this can be a negative number when the encoded output
    wraps around. """

    if input == SENTINEL_VALUE_FOR_MISSING_DATA:
      return [None]

    else:
      if input < self.minval:
        # Don't clip periodic inputs. Out-of-range input is always an error
        if self.clipInput and not self.periodic:
          if self.verbosity > 0:
            print "Clipped input %s=%.2f to minval %.2f" % (self.name, input,
                                                            self.minval)
          input = self.minval
        else:
          raise Exception('input (%s) less than range (%s - %s)' %
                          (str(input), str(self.minval), str(self.maxval)))

      if self.periodic:
        # Don't clip periodic inputs. Out-of-range input is always an error
        if input >= self.maxval:
          raise Exception('input (%s) greater than periodic range (%s - %s)' %
                          (str(input), str(self.minval), str(self.maxval)))
      else:
        if input > self.maxval:
          if self.clipInput:
            if self.verbosity > 0:
              print "Clipped input %s=%.2f to maxval %.2f" % (self.name, input,
                                                              self.maxval)
            input = self.maxval
          else:
            raise Exception('input (%s) greater than range (%s - %s)' %
                            (str(input), str(self.minval), str(self.maxval)))

      if self.periodic:
        centerbin = int((input - self.minval) * self.nInternal / self.range) \
                      + self.padding
      else:
        centerbin = int(((input - self.minval) + self.resolution/2) \
                          / self.resolution ) + self.padding


      # We use the first bit to be set in the encoded output as the bucket index
      minbin = centerbin - self.halfwidth
      return [minbin]


  def getBucketIndices(self, input):
    """ See method description in base.py """

    if type(input) is float and math.isnan(input):
      input = SENTINEL_VALUE_FOR_MISSING_DATA

    if input == SENTINEL_VALUE_FOR_MISSING_DATA:
      return [None]

    minbin = self._getFirstOnBit(input)[0]

    # For periodic encoders, the bucket index is the index of the center bit
    if self.periodic:
      bucketIdx = minbin + self.halfwidth
      if bucketIdx < 0:
        bucketIdx += self.n

    # for non-periodic encoders, the bucket index is the index of the left bit
    else:
      bucketIdx = minbin

    return [bucketIdx]


  def encodeIntoArray(self, input, output, learn=True):
    """ See method description in base.py """

    if input is not None and not isinstance(input, numbers.Number):
      raise TypeError(
          "Expected a scalar input but got input of type %s" % type(input))

    if type(input) is float and math.isnan(input):
      input = SENTINEL_VALUE_FOR_MISSING_DATA

    # Get the bucket index to use
    bucketIdx = self._getFirstOnBit(input)[0]

    if bucketIdx is None:
      # None is returned for missing value
      output[0:self.n] = 0  #TODO: should all 1s, or random SDR be returned instead?

    else:
      # The bucket index is the index of the first bit to set in the output
      output[:self.n] = 0
      minbin = bucketIdx
      maxbin = minbin + 2*self.halfwidth
      if self.periodic:
        # Handle the edges by computing wrap-around
        if maxbin >= self.n:
          bottombins = maxbin - self.n + 1
          output[:bottombins] = 1
          maxbin = self.n - 1
        if minbin < 0:
          topbins = -minbin
          output[self.n - topbins:self.n] = 1
          minbin = 0

      assert minbin >= 0
      assert maxbin < self.n
      # set the output (except for periodic wraparound)
      output[minbin:maxbin + 1] = 1

    # Debug the decode() method
    if self.verbosity >= 2:
      print
      print "input:", input
      print "range:", self.minval, "-", self.maxval
      print "n:", self.n, "w:", self.w, "resolution:", self.resolution, \
            "radius", self.radius, "periodic:", self.periodic
      print "output:",
      self.pprint(output)
      print "input desc:", self.decodedToStr(self.decode(output))


  def decode(self, encoded, parentFieldName=''):
    """ See the function description in base.py
    """

    # For now, we simply assume any top-down output greater than 0
    #  is ON. Eventually, we will probably want to incorporate the strength
    #  of each top-down output.
    tmpOutput = numpy.array(encoded[:self.n] > 0).astype(encoded.dtype)
    if not tmpOutput.any():
      return (dict(), [])

    # ------------------------------------------------------------------------
    # First, assume the input pool is not sampled 100%, and fill in the
    #  "holes" in the encoded representation (which are likely to be present
    #  if this is a coincidence that was learned by the SP).

    # Search for portions of the output that have "holes"
    maxZerosInARow = self.halfwidth
    for i in xrange(maxZerosInARow):
      searchStr = numpy.ones(i + 3, dtype=encoded.dtype)
      searchStr[1:-1] = 0
      subLen = len(searchStr)

      # Does this search string appear in the output?
      if self.periodic:
        for j in xrange(self.n):
          outputIndices = numpy.arange(j, j + subLen)
          outputIndices %= self.n
          if numpy.array_equal(searchStr, tmpOutput[outputIndices]):
            tmpOutput[outputIndices] = 1

      else:
        for j in xrange(self.n - subLen + 1):
          if numpy.array_equal(searchStr, tmpOutput[j:j + subLen]):
            tmpOutput[j:j + subLen] = 1


    if self.verbosity >= 2:
      print "raw output:", encoded[:self.n]
      print "filtered output:", tmpOutput

    # ------------------------------------------------------------------------
    # Find each run of 1's.
    nz = tmpOutput.nonzero()[0]
    runs = []     # will be tuples of (startIdx, runLength)
    run = [nz[0], 1]
    i = 1
    while (i < len(nz)):
      if nz[i] == run[0] + run[1]:
        run[1] += 1
      else:
        runs.append(run)
        run = [nz[i], 1]
      i += 1
    runs.append(run)

    # If we have a periodic encoder, merge the first and last run if they
    #  both go all the way to the edges
    if self.periodic and len(runs) > 1:
      if runs[0][0] == 0 and runs[-1][0] + runs[-1][1] == self.n:
        runs[-1][1] += runs[0][1]
        runs = runs[1:]


    # ------------------------------------------------------------------------
    # Now, for each group of 1's, determine the "left" and "right" edges, where
    #  the "left" edge is inset by halfwidth and the "right" edge is inset by
    #  halfwidth.
    # For a group of width w or less, the "left" and "right" edge are both at
    #   the center position of the group.
    ranges = []
    for run in runs:
      (start, runLen) = run
      if runLen <= self.w:
        left = right = start + runLen / 2
      else:
        left = start + self.halfwidth
        right = start + runLen - 1 - self.halfwidth

      # Convert to input space.
      if not self.periodic:
        inMin = (left - self.padding) * self.resolution + self.minval
        inMax = (right - self.padding) * self.resolution + self.minval
      else:
        inMin = (left - self.padding) * self.range / self.nInternal + self.minval
        inMax = (right - self.padding) * self.range / self.nInternal + self.minval
      # Handle wrap-around if periodic
      if self.periodic:
        if inMin >= self.maxval:
          inMin -= self.range
          inMax -= self.range

      # Clip low end
      if inMin < self.minval:
        inMin = self.minval
      if inMax < self.minval:
        inMax = self.minval

      # If we have a periodic encoder, and the max is past the edge, break into
      #  2 separate ranges
      if self.periodic and inMax >= self.maxval:
        ranges.append([inMin, self.maxval])
        ranges.append([self.minval, inMax - self.range])
      else:
        if inMax > self.maxval:
          inMax = self.maxval
        if inMin > self.maxval:
          inMin = self.maxval
        ranges.append([inMin, inMax])

    desc = self._generateRangeDescription(ranges)
    # Return result
    if parentFieldName != '':
      fieldName = "%s.%s" % (parentFieldName, self.name)
    else:
      fieldName = self.name

    return ({fieldName: (ranges, desc)}, [fieldName])


  def _generateRangeDescription(self, ranges):
    """generate description from a text description of the ranges"""
    desc = ""
    numRanges = len(ranges)
    for i in xrange(numRanges):
      if ranges[i][0] != ranges[i][1]:
        desc += "%.2f-%.2f" % (ranges[i][0], ranges[i][1])
      else:
        desc += "%.2f" % (ranges[i][0])
      if i < numRanges - 1:
        desc += ", "
    return desc


  def _getTopDownMapping(self):
    """ Return the interal _topDownMappingM matrix used for handling the
    bucketInfo() and topDownCompute() methods. This is a matrix, one row per
    category (bucket) where each row contains the encoded output for that
    category.
    """

    # Do we need to build up our reverse mapping table?
    if self._topDownMappingM is None:

      # The input scalar value corresponding to each possible output encoding
      if self.periodic:
        self._topDownValues = numpy.arange(self.minval + self.resolution / 2.0,
                                           self.maxval,
                                           self.resolution)
      else:
        #Number of values is (max-min)/resolutions
        self._topDownValues = numpy.arange(self.minval,
                                           self.maxval + self.resolution / 2.0,
                                           self.resolution)

      # Each row represents an encoded output pattern
      numCategories = len(self._topDownValues)
      self._topDownMappingM = SM32(numCategories, self.n)

      outputSpace = numpy.zeros(self.n, dtype=GetNTAReal())
      for i in xrange(numCategories):
        value = self._topDownValues[i]
        value = max(value, self.minval)
        value = min(value, self.maxval)
        self.encodeIntoArray(value, outputSpace, learn=False)
        self._topDownMappingM.setRowFromDense(i, outputSpace)

    return self._topDownMappingM


  def getBucketValues(self):
    """ See the function description in base.py """

    # Need to re-create?
    if self._bucketValues is None:
      topDownMappingM = self._getTopDownMapping()
      numBuckets = topDownMappingM.nRows()
      self._bucketValues = []
      for bucketIdx in range(numBuckets):
        self._bucketValues.append(self.getBucketInfo([bucketIdx])[0].value)

    return self._bucketValues


  def getBucketInfo(self, buckets):
    """ See the function description in base.py """

    # Get/generate the topDown mapping table
    #NOTE: although variable topDownMappingM is unused, some (bad-style) actions
    #are executed during _getTopDownMapping() so this line must stay here
    topDownMappingM = self._getTopDownMapping()

    # The "category" is simply the bucket index
    category = buckets[0]
    encoding = self._topDownMappingM.getRow(category)

    # Which input value does this correspond to?
    if self.periodic:
      inputVal = (self.minval + (self.resolution / 2.0) +
                  (category * self.resolution))
    else:
      inputVal = self.minval + (category * self.resolution)

    return [EncoderResult(value=inputVal, scalar=inputVal, encoding=encoding)]


  def topDownCompute(self, encoded):
    """ See the function description in base.py
    """

    # Get/generate the topDown mapping table
    topDownMappingM = self._getTopDownMapping()

    # See which "category" we match the closest.
    category = topDownMappingM.rightVecProd(encoded).argmax()

    # Return that bucket info
    return self.getBucketInfo([category])


  def closenessScores(self, expValues, actValues, fractional=True):
    """ See the function description in base.py
    """

    expValue = expValues[0]
    actValue = actValues[0]
    if self.periodic:
      expValue = expValue % self.maxval
      actValue = actValue % self.maxval

    err = abs(expValue - actValue)
    if self.periodic:
      err = min(err, self.maxval - err)
    if fractional:
      pctErr = float(err) / (self.maxval - self.minval)
      pctErr = min(1.0, pctErr)
      closeness = 1.0 - pctErr
    else:
      closeness = err

    return numpy.array([closeness])


  def dump(self):
    print "ScalarEncoder:"
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


  @classmethod
  def read(cls, proto):
    if proto.n is not None:
      radius = DEFAULT_RADIUS
      resolution = DEFAULT_RESOLUTION
    else:
      radius = proto.radius
      resolution = proto.resolution

    return cls(w=proto.w,
               minval=proto.minval,
               maxval=proto.maxval,
               periodic=proto.periodic,
               n=proto.n,
               name=proto.name,
               verbosity=proto.verbosity,
               clipInput=proto.clipInput,
               forced=True)


  def write(self, proto):
    proto.w = self.w
    proto.minval = self.minval
    proto.maxval = self.maxval
    proto.periodic = self.periodic
    # Radius and resolution can be recalculated based on n
    proto.n = self.n
    proto.name = self.name
    proto.verbosity = self.verbosity
    proto.clipInput = self.clipInput
