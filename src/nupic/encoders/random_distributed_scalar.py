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
import pprint
import sys

import numpy

from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
from nupic.data.fieldmeta import FieldMetaType
from nupic.encoders.base import Encoder
from nupic.bindings.math import Random as NupicRandom



INITIAL_BUCKETS = 1000



class RandomDistributedScalarEncoder(Encoder):
  """
  A scalar encoder encodes a numeric (floating point) value into an array
  of bits.

  This class maps a scalar value into a random distributed representation that
  is suitable as scalar input into the spatial pooler. The encoding scheme is
  designed to replace a simple ScalarEncoder. It preserves the important
  properties around overlapping representations. Unlike ScalarEncoder the min
  and max range can be dynamically increased without any negative effects. The
  only required parameter is resolution, which determines the resolution of
  input values.

  Scalar values are mapped to a bucket. The class maintains a random distributed
  encoding for each bucket. The following properties are maintained by
  RandomDistributedEncoder:

  1) Similar scalars should have high overlap. Overlap should decrease smoothly
  as scalars become less similar. Specifically, neighboring bucket indices must
  overlap by a linearly decreasing number of bits.

  2) Dissimilar scalars should have very low overlap so that the SP does not
  confuse representations. Specifically, buckets that are more than w indices
  apart should have at most maxOverlap bits of overlap. We arbitrarily (and
  safely) define "very low" to be 2 bits of overlap or lower.

  Properties 1 and 2 lead to the following overlap rules for buckets i and j:

      If abs(i-j) < w then:
        overlap(i,j) = w - abs(i-j)
      else:
        overlap(i,j) <= maxOverlap

  3) The representation for a scalar must not change during the lifetime of
  the object. Specifically, as new buckets are created and the min/max range
  is extended, the representation for previously in-range sscalars and
  previously created buckets must not change.
  """


  def __init__(self, resolution, w=21, n=400, name=None, offset=None,
               seed=42, verbosity=0):
    """Constructor

    @param resolution A floating point positive number denoting the resolution
                    of the output representation. Numbers within
                    [offset-resolution/2, offset+resolution/2] will fall into
                    the same bucket and thus have an identical representation.
                    Adjacent buckets will differ in one bit. resolution is a
                    required parameter.

    @param w Number of bits to set in output. w must be odd to avoid centering
                    problems.  w must be large enough that spatial pooler
                    columns will have a sufficiently large overlap to avoid
                    false matches. A value of w=21 is typical.

    @param n Number of bits in the representation (must be > w). n must be
                    large enough such that there is enough room to select
                    new representations as the range grows. With w=21 a value
                    of n=400 is typical. The class enforces n > 6*w.

    @param name An optional string which will become part of the description.

    @param offset A floating point offset used to map scalar inputs to bucket
                    indices. The middle bucket will correspond to numbers in the
                    range [offset - resolution/2, offset + resolution/2). If set
                    to None, the very first input that is encoded will be used
                    to determine the offset.

    @param seed The seed used for numpy's random number generator. If set to -1
                    the generator will be initialized without a fixed seed.

    @param verbosity An integer controlling the level of debugging output. A
                    value of 0 implies no output. verbosity=1 may lead to
                    one-time printouts during construction, serialization or
                    deserialization. verbosity=2 may lead to some output per
                    encode operation. verbosity>2 may lead to significantly
                    more output.
    """
    # Validate inputs
    if (w <= 0) or (w%2 == 0):
      raise ValueError("w must be an odd positive integer")

    if resolution <= 0:
      raise ValueError("resolution must be a positive number")

    if (n <= 6*w) or (not isinstance(n, int)):
      raise ValueError("n must be an int strictly greater than 6*w. For "
                       "good results we recommend n be strictly greater "
                       "than 11*w")

    self.encoders = None
    self.verbosity = verbosity
    self.w = w
    self.n = n
    self.resolution = float(resolution)

    # The largest overlap we allow for non-adjacent encodings
    self._maxOverlap = 2

    # initialize the random number generators
    self._seed(seed)

    # Internal parameters for bucket mapping
    self.minIndex = None
    self.maxIndex = None
    self._offset = None
    self._initializeBucketMap(INITIAL_BUCKETS, offset)

    # A name used for debug printouts
    if name is not None:
      self.name = name
    else:
      self.name = "[%s]" % (self.resolution)

    if self.verbosity > 0:
      self.dump()


  def __setstate__(self, state):
    self.__dict__.update(state)

    # Initialize self.random as an instance of NupicRandom derived from the
    # previous numpy random state
    randomState = state["random"]
    if isinstance(randomState, numpy.random.mtrand.RandomState):
      self.random = NupicRandom(randomState.randint(sys.maxint))


  def _seed(self, seed=-1):
    """
    Initialize the random seed
    """
    if seed != -1:
      self.random = NupicRandom(seed)
    else:
      self.random = NupicRandom()


  def getDecoderOutputFieldTypes(self):
    """ See method description in base.py """
    return (FieldMetaType.float, )


  def getWidth(self):
    """ See method description in base.py """
    return self.n


  def getDescription(self):
    return [(self.name, 0)]


  def getBucketIndices(self, x):
    """ See method description in base.py """

    if ((isinstance(x, float) and math.isnan(x)) or
        x == SENTINEL_VALUE_FOR_MISSING_DATA):
      return [None]

    if self._offset is None:
      self._offset = x

    bucketIdx = (
        (self._maxBuckets/2) + int(round((x - self._offset) / self.resolution))
    )

    if bucketIdx < 0:
      bucketIdx = 0
    elif bucketIdx >= self._maxBuckets:
      bucketIdx = self._maxBuckets-1

    return [bucketIdx]


  def mapBucketIndexToNonZeroBits(self, index):
    """
    Given a bucket index, return the list of non-zero bits. If the bucket
    index does not exist, it is created. If the index falls outside our range
    we clip it.

    @param index The bucket index to get non-zero bits for.
    @returns numpy array of indices of non-zero bits for specified index.
    """
    if index < 0:
      index = 0

    if index >= self._maxBuckets:
      index = self._maxBuckets-1

    if not self.bucketMap.has_key(index):
      if self.verbosity >= 2:
        print "Adding additional buckets to handle index=", index
      self._createBucket(index)
    return self.bucketMap[index]


  def encodeIntoArray(self, x, output):
    """ See method description in base.py """

    if x is not None and not isinstance(x, numbers.Number):
      raise TypeError(
          "Expected a scalar input but got input of type %s" % type(x))

    # Get the bucket index to use
    bucketIdx = self.getBucketIndices(x)[0]

    # None is returned for missing value in which case we return all 0's.
    output[0:self.n] = 0
    if bucketIdx is not None:
      output[self.mapBucketIndexToNonZeroBits(bucketIdx)] = 1


  def _createBucket(self, index):
    """
    Create the given bucket index. Recursively create as many in-between
    bucket indices as necessary.
    """
    if index < self.minIndex:
      if index == self.minIndex - 1:
        # Create a new representation that has exactly w-1 overlapping bits
        # as the min representation
        self.bucketMap[index] = self._newRepresentation(self.minIndex,
                                                        index)
        self.minIndex = index
      else:
        # Recursively create all the indices above and then this index
        self._createBucket(index+1)
        self._createBucket(index)
    else:
      if index == self.maxIndex + 1:
        # Create a new representation that has exactly w-1 overlapping bits
        # as the max representation
        self.bucketMap[index] = self._newRepresentation(self.maxIndex,
                                                        index)
        self.maxIndex = index
      else:
        # Recursively create all the indices below and then this index
        self._createBucket(index-1)
        self._createBucket(index)


  def _newRepresentation(self, index, newIndex):
    """
    Return a new representation for newIndex that overlaps with the
    representation at index by exactly w-1 bits
    """
    newRepresentation = self.bucketMap[index].copy()

    # Choose the bit we will replace in this representation. We need to shift
    # this bit deterministically. If this is always chosen randomly then there
    # is a 1 in w chance of the same bit being replaced in neighboring
    # representations, which is fairly high
    ri = newIndex % self.w

    # Now we choose a bit such that the overlap rules are satisfied.
    newBit = self.random.getUInt32(self.n)
    newRepresentation[ri] = newBit
    while newBit in self.bucketMap[index] or \
          not self._newRepresentationOK(newRepresentation, newIndex):
      self.numTries += 1
      newBit = self.random.getUInt32(self.n)
      newRepresentation[ri] = newBit

    return newRepresentation


  def _newRepresentationOK(self, newRep, newIndex):
    """
    Return True if this new candidate representation satisfies all our overlap
    rules. Since we know that neighboring representations differ by at most
    one bit, we compute running overlaps.
    """
    if newRep.size != self.w:
      return False
    if (newIndex < self.minIndex-1) or (newIndex > self.maxIndex+1):
      raise ValueError("newIndex must be within one of existing indices")

    # A binary representation of newRep. We will use this to test containment
    newRepBinary = numpy.array([False]*self.n)
    newRepBinary[newRep] = True

    # Midpoint
    midIdx = self._maxBuckets/2

    # Start by checking the overlap at minIndex
    runningOverlap = self._countOverlap(self.bucketMap[self.minIndex], newRep)
    if not self._overlapOK(self.minIndex, newIndex, overlap=runningOverlap):
      return False

    # Compute running overlaps all the way to the midpoint
    for i in range(self.minIndex+1, midIdx+1):
      # This is the bit that is going to change
      newBit = (i-1)%self.w

      # Update our running overlap
      if newRepBinary[self.bucketMap[i-1][newBit]]:
        runningOverlap -= 1
      if newRepBinary[self.bucketMap[i][newBit]]:
        runningOverlap += 1

      # Verify our rules
      if not self._overlapOK(i, newIndex, overlap=runningOverlap):
        return False

    # At this point, runningOverlap contains the overlap for midIdx
    # Compute running overlaps all the way to maxIndex
    for i in range(midIdx+1, self.maxIndex+1):
      # This is the bit that is going to change
      newBit = i%self.w

      # Update our running overlap
      if newRepBinary[self.bucketMap[i-1][newBit]]:
        runningOverlap -= 1
      if newRepBinary[self.bucketMap[i][newBit]]:
        runningOverlap += 1

      # Verify our rules
      if not self._overlapOK(i, newIndex, overlap=runningOverlap):
        return False

    return True


  def _countOverlapIndices(self, i, j):
    """
    Return the overlap between bucket indices i and j
    """
    if self.bucketMap.has_key(i) and self.bucketMap.has_key(j):
      iRep = self.bucketMap[i]
      jRep = self.bucketMap[j]
      return self._countOverlap(iRep, jRep)
    else:
      raise ValueError("Either i or j don't exist")


  @staticmethod
  def _countOverlap(rep1, rep2):
    """
    Return the overlap between two representations. rep1 and rep2 are lists of
    non-zero indices.
    """
    overlap = 0
    for e in rep1:
      if e in rep2:
        overlap += 1
    return overlap


  def _overlapOK(self, i, j, overlap=None):
    """
    Return True if the given overlap between bucket indices i and j are
    acceptable. If overlap is not specified, calculate it from the bucketMap
    """
    if overlap is None:
      overlap = self._countOverlapIndices(i, j)
    if abs(i-j) < self.w:
      if overlap == (self.w - abs(i-j)):
        return True
      else:
        return False
    else:
      if overlap <= self._maxOverlap:
        return True
      else:
        return False


  def _initializeBucketMap(self, maxBuckets, offset):
    """
    Initialize the bucket map assuming the given number of maxBuckets.
    """
    # The first bucket index will be _maxBuckets / 2 and bucket indices will be
    # allowed to grow lower or higher as long as they don't become negative.
    # _maxBuckets is required because the current SDR Classifier assumes bucket
    # indices must be non-negative. This normally does not need to be changed
    # but if altered, should be set to an even number.
    self._maxBuckets = maxBuckets
    self.minIndex = self._maxBuckets / 2
    self.maxIndex = self._maxBuckets / 2

    # The scalar offset used to map scalar values to bucket indices. The middle
    # bucket will correspond to numbers in the range
    # [offset-resolution/2, offset+resolution/2).
    # The bucket index for a number x will be:
    #     maxBuckets/2 + int( round( (x-offset)/resolution ) )
    self._offset = offset

    # This dictionary maps a bucket index into its bit representation
    # We initialize the class with a single bucket with index 0
    self.bucketMap = {}

    def _permutation(n):
      r = numpy.arange(n, dtype=numpy.uint32)
      self.random.shuffle(r)
      return r

    self.bucketMap[self.minIndex] = _permutation(self.n)[0:self.w]

    # How often we need to retry when generating valid encodings
    self.numTries = 0


  def dump(self):
    print "RandomDistributedScalarEncoder:"
    print "  minIndex:   %d" % self.minIndex
    print "  maxIndex:   %d" % self.maxIndex
    print "  w:          %d" % self.w
    print "  n:          %d" % self.getWidth()
    print "  resolution: %g" % self.resolution
    print "  offset:     %s" % str(self._offset)
    print "  numTries:   %d" % self.numTries
    print "  name:       %s" % self.name
    if self.verbosity > 2:
      print "  All buckets:     "
      pprint.pprint(self.bucketMap)


  @classmethod
  def read(cls, proto):
    encoder = object.__new__(cls)
    encoder.resolution = proto.resolution
    encoder.w = proto.w
    encoder.n = proto.n
    encoder.name = proto.name
    encoder._offset = proto.offset
    encoder.random = NupicRandom()
    encoder.random.read(proto.random)
    encoder.resolution = proto.resolution
    encoder.verbosity = proto.verbosity
    encoder.minIndex = proto.minIndex
    encoder.maxIndex = proto.maxIndex
    encoder.encoders = None
    encoder._maxBuckets = INITIAL_BUCKETS
    encoder.bucketMap = {x.key: numpy.array(x.value, dtype=numpy.uint32)
                         for x in proto.bucketMap}

    return encoder


  def write(self, proto):
    proto.resolution = self.resolution
    proto.w = self.w
    proto.n = self.n
    proto.name = self.name
    proto.offset = self._offset
    self.random.write(proto.random)
    proto.verbosity = self.verbosity
    proto.minIndex = self.minIndex
    proto.maxIndex = self.maxIndex
    proto.bucketMap = [{"key": key, "value": value.tolist()}
                       for key, value in self.bucketMap.items()]
