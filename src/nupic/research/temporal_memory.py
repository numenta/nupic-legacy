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
from nupic.research.connections import Connections

from sys import maxint as MAX_INT
from bisect import bisect_left

EPSILON = 0.000001



def binSearch(arr, val):
  """ function for running binary search on a sorted list.

  @param arr (list) a sorted list of integers to search
  @param val (int)  a integer to search for in the sorted array

  @return (int) the index of the element if it is found and -1 otherwise.

  """
  i = bisect_left(arr, val)
  if i != len(arr) and arr[i] == val:
    return i
  return -1



def excitedColumnsGenerator(activeColumns,
                            activeSegments,
                            matchingSegments,
                            cellsPerColumn,
                            connections):
  """ Generator used for iterating over the lists of active columns,
  active segments, and matching segments, each sorted by the column they
  correspond to.

  @param activeColumns    (list)   Sorted List of currently active columns
  @param activeSegments   (list)   Sorted list of segments active from lateral
                                   input
  @param matchingSegments (list)   Sorted list of segments matching from lateral
                                   input
  @param cellsPerColumn   (int)    Number of cells per column in the tm
  @param connections      (Object) Connections instance of the tm

  @return (dict){
                  `column`                 (int),
                  `isActiveColumn`         (bool),
                  `activeSegments`         (Generator),
                  `activeSegmentsCount`    (int),
                  `matchingSegments`       (Generator),
                  `matchingSegmentsCount`  (int)
                }

  Notes:
   The generators returned yield the segments associated with the column
   and the counts represent how many segments exist in the generator.
  """
  activeColumnsProcessed = 0
  activeSegmentsProcessed = 0
  matchingSegmentsProcessed = 0

  activeColumnsNum = len(activeColumns)
  activeSegmentsNum = len(activeSegments)
  matchingSegmentsNum = len(matchingSegments)

  isActiveColumn = None
  while (activeColumnsProcessed < activeColumnsNum or
         activeSegmentsProcessed < activeSegmentsNum or
         matchingSegmentsProcessed < matchingSegmentsNum):

    currentColumn = MAX_INT
    if activeSegmentsProcessed < activeSegmentsNum:
      currentColumn = min(currentColumn,
                          connections.columnForSegment(
                            activeSegments[activeSegmentsProcessed].segment,
                            cellsPerColumn))

    if matchingSegmentsProcessed < matchingSegmentsNum:
      currentColumn = min(currentColumn,
                          connections.columnForSegment(
                            matchingSegments[matchingSegmentsProcessed].segment,
                            cellsPerColumn))

    if (activeColumnsProcessed < activeColumnsNum and
        activeColumns[activeColumnsProcessed] <= currentColumn):
      currentColumn = activeColumns[activeColumnsProcessed]
      isActiveColumn = True
      activeColumnsProcessed += 1
    else:
      isActiveColumn = False

    activeSegmentsBegin = activeSegmentsProcessed
    activeSegmentsEnd = activeSegmentsProcessed
    for i in xrange(activeSegmentsProcessed, activeSegmentsNum):
      if connections.columnForSegment(activeSegments[i].segment,
                                      cellsPerColumn) == currentColumn:
        activeSegmentsProcessed += 1
        activeSegmentsEnd += 1
      else:
        break

    matchingSegmentsBegin = matchingSegmentsProcessed
    matchingSegmentsEnd = matchingSegmentsProcessed
    for i in xrange(matchingSegmentsProcessed, matchingSegmentsNum):
      if connections.columnForSegment(matchingSegments[i].segment,
                                      cellsPerColumn) == currentColumn:
        matchingSegmentsProcessed += 1
        matchingSegmentsEnd += 1
      else:
        break

    asIndexGenerator = xrange(activeSegmentsBegin, activeSegmentsEnd)
    msIndexGenerator = xrange(matchingSegmentsBegin, matchingSegmentsEnd)
    yield {"column": currentColumn,
           "isActiveColumn": isActiveColumn,
           "activeSegments": (activeSegments[i] for i in asIndexGenerator),
           "activeSegmentsCount": activeSegmentsEnd - activeSegmentsBegin,
           "matchingSegments": (matchingSegments[i] for i in msIndexGenerator),
           "matchingSegmentsCount": matchingSegmentsEnd - matchingSegmentsBegin
          }



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

    Updates member variables:
      - `activeCells`     (list)
      - `winnerCells`     (list)
      - `activeSegments`  (list)
      - `matchingSegments`(list)

    Pseudocode:
    for each column
      if column is active and has active distal dendrite segments
        call activatePredictedColumn
      if column is active and doesn't have active distal dendrite segments
        call burstColumn
      if column is inactive and has matching distal dendrite segments
        call punishPredictedColumn
    for each distal dendrite segment with activity >= activationThreshold
      mark the segment as active
    for each distal dendrite segment with unconnected activity >= minThreshold
      mark the segment as matching
    """
    prevActiveCells = self.activeCells
    prevWinnerCells = self.winnerCells

    activeColumns = sorted(activeColumns)

    self.activeCells = []
    self.winnerCells = []

    for excitedColumn in excitedColumnsGenerator(activeColumns,
                                                 self.activeSegments,
                                                 self.matchingSegments,
                                                 self.cellsPerColumn,
                                                 self.connections):
      if excitedColumn["isActiveColumn"]:
        if excitedColumn["activeSegmentsCount"] != 0:
          cellsToAdd = TemporalMemory.activatePredictedColumn(
            self.connections,
            excitedColumn,
            learn,
            self.permanenceDecrement,
            self.permanenceIncrement,
            prevActiveCells)

          self.activeCells += cellsToAdd
          self.winnerCells += cellsToAdd
        else:
          (cellsToAdd,
           winnerCell) = TemporalMemory.burstColumn(self.cellsPerColumn,
                                                    self.connections,
                                                    excitedColumn,
                                                    learn,
                                                    self.initialPermanence,
                                                    self.maxNewSynapseCount,
                                                    self.permanenceDecrement,
                                                    self.permanenceIncrement,
                                                    prevActiveCells,
                                                    prevWinnerCells,
                                                    self._random)

          self.activeCells += cellsToAdd
          self.winnerCells.append(winnerCell)
      else:
        if learn:
          TemporalMemory.punishPredictedColumn(self.connections, excitedColumn,
                                               self.predictedSegmentDecrement,
                                               prevActiveCells)

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


  @staticmethod
  def activatePredictedColumn(connections, excitedColumn, learn,
                              permanenceDecrement, permanenceIncrement,
                              prevActiveCells):
    """ Determines which cells in a predicted column should be added to
    winner cells list and calls adaptSegment on the segments that correctly
    predicted this column.

    @param connections     (Object) Connections instance for the tm
    @param excitedColumn   (dict)   Dict generated by excitedColumnsGenerator
    @param learn           (bool)   Determines if permanences are adjusted
    @permanenceDecrement   (float)  Amount by which permanences of synapses are
                                    decremented during learning.
    @permanenceIncrement   (float)  Amount by which permanences of synapses are
                                    incremented during learning.
    @param prevActiveCells (list)   Active cells in `t-1`

    @return cellsToAdd (list) A list of predicted cells that will be added to
                              active cells and winner cells.
                              
    Pseudocode:
    for each cell in the column that has an active distal dendrite segment
      mark the cell as active
      mark the cell as a winner cell
      (learning) for each active distal dendrite segment
        strengthen active synapses
        weaken inactive synapses
    """

    cellsToAdd = []
    cell = None
    for active in excitedColumn["activeSegments"]:
      newCell = cell != active.segment.cell
      if newCell:
        cell = active.segment.cell
        cellsToAdd.append(cell)

      if learn:
        TemporalMemory.adaptSegment(connections, prevActiveCells,
                                    permanenceIncrement, permanenceDecrement,
                                    active.segment)

    return cellsToAdd


  @staticmethod
  def burstColumn(cellsPerColumn, connections, excitedColumn,
                  learn, initialPermanence, maxNewSynapseCount,
                  permanenceDecrement, permanenceIncrement,
                  prevActiveCells, prevWinnerCells, random):
    """ Activates all of the cells in an unpredicted active column,
    chooses a winner cell, and, if learning is turned on, either adapts or
    creates a segment. growSynapses is invoked on this segment.

    @param cellsPerColumn      (int)    Number of cells per column
    @param connections         (Object) Connections instance for the tm
    @param excitedColumn       (dict)   Excited Column instance from
                                        excitedColumnsGenerator
    @param learn               (bool)   Whether or not learning is enabled
    @param initialPermanence   (float)  Initial permanence of a new synapse.
    @param maxNewSynapseCount  (int)    The maximum number of synapses added to
                                        a segment during learning
    @param permanenceDecrement (float)  Amount by which permanences of synapses
                                        are decremented during learning
    @param permanenceIncrement (float)  Amount by which permanences of synapses
                                        are incremented during learning
    @param prevActiveCells     (list)   Active cells in `t-1`
    @param prevWinnerCells     (list)   Winner cells in `t-1`
    @param random              (object) Random number generator

    @return (tuple) Contains:
                      `cells`         (list),
                      `bestCell`      (int),

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
    start = cellsPerColumn * excitedColumn["column"]
    cells = range(start, start + cellsPerColumn)

    if excitedColumn["matchingSegmentsCount"] != 0:
      bestSegment = TemporalMemory.bestMatchingSegment(connections,
                                                       excitedColumn,
                                                       prevActiveCells)
      bestCell = bestSegment.segment.cell
      if learn:
        TemporalMemory.adaptSegment(connections, prevActiveCells,
                                    permanenceIncrement, permanenceDecrement,
                                    bestSegment.segment)

        nGrowDesired = maxNewSynapseCount - bestSegment.overlap

        if nGrowDesired > 0:
          TemporalMemory.growSynapses(connections, initialPermanence,
                                      nGrowDesired, prevWinnerCells,
                                      random, bestSegment.segment)
    else:
      bestCell = TemporalMemory.leastUsedCell(cells, connections, random)
      if learn:
        nGrowExact = min(maxNewSynapseCount, len(prevWinnerCells))
        if nGrowExact > 0:
          bestSegment = connections.createSegment(bestCell)
          TemporalMemory.growSynapses(connections, initialPermanence,
                                      nGrowExact, prevWinnerCells,
                                      random, bestSegment)

    return cells, bestCell


  @staticmethod
  def punishPredictedColumn(connections, excitedColumn,
                            predictedSegmentDecrement, prevActiveCells):
    """Punishes the Segments that incorrectly predicted a column to be active.

    @param connections         (Object) Connections instance for the tm
    @param excitedColumn       (dict)   Excited Column instance from
                                        excitedColumnsGenerator
    @param permanenceDecrement (float)  Amount by which permanences of synapses
                                        are decremented during learning.
    @param prevActiveCells     (list)   Active cells in `t-1`

    Pseudocode:
    for each matching segment in the column
      weaken active synapses
    """
    if predictedSegmentDecrement > 0.0:
      for segment in excitedColumn["matchingSegments"]:
        TemporalMemory.adaptSegment(connections, prevActiveCells,
                                    -predictedSegmentDecrement,
                                    0.0, segment.segment)

  # ==============================
  # Helper functions
  # ==============================

  @staticmethod
  def bestMatchingSegment(connections, excitedColumn, prevActiveCells):
    """Gets the segment on a cell with the largest number of active synapses.
    Returns an int representing the segment and the number of synapses
    corresponding to it.

    @param connections      (Object) Connections instance for the tm
    @param excitedColumn    (dict)   Excited Column instance from
                                     excitedColumnsGenerator
    @param prevActiveCells  (list)   Active cells in `t-1`

    @return (tuple) Contains:
                      `bestSegment`                 (int),
                      `bestNumActiveSynapses`       (int)
    """
    maxOverlap = 0
    bestSegment = None

    for segment in excitedColumn["matchingSegments"]:
      if segment.overlap > maxOverlap:
        maxOverlap = segment.overlap
        bestSegment = segment

    return bestSegment


  @staticmethod
  def leastUsedCell(cells, connections, random):
    """ Gets the cell with the smallest number of segments.
    Break ties randomly.

    @param cells       (list)   Indices of cells
    @param connections (Object) Connections instance for the tm
    @param random      (object) Random number generator

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
  def growSynapses(connections, initialPermanence, nDesiredNewSynapes,
                   prevWinnerCells, random, segment):
    """ Creates nDesiredNewSynapes synapses on the segment passed in if
    possible, choosing random cells from the previous winner cells that are
    not already on the segment.

    @param  connections        (Object) Connections instance for the tm
    @param  initialPermanence  (float)  Initial permanence of a new synapse.
    @params nDesiredNewSynapes (int)    Desired number of synapses to grow
    @params prevWinnerCells    (list)   Winner cells in `t-1`
    @param  random             (object) Tm object used to generate random
                                        numbers
    @param  segment            (int)    Segment to grow synapses on.

    Notes: The process of writing the last value into the index in the array
    that was most recently changed is to ensure the same results that we get
    in the c++ implentation using iter_swap with vectors.
    """
    candidates = list(prevWinnerCells)
    eligibleEnd = len(candidates) - 1

    for synapse in connections.synapsesForSegment(segment):
      presynapticCell = connections.dataForSynapse(synapse).presynapticCell
      index = binSearch(candidates, presynapticCell)
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
  def adaptSegment(connections, prevActiveCells, permanenceIncrement,
                   permanenceDecrement, segment):
    """ Updates synapses on segment.
    Strengthens active synapses; weakens inactive synapses.

    @param  connections        (Object) Connections instance for the tm
    @param prevActiveCells      (list)   Active cells in `t-1`
    @param permanenceIncrement  (float)  Amount to increment active synapses
    @param permanenceDecrement  (float)  Amount to decrement inactive synapses
    @param segment              (int)    Segment to adapt
    """

    # Need to copy synapses for segment set below because it will be modified
    # during iteration by `destroySynapse`
    
    for synapse in set(connections.synapsesForSegment(segment)):
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

    if (len(connections.synapsesForSegment(segment)) == 0):
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


  def write(self, proto):
    """ Writes serialized data to proto object

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
    proto.predictedSegmentDecrement = self.predictedSegmentDecrement

    self.connections.write(proto.connections)
    self._random.write(proto.random)

    proto.activeCells = list(self.activeCells)
    proto.winnerCells = list(self.winnerCells)
    for i, active in enumerate(self.activeSegments):
      activeSegmentOverlaps = \
        proto.init('activeSegmentOverlaps', len(self.activeSegments))

      activeSegmentOverlaps[i].cell = active.segment.cell
      activeSegmentOverlaps[i].segment = active.segment.idx
      activeSegmentOverlaps[i].overlap = active.overlap

    for i, matching in enumerate(self.matchingSegments):
      matchingSegmentOverlaps = \
        proto.init('matchingSegmentOverlaps', len(self.matchingSegments))

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

    tm.columnDimensions = list(proto.columnDimensions)
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
    tm.activeSegments = [int(x) for x in proto.activeSegments]
    tm.winnerCells = [int(x) for x in proto.winnerCells]
    tm.matchingSegments = [int(x) for x in proto.matchingSegments]

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
