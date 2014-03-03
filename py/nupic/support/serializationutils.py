#! /usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
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

'''
A series of functions useful to serializing data beyond json or pickle
'''

import json
import bz2

#########################################################
def pack(pyObject):
  '''
  Serialize and zip a py object

  Using JSON rather than Pickle due to C* mailing list suggestions:
   - JSON is multi-language friendly
   - Unpickling data can lead to arbitrary code execution
  '''
  return bz2.compress(json.dumps(pyObject))


#########################################################
def unpack(packedData):
  '''
  Unzip and de-serialize a python object
  '''
  return json.loads(bz2.decompress(packedData))
  
  
#############################################################################
def sortedJSONDumpS(obj):
  """
  Return a JSON representation of obj with sorted keys on any embedded dicts.
  This insures that the same object will always be represented by the same
  string even if it contains dicts (where the sort order of the keys is
  normally undefined).
  """

  itemStrs = []

  if isinstance(obj, dict):
    items = obj.items()
    items.sort()
    for key, value in items:
      itemStrs.append('%s: %s' % (json.dumps(key), sortedJSONDumpS(value)))
    return '{%s}' % (', '.join(itemStrs))

  elif hasattr(obj, '__iter__'):
    for val in obj:
      itemStrs.append(sortedJSONDumpS(val))
    return '[%s]' % (', '.join(itemStrs))

  else:
    return json.dumps(obj)

