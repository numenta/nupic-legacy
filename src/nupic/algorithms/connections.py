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

from bisect import bisect_left
from collections import defaultdict

from nupic.serializable import Serializable

EPSILON = 0.00001 # constant error threshold to check equality of permanences to
                  # other floats



class Segment(object):
  """
  Class containing minimal information to identify a unique segment.
  
  :param cell: (int) Index of the cell that this segment is on.

  :param flatIdx: (int) The segment's flattened list index.

  :param ordinal: (long) Used to sort segments. The sort order needs to be 
         consistent between implementations so that tie-breaking is consistent 
         when finding the best matching segment.
  """

  __slots__ = ["cell", "flatIdx", "_synapses", "_ordinal"]

  def __init__(self, cell, flatIdx, ordinal):
    self.cell = cell
    self.flatIdx = flatIdx
    self._synapses = set()
    self._ordinal = ordinal


  def __eq__(self, other):
    """ Explicitly implement this for unit testing. The flatIdx is not designed
    to be consistent after serialize / deserialize, and the synapses might not
    enumerate in the same order.
    """

    return (self.cell == other.cell and
            (sorted(self._synapses, key=lambda x: x._ordinal) ==
             sorted(other._synapses, key=lambda x: x._ordinal)))



class Synapse(object):
  """
  Class containing minimal information to identify a unique synapse.

  :param segment: (Object) Segment object that the synapse is synapsed to.

  :param presynapticCell: (int) The index of the presynaptic cell of the 
         synapse.

  :param permanence: (float) Permanence of the synapse from 0.0 to 1.0.

  :param ordinal: (long) Used to sort synapses. The sort order needs to be 
         consistent between implementations so that tie-breaking is consistent 
         when finding the min permanence synapse.
  """

  __slots__ = ["segment", "presynapticCell", "permanence", "_ordinal"]

  def __init__(self, segment, presynapticCell, permanence, ordinal):
    self.segment = segment
    self.presynapticCell = presynapticCell
    self.permanence = permanence
    self._ordinal = ordinal


  def __eq__(self, other):
    """ Explicitly implement this for unit testing. Allow floating point
    differences for synapse permanence.

    """
    return (self.segment.cell == other.segment.cell and
            self.presynapticCell == other.presynapticCell and
            abs(self.permanence - other.permanence) < EPSILON)



class CellData(object):
  # Class containing cell information. Internal to the Connections

  __slots__ = ["_segments"]

  def __init__(self):
    self._segments = []



def binSearch(arr, val):
  """ 
  Function for running binary search on a sorted list.

  :param arr: (list) a sorted list of integers to search
  :param val: (int)  a integer to search for in the sorted array
  :returns: (int) the index of the element if it is found and -1 otherwise.
  """
  i = bisect_left(arr, val)
  if i != len(arr) and arr[i] == val:
    return i
  return -1



