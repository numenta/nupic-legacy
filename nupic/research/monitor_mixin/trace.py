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


  def __init__(self, title):
    self.title = title

    self.data = []


  @staticmethod
  def prettyPrintDatum(datum):
    """
    @param datum (object) Datum from `self.data` to pretty-print

    @return (string) Pretty-printed datum
    """
    return str(datum)



class IndicesTrace(Trace):
  """
  Each entry contains indices (for example of predicted => active cells).
  """

  def makeCountsTrace(self):
    """
    @return (CountsTrace) A new Trace made up of counts of this trace's indices.
    """
    trace = CountsTrace("# {0}".format(self.title))
    trace.data = [len(indices) for indices in self.data]
    return trace


  def makeCumCountsTrace(self):
    """
    @return (CountsTrace) A new Trace made up of cumulative counts of this
    trace's indices.
    """
    trace = CountsTrace("# (cumulative) {0}".format(self.title))
    countsTrace = self.makeCountsTrace()

    def accumulate(iterator):
      total = 0
      for item in iterator:
        total += item
        yield total

    trace.data = list(accumulate(countsTrace.data))
    return trace



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
