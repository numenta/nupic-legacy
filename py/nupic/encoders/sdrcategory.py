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

from base import *
from nupic.bindings.math import SM32, GetNTAReal
import random
import math
from nupic.data.fieldmeta import FieldMetaType
from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA

############################################################################
class SDRCategoryEncoder(Encoder):
  """Encodes a list of discrete categories (described by strings), that aren't
  related to each other.

  Each  encoding is an SDR in which w out of n bits are turned on.

  Unknown categories are encoded as a single

  Internally we use a ScalarEncoder with a radius of 1, but since we only encode
  integers, we never get mixture outputs.

  The SDRCategoryEncoder uses a different method to encode categories"""

  ############################################################################
  def __init__(self, n, w, categoryList = None, name="category", verbosity=0,
               encoderSeed=1):
    """
    n is  total bits in output
    w is the number of bits that are turned on for each rep
    categoryList is a list of strings that define the categories.
    If "none" then categories will automatically be added as they are encountered.
    """

    self.n = n
    self.w = w

    self._learningEnabled = True
    self.random = random.Random()
    if encoderSeed != -1:
        self.random.seed(encoderSeed)

    # TODO: discuss whether this is important. Was commented out to
    # enable certain experiments.
    #
    # "5" is arbitrary -- this is just to catch bad parameter choices
    #if self.w >= self.n - 4:
    #  raise RuntimeError("Number of bits in SDR (%d) must be much smaller than "
    #                     "the output width (%d)" % (self.w, self.n))

    # Another arbitrary cutoff to catch likely mistakes
    if self.w < 3:
      raise RuntimeError("Number of bits in the SDR (%d) must be greater than 2"
                         % self.w)


    # Calculate average overlap of SDRs for decoding
    # Density is fraction of bits on, and it is also the
    # probability that any individual bit is on.
    density = float(self.w) / self.n
    self.averageOverlap =  w * density
    # We can do a better job of calculating the threshold. For now, just
    # something quick and dirty, which is the midway point between average
    # and full overlap. averageOverlap is always < w,  so the threshold
    # is always < w.
    self.thresholdOverlap =  int((self.averageOverlap + self.w)/2)
    #  1.25 -- too sensitive for decode test, so make it less sensitive
    if self.thresholdOverlap < self.w - 3:
      self.thresholdOverlap = self.w - 3

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


  ############################################################################
  def getDecoderOutputFieldTypes(self):
    """ [Encoder class virtual method override]
    """
    # TODO: change back to string meta-type after the decoding logic is fixed
    #       to output strings instead of internal index values.
    return (FieldMetaType.string,)
    #return (FieldMetaType.integer,)


  ############################################################################
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


  ############################################################################
  def _newRep(self):
    """Generate a new and unique representation. Returns a numpy array
    of shape (n,). """
    maxAttempts = 1000

    for attempt in xrange(maxAttempts):
      foundUnique = True
      oneBits = sorted(self.random.sample(xrange(self.n), self.w))
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


  ############################################################################
  def getWidth(self):
    return self.n

  ############################################################################
  def getDescription(self):
    return self.description

  ############################################################################
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

  ############################################################################
  def getBucketIndices(self, input):
    """ See method description in base.py """

    # For category encoder, the "scalar" we map to each category is the
    #  bucket index
    return self.getScalars(input)

  ############################################################################
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



  ############################################################################
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


  ############################################################################
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


  ############################################################################
  def getBucketValues(self):
    """ See the function description in base.py """

    return self.categories


  ############################################################################
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

  ############################################################################
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

  ############################################################################
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


