# Copyright 2014 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import unittest

from nupic.algorithms.monitor_mixin.trace import IndicesTrace



class IndicesTraceTest(unittest.TestCase):


  def setUp(self):
    self.trace = IndicesTrace(self, "active cells")
    self.trace.data.append(set([1, 2, 3]))
    self.trace.data.append(set([4, 5]))
    self.trace.data.append(set([6]))
    self.trace.data.append(set([]))


  def testMakeCountsTrace(self):
    countsTrace = self.trace.makeCountsTrace()
    self.assertEqual(countsTrace.title, "# active cells")
    self.assertEqual(countsTrace.data, [3, 2, 1, 0])


  def testMakeCumCountsTrace(self):
    countsTrace = self.trace.makeCumCountsTrace()
    self.assertEqual(countsTrace.title, "# (cumulative) active cells")
    self.assertEqual(countsTrace.data, [3, 5, 6, 6])



if __name__ == '__main__':
  unittest.main()
