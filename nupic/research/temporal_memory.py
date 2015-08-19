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
from nupic.network.cell import Cell
from nupic.network.layer import Layer



EPSILON = 0.0000001



class TemporalMemory(object):
  """
  Class implementing the Temporal Memory algorithm.
  """

  def __init__(self,
               layer=Layer(columnDimensions=(2048,), numCellsPerColumn=32),
               activationThreshold=13,
               initialPermanence=0.21,
               connectedPermanence=0.50,
               minThreshold=10,
               maxNewSynapseCount=20,
               permanenceIncrement=0.10,
               permanenceDecrement=0.10,
               predictedSegmentDecrement = 0.0,
               seed=42):
    """
    @param layer                     (Layer)  The cortical layer which will be processed.
    @param activationThreshold       (int)    If the number of active connected synapses on a segment is at least this threshold, the segment is said to be active.
    @param initialPermanence         (float)  Initial permanence of a new synapse.
    @param connectedPermanence       (float)  If the permanence value for a synapse is greater than this value, it is said to be connected.
    @param minThreshold              (int)    If the number of synapses active on a segment is at least this threshold, it is selected as the best matching cell in a bursting column.
    @param maxNewSynapseCount        (int)    The maximum number of synapses added to a segment during learning.
    @param permanenceIncrement       (float)  Amount by which permanences of synapses are incremented during learning.
    @param permanenceDecrement       (float)  Amount by which permanences of synapses are decremented during learning.
    @param predictedSegmentDecrement (float)  Amount by which active permanences of synapses of previously predicted but inactive segments are decremented.
    @param seed                      (int)    Seed for the random number generator.
    """

    # TODO: Validate all parameters (and add validation tests)
    if layer is None:
      raise ValueError("Layer must be an instance of Layer class")

    # Save member variables
    self.layer = layer
    self.activationThreshold = activationThreshold
    self.initialPermanence = initialPermanence
    self.connectedPermanence = connectedPermanence
    self.minThreshold = minThreshold
    self.maxNewSynapseCount = maxNewSynapseCount
    self.permanenceIncrement = permanenceIncrement
    self.permanenceDecrement = permanenceDecrement
    self.predictedSegmentDecrement = predictedSegmentDecrement
    # Initialize member variables
    self._random = Random(seed)

    self.activeCells = set()
    self.predictiveCells = set()
    self.activeSegments = set()
    self.winnerCells = set()
    self.matchingSegments = set()
    self.matchingCells = set()

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
     predictedColumns,
     matchingSegments,
     matchingCells) = self.computeFn(activeColumns,
                                     self.predictiveCells,
                                     self.activeSegments,
                                     self.activeCells,
                                     self.winnerCells,
                                     self.matchingSegments,
                                     self.matchingCells,
                                     learn=learn)

    self.activeCells = activeCells
    self.winnerCells = winnerCells
    self.activeSegments = activeSegments
    self.predictiveCells = predictiveCells
    self.matchingSegments = matchingSegments
    self.matchingCells = matchingCells

  def computeFn(self,
                activeColumns,
                prevPredictiveCells,
                prevActiveSegments,
                prevActiveCells,
                prevWinnerCells,
                prevMatchingSegments,
                prevMatchingCells,
                learn=True):
    """
    'Functional' version of compute.
    Returns new state.

    @param activeColumns         (set)         Indices of active columns in `t`
    @param prevPredictiveCells   (set)         Indices of predictive cells in `t-1`
    @param prevActiveSegments    (set)         Indices of active segments in `t-1`
    @param prevActiveCells       (set)         Indices of active cells in `t-1`
    @param prevWinnerCells       (set)         Indices of winner cells in `t-1`
    @param prevMatchingSegments  (set)         Indices of matching segments in `t-1`
    @param prevMatchingCells     (set)         Indices of matching cells in `t-1`
    @param learn                 (bool)        Whether or not learning is enabled

    @return (tuple) Contains:
                      `activeCells`     (set),
                      `winnerCells`     (set),
                      `activeSegments`  (set),
                      `predictiveCells` (set),
                      'matchingSegments'(set),
                      'matchingCells'   (set)
    """
    activeCells = set()
    winnerCells = set()

    (_activeCells,
     _winnerCells,
     predictedColumns,
     predictedInactiveCells) = self.activateCorrectlyPredictiveCells(
       prevPredictiveCells,
       prevMatchingCells,
       activeColumns)

    activeCells.update(_activeCells)
    winnerCells.update(_winnerCells)

    (_activeCells,
     _winnerCells,
     learningSegments) = self.burstColumns(activeColumns,
                                           predictedColumns,
                                           prevActiveCells,
                                           prevWinnerCells)

    activeCells.update(_activeCells)
    winnerCells.update(_winnerCells)

    if learn:
      self.learnOnSegments(prevActiveSegments,
                           learningSegments,
                           prevActiveCells,
                           winnerCells,
                           prevWinnerCells,
                           predictedInactiveCells,
                           prevMatchingSegments)

    (activeSegments,
     predictiveCells,
     matchingSegments,
     matchingCells) = self.computePredictiveCells(activeCells)

    return (activeCells,
            winnerCells,
            activeSegments,
            predictiveCells,
            predictedColumns,
            matchingSegments,
            matchingCells)


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
                                       prevMatchingCells,
                                       activeColumns):
    """
    Phase 1: Activate the correctly predictive cells.

    Pseudocode:

      - for each prev predictive cell
        - if in active column
          - mark it as active
          - mark it as winner cell
          - mark column as predicted
        - if not in active column
          - mark it as an predicted but inactive cell

    @param prevPredictiveCells (set) Indices of predictive cells in `t-1`
    @param activeColumns       (set) Indices of active columns in `t`

    @return (tuple) Contains:
                      `activeCells`               (set),
                      `winnerCells`               (set),
                      `predictedColumns`          (set),
                      `predictedInactiveCells`    (set)
    """
    activeCells = set()
    winnerCells = set()
    predictedColumns = set()
    predictedInactiveCells = set()

    for cell in prevPredictiveCells:
      column = cell.column

      if column in activeColumns:
        activeCells.add(cell)
        winnerCells.add(cell)
        predictedColumns.add(column)

    if self.predictedSegmentDecrement > 0:
      for cell in prevMatchingCells:
        column = cell.column

        if column not in activeColumns:
          predictedInactiveCells.add(cell)

    return activeCells, winnerCells, predictedColumns, predictedInactiveCells


  def burstColumns(self,
                   activeColumns,
                   predictedColumns,
                   prevActiveCells,
                   prevWinnerCells):
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
      cells = column.cells
      activeCells.update(cells)

      (bestCell,
       bestSegment) = self.bestMatchingCell(cells,
                                            prevActiveCells)
      winnerCells.add(bestCell)

      if bestSegment is None and len(prevWinnerCells):
        bestSegment = bestCell.createSegment()

      if bestSegment is not None:
        learningSegments.add(bestSegment)

    return activeCells, winnerCells, learningSegments


  def learnOnSegments(self,
                      prevActiveSegments,
                      learningSegments,
                      prevActiveCells,
                      winnerCells,
                      prevWinnerCells,
                      predictedInactiveCells,
                      prevMatchingSegments):
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

      - if predictedSegmentDecrement > 0
        - for each previously matching segment
          - if cell is a predicted inactive cell
            - weaken active synapses but don't touch inactive synapses

    @param prevActiveSegments           (set)         Indices of active segments in `t-1`
    @param learningSegments             (set)         Indices of learning segments in `t`
    @param prevActiveCells              (set)         Indices of active cells in `t-1`
    @param winnerCells                  (set)         Indices of winner cells in `t`
    @param prevWinnerCells              (set)         Indices of winner cells in `t-1`
    @param predictedInactiveCells       (set)         Indices of predicted inactive cells
    @param prevMatchingSegments         (set)         Indices of segments with
    """
    for segment in prevActiveSegments | learningSegments:
      isLearningSegment = segment in learningSegments
      isFromWinnerCell = segment.cell in winnerCells

      activeSynapses = self.activeSynapsesForSegment(
        segment, prevActiveCells)

      if isLearningSegment or isFromWinnerCell:
        self.adaptSegment(segment, activeSynapses,
                          self.permanenceIncrement,
                          self.permanenceDecrement)

      if isLearningSegment:
        n = self.maxNewSynapseCount - len(activeSynapses)

        for presynapticCell in self.pickCellsToLearnOn(n,
                                                       segment,
                                                       prevWinnerCells):
          segment.createSynapse(presynapticCell=presynapticCell,
                                permanence=self.initialPermanence)

    if self.predictedSegmentDecrement > 0:
      for segment in prevMatchingSegments:
        isPredictedInactiveCell = segment.cell in predictedInactiveCells
        activeSynapses = self.activeSynapsesForSegment(
          segment, prevActiveCells)

        if isPredictedInactiveCell:
          self.adaptSegment(segment, activeSynapses,
                            -self.predictedSegmentDecrement,
                            0.0)



  def computePredictiveCells(self, activeCells):
    """
    Phase 4: Compute predictive cells due to lateral input
    on distal dendrites.

    Pseudocode:

      - for each distal dendrite segment with activity >= activationThreshold
        - mark the segment as active
        - mark the cell as predictive

      - if predictedSegmentDecrement > 0
        - for each distal dendrite segment with unconnected
          activity >=  minThreshold
          - mark the segment as matching
          - mark the cell as matching

    Forward propagates activity from active cells to the synapses that touch
    them, to determine which synapses are active.

    @param activeCells (set)         Indices of active cells in `t`

    @return (tuple) Contains:
                      `activeSegments`  (set),
                      `predictiveCells` (set),
                      `matchingSegments` (set),
                      `matchingCells`    (set)
    """
    numActiveConnectedSynapsesForSegment = defaultdict(int)
    numActiveSynapsesForSegment = defaultdict(int)
    activeSegments = set()
    predictiveCells = set()

    matchingSegments = set()
    matchingCells = set()

    for cell in activeCells:
      for synapse in cell.postsynapticCellsSynapses:
        segment = synapse.segment
        permanence = synapse.permanence

        if permanence >= self.connectedPermanence:
          numActiveConnectedSynapsesForSegment[segment] += 1

          if (numActiveConnectedSynapsesForSegment[segment] >=
              self.activationThreshold):
            activeSegments.add(segment)
            predictiveCells.add(segment.cell)

        if permanence > 0 and self.predictedSegmentDecrement > 0:
          numActiveSynapsesForSegment[segment] += 1

          if numActiveSynapsesForSegment[segment] >= self.minThreshold:
            matchingSegments.add(segment)
            matchingCells.add(segment.cell)

    return activeSegments, predictiveCells, matchingSegments, matchingCells


  # ==============================
  # Helper functions
  # ==============================

  def bestMatchingCell(self, cells, activeCells):
    """
    Gets the cell with the best matching segment
    (see `TM.bestMatchingSegment`) that has the largest number of active
    synapses of all best matching segments.

    If none were found, pick the least used cell (see `TM.leastUsedCell`).

    @param cells                       (set)         Indices of cells
    @param activeCells                 (set)         Indices of active cells

    @return (tuple) Contains:
                      `cell`        (int),
                      `bestSegment` (int)
    """
    maxSynapses = 0
    bestCell = None
    bestSegment = None

    for cell in cells:
      segment, numActiveSynapses = self.bestMatchingSegment(
        cell, activeCells)

      if segment is not None and numActiveSynapses > maxSynapses:
        maxSynapses = numActiveSynapses
        bestCell = cell
        bestSegment = segment

    if bestCell is None:
      bestCell = self.leastUsedCell(cells)

    return bestCell, bestSegment


  def bestMatchingSegment(self, cell, activeCells):
    """
    Gets the segment on a cell with the largest number of activate synapses,
    including all synapses with non-zero permanences.

    @param cell                        (int)         Cell index
    @param activeCells                 (set)         Indices of active cells

    @return (tuple) Contains:
                      `segment`                 (int),
                      `connectedActiveSynapses` (set)
    """
    maxSynapses = self.minThreshold
    bestSegment = None
    bestNumActiveSynapses = None

    for segment in cell.segments:
      numActiveSynapses = 0

      for synapse in segment.synapses:
        if synapse.presynapticCell in activeCells and \
           synapse.permanence > 0:
          numActiveSynapses += 1

      if numActiveSynapses >= maxSynapses:
        maxSynapses = numActiveSynapses
        bestSegment = segment
        bestNumActiveSynapses = numActiveSynapses

    return bestSegment, bestNumActiveSynapses


  def leastUsedCell(self, cells):
    """
    Gets the cell with the smallest number of segments.
    Break ties randomly.

    @param cells       (set)         Indices of cells

    @return (int) Cell index
    """
    leastUsedCells = set()
    minNumSegments = float("inf")

    for cell in cells:
      numSegments = len(cell.segments)

      if numSegments < minNumSegments:
        minNumSegments = numSegments
        leastUsedCells = set()

      if numSegments == minNumSegments:
        leastUsedCells.add(cell)

    i = self._random.getUInt32(len(leastUsedCells))
    return sorted(leastUsedCells)[i]


  @staticmethod
  def activeSynapsesForSegment(segment, activeCells):
    """
    Returns the synapses on a segment that are active due to lateral input
    from active cells.

    @param segment     (int)         Segment index
    @param activeCells (set)         Indices of active cells

    @return (set) Indices of active synapses on segment
    """
    synapses = set()

    for synapse in segment.synapses:

      if synapse.presynapticCell in activeCells:
        synapses.add(synapse)

    return synapses


  def adaptSegment(self, segment, activeSynapses,
                   permanenceIncrement, permanenceDecrement):
    """
    Updates synapses on segment.
    Strengthens active synapses; weakens inactive synapses.

    @param segment              (int)         Segment index
    @param activeSynapses       (set)         Indices of active synapses
    @param permanenceIncrement  (float)  Amount to increment active synapses
    @param permanenceDecrement  (float)  Amount to decrement inactive synapses
    """
    # Need to copy synapses for segment set below because it will be modified
    # during iteration by `destroySynapse`
    synapsesToDestroy = set()
    for synapse in segment.synapses:
      permanence = synapse.permanence

      if synapse in activeSynapses:
        permanence += permanenceIncrement
      else:
        permanence -= permanenceDecrement

      # Keep permanence within min/max bounds
      permanence = max(0.0, min(1.0, permanence))

      if (abs(permanence) < EPSILON):
        synapsesToDestroy.add(synapse)
      else:
        synapse.permanence = permanence

    for synapse in synapsesToDestroy:
      segment.destroySynapse(synapse)


  def pickCellsToLearnOn(self, n, segment, winnerCells):
    """
    Pick cells to form distal connections to.

    TODO: Respect topology and learningRadius

    @param n           (int)         Number of cells to pick
    @param segment     (int)         Segment index
    @param winnerCells (set)         Indices of winner cells in `t`

    @return (set) Indices of cells picked
    """
    candidates = set(winnerCells)

    # Remove cells that are already synapsed on by this segment
    for synapse in segment.synapses:
      presynapticCell = synapse.presynapticCell

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


  @classmethod
  def getCellIndices(cls, cells):
    return [cls.getCellIndex(c) for c in cells]


  @staticmethod
  def getCellIndex(cell):
    return cell.idx
