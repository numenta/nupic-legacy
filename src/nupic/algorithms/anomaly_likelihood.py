# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014-2016, Numenta, Inc.  Unless you have an agreement
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

"""
This module analyzes and estimates the distribution of averaged anomaly scores
from a given model. Given a new anomaly score ``s``, estimates
``P(score >= s)``.

The number ``P(score >= s)`` represents the likelihood of the current state of
predictability. For example, a likelihood of 0.01 or 1% means we see this much
predictability about one out of every 100 records. The number is not as unusual
as it seems. For records that arrive every minute, this means once every hour
and 40 minutes. A likelihood of 0.0001 or 0.01% means we see it once out of
10,000 records, or about once every 7 days.

USAGE
+++++

There are two ways to use the code: using the
:class:`.anomaly_likelihood.AnomalyLikelihood` helper class or using the raw
individual functions :func:`~.anomaly_likelihood.estimateAnomalyLikelihoods` and
:func:`~.anomaly_likelihood.updateAnomalyLikelihoods`.


Low-Level Function Usage
++++++++++++++++++++++++

There are two primary interface routines.

- :func:`~.anomaly_likelihood.estimateAnomalyLikelihoods`: batch routine, called
  initially and once in a while
- :func:`~.anomaly_likelihood.updateAnomalyLikelihoods`: online routine, called
  for every new data point

Initially:

.. code-block:: python

   likelihoods, avgRecordList, estimatorParams = \\
     estimateAnomalyLikelihoods(metric_data)

Whenever you get new data:

.. code-block:: python

   likelihoods, avgRecordList, estimatorParams = \\
     updateAnomalyLikelihoods(data2, estimatorParams)

And again (make sure you use the new estimatorParams returned in the above call
to updateAnomalyLikelihoods!).

.. code-block:: python

   likelihoods, avgRecordList, estimatorParams = \\
     updateAnomalyLikelihoods(data3, estimatorParams)

Every once in a while update estimator with a lot of recent data.

.. code-block:: python

   likelihoods, avgRecordList, estimatorParams = \\
     estimateAnomalyLikelihoods(lots_of_metric_data)


PARAMS
++++++

The parameters dict returned by the above functions has the following
structure. Note: the client does not need to know the details of this.

::

 {
   "distribution":               # describes the distribution
     {
       "name": STRING,           # name of the distribution, such as 'normal'
       "mean": SCALAR,           # mean of the distribution
       "variance": SCALAR,       # variance of the distribution

       # There may also be some keys that are specific to the distribution
     },

   "historicalLikelihoods": []   # Contains the last windowSize likelihood
                                 # values returned

   "movingAverage":              # stuff needed to compute a rolling average
                                 # of the anomaly scores
     {
       "windowSize": SCALAR,     # the size of the averaging window
       "historicalValues": [],   # list with the last windowSize anomaly
                                 # scores
       "total": SCALAR,          # the total of the values in historicalValues
     },

 }

"""

import collections
import math
import numbers
import numpy

from nupic.serializable import Serializable
from nupic.utils import MovingAverage


