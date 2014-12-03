#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
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

import numpy as np

import unittest2 as unittest

from nupic.frameworks.opf.metrics import getModule, MetricSpec



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



if __name__ == "__main__":
  unittest.main()
