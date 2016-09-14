# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2016, Numenta, Inc.  Unless you have an agreement
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
import unittest

from nupic.support.group_by import groupby2

""" File to test src/nupic/support/group_by.py  """

class GroupByTest(unittest.TestCase):

  def testOneSequence(self):
    sequence0 = [7, 12, 12, 16]

    identity = lambda x: int(x)

    expectedValues = [(7, [7]),
                      (12, [12, 12]),
                      (16, [16])]
    i = 0
    for data in groupby2(sequence0, identity):
      self.assertEqual(data[0], expectedValues[i][0])
      for j in xrange(1, len(data)):
        temp = list(data[j]) if data[j] else data[j]
        self.assertEqual(temp, expectedValues[i][j])
      i += 1


  def testTwoSequences(self):
    sequence0 = [7, 12, 16]
    sequence1 = [3, 4, 5]

    identity = lambda x: int(x)
    times3 = lambda x: int(3 * x)

    expectedValues = [(7, [7], None),
                      (9, None, [3]),
                      (12, [12], [4]),
                      (15, None, [5]),
                      (16, [16], None)]

    i = 0
    for data in groupby2(sequence0, identity,
                         sequence1, times3):
      self.assertEqual(data[0], expectedValues[i][0])
      for j in xrange(1, len(data)):
        temp = list(data[j]) if data[j] else data[j]
        self.assertEqual(temp, expectedValues[i][j])
      i += 1


  def testThreeSequences(self):
    sequence0 = [7, 12, 16]
    sequence1 = [3, 4, 5]
    sequence2 = [3, 3, 4, 5]

    identity = lambda x: int(x)
    times3 = lambda x: int(3 * x)
    times4 = lambda x: int(4 * x)

    expectedValues = [(7, [7], None, None),
                      (9, None, [3], None),
                      (12, [12], [4], [3, 3]),
                      (15, None, [5], None),
                      (16, [16], None, [4]),
                      (20, None, None, [5])]

    i = 0
    for data in groupby2(sequence0, identity,
                         sequence1, times3,
                         sequence2, times4):
      self.assertEqual(data[0], expectedValues[i][0])
      for j in xrange(1, len(data)):
        temp = list(data[j]) if data[j] else data[j]
        self.assertEqual(temp, expectedValues[i][j])
      i += 1


  def testFourSequences(self):
    sequence0 = [7, 12, 16]
    sequence1 = [3, 4, 5]
    sequence2 = [3, 3, 4, 5]
    sequence3 = [3, 3, 4, 5]

    identity = lambda x: int(x)
    times3 = lambda x: int(3 * x)
    times4 = lambda x: int(4 * x)
    times5 = lambda x: int(5 * x)

    expectedValues = [(7, [7], None, None, None),
                      (9, None, [3], None, None),
                      (12, [12], [4], [3, 3], None),
                      (15, None, [5], None, [3, 3]),
                      (16, [16], None, [4], None),
                      (20, None, None, [5], [4]),
                      (25, None, None, None, [5])]

    i = 0
    for data in groupby2(sequence0, identity,
                         sequence1, times3,
                         sequence2, times4,
                         sequence3, times5):
      self.assertEqual(data[0], expectedValues[i][0])
      for j in xrange(1, len(data)):
        temp = list(data[j]) if data[j] else data[j]
        self.assertEqual(temp, expectedValues[i][j])
      i += 1



  def testFiveSequences(self):
    sequence0 = [7, 12, 16]
    sequence1 = [3, 4, 5]
    sequence2 = [3, 3, 4, 5]
    sequence3 = [3, 3, 4, 5]
    sequence4 = [2, 2, 3]

    identity = lambda x: int(x)
    times3 = lambda x: int(3 * x)
    times4 = lambda x: int(4 * x)
    times5 = lambda x: int(5 * x)
    times6 = lambda x: int(6 * x)

    expectedValues = [(7, [7], None, None, None, None),
                      (9, None, [3], None, None, None),
                      (12, [12], [4], [3, 3], None, [2, 2]),
                      (15, None, [5], None, [3, 3], None),
                      (16, [16], None, [4], None, None),
                      (18, None, None, None, None, [3]),
                      (20, None, None, [5], [4], None),
                      (25, None, None, None, [5], None)]

    i = 0
    for data in groupby2(sequence0, identity,
                         sequence1, times3,
                         sequence2, times4,
                         sequence3, times5,
                         sequence4, times6):
      self.assertEqual(data[0], expectedValues[i][0])
      for j in xrange(1, len(data)):
        temp = list(data[j]) if data[j] else data[j]
        self.assertEqual(temp, expectedValues[i][j])
      i += 1


  def testNone(self):
    sequence0 = None
    sequence1 = [3, 4, 5]
    sequence2 = None
    sequence3 = [3, 3, 4, 5]
    sequence4 = None

    identity = lambda x: int(x)
    times3 = lambda x: int(3 * x)
    times4 = lambda x: int(4 * x)
    times5 = lambda x: int(5 * x)
    times6 = lambda x: int(6 * x)

    expectedValues = [(9, None, [3], None, None, None),
                      (12, None, [4], None, None, None),
                      (15, None, [5], None, [3, 3], None),
                      (20, None, None, None, [4], None),
                      (25, None, None, None, [5], None)]

    i = 0
    for data in groupby2(sequence0, identity,
                         sequence1, times3,
                         sequence2, times4,
                         sequence3, times5,
                         sequence4, times6):
      self.assertEqual(data[0], expectedValues[i][0])
      for j in xrange(1, len(data)):
        temp = list(data[j]) if data[j] else data[j]
        self.assertEqual(temp, expectedValues[i][j])
      i += 1


if __name__ == "__main__":
  unittest.main()
