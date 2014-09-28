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
Temporal Memory mixin that enables detailed monitoring of history.
"""

from collections import defaultdict

from nupic.research.monitor_mixin.trace import (
  IndicesTrace, BoolsTrace, StringsTrace)
from nupic.research.monitor_mixin.metric import Metric
from nupic.research.monitor_mixin.monitor_mixin_base import MonitorMixinBase


class TemporalMemoryMonitorMixin(MonitorMixinBase):
  """
  Mixin for TemporalMemory that stores a detailed history, for inspection and
  debugging.
  """

  def __init__(self, *args, **kwargs):
    super(TemporalMemoryMonitorMixin, self).__init__(*args, **kwargs)

    self._resetActive = True  # First iteration is always a reset
    self._transitionTracesStale = True


  def getTraceActiveColumns(self):
    """
    @return (Trace) Trace of active columns
    """
    return self._traces["activeColumns"]


  def getTracePredictiveCells(self):
    """
    @return (Trace) Trace of predictive cells
    """
    return self._traces["predictiveCells"]


  def getTraceSequenceLabels(self):
    """
    @return (Trace) Trace of sequence labels
    """
    return self._traces["sequenceLabels"]


  def getTraceResets(self):
    """
    @return (Trace) Trace of resets
    """
    return self._traces["resets"]


  def getTracePredictedActiveCells(self):
    """
    @return (Trace) Trace of predicted => active cells
    """
    self._computeTransitionTraces()
    return self._traces["predictedActiveCells"]


  def getTracePredictedInactiveCells(self):
    """
    @return (Trace) Trace of predicted => inactive cells
    """
    self._computeTransitionTraces()
    return self._traces["predictedInactiveCells"]


  def getTracePredictedActiveColumns(self):
    """
    @return (Trace) Trace of predicted => active columns
    """
    self._computeTransitionTraces()
    return self._traces["predictedActiveColumns"]


  def getTracePredictedInactiveColumns(self):
    """
    @return (Trace) Trace of predicted => inactive columns
    """
    self._computeTransitionTraces()
    return self._traces["predictedInactiveColumns"]


  def getTraceUnpredictedActiveColumns(self):
    """
    @return (Trace) Trace of unpredicted => active columns
    """
    self._computeTransitionTraces()
    return self._traces["unpredictedActiveColumns"]


  def getMetricFromTrace(self, trace):
    """
    Convenience method to compute a metric over an indices trace, excluding
    resets.

    @param (IndicesTrace) Trace of indices

    @return (Metric) Metric over trace excluding resets
    """
    return Metric.createFromTrace(trace.makeCountsTrace(),
                                  excludeResets=self.getTraceResets())


  def getMetricSequencesPredictedActiveCellsPerColumn(self):
    """
    Metric for number of predicted => active cells per column for each sequence

    @return (Metric) metric
    """
    self._computeTransitionTraces()

    numCellsPerColumn = []

    for predictedActiveCells in (
        self._data["predictedActiveCellsForSequence"].values()):
      cellsForColumn = self.connections.mapCellsToColumns(predictedActiveCells)
      numCellsPerColumn += [len(x) for x in cellsForColumn.values()]

    return Metric(self,
                  "# predicted => active cells per column for each sequence",
                  numCellsPerColumn)


  def getMetricSequencesPredictedActiveCellsShared(self):
    """
    Metric for number of sequences each predicted => active cell appears in

    Note: This metric is flawed when it comes to high-order sequences.

    @return (Metric) metric
    """
    self._computeTransitionTraces()

    numSequencesForCell = defaultdict(lambda: 0)

    for predictedActiveCells in (
          self._data["predictedActiveCellsForSequence"].values()):
      for cell in predictedActiveCells:
        numSequencesForCell[cell] += 1

    return Metric(self,
                  "# sequences each predicted => active cells appears in",
                  numSequencesForCell.values())


  def prettyPrintConnections(self):
    """
    Pretty print the connections in the temporal memory.

    TODO: Use PrettyTable.

    @return (string) Pretty-printed text
    """
    text = ""

    text += ("Segments: (format => "
             "[[(source cell, permanence), ...], ...])\n")
    text += "------------------------------------\n"

    columns = range(self.connections.numberOfColumns())

    for column in columns:
      cells = self.connections.cellsForColumn(column)

      for cell in cells:
        segmentDict = dict()

        for seg in self.connections.segmentsForCell(cell):
          synapseList = []

          for synapse in self.connections.synapsesForSegment(seg):
            (_, sourceCell, permanence) = self.connections.dataForSynapse(
              synapse)

            synapseList.append((sourceCell,
                                "{0:.2f}".format(permanence)))

          segmentDict[seg] = synapseList

        text += ("Column {0} / Cell {1}:\t{2}\n".format(
          column, cell, segmentDict.values()))

      if column < len(columns) - 1:  # not last
        text += "\n"

    text += "------------------------------------\n"

    return text


  # ==============================
  # Helper methods
  # ==============================

  def _computeTransitionTraces(self):
    """
    Computes the transition traces, if necessary.

    Transition traces are the following:

        predicted => active cells
        predicted => inactive cells
        predicted => active columns
        predicted => inactive columns
        unpredicted => active columns
    """
    if not self._transitionTracesStale:
      return

    self._traces["predictedActiveCells"] = IndicesTrace(self,
      "predicted => active cells (correct)")
    self._traces["predictedInactiveCells"] = IndicesTrace(self,
      "predicted => inactive cells (extra)")
    self._traces["predictedActiveColumns"] = IndicesTrace(self,
      "predicted => active columns (correct)")
    self._traces["predictedInactiveColumns"] = IndicesTrace(self,
      "predicted => inactive columns (extra)")
    self._traces["unpredictedActiveColumns"] = IndicesTrace(self,
      "unpredicted => active columns (bursting)")

    predictedCellsTrace = self._traces["predictedCells"]

    for i, activeColumns in enumerate(self.getTraceActiveColumns().data):
      predictedActiveCells = set()
      predictedInactiveCells = set()
      predictedActiveColumns = set()
      predictedInactiveColumns = set()

      for predictedCell in predictedCellsTrace.data[i]:
        predictedColumn = self.connections.columnForCell(predictedCell)

        if predictedColumn  in activeColumns:
          predictedActiveCells.add(predictedCell)
          predictedActiveColumns.add(predictedColumn)

          sequenceLabel = self.getTraceSequenceLabels().data[i]
          if sequenceLabel is not None:
            self._data["predictedActiveCellsForSequence"][sequenceLabel].add(
              predictedCell)
        else:
          predictedInactiveCells.add(predictedCell)
          predictedInactiveColumns.add(predictedColumn)

      unpredictedActiveColumns = activeColumns - predictedActiveColumns

      self._traces["predictedActiveCells"].data.append(predictedActiveCells)
      self._traces["predictedInactiveCells"].data.append(predictedInactiveCells)
      self._traces["predictedActiveColumns"].data.append(predictedActiveColumns)
      self._traces["predictedInactiveColumns"].data.append(
        predictedInactiveColumns)
      self._traces["unpredictedActiveColumns"].data.append(
        unpredictedActiveColumns)

    self._transitionTracesStale = False


  # ==============================
  # Overrides
  # ==============================

  def compute(self, activeColumns, sequenceLabel=None, **kwargs):
    self._traces["predictedCells"].data.append(self.predictiveCells)

    super(TemporalMemoryMonitorMixin, self).compute(activeColumns, **kwargs)

    self._traces["predictiveCells"].data.append(self.predictiveCells)
    self._traces["activeColumns"].data.append(activeColumns)
    self._traces["sequenceLabels"].data.append(sequenceLabel)

    self._traces["resets"].data.append(self._resetActive)
    self._resetActive = False

    self._transitionTracesStale = True


  def reset(self):
    super(TemporalMemoryMonitorMixin, self).reset()

    self._resetActive = True


  def getDefaultTraces(self, verbosity=1):
    traces = [
      self.getTraceActiveColumns(),
      self.getTracePredictedActiveColumns(),
      self.getTracePredictedInactiveColumns(),
      self.getTraceUnpredictedActiveColumns(),
      self.getTracePredictedActiveCells(),
      self.getTracePredictedInactiveCells()
    ]

    if verbosity == 1:
      traces = [trace.makeCountsTrace() for trace in traces]

    return traces + [self.getTraceSequenceLabels()]


  def getDefaultMetrics(self, verbosity=1):
    resetsTrace = self.getTraceResets()
    return ([Metric.createFromTrace(trace, excludeResets=resetsTrace)
            for trace in self.getDefaultTraces()[:-1]] +
            [self.getMetricSequencesPredictedActiveCellsPerColumn(),
             self.getMetricSequencesPredictedActiveCellsShared()])


  def clearHistory(self):
    super(TemporalMemoryMonitorMixin, self).clearHistory()

    self._traces["predictedCells"] = IndicesTrace(self, "predicted cells")
    self._traces["activeColumns"] = IndicesTrace(self, "active columns")
    self._traces["predictiveCells"] = IndicesTrace(self, "predictive cells")
    self._traces["sequenceLabels"] = StringsTrace(self, "sequence labels")
    self._traces["resets"] = BoolsTrace(self, "resets")

    self._data["predictedActiveCellsForSequence"] = defaultdict(set)

    self._transitionTracesStale = True
