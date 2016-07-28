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

class Segment(object):

  def __init__(self, idx, cell):
    self.SegmentIdx = idx
    self.cell = cell


class Synapse(object):

  def __init__(self, idx, segment):
    self.SynapseIdx = idx
    self.segment = segment
    


class SynapseData(object):

  __slots__ = ("segment", "presynapticCell", "permanence")


  def __init__(self, segment, presynapticCell, permanence):
    self.segment = segment
    self.presynapticCell = presynapticCell
    self.permanence = permanence


  def __eq__(self, other):
    return (self.segment, self.presynapticCell, self.permanence) == other


class SegmentData(object):
  
  def __init__(self, flatIdx):
    self.synapses = []
    self.numDestroyedSynapses = 0
    self.destroyed = False
    self.lastUsedIteration = -1
    self.flatIdx = flatIdx


class CellData(object):

  def __init__(self):
    self.segments = []
    self.numDestroyedSegments = 0


class SegmentOverlap(object):

  def __init__(self, segment, overlap):
    self.segment = segment
    self.overlap = overlap



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
    self.maxSegmentsPerCell = maxSegmentsPerCell
    self.maxSynapsesPerSegment = maxSynapsesPerSegment

    self._cells = dict()
    self._synapsesForPresynapticCell = dict()
    self._segmentForFlatIdx = []

    self._numSegments = 0
    self._numSynapses = 0
    self._nextFlatIdx = 0
    self._iteration = 0


  def cellForSegment(self, segment):
    """ Returns the cell that a segment belongs to.

    @param segment (Segment) Segment index

    @return (int) Cell index
    """
    return segment.cell


  def columnForSegment(self, segment, cellsPerColumn):
    """ Returns the column that a segment's presynapticCell belongs to

    @param segment        (Segment) Segment
    @param cellsPerColumn (int) Number of cells in a column in the tm

    @return (int)
    """
    return segment.cell / cellsPerColumn


  def segmentsForCell(self, cell):
    """ Returns the segments that belong to a cell.

    @param cell (int) Cell index

    @return (set) Segment indices
    """
    self._validateCell(cell)

    if not cell in self._cells:
      return list()

    return [seg for seg in self._cells[cell].segments if not seg.destroyed]

  def synapsesForSegment(self, segment):
    """ Returns the synapses on a segment.

    @param segment (int) Segment index

    @return (set) Synapse indices
    """
    segmentData = self.dataForSegment(segment)
    if segmentData.destroyed:
      raise ValueError("Attempting to access destroyed segment's synapses")
    
    return [syn for syn in segmentData.synapses if not syn.destroyed]


  def dataForSynapse(self, synapse):
    """ Returns the data for a synapse.

    @param synapse (int) Synapse index

    @return (SynapseData) Synapse data
    """

    return self._cells[synapse.segment.cell].segments\
                      [synapse.segment.idx].synapses[synapse.idx]

  def dataForSegment(self, segment):
    return self._cells[segment.cell].segments[segment.idx]


  def synapsesForPresynapticCell(self, presynapticCell):
    if not presynapticCell in self._synapsesForPresynapticCell:
      return []

    return self._synapsesForPresynapticCell[presynapticCell]


  def _leastRecentlyUsedSegment(self, cell):
    segments = self._cells[cell].segments
    minIdx = -float("inf")
    minIteration = -float("inf")

    for i in xrange(len(segments)):
      if (not segments[i].destroyed and 
          segments[i].lastUsedIteration < minIteration):
        minIdx = i
        minIteration = segments[i].lastUsedIteration

    return Segment(minIdx, cell)

  
  def _minPermanenceSynapse(self, segment):
    synapses = self._cells[segment.cell].segments[segment.idx].synapses
    minIdx = -float("inf")
    minPermanence = -float("inf")

    for i in xrange(len(synapses)):
      if not synapses[i].destroyed and synapses[i].permanence < minPermanence:
        minIdx = i
        minPermanence = synapses[i].permanence

    return Synapse(minIdx, segment)




  def synapsesForPresynapticCell(self, presynapticCell):
    """ Returns the synapses for the source cell that they synapse on.

    @param presynapticCell (int) Source cell index

    @return (set) Synapse indices
    """
    return self._synapsesForPresynapticCell[presynapticCell]


  def createSegment(self, cell):
    """ Adds a new segment on a cell.

    @param cell (int) Cell index

    @return (int) New segment index
    """
    if not cell in self._cells:
      self._cells[cell] = CellData()

    while self.numSegments(cell) >= self.maxSegmentsPerCell:
      self.destroySegment(self._leastRecentlyUsedSegment(cell))

    cellData = self._cells[cell]
    segment = Segment(-1, cell)

    if cellData.numDestroyedSegments > 0:
      found = False
      for i in xrange(len(cellData.segments)):
        if cellData.segments[i].destroyed:
          segment.idx = i
          found = True

      if not found:
        raise AssertionError("Failed to find a destroyed segment.")
       
      cellData.segments[segment.idx].destroyed = False
      self.numDestroyedSegments -= 1
    else:
      segment.idx = len(cellData.segments)
      cellData.segments.append(SegmentData(self._nextFlatIdx))
      self._segmentForFlatIdx.append(segment)
      self._nextFlatIdx += 1

    return segment


  def destroySegment(self, segment):
    """ Destroys a segment.

    @param segment (int) Segment index
    """
    segmentData = self.dataForSegment(segment)

    if not segmentData.destroyed:
      for i in xrange(len(segmentData.synapses)):
        synapse = Synapse(i, segment)
        synapseData = self.dataForSynapse(synapse) #dont think this is neeeded

        if not synData.destroyed:
          cell = synapseData.presynapticCell
          presynapticSynapses = self._synapsesForPresynapticCell[cell]
          
          for i in xrange(len(presynapticSynapses)):
            if presynapticSynapsaes[i] == synapse:
              del presynapticSynpses[i]

              if len(presynapticSynapses) == 0:
                del self._synapsesForPresynapticCell[cell]
              self._numSynapses -= 1
              break

      segmentData.synapses = []
      segmentData.numDestroyedSynapses = 0
      segmentData.destroyed = True
      self._cells[segment.cell].numDestroyedSegments += 1
      self._numSegments -= 1


  def createSynapse(self, segment, presynapticCell, permanence):
    """ Creates a new synapse on a segment.

    @param segment         (int)   Segment index
    @param presynapticCell (int)   Source cell index
    @param permanence      (float) Initial permanence

    @return (int) Synapse index
    """
    
    while numSynapses(segment) >= self.maxSynapsesPerSegment:
      self.destroySynapse(self._minPermanenceSynapse(segment))

    segmentData = self.dataForSegment(segment)
    synapseIdx = -1

    if segmentData.numDestroyedSynapses > 0:
      found = False
      for i in xrange(len(segmentData.synapses)):
        if segmentData.synapses[i].destroyed:
          synapseIdx = i
          found = True
          break

      if not found:
        raise AssertionError("Failed to find a destroyed synapse.")

      segmentData.synapses[synapseIdx].destroyed = False
      segmentData.numDestroyedSynapses -= 1

      segmentDAta.synapses[synapseIdx].presynapticCell = presynapticCell
      segmentDAta.synapses[synapseIdx].permanence = permanence

    else:
      synapseIdx = len(segmentData.synapses)
      segmentData.synapses.append(
        SynapseData(segment, presynapticCell, permanence))
    
    synapse = Synapse(synapseIdx, segment)
    self._synapsesForPresynapticCell[presynapticCell].append(synapse)
    self._numSynapses += 1

    return synapse


  def destroySynapse(self, synapse):
    """ Destroys a synapse.

    @param synapse (int) Synapse index
    """
    synapseData = self.dataForSynapse(synapse)

    if not synapseData.destroyed:
      presynapticSynapses = self._synapsesForPresynapticCell(
        synapseData.presynapticCell)
      
      for i in xrange(len(presynapticSynapses)):
        if presynapticSynapsaes[i] == synapse:
          del presynapticSynpses[i]

          if len(presynapticSynapses) == 0:
            del self._synapsesForPresynapticCell[cell]

          synapseData.destroyed = True
          self.dataForSegment(synapse.segment).numDestroyedSynapses += 1
          self._numSynapses -= 1
          break


  def updateSynapsePermanence(self, synapse, permanence):
    """ Updates the permanence for a synapse.

    @param synapse    (int)   Synapse index
    @param permanence (float) New permanence
    """

    self.dataForSynapse(synapse).permanence = permanence


  def computeActivity(self, activeInput, activePermanenceThreshold,
                      activeSynapseThreshold, matchingPermananceThreshold,
                      matchingSynapseThreshold):
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

    @return (tuple) Contains:
                      `activeSegments`         (list),
                      `matchingSegments`        (list),

    Notes:
      activeSegments and matchingSegments are sorted by the cell they are on.
    """

    numActiveSynapsesForSegment = [0] * self._nextSegmentIdx
    numMatchingSynapsesForSegment = [0] * self._nextSegmentIdx

    for cell in activeInput:
      for synapseData in self.synapsesForPresynapticCell(cell).values():
        segment = synapseData.segment
        permanence = synapseData.permanence
        if permanence >= matchingPermananceThreshold:
          numMatchingSynapsesForSegment[segment] += 1
          if synapseData.permanence >= activePermanenceThreshold:
            numActiveSynapsesForSegment[segment] += 1

    activeSegments = []
    matchingSegments = []
    for i in xrange(self._nextSegmentIdx):
      if numActiveSynapsesForSegment[i] >= activeSynapseThreshold:
        activeSegments.append(i)

    for i in xrange(self._nextSegmentIdx):
      if numMatchingSynapsesForSegment[i] >= matchingSynapseThreshold:
        matchingSegments.append(i)

    segCmp = lambda a, b: self._segments[a] - self._segments[b]
    return (sorted(activeSegments, cmp = segCmp),
            sorted(matchingSegments, cmp = segCmp))


  def numSegments(self):
    """ Returns the number of segments. """
    return self._numSegments


  def numSynapses(self):
    """ Returns the number of synapses. """
    return self._numSynapses

  def write(self, proto):
    """ Writes serialized data to proto object

    @param proto (DynamicStructBuilder) Proto object
    """
    protoCells = proto.init('cells', self.numCells)

    for cell in xrange(self.numCells):
      segments = self.segmentsForCell(cell)
      protoSegments = protoCells[cell].init('segments', len(segments))

      for j, segment in enumerate(segments):
        synapses = self.synapsesForSegment(segment)
        protoSynapses = protoSegments[j].init('synapses', len(synapses))

        for k, synapse in enumerate(synapses):
          synapseData = self.dataForSynapse(synapse)
          protoSynapse = protoSynapses[k]

          protoSynapse.presynapticCell = synapseData.presynapticCell
          protoSynapse.permanence = synapseData.permanence



  @classmethod
  def read(cls, proto):
    """ Reads deserialized data from proto object

    @param proto (DynamicStructBuilder) Proto object

    @return (Connections) Connections instance
    """
    protoCells = proto.cells
    connections = cls(len(protoCells))

    for i in xrange(len(protoCells)):
      protoCell = protoCells[i]
      protoSegments = protoCell.segments

      for j in xrange(len(protoSegments)):
        protoSegment = protoSegments[j]
        protoSynapses = protoSegment.synapses
        segment = connections.createSegment(i)

        for k in xrange(len(protoSynapses)):
          protoSynapse = protoSynapses[k]
          connections.createSynapse(segment,
                                    int(protoSynapse.presynapticCell),
                                    protoSynapse.permanence)

    return connections


  def __eq__(self, other):
    """ Equality operator for Connections instances.
    Checks if two instances are functionally identical
    (might have different internal state).

    @param other (Connections) Connections instance to compare to
    """
    if self.numCells != other.numCells:
      return False

    for cell in xrange(self.numCells):
      segmentSet = set()
      for segment in self.segmentsForCell(cell):
        synapseSet = self._synapseSetForSynapses(
          self.synapsesForSegment(segment))
        segmentSet.add(frozenset(synapseSet))

      otherSegmentSet = set()
      #pylint: disable=W0212
      for segment in other.segmentsForCell(cell):
        otherSynapseSet = other._synapseSetForSynapses(
          other.synapsesForSegment(segment))
        otherSegmentSet.add(frozenset(otherSynapseSet))

      if segmentSet != otherSegmentSet:
        return False

      synapseSet = self._synapseSetForSynapses(
        self.synapsesForPresynapticCell(cell))

      otherSynapseSet = other._synapseSetForSynapses(
        other.synapsesForPresynapticCell(cell))
      #pylint: enable=W0212
      if synapseSet != otherSynapseSet:
        return False

    return True


  def __ne__(self, other):
    """ Non-equality operator for Connections instances.
    Checks if two instances are not functionally identical
    (might have different internal state).

    @param other (Connections) Connections instance to compare to
    """
    return not self.__eq__(other)


  def _validateCell(self, cell):
    """ Raises an error if cell index is invalid.

    @param cell (int) Cell index
    """
    if cell >= self.numCells or cell < 0:
      raise IndexError("Invalid cell")


  def _validateSegment(self, segment):
    """ Raises an error if segment index is invalid.

    @param segment (int) Segment index
    """
    if not segment in self._segments:
      raise IndexError("Invalid segment")
