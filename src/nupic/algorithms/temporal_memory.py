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
Temporal Memory implementation in Python. See 
`numenta.com <https://numenta.com/temporal-memory-algorithm/>`_ for details.
"""

from collections import defaultdict
from nupic.bindings.math import Random
from operator import mul

from nupic.algorithms.connections import Connections, binSearch
from nupic.serializable import Serializable
from nupic.support.group_by import groupby2

EPSILON = 0.00001 # constant error threshold to check equality of permanences to
                  # other floats



class TemporalMemory(Serializable):
  """
  Class implementing the Temporal Memory algorithm. 

  .. note::

    ``predictedSegmentDecrement``: A good value is just a bit larger than
    (the column-level sparsity * permanenceIncrement). So, if column-level
    sparsity is 2% and permanenceIncrement is 0.01, this parameter should be
    something like 4% * 0.01 = 0.0004).

  :param columnDimensions: (list or tuple) Dimensions of the column space. 
         Default value ``[2048]``.

  :param cellsPerColumn: (int) Number of cells per column. Default value ``32``.

  :param activationThreshold: (int) If the number of active connected synapses 
         on a segment is at least this threshold, the segment is said to be 
         active. Default value ``13``.

  :param initialPermanence: (float) Initial permanence of a new synapse. Default
         value ``0.21``.

  :param connectedPermanence: (float) If the permanence value for a synapse is 
         greater than this value, it is said to be connected. Default value 
         ``0.5``.

  :param minThreshold: (int) If the number of potential synapses active on a 
         segment is at least this threshold, it is said to be "matching" and 
         is eligible for learning. Default value ``10``.

  :param maxNewSynapseCount: (int) The maximum number of synapses added to a 
         segment during learning. Default value ``20``.

  :param permanenceIncrement: (float) Amount by which permanences of synapses 
         are incremented during learning. Default value ``0.1``.

  :param permanenceDecrement: (float) Amount by which permanences of synapses 
         are decremented during learning. Default value ``0.1``.

  :param predictedSegmentDecrement: (float) Amount by which segments are 
         punished for incorrect predictions. Default value ``0.0``.

  :param seed: (int) Seed for the random number generator. Default value ``42``.

  :param maxSegmentsPerCell: (int) The maximum number of segments per cell. 
         Default value ``255``.

  :param maxSynapsesPerSegment: (int) The maximum number of synapses per 
         segment. Default value ``255``.

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
               predictedSegmentDecrement=0.0,
               maxSegmentsPerCell=255,
               maxSynapsesPerSegment=255,
               seed=42,
               **kwargs):
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
    self.maxSegmentsPerCell = maxSegmentsPerCell
    self.maxSynapsesPerSegment = maxSynapsesPerSegment

    # Initialize member variables
    self.connections = self.connectionsFactory(self.numberOfCells())
    self._random = Random(seed)
    self.activeCells = []
    self.winnerCells = []
    self.activeSegments = []
    self.matchingSegments = []

    self.numActiveConnectedSynapsesForSegment = []
    self.numActivePotentialSynapsesForSegment = []

    self.iteration = 0
    self.lastUsedIterationForSegment = []



  @staticmethod
  def connectionsFactory(*args, **kwargs):
    """
    Create a :class:`~nupic.algorithms.connections.Connections` instance.  
    :class:`TemporalMemory` subclasses may override this method to choose a 
    different :class:`~nupic.algorithms.connections.Connections` implementation, 
    or to augment the instance otherwise returned by the default 
    :class:`~nupic.algorithms.connections.Connections` implementation.

    See :class:`~nupic.algorithms.connections.Connections` for constructor 
    signature and usage.

    :returns: :class:`~nupic.algorithms.connections.Connections` instance
    """
    return Connections(*args, **kwargs)


  # ==============================
  # Main methods
  # ==============================


  def compute(self, activeColumns, learn=True):
    """
    Perform one time step of the Temporal Memory algorithm.

    This method calls :meth:`activateCells`, then calls 
    :meth:`activateDendrites`. Using :class:`TemporalMemory` via its 
    :meth:`compute` method ensures that you'll always be able to call 
    :meth:`getPredictiveCells` to get predictions for the next time step.

    :param activeColumns: (iter) Indices of active columns.

    :param learn: (bool) Whether or not learning is enabled.
    """
    self.activateCells(sorted(activeColumns), learn)
    self.activateDendrites(learn)


  def activateCells(self, activeColumns, learn=True):
    """
    Calculate the active cells, using the current active columns and dendrite
    segments. Grow and reinforce synapses.

    :param activeColumns: (iter) A sorted list of active column indices.

    :param learn: (bool) If true, reinforce / punish / grow synapses.

      **Pseudocode:**
      
      ::

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

    :param learn: (bool) If true, segment activations will be recorded. This 
           information is used during segment cleanup.

    **Pseudocode:**
    
    ::

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
        self.lastUsedIterationForSegment[segment.flatIdx] = self.iteration
      self.iteration += 1


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

    :param column: (int) Index of bursting column.

    :param columnActiveSegments: (iter) Active segments in this column.

    :param columnMatchingSegments: (iter) Matching segments in this column.

    :param prevActiveCells: (list) Active cells in ``t-1``.

    :param prevWinnerCells: (list) Winner cells in ``t-1``.

    :param learn: (bool) If true, grow and reinforce synapses.

    :returns: (list) A list of predicted cells that will be added to 
              active cells and winner cells.
    """
    return self._activatePredictedColumn(
      self.connections, self._random,
      columnActiveSegments, prevActiveCells, prevWinnerCells,
      self.numActivePotentialSynapsesForSegment,
      self.maxNewSynapseCount, self.initialPermanence,
      self.permanenceIncrement, self.permanenceDecrement,
      self.maxSynapsesPerSegment, learn)


  def burstColumn(self, column, columnMatchingSegments, prevActiveCells,
                  prevWinnerCells, learn):
    """
    Activates all of the cells in an unpredicted active column, chooses a winner
    cell, and, if learning is turned on, learns on one segment, growing a new
    segment if necessary.

    :param column: (int) Index of bursting column.

    :param columnMatchingSegments: (iter) Matching segments in this column, or 
           None if there aren't any.

    :param prevActiveCells: (list) Active cells in ``t-1``.

    :param prevWinnerCells: (list) Winner cells in ``t-1``.

    :param learn: (bool) Whether or not learning is enabled.

    :returns: (tuple) Contains (``cells`` [iter], ``winnerCell`` [int])
    """

    start = self.cellsPerColumn * column
    cellsForColumn = xrange(start, start + self.cellsPerColumn)

    return self._burstColumn(
      self.connections, self._random, self.lastUsedIterationForSegment, column,
      columnMatchingSegments, prevActiveCells, prevWinnerCells, cellsForColumn,
      self.numActivePotentialSynapsesForSegment, self.iteration,
      self.maxNewSynapseCount, self.initialPermanence, self.permanenceIncrement,
      self.permanenceDecrement, self.maxSegmentsPerCell,
      self.maxSynapsesPerSegment, learn)


  def punishPredictedColumn(self, column, columnActiveSegments,
                            columnMatchingSegments, prevActiveCells,
                            prevWinnerCells):
    """
    Punishes the Segments that incorrectly predicted a column to be active.

    :param column: (int) Index of bursting column.

    :param columnActiveSegments: (iter) Active segments for this column, or None 
           if there aren't any.

    :param columnMatchingSegments: (iter) Matching segments for this column, or 
           None if there aren't any.

    :param prevActiveCells: (list) Active cells in ``t-1``.

    :param prevWinnerCells: (list) Winner cells in ``t-1``.

    """
    self._punishPredictedColumn(
      self.connections, columnMatchingSegments, prevActiveCells,
      self.predictedSegmentDecrement)


  def createSegment(self, cell):
    """
    Create a :class:`~nupic.algorithms.connections.Segment` on the specified 
    cell. This method calls 
    :meth:`~nupic.algorithms.connections.Connections.createSegment` on the 
    underlying :class:`~nupic.algorithms.connections.Connections`, and it does 
    some extra bookkeeping. Unit tests should call this method, and not 
    :meth:`~nupic.algorithms.connections.Connections.createSegment`.

    :param cell: (int) Index of cell to create a segment on.

    :returns: (:class:`~nupic.algorithms.connections.Segment`) The created 
              segment.
    """
    return self._createSegment(
      self.connections, self.lastUsedIterationForSegment, cell, self.iteration,
      self.maxSegmentsPerCell)


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
                               maxNewSynapseCount, initialPermanence,
                               permanenceIncrement, permanenceDecrement,
                               maxSynapsesPerSegment, learn):
    """
    :param connections: (Object)
    Connections for the TM. Gets mutated.

    :param random: (Object)
    Random number generator. Gets mutated.

    :param columnActiveSegments: (iter)
    Active segments in this column.

    :param prevActiveCells: (list)
    Active cells in `t-1`.

    :param prevWinnerCells: (list)
    Winner cells in `t-1`.

    :param numActivePotentialSynapsesForSegment: (list)
    Number of active potential synapses per segment, indexed by the segment's
    flatIdx.

    :param maxNewSynapseCount: (int)
    The maximum number of synapses added to a segment during learning

    :param initialPermanence: (float)
    Initial permanence of a new synapse.

    @permanenceIncrement (float)
    Amount by which permanences of synapses are incremented during learning.

    @permanenceDecrement (float)
    Amount by which permanences of synapses are decremented during learning.

    :param maxSynapsesPerSegment: (int)
    The maximum number of synapses per segment.

    :param learn: (bool)
    If true, grow and reinforce synapses.

    :returns: cellsToAdd (list)
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
                            prevWinnerCells, initialPermanence,
                            maxSynapsesPerSegment)

    return cellsToAdd


  @classmethod
  def _burstColumn(cls, connections, random, lastUsedIterationForSegment,
                   column, columnMatchingSegments, prevActiveCells,
                   prevWinnerCells, cellsForColumn,
                   numActivePotentialSynapsesForSegment, iteration,
                   maxNewSynapseCount, initialPermanence, permanenceIncrement,
                   permanenceDecrement, maxSegmentsPerCell,
                   maxSynapsesPerSegment, learn):
    """
    :param connections: (Object)
    Connections for the TM. Gets mutated.

    :param random: (Object)
    Random number generator. Gets mutated.

    :param lastUsedIterationForSegment: (list)
    Last used iteration for each segment, indexed by the segment's flatIdx.
    Gets mutated.

    :param column: (int)
    Index of bursting column.

    :param columnMatchingSegments: (iter)
    Matching segments in this column.

    :param prevActiveCells: (list)
    Active cells in `t-1`.

    :param prevWinnerCells: (list)
    Winner cells in `t-1`.

    :param cellsForColumn: (sequence)
    Range of cell indices on which to operate.

    :param numActivePotentialSynapsesForSegment: (list)
    Number of active potential synapses per segment, indexed by the segment's
    flatIdx.

    :param iteration: (int)
    The current timestep.

    :param maxNewSynapseCount: (int)
    The maximum number of synapses added to a segment during learning.

    :param initialPermanence: (float)
    Initial permanence of a new synapse.

    :param permanenceIncrement: (float)
    Amount by which permanences of synapses are incremented during learning.

    :param permanenceDecrement: (float)
    Amount by which permanences of synapses are decremented during learning.

    :param maxSegmentsPerCell: (int)
    The maximum number of segments per cell.

    :param maxSynapsesPerSegment: (int)
    The maximum number of synapses per segment.

    :param learn: (bool)
    Whether or not learning is enabled.

    :returns: (tuple) Contains:
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
                            nGrowDesired, prevWinnerCells, initialPermanence,
                            maxSynapsesPerSegment)
    else:
      winnerCell = cls._leastUsedCell(random, cellsForColumn, connections)
      if learn:
        nGrowExact = min(maxNewSynapseCount, len(prevWinnerCells))
        if nGrowExact > 0:
          segment = cls._createSegment(connections,
                                       lastUsedIterationForSegment, winnerCell,
                                       iteration, maxSegmentsPerCell)
          cls._growSynapses(connections, random, segment, nGrowExact,
                            prevWinnerCells, initialPermanence,
                            maxSynapsesPerSegment)

    return cellsForColumn, winnerCell


  @classmethod
  def _punishPredictedColumn(cls, connections, columnMatchingSegments,
                             prevActiveCells, predictedSegmentDecrement):
    """
    :param connections: (Object)
    Connections for the TM. Gets mutated.

    :param columnMatchingSegments: (iter)
    Matching segments for this column.

    :param prevActiveCells: (list)
    Active cells in `t-1`.

    :param predictedSegmentDecrement: (float)
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
  def _createSegment(cls, connections, lastUsedIterationForSegment, cell,
                     iteration, maxSegmentsPerCell):
    """
    Create a segment on the connections, enforcing the maxSegmentsPerCell
    parameter.
    """
    # Enforce maxSegmentsPerCell.
    while connections.numSegments(cell) >= maxSegmentsPerCell:
      leastRecentlyUsedSegment = min(
        connections.segmentsForCell(cell),
        key=lambda segment : lastUsedIterationForSegment[segment.flatIdx])

      connections.destroySegment(leastRecentlyUsedSegment)

    # Create the segment.
    segment = connections.createSegment(cell)

    # Do TM-specific bookkeeping for the segment.
    if segment.flatIdx == len(lastUsedIterationForSegment):
      lastUsedIterationForSegment.append(iteration)
    elif segment.flatIdx < len(lastUsedIterationForSegment):
      # A flatIdx was recycled.
      lastUsedIterationForSegment[segment.flatIdx] = iteration
    else:
      raise AssertionError(
        "All segments should be created with the TM createSegment method.")

    return segment


  @classmethod
  def _destroyMinPermanenceSynapses(cls, connections, random, segment,
                                    nDestroy, excludeCells):
    """
    Destroy nDestroy synapses on the specified segment, but don't destroy
    synapses to the "excludeCells".
    """

    destroyCandidates = sorted(
      (synapse for synapse in connections.synapsesForSegment(segment)
       if synapse.presynapticCell not in excludeCells),
      key=lambda s: s._ordinal
    )

    for _ in xrange(nDestroy):
      if len(destroyCandidates) == 0:
        break

      minSynapse = None
      minPermanence = float("inf")

      for synapse in destroyCandidates:
        if synapse.permanence < minPermanence - EPSILON:
          minSynapse = synapse
          minPermanence = synapse.permanence

      connections.destroySynapse(minSynapse)
      destroyCandidates.remove(minSynapse)


  @classmethod
  def _leastUsedCell(cls, random, cells, connections):
    """
    Gets the cell with the smallest number of segments.
    Break ties randomly.

    :param random: (Object)
    Random number generator. Gets mutated.

    :param cells: (list)
    Indices of cells.

    :param connections: (Object)
    Connections instance for the TM.

    :returns: (int) Cell index.
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
                    prevWinnerCells, initialPermanence, maxSynapsesPerSegment):
    """
    Creates nDesiredNewSynapes synapses on the segment passed in if
    possible, choosing random cells from the previous winner cells that are
    not already on the segment.

    :param connections:        (Object) Connections instance for the tm
    :param random:             (Object) TM object used to generate random
                                        numbers
    :param segment:            (int)    Segment to grow synapses on.
    :param nDesiredNewSynapes: (int)    Desired number of synapses to grow
    :param prevWinnerCells:    (list)   Winner cells in `t-1`
    :param initialPermanence:  (float)  Initial permanence of a new synapse.

    """
    candidates = list(prevWinnerCells)

    for synapse in connections.synapsesForSegment(segment):
      i = binSearch(candidates, synapse.presynapticCell)
      if i != -1:
        del candidates[i]

    nActual = min(nDesiredNewSynapes, len(candidates))

    # Check if we're going to surpass the maximum number of synapses.
    overrun = connections.numSynapses(segment) + nActual - maxSynapsesPerSegment
    if overrun > 0:
      cls._destroyMinPermanenceSynapses(connections, random, segment, overrun,
                                        prevWinnerCells)

    # Recalculate in case we weren't able to destroy as many synapses as needed.
    nActual = min(nActual,
                  maxSynapsesPerSegment - connections.numSynapses(segment))

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

    :param connections:          (Object) Connections instance for the tm
    :param segment:              (int)    Segment to adapt
    :param prevActiveCells:      (list)   Active cells in `t-1`
    :param permanenceIncrement:  (float)  Amount to increment active synapses
    :param permanenceDecrement:  (float)  Amount to decrement inactive synapses
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

    :param cell: (int) Cell index

    :returns: (int) Column index
    """
    self._validateCell(cell)

    return int(cell / self.cellsPerColumn)


  def cellsForColumn(self, column):
    """
    Returns the indices of cells that belong to a column.

    :param column: (int) Column index

    :returns: (list) Cell indices
    """
    self._validateColumn(column)

    start = self.cellsPerColumn * column
    end = start + self.cellsPerColumn
    return range(start, end)


  def numberOfColumns(self):
    """
    Returns the number of columns in this layer.

    :returns: (int) Number of columns
    """
    return reduce(mul, self.columnDimensions, 1)


  def numberOfCells(self):
    """
    Returns the number of cells in this layer.

    :returns: (int) Number of cells
    """
    return self.numberOfColumns() * self.cellsPerColumn


  def mapCellsToColumns(self, cells):
    """
    Maps cells to the columns they belong to.

    :param cells: (set) Cells

    :returns: (dict) Mapping from columns to their cells in `cells`
    """
    cellsForColumns = defaultdict(set)

    for cell in cells:
      column = self.columnForCell(cell)
      cellsForColumns[column].add(cell)

    return cellsForColumns


  def getActiveCells(self):
    """
    Returns the indices of the active cells.

    :returns: (list) Indices of active cells.
    """
    return self.getCellIndices(self.activeCells)


  def getPredictiveCells(self):
    """ Returns the indices of the predictive cells.

    :returns: (list) Indices of predictive cells.
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

    :returns: (list) Indices of winner cells.
    """
    return self.getCellIndices(self.winnerCells)


  def getActiveSegments(self):
    """
    Returns the active segments.

    :returns: (list) Active segments
    """
    return self.activeSegments


  def getMatchingSegments(self):
    """
    Returns the matching segments.

    :returns: (list) Matching segments
    """
    return self.matchingSegments


  def getCellsPerColumn(self):
    """
    Returns the number of cells per column.

    :returns: (int) The number of cells per column.
    """
    return self.cellsPerColumn


  def getColumnDimensions(self):
    """
    Returns the dimensions of the columns in the region.

    :returns: (tuple) Column dimensions
    """
    return self.columnDimensions


  def getActivationThreshold(self):
    """
    Returns the activation threshold.

    :returns: (int) The activation threshold.
    """
    return self.activationThreshold


  def setActivationThreshold(self, activationThreshold):
    """
    Sets the activation threshold.
    
    :param activationThreshold: (int) activation threshold.
    """
    self.activationThreshold = activationThreshold


  def getInitialPermanence(self):
    """
    Get the initial permanence.
    
    :returns: (float) The initial permanence.
    """
    return self.initialPermanence


  def setInitialPermanence(self, initialPermanence):
    """
    Sets the initial permanence.
    
    :param initialPermanence: (float) The initial permanence.
    """
    self.initialPermanence = initialPermanence


  def getMinThreshold(self):
    """
    Returns the min threshold.
    
    :returns: (int) The min threshold.
    """
    return self.minThreshold


  def setMinThreshold(self, minThreshold):
    """
    Sets the min threshold.
    
    :param minThreshold: (int) min threshold.
    """
    self.minThreshold = minThreshold


  def getMaxNewSynapseCount(self):
    """
    Returns the max new synapse count.
    
    :returns: (int) The max new synapse count.
    """
    return self.maxNewSynapseCount


  def setMaxNewSynapseCount(self, maxNewSynapseCount):
    """
    Sets the max new synapse count.
    
    :param maxNewSynapseCount: (int) Max new synapse count.
    """
    self.maxNewSynapseCount = maxNewSynapseCount


  def getPermanenceIncrement(self):
    """
    Get the permanence increment.
    
    :returns: (float) The permanence increment.
    """
    return self.permanenceIncrement


  def setPermanenceIncrement(self, permanenceIncrement):
    """
    Sets the permanence increment.
    
    :param permanenceIncrement: (float) The permanence increment.
    """
    self.permanenceIncrement = permanenceIncrement


  def getPermanenceDecrement(self):
    """
    Get the permanence decrement.
    
    :returns: (float) The permanence decrement.
    """
    return self.permanenceDecrement


  def setPermanenceDecrement(self, permanenceDecrement):
    """
    Sets the permanence decrement.
    
    :param permanenceDecrement: (float) The permanence decrement.
    """
    self.permanenceDecrement = permanenceDecrement


  def getPredictedSegmentDecrement(self):
    """
    Get the predicted segment decrement.
    
    :returns: (float) The predicted segment decrement.
    """
    return self.predictedSegmentDecrement


  def setPredictedSegmentDecrement(self, predictedSegmentDecrement):
    """
    Sets the predicted segment decrement.
    
    :param predictedSegmentDecrement: (float) The predicted segment decrement.
    """
    self.predictedSegmentDecrement = predictedSegmentDecrement


  def getConnectedPermanence(self):
    """
    Get the connected permanence.
    
    :returns: (float) The connected permanence.
    """
    return self.connectedPermanence


  def setConnectedPermanence(self, connectedPermanence):
    """
    Sets the connected permanence.
    
    :param connectedPermanence: (float) The connected permanence.
    """
    self.connectedPermanence = connectedPermanence


  def getMaxSegmentsPerCell(self):
      """
      Get the maximum number of segments per cell
      
      :returns: (int) max number of segments per cell
      """
      return self.maxSegmentsPerCell


  def getMaxSynapsesPerSegment(self):
      """
      Get the maximum number of synapses per segment.
      
      :returns: (int) max number of synapses per segment
      """
      return self.maxSynapsesPerSegment


  def write(self, proto):
    """
    Writes serialized data to proto object.

    :param proto: (DynamicStructBuilder) Proto object
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

    proto.maxSegmentsPerCell = self.maxSegmentsPerCell
    proto.maxSynapsesPerSegment = self.maxSynapsesPerSegment

    self.connections.write(proto.connections)
    self._random.write(proto.random)

    proto.activeCells = list(self.activeCells)
    proto.winnerCells = list(self.winnerCells)

    protoActiveSegments = proto.init("activeSegments", len(self.activeSegments))
    for i, segment in enumerate(self.activeSegments):
      protoActiveSegments[i].cell = segment.cell
      idx = self.connections.segmentsForCell(segment.cell).index(segment)
      protoActiveSegments[i].idxOnCell = idx

    protoMatchingSegments = proto.init("matchingSegments",
                                       len(self.matchingSegments))
    for i, segment in enumerate(self.matchingSegments):
      protoMatchingSegments[i].cell = segment.cell
      idx = self.connections.segmentsForCell(segment.cell).index(segment)
      protoMatchingSegments[i].idxOnCell = idx

    protoNumActivePotential = proto.init(
      "numActivePotentialSynapsesForSegment",
      len(self.numActivePotentialSynapsesForSegment))
    for i, numActivePotentialSynapses in enumerate(
        self.numActivePotentialSynapsesForSegment):
      segment = self.connections.segmentForFlatIdx(i)
      if segment is not None:
        protoNumActivePotential[i].cell = segment.cell
        idx = self.connections.segmentsForCell(segment.cell).index(segment)
        protoNumActivePotential[i].idxOnCell = idx
        protoNumActivePotential[i].number = numActivePotentialSynapses

    proto.iteration = self.iteration

    protoLastUsedIteration = proto.init(
      "lastUsedIterationForSegment",
      len(self.numActivePotentialSynapsesForSegment))
    for i, lastUsed in enumerate(self.lastUsedIterationForSegment):
      segment = self.connections.segmentForFlatIdx(i)
      if segment is not None:
        protoLastUsedIteration[i].cell = segment.cell
        idx = self.connections.segmentsForCell(segment.cell).index(segment)
        protoLastUsedIteration[i].idxOnCell = idx
        protoLastUsedIteration[i].number = lastUsed


  @classmethod
  def read(cls, proto):
    """
    Reads deserialized data from proto object.

    :param proto: (DynamicStructBuilder) Proto object

    :returns: (:class:TemporalMemory) TemporalMemory instance
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

    tm.maxSegmentsPerCell = int(proto.maxSegmentsPerCell)
    tm.maxSynapsesPerSegment = int(proto.maxSynapsesPerSegment)

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
    tm.lastUsedIterationForSegment = [0] * flatListLength

    tm.activeSegments = []
    tm.matchingSegments = []

    for protoSegment in proto.activeSegments:
      tm.activeSegments.append(
        tm.connections.getSegment(protoSegment.cell,
                                  protoSegment.idxOnCell))

    for protoSegment in proto.matchingSegments:
      tm.matchingSegments.append(
        tm.connections.getSegment(protoSegment.cell,
                                  protoSegment.idxOnCell))

    for protoSegment in proto.numActivePotentialSynapsesForSegment:
      segment = tm.connections.getSegment(protoSegment.cell,
                                          protoSegment.idxOnCell)

      tm.numActivePotentialSynapsesForSegment[segment.flatIdx] = (
        int(protoSegment.number))

    tm.iteration = long(proto.iteration)

    for protoSegment in proto.lastUsedIterationForSegment:
      segment = tm.connections.getSegment(protoSegment.cell,
                                          protoSegment.idxOnCell)

      tm.lastUsedIterationForSegment[segment.flatIdx] = (
        long(protoSegment.number))

    return tm


  def __eq__(self, other):
    """
    Non-equality operator for TemporalMemory instances.
    Checks if two instances are functionally identical
    (might have different internal state).

    :param other: (TemporalMemory) TemporalMemory instance to compare to
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

    :param other: (TemporalMemory) TemporalMemory instance to compare to
    """
    return not self.__eq__(other)


  def _validateColumn(self, column):
    """
    Raises an error if column index is invalid.

    :param column: (int) Column index
    """
    if column >= self.numberOfColumns() or column < 0:
      raise IndexError("Invalid column")


  def _validateCell(self, cell):
    """
    Raises an error if cell index is invalid.

    :param cell: (int) Cell index
    """
    if cell >= self.numberOfCells() or cell < 0:
      raise IndexError("Invalid cell")


  @classmethod
  def getCellIndices(cls, cells):
    """
    Returns the indices of the cells passed in.

    :param cells: (list) cells to find the indices of
    """
    return [cls.getCellIndex(c) for c in cells]


  @staticmethod
  def getCellIndex(cell):
    """
    Returns the index of the cell.

    :param cell: (int) cell to find the index of
    """
    return cell