class AnomalyLikelihood(Serializable):
  """
  Helper class for running anomaly likelihood computation. To use it simply
  create an instance and then feed it successive anomaly scores:

  .. code-block:: python

      anomalyLikelihood = AnomalyLikelihood()
      while still_have_data:
        # Get anomaly score from model

        # Compute probability that an anomaly has ocurred
        anomalyProbability = anomalyLikelihood.anomalyProbability(
            value, anomalyScore, timestamp)

  """


  def __init__(self,
               claLearningPeriod=None,
               learningPeriod=288,
               estimationSamples=100,
               historicWindowSize=8640,
               reestimationPeriod=100):
    """
    NOTE: Anomaly likelihood scores are reported at a flat 0.5 for
    learningPeriod + estimationSamples iterations.

    claLearningPeriod and learningPeriod are specifying the same variable,
    although claLearningPeriod is a deprecated name for it.

    :param learningPeriod: (claLearningPeriod: deprecated) - (int) the number of
      iterations required for the algorithm to learn the basic patterns in the
      dataset and for the anomaly score to 'settle down'. The default is based
      on empirical observations but in reality this could be larger for more
      complex domains. The downside if this is too large is that real anomalies
      might get ignored and not flagged.

    :param estimationSamples: (int) the number of reasonable anomaly scores
      required for the initial estimate of the Gaussian. The default of 100
      records is reasonable - we just need sufficient samples to get a decent
      estimate for the Gaussian. It's unlikely you will need to tune this since
      the Gaussian is re-estimated every 10 iterations by default.

    :param historicWindowSize: (int) size of sliding window of historical
      data points to maintain for periodic reestimation of the Gaussian. Note:
      the default of 8640 is based on a month's worth of history at 5-minute
      intervals.

    :param reestimationPeriod: (int) how often we re-estimate the Gaussian
      distribution. The ideal is to re-estimate every iteration but this is a
      performance hit. In general the system is not very sensitive to this
      number as long as it is small relative to the total number of records
      processed.
    """
    if historicWindowSize < estimationSamples:
      raise ValueError("estimationSamples exceeds historicWindowSize")

    self._iteration = 0
    self._historicalScores = collections.deque(maxlen=historicWindowSize)
    self._distribution = None


    if claLearningPeriod != None:
      print("claLearningPeriod is deprecated, use learningPeriod instead.")
      self._learningPeriod = claLearningPeriod
    else:
      self._learningPeriod = learningPeriod

    self._probationaryPeriod = self._learningPeriod + estimationSamples
    self._reestimationPeriod = reestimationPeriod


  def __eq__(self, o):
    # pylint: disable=W0212
    return (isinstance(o, AnomalyLikelihood) and
            self._iteration == o._iteration and
            self._historicalScores == o._historicalScores and
            self._distribution == o._distribution and
            self._probationaryPeriod == o._probationaryPeriod and
            self._learningPeriod == o._learningPeriod and
            self._reestimationPeriod == o._reestimationPeriod)
    # pylint: enable=W0212


  def __str__(self):
    return ("AnomalyLikelihood: %s %s %s %s %s %s" % (
      self._iteration,
      self._historicalScores,
      self._distribution,
      self._probationaryPeriod,
      self._learningPeriod,
      self._reestimationPeriod) )


  @staticmethod
  def computeLogLikelihood(likelihood):
    """
    Compute a log scale representation of the likelihood value. Since the
    likelihood computations return low probabilities that often go into four 9's
    or five 9's, a log value is more useful for visualization, thresholding,
    etc.
    """
    # The log formula is:
    #     Math.log(1.0000000001 - likelihood) / Math.log(1.0 - 0.9999999999)
    return math.log(1.0000000001 - likelihood) / -23.02585084720009


  @staticmethod
  def _calcSkipRecords(numIngested, windowSize, learningPeriod):
    """Return the value of skipRecords for passing to estimateAnomalyLikelihoods

    If `windowSize` is very large (bigger than the amount of data) then this
    could just return `learningPeriod`. But when some values have fallen out of
    the historical sliding window of anomaly records, then we have to take those
    into account as well so we return the `learningPeriod` minus the number
    shifted out.

    :param numIngested - (int) number of data points that have been added to the
      sliding window of historical data points.
    :param windowSize - (int) size of sliding window of historical data points.
    :param learningPeriod - (int) the number of iterations required for the
      algorithm to learn the basic patterns in the dataset and for the anomaly
      score to 'settle down'.
    """
    numShiftedOut = max(0, numIngested - windowSize)
    return min(numIngested, max(0, learningPeriod - numShiftedOut))


  @classmethod
  def read(cls, proto):
    """ capnp deserialization method for the anomaly likelihood object

    :param proto: (Object) capnp proto object specified in
                          nupic.regions.AnomalyLikelihoodRegion.capnp

    :returns: (Object) the deserialized AnomalyLikelihood object
    """
    # pylint: disable=W0212
    anomalyLikelihood = object.__new__(cls)
    anomalyLikelihood._iteration = proto.iteration

    anomalyLikelihood._historicalScores = collections.deque(
      maxlen=proto.historicWindowSize)
    for i, score in enumerate(proto.historicalScores):
      anomalyLikelihood._historicalScores.append((i, score.value,
                                                  score.anomalyScore))
    if proto.distribution.name: # is "" when there is no distribution.
      anomalyLikelihood._distribution = {}
      anomalyLikelihood._distribution["name"] = proto.distribution.name
      anomalyLikelihood._distribution["mean"] = proto.distribution.mean
      anomalyLikelihood._distribution["variance"] = proto.distribution.variance
      anomalyLikelihood._distribution["stdev"] = proto.distribution.stdev

      anomalyLikelihood._distribution["movingAverage"] = {}
      anomalyLikelihood._distribution["movingAverage"]["windowSize"] =\
        proto.distribution.movingAverage.windowSize
      anomalyLikelihood._distribution["movingAverage"]["historicalValues"] = []
      for value in proto.distribution.movingAverage.historicalValues:
        anomalyLikelihood._distribution["movingAverage"]["historicalValues"]\
          .append(value)
      anomalyLikelihood._distribution["movingAverage"]["total"] =\
        proto.distribution.movingAverage.total

      anomalyLikelihood._distribution["historicalLikelihoods"] = []
      for likelihood in proto.distribution.historicalLikelihoods:
        anomalyLikelihood._distribution["historicalLikelihoods"].append(
          likelihood)
    else:
      anomalyLikelihood._distribution = None

    anomalyLikelihood._probationaryPeriod = proto.probationaryPeriod
    anomalyLikelihood._learningPeriod = proto.learningPeriod
    anomalyLikelihood._reestimationPeriod = proto.reestimationPeriod
    # pylint: enable=W0212

    return anomalyLikelihood


  def write(self, proto):
    """ capnp serialization method for the anomaly likelihood object

    :param proto: (Object) capnp proto object specified in
                          nupic.regions.AnomalyLikelihoodRegion.capnp
    """
    proto.iteration = self._iteration

    pHistScores = proto.init('historicalScores', len(self._historicalScores))
    for i, score in enumerate(list(self._historicalScores)):
      _, value, anomalyScore = score
      record = pHistScores[i]
      record.value = float(value)
      record.anomalyScore = float(anomalyScore)

    if self._distribution:
      proto.distribution.name = self._distribution["distributionParams"]["name"]
      proto.distribution.mean = self._distribution["distributionParams"]["mean"]
      proto.distribution.variance = self._distribution["distributionParams"]\
        ["variance"]
      proto.distribution.stdev = self._distribution["distributionParams"]\
        ["stdev"]

      proto.distribution.movingAverage.windowSize = self._distribution\
        ["movingAverage"]["windowSize"]

      historicalValues = self._distribution["movingAverage"]["historicalValues"]
      pHistValues = proto.distribution.movingAverage.init(
        "historicalValues", len(historicalValues))
      for i, value in enumerate(historicalValues):
        pHistValues[i] = float(value)

      proto.distribution.movingAverage.historicalValues = self._distribution\
        ["movingAverage"]["historicalValues"]
      proto.distribution.movingAverage.total = self._distribution\
        ["movingAverage"]["total"]

      historicalLikelihoods = self._distribution["historicalLikelihoods"]
      pHistLikelihoods = proto.distribution.init("historicalLikelihoods",
                                                 len(historicalLikelihoods))
      for i, likelihood in enumerate(historicalLikelihoods):
        pHistLikelihoods[i] = float(likelihood)

    proto.probationaryPeriod = self._probationaryPeriod
    proto.learningPeriod = self._learningPeriod
    proto.reestimationPeriod = self._reestimationPeriod
    proto.historicWindowSize = self._historicalScores.maxlen


  def anomalyProbability(self, value, anomalyScore, timestamp=None):
    """
    Compute the probability that the current value plus anomaly score represents
    an anomaly given the historical distribution of anomaly scores. The closer
    the number is to 1, the higher the chance it is an anomaly.

    :param value: the current metric ("raw") input value, eg. "orange", or
                   '21.2' (deg. Celsius), ...
    :param anomalyScore: the current anomaly score
    :param timestamp: [optional] timestamp of the ocurrence,
                       default (None) results in using iteration step.
    :returns: the anomalyLikelihood for this record.
    """
    if timestamp is None:
      timestamp = self._iteration

    dataPoint = (timestamp, value, anomalyScore)
    # We ignore the first probationaryPeriod data points
    if self._iteration < self._probationaryPeriod:
      likelihood = 0.5
    else:
      # On a rolling basis we re-estimate the distribution
      if ( (self._distribution is None) or
           (self._iteration % self._reestimationPeriod == 0) ):

        numSkipRecords = self._calcSkipRecords(
          numIngested=self._iteration,
          windowSize=self._historicalScores.maxlen,
          learningPeriod=self._learningPeriod)

        _, _, self._distribution = estimateAnomalyLikelihoods(
          self._historicalScores,
          skipRecords=numSkipRecords)

      likelihoods, _, self._distribution = updateAnomalyLikelihoods(
        [dataPoint],
        self._distribution)

      likelihood = 1.0 - likelihoods[0]

    # Before we exit update historical scores and iteration
    self._historicalScores.append(dataPoint)
    self._iteration += 1

    return likelihood



