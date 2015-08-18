# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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
Metric class used in monitor mixin framework.
"""

import numpy



class Metric(object):
  """
  A metric computed over a set of data (usually from a `CountsTrace`).
  """

  def __init__(self, monitor, title, data):
    """
    @param monitor (MonitorMixinBase) Monitor Mixin instance that generated
                                      this trace
    @param title   (string)           Title
    @param data    (list)             List of numbers to compute metric from
    """
    self.monitor = monitor
    self.title = title

    self.min = None
    self.max = None
    self.sum = None
    self.mean = None
    self.standardDeviation = None

    self._computeStats(data)


  @staticmethod
  def createFromTrace(trace, excludeResets=None):
    data = list(trace.data)
    if excludeResets is not None:
      data = [x for i, x in enumerate(trace.data) if not excludeResets.data[i]]
    return Metric(trace.monitor, trace.title, data)


  def copy(self):
    metric = Metric(self.monitor, self.title, [])

    metric.min = self.min
    metric.max = self.max
    metric.sum = self.sum
    metric.mean = self.mean
    metric.standardDeviation = self.standardDeviation

    return metric


  def prettyPrintTitle(self):
    return ("[{0}] {1}".format(self.monitor.mmName, self.title)
            if self.monitor.mmName is not None else self.title)


  def _computeStats(self, data):
    if not len(data):
      return

    self.min = min(data)
    self.max = max(data)
    self.sum = sum(data)
    self.mean = numpy.mean(data)
    self.standardDeviation = numpy.std(data)


  def getStats(self, sigFigs=7):
    if self.mean is None:
      return [None, None, None, None, None]
    return [round(self.mean, sigFigs),
            round(self.standardDeviation, sigFigs),
            round(self.min, sigFigs),
            round(self.max, sigFigs),
            round(self.sum, sigFigs)]
