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
Temporal Memory implementation in Python.
"""

from collections import defaultdict
from operator import mul

from nupic.research.temporal_memory import TemporalMemory
from nupic.bindings.algorithms import Connections, ConnectionsCell



class FastTemporalMemory(TemporalMemory):
  """
  Class implementing the Temporal Memory algorithm.
  """

  def __init__(self, *args, **kwargs):
    super(FastTemporalMemory, self).__init__(*args, **kwargs)
    self.connections = Connections(self.numberOfCells())


  def burstColumns(self,
                   activeColumns,
                   predictedColumns,
                   prevActiveCells,
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
        cell = self.leastUsedCell(cells, connections)
        # TODO: (optimization) Only do this if there are prev winner cells
        bestSegment = connections.createSegment(cell)

      # TODO: For some reason, bestSegment.cell is garbage-collected after
      # this function returns. So we have to use the below hack. Figure out
      # why and clean up.
      bestCell = ConnectionsCell(bestSegment.cell.idx)

      winnerCells.add(bestCell)
      learningSegments.add(bestSegment)

    return activeCells, winnerCells, learningSegments


  def learnOnSegments(self,
                      prevActiveSegments,
                      learningSegments,
                      prevActiveCells,
                      winnerCells,
                      prevWinnerCells,
                      connections):
    """
    Phase 3: Perform learning by adapting segments.

    Pseudocode:

      - (learning) for each prev active or learning segment
        - if learning segment or from winner cell
          - strengthen active synapses
          - weaken inactive synapses
        - if learning segment
          - add some synapses to the segment
            - subsample from prev winner cells

    @param prevActiveSegments           (set)         Indices of active segments in `t-1`
    @param learningSegments             (set)         Indices of learning segments in `t`
    @param prevActiveCells              (set)         Indices of active cells in `t-1`
    @param winnerCells                  (set)         Indices of winner cells in `t`
    @param prevWinnerCells              (set)         Indices of winner cells in `t-1`
    @param connections                  (Connections) Connectivity of layer
    """
    # TODO: Merge this into TemporalMemory.learnOnSegments
    for segment in prevActiveSegments | learningSegments:
      isLearningSegment = segment in learningSegments
      isFromWinnerCell = segment.cell in winnerCells

      activeSynapses = self.activeSynapsesForSegment(
        segment, prevActiveCells, connections)

      if isLearningSegment or isFromWinnerCell:
        self.adaptSegment(segment, activeSynapses, connections)

      if isLearningSegment:
        n = self.maxNewSynapseCount - len(activeSynapses)

        for presynapticCell in self.pickCellsToLearnOn(n,
                                                       segment,
                                                       prevWinnerCells,
                                                       connections):
          connections.createSynapse(segment,
                                    presynapticCell,
                                    self.initialPermanence)


  def computePredictiveCells(self, activeCells, connections):
    """
    Phase 4: Compute predictive cells due to lateral input
    on distal dendrites.

    Pseudocode:

      - for each distal dendrite segment with activity >= activationThreshold
        - mark the segment as active
        - mark the cell as predictive

    Forward propagates activity from active cells to the synapses that touch
    them, to determine which synapses are active.

    @param activeCells (set)         Indices of active cells in `t`
    @param connections (Connections) Connectivity of layer

    @return (tuple) Contains:
                      `activeSegments`  (set),
                      `predictiveCells` (set)
    """
    activity = connections.computeActivity(list(activeCells),
                                           self.connectedPermanence,
                                           self.activationThreshold)
    activeSegments = set(connections.activeSegments(activity))
    predictiveCells = set(connections.activeCells(activity))

    return activeSegments, predictiveCells


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
    return set([ConnectionsCell(idx) for idx in range(start, end)])


  def _validateCell(self, cell):
    """
    Raises an error if cell index is invalid.

    @param cell (int) Cell index
    """
    if cell.idx >= self.numberOfCells() or cell.idx < 0:
      raise IndexError("Invalid cell")
