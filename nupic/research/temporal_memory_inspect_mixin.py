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
Temporal Memory mixin that enables detailed inspection of history.
"""

from collections import namedtuple

import numpy
from prettytable import PrettyTable



class TemporalMemoryInspectMixin(object):
  """
  Stores a detailed history, for inspection and debugging.
  """

  def __init__(self, *args, **kwargs):
    super(TemporalMemoryInspectMixin, self).__init__(*args, **kwargs)

    # Initialize history
    self.patterns = None
    self.sequenceLabels = None
    self.predictedActiveCellsList = None
    self.predictedInactiveCellsList = None
    self.predictedActiveColumnsList = None
    self.predictedInactiveColumnsList = None
    self.unpredictedActiveColumnsList = None
    self.clearHistory()


  def clearHistory(self):
    self.patterns = []
    self.sequenceLabels = []
    self.predictedActiveCellsList = []
    self.predictedInactiveCellsList = []
    self.predictedActiveColumnsList = []
    self.predictedInactiveColumnsList = []
    self.unpredictedActiveColumnsList = []


  def prettyPrintHistory(self, verbosity=0):
    """
    Pretty print history.

    @param verbosity (int) Verbosity level

    @return (string) Pretty-printed text
    """
    cols = ["#",
            "Pattern",
            "Sequence Label",
            "pred=>active columns",
            "pred=>inactive columns",
            "unpred=>active columns",
            "pred=>active cells",
            "pred=>inactive cells"]

    if verbosity == 0:
      cols[1] = "Pattern (# bits)"
      cols[3:] = ["# {0}".format(x) for x in cols[3:]]

    table = PrettyTable(cols)

    for i in xrange(len(self.patterns)):
      pattern = self.patterns[i]
      sequenceLabel = self.sequenceLabels[i]
      sequenceLabel = "" if sequenceLabel is None else sequenceLabel

      if pattern is None:
        row = [i] + ["<reset>"] * 7

      else:
        row = [i]

        if verbosity == 0:
          row.append(len(pattern))
          row.append(sequenceLabel)
          row.append(len(self.predictedActiveColumnsList[i]))
          row.append(len(self.predictedInactiveColumnsList[i]))
          row.append(len(self.unpredictedActiveColumnsList[i]))
          row.append(len(self.predictedActiveCellsList[i]))
          row.append(len(self.predictedInactiveCellsList[i]))

        else:
          row.append(list(pattern))
          row.append(sequenceLabel)
          row.append(list(self.predictedActiveColumnsList[i]))
          row.append(list(self.predictedInactiveColumnsList[i]))
          row.append(list(self.unpredictedActiveColumnsList[i]))
          row.append(list(self.predictedActiveCellsList[i]))
          row.append(list(self.predictedInactiveCellsList[i]))

      table.add_row(row)

    return table.get_string()


  def prettyPrintConnections(self):
    """
    Pretty print the connections in the temporal memory.

    @param verbosity (int) Verbosity level

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


  def getStatistics(self):
    """
    Returns statistics for the history, as a named tuple with the following
    fields:

        - `predictedActiveCells`
        - `predictedInactiveCells`
        - `predictedActiveColumns`
        - `predictedInactiveColumns`
        - `unpredictedActiveColumns`

    Each element in the tuple is a named tuple with the following fields:

        - `min`
        - `max`
        - `sum`
        - `average`
        - `standardDeviation`

    Note: The first element, any reset and the element immediately following it
    is ignored when computing stats.

    @return (namedtuple) Statistics for detailed results
    """
    Stats = namedtuple('Stats', ['predictedActiveCells',
                                 'predictedInactiveCells',
                                 'predictedActiveColumns',
                                 'predictedInactiveColumns',
                                 'unpredictedActiveColumns'])
    Data = namedtuple('Data', ['min',
                               'max',
                               'sum',
                               'average',
                               'standardDeviation'])
    def statsForResult(result):
      counts = [len(x) for idx, x in enumerate(result)
                if (idx > 0 and
                    self.patterns[idx] is not None and
                    self.patterns[idx-1] is not None)]
      return Data(min(counts),
                  max(counts),
                  sum(counts),
                  numpy.mean(counts),
                  numpy.std(counts))

    history = (
      self.predictedActiveCellsList,
      self.predictedInactiveCellsList,
      self.predictedActiveColumnsList,
      self.predictedInactiveColumnsList,
      self.unpredictedActiveColumnsList
    )
    return Stats._make([statsForResult(result) for result in history])


  # ==============================
  # Overrides
  # ==============================

  def compute(self, activeColumns, sequenceLabel=None, **kwargs):
    self._record(activeColumns, sequenceLabel)

    super(TemporalMemoryInspectMixin, self).compute(activeColumns, **kwargs)


  def reset(self):
    self._record(None, None)

    super(TemporalMemoryInspectMixin, self).reset()


  # ==============================
  # Helper methods
  # ==============================

  def _record(self, activeColumns, sequenceLabel):
    self.patterns.append(activeColumns)
    self.sequenceLabels.append(sequenceLabel)

    activeColumns = activeColumns if activeColumns else set()
    predictedActiveCells = set()
    predictedInactiveCells = set()
    predictedActiveColumns = set()
    predictedInactiveColumns = set()

    for prevPredictedCell in self.predictiveCells:
      prevPredictedColumn = self.connections.columnForCell(
        prevPredictedCell)

      if prevPredictedColumn in activeColumns:
        predictedActiveCells.add(prevPredictedCell)
        predictedActiveColumns.add(prevPredictedColumn)
      else:
        predictedInactiveCells.add(prevPredictedCell)
        predictedInactiveColumns.add(prevPredictedColumn)

    unpredictedActiveColumns = activeColumns - predictedActiveColumns

    self.predictedActiveCellsList.append(predictedActiveCells)
    self.predictedInactiveCellsList.append(predictedInactiveCells)
    self.predictedActiveColumnsList.append(predictedActiveColumns)
    self.predictedInactiveColumnsList.append(predictedInactiveColumns)
    self.unpredictedActiveColumnsList.append(unpredictedActiveColumns)

