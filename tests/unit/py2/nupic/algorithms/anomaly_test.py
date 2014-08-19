#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

"""Tests for anomaly-related algorithms."""

import unittest2 as unittest
import numpy as np
import timeit

from numpy import array

from nupic.algorithms.anomaly import Anomaly



class AnomalyTest(unittest.TestCase):

  def setUp(self):
    """init"""
    self._anomalyImpl = Anomaly()


  def testComputeAnomalyScoreNoActiveOrPredicted(self):
    score = self._anomalyImpl.computeAnomalyScore(array([]), array([]))
    self.assertAlmostEqual(score, 0.0)


  def testComputeAnomalyScoreNoActive(self):
    score = self._anomalyImpl.computeAnomalyScore(array([]), array([3, 5]))
    self.assertAlmostEqual(score, 1.0)


  def testComputeAnomalyScorePerfectMatch(self):
    score = self._anomalyImpl.computeAnomalyScore(array([3, 5, 7]), array([3, 5, 7]))
    self.assertAlmostEqual(score, 0.0)


  def testComputeAnomalyScoreNoMatch(self):
    score = self._anomalyImpl.computeAnomalyScore(array([2, 4, 6]), array([3, 5, 7]))
    self.assertAlmostEqual(score, 1.0)


  def testComputeAnomalyScorePartialMatch(self):
    score = self._anomalyImpl.computeAnomalyScore(array([2, 3, 6]), array([3, 5, 7]))
    self.assertAlmostEqual(score, 2.0 / 3.0)


  def testAnomalyUseTP(self):
    """anomaly implementation that is using provided temporal pooler"""
    # TODO
    pass


  def testAnomalyCumulative(self):
    """cumulative anomaly implementation"""
    anomalyCum = Anomaly(slidingWindowSize = 3)
    predicted = (array([1, 2, 6]), array([1, 2, 6]), array([1, 2, 6]), array([1, 2, 6]), array([1, 2, 6]), array([1, 2, 6]), array([1, 2, 6]), array([1, 2, 6]), array([1, 2, 6]))
    actual =    (array([1, 2, 6]), array([1, 2, 6]), array([1, 4, 6]), array([10, 11, 6]), array([10, 11, 12]), array([10, 11, 12]), array([10, 11, 12]), array([1, 2, 6]), array([1, 2, 6]))
    anomaly = [] # to be computed
    anomalyExpected = (0.0, 0.0, 1/9.0, (1+2)/9.0, 2/3.0, 8/9.0, 1.0, 2/3.0, 1/3.0)

    # run anomalies
    for i in range(len(actual)): 
      score = anomalyCum.computeAnomalyScore(actual[i], predicted[i])
      anomaly.extend([score])
      self.assertAlmostEqual(anomaly[i], anomalyExpected[i], "not equal anomaly and expected " + str(anomaly) + " vs " + str(anomalyExpected))


if __name__ == "__main__":
  unittest.main()
