# Copyright 2014-2016 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""Anomaly-related algorithms."""

import numpy

from nupic.algorithms.anomaly_likelihood import AnomalyLikelihood
from nupic.utils import MovingAverage


def computeRawAnomalyScore(activeColumns, prevPredictedColumns):
  """Computes the raw anomaly score.

  The raw anomaly score is the fraction of active columns not predicted.

  :param activeColumns: array of active column indices
  :param prevPredictedColumns: array of columns indices predicted in prev step
  :returns: anomaly score 0..1 (float)
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

  :param slidingWindowSize: [optional] - how many elements are summed up;
      enables moving average on final anomaly score; int >= 0

  :param mode: (string) [optional] how to compute anomaly, one of:

      - :const:`nupic.algorithms.anomaly.Anomaly.MODE_PURE`
      - :const:`nupic.algorithms.anomaly.Anomaly.MODE_LIKELIHOOD`
      - :const:`nupic.algorithms.anomaly.Anomaly.MODE_WEIGHTED`

  :param binaryAnomalyThreshold: [optional] if set [0,1] anomaly score
       will be discretized to 1/0 (1 if >= binaryAnomalyThreshold)
       The transformation is applied after moving average is computed.

  """


  # anomaly modes supported
  MODE_PURE = "pure"
  """
  Default mode. The raw anomaly score as computed by
  :func:`~.anomaly_likelihood.computeRawAnomalyScore`
  """
  MODE_LIKELIHOOD = "likelihood"
  """
  Uses the :class:`~.anomaly_likelihood.AnomalyLikelihood` class, which models
  probability of receiving this value and anomalyScore
  """
  MODE_WEIGHTED = "weighted"
  """
  Multiplies the likelihood result with the raw anomaly score that was used to
  generate the likelihood (anomaly * likelihood)
  """

  _supportedModes = (MODE_PURE, MODE_LIKELIHOOD, MODE_WEIGHTED)


  def __init__(self,
               slidingWindowSize=None,
               mode=MODE_PURE,
               binaryAnomalyThreshold=None):
    self._mode = mode
    if slidingWindowSize is not None:
      self._movingAverage = MovingAverage(windowSize=slidingWindowSize)
    else:
      self._movingAverage = None

    if (self._mode == Anomaly.MODE_LIKELIHOOD or
        self._mode == Anomaly.MODE_WEIGHTED):
      self._likelihood = AnomalyLikelihood() # probabilistic anomaly
    else:
      self._likelihood = None

    if not self._mode in self._supportedModes:
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

    :param activeColumns: array of active column indices
    :param predictedColumns: array of columns indices predicted in this step
                             (used for anomaly in step T+1)
    :param inputValue: (optional) value of current input to encoders
                                  (eg "cat" for category encoder)
                                  (used in anomaly-likelihood)
    :param timestamp: (optional) date timestamp when the sample occured
                                 (used in anomaly-likelihood)
    :returns: the computed anomaly score; float 0..1
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


  def __eq__(self, other):
    return (isinstance(other, Anomaly) and
            other._mode == self._mode and
            other._binaryThreshold == self._binaryThreshold and
            other._movingAverage == self._movingAverage and
            other._likelihood == self._likelihood)


  def __setstate__(self, state):
    """deserialization"""
    self.__dict__.update(state)

    if not hasattr(self, '_mode'):
      self._mode = Anomaly.MODE_PURE
    if not hasattr(self, '_movingAverage'):
      self._movingAverage = None
    if not hasattr(self, '_binaryThreshold'):
      self._binaryThreshold = None
