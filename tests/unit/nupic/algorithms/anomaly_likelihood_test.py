# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013-2015, Numenta, Inc.  Unless you have an agreement
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

"""Unit tests for anomaly likelihood module."""

# disable pylint warning: "Access to a protected member xxxxx of a client class"
# pylint: disable=W0212

import copy
import datetime
import math
import numpy
import pickle
import unittest2 as unittest

import mock

from nupic.algorithms import anomaly_likelihood as an
from nupic.support.unittesthelpers.testcasebase import TestCaseBase


def _sampleDistribution(params, numSamples, verbosity=0):
  """
  Given the parameters of a distribution, generate numSamples points from it.
  This routine is mostly for testing.

  :returns: A numpy array of samples.
  """
  if params.has_key("name"):
    if params["name"] == "normal":
      samples = numpy.random.normal(loc=params["mean"],
                                    scale=math.sqrt(params["variance"]),
                                    size=numSamples)
    elif params["name"] == "pareto":
      samples = numpy.random.pareto(params["alpha"], size=numSamples)
    elif params["name"] == "beta":
      samples = numpy.random.beta(a=params["alpha"], b=params["beta"],
                                  size=numSamples)
    else:
      raise ValueError("Undefined distribution: " + params["name"])
  else:
    raise ValueError("Bad distribution params: " + str(params))

  if verbosity > 0:
    print "\nSampling from distribution:", params
    print "After estimation, mean=", numpy.mean(samples), \
          "var=", numpy.var(samples), "stdev=", math.sqrt(numpy.var(samples))
  return samples


def _generateSampleData(mean=0.2, variance=0.2, metricMean=0.2,
                        metricVariance=0.2):
  """
  Generate 1440 samples of fake metrics data with a particular distribution
  of anomaly scores and metric values. Here we generate values every minute.
  """
  data = []
  p = {"mean": mean,
       "name": "normal",
       "stdev": math.sqrt(variance),
       "variance": variance}
  samples = _sampleDistribution(p, 1440)
  p = {"mean": metricMean,
       "name": "normal",
       "stdev": math.sqrt(metricVariance),
       "variance": metricVariance}
  metricValues = _sampleDistribution(p, 1440)
  for hour in range(0, 24):
    for minute in range(0, 60):
      data.append(
        [
          datetime.datetime(2013, 2, 2, hour, minute, 0),
          metricValues[hour * 60 + minute],
          samples[hour * 60 + minute],
        ]
      )

  return data



