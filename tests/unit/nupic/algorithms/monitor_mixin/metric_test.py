# Copyright 2014 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import unittest
from nupic.algorithms.monitor_mixin.metric import Metric

from nupic.algorithms.monitor_mixin.trace import CountsTrace, BoolsTrace



class MetricTest(unittest.TestCase):


  def setUp(self):
    self.trace = CountsTrace(self, "# active cells")
    self.trace.data = [1, 2, 3, 4, 5, 0]


  def testCreateFromTrace(self):
    metric = Metric.createFromTrace(self.trace)
    self.assertEqual(metric.title, self.trace.title)
    self.assertEqual(metric.min, 0)
    self.assertEqual(metric.max, 5)
    self.assertEqual(metric.sum, 15)
    self.assertEqual(metric.mean, 2.5)
    self.assertEqual(metric.standardDeviation, 1.707825127659933)


  def testCreateFromTraceExcludeResets(self):
    resetTrace = BoolsTrace(self, "resets")
    resetTrace.data = [True, False, False, True, False, False]
    metric = Metric.createFromTrace(self.trace, excludeResets=resetTrace)
    self.assertEqual(metric.title, self.trace.title)
    self.assertEqual(metric.min, 0)
    self.assertEqual(metric.max, 5)
    self.assertEqual(metric.sum, 10)
    self.assertEqual(metric.mean, 2.5)
    self.assertEqual(metric.standardDeviation, 1.8027756377319946)



if __name__ == '__main__':
  unittest.main()