def estimateAnomalyLikelihoods(anomalyScores,
                               averagingWindow=10,
                               skipRecords=0,
                               verbosity=0):
  """
  Given a series of anomaly scores, compute the likelihood for each score. This
  function should be called once on a bunch of historical anomaly scores for an
  initial estimate of the distribution. It should be called again every so often
  (say every 50 records) to update the estimate.

  :param anomalyScores: a list of records. Each record is a list with the
                        following three elements: [timestamp, value, score]

                        Example::

                            [datetime.datetime(2013, 8, 10, 23, 0), 6.0, 1.0]

                        For best results, the list should be between 1000
                        and 10,000 records
  :param averagingWindow: integer number of records to average over
  :param skipRecords: integer specifying number of records to skip when
                      estimating distributions. If skip records are >=
                      len(anomalyScores), a very broad distribution is returned
                      that makes everything pretty likely.
  :param verbosity: integer controlling extent of printouts for debugging

                      0 = none
                      1 = occasional information
                      2 = print every record

  :returns: 3-tuple consisting of:

            - likelihoods

              numpy array of likelihoods, one for each aggregated point

            - avgRecordList

              list of averaged input records

            - params

              a small JSON dict that contains the state of the estimator

  """
  if verbosity > 1:
    print("In estimateAnomalyLikelihoods.")
    print("Number of anomaly scores:", len(anomalyScores))
    print("Skip records=", skipRecords)
    print("First 20:", anomalyScores[0:min(20, len(anomalyScores))])

  if len(anomalyScores) == 0:
    raise ValueError("Must have at least one anomalyScore")

  # Compute averaged anomaly scores
  aggRecordList, historicalValues, total =  _anomalyScoreMovingAverage(
    anomalyScores,
    windowSize = averagingWindow,
    verbosity = verbosity)
  s = [r[2] for r in aggRecordList]
  dataValues = numpy.array(s)

  # Estimate the distribution of anomaly scores based on aggregated records
  if len(aggRecordList) <= skipRecords:
    distributionParams = nullDistribution(verbosity = verbosity)
  else:
    distributionParams = estimateNormal(dataValues[skipRecords:])

    # HACK ALERT! The HTMPredictionModel currently does not handle constant
    # metric values very well (time of day encoder changes sometimes lead to
    # unstable SDR's even though the metric is constant). Until this is
    # resolved, we explicitly detect and handle completely flat metric values by
    # reporting them as not anomalous.
    s = [r[1] for r in aggRecordList]
    # Only do this if the values are numeric
    if all([isinstance(r[1], numbers.Number) for r in aggRecordList]):
      metricValues = numpy.array(s)
      metricDistribution = estimateNormal(metricValues[skipRecords:],
                                          performLowerBoundCheck=False)

      if metricDistribution["variance"] < 1.5e-5:
        distributionParams = nullDistribution(verbosity = verbosity)

  # Estimate likelihoods based on this distribution
  likelihoods = numpy.array(dataValues, dtype=float)
  for i, s in enumerate(dataValues):
    likelihoods[i] = tailProbability(s, distributionParams)

  # Filter likelihood values
  filteredLikelihoods = numpy.array(
    _filterLikelihoods(likelihoods) )

  params = {
    "distribution":       distributionParams,
    "movingAverage": {
      "historicalValues": historicalValues,
      "total":            total,
      "windowSize":       averagingWindow,
    },
    "historicalLikelihoods":
      list(likelihoods[-min(averagingWindow, len(likelihoods)):]),
  }

  if verbosity > 1:
    print("Discovered params=")
    print(params)
    print("Number of likelihoods:", len(likelihoods))
    print("First 20 likelihoods:", (
      filteredLikelihoods[0:min(20, len(filteredLikelihoods))] ))
    print("leaving estimateAnomalyLikelihoods")


  return (filteredLikelihoods, aggRecordList, params)



