#!/usr/bin/env python
# ----------------------------------------------------------------------
# Copyright (C) 2013 Numenta Inc. All rights reserved.
#
# The information and source code contained herein is the
# exclusive property of Numenta Inc.  No part of this software
# may be used, reproduced, stored or distributed in any form,
# without explicit written authorization from Numenta Inc.
# ----------------------------------------------------------------------

"""Unit tests for anomaly likelihood module."""

import unittest2 as unittest
import numpy
import math
import datetime
import copy
from nupic.support.unittesthelpers.testcasebase import TestCaseBase
import nupic.algorithms.anomaly_likelihood as an


class anomalyLikelihoodTest(TestCaseBase):

  def setUp(self):
    
    pass

  def _generateSampleData(self, mean = 0.2, variance = 0.2,
                          metricMean = 0.2, metricVariance = 0.2):
    """
    Generate 1440 samples of fake metrics data with a particular distribution
    of anomaly scores and metric values. Here we generate values every minute. 
    """
    data = []
    p = {'mean': mean,
        'name': 'normal',
        'stdev': math.sqrt(variance),
        'variance': variance}
    samples = an.sampleDistribution(p, 1440)
    p = {'mean': metricMean,
        'name': 'normal',
        'stdev': math.sqrt(metricVariance),
        'variance': metricVariance}
    metricValues = an.sampleDistribution(p, 1440)
    for hour in range(0,24):
      for minute in range(0,60):
        data.append(
          [
            datetime.datetime(2013,2,2,hour,minute,0),
            metricValues[hour*60 + minute],
            samples[hour*60 + minute],
          ]
        )
    
    return data



  def _generateFlatData(self, value = 42.0):
    """
    Generate 1440 samples of flat (unchanging) data. Both anomaly scores and
    metric values are flat.
    """
    data = []
    for hour in range(0,24):
      for minute in range(0,60):
        data.append(
          [
            datetime.datetime(2013,2,2,hour,minute,0),
            value,  
            value,
          ]
        )
    
    return data



  def assertWithinEpsilon(self, a, b, epsilon = 0.001):
    self.assertLessEqual(abs(a-b), epsilon,
                         "Values %g and %g are not within %g" % (a,b,epsilon))



  def testNormalProbability(self):
    """
    Test that the normalProbability function returns correct normal values
    """
    # Test a standard normal distribution
    # Values taken from http://en.wikipedia.org/wiki/Standard_normal_table
    p = {"name": "normal", "mean": 0.0, "variance": 1.0, "stdev": 1.0}
    self.assertWithinEpsilon( an.normalProbability(0.0,p), 0.5 )
    self.assertWithinEpsilon( an.normalProbability(0.3,p), 0.3820885780 )
    self.assertWithinEpsilon( an.normalProbability(1.0,p), 0.1587)
    self.assertWithinEpsilon( 1.0 - an.normalProbability(1.0,p),
                             an.normalProbability(-1.0,p) )
    self.assertWithinEpsilon( an.normalProbability(-0.3,p),
                             1.0 - an.normalProbability(0.3,p) )

    # Non standard normal distribution
    p = {"name": "normal", "mean": 1.0, "variance": 4.0, "stdev": 2.0}
    self.assertWithinEpsilon( an.normalProbability(1.0,p), 0.5)
    self.assertWithinEpsilon( an.normalProbability(2.0,p), 0.3085) 
    self.assertWithinEpsilon( an.normalProbability(3.0,p), 0.1587)
    self.assertWithinEpsilon( an.normalProbability(3.0,p),
                             1.0 - an.normalProbability(-1.0,p) )
    self.assertWithinEpsilon( an.normalProbability(0.0,p),
                             1.0 - an.normalProbability(2.0,p) ) 
    
    # Non standard normal distribution
    p = {"name": "normal", "mean": -2.0, "variance": 0.5,
         "stdev": math.sqrt(0.5)}
    self.assertWithinEpsilon( an.normalProbability(-2.0,p), 0.5)
    self.assertWithinEpsilon( an.normalProbability(-1.5,p), 0.241963652)
    self.assertWithinEpsilon( an.normalProbability(-2.5,p),
                             1.0 - an.normalProbability(-1.5,p))



  def testMovingAverage(self):
    """
    Test that the (internal) moving average maintains the averages correctly,
    even for null initial condition and when the number of values goes over
    windowSize.  Pass in integers and floats. 
    """
    historicalValues = []
    total = 0
    windowSize = 3
    newAverage, historicalValues, total = (
      an._movingAverage(historicalValues, total, 3, windowSize)
      )
    self.assertEqual(newAverage, 3.0)
    self.assertEqual(historicalValues, [3.0])
    self.assertEqual(total, 3.0)
    
    newAverage, historicalValues, total = (
      an._movingAverage(historicalValues, total, 4, windowSize)
      )
    self.assertEqual(newAverage, 3.5)
    self.assertEqual(historicalValues, [3.0, 4.0])
    self.assertEqual(total, 7.0)

    newAverage, historicalValues, total = (
      an._movingAverage(historicalValues, total, 5.0, windowSize)
      )
    self.assertEqual(newAverage, 4.0)
    self.assertEqual(historicalValues, [3.0, 4.0, 5.0])
    self.assertEqual(total, 12.0)

    # Ensure the first value gets popped
    newAverage, historicalValues, total = (
      an._movingAverage(historicalValues, total, 6.0, windowSize)
      )
    self.assertEqual(newAverage, 5.0)
    self.assertEqual(historicalValues, [4.0, 5.0, 6.0])
    self.assertEqual(total, 15.0)


    
  def testEstimateNormal(self):
    """
    This passes in a known set of data and ensures the estimateNormal
    function returns the expected results.
    """
    # 100 samples drawn from mean=0.4, stdev = 0.5
    samples = numpy.array(
      [ 0.32259025, -0.44936321, -0.15784842,  0.72142628,  0.8794327 ,
        0.06323451, -0.15336159, -0.02261703,  0.04806841,  0.47219226,
        0.31102718,  0.57608799,  0.13621071,  0.92446815,  0.1870912 ,
        0.46366935, -0.11359237,  0.66582357,  1.20613048, -0.17735134,
        0.20709358,  0.74508479,  0.12450686, -0.15468728,  0.3982757 ,
        0.87924349,  0.86104855,  0.23688469, -0.26018254,  0.10909429,
        0.65627481,  0.39238532,  0.77150761,  0.47040352,  0.9676175 ,
        0.42148897,  0.0967786 , -0.0087355 ,  0.84427985,  1.46526018,
        1.19214798,  0.16034816,  0.81105554,  0.39150407,  0.93609919,
        0.13992161,  0.6494196 ,  0.83666217,  0.37845278,  0.0368279 ,
       -0.10201944,  0.41144746,  0.28341277,  0.36759426,  0.90439446,
        0.05669459, -0.11220214,  0.34616676,  0.49898439, -0.23846184,
        1.06400524,  0.72202135, -0.2169164 ,  1.136582  , -0.69576865,
        0.48603271,  0.72781008, -0.04749299,  0.15469311,  0.52942518,
        0.24816816,  0.3483905 ,  0.7284215 ,  0.93774676,  0.07286373,
        1.6831539 ,  0.3851082 ,  0.0637406 , -0.92332861, -0.02066161,
        0.93709862,  0.82114131,  0.98631562,  0.05601529,  0.72214694,
        0.09667526,  0.3857222 ,  0.50313998,  0.40775344, -0.69624046,
       -0.4448494 ,  0.99403206,  0.51639049,  0.13951548,  0.23458214,
        1.00712699,  0.40939048, -0.06436434, -0.02753677, -0.23017904])
    
    params = an.estimateNormal(samples)
    self.assertWithinEpsilon( params["mean"], 0.3721)
    self.assertWithinEpsilon( params["variance"], 0.22294)
    self.assertWithinEpsilon( params["stdev"], 0.47216)
    self.assertEqual(params["name"], "normal")




  def testSampleDistribution(self):
    """
    Test that sampleDistribution from a generated distribution returns roughly
    the same parameters.
    """
    # 1000 samples drawn from mean=0.4, stdev = 0.1
    p = {'mean': 0.5,
        'name': 'normal',
        'stdev': math.sqrt(0.1),
        'variance': 0.1}
    samples = an.sampleDistribution(p, 1000)
    
    # Ensure estimate is reasonable
    np = an.estimateNormal(samples)
    self.assertWithinEpsilon( p["mean"], np["mean"], 0.1)
    self.assertWithinEpsilon( p["variance"], np["variance"], 0.1)
    self.assertWithinEpsilon( p["stdev"], np["stdev"], 0.1)
    self.assertTrue(np["name"], "normal")


    
  def testEstimateAnomalyLikelihoods(self):
    """
    This calls estimateAnomalyLikelihoods to estimate the distribution on fake
    data and validates the results
    """
    
    # Generate an estimate using fake distribution of anomaly scores. 
    data1 = self._generateSampleData(mean = 0.2)
      
    likelihoods, avgRecordList, estimatorParams = (
      an.estimateAnomalyLikelihoods(data1[0:1000])
    )
    self.assertEqual(len(likelihoods), 1000)
    self.assertEqual(len(avgRecordList), 1000)
    self.assertTrue(an.isValidEstimatorParams(estimatorParams))
    
    # Check that the sum is correct
    avgParams = estimatorParams["movingAverage"]
    total = 0
    for v in avgRecordList: total = total + v[2]
    self.assertTrue(avgParams["total"],total)
    
    # Check that the estimated mean is correct
    dParams = estimatorParams["distribution"]
    self.assertWithinEpsilon( dParams["mean"],
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
    
    # Generate an estimate using fake distribution of anomaly scores. 
    data1 = self._generateSampleData(mean = 0.2)
    data1 = data1 + [(2,2), (2,2,2,2), (), (2)]  # Malformed records
      
    likelihoods, avgRecordList, estimatorParams = (
      an.estimateAnomalyLikelihoods(data1[0:1000])
    )
    self.assertEqual(len(likelihoods), 1000)
    self.assertEqual(len(avgRecordList), 1000)
    self.assertTrue(an.isValidEstimatorParams(estimatorParams))
    
    # Check that the sum is correct
    avgParams = estimatorParams["movingAverage"]
    total = 0
    for v in avgRecordList: total = total + v[2]
    self.assertTrue(avgParams["total"],total)
    
    # Check that the estimated mean is correct
    dParams = estimatorParams["distribution"]
    self.assertWithinEpsilon( dParams["mean"],
                                    total / float(len(avgRecordList)))
    
    


  def testSkipRecords(self):
    """
    This calls estimateAnomalyLikelihoods with various values of skipRecords
    """
    
    # Check happy path
    data1 = self._generateSampleData(mean = 0.1)[0:200]
    data1 = data1 + (self._generateSampleData(mean = 0.9)[0:200])
    
    likelihoods, avgRecordList, estimatorParams = (
      an.estimateAnomalyLikelihoods(data1, skipRecords=200)
    )
    
    # Check results are correct, i.e. we are actually skipping the first 50
    dParams = estimatorParams["distribution"]
    self.assertWithinEpsilon(dParams["mean"], 0.9, epsilon=0.1)
    
    # Check case where skipRecords > num records
    # In this case a null distribution should be returned which makes all
    # the likelihoods reasonably high
    likelihoods, avgRecordList, estimatorParams = (
      an.estimateAnomalyLikelihoods(data1, skipRecords=500)
    )
    self.assertEqual(len(likelihoods),len(data1))
    self.assertTrue(likelihoods.sum() >= 0.3*len(likelihoods))
        
    # Check the case where skipRecords == num records
    likelihoods, avgRecordList, estimatorParams = (
      an.estimateAnomalyLikelihoods(data1, skipRecords=len(data1))
    )
    self.assertEqual(len(likelihoods),len(data1))
    self.assertTrue(likelihoods.sum() >= 0.3*len(likelihoods))



  def testUpdateAnomalyLikelihoods(self):
    """
    A slight more complex test. This calls estimateAnomalyLikelihoods
    to estimate the distribution on fake data, followed by several calls
    to updateAnomalyLikelihoods. 
    """
    
    #------------------------------------------
    # Step 1. Generate an initial estimate using fake distribution of anomaly
    # scores. 
    data1 = self._generateSampleData(mean = 0.2)[0:1000]
    likelihoods, avgRecordList, estimatorParams = (
      an.estimateAnomalyLikelihoods(data1,averagingWindow=5)
    )
    
    #------------------------------------------
    # Step 2. Generate some new data with a higher average anomaly
    # score. Using the estimator from step 1, to compute likelihoods. Now we
    # should see a lot more anomalies.  
    data2 = self._generateSampleData(mean=0.6)[0:300]
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
    data3 = self._generateSampleData(mean=0.2)[0:1000]
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
    averagedRecordListAll, historicalValuesAll, totalAll = (
      an._anomalyScoreMovingAverage(allData, windowSize = 5)
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
    data1 = self._generateSampleData(mean = 42.0, variance = 1e-10)
      
    likelihoods, avgRecordList, estimatorParams = (
      an.estimateAnomalyLikelihoods(data1[0:1000])
    )
    self.assertEqual(len(likelihoods), 1000)
    self.assertEqual(len(avgRecordList), 1000)
    self.assertTrue(an.isValidEstimatorParams(estimatorParams))
    
    ## Check that the estimated mean is correct
    dParams = estimatorParams["distribution"]
    self.assertWithinEpsilon( dParams["mean"], data1[0][2])

    # If you deviate from the mean, you should get probability 0
    # Test this by sending in just slightly different values.
    data2 = self._generateSampleData(mean = 42.5, variance = 1e-10)
    likelihoods2, _, estimatorParams2 = (
      an.updateAnomalyLikelihoods(data2[0:10], estimatorParams)
    )

    # The likelihoods should go to zero very quickly
    self.assertLessEqual(likelihoods2.sum(), 0.01)


    # Test edge case where anomaly scores are very close to 0
    # In this case we don't let likelihood to get too low. An average
    # anomaly score of 0.1 should be essentially zero, but an average
    # of 0.04 should be higher
    data3 = self._generateSampleData(mean = 0.01, variance = 1e-6)
    
    likelihoods3, _, estimatorParams3 = (
      an.estimateAnomalyLikelihoods(data3[0:1000])
    )
    
    data4 = self._generateSampleData(mean = 0.1, variance = 1e-6)
    likelihoods4, _, estimatorParams4 = (
      an.updateAnomalyLikelihoods(data4[0:20], estimatorParams3)
    )
    
    # Average of 0.1 should go to zero 
    self.assertLessEqual(likelihoods4[10:].mean(), 0.002)
    
    data5 = self._generateSampleData(mean = 0.05, variance = 1e-6)
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
    data1 = self._generateSampleData(
      metricMean = 42.0, metricVariance = 1e-10)[0:1000]
      
    likelihoods, avgRecordList, estimatorParams = (
      an.estimateAnomalyLikelihoods(data1)
    )
    
    # Check that we do indeed get reasonable likelihood values
    self.assertEqual(len(likelihoods), len(data1))
    self.assertTrue(likelihoods.sum() >= 0.4*len(likelihoods))

    # Check that we do indeed get null distribution    
    self.assertDictEqual(estimatorParams['distribution'], an.nullDistribution())



  def testVeryFewScores(self):
    """
    This calls estimateAnomalyLikelihoods and updateAnomalyLikelihoods
    with one or no scores.
    """
    
    # Generate an estimate using two data points
    data1 = self._generateSampleData(mean = 42.0, variance = 1e-10)

    likelihoods, avgRecordList, estimatorParams = (
      an.estimateAnomalyLikelihoods(data1[0:2])
    )

    self.assertTrue(an.isValidEstimatorParams(estimatorParams))
    
    # Check that the estimated mean is that value
    dParams = estimatorParams["distribution"]
    self.assertWithinEpsilon( dParams["mean"], data1[0][2])

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
    data1 = self._generateSampleData(mean=42.0, variance=1e-10)

    likelihoods, avgRecordList, estimatorParams = (
      an.estimateAnomalyLikelihoods(data1[0:1])
    )

    self.assertTrue(an.isValidEstimatorParams(estimatorParams))
    
    # Can't pass in a bad params structure
    with self.assertRaises(ValueError):
      an.updateAnomalyLikelihoods(data1, {'haha': 'heehee'})

    # Can't pass in something not a dict
    with self.assertRaises(ValueError):
      an.updateAnomalyLikelihoods(data1, 42.0)

  
  def testFilterLikelihods2(self):
    """
    Tests _filterLikelihoods function
    """
    redThreshold    = 0.99999
    yellowThreshold = 0.999
    
    # Test first with a list of floats    

    # Since windowSize will be 3, the numbers with an underscore should
    # be replaced with 1-yellowThreshold
    l     = [0.0, 0.0, 0.1, 0.2, 0.5, 0.6, 0.0, 0.0, 0.4, 0.0]
    #             ___                           ___
    l2    = copy.copy(l)
    l2[1] = 1 - yellowThreshold
    l2[7] = 1 - yellowThreshold
    
    l3 = an._filterLikelihoods(l)
    for i, v in enumerate(l3):
      self.assertAlmostEqual(v, l2[i])
      
    # This time test with numpy arrays using values we really got
    # Indices 1-10 should be at 1 - yellowThreshold
    l     = numpy.array([0.999978229, 0.999978229, 0.999999897, 1, 1, 1,
                         1, 0.999999994, 0.999999966, 0.999999966,
                         0.999994331, 0.999516576, 0.99744487])
    l = 1.0 - l
    l2 = copy.copy(l)
    for i in range(1,11):
      l2[i] = 1 - yellowThreshold
    l3 = an._filterLikelihoods(l)
    for i, v in enumerate(l3):
      self.assertAlmostEqual(v, l2[i])


if __name__ == '__main__':
  unittest.main()
