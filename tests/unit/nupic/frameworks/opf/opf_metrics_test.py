# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
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

import numpy as np

import unittest2 as unittest

from nupic.frameworks.opf.metrics import getModule, MetricSpec, MetricMulti



class OPFMetricsTest(unittest.TestCase):

  DELTA = 0.01
  VERBOSITY = 0


  def testRMSE(self):
    rmse = getModule(MetricSpec("rmse", None, None,
{"verbosity" : OPFMetricsTest.VERBOSITY}))
    gt = [9, 4, 5, 6]
    p = [0, 13, 8, 3]
    for i in xrange(len(gt)):
      rmse.addInstance(gt[i], p[i])
    target = 6.71

    self.assertTrue(abs(rmse.getMetric()["value"]-target)\
< OPFMetricsTest.DELTA)


  def testNRMSE(self):
    nrmse = getModule(MetricSpec("nrmse", None, None,
                                 {"verbosity" : OPFMetricsTest.VERBOSITY}))
    gt = [9, 4, 5, 6]
    p = [0, 13, 8, 3]
    for i in xrange(len(gt)):
      nrmse.addInstance(gt[i], p[i])
    target = 3.5856858280031814

    self.assertAlmostEqual(nrmse.getMetric()["value"], target)


  def testWindowedRMSE(self):
    wrmse = getModule(MetricSpec("rmse", None, None,
{"verbosity": OPFMetricsTest.VERBOSITY, "window":3}))
    gt = [9, 4, 4, 100, 44]
    p = [0, 13, 4, 6, 7]
    for gv, pv in zip(gt, p):
      wrmse.addInstance(gv, pv)
    target = 58.324

    self.assertTrue (abs(wrmse.getMetric()["value"]-target)\
< OPFMetricsTest.DELTA)


  def testAAE(self):
    aae = getModule(MetricSpec("aae", None, None,
{"verbosity" : OPFMetricsTest.VERBOSITY}))
    gt = [9, 4, 5, 6]
    p = [0, 13, 8, 3]
    for i in xrange(len(gt)):
      aae.addInstance(gt[i], p[i])
    target = 6.0
    self.assertTrue(abs(aae.getMetric()["value"]-target) < OPFMetricsTest.DELTA)


  def testTrivialAAE(self):
    trivialaae = getModule(MetricSpec("trivial", None, None,
                {"verbosity" : OPFMetricsTest.VERBOSITY,"errorMetric":"aae"}))
    gt = [i/4+1 for i in range(100)]
    p = [i for i in range(100)]
    for i in xrange(len(gt)):
      trivialaae.addInstance(gt[i], p[i])
    target = .25
    self.assertTrue(abs(trivialaae.getMetric()["value"]-target) \
< OPFMetricsTest.DELTA)


  def testTrivialAccuracy(self):
    trivialaccuracy = getModule(MetricSpec("trivial", None, None,
                {"verbosity" : OPFMetricsTest.VERBOSITY,"errorMetric":"acc"}))
    gt = [str(i/4+1) for i in range(100)]
    p = [str(i) for i in range(100)]
    for i in xrange(len(gt)):
      trivialaccuracy.addInstance(gt[i], p[i])
    target = .75
    self.assertTrue(abs(trivialaccuracy.getMetric()["value"]-target) \
< OPFMetricsTest.DELTA)


  def testWindowedTrivialAAE (self):
    """Trivial Average Error metric test"""
    trivialAveErr = getModule(MetricSpec("trivial", None, None,
            {"verbosity" : OPFMetricsTest.VERBOSITY,"errorMetric":"avg_err"}))
    gt = [str(i/4+1) for i in range(100)]
    p = [str(i) for i in range(100)]
    for i in xrange(len(gt)):
      trivialAveErr.addInstance(gt[i], p[i])
    target = .25
    self.assertTrue(abs(trivialAveErr.getMetric()["value"]-target)\
< OPFMetricsTest.DELTA)


  def testWindowedTrivialAccuract(self):
    """Trivial AAE metric test"""
    trivialaae = getModule(MetricSpec("trivial", None, None,
    {"verbosity" : OPFMetricsTest.VERBOSITY, "window":100,"errorMetric":"aae"}))
    gt = [i/4+1 for i in range(1000)]
    p = [i for i in range(1000)]
    for i in xrange(len(gt)):
      trivialaae.addInstance(gt[i], p[i])
    target = .25
    self.assertTrue(abs(trivialaae.getMetric()["value"]-target) \
< OPFMetricsTest.DELTA)


  def testWindowedTrivialAccuracy(self):
    """Trivial Accuracy metric test"""
    trivialaccuracy = getModule(MetricSpec("trivial", None, None,
 {"verbosity" : OPFMetricsTest.VERBOSITY, "window":100,"errorMetric":"acc"}))
    gt = [str(i/4+1) for i in range(1000)]
    p = [str(i) for i in range(1000)]
    for i in xrange(len(gt)):
      trivialaccuracy.addInstance(gt[i], p[i])
    target = .75
    self.assertTrue(abs(trivialaccuracy.getMetric()["value"]-target)\
< OPFMetricsTest.DELTA)


  def testWindowedTrivialAverageError (self):
    """Trivial Average Error metric test"""
    trivialAveErr = getModule(MetricSpec("trivial", None, None,
{"verbosity" : OPFMetricsTest.VERBOSITY, "window":100,"errorMetric":"avg_err"}))
    gt = [str(i/4+1) for i in range(500, 1000)]
    p = [str(i) for i in range(1000)]
    for i in xrange(len(gt)):
      trivialAveErr.addInstance(gt[i], p[i])
    target = .25
    self.assertTrue(abs(trivialAveErr.getMetric()["value"]-target)\
< OPFMetricsTest.DELTA)


  def testMultistepAAE(self):
    """Multistep AAE metric test"""
    msp = getModule(MetricSpec("multiStep", None, None,
     {"verbosity" : OPFMetricsTest.VERBOSITY, "window":100, "errorMetric":"aae",
           "steps": 3}))
    
    # Make each ground truth 1 greater than the prediction
    gt = [i+1 for i in range(100)]
    p = [{3: {i: .7, 5: 0.3}} for i in range(100)]

    for i in xrange(len(gt)):
      msp.addInstance(gt[i], p[i])
    target = 1
    self.assertTrue(abs(msp.getMetric()["value"]-target) < OPFMetricsTest.DELTA)


  def testMultistepAAEMultipleSteps(self):
    """Multistep AAE metric test, predicting 2 different step sizes"""
    msp = getModule(MetricSpec("multiStep", None, None,
     {"verbosity" : OPFMetricsTest.VERBOSITY, "window":100, "errorMetric":"aae",
           "steps": [3,6]}))
    
    # Make each 3 step prediction +1 over ground truth and each 6 step
    # prediction +0.5 over ground truth
    gt = [i for i in range(100)]
    p = [{3: {i+1: .7, 5: 0.3},
          6: {i+0.5: .7, 5: 0.3}} for i in range(100)]

    for i in xrange(len(gt)):
      msp.addInstance(gt[i], p[i])
    target = 0.75  # average of +1 error and 0.5 error
    self.assertTrue(abs(msp.getMetric()["value"]-target) < OPFMetricsTest.DELTA)


  def testMultistepProbability(self):
    """Multistep with probabilities metric test"""
    msp = getModule(MetricSpec("multiStepProbability", None, None,
 {"verbosity" : OPFMetricsTest.VERBOSITY, "window":100, "errorMetric":"aae",
           "steps":3}))
    gt = [5 for i in range(1000)]
    p = [{3: {i: .3, 5: .7}} for i in range(1000)]
    for i in xrange(len(gt)):
      msp.addInstance(gt[i], p[i])
    #((999-5)(1000-5)/2-(899-5)(900-5)/2)*.3/100
    target = 283.35
    self.assertTrue(abs(msp.getMetric()["value"]-target) < OPFMetricsTest.DELTA)


  def testMultistepProbabilityMultipleSteps(self):
    """Multistep with probabilities metric test, predicting 2 different step
    sizes"""
    msp = getModule(MetricSpec("multiStepProbability", None, None,
          {"verbosity" : OPFMetricsTest.VERBOSITY, "window":100,
           "errorMetric":"aae", "steps": [1,3]}))
    gt = [5 for i in range(1000)]
    p = [{3: {i: .3, 5: .7},
          1: {5: 1.0}} for i in range(1000)]
    for i in xrange(len(gt)):
      msp.addInstance(gt[i], p[i])
    #(((999-5)(1000-5)/2-(899-5)(900-5)/2)*.3/100) / 2
    #  / 2 because the 1-step prediction is 100% accurate
    target = 283.35/2
    self.assertTrue(abs(msp.getMetric()["value"]-target) < OPFMetricsTest.DELTA)


  def testMovingMeanAbsoluteError(self):
    """Moving mean Average Absolute Error metric test"""
    movingMeanAAE = getModule(MetricSpec("moving_mean", None, None,
         {"verbosity" : OPFMetricsTest.VERBOSITY, "window":100, "mean_window":3,
             "errorMetric":"aae"}))
    gt = [i for i in range(890)]
    gt.extend([2*i for i in range(110)])
    p = [i for i in range(1000)]
    res = []
    for i in xrange(len(gt)):
      movingMeanAAE.addInstance(gt[i], p[i])
      res.append(movingMeanAAE.getMetric()["value"])
    self.assertTrue(max(res[1:890]) == 2.0)
    self.assertTrue(min(res[891:])>=4.0)
    target = 4.0
    self.assertTrue(abs(movingMeanAAE.getMetric()["value"]-target)\
< OPFMetricsTest.DELTA)


  def testMovingMeanRMSE(self):
    """Moving mean RMSE metric test"""
    movingMeanRMSE = getModule(MetricSpec("moving_mean", None, None,
         {"verbosity" : OPFMetricsTest.VERBOSITY, "window":100, "mean_window":3,
          "errorMetric":"rmse"}))
    gt = [i for i in range(890)]
    gt.extend([2*i for i in range(110)])
    p = [i for i in range(1000)]
    res = []
    for i in xrange(len(gt)):
      movingMeanRMSE.addInstance(gt[i], p[i])
      res.append(movingMeanRMSE.getMetric()["value"])
    self.assertTrue(max(res[1:890]) == 2.0)
    self.assertTrue(min(res[891:])>=4.0)
    target = 4.0
    self.assertTrue(abs(movingMeanRMSE.getMetric()["value"]-target) \
< OPFMetricsTest.DELTA)


  def testMovingModeAverageError(self):
    """Moving mode Average Error metric test"""
    movingModeAvgErr = getModule(MetricSpec("moving_mode", None, None,
      {"verbosity" : OPFMetricsTest.VERBOSITY, "window":100, "mode_window":3,
           "errorMetric":"avg_err"}))
    #Should initially assymptote to .5
    #Then after 900 should go to 1.0 as the predictions will always be offset
    gt = [i/4 for i in range(900)]
    gt.extend([2*i/4 for i in range(100)])
    p = [i for i in range(1000)]
    res = []
    for i in xrange(len(gt)):
      movingModeAvgErr.addInstance(gt[i], p[i])
      res.append(movingModeAvgErr.getMetric()["value"])
    #Make sure that there is no point where the average error is >.5
    self.assertTrue(max(res[1:890]) == .5)
    #Make sure that after the statistics switch the error goes to 1.0
    self.assertTrue(min(res[891:])>=.5)
    #Make sure that the statistics change is still noticeable while it is
    #in the window
    self.assertTrue(res[998]<1.0)
    target = 1.0
    self.assertTrue(abs(movingModeAvgErr.getMetric()["value"]-target)\
< OPFMetricsTest.DELTA)


  def testMovingModeAccuracy(self):
    """Moving mode Accuracy metric test"""
    movingModeACC = getModule(MetricSpec("moving_mode", None, None,
       {"verbosity" : OPFMetricsTest.VERBOSITY, "window":100, "mode_window":3,
        "errorMetric":"acc"}))
    #Should initially asymptote to .5
    #Then after 900 should go to 0.0 as the predictions will always be offset
    gt = [i/4 for i in range(900)]
    gt.extend([2*i/4 for i in range(100)])
    p = [i for i in range(1000)]
    res = []
    for i in xrange(len(gt)):
      movingModeACC.addInstance(gt[i], p[i])
      res.append(movingModeACC.getMetric()["value"])
    #Make sure that there is no point where the average acc is <.5
    self.assertTrue(min(res[1:899]) == .5)
    #Make sure that after the statistics switch the acc goes to 0.0
    self.assertTrue(max(res[900:])<=.5)
    #Make sure that the statistics change is still noticeable while it
    #is in the window
    self.assertTrue(res[998]>0.0)
    target = 0.0
    self.assertTrue(abs(movingModeACC.getMetric()["value"]-target)\
< OPFMetricsTest.DELTA)


  def testTwoGramScalars(self):
    """Two gram scalars test"""
    oneGram = getModule(MetricSpec("two_gram", None, None,
{"verbosity" : OPFMetricsTest.VERBOSITY, \
"window":100, "predictionField":"test",
               "errorMetric":"acc"}))

    # Sequences of 0,1,2,3,4,0,1,2,3,4,...
    encodings = [np.zeros(10) for i in range(5)]
    for i in range(len(encodings)):
      encoding = encodings[i]
      encoding[i] = 1
    gt = [i%5 for i in range(1000)]
    res = []
    for i in xrange(len(gt)):
      if i == 20:
        # Make sure we don"t barf with missing values
        oneGram.addInstance(np.zeros(10), prediction=None,
record={"test":None})
      else:
        # Feed in next groundTruth
        oneGram.addInstance(encodings[i%5], prediction=None,
record={"test":gt[i]})
      res.append(oneGram.getMetric()["value"])
    target = 1.0
    self.assertTrue(abs(oneGram.getMetric()["value"]-target)\
< OPFMetricsTest.DELTA)


  def testTwoGramScalarsStepsGreaterOne(self):
    """Two gram scalars test with step size other than 1"""
    oneGram = getModule(MetricSpec("two_gram", None, None,
              {"verbosity" : OPFMetricsTest.VERBOSITY,\
"window":100, "predictionField":"test",
               "errorMetric":"acc", "steps": 2}))

    # Sequences of 0,1,2,3,4,0,1,2,3,4,...
    encodings = [np.zeros(10) for i in range(5)]
    for i in range(len(encodings)):
      encoding = encodings[i]
      encoding[i] = 1
    gt = [i%5 for i in range(1000)]
    res = []
    for i in xrange(len(gt)):
      if i == 20:
        # Make sure we don"t barf with missing values
        oneGram.addInstance(np.zeros(10), prediction=None,
record={"test":None})
      else:
        # Feed in next groundTruth
        oneGram.addInstance(encodings[i%5], prediction=None,
record={"test":gt[i]})
      res.append(oneGram.getMetric()["value"])
    target = 1.0
    self.assertTrue(abs(oneGram.getMetric()["value"]-target) \
< OPFMetricsTest.DELTA)


  def testTwoGramStrings(self):
    """One gram string test"""
    oneGram = getModule(MetricSpec("two_gram", None, None,
    {"verbosity" : OPFMetricsTest.VERBOSITY, "window":100, "errorMetric":"acc",
           "predictionField":"test"}))

    # Sequences of "0", "1", "2", "3", "4", "0", "1", ...
    gt = [str(i%5) for i in range(1000)]
    encodings = [np.zeros(10) for i in range(5)]
    for i in range(len(encodings)):
      encoding = encodings[i]
      encoding[i] = 1

    # Make every 5th element random
    newElem = 100
    for i in range(5, 1000, 5):
      gt[i] = str(newElem)
      newElem += 20

    res = []
    for i in xrange(len(gt)):
      if i==20:
        # Make sure we don"t barf with missing values
        oneGram.addInstance(np.zeros(10), prediction=None,
record={"test":None})
      else:
        oneGram.addInstance(encodings[i%5], prediction=None,
record={"test":gt[i]})
      res.append(oneGram.getMetric()["value"])
    target = .8
    self.assertTrue(abs(oneGram.getMetric()["value"]-target)\
< OPFMetricsTest.DELTA)


  def testWindowedAAE(self):
    """Windowed AAE"""
    waae = getModule(MetricSpec("aae", None, None,
{"verbosity" : OPFMetricsTest.VERBOSITY, "window":1}))
    gt = [9, 4, 5, 6]
    p = [0, 13, 8, 3]
    for i in xrange(len(gt)):
      waae.addInstance(gt[i], p[i])
    target = 3.0
    self.assertTrue( abs(waae.getMetric()["value"]-target) \
< OPFMetricsTest.DELTA, "Got %s" %waae.getMetric())


  def testAccuracy(self):
    """Accuracy"""
    acc = getModule(MetricSpec("acc", None, None,
{"verbosity" : OPFMetricsTest.VERBOSITY}))
    gt = [0, 1, 2, 3, 4, 5]
    p = [0, 1, 2, 4, 5, 6]
    for i in xrange(len(gt)):
      acc.addInstance(gt[i], p[i])
    target = 0.5
    self.assertTrue(abs(acc.getMetric()["value"]-target) < OPFMetricsTest.DELTA)


  def testWindowedAccuracy(self):
    """Windowed accuracy"""
    acc = getModule(MetricSpec("acc", None, None, \
{"verbosity" : OPFMetricsTest.VERBOSITY,  "window":2}))
    gt = [0, 1, 2, 3, 4, 5]
    p = [0, 1, 2, 4, 5, 6]
    for i in xrange(len(gt)):
      acc.addInstance(gt[i], p[i])
    target = 0.0

    self.assertTrue(abs(acc.getMetric()["value"]-target) < OPFMetricsTest.DELTA)


  def testAverageError(self):
    """Ave Error"""
    err = getModule(MetricSpec("avg_err", None, None,
{"verbosity" : OPFMetricsTest.VERBOSITY}))
    gt = [1, 1, 2, 3, 4, 5]
    p = [0, 1, 2, 4, 5, 6]
    for i in xrange(len(gt)):
      err.addInstance(gt[i], p[i])
    target = (2.0/3.0)
    self.assertTrue(abs(err.getMetric()["value"]-target) < OPFMetricsTest.DELTA)


  def testWindowedAverageError(self):
    """Windowed Ave Error"""
    err = getModule(MetricSpec("avg_err", None, None, \
{"verbosity" : OPFMetricsTest.VERBOSITY, "window":2}))
    gt = [0, 1, 2, 3, 4, 5]
    p = [0, 1, 2, 4, 5, 6]
    for i in xrange(len(gt)):
      err.addInstance(gt[i], p[i])
    target = 1.0

    self.assertTrue(abs(err.getMetric()["value"]-target) < OPFMetricsTest.DELTA)


  def testLongWindowRMSE(self):
    """RMSE"""
    rmse = getModule(MetricSpec("rmse", None, None,
{"verbosity" : OPFMetricsTest.VERBOSITY, "window":100}))
    gt = [9, 4, 5, 6]
    p = [0, 13, 8, 3]
    for i in xrange(len(gt)):
      rmse.addInstance(gt[i], p[i])
    target = 6.71

    self.assertTrue(abs(rmse.getMetric()["value"]-target)\
< OPFMetricsTest.DELTA)


  def testNegativeLogLikelihood(self):
    # make sure negativeLogLikelihood returns correct LL numbers

    # mock objects for ClassifierInput and ModelResult (see opfutils.py)
    class MockClassifierInput(object):
      def __init__(self, bucketIdx):
        self.bucketIndex = bucketIdx

    class MockModelResult(object):
      def __init__(self, bucketll, bucketIdx):
        self.inferences = {'multiStepBucketLikelihoods': {1: bucketll}}
        self.classifierInput = MockClassifierInput(bucketIdx)


    bucketLL = {0: 1.0, 1: 0, 2: 0, 3: 0} # model prediction as a dictionary
    gt_bucketIdx = 0 # bucket index for ground truth
    negLL = getModule(MetricSpec("negativeLogLikelihood", None, None,
                                {"verbosity" : OPFMetricsTest.VERBOSITY}))
    negLL.addInstance(0, 0, record = None,
                      result=MockModelResult(bucketLL, gt_bucketIdx))
    target = 0.0 # -log(1.0)
    self.assertAlmostEqual(negLL.getMetric()["value"], target)

    bucketLL = {0: 0.5, 1: 0.5, 2: 0, 3: 0} # model prediction as a dictionary
    gt_bucketIdx = 0 # bucket index for ground truth
    negLL = getModule(MetricSpec("negativeLogLikelihood", None, None,
                                {"verbosity" : OPFMetricsTest.VERBOSITY}))
    negLL.addInstance(0, 0, record = None,
                      result=MockModelResult(bucketLL, gt_bucketIdx))
    target = 0.6931471 # -log(0.5)
    self.assertTrue(abs(negLL.getMetric()["value"]-target)
                    < OPFMetricsTest.DELTA)

    # test accumulated negLL for multiple steps
    bucketLL = []
    bucketLL.append({0: 1, 1: 0, 2: 0, 3: 0})
    bucketLL.append({0: 0, 1: 1, 2: 0, 3: 0})
    bucketLL.append({0: 0, 1: 0, 2: 1, 3: 0})
    bucketLL.append({0: 0, 1: 0, 2: 0, 3: 1})

    gt_bucketIdx = [0, 2, 1, 3]
    negLL = getModule(MetricSpec("negativeLogLikelihood", None, None,
                                {"verbosity" : OPFMetricsTest.VERBOSITY}))
    for i in xrange(len(bucketLL)):
      negLL.addInstance(0, 0, record = None,
                        result=MockModelResult(bucketLL[i], gt_bucketIdx[i]))
    target = 5.756462
    self.assertTrue(abs(negLL.getMetric()["value"]-target)
                    < OPFMetricsTest.DELTA)


  def testNegLLMultiplePrediction(self):
    # In cases where the ground truth has multiple possible outcomes, make sure
    # that the prediction that captures ground truth distribution has best LL
    # and models that gives single prediction (either most likely outcome or
    # average outcome) has worse LL

    # mock objects for ClassifierInput and ModelResult (see opfutils.py)
    class MockClassifierInput(object):
      def __init__(self, bucketIdx):
        self.bucketIndex = bucketIdx

    class MockModelResult(object):
      def __init__(self, bucketll, bucketIdx):
        self.inferences = {'multiStepBucketLikelihoods': {1: bucketll}}
        self.classifierInput = MockClassifierInput(bucketIdx)

    # the ground truth lies in bucket 0 with p=0.45, in bucket 1 with p=0.0
    # and in bucket 2 with p=0.55
    gt_bucketIdx = [0]*45+[2]*55

    # compare neg log-likelihood for three type of model predictions
    # a model that predicts ground truth distribution
    prediction_gt = {0: 0.45, 1: 0, 2: 0.55}

    # a model that predicts only the most likely outcome
    prediction_ml = {0: 0.0, 1: 0, 2: 1.0}

    # a model that only predicts mean (bucket 1)
    prediction_mean = {0: 0, 1: 1, 2: 0}

    negLL_gt = getModule(MetricSpec("negativeLogLikelihood", None, None,
                                {"verbosity" : OPFMetricsTest.VERBOSITY}))
    negLL_ml = getModule(MetricSpec("negativeLogLikelihood", None, None,
                                {"verbosity" : OPFMetricsTest.VERBOSITY}))
    negLL_mean = getModule(MetricSpec("negativeLogLikelihood", None, None,
                                {"verbosity" : OPFMetricsTest.VERBOSITY}))
    for i in xrange(len(gt_bucketIdx)):
      negLL_gt.addInstance(0, 0, record = None,
                        result=MockModelResult(prediction_gt, gt_bucketIdx[i]))
      negLL_ml.addInstance(0, 0, record = None,
                        result=MockModelResult(prediction_ml, gt_bucketIdx[i]))
      negLL_mean.addInstance(0, 0, record = None,
                        result=MockModelResult(prediction_mean, gt_bucketIdx[i]))

    self.assertTrue(negLL_gt.getMetric()["value"] < negLL_ml.getMetric()["value"])
    self.assertTrue(negLL_gt.getMetric()["value"] < negLL_mean.getMetric()["value"])


  def testCustomErrorMetric(self):
    customFunc = """def getError(pred,ground,tools):
                      return abs(pred-ground)"""

    customEM = getModule(MetricSpec("custom_error_metric", None, None,
{"customFuncSource":customFunc, "errorWindow":3}))
    gt = [9, 4, 5, 6]
    p = [0, 13, 8, 3]
    for i in xrange(len(gt)):
      aggErr = customEM.addInstance(gt[i], p[i])
    target = 5.0
    delta = 0.001

    # insure that addInstance returns the aggregate error - other
    # uber metrics depend on this behavior.
    self.assertEqual(aggErr, customEM.getMetric()["value"])
    self.assertTrue(abs(customEM.getMetric()["value"]-target) < delta)

    customFunc = """def getError(pred,ground,tools):
        sum = 0
        for i in range(min(3,tools.getBufferLen())):
          sum+=abs(tools.getPrediction(i)-tools.getGroundTruth(i))
        return sum/3"""

    customEM = getModule(MetricSpec("custom_error_metric", None, None,
{"customFuncSource":customFunc}))
    gt = [9, 4, 5, 6]
    p = [0, 13, 8, 3]
    for i in xrange(len(gt)):
      customEM.addInstance(gt[i], p[i])
    target = 5.0
    delta = 0.001
    self.assertTrue(abs(customEM.getMetric()["value"]-target) < delta)

    # Test custom error metric helper functions
    # Test getPrediction
    # Not-Windowed
    storeWindow=4
    failed = False
    for lookBack in range(3):
      customFunc = """def getError(pred,ground,tools):
          return tools.getPrediction(%d)""" % lookBack

      customEM = getModule(MetricSpec("custom_error_metric", None, None,
{"customFuncSource":customFunc}))
      gt = [i for i in range(100)]
      p = [2*i for i in range(100)]
      t1 = [3*i for i in range(100)]
      t2 = [str(4*i) for i in range(100)]

      for i in xrange(len(gt)):
        curRecord = {"pred":p[i], "ground":gt[i], "test1":t1[i], "test2":t2[i]}
        if i < lookBack:
          try:
            customEM.addInstance(gt[i], p[i], curRecord)
            failed = True
          except:
            self.assertTrue( not failed,
"An exception should have been generated, but wasn't")
        else:
          customEM.addInstance(gt[i], p[i], curRecord)
          self.assertTrue( customEM.getMetric()["value"] == p[i-lookBack])
    #Windowed
    for lookBack in range(5):
      customFunc = """def getError(pred,ground,tools):
          return tools.getPrediction(%d)""" % lookBack

      customEM = getModule(MetricSpec("custom_error_metric", None, None,
{"customFuncSource":customFunc,"storeWindow":storeWindow}))
      gt = [i for i in range(100)]
      p = [2*i for i in range(100)]
      t1 = [3*i for i in range(100)]
      t2 = [str(4*i) for i in range(100)]

      for i in xrange(len(gt)):
        curRecord = {"pred":p[i], "ground":gt[i], "test1":t1[i], "test2":t2[i]}
        if lookBack>=storeWindow-1:
          pass
        if i < lookBack or lookBack>=storeWindow:
          try:
            customEM.addInstance(gt[i], p[i], curRecord)
            failed = True
          except:
            self.assertTrue (not failed ,
"An exception should have been generated, but wasn't")
        else:
          customEM.addInstance(gt[i], p[i], curRecord)
          self.assertTrue (customEM.getMetric()["value"] == p[i-lookBack])

    #Test getGroundTruth
    #Not-Windowed
    for lookBack in range(3):
      customFunc = """def getError(pred,ground,tools):
          return tools.getGroundTruth(%d)""" % lookBack

      customEM = getModule(MetricSpec("custom_error_metric", None, None,
{"customFuncSource":customFunc}))
      gt = [i for i in range(100)]
      p = [2*i for i in range(100)]
      t1 = [3*i for i in range(100)]
      t2 = [str(4*i) for i in range(100)]

      for i in xrange(len(gt)):
        curRecord = {"pred":p[i], "ground":gt[i], "test1":t1[i], "test2":t2[i]}
        if i < lookBack:
          try:
            customEM.addInstance(gt[i], p[i], curRecord)
            failed = True
          except:
            self.assertTrue( not failed ,
"An exception should have been generated, but wasn't")
        else:
          customEM.addInstance(gt[i], p[i], curRecord)
          self.assertTrue (customEM.getMetric()["value"] == gt[i-lookBack])
    #Windowed
    for lookBack in range(5):
      customFunc = """def getError(pred,ground,tools):
          return tools.getGroundTruth(%d)""" % lookBack

      customEM = getModule(MetricSpec("custom_error_metric", None, None,
{"customFuncSource":customFunc,"storeWindow":storeWindow}))
      gt = [i for i in range(100)]
      p = [2*i for i in range(100)]
      t1 = [3*i for i in range(100)]
      t2 = [str(4*i) for i in range(100)]

      for i in xrange(len(gt)):
        curRecord = {"pred":p[i], "ground":gt[i], "test1":t1[i], "test2":t2[i]}
        if i < lookBack or lookBack>=storeWindow:
          try:
            customEM.addInstance(gt[i], p[i], curRecord)
            failed = True
          except:
            self.assertTrue( not failed ,
"An exception should have been generated, but wasn't")
        else:
          customEM.addInstance(gt[i], p[i], curRecord)
          self.assertTrue( customEM.getMetric()["value"] == gt[i-lookBack])

    #Test getFieldValue
    #Not-Windowed Scalar
    for lookBack in range(3):
      customFunc = """def getError(pred,ground,tools):
          return tools.getFieldValue(%d,"test1")""" % lookBack

      customEM = getModule(MetricSpec("custom_error_metric", None, None,
{"customFuncSource":customFunc}))
      gt = [i for i in range(100)]
      p = [2*i for i in range(100)]
      t1 = [3*i for i in range(100)]
      t2 = [str(4*i) for i in range(100)]

      for i in xrange(len(gt)):
        curRecord = {"pred":p[i], "ground":gt[i], "test1":t1[i], "test2":t2[i]}
        if i < lookBack:
          try:
            customEM.addInstance(gt[i], p[i], curRecord)
            failed = True
          except:
            self.assertTrue( not failed ,
"An exception should have been generated, but wasn't")
        else:
          customEM.addInstance(gt[i], p[i], curRecord)
          self.assertTrue (customEM.getMetric()["value"] == t1[i-lookBack])
    #Windowed Scalar
    for lookBack in range(3):
      customFunc = """def getError(pred,ground,tools):
          return tools.getFieldValue(%d,"test1")""" % lookBack

      customEM = getModule(MetricSpec("custom_error_metric", None, None,
{"customFuncSource":customFunc,"storeWindow":storeWindow}))
      gt = [i for i in range(100)]
      p = [2*i for i in range(100)]
      t1 = [3*i for i in range(100)]
      t2 = [str(4*i) for i in range(100)]

      for i in xrange(len(gt)):
        curRecord = {"pred":p[i], "ground":gt[i], "test1":t1[i], "test2":t2[i]}
        if i < lookBack or lookBack>=storeWindow:
          try:
            customEM.addInstance(gt[i], p[i], curRecord)
            failed = True
          except:
            self.assertTrue (not failed ,
"An exception should have been generated, but wasn't")
        else:
          customEM.addInstance(gt[i], p[i], curRecord)
          self.assertTrue( customEM.getMetric()["value"] == t1[i-lookBack])
    #Not-Windowed category
    for lookBack in range(3):
      customFunc = """def getError(pred,ground,tools):
          return tools.getFieldValue(%d,"test1")""" % lookBack

      customEM = getModule(MetricSpec("custom_error_metric", None, None,
{"customFuncSource":customFunc}))
      gt = [i for i in range(100)]
      p = [2*i for i in range(100)]
      t1 = [3*i for i in range(100)]
      t2 = [str(4*i) for i in range(100)]

      for i in xrange(len(gt)):
        curRecord = {"pred":p[i], "ground":gt[i], "test1":t1[i], "test2":t2[i]}
        if i < lookBack:
          try:
            customEM.addInstance(gt[i], p[i], curRecord)
            failed = True
          except:
            self.assertTrue( not failed ,
"An exception should have been generated, but wasn't")
        else:
          customEM.addInstance(gt[i], p[i], curRecord)
          self.assertTrue (customEM.getMetric()["value"] == t1[i-lookBack])

    #Windowed category
    for lookBack in range(3):
      customFunc = """def getError(pred,ground,tools):
          return tools.getFieldValue(%d,"test1")""" % lookBack

      customEM = getModule(MetricSpec("custom_error_metric", None, None,
{"customFuncSource":customFunc,"storeWindow":storeWindow}))
      gt = [i for i in range(100)]
      p = [2*i for i in range(100)]
      t1 = [3*i for i in range(100)]
      t2 = [str(4*i) for i in range(100)]

      for i in xrange(len(gt)):
        curRecord = {"pred":p[i], "ground":gt[i], "test1":t1[i], "test2":t2[i]}
        if i < lookBack or lookBack>=storeWindow:
          try:
            customEM.addInstance(gt[i], p[i], curRecord)
            failed = True
          except:
            self.assertTrue (not failed ,
"An exception should have been generated, but wasn't")
        else:
          customEM.addInstance(gt[i], p[i], curRecord)
          self.assertTrue (customEM.getMetric()["value"] == t1[i-lookBack])
    #Test getBufferLen
    #Not-Windowed
    customFunc = """def getError(pred,ground,tools):
        return tools.getBufferLen()"""

    customEM = getModule(MetricSpec("custom_error_metric", None, None,
{"customFuncSource":customFunc}))
    gt = [i for i in range(100)]
    p = [2*i for i in range(100)]
    t1 = [3*i for i in range(100)]
    t2 = [str(4*i) for i in range(100)]

    for i in xrange(len(gt)):
      curRecord = {"pred":p[i], "ground":gt[i], "test1":t1[i], "test2":t2[i]}
      customEM.addInstance(gt[i], p[i], curRecord)
      self.assertTrue (customEM.getMetric()["value"] == i+1)
    #Windowed
    customFunc = """def getError(pred,ground,tools):
        return tools.getBufferLen()"""

    customEM = getModule(MetricSpec("custom_error_metric", None, None,
{"customFuncSource":customFunc,"storeWindow":storeWindow}))
    gt = [i for i in range(100)]
    p = [2*i for i in range(100)]
    t1 = [3*i for i in range(100)]
    t2 = [str(4*i) for i in range(100)]

    for i in xrange(len(gt)):
      curRecord = {"pred":p[i], "ground":gt[i], "test1":t1[i], "test2":t2[i]}
      customEM.addInstance(gt[i], p[i], curRecord)
      self.assertTrue (customEM.getMetric()["value"] == min(i+1, 4))



    #Test initialization edge cases
    try:
      customEM = getModule(MetricSpec("custom_error_metric", None, None,
{"customFuncSource":customFunc,"errorWindow":0}))
      self.assertTrue (False , "error Window of 0 should fail self.assertTrue")
    except:
      pass

    try:
      customEM = getModule(MetricSpec("custom_error_metric", None, None,
{"customFuncSource":customFunc,"storeWindow":0}))
      self.assertTrue (False , "error Window of 0 should fail self.assertTrue")
    except:
      pass


  def testMultiMetric(self):
    ms1 = MetricSpec(field='a', metric='trivial',  inferenceElement='prediction', params={'errorMetric': 'aae', 'window': 1000, 'steps': 1})
    ms2 = MetricSpec(metric='trivial', inferenceElement='prediction', field='a', params={'window': 10, 'steps': 1, 'errorMetric': 'rmse'})
    metric1000 = getModule(ms1)
    metric10 = getModule(ms2)
    # create multi metric
    multi = MetricMulti(weights=[0.2, 0.8], metrics=[metric10, metric1000])
    multi.verbosity = 1
    # create reference metrics (must be diff from metrics above used in MultiMetric, as they keep history)
    metric1000ref = getModule(ms1)
    metric10ref = getModule(ms2)

    
    gt = range(500, 1000)
    p = range(500)
 
    for i in xrange(len(gt)):
      v10=metric10ref.addInstance(gt[i], p[i])
      v1000=metric1000ref.addInstance(gt[i], p[i])
      if v10 is None or v1000 is None:
        check=None
      else:
        check=0.2*float(v10) + 0.8*float(v1000)
      metricValue = multi.addInstance(gt[i], p[i])
      self.assertEqual(check, metricValue, "iter i= %s gt=%s pred=%s multi=%s sub1=%s sub2=%s" % (i, gt[i], p[i], metricValue, v10, v1000))



if __name__ == "__main__":
  unittest.main()
