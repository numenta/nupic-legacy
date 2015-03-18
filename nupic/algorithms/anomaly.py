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

  The implementation is using in1D() function, 
  "satisfied" means it only cares if activeColumns at time T have been 
  predicted at T-1. 

  Which means a temporal pooler TP with all columns in predictive state at T-1
  would have zero anomaly score at T for any active state. 

  @param activeColumns: array of active column indices
  @param prevPredictedColumns: array of columns indices predicted in prev step
  @return anomaly score 0..1 (float)

  This is the "original" computeRawAnomalyScore() implementation.

  This method is a placeholder for the default computeAnomalyScore() implementation.
  """
  return Anomaly.compute_In1D_Satisfied(activeColumns, prevPredictedColumns)



class Anomaly(object):
  """Utility class for generating anomaly scores in different ways.

  Supported modes:
    MODE_PURE - the raw anomaly score as computed by computeRawAnomalyScore
    MODE_LIKELIHOOD - uses the AnomalyLikelihood class on top of the raw
        anomaly scores
    MODE_WEIGHTED - multiplies the likelihood result with the raw anomaly score
        that was used to generate the likelihood
  """


  # anomaly modes supported
  MODE_PURE = "pure"
  MODE_LIKELIHOOD = "likelihood"
  MODE_WEIGHTED = "weighted"
  _supportedModes = (MODE_PURE, MODE_LIKELIHOOD, MODE_WEIGHTED)


  def __init__(self, slidingWindowSize=None, mode=MODE_PURE, binaryAnomalyThreshold=None):
    """
    @param slidingWindowSize (optional) - how many elements are summed up;
        enables moving average on final anomaly score; int >= 0
    @param mode (optional) - (string) how to compute anomaly;
        possible values are:
          - "pure" - the default, how much anomal the value is;
              float 0..1 where 1=totally unexpected
          - "likelihood" - uses the anomaly_likelihood code;
              models probability of receiving this value and anomalyScore
          - "weighted" - "pure" anomaly weighted by "likelihood"
              (anomaly * likelihood)
    @param binaryAnomalyThreshold (optional) - if set [0,1] anomaly score
         will be discretized to 1/0 (1 if >= binaryAnomalyThreshold)
         The transformation is applied after moving average is computed and updated.
    """
    self._mode = mode
    if slidingWindowSize is not None:
      self._movingAverage = MovingAverage(windowSize=slidingWindowSize)
    else:
      self._movingAverage = None

    if self._mode == Anomaly.MODE_LIKELIHOOD or self._mode == Anomaly.MODE_WEIGHTED:
      self._likelihood = AnomalyLikelihood() # probabilistic anomaly
    if not self._mode in Anomaly._supportedModes:
      raise ValueError("Invalid anomaly mode; only supported modes are: "
                       "Anomaly.MODE_PURE, Anomaly.MODE_LIKELIHOOD, "
                       "Anomaly.MODE_WEIGHTED; you used: %r" % self._mode)
    self._binaryThreshold = binaryAnomalyThreshold
    if binaryAnomalyThreshold is not None and ( 
          not isinstance(binaryAnomalyThreshold, float) or
          binaryAnomalyThreshold >= 1.0  or 
          binaryAnomalyThreshold <= 0.0 ):
      raise ValueError("Anomaly: binaryAnomalyThreshold must be from (0,1) "
                       "or None if disabled.")


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
    # Start by computing the raw anomaly score.
    anomalyScore = computeRawAnomalyScore(activeColumns, predictedColumns)

    # Compute final anomaly based on selected mode.
    if self._mode == Anomaly.MODE_PURE:
      score = anomalyScore
    elif self._mode == Anomaly.MODE_LIKELIHOOD:
      if inputValue is None:
        raise ValueError("Selected anomaly mode 'Anomaly.MODE_LIKELIHOOD' "
                 "requires 'inputValue' as parameter to compute() method. ")

      probability = self._likelihood.anomalyProbability(
          inputValue, anomalyScore, timestamp)
      # low likelihood -> hi anomaly
      score = 1 - probability
    elif self._mode == Anomaly.MODE_WEIGHTED:
      probability = self._likelihood.anomalyProbability(
          inputValue, anomalyScore, timestamp)
      score = anomalyScore * (1 - probability)

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


  def __str__(self):
    windowSize = 0
    if self._movingAverage is not None:
      windowSize = self._movingAverage.windowSize
    return "Anomaly:\tmode=%s\twindowSize=%r" % (self._mode, windowSize)


  def __setstate__(self, state):
    """deserialization"""
    self.__dict__.update(state)

    if not hasattr(self, '_mode'):
      self._mode = Anomaly.MODE_PURE
    if not hasattr(self, '_movingAverage'):
      self._movingAverage = None
    if not hasattr(self, '_binaryThreshold'):
      self._binaryThreshold = None

  ##################################################################
  # these methods are alternative implementations of 'how to compute'
  # anomaly score from the neural output (2 binary vectors)
  ##################################################################
  @staticmethod
  def compute_In1D_Satisfied(activeColumns, prevPredictedColumns):
  """Computes the raw anomaly score.

  The raw anomaly score is the fraction of active columns not predicted.

  The implementation is using in1D() function, 
  "satisfied" means it only cares if activeColumns at time T have been 
  predicted at T-1. 

  Which means a temporal pooler TP with all columns in predictive state at T-1
  would have zero anomaly score at T for any active state. 

  @param activeColumns: array of active column indices
  @param prevPredictedColumns: array of columns indices predicted in prev step
  @return anomaly score 0..1 (float)

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
  elif len(prevPredictedColumns) > 0:
    # There were predicted columns but none active.
    score = 1.0
  else:
    # There were no predicted or active columns.
    score = 0.0
  return score

  ####################################################################
  @staticmethod
  def compute_In1D_Predicted(activeColumns, prevPredictedColumns):
  """Computes the raw anomaly score.

  The raw anomaly score is the fraction of predicted columns not activated.

  The implementation is using in1D() function, 
  "predicted" means it only cares if all predictedColumns at time T-1 are 
  active at T. 

  Which means a temporal pooler TP with none columns in predictive state at T-1
  would have zero anomaly score at T for any active state. 

  Compare with compute_In1D_Satisfied(), this is a complement.

  @param activeColumns: array of active column indices
  @param prevPredictedColumns: array of columns indices predicted in prev step
  @return anomaly score 0..1 (float)
  """
  return Anomaly.compute_In1D_Satisfied(prevPredictedColumns, activeColumns)

  ####################################################################
  @staticmethod
  def compute_XOR_Both(activeColumns, prevPredictedColumns):
    """Computes the raw anomaly score.

    The raw anomaly score is difference between predicted and actual state: 
     = the fraction of active columns not predicted +
       the fraction of non-active columns predicted as active.

    The implementation is using xor() function, 
    "both" means either active & unpredicted and
    predicted but inactive columns will contribute to the anomaly score.

    It is a "combination" of compute_In1D_Satisfied() and compute_In1D_Predicted(), 
    this method will also be the most sensitive (detect most & highest) anomalies.

    @param activeColumns: array of active column indices
    @param prevPredictedColumns: array of columns indices predicted in prev step
    @return anomaly score 0..1 (float)
    """
    nTotal = len(activeColumns) + len(prevPredictedColumns) #FIXME this does not look correct
    if nTotal == 0:
      score = 0.0
    else:
      unique = numpy.setxor1d(activeColumns, prevPredictedColumns)
      score = len(unique)/float(nTotal)
    return score

