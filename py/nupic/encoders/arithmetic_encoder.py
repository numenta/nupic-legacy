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
from collections import deque

from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
from nupic.data.fieldmeta import FieldMetaType
from nupic.encoders.base import Encoder, EncoderResult

DEFAULT_DTYPE = numpy.uint8


class ArithmeticEncoder(Encoder):
  """
  A scalar encoder based loosely on arithmetic coding.

  This encoder uses a moving window of scalar values and keeps an equal
  number of values in each bucket. So a new value will typically not have
  a significant impact on the representations of values. If there are not
  an even number of values per bucket then the left-most buckets will
  contain an extra value.

  **NOTE:** This encoder is not completely implemented.

  [Wikipedia on arithmetic coding](http://en.wikipedia.org/wiki/Arithmetic_coding)

  TODO: Perhaps arithmetic coding isn't the best analogy?
  """

  def __init__(self, w, n, periodic=False, window=200, name=None, verbosity=0):
    """
    TODO: document
    @param w TODO: document
    @param n TODO: document
    @param periodic TODO: document
    @param window TODO: document
    @param name TODO: document
    @param verbosity TODO: document
    """
    self.w = w
    self.n = n
    self.periodic = periodic
    self.window = window
    self.history = deque(maxlen=window)
    self.name = name
    self.verbosity = verbosity

    self.maxBuckets = n - w + 1
    assert window >= self.maxBuckets
    # List of buckets, where a bucket is sequence of
    # (minVal, maxVal, list of current values). A minVal or maxVal of None
    # corresponds to negative and positive infinity.
    self.buckets = [Bucket(float('-inf'), float('inf'), [])]

    # Used in base.Encoder.
    self.encoders = None

    self._learningEnabled = True


  def getDecoderOutputFieldTypes(self):
    """
    [overrides nupic.encoders.base.Encoder.getDecoderOutputFieldTypes]
    @return output field type
    """
    return (FieldMetaType.float,)


  def getBucketInfo(self, buckets):
    """
    [overrides overrides nupic.encoders.base.Encoder.getBucketInfo]
    """
    b = self.buckets[buckets[0]]
    encoding = numpy.zeros(self.n, dtype=DEFAULT_DTYPE)
    self._encode(encoding, [buckets[0]])
    return [EncoderResult(value=b.minVal, scalar=b.minVal, encoding=encoding)]


  def getWidth(self):
    """
    TODO: document
    """
    return self.n


  def isDelta(self):
    """
    TODO: document
    """
    pass


  def getBucketIndices(self, inputValue):
    """
    TODO: document
    """
    for i, bucket in enumerate(self.buckets):
      if inputValue < bucket.maxVal:
        assert inputValue >= bucket.minVal
        return [i]
    raise KeyError('No bucket found containing value: ' % inputValue)


  def getBucketValues(self):
    """
    TODO: document
    TODO: What values go in the return value?
    """
    values = []
    for bucket in self.buckets:
      if bucket.minVal == float('-inf') and bucket.maxVal == float('inf'):
        values.append(0.0)
      else:
        values.append(sum(bucket.values) / len(bucket.values))


  def _addNewValue(self, inputValue):
    # Find the right bucket and add the value.
    bucket = None
    for b in self.buckets:
      if inputValue in b:
        bucket = b
        break
    else:
      raise LookupError("Unable to find bucket for inputValue: %s" % str(inputValue))
    bucket.add(inputValue)
    # Add the value to the history, removing the oldest value if the history
    # is full.
    if len(self.history) == self.window:
      toRemove = self.history.popleft()
      found = False
      for i, b in enumerate(self.buckets):
        if toRemove in b:
          found = True
          b.remove(toRemove)
          if i > 0:
            self.buckets[i - 1].maxVal = b.minVal
          break
      assert found
    self.history.append(inputValue)
    # Rebalance the buckets.
    self._rebalance()
    # Return the final bucket index.
    for i, b in enumerate(self.buckets):
      if inputValue in b:
        ret = [i]
        for j in xrange(i + 1, len(self.buckets)):
          if inputValue in self.buckets[j]:
            ret.append(j)
          else:
            break
        return ret


  def _rebalance(self):
    """
    Adjust values to keep the same number of values in each bucket.

    This function only works if there is only one value out of place.
    """
    assert self.buckets[-1].maxVal == float('inf')
    if len(self.buckets) < self.maxBuckets:
      # Get the indices of each bucket that needs to be split.
      bucketIndices = []
      for i, b in enumerate(self.buckets):
        if len(b) > 1:
          bucketIndices.append(i)
      # Split the buckets.
      bucketIndices.reverse()
      for i in bucketIndices:
        originalBucket = self.buckets[i]
        # Create new buckets for all but the last value.
        maxVal = originalBucket.values[-1]
        for v in reversed(originalBucket[:-1]):
          self.buckets.insert(i, Bucket(v, maxVal, [v]))
          maxVal = v
        self.buckets[i].minVal = originalBucket.minVal
        # Update the original bucket to hold just the last value.
        originalBucket.values = originalBucket.values[-1:]
        originalBucket.minVal = originalBucket.values[0]
    else:
      minValuesPerBucket = len(self.history) / len(self.buckets)
      mod = len(self.history) % len(self.buckets)
      for i, b in enumerate(self.buckets):
        numValues = minValuesPerBucket
        if i < mod:
          numValues += 1
        if len(b) > numValues:
          extra = len(b) - numValues
          values = b[-extra:]
          # Insert the values into the next bucket.
          self.buckets[i + 1].values[:0] = values
          self.buckets[i + 1].minVal = values[0]
          # Remove the values from the current bucket.
          b.values = b.values[:-extra]
          b.maxVal = values[0]
        elif len(b) < numValues:
          needed = numValues - len(b)
          assert len(self.buckets[i + 1]) >= needed
          values = self.buckets[i + 1].values[:needed]
          # Remove the values from the next bucket.
          self.buckets[i + 1].values = self.buckets[i + 1].values[needed:]
          if len(self.buckets[i + 1]) > 0:
            self.buckets[i + 1].minVal = self.buckets[i + 1].values[0]
          else:
            self.buckets[i + 1].minVal = self.buckets[i + 2].values[0]
          # Add the values to the current bucket.
          b.values.extend(values)
          b.maxVal = self.buckets[i + 1].minVal
          if b.minVal > float('-inf'):
            b.minVal = b.values[0]
            self.buckets[i - 1].maxVal = b.minVal
    assert self.buckets[-1].maxVal == float('inf')


  def _encode(self, outputArray, bucketIdxs):
      outputArray[:self.n] = 0
      # If there are not enough buckets to fill the range, increase the width
      # of each bucket.
      w = max(self.n + 1 - len(self.buckets), self.w)
      start = bucketIdxs[0]
      end = start + w + len(bucketIdxs) - 1
      #if self.periodic and end > self.n:
      #  outputArray[bucketIdx:] = 1
      #  outputArray[:end % self.n] = 1
      #else:
      outputArray[start:end] = 1


  def encodeIntoArray(self, inputValue, outputArray):
    """
    Encode inputValue and write the output bit array to outputArray.

    @param inputValue TODO: document
    @param outputArray TODO: document
    """
    if inputValue == SENTINEL_VALUE_FOR_MISSING_DATA:
      outputArray[:self.n] = 0
    else:
      bucketIdxs = self._addNewValue(inputValue)
      self._encode(outputArray, bucketIdxs)
    self._checkInvariants()


  def decode(self, encoded, parentFieldName=''):
    """
    [overrides overrides nupic.encoders.base.Encoder.decode]
    Not implemented, but required override.
    """
    raise NotImplementedError()


  def topDownCompute(self, encoded):
    """
    [overrides overrides nupic.encoders.base.Encoder.topDownCompute]
    Not implemented, but required override.
    """
    raise NotImplementedError()


  def closenessScores(self, expValues, actValues, fractional=True):
    """
    TODO: document

    @param expValues TODO: document
    @param actValues TODO: document
    @param fractional TODO: document
    @returns TODO: document
    """
    expValue = expValues[0]
    actValue = actValues[0]
    #if self.periodic:
    #  expValue = expValue % self.maxval
    #  actValue = actValue % self.maxval
    error = abs(expValue - actValue)
    #if self.periodic:
    #  error = min(error, self.maxval - error)

    if fractional:
      minVal = self.buckets[0].values[0]
      maxVal = self.buckets[-1].values[-1]
      pctErr = float(error) / (maxVal - minVal)
      pctErr = min(1.0, pctErr)
      closeness = 1.0 - pctErr
    else:
      closeness = error

    return numpy.array([closeness])


  def getDescription(self):
    """
    TODO: document
    @returns TODO: document
    """
    return [(self.name, 0)]


  def _checkInvariants(self):
    """Check that all invariants are currently met.

    Invariants that are checked:
      - The number of buckets is either self.maxBuckets or the length of
        self.history.
      - self.history has the exact same set as the union of all buckets.
      - Values within a bucket are sorted in increasing order.
      - Values in a bucket are greater than or equal to the values in the
        previous bucket.
      - The buckets are balanced. Specifically, any two buckets have a
        difference in the number of values of at most one and no bucket can
        have more values than a bucket before it.
    """
    # Check there are the correct number of buckets.
    assert len(self.buckets) == min(self.maxBuckets, len(self.history))

    valuesNotSeen = [v for v in self.history]
    totalValuesSeen = 0
    prev = float('-inf')
    minValsPerBucket = len(self.history) / len(self.buckets)
    numExtraVals = len(self.history) % len(self.buckets)

    for i, b in enumerate(self.buckets):
      expectedNumValues = minValsPerBucket
      if i < numExtraVals:
        expectedNumValues += 1
      assert len(b) == expectedNumValues
      for v in b:
        totalValuesSeen += 1
        assert v in valuesNotSeen
        valuesNotSeen.remove(v)
        assert v >= prev
        prev = v
      assert b.minVal in (float('-inf'), b.values[0]), (str([self.buckets[i - 1],
                                                            b,
                                                            self.buckets[i + 1]]),
                                                            self.history)
      assert b.maxVal >= b.values[-1], str(('Expected: %g >= %g' % (b.maxVal,
                                                               b.values[-1]),
                                            i, len(self.buckets),
                                            [self.buckets[i - 1], b]))
      if i + 1 < len(self.buckets):
        assert b.maxVal == self.buckets[i + 1].minVal
      else:
        assert b.maxVal == float('inf')

    assert totalValuesSeen == len(self.history)
    assert not valuesNotSeen



