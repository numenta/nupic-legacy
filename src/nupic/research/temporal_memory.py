# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014-2016, Numenta, Inc.  Unless you have an agreement
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

from collections import defaultdict
from operator import mul


from nupic.bindings.math import Random
from nupic.research.connections import Connections, binSearch
from nupic.support.group_by import groupby2

EPSILON = 0.00001 # constant error threshold to check equality of permanences to
                  # other floats



class TemporalMemory(object):
  """ Class implementing the Temporal Memory algorithm. """

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
               predictedSegmentDecrement=0.0,
               maxSegmentsPerCell=255,
               maxSynapsesPerSegment=255,
               seed=42,
               **kwargs):
    """
    @param columnDimensions (list)
    Dimensions of the column space

    @param cellsPerColumn (int)
    Number of cells per column

    @param activationThreshold (int)
    If the number of active connected synapses on a segment is at least this
    threshold, the segment is said to be active.

    @param initialPermanence (float)
    Initial permanence of a new synapse

    @param connectedPermanence (float)
    If the permanence value for a synapse is greater than this value, it is said
    to be connected.

    @param minThreshold (int)
    If the number of potential synapses active on a segment is at least this
    threshold, it is said to be "matching" and is eligible for learning.

    @param maxNewSynapseCount (int)
    The maximum number of synapses added to a segment during learning.

    @param permanenceIncrement (float)
    Amount by which permanences of synapses are incremented during learning.

    @param permanenceDecrement (float)
    Amount by which permanences of synapses are decremented during learning.

    @param predictedSegmentDecrement (float)
    Amount by which segments are punished for incorrect predictions.

    @param seed (int)
    Seed for the random number generator.

    @param maxSegmentsPerCell
    The maximum number of segments per cell.

    @param maxSynapsesPerSegment
    The maximum number of synapses per segment.


    Notes:

    predictedSegmentDecrement: A good value is just a bit larger than
    (the column-level sparsity * permanenceIncrement). So, if column-level
    sparsity is 2% and permanenceIncrement is 0.01, this parameter should be
    something like 4% * 0.01 = 0.0004).
    """
    # Error checking
    if not len(columnDimensions):
      raise ValueError("Number of column dimensions must be greater than 0")

    if cellsPerColumn <= 0:
      raise ValueError("Number of cells per column must be greater than 0")

    if minThreshold > activationThreshold:
      raise ValueError(
        "The min threshold can't be greater than the activation threshold")

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
    self.predictedSegmentDecrement = predictedSegmentDecrement

    # Initialize member variables
    self.connections = self.connectionsFactory(
      self.numberOfCells(),
      maxSegmentsPerCell=maxSegmentsPerCell,
      maxSynapsesPerSegment=maxSynapsesPerSegment
    )
    self._random = Random(seed)
    self.activeCells = []
    self.winnerCells = []
    self.activeSegments = []
    self.matchingSegments = []

    self.numActiveConnectedSynapsesForSegment = []
    self.numActivePotentialSynapsesForSegment = []



  @staticmethod
  def connectionsFactory(*args, **kwargs):
    """
    Create a Connections instance.  TemporalMemory subclasses may override this
    method to choose a different Connections implementation, or to augment the
    instance otherwise returned by the default Connections implementation.

    See Connections for constructor signature and usage.

    @return: Connections instance
    """
    return Connections(*args, **kwargs)


  # ==============================
  # Main methods
  # ==============================


  def compute(self, activeColumns, learn=True):
    """
    Perform one time step of the Temporal Memory algorithm.

    This method calls activateCells, then calls activateDendrites. Using
    the TemporalMemory via its compute method ensures that you'll always
    be able to call getPredictiveCells to get predictions for the next
    time step.

    @param activeColumns (iter)
    Indices of active columns

    @param learn (bool)
    Whether or not learning is enabled

    """
    self.activateCells(sorted(activeColumns), learn)
    self.activateDendrites(learn)


  def activateCells(self, activeColumns, learn=True):
    """
    Calculate the active cells, using the current active columns and dendrite
    segments. Grow and reinforce synapses.

    @param activeColumns (iter)
    A sorted list of active column indices.

    @param learn (bool)
    If true, reinforce / punish / grow synapses.

    Pseudocode:
    for each column
      if column is active and has active distal dendrite segments
        call activatePredictedColumn
      if column is active and doesn't have active distal dendrite segments
        call burstColumn
      if column is inactive and has matching distal dendrite segments
        call punishPredictedColumn
    """
    prevActiveCells = self.activeCells
    prevWinnerCells = self.winnerCells
    self.activeCells = []
    self.winnerCells = []

    segToCol = lambda segment: int(segment.cell / self.cellsPerColumn)
    identity = lambda x: x

    for columnData in groupby2(activeColumns, identity,
                               self.activeSegments, segToCol,
                               self.matchingSegments, segToCol):
      (column,
       activeColumns,
       columnActiveSegments,
       columnMatchingSegments) = columnData
      if activeColumns is not None:
        if columnActiveSegments is not None:
          cellsToAdd = self.activatePredictedColumn(column,
                                                    columnActiveSegments,
                                                    columnMatchingSegments,
                                                    prevActiveCells,
                                                    prevWinnerCells,
                                                    learn)

          self.activeCells += cellsToAdd
          self.winnerCells += cellsToAdd
        else:
          (cellsToAdd,
           winnerCell) = self.burstColumn(column,
                                          columnMatchingSegments,
                                          prevActiveCells,
                                          prevWinnerCells,
                                          learn)

          self.activeCells += cellsToAdd
          self.winnerCells.append(winnerCell)
      else:
        if learn:
          self.punishPredictedColumn(column,
                                     columnActiveSegments,
                                     columnMatchingSegments,
                                     prevActiveCells,
                                     prevWinnerCells)


  def activateDendrites(self, learn=True):
    """
    Calculate dendrite segment activity, using the current active cells.

    @param learn (bool)
    If true, segment activations will be recorded. This information is used
    during segment cleanup.

    Pseudocode:
    for each distal dendrite segment with activity >= activationThreshold
      mark the segment as active
    for each distal dendrite segment with unconnected activity >= minThreshold
      mark the segment as matching
    """
    (numActiveConnected,
     numActivePotential) = self.connections.computeActivity(
       self.activeCells,
       self.connectedPermanence)

    activeSegments = (
      self.connections.segmentForFlatIdx(i)
      for i in xrange(len(numActiveConnected))
      if numActiveConnected[i] >= self.activationThreshold
    )

    matchingSegments = (
      self.connections.segmentForFlatIdx(i)
      for i in xrange(len(numActivePotential))
      if numActivePotential[i] >= self.minThreshold
    )

    self.activeSegments = sorted(activeSegments,
                                 key=self.connections.segmentPositionSortKey)
    self.matchingSegments = sorted(matchingSegments,
                                   key=self.connections.segmentPositionSortKey)
    self.numActiveConnectedSynapsesForSegment = numActiveConnected
    self.numActivePotentialSynapsesForSegment = numActivePotential

    if learn:
      for segment in self.activeSegments:
        self.connections.recordSegmentActivity(segment)
      self.connections.startNewIteration()


  def reset(self):
    """
    Indicates the start of a new sequence. Clears any predictions and makes sure
    synapses don't grow to the currently active cells in the next time step.
    """
    self.activeCells = []
    self.winnerCells = []
    self.activeSegments = []
    self.matchingSegments = []


  # ==============================
  # Extension points
  # These methods are designed to be overridden.
  # ==============================


  def activatePredictedColumn(self, column, columnActiveSegments,
                              columnMatchingSegments, prevActiveCells,
                              prevWinnerCells, learn):
    """
    Determines which cells in a predicted column should be added to winner cells
    list, and learns on the segments that correctly predicted this column.

    @param column (int)
    Index of bursting column.

    @param columnActiveSegments (iter)
    Active segments in this column.

    @param columnActiveSegments (iter)
    Matching segments in this column.

    @param prevActiveCells (list)
    Active cells in `t-1`.

    @param prevWinnerCells (list)
    Winner cells in `t-1`.

    @param learn (bool)
    If true, grow and reinforce synapses.

    @return cellsToAdd (list)
    A list of predicted cells that will be added to active cells and winner
    cells.
    """
    return self._activatePredictedColumn(
      self.connections, self._random,
      columnActiveSegments, prevActiveCells, prevWinnerCells,
      self.numActivePotentialSynapsesForSegment,
      self.maxNewSynapseCount, self.initialPermanence,
      self.permanenceIncrement, self.permanenceDecrement, learn)


  def burstColumn(self, column, columnMatchingSegments, prevActiveCells,
                  prevWinnerCells, learn):
    """
    Activates all of the cells in an unpredicted active column, chooses a winner
    cell, and, if learning is turned on, learns on one segment, growing a new
    segment if necessary.

    @param column (int)
    Index of bursting column.

    @param columnMatchingSegments (iter)
    Matching segments in this column, or None if there aren't any.

    @param prevActiveCells (list)
    Active cells in `t-1`.

    @param prevWinnerCells (list)
    Winner cells in `t-1`.

    @param learn (bool)
    Whether or not learning is enabled.

    @return (tuple) Contains:
                      `cells`         (iter),
                      `winnerCell`    (int),
    """

    start = self.cellsPerColumn * column
    cellsForColumn = xrange(start, start + self.cellsPerColumn)

    return self._burstColumn(
      self.connections, self._random, column, columnMatchingSegments,
      prevActiveCells, prevWinnerCells, cellsForColumn,
      self.numActivePotentialSynapsesForSegment, self.maxNewSynapseCount,
      self.initialPermanence, self.permanenceIncrement,
      self.permanenceDecrement, learn)


  def punishPredictedColumn(self, column, columnActiveSegments,
                            columnMatchingSegments, prevActiveCells,
                            prevWinnerCells):
    """
    Punishes the Segments that incorrectly predicted a column to be active.

    @param column (int)
    Index of bursting column.

    @param columnActiveSegments (iter)
    Active segments for this column, or None if there aren't any.

    @param columnMatchingSegments (iter)
    Matching segments for this column, or None if there aren't any.

    @param prevActiveCells (list)
    Active cells in `t-1`.

    @param prevWinnerCells (list)
    Winner cells in `t-1`.

    """
    self._punishPredictedColumn(
      self.connections, columnMatchingSegments, prevActiveCells,
      self.predictedSegmentDecrement)


  # ==============================
  # Helper methods
  #
  # These class methods use the following parameter ordering convention:
  #
  # 1. Output / mutated params
  # 2. Traditional parameters to the method, i.e. the ones that would still
  #    exist if this were in instance method.
  # 3. Model state (not mutated)
  # 4. Model parameters (including "learn")
  # ==============================


  @classmethod
  def _activatePredictedColumn(cls, connections, random, columnActiveSegments,
                               prevActiveCells, prevWinnerCells,
                               numActivePotentialSynapsesForSegment,
                               maxNewSynapseCount,
                               initialPermanence, permanenceIncrement,
                               permanenceDecrement, learn):
    """
    @param connections (Object)
    Connections for the TM. Gets mutated.

    @param random (Object)
    Random number generator. Gets mutated.

    @param columnActiveSegments (iter)
    Active segments in this column.

    @param prevActiveCells (list)
    Active cells in `t-1`.

    @param prevWinnerCells (list)
    Winner cells in `t-1`.

    @param numActivePotentialSynapsesForSegment (list)
    Number of active potential synapses per segment, indexed by the segment's
    flatIdx.

    @param maxNewSynapseCount (int)
    The maximum number of synapses added to a segment during learning

    @param initialPermanence (float)
    Initial permanence of a new synapse.

    @permanenceIncrement (float)
    Amount by which permanences of synapses are incremented during learning.

    @permanenceDecrement (float)
    Amount by which permanences of synapses are decremented during learning.

    @param learn (bool)
    If true, grow and reinforce synapses.

    @return cellsToAdd (list)
    A list of predicted cells that will be added to active cells and winner
    cells.

    Pseudocode:
    for each cell in the column that has an active distal dendrite segment
      mark the cell as active
      mark the cell as a winner cell
      (learning) for each active distal dendrite segment
        strengthen active synapses
        weaken inactive synapses
        grow synapses to previous winner cells
    """

    cellsToAdd = []
    previousCell = None
    for segment in columnActiveSegments:
      if segment.cell != previousCell:
        cellsToAdd.append(segment.cell)
        previousCell = segment.cell

      if learn:
        cls._adaptSegment(connections, segment, prevActiveCells,
                          permanenceIncrement, permanenceDecrement)

        active = numActivePotentialSynapsesForSegment[segment.flatIdx]
        nGrowDesired = maxNewSynapseCount - active

        if nGrowDesired > 0:
          cls._growSynapses(connections, random, segment, nGrowDesired,
                            prevWinnerCells, initialPermanence)

    return cellsToAdd


  @classmethod
  def _burstColumn(cls, connections, random, column, columnMatchingSegments,
                   prevActiveCells, prevWinnerCells, cellsForColumn,
                   numActivePotentialSynapsesForSegment, maxNewSynapseCount,
                   initialPermanence, permanenceIncrement,
                   permanenceDecrement, learn):
    """
    @param connections (Object)
    Connections for the TM. Gets mutated.

    @param random (Object)
    Random number generator. Gets mutated.

    @param column (int)
    Index of bursting column.

    @param columnMatchingSegments (iter)
    Matching segments in this column.

    @param prevActiveCells (list)
    Active cells in `t-1`.

    @param prevWinnerCells (list)
    Winner cells in `t-1`.

    @param cellsForColumn (sequence)
    Range of cell indices on which to operate.

    @param numActivePotentialSynapsesForSegment (list)
    Number of active potential synapses per segment, indexed by the segment's
    flatIdx.

    @param maxNewSynapseCount (int)
    The maximum number of synapses added to a segment during learning.

    @param initialPermanence (float)
    Initial permanence of a new synapse.

    @param permanenceIncrement (float)
    Amount by which permanences of synapses are incremented during learning.

    @param permanenceDecrement (float)
    Amount by which permanences of synapses are decremented during learning.

    @param learn (bool)
    Whether or not learning is enabled.

    @return (tuple) Contains:
                      `cells`         (iter),
                      `winnerCell`    (int),

    Pseudocode:
    mark all cells as active
    if there are any matching distal dendrite segments
      find the most active matching segment
      mark its cell as a winner cell
      (learning)
        grow and reinforce synapses to previous winner cells
    else
      find the cell with the least segments, mark it as a winner cell
      (learning)
        (optimization) if there are prev winner cells
          add a segment to this winner cell
          grow synapses to previous winner cells
    """
    if columnMatchingSegments is not None:
      numActive = lambda s: numActivePotentialSynapsesForSegment[s.flatIdx]
      bestMatchingSegment = max(columnMatchingSegments, key=numActive)
      winnerCell = bestMatchingSegment.cell

      if learn:
        cls._adaptSegment(connections, bestMatchingSegment, prevActiveCells,
                          permanenceIncrement, permanenceDecrement)

        nGrowDesired = maxNewSynapseCount - numActive(bestMatchingSegment)

        if nGrowDesired > 0:
          cls._growSynapses(connections, random, bestMatchingSegment,
                            nGrowDesired, prevWinnerCells, initialPermanence)
    else:
      winnerCell = cls._leastUsedCell(random, cellsForColumn, connections)
      if learn:
        nGrowExact = min(maxNewSynapseCount, len(prevWinnerCells))
        if nGrowExact > 0:
          segment = connections.createSegment(winnerCell)
          cls._growSynapses(connections, random, segment, nGrowExact,
                            prevWinnerCells, initialPermanence)

    return cellsForColumn, winnerCell


  @classmethod
  def _punishPredictedColumn(cls, connections, columnMatchingSegments,
                             prevActiveCells, predictedSegmentDecrement):
    """
    @param connections (Object)
    Connections for the TM. Gets mutated.

    @param columnMatchingSegments (iter)
    Matching segments for this column.

    @param prevActiveCells (list)
    Active cells in `t-1`.

    @param predictedSegmentDecrement (float)
    Amount by which segments are punished for incorrect predictions.

    Pseudocode:
    for each matching segment in the column
      weaken active synapses
    """
    if predictedSegmentDecrement > 0.0 and columnMatchingSegments is not None:
      for segment in columnMatchingSegments:
        cls._adaptSegment(connections, segment, prevActiveCells,
                          -predictedSegmentDecrement, 0.0)


  @classmethod
  def _leastUsedCell(cls, random, cells, connections):
    """
    Gets the cell with the smallest number of segments.
    Break ties randomly.

    @param random (Object)
    Random number generator. Gets mutated.

    @param cells (list)
    Indices of cells.

    @param connections (Object)
    Connections instance for the TM.

    @return (int) Cell index.
    """
    leastUsedCells = []
    minNumSegments = float("inf")
    for cell in cells:
      numSegments = connections.numSegments(cell)

      if numSegments < minNumSegments:
        minNumSegments = numSegments
        leastUsedCells = []

      if numSegments == minNumSegments:
        leastUsedCells.append(cell)

    i = random.getUInt32(len(leastUsedCells))
    return leastUsedCells[i]


  @classmethod
  def _growSynapses(cls, connections, random, segment, nDesiredNewSynapes,
                    prevWinnerCells, initialPermanence):
    """
    Creates nDesiredNewSynapes synapses on the segment passed in if
    possible, choosing random cells from the previous winner cells that are
    not already on the segment.

    @param  connections        (Object) Connections instance for the tm
    @param  random             (Object) TM object used to generate random
                                        numbers
    @param  segment            (int)    Segment to grow synapses on.
    @params nDesiredNewSynapes (int)    Desired number of synapses to grow
    @params prevWinnerCells    (list)   Winner cells in `t-1`
    @param  initialPermanence  (float)  Initial permanence of a new synapse.

    """
    candidates = list(prevWinnerCells)

    for synapse in connections.synapsesForSegment(segment):
      i = binSearch(candidates, synapse.presynapticCell)
      if i != -1:
        del candidates[i]

    nActual = min(nDesiredNewSynapes, len(candidates))

    for _ in range(nActual):
      i = random.getUInt32(len(candidates))
      connections.createSynapse(segment, candidates[i], initialPermanence)
      del candidates[i]


  @classmethod
  def _adaptSegment(cls, connections, segment, prevActiveCells,
                    permanenceIncrement, permanenceDecrement):
    """
    Updates synapses on segment.
    Strengthens active synapses; weakens inactive synapses.

    @param connections          (Object) Connections instance for the tm
    @param segment              (int)    Segment to adapt
    @param prevActiveCells      (list)   Active cells in `t-1`
    @param permanenceIncrement  (float)  Amount to increment active synapses
    @param permanenceDecrement  (float)  Amount to decrement inactive synapses
    """

    # Destroying a synapse modifies the set that we're iterating through.
    synapsesToDestroy = []

    for synapse in connections.synapsesForSegment(segment):
      permanence = synapse.permanence

      if binSearch(prevActiveCells, synapse.presynapticCell) != -1:
        permanence += permanenceIncrement
      else:
        permanence -= permanenceDecrement

      # Keep permanence within min/max bounds
      permanence = max(0.0, min(1.0, permanence))

      if permanence < EPSILON:
        synapsesToDestroy.append(synapse)
      else:
        connections.updateSynapsePermanence(synapse, permanence)

    for synapse in synapsesToDestroy:
      connections.destroySynapse(synapse)

    if connections.numSynapses(segment) == 0:
      connections.destroySegment(segment)


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

    @return (list) Cell indices
    """
    self._validateColumn(column)

    start = self.cellsPerColumn * column
    end = start + self.cellsPerColumn
    return range(start, end)


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
    Maps cells to the columns they belong to.

    @param cells (set) Cells

    @return (dict) Mapping from columns to their cells in `cells`
    """
    cellsForColumns = defaultdict(set)

    for cell in cells:
      column = self.columnForCell(cell)
      cellsForColumns[column].add(cell)

    return cellsForColumns


  def getActiveCells(self):
    """
    Returns the indices of the active cells.

    @return (list) Indices of active cells.
    """
    return self.getCellIndices(self.activeCells)


  def getPredictiveCells(self):
    """ Returns the indices of the predictive cells.

    @return (list) Indices of predictive cells.
    """
    previousCell = None
    predictiveCells = []
    for segment in self.activeSegments:
      if segment.cell != previousCell:
        predictiveCells.append(segment.cell)
        previousCell = segment.cell

    return predictiveCells


  def getWinnerCells(self):
    """
    Returns the indices of the winner cells.

    @return (list) Indices of winner cells.
    """
    return self.getCellIndices(self.winnerCells)


  def getActiveSegments(self):
    """
    Returns the active segments.

    @return (list) Active segments
    """
    return self.activeSegments


  def getMatchingSegments(self):
    """
    Returns the matching segments.

    @return (list) Matching segments
    """
    return self.matchingSegments


  def getCellsPerColumn(self):
    """
    Returns the number of cells per column.

    @return (int) The number of cells per column.
    """
    return self.cellsPerColumn


  def getColumnDimensions(self):
    """
    Returns the dimensions of the columns in the region.
    @return (tuple) Column dimensions
    """
    return self.columnDimensions


  def getActivationThreshold(self):
    """
    Returns the activation threshold.
    @return (int) The activation threshold.
    """
    return self.activationThreshold


  def setActivationThreshold(self, activationThreshold):
    """
    Sets the activation threshold.
    @param activationThreshold (int) activation threshold.
    """
    self.activationThreshold = activationThreshold


  def getInitialPermanence(self):
    """
    Get the initial permanence.
    @return (float) The initial permanence.
    """
    return self.initialPermanence


  def setInitialPermanence(self, initialPermanence):
    """
    Sets the initial permanence.
    @param initialPermanence (float) The initial permanence.
    """
    self.initialPermanence = initialPermanence


  def getMinThreshold(self):
    """
    Returns the min threshold.
    @return (int) The min threshold.
    """
    return self.minThreshold


  def setMinThreshold(self, minThreshold):
    """
    Sets the min threshold.
    @param minThreshold (int) min threshold.
    """
    self.minThreshold = minThreshold


  def getMaxNewSynapseCount(self):
    """
    Returns the max new synapse count.
    @return (int) The max new synapse count.
    """
    return self.maxNewSynapseCount


  def setMaxNewSynapseCount(self, maxNewSynapseCount):
    """
    Sets the max new synapse count.
    @param maxNewSynapseCount (int) Max new synapse count.
    """
    self.maxNewSynapseCount = maxNewSynapseCount


  def getPermanenceIncrement(self):
    """
    Get the permanence increment.
    @return (float) The permanence increment.
    """
    return self.permanenceIncrement


  def setPermanenceIncrement(self, permanenceIncrement):
    """
    Sets the permanence increment.
    @param permanenceIncrement (float) The permanence increment.
    """
    self.permanenceIncrement = permanenceIncrement


  def getPermanenceDecrement(self):
    """
    Get the permanence decrement.
    @return (float) The permanence decrement.
    """
    return self.permanenceDecrement


  def setPermanenceDecrement(self, permanenceDecrement):
    """
    Sets the permanence decrement.
    @param permanenceDecrement (float) The permanence decrement.
    """
    self.permanenceDecrement = permanenceDecrement


  def getPredictedSegmentDecrement(self):
    """
    Get the predicted segment decrement.
    @return (float) The predicted segment decrement.
    """
    return self.predictedSegmentDecrement


  def setPredictedSegmentDecrement(self, predictedSegmentDecrement):
    """
    Sets the predicted segment decrement.
    @param predictedSegmentDecrement (float) The predicted segment decrement.
    """
    self.predictedSegmentDecrement = predictedSegmentDecrement


  def getConnectedPermanence(self):
    """
    Get the connected permanence.
    @return (float) The connected permanence.
    """
    return self.connectedPermanence


  def setConnectedPermanence(self, connectedPermanence):
    """
    Sets the connected permanence.
    @param connectedPermanence (float) The connected permanence.
    """
    self.connectedPermanence = connectedPermanence

  
  def getMaxSegmentsPerCell(self):
      """
      Get the maximum number of segments per cell
      @return (int) max number of segments per cell
      """
      return self.connections.maxSegmentsPerCell

  
  def getMaxSynapsesPerSegment(self):
      """
      Get the maximum number of synapses per segment.
      @return (int) max number of synapses per segment
      """
      return self.connections.maxSynapsesPerSegment


  def write(self, proto):
    """
    Writes serialized data to proto object.

    @param proto (DynamicStructBuilder) Proto object
    """
    # capnp fails to save a tuple.  Let's force columnDimensions to list.
    proto.columnDimensions = list(self.columnDimensions)
    proto.cellsPerColumn = self.cellsPerColumn
    proto.activationThreshold = self.activationThreshold
    proto.initialPermanence = self.initialPermanence
    proto.connectedPermanence = self.connectedPermanence
    proto.minThreshold = self.minThreshold
    proto.maxNewSynapseCount = self.maxNewSynapseCount
    proto.permanenceIncrement = self.permanenceIncrement
    proto.permanenceDecrement = self.permanenceDecrement
    proto.predictedSegmentDecrement = self.predictedSegmentDecrement

    self.connections.write(proto.connections)
    self._random.write(proto.random)

    proto.activeCells = list(self.activeCells)
    proto.winnerCells = list(self.winnerCells)
    activeSegmentOverlaps = \
        proto.init('activeSegmentOverlaps', len(self.activeSegments))
    for i, segment in enumerate(self.activeSegments):
      activeSegmentOverlaps[i].cell = segment.cell
      idx = self.connections.segmentsForCell(segment.cell).index(segment)
      activeSegmentOverlaps[i].segment = idx
      activeSegmentOverlaps[i].overlap = (
        self.numActiveConnectedSynapsesForSegment[segment.flatIdx]
      )

    matchingSegmentOverlaps = \
        proto.init('matchingSegmentOverlaps', len(self.matchingSegments))
    for i, segment in enumerate(self.matchingSegments):
      matchingSegmentOverlaps[i].cell = segment.cell
      idx = self.connections.segmentsForCell(segment.cell).index(segment)
      matchingSegmentOverlaps[i].segment = idx
      matchingSegmentOverlaps[i].overlap = (
        self.numActivePotentialSynapsesForSegment[segment.flatIdx]
      )


  @classmethod
  def read(cls, proto):
    """
    Reads deserialized data from proto object.

    @param proto (DynamicStructBuilder) Proto object

    @return (TemporalMemory) TemporalMemory instance
    """
    tm = object.__new__(cls)

    # capnp fails to save a tuple, so proto.columnDimensions was forced to
    # serialize as a list.  We prefer a tuple, however, because columnDimensions
    # should be regarded as immutable.
    tm.columnDimensions = tuple(proto.columnDimensions)
    tm.cellsPerColumn = int(proto.cellsPerColumn)
    tm.activationThreshold = int(proto.activationThreshold)
    tm.initialPermanence = proto.initialPermanence
    tm.connectedPermanence = proto.connectedPermanence
    tm.minThreshold = int(proto.minThreshold)
    tm.maxNewSynapseCount = int(proto.maxNewSynapseCount)
    tm.permanenceIncrement = proto.permanenceIncrement
    tm.permanenceDecrement = proto.permanenceDecrement
    tm.predictedSegmentDecrement = proto.predictedSegmentDecrement

    tm.connections = Connections.read(proto.connections)
    #pylint: disable=W0212
    tm._random = Random()
    tm._random.read(proto.random)
    #pylint: enable=W0212

    tm.activeCells = [int(x) for x in proto.activeCells]
    tm.winnerCells = [int(x) for x in proto.winnerCells]

    flatListLength = tm.connections.segmentFlatListLength()
    tm.numActiveConnectedSynapsesForSegment = [0] * flatListLength
    tm.numActivePotentialSynapsesForSegment = [0] * flatListLength

    tm.activeSegments = []
    tm.matchingSegments = []

    for i in xrange(len(proto.activeSegmentOverlaps)):
      protoSegmentOverlap = proto.activeSegmentOverlaps[i]

      segment = tm.connections.getSegment(protoSegmentOverlap.cell,
                                          protoSegmentOverlap.segment)
      tm.activeSegments.append(segment)

      overlap = protoSegmentOverlap.overlap
      tm.numActiveConnectedSynapsesForSegment[segment.flatIdx] = overlap

    for i in xrange(len(proto.matchingSegmentOverlaps)):
      protoSegmentOverlap = proto.matchingSegmentOverlaps[i]

      segment = tm.connections.getSegment(protoSegmentOverlap.cell,
                                          protoSegmentOverlap.segment)
      tm.matchingSegments.append(segment)

      overlap = protoSegmentOverlap.overlap
      tm.numActivePotentialSynapsesForSegment[segment.flatIdx] = overlap

    return tm


  def __eq__(self, other):
    """
    Non-equality operator for TemporalMemory instances.
    Checks if two instances are functionally identical
    (might have different internal state).

    @param other (TemporalMemory) TemporalMemory instance to compare to
    """
    if self.columnDimensions != other.columnDimensions:
      return False
    if self.cellsPerColumn != other.cellsPerColumn:
      return False
    if self.activationThreshold != other.activationThreshold:
      return False
    if abs(self.initialPermanence - other.initialPermanence) > EPSILON:
      return False
    if abs(self.connectedPermanence - other.connectedPermanence) > EPSILON:
      return False
    if self.minThreshold != other.minThreshold:
      return False
    if self.maxNewSynapseCount != other.maxNewSynapseCount:
      return False
    if abs(self.permanenceIncrement - other.permanenceIncrement) > EPSILON:
      return False
    if abs(self.permanenceDecrement - other.permanenceDecrement) > EPSILON:
      return False
    if abs(self.predictedSegmentDecrement -
           other.predictedSegmentDecrement) > EPSILON:
      return False

    if self.connections != other.connections:
      return False
    if self.activeCells != other.activeCells:
      return False
    if self.winnerCells != other.winnerCells:
      return False

    if self.matchingSegments != other.matchingSegments:
      return False
    if self.activeSegments != other.activeSegments:
      return False

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
    """
    Returns the indices of the cells passed in.

    @param cells (list) cells to find the indices of
    """
    return [cls.getCellIndex(c) for c in cells]


  @staticmethod
  def getCellIndex(cell):
    """
    Returns the index of the cell.

    @param cell (int) cell to find the index of
    """
    return cell
