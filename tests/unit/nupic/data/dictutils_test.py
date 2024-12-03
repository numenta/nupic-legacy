# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

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
