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


class Anomaly(object):
  """basic class that computes anomaly"""

  def computeAnomalyScore(self, activeColumns, prevPredictedColumns):
    """Compute the anomaly score as the percent of active columns not predicted.
  
    :param activeColumns: array of active column indices
    :param prevPredictedColumns: array of columns indices predicted in previous step
    :returns: the computed anomaly score
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

