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
from scalar import ScalarEncoder
from nupic.bindings.math import SM32, GetNTAReal
from nupic.data.fieldmeta import FieldMetaType
from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA

############################################################################
class CategoryEncoder(Encoder):
  """Encodes a list of discrete categories (described by strings), that aren't
  related to each other, so we never emit a mixture of categories.

  The value of zero is reserved for "unknown category"

  Internally we use a ScalarEncoder with a radius of 1, but since we only encode
  integers, we never get mixture outputs.

  The SDRCategoryEncoder uses a different method to encode categories"""

  ############################################################################
  def __init__(self, w, categoryList, name="category", verbosity=0):

    self.encoders = None
    self.verbosity = verbosity

    # number of categories includes "unknown"
    self.ncategories = len(categoryList) + 1

    self.categoryToIndex = dict()
    self.indexToCategory = dict()
    self.indexToCategory[0] = "<UNKNOWN>"
    for i in xrange(len(categoryList)):
      self.categoryToIndex[categoryList[i]] = i+1
      self.indexToCategory[i+1] = categoryList[i]

    self.encoder = ScalarEncoder(w, minval=0, maxval=self.ncategories - 1,
                      radius=1, periodic=False)
    self.width = w * self.ncategories
    assert self.encoder.getWidth() == self.width

    self.description = [(name, 0)]
    self.name = name

    # These are used to support the topDownCompute method
    self._topDownMappingM = None

    # This gets filled in by getBucketValues
    self._bucketValues = None


  ############################################################################
  def getDecoderOutputFieldTypes(self):
    """ [Encoder class virtual method override]
    """
    # TODO: change back to string meta-type after the decoding logic is fixed
    #       to output strings instead of internal index values.
    #return (FieldMetaType.string,)
    return (FieldMetaType.integer,)


  ############################################################################
  def getWidth(self):
    return self.width

  ############################################################################
  def getDescription(self):
    return self.description

  ############################################################################
  def getScalars(self, input):
    """ See method description in base.py """
    if input == SENTINEL_VALUE_FOR_MISSING_DATA:
      return numpy.array([None])
    else:
      return numpy.array([self.categoryToIndex.get(input, 0)])


  ############################################################################
  def getBucketIndices(self, input):
    """ See method description in base.py """

    # Get the bucket index from the underlying scalar encoder
    if input == SENTINEL_VALUE_FOR_MISSING_DATA:
      return [None]
    else:
      return self.encoder.getBucketIndices(self.categoryToIndex.get(input, 0))



  ############################################################################
  def encodeIntoArray(self, input, output):
    # if not found, we encode category 0
    if input == SENTINEL_VALUE_FOR_MISSING_DATA:
      output[0:] = 0
      val = "<missing>"
    else:
      val = self.categoryToIndex.get(input, 0)
      self.encoder.encodeIntoArray(val, output)

    if self.verbosity >= 2:
      print "input:", input, "va:", val, "output:", output
      print "decoded:", self.decodedToStr(self.decode(output))


  ############################################################################
  def decode(self, encoded, parentFieldName=''):
    """ See the function description in base.py
    """

    # Get the scalar values from the underlying scalar encoder
    (fieldsDict, fieldNames) = self.encoder.decode(encoded)
    if len(fieldsDict) == 0:
      return (fieldsDict, fieldNames)

    # Expect only 1 field
    assert(len(fieldsDict) == 1)

    # Get the list of categories the scalar values correspond to and
    #  generate the description from the category name(s).
    (inRanges, inDesc) = fieldsDict.values()[0]
    outRanges = []
    desc = ""
    for (minV, maxV) in inRanges:
      minV = int(round(minV))
      maxV = int(round(maxV))
      outRanges.append((minV, maxV))
      while minV <= maxV:
        if len(desc) > 0:
          desc += ", "
        desc += self.indexToCategory[minV]
        minV += 1

    # Return result
    if parentFieldName != '':
      fieldName = "%s.%s" % (parentFieldName, self.name)
    else:
      fieldName = self.name
    return ({fieldName: (outRanges, desc)}, [fieldName])


  ############################################################################
  def closenessScores(self, expValues, actValues, fractional=True,):
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

    #print "category::", "expValue:", expValue, "actValue:", actValue, \
    #      "closeness", closeness
    #import pdb; pdb.set_trace()

    return numpy.array([closeness])



  ############################################################################
  def getBucketValues(self):
    """ See the function description in base.py """

    if self._bucketValues is None:
      numBuckets = len(self.encoder.getBucketValues())
      self._bucketValues = []
      for bucketIndex in range(numBuckets):
        self._bucketValues.append(self.getBucketInfo([bucketIndex])[0].value)

    return self._bucketValues

  ############################################################################
  def getBucketInfo(self, buckets):
    """ See the function description in base.py
    """

    # For the category encoder, the bucket index is the category index
    bucketInfo = self.encoder.getBucketInfo(buckets)[0]

    categoryIndex = int(round(bucketInfo.value))
    category = self.indexToCategory[categoryIndex]

    return [EncoderResult(value=category, scalar=categoryIndex,
                         encoding=bucketInfo.encoding)]



  ############################################################################
  def topDownCompute(self, encoded):
    """ See the function description in base.py
    """

    encoderResult = self.encoder.topDownCompute(encoded)[0]
    value = encoderResult.value
    categoryIndex = int(round(value))
    category = self.indexToCategory[categoryIndex]

    return EncoderResult(value=category, scalar=categoryIndex,
                         encoding=encoderResult.encoding)


