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

from operator import mul

from nupic.bindings.math import Random



class TM(object):
  """
  Class implementing the Temporal Memory algorithm.
  """

  def __init__(self,
               columnDimensions=[2048],
               cellsPerColumn=32,
               activationThreshold=13,
               learningRadius=2048,
               initialPermanence=0.21,
               connectedPermanence=0.50,
               minThreshold=10,
               newSynapseCount=20,
               permanenceIncrement=0.10,
               permanenceDecrement=0.10,
               seed=42):
    """
    @param columnDimensions    (list)   Dimensions of the column space

    @param cellsPerColumn      (int)    Number of cells per column

    @param activationThreshold (int)    Minimum number of synapses active on
                                        a segment to make the segment active.

    @param learningRadius      (int)    Radius around cell from which it can
                                        sample to form distal dendrite
                                        connections.

    @param initialPermanence   (float)  Initial permanence of a new synapse.

    @param connectedPermanence (float)  Minimum permanence of a synapse to
                                        make it connected.

    @param minThreshold        (int)    Minimum number of synapses active on
                                        a segment for it to be selected as the
                                        best matching cell in a bursing column.

    @param newSynapseCount     (int)    The maximum number of synapses added
                                        to a segment during learning.

    @param permanenceIncrement (float)  Amount by which permanences of synapses
                                        are incremented during learning.

    @param permanenceDecrement (float)  Amount by which permanences of synapses
                                        are decremented during learning.

    @param seed                (int)    Seed for the random number generator.
    """
    # TODO: Validate all parameters (and add validation tests)

    # Initialize member variables
    self.connections = Connections(columnDimensions, cellsPerColumn)
    self._random = Random(seed)

    # Save member variables
    self.activationThreshold = activationThreshold
    self.learningRadius = learningRadius
    self.initialPermanence = initialPermanence
    self.connectedPermanence = connectedPermanence
    self.minThreshold = minThreshold
    self.newSynapseCount = newSynapseCount
    self.permanenceIncrement = permanenceIncrement
    self.permanenceDecrement = permanenceDecrement


  # Phases

  def activateCorrectlyPredictiveCells(self,
                                       prevPredictiveCells,
                                       activeColumns):
    """
    Phase 1: Activate the correctly predictive cells.

    Pseudocode:

      - for each prev predictive cell
        - if in active column
          - mark it as active
          - mark it as winner cell
          - mark column as predicted

    @param prevPredictiveCells (set) Indices of predictive cells in `t-1`
    @param activeColumns       (set) Indices of active columns in `t`

    @return (tuple) Contains:
                      activeCells      (set)
                      winnerCells      (set)
                      predictedColumns (set)
    """
    activeCells      = set()
    winnerCells      = set()
    predictedColumns = set()

    for cell in prevPredictiveCells:
      column = self.connections.columnForCell(cell)

      if column in activeColumns:
        activeCells.add(cell)
        winnerCells.add(cell)
        predictedColumns.add(column)

    return (activeCells, winnerCells, predictedColumns)


  def burstColumns(self,
                   activeColumns,
                   predictedColumns,
                   prevActiveCells,
                   connections):
    """
    Phase 2: Burst unpredicted columns.

    Pseudocode:

      - for each unpredicted active column
        - mark all cells as active
        - mark the best matching cell as winner cell
          - (learning)
            - if it has matching segment
              - mark the segment as learning
            - else
              - add a segment to it
              - mark the segment as learning

    @param activeColumns    (set)        Indices of active columns in `t`
    @param predictedColumns (set)        Indices of predicted columns in `t`
    @param prevActiveCells  (set)        Indices of active cells in `t-1`
    @param connections      (Connection) Connectivity of layer

    @return (tuple) Contains:
                      activeCells      (set)
                      winnerCells      (set)
                      learningSegments (set)
    """
    activeCells      = set()
    winnerCells      = set()
    learningSegments = set()

    return (activeCells, winnerCells, learningSegments)


  # Helper functions

  def getActiveSynapses(self,
                        segment,
                        activeCells,
                        permanenceThreshold,
                        connections):
    """
    Returns the synapses on a segment that are active due to lateral input
    from active cells.

    @param segment             (int)        Segment index
    @param activeCells         (set)        Indices of active cells
    @param permanenceThreshold (float)      Minimum threshold for permanence
                                            for synapse to be connected
    @param connections         (Connection) Connectivity of layer

    @return (set) Indices of active synapses on segment
    """
    activeSynapses = set()

    for synapse in connections.synapsesForSegment(segment):
      (_, sourceCell, permanence) = connections.dataForSynapse(synapse)
      if (sourceCell in activeCells) and permanence >= permanenceThreshold:
        activeSynapses.add(synapse)

    return activeSynapses



