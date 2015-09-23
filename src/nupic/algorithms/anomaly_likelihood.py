# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014-2015, Numenta, Inc.  Unless you have an agreement
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
from a CLA model. Given a new anomaly score `s`, estimates `P(score >= s)`.

The number `P(score >= s)` represents the likelihood of the current state of
predictability. For example, a likelihood of 0.01 or 1% means we see this much
predictability about one out of every 100 records. The number is not as unusual
as it seems. For records that arrive every minute, this means once every hour
and 40 minutes. A likelihood of 0.0001 or 0.01% means we see it once out of
10,000 records, or about once every 7 days.

USAGE
-----

There are two ways to use the code: using the AnomalyLikelihood helper class or
using the raw individual functions.


Helper Class
------------
The helper class AnomalyLikelihood is the easiest to use.  To use it simply
create an instance and then feed it successive anomaly scores:

anomalyLikelihood = AnomalyLikelihood()
while still_have_data:
  # Get anomaly score from model

  # Compute probability that an anomaly has ocurred
  anomalyProbability = anomalyLikelihood.anomalyProbability(
      value, anomalyScore, timestamp)


Raw functions
-------------

There are two lower level functions, estimateAnomalyLikelihoods and
updateAnomalyLikelihoods. The details of these are described below.

"""

import collections
import math
import numpy

from nupic.utils import MovingAverage


class AnomalyLikelihood(object):
  """
  Helper class for running anomaly likelihood computation.
  """


  def __init__(self,
               claLearningPeriod=288,
               estimationSamples=100,
               historicWindowSize=8640,
               reestimationPeriod=100):
    """
    NOTE: Anomaly likelihood scores are reported at a flat 0.5 for
    claLearningPeriod + estimationSamples iterations.

    @param claLearningPeriod - (int) the number of iterations required for the
      CLA to learn the basic patterns in the dataset and for the anomaly score
      to 'settle down'. The default is based on empirical observations but in
      reality this could be larger for more complex domains. The downside if
      this is too large is that real anomalies might get ignored and not
      flagged.

    @param estimationSamples - (int) the number of reasonable anomaly scores
      required for the initial estimate of the Gaussian. The default of 100
      records is reasonable - we just need sufficient samples to get a decent
      estimate for the Gaussian. It's unlikely you will need to tune this since
      the Gaussian is re-estimated every 10 iterations by default.

    @param historicWindowSize - (int) size of sliding window of historical
      data points to maintain for periodic reestimation of the Gaussian. Note:
      the default of 8640 is based on a month's worth of history at 5-minute
      intervals.

    @param reestimationPeriod - (int) how often we re-estimate the Gaussian
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
    self._probationaryPeriod = claLearningPeriod + estimationSamples
    self._claLearningPeriod = claLearningPeriod

    self._reestimationPeriod = reestimationPeriod


  def __eq__(self, o):
    # pylint: disable=W0212
    return (isinstance(o, AnomalyLikelihood) and
            self._iteration == o._iteration and
            self._historicalScores == o._historicalScores and
            self._distribution == o._distribution and
            self._probationaryPeriod == o._probationaryPeriod and
            self._claLearningPeriod == o._claLearningPeriod and
            self._reestimationPeriod == o._reestimationPeriod)
    # pylint: enable=W0212


  def __str__(self):
    return ("AnomalyLikelihood: %s %s %s %s %s %s" % (
      self._iteration,
      self._historicalScores,
      self._distribution,
      self._probationaryPeriod,
      self._claLearningPeriod,
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

    @param numIngested - (int) number of data points that have been added to the
      sliding window of historical data points.
    @param windowSize - (int) size of sliding window of historical data points.
    @param learningPeriod - (int) the number of iterations required for the CLA
      to learn the basic patterns in the dataset and for the anomaly score to
      'settle down'.
    """
    numShiftedOut = max(0, numIngested - windowSize)
    return min(numIngested, max(0, learningPeriod - numShiftedOut))


  def anomalyProbability(self, value, anomalyScore, timestamp=None):
    """
    Compute the probability that the current value plus anomaly score represents
    an anomaly given the historical distribution of anomaly scores. The closer
    the number is to 1, the higher the chance it is an anomaly.

    @param value - the current metric ("raw") input value, eg. "orange", or
                   '21.2' (deg. Celsius), ...
    @param anomalyScore - the current anomaly score
    @param timestamp - (optional) timestamp of the ocurrence,
                       default (None) results in using iteration step.
    @return theanomalyLikelihood for this record.
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
          learningPeriod=self._claLearningPeriod)

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


#
# USAGE FOR LOW-LEVEL FUNCTIONS
# -----------------------------
#
# There are two primary interface routines:
#
# estimateAnomalyLikelihoods: batch routine, called initially and once in a
#                                while
# updateAnomalyLikelihoods: online routine, called for every new data point
#
# 1. Initially::
#
#    likelihoods, avgRecordList, estimatorParams = \
# estimateAnomalyLikelihoods(metric_data)
#
# 2. Whenever you get new data::
#
#    likelihoods, avgRecordList, estimatorParams = \
# updateAnomalyLikelihoods(data2, estimatorParams)
#
# 3. And again (make sure you use the new estimatorParams returned in the above
#   call to updateAnomalyLikelihoods!)::
#
#    likelihoods, avgRecordList, estimatorParams = \
# updateAnomalyLikelihoods(data3, estimatorParams)
#
# 4. Every once in a while update estimator with a lot of recent data::
#
#    likelihoods, avgRecordList, estimatorParams = \
# estimateAnomalyLikelihoods(lots_of_metric_data)
#
#
# PARAMS
# ~~~~~~
#
# The parameters dict returned by the above functions has the following
# structure. Note: the client does not need to know the details of this.
#
# ::
#
#  {
#    "distribution":               # describes the distribution
#      {
#        "name": STRING,           # name of the distribution, such as 'normal'
#        "mean": SCALAR,           # mean of the distribution
#        "variance": SCALAR,       # variance of the distribution
#
#        # There may also be some keys that are specific to the distribution
#      },
#
#    "historicalLikelihoods": []   # Contains the last windowSize likelihood
#                                  # values returned
#
#    "movingAverage":              # stuff needed to compute a rolling average
#                                  # of the anomaly scores
#      {
#        "windowSize": SCALAR,     # the size of the averaging window
#        "historicalValues": [],   # list with the last windowSize anomaly
#                                  # scores
#        "total": SCALAR,          # the total of the values in historicalValues
#      },
#
#  }


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
    print "In estimateAnomalyLikelihoods."
    print "Number of anomaly scores:", len(anomalyScores)
    print "Skip records=", skipRecords
    print "First 20:", anomalyScores[0:min(20, len(anomalyScores))]

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

    # HACK ALERT! The CLA model currently does not handle constant metric values
    # very well (time of day encoder changes sometimes lead to unstable SDR's
    # even though the metric is constant). Until this is resolved, we explicitly
    # detect and handle completely flat metric values by reporting them as not
    # anomalous.
    s = [r[1] for r in aggRecordList]
    metricValues = numpy.array(s)
    metricDistribution = estimateNormal(metricValues[skipRecords:],
                                        performLowerBoundCheck=False)

    if metricDistribution["variance"] < 1.5e-5:
      distributionParams = nullDistribution(verbosity = verbosity)

  # Estimate likelihoods based on this distribution
  likelihoods = numpy.array(dataValues, dtype=float)
  for i, s in enumerate(dataValues):
    likelihoods[i] = normalProbability(s, distributionParams)

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
    print "Discovered params="
    print params
    print "Number of likelihoods:", len(likelihoods)
    print "First 20 likelihoods:", (
      filteredLikelihoods[0:min(20, len(filteredLikelihoods))] )
    print "leaving estimateAnomalyLikelihoods"


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
    print "In updateAnomalyLikelihoods."
    print "Number of anomaly scores:", len(anomalyScores)
    print "First 20:", anomalyScores[0:min(20, len(anomalyScores))]
    print "Params:", params

  if len(anomalyScores) == 0:
    raise ValueError("Must have at least one anomalyScore")

  if not isValidEstimatorParams(params):
    raise ValueError("'params' is not a valid params structure")

  # For backward compatibility.
  if not params.has_key("historicalLikelihoods"):
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
    likelihoods[i]   = normalProbability(newAverage, params["distribution"])

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
    print "Number of likelihoods:", len(likelihoods)
    print "First 20 likelihoods:", likelihoods[0:min(20, len(likelihoods))]
    print "Leaving updateAnomalyLikelihoods."

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
        print "Malformed record:", record
      continue

    avg, historicalValues, total = (
      MovingAverage.compute(historicalValues, total, record[2], windowSize)
      )

    averagedRecordList.append( [record[0], record[1], avg] )

    if verbosity > 2:
      print "Aggregating input record:", record
      print "Result:", [record[0], record[1], avg]

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
    print "Returning nullDistribution"
  return {
    "name": "normal",
    "mean": 0.5,
    "variance": 1e6,
    "stdev": 1e3,
  }



def normalProbability(x, distributionParams):
  """
  Given the normal distribution specified in distributionParams, return
  the probability of getting samples > x
  This is essentially the Q-function
  """
  # Distribution is symmetrical around mean
  if x < distributionParams["mean"] :
    xp = 2*distributionParams["mean"] - x
    return 1.0 - normalProbability(xp, distributionParams)

  # How many standard deviations above the mean are we, scaled by 10X for table
  xs = 10*(x - distributionParams["mean"]) / distributionParams["stdev"]

  xs = round(xs)
  if xs > 70:
    return 0.0
  else:
    return Q[xs]



def isValidEstimatorParams(p):
  """
  :returns: ``True`` if ``p`` is a valid estimator params as might be returned
    by ``estimateAnomalyLikelihoods()`` or ``updateAnomalyLikelihoods``,
    ``False`` otherwise.  Just does some basic validation.
  """
  if not isinstance(p, dict):
    return False
  if not p.has_key("distribution"):
    return False
  if not p.has_key("movingAverage"):
    return False
  dist = p["distribution"]
  if not (dist.has_key("mean") and dist.has_key("name")
          and dist.has_key("variance") and dist.has_key("stdev")):
    return False

  return True



# Table lookup for Q function, from wikipedia
# http://en.wikipedia.org/wiki/Q-function
Q = numpy.zeros(71)
Q[0] = 0.500000000
Q[1] = 0.460172163
Q[2] = 0.420740291
Q[3] = 0.382088578
Q[4] = 0.344578258
Q[5] = 0.308537539
Q[6] = 0.274253118
Q[7] = 0.241963652
Q[8] = 0.211855399
Q[9] = 0.184060125
Q[10] = 0.158655254
Q[11] = 0.135666061
Q[12] = 0.115069670
Q[13] = 0.096800485
Q[14] = 0.080756659
Q[15] = 0.066807201
Q[16] = 0.054799292
Q[17] = 0.044565463
Q[18] = 0.035930319
Q[19] = 0.028716560
Q[20] = 0.022750132
Q[21] = 0.017864421
Q[22] = 0.013903448
Q[23] = 0.010724110
Q[24] = 0.008197536
Q[25] = 0.006209665
Q[26] = 0.004661188
Q[27] = 0.003466974
Q[28] = 0.002555130
Q[29] = 0.001865813
Q[30] = 0.001349898
Q[31] = 0.000967603
Q[32] = 0.000687138
Q[33] = 0.000483424
Q[34] = 0.000336929
Q[35] = 0.000232629
Q[36] = 0.000159109
Q[37] = 0.000107800
Q[38] = 0.000072348
Q[39] = 0.000048096
Q[40] = 0.000031671

# From here on use the approximation in http://cnx.org/content/m11537/latest/
Q[41] = 0.000021771135897
Q[42] = 0.000014034063752
Q[43] = 0.000008961673661
Q[44] = 0.000005668743475
Q[45] = 0.000003551942468
Q[46] = 0.000002204533058
Q[47] = 0.000001355281953
Q[48] = 0.000000825270644
Q[49] = 0.000000497747091
Q[50] = 0.000000297343903
Q[51] = 0.000000175930101
Q[52] = 0.000000103096834
Q[53] = 0.000000059836778
Q[54] = 0.000000034395590
Q[55] = 0.000000019581382
Q[56] = 0.000000011040394
Q[57] = 0.000000006164833
Q[58] = 0.000000003409172
Q[59] = 0.000000001867079
Q[60] = 0.000000001012647
Q[61] = 0.000000000543915
Q[62] = 0.000000000289320
Q[63] = 0.000000000152404
Q[64] = 0.000000000079502
Q[65] = 0.000000000041070
Q[66] = 0.000000000021010
Q[67] = 0.000000000010644
Q[68] = 0.000000000005340
Q[69] = 0.000000000002653
Q[70] = 0.000000000001305