class Connections(Serializable):
  """ 
  Class to hold data representing the connectivity of a collection of cells. 
  
  :param numCells: (int) Number of cells in collection. 
  """

  def __init__(self, numCells):

    # Save member variables
    self.numCells = numCells

    self._cells = [CellData() for _ in xrange(numCells)]
    self._synapsesForPresynapticCell = defaultdict(set)
    self._segmentForFlatIdx = []

    self._numSynapses = 0
    self._freeFlatIdxs = []
    self._nextFlatIdx = 0

    # Whenever creating a new Synapse or Segment, give it a unique ordinal.
    # These can be used to sort synapses or segments by age.
    self._nextSynapseOrdinal = long(0)
    self._nextSegmentOrdinal = long(0)


  def segmentsForCell(self, cell):
    """ 
    Returns the segments that belong to a cell.

    :param cell: (int) Cell index
    :returns: (list) Segment objects representing segments on the given cell.
    """

    return self._cells[cell]._segments


  def synapsesForSegment(self, segment):
    """ 
    Returns the synapses on a segment.

    :param segment: (int) Segment index
    :returns: (set) Synapse objects representing synapses on the given segment.
    """

    return segment._synapses


  def dataForSynapse(self, synapse):
    """ 
    Returns the data for a synapse.

    .. note:: This method exists to match the interface of the C++ Connections. 
       This allows tests and tools to inspect the connections using a common 
       interface.

    :param synapse: (:class:`Synapse`)
    :returns: Synapse data
    """
    return synapse


  def dataForSegment(self, segment):
    """ 
    Returns the data for a segment.

    .. note:: This method exists to match the interface of the C++ Connections. 
       This allows tests and tools to inspect the connections using a common 
       interface.

    :param segment (:class:`Segment`)
    :returns: segment data
    """
    return segment


  def getSegment(self, cell, idx):
    """ 
    Returns a :class:`Segment` object of the specified segment using data from 
    the ``self._cells`` array.

    :param cell: (int) cell index
    :param idx:  (int) segment index on a cell
    :returns: (:class:`Segment`) Segment object with index idx on the specified cell
    """

    return self._cells[cell]._segments[idx]


  def segmentForFlatIdx(self, flatIdx):
    """ 
    Get the segment with the specified flatIdx.

    :param flatIdx: (int) The segment's flattened list index.

    :returns: (:class:`Segment`)
    """
    return self._segmentForFlatIdx[flatIdx]


  def segmentFlatListLength(self):
    """ 
    Get the needed length for a list to hold a value for every segment's 
    flatIdx.

    :returns: (int) Required list length
    """
    return self._nextFlatIdx


  def synapsesForPresynapticCell(self, presynapticCell):
    """ 
    Returns the synapses for the source cell that they synapse on.

    :param presynapticCell: (int) Source cell index

    :returns: (set) :class:`Synapse` objects
    """
    return self._synapsesForPresynapticCell[presynapticCell]


  def createSegment(self, cell):
    """ 
    Adds a new segment on a cell.

    :param cell: (int) Cell index
    :returns: (int) New segment index
    """
    cellData = self._cells[cell]

    if len(self._freeFlatIdxs) > 0:
      flatIdx = self._freeFlatIdxs.pop()
    else:
      flatIdx = self._nextFlatIdx
      self._segmentForFlatIdx.append(None)
      self._nextFlatIdx += 1

    ordinal = self._nextSegmentOrdinal
    self._nextSegmentOrdinal += 1

    segment = Segment(cell, flatIdx, ordinal)
    cellData._segments.append(segment)
    self._segmentForFlatIdx[flatIdx] = segment

    return segment


  def destroySegment(self, segment):
    """
    Destroys a segment.

    :param segment: (:class:`Segment`) representing the segment to be destroyed.
    """
    # Remove the synapses from all data structures outside this Segment.
    for synapse in segment._synapses:
      self._removeSynapseFromPresynapticMap(synapse)
    self._numSynapses -= len(segment._synapses)

    # Remove the segment from the cell's list.
    segments = self._cells[segment.cell]._segments
    i = segments.index(segment)
    del segments[i]

    # Free the flatIdx and remove the final reference so the Segment can be
    # garbage-collected.
    self._freeFlatIdxs.append(segment.flatIdx)
    self._segmentForFlatIdx[segment.flatIdx] = None


  def createSynapse(self, segment, presynapticCell, permanence):
    """ 
    Creates a new synapse on a segment.

    :param segment: (:class:`Segment`) Segment object for synapse to be synapsed 
           to.
    :param presynapticCell: (int) Source cell index.
    :param permanence: (float) Initial permanence of synapse.
    :returns: (:class:`Synapse`) created synapse
    """
    idx = len(segment._synapses)
    synapse = Synapse(segment, presynapticCell, permanence,
                      self._nextSynapseOrdinal)
    self._nextSynapseOrdinal += 1
    segment._synapses.add(synapse)

    self._synapsesForPresynapticCell[presynapticCell].add(synapse)

    self._numSynapses += 1

    return synapse


  def _removeSynapseFromPresynapticMap(self, synapse):
    inputSynapses = self._synapsesForPresynapticCell[synapse.presynapticCell]

    inputSynapses.remove(synapse)

    if len(inputSynapses) == 0:
      del self._synapsesForPresynapticCell[synapse.presynapticCell]


  def destroySynapse(self, synapse):
    """
    Destroys a synapse.

    :param synapse: (:class:`Synapse`) synapse to destroy
    """

    self._numSynapses -= 1

    self._removeSynapseFromPresynapticMap(synapse)

    synapse.segment._synapses.remove(synapse)


  def updateSynapsePermanence(self, synapse, permanence):
    """ 
    Updates the permanence for a synapse.
    
    :param synapse: (class:`Synapse`) to be updated.
    :param permanence: (float) New permanence.
    """

    synapse.permanence = permanence


  def computeActivity(self, activePresynapticCells, connectedPermanence):
    """ 
    Compute each segment's number of active synapses for a given input.
    In the returned lists, a segment's active synapse count is stored at index
    ``segment.flatIdx``.

    :param activePresynapticCells: (iter) Active cells.
    :param connectedPermanence: (float) Permanence threshold for a synapse to be 
           considered connected

    :returns: (tuple) (``numActiveConnectedSynapsesForSegment`` [list],
                      ``numActivePotentialSynapsesForSegment`` [list])
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


  def numSegments(self, cell=None):
    """ 
    Returns the number of segments.

    :param cell: (int) Optional parameter to get the number of segments on a 
           cell.
    :returns: (int) Number of segments on all cells if cell is not specified, or 
              on a specific specified cell
    """
    if cell is not None:
      return len(self._cells[cell]._segments)

    return self._nextFlatIdx - len(self._freeFlatIdxs)


  def numSynapses(self, segment=None):
    """ 
    Returns the number of Synapses.

    :param segment: (:class:`Segment`) Optional parameter to get the number of 
           synapses on a segment.

    :returns: (int) Number of synapses on all segments if segment is not 
              specified, or on a specified segment.
    """
    if segment is not None:
      return len(segment._synapses)
    return self._numSynapses


  def segmentPositionSortKey(self, segment):
    """ 
    Return a numeric key for sorting this segment. This can be used with the 
    python built-in ``sorted()`` function.

    :param segment: (:class:`Segment`) within this :class:`Connections` 
           instance.
    :returns: (float) A numeric key for sorting.
    """
    return segment.cell + (segment._ordinal / float(self._nextSegmentOrdinal))


  def write(self, proto):
    """ 
    Writes serialized data to proto object.

    :param proto: (DynamicStructBuilder) Proto object
    """
    protoCells = proto.init('cells', self.numCells)

    for i in xrange(self.numCells):
      segments = self._cells[i]._segments
      protoSegments = protoCells[i].init('segments', len(segments))

      for j, segment in enumerate(segments):
        synapses = segment._synapses
        protoSynapses = protoSegments[j].init('synapses', len(synapses))

        for k, synapse in enumerate(sorted(synapses, key=lambda s: s._ordinal)):
          protoSynapses[k].presynapticCell = synapse.presynapticCell
          protoSynapses[k].permanence = synapse.permanence


  @classmethod
  def read(cls, proto):
    """ 
    Reads deserialized data from proto object

    :param proto: (DynamicStructBuilder) Proto object

    :returns: (:class:`Connections`) instance
    """
    #pylint: disable=W0212
    protoCells = proto.cells
    connections = cls(len(protoCells))

    for cellIdx, protoCell in enumerate(protoCells):
      protoCell = protoCells[cellIdx]
      protoSegments = protoCell.segments
      connections._cells[cellIdx] = CellData()
      segments = connections._cells[cellIdx]._segments

      for segmentIdx, protoSegment in enumerate(protoSegments):
        segment = Segment(cellIdx, connections._nextFlatIdx,
                          connections._nextSegmentOrdinal)

        segments.append(segment)
        connections._segmentForFlatIdx.append(segment)
        connections._nextFlatIdx += 1
        connections._nextSegmentOrdinal += 1

        synapses = segment._synapses
        protoSynapses = protoSegment.synapses

        for synapseIdx, protoSynapse in enumerate(protoSynapses):
          presynapticCell = protoSynapse.presynapticCell
          synapse = Synapse(segment, presynapticCell, protoSynapse.permanence,
                            ordinal=connections._nextSynapseOrdinal)
          connections._nextSynapseOrdinal += 1
          synapses.add(synapse)
          connections._synapsesForPresynapticCell[presynapticCell].add(synapse)

          connections._numSynapses += 1

    #pylint: enable=W0212
    return connections


  def __eq__(self, other):
    """ Equality operator for Connections instances.
    Checks if two instances are functionally identical

    :param other: (:class:`Connections`) Connections instance to compare to
    """
    #pylint: disable=W0212
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

        if len(synapses) != len(otherSynapses):
          return False

        for synapse in synapses:
          found = False
          for candidate in otherSynapses:
            if synapse == candidate:
              found = True
              break

          if not found:
            return False

    if (len(self._synapsesForPresynapticCell) !=
        len(self._synapsesForPresynapticCell)):
      return False

    for i in self._synapsesForPresynapticCell.keys():
      synapses = self._synapsesForPresynapticCell[i]
      otherSynapses = other._synapsesForPresynapticCell[i]
      if len(synapses) != len(otherSynapses):
        return False

      for synapse in synapses:
        found = False
        for candidate in otherSynapses:
          if synapse == candidate:
            found = True
            break

        if not found:
          return False

    if self._numSynapses != other._numSynapses:
      return False

    #pylint: enable=W0212
    return True


  def __ne__(self, other):
    """ 
    Non-equality operator for Connections instances.
    Checks if two instances are not functionally identical

    :param other: (:class:`Connections`) Connections instance to compare to
    """
    return not self.__eq__(other)