class AnomalyLikelihoodClassTest(TestCaseBase):
  """Tests the high-level AnomalyLikelihood class"""


  def testCalcSkipRecords(self):

    # numIngested is less than both learningPeriod and windowSize
    numSkip = an.AnomalyLikelihood._calcSkipRecords(
      numIngested=5,
      windowSize=10,
      learningPeriod=10)
    self.assertEqual(numSkip, 5)

    # numIngested is equal to learningPeriod, but less than windowSize
    numSkip = an.AnomalyLikelihood._calcSkipRecords(
      numIngested=10,
      windowSize=15,
      learningPeriod=10)
    self.assertEqual(numSkip, 10)

    # edge case: learningPeriod is 0
    numSkip = an.AnomalyLikelihood._calcSkipRecords(
      numIngested=10,
      windowSize=10,
      learningPeriod=0)
    self.assertEqual(numSkip, 0)

    # boundary case: numIngested is equal to learningPeriod and windowSize
    numSkip = an.AnomalyLikelihood._calcSkipRecords(
      numIngested=10,
      windowSize=10,
      learningPeriod=10)
    self.assertEqual(numSkip, 10)

    # learning samples partially shifted out
    numSkip = an.AnomalyLikelihood._calcSkipRecords(
      numIngested=14,
      windowSize=10,
      learningPeriod=10)
    self.assertEqual(numSkip, 6)

    # learning samples fully shifted out
    numSkip = an.AnomalyLikelihood._calcSkipRecords(
      numIngested=20,
      windowSize=10,
      learningPeriod=10)
    self.assertEqual(numSkip, 0)

    # learning samples plus others shifted out
    numSkip = an.AnomalyLikelihood._calcSkipRecords(
      numIngested=25,
      windowSize=10,
      learningPeriod=10)
    self.assertEqual(numSkip, 0)


  def testHistoricWindowSize(self):
    l = an.AnomalyLikelihood(claLearningPeriod=2,
                             estimationSamples=2,
                             historicWindowSize=3)

    l.anomalyProbability(5, 0.1, timestamp=1) # burn in
    self.assertEqual(len(l._historicalScores), 1)

    l.anomalyProbability(5, 0.1, timestamp=2)
    self.assertEqual(len(l._historicalScores), 2)

    l.anomalyProbability(5, 0.1, timestamp=3)
    self.assertEqual(len(l._historicalScores), 3)

    l.anomalyProbability(5, 0.1, timestamp=4)
    self.assertEqual(len(l._historicalScores), 3)


  def testdWindowSizeImpactOnEstimateAnomalyLikelihoodsArgs(self):

    # Verify that AnomalyLikelihood's historicWindowSize plays nice with args
    # passed to estimateAnomalyLikelihoods"""

    originalEstimateAnomalyLikelihoods = an.estimateAnomalyLikelihoods

    estimationArgs = []

    def estimateAnomalyLikelihoodsWrap(anomalyScores,
                                       averagingWindow=10,
                                       skipRecords=0,
                                       verbosity=0):
      estimationArgs.append((tuple(anomalyScores), skipRecords))

      return originalEstimateAnomalyLikelihoods(anomalyScores,
                                                averagingWindow=averagingWindow,
                                                skipRecords=skipRecords,
                                                verbosity=verbosity)


    estimateAnomalyLikelihoodsPatch = mock.patch(
      "nupic.algorithms.anomaly_likelihood.estimateAnomalyLikelihoods",
      side_effect=estimateAnomalyLikelihoodsWrap, autospec=True)
    with estimateAnomalyLikelihoodsPatch as estimateAnomalyLikelihoodsMock:
      l = an.AnomalyLikelihood(claLearningPeriod=2,
                               estimationSamples=2,
                               historicWindowSize=3)

      l.anomalyProbability(10, 0.1, timestamp=1)
      self.assertEqual(estimateAnomalyLikelihoodsMock.call_count, 0)

      l.anomalyProbability(20, 0.2, timestamp=2)
      self.assertEqual(estimateAnomalyLikelihoodsMock.call_count, 0)

      l.anomalyProbability(30, 0.3, timestamp=3)
      self.assertEqual(estimateAnomalyLikelihoodsMock.call_count, 0)

      l.anomalyProbability(40, 0.4, timestamp=4)
      self.assertEqual(estimateAnomalyLikelihoodsMock.call_count, 0)

      # Estimation should kick in after claLearningPeriod + estimationSamples
      # samples have been ingested
      l.anomalyProbability(50, 0.5, timestamp=5)
      self.assertEqual(estimateAnomalyLikelihoodsMock.call_count, 1)
      # NOTE: we cannot use mock's assert_called_with, because the sliding
      # window container changes in-place after estimateAnomalyLikelihoods is
      # called
      scores, numSkip = estimationArgs.pop()
      self.assertEqual(scores, ((2, 20, 0.2), (3, 30, 0.3), (4, 40, 0.4)))
      self.assertEqual(numSkip, 1)


  def testReestimationPeriodArg(self):
    estimateAnomalyLikelihoodsWrap = mock.Mock(
      wraps=an.estimateAnomalyLikelihoods,
      autospec=True)

    estimateAnomalyLikelihoodsPatch = mock.patch(
      "nupic.algorithms.anomaly_likelihood.estimateAnomalyLikelihoods",
      side_effect=estimateAnomalyLikelihoodsWrap, autospec=True)
    with estimateAnomalyLikelihoodsPatch:
      l = an.AnomalyLikelihood(claLearningPeriod=2,
                               estimationSamples=2,
                               historicWindowSize=3,
                               reestimationPeriod=2)

      # burn-in
      l.anomalyProbability(10, 0.1, timestamp=1)
      l.anomalyProbability(10, 0.1, timestamp=2)
      l.anomalyProbability(10, 0.1, timestamp=3)
      l.anomalyProbability(10, 0.1, timestamp=4)
      self.assertEqual(estimateAnomalyLikelihoodsWrap.call_count, 0)

      l.anomalyProbability(10, 0.1, timestamp=5)
      self.assertEqual(estimateAnomalyLikelihoodsWrap.call_count, 1)
      l.anomalyProbability(10, 0.1, timestamp=6)
      self.assertEqual(estimateAnomalyLikelihoodsWrap.call_count, 1)
      l.anomalyProbability(10, 0.1, timestamp=7)
      self.assertEqual(estimateAnomalyLikelihoodsWrap.call_count, 2)
      l.anomalyProbability(10, 0.1, timestamp=8)
      self.assertEqual(estimateAnomalyLikelihoodsWrap.call_count, 2)


  def testAnomalyProbabilityResultsDuringProbationaryPeriod(self):
    originalUpdateAnomalyLikelihoods = an.updateAnomalyLikelihoods

    def updateAnomalyLikelihoodsWrap(anomalyScores, params, verbosity=0):
      likelihoods, avgRecordList, params = originalUpdateAnomalyLikelihoods(
        anomalyScores=anomalyScores,
        params=params,
        verbosity=verbosity)

      self.assertEqual(len(likelihoods), 1)

      return [0.1], avgRecordList, params


    updateAnomalyLikelihoodsPatch = mock.patch(
      "nupic.algorithms.anomaly_likelihood.updateAnomalyLikelihoods",
      side_effect=updateAnomalyLikelihoodsWrap, autospec=True)
    with updateAnomalyLikelihoodsPatch:
      l = an.AnomalyLikelihood(claLearningPeriod=2,
                               estimationSamples=2,
                               historicWindowSize=3)

      # 0.5 result is expected during burn-in
      self.assertEqual(l.anomalyProbability(10, 0.1, timestamp=1), 0.5)
      self.assertEqual(l.anomalyProbability(10, 0.1, timestamp=2), 0.5)
      self.assertEqual(l.anomalyProbability(10, 0.1, timestamp=3), 0.5)
      self.assertEqual(l.anomalyProbability(10, 0.1, timestamp=4), 0.5)

      self.assertEqual(l.anomalyProbability(10, 0.1, timestamp=5), 0.9)
      self.assertEqual(l.anomalyProbability(10, 0.1, timestamp=6), 0.9)


  def testEquals(self):
    l = an.AnomalyLikelihood(claLearningPeriod=2, estimationSamples=2)
    l2 = an.AnomalyLikelihood(claLearningPeriod=2, estimationSamples=2)
    self.assertEqual(l, l2)

    # Use 5 iterations to force the distribution to be created (4 probationary
    # samples + 1)
    l2.anomalyProbability(5, 0.1, timestamp=1) # burn in
    l2.anomalyProbability(5, 0.1, timestamp=2)
    l2.anomalyProbability(5, 0.1, timestamp=3)
    l2.anomalyProbability(5, 0.1, timestamp=4)
    self.assertIsNone(l2._distribution)
    l2.anomalyProbability(1, 0.3, timestamp=5)
    self.assertIsNotNone(l2._distribution)
    self.assertNotEqual(l, l2)

    l.anomalyProbability(5, 0.1, timestamp=1) # burn in
    l.anomalyProbability(5, 0.1, timestamp=2)
    l.anomalyProbability(5, 0.1, timestamp=3)
    l.anomalyProbability(5, 0.1, timestamp=4)
    self.assertIsNone(l._distribution)
    l.anomalyProbability(1, 0.3, timestamp=5)
    self.assertIsNotNone(l._distribution)
    self.assertEqual(l, l2, "equal? \n%s\n vs. \n%s" % (l, l2))


  def testSerialization(self):
    """serialization using pickle"""
    l = an.AnomalyLikelihood(claLearningPeriod=2, estimationSamples=2)

    l.anomalyProbability("hi", 0.1, timestamp=1) # burn in
    l.anomalyProbability("hi", 0.1, timestamp=2)
    l.anomalyProbability("hello", 0.3, timestamp=3)

    stored = pickle.dumps(l)
    restored = pickle.loads(stored)

    self.assertEqual(l, restored)



