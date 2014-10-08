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

  ####################################################################
  def testAnomalyWithLikelihood(self):
    """example use of anomaly and tests likelihood code"""
    from nupic.encoders.scalar import ScalarEncoder as DataEncoder
    from nupic.research.spatial_pooler import SpatialPooler
#    from nupic.bindings.algorithms import SpatialPooler
    from nupic.research.TP10X2 import TP as TemporalPooler
#    from nupic.research.TP import TP as TemporalPooler
    from nupic.algorithms.anomaly import Anomaly
    from nupic.bindings.math import GetNTAReal

    import numpy
    import math

    # init
    realType=GetNTAReal()
    encoder= DataEncoder(w=21, minval=0, maxval=9, resolution=0.1, forced=True)
    _numCols=10**2 # must be power of 2
    sp= SpatialPooler(inputDimensions=[encoder.getWidth()], columnDimensions=[_numCols])
    tp= TemporalPooler(numberOfCols=_numCols)#int(math.sqrt(_numCols)))
    an= Anomaly(mode=Anomaly.MODE_LIKELIHOOD)

    data=range(10)
    nTrainSPTP=70 # find minimal acceptable values (to speed up the test)
    nTrainLikelihood=50 # generally needs to be >=300 as it's a burn-in time for likelihood
    # ^^ or "hack" likelihood to use shorter time:
    an._likelihood._claLearningPeriod = 30
    an._likelihood._probationaryPeriod = 330
   
    # first, some training to stabilize patterns in SP, TP 
    for i in xrange(nTrainSPTP): # train the weights in SP, TP
      # run some data through the pipes
      for raw in data:
        encD=encoder.encode(raw)
        spD=numpy.zeros(_numCols)
        sp.compute(encD, True, spD) # learn
#        spD=sp.stripUnlearnedColumns(spD)
        spD=spD.nonzero()[0]
        spD=spD[spD>0.5]
        tpD=tp.compute(spD, enableLearn=True, computeInfOutput=True).nonzero()[0] # learn

    # now train the likelihood model
    for i in xrange(nTrainLikelihood):
      _prev=[]
      tpD=[]
      for raw in data:
        encD=encoder.encode(raw)
        spD=numpy.array([0]*_numCols, dtype=float)
        sp.compute(encD, False, spD)
        spD=spD.nonzero()[0]
        spD=spD[spD>0.5]
        _prev=tpD
        tpD=tp.compute(spD, enableLearn=False, computeInfOutput=True).nonzero()[0]
        anD=an.compute(tpD, _prev, inputValue=raw) # anomaly likelihood

    # evaluate 
    likely=range(10) # trained data -> high likelihood
    unlikely=numpy.random.randint(0,10,10) # random data -> low likelihood
    data= likely + unlikely.tolist()
    results=[]
    _prev=[]
    tpD=[]
    for raw in data:
      encD=encoder.encode(raw)
      spD=numpy.array([0]*_numCols, dtype=float)
      sp.compute(encD, False, spD)
      spD=spD.nonzero()[0]
      spD=spD[spD>0.5]
      _prev=tpD
      tpD=tp.compute(spD, enableLearn=False, computeInfOutput=True).nonzero()[0]
      
      anD=an.compute(tpD, _prev, inputValue=raw) # anomaly likelihood
      results.append(anD)
    #  print "------\ndata= %r\tanomaly=%r" % (raw, anD)
    #  print "ENC=", encD.nonzero()
    #  print "SP =", spD
    #  print "TP =", tpD

    # finally check results
    hi=sum(results[0:10])
    low=sum(results[11:20])
    # if the test below is failing, increase SP/likelihood training times, or reduce confidence
    self.assertTrue(low*3 <= hi, "low= %r, hi= %r" %(low, hi)) # at least 5x difference in likelihoods for known vs. unexpected data


    
if __name__ == "__main__":
  unittest.main()
