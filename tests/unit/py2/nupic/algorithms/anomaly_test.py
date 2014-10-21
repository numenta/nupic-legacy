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

import unittest

from numpy import array

from nupic.algorithms import anomaly


class AnomalyTest(unittest.TestCase):
  """Tests for anomaly score functions and classes."""


  def testComputeRawAnomalyScoreNoActiveOrPredicted(self):
    score = anomaly.computeRawAnomalyScore(array([]), array([]))
    self.assertAlmostEqual(score, 0.0)


  def testComputeRawAnomalyScoreNoActive(self):
    score = anomaly.computeRawAnomalyScore(array([]), array([3, 5]))
    self.assertAlmostEqual(score, 1.0)


  def testComputeRawAnomalyScorePerfectMatch(self):
    score = anomaly.computeRawAnomalyScore(array([3, 5, 7]), array([3, 5, 7]))
    self.assertAlmostEqual(score, 0.0)


  def testComputeRawAnomalyScoreNoMatch(self):
    score = anomaly.computeRawAnomalyScore(array([2, 4, 6]), array([3, 5, 7]))
    self.assertAlmostEqual(score, 1.0)


  def testComputeRawAnomalyScorePartialMatch(self):
    score = anomaly.computeRawAnomalyScore(array([2, 3, 6]), array([3, 5, 7]))
    self.assertAlmostEqual(score, 2.0 / 3.0)

###################
  def testComputeAnomalyScoreNoActiveOrPredicted(self):
    anomalyComputer = anomaly.Anomaly()
    score = anomalyComputer.compute(array([]), array([]))
    self.assertAlmostEqual(score, 0.0)


  def testComputeAnomalyScoreNoActive(self):
    anomalyComputer = anomaly.Anomaly()
    score = anomalyComputer.compute(array([]), array([3, 5]))
    self.assertAlmostEqual(score, 1.0)


  def testComputeAnomalyScorePerfectMatch(self):
    anomalyComputer = anomaly.Anomaly()
    score = anomalyComputer.compute(array([3, 5, 7]), array([3, 5, 7]))
    self.assertAlmostEqual(score, 0.0)


  def testComputeAnomalyScoreNoMatch(self):
    anomalyComputer = anomaly.Anomaly()
    score = anomalyComputer.compute(array([2, 4, 6]), array([3, 5, 7]))
    self.assertAlmostEqual(score, 1.0)


  def testComputeAnomalyScorePartialMatch(self):
    anomalyComputer = anomaly.Anomaly()
    score = anomalyComputer.compute(array([2, 3, 6]), array([3, 5, 7]))
    self.assertAlmostEqual(score, 2.0 / 3.0)


  def testAnomalyCumulative(self):
    """Test cumulative anomaly scores."""
    anomalyComputer = anomaly.Anomaly(slidingWindowSize=3)
    predicted = (array([1, 2, 6]), array([1, 2, 6]), array([1, 2, 6]),
                 array([1, 2, 6]), array([1, 2, 6]), array([1, 2, 6]),
                 array([1, 2, 6]), array([1, 2, 6]), array([1, 2, 6]))
    actual = (array([1, 2, 6]), array([1, 2, 6]), array([1, 4, 6]),
              array([10, 11, 6]), array([10, 11, 12]), array([10, 11, 12]),
              array([10, 11, 12]), array([1, 2, 6]), array([1, 2, 6]))
    anomalyExpected = (0.0, 0.0, 1.0/9.0, 3.0/9.0, 2.0/3.0, 8.0/9.0, 1.0,
                       2.0/3.0, 1.0/3.0)

    for act, pred, expected in zip(actual, predicted, anomalyExpected):
      score = anomalyComputer.compute(act, pred)
      self.assertAlmostEqual(
          score, expected, places=5,
          msg="Anomaly score of %f doesn't match expected of %f" % (
              score, expected))


  def testComputeAnomalySelectModePure(self):
    anomalyComputer = anomaly.Anomaly(mode=anomaly.Anomaly.MODE_PURE)
    score = anomalyComputer.compute(array([2, 3, 6]), array([3, 5, 7]))
    self.assertAlmostEqual(score, 2.0 / 3.0)



if __name__ == "__main__":
  unittest.main()