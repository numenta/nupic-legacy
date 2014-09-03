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
Utilities for running data through the TM, and analyzing the results.
"""

import numpy
from prettytable import PrettyTable



class TemporalMemoryTestMachine(object):
  """
  Base TM test machine class.
  """

  def __init__(self, tm):
    """
    @param tm (TM) Temporal memory
    """
    # Save member variables
    self.tm = tm


  def feedSequence(self, sequence, learn=True):
    """
    Feed a sequence through the TM.

    @param sequence (list) List of patterns, with None for resets
    @param learn    (bool) Learning enabled

    @return (list) List of sets containing predictive cells,
                   one for each element in `sequence`
    """
    results = []

    for pattern in sequence:
      if pattern == None:
        self.tm.reset()
      else:
        self.tm.compute(pattern, learn=learn)

      results.append(self.tm.predictiveCells)

    return results


  def computeDetailedResult(self, prevPredictedCells, pattern):
    """
    Compute detailed result from previous predicted cells and pattern.

    @param prevPredictedCells (set) Predicted cells at `t-1`
    @param pattern            (set) Current pattern

    @return (tuple) Contains:
                      `predictedActiveCells`     (set),
                      `predictedInactiveCells`   (set),
                      `predictedActiveColumns`   (set),
                      `predictedInactiveColumns` (set),
                      `unpredictedActiveColumns` (set)
    """
    predictedActiveCells = set()
    predictedInactiveCells = set()
    predictedActiveColumns = set()
    predictedInactiveColumns = set()

    for prevPredictedCell in prevPredictedCells:
      prevPredictedColumn = self.tm.connections.columnForCell(
        prevPredictedCell)

      if prevPredictedColumn in pattern:
        predictedActiveCells.add(prevPredictedCell)
        predictedActiveColumns.add(prevPredictedColumn)
      else:
        predictedInactiveCells.add(prevPredictedCell)
        predictedInactiveColumns.add(prevPredictedColumn)

    unpredictedActiveColumns = pattern - predictedActiveColumns

    return (
      predictedActiveCells,
      predictedInactiveCells,
      predictedActiveColumns,
      predictedInactiveColumns,
      unpredictedActiveColumns
    )


  def computeDetailedResults(self, results, sequence):
    """
    Compute detailed results from results of `feedSequence`.

    @param results  (list) Results from `feedSequence`
    @param sequence (list) Sequence that generated the results

    @return (tuple) Contains:
                      `predictedActiveCellsList`     (list),
                      `predictedInactiveCellsList`   (list),
                      `predictedActiveColumnsList`   (list),
                      `predictedInactiveColumnsList` (list),
                      `unpredictedActiveColumnsList` (list)
    """
    predictedActiveCellsList = []
    predictedInactiveCellsList = []
    predictedActiveColumnsList = []
    predictedInactiveColumnsList = []
    unpredictedActiveColumnsList = []

    for i in xrange(len(results)):
      pattern = sequence[i]

      predictedActiveCells = set()
      predictedInactiveCells = set()
      predictedActiveColumns = set()
      predictedInactiveColumns = set()
      unpredictedActiveColumns = set()

      if pattern is not None:
        prevPredictedCells = results[i-1] if i > 0 else set()
        (
          predictedActiveCells,
          predictedInactiveCells,
          predictedActiveColumns,
          predictedInactiveColumns,
          unpredictedActiveColumns
        ) = self.computeDetailedResult(prevPredictedCells, pattern)

      predictedActiveCellsList.append(predictedActiveCells)
      predictedInactiveCellsList.append(predictedInactiveCells)
      predictedActiveColumnsList.append(predictedActiveColumns)
      predictedInactiveColumnsList.append(predictedInactiveColumns)
      unpredictedActiveColumnsList.append(unpredictedActiveColumns)

    return (predictedActiveCellsList,
            predictedInactiveCellsList,
            predictedActiveColumnsList,
            predictedInactiveColumnsList,
            unpredictedActiveColumnsList)


  @staticmethod
  def computeStatistics(detailedResults, sequence):
    """
    Returns statistics for the given detailed results.
    Each element in the returned tuple is itself a tuple with the following form:

        (min, max, sum, average, standard deviation)

    Note: The first element, any reset and the element immediately following it
    is ignored when computing stats.

    @param detailedResults (tuple)          Detailed results from
                                            `computeDetailedResults`
    @param sequence        (list)           Sequence that generated the results

    @return (tuple) Statistics for detailed results
    """
    def statsForResult(result):
      counts = [len(x) for idx, x in enumerate(result)
                if (idx > 0 and
                    sequence[idx] is not None and
                    sequence[idx-1] is not None)]
      return (min(counts),
              max(counts),
              sum(counts),
              numpy.mean(counts),
              numpy.std(counts))

    return tuple([statsForResult(result) for result in detailedResults])


  @staticmethod
  def prettyPrintDetailedResults(detailedResults,
                                 sequence,
                                 patternMachine,
                                 verbosity=0):
    """
    Pretty print the detailed results from `feedSequence`.

    @param detailedResults (tuple)          Detailed results from
                                            `computeDetailedResults`
    @param sequence        (list)           Sequence that generated the results
    @param patternMachine  (PatternMachine) Pattern machine
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
    (
    predictedActiveCellsList,
    predictedInactiveCellsList,
    predictedActiveColumnsList,
    predictedInactiveColumnsList,
    unpredictedActiveColumnsList
    ) = detailedResults

    for i in xrange(len(sequence)):
      pattern = sequence[i]

      if pattern == None:
        row = [i] + ["<reset>"] * 6

        if verbosity > 2:
          row += ["<reset>"] * 2

      else:
        row = [i]

        if verbosity == 0:
          row.append(len(pattern))
          row.append(len(predictedActiveColumnsList[i]))
          row.append(len(predictedInactiveColumnsList[i]))
          row.append(len(unpredictedActiveColumnsList[i]))
          row.append(len(predictedActiveCellsList[i]))
          row.append(len(predictedInactiveCellsList[i]))

        else:
          row.append(patternMachine.prettyPrintPattern(pattern,
                                                       verbosity=verbosity))
          row.append(
            patternMachine.prettyPrintPattern(predictedActiveColumnsList[i],
                                              verbosity=verbosity))
          row.append(
            patternMachine.prettyPrintPattern(predictedInactiveColumnsList[i],
                                              verbosity=verbosity))
          row.append(
            patternMachine.prettyPrintPattern(unpredictedActiveColumnsList[i],
                                              verbosity=verbosity))
          row.append(list(predictedActiveCellsList[i]))
          row.append(list(predictedInactiveCellsList[i]))

      table.add_row(row)

    return table.get_string()


  def prettyPrintConnections(self):
    """
    Pretty print the connections in the temporal memory.

    @param verbosity (int) Verbosity level

    @return (string) Pretty-printed text
    """
    tm = self.tm
    text = ""

    text += ("Segments: (format => "
             "{segment: [(source cell, permanence), ...])\n")
    text += "------------------------------------\n"

    columns = range(tm.connections.numberOfColumns())

    for column in columns:
      cells = tm.connections.cellsForColumn(column)

      for cell in cells:
        segmentDict = dict()

        for seg in tm.connections.segmentsForCell(cell):
          synapseList = []

          for synapse in tm.connections.synapsesForSegment(seg):
            (_, sourceCell, permanence) = tm.connections.dataForSynapse(synapse)

            synapseList.append([sourceCell,
                                permanence])

          segmentDict[seg] = synapseList

        text += ("Column {0} / Cell {1}:\t{2}\n".format(
                 column, cell, segmentDict))

      if column < len(columns) - 1:  # not last
        text += "\n"

    text += "------------------------------------\n"

    return text
