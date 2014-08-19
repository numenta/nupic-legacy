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
import nupic

def computeRawAnomalyScore(activeColumns, prevPredictedColumns):
    """Computes the raw anomaly score.

    The raw anomaly score is the fraction of active columns not predicted.

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



class Anomaly(object):
  """basic class that computes anomaly"""


  # anomaly modes supported
  MODE_PURE = "pure"
  MODE_LIKELIHOOD = "likelihood"
  MODE_WEIGHTED = "weighted"
  _supportedModes = [MODE_PURE, MODE_LIKELIHOOD, MODE_WEIGHTED]


  def __init__(self, useTP = None, slidingWindowSize = None, anomalyMode="pure"):
    """
    @param (optional) useTP -- tp temporal pooler instance used
    @param (optional) slidingWindowSize -- enables moving average on final 
            anomaly score; how many elements are summed up, sliding window size; int >= 0
    @param (optional) anomalyMode -- (string) which way to use to compute anomaly; 
                      possible values are: 
                           -- "pure" -- the default, how much anomal the value is; 
                                        float 0..1 where 1=totally unexpected
                           -- "likelihood" -- uses the anomaly_likelihood code; 
                                        models probability of receiving this value and anomalyScore; 
                                        used in Grok
                           -- "weighted" -- "pure" anomaly weighted by "likelihood" (anomaly * likelihood)  
    """

    # using TP
    if useTP is not None and isinstance(useTP, nupic.frameworks.opf.clamodel.CLAModel):
      self._tp = useTP
      self._prevPredictedColumns = numpy.array([])
    elif useTP is not None:
      raise Exception("Anomaly: you've provided instance of TP, but it does not look as a correct temporal pooler object: "+str(type(useTP)))

    # using cumulative anomaly , sliding window
    if slidingWindowSize > 0:
      self._windowSize = slidingWindowSize
      self._buf = numpy.array([0] * self._windowSize, dtype=numpy.float) #sliding window buffer
      self._i = 0 # index pointer to actual position
    elif slidingWindowSize is not None:
      raise Exception("Anomaly: if you define slidingWindowSize, it has to be an integer > 0; slidingWindowSize="+str(slidingWindowSize))

    # mode
    self._mode = anomalyMode
    if self._mode == Anomaly.MODE_LIKELIHOOD:
      self._likelihood = AnomalyLikelihood() # probabilistic anomaly
    if not (self._mode in Anomaly._supportedModes):
      raise ValueError('Invalid anomaly mode; only supported modes are: "pure",\
                       "likelihood", "weighted"; you used:' +self._mode)



  def computeAnomalyScore(self, activeColumns, prevPredictedColumns, value=None, timestamp=None):
    """Compute the anomaly score as the percent of active columns not predicted.
  
    @param activeColumns: array of active column indices
    @param prevPredictedColumns: array of columns indices predicted in previous step (ignored with useTP != None)
    @param value: (optional) input value, that is what activeColumns represent; used in anomaly-likelihood
    @param timestamp: (optional) date timestamp when the sample occured; used in anomaly-likelihood
    @return the computed anomaly score; float 0..1
    """

    # using TP provided during init, _prevPredColumns stored internally here
    if hasattr(self, "_tp"):
      prevPredictedColumns = self._prevPredictedColumns # override the values passed by parameter with the stored value
      self._prevPredictedColumns = self._tp._getTPRegion().getOutputData("topDownOut").nonzero()[0] 

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