class Connections(object):
  """
  Class to hold data representing the connectivity of a layer of cells,
  that the TM operates on.
  """

  def __init__(self,
               columnDimensions,
               cellsPerColumn):
    """
    @param columnDimensions (list) Dimensions of the column space
    @param cellsPerColumn   (int)  Number of cells per column
    """
    # Error checking
    if not len(columnDimensions):
      raise ValueError("Number of column dimensions must be greater than 0")

    if not cellsPerColumn > 0:
      raise ValueError("Number of cells per column must be greater than 0")

    # Save member variables
    self.columnDimensions = columnDimensions
    self.cellsPerColumn = cellsPerColumn

    # Mappings
    self._segments = dict()
    self._synapses = dict()

    # Indexes into the mappings (for performance)
    self._segmentsForCell = dict()
    self._synapsesForSegment = dict()
    self._synapsesForSourceCell = dict()

    # Index of the next segment to be created
    self._nextSegmentIdx = 0
    # Index of the next synapse to be created
    self._nextSynapseIdx = 0


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

    @return (set) Cell indices
    """
    self._validateColumn(column)

    start = self.cellsPerColumn * column
    end = start + self.cellsPerColumn
    return {cell for cell in range(start, end)}


  def cellForSegment(self, segment):
    """
    Returns the cell that a segment belongs to.

    @param segment (int) Segment index

    @return (int) Cell index
    """
    self._validateSegment(segment)

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

    @return (tuple) Contains:
                      segment    (int)
                      sourceCell (int)
                      permanence (float)
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


  def synapsesForSourceCell(self, sourceCell):
    """
    Returns the synapses for the source cell that they synapse on.

    @param sourceCell (int) Source cell index

    @return (set) Synapse indices
    """
    self._validateCell(sourceCell)

    if not sourceCell in self._synapsesForSourceCell:
      return set()

    return self._synapsesForSourceCell[sourceCell]


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
    
    if not len(self.segmentsForCell(cell)):
      self._segmentsForCell[cell] = set()
    self._segmentsForCell[cell].add(segment)

    return segment


  def createSynapse(self, segment, sourceCell, permanence):
    """
    Creates a new synapse on a segment.

    @param segment    (int)   Segment index
    @param sourceCell (int)   Source cell index
    @param permanence (float) Initial permanence
    """
    self._validateSegment(segment)
    self._validateCell(sourceCell)
    self._validatePermanence(permanence)

    # Add data
    
    synapse = self._nextSynapseIdx
    self._synapses[synapse] = (segment, sourceCell, permanence)
    self._nextSynapseIdx += 1

    # Update indexes

    if not len(self.synapsesForSegment(segment)):
      self._synapsesForSegment[segment] = set()
    self._synapsesForSegment[segment].add(synapse)

    if not len(self.synapsesForSourceCell(sourceCell)):
      self._synapsesForSourceCell[sourceCell] = set()
    self._synapsesForSourceCell[sourceCell].add(synapse)

    return synapse


  def updateSynapsePermanence(self, synapse, permanence):
    """
    Updates the permanence for a synapse.

    @param synapse    (int)   Synapse index
    @param permanence (float) New permanence
    """
    self._validateSynapse(synapse)
    self._validatePermanence(permanence)

    data = self._synapses[synapse]
    self._synapses[synapse] = data[:-1] + (permanence,)


  # Helper functions

  def _validateColumn(self, column):
    """
    Raises an error if column index is invalid.

    @param column (int) Column index
    """
    if column >= self._numberOfColumns() or column < 0:
      raise IndexError("Invalid column")


  def _validateCell(self, cell):
    """
    Raises an error if cell index is invalid.

    @param cell (int) Cell index
    """
    if cell >= self._numberOfCells() or cell < 0:
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


  def _validatePermanence(self, permanence):
    """
    Raises an error if permanence is invalid.

    @param permanence (float) Permanence
    """
    if permanence < 0 or permanence > 1:
      raise ValueError("Invalid permanence")


  def _numberOfColumns(self):
    """
    Returns the number of columns in this layer.

    @return (int) Number of columns
    """
    return reduce(mul, self.columnDimensions, 1)


  def _numberOfCells(self):
    return self._numberOfColumns() * self.cellsPerColumn
