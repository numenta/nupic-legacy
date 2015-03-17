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

  @param activeColumns: array of active column indices
  @param prevPredictedColumns: array of columns indices predicted in prev step
  @return anomaly score 0..1 (float)
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


  def __init__(self, slidingWindowSize=0, mode=MODE_PURE, binaryAnomalyThreshold=0.0):
    """
    @param slidingWindowSize (optional) - how many elements are summed up;
        enables moving average on final anomaly score; int >= 0;
        0 means disabled (default)
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
         0.0 means disabled (default)
    """
    self._mode = mode
    if slidingWindowSize > 0:
      self._movingAverage = MovingAverage(windowSize=slidingWindowSize)
    else:
      self._movingAverage = None

    if self._mode == Anomaly.MODE_LIKELIHOOD or \
       self._mode == Anomaly.MODE_WEIGHTED:
      self._likelihood = AnomalyLikelihood() # probabilistic anomaly
    assert self._mode in Anomaly._supportedModes, "Invalid anomaly mode; \
                       only supported modes are: \n\
                       Anomaly.MODE_PURE, Anomaly.MODE_LIKELIHOOD, \n\
                       Anomaly.MODE_WEIGHTED;\n you used: %r" % self._mode
    self._binaryThreshold = binaryAnomalyThreshold
    assert isinstance(binaryAnomalyThreshold, float) and \
       binaryAnomalyThreshold < 1.0  and \
       binaryAnomalyThreshold >= 0.0, "Anomaly: \
      binaryAnomalyThreshold must be from [0,1); 0 for disabled."


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
      assert inputValue is not None, "Selected anomaly mode \
        'Anomaly.MODE_LIKELIHOOD' requires 'inputValue' as parameter to compute() method. "

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
    if self._binaryThreshold > 0.0:
      if score >= self._binaryThreshold:
        score = 1.0
      else:
        score = 0.0

    return score


  @staticmethod
  def initFactory(slidingWindowSize, mode, binaryAnomalyThreshold):
    """
    factory method for initiation of Anomaly() instance using parameters as text strings, 
    useful eg for OPF. 
    This method parses the parameters and calls the default __init__() properly. 
    For details of the parameters see __init__. 
    Use None to automatically supply default values.

    @param slidingWindowSize (str) length of sliding window
    @param mode (str) Anomaly mode
    @param binaryAnomalyThreshold (str) binary discretization threshold
    @return Anomaly instance, call Anomaly.initFactory(....) 
    """
    # defaults
    if slidingWindowSize is None:
      slidingWindowSize = "0"
    if mode is None:
      mode = "pure"
    if binaryAnomalyThreshold is None:
      binaryAnomalyThreshold = "0.0"

    try:
      iWindow = int(slidingWindowSize)
      fThreshold = float(binaryAnomalyThreshold)
    except:
      raise ValueError("Anomaly.initFactory(): failed to parse parameters properly")

    return Anomaly(slidingWindowSize=iWindow,
                   mode=mode,
                   binaryAnomalyThreshold=fThreshold)


  def __str__(self):
    windowSize = 0
    if self._movingAverage is not None:
      windowSize = self._movingAverage.windowSize
    return "Anomaly:\tmode=%s\twindowSize=%r" % (self._mode, windowSize)


  def __cmp__(self, other):
    if not isinstance(other, Anomaly): 
      return -1
    if (other._mode == self._mode and
        other._score == self._score and
        other._binaryThreshold == self._binaryThreshold and
        other._movingAverage == self._movingAverage):
      return 0 #equal
    else:
      return -1


  def __setstate__(self, state):
    """deserialization"""
    self.__dict__.update(state)

    if not hasattr(self, '_mode'):
      self._mode = Anomaly.MODE_PURE
    if not hasattr(self, '_movingAverage'):
      self._movingAverage = 0
    if not hasattr(self, '_binaryThreshold'):
      self._binaryThreshold = 0.0