############################################################################
def testSDRCategoryEncoder():
  print "Testing CategoryEncoder...",
  # make sure we have > 16 categories so that we have to grow our sdrs
  categories = ["ES", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8",
                "S9","S10", "S11", "S12", "S13", "S14", "S15", "S16",
                "S17", "S18", "S19", "GB", "US"]

  fieldWidth = 100
  bitsOn = 10

  s = SDRCategoryEncoder(n=fieldWidth, w=bitsOn, categoryList = categories,
                         name="foo", verbosity=0)

  # internal check
  assert s.sdrs.shape == (32, fieldWidth)

  # ES
  es = s.encode("ES")
  assert es.sum() == bitsOn
  assert es.shape == (fieldWidth,)
  assert es.sum() == bitsOn

  x = s.decode(es)
  assert isinstance(x[0], dict)
  assert "foo" in x[0]
  assert x[0]["foo"][1] == "ES"

  topDown = s.topDownCompute(es)
  assert topDown.value == 'ES'
  assert topDown.scalar == 1
  assert topDown.encoding.sum() == bitsOn

  # ----------------------------------------------------------------------
  # Test topdown compute
  for v in categories:
    output = s.encode(v)
    topDown = s.topDownCompute(output)
    assert topDown.value == v
    assert topDown.scalar == s.getScalars(v)[0]

    bucketIndices = s.getBucketIndices(v)
    print "bucket index =>", bucketIndices[0]
    topDown = s.getBucketInfo(bucketIndices)[0]
    assert topDown.value == v
    assert topDown.scalar == s.getScalars(v)[0]
    assert (topDown.encoding == output).all()
    assert topDown.value == s.getBucketValues()[bucketIndices[0]]


  # Unknown
  unknown = s.encode("ASDFLKJLK")
  assert unknown.sum() == bitsOn
  assert unknown.shape == (fieldWidth,)
  assert unknown.sum() == bitsOn
  x = s.decode(unknown)
  assert x[0]["foo"][1] == "<UNKNOWN>"

  topDown = s.topDownCompute(unknown)
  assert topDown.value == "<UNKNOWN>"
  assert topDown.scalar == 0

  # US
  us = s.encode("US")
  assert us.sum() == bitsOn
  assert us.shape == (fieldWidth,)
  assert us.sum() == bitsOn
  x = s.decode(us)
  assert x[0]["foo"][1] == "US"

  topDown = s.topDownCompute(us)
  assert topDown.value == "US"
  assert topDown.scalar == len(categories)
  assert topDown.encoding.sum() == bitsOn

  # empty field
  empty = s.encode(SENTINEL_VALUE_FOR_MISSING_DATA)
  assert empty.sum() == 0
  assert empty.shape == (fieldWidth,)
  assert empty.sum() == 0

  # make sure it can still be decoded after a change
  bit =  s.random.randint(0, s.getWidth()-1)
  us[bit] = 1 - us[bit]
  x = s.decode(us)
  assert x[0]["foo"][1] == "US"


  # add two reps together
  newrep = ((us + unknown) > 0).astype('uint8')
  x = s.decode(newrep)
  name =x[0]["foo"][1]
  if name != "US <UNKNOWN>" and name != "<UNKNOWN> US":
    othercategory = name.replace("US", "")
    othercategory = othercategory.replace("<UNKNOWN>", "")
    othercategory = othercategory.replace(" ", "")
    otherencoded = s.encode(othercategory)
    print "Got: %s instead of US/unknown" % name
    print "US: %s" % us
    print "unknown: %s" % unknown
    print "Sum: %s" % newrep
    print "%s: %s" % (othercategory, s.encode(othercategory))

    print "Matches with US: %d" % (us * newrep).sum()
    print "Matches with unknown: %d" % (unknown * newrep).sum()
    print "Matches with %s: %d" % (othercategory,
                     (otherencoded * newrep).sum())

    raise RuntimeError("Decoding failure")

  # serialization
  import cPickle as pickle
  t = pickle.loads(pickle.dumps(s))
  assert (t.encode("ES") == es).all()
  assert (t.encode("GB") == s.encode("GB")).all()


  # Test autogrow
  s = SDRCategoryEncoder(n=fieldWidth, w=bitsOn, categoryList = None, name="bar")

  es = s.encode("ES")
  assert es.shape == (fieldWidth,)
  assert es.sum() == bitsOn
  x = s.decode(es)
  assert isinstance(x[0], dict)
  assert "bar" in x[0]
  assert x[0]["bar"][1] == "ES"


  us = s.encode("US")
  assert us.shape == (fieldWidth,)
  assert us.sum() == bitsOn
  x = s.decode(us)
  assert x[0]["bar"][1] == "US"

  es2 = s.encode("ES")
  assert (es2 == es).all()

  us2 = s.encode("US")
  assert (us2 == us).all()

  # make sure it can still be decoded after a change
  bit =  s.random.randint(0, s.getWidth()-1)
  us[bit] = 1 - us[bit]
  x = s.decode(us)
  assert x[0]["bar"][1] == "US"

  # add two reps together
  newrep = ((us + es) > 0).astype('uint8')
  x = s.decode(newrep)
  name =x[0]["bar"][1]
  assert name == "US ES" or name == "ES US"

  # Catch duplicate categories
  caughtException = False
  newcategories = categories[:]
  assert "ES" in newcategories
  newcategories.append("ES")
  try:
    s = SDRCategoryEncoder(n=fieldWidth, w=bitsOn, categoryList = newcategories, name="foo")
  except RuntimeError, e:
    caughtException = True
  if not caughtException:
    raise RuntimeError("Did not catch duplicate category in constructor")
    raise

  # serialization for autogrow encoder
  gs = s.encode("GS")
  t = pickle.loads(pickle.dumps(s))
  assert (t.encode("ES") == es).all()
  assert (t.encode("GS") == gs).all()

  testAutogrow()

  print "passed"

# -----------------------------------------------------------------------

def testAutogrow():
  fieldWidth = 100
  bitsOn = 10

  s = SDRCategoryEncoder(n=fieldWidth, w=bitsOn, name="foo", verbosity=2)

  encoded = numpy.zeros(fieldWidth)
  assert s.topDownCompute(encoded).value == "<UNKNOWN>"

  s.encodeIntoArray("catA", encoded)
  assert encoded.sum() == bitsOn
  assert s.getScalars('catA') == 1
  catA = encoded.copy()

  s.encodeIntoArray("catB", encoded)
  assert encoded.sum() == bitsOn
  assert s.getScalars('catB') == 2
  catB = encoded.copy()

  assert s.topDownCompute(catA).value == 'catA'
  assert s.topDownCompute(catB).value == 'catB'

  s.encodeIntoArray(SENTINEL_VALUE_FOR_MISSING_DATA, encoded)
  assert sum(encoded) == 0
  assert s.topDownCompute(encoded).value == "<UNKNOWN>"

  #Test Disabling Learning and autogrow
  s.setLearning(False)
  s.encodeIntoArray("catC", encoded)
  assert encoded.sum() == bitsOn
  assert s.getScalars('catC') == 0
  assert s.topDownCompute(encoded).value == "<UNKNOWN>"

  s.setLearning(True)
  s.encodeIntoArray("catC", encoded)
  assert encoded.sum() == bitsOn
  assert s.getScalars('catC') == 3
  assert s.topDownCompute(encoded).value == "catC"



################################################################################
if __name__=='__main__':

  # Run all tests
  testSDRCategoryEncoder()