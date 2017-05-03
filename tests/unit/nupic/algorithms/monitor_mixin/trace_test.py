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
