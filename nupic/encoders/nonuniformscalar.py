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

import numpy

from nupic.bindings.math import SM32, GetNTAReal
from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
from nupic.encoders.scalar import ScalarEncoder
from nupic.encoders.base import defaultDtype
from nupic.encoders.base import EncoderResult


class NonUniformScalarEncoder(ScalarEncoder):
  """
  This is an implementation of the scalar encoder that encodes
  the value into unequal ranges, such that each encoding occurs with
  approximately equal frequency.

  This means that value ranges that occur more frequently will have higher
  resolution than those that occur less frequently
  """

  ############################################################################
  def __init__(self, w, n, data = None, bins = None,
                      weights=None, name=None, verbosity=0, forced=False):



    self._numBins = n - w + 1
    self.weights = weights
    super(NonUniformScalarEncoder, self).__init__(w=w, n=n, minval= 0, maxval=self._numBins-1,
                                                                          clipInput=True, name=name,
                                                                          verbosity=verbosity, forced=forced)
    hasData = data is None
    hasBins = bins is None
    if hasData == hasBins:
      raise ValueError("Exactly one argument must be supplied: data or bins")

    if data is not None:
      self.data = numpy.array(data)
      self.bins =  self.ComputeBins(self._numBins, self.data, self.weights, self.verbosity)

    if bins is not None:
      #if self._numBins != len(bins):
      #  raise ValueError(
      #    '''Incorrect number of bins for given resolution
      #    Num bins supplied:%d
      #    Num bins expected (according to n and w):%d''' %(len(bins), self._numBins))
      self.bins = numpy.array(bins)
      self._numBins = self.bins.shape[0]




  ############################################################################
  @classmethod
  def ComputeBins(cls, nBins, data, weights=None, verbosity = 0):
    data = numpy.array(data)
    bins = numpy.zeros((nBins, 2))
    #If no weights were specified, default to uniformly weighted
    if weights is None:
      weights = numpy.ones(data.shape, dtype = defaultDtype)

    sortedIndices = numpy.argsort(data)
    sortedValues = data[sortedIndices]
    sortedWeights = weights[sortedIndices]
    cumWeights = numpy.cumsum(sortedWeights)
    avgBinWeight = cumWeights[-1] / float(nBins)

    #Prepend 0s to the values and weights because we
    #are actually dealing with intervals, not values
    sortedValues = numpy.append(sortedValues[0], sortedValues)
    cumWeights = numpy.append(0, cumWeights)

    #-------------------------------------------------------------------------
    # Iterate through each bin and find the appropriate start
    # and end value for each one. We use the numpy.interp
    # function to deal with non-integer indices

    startValue = sortedValues[0]
    cumBinWeight = 0
    binIndex = 0

    if verbosity > 0:
      print "Average Bin Weight: %.3f"% avgBinWeight

    while True:
      # Use the inverse cumulative probability mass function
      # to compute the bin endpoint
      bins[binIndex, 0] = startValue
      cumBinWeight += avgBinWeight
      endValue = numpy.interp(cumBinWeight, xp=cumWeights, fp=sortedValues)
      bins[binIndex,1] = endValue

      if verbosity > 1:
          print "Start Value:%.2f EndValue:%.2f" %(startValue, endValue)

      if abs(cumWeights[-1] - cumBinWeight) < 1e-10:
        break

      startValue = endValue
      binIndex += 1

    # --------------------------------------------
    # Cleanup: if there are any identical bins, only leave one copy
    matches = (bins[0:-1, :] == bins[1:, :])
    if numpy.any(matches):
      # Assume the last bin is unique
      matches = numpy.vstack([matches, [False, False]])
      #matchingBins = numpy.all(matches, axis=1)
      matchingBins = matches[:,0]
      bins=bins[numpy.logical_not(matchingBins), :]

    #All done, print out if necessary
    if verbosity > 0:
      print "Bins:\n", bins
    return bins



  ############################################################################
  def getBucketIndices(self, input):
    """[ScalarEncoder class method override]"""

    if input != SENTINEL_VALUE_FOR_MISSING_DATA:
      bin = self._findBin(input)
    else:
      bin = SENTINEL_VALUE_FOR_MISSING_DATA

    return super(NonUniformScalarEncoder, self).getBucketIndices(bin)


  ############################################################################
  def encodeIntoArray(self, input, output):
    """[ScalarEncoder class method override]"""

    if input != SENTINEL_VALUE_FOR_MISSING_DATA:
      bin = self._findBin(input)
    else:
      bin = SENTINEL_VALUE_FOR_MISSING_DATA

    super(NonUniformScalarEncoder, self).encodeIntoArray(bin, output)


  ############################################################################
  def _findBin(self, value):
    assert self.bins is not None
    lower = value >= self.bins[:,0]
    upper = value < self.bins[:,1]

    # The last range is both left and right inclusive
    upper[-1] = (value <= self.bins[-1, -1])

    bins = numpy.where(numpy.logical_and(lower,upper))[0]

    if len(bins) == 0:
      if value < self.bins[0,0]:
        return -1
      elif value >= self.bins[-1,-1]:
        return self._numBins
      else:

        raise ValueError("Improper value for encoder: %f\nBins:%r" % (value, self.bins))
    else:
      assert len(bins)==1
      return bins[0]

  ############################################################################
  def decode(self, encoded, parentFieldName=""):
    """ Overidden from scalar.py"""

    (rangeDict, fieldNames) = super(NonUniformScalarEncoder, self).decode(encoded, parentFieldName)
    range = self._getRangeForEncoding(encoded, rangeDict, fieldNames)
    desc = self._generateRangeDescription([range])

    for fieldName, (bins, desc) in rangeDict.iteritems():
      rangeDict[fieldName] = ([range], desc)

    return (rangeDict, fieldNames)

  ############################################################################
  def _getRangeForEncoding(self, encoded, rangeDict, fieldNames):

    assert  len(rangeDict)==1

    (bins, description) = rangeDict.values()[0]
    assert len(bins)==1

    bin = bins[0]
    # if the decoding leads to a range of bin, just take the mean for now
    if bin[0] == bin[1]:
      binIndex = bin[0]
    else:
      binIndex = numpy.round(numpy.mean(bins))

    assert binIndex >= 0 and binIndex < self.bins.shape[0]
    curRange = self.bins[binIndex,:]
    ranges = list(curRange)

    return ranges

  ############################################################################
  def _getTopDownMapping(self):
    """ Return the interal _topDownMappingM matrix used for handling the
    bucketInfo() and topDownCompute() methods. This is a matrix, one row per
    category (bucket) where each row contains the encoded output for that
    category.
    """

    if self._topDownMappingM is None:
      self._topDownMappingM = SM32(self._numBins, self.n)

      outputSpace = numpy.zeros(self.n, dtype = GetNTAReal())

      for i in xrange(self._numBins):
        outputSpace[:] = 0.0
        outputSpace[i:i+self.w] = 1.0
        self._topDownMappingM.setRowFromDense(i, outputSpace)

    return self._topDownMappingM

  ############################################################################
  def getBucketValues(self):
    """ See the function description in base.py """

    if self._bucketValues is None:
      topDownMappingM = self._getTopDownMapping()
      numBuckets = topDownMappingM.nRows()
      self._bucketValues = []
      for bucketIdx in range(numBuckets):
        self._bucketValues.append(self.getBucketInfo([bucketIdx])[0].value)

    return self._bucketValues

  ############################################################################
  def getBucketInfo(self, buckets):
    """ See the function description in base.py """

    binIndex = buckets[0]
    value = numpy.mean(self.bins[binIndex, :])

    return [EncoderResult(value=value, scalar=value,
                         encoding=self._topDownMappingM.getRow(binIndex))]

  ############################################################################
  def topDownCompute(self, encoded):
    """ See the function description in base.py """

    topDownMappingM = self._getTopDownMapping()

    binIndex = topDownMappingM.rightVecProd(encoded).argmax()
    value = numpy.mean(self.bins[binIndex, :])

    return [EncoderResult(value=value, scalar=value,
                         encoding=self._topDownMappingM.getRow(binIndex))]

############################################################################
  def dump(self):
    print "NonUniformScalarEncoder:"
    print " ranges: %r"% self.bins
    print "  w:   %d" % self.w
    print "  n:   %d" % self.n
    print "  resolution: %f" % self.resolution
    print "  radius:     %f" % self.radius
    print "  nInternal: %d" % self.nInternal
    print "  rangeInternal: %f" % self.rangeInternal
    print "  padding: %d" % self.padding
