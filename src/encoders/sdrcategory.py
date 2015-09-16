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

import random

import numpy
from nupic.data.fieldmeta import FieldMetaType
from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
from nupic.encoders.base import Encoder, EncoderResult
from nupic.bindings.math import SM32, GetNTAReal, Random as NupicRandom



class SDRCategoryEncoder(Encoder):
  """Encodes a list of discrete categories (described by strings), that aren't
  related to each other.

  Each  encoding is an SDR in which w out of n bits are turned on.

  Unknown categories are encoded as a single

  Internally we use a ScalarEncoder with a radius of 1, but since we only encode
  integers, we never get mixture outputs.

  The SDRCategoryEncoder uses a different method to encode categories"""


  def __init__(self, n, w, categoryList = None, name="category", verbosity=0,
               encoderSeed=1, forced=False):
    """
    n is  total bits in output
    w is the number of bits that are turned on for each rep
    categoryList is a list of strings that define the categories.
    If "none" then categories will automatically be added as they are encountered.
    forced (default False) : if True, skip checks for parameters' settings; see encoders/scalar.py for details
    """

    self.n = n
    self.w = w

    self._learningEnabled = True

    # initialize the random number generators
    self._seed(encoderSeed)

    if not forced:
      # -- this is just to catch bad parameter choices
      if (self.n/self.w) < 2: # w is 50% of total len
        raise ValueError("Number of ON bits in SDR (%d) must be much smaller than "
                           "the output width (%d)" % (self.w, self.n))

      # Another arbitrary cutoff to catch likely mistakes
      if self.w < 21:
        raise ValueError("Number of bits in the SDR (%d) must be greater than 2, and should be >= 21, pass forced=True to init() to override this check"
                           % self.w)

    self._initOverlap()

    self.verbosity = verbosity

    self.description = [(name, 0)]
    self.name = name

    self.categoryToIndex = dict()
    self.ncategories = 0
    self.categories = list()
    self.sdrs = None

    # Always include an 'unknown' category for
    # edge cases

    self._addCategory("<UNKNOWN>")
    if categoryList is None:
      self._learningEnabled = True
    else:
      self._learningEnabled = False
      for category in categoryList:
        self._addCategory(category)
      assert self.ncategories == len(categoryList) + 1

    # Not used by this class. Used for decoding (scalarsToStr())
    self.encoders = None

    # This matrix is used for the topDownCompute. We build it the first time
    #  topDownCompute is called
    self._topDownMappingM = None
    self._topDownValues = None


  def _initOverlap(self):
    # Calculate average overlap of SDRs for decoding
    # Density is fraction of bits on, and it is also the
    # probability that any individual bit is on.
    density = float(self.w) / self.n
    self.averageOverlap =  self.w * density
    # We can do a better job of calculating the threshold. For now, just
    # something quick and dirty, which is the midway point between average
    # and full overlap. averageOverlap is always < w,  so the threshold
    # is always < w.
    self.thresholdOverlap =  int((self.averageOverlap + self.w)/2)
    #  1.25 -- too sensitive for decode test, so make it less sensitive
    if self.thresholdOverlap < self.w - 3:
      self.thresholdOverlap = self.w - 3


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
    """ [Encoder class virtual method override]
    """
    # TODO: change back to string meta-type after the decoding logic is fixed
    #       to output strings instead of internal index values.
    return (FieldMetaType.string,)
    #return (FieldMetaType.integer,)


  def  _addCategory(self, category):
    if category in self.categories:
      raise RuntimeError("Attempt to add add encoder category '%s' "
                         "that already exists" % category)

    if self.sdrs is None:
      assert self.ncategories == 0
      assert len(self.categoryToIndex) == 0
      # Initial allocation -- 16 rows
      self.sdrs = numpy.zeros((16, self.n), dtype='uint8')
    elif self.ncategories > self.sdrs.shape[0] - 2:
      # Preallocated sdrs are used up. Double our size
      currentMax = self.sdrs.shape[0]
      newsdrs = numpy.zeros((currentMax * 2, self.n), dtype='uint8')
      newsdrs[0:currentMax] = self.sdrs[0:currentMax]
      self.sdrs = newsdrs

    newrep = self._newRep()
    self.sdrs[self.ncategories] = newrep
    self.categories.append(category)
    self.categoryToIndex[category] = self.ncategories
    self.ncategories += 1
    self._topDownMappingM = None


  def _newRep(self):
    """Generate a new and unique representation. Returns a numpy array
    of shape (n,). """
    maxAttempts = 1000

    for _ in xrange(maxAttempts):
      foundUnique = True
      population = numpy.arange(self.n, dtype=numpy.uint32)
      choices = numpy.arange(self.w, dtype=numpy.uint32)
      oneBits = sorted(self.random.sample(population, choices))
      sdr =  numpy.zeros(self.n, dtype='uint8')
      sdr[oneBits] = 1
      for i in xrange(self.ncategories):
        if (sdr == self.sdrs[i]).all():
          foundUnique = False
          break
      if foundUnique:
        break;
    if not foundUnique:
      raise RuntimeError("Error, could not find unique pattern %d after "
                         "%d attempts" % (self.ncategories, maxAttempts))
    return sdr


  def getWidth(self):
    return self.n


  def getDescription(self):
    return self.description


  def getScalars(self, input):
    """ See method description in base.py """
    if input == SENTINEL_VALUE_FOR_MISSING_DATA:
        return numpy.array([0])

    index = self.categoryToIndex.get(input, None)
    if index is None:
      if self._learningEnabled:
        self._addCategory(input)
        index = self.ncategories - 1
      else:
        # if not found, we encode category 0
        index = 0

    return numpy.array([index])


  def getBucketIndices(self, input):
    """ See method description in base.py """

    # For category encoder, the "scalar" we map to each category is the
    #  bucket index
    return self.getScalars(input)


  def encodeIntoArray(self, input, output):
    if input == SENTINEL_VALUE_FOR_MISSING_DATA:
      output[0:self.n] = 0
      index = 0
    else:
      index = self.getBucketIndices(input)[0]
      output[0:self.n] = self.sdrs[index,:]

    if self.verbosity >= 2:
      print "input:", input, "index:", index, "output:", output
      print "decoded:", self.decodedToStr(self.decode(output))


  def decode(self, encoded, parentFieldName=''):
    """ See the function description in base.py
    """

    assert (encoded[0:self.n] <= 1.0).all()

    resultString =  ""
    resultRanges = []

    overlaps =  (self.sdrs * encoded[0:self.n]).sum(axis=1)

    if self.verbosity >= 2:
      print "Overlaps for decoding:"
      for i in xrange(0, self.ncategories):
        print "%d %s" % (overlaps[i], self.categories[i])

    matchingCategories =  (overlaps > self.thresholdOverlap).nonzero()[0]

    for index in matchingCategories:
      if resultString != "":
        resultString += " "
      resultString +=  str(self.categories[index])
      resultRanges.append([int(index),int(index)])

    if parentFieldName != '':
      fieldName = "%s.%s" % (parentFieldName, self.name)
    else:
      fieldName = self.name
    return ({fieldName: (resultRanges, resultString)}, [fieldName])


  def _getTopDownMapping(self):
    """ Return the interal _topDownMappingM matrix used for handling the
    bucketInfo() and topDownCompute() methods. This is a matrix, one row per
    category (bucket) where each row contains the encoded output for that
    category.
    """

    # -------------------------------------------------------------------------
    # Do we need to build up our reverse mapping table?
    if self._topDownMappingM is None:

      # Each row represents an encoded output pattern
      self._topDownMappingM = SM32(self.ncategories, self.n)

      outputSpace = numpy.zeros(self.n, dtype=GetNTAReal())
      for i in xrange(self.ncategories):
        self.encodeIntoArray(self.categories[i], outputSpace)
        self._topDownMappingM.setRowFromDense(i, outputSpace)

    return self._topDownMappingM


  def getBucketValues(self):
    """ See the function description in base.py """

    return self.categories


  def getBucketInfo(self, buckets):
    """ See the function description in base.py
    """

    if self.ncategories==0:
      return 0

    topDownMappingM = self._getTopDownMapping()

    categoryIndex = buckets[0]
    category = self.categories[categoryIndex]
    encoding = topDownMappingM.getRow(categoryIndex)

    return [EncoderResult(value=category, scalar=categoryIndex,
                          encoding=encoding)]


  def topDownCompute(self, encoded):
    """ See the function description in base.py
    """

    if self.ncategories==0:
      return 0

    topDownMappingM = self._getTopDownMapping()

    categoryIndex = topDownMappingM.rightVecProd(encoded).argmax()
    category = self.categories[categoryIndex]
    encoding = topDownMappingM.getRow(categoryIndex)

    return EncoderResult(value=category, scalar=categoryIndex, encoding=encoding)


  def closenessScores(self, expValues, actValues, fractional=True):
    """ See the function description in base.py

    kwargs will have the keyword "fractional", which is ignored by this encoder
    """

    expValue = expValues[0]
    actValue = actValues[0]

    if expValue == actValue:
      closeness = 1.0
    else:
      closeness = 0.0

    if not fractional:
      closeness = 1.0 - closeness

    return numpy.array([closeness])


  @classmethod
  def read(cls, proto):
    encoder = object.__new__(cls)

    encoder.n = proto.n
    encoder.w = proto.w
    encoder.random = NupicRandom()
    encoder.random.read(proto.random)
    encoder.verbosity = proto.verbosity
    encoder.name = proto.name
    encoder.description = [(proto.name, 0)]
    encoder.categories = list(proto.categories)
    encoder.sdrs = numpy.array(proto.sdrs, dtype=numpy.uint8)

    encoder.categoryToIndex = {category:index
                               for index, category
                               in enumerate(encoder.categories)}
    encoder.ncategories = len(encoder.categories)
    encoder._learningEnabled = False
    encoder._initOverlap()

    return encoder


  def write(self, proto):
    proto.n = self.n
    proto.w = self.w
    self.random.write(proto.random)
    proto.verbosity = self.verbosity
    proto.name = self.name
    proto.categories = self.categories
    proto.sdrs = self.sdrs.tolist()
