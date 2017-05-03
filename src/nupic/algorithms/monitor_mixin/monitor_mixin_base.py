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
MonitorMixinBase class used in monitor mixin framework.

Using a monitor mixin with your algorithm
-----------------------------------------

1. Create a subclass of your algorithm class, with the first parent being the
corresponding Monitor class. For example,

    class MonitoredTemporalMemory(TemporalMemoryMonitorMixin,
                                  TemporalMemory): pass

2. Create an instance of the monitored class and use that.

    instance = MonitoredTemporalMemory()
    # Run data through instance

3. Now you can call the following methods to print monitored data from of your
instance:

- instance.mmPrettyPrintMetrics(instance.mmGetDefaultMetrics())
- instance.mmPrettyPrintTraces(instance.mmGetDefaultTraces())

Each specific monitor also has specific methods you can call to extract data
out of it.

Adding data to a monitor mixin
-----------------------------------------

1. Create a variable for the data you want to capture in your specific monitor's
`mmClearHistory` method. For example,

    self._mmTraces["predictedCells"] = IndicesTrace(self, "predicted cells")

Make sure you use the correct type of trace for your data.

2. Add data to this trace in your algorithm's `compute` method (or anywhere
else).

    self._mmTraces["predictedCells"].data.append(set(self.getPredictiveCells()))

3. You can optionally add this trace as a default trace in `mmGetDefaultTraces`,
or define a function to return that trace:

    def mmGetTracePredictiveCells(self):

Any trace can be converted to a metric using the utility functions provided in
the framework (see `metric.py`).

Extending the functionality of the monitor mixin framework
-----------------------------------------

If you want to add new types of traces and metrics, add them to `trace.py`
and `metric.py`. You can also create new monitors by simply defining new classes
that inherit from MonitorMixinBase.
"""

import abc
import numpy
from prettytable import PrettyTable

from nupic.algorithms.monitor_mixin.plot import Plot



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
  def mmPrettyPrintMetrics(metrics, sigFigs=5):
    """
    Returns pretty-printed table of metrics.

    @param metrics (list) Traces to print in table
    @param sigFigs (int)  Number of significant figures to print

    @return (string) Pretty-printed table of metrics.
    """
    assert len(metrics) > 0, "No metrics found"
    table = PrettyTable(["Metric", "mean", "standard deviation",
                         "min", "max", "sum", ])

    for metric in metrics:
      table.add_row([metric.prettyPrintTitle()] + metric.getStats())

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


  def mmGetCellTracePlot(self, cellTrace, cellCount, activityType, title="",
                         showReset=False, resetShading=0.25):
    """
    Returns plot of the cell activity. Note that if many timesteps of
    activities are input, matplotlib's image interpolation may omit activities
    (columns in the image).

    @param cellTrace    (list)   a temporally ordered list of sets of cell
                                 activities

    @param cellCount    (int)    number of cells in the space being rendered

    @param activityType (string) type of cell activity being displayed

    @param title        (string) an optional title for the figure

    @param showReset    (bool)   if true, the first set of cell activities
                                 after a reset will have a grayscale background

    @param resetShading (float)  applicable if showReset is true, specifies the
                                 intensity of the reset background with 0.0
                                 being white and 1.0 being black

    @return (Plot) plot
    """
    plot = Plot(self, title)
    resetTrace = self.mmGetTraceResets().data
    data = numpy.zeros((cellCount, 1))
    for i in xrange(len(cellTrace)):
      # Set up a "background" vector that is shaded or blank
      if showReset and resetTrace[i]:
        activity = numpy.ones((cellCount, 1)) * resetShading
      else:
        activity = numpy.zeros((cellCount, 1))

      activeIndices = cellTrace[i]
      activity[list(activeIndices)] = 1
      data = numpy.concatenate((data, activity), 1)

    plot.add2DArray(data, xlabel="Time", ylabel=activityType, name=title)
    return plot
