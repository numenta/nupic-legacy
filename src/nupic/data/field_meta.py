# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013-15, Numenta, Inc.  Unless you have an agreement
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

"""
This module defines the structure of meta-data that describes the field name,
field type, special field attribute, etc. for a field in a dataset.
"""

from collections import namedtuple



FieldMetaInfoBase = namedtuple('FieldMetaInfoBase', ['name', 'type', 'special'])



class FieldMetaInfo(FieldMetaInfoBase):
  """
  This class acts as a container of meta-data for a single field (column) of
  a dataset. Each instance of this class has ``name``, ``type``, and ``special``
  properties.

  Examples:

  1. Access a sub-element from an instance of FieldMetaInfo:

     - ``metainfo.name``
     - ``metainfo.type``
     - ``metainfo.special``

  2. Create a single element of ``FieldMetaInfo`` from a tuple of ``name``,
     ``type``, and ``special``:

     .. code-block:: python

        e = ('pounds', FieldMetaType.float, FieldMetaSpecial.none)
        m = FieldMetaInfo.createFromFileFieldElement(e)

  :param str name: field name
  :param str type: one of the values from FieldMetaType
  :param str special: one of the values from FieldMetaSpecial
  :raises ValueError: if type or special arg values are invalid
  """


  def __init__(self,
               name,
               type,  # pylint: disable=W0622
               special):

    if not FieldMetaType.isValid(type):
      raise ValueError('Unexpected field type %r' % (type,))

    if not FieldMetaSpecial.isValid(special):
      raise ValueError('Unexpected field special attribute %r' % (special,))

    super(FieldMetaInfo, self).__init__(name, type, special)


  @staticmethod
  def createFromFileFieldElement(fieldInfoTuple):
    """
    Creates a :class:`.field_meta.FieldMetaInfo` instance from a tuple containing
    ``name``, ``type``, and ``special``.

    :param fieldInfoTuple: Must contain ``name``, ``type``, and ``special``
    :return: (:class:`~.field_meta.FieldMetaInfo`) instance
    """
    return FieldMetaInfo._make(fieldInfoTuple)


  @classmethod
  def createListFromFileFieldList(cls, fields):
    """
    Creates a FieldMetaInfo list from the a list of tuples. Basically runs
    :meth:`~.field_meta.FieldMetaInfo.createFromFileFieldElement` on each tuple.

    *Example:*

    .. code-block:: python

        # Create a list of FieldMetaInfo instances from a list of File meta-data
        # tuples
        el = [("pounds", FieldMetaType.float, FieldMetaSpecial.none),
              ("price", FieldMetaType.float, FieldMetaSpecial.none),
              ("id", FieldMetaType.string, FieldMetaSpecial.sequence),
              ("date", FieldMetaType.datetime, FieldMetaSpecial.timestamp),
             ]
        ml = FieldMetaInfo.createListFromFileFieldList(el)

    :param fields: a sequence of field attribute tuples conforming to the format
                   of ``name``, ``type``, and ``special``

    :return: A list of :class:`~.field_meta.FieldMetaInfo` elements corresponding
             to the given 'fields' list.
    """
    return [cls.createFromFileFieldElement(f) for f in fields]



class FieldMetaType(object):
  """
  Public values for the field data types. Valid types are:

    - ``string``
    - ``datetime``
    - ``int``
    - ``float``
    - ``bool``
    - ``list``
    - ``sdr``
  """
  string = 'string'
  datetime = 'datetime'
  integer = 'int'
  float = 'float'
  boolean = 'bool'
  list = 'list'
  sdr = 'sdr'

  _ALL = (string, datetime, integer, float, boolean, list, sdr)


  @classmethod
  def isValid(cls, fieldDataType):
    """Check a candidate value whether it's one of the valid field data types

    :param fieldDataType: (string) candidate field data type
    :returns: True if the candidate value is a legitimate field data type value;
              False if not
    """
    return fieldDataType in cls._ALL



class FieldMetaSpecial(object):
  """
  Public values for the "special" field attribute. Valid values are:

    - ``R``: reset
    - ``S``: sequence
    - ``T``: timestamp
    - ``C``: category
    - ``L``: learning
  """
  none = ''
  reset = 'R'
  sequence = 'S'
  timestamp = 'T'
  category = 'C'
  learning = 'L'

  _ALL = (none, reset, sequence, timestamp, category, learning,)


  @classmethod
  def isValid(cls, attr):
    """Check a candidate value whether it's one of the valid attributes

    :param attr: (string) candidate value
    :returns: True if the candidate value is a legitimate "special" field
              attribute; False if not
    """
    return attr in cls._ALL