def updateAnomalyLikelihoods(anomalyScores,
                             params,
                             verbosity=0):
  """
  Compute updated probabilities for anomalyScores using the given params.

  :param anomalyScores: a list of records. Each record is a list with the
                        following three elements: [timestamp, value, score]

                        Example::

                            [datetime.datetime(2013, 8, 10, 23, 0), 6.0, 1.0]

  :param params: the JSON dict returned by estimateAnomalyLikelihoods
  :param verbosity: integer controlling extent of printouts for debugging
  :type verbosity: int

  :returns: 3-tuple consisting of:

            - likelihoods

              numpy array of likelihoods, one for each aggregated point

            - avgRecordList

              list of averaged input records

            - params

              an updated JSON object containing the state of this metric.

  """
  if verbosity > 3:
    print("In updateAnomalyLikelihoods.")
    print("Number of anomaly scores:", len(anomalyScores))
    print("First 20:", anomalyScores[0:min(20, len(anomalyScores))])
    print("Params:", params)

  if len(anomalyScores) == 0:
    raise ValueError("Must have at least one anomalyScore")

  if not isValidEstimatorParams(params):
    raise ValueError("'params' is not a valid params structure")

  # For backward compatibility.
  if "historicalLikelihoods" not in params:
    params["historicalLikelihoods"] = [1.0]

  # Compute moving averages of these new scores using the previous values
  # as well as likelihood for these scores using the old estimator
  historicalValues  = params["movingAverage"]["historicalValues"]
  total             = params["movingAverage"]["total"]
  windowSize        = params["movingAverage"]["windowSize"]

  aggRecordList = numpy.zeros(len(anomalyScores), dtype=float)
  likelihoods = numpy.zeros(len(anomalyScores), dtype=float)
  for i, v in enumerate(anomalyScores):
    newAverage, historicalValues, total = (
      MovingAverage.compute(historicalValues, total, v[2], windowSize)
    )
    aggRecordList[i] = newAverage
    likelihoods[i]   = tailProbability(newAverage, params["distribution"])

  # Filter the likelihood values. First we prepend the historical likelihoods
  # to the current set. Then we filter the values.  We peel off the likelihoods
  # to return and the last windowSize values to store for later.
  likelihoods2 = params["historicalLikelihoods"] + list(likelihoods)
  filteredLikelihoods = _filterLikelihoods(likelihoods2)
  likelihoods[:] = filteredLikelihoods[-len(likelihoods):]
  historicalLikelihoods = likelihoods2[-min(windowSize, len(likelihoods2)):]

  # Update the estimator
  newParams = {
    "distribution": params["distribution"],
    "movingAverage": {
      "historicalValues": historicalValues,
      "total": total,
      "windowSize": windowSize,
    },
    "historicalLikelihoods": historicalLikelihoods,
  }

  assert len(newParams["historicalLikelihoods"]) <= windowSize

  if verbosity > 3:
    print("Number of likelihoods:", len(likelihoods))
    print("First 20 likelihoods:", likelihoods[0:min(20, len(likelihoods))])
    print("Leaving updateAnomalyLikelihoods.")

  return (likelihoods, aggRecordList, newParams)