class Bucket(object):
  """
  A single bucket that holds values and tracks its range.
  """

  __slots__ = ('version', 'minVal', 'maxVal', 'values')


  def __init__(self, minVal, maxVal, values):
    """
    @param minVal minimum bucket value
    @param maxVal maximum bucket value
    @param values initial bucket values
    """
    self.version = 0
    self.minVal = minVal
    self.maxVal = maxVal
    self.values = values


  def __contains__(self, value):
    if self.values:
      lastValue = value == self.values[-1]
    else:
      lastValue = False
    return value >= self.minVal and (value < self.maxVal or lastValue)


  def __getitem__(self, i):
    return self.values[i]


  def __len__(self):
    return len(self.values)


  def __repr__(self):
    return 'Bucket(%g, %g, %s)' % (self.minVal, self.maxVal, str(self.values))


  def __getstate__(self):
    return {'version': self.version,
            'minVal': self.minVal,
            'maxVal': self.maxVal,
            'values': self.values}


  def __setstate__(self, state):
    assert state['version'] == 0
    self.minVal = state['minVal']
    self.maxVal = state['maxVal']
    self.values = state['values']


  def add(self, value):
    """
    Adds a value to the bucket.
    @param value to add
    """
    self.values.append(value)
    self.values.sort()


  def remove(self, value):
    """
    Removes a value from the bucket.
    @param value to remove
    """
    self.values.remove(value)
    if self.minVal > float('-inf'):
      if len(self.values) > 0:
        self.minVal = self.values[0]
