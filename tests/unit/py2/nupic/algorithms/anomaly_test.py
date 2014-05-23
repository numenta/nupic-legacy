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

from nupic.algorithms.anomaly import Anomaly as AnomalyImpl



class AnomalyTest(unittest.TestCase):

  def setUp(self):
    """init"""
    self._anomalyImpl = AnomalyImpl()


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


  def testNumpyVsPythonSumSpeed(self):
    """testing the python / numpy .sum() speed"""
    # from https://stackoverflow.com/questions/10922231/pythons-sum-vs-numpys-numpy-sum

    data = np.in1d(np.random.standard_normal(1000), np.random.standard_normal(1000)) # this function is called in each computeAnomalyScore()
    def pure_sum():
      return sum(data)

    def numpy_sum():
      return np.sum(data)
    
    n = 1 # rounds

    tPython = timeit.timeit(pure_sum, number = n)
    tNpy = timeit.timeit(numpy_sum, number = n)
    speedup = tPython/float(tNpy)
    print "speedup: "+str(speedup)+"x"
    self.assertGreater(speedup, 1)


  def testAnomalyUseTP(self):
    """anomaly implementation that is using provided temporal pooler"""
    # TODO
    pass


  def testAnomalyCumulative(self):
    """cumulative anomaly implementation"""
    anomalyCum = AnomalyImpl(slidingWindowSize = 3)
    predicted = [array([1, 2, 6]), array([1, 2, 6]), array([1, 2, 6]), array([1, 2, 6]), array([1, 2, 6]), array([1, 2, 6]), array([1, 2, 6]), array([1, 2, 6]), array([1, 2, 6])]
    actual =    [array([1, 2, 6]), array([1, 2, 6]), array([1, 4, 6]), array([10, 11, 6]), array([10, 11, 12]), array([10, 11, 12]), array([10, 11, 12]), array([1, 2, 6]), array([1, 2, 6])]
    anomaly = [] # to be computed
    anomalyExpected = [0, 0, 1/float(9), (1+2)/float(9), 2/float(3), 8/float(9), 1, 2/float(3), 1/float(3)]

    # run anomalies
    for i in range(len(actual)): 
      score = anomalyCum.computeAnomalyScore(actual[i], predicted[i])
      anomaly.extend([score])

    self.assertTrue(anomaly == anomalyExpected, "not equal anomaly and expected " + str(anomaly) + " vs " + str(anomalyExpected))


if __name__ == "__main__":
  unittest.main()