def _filterLikelihoods(likelihoods,
                       redThreshold=0.99999, yellowThreshold=0.999):
  """
  Filter the list of raw (pre-filtered) likelihoods so that we only preserve
  sharp increases in likelihood. 'likelihoods' can be a numpy array of floats or
  a list of floats.

  :returns: A new list of floats likelihoods containing the filtered values.
  """
  redThreshold    = 1.0 - redThreshold
  yellowThreshold = 1.0 - yellowThreshold

  # The first value is untouched
  filteredLikelihoods = [likelihoods[0]]

  for i, v in enumerate(likelihoods[1:]):

    if v <= redThreshold:
      # Value is in the redzone

      if likelihoods[i] > redThreshold:
        # Previous value is not in redzone, so leave as-is
        filteredLikelihoods.append(v)
      else:
        filteredLikelihoods.append(yellowThreshold)

    else:
      # Value is below the redzone, so leave as-is
      filteredLikelihoods.append(v)

  return filteredLikelihoods



def _anomalyScoreMovingAverage(anomalyScores,
                               windowSize=10,
                               verbosity=0,
                              ):
  """
  Given a list of anomaly scores return a list of averaged records.
  anomalyScores is assumed to be a list of records of the form:
                [datetime.datetime(2013, 8, 10, 23, 0), 6.0, 1.0]

  Each record in the returned list list contains:
      [datetime, value, averagedScore]

  *Note:* we only average the anomaly score.
  """

  historicalValues = []
  total = 0.0
  averagedRecordList = []    # Aggregated records
  for record in anomalyScores:

    # Skip (but log) records without correct number of entries
    if not isinstance(record, (list, tuple)) or len(record) != 3:
      if verbosity >= 1:
        print("Malformed record:", record)
      continue

    avg, historicalValues, total = (
      MovingAverage.compute(historicalValues, total, record[2], windowSize)
      )

    averagedRecordList.append( [record[0], record[1], avg] )

    if verbosity > 2:
      print("Aggregating input record:", record)
      print("Result:", [record[0], record[1], avg])

  return averagedRecordList, historicalValues, total



