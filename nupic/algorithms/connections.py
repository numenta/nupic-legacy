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

from collections import defaultdict, namedtuple



class Connections(object):
  """
  Class to hold data representing the connectivity of a collection of cells.
  """

  SynapseData = namedtuple("SynapseData", ["segment",
                                           "presynapticCell",
                                           "permanence"])

  def __init__(self, numCells):
    """
    @param numCells (int) Number of cells in collection
    """

    # Save member variables
    self.numCells = numCells

    # Mappings
    self._segments = dict()
    self._synapses = dict()

    # Indexes into the mappings (for performance)
    self._segmentsForCell = dict()
    self._synapsesForSegment = dict()
    self._synapsesForPresynapticCell = defaultdict(dict)

    # Index of the next segment to be created
    self._nextSegmentIdx = 0
    # Index of the next synapse to be created
    self._nextSynapseIdx = 0


  def cellForSegment(self, segment):
    """
    Returns the cell that a segment belongs to.

    @param segment (int) Segment index

    @return (int) Cell index
    """
    return self._segments[segment]


  def segmentsForCell(self, cell):
    """
    Returns the segments that belong to a cell.

    @param cell (int) Cell index

    @return (set) Segment indices
    """
    self._validateCell(cell)

    if not cell in self._segmentsForCell:
      return set()

    return self._segmentsForCell[cell]


  def dataForSynapse(self, synapse):
    """
    Returns the data for a synapse.

    @param synapse (int) Synapse index

    @return (SynapseData) Synapse data
    """
    self._validateSynapse(synapse)

    return self._synapses[synapse]


  def synapsesForSegment(self, segment):
    """
    Returns the synapses on a segment.

    @param segment (int) Segment index

    @return (set) Synapse indices
    """
    self._validateSegment(segment)

    if not segment in self._synapsesForSegment:
      return set()

    return self._synapsesForSegment[segment]


  def synapsesForPresynapticCell(self, presynapticCell):
    """
    Returns the synapses for the source cell that they synapse on.

    @param presynapticCell (int) Source cell index

    @return (set) Synapse indices
    """
    return self._synapsesForPresynapticCell[presynapticCell]


  def createSegment(self, cell):
    """
    Adds a new segment on a cell.

    @param cell (int) Cell index

    @return (int) New segment index
    """
    self._validateCell(cell)

    # Add data
    segment = self._nextSegmentIdx
    self._segments[segment] = cell
    self._nextSegmentIdx += 1

    # Update indexes
    if not cell in self._segmentsForCell:
      self._segmentsForCell[cell] = set()
    self._segmentsForCell[cell].add(segment)

    return segment


  def destroySegment(self, segment):
    """
    Destroys a segment.

    @param segment (int) Segment index
    """
    synapses = set(self.synapsesForSegment(segment))
    for synapse in synapses:
      self.destroySynapse(synapse)

    cell = self._segments[segment]
    del self._segments[segment]

    # Update indexes
    self._segmentsForCell[cell].remove(segment)


  def createSynapse(self, segment, presynapticCell, permanence):
    """
    Creates a new synapse on a segment.

    @param segment         (int)   Segment index
    @param presynapticCell (int)   Source cell index
    @param permanence      (float) Initial permanence

    @return (int) Synapse index
    """
    self._validateSegment(segment)
    self._validatePermanence(permanence)

    # Add data
    synapse = self._nextSynapseIdx
    synapseData = self.SynapseData(segment, presynapticCell, permanence)
    self._synapses[synapse] = synapseData
    self._nextSynapseIdx += 1

    # Update indexes
    if not len(self.synapsesForSegment(segment)):
      self._synapsesForSegment[segment] = set()
    self._synapsesForSegment[segment].add(synapse)

    self._synapsesForPresynapticCell[presynapticCell][synapse] = synapseData

    return synapse


  def destroySynapse(self, synapse):
    """
    Destroys a synapse.

    @param synapse (int) Synapse index
    """
    data = self._synapses[synapse]
    del self._synapses[synapse]

    # Update indexes
    self._synapsesForSegment[data.segment].remove(synapse)
    del self._synapsesForPresynapticCell[data.presynapticCell][synapse]


  def updateSynapsePermanence(self, synapse, permanence):
    """
    Updates the permanence for a synapse.

    @param synapse    (int)   Synapse index
    @param permanence (float) New permanence
    """
    self._validatePermanence(permanence)

    data = self._synapses[synapse]
    newData = self.SynapseData(data.segment,
                               data.presynapticCell,
                               permanence)
    self._synapses[synapse] = newData

    # Update indexes
    self._synapsesForPresynapticCell[newData.presynapticCell][synapse] = newData


  def numSegments(self):
    """
    Returns the number of segments.
    """
    return len(self._segments)


  def numSynapses(self):
    """
    Returns the number of synapses.
    """
    return len(self._synapses)


  def _validateCell(self, cell):
    """
    Raises an error if cell index is invalid.

    @param cell (int) Cell index
    """
    if cell >= self.numCells or cell < 0:
      raise IndexError("Invalid cell")


  def _validateSegment(self, segment):
    """
    Raises an error if segment index is invalid.

    @param segment (int) Segment index
    """
    if not segment in self._segments:
      raise IndexError("Invalid segment")


  def _validateSynapse(self, synapse):
    """
    Raises an error if synapse index is invalid.

    @param synapse (int) Synapse index
    """
    if not synapse in self._synapses:
      raise IndexError("Invalid synapse")


  @staticmethod
  def _validatePermanence(permanence):
    """
    Raises an error if permanence is invalid.

    @param permanence (float) Permanence
    """
    if permanence < 0 or permanence > 1:
      raise ValueError("Invalid permanence")

