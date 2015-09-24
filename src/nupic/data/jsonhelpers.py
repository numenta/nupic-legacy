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

# This script is a wrapper for JSON primitives, such as validation.
# Using routines of this module permits us to replace the underlying
# implementation with a better one without disrupting client code.
#
# In particular, at the time of this writing, there weren't really great
# json validation packages available for python.  We initially settled
# on validictory, but it has a number of shortcomings, such as:
#   * format error diagnostic message isn't always helpful for diagnosis
#   * doesn't support references
#   * doesn't support application of defaults
#   * doesn't support dependencies
#
# TODO: offer a combined json parsing/validation function that applies
#       defaults from the schema
# TODO: duplicate of 'validate', 'ValidationError', 'loadJSONValueFromFile'
# in swarming.hypersearch.utils -- will want to remove that later

import json
import math
import os

import validictory


class ValidationError(validictory.ValidationError):
  pass


class NaNInvalidator(validictory.SchemaValidator):
  """ validictory.SchemaValidator subclass to not accept NaN values as numbers.

  Usage:

      validate(value, schemaDict, validator_cls=NaNInvalidator)

  """
  def validate_type_number(self, val):
    return not math.isnan(val) \
      and super(NaNInvalidator, self).validate_type_number(val)



def validate(value, **kwds):
  """ Validate a python value against json schema:
  validate(value, schemaPath)
  validate(value, schemaDict)

  value:          python object to validate against the schema

  The json schema may be specified either as a path of the file containing
  the json schema or as a python dictionary using one of the
  following keywords as arguments:
    schemaPath:     Path of file containing the json schema object.
    schemaDict:     Python dictionary containing the json schema object

  Returns: nothing

  Raises:
          ValidationError when value fails json validation
  """

  assert len(kwds.keys()) >= 1
  assert 'schemaPath' in kwds or 'schemaDict' in kwds

  schemaDict = None
  if 'schemaPath' in kwds:
    schemaPath = kwds.pop('schemaPath')
    schemaDict = loadJsonValueFromFile(schemaPath)
  elif 'schemaDict' in kwds:
    schemaDict = kwds.pop('schemaDict')

  try:
    validictory.validate(value, schemaDict, **kwds)
  except validictory.ValidationError as e:
    raise ValidationError(e)



def loadJsonValueFromFile(inputFilePath):
  """ Loads a json value from a file and converts it to the corresponding python
  object.

  inputFilePath:
                  Path of the json file;

  Returns:
                  python value that represents the loaded json value

  """
  with open(inputFilePath) as fileObj:
    value = json.load(fileObj)

  return value



def test():
  """
  """
  import sys

  schemaDict = {
    "description":"JSON schema for jsonhelpers.py test code",
    "type":"object",
    "additionalProperties":False,
    "properties":{
      "myBool":{
        "description":"Some boolean property",
        "required":True,
        "type":"boolean"
      }
    }
  }

  d = {
    'myBool': False
  }

  print "Validating schemaDict method in positive test..."
  validate(d, schemaDict=schemaDict)
  print "ok\n"

  print "Validating schemaDict method in negative test..."
  try:
    validate({}, schemaDict=schemaDict)
  except ValidationError:
    print "ok\n"
  else:
    print "FAILED\n"
    sys.exit(1)


  schemaPath = os.path.join(os.path.dirname(__file__), "testSchema.json")
  print "Validating schemaPath method in positive test using %s..." % \
            (os.path.abspath(schemaPath),)
  validate(d, schemaPath=schemaPath)
  print "ok\n"

  print "Validating schemaPath method in negative test using %s..." % \
            (os.path.abspath(schemaPath),)
  try:
    validate({}, schemaPath=schemaPath)
  except ValidationError:
    print "ok\n"
  else:
    print "FAILED\n"
    sys.exit(1)



  return



if __name__ == "__main__":
  test()
