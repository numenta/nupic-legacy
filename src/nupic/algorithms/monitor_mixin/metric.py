# Copyright 2014 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

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
