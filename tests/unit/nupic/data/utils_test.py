# Copyright 2013-2015 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""Unit tests for nupic.data.utils."""

from datetime import datetime

from nupic.data import utils
from nupic.support.unittesthelpers.testcasebase import (TestCaseBase,
                                                        unittest)


class UtilsTest(TestCaseBase):
  """Utility unit tests."""

  def testParseTimestamp(self):
    expectedResults = (
        ('2011-09-08T05:30:32.920000Z', datetime(2011, 9, 8, 5, 30, 32, 920000)),
        ('2011-09-08T05:30:32Z', datetime(2011, 9, 8, 5, 30, 32, 0)),
        ('2011-09-08T05:30:32', datetime(2011, 9, 8, 5, 30, 32, 0)),
        ('2011-09-08 05:30:32:920000', datetime(2011, 9, 8, 5, 30, 32, 920000)),
        ('2011-09-08 05:30:32.920000', datetime(2011, 9, 8, 5, 30, 32, 920000)),
        ('2011-09-08 5:30:32:92', datetime(2011, 9, 8, 5, 30, 32, 920000)),
        ('2011-09-08 5:30:32', datetime(2011, 9, 8, 5, 30, 32)),
        ('2011-09-08 5:30', datetime(2011, 9, 8, 5, 30)),
        ('2011-09-08', datetime(2011, 9, 8)))
    for timestamp, dt in expectedResults:
      self.assertEqual(utils.parseTimestamp(timestamp), dt)

  def testSerializeTimestamp(self):
    self.assertEqual(
        utils.serializeTimestamp(datetime(2011, 9, 8, 5, 30, 32, 920000)),
        '2011-09-08 05:30:32.920000')

  def testSerializeTimestampNoMS(self):
    self.assertEqual(
        utils.serializeTimestampNoMS(datetime(2011, 9, 8, 5, 30, 32, 920000)),
        '2011-09-08 05:30:32')

  def testParseSdr(self):
    self.assertSequenceEqual(utils.parseSdr("000101000"), [0, 0, 0, 1, 0, 1, 0, 0, 0])

  def testSerializeSdr(self):
    self.assertSequenceEqual(utils.serializeSdr([0, 0, 0, 1, 0, 1, 0, 0, 0]), "000101000")

  def testParseStringList(self):
    stringLists = ["", "0", "0 1"]
    expectedResults = [[], [0], [0, 1]]
    for s, r in zip(stringLists, expectedResults):
      self.assertSequenceEqual(r, utils.parseStringList(s))

  def testStripList(self):
    lists = [[], [0], [0, 1]]
    expectedResults = ["", "0", "0 1"]
    for listObj, r in zip(lists, expectedResults):
      self.assertSequenceEqual(r, utils.stripList(listObj))


if __name__ == '__main__':
  unittest.main()
