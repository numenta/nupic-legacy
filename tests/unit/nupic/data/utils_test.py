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
