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

from nupic.encoders.base import Encoder
from nupic.encoders import (ScalarEncoder,
                            AdaptiveScalarEncoder,
                            DateEncoder,LogEncoder,
                            CategoryEncoder,
                            SDRCategoryEncoder,
                            DeltaEncoder,
                            ScalarSpaceEncoder,
                            PassThroughEncoder,
                            SparsePassThroughEncoder,
                            CoordinateEncoder,
                            GeospatialCoordinateEncoder,
                            RandomDistributedScalarEncoder)


# Map class to Cap'n Proto schema union attribute
_CLASS_ATTR_MAP = {
  ScalarEncoder: "scalarEncoder",
  AdaptiveScalarEncoder: "adaptiveScalarEncoder",
  DateEncoder: "dateEncoder",
  LogEncoder: "logEncoder",
  CategoryEncoder: "categoryEncoder",
  CoordinateEncoder: "coordinateEncoder",
  SDRCategoryEncoder: "sdrCategoryEncoder",
  DeltaEncoder: "deltaEncoder",
  PassThroughEncoder: "passThroughEncoder",
  SparsePassThroughEncoder: "sparsePassThroughEncoder",
  GeospatialCoordinateEncoder: "geospatialCoordinateEncoder",
  ScalarSpaceEncoder: "scalarSpaceEncoder",
  RandomDistributedScalarEncoder: "randomDistributedScalarEncoder"
}

# Invert for fast lookup in MultiEncoder.read()
_ATTR_CLASS_MAP = {value: key for key, value in _CLASS_ATTR_MAP.items()}


class MultiEncoder(Encoder):
  """
  A MultiEncoder encodes a dictionary or object with multiple components. A
  MultiEncoder contains a number of sub-encoders, each of which encodes a
  separate component.

  :param encoderDefinitions: a dict of dicts, mapping field names to the field
         params dict. Sent directly to :meth:`.addMultipleEncoders`.
  """

  def __init__(self, encoderDefinitions=None):
    self.width = 0
    self.encoders = []
    self.description = []
    self.name = ''
    if encoderDefinitions is not None:
      self.addMultipleEncoders(encoderDefinitions)


  def setFieldStats(self, fieldName, fieldStatistics ):
    for (name, encoder, offset) in self.encoders:
      encoder.setFieldStats(name, fieldStatistics)


  def addEncoder(self, name, encoder):
    """
    Adds one encoder.

    :param name: (string) name of encoder, should be unique
    :param encoder: (:class:`.Encoder`) the encoder to add
    """
    self.encoders.append((name, encoder, self.width))
    for d in encoder.getDescription():
      self.description.append((d[0], d[1] + self.width))
    self.width += encoder.getWidth()

    self._flattenedEncoderList = None
    self._flattenedFieldTypeList = None


  def encodeIntoArray(self, obj, output):
    for name, encoder, offset in self.encoders:
        encoder.encodeIntoArray(self._getInputValue(obj, name), output[offset:])


  def getDescription(self):
    return self.description


  def getWidth(self):
    """Represents the sum of the widths of each fields encoding."""
    return self.width

  def setLearning(self,learningEnabled):
    encoders = self.getEncoderList()
    for encoder in encoders:
      encoder.setLearning(learningEnabled)
    return


  def encodeField(self, fieldName, value):
    for name, encoder, offset in self.encoders:
      if name == fieldName:
        return encoder.encode(value)


  def encodeEachField(self, inputRecord):
    encodings = []
    for name, encoder, offset in self.encoders:
      encodings.append(encoder.encode(getattr(inputRecord, name)))
    return encodings


  def addMultipleEncoders(self, fieldEncodings):
    """

    :param fieldEncodings: dict of dicts, mapping field names to the field
           params dict.

           Each field params dict has the following keys:

           1. ``fieldname``: data field name
           2. ``type`` an encoder type
           3. All other keys are encoder parameters

    For example,

    .. code-block:: python

      fieldEncodings={
          'dateTime': dict(fieldname='dateTime', type='DateEncoder',
                           timeOfDay=(5,5)),
          'attendeeCount': dict(fieldname='attendeeCount', type='ScalarEncoder',
                                name='attendeeCount', minval=0, maxval=250,
                                clipInput=True, w=5, resolution=10),
          'consumption': dict(fieldname='consumption',type='ScalarEncoder',
                              name='consumption', minval=0,maxval=110,
                              clipInput=True, w=5, resolution=5),
      }

    would yield a vector with a part encoded by the :class:`.DateEncoder`, and
    to parts seperately taken care of by the :class:`.ScalarEncoder` with the
    specified parameters. The three seperate encodings are then merged together
    to the final vector, in such a way that they are always at the same location
    within the vector.
    """

    # Sort the encoders so that they end up in a controlled order
    encoderList = sorted(fieldEncodings.items())
    for key, fieldParams in encoderList:
      if ':' not in key and fieldParams is not None:
        fieldParams = fieldParams.copy()
        fieldName   = fieldParams.pop('fieldname')
        encoderName = fieldParams.pop('type')
        try:
          self.addEncoder(fieldName, eval(encoderName)(**fieldParams))
        except TypeError, e:
          print ("#### Error in constructing %s encoder. Possibly missing "
                "some required constructor parameters. Parameters "
                "that were provided are: %s" %  (encoderName, fieldParams))
          raise


  @classmethod
  def read(cls, proto):
    encoder = object.__new__(cls)

    encoder.encoders = [None] * len(proto.encoders)

    encoder.width = 0

    for index, encoderProto in enumerate(proto.encoders):
      # Identify which attr is set in union
      encoderType = encoderProto.which()

      encoderDetails = getattr(encoderProto, encoderType)
      encoder.encoders[index] = (
        encoderProto.name,
        # Call class.read() where class is determined by _ATTR_CLASS_MAP
        _ATTR_CLASS_MAP.get(encoderType).read(encoderDetails),
        encoderProto.offset
      )

      encoder.width += encoder.encoders[index][1].getWidth()

    # Derive description from encoder list
    encoder.description = [(enc[1].name, enc[2]) for enc in encoder.encoders]
    encoder.name = proto.name

    return encoder


  def write(self, proto):

    proto.init("encoders", len(self.encoders))

    for index, (name, encoder, offset) in enumerate(self.encoders):
      encoderProto = proto.encoders[index]
      encoderType = _CLASS_ATTR_MAP.get(encoder.__class__)
      encoderProto.init(encoderType)
      encoderDetails = getattr(encoderProto, encoderType)
      encoder.write(encoderDetails)
      encoderProto.name = name
      encoderProto.offset = offset

    proto.name = self.name
