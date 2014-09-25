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
  """
  __metaclass__ = abc.ABCMeta


  def __init__(self, *args, **kwargs):
    super(MonitorMixinBase, self).__init__(*args, **kwargs)

    # Mapping from key (string) => trace (Trace)
    self._traces = None
    self.clearHistory()


  def clearHistory(self):
    """
    Clears the stored history.
    """
    self._traces = {}


  @staticmethod
  def prettyPrintTraces(traces, breakOnResets=None):
    """
    Returns pretty-printed table of traces.

    @param traces (list) Traces to print in table
    @param breakOnResets (BoolsTrace) Trace of resets to break table on

    @return (string) Pretty-printed table of traces.
    """
    assert len(traces) > 0, "No traces found"
    table = PrettyTable(["Iteration"] + [trace.title for trace in traces])

    for i in xrange(len(traces[0].data)):
      if breakOnResets and breakOnResets.data[i]:
        table.add_row(["<reset>"] * (len(traces) + 1))
      table.add_row([i] +
        [trace.prettyPrintDatum(trace.data[i]) for trace in traces])

    return table.get_string()


  def getDefaultTraces(self, verbosity=1):
    """
    Returns list of default traces. (To be overridden.)

    @param verbosity (int) Verbosity level

    @return (list) Default traces
    """
    return []