############################################################################
def testCategoryEncoder():
  verbosity = 0

  print "Testing CategoryEncoder...",
  categories = ["ES", "GB", "US"]

  e = CategoryEncoder(w=3, categoryList=categories)
  output = e.encode("US")
  assert (output == numpy.array([0,0,0,0,0,0,0,0,0,1,1,1], dtype=defaultDtype)).all()

  # Test reverse lookup
  decoded = e.decode(output)
  (fieldsDict, fieldNames) = decoded
  assert len(fieldsDict) == 1
  (ranges, desc) = fieldsDict.values()[0]
  assert len(ranges) == 1 and numpy.array_equal(ranges[0], [3,3])
  print "decodedToStr of", ranges, "=>", e.decodedToStr(decoded)

  # Test topdown compute
  for v in categories:
    output = e.encode(v)
    topDown = e.topDownCompute(output)
    assert topDown.value == v
    assert topDown.scalar == e.getScalars(v)[0]

    bucketIndices = e.getBucketIndices(v)
    print "bucket index =>", bucketIndices[0]
    topDown = e.getBucketInfo(bucketIndices)[0]
    assert topDown.value == v
    assert topDown.scalar == e.getScalars(v)[0]
    assert (topDown.encoding == output).all()
    assert topDown.value == e.getBucketValues()[bucketIndices[0]]



  # ---------------------
  # unknown category
  output = e.encode("NA")
  assert (output == numpy.array([1,1,1,0,0,0,0,0,0,0,0,0], dtype=defaultDtype)).all()

  # Test reverse lookup
  decoded = e.decode(output)
  (fieldsDict, fieldNames) = decoded
  assert len(fieldsDict) == 1
  (ranges, desc) = fieldsDict.values()[0]
  assert len(ranges) == 1 and numpy.array_equal(ranges[0], [0,0])
  print "decodedToStr of", ranges, "=>", e.decodedToStr(decoded)

  # Test topdown compute
  topDown = e.topDownCompute(output)
  assert topDown.value == "<UNKNOWN>"
  assert topDown.scalar == 0


  # --------------------------------
  # ES
  output = e.encode("ES")
  assert (output == numpy.array([0,0,0,1,1,1,0,0,0,0,0,0], dtype=defaultDtype)).all()

  # MISSING VALUE
  outputForMissing = e.encode(SENTINEL_VALUE_FOR_MISSING_DATA)
  assert sum(outputForMissing) == 0

  # Test reverse lookup
  decoded = e.decode(output)
  (fieldsDict, fieldNames) = decoded
  assert len(fieldsDict) == 1
  (ranges, desc) = fieldsDict.values()[0]
  assert len(ranges) == 1 and numpy.array_equal(ranges[0], [1,1])
  print "decodedToStr of", ranges, "=>", e.decodedToStr(decoded)

  # Test topdown compute
  topDown = e.topDownCompute(output)
  assert topDown.value == "ES"
  assert topDown.scalar == e.getScalars("ES")[0]


  # --------------------------------
  # Multiple categories
  output.fill(1)

  # Test reverse lookup
  decoded = e.decode(output)
  (fieldsDict, fieldNames) = decoded
  assert len(fieldsDict) == 1
  (ranges, desc) = fieldsDict.values()[0]
  assert len(ranges) == 1 and numpy.array_equal(ranges[0], [0,3])
  print "decodedToStr of", ranges, "=>", e.decodedToStr(decoded)



  # -------------------------------------------------------------
  # Test with width = 1
  categories = ["cat1", "cat2", "cat3", "cat4", "cat5"]
  e = CategoryEncoder(w=1, categoryList=categories)
  for cat in categories:
    output = e.encode(cat)
    topDown = e.topDownCompute(output)
    if verbosity >= 1:
      print cat, "->", output, output.nonzero()[0]
      print " scalarTopDown:", e.encoder.topDownCompute(output)
      print " topdown:", topDown
    assert topDown.value == cat
    assert topDown.scalar == e.getScalars(cat)[0]


  # -------------------------------------------------------------
  # Test with width = 9, removing some bits end the encoded output
  categories = ["cat%d" % (x) for x in range(1, 10)]
  e = CategoryEncoder(w=9, categoryList=categories)
  for cat in categories:
    output = e.encode(cat)
    topDown = e.topDownCompute(output)
    if verbosity >= 1:
      print cat, "->", output, output.nonzero()[0]
      print " scalarTopDown:", e.encoder.topDownCompute(output)
      print " topdown:", topDown
    assert topDown.value == cat
    assert topDown.scalar == e.getScalars(cat)[0]

    # Get rid of 1 bit on the left
    outputNZs = output.nonzero()[0]
    output[outputNZs[0]] = 0
    topDown = e.topDownCompute(output)
    if verbosity >= 1:
      print "missing 1 bit on left:", output, output.nonzero()[0]
      print " scalarTopDown:", e.encoder.topDownCompute(output)
      print " topdown:", topDown
    assert topDown.value == cat
    assert topDown.scalar == e.getScalars(cat)[0]

    # Get rid of 1 bit on the right
    output[outputNZs[0]] = 1
    output[outputNZs[-1]] = 0
    topDown = e.topDownCompute(output)
    if verbosity >= 1:
      print "missing 1 bit on right:", output, output.nonzero()[0]
      print " scalarTopDown:", e.encoder.topDownCompute(output)
      print " topdown:", topDown
    assert topDown.value == cat
    assert topDown.scalar == e.getScalars(cat)[0]

    # Get rid of 4 bits on the left
    output.fill(0)
    output[outputNZs[-5:]] = 1
    topDown = e.topDownCompute(output)
    if verbosity >= 1:
      print "missing 4 bits on left:", output, output.nonzero()[0]
      print " scalarTopDown:", e.encoder.topDownCompute(output)
      print " topdown:", topDown
    assert topDown.value == cat
    assert topDown.scalar == e.getScalars(cat)[0]

    # Get rid of 4 bits on the right
    output.fill(0)
    output[outputNZs[0:5]] = 1
    topDown = e.topDownCompute(output)
    if verbosity >= 1:
      print "missing 4 bits on right:", output, output.nonzero()[0]
      print " scalarTopDown:", e.encoder.topDownCompute(output)
      print " topdown:", topDown
    assert topDown.value == cat
    assert topDown.scalar == e.getScalars(cat)[0]


  # OR together the output of 2 different categories, we should not get
  #  back the mean, but rather one or the other
  output1 = e.encode("cat1")
  output2 = e.encode("cat9")
  output = output1 + output2
  topDown = e.topDownCompute(output)
  if verbosity >= 1:
    print "cat1 + cat9 ->", output, output.nonzero()[0]
    print " scalarTopDown:", e.encoder.topDownCompute(output)
    print " topdown:", topDown
  assert topDown.scalar == e.getScalars("cat1")[0] \
          or topDown.scalar == e.getScalars("cat9")[0]



  print "passed"


################################################################################
if __name__=='__main__':

  # Run all tests
  testCategoryEncoder()