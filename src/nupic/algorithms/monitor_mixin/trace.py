# Copyright 2014 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""
Trace classes used in monitor mixin framework.
"""

import abc

import numpy



class Trace(object):
  """
  A record of the past data the algorithm has seen, with an entry for each
  iteration.
  """
  __metaclass__ = abc.ABCMeta


  def __init__(self, monitor, title):
    """
    @param monitor (MonitorMixinBase) Monitor Mixin instance that generated
                                      this trace
    @param title   (string)           Title
    """
    self.monitor = monitor
    self.title = title

    self.data = []


  def prettyPrintTitle(self):
    return ("[{0}] {1}".format(self.monitor.mmName, self.title)
            if self.monitor.mmName is not None else self.title)


  @staticmethod
  def prettyPrintDatum(datum):
    """
    @param datum (object) Datum from `self.data` to pretty-print

    @return (string) Pretty-printed datum
    """
    return str(datum) if datum is not None else ""



class IndicesTrace(Trace):
  """
  Each entry contains indices (for example of predicted => active cells).
  """

  def makeCountsTrace(self):
    """
    @return (CountsTrace) A new Trace made up of counts of this trace's indices.
    """
    trace = CountsTrace(self.monitor, "# {0}".format(self.title))
    trace.data = [len(indices) for indices in self.data]
    return trace


  def makeCumCountsTrace(self):
    """
    @return (CountsTrace) A new Trace made up of cumulative counts of this
    trace's indices.
    """
    trace = CountsTrace(self.monitor, "# (cumulative) {0}".format(self.title))
    countsTrace = self.makeCountsTrace()

    def accumulate(iterator):
      total = 0
      for item in iterator:
        total += item
        yield total

    trace.data = list(accumulate(countsTrace.data))
    return trace


  @staticmethod
  def prettyPrintDatum(datum):
    return str(sorted(list(datum)))



class BoolsTrace(Trace):
  """
  Each entry contains bools (for example resets).
  """
  pass



class CountsTrace(Trace):
  """
  Each entry contains counts (for example # of predicted => active cells).
  """
  pass



class StringsTrace(Trace):
  """
  Each entry contains strings (for example sequence labels).
  """
  pass



class MetricsTrace(Trace):
  """
  Each entry contains Metrics (for example metric for # of predicted => active
  cells).
  """
  @staticmethod
  def prettyPrintDatum(datum):
    return ("min: {0:.2f}, max: {1:.2f}, sum: {2:.2f}, "
            "mean: {3:.2f}, std dev: {4:.2f}").format(
      datum.min, datum.max, datum.sum, datum.mean, datum.standardDeviation)
