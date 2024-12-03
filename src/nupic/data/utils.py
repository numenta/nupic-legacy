# Copyright 2013-2015 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""
Collection of utilities to process input data
"""

import datetime
import string
# Workaround for this error:
#  "ImportError: Failed to import _strptime because the import lockis held by
#     another thread"

DATETIME_FORMATS = ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S:%f',
                    '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d',
                    '%m/%d/%Y %H:%M', '%m/%d/%y %H:%M',
                    '%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ',
                    '%Y-%m-%dT%H:%M:%S')
"""
These are the supported timestamp formats to parse. The first is the format used
by NuPIC when serializing datetimes.
"""



def parseTimestamp(s):
  """
  Parses a textual datetime format and return a Python datetime object.

  The supported format is: ``yyyy-mm-dd h:m:s.ms``

  The time component is optional.

  - hours are 00..23 (no AM/PM)
  - minutes are 00..59
  - seconds are 00..59
  - micro-seconds are 000000..999999

  :param s: (string) input time text
  :return: (datetime.datetime)
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
  """
  Turns a datetime object into a string.

  :param t: (datetime.datetime)
  :return: (string) in default format (see 
           :const:`~nupic.data.utils.DATETIME_FORMATS` [0])
  """
  return t.strftime(DATETIME_FORMATS[0])



def serializeTimestampNoMS(t):
  """
  Turns a datetime object into a string ignoring milliseconds.

  :param t: (datetime.datetime)
  :return: (string) in default format (see 
           :const:`~nupic.data.utils.DATETIME_FORMATS` [2])
  """
  return t.strftime(DATETIME_FORMATS[2])



def parseBool(s):
  """
  String to boolean

  :param s: (string)
  :return: (bool)
  """
  l = s.lower()
  if l in ("true", "t", "1"):
    return True
  if l in ("false", "f", "0"):
    return False
  raise Exception("Unable to convert string '%s' to a boolean value" % s)



def floatOrNone(f):
  """
  Tries to convert input to a float input or returns ``None``.

  :param f: (object) thing to convert to a float
  :return: (float or ``None``)
  """
  if f == 'None':
    return None
  return float(f)



def intOrNone(i):
  """
  Tries to convert input to a int input or returns ``None``.

  :param f: (object) thing to convert to a int
  :return: (int or ``None``)
  """
  if i.strip() == 'None' or i.strip() == 'NULL':
    return None
  return int(i)



def escape(s):
  """
  Escape commas, tabs, newlines and dashes in a string

  Commas are encoded as tabs.

  :param s: (string) to escape
  :returns: (string) escaped string
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
  """
  Unescapes a string that may contain commas, tabs, newlines and dashes

  Commas are decoded from tabs.

  :param s: (string) to unescape
  :returns: (string) unescaped string
  """
  assert isinstance(s, basestring)
  s = s.replace('\t', ',')
  s = s.replace('\\,', ',')
  s = s.replace('\\n', '\n')
  s = s.replace('\\\\', '\\')

  return s



def parseSdr(s):
  """
  Parses a string containing only 0's and 1's and return a Python list object.

  :param s: (string) string to parse
  :returns: (list) SDR out
  """
  assert isinstance(s, basestring)
  sdr = [int(c) for c in s if c in ("0", "1")]
  if len(sdr) != len(s):
    raise ValueError("The provided string %s is malformed. The string should "
                     "have only 0's and 1's.")

  return sdr



def serializeSdr(sdr):
  """
  Serialize Python list object containing only 0's and 1's to string.

  :param sdr: (list) binary
  :returns: (string) SDR out
  """

  return "".join(str(bit) for bit in sdr)



def parseStringList(s):
  """
  Parse a string of space-separated numbers, returning a Python list.

  :param s: (string) to parse
  :returns: (list) binary SDR
  """
  assert isinstance(s, basestring)
  return [int(i) for i in s.split()]



def stripList(listObj):
  """
  Convert a list of numbers to a string of space-separated values.

  :param listObj: (list) to convert
  :returns: (string) of space-separated values
  """
  return " ".join(str(i) for i in listObj)

