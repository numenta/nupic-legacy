# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import numpy

from nupic.data.field_meta import FieldMetaType
from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
from nupic.encoders.base import Encoder, EncoderResult
from nupic.encoders.scalar import ScalarEncoder

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.encoders.category_capnp import CategoryEncoderProto


UNKNOWN = "<UNKNOWN>"



class CategoryEncoder(Encoder):
  """
  Encodes a list of discrete categories (described by strings), that aren't
  related to each other, so we never emit a mixture of categories.

  The value of zero is reserved for "unknown category"

  Internally we use a :class:`.ScalarEncoder` with a radius of 1, but since we
  only encode integers, we never get mixture outputs.

  The :class:`.SDRCategoryEncoder` uses a different method to encode categories.

  :param categoryList: list of discrete string categories
  :param forced: if True, skip checks for parameters' settings; see
                 :class:`.ScalarEncoder` for details. (default False)
  """


  def __init__(self, w, categoryList, name="category", verbosity=0, forced=False):
    self.encoders = None
    self.verbosity = verbosity

    # number of categories includes "unknown"
    self.ncategories = len(categoryList) + 1

    self.categoryToIndex = dict()
    self.indexToCategory = dict()
    self.indexToCategory[0] = UNKNOWN
    for i in xrange(len(categoryList)):
      self.categoryToIndex[categoryList[i]] = i+1
      self.indexToCategory[i+1] = categoryList[i]

    self.encoder = ScalarEncoder(w, minval=0, maxval=self.ncategories - 1,
                      radius=1, periodic=False, forced=forced)
    self.width = w * self.ncategories
    assert self.encoder.getWidth() == self.width

    self.description = [(name, 0)]
    self.name = name

    # These are used to support the topDownCompute method
    self._topDownMappingM = None

    # This gets filled in by getBucketValues
    self._bucketValues = None


  def getDecoderOutputFieldTypes(self):
    """ [Encoder class virtual method override]
    """
    # TODO: change back to string meta-type after the decoding logic is fixed
    #       to output strings instead of internal index values.
    #return (FieldMetaType.string,)
    return (FieldMetaType.integer,)


  def getWidth(self):
    return self.width


  def getDescription(self):
    return self.description


  def getScalars(self, input):
    """ See method description in base.py """
    if input == SENTINEL_VALUE_FOR_MISSING_DATA:
      return numpy.array([None])
    else:
      return numpy.array([self.categoryToIndex.get(input, 0)])


  def getBucketIndices(self, input):
    """ See method description in base.py """

    # Get the bucket index from the underlying scalar encoder
    if input == SENTINEL_VALUE_FOR_MISSING_DATA:
      return [None]
    else:
      return self.encoder.getBucketIndices(self.categoryToIndex.get(input, 0))


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

    return numpy.array([closeness])


  def getBucketValues(self):
    """ See the function description in base.py """

    if self._bucketValues is None:
      numBuckets = len(self.encoder.getBucketValues())
      self._bucketValues = []
      for bucketIndex in range(numBuckets):
        self._bucketValues.append(self.getBucketInfo([bucketIndex])[0].value)

    return self._bucketValues


  def getBucketInfo(self, buckets):
    """ See the function description in base.py
    """

    # For the category encoder, the bucket index is the category index
    bucketInfo = self.encoder.getBucketInfo(buckets)[0]

    categoryIndex = int(round(bucketInfo.value))
    category = self.indexToCategory[categoryIndex]

    return [EncoderResult(value=category, scalar=categoryIndex,
                         encoding=bucketInfo.encoding)]


  def topDownCompute(self, encoded):
    """ See the function description in base.py
    """

    encoderResult = self.encoder.topDownCompute(encoded)[0]
    value = encoderResult.value
    categoryIndex = int(round(value))
    category = self.indexToCategory[categoryIndex]

    return EncoderResult(value=category, scalar=categoryIndex,
                         encoding=encoderResult.encoding)


  @classmethod
  def getSchema(cls):
    return CategoryEncoderProto

  @classmethod
  def read(cls, proto):
    encoder = object.__new__(cls)

    encoder.verbosity = proto.verbosity
    encoder.encoder = ScalarEncoder.read(proto.encoder)
    encoder.width = proto.width
    encoder.description = [(proto.name, 0)]
    encoder.name = proto.name
    encoder.indexToCategory = {x.index: x.category
                               for x in proto.indexToCategory}
    encoder.categoryToIndex = {category: index
                               for index, category
                               in encoder.indexToCategory.items()
                               if category != UNKNOWN}
    encoder._topDownMappingM = None
    encoder.ncategories = len(proto.indexToCategory)
    encoder._bucketValues = None
    encoder.encoders = None

    return encoder


  def write(self, proto):
    proto.width = self.width
    proto.indexToCategory = [
      {"index": index, "category": category}
      for index, category in self.indexToCategory.items()
    ]
    proto.name = self.name
    proto.verbosity = self.verbosity
    self.encoder.write(proto.encoder)