class AnomalyLikelihoodAlgorithmTest(TestCaseBase):
  """Tests the low-level algorithm functions"""


  def assertWithinEpsilon(self, a, b, epsilon=0.005):
    self.assertLessEqual(abs(a - b), epsilon,
                         "Values %g and %g are not within %g" % (a, b, epsilon))


  def testNormalProbability(self):
    """
    Test that the tailProbability function returns correct normal values
    """
    # Test a standard normal distribution
    # Values taken from http://en.wikipedia.org/wiki/Standard_normal_table
    p = {"name": "normal", "mean": 0.0, "variance": 1.0, "stdev": 1.0}
    self.assertWithinEpsilon(an.tailProbability(0.0, p), 0.5)
    self.assertWithinEpsilon(an.tailProbability(0.3, p), 0.3820885780)
    self.assertWithinEpsilon(an.tailProbability(1.0, p), 0.1587)
    self.assertWithinEpsilon(an.tailProbability(1.0, p),
                             an.tailProbability(-1.0, p))
    self.assertWithinEpsilon(an.tailProbability(-0.3, p),
                             an.tailProbability(0.3, p))

    # Non standard normal distribution
    p = {"name": "normal", "mean": 1.0, "variance": 4.0, "stdev": 2.0}
    self.assertWithinEpsilon(an.tailProbability(1.0, p), 0.5)
    self.assertWithinEpsilon(an.tailProbability(2.0, p), 0.3085)
    self.assertWithinEpsilon(an.tailProbability(3.0, p), 0.1587)
    self.assertWithinEpsilon(an.tailProbability(3.0, p),
                             an.tailProbability(-1.0, p))
    self.assertWithinEpsilon(an.tailProbability(0.0, p),
                             an.tailProbability(2.0, p))

    # Non standard normal distribution
    p = {"name": "normal", "mean": -2.0, "variance": 0.5,
         "stdev": math.sqrt(0.5)}
    self.assertWithinEpsilon(an.tailProbability(-2.0, p), 0.5)
    self.assertWithinEpsilon(an.tailProbability(-1.5, p), 0.241963652)
    self.assertWithinEpsilon(an.tailProbability(-2.5, p),
                             an.tailProbability(-1.5, p))


  def testEstimateNormal(self):
    """
    This passes in a known set of data and ensures the estimateNormal
    function returns the expected results.
    """
    # 100 samples drawn from mean=0.4, stdev = 0.5
    samples = numpy.array(
      [0.32259025, -0.44936321, -0.15784842, 0.72142628, 0.8794327,
       0.06323451, -0.15336159, -0.02261703, 0.04806841, 0.47219226,
       0.31102718, 0.57608799, 0.13621071, 0.92446815, 0.1870912,
       0.46366935, -0.11359237, 0.66582357, 1.20613048, -0.17735134,
       0.20709358, 0.74508479, 0.12450686, -0.15468728, 0.3982757,
       0.87924349, 0.86104855, 0.23688469, -0.26018254, 0.10909429,
       0.65627481, 0.39238532, 0.77150761, 0.47040352, 0.9676175,
       0.42148897, 0.0967786, -0.0087355, 0.84427985, 1.46526018,
       1.19214798, 0.16034816, 0.81105554, 0.39150407, 0.93609919,
       0.13992161, 0.6494196, 0.83666217, 0.37845278, 0.0368279,
       -0.10201944, 0.41144746, 0.28341277, 0.36759426, 0.90439446,
       0.05669459, -0.11220214, 0.34616676, 0.49898439, -0.23846184,
       1.06400524, 0.72202135, -0.2169164, 1.136582, -0.69576865,
       0.48603271, 0.72781008, -0.04749299, 0.15469311, 0.52942518,
       0.24816816, 0.3483905, 0.7284215, 0.93774676, 0.07286373,
       1.6831539, 0.3851082, 0.0637406, -0.92332861, -0.02066161,
       0.93709862, 0.82114131, 0.98631562, 0.05601529, 0.72214694,
       0.09667526, 0.3857222, 0.50313998, 0.40775344, -0.69624046,
       -0.4448494, 0.99403206, 0.51639049, 0.13951548, 0.23458214,
       1.00712699, 0.40939048, -0.06436434, -0.02753677, -0.23017904])

    params = an.estimateNormal(samples)
    self.assertWithinEpsilon(params["mean"], 0.3721)
    self.assertWithinEpsilon(params["variance"], 0.22294)
    self.assertWithinEpsilon(params["stdev"], 0.47216)
    self.assertEqual(params["name"], "normal")


  def testSampleDistribution(self):
    """
    Test that sampleDistribution from a generated distribution returns roughly
    the same parameters.
    """
    # 1000 samples drawn from mean=0.4, stdev = 0.1
    p = {"mean": 0.5,
         "name": "normal",
         "stdev": math.sqrt(0.1),
         "variance": 0.1}
    samples = _sampleDistribution(p, 1000)

    # Ensure estimate is reasonable
    np = an.estimateNormal(samples)
    self.assertWithinEpsilon(p["mean"], np["mean"], 0.1)
    self.assertWithinEpsilon(p["variance"], np["variance"], 0.1)
    self.assertWithinEpsilon(p["stdev"], np["stdev"], 0.1)
    self.assertTrue(np["name"], "normal")


  def testEstimateAnomalyLikelihoods(self):
    """
    This calls estimateAnomalyLikelihoods to estimate the distribution on fake
    data and validates the results
    """

    # Generate an estimate using fake distribution of anomaly scores.
    data1 = _generateSampleData(mean=0.2)

    likelihoods, avgRecordList, estimatorParams = (
      an.estimateAnomalyLikelihoods(data1[0:1000])
    )
    self.assertEqual(len(likelihoods), 1000)
    self.assertEqual(len(avgRecordList), 1000)
    self.assertTrue(an.isValidEstimatorParams(estimatorParams))

    # Check that the sum is correct
    avgParams = estimatorParams["movingAverage"]
    total = 0
    for v in avgRecordList:
      total = total + v[2]
    self.assertTrue(avgParams["total"], total)

    # Check that the estimated mean is correct
    dParams = estimatorParams["distribution"]
    self.assertWithinEpsilon(dParams["mean"],
                             total / float(len(avgRecordList)))

    # Number of points with lower than 2% probability should be pretty low
    # but not zero. Can't use exact 2% here due to random variations
    self.assertLessEqual(numpy.sum(likelihoods < 0.02), 50)
    self.assertGreaterEqual(numpy.sum(likelihoods < 0.02), 1)


  def testEstimateAnomalyLikelihoodsMalformedRecords(self):
    """
    This calls estimateAnomalyLikelihoods with malformed records, which should
    be quietly skipped.
    """

    # Generate a fake distribution of anomaly scores, and add malformed records
    data1 = _generateSampleData(mean=0.2)
    data1 = data1[0:1000] + [(2, 2)] + [(2, 2, 2, 2)] + [()] + [(2)]

    likelihoods, avgRecordList, estimatorParams = (
      an.estimateAnomalyLikelihoods(data1[0:1004])
    )
    self.assertEqual(len(likelihoods), 1000)
    self.assertEqual(len(avgRecordList), 1000)
    self.assertTrue(an.isValidEstimatorParams(estimatorParams))

    # Check that the sum is correct
    avgParams = estimatorParams["movingAverage"]
    total = 0
    for v in avgRecordList:
      total = total + v[2]
    self.assertTrue(avgParams["total"], total)

    # Check that the estimated mean is correct
    dParams = estimatorParams["distribution"]
    self.assertWithinEpsilon(dParams["mean"],
                             total / float(len(avgRecordList)))


  def testSkipRecords(self):
    """
    This calls estimateAnomalyLikelihoods with various values of skipRecords
    """

    # Check happy path
    data1 = _generateSampleData(mean=0.1)[0:200]
    data1 = data1 + (_generateSampleData(mean=0.9)[0:200])

    likelihoods, _, estimatorParams = (
      an.estimateAnomalyLikelihoods(data1, skipRecords=200)
    )

    # Check results are correct, i.e. we are actually skipping the first 50
    dParams = estimatorParams["distribution"]
    self.assertWithinEpsilon(dParams["mean"], 0.9, epsilon=0.1)

    # Check case where skipRecords > num records
    # In this case a null distribution should be returned which makes all
    # the likelihoods reasonably high
    likelihoods, _, estimatorParams = (
      an.estimateAnomalyLikelihoods(data1, skipRecords=500)
    )
    self.assertEqual(len(likelihoods), len(data1))
    self.assertTrue(likelihoods.sum() >= 0.3 * len(likelihoods))

    # Check the case where skipRecords == num records
    likelihoods, _, estimatorParams = (
      an.estimateAnomalyLikelihoods(data1, skipRecords=len(data1))
    )
    self.assertEqual(len(likelihoods), len(data1))
    self.assertTrue(likelihoods.sum() >= 0.3 * len(likelihoods))


  def testUpdateAnomalyLikelihoods(self):
    """
    A slight more complex test. This calls estimateAnomalyLikelihoods
    to estimate the distribution on fake data, followed by several calls
    to updateAnomalyLikelihoods.
    """

    #------------------------------------------
    # Step 1. Generate an initial estimate using fake distribution of anomaly
    # scores.
    data1 = _generateSampleData(mean=0.2)[0:1000]
    _, _, estimatorParams = (
      an.estimateAnomalyLikelihoods(data1, averagingWindow=5)
    )

    #------------------------------------------
    # Step 2. Generate some new data with a higher average anomaly
    # score. Using the estimator from step 1, to compute likelihoods. Now we
    # should see a lot more anomalies.
    data2 = _generateSampleData(mean=0.6)[0:300]
    likelihoods2, avgRecordList2, estimatorParams2 = (
      an.updateAnomalyLikelihoods(data2, estimatorParams)
    )
    self.assertEqual(len(likelihoods2), len(data2))
    self.assertEqual(len(avgRecordList2), len(data2))
    self.assertTrue(an.isValidEstimatorParams(estimatorParams))

    # The new running total should be different
    self.assertNotEqual(estimatorParams2["movingAverage"]["total"],
                        estimatorParams["movingAverage"]["total"])

    # We should have many more samples where likelihood is < 0.01, but not all
    self.assertGreaterEqual(numpy.sum(likelihoods2 < 0.01), 25)
    self.assertLessEqual(numpy.sum(likelihoods2 < 0.01), 250)

    #------------------------------------------
    # Step 3. Generate some new data with the expected average anomaly score. We
    # should see fewer anomalies than in Step 2.
    data3 = _generateSampleData(mean=0.2)[0:1000]
    likelihoods3, avgRecordList3, estimatorParams3 = (
      an.updateAnomalyLikelihoods(data3, estimatorParams2)
    )

    self.assertEqual(len(likelihoods3), len(data3))
    self.assertEqual(len(avgRecordList3), len(data3))
    self.assertTrue(an.isValidEstimatorParams(estimatorParams3))

    # The new running total should be different
    self.assertNotEqual(estimatorParams3["movingAverage"]["total"],
                        estimatorParams["movingAverage"]["total"])
    self.assertNotEqual(estimatorParams3["movingAverage"]["total"],
                        estimatorParams2["movingAverage"]["total"])

    # We should have a small number samples where likelihood is < 0.02, but at
    # least one
    self.assertGreaterEqual(numpy.sum(likelihoods3 < 0.01), 1)
    self.assertLessEqual(numpy.sum(likelihoods3 < 0.01), 100)

    #------------------------------------------
    # Step 4. Validate that sending data incrementally is the same as sending
    # in one batch
    allData = data1
    allData.extend(data2)
    allData.extend(data3)

    # Compute moving average of all the data and check it's the same
    _, historicalValuesAll, totalAll = (
      an._anomalyScoreMovingAverage(allData, windowSize=5)
    )
    self.assertEqual(sum(historicalValuesAll),
                     sum(estimatorParams3["movingAverage"]["historicalValues"]))
    self.assertEqual(totalAll,
                     estimatorParams3["movingAverage"]["total"])


  def testFlatAnomalyScores(self):
    """
    This calls estimateAnomalyLikelihoods with flat distributions and
    ensures things don't crash.
    """

    # Generate an estimate using fake distribution of anomaly scores.
    data1 = _generateSampleData(mean=42.0, variance=1e-10)

    likelihoods, avgRecordList, estimatorParams = (
      an.estimateAnomalyLikelihoods(data1[0:1000])
    )
    self.assertEqual(len(likelihoods), 1000)
    self.assertEqual(len(avgRecordList), 1000)
    self.assertTrue(an.isValidEstimatorParams(estimatorParams))

    ## Check that the estimated mean is correct
    dParams = estimatorParams["distribution"]
    self.assertWithinEpsilon(dParams["mean"], data1[0][2])

    # If you deviate from the mean, you should get probability 0
    # Test this by sending in just slightly different values.
    data2 = _generateSampleData(mean=42.5, variance=1e-10)
    likelihoods2, _, _ = (
      an.updateAnomalyLikelihoods(data2[0:10], estimatorParams)
    )

    # The likelihoods should go to zero very quickly
    self.assertLessEqual(likelihoods2.sum(), 0.01)


    # Test edge case where anomaly scores are very close to 0
    # In this case we don't let likelihood to get too low. An average
    # anomaly score of 0.1 should be essentially zero, but an average
    # of 0.04 should be higher
    data3 = _generateSampleData(mean=0.01, variance=1e-6)

    _, _, estimatorParams3 = (
      an.estimateAnomalyLikelihoods(data3[0:1000])
    )

    data4 = _generateSampleData(mean=0.1, variance=1e-6)
    likelihoods4, _, estimatorParams4 = (
      an.updateAnomalyLikelihoods(data4[0:20], estimatorParams3)
    )

    # Average of 0.1 should go to zero
    self.assertLessEqual(likelihoods4[10:].mean(), 0.002)

    data5 = _generateSampleData(mean=0.05, variance=1e-6)
    likelihoods5, _, _ = (
      an.updateAnomalyLikelihoods(data5[0:20], estimatorParams4)
    )

    # The likelihoods should be low but not near zero
    self.assertLessEqual(likelihoods5[10:].mean(), 0.28)
    self.assertGreater(likelihoods5[10:].mean(), 0.015)


  def testFlatMetricScores(self):
    """
    This calls estimateAnomalyLikelihoods with flat metric values. In this case
    we should use the null distribution, which gets reasonably high likelihood
    for everything.
    """
    # Generate samples with very flat metric values
    data1 = _generateSampleData(
      metricMean=42.0, metricVariance=1e-10)[0:1000]

    likelihoods, _, estimatorParams = (
      an.estimateAnomalyLikelihoods(data1)
    )

    # Check that we do indeed get reasonable likelihood values
    self.assertEqual(len(likelihoods), len(data1))
    self.assertTrue(likelihoods.sum() >= 0.4 * len(likelihoods))

    # Check that we do indeed get null distribution
    self.assertDictEqual(estimatorParams["distribution"], an.nullDistribution())


  def testVeryFewScores(self):
    """
    This calls estimateAnomalyLikelihoods and updateAnomalyLikelihoods
    with one or no scores.
    """

    # Generate an estimate using two data points
    data1 = _generateSampleData(mean=42.0, variance=1e-10)

    _, _, estimatorParams = (
      an.estimateAnomalyLikelihoods(data1[0:2])
    )

    self.assertTrue(an.isValidEstimatorParams(estimatorParams))

    # Check that the estimated mean is that value
    dParams = estimatorParams["distribution"]
    self.assertWithinEpsilon(dParams["mean"], data1[0][2])

    # Can't generate an estimate using no data points
    data1 = numpy.zeros(0)
    with self.assertRaises(ValueError):
      an.estimateAnomalyLikelihoods(data1)

    # Can't update with no scores
    with self.assertRaises(ValueError):
      an.updateAnomalyLikelihoods(data1, estimatorParams)


  def testBadParams(self):
    """
    Calls updateAnomalyLikelihoods with bad params.
    """

    # Generate an estimate using one data point
    data1 = _generateSampleData(mean=42.0, variance=1e-10)

    _, _, estimatorParams = (
      an.estimateAnomalyLikelihoods(data1[0:1])
    )

    self.assertTrue(an.isValidEstimatorParams(estimatorParams))

    # Can't pass in a bad params structure
    with self.assertRaises(ValueError):
      an.updateAnomalyLikelihoods(data1, {"haha": "heehee"})

    # Can't pass in something not a dict
    with self.assertRaises(ValueError):
      an.updateAnomalyLikelihoods(data1, 42.0)


  def testFilterLikelihodsInputType(self):
    """
    Calls _filterLikelihoods with both input types -- numpy array of floats and
    list of floats.
    """
    l =[0.0, 0.0, 0.3, 0.3, 0.5]
    l2 = an._filterLikelihoods(l)
    n = numpy.array(l)
    n2 = an._filterLikelihoods(n)
    filtered = [0.0, 0.001, 0.3, 0.3, 0.5]

    for i in range(len(l)):
      self.assertAlmostEqual(
        l2[i], filtered[i],
        msg="Input of type list returns incorrect result")

    for i in range(len(n)):
      self.assertAlmostEqual(
        n2[i], filtered[i],
        msg="Input of type numpy array returns incorrect result")



  def testFilterLikelihoods(self):
    """
    Tests _filterLikelihoods function for several cases:
      i. Likelihood goes straight to redzone, skipping over yellowzone, repeats
      ii. Case (i) with different values, and numpy array instead of float list
      iii. A scenario where changing the redzone from four to five 9s should
           filter differently
    """
    redThreshold = 0.9999
    yellowThreshold = 0.999

    # Case (i): values at indices 1 and 7 should be filtered to yellowzone
    l = [1.0, 1.0, 0.9, 0.8, 0.5, 0.4, 1.0, 1.0, 0.6, 0.0]
    l = [1 - x for x in l]
    l2 = copy.copy(l)
    l2[1] = 1 - yellowThreshold
    l2[7] = 1 - yellowThreshold
    l3 = an._filterLikelihoods(l, redThreshold=redThreshold)

    for i in range(len(l2)):
      self.assertAlmostEqual(l2[i], l3[i], msg="Failure in case (i)")


    # Case (ii): values at indices 1-10 should be filtered to yellowzone
    l = numpy.array([0.999978229, 0.999978229, 0.999999897, 1, 1, 1, 1,
                     0.999999994, 0.999999966, 0.999999966, 0.999994331,
                     0.999516576, 0.99744487])
    l = 1.0 - l
    l2 = copy.copy(l)
    l2[1:11] = 1 - yellowThreshold
    l3 = an._filterLikelihoods(l, redThreshold=redThreshold)

    for i in range(len(l2)):
      self.assertAlmostEqual(l2[i], l3[i], msg="Failure in case (ii)")


    # Case (iii): redThreshold difference should be at index 2
    l = numpy.array([0.999968329, 0.999999897, 1, 1, 1,
                     1, 0.999999994, 0.999999966, 0.999999966,
                     0.999994331, 0.999516576, 0.99744487])
    l = 1.0 - l
    l2a = copy.copy(l)
    l2b = copy.copy(l)
    l2a[1:10] = 1 - yellowThreshold
    l2b[2:10] = 1 - yellowThreshold
    l3a = an._filterLikelihoods(l, redThreshold=redThreshold)
    l3b = an._filterLikelihoods(l, redThreshold=0.99999)

    for i in range(len(l2a)):
      self.assertAlmostEqual(l2a[i], l3a[i],
                             msg="Failure in case (iii), list a")

    for i in range(len(l2b)):
      self.assertAlmostEqual(l2b[i], l3b[i],
                             msg="Failure in case (iii), list b")

    self.assertFalse(numpy.array_equal(l3a, l3b),
                     msg="Failure in case (iii), list 3")



if __name__ == "__main__":
  unittest.main()
