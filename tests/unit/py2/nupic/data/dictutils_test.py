#! /usr/bin/env python
# ----------------------------------------------------------------------
#  Copyright (C) 2012 Numenta Inc. All rights reserved.
#
#  The information and source code contained herein is the
#  exclusive property of Numenta Inc. No part of this software
#  may be used, reproduced, stored or distributed in any form,
#  without explicit written authorization from Numenta Inc.
# ----------------------------------------------------------------------

from nupic.data import dictutils
from nupic.support.unittesthelpers.testcasebase import (TestCaseBase,
                                                        TestOptionParser,
                                                        unittest)


class TestDictUtils(TestCaseBase):

  def testRUpdateEmpty(self):
    d = {}

    # Both empty.
    dictutils.rUpdate(d, {})
    self.assertDictEqual(d, {})

    # Original empty.
    dictutils.rUpdate(d, {'a': 1})
    self.assertDictEqual(d, {'a': 1})

    # Update empty.
    dictutils.rUpdate(d, {})
    self.assertDictEqual(d, {'a': 1})

  def testRUpdateBasic(self):
    d = {'a': {'b': 2, 'e': 4},
         'c': {'d': 3}}
    dictutils.rUpdate(d, {'a': {'b': 5}})
    self.assertDictEqual(d, {'a': {'b': 5, 'e': 4},
                             'c': {'d': 3}})

  def testRCopyEmpty(self):
    d = {}
    self.assertDictEqual(d, dictutils.rCopy(d))
    self.assertDictEqual(d, dictutils.rCopy(d, lambda x: 2* x))

  def testRCopyFlatDict(self):
    d = {'a': 1, 'b': 2, 'c': 3}
    self.assertDictEqual(d, dictutils.rCopy(d))
    expected = {'a': 2, 'b': 4, 'c': 6}
    self.assertDictEqual(expected, dictutils.rCopy(d, lambda x: 2*x))

  def testRCopyNestedDict(self):
    d = {'a': {'b': {'c': 1}}}
    self.assertDictEqual(d, dictutils.rCopy(d))
    expected = {'a': {'b': {'c': 2}}}
    self.assertDictEqual(expected, dictutils.rCopy(d, lambda x: 2*x))

  def testRCopyComplexNestedDict(self):
    d = {'a': {'b': {'c': [1, 2, 3]}, 'd': 'Hello', 'e': 17}}
    self.assertDictEqual(d, dictutils.rCopy(d))
    expected = {'a': {'b': {'c': [1, 2, 3, 1, 2, 3]},
                      'd': 'HelloHello', 'e': 34}}
    self.assertDictEqual(expected, dictutils.rCopy(d, lambda x: 2*x))


if __name__ == '__main__':
  parser = TestOptionParser()
  parser.parse_args()

  unittest.main()
