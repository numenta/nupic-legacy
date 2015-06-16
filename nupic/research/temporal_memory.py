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
from nupic.research.connections import Connections



class TemporalMemory(object):
  """
  Class implementing the Temporal Memory algorithm.
  """

  def __init__(self,
               columnDimensions=(2048,),
               cellsPerColumn=32,
               activationThreshold=13,
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

    @param activeColumns       (set)         Indices of active columns in `t`
    @param prevPredictiveCells (set)         Indices of predictive cells in `t-1`
    @param prevActiveSegments  (set)         Indices of active segments in `t-1`
    @param prevActiveCells     (set)         Indices of active cells in `t-1`
    @param prevWinnerCells     (set)         Indices of winner cells in `t-1`
    @param connections         (Connections) Connectivity of layer
    @param learn               (bool)        Whether or not learning is enabled

    @return (tuple) Contains:
                      `activeCells`     (set),
                      `winnerCells`     (set),
                      `activeSegments`  (set),
                      `predictiveCells` (set)
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


  def write(self, proto):
    """
    Writes serialized data to proto object

    @param proto (DynamicStructBuilder) Proto object
    """
    proto.columnDimensions = self.columnDimensions
    proto.cellsPerColumn = self.cellsPerColumn
    proto.activationThreshold = self.activationThreshold
    proto.initialPermanence = self.initialPermanence
    proto.connectedPermanence = self.connectedPermanence
    proto.minThreshold = self.minThreshold
    proto.maxNewSynapseCount = self.maxNewSynapseCount
    proto.permanenceIncrement = self.permanenceIncrement
    proto.permanenceDecrement = self.permanenceDecrement

    self.connections.write(proto.connections)
    self._random.write(proto.random)

    proto.activeCells = list(self.activeCells)
    proto.predictiveCells = list(self.predictiveCells)
    proto.activeSegments = list(self.activeSegments)
    proto.winnerCells = list(self.winnerCells)


  @classmethod
  def read(cls, proto):
    """
    Reads deserialized data from proto object

    @param proto (DynamicStructBuilder) Proto object

    @return (TemporalMemory) TemporalMemory instance
    """
    tm = object.__new__(cls)

    tm.columnDimensions = list(proto.columnDimensions)
    tm.cellsPerColumn = int(proto.cellsPerColumn)
    tm.activationThreshold = int(proto.activationThreshold)
    tm.initialPermanence = proto.initialPermanence
    tm.connectedPermanence = proto.connectedPermanence
    tm.minThreshold = int(proto.minThreshold)
    tm.maxNewSynapseCount = int(proto.maxNewSynapseCount)
    tm.permanenceIncrement = proto.permanenceIncrement
    tm.permanenceDecrement = proto.permanenceDecrement

    tm.connections = Connections.read(proto.connections)
    tm._random = Random()
    tm._random.read(proto.random)

    tm.activeCells = set([int(x) for x in proto.activeCells])
    tm.predictiveCells = set([int(x) for x in proto.predictiveCells])
    tm.activeSegments = set([int(x) for x in proto.activeSegments])
    tm.winnerCells = set([int(x) for x in proto.winnerCells])

    return tm


  def __eq__(self, other):
    """
    Equality operator for TemporalMemory instances.
    Checks if two instances are functionally identical
    (might have different internal state).

    @param other (TemporalMemory) TemporalMemory instance to compare to
    """
    epsilon = 0.0000001

    if self.columnDimensions != other.columnDimensions: return False
    if self.cellsPerColumn != other.cellsPerColumn: return False
    if self.activationThreshold != other.activationThreshold: return False
    if abs(self.initialPermanence - other.initialPermanence) > epsilon:
      return False
    if abs(self.connectedPermanence - other.connectedPermanence) > epsilon:
      return False
    if self.minThreshold != other.minThreshold: return False
    if self.maxNewSynapseCount != other.maxNewSynapseCount: return False
    if abs(self.permanenceIncrement - other.permanenceIncrement) > epsilon:
      return False
    if abs(self.permanenceDecrement - other.permanenceDecrement) > epsilon:
      return False

    if self.connections != other.connections: return False

    if self.activeCells != other.activeCells: return False
    if self.predictiveCells != other.predictiveCells: return False
    if self.winnerCells != other.winnerCells: return False

    return True


  def __ne__(self, other):
    """
    Non-equality operator for TemporalMemory instances.
    Checks if two instances are not functionally identical
    (might have different internal state).

    @param other (TemporalMemory) TemporalMemory instance to compare to
    """
    return not self.__eq__(other)


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


  @classmethod
  def getCellIndices(cls, cells):
    return [cls.getCellIndex(c) for c in cells]


  @staticmethod
  def getCellIndex(cell):
    return cell.idx
