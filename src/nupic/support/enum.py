# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import re
import keyword
import functools

__IDENTIFIER_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
def __isidentifier(s):
  if s in keyword.kwlist:
      return False
  return __IDENTIFIER_PATTERN.match(s) is not None

def Enum(*args, **kwargs):
  """
  Utility function for creating enumerations in python

  Example Usage:
    >> Color = Enum("Red", "Green", "Blue", "Magenta")
    >> print Color.Red
    >> 0
    >> print Color.Green
    >> 1
    >> print Color.Blue
    >> 2
    >> print Color.Magenta
    >> 3
    >> Color.Violet
    >> 'violet'
    >> Color.getLabel(Color.Red)
    >> 'Red'
    >> Color.getLabel(2)
    >> 'Blue'



  """

  def getLabel(cls, val):
    """ Get a string label for the current value of the enum """
    return cls.__labels[val]

  def validate(cls, val):
    """ Returns True if val is a valid value for the enumeration """
    return val in cls.__values

  def getValues(cls):
    """ Returns a list of all the possible values for this enum """
    return list(cls.__values)

  def getLabels(cls):
    """ Returns a list of all possible labels for this enum """
    return list(cls.__labels.values())

  def getValue(cls, label):
    """ Returns value given a label """
    return cls.__labels[label]


  for arg in list(args)+kwargs.keys():
    if type(arg) is not str:
      raise TypeError("Enum arg {0} must be a string".format(arg))

    if not __isidentifier(arg):
      raise ValueError("Invalid enum value '{0}'. "\
                       "'{0}' is not a valid identifier".format(arg))

  #kwargs.update(zip(args, range(len(args))))
  kwargs.update(zip(args, args))
  newType = type("Enum", (object,), kwargs)

  newType.__labels = dict( (v,k) for k,v in kwargs.iteritems())
  newType.__values = set(newType.__labels.keys())
  newType.getLabel = functools.partial(getLabel, newType)
  newType.validate = functools.partial(validate, newType)
  newType.getValues = functools.partial(getValues, newType)
  newType.getLabels = functools.partial(getLabels, newType)
  newType.getValue = functools.partial(getValue, newType)

  return newType

if __name__ == '__main__':

  Color = Enum("Red", "Blue")
  Shape = Enum("Square", "Triangle")
