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

  __slots__ = ['idx', 'cell', 'data']

  def __init__(self, idx, cell, data):
    """
       @param idx  (int) Index of the segment on the cell
       @param cell (int) Index of the cell that this segment is on
    """
    self.idx = idx
    self.cell = cell
    self.data = data


  def __eq__(self, other):
    return (self.idx, self.cell) == (other.idx, other.cell)


class Synapse(object):
  """ Class containing minimal information to identify a unique synapse """

  __slots__ = ['idx', 'segment', 'data']

  def __init__(self, idx, segment, synapseData):
    """
       @param idx     (int)    Index of the synapse on the segment
       @param segment (Object) Segment Object that the synapse is synapsed to
    """
    self.idx = idx
    self.segment = segment
    self.data = synapseData


  def __eq__(self, other):
    return ((self.idx, self.segment, self.data) ==
            (other.idx, other.segment, other.data))


class SynapseData(object):
  """ Class containing other important synapse information """

  __slots__ = ['presynapticCell', 'permanence', 'destroyed']

  def __init__(self, presynapticCell, permanence):
    """
       @param presynapticCell (int)   The index of the presynaptic cell of the
                                      synapse
       @param permanence      (float) permanence of the synapse from 0.0 to 1.0
    """
    self.presynapticCell = presynapticCell
    self.permanence = permanence
    self.destroyed = False  # boolean destroyed flag so object can be reused


  def __eq__(self, other):
    return (self.segment == other.segment and
            self.presynapticCell == other.presynapticCell and
            abs(self.permanence - other.permanence) < EPSILON)


class SegmentData(object):
  """ Class containing other important segment information """

  __slots__ = ['synapses', 'numDestroyedSynapses', 'destroyed',
               'lastUsedIteration', 'flatIdx']

  def __init__(self, flatIdx):
    """
       @param flatIdx (int) global index of the segment
    """
    self.synapses = []
    self.numDestroyedSynapses = 0
    self.destroyed = False
    self.lastUsedIteration = -1
    self.flatIdx = flatIdx


class CellData(object):
  """ Class containing cell information """

  __slots__ = ['segments', 'numDestroyedSegments']

  def __init__(self):
    self.segments = []   # list of segments on the cell
    self.numDestroyedSegments = 0


