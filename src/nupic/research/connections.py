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

from collections import defaultdict
from bisect import bisect_left

EPSILON = 0.00001 # constant error threshold to check equality of permanences to
                  # other floats



class Segment(object):
  """ Class containing minimal information to identify a unique segment """

  __slots__ = ["cell", "idx", "flatIdx", "_synapses", "_numDestroyedSynapses",
               "_destroyed", "_lastUsedIteration"]

  def __init__(self, cell, idx, flatIdx):
    """
    @param cell (int) Index of the cell that this segment is on.
    @param idx (int) Index of the segment on the cell.
    @param flatIdx (int) The segment's flattened list index.
    """
    self.cell = cell
    self.idx = idx
    self.flatIdx = flatIdx
    self._synapses = []
    self._numDestroyedSynapses = 0
    self._destroyed = False
    self._lastUsedIteration = -1


  def __eq__(self, other):
    """ Explicitly implement this for unit testing. The flatIdx is not designed
    to be consistent after serialize / deserialize.

    """
    return (self.idx == other.idx and
            self.cell == other.cell and
            self._numDestroyedSynapses == other._numDestroyedSynapses and
            self._destroyed == other._destroyed and
            self._lastUsedIteration == other._lastUsedIteration)



class Synapse(object):
  """ Class containing minimal information to identify a unique synapse """

  __slots__ = ["segment", "idx", "presynapticCell", "permanence", "_destroyed"]

  def __init__(self, segment, idx, presynapticCell, permanence):
    """
    @param segment
    (Object) Segment object that the synapse is synapsed to.

    @param idx (int)
    Index of the synapse on the segment.

    @param presynapticCell (int)
    The index of the presynaptic cell of the synapse.

    @param permanence (float)
    Permanence of the synapse from 0.0 to 1.0.
    """
    self.segment = segment
    self.idx = idx
    self.presynapticCell = presynapticCell
    self.permanence = permanence
    self._destroyed = False


  def __eq__(self, other):
    """ Explicitly implement this for unit testing. Allow floating point
    differences for synapse permanence.

    """
    return (self.segment.cell == other.segment.cell and
            self.segment.idx == other.segment.idx and
            self.idx == other.idx and
            self.presynapticCell == other.presynapticCell and
            abs(self.permanence - other.permanence) < EPSILON)



class CellData(object):
  """ Class containing cell information. Internal to the Connections. """

  __slots__ = ["_segments", "_numDestroyedSegments"]

  def __init__(self):
    self._segments = []
    self._numDestroyedSegments = 0



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



