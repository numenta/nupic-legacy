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
    self.predictedActiveCellsList = None
    self.predictedInactiveCellsList = None
    self.predictedActiveColumnsList = None
    self.predictedInactiveColumnsList = None
    self.unpredictedActiveColumnsList = None
    self.clearHistory()


  def clearHistory(self):
    self.patterns = []
    self.predictedActiveCellsList = []
    self.predictedInactiveCellsList = []
    self.predictedActiveColumnsList = []
    self.predictedInactiveColumnsList = []
    self.unpredictedActiveColumnsList = []


  def prettyPrintHistory(self, verbosity=0):
    """
    Pretty print history.

    @param verbosity       (int)            Verbosity level

    @return (string) Pretty-printed text
    """
    cols = ["#",
            "Pattern",
            "pred=>active columns",
            "pred=>inactive columns",
            "unpred=>active columns",
            "pred=>active cells",
            "pred=>inactive cells"]

    if verbosity == 0:
      cols[1] = "Pattern (# bits)"
      cols[2:] = ["# {0}".format(x) for x in cols[2:]]

    table = PrettyTable(cols)

    for i in xrange(len(self.patterns)):
      pattern = self.patterns[i]

      if pattern is None:
        row = [i] + ["<reset>"] * 6

      else:
        row = [i]

        if verbosity == 0:
          row.append(len(pattern))
          row.append(len(self.predictedActiveColumnsList[i]))
          row.append(len(self.predictedInactiveColumnsList[i]))
          row.append(len(self.unpredictedActiveColumnsList[i]))
          row.append(len(self.predictedActiveCellsList[i]))
          row.append(len(self.predictedInactiveCellsList[i]))

        else:
          row.append(list(pattern))
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
    Returns statistics for the history, as tuple:

        (`predictedActiveCellsStats`,
         `predictedInactiveCellsStats`,
         `predictedActiveColumnsStats`,
         `predictedInactiveColumnsStats`,
         `unpredictedActiveColumnsStats`)

    Each element in the returned tuple is itself a tuple with the following form:

        (min, max, sum, average, standard deviation)

    Note: The first element, any reset and the element immediately following it
    is ignored when computing stats.

    @return (tuple) Statistics for detailed results
    """
    def statsForResult(result):
      counts = [len(x) for idx, x in enumerate(result)
                if (idx > 0 and
                    self.patterns[idx] is not None and
                    self.patterns[idx-1] is not None)]
      return (min(counts),
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
    return tuple([statsForResult(result) for result in history])


  # ==============================
  # Overrides
  # ==============================

  def compute(self, activeColumns, learn=True):
    self._record(activeColumns)
    self.patterns.append(activeColumns)

    super(TemporalMemoryInspectMixin, self).compute(activeColumns, learn=True)


  def reset(self):
    self._record(set())
    self.patterns.append(None)

    super(TemporalMemoryInspectMixin, self).reset()


  # ==============================
  # Helper methods
  # ==============================

  def _record(self, activeColumns):
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

