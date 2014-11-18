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

from collections import defaultdict, namedtuple
from operator import mul

from nupic.bindings.math import Random



class TemporalMemory(object):
  """
  Class implementing the Temporal Memory algorithm.
  """

  def __init__(self,
               columnDimensions=(2048,),
               cellsPerColumn=32,
               activationThreshold=13,
               learningRadius=2048,
               initialPermanence=0.21,
               connectedPermanence=0.50,
               minThreshold=10,
               maxNewSynapseCount=20,
               permanenceIncrement=0.10,
               permanenceDecrement=0.10,
               seed=42):
    """
    @param columnDimensions    (list)  Dimensions of the column space
    @param cellsPerColumn      (int)   Number of cells per column
    @param activationThreshold (int)   If the number of active connected synapses on a segment is at least this threshold, the segment is said to be active.
    @param learningRadius      (int)   Radius around cell from which it can sample to form distal dendrite connections.
    @param initialPermanence   (float) Initial permanence of a new synapse.
    @param connectedPermanence (float) If the permanence value for a synapse is greater than this value, it is said to be connected.
    @param minThreshold        (int)   If the number of synapses active on a segment is at least this threshold, it is selected as the best matching cell in a bursting column.
    @param maxNewSynapseCount  (int)   The maximum number of synapses added to a segment during learning.
    @param permanenceIncrement (float) Amount by which permanences of synapses are incremented during learning.
    @param permanenceDecrement (float) Amount by which permanences of synapses are decremented during learning.
    @param seed                (int)   Seed for the random number generator.
    """
    # Error checking
    if not len(columnDimensions):
      raise ValueError("Number of column dimensions must be greater than 0")

    if not cellsPerColumn > 0:
      raise ValueError("Number of cells per column must be greater than 0")

    # TODO: Validate all parameters (and add validation tests)

    # Save member variables
    self.columnDimensions = columnDimensions
    self.cellsPerColumn = cellsPerColumn
    self.activationThreshold = activationThreshold
    self.learningRadius = learningRadius
    self.initialPermanence = initialPermanence
    self.connectedPermanence = connectedPermanence
    self.minThreshold = minThreshold
    self.maxNewSynapseCount = maxNewSynapseCount
    self.permanenceIncrement = permanenceIncrement
    self.permanenceDecrement = permanenceDecrement

    # Initialize member variables
    self.connections = Connections(self.numberOfCells())
    self._random = Random(seed)

    self.activeCells = set()
    self.predictiveCells = set()
    self.activeSegments = set()
    self.winnerCells = set()


  # ==============================
  # Main functions
  # ==============================

  def compute(self, activeColumns, learn=True):
    """
    Feeds input record through TM, performing inference and learning.
    Updates member variables with new state.

    @param activeColumns (set) Indices of active columns in `t`
    """
    (activeCells,
     winnerCells,
     activeSegments,
     predictiveCells,
     predictedColumns) = self.computeFn(activeColumns,
                                        self.predictiveCells,
                                        self.activeSegments,
                                        self.activeCells,
                                        self.winnerCells,
                                        self.connections,
                                        learn=learn)

    self.activeCells = activeCells
    self.winnerCells = winnerCells
    self.activeSegments = activeSegments
    self.predictiveCells = predictiveCells


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
                                           prevWinnerCells,
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


  def reset(self):
    """
    Indicates the start of a new sequence. Resets sequence state of the TM.
    """
    self.activeCells = set()
    self.predictiveCells = set()
    self.activeSegments = set()
    self.winnerCells = set()


  # ==============================
  # Phases
  # ==============================

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

      (bestCell,
       bestSegment) = self.bestMatchingCell(cells,
                                            prevActiveCells,
                                            connections)
      winnerCells.add(bestCell)

      if bestSegment is None and len(prevWinnerCells):
        bestSegment = connections.createSegment(bestCell)

      if bestSegment is not None:
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
      isFromWinnerCell = connections.cellForSegment(segment) in winnerCells

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
    numActiveConnectedSynapsesForSegment = defaultdict(lambda: 0)
    activeSegments = set()
    predictiveCells = set()

    for cell in activeCells:
      for synapseData in connections.synapsesForPresynapticCell(cell).values():
        segment = synapseData.segment
        permanence = synapseData.permanence

        if permanence >= self.connectedPermanence:
          numActiveConnectedSynapsesForSegment[segment] += 1

          if (numActiveConnectedSynapsesForSegment[segment] >=
              self.activationThreshold):
            activeSegments.add(segment)
            predictiveCells.add(connections.cellForSegment(segment))

    return activeSegments, predictiveCells


  # ==============================
  # Helper functions
  # ==============================

  def bestMatchingCell(self, cells, activeCells, connections):
    """
    Gets the cell with the best matching segment
    (see `TM.bestMatchingSegment`) that has the largest number of active
    synapses of all best matching segments.

    If none were found, pick the least used cell (see `TM.leastUsedCell`).

    @param cells                       (set)         Indices of cells
    @param activeCells                 (set)         Indices of active cells
    @param connections                 (Connections) Connectivity of layer

    @return (tuple) Contains:
                      `cell`        (int),
                      `bestSegment` (int)
    """
    maxSynapses = 0
    bestCell = None
    bestSegment = None

    for cell in cells:
      segment, numActiveSynapses = self.bestMatchingSegment(
        cell, activeCells, connections)

      if segment is not None and numActiveSynapses > maxSynapses:
        maxSynapses = numActiveSynapses
        bestCell = cell
        bestSegment = segment

    if bestCell is None:
      bestCell = self.leastUsedCell(cells, connections)

    return bestCell, bestSegment


  def bestMatchingSegment(self, cell, activeCells, connections):
    """
    Gets the segment on a cell with the largest number of activate synapses,
    including all synapses with non-zero permanences.

    @param cell                        (int)         Cell index
    @param activeCells                 (set)         Indices of active cells
    @param connections                 (Connections) Connectivity of layer

    @return (tuple) Contains:
                      `segment`                 (int),
                      `connectedActiveSynapses` (set)
    """
    maxSynapses = self.minThreshold
    bestSegment = None
    bestNumActiveSynapses = None

    for segment in connections.segmentsForCell(cell):
      numActiveSynapses = 0

      for synapse in connections.synapsesForSegment(segment):
        synapseData = connections.dataForSynapse(synapse)
        if synapseData.presynapticCell in activeCells:
          numActiveSynapses += 1

      if numActiveSynapses >= maxSynapses:
        maxSynapses = numActiveSynapses
        bestSegment = segment
        bestNumActiveSynapses = numActiveSynapses

    return bestSegment, bestNumActiveSynapses


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

      if synapseData.presynapticCell in activeCells:
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
      presynapticCell = synapseData.presynapticCell

      if presynapticCell in candidates:
        candidates.remove(presynapticCell)

    n = min(n, len(candidates))
    candidates = sorted(candidates)
    cells = set()

    # Pick n cells randomly
    for _ in range(n):
      i = self._random.getUInt32(len(candidates))
      cells.add(candidates[i])
      del candidates[i]

    return cells


  def columnForCell(self, cell):
    """
    Returns the index of the column that a cell belongs to.

    @param cell (int) Cell index

    @return (int) Column index
    """
    self._validateCell(cell)

    return int(cell / self.cellsPerColumn)


  def cellsForColumn(self, column):
    """
    Returns the indices of cells that belong to a column.

    @param column (int) Column index

    @return (set) Cell indices
    """
    self._validateColumn(column)

    start = self.cellsPerColumn * column
    end = start + self.cellsPerColumn
    return set([cell for cell in range(start, end)])


  def numberOfColumns(self):
    """
    Returns the number of columns in this layer.

    @return (int) Number of columns
    """
    return reduce(mul, self.columnDimensions, 1)


  def numberOfCells(self):
    """
    Returns the number of cells in this layer.

    @return (int) Number of cells
    """
    return self.numberOfColumns() * self.cellsPerColumn


  def mapCellsToColumns(self, cells):
    """
    Maps cells to the columns they belong to

    @param cells (set) Cells

    @return (dict) Mapping from columns to their cells in `cells`
    """
    cellsForColumns = defaultdict(set)

    for cell in cells:
      column = self.columnForCell(cell)
      cellsForColumns[column].add(cell)

    return cellsForColumns


  def _validateColumn(self, column):
    """
    Raises an error if column index is invalid.

    @param column (int) Column index
    """
    if column >= self.numberOfColumns() or column < 0:
      raise IndexError("Invalid column")


  def _validateCell(self, cell):
    """
    Raises an error if cell index is invalid.

    @param cell (int) Cell index
    """
    if cell >= self.numberOfCells() or cell < 0:
      raise IndexError("Invalid cell")



