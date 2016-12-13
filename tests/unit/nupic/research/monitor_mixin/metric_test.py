# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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

from nupic.research.monitor_mixin.metric import Metric
from nupic.research.monitor_mixin.trace import CountsTrace, BoolsTrace



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
