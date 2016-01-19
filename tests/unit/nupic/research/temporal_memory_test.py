#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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
TODO: Mock out all function calls.
TODO: Make default test TM instance simpler, with 4 cells per column.
"""

import tempfile
import unittest

from nupic.data.generators.pattern_machine import PatternMachine
from nupic.data.generators.sequence_machine import SequenceMachine
from nupic.research.temporal_memory import TemporalMemory

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.proto import TemporalMemoryProto_capnp



class TemporalMemoryTest(unittest.TestCase):


  def setUp(self):
    self.tm = TemporalMemory()


  def testInitInvalidParams(self):
    # Invalid columnDimensions
    kwargs = {"columnDimensions": [], "cellsPerColumn": 32}
    self.assertRaises(ValueError, TemporalMemory, **kwargs)

    # Invalid cellsPerColumn
    kwargs = {"columnDimensions": [2048], "cellsPerColumn": 0}
    self.assertRaises(ValueError, TemporalMemory, **kwargs)
    kwargs = {"columnDimensions": [2048], "cellsPerColumn": -10}
    self.assertRaises(ValueError, TemporalMemory, **kwargs)


  def testActivateCorrectlyPredictiveCells(self):
    tm = self.tm

    prevPredictiveCells = set([0, 237, 1026, 26337, 26339, 55536])
    activeColumns = set([32, 47, 823])
    prevMatchingCells = set()

    (activeCells,
    winnerCells,
    predictedColumns,
    predictedInactiveCells) = tm.activateCorrectlyPredictiveCells(prevPredictiveCells,
                                                                  prevMatchingCells,
                                                                  activeColumns)

    self.assertEqual(activeCells, set([1026, 26337, 26339]))
    self.assertEqual(winnerCells, set([1026, 26337, 26339]))
    self.assertEqual(predictedColumns, set([32, 823]))
    self.assertEqual(predictedInactiveCells, set())


  def testActivateCorrectlyPredictiveCellsEmpty(self):
    tm = self.tm

    # No previous predictive cells, no active columns
    prevPredictiveCells = set()
    activeColumns      = set()
    prevMatchingCells = set()

    (activeCells,
    winnerCells,
    predictedColumns,
    predictedInactiveCells) = tm.activateCorrectlyPredictiveCells(prevPredictiveCells,
                                                                  prevMatchingCells,
                                                                  activeColumns)

    self.assertEqual(activeCells,      set())
    self.assertEqual(winnerCells,      set())
    self.assertEqual(predictedColumns, set())
    self.assertEqual(predictedInactiveCells, set())

    # No previous predictive cells, with active columns

    prevPredictiveCells = set()
    activeColumns = set([32, 47, 823])
    prevMatchingCells = set()

    (activeCells,
    winnerCells,
    predictedColumns,
    predictedInactiveCells) = tm.activateCorrectlyPredictiveCells(prevPredictiveCells,
                                                                  prevMatchingCells,
                                                                  activeColumns)

    self.assertEqual(activeCells,      set())
    self.assertEqual(winnerCells,      set())
    self.assertEqual(predictedColumns, set())
    self.assertEqual(predictedInactiveCells, set())

    # No active columns, with previously predictive cells

    prevPredictiveCells = set([0, 237, 1026, 26337, 26339, 55536])
    activeColumns = set()
    prevMatchingCells = set()

    (activeCells,
    winnerCells,
    predictedColumns,
    predictedInactiveCells) = tm.activateCorrectlyPredictiveCells(prevPredictiveCells,
                                                                  prevMatchingCells,
                                                                  activeColumns)

    self.assertEqual(activeCells,      set())
    self.assertEqual(winnerCells,      set())
    self.assertEqual(predictedColumns, set())
    self.assertEqual(predictedInactiveCells, set())

  def testActivateCorrectlyPredictiveCellsOrphan(self):
    tm = self.tm
    tm.predictedSegmentDecrement = 0.001
    prevPredictiveCells = set([])
    activeColumns = set([32, 47, 823])
    prevMatchingCells = set([32, 47])

    (activeCells,
    winnerCells,
    predictedColumns,
    predictedInactiveCells) = tm.activateCorrectlyPredictiveCells(prevPredictiveCells,
                                                                  prevMatchingCells,
                                                                  activeColumns)

    self.assertEqual(activeCells, set([]))
    self.assertEqual(winnerCells, set([]))
    self.assertEqual(predictedColumns, set([]))
    self.assertEqual(predictedInactiveCells, set([32,47]))

  def testBurstColumns(self):
    tm = TemporalMemory(
      cellsPerColumn=4,
      connectedPermanence=0.50,
      minThreshold=1,
      seed=42
    )

    connections = tm.connections
    connections.createSegment(0)
    connections.createSynapse(0, 23, 0.6)
    connections.createSynapse(0, 37, 0.4)
    connections.createSynapse(0, 477, 0.9)

    connections.createSegment(0)
    connections.createSynapse(1, 49, 0.9)
    connections.createSynapse(1, 3, 0.8)

    connections.createSegment(1)
    connections.createSynapse(2, 733, 0.7)

    connections.createSegment(108)
    connections.createSynapse(3, 486, 0.9)

    activeColumns = set([0, 1, 26])
    predictedColumns = set([26])
    prevActiveCells = set([23, 37, 49, 733])
    prevWinnerCells = set([23, 37, 49, 733])

    (activeCells,
     winnerCells,
     learningSegments) = tm.burstColumns(activeColumns,
                                         predictedColumns,
                                         prevActiveCells,
                                         prevWinnerCells,
                                         connections)

    self.assertEqual(activeCells, set([0, 1, 2, 3, 4, 5, 6, 7]))
    randomWinner = 4
    self.assertEqual(winnerCells, set([0, randomWinner]))  # 4 is randomly chosen cell
    self.assertEqual(learningSegments, set([0, 4]))  # 4 is new segment created

    # Check that new segment was added to winner cell (6) in column 1
    self.assertEqual(connections.segmentsForCell(randomWinner), set([4]))


  def testBurstColumnsEmpty(self):
    tm = self.tm

    activeColumns    = set()
    predictedColumns = set()
    prevActiveCells = set()
    prevWinnerCells = set()
    connections = tm.connections

    (activeCells,
     winnerCells,
     learningSegments) = tm.burstColumns(activeColumns,
                                         predictedColumns,
                                         prevActiveCells,
                                         prevWinnerCells,
                                         connections)

    self.assertEqual(activeCells,      set())
    self.assertEqual(winnerCells,      set())
    self.assertEqual(learningSegments, set())


  def testLearnOnSegments(self):
    tm = TemporalMemory(maxNewSynapseCount=2)

    connections = tm.connections
    connections.createSegment(0)
    connections.createSynapse(0, 23, 0.6)
    connections.createSynapse(0, 37, 0.4)
    connections.createSynapse(0, 477, 0.9)

    connections.createSegment(1)
    connections.createSynapse(1, 733, 0.7)

    connections.createSegment(8)
    connections.createSynapse(2, 486, 0.9)

    connections.createSegment(100)

    prevActiveSegments = set([0, 2])
    learningSegments = set([1, 3])
    prevActiveCells = set([23, 37, 733])
    winnerCells = set([0])
    prevWinnerCells = set([10, 11, 12, 13, 14])
    predictedInactiveCells = set()
    prevMatchingSegments = set()
    tm.learnOnSegments(prevActiveSegments,
                       learningSegments,
                       prevActiveCells,
                       winnerCells,
                       prevWinnerCells,
                       connections,
                       predictedInactiveCells,
                       prevMatchingSegments)

    # Check segment 0
    synapseData = connections.dataForSynapse(0)
    self.assertAlmostEqual(synapseData.permanence, 0.7)

    synapseData = connections.dataForSynapse(1)
    self.assertAlmostEqual(synapseData.permanence, 0.5)

    synapseData = connections.dataForSynapse(2)
    self.assertAlmostEqual(synapseData.permanence, 0.8)

    # Check segment 1
    synapseData = connections.dataForSynapse(3)
    self.assertAlmostEqual(synapseData.permanence, 0.8)

    self.assertEqual(len(connections.synapsesForSegment(1)), 2)

    # Check segment 2
    synapseData = connections.dataForSynapse(4)
    self.assertAlmostEqual(synapseData.permanence, 0.9)

    self.assertEqual(len(connections.synapsesForSegment(2)), 1)

    # Check segment 3
    self.assertEqual(len(connections.synapsesForSegment(3)), 2)


  def testComputePredictiveCells(self):
    tm = TemporalMemory(activationThreshold=2, minThreshold=2, predictedSegmentDecrement=0.004)

    connections = tm.connections
    connections.createSegment(0)
    connections.createSynapse(0, 23, 0.6)
    connections.createSynapse(0, 37, 0.5)
    connections.createSynapse(0, 477, 0.9)

    connections.createSegment(1)
    connections.createSynapse(1, 733, 0.7)
    connections.createSynapse(1, 733, 0.4)

    connections.createSegment(1)
    connections.createSynapse(2, 974, 0.9)

    connections.createSegment(8)
    connections.createSynapse(3, 486, 0.9)

    connections.createSegment(100)

    activeCells = set([23, 37, 733, 974])

    (activeSegments,
     predictiveCells,
     matchingSegments,
     matchingCells) = tm.computePredictiveCells(activeCells, connections)
    self.assertEqual(activeSegments, set([0]))
    self.assertEqual(predictiveCells, set([0]))
    self.assertEqual(matchingSegments, set([0,1]))
    self.assertEqual(matchingCells, set([0,1]))


  def testBestMatchingCell(self):
    tm = TemporalMemory(
      connectedPermanence=0.50,
      minThreshold=1,
      seed=42
    )

    connections = tm.connections
    connections.createSegment(0)
    connections.createSynapse(0, 23, 0.6)
    connections.createSynapse(0, 37, 0.4)
    connections.createSynapse(0, 477, 0.9)

    connections.createSegment(0)
    connections.createSynapse(1, 49, 0.9)
    connections.createSynapse(1, 3, 0.8)

    connections.createSegment(1)
    connections.createSynapse(2, 733, 0.7)

    connections.createSegment(108)
    connections.createSynapse(3, 486, 0.9)

    activeCells = set([23, 37, 49, 733])

    self.assertEqual(tm.bestMatchingCell(tm.cellsForColumn(0),
                                         activeCells,
                                         connections),
                     (0, 0))

    self.assertEqual(tm.bestMatchingCell(tm.cellsForColumn(3),  # column containing cell 108
                                         activeCells,
                                         connections),
                     (103, None))  # Random cell from column

    self.assertEqual(tm.bestMatchingCell(tm.cellsForColumn(999),
                                         activeCells,
                                         connections),
                     (31979, None))  # Random cell from column


  def testBestMatchingCellFewestSegments(self):
    tm = TemporalMemory(
      columnDimensions=[2],
      cellsPerColumn=2,
      connectedPermanence=0.50,
      minThreshold=1,
      seed=42
    )

    connections = tm.connections
    connections.createSegment(0)
    connections.createSynapse(0, 3, 0.3)

    activeSynapsesForSegment = set([])

    for _ in range(100):
      # Never pick cell 0, always pick cell 1
      (cell, _) = tm.bestMatchingCell(tm.cellsForColumn(0),
                                      activeSynapsesForSegment,
                                      connections)
      self.assertEqual(cell, 1)


  def testBestMatchingSegment(self):
    tm = TemporalMemory(
      connectedPermanence=0.50,
      minThreshold=1
    )

    connections = tm.connections
    connections.createSegment(0)
    connections.createSynapse(0, 23, 0.6)
    connections.createSynapse(0, 37, 0.4)
    connections.createSynapse(0, 477, 0.9)

    connections.createSegment(0)
    connections.createSynapse(1, 49, 0.9)
    connections.createSynapse(1, 3, 0.8)

    connections.createSegment(1)
    connections.createSynapse(2, 733, 0.7)

    connections.createSegment(8)
    connections.createSynapse(3, 486, 0.9)

    activeCells = set([23, 37, 49, 733])

    self.assertEqual(tm.bestMatchingSegment(0,
                                            activeCells,
                                            connections),
                     (0, 2))

    self.assertEqual(tm.bestMatchingSegment(1,
                                            activeCells,
                                            connections),
                     (2, 1))

    self.assertEqual(tm.bestMatchingSegment(8,
                                            activeCells,
                                            connections),
                     (None, None))

    self.assertEqual(tm.bestMatchingSegment(100,
                                            activeCells,
                                            connections),
                     (None, None))


  def testLeastUsedCell(self):
    tm = TemporalMemory(
      columnDimensions=[2],
      cellsPerColumn=2,
      seed=42
    )

    connections = tm.connections
    connections.createSegment(0)
    connections.createSynapse(0, 3, 0.3)

    for _ in range(100):
      # Never pick cell 0, always pick cell 1
      self.assertEqual(tm.leastUsedCell(tm.cellsForColumn(0),
                                        connections),
                       1)


  def testAdaptSegment(self):
    tm = self.tm

    connections = tm.connections
    connections.createSegment(0)
    connections.createSynapse(0, 23, 0.6)
    connections.createSynapse(0, 37, 0.4)
    connections.createSynapse(0, 477, 0.9)

    tm.adaptSegment(0, set([0, 1]), connections,
                    tm.permanenceIncrement,
                    tm.permanenceDecrement)

    synapseData = connections.dataForSynapse(0)
    self.assertAlmostEqual(synapseData.permanence, 0.7)

    synapseData = connections.dataForSynapse(1)
    self.assertAlmostEqual(synapseData.permanence, 0.5)

    synapseData = connections.dataForSynapse(2)
    self.assertAlmostEqual(synapseData.permanence, 0.8)


  def testAdaptSegmentToMax(self):
    tm = self.tm

    connections = tm.connections
    connections.createSegment(0)
    connections.createSynapse(0, 23, 0.9)

    tm.adaptSegment(0, set([0]), connections,
                    tm.permanenceIncrement,
                    tm.permanenceDecrement)
    synapseData = connections.dataForSynapse(0)
    self.assertAlmostEqual(synapseData.permanence, 1.0)

    # Now permanence should be at max
    tm.adaptSegment(0, set([0]), connections,
                    tm.permanenceIncrement,
                    tm.permanenceDecrement)
    synapseData = connections.dataForSynapse(0)
    self.assertAlmostEqual(synapseData.permanence, 1.0)


  def testAdaptSegmentToMin(self):
    tm = self.tm

    connections = tm.connections
    connections.createSegment(0)
    connections.createSynapse(0, 23, 0.1)

    tm.adaptSegment(0, set(), connections,
                    tm.permanenceIncrement,
                    tm.permanenceDecrement)

    synapses = connections.synapsesForSegment(0)
    self.assertFalse(0 in synapses)


  def testPickCellsToLearnOn(self):
    tm = TemporalMemory(seed=42)

    connections = tm.connections
    connections.createSegment(0)

    winnerCells = set([4, 47, 58, 93])

    self.assertEqual(tm.pickCellsToLearnOn(2, 0, winnerCells, connections),
                     set([4, 93]))  # randomly picked

    self.assertEqual(tm.pickCellsToLearnOn(100, 0, winnerCells, connections),
                     set([4, 47, 58, 93]))

    self.assertEqual(tm.pickCellsToLearnOn(0, 0, winnerCells, connections),
                     set())


  def testPickCellsToLearnOnAvoidDuplicates(self):
    tm = TemporalMemory(seed=42)

    connections = tm.connections
    connections.createSegment(0)
    connections.createSynapse(0, 23, 0.6)

    winnerCells = set([23])

    # Ensure that no additional (duplicate) cells were picked
    self.assertEqual(tm.pickCellsToLearnOn(2, 0, winnerCells, connections),
                     set())


  def testColumnForCell1D(self):
    tm = TemporalMemory(
      columnDimensions=[2048],
      cellsPerColumn=5
    )
    self.assertEqual(tm.columnForCell(0), 0)
    self.assertEqual(tm.columnForCell(4), 0)
    self.assertEqual(tm.columnForCell(5), 1)
    self.assertEqual(tm.columnForCell(10239), 2047)


  def testColumnForCell2D(self):
    tm = TemporalMemory(
      columnDimensions=[64, 64],
      cellsPerColumn=4
    )
    self.assertEqual(tm.columnForCell(0), 0)
    self.assertEqual(tm.columnForCell(3), 0)
    self.assertEqual(tm.columnForCell(4), 1)
    self.assertEqual(tm.columnForCell(16383), 4095)


  def testColumnForCellInvalidCell(self):
    tm = TemporalMemory(
      columnDimensions=[64, 64],
      cellsPerColumn=4
    )

    try:
      tm.columnForCell(16383)
    except IndexError:
      self.fail("IndexError raised unexpectedly")

    args = [16384]
    self.assertRaises(IndexError, tm.columnForCell, *args)

    args = [-1]
    self.assertRaises(IndexError, tm.columnForCell, *args)


  def testCellsForColumn1D(self):
    tm = TemporalMemory(
      columnDimensions=[2048],
      cellsPerColumn=5
    )
    expectedCells = set([5, 6, 7, 8, 9])
    self.assertEqual(tm.cellsForColumn(1), expectedCells)


  def testCellsForColumn2D(self):
    tm = TemporalMemory(
      columnDimensions=[64, 64],
      cellsPerColumn=4
    )
    expectedCells = set([256, 257, 258, 259])
    self.assertEqual(tm.cellsForColumn(64), expectedCells)


  def testCellsForColumnInvalidColumn(self):
    tm = TemporalMemory(
      columnDimensions=[64, 64],
      cellsPerColumn=4
    )

    try:
      tm.cellsForColumn(4095)
    except IndexError:
      self.fail("IndexError raised unexpectedly")

    args = [4096]
    self.assertRaises(IndexError, tm.cellsForColumn, *args)

    args = [-1]
    self.assertRaises(IndexError, tm.cellsForColumn, *args)


  def testNumberOfColumns(self):
    tm = TemporalMemory(
      columnDimensions=[64, 64],
      cellsPerColumn=32
    )
    self.assertEqual(tm.numberOfColumns(), 64 * 64)


  def testNumberOfCells(self):
    tm = TemporalMemory(
      columnDimensions=[64, 64],
      cellsPerColumn=32
    )
    self.assertEqual(tm.numberOfCells(), 64 * 64 * 32)


  def testMapCellsToColumns(self):
    tm = TemporalMemory(
      columnDimensions=[100],
      cellsPerColumn=4
    )
    columnsForCells = tm.mapCellsToColumns(set([0, 1, 2, 5, 399]))
    self.assertEqual(columnsForCells[0], set([0, 1, 2]))
    self.assertEqual(columnsForCells[1], set([5]))
    self.assertEqual(columnsForCells[99], set([399]))


  @unittest.skipUnless(
      capnp, "pycapnp is not installed, skipping serialization test.")
  def testWriteRead(self):
    tm1 = TemporalMemory(
      columnDimensions=[100],
      cellsPerColumn=4,
      activationThreshold=7,
      initialPermanence=0.37,
      connectedPermanence=0.58,
      minThreshold=4,
      maxNewSynapseCount=18,
      permanenceIncrement=0.23,
      permanenceDecrement=0.08,
      seed=91
    )

    # Run some data through before serializing
    self.patternMachine = PatternMachine(100, 4)
    self.sequenceMachine = SequenceMachine(self.patternMachine)
    sequence = self.sequenceMachine.generateFromNumbers(range(5))
    for _ in range(3):
      for pattern in sequence:
        tm1.compute(pattern)

    proto1 = TemporalMemoryProto_capnp.TemporalMemoryProto.new_message()
    tm1.write(proto1)

    # Write the proto to a temp file and read it back into a new proto
    with tempfile.TemporaryFile() as f:
      proto1.write(f)
      f.seek(0)
      proto2 = TemporalMemoryProto_capnp.TemporalMemoryProto.read(f)

    # Load the deserialized proto
    tm2 = TemporalMemory.read(proto2)

    # Check that the two temporal memory objects have the same attributes
    self.assertEqual(tm1, tm2)

    # Run a couple records through after deserializing and check results match
    tm1.compute(self.patternMachine.get(0))
    tm2.compute(self.patternMachine.get(0))
    self.assertEqual(set(tm1.getActiveCells()), set(tm2.getActiveCells()))
    self.assertEqual(set(tm1.getPredictiveCells()),
                     set(tm2.getPredictiveCells()))
    self.assertEqual(set(tm1.getWinnerCells()), set(tm2.getWinnerCells()))
    self.assertEqual(tm1.connections, tm2.connections)

    tm1.compute(self.patternMachine.get(3))
    tm2.compute(self.patternMachine.get(3))
    self.assertEqual(set(tm1.getActiveCells()), set(tm2.getActiveCells()))
    self.assertEqual(set(tm1.getPredictiveCells()),
                     set(tm2.getPredictiveCells()))
    self.assertEqual(set(tm1.getWinnerCells()), set(tm2.getWinnerCells()))
    self.assertEqual(tm1.connections, tm2.connections)



if __name__ == '__main__':
  unittest.main()
