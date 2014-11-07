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


  def computeFn(self,
                activeColumns,
                prevPredictiveCells,
                prevActiveSegments,
                prevActiveCells,
                prevWinnerCells,
                connections,
                learn=True):
    """
    'Functional' version of compute.
    Returns new state.

    @param activeColumns                   (set)         Indices of active columns in `t`
    @param prevPredictiveCells             (set)         Indices of predictive cells in `t-1`
    @param prevActiveSegments              (set)         Indices of active segments in `t-1`
    @param prevActiveCells                 (set)         Indices of active cells in `t-1`
    @param prevWinnerCells                 (set)         Indices of winner cells in `t-1`
    @param connections                     (Connections) Connectivity of layer
    @param learn                           (bool)        Whether or not learning is enabled

    @return (tuple) Contains:
                      `activeCells`               (set),
                      `winnerCells`               (set),
                      `activeSegments`            (set),
                      `predictiveCells`           (set)
    """
    activeCells = set()
    winnerCells = set()

    (_activeCells,
     _winnerCells,
     predictedColumns) = self.activateCorrectlyPredictiveCells(
       prevPredictiveCells,
       activeColumns)

    activeCells.update(_activeCells)
    winnerCells.update(_winnerCells)

    (_activeCells,
     _winnerCells,
     learningSegments) = self.burstColumns(activeColumns,
                                           predictedColumns,
                                           prevActiveCells,
                                           connections)

    activeCells.update(_activeCells)
    winnerCells.update(_winnerCells)

    if learn:
      self.learnOnSegments(prevActiveSegments,
                           learningSegments,
                           prevActiveCells,
                           winnerCells,
                           prevWinnerCells,
                           connections)

    (activeSegments,
     predictiveCells) = self.computePredictiveCells(activeCells, connections)

    return (activeCells,
            winnerCells,
            activeSegments,
            predictiveCells,
            predictedColumns)


  def activateCorrectlyPredictiveCells(self,
                                       prevPredictiveCells,
                                       activeColumns):
    """
    Phase 1: Activate the correctly predictive cells.

    Pseudocode:

      - for each prev predictive cell
        - if in active column
          - mark it as active
          - mark it as winner cell
          - mark column as predicted

    @param prevPredictiveCells (set) Indices of predictive cells in `t-1`
    @param activeColumns       (set) Indices of active columns in `t`

    @return (tuple) Contains:
                      `activeCells`      (set),
                      `winnerCells`      (set),
                      `predictedColumns` (set)
    """
    activeCells = set()
    winnerCells = set()
    predictedColumns = set()

    for cell in prevPredictiveCells:
      column = self.columnForCell(cell)

      if column in activeColumns:
        activeCells.add(cell)
        winnerCells.add(cell)
        predictedColumns.add(column)

    return activeCells, winnerCells, predictedColumns


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

      bestCell = ConnectionsCell(bestSegment.cell.idx)  # TODO: clean up
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

  def leastUsedCell(self, cells, connections):
    """
    Gets the cell with the smallest number of segments.
    Break ties randomly.

    @param cells       (set)         Indices of cells
    @param connections (Connections) Connectivity of layer

    @return (int) Cell index
    """
    leastUsedCells = set()
    minNumSegments = float("inf")

    for cell in cells:
      numSegments = len(connections.segmentsForCell(cell))

      if numSegments < minNumSegments:
        minNumSegments = numSegments
        leastUsedCells = set()

      if numSegments == minNumSegments:
        leastUsedCells.add(cell)

    i = self._random.getUInt32(len(leastUsedCells))
    return sorted(leastUsedCells)[i]


  @staticmethod
  def activeSynapsesForSegment(segment, activeCells, connections):
    """
    Returns the synapses on a segment that are active due to lateral input
    from active cells.

    @param segment     (int)         Segment index
    @param activeCells (set)         Indices of active cells
    @param connections (Connections) Connectivity of layer

    @return (set) Indices of active synapses on segment
    """
    synapses = set()

    for synapse in connections.synapsesForSegment(segment):
      synapseData = connections.dataForSynapse(synapse)

      if (synapseData.presynapticCell in activeCells and
          synapseData.permanence >= 0):
        synapses.add(synapse)

    return synapses


  def adaptSegment(self, segment, activeSynapses, connections):
    """
    Updates synapses on segment.
    Strengthens active synapses; weakens inactive synapses.

    @param segment        (int)         Segment index
    @param activeSynapses (set)         Indices of active synapses
    @param connections    (Connections) Connectivity of layer
    """
    for synapse in connections.synapsesForSegment(segment):
      synapseData = connections.dataForSynapse(synapse)
      permanence = synapseData.permanence

      if synapse in activeSynapses:
        permanence += self.permanenceIncrement
      else:
        permanence -= self.permanenceDecrement

      # Keep permanence within min/max bounds
      permanence = max(0.0, min(1.0, permanence))

      connections.updateSynapsePermanence(synapse, permanence)


  def pickCellsToLearnOn(self, n, segment, winnerCells, connections):
    """
    Pick cells to form distal connections to.

    TODO: Respect topology and learningRadius

    @param n           (int)         Number of cells to pick
    @param segment     (int)         Segment index
    @param winnerCells (set)         Indices of winner cells in `t`
    @param connections (Connections) Connectivity of layer

    @return (set) Indices of cells picked
    """
    candidates = set(winnerCells)

    # Remove cells that are already synapsed on by this segment
    for synapse in connections.synapsesForSegment(segment):
      synapseData = connections.dataForSynapse(synapse)
      if synapseData.presynapticCell in candidates:
        candidates.remove(synapseData.presynapticCell)

    n = min(n, len(candidates))
    candidates = sorted(candidates)
    cells = set()

    # Pick n cells randomly
    for _ in range(n):
      i = self._random.getUInt32(len(candidates))
      cells.add(candidates[i])
      del candidates[i]

    return cells


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
