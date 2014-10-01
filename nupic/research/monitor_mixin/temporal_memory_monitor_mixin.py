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

from prettytable import PrettyTable

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


  def getTraceActiveColumns(self):
    """
    @return (Trace) Trace of active columns
    """
    return self._mmTraces["activeColumns"]


  def getTracePredictiveCells(self):
    """
    @return (Trace) Trace of predictive cells
    """
    return self._mmTraces["predictiveCells"]


  def getTraceSequenceLabels(self):
    """
    @return (Trace) Trace of sequence labels
    """
    return self._mmTraces["sequenceLabels"]


  def getTraceResets(self):
    """
    @return (Trace) Trace of resets
    """
    return self._mmTraces["resets"]


  def getTracePredictedActiveCells(self):
    """
    @return (Trace) Trace of predicted => active cells
    """
    self._computeTransitionTraces()
    return self._mmTraces["predictedActiveCells"]


  def getTracePredictedInactiveCells(self):
    """
    @return (Trace) Trace of predicted => inactive cells
    """
    self._computeTransitionTraces()
    return self._mmTraces["predictedInactiveCells"]


  def getTracePredictedActiveColumns(self):
    """
    @return (Trace) Trace of predicted => active columns
    """
    self._computeTransitionTraces()
    return self._mmTraces["predictedActiveColumns"]


  def getTracePredictedInactiveColumns(self):
    """
    @return (Trace) Trace of predicted => inactive columns
    """
    self._computeTransitionTraces()
    return self._mmTraces["predictedInactiveColumns"]


  def getTraceUnpredictedActiveColumns(self):
    """
    @return (Trace) Trace of unpredicted => active columns
    """
    self._computeTransitionTraces()
    return self._mmTraces["unpredictedActiveColumns"]


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
        self._mmData["predictedActiveCellsForSequence"].values()):
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
          self._mmData["predictedActiveCellsForSequence"].values()):
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


  def prettyPrintSequenceCellRepresentations(self, sortby="Column"):
    """
    Pretty print the cell representations for sequences in the history.

    @param sortby (string) Column of table to sort by

    @return (string) Pretty-printed text
    """
    self._computeTransitionTraces()
    table = PrettyTable(["Pattern", "Column", "predicted=>active cells"])

    for sequenceLabel, predictedActiveCells in (
          self._mmData["predictedActiveCellsForSequence"].iteritems()):
      cellsForColumn = self.connections.mapCellsToColumns(predictedActiveCells)
      for column, cells in cellsForColumn.iteritems():
        table.add_row([sequenceLabel, column, list(cells)])

    return table.get_string(sortby=sortby)


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

    self._mmData["predictedActiveCellsForSequence"] = defaultdict(set)

    self._mmTraces["predictedActiveCells"] = IndicesTrace(self,
      "predicted => active cells (correct)")
    self._mmTraces["predictedInactiveCells"] = IndicesTrace(self,
      "predicted => inactive cells (extra)")
    self._mmTraces["predictedActiveColumns"] = IndicesTrace(self,
      "predicted => active columns (correct)")
    self._mmTraces["predictedInactiveColumns"] = IndicesTrace(self,
      "predicted => inactive columns (extra)")
    self._mmTraces["unpredictedActiveColumns"] = IndicesTrace(self,
      "unpredicted => active columns (bursting)")

    predictedCellsTrace = self._mmTraces["predictedCells"]

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
            self._mmData["predictedActiveCellsForSequence"][sequenceLabel].add(
              predictedCell)
        else:
          predictedInactiveCells.add(predictedCell)
          predictedInactiveColumns.add(predictedColumn)

      unpredictedActiveColumns = activeColumns - predictedActiveColumns

      self._mmTraces["predictedActiveCells"].data.append(predictedActiveCells)
      self._mmTraces["predictedInactiveCells"].data.append(predictedInactiveCells)
      self._mmTraces["predictedActiveColumns"].data.append(predictedActiveColumns)
      self._mmTraces["predictedInactiveColumns"].data.append(
        predictedInactiveColumns)
      self._mmTraces["unpredictedActiveColumns"].data.append(
        unpredictedActiveColumns)

    self._transitionTracesStale = False


  # ==============================
  # Overrides
  # ==============================

  def compute(self, activeColumns, sequenceLabel=None, **kwargs):
    self._mmTraces["predictedCells"].data.append(self.predictiveCells)

    super(TemporalMemoryMonitorMixin, self).compute(activeColumns, **kwargs)

    self._mmTraces["predictiveCells"].data.append(self.predictiveCells)
    self._mmTraces["activeColumns"].data.append(activeColumns)
    self._mmTraces["sequenceLabels"].data.append(sequenceLabel)

    self._mmTraces["resets"].data.append(self._resetActive)
    self._resetActive = False

    self._transitionTracesStale = True


  def reset(self):
    super(TemporalMemoryMonitorMixin, self).reset()

    self._resetActive = True


  def mmGetDefaultTraces(self, verbosity=1):
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


  def mmGetDefaultMetrics(self, verbosity=1):
    resetsTrace = self.getTraceResets()
    return ([Metric.createFromTrace(trace, excludeResets=resetsTrace)
            for trace in self.mmGetDefaultTraces()[:-1]] +
            [self.getMetricSequencesPredictedActiveCellsPerColumn(),
             self.getMetricSequencesPredictedActiveCellsShared()])


  def mmClearHistory(self):
    super(TemporalMemoryMonitorMixin, self).mmClearHistory()

    self._mmTraces["predictedCells"] = IndicesTrace(self, "predicted cells")
    self._mmTraces["activeColumns"] = IndicesTrace(self, "active columns")
    self._mmTraces["predictiveCells"] = IndicesTrace(self, "predictive cells")
    self._mmTraces["sequenceLabels"] = StringsTrace(self, "sequence labels")
    self._mmTraces["resets"] = BoolsTrace(self, "resets")

    self._transitionTracesStale = True
