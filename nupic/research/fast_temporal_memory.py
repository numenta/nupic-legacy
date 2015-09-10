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
Temporal Memory implementation in Python.
"""

from nupic.research.temporal_memory import TemporalMemory
from nupic.bindings.algorithms import Connections, ConnectionsCell



class FastTemporalMemory(TemporalMemory):
  """
  Class implementing the Temporal Memory algorithm.

  Uses C++ Connections data structure for optimization.
  """

  def __init__(self, *args, **kwargs):
    super(FastTemporalMemory, self).__init__(*args, **kwargs)
    self.connections = Connections(self.numberOfCells())


  def burstColumns(self,
                   activeColumns,
                   predictedColumns,
                   prevActiveCells,
                   prevWinnerCells,
                   connections):
    """
    Phase 2: Burst unpredicted columns.

    Pseudocode:

      - for each unpredicted active column
        - mark all cells as active
        - mark the best matching cell as winner cell
          - (learning)
            - if it has no matching segment
              - (optimization) if there are prev winner cells
                - add a segment to it
            - mark the segment as learning

    @param activeColumns                   (set)         Indices of active columns in `t`
    @param predictedColumns                (set)         Indices of predicted columns in `t`
    @param prevActiveCells                 (set)         Indices of active cells in `t-1`
    @param prevWinnerCells                 (set)         Indices of winner cells in `t-1`
    @param connections                     (Connections) Connectivity of layer

    @return (tuple) Contains:
                      `activeCells`      (set),
                      `winnerCells`      (set),
                      `learningSegments` (set)
    """
    activeCells = set()
    winnerCells = set()
    learningSegments = set()

    unpredictedColumns = activeColumns - predictedColumns

    for column in unpredictedColumns:
      cells = self.cellsForColumn(column)
      activeCells.update(cells)

      bestSegment = connections.mostActiveSegmentForCells(
        list(cells), list(prevActiveCells), self.minThreshold)

      if bestSegment is None:
        bestCell = self.leastUsedCell(cells, connections)
        if len(prevWinnerCells):
          bestSegment = connections.createSegment(bestCell)
      else:
        # TODO: For some reason, bestSegment.cell is garbage-collected after
        # this function returns. So we have to use the below hack. Figure out
        # why and clean up.
        bestCell = ConnectionsCell(bestSegment.cell.idx)

      winnerCells.add(bestCell)

      if bestSegment:
        learningSegments.add(bestSegment)

    return activeCells, winnerCells, learningSegments


  def computePredictiveCells(self, activeCells, connections):
    """
    Phase 4: Compute predictive cells due to lateral input
    on distal dendrites.

    Pseudocode:

      - for each distal dendrite segment with activity >= activationThreshold
        - mark the segment as active
        - mark the cell as predictive

      - for each distal dendrite segment with unconnected
        activity >=  minThreshold
        - mark the segment as matching
        - mark the cell as matching

    Forward propagates activity from active cells to the synapses that touch
    them, to determine which synapses are active.

    @param activeCells (set)         Indices of active cells in `t`
    @param connections (Connections) Connectivity of layer

    @return (tuple) Contains:
                      `activeSegments`   (set),
                      `predictiveCells`  (set),
                      `matchingSegments` (set),
                      `matchingCells`    (set)
    """
    activity = connections.computeActivity(list(activeCells),
                                           self.connectedPermanence,
                                           self.activationThreshold)
    activeSegments = set(connections.activeSegments(activity))
    predictiveCells = set(connections.activeCells(activity))

    if self.predictedSegmentDecrement > 0:
      activity = connections.computeActivity(list(activeCells),
                                             0,
                                             self.minThreshold)

      matchingSegments = set(connections.activeSegments(activity))
      matchingCells = set(connections.activeCells(activity))
    else:
      matchingSegments = set()
      matchingCells = set()

    return activeSegments, predictiveCells, matchingSegments, matchingCells


  @staticmethod
  def getCellIndex(cell):
    return cell.idx


  # ==============================
  # Helper functions
  # ==============================

  def columnForCell(self, cell):
    """
    Returns the index of the column that a cell belongs to.

    @param cell (int) Cell index

    @return (int) Column index
    """
    self._validateCell(cell)

    return int(cell.idx / self.cellsPerColumn)


  def cellsForColumn(self, column):
    """
    Returns the indices of cells that belong to a column.

    @param column (int) Column index

    @return (set) Cell indices
    """
    self._validateColumn(column)

    start = self.cellsPerColumn * column
    end = start + self.cellsPerColumn
    return set([ConnectionsCell(idx) for idx in xrange(start, end)])


  def _validateCell(self, cell):
    """
    Raises an error if cell index is invalid.

    @param cell (int) Cell index
    """
    if cell.idx >= self.numberOfCells() or cell.idx < 0:
      raise IndexError("Invalid cell")