class Connections(object):
  """ Class to hold data representing the connectivity of a
      collection of cells. """

  def __init__(self,
               numCells,
               maxSegmentsPerCell=255,
               maxSynapsesPerSegment=255):
    """ @param numCells (int) Number of cells in collection """

    # Save member variables
    self.numCells = numCells
    assert maxSegmentsPerCell > 0
    assert maxSynapsesPerSegment > 0
    self.maxSegmentsPerCell = maxSegmentsPerCell
    self.maxSynapsesPerSegment = maxSynapsesPerSegment

    CellDataFactory = self.cellDataFactory # Mitigate fn lookup penalty below
    self._cells = [CellDataFactory() for _ in xrange(numCells)]
    self._synapsesForPresynapticCell = defaultdict(list)
    self._segmentForFlatIdx = []

    self._numSegments = 0
    self._numSynapses = 0
    self._nextFlatIdx = 0
    self._iteration = 0


  @staticmethod
  def cellDataFactory():
    return CellData()


  def segmentsForCell(self, cell):
    """ Returns the segments that belong to a cell.

    @param cell (int) Cell index

    @return (generator)
    Segment objects representing segments on the given cell.
    """

    return (segment
            for segment in self._cells[cell]._segments
            if not segment._destroyed)


  def synapsesForSegment(self, segment):
    """ Returns the synapses on a segment.

    @param segment (int) Segment index

    @return (generator)
    Synapse objects representing synapses on the given segment.
    """

    if segment._destroyed:
      raise ValueError("Attempting to access destroyed segment's synapses")

    return (synapse
            for synapse in segment._synapses
            if not synapse._destroyed)


  def dataForSynapse(self, synapse):
    """ Returns the data for a synapse.

    This method exists to match the interface of the C++ Connections. This
    allows tests and tools to inspect the connections using a common interface.

    @param synapse (Object) Synapse object

    @return Synapse data
    """
    return synapse


  def dataForSegment(self, segment):
    """ Returns the data for a segment.

    This method exists to match the interface of the C++ Connections. This
    allows tests and tools to inspect the connections using a common interface.

    @param synapse (Object) Segment object

    @return segment data
    """
    return segment


  def getSegment(self, cell, idx):
    """ Returns a Segment object of the specified segment using data from the
        self._cells array.

    @param idx  (int) segment index on a cell
    @param cell (int) cell index

    @return (Segment) Segment object with index idx on the specified cell

    """

    return self._cells[cell]._segments[idx]


  def _minPermanenceSynapse(self, segment):
    """ Find this segment's synapse with the smallest permanence.

    This method is NOT equivalent to a simple min() call. It uses an EPSILON to
    account for floating point differences between C++ and Python.

    @param segment (Object) Segment to query.

    @return (Object) Synapse with the minimal permanence

    Note: On ties it will choose the first occurrence of the minimum permanence.

    """
    minSynapse = None
    minPermanence = float("inf")

    for synapse in self.synapsesForSegment(segment):
      if synapse.permanence < minPermanence - EPSILON:
        minSynapse = synapse
        minPermanence = synapse.permanence

    assert minSynapse is not None

    return minSynapse


  def segmentForFlatIdx(self, flatIdx):
    """ Get the segment with the specified flatIdx.

    @param flatIdx (int) The segment's flattened list index.

    @return (Segment) segment object
    """
    return self._segmentForFlatIdx[flatIdx]


  def segmentFlatListLength(self):
    """ Get the needed length for a list to hold a value for every segment's
    flatIdx.

    @return (int) Required list length
    """
    return self._nextFlatIdx


  def synapsesForPresynapticCell(self, presynapticCell):
    """ Returns the synapses for the source cell that they synapse on.

    @param presynapticCell (int) Source cell index

    @return (list) Synapse objects
    """
    return self._synapsesForPresynapticCell[presynapticCell]


  def createSegment(self, cell):
    """ Adds a new segment on a cell.

    @param cell (int) Cell index

    @return (int) New segment index
    """
    while self.numSegments(cell) >= self.maxSegmentsPerCell:
      leastRecentlyUsed = min(self.segmentsForCell(cell),
                              key=lambda s: s._lastUsedIteration)
      self.destroySegment(leastRecentlyUsed)

    cellData = self._cells[cell]

    if cellData._numDestroyedSegments > 0:
      segment = next(s for s in cellData._segments if s._destroyed)
      segment._destroyed = False
      cellData._numDestroyedSegments -= 1
    else:
      idx = len(cellData._segments)
      segment = Segment(cell, idx, self._nextFlatIdx)
      cellData._segments.append(segment)
      self._segmentForFlatIdx.append(segment)
      self._nextFlatIdx += 1

    segment._lastUsedIteration = self._iteration
    self._numSegments += 1

    return segment


  def destroySegment(self, segment):
    """ Destroys a segment.

    @param segment (Object) Segment object representing the segment to be
                            destroyed
    """
    assert not segment._destroyed

    for synapse in self.synapsesForSegment(segment):
      self.destroySynapse(synapse)

    segment._synapses = []
    segment._numDestroyedSynapses = 0
    segment._destroyed = True
    self._numSegments -= 1
    self._cells[segment.cell]._numDestroyedSegments += 1


  def createSynapse(self, segment, presynapticCell, permanence):
    """ Creates a new synapse on a segment.

    @param segment         (Object) Segment object for synapse to be synapsed to
    @param presynapticCell (int)    Source cell index
    @param permanence      (float)  Initial permanence

    @return (Object) created Synapse object
    """

    while self.numSynapses(segment) >= self.maxSynapsesPerSegment:
      self.destroySynapse(self._minPermanenceSynapse(segment))

    if segment._numDestroyedSynapses > 0:
      synapse = next(s for s in segment._synapses if s._destroyed)

      synapse._destroyed = False
      segment._numDestroyedSynapses -= 1

      synapse.presynapticCell = presynapticCell
      synapse.permanence = permanence

    else:
      idx = len(segment._synapses)
      synapse = Synapse(segment, idx, presynapticCell, permanence)
      segment._synapses.append(synapse)

    self._synapsesForPresynapticCell[presynapticCell].append(synapse)
    self._numSynapses += 1

    return synapse


  def destroySynapse(self, synapse):
    """ Destroys a synapse.

    @param synapse (Object) Synapse object to destroy
    """
    assert not synapse._destroyed

    synapse._destroyed = True
    synapse.segment._numDestroyedSynapses += 1
    self._numSynapses -= 1

    presynapticSynapses = \
      self._synapsesForPresynapticCell[synapse.presynapticCell]

    i = next(i
             for i, syn in enumerate(presynapticSynapses)
             if syn is synapse)
    del presynapticSynapses[i]

    if len(presynapticSynapses) == 0:
      del self._synapsesForPresynapticCell[synapse.presynapticCell]


  def updateSynapsePermanence(self, synapse, permanence):
    """ Updates the permanence for a synapse.
    @param synapse    (Object) Synapse object to be updated
    @param permanence (float)  New permanence
    """

    synapse.permanence = permanence


  def computeActivity(self, activePresynapticCells, connectedPermanence):
    """ Compute each segment's number of active synapses for a given input.
    In the returned lists, a segment's active synapse count is stored at index
    `segment.flatIdx`.

    @param activePresynapticCells (iter)  active cells
    @param connectedPermanence    (float) permanence threshold for a synapse
                                          to be considered connected

    @return (tuple) Contains:
                      `numActiveConnectedSynapsesForSegment`  (list),
                      `numActivePotentialSynapsesForSegment`  (list)
    """

    numActiveConnectedSynapsesForSegment = [0] * self._nextFlatIdx
    numActivePotentialSynapsesForSegment = [0] * self._nextFlatIdx

    threshold = connectedPermanence - EPSILON

    for cell in activePresynapticCells:
      for synapse in self._synapsesForPresynapticCell[cell]:
        flatIdx = synapse.segment.flatIdx
        numActivePotentialSynapsesForSegment[flatIdx] += 1
        if synapse.permanence > threshold:
          numActiveConnectedSynapsesForSegment[flatIdx] += 1

    return (numActiveConnectedSynapsesForSegment,
            numActivePotentialSynapsesForSegment)


  def recordSegmentActivity(self, segment):
    """ Record the fact that a segment had some activity. This information is
        used during segment cleanup.

        @param segment The segment that had some activity.
    """
    segment._lastUsedIteration = self._iteration


  def startNewIteration(self):
    """ Mark the passage of time. This information is used during segment
    cleanup.
    """
    self._iteration += 1


  def numSegments(self, cell=None):
    """ Returns the number of segments.

    @param cell (int) optional parameter to get the number of segments on a cell

    @retval (int) number of segments on all cells if cell is not specified,
                  or on a specific specified cell
    """
    if cell is not None:
      cellData = self._cells[cell]
      return len(cellData._segments) - cellData._numDestroyedSegments

    return self._numSegments


  def numSynapses(self, segment=None):
    """ Returns the number of Synapses.

    @param segment (Object) optional parameter to get the number of synapses on
                            a segment

    @retval (int) number of synapses on all segments if segment is not
                  specified, or on a specified segment
    """
    if segment is not None:
      return len(segment._synapses) - segment._numDestroyedSynapses
    return self._numSynapses


  def write(self, proto):
    """ Writes serialized data to proto object

    @param proto (DynamicStructBuilder) Proto object
    """
    protoCells = proto.init('cells', self.numCells)

    for i in xrange(self.numCells):
      segments = self._cells[i]._segments
      protoSegments = protoCells[i].init('segments', len(segments))

      for j in xrange(len(segments)):
        synapses = segments[j]._synapses
        protoSynapses = protoSegments[j].init('synapses', len(synapses))
        protoSegments[j].destroyed = segments[j]._destroyed
        protoSegments[j].lastUsedIteration = segments[j]._lastUsedIteration

        for k in xrange(len(synapses)):
          protoSynapses[k].presynapticCell = synapses[k].presynapticCell
          protoSynapses[k].permanence = synapses[k].permanence
          protoSynapses[k].destroyed = synapses[k]._destroyed

    proto.maxSegmentsPerCell = self.maxSegmentsPerCell
    proto.maxSynapsesPerSegment = self.maxSynapsesPerSegment
    proto.iteration = self._iteration


  @classmethod
  def read(cls, proto):
    """ Reads deserialized data from proto object

    @param proto (DynamicStructBuilder) Proto object

    @return (Connections) Connections instance
    """
    #pylint: disable=W0212
    protoCells = proto.cells
    connections = cls(len(protoCells),
                      proto.maxSegmentsPerCell,
                      proto.maxSynapsesPerSegment)

    for cellIdx, protoCell in enumerate(protoCells):
      protoCell = protoCells[cellIdx]
      protoSegments = protoCell.segments
      connections._cells[cellIdx] = cls.cellDataFactory()
      segments = connections._cells[cellIdx]._segments

      for segmentIdx, protoSegment in enumerate(protoSegments):
        segment = Segment(cellIdx, segmentIdx, connections._nextFlatIdx)
        segment._destroyed = protoSegment.destroyed
        segment._lastUsedIteration = protoSegment.lastUsedIteration

        segments.append(segment)
        connections._segmentForFlatIdx.append(segment)
        connections._nextFlatIdx += 1

        synapses = segment._synapses
        protoSynapses = protoSegment.synapses

        for synapseIdx, protoSynapse in enumerate(protoSynapses):
          presynapticCell = protoSynapse.presynapticCell
          synapse = Synapse(segment, synapseIdx, presynapticCell,
                            protoSynapse.permanence)
          synapse._destroyed = protoSynapse.destroyed
          synapses.append(synapse)
          connections._synapsesForPresynapticCell[presynapticCell].append(
            synapse)

          if synapse._destroyed:
            segment._numDestroyedSynapses += 1
          else:
            connections._numSynapses += 1

        if segment._destroyed:
          connections._cells[cellIdx]._numDestroyedSegments += 1
        else:
          connections._numSegments += 1

    connections._iteration = proto.iteration
    #pylint: enable=W0212
    return connections


  def __eq__(self, other):
    """ Equality operator for Connections instances.
    Checks if two instances are functionally identical

    @param other (Connections) Connections instance to compare to
    """
    #pylint: disable=W0212
    if self.maxSegmentsPerCell != other.maxSegmentsPerCell:
      return False
    if self.maxSynapsesPerSegment != other.maxSynapsesPerSegment:
      return False

    for i in xrange(self.numCells):
      segments = self._cells[i]._segments
      otherSegments = other._cells[i]._segments

      if len(segments) != len(otherSegments):
        return False

      for j in xrange(len(segments)):
        segment = segments[j]
        otherSegment = otherSegments[j]
        synapses = segment._synapses
        otherSynapses = otherSegment._synapses

        if segment._destroyed != otherSegment._destroyed:
          return False
        if segment._lastUsedIteration != otherSegment._lastUsedIteration:
          return False
        if len(synapses) != len(otherSynapses):
          return False

        for k in xrange(len(synapses)):
          synapse = synapses[k]
          otherSynapse = otherSynapses[k]

          if synapse.presynapticCell != otherSynapse.presynapticCell:
            return False
          if (synapse.permanence - otherSynapse.permanence) > EPSILON :
            return False
          if synapse._destroyed != otherSynapse._destroyed:
            return False

    if (len(self._synapsesForPresynapticCell) !=
        len(self._synapsesForPresynapticCell)):
      return False

    for i in self._synapsesForPresynapticCell.keys():
      synapses = self._synapsesForPresynapticCell[i]
      otherSynapses = other._synapsesForPresynapticCell[i]
      if len(synapses) != len(otherSynapses):
        return False

      for j in xrange(len(synapses)):
        synapse = synapses[j]
        otherSynapse = otherSynapses[j]
        segment = synapse.segment
        otherSegment = otherSynapse.segment
        cell = segment.cell
        otherCell = otherSegment.cell

        if synapse.idx != otherSynapse.idx:
          return False
        if segment.idx != otherSegment.idx:
          return False
        if cell != otherCell:
          return False

    if self._numSegments != other._numSegments:
      return False
    if self._numSynapses != other._numSynapses:
      return False
    if self._iteration != other._iteration:
      return False

    #pylint: enable=W0212
    return True


  def __ne__(self, other):
    """ Non-equality operator for Connections instances.
    Checks if two instances are not functionally identical

    @param other (Connections) Connections instance to compare to
    """
    return not self.__eq__(other)
