# Copyright 2014 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""Tests for anomaly-related algorithms."""

import unittest

from numpy import array
import pickle

from nupic.algorithms import anomaly
from nupic.algorithms.anomaly import Anomaly

class AnomalyTest(unittest.TestCase):
  """Tests for anomaly score functions and classes."""


  def testComputeRawAnomalyScoreNoActiveOrPredicted(self):
    score = anomaly.computeRawAnomalyScore(array([]), array([]))
    self.assertAlmostEqual(score, 0.0)


  def testComputeRawAnomalyScoreNoActive(self):
    score = anomaly.computeRawAnomalyScore(array([]), array([3, 5]))
    self.assertAlmostEqual(score, 0.0)


  def testComputeRawAnomalyScorePerfectMatch(self):
    score = anomaly.computeRawAnomalyScore(array([3, 5, 7]), array([3, 5, 7]))
    self.assertAlmostEqual(score, 0.0)


  def testComputeRawAnomalyScoreNoMatch(self):
    score = anomaly.computeRawAnomalyScore(array([2, 4, 6]), array([3, 5, 7]))
    self.assertAlmostEqual(score, 1.0)


  def testComputeRawAnomalyScorePartialMatch(self):
    score = anomaly.computeRawAnomalyScore(array([2, 3, 6]), array([3, 5, 7]))
    self.assertAlmostEqual(score, 2.0 / 3.0)


  def testComputeAnomalyScoreNoActiveOrPredicted(self):
    anomalyComputer = anomaly.Anomaly()
    score = anomalyComputer.compute(array([]), array([]))
    self.assertAlmostEqual(score, 0.0)


  def testComputeAnomalyScoreNoActive(self):
    anomalyComputer = anomaly.Anomaly()
    score = anomalyComputer.compute(array([]), array([3, 5]))
    self.assertAlmostEqual(score, 0.0)


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


  def testSerialization(self):
    """serialization using pickle"""
    # instances to test
    aDef = Anomaly()
    aLike = Anomaly(mode=Anomaly.MODE_LIKELIHOOD)
    aWeig = Anomaly(mode=Anomaly.MODE_WEIGHTED)
    # test anomaly with all whistles (MovingAverage, Likelihood, ...)
    aAll = Anomaly(mode=Anomaly.MODE_LIKELIHOOD, slidingWindowSize=5)
    inst = [aDef, aLike, aWeig, aAll] 

    for a in inst:
      stored = pickle.dumps(a)
      restored = pickle.loads(stored)
      self.assertEqual(a, restored)


  def testEquals(self):
    an = Anomaly()
    anP = Anomaly()
    self.assertEqual(an, anP, "default constructors equal")

    anN = Anomaly(mode=Anomaly.MODE_LIKELIHOOD)
    self.assertNotEqual(an, anN)
    an = Anomaly(mode=Anomaly.MODE_LIKELIHOOD)
    self.assertEqual(an, anN)

    an = Anomaly(slidingWindowSize=5, mode=Anomaly.MODE_WEIGHTED, binaryAnomalyThreshold=0.9)
    anP = Anomaly(slidingWindowSize=5, mode=Anomaly.MODE_WEIGHTED, binaryAnomalyThreshold=0.9)
    anN = Anomaly(slidingWindowSize=4, mode=Anomaly.MODE_WEIGHTED, binaryAnomalyThreshold=0.9)
    self.assertEqual(an, anP)
    self.assertNotEqual(an, anN)
    anN = Anomaly(slidingWindowSize=5, mode=Anomaly.MODE_WEIGHTED, binaryAnomalyThreshold=0.5)
    self.assertNotEqual(an, anN)

    

if __name__ == "__main__":
  unittest.main()
