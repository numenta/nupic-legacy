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

"""JSON encoding and decoding."""

# Pylint gets confused about return types from deserialization.
# pylint: disable=E1103

import json
import sys

NON_OBJECT_TYPES = (type(None), bool, int, float, long, str, unicode)


class Types(object):
  TUPLE = 'py/tuple'
  SET = 'py/set'
  DATETIME = 'datetime/datetime.datetime'
  REPR = 'py/repr'
  OBJECT = 'py/object'
  KEYS = 'py/dict/keys'


def getImportPath(obj):
  cls = obj.__class__
  return '%s.%s' % (cls.__module__, cls.__name__)


def convertDict(obj):
  obj = dict(obj)
  for k, v in obj.items():
    del obj[k]
    if not (isinstance(k, str) or isinstance(k, unicode)):
      k = dumps(k)
      # Keep track of which keys need to be decoded when loading.
      if Types.KEYS not in obj:
        obj[Types.KEYS] = []
      obj[Types.KEYS].append(k)
    obj[k] = convertObjects(v)
  return obj


def restoreKeysPostDecoding(obj):
  if isinstance(obj, dict):
    if Types.KEYS in obj:
      for k in obj[Types.KEYS]:
        v = obj[k]
        del obj[k]
        newKey = loads(k)
        obj[newKey] = v
      del obj[Types.KEYS]
    for k, v in obj.items():
      if isinstance(v, dict):
        obj[k] = restoreKeysPostDecoding(v)
  elif isinstance(obj, list):
    obj = [restoreKeysPostDecoding(item) for item in obj]
  elif isinstance(obj, set):
    obj = set([restoreKeysPostDecoding(item) for item in obj])
  elif isinstance(obj, tuple):
    obj = tuple([restoreKeysPostDecoding(item) for item in obj])
  return obj


def convertObjects(obj):
  if type(obj) in NON_OBJECT_TYPES:
    return obj
  elif isinstance(obj, list):
    return [convertObjects(item) for item in obj]
  elif isinstance(obj, dict):
    return convertDict(obj)
  elif isinstance(obj, tuple):
    return {Types.TUPLE: [convertObjects(item) for item in obj]}
  elif isinstance(obj, set):
    return {Types.SET: [convertObjects(item) for item in obj]}
  else:
    if hasattr(obj, '__getstate__'):
      state = obj.__getstate__()
    elif hasattr(obj, '__slots__'):
      values = map(lambda x: getattr(obj, x), obj.__slots__)
      state = dict(zip(obj.__slots__, values))
    elif hasattr(obj, '__dict__'):
      state = obj.__dict__
    else:
      if not hasattr(obj, '__class__'):
        raise TypeError('Cannot encode object: %s' % repr(obj))
      state = {Types.REPR: repr(obj)}
    state[Types.OBJECT] = getImportPath(obj)
    return convertObjects(state)


def objectDecoderHook(obj):
  obj = restoreKeysPostDecoding(obj)
  if isinstance(obj, dict):
    if Types.TUPLE in obj:
      return tuple(obj[Types.TUPLE])
    elif Types.SET in obj:
      return set(obj[Types.SET])
    elif Types.DATETIME in obj:
      return eval(obj[Types.DATETIME])
    elif Types.REPR in obj:
      module, name = obj[Types.OBJECT].rsplit('.', 1)
      return eval(obj[Types.REPR], {module: __import__(module)})
    elif Types.OBJECT in obj:
      module, name = obj[Types.OBJECT].rsplit('.', 1)
      __import__(module)
      cls = getattr(sys.modules[module], name)
      try:
        if hasattr(cls, '__new__'):
          instance = cls.__new__(cls)
        else:
          instance = object.__new__(cls)
      except TypeError:
        try:
          instance = cls()
        except TypeError:
          raise TypeError('Old style class cannot be instantiated: %s' %
                          obj[Types.OBJECT])
      attrs = obj
      del attrs[Types.OBJECT]
      if hasattr(instance, '__setstate__'):
        instance.__setstate__(attrs)
      else:
        for k, v in attrs.iteritems():
          setattr(instance, k, v)
      return instance
  return obj


def clean(s):
  """Removes trailing whitespace on each line."""
  lines = [l.rstrip() for l in s.split('\n')]
  return '\n'.join(lines)


def dumps(obj, **kwargs):
  return clean(json.dumps(convertObjects(obj), **kwargs))


def dump(obj, f, **kwargs):
  f.write(dumps(obj, **kwargs))


def loads(s, **kwargs):
  return restoreKeysPostDecoding(
      json.loads(s, object_hook=objectDecoderHook, **kwargs))


def load(f, **kwargs):
  return restoreKeysPostDecoding(
      json.load(f, object_hook=objectDecoderHook, **kwargs))