class SegmentOverlap(object):
  """ Class that allows tracking of overlap scores on segments """

  __slots__ = ['segment', 'overlap']

  def __init__(self, segment, overlap):
    """
       @param segment (Object) Segment object to keep track of
       @param overlap (int)    The number of synapses on the segment that
                               are above either the matching threshold or
                               the active threshold
    """
    self.segment = segment
    self.overlap = overlap

  def __eq__(self, other):
    return (self.segment, self.overlap) == (other.segment, other.overlap)



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

    self._cells = [CellData() for _ in xrange(numCells)]
    self._synapsesForPresynapticCell = defaultdict(list)
    self._segmentForFlatIdx = []

    self._synapsesForSegment = defaultdict(list)

    self._numSegments = 0
    self._numSynapses = 0
    self._nextFlatIdx = 0
    self._iteration = 0


  def segmentsForCell(self, cell):
    """ Returns the segments that belong to a cell.

    @param cell (int) Cell index

    @return (list) Segment objects representing segments on the given cell
    """

    segmentsList = self._cells[cell].segments


    return [Segment(i, cell, segmentsList[i])
            for i in xrange(len(segmentsList))
            if not segmentsList[i].destroyed]


  def synapsesForSegment(self, segment):
    """ Returns the synapses on a segment.

    @param segment (int) Segment index

    @return (list) Synapse objects representing synapses on the given segment
    """

    segmentData = segment.data
    if segmentData.destroyed:
      raise ValueError("Attempting to access destroyed segment's synapses")

    return [synapse
            for synapse in self._synapsesForSegment[segmentData.flatIdx]
            if not synapse.data.destroyed]


  def dataForSynapse(self, synapse):
    """ Returns the data for a synapse.

    @param synapse (Object) Synapse object

    @return (SynapseData) Synapse data
    """

    return synapse.data


  def dataForSegment(self, segment):
    """ Returns the data for a segment.

    @param segment (Object) Segment object

    @return (SegmentData) Segment data
    """

    return segment.data


  def getSegment(self, idx, cell):
    """ Returns a Segment object of the specified segment using data from the
        self._cells array.

    @param idx  (int) segment index on a cell
    @param cell (int) cell index

    @return (Segment) Segment object with index idx on the specified cell

    """

    return Segment(idx, cell, self._cells[cell].segments[idx])


  def _leastRecentlyUsedSegment(self, cell):
    """ Internal method for finding the least recently activated segment on a
        cell

    @param cell (int) cell index to search for segments on

    @return (Object) Segment object of the segment that was least recently
                     created/activated.
    """
    segments = self._cells[cell].segments
    minIdx = float("inf")
    minIteration = float("inf")

    for i in xrange(len(segments)):
      segment = segments[i]
      if (not segment.destroyed and
          segment.lastUsedIteration < minIteration):
        minIdx = i
        minIteration = segment.lastUsedIteration

    return Segment(minIdx, cell, segments[minIdx])


  def _minPermanenceSynapse(self, segment):
    """ Internal method for finding the synapse with the smallest permanence
    on the given segment.

    @param segment (Object) Segment object to search for synapses on

    @return (Object) Synapse object on the segment of the minimal permanence

    Note: On ties it will chose the first occurrence of the minimum permanence
    """
    synapses = self._synapsesForSegment[segment.data.flatIdx]
    minIdx = float("inf")
    minPermanence = float("inf")

    for i in xrange(len(synapses)):
      synapseData = synapses[i].data
      if (not synapseData.destroyed) and (synapseData.permanence
                                          < minPermanence - EPSILON):
        minIdx = i
        minPermanence = synapseData.permanence

    return synapses[minIdx]


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
      self.destroySegment(self._leastRecentlyUsedSegment(cell))

    cellData = self._cells[cell]
    segment = Segment(-1, cell, None) # New segment with some default values

    if cellData.numDestroyedSegments > 0:
      found = False
      for i in xrange(len(cellData.segments)):
        if cellData.segments[i].destroyed:
          segment.idx = i
          found = True

      if not found:
        raise AssertionError("Failed to find a destroyed segment.")

      cellData.segments[segment.idx].destroyed = False
      cellData.numDestroyedSegments -= 1
    else:
      segment.idx = len(cellData.segments)
      cellData.segments.append(SegmentData(self._nextFlatIdx))
      self._segmentForFlatIdx.append(segment)
      self._nextFlatIdx += 1

    segmentData = cellData.segments[segment.idx]
    segmentData.lastUsedIteration = self._iteration
    segment.data = segmentData
    self._numSegments += 1

    return segment


  def destroySegment(self, segment):
    """ Destroys a segment.

    @param segment (Object) Segment object representing the segment to be
                            destroyed
    """
    segmentData = segment.data
    if not segmentData.destroyed:
      for i in xrange(len(segmentData.synapses)):
        synapse = Synapse(i, segment, segmentData.synapses[i])
        synapseData = synapse.data

        if not synapseData.destroyed:
          cell = synapseData.presynapticCell
          presynapticSynapses = self._synapsesForPresynapticCell[cell]

          for i in xrange(len(presynapticSynapses)):
            if presynapticSynapses[i] == synapse:
              del presynapticSynapses[i]

              if len(presynapticSynapses) == 0:
                del self._synapsesForPresynapticCell[cell]
              self._numSynapses -= 1
              break

      segmentData.synapses = []
      self._synapsesForSegment[segmentData.flatIdx] = []
      segmentData.numDestroyedSynapses = 0
      segmentData.destroyed = True
      self._cells[segment.cell].numDestroyedSegments += 1
      self._numSegments -= 1



  def createSynapse(self, segment, presynapticCell, permanence):
    """ Creates a new synapse on a segment.

    @param segment         (Object) Segment object for synapse to be synapsed to
    @param presynapticCell (int)    Source cell index
    @param permanence      (float)  Initial permanence

    @return (Object) created Synapse object
    """

    while self.numSynapses(segment) >= self.maxSynapsesPerSegment:
      self.destroySynapse(self._minPermanenceSynapse(segment))

    segmentData = segment.data
    synapseIdx = -1
    found = False
    if segmentData.numDestroyedSynapses > 0:
      for i in xrange(len(segmentData.synapses)):
        if segmentData.synapses[i].destroyed:
          synapseIdx = i
          found = True
          break

      if not found:
        raise AssertionError("Failed to find a destroyed synapse.")

      synapseData = segmentData.synapses[synapseIdx]
      synapseData.destroyed = False
      segmentData.numDestroyedSynapses -= 1

      synapseData.presynapticCell = presynapticCell
      synapseData.permanence = permanence
      self._synapsesForSegment[segmentData.flatIdx][synapseIdx].data =\
        synapseData

    else:
      synapseIdx = len(segmentData.synapses)
      synapseData = SynapseData(presynapticCell, permanence)
      segmentData.synapses.append(synapseData)

    synapse = Synapse(synapseIdx, segment, synapseData)
    self._synapsesForPresynapticCell[presynapticCell].append(synapse)
    if not found:
      self._synapsesForSegment[segmentData.flatIdx].append(synapse)
    self._numSynapses += 1

    return synapse


  def destroySynapse(self, synapse):
    """ Destroys a synapse.

    @param synapse (Object) Synapse object to destroy
    """
    synapseData = synapse.data
    if not synapseData.destroyed:
      presynapticSynapses = \
        self._synapsesForPresynapticCell[synapseData.presynapticCell]

      for i in xrange(len(presynapticSynapses)):
        if presynapticSynapses[i] == synapse:
          del presynapticSynapses[i]

          if len(presynapticSynapses) == 0:
            del self._synapsesForPresynapticCell[synapseData.presynapticCell]

          synapseData.destroyed = True
          synapse.segment.data.numDestroyedSynapses += 1
          self._numSynapses -= 1
          break


  def updateSynapsePermanence(self, synapse, permanence):
    """ Updates the permanence for a synapse.

    @param synapse    (Object) Synapse object to be updated
    @param permanence (float)  New permanence
    """

    synapse.data.permanence = permanence


  def computeActivity(self, activeInput, activePermanenceThreshold,
                      activeSynapseThreshold, matchingPermananceThreshold,
                      matchingSynapseThreshold, recordIteration=True):
    """ Computes active and matching segments given the current active input.

    @param activeInput                 (set)   currently active cells
    @param activePermanenceThreshold   (float) permanence threshold for a
                                               synapse to be considered active
    @param activeSynapseThreshold      (int)   number of synapses needed for a
                                               segment to be considered active
    @param matchingPermananceThreshold (float) permanence threshold for a
                                               synapse to be considered matching
    @param matchingSynapseThreshold    (int)   number of synapses needed for a
                                               segment to be considered matching
    @param recordIteration             (bool)  bool to determine if we should
                                               update the lastUsedIteration on
                                               active segments and the internal
                                               iteration variable

    @return (tuple) Contains:
                      `activeSegments`         (list),
                      `matchingSegments`       (list),

    Notes:
      activeSegments and matchingSegments are sorted by the cell they are on
      and they are lists of SegmentOverlap objects.
    """

    numActiveSynapsesForSegment = [0] * self._nextFlatIdx
    numMatchingSynapsesForSegment = [0] * self._nextFlatIdx

    for cell in activeInput:
      for synapse in self._synapsesForPresynapticCell[cell]:
        synapseData = synapse.data
        segment = synapse.segment
        permanence = synapseData.permanence
        segmentData = segment.data
        if permanence - matchingPermananceThreshold > -EPSILON:
          numMatchingSynapsesForSegment[segmentData.flatIdx] += 1
          if permanence - activePermanenceThreshold > -EPSILON:
            numActiveSynapsesForSegment[segmentData.flatIdx] += 1

    if recordIteration:
      self._iteration += 1

    activeSegments = []
    matchingSegments = []
    for i in xrange(self._nextFlatIdx):
      numActive = numActiveSynapsesForSegment[i]
      if numActive >= activeSynapseThreshold:
        activeSegments.append(SegmentOverlap(self._segmentForFlatIdx[i],
                                             numActive))

        if recordIteration:
          segment.data.lastUsedIteration = self._iteration


    for i in xrange(self._nextFlatIdx):
      numMatching = numMatchingSynapsesForSegment[i]
      if numMatching >= matchingSynapseThreshold:
        matchingSegments.append(SegmentOverlap(self._segmentForFlatIdx[i],
                                               numMatching))

    segmentKey = lambda s: (s.segment.cell * self.maxSegmentsPerCell
                            + s.segment.idx)
    return (sorted(activeSegments, key = segmentKey),
            sorted(matchingSegments, key = segmentKey))


  def numSegments(self, cell=None):
    """ Returns the number of segments.

    @param cell (int) optional parameter to get the number of segments on a cell

    @retval (int) number of segments on all cells if cell is not specified,
                  or on a specific specified cell
    """
    if cell is not None:
      cellData = self._cells[cell]
      return len(cellData.segments) - cellData.numDestroyedSegments

    return self._numSegments


  def numSynapses(self, segment=None):
    """ Returns the number of Synapses.

    @param segment (Object) optional parameter to get the number of synapses on
                            a segment

    @retval (int) number of synapses on all segments if segment is not
                  specified, or on a specified segment
    """
    if segment is not None:
      segmentData = self._cells[segment.cell].segments[segment.idx]
      return len(segmentData.synapses) - segmentData.numDestroyedSynapses
    return self._numSynapses


  def write(self, proto):
    """ Writes serialized data to proto object

    @param proto (DynamicStructBuilder) Proto object
    """
    protoCells = proto.init('cells', self.numCells)

    for i in xrange(self.numCells):
      segments = self._cells[i].segments
      protoSegments = protoCells[i].init('segments', len(segments))

      for j in xrange(len(segments)):
        synapses = segments[j].synapses
        protoSynapses = protoSegments[j].init('synapses', len(synapses))
        protoSegments[j].destroyed = segments[j].destroyed
        protoSegments[j].lastUsedIteration = segments[j].lastUsedIteration

        for k in xrange(len(synapses)):
          protoSynapses[k].presynapticCell = synapses[k].presynapticCell
          protoSynapses[k].permanence = synapses[k].permanence
          protoSynapses[k].destroyed = synapses[k].destroyed

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

    for i in xrange(len(protoCells)):
      protoCell = protoCells[i]
      protoSegments = protoCell.segments
      connections._cells[i] = CellData()
      segments = connections._cells[i].segments

      for j in xrange(len(protoSegments)):
        segmentData = SegmentData(connections._nextFlatIdx)
        segmentData.destroyed = protoSegments[j].destroyed
        segmentData.lastUsedIteration = protoSegments[j].lastUsedIteration
        connections._nextFlatIdx += 1
        segments.append(segmentData)

        segment = Segment(j, i, segmentData)
        connections._segmentForFlatIdx.append(segment)

        protoSynapses = protoSegments[j].synapses
        synapses = segments[j].synapses

        for k in xrange(len(protoSynapses)):
          presynapticCell = protoSynapses[k].presynapticCell
          synapseData = SynapseData(presynapticCell,
                                    protoSynapses[k].permanence)
          synapseData.destroyed = protoSynapses[k].destroyed
          synapses.append(synapseData)

          synapse = Synapse(k, segment, synapseData)
          connections._synapsesForPresynapticCell[presynapticCell].append(
            synapse)
          connections._synapsesForSegment[segmentData.flatIdx].append(synapse)

          if synapseData.destroyed:
            segments[j].numDestroyedSynapses += 1
          else:
            connections._numSynapses += 1

        if segmentData.destroyed:
          connections._cells[i].numDestroyedSegments += 1
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
      segments = self._cells[i].segments
      otherSegments = other._cells[i].segments

      if len(segments) != len(otherSegments):
        return False

      for j in xrange(len(segments)):
        segment = segments[j]
        otherSegment = otherSegments[j]
        synapses = segment.synapses
        otherSynapses = otherSegment.synapses

        if segment.destroyed != otherSegment.destroyed:
          return False
        if segment.lastUsedIteration != otherSegment.lastUsedIteration:
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
          if synapse.destroyed != otherSynapse.destroyed:
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
