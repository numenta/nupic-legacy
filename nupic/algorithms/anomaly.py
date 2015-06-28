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
from nupic.utils import MovingAverage


def computeRawAnomalyScore(activeColumns, prevPredictedColumns):
  """Computes the raw anomaly score.

  The raw anomaly score is the fraction of active columns not predicted.

  If all columns were predicted at previous time step (prevPredictedColumns) 
  then the score will be zero regardless of which columns, if any, 
  are active currently (activeColumns).

  @param activeColumns: array of active column indices
  @param prevPredictedColumns: array of columns indices predicted in prev step
  @return anomaly score [0..1] (float)

  This is the "original" computeRawAnomalyScore() implementation.
  """
  nActiveColumns = len(activeColumns)
  if nActiveColumns > 0:
    # Test whether each element of a 1-D array is also present in a second
    # array. Sum to get the total # of columns that are active and were
    # predicted.
    score = numpy.in1d(activeColumns, prevPredictedColumns).sum()
    # Get the percent of active columns that were NOT predicted, that is
    # our anomaly score.
    score = (nActiveColumns - score) / float(nActiveColumns)
  else:
    # There are no active columns.
    score = 0.0

  return score



class Anomaly(object):
  """Utility class for generating anomaly scores in different ways.

  Supported modes:
    MODE_PURE - the raw anomaly score as computed by computeRawAnomalyScore
    MODE_LIKELIHOOD - uses the AnomalyLikelihood class on top of the raw
        anomaly scores
    MODE_WEIGHTED - multiplies the likelihood result with the raw anomaly score
        that was used to generate the likelihood
    MODE_CUSTOM - user defined callable used in compute()
  """

  # anomaly modes supported
  MODE_PURE = "pure"
  MODE_LIKELIHOOD = "likelihood"
  MODE_WEIGHTED = "weighted"
  MODE_CUSTOM = "custom"
  supportedModes = (MODE_PURE, MODE_LIKELIHOOD, MODE_WEIGHTED, MODE_CUSTOM)
  

  def __init__(self, slidingWindowSize=None, 
                     mode=MODE_PURE, 
                     binaryAnomalyThreshold=None,
                     customComputeFn=None):
    """
    @param slidingWindowSize (optional) - how many elements are summed up;
        enables moving average on final anomaly score; int >= 0
    @param mode (optional) - (string) how to compute anomaly;
        possible values are:
          - Anomaly.MODE_PURE - the default, how much anomal the value is;
              float 0..1 where 1=totally unexpected
          - Anomaly.MODE_LIKELIHOOD - uses the anomaly_likelihood code;
              models probability of receiving this value and anomalyScore
          - Anomaly.MODE_WEIGHTED - "pure" anomaly weighted by "likelihood"
              (anomaly * likelihood)
          - Anomaly.MODE_CUSTOM - implies custom function will be provided 
                       and used directly to compute score
    @param binaryAnomalyThreshold (optional) - if set [0,1] anomaly score
         will be discretized to 1/0 (1 if >= binaryAnomalyThreshold)
         The transformation is applied after moving average is computed and updated.
    @param customComputeFn (optional) - required with mode="custom", a callable
                       used for user-defined anomaly computation.
                       Requirements on this callable are:
                         params:
                           activeColumns: array of active cols. indices
                           prevPredictedColumns: array of pred. cols. indices
                           inputValue: raw input (default=None) 
                           timestamp: (default=None)
                         return:
                           anomaly score: float [0..1]
                       @see description for compute() method for details
    """
    self._mode = mode
    self._likelihood = None
    self._movingAverage = None
    self._likelihood = None
    self._binaryThreshold = binaryAnomalyThreshold
    self._computeAnomaly = None

    # sliding window / moving average
    if slidingWindowSize is not None:
      self._movingAverage = MovingAverage(windowSize=slidingWindowSize)

    # binarization
    if binaryAnomalyThreshold is not None and ( 
          not isinstance(binaryAnomalyThreshold, float) or
          binaryAnomalyThreshold >= 1.0  or 
          binaryAnomalyThreshold <= 0.0 ):
      raise ValueError("Anomaly: binaryAnomalyThreshold must be from (0,1) "
                       "or None if disabled.")

    # switch and setup compute() based on mode
    self._registerCustomComputeFn(mode, customComputeFn)


  def _registerCustomComputeFn(self, mode, customComputeFn):
    """
    @param mode - name of the mode, eg Anomaly.MODE_PURE, ...
    @param customComputeFn - a callable use for custom compute() calls
    """
    if mode == Anomaly.MODE_CUSTOM:
      if callable(customComputeFn):
        self._computeAnomaly = customComputeFn
      else:
        raise ValueError("Anomaly: with mode='custom' a callable must be "
                         "provided as 'customComputeFn' param, but got %r" % 
                         (customComputeFn,))
    elif mode == Anomaly.MODE_PURE:
      self._computeAnomaly =  self._computeRaw
    elif mode == Anomaly.MODE_LIKELIHOOD:
      self._likelihood = AnomalyLikelihood() # probabilistic anomaly
      self._computeAnomaly = self._computeLikelihood
    elif mode == Anomaly.MODE_WEIGHTED:
      self._likelihood = AnomalyLikelihood() # probabilistic anomaly
      self._computeAnomaly = self._computeWeighted
    else:
      raise ValueError("Anomaly: mode has to be one of '%s' but is '%r' "
                         % (self.supportedModes, mode) )


  def compute(self, activeColumns, predictedColumns, 
			inputValue=None, timestamp=None):
    """Compute the anomaly score as the percent of active columns not predicted.

    @param activeColumns: array of active column indices
    @param predictedColumns: array of columns indices predicted in this step
                             (used for anomaly in step T+1)
    @param inputValue: (optional) value of current input to encoders 
				(eg "cat" for category encoder)
                              	(used in anomaly-likelihood)
    @param timestamp: (optional) date timestamp when the sample occured
                              	(used in anomaly-likelihood)
    @return the computed anomaly score; float 0..1
    """

    # Compute final anomaly based on selected mode.
    score = self._computeAnomaly(activeColumns, predictedColumns, inputValue, timestamp)

    # Last, do moving-average if windowSize was specified.
    if self._movingAverage is not None:
      score = self._movingAverage.next(score)

    # apply binary discretization if required
    if self._binaryThreshold is not None:
      if score >= self._binaryThreshold:
        score = 1.0
      else:
        score = 0.0

    return score


