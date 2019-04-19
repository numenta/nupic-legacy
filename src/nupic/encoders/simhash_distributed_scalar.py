# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# https://numenta.org/licenses/
#
# Copyright (C) 2013-2019 Numenta, Inc. https://numenta.com
#           (C) 2019 Brev Patterson, Lux Rota LLC. https://luxrota.com
#
# Unless you have an agreement with Numenta, Inc., for a separate license
# for this software code, the following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero Public License version 3 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# Public License for more details.
#
# You should have received a copy of the GNU Affero Public License along
# with this program. If not, see http://www.gnu.org/licenses.
# ----------------------------------------------------------------------

import hashlib
import math
import numbers
import numpy
import sha3

from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
from nupic.data.field_meta import FieldMetaType
from nupic.encoders.base import Encoder


class SimHashDistributedScalarEncoder(Encoder):
  """
  SimHash Distributed Scalar Encoder (SHaDSE).

  A Locality-Sensitive Hashing approach towards encoding semantic data into
  Sparse Distributed Representations, ready to be fed into an Hierarchical
  Temporal Memory, like NuPIC. This uses the SimHash algorithm to
  accomplish this. LSH and SimHash come from the world of nearest-neighbor
  document similarity searching.

  This encoder is sibling with the original Scalar Encoder, and the Random
  Distributed Scalar Encoder (RDSE). The static bucketing strategy here is
  generally lifted straight from the RDSE, although the "contents" and
  representations are created differently.

  Instead of creating a random hash for our target bucket, we first generate
  a SHA-3+SHAKE256 hash of the bucket index (the SHAKE extension provides a
  variable-length hash (n)). Using that hash, and hash values from nearby
  neighbor buckets (within bucketRadius), we then create a weighted SimHash
  for our target bucket index. This SimHash output will represent both
  individual bucket value, and represent the relations between nearby neighbor
  values in bucket space. A stable number of On bits (w) is achieved during
  final collapsing step of SimHashing.

  :param int n: Required. Number of bits in the representation (must be > w).
    n must be large enough such that there is enough room to select new
    representations as the range grows. A value of n=400 is typical.

  :param int w: Required. Number of bits to set in output. w must be odd to
    avoid centering problems. w must be large enough that spatial pooler
    columns will have a sufficiently large overlap to avoid false matches.
    A value of w=21 is typical.

  :param float resolution: Required. A floating point positive number
    denoting the ratio between input values and bucket index number.
    Input values within the range [offset-resolution/2, offset+resolution/2]
    will fall into the same bucket and thus have an identical representation.
    Adjacent buckets will differ slightly by bits, non-adjacent buckets
    will differ by many bits.

  :param str name: Name for this encoder instance. It will become part of
    the description and debugging output.

  :param bool periodic: If True, then the input semantics will "wrap around"
    such that the largest and smallest values will by semantically similar.
    When in periodic mode, the output space will be circular, instead of the
    usual linear space (small and large values are semantically most
    unsimilar). When in periodic mode, edge representations will change and
    adapt subtly as buckets usage grows, and will settle after full value
    range has been input.

  :param int bucketRadius: Two buckets separated by more than the radius have
    non-overlapping simhash representations. Two buckets separated by less
    than the  radius will in general overlap in at least some of their
    simhash bits. A setting of 0 will leave buckets with no non-random
    semantic or binary similarity, and thus can be used like a Category
    encoder (if you keep an external mapping). A good starting value is usually
    somewhere between w/4 and w.

  :param float bucketOffset: A floating point offset used to map scalar
    inputs to bucket indices. The middle bucket will correspond to numbers
    in the range [offset-resolution/2, offset+resolution/2). If set
    to None, the very first input that is encoded will be used to determine
    the offset. This can be used as a custom override (Rare).

  :param int initialBuckets: Internal bucket array size to use, defaults
    to 1000. If you get an error from overloading the default bucket size,
    this number can be increased (Rare).

  :param int verbosity: Controlling the level of debugging output. A value
    of 0 implies no output. verbosity=1 may lead to one-time printouts during
    construction, serialization or deserialization. verbosity=2 may lead to
    some output per encode operation. verbosity>2 may lead to significantly
    more output.
  """

  def __init__(self,
               n,
               w,
               resolution,
               name=None,
               periodic=False,
               bucketRadius=None,
               bucketOffset=None,
               initialBuckets=1000,
               verbosity=0):
    """ Constructor - See base.py """
    if (n <= 0) or (n < w):
      raise ValueError("n must be: positive integer, more than w")
    if (w <= 0) or (w > n):
      raise ValueError("w must be: positive integer, less than n")
    if (w % 2 == 0):
      raise ValueError("w must be: an odd number")
    if resolution <= 0.0:
      raise ValueError("resolution must be a positive number")

    self._bitsPerByte = (255).bit_length()
    self._n = n
    self._w = w
    self._resolution = float(resolution)
    self._name = "[SHaDSE:%s:%s:%s]" % (n, w, resolution)
    if name is not None:
      self._name = name
    self._periodic = periodic
    self._bucketRadius = self._w / 2
    if bucketRadius is not None:
      self._bucketRadius = bucketRadius
    self._bucketOffset = bucketOffset
    self._bucketsWidth = initialBuckets
    self._bucketMinIndex = self._bucketsWidth / 2
    self._bucketMaxIndex = self._bucketsWidth / 2
    self._verbosity = verbosity

    if self._verbosity > 0:
      print "SimHashDistrubutedScalarEncoder"
      print "  bitsPerByte %s" % self._bitsPerByte
      print "  n %s" % self.getWidth()
      print "  w %s" % self._w
      print "  resolution %s" % self._resolution
      print "  name %s" % self._name
      print "  periodic %s" % self._periodic
      print "  bucketRadius %s" % self._bucketRadius
      print "  bucketOffset %s" % self._bucketOffset
      print "  bucketsWidth %s" % self._bucketsWidth
      print "  bucketMaxIndex %s" % self._bucketMaxIndex
      print "  bucketMinIndex %s" % self._bucketMinIndex
      print "  verbosity %s" % self._verbosity

  def _createBucketSimHash(self, bucketIndex):
    """
    Generate SimHash for bucket bucketIndex. This uses hashes for the current
    center bucket idex, and bucketRadius neighbor hashes. Current center
    bucket index is weighted higher than neighobrs, and neighbor weightings
    fall off with radius distance. Weighting is inverse-square (commented
    linear weighting line of code is included below too).

    :param int bucketIndex: Required. Bucket index to generate a SimHash
      for (using individual bucket and neighbor SHA-3 hashes, based on
      bucketRadius).

    :returns numpy.ndarray: Numpy uint8 binary array with w bits on. SimHash
      for this bucket index will represent both current index and,
      decreasingly down to bucketRadius, neighbor indices.
    """
    # convert from binary/0 => float/-1.0 for summation, and then weighting
    def __toAdder(binary, weight=1.0):
      adder = numpy.array(binary, numpy.float64)
      adder = numpy.where(adder==0.0, -1.0, adder)
      #adder *= float(weight)  # linear
      adder *= 2 - (1 / float(weight)**2)  # inverse square
      return adder

    # Get bucket hash for current bucket index, and convert to weighted adder
    ownHash = self._createValueHash(bucketIndex)
    ownAdder = __toAdder(ownHash, self._bucketRadius + 1)
    bucketAdders = [ownAdder]
    # Get bucket hashes for neighbor bucket indices (based on radius), then
    #   convert to weighted adders.
    for n in range(1, self._bucketRadius + 1):
      preIndex = bucketIndex - n
      postIndex = bucketIndex + n

      # periodic wrapping
      if self._periodic is True:
        spread = self._bucketMaxIndex - self._bucketMinIndex
        if preIndex < self._bucketMinIndex:
          preIndex += spread + 1
        if postIndex > self._bucketMaxIndex:
          postIndex -= spread + 1

      preHash = self._createValueHash(preIndex)
      postHash = self._createValueHash(postIndex)
      weight = self._bucketRadius + 1 - n
      bucketAdders.insert(0, __toAdder(preHash, weight))
      bucketAdders.append(__toAdder(postHash, weight))

    # sum weighted adder columns for histogram-like totals at each bit position
    simHashSums = numpy.sum(bucketAdders, axis=0)

    # Flatten/quantize sums back to binary for simhash. For our case,
    #   to achieve exact stable sparsity, we take 'w' highest sums.
    # Simhash usual default threshold for 1-bits is: >= 0 (~50% sparse).
    #   simHash = numpy.where(simHashSums >= 0, 1, 0).astype(numpy.uint8)
    simHashSparse = numpy.zeros(self.getWidth(), numpy.uint8)
    wTopSums = numpy.argpartition(simHashSums, -self._w)[-self._w:]
    simHashSparse[wTopSums] = 1

    if self._verbosity > 1:
      print "_createBucketSimHash bucketIndex=%s" % bucketIndex
      if self._verbosity > 2:
        print "  bucketAdders %s" % bucketAdders
        print "  simHashSums %s" % simHashSums
        print "  simHashSparse %s" % simHashSparse
        print "  onbits: %s" % numpy.count_nonzero(simHashSparse)

    return simHashSparse

  def _createValueHash(self, input):
    """
    Generate a SHA-3+SHAKE256 binary hash digest. SHAKE256 gives us a
    variable-length hash digest output string, which is great for SDR output
    encodings (hash functions are usually heavily restricted to small
    2^n-bit-width outputs).

    :param float input: Input scalar value to create a SHA-3+SHAKE256 hash
      for. Hash will be n-bits wide.

    :returns numpy.ndarray: Binary unit8 ndarray of a SHA-3+SHAKE256 hash
      for the requested input value. This will be used later to generate
      a SimHash for this (and neighbor) bucket indices.
    """
    hasher = hashlib.shake_256()
    hasher.update(str(input).encode())
    hashBytes = hasher.digest(self.getWidth() / self._bitsPerByte)
    integers = map(lambda x: ord(x), list(hashBytes))
    bitStrings = map(lambda x: numpy.binary_repr(x).zfill(self._bitsPerByte),
                     integers)
    bits = numpy.array(map(lambda x: list(x), bitStrings),
                       numpy.uint8).flatten()

    if self._verbosity > 1:
      print "_createValueHash input=%s type=%s" % (input, type(input))
      if self._verbosity > 2:
        print "  bytes %s %s" % (str(input).encode(),
                                 type(str(input).encode()))
        print "  hashBytes %s %s %s" % (hashBytes, type(hashBytes),
                                        len(hashBytes))
        print "  integers %s %s %s" % (integers, type(integers),
                                       len(integers))
        print "  bitStrings %s %s %s" % (bitStrings, type(bitStrings),
                                         len(bitStrings))
        print "  bits %s %s %s" % (bits, type(bits), len(bits))

    return bits

  def encodeIntoArray(self, input, output):
    """ See method description in base.py """
    if input is not None and not isinstance(input, numbers.Number):
      raise TypeError("Expected scalar but got input of type %s" % type(input))
    if type(input) is float and math.isnan(input):
      input = SENTINEL_VALUE_FOR_MISSING_DATA

    bucketIndex = self.getBucketIndices(input)[0]
    if bucketIndex is not None:
      # make sure bucket is in bounds
      if (bucketIndex < 0) or (bucketIndex >= self._bucketsWidth):
        raise ValueError("BucketIndex %s has exceeded bounds!" % bucketIndex)

      # adjust bucket edge tracking with bucket growth (new min/max inputs)
      if bucketIndex < self._bucketMinIndex:
        self._bucketMinIndex = bucketIndex
      elif bucketIndex > self._bucketMaxIndex:
        self._bucketMaxIndex = bucketIndex

      # create simash for bucket (bucket hash + neighbor hashes) and return
      bucketSimHash = self._createBucketSimHash(bucketIndex)
      numpy.copyto(output, bucketSimHash)

      if self._verbosity > 1:
        print "encodeIntoArray input=%s" % input
        if self._verbosity > 2:
          print "  bucket simhash %s" % output
          print "  _bucketMinIndex %s" % self._bucketMinIndex
          print "  _bucketMaxIndex %s" % self._bucketMaxIndex

  def getBucketIndices(self, input):
    """ See method description in base.py """
    if ((isinstance(input, float) and math.isnan(input)) or
        input == SENTINEL_VALUE_FOR_MISSING_DATA):
      return [None]
    if self._bucketOffset is None:
      self._bucketOffset = input

    bucketIndex = ((self._bucketsWidth / 2) +
                   int(round((input - self._bucketOffset) / self._resolution)))
    if bucketIndex < 0:
      bucketIndex = 0
    elif bucketIndex >= self._bucketsWidth:
      bucketIndex = self._bucketsWidth - 1

    if self._verbosity > 1:
      print("getBucketIndices input %s = %s" % (input, bucketIndex))

    return [bucketIndex]

  def getDecoderOutputFieldTypes(self):
    """ [Encoder class virtual method override] """
    return (FieldMetaType.float)

  def getDescription(self):
    """ See method description in base.py """
    return [(self._name, 0)]

  def getWidth(self):
    """ See method description in base.py """
    return self._n

  def write(self):
    """ See method description in base.py """
    return None

