# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013-2014, Numenta, Inc.  Unless you have an agreement
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
Test the anomaly likelihood stuff with specific artificial distributions of
anomaly scores. We want to specifically cover the various situations Jeff drew
on the board.

Some of the tests currently don't pass and are marked as such. We understand why
but fixing them needs a deeper algoerithm discussion.
"""

import copy
import datetime
import unittest2 as unittest

from nupic.algorithms import anomaly_likelihood as an
from nupic.support.unittesthelpers.testcasebase import TestCaseBase



def _getDateList(numSamples, startDatetime):
  """
  Generate a sequence of sample dates starting at startDatetime and incrementing
  every minute.
  """
  dateList = []
  td = datetime.timedelta(minutes=1)
  curDate = startDatetime + td
  for _ in range(numSamples):
    dateList.append(curDate)
    curDate = curDate + td
  return dateList




class ArtificialAnomalyTest(TestCaseBase):


  def assertWithinEpsilon(self, a, b, epsilon=0.001):
    self.assertLessEqual(abs(a - b), epsilon,
                         "Values %g and %g are not within %g" % (a, b, epsilon))


  @staticmethod
  def _addSampleData(origData=None, numSamples=1440, spikeValue=1.0,
                     spikePeriod=20):
    """
    Add sample anomaly data to the existing data list and return it.
    Note: this does not modify the original data list
    Note 2: here we just add in increasing integers as the metric value
    """
    if origData is None:
      origData = []
    # Get a list of dates
    if len(origData) > 0:
      lastDate = origData[-1][0]
    else:
      lastDate = datetime.datetime(2013, 2, 3)
    dateList = _getDateList(numSamples, lastDate)

    # Add anomaly spikes as appropriate
    data = copy.copy(origData)
    for idx, date in enumerate(dateList):
      if (spikePeriod > 0) and ( (idx + 1) % spikePeriod == 0):
        data.append([date, idx, spikeValue])
      else:
        data.append([date, idx, 0.0])
    return data


  def testCaseSingleSpike(self):
    """
    No anomalies, and then you see a single spike. The likelihood of that
    spike should be 0
    """
    data = self._addSampleData(spikePeriod=0, numSamples=1000)

    _, _, estimatorParams = (
      an.estimateAnomalyLikelihoods(data[0:1000])
    )

    data = self._addSampleData(numSamples=1, spikePeriod=1)
    likelihoods1, _, _ = (
      an.updateAnomalyLikelihoods(data, estimatorParams)
    )

    self.assertWithinEpsilon(likelihoods1[0], 0.0)


  def testCaseUnusuallyHighSpikeFrequency(self):
    """
    Test B: one anomaly spike every 20 records. Then we suddenly get a bunch
    in a row. The likelihood of those spikes should be low.
    """
    data = self._addSampleData(spikePeriod=20, numSamples=1019)

    _, _, estimatorParams = (
      an.estimateAnomalyLikelihoods(data[0:1000])
    )

    # If we continue to see the same distribution, we should get reasonable
    # likelihoods
    data = self._addSampleData(numSamples=119, spikePeriod=20)
    likelihoods1, _, estimatorParams1 = (
      an.updateAnomalyLikelihoods(data, estimatorParams)
    )

    # The minimum likelihood should be reasonably high
    self.assertTrue((likelihoods1.min() > 0.1 ))

    data = self._addSampleData(numSamples=20, spikePeriod=2)
    likelihoods2, _, _ = (
      an.updateAnomalyLikelihoods(data, estimatorParams1)
    )

    # The likelihood once you get past the initial averaging should be very low.
    self.assertTrue((likelihoods2[5:].sum() / 15.0) < 0.001)


  @unittest.skip("Currently fails because the periodicity is greater than the "
                 "window size. Requires some algorithm enhancements. "
                 "Filed as https://github.com/numenta/nupic/issues/948.")
  def testCaseMissingSpike(self):
    """
    Test C: one anomaly every 20 records, but then see none. The likelihood
    at the end should be very low.
    """

    # Initial data
    data = self._addSampleData(spikePeriod=20, numSamples=1019)
    _, _, estimatorParams = (
      an.estimateAnomalyLikelihoods(data[0:1000])
    )

    # Now feed in none
    data = self._addSampleData(numSamples=100, spikePeriod=0)
    likelihoods2, _, _ = (
      an.updateAnomalyLikelihoods(data, estimatorParams)
    )

    # The likelihood once you get past the initial averaging should be very low.
    self.assertTrue((likelihoods2[5:].sum() / 15.0) < 0.0001)


  def testCaseContinuousBunchesOfSpikes(self):
    """
    Test D: bunches of anomalies every 20 records that continue. This should not
    be anomalous.
    """

    # Generate initial data
    data = []
    for _ in range(30):
      data = self._addSampleData(data, spikePeriod=0, numSamples=30)
      data = self._addSampleData(data, spikePeriod=3, numSamples=10)

    _, _, estimatorParams = (
      an.estimateAnomalyLikelihoods(data[0:1000])
    )

    # Now feed in the same distribution
    data = self._addSampleData(spikePeriod=0, numSamples=30)
    data = self._addSampleData(data, spikePeriod=3, numSamples=10)
    likelihoods2, _, _ = (
      an.updateAnomalyLikelihoods(data, estimatorParams)
    )

    # The likelihood should be reasonable high everywhere
    self.assertTrue(likelihoods2.min() > 0.01)


  def testCaseIncreasedSpikeFrequency(self):
    """
    Test E: bunches of anomalies every 20 records that become even more
    frequent. This should be anomalous.
    """

    # Generate initial data
    data = []
    for _ in range(30):
      data = self._addSampleData(data, spikePeriod=0, numSamples=30)
      data = self._addSampleData(data, spikePeriod=3, numSamples=10)

    _, _, estimatorParams = (
      an.estimateAnomalyLikelihoods(data[0:1000])
    )

    # Now feed in a more frequent distribution
    data = self._addSampleData(spikePeriod=0, numSamples=30)
    data = self._addSampleData(data, spikePeriod=1, numSamples=10)
    likelihoods2, _, _ = (
      an.updateAnomalyLikelihoods(data, estimatorParams)
    )

    # The likelihood should become anomalous but only near the end
    self.assertTrue(likelihoods2[0:30].min() > 0.01)
    self.assertTrue(likelihoods2[-5:].min() < 0.002)


  @unittest.skip("Currently fails because the periodicity is greater than the "
                 "window size. Requires some algorithm enhancements. "
                 "Filed as https://github.com/numenta/nupic/issues/948.")
  def testCaseMissingBunchesOfSpikes(self):
    """
    Test F: bunches of anomalies every 20 records that disappear. This should
    be anomalous.
    """
    # Generate initial data
    data = []
    for _ in range(30):
      data = self._addSampleData(data, spikePeriod=0, numSamples=30)
      data = self._addSampleData(data, spikePeriod=3, numSamples=10)

    _, _, estimatorParams = (
      an.estimateAnomalyLikelihoods(data)
    )

    # Now feed in a more frequent distribution
    data = self._addSampleData(spikePeriod=0, numSamples=40)
    likelihoods2, _, _ = (
      an.updateAnomalyLikelihoods(data, estimatorParams)
    )

    # The likelihood should become anomalous but only near the end
    self.assertTrue(likelihoods2[0:30].min() > 0.01)
    self.assertTrue(likelihoods2[-5:].min() < 0.00001)


  def testCaseIncreasedAnomalyScore(self):
    """
    Test F: small anomaly score every 20 records, but then a large one when you
    would expect a small one. This should be anomalous.
    """

    # Generate initial data
    data = []
    data = self._addSampleData(data, spikePeriod=20,
                               spikeValue=0.4, numSamples=1000)

    _, _, estimatorParams = (
      an.estimateAnomalyLikelihoods(data)
    )

    # Now feed in a more frequent distribution
    data = self._addSampleData(spikePeriod=20, spikeValue=1.0,
                               numSamples=100)
    likelihoods2, _, _ = (
      an.updateAnomalyLikelihoods(data, estimatorParams)
    )

    # We should detect highly unusual behavior
    self.assertTrue(likelihoods2.min() < 0.0003)

    # We should detect it pretty often
    self.assertTrue((likelihoods2 < 0.0003).sum() > 40)



if __name__ == "__main__":
  unittest.main()