############################################
# implementations of compute() function
  def _computeRaw(self, active, prevPredicted, inputValue=None, timestamp=None):
    """
    compute anomaly score using the "classical" (raw) implementation.
    Used in mode Anomaly.MODE_PURE
    @see computeRawAnomalyScore for details and params
    """
    return computeRawAnomalyScore(active, prevPredicted)

  def _computeLikelihood(self, active, prevPredicted, inputValue, ts=None):
    """
    Anomaly computed using the anomaly_likelihood score, 
    which models probability of (input, anomalyScore) pair.
    Used in mode Anomaly.MODE_LIKELIHOOD
    @see compute() for parameters 
         and anomaly_likelihood.py file for functionality
    """
    assert isinstance(self._likelihood, AnomalyLikelihood)
    if inputValue is None:
      raise ValueError("Selected anomaly mode 'Anomaly.MODE_LIKELIHOOD' "
                       "requires 'inputValue' as parameter to compute() method. ")
    rawScore = computeRawAnomalyScore(active, prevPredicted)
    return self._likelihood.anomalyProbability(inputValue, rawScore, ts) # probability

  def _computeWeighted(self, active, prevPredicted, inputValue, timestamp=None):
    """
    Raw anomaly weighted by likelihood, 
    combination of "pure" and "likelihood" modes.
    Used in Anomaly.MODE_WEIGHTED
    @see compute() for parameters
    """
    prob = self._computeLikelihood(active, prevPredicted, inputValue, timestamp)
    raw = computeRawAnomalyScore(active, prevPredicted)
    return (raw * prob)


# support functions
  def __str__(self):
    windowSize = 0
    if self._movingAverage is not None:
      windowSize = self._movingAverage.windowSize
    return "Anomaly:\tmode=%s\twindowSize=%r" % (self._mode, windowSize)


  def __eq__(self, other):
    if not isinstance(other, Anomaly): 
      return False
    if (other._mode == self._mode and
        other._binaryThreshold == self._binaryThreshold and
        other._movingAverage == self._movingAverage and
        other._likelihood == self._likelihood):
      return True #equal
    else:
      return False


  def __setstate__(self, state):
    """deserialization"""
    self.__dict__.update(state)
    if not hasattr(self, '_mode'):
      self._mode = Anomaly.MODE_PURE
    if not hasattr(self, '_movingAverage'):
      self._movingAverage = None
    if not hasattr(self, '_binaryThreshold'):
      self._binaryThreshold = None
    if not hasattr(self, '_computeAnomaly'):
      self._registerCustomComputeFn(self._mode, None)


  def __getstate__(self):
    result = self.__dict__.copy()
    if result['_mode'] == Anomaly.MODE_CUSTOM:
      raise ValueError("Anomaly: cannot serialize custom compute functions provided.")
    del result['_computeAnomaly']
    return result
