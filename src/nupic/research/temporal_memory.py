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
from nupic.research.connections import Connections, SegmentOverlap, binSearch
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
    @param columnDimensions          (list)  Dimensions of the column space
    @param cellsPerColumn            (int)   Number of cells per column
    @param activationThreshold       (int)   If the number of active connected
                                             synapses on a segment is at least
                                             this threshold, the segment is said
                                             to be active.
    @param initialPermanence         (float) Initial permanence of a new synapse
    @param connectedPermanence       (float) If the permanence value for a
                                             synapse is greater than this value,
                                             it is said to be connected.
    @param minThreshold              (int)   If the number of synapses active on
                                             a segment is at least this
                                             threshold, it is selected as the
                                             best matching cell in a bursting
                                             column
    @param maxNewSynapseCount        (int)   The maximum number of synapses
                                             added to a segment during learning
    @param permanenceIncrement       (float) Amount by which permanences of
                                             synapses are incremented during
                                             learning.
    @param permanenceDecrement       (float) Amount by which permanences of
                                             synapses are decremented during
                                             learning.
    @param predictedSegmentDecrement (float) Amount by which active permanences
                                             of synapses of previously predicted
                                             but inactive segments are
                                             decremented.
    @param seed                      (int)   Seed for the random number
                                             generator
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
    self.connections = Connections(self.numberOfCells(),
                                   maxSegmentsPerCell=maxSegmentsPerCell,
                                   maxSynapsesPerSegment=maxSynapsesPerSegment)
    self._random = Random(seed)

    self.activeCells = []
    self.winnerCells = []
    self.activeSegments = []
    self.matchingSegments = []

  # ==============================
  # Main functions
  # ==============================

  def compute(self, activeColumns, learn=True):
    """ Feeds input record through TM, performing inference and learning.

    @param activeColumns (set)  Indices of active columns
    @param learn         (bool) Whether or not learning is enabled
    """
    self.activateCells(sorted(activeColumns), learn)
    self.activateDendrites(learn)


  def activateCells(self, activeColumns, learn=True):
    """ Calculate the active cells, using the current active columns and
    dendrite segments. Grow and reinforce synapses.

    @param activeColumns (list) A sorted list of active column indices.
    @param learn (bool) If true, reinforce / punish / grow synapses.

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

    segToCol = lambda segment: int(segment.segment.cell / self.cellsPerColumn)
    identity = lambda x: x

    for columnData in groupby2(activeColumns, identity,
                               self.activeSegments, segToCol,
                               self.matchingSegments, segToCol):
      (column,
       activeColumns,
       activeSegmentsOnCol,
       matchingSegmentsOnCol) = columnData
      if activeColumns is not None:
        if activeSegmentsOnCol is not None:
          cellsToAdd = self.activatePredictedColumn(
            self.connections,
            self._random,
            activeSegmentsOnCol,
            matchingSegmentsOnCol,
            prevActiveCells,
            prevWinnerCells,
            self.maxNewSynapseCount,
            self.initialPermanence,
            self.permanenceIncrement,
            self.permanenceDecrement,
            learn)

          self.activeCells += cellsToAdd
          self.winnerCells += cellsToAdd
        else:
          (cellsToAdd,
           winnerCell) = self.burstColumn(self.connections,
                                          self._random,
                                          column,
                                          matchingSegmentsOnCol,
                                          prevActiveCells,
                                          prevWinnerCells,
                                          self.cellsPerColumn,
                                          self.maxNewSynapseCount,
                                          self.initialPermanence,
                                          self.permanenceIncrement,
                                          self.permanenceDecrement,
                                          learn)

          self.activeCells += cellsToAdd
          self.winnerCells.append(winnerCell)
      else:
        if learn:
          self.punishPredictedColumn(self.connections,
                                     matchingSegmentsOnCol,
                                     self.predictedSegmentDecrement,
                                     prevActiveCells)


  def activateDendrites(self, learn=True):
    """ Calculate dendrite segment activity, using the current active cells.

    @param learn (bool)
    If true, segment activations will be recorded. This information is used
    during segment cleanup.

    Pseudocode:
    for each distal dendrite segment with activity >= activationThreshold
      mark the segment as active
    for each distal dendrite segment with unconnected activity >= minThreshold
      mark the segment as matching
    """
    (activeSegments,
     matchingSegments) = self.connections.computeActivity(
       self.activeCells,
       self.connectedPermanence,
       self.activationThreshold,
       0.0,
       self.minThreshold,
       learn)

    self.activeSegments = activeSegments
    self.matchingSegments = matchingSegments


  def reset(self):
    """ Indicates the start of a new sequence and resets the sequence
        state of the TM. """
    self.activeCells = []
    self.winnerCells = []
    self.activeSegments = []
    self.matchingSegments = []


  @classmethod
  def activatePredictedColumn(cls, connections, random, activeSegments,
                              matchingSegments, prevActiveCells,
                              prevWinnerCells, maxNewSynapseCount,
                              initialPermanence, permanenceIncrement,
                              permanenceDecrement, learn):
    """ Determines which cells in a predicted column should be added to winner
    cells list, and learns on the segments that correctly predicted this column.

    @param connections     (Object) Connections for the TM. Gets mutated.
    @param random          (Object) Random number generator. Gets mutated.
    @param activeSegments  (iter)   An iterable of SegmentOverlap objects.
                                    Active segments for this column, and
                                    an overlap for each segment.
    @param matchingSegments (iter)  An iterable of SegmentOverlap objects.
                                    Matching segments for this column, and
                                    an overlap for each segment.
    @param prevActiveCells (list)   Active cells in `t-1`.
    @param prevWinnerCells     (list)   Winner cells in `t-1`.
    @param maxNewSynapseCount  (int)    The maximum number of synapses added to
                                        a segment during learning.
    @param initialPermanence   (float)  Initial permanence of a new synapse.
    @permanenceIncrement   (float)  Amount by which permanences of synapses are
                                    incremented during learning.
    @permanenceDecrement   (float)  Amount by which permanences of synapses are
                                    decremented during learning.
    @param learn           (bool)   Determines if permanences are adjusted.

    @return cellsToAdd (list) A list of predicted cells that will be added to
                              active cells and winner cells.

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

    byCell = lambda x: x.segment.cell
    for cellData in groupby2(activeSegments, byCell,
                             matchingSegments, byCell):
      (cell,
       activeSegmentsOnCell,
       matchingSegmentsOnCell) = cellData

      if activeSegmentsOnCell is not None:
        cellsToAdd.append(cell)

        if learn:
          # Learn on every active segment.
          #
          # For each active segment, get its corresponding matching
          # segment so that we can use its overlap to compute the
          # number of synapses to grow.
          bySegment = lambda x: x.segment
          for segmentData in groupby2(activeSegmentsOnCell, bySegment,
                                      matchingSegmentsOnCell, bySegment):
            (segment,
             activeOverlaps,
             matchingOverlaps) = segmentData

            if activeOverlaps is not None:
              # Active segments are a superset of matching segments,
              # so this iterator must contain a segment (and overlap).
              matching = matchingOverlaps.next()

              cls.adaptSegment(connections, segment, prevActiveCells,
                               permanenceIncrement, permanenceDecrement)

              nGrowDesired = maxNewSynapseCount - matching.overlap
              if nGrowDesired > 0:
                cls.growSynapses(connections, random, segment, nGrowDesired,
                                 prevWinnerCells, initialPermanence)

    return cellsToAdd


  @classmethod
  def burstColumn(cls, connections, random, column, matchingSegments,
                  prevActiveCells, prevWinnerCells, cellsPerColumn,
                  maxNewSynapseCount, initialPermanence, permanenceIncrement,
                  permanenceDecrement, learn):
    """ Activates all of the cells in an unpredicted active column, chooses a
    winner cell, and, if learning is turned on, learns on one segment, growing a
    new segment if necessary.

    @param connections         (Object) Connections for the TM. Gets mutated.
    @param random              (Object) Random number generator. Gets mutated.
    @param column              (int)    Index of bursting column.
    @param matchingSegments    (iter)   An iterable of SegmentOverlap objects.
                                        Matching segments for this column, and
                                        an overlap for each segment.
    @param prevActiveCells     (list)   Active cells in `t-1`.
    @param prevWinnerCells     (list)   Winner cells in `t-1`.
    @param cellsPerColumn      (int)    Number of cells per column.
    @param maxNewSynapseCount  (int)    The maximum number of synapses added to
                                        a segment during learning.
    @param initialPermanence   (float)  Initial permanence of a new synapse.
    @param permanenceIncrement (float)  Amount by which permanences of synapses
                                        are incremented during learning.
    @param permanenceDecrement (float)  Amount by which permanences of synapses
                                        are decremented during learning.
    @param learn               (bool)   Whether or not learning is enabled.

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
    start = cellsPerColumn * column
    cells = xrange(start, start + cellsPerColumn)

    if matchingSegments is not None:
      bestMatching = max(matchingSegments, key=lambda seg: seg.overlap)
      winnerCell = bestMatching.segment.cell

      if learn:
        cls.adaptSegment(connections, bestMatching.segment, prevActiveCells,
                         permanenceIncrement, permanenceDecrement)

        nGrowDesired = maxNewSynapseCount - bestMatching.overlap

        if nGrowDesired > 0:
          cls.growSynapses(connections, random, bestMatching.segment,
                           nGrowDesired, prevWinnerCells, initialPermanence)
    else:
      winnerCell = cls.leastUsedCell(cells, connections, random)
      if learn:
        nGrowExact = min(maxNewSynapseCount, len(prevWinnerCells))
        if nGrowExact > 0:
          segment = connections.createSegment(winnerCell)
          cls.growSynapses(connections, random, segment, nGrowExact,
                           prevWinnerCells, initialPermanence)

    return cells, winnerCell


  @classmethod
  def punishPredictedColumn(cls, connections, matchingSegments,
                            predictedSegmentDecrement, prevActiveCells):
    """Punishes the Segments that incorrectly predicted a column to be active.

    @param connections         (Object) Connections for the TM. Gets mutated.
    @param matchingSegments    (iter)   An iterable of SegmentOverlap objects.
                                        Matching segments for this column, and
                                        an overlap for each segment.
    @param permanenceDecrement (float)  Amount by which permanences of synapses
                                        are decremented during learning.
    @param prevActiveCells     (list)   Active cells in `t-1`

    Pseudocode:
    for each matching segment in the column
      weaken active synapses
    """
    if predictedSegmentDecrement > 0.0 and matchingSegments is not None:
      for matching in matchingSegments:
        cls.adaptSegment(connections, matching.segment, prevActiveCells,
                         -predictedSegmentDecrement, 0.0)

  # ==============================
  # Helper functions
  # ==============================


  @staticmethod
  def leastUsedCell(cells, connections, random):
    """ Gets the cell with the smallest number of segments.
    Break ties randomly.

    @param cells       (list)   Indices of cells
    @param connections (Object) Connections instance for the tm
    @param random      (Object) Random number generator

    @return (int) Cell index
    """
    leastUsedCells = []
    minNumSegments = float("inf")
    for cell in cells:
      numSegments = len(connections.segmentsForCell(cell))

      if numSegments < minNumSegments:
        minNumSegments = numSegments
        leastUsedCells = []

      if numSegments == minNumSegments:
        leastUsedCells.append(cell)

    i = random.getUInt32(len(leastUsedCells))
    return leastUsedCells[i]


  @staticmethod
  def growSynapses(connections, random, segment, nDesiredNewSynapes,
                   prevWinnerCells, initialPermanence):
    """ Creates nDesiredNewSynapes synapses on the segment passed in if
    possible, choosing random cells from the previous winner cells that are
    not already on the segment.

    @param  connections        (Object) Connections instance for the tm
    @param  random             (Object) Tm object used to generate random
                                        numbers
    @param  segment            (int)    Segment to grow synapses on.
    @params nDesiredNewSynapes (int)    Desired number of synapses to grow
    @params prevWinnerCells    (list)   Winner cells in `t-1`
    @param  initialPermanence  (float)  Initial permanence of a new synapse.

    Notes: The process of writing the last value into the index in the array
    that was most recently changed is to ensure the same results that we get
    in the c++ implentation using iter_swap with vectors.
    """
    candidates = list(prevWinnerCells)
    eligibleEnd = len(candidates) - 1

    for synapse in connections.synapsesForSegment(segment):
      presynapticCell = connections.dataForSynapse(synapse).presynapticCell
      try:
        index = candidates[:eligibleEnd + 1].index(presynapticCell)
      except ValueError:
        index = -1
      if index != -1:
        candidates[index] = candidates[eligibleEnd]
        eligibleEnd -= 1

    candidatesLength = eligibleEnd + 1
    nActual = min(nDesiredNewSynapes, candidatesLength)

    for _ in range(nActual):
      rand = random.getUInt32(candidatesLength)
      connections.createSynapse(segment, candidates[rand],
                                initialPermanence)
      candidates[rand] = candidates[candidatesLength - 1]
      candidatesLength -= 1


  @staticmethod
  def adaptSegment(connections, segment, prevActiveCells, permanenceIncrement,
                   permanenceDecrement):
    """ Updates synapses on segment.
    Strengthens active synapses; weakens inactive synapses.

    @param connections          (Object) Connections instance for the tm
    @param segment              (int)    Segment to adapt
    @param prevActiveCells      (list)   Active cells in `t-1`
    @param permanenceIncrement  (float)  Amount to increment active synapses
    @param permanenceDecrement  (float)  Amount to decrement inactive synapses
    """

    for synapse in connections.synapsesForSegment(segment):
      synapseData = connections.dataForSynapse(synapse)
      permanence = synapseData.permanence

      if binSearch(prevActiveCells, synapseData.presynapticCell) != -1:
        permanence += permanenceIncrement
      else:
        permanence -= permanenceDecrement

      # Keep permanence within min/max bounds
      permanence = max(0.0, min(1.0, permanence))

      if permanence < EPSILON:
        connections.destroySynapse(synapse)
      else:
        connections.updateSynapsePermanence(synapse, permanence)

    if connections.numSynapses(segment) == 0:
      connections.destroySegment(segment)


  def columnForCell(self, cell):
    """ Returns the index of the column that a cell belongs to.

    @param cell (int) Cell index

    @return (int) Column index
    """
    self._validateCell(cell)

    return int(cell / self.cellsPerColumn)


  def cellsForColumn(self, column):
    """ Returns the indices of cells that belong to a column.

    @param column (int) Column index

    @return (list) Cell indices
    """
    self._validateColumn(column)

    start = self.cellsPerColumn * column
    end = start + self.cellsPerColumn
    return range(start, end)


  def numberOfColumns(self):
    """ Returns the number of columns in this layer.

    @return (int) Number of columns
    """
    return reduce(mul, self.columnDimensions, 1)


  def numberOfCells(self):
    """ Returns the number of cells in this layer.

    @return (int) Number of cells
    """
    return self.numberOfColumns() * self.cellsPerColumn


  def mapCellsToColumns(self, cells):
    """ Maps cells to the columns they belong to

    @param cells (set) Cells

    @return (dict) Mapping from columns to their cells in `cells`
    """
    cellsForColumns = defaultdict(set)

    for cell in cells:
      column = self.columnForCell(cell)
      cellsForColumns[column].add(cell)

    return cellsForColumns


  def getActiveCells(self):
    """ Returns the indices of the active cells.

    @return (list) Indices of active cells.
    """
    return self.getCellIndices(self.activeCells)


  def getPredictiveCells(self):
    """ Returns the indices of the predictive cells.

    @return (list) Indices of predictive cells.
    """
    predictiveCells = set()
    for activeSegment in self.activeSegments:
      cell = activeSegment.segment.cell
      if not cell in predictiveCells:
        predictiveCells.add(cell)

    return sorted(predictiveCells)


  def getWinnerCells(self):
    """ Returns the indices of the winner cells.

    @return (list) Indices of winner cells.
    """
    return self.getCellIndices(self.winnerCells)


  def getCellsPerColumn(self):
    """ Returns the number of cells per column.

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


  def write(self, proto):
    """ Writes serialized data to proto object

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
    for i, active in enumerate(self.activeSegments):
      activeSegmentOverlaps[i].cell = active.segment.cell
      activeSegmentOverlaps[i].segment = active.segment.idx
      activeSegmentOverlaps[i].overlap = active.overlap

    matchingSegmentOverlaps = \
        proto.init('matchingSegmentOverlaps', len(self.matchingSegments))
    for i, matching in enumerate(self.matchingSegments):
      matchingSegmentOverlaps[i].cell = matching.segment.cell
      matchingSegmentOverlaps[i].segment = matching.segment.idx
      matchingSegmentOverlaps[i].overlap = matching.overlap



  @classmethod
  def read(cls, proto):
    """ Reads deserialized data from proto object

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

    tm.activeSegments = []
    tm.matchingSegments = []

    for i in xrange(len(proto.activeSegmentOverlaps)):
      protoSegmentOverlap = proto.activeSegmentOverlaps[i]
      segment = tm.connections.getSegment(protoSegmentOverlap.segment,
                                          protoSegmentOverlap.cell)
      segmentOverlap = SegmentOverlap(segment, protoSegmentOverlap.overlap)
      tm.activeSegments.append(segmentOverlap)

    for i in xrange(len(proto.matchingSegmentOverlaps)):
      protoSegmentOverlap = proto.matchingSegmentOverlaps[i]
      segment = tm.connections.getSegment(protoSegmentOverlap.segment,
                                          protoSegmentOverlap.cell)
      segmentOverlap = SegmentOverlap(segment, protoSegmentOverlap.overlap)
      tm.matchingSegments.append(segmentOverlap)

    return tm


  def __eq__(self, other):
    """ Equality operator for TemporalMemory instances.
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
    """ Non-equality operator for TemporalMemory instances.
    Checks if two instances are not functionally identical
    (might have different internal state).

    @param other (TemporalMemory) TemporalMemory instance to compare to
    """
    return not self.__eq__(other)


  def _validateColumn(self, column):
    """ Raises an error if column index is invalid.

    @param column (int) Column index
    """
    if column >= self.numberOfColumns() or column < 0:
      raise IndexError("Invalid column")


  def _validateCell(self, cell):
    """ Raises an error if cell index is invalid.

    @param cell (int) Cell index
    """
    if cell >= self.numberOfCells() or cell < 0:
      raise IndexError("Invalid cell")


  @classmethod
  def getCellIndices(cls, cells):
    """ Returns the indices of the cells passed in.

    @param cells (list) cells to find the indices of
    """
    return [cls.getCellIndex(c) for c in cells]


  @staticmethod
  def getCellIndex(cell):
    """ Returns the index of the cell

    @param cell (int) cell to find the index of
    """
    return cell
