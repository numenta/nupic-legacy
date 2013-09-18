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

import numpy
defaultDtype = numpy.uint8
from utils import bitsToString
from collections import namedtuple

"""Classes for encoding different types of values into bitstrings for HTM input"""

################################################################################
# EncoderResult class
# -----------------------------------------------------------------------
# Tuple to represent the results of computations in different forms.
# value:    A representation of the encoded value in the same format as the input
#           (i.e. float for scalars, string for categories)
# scalar:   A representation of the encoded value as a number. All encoded values
#           are represented as some form of numeric value before being encoded
#           (e.g. for categories, this is the internal index used by the encoder)
# encoding: The bit-string representation of the value
EncoderResult = namedtuple("EncoderResult", ['value', 'scalar','encoding'])

################################################################################
def _isSequence(obj):
  """ Helper function to determine if a function is a list or sequence """
  mType = type(obj)
  return mType is list or mType is tuple

################################################################################
class Encoder(object):
  """
  An encoder takes a value and encodes it with a partial sparse representation
  of bits.  The Encoder superclass implements
  - encode(input) - returns a numpy array encoding the input; syntactic sugar
    on top of encodeIntoArray. If pprint, prints the encoding to the terminal
  - pprintHeader() -- prints a header describing the encoding to the terminal
  - pprint(array) -- prints an encoding to the terminal

  Methods/properties that must be implemented by subclasses
  - getDecoderOutputFieldTypes() -- must be implemented by leaf encoders; returns
    [fieldmeta.FieldMetaType.XXXXX] (e.g., [FieldMetaType.float])
  - getWidth() -- returns the output width, in bits
  - encodeIntoArray(input, output) -- encodes input and puts the encoded value
    into the numpy output array, which is a 1-D array of length returned
    by getWidth()
  - getDescription() -- returns a list of (name, offset) pairs describing the
    encoded output


  """

  ############################################################################
  def __init__(self):
    pass


  ############################################################################
  def getWidth(self):
    raise Exception("getWidth must be implemented by all subclasses")

  ############################################################################
  def isDelta(self):
    #A function that returns true if the underlying encoder works on deltas
    return False

  ############################################################################
  def encodeIntoArray(self, input, output):
    raise Exception("encodeIntoArray must be implemented by all subclasses")

  ############################################################################
  def setLearning(self, learningEnabled):
    if hasattr(self,"_learningEnabled"):
      self._learningEnabled = learningEnabled

  ############################################################################
  def setFieldStats(self,fieldName,fieldStatistics ):
    """ This method is called by the model to set the statistics like min and
    max for the underlying encoders if this information is available.
    
    Parameters:
      
      fieldName: name of the field this encoder is encoding, provided by
          multiencoder

      fieldStatistics: dictionary of dictionaries with the first level being
          the fieldname and the second index the statistic ie:
          fieldStatistics['pounds']['min']

    """
    pass
  ############################################################################
  def encode(self, input):
    output = numpy.zeros((self.getWidth(),), dtype=defaultDtype)
    self.encodeIntoArray(input, output)
    return output

  ############################################################################
  def getScalarNames(self, parentFieldName=''):
    """ Return the field names for each of the scalar values returned by
    getScalars.

    Parameters:
    ------------------------------------------------------------------------
    parentFieldName:  The name of the encoder which is our parent. This name is
                  prefixed to each of the field names within this encoder to
                  form the keys of the dict() in the retval.

    retval:       array of field names


    """

    names = []

    if self.encoders is not None:
      for (name, encoder, offset) in self.encoders:
        subNames = encoder.getScalarNames(parentFieldName=name)
        if parentFieldName != '':
          subNames = ['%s.%s' % (parentFieldName, name) for name in subNames]
        names.extend(subNames)
    else:
      if parentFieldName != '':
        names.append(parentFieldName)
      else:
        names.append(self.name)

    return names


  ############################################################################
  def getDecoderOutputFieldTypes(self):
    """ Returns a sequence of field types corresponding to the elements in the
    decoded output field array.  The types are defined by
    fieldmeta.FieldMetaType
    """
    if hasattr(self, '_flattenedFieldTypeList') and \
          self._flattenedFieldTypeList is not None:
      return self._flattenedFieldTypeList

    fieldTypes = []

    # NOTE: we take care of the composites, but leaf encoders must override
    #       this method and return a list of one fieldmeta.FieldMetaType.XXXX
    #       element corresponding to the encoder's decoder output field type
    for (name, encoder, offset) in self.encoders:
      subTypes = encoder.getDecoderOutputFieldTypes()
      fieldTypes.extend(subTypes)

    self._flattenedFieldTypeList = fieldTypes
    return fieldTypes


  ############################################################################
  #setting this to true freezes the state of the encoder
  #This is separate from the learning state which affects changing parameters.
  def setStateLock(self,lock):
    pass

  ############################################################################
  def _getInputValue(self, obj, fieldname):
    """Gets the value of a given field from the input record"""
    if isinstance(obj, dict):
      return obj[fieldname]
    else:
      return getattr(obj, fieldname)

  ############################################################################
  def getEncoderList(self):
    """ Returns a reference to each sub-encoder in this encoder. They are
    returned in the same order as they are for getScalarNames and getScalars
    """
    if hasattr(self, '_flattenedEncoderList') and \
        self._flattenedEncoderList is not None:

      return self._flattenedEncoderList

    encoders = []

    if self.encoders is not None:
      for (name, encoder, offset) in self.encoders:
        subEncoders = encoder.getEncoderList()
        encoders.extend(subEncoders)
    else:
      encoders.append(self)

    self._flattenedEncoderList = encoders
    return encoders


  ############################################################################
  def getScalars(self, input):
    """ Returns a numpy array containing the sub-field scalar value(s) for
    each sub-field of the input. To get the associated field names for each of
    the scalar values, call getScalarNames().

    For a simple scalar encoder, the scalar value is simply the input unmodified.
    For category encoders, it is the scalar representing the category string
    that is passed in. For the datetime encoder, the scalar value is the
    the number of seconds since epoch.

    The intent of the scalar representation of a sub-field is to provide a
    baseline for measuring error differences. You can compare the scalar value
    of the input with the scalar value returned from topDownCompute() on a
    top-down representation to evaluate prediction accuracy, for example.

    Parameters:
    ------------------------------------------------------------------------
    input:        The data from the source. This is typically a object with
                   members.
    retval:       array of scalar values


    """

    retVals = numpy.array([])

    if self.encoders is not None:
      for (name, encoder, offset) in self.encoders:
        values = encoder.getScalars(self._getInputValue(input, name))
        retVals = numpy.hstack((retVals, values))
    else:
      retVals = numpy.hstack((retVals, input))

    return retVals


  ############################################################################
  def getEncodedValues(self, input):
    """Returns the input in the same format as is returned by topDownCompute().
    For most encoder types, this is the same as the input data.
    For instance, for scalar and category types, this corresponds to the numeric
    and string values, respectively, from the inputs. For datetime encoders, this
    returns the list of scalars for each of the sub-fields (timeOfDay, dayOfWeek, etc.)

    This method is essentially the same as getScalars() except that it returns
    strings


    Parameters:
    -----------------------------------------------------------------------
    input :               The input data in the format it is recieved from the
                          data source

    Returns:              A list of values, in the same format and in the same order
                          as they are returned by topDownCompute.
    """

    retVals = []

    if self.encoders is not None:
      for(name, encoders, offset) in self.encoders:
        values = encoders.getEncodedValues(self._getInputValue(input, name))

        if _isSequence(values):
          retVals.extend(values)
        else:
          retVals.append(values)
    else:
      if _isSequence(input):
        retVals.extend(input)
      else:
        retVals.append(input)

    return tuple(retVals)

  ############################################################################
  def getBucketIndices(self, input):
    """ Returns an array containing the sub-field bucket indices for
    each sub-field of the input. To get the associated field names for each of
    the buckets, call getScalarNames().


    Parameters:
    ------------------------------------------------------------------------
    input:        The data from the source. This is typically a object with
                   members.
    retval:       array of bucket indices


    """

    retVals = []

    if self.encoders is not None:
      for (name, encoder, offset) in self.encoders:
        values = encoder.getBucketIndices(self._getInputValue(input, name))
        retVals.extend(values)
    else:
      assert False, "Should be implemented in base classes that are not " \
        "containers for other encoders"

    return retVals


  ############################################################################
  def scalarsToStr(self, scalarValues, scalarNames=None):
    """ Return a pretty print string representing the return values from
    getScalars and getScalarNames()
    """

    if scalarNames is None:
      scalarNames = self.getScalarNames()

    desc = ''
    for (name, value) in zip(scalarNames, scalarValues):
      if len(desc) > 0:
        desc += ", %s:%.2f" % (name, value)
      else:
        desc += "%s:%.2f" % (name, value)

    return desc



  ############################################################################
  def getDescription(self):
    """ This returns a list of tuples, each containing (name, offset).
    The 'name' is a string description of each sub-field, and offset is the bit
    offset of the sub-field for that encoder.

    For now, only the 'multi' and 'date' encoders have multiple (name, offset)
    pairs. All other encoders have a single pair, where the offset is 0.
    """
    raise Exception("getDescription must be implemented by all subclasses")


  ############################################################################
  def getFieldDescription(self, fieldName):
    """ Return the offset and length of a given field within the encoded
    output.

    Parameters:
    ----------------------------------------------------
    fieldName:      Name of the field
    retval:         (offset, width)
                    offset and width of the field within the encoded output

    """

    # Find which field it's in
    description = self.getDescription() + [("end", self.getWidth())]
    for i in xrange(len(description)):
      (name, offset) = description[i]
      if (name == fieldName):
        break

    if i >= len(description)-1:
      raise RuntimeError("Field name %s not found in this encoder" % fieldName)

    # Return the offset and width
    return (offset, description[i+1][1] - offset)


  ############################################################################
  def encodedBitDescription(self, bitOffset, formatted=False):
    """ Return a description of the given bit in the encoded output.
    This will include the field name and the offset within the field.

    Parameters:
    ----------------------------------------------------
    bitOffset:      Offset of the bit to get the description of
    formatted:      If True, the bitOffset is w.r.t. formatted output,
                    which includes separators
    retval:         (fieldName, offsetWithinField)
    """

    # Find which field it's in
    (prevFieldName, prevFieldOffset) = (None, None)
    description = self.getDescription()
    for i in xrange(len(description)):
      (name, offset) = description[i]
      if formatted:
        offset = offset + i
        if bitOffset == offset-1:
          prevFieldName = "separator"
          prevFieldOffset = bitOffset
          break

      if bitOffset < offset:
        break
      (prevFieldName, prevFieldOffset) = (name, offset)

    # Return the field name and offset within the field
    # return (fieldName, bitOffset - fieldOffset)
    width = self.getDisplayWidth() if formatted else self.getWidth()

    if prevFieldOffset is None or bitOffset > self.getWidth():
      raise IndexError("Bit is outside of allowable range: [0 - %d]" % width)

    return (prevFieldName, bitOffset - prevFieldOffset)



  ############################################################################
  def pprintHeader(self, prefix=""):
    """ Pretty-print a header that labels the sub-fields of the encoded
    output. This can be used in conjuction with pprint.
    """
    print prefix,
    description = self.getDescription() + [("end", self.getWidth())]
    for i in xrange(len(description) - 1):
      name = description[i][0]
      width = description[i+1][1] - description[i][1]
      formatStr = "%%-%ds |" % width
      if len(name) > width:
        pname = name[0:width]
      else:
        pname = name
      print formatStr % pname,
    print
    print prefix, "-" * (self.getWidth() + (len(description) - 1)*3 - 1)

  ############################################################################
  def pprint(self, output, prefix=""):
    """ Pretty-print the encoded output using ascii art.
    """
    print prefix,
    description = self.getDescription() + [("end", self.getWidth())]
    for i in xrange(len(description) - 1):
      offset = description[i][1]
      nextoffset = description[i+1][1]
      print "%s |" % bitsToString(output[offset:nextoffset]),
    print


  ############################################################################
  def decode(self, encoded, parentFieldName=''):
    """ Takes an encoded output and does its best to work backwards and generate
    the input that would have generated it.

    In cases where the encoded output contains more ON bits than an input
    would have generated, this routine will return one or more ranges of inputs
    which, if their encoded outputs were ORed together, would produce the
    target output. This behavior makes this method suitable for doing things
    like generating a description of a learned coincidence in the SP, which
    in many cases might be a union of one or more inputs.

    If instead, you want to figure the *most likely* single input scalar value
    that would have generated a specific encoded output, use the topDownCompute()
    method.

    If you want to pretty print the return value from this method, use the
    decodedToStr() method.

    Parameters:
    ------------------------------------------------------------------------
    encoded:      The encoded output that you want decode
    parentFieldName:  The name of the encoder which is our parent. This name is
                  prefixed to each of the field names within this encoder to
                  form the keys of the dict() in the retval.

    retval:       (fieldsDict, fieldOrder)
                  fieldsDict is a dict() where the keys represent field names
                  (only 1 if this is a simple encoder, > 1 if this is a multi
                  or date encoder) and the values are the result of decoding each
                  field. If there are  no bits in encoded that would have been
                  generated by a field, it won't be present in the dict. The
                  key of each entry in the dict is formed by joining the passed in
                  parentFieldName with the child encoder name using a '.'.

                  Each 'value' in fieldsDict consists of (ranges, desc), where
                  ranges is a list of one or more (minVal, maxVal) ranges of
                  input that would generate bits in the encoded output and 'desc'
                  is a pretty print description of the ranges. For encoders like
                  the category encoder, the 'desc' will contain the category
                  names that correspond to the scalar values included in the
                  ranges.

                  The fieldOrder is a list of the keys from fieldsDict, in the
                  same order as the fields appear in the encoded output.
                  # TODO: when we switch to Python 2.7 or 3.x, use OrderedDict

    Example retvals for a scalar encoder:
     {'amount':  ( [[1,3], [7,10]], '1-3, 7-10' )}
     {'amount':  ( [[2.5,2.5]],     '2.5'       )}

    Example retval for a category encoder:
     {'country': ( [[1,1], [5,6]], 'US, GB, ES' )}

    Example retval for a multi encoder:
     {'amount':  ( [[2.5,2.5]],     '2.5'       ),
      'country': ( [[1,1], [5,6]],  'US, GB, ES' )}


    """

    fieldsDict = dict()
    fieldsOrder = []

    # What is the effective parent name?
    if parentFieldName == '':
      parentName = self.name
    else:
      parentName = "%s.%s" % (parentFieldName, self.name)

    # Merge decodings of all child encoders together
    for i in xrange(len(self.encoders)):

      # Get the encoder and the encoded output
      (name, encoder, offset) = self.encoders[i]
      if i < len(self.encoders)-1:
        nextOffset = self.encoders[i+1][2]
      else:
        nextOffset = self.width
      fieldOutput = encoded[offset:nextOffset]
      (subFieldsDict, subFieldsOrder) = encoder.decode(fieldOutput,
                                            parentFieldName=parentName)

      fieldsDict.update(subFieldsDict)
      fieldsOrder.extend(subFieldsOrder)


    return (fieldsDict, fieldsOrder)



  ############################################################################
  def decodedToStr(self, decodeResults):
    """ Return a pretty print string representing the return value from
    decode()
    """

    (fieldsDict, fieldsOrder) = decodeResults

    desc = ''
    for fieldName in fieldsOrder:
      (ranges, rangesStr) = fieldsDict[fieldName]
      if len(desc) > 0:
        desc += ", %s:" % (fieldName)
      else:
        desc += "%s:" % (fieldName)

      desc += "[%s]" % (rangesStr)

    return desc


  ############################################################################
  def getBucketValues(self):
    """ Returns a list of items, one for each bucket defined by this encoder.
    Each item is the value assigned to that bucket, this is the same as the
    EncoderResult.value that would be returned by getBucketInfo() for that
    bucket and is in the same format as the input that would be passed to
    encode().

    This call is faster than calling getBucketInfo() on each bucket individually
    if all you need are the bucket values.

    Parameters:
    ----------------------------------------------------------------------
    retval:   list of items, each item representing the bucket value for
                that bucket.
    """
    raise Exception("getBucketValues must be implemented by all subclasses")


  ############################################################################
  def getBucketInfo(self, buckets):
    """ Returns a list of EncoderResult namedtuples describing the inputs for
    each sub-field that correspond to the bucket indices passed in 'buckets'.
    To get the associated field names for each of the values, call getScalarNames().

    Parameters:
    ------------------------------------------------------------------------
    buckets:      The list of bucket indices, one for each sub-field encoder.
                  These bucket indices for example may have been retrieved
                  from the getBucketIndices() call.
    retval:       A list of EncoderResult namedtuples. Each EncoderResult has
                  three attributes:

                  1) value:         This is the value for the sub-field
                                    in a format that is consistent with the type
                                    specified by getDecoderOutputFieldTypes().
                                    Note that this value is not necessarily
                                    numeric.

                  2) scalar:        The scalar representation of value. This
                                    number is consistent with what is returned
                                    by getScalars(). This value is always an
                                    int or float, and can be used for
                                    numeric comparisons

                  3) encoding       This is the encoded bit-array (numpy array)
                                    that represents 'value'. That is, if 'value'
                                    was passed to encode(), an identical
                                    bit-array should be returned

    """


    # ---------------------------------------------------------------------
    # Fall back topdown compute
    if self.encoders is None:
      raise RuntimeError("Must be implemented in sub-class")

    # ---------------------------------------------------------------------
    # Concatenate the results from bucketInfo on each child encoder
    retVals = []
    bucketOffset = 0
    for i in xrange(len(self.encoders)):
      (name, encoder, offset) = self.encoders[i]

      if encoder.encoders is not None:
        nextBucketOffset = bucketOffset + len(encoder.encoders)
      else:
        nextBucketOffset = bucketOffset + 1
      bucketIndices = buckets[bucketOffset:nextBucketOffset]
      values = encoder.getBucketInfo(bucketIndices)

      retVals.extend(values)

      bucketOffset = nextBucketOffset

    return retVals


  ############################################################################
  def topDownCompute(self, encoded):
    """ Returns a list of EncoderResult namedtuples describing the top-down
    best guess inputs for each sub-field given the encoded output. These are the
    values which are most likely to generate the given encoded output.
    To get the associated field names for each of the values, call
    getScalarNames().

    Parameters:
    ------------------------------------------------------------------------
    encoded:      The encoded output. Typically received from the topDown outputs
                    from the spatial pooler just above us.
    retval:       A list of EncoderResult namedtuples. Each EncoderResult has
                  three attributes:

                  1) value:         This is the best-guess value for the sub-field
                                    in a format that is consistent with the type
                                    specified by getDecoderOutputFieldTypes().
                                    Note that this value is not necessarily
                                    numeric.

                  2) scalar:        The scalar representation of this best-guess
                                    value. This number is consistent with what
                                    is returned by getScalars(). This value is
                                    always an int or float, and can be used for
                                    numeric comparisons

                  3) encoding       This is the encoded bit-array (numpy array)
                                    that represents the best-guess value.
                                    That is, if 'value' was passed to
                                    encode(), an identical bit-array should be
                                    returned

    """


    # ---------------------------------------------------------------------
    # Fallback topdown compute
    if self.encoders is None:
      raise RuntimeError("Must be implemented in sub-class")

    # ---------------------------------------------------------------------
    # Concatenate the results from topDownCompute on each child encoder
    retVals = []
    for i in xrange(len(self.encoders)):
      (name, encoder, offset) = self.encoders[i]

      if i < len(self.encoders)-1:
        nextOffset = self.encoders[i+1][2]
      else:
        nextOffset = self.width

      fieldOutput = encoded[offset:nextOffset]
      values = encoder.topDownCompute(fieldOutput)

      if _isSequence(values):
        retVals.extend(values)
      else:
        retVals.append(values)

    return retVals


  ############################################################################
  def closenessScores(self, expValues, actValues, fractional=True):
    """ Compute closeness scores between the expected scalar value(s) and actual
    scalar value(s). The expected scalar values are typically those obtained
    from the getScalars() method. The actual scalar values are typically those
    returned from the topDownCompute() method.

    This method returns one closeness score for each value in expValues (or
    actValues which must be the same length). The closeness score ranges from
    0 to 1.0, 1.0 being a perfect match and 0 being the worst possible match.

    If this encoder is a simple, single field encoder, then it will expect
    just 1 item in each of the expValues and actValues arrays. Multi-encoders
    will expect 1 item per sub-encoder.

    Each encoder type can define it's own metric for closeness. For example,
    a category encoder may return either 1 or 0, if the scalar matches exactly
    or not. A scalar encoder might return a percentage match, etc.

    Parameters:
    ------------------------------------------------------------------------
    expValues:    Array of expected scalar values, typically obtained from the
                    getScalars() method
    actValues:    Array of actual values, typically obtained from topDownCompute()
    retval:       Array of closeness scores, one per item in expValues (or
                    actValues).

    """



    # ---------------------------------------------------------------------
    # Fallback closenss is a percentage match
    if self.encoders is None:
      err = abs(expValues[0] - actValues[0])
      if fractional:
        denom = max(expValues[0], actValues[0])
        if denom == 0:
          denom = 1.0
        closeness = 1.0 - float(err)/denom
        if closeness < 0:
          closeness = 0
      else:
        closeness = err

      return numpy.array([closeness])


    # ---------------------------------------------------------------------
    # Concatenate the results from closeness scores on each child encoder
    scalarIdx = 0
    retVals = numpy.array([])
    for (name, encoder, offset) in self.encoders:
      values = encoder.closenessScores(expValues[scalarIdx:], actValues[scalarIdx:],
                                       fractional=fractional)
      scalarIdx += len(values)
      retVals = numpy.hstack((retVals, values))

    return retVals




  ############################################################################
  def getDisplayWidth(self):
    """Calculate width of display for bits plus blanks between fields.
    """
    width = self.getWidth() + len(self.getDescription()) - 1
    return width

  ############################################################################
  def formatBits(self, inarray, outarray, scale=1, blank=255, leftpad=0):
    """
    Copy one array to another, inserting blanks
    between fields (for display)
    If leftpad is one, then there is a dummy value at element 0
    of the arrays, and we should start our counting from 1 rather than 0
    """
    description = self.getDescription() + [("end", self.getWidth())]

    # copy the data, but put one blank in between each field
    for i in xrange(len(description) - 1):
      start = description[i][1]
      end = description[i+1][1]
      # print "Copying: %s" % inarray[start:end]
      outarray[start+i+leftpad:end+i+leftpad] = inarray[(start+leftpad):(end+leftpad)] * scale
      if end < self.getWidth():
        outarray[end+i+leftpad] = blank

################################################################################
