# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
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

"""
MonitorMixinBase class used in monitor mixin framework.
"""

import abc

from prettytable import PrettyTable


class MonitorMixinBase(object):
  """
  Base class for MonitorMixin. Each subclass will be a mixin for a particular
  algorithm.

  All arguments, variables, and methods in monitor mixin classes should be
  prefixed with "mm" (to avoid collision with the classes they mix in to).
  """
  __metaclass__ = abc.ABCMeta


  def __init__(self, *args, **kwargs):
    """
    Note: If you set the kwarg "mmName", then pretty-printing of traces and
          metrics will include the name you specify as a tag before every title.
    """
    self.mmName = kwargs.get("mmName")
    if "mmName" in kwargs:
      del kwargs["mmName"]

    super(MonitorMixinBase, self).__init__(*args, **kwargs)

    # Mapping from key (string) => trace (Trace)
    self._mmTraces = None
    self._mmData = None
    self.mmClearHistory()


  def mmClearHistory(self):
    """
    Clears the stored history.
    """
    self._mmTraces = {}
    self._mmData = {}


  @staticmethod
  def mmPrettyPrintTraces(traces, breakOnResets=None):
    """
    Returns pretty-printed table of traces.

    @param traces (list) Traces to print in table
    @param breakOnResets (BoolsTrace) Trace of resets to break table on

    @return (string) Pretty-printed table of traces.
    """
    assert len(traces) > 0, "No traces found"
    table = PrettyTable(["#"] + [trace.prettyPrintTitle() for trace in traces])

    for i in xrange(len(traces[0].data)):
      if breakOnResets and breakOnResets.data[i]:
        table.add_row(["<reset>"] * (len(traces) + 1))
      table.add_row([i] +
        [trace.prettyPrintDatum(trace.data[i]) for trace in traces])

    return table.get_string().encode("utf-8")


  @staticmethod
  def mmPrettyPrintMetrics(metrics):
    """
    Returns pretty-printed table of metrics.

    @param metrics (list) Traces to print in table

    @return (string) Pretty-printed table of metrics.
    """
    assert len(metrics) > 0, "No metrics found"
    table = PrettyTable(["Metric",
                         "min", "max", "sum", "mean", "standard deviation"])

    for metric in metrics:
      table.add_row([metric.prettyPrintTitle(),
                     metric.min,
                     metric.max,
                     metric.sum,
                     metric.mean,
                     metric.standardDeviation])

    return table.get_string().encode("utf-8")


  def mmGetDefaultTraces(self, verbosity=1):
    """
    Returns list of default traces. (To be overridden.)

    @param verbosity (int) Verbosity level

    @return (list) Default traces
    """
    return []


  def mmGetDefaultMetrics(self, verbosity=1):
    """
    Returns list of default metrics. (To be overridden.)

    @param verbosity (int) Verbosity level

    @return (list) Default metrics
    """
    return []
