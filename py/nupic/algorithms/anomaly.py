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

"""Anomaly-related algorithms."""

import numpy

from nupic.algorithms.anomaly_likelihood import AnomalyLikelihood

class Anomaly(object):
  """basic class that computes anomaly"""

  
  def __init__(self, useTP = None, slidingWindowSize = None, useProbLikelihood = False):
    """
    @param (optional) useTP -- tp temporal pooler instance used
    @param (optional) slidingWindowSize -- how many elements are summed up, sliding window size
    @param (optional) useProbLikelihood -- TODO subutai's code for likelihood prob distribution anomaly
    """
    # using TP
    self._tp = useTP
    if self._tp is not None:
      self._prevPredictedColumns = numpy.array([])
    # using cumulative anomaly , sliding window
    self._windowSize = slidingWindowSize
    if self._windowSize is not None:
      self._buf = numpy.array([0] * self._windowSize, dtype=numpy.float)
      self._i = 0
    # probabilistic anomaly
    self._useLikelihood = useProbLikelihood
    if useProbLikelihood:
      self._likelihood = AnomalyLikelihood()


  def computeAnomalyScore(self, activeColumns, prevPredictedColumnsi, value=None, timestamp=None):
    """Compute the anomaly score as the percent of active columns not predicted.
  
    @param activeColumns: array of active column indices
    @param prevPredictedColumns: array of columns indices predicted in previous step (ignored with useTP != None)
    @param value: (optional) input value, that is what activeColumns represent; used in anomaly-likelihood
    @param timestamp: (optional) date timestamp when the sample occured; used in anomaly-likelihood
    @return the computed anomaly score; float 0..1
    """

    # using TP provided during init, _prevPredColumns stored internally here
    if self._tp is not None:
      prevPredictedColumns = self._prevPredictedColumns # override the values passed by parameter with the stored value
      self._prevPredictedColumns = self._tp.getOutputData("topDownOut").nonzero()[0] 

    # 1. here is the 'classic' anomaly score
    anomalyScore = Anomaly._pureAnomaly(activeColumns, prevPredictedColumns)

    # use probabilistic anomaly 
    if self._useLikelihood:
      probability = self._likelihood.anomalyProbability(value, anomalyScore, timestamp)
      anomalyScore = probability

    # 3. score is cumulative score over windowSize
    if self._windowSize is not None:
      anomalyScore = self._movingAverage(anomalyScore)

    return anomalyScore


  def _movingAverage(self, newElement=None)
    """moving average

    @param newValue (optional) add a new element before computing the avg
    @return moving average of self._windowSize last elements
    """
    if self._windowSize is None:
      raise RuntimeError("Moving average has not been enabled during __init__ (self._windowSize not set)")
    if newElement is not None:
      self._buf[self._i]= newElement
#debug      print "buf="+str(self._buf)+"  i="+str(self._i)+" score="+str(score)
      self._i = (self._i + 1) % self._windowSize
    return self._buf.sum()/float(self._windowSize) # normalize to 0..1

  @staticmethod
  def _pureAnomaly(activeColumns, prevPredictedColumns)
    """the pure anomaly score 

    computed as diff of current active columns and columns predicted from previous round
    @param activeColumns: array of active column indices
    @param prevPredictedColumns: array of columns indices predicted in previous step
    @return anomaly score 0..1 (float)
    """
    nActiveColumns = len(activeColumns)
    if nActiveColumns > 0:
      # Test whether each element of a 1-D array is also present in a second
      # array. Sum to get the total # of columns that are active and were
      # predicted.
      score = numpy.sum(numpy.in1d(activeColumns, prevPredictedColumns))
      # Get the percent of active columns that were NOT predicted, that is
      # our anomaly score.
      score = (nActiveColumns - score) / float(nActiveColumns)
    elif len(prevPredictedColumns) > 0:
      # There were predicted columns but none active.
      score = 1.0
    else:
      # There were no predicted or active columns.
      score = 0.0
    return score
