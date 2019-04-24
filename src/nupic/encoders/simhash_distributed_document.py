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
import numpy
import sha3

from nupic.data.field_meta import FieldMetaType
from nupic.encoders.base import Encoder


class SimHashDistributedDocumentEncoder(Encoder):
  """
  SimHash Distributed Document Encoder.

  A Locality-Sensitive Hashing approach towards encoding semantic document
  text data into Sparse Distributed Representations, ready to be fed into an
  Hierarchical Temporal Memory, like NuPIC. This uses the SimHash algorithm to
  accomplish this. LSH and SimHash come from the world of nearest-neighbor
  document similarity searching. This is the exact same approach used in the
  SimHash Distributed Scalar Encoder.

  Document Tokens are supplied with opitional weighting values. We generate a
  SHA-3 hash digest for each word token (using SHAKE256 to get a variable-
  width digest output size). The hashes for a document are combined into a
  sparse SimHash. Documents that are semantically similar will have similar
  encodings. Dissimilar documents will have very different encodings from
  each other.

  :param int n: Required. Number of bits in the representation (must be > w).
    n must be large enough such that there is enough room to select new
    representations as the range grows. A value of n=400 is typical.

  :param int w: Required. Number of bits to set in output. w must be odd to
    avoid centering problems. w must be large enough that spatial pooler
    columns will have a sufficiently large overlap to avoid false matches.
    A value of w=21 is typical.

  :param str name: Name for this encoder instance. It will become part of
    the description and debugging output.

  :param int verbosity: Controlling the level of debugging output. A value
    of 0 implies no output. verbosity=1 may lead to one-time printouts during
    construction, serialization or deserialization. verbosity=2 may lead to
    some output per encode operation. verbosity>2 may lead to significantly
    more output.
  """

  def __init__(self,
               n,
               w,
               name=None,
               verbosity=0):
    """ Constructor - See base.py """
    if (n <= 0) or (n < w):
      raise ValueError("n must be: positive integer, more than w")
    if (w <= 0) or (w > n):
      raise ValueError("w must be: positive integer, less than n")
    if (w % 2 == 0):
      raise ValueError("w must be: an odd number")

    self._bitsPerByte = (255).bit_length()
    self._n = n
    self._w = w
    self._name = "[SHaDDE:%s:%s]" % (n, w)
    if name is not None:
      self._name = name
    self._verbosity = verbosity

    if self._verbosity > 0:
      print "SimHashDistrubutedDocumentEncoder"
      print "  bitsPerByte %s" % self._bitsPerByte
      print "  n %s" % self.getWidth()
      print "  w %s" % self._w
      print "  name %s" % self._name
      print "  verbosity %s" % self._verbosity

  def _createDocumentSimHash(self, hashes, weights):
    """
    Generate SimHash for Document. This uses token hashes for the current
    document. Weights will be applied if supplied.

    :param list hashes: Required. List of word token hashes, to be SimHashed.

    :returns numpy.ndarray: Numpy uint8 binary array with w bits on. SimHash
      for this document will represent all the token hashes for that document.
      Similar representations will have similar simhashes, differing documents
      will not.
    """
    def __toAdder(binary, weight=1.0):
      """ Convert from binary/0 => float/-1.0 for summation. then weight. """
      adder = numpy.array(binary, numpy.float64)
      adder = numpy.where(adder==0.0, -1.0, adder)
      adder *= float(weight)  # linear
      return adder

    # convert from binary/0 => float/-1.0 for summation, and then weighting
    adders = map(lambda (i, h): __toAdder(h, weights[i]),
                 list(enumerate(hashes)))

    # sum weighted adder columns for histogram-like totals at each bit position
    simHashSums = numpy.sum(adders, axis=0)

    # Flatten/quantize sums back to binary for simhash. For our case,
    #   to achieve exact stable sparsity, we take 'w' highest sums.
    # Simhash usual default threshold for 1-bits is: >= 0 (~50% sparse).
    #   simHash = numpy.where(simHashSums >= 0, 1, 0).astype(numpy.uint8)
    simHashSparse = numpy.zeros(self.getWidth(), numpy.uint8)
    wTopSums = numpy.argpartition(simHashSums, -self._w)[-self._w:]
    simHashSparse[wTopSums] = 1

    if self._verbosity > 1:
      print "_createDocumentSimHash"
      if self._verbosity > 2:
        print "  hashes %s" % hashes
        print "  weights %s" % weights
        print "  adders %s" % adders
        print "  simHashSums %s" % simHashSums
        print "  simHashSparse %s" % simHashSparse
        print "  onbits: %s" % numpy.count_nonzero(simHashSparse)

    return simHashSparse

  def _createTokenHash(self, input):
    """
    Generate a SHA-3+SHAKE256 binary hash digest. SHAKE256 gives us a
    variable-length hash digest output string, which is great for SDR output
    encodings (hash functions are usually heavily restricted to small
    2^n-bit-width outputs).

    :param str input: Input text string (word token from document, for simash)
      used to create a SHA-3+SHAKE256 hash. Hash digest will be n-bits wide.

    :returns numpy.ndarray: Binary unit8 ndarray of a SHA-3+SHAKE256 hash
      for the requested input token. This will be used later to generate
      a SimHash for the current document.
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
      print "_createTokenHash input=%s type=%s" % (input, type(input))
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
    """
    See method description in base.py

    TODO

    :param list/dict input: TODO
    """
    hashes = []
    tokens = []
    weights = []

    # process tokens from input
    if type(input) is list:
      tokens = input
      weights = weights + [1]*len(tokens)
    elif type(input) is dict:
      tokens = input.keys()
      weights = input.values()
    else:
      raise TypeError("input type must be: list or dict")

    hashes = map(lambda h: self._createTokenHash(h), tokens)

    if hashes is not None:
      simhash = self._createDocumentSimHash(hashes, weights)
      numpy.copyto(output, simhash)

      if self._verbosity > 1:
        print "encodeIntoArray input=%s" % input
        if self._verbosity > 2:
          print "  bucket simhash %s" % output

  def getDecoderOutputFieldTypes(self):
    """ [Encoder class virtual method override] """
    return (FieldMetaType.str)

  def getDescription(self):
    """ See method description in base.py """
    return [(self._name, 0)]

  def getWidth(self):
    """ See method description in base.py """
    return self._n

  def write(self):
    """ See method description in base.py """
    return None

