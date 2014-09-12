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

def computeRawAnomalyScore(activeColumns, prevPredictedColumns):
  """Computes the raw anomaly score.

  The raw anomaly score is difference between predicted and actual state: 
   = the fraction of active columns not predicted +
     the fraction of non-active columns predicted as active.

  computed as diff of current active columns and columns predicted from 
  previous round

  @param activeColumns: array of active column indices
  @param prevPredictedColumns: array of columns indices predicted in prev step
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



class Anomaly(object):
  """basic class that computes anomaly

     Anomaly is used to detect strange patterns/behaviors (outliners) 
     by a trained CLA model. 
  """



  # anomaly modes supported
  MODE_PURE = "pure"
  MODE_LIKELIHOOD = "likelihood"
  MODE_WEIGHTED = "weighted"
  _supportedModes = [MODE_PURE, MODE_LIKELIHOOD, MODE_WEIGHTED]


  def __init__(self, slidingWindowSize = None, anomalyMode=MODE_PURE, 
               shiftPredicted=False):
    """
    @param (optional) slidingWindowSize -- enables moving average on final 
                      anomaly score; how many elements are summed up, 
                      sliding window size; int >= 0
    @param (optional) anomalyMode -- (string) how to compute anomaly;
                      possible values are: 
                         -- "pure" -- the default, how much anomal the value is; 
                                      float 0..1 where 1=totally unexpected
                         -- "likelihood" -- uses the anomaly_likelihood code; 
                                      models probability of receiving this 
                                      value and anomalyScore; used in Grok
                         -- "weighted" -- "pure" anomaly weighted by "likelihood" (anomaly * likelihood)
    @param shiftPredicted (optional) -- boolean [default=False]; 
                                      normally active vs predicted are compared
                          if shiftPredicted=True: predicted(T-1) vs active(T) 
                             are compared (eg from TP, CLAModel)
    """

    # using cumulative anomaly , sliding window
    if slidingWindowSize > 0:
      self._windowSize = slidingWindowSize
      #sliding window buffer
      self._buf = numpy.array([0] * self._windowSize, dtype=numpy.float)
      self._i = 0 # index pointer to actual position
    elif slidingWindowSize is not None:
      raise Exception("Anomaly: if you define slidingWindowSize, \
      it has to be an integer > 0; \
      slidingWindowSize="+str(slidingWindowSize))

    # mode
    self._mode = anomalyMode
    if self._mode == Anomaly.MODE_LIKELIHOOD:
      self._likelihood = AnomalyLikelihood() # probabilistic anomaly
    if not self._mode in Anomaly._supportedModes:
      raise ValueError('Invalid anomaly mode; only supported modes are: \
                       "Anomaly.MODE_PURE", "Anomaly.MODE_LIKELIHOOD", \
                       "Anomaly.MODE_WEIGHTED"; you used:' +self._mode)

    if shiftPredicted:
      self._prevPredictedColumns = numpy.array([])


  def computeAnomalyScore(self, activeColumns, predictedColumns, value=None, 
                          timestamp=None):
    """Compute the anomaly score as the percent of active columns not predicted
  
    @param activeColumns: array of active column indices
    @param predictedColumns: array of columns indices predicted in this step 
                             (used for anomaly in step T+1)
    @param value: (optional) input value, that is what activeColumns represent
                              (used in anomaly-likelihood)
    @param timestamp: (optional) date timestamp when the sample occured 
                              (used in anomaly-likelihood)
    @return the computed anomaly score; float 0..1
    """

    if hasattr(self, "_prevPredictedColumns"): # shiftPredicted==True
      prevPredictedColumns = self._prevPredictedColumns
      self._prevPredictedColumns = predictedColumns # to be used in step T+1
    else:
      prevPredictedColumns = predictedColumns

    # 1. here is the 'classic' anomaly score
    anomalyScore = computeRawAnomalyScore(activeColumns, prevPredictedColumns)

    # compute final anomaly based on selected mode
    if self._mode == Anomaly.MODE_PURE:
      score = anomalyScore
    elif self._mode == Anomaly.MODE_LIKELIHOOD:
      probability = self._likelihood.anomalyProbability(value, anomalyScore, timestamp)
      score = probability
    elif self._mode == Anomaly.MODE_WEIGHTED:
      probability = self._likelihood.anomalyProbability(value, anomalyScore, timestamp)
      score = anomalyScore * probability

    # last, do moving-average if windowSize is set
    if hasattr(self, "_windowSize"):
      score = self._movingAverage(score)

    return score


  def _movingAverage(self, newElement=None):
    """moving average

    @param newValue (optional) add a new element before computing the avg
    @return moving average of self._windowSize last elements
    """
    if newElement is not None:
      self._buf[self._i]= newElement
      self._i = (self._i + 1) % self._windowSize
    return self._buf.sum()/float(self._windowSize) # normalize to 0..1