class Connections(object):
  """
  Class to hold data representing the connectivity of a collection of cells.
  """

  SynapseData = namedtuple("SyanpseData", ["segment",
                                           "presynapticCell",
                                           "permanence"])

  def __init__(self, numCells):
    """
    @param numCells (int) Number of cells in collection
    """

    # Save member variables
    self.numCells = numCells

    # Mappings
    self._segments = dict()
    self._synapses = dict()

    # Indexes into the mappings (for performance)
    self._segmentsForCell = dict()
    self._synapsesForSegment = dict()
    self._synapsesForPresynapticCell = defaultdict(dict)

    # Index of the next segment to be created
    self._nextSegmentIdx = 0
    # Index of the next synapse to be created
    self._nextSynapseIdx = 0


  def cellForSegment(self, segment):
    """
    Returns the cell that a segment belongs to.

    @param segment (int) Segment index

    @return (int) Cell index
    """
    return self._segments[segment]


  def segmentsForCell(self, cell):
    """
    Returns the segments that belong to a cell.

    @param cell (int) Cell index

    @return (set) Segment indices
    """
    self._validateCell(cell)

    if not cell in self._segmentsForCell:
      return set()

    return self._segmentsForCell[cell]


  def dataForSynapse(self, synapse):
    """
    Returns the data for a synapse.

    @param synapse (int) Synapse index

    @return (SynapseData) Synapse data
    """
    return self._synapses[synapse]


  def synapsesForSegment(self, segment):
    """
    Returns the synapses on a segment.

    @param segment (int) Segment index

    @return (set) Synapse indices
    """
    self._validateSegment(segment)

    if not segment in self._synapsesForSegment:
      return set()

    return self._synapsesForSegment[segment]


  def synapsesForPresynapticCell(self, presynapticCell):
    """
    Returns the synapses for the source cell that they synapse on.

    @param presynapticCell (int) Source cell index

    @return (set) Synapse indices
    """
    return self._synapsesForPresynapticCell[presynapticCell]


  def createSegment(self, cell):
    """
    Adds a new segment on a cell.

    @param cell (int) Cell index

    @return (int) New segment index
    """
    self._validateCell(cell)

    # Add data
    segment = self._nextSegmentIdx
    self._segments[segment] = cell
    self._nextSegmentIdx += 1

    # Update indexes
    if not cell in self._segmentsForCell:
      self._segmentsForCell[cell] = set()
    self._segmentsForCell[cell].add(segment)

    return segment


  def createSynapse(self, segment, presynapticCell, permanence):
    """
    Creates a new synapse on a segment.

    @param segment         (int)   Segment index
    @param presynapticCell (int)   Source cell index
    @param permanence      (float) Initial permanence

    @return (int) Synapse index
    """
    self._validateSegment(segment)
    self._validatePermanence(permanence)

    # Add data
    synapse = self._nextSynapseIdx
    synapseData = self.SynapseData(segment, presynapticCell, permanence)
    self._synapses[synapse] = synapseData
    self._nextSynapseIdx += 1

    # Update indexes
    if not len(self.synapsesForSegment(segment)):
      self._synapsesForSegment[segment] = set()
    self._synapsesForSegment[segment].add(synapse)

    self._synapsesForPresynapticCell[presynapticCell][synapse] = synapseData

    return synapse


  def updateSynapsePermanence(self, synapse, permanence):
    """
    Updates the permanence for a synapse.

    @param synapse    (int)   Synapse index
    @param permanence (float) New permanence
    """
    self._validatePermanence(permanence)

    data = self._synapses[synapse]
    newData = self.SynapseData(data.segment,
                               data.presynapticCell,
                               permanence)
    self._synapses[synapse] = newData

    # Update indexes
    self._synapsesForPresynapticCell[newData.presynapticCell][synapse] = newData


  def numSegments(self):
    """
    Returns the number of segments.
    """
    return len(self._segments)


  def numSynapses(self):
    """
    Returns the number of synapses.
    """
    return len(self._synapses)


  def _validateCell(self, cell):
    """
    Raises an error if cell index is invalid.

    @param cell (int) Cell index
    """
    if cell >= self.numCells or cell < 0:
      raise IndexError("Invalid cell")


  def _validateSegment(self, segment):
    """
    Raises an error if segment index is invalid.

    @param segment (int) Segment index
    """
    if not segment in self._segments:
      raise IndexError("Invalid segment")


  @staticmethod
  def _validatePermanence(permanence):
    """
    Raises an error if permanence is invalid.

    @param permanence (float) Permanence
    """
    if permanence < 0 or permanence > 1:
      raise ValueError("Invalid permanence")