def estimateNormal(sampleData, performLowerBoundCheck=True):
  """
  :param sampleData:
  :type sampleData: Numpy array.
  :param performLowerBoundCheck:
  :type performLowerBoundCheck: bool
  :returns: A dict containing the parameters of a normal distribution based on
      the ``sampleData``.
  """
  params = {
    "name": "normal",
    "mean": numpy.mean(sampleData),
    "variance": numpy.var(sampleData),
  }

  if performLowerBoundCheck:
    # Handle edge case of almost no deviations and super low anomaly scores. We
    # find that such low anomaly means can happen, but then the slightest blip
    # of anomaly score can cause the likelihood to jump up to red.
    if params["mean"] < 0.03:
      params["mean"] = 0.03

    # Catch all for super low variance to handle numerical precision issues
    if params["variance"] < 0.0003:
      params["variance"] = 0.0003

  # Compute standard deviation
  if params["variance"] > 0:
    params["stdev"] = math.sqrt(params["variance"])
  else:
    params["stdev"] = 0

  return params



def nullDistribution(verbosity=0):
  """
  :param verbosity: integer controlling extent of printouts for debugging
  :type verbosity: int
  :returns: A distribution that is very broad and makes every anomaly score
      between 0 and 1 pretty likely.
  """
  if verbosity>0:
    print("Returning nullDistribution")
  return {
    "name": "normal",
    "mean": 0.5,
    "variance": 1e6,
    "stdev": 1e3,
  }



def tailProbability(x, distributionParams):
  """
  Given the normal distribution specified by the mean and standard deviation
  in distributionParams, return the probability of getting samples further
  from the mean. For values above the mean, this is the probability of getting
  samples > x and for values below the mean, the probability of getting
  samples < x. This is the Q-function: the tail probability of the normal distribution.

  :param distributionParams: dict with 'mean' and 'stdev' of the distribution
  """
  if "mean" not in distributionParams or "stdev" not in distributionParams:
    raise RuntimeError("Insufficient parameters to specify the distribution.")

  if x < distributionParams["mean"]:
    # Gaussian is symmetrical around mean, so flip to get the tail probability
    xp = 2 * distributionParams["mean"] - x
    return tailProbability(xp, distributionParams)

  # Calculate the Q function with the complementary error function, explained
  # here: http://www.gaussianwaves.com/2012/07/q-function-and-error-functions
  z = (x - distributionParams["mean"]) / distributionParams["stdev"]
  return 0.5 * math.erfc(z/1.4142)



def isValidEstimatorParams(p):
  """
  :returns: ``True`` if ``p`` is a valid estimator params as might be returned
    by ``estimateAnomalyLikelihoods()`` or ``updateAnomalyLikelihoods``,
    ``False`` otherwise.  Just does some basic validation.
  """
  if not isinstance(p, dict):
    return False
  if "distribution" not in p:
    return False
  if "movingAverage" not in p:
    return False
  dist = p["distribution"]
  if not ("mean" in dist and "name" in dist
          and "variance" in dist and "stdev" in dist):
    return False

  return True
