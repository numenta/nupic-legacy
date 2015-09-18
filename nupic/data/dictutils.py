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

import copy


# TODO: Note the functions 'rUpdate' are duplicated in
# the swarming.hypersearch.utils.py module


class DictObj(dict):
  """Dictionary that allows attribute-like access to its elements.
  Attributes are read-only."""

  def __getattr__(self, name):
    if name == '__deepcopy__':
      return super(DictObj, self).__getattribute__("__deepcopy__")
    return self[name]

  def __setstate__(self, state):
    for k, v in state.items():
      self[k] = v


def rUpdate(original, updates):
  """Recursively updates the values in original with the values from updates."""
  # Keep a list of the sub-dictionaries that need to be updated to avoid having
  # to use recursion (which could fail for dictionaries with a lot of nesting.
  dictPairs = [(original, updates)]
  while len(dictPairs) > 0:
    original, updates = dictPairs.pop()
    for k, v in updates.iteritems():
      if k in original and isinstance(original[k], dict) and isinstance(v, dict):
        dictPairs.append((original[k], v))
      else:
        original[k] = v


def rApply(d, f):
  """Recursively applies f to the values in dict d.

  Args:
    d: The dict to recurse over.
    f: A function to apply to values in d that takes the value and a list of
        keys from the root of the dict to the value.
  """
  remainingDicts = [(d, ())]
  while len(remainingDicts) > 0:
    current, prevKeys = remainingDicts.pop()
    for k, v in current.iteritems():
      keys = prevKeys + (k,)
      if isinstance(v, dict):
        remainingDicts.insert(0, (v, keys))
      else:
        f(v, keys)


def find(d, target):
  remainingDicts = [d]
  while len(remainingDicts) > 0:
    current = remainingDicts.pop()
    for k, v in current.iteritems():
      if k == target:
        return v
      if isinstance(v, dict):
        remainingDicts.insert(0, v)
  return None


def get(d, keys):
  for key in keys:
    d = d[key]
  return d


def set(d, keys, value):
  for key in keys[:-1]:
    d = d[key]
  d[keys[-1]] = value


def dictDiffAndReport(da, db):
  """ Compares two python dictionaries at the top level and report differences,
  if any, to stdout

  da:             first dictionary
  db:             second dictionary

  Returns:        The same value as returned by dictDiff() for the given args
  """
  differences = dictDiff(da, db)

  if not differences:
    return differences

  if differences['inAButNotInB']:
    print ">>> inAButNotInB: %s" % differences['inAButNotInB']

  if differences['inBButNotInA']:
    print ">>> inBButNotInA: %s" % differences['inBButNotInA']

  for key in differences['differentValues']:
    print ">>> da[%s] != db[%s]" % (key, key)
    print "da[%s] = %r" % (key, da[key])
    print "db[%s] = %r" % (key, db[key])

  return differences


def dictDiff(da, db):
  """ Compares two python dictionaries at the top level and return differences

  da:             first dictionary
  db:             second dictionary

  Returns:        None if dictionaries test equal; otherwise returns a
                  dictionary as follows:
                  {
                    'inAButNotInB':
                        <sequence of keys that are in da but not in db>
                    'inBButNotInA':
                        <sequence of keys that are in db but not in da>
                    'differentValues':
                        <sequence of keys whose corresponding values differ
                         between da and db>
                  }
  """
  different = False

  resultDict = dict()

  resultDict['inAButNotInB'] = set(da) - set(db)
  if resultDict['inAButNotInB']:
    different = True

  resultDict['inBButNotInA'] = set(db) - set(da)
  if resultDict['inBButNotInA']:
    different = True

  resultDict['differentValues'] = []
  for key in (set(da) - resultDict['inAButNotInB']):
    comparisonResult = da[key] == db[key]
    if isinstance(comparisonResult, bool):
      isEqual = comparisonResult
    else:
      # This handles numpy arrays (but only at the top level)
      isEqual = comparisonResult.all()
    if not isEqual:
      resultDict['differentValues'].append(key)
      different = True

  assert (((resultDict['inAButNotInB'] or resultDict['inBButNotInA'] or
          resultDict['differentValues']) and different) or not different)

  return resultDict if different else None
