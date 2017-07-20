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

"""Unit tests for dictutils module."""

import unittest2 as unittest

from nupic.data import dict_utils
from nupic.swarming.utils import rCopy



class TestDictUtils(unittest.TestCase):


  def testRUpdateEmpty(self):
    d = {}

    # Both empty.
    dict_utils.rUpdate(d, {})
    self.assertDictEqual(d, {})

    # Original empty.
    dict_utils.rUpdate(d, {"a": 1})
    self.assertDictEqual(d, {"a": 1})

    # Update empty.
    dict_utils.rUpdate(d, {})
    self.assertDictEqual(d, {"a": 1})


  def testRUpdateBasic(self):
    d = {"a": {"b": 2, "e": 4},
         "c": {"d": 3}}
    dict_utils.rUpdate(d, {"a": {"b": 5}})
    self.assertDictEqual(d, {"a": {"b": 5, "e": 4},
                             "c": {"d": 3}})


  def testRCopyEmpty(self):
    d = {}
    self.assertDictEqual(d, rCopy(d))
    self.assertDictEqual(d, rCopy(d, lambda x: 2* x))


  def testRCopyFlatDict(self):
    d = {"a": 1, "b": 2, "c": 3}
    self.assertDictEqual(d, rCopy(d))

    def f(value, _keys):
      return value * 2
    expected = {"a": 2, "b": 4, "c": 6}
    self.assertDictEqual(expected, rCopy(d, f))


  def testRCopyNestedDict(self):
    d = {"a": {"b": {"c": 1}}}
    self.assertDictEqual(d, rCopy(d))

    def f(value, _keys):
      return value * 2
    expected = {"a": {"b": {"c": 2}}}
    self.assertDictEqual(expected, rCopy(d, f))


  def testRCopyComplexNestedDict(self):
    d = {"a": {"b": {"c": [1, 2, 3]}, "d": "Hello", "e": 17}}
    self.assertDictEqual(d, rCopy(d))

    def f(value, _keys):
      return value * 2
    expected = {"a": {"b": {"c": [1, 2, 3, 1, 2, 3]},
                      "d": "HelloHello", "e": 34}}
    self.assertDictEqual(expected, rCopy(d, f))



if __name__ == "__main__":
  unittest.main()
