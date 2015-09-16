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
Collection of utilities to process input data
"""

import datetime
import string
# Workaround for this error: 
#  "ImportError: Failed to import _strptime because the import lockis held by 
#     another thread"

# These are the supported timestamp formats to parse. The first is used for
# serializing datetimes. Functions in this file rely on specific formats from
# this tuple so be careful when changing the indices for existing formats.
DATETIME_FORMATS = ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S:%f',
                    '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d',
                    '%m/%d/%Y %H:%M', '%m/%d/%y %H:%M',
                    '%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ',
                    '%Y-%m-%dT%H:%M:%S')



def parseTimestamp(s):
  """Parses a textual datetime format and return a Python datetime object.

  The supported format is: yyyy-mm-dd h:m:s.ms

  The time component is optional
  hours are 00..23 (no AM/PM)
  minutes are 00..59
  seconds are 00..59
  micro-seconds are 000000..999999
  """
  s = s.strip()
  for pattern in DATETIME_FORMATS:
    try:
      return datetime.datetime.strptime(s, pattern)
    except ValueError:
      pass
  raise ValueError('The provided timestamp %s is malformed. The supported '
                   'formats are: [%s]' % (s, ', '.join(DATETIME_FORMATS)))



def serializeTimestamp(t):
  return t.strftime(DATETIME_FORMATS[0])



def serializeTimestampNoMS(t):
  return t.strftime(DATETIME_FORMATS[2])



def parseBool(s):
  l = s.lower()
  if l in ("true", "t", "1"):
    return True
  if l in ("false", "f", "0"):
    return False
  raise Exception("Unable to convert string '%s' to a boolean value" % s)



def floatOrNone(f):
  if f == 'None':
    return None
  return float(f)



def intOrNone(i):
  if i.strip() == 'None' or i.strip() == 'NULL':
    return None
  return int(i)



def escape(s):
  """Escape commas, tabs, newlines and dashes in a string

  Commas are encoded as tabs
  """
  if s is None:
    return ''
  
  assert isinstance(s, basestring), \
        "expected %s but got %s; value=%s" % (basestring, type(s), s)
  s = s.replace('\\', '\\\\')
  s = s.replace('\n', '\\n')
  s = s.replace('\t', '\\t')
  s = s.replace(',', '\t')
  return s



def unescape(s):
  """Unescapes a string that may contain commas, tabs, newlines and dashes

  Commas are decoded from tabs
  """
  assert isinstance(s, basestring)
  s = s.replace('\t', ',')
  s = s.replace('\\,', ',')
  s = s.replace('\\n', '\n')
  s = s.replace('\\\\', '\\')

  return s



def parseSdr(s):
  """Parses a string containing only 0's and 1's and return a Python list object.
  """
  assert isinstance(s, basestring)
  sdr = [int(c) for c in s if c in ("0", "1")]
  if len(sdr) != len(s):
    raise ValueError("The provided string %s is malformed. The string should "
                     "have only 0's and 1's.")

  return sdr



def serializeSdr(sdr):
  """Serialize Python list object containing only 0's and 1's to string.
  """

  return "".join(str(bit) for bit in sdr)



def parseStringList(s):
  """Parse a string of space-separated numbers, returning a Python list."""
  assert isinstance(s, basestring)
  return [int(i) for i in s.split()]



def stripList(listObj):
  """Convert a list of numbers to a string of space-separated numbers."""
  return " ".join(str(i) for i in listObj)
  
