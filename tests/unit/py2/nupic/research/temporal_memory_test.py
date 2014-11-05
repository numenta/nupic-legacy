#!/usr/bin/env python
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
TODO: Mock out all function calls.
TODO: Make default test TM instance simpler, with 4 cells per column.
TODO: Move all duplicate connections logic into shared function.
"""

import unittest

from nupic.research.temporal_memory import Connections, TemporalMemory



class TemporalMemoryTest(unittest.TestCase):


  def setUp(self):
    self.tm = TemporalMemory()


  def testActivateCorrectlyPredictiveCells(self):
    tm = self.tm

    prevPredictiveCells = set([0, 237, 1026, 26337, 26339, 55536])
    activeColumns = set([32, 47, 823])

    (activeCells,
    winnerCells,
    predictedColumns) = tm.activateCorrectlyPredictiveCells(prevPredictiveCells,
                                                            activeColumns,
                                                            tm.connections)

    self.assertEqual(activeCells, set([1026, 26337, 26339]))
    self.assertEqual(winnerCells, set([1026, 26337, 26339]))
    self.assertEqual(predictedColumns, set([32, 823]))


  def testActivateCorrectlyPredictiveCellsEmpty(self):
    tm = self.tm

    prevPredictiveCells = set()
    activeColumns      = set()

    (activeCells,
    winnerCells,
    predictedColumns) = tm.activateCorrectlyPredictiveCells(prevPredictiveCells,
                                                            activeColumns,
                                                            tm.connections)

    self.assertEqual(activeCells,      set())
    self.assertEqual(winnerCells,      set())
    self.assertEqual(predictedColumns, set())

    # No previous predictive cells

    prevPredictiveCells = set()
    activeColumns = set([32, 47, 823])

    (activeCells,
    winnerCells,
    predictedColumns) = tm.activateCorrectlyPredictiveCells(prevPredictiveCells,
                                                            activeColumns,
                                                            tm.connections)

    self.assertEqual(activeCells,      set())
    self.assertEqual(winnerCells,      set())
    self.assertEqual(predictedColumns, set())

    # No active columns

    prevPredictiveCells = set([0, 237, 1026, 26337, 26339, 55536])
    activeColumns = set()

    (activeCells,
    winnerCells,
    predictedColumns) = tm.activateCorrectlyPredictiveCells(prevPredictiveCells,
                                                            activeColumns,
                                                            tm.connections)

    self.assertEqual(activeCells,      set())
    self.assertEqual(winnerCells,      set())
    self.assertEqual(predictedColumns, set())


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

    activeColumns    = set([0, 1, 26])
    predictedColumns = set([26])
    prevActiveSynapsesForSegment = {
      0: set([0, 1]),
      1: set([3]),
      2: set([5])
    }

    (activeCells,
     winnerCells,
     learningSegments) = tm.burstColumns(activeColumns,
                                         predictedColumns,
                                         prevActiveSynapsesForSegment,
                                         connections)

    self.assertEqual(activeCells,      set([0, 1, 2, 3, 4, 5, 6, 7]))
    self.assertEqual(winnerCells,      set([0, 6]))  # 6 is randomly chosen cell
    self.assertEqual(learningSegments, set([0, 4]))  # 4 is new segment created

    # Check that new segment was added to winner cell (6) in column 1
    self.assertEqual(connections.segmentsForCell(6), set([4]))


  def testBurstColumnsEmpty(self):
    tm = self.tm

    activeColumns    = set()
    predictedColumns = set()
    prevActiveSynapsesForSegment = dict()
    connections = tm.connections

    (activeCells,
     winnerCells,
     learningSegments) = tm.burstColumns(activeColumns,
                                         predictedColumns,
                                         prevActiveSynapsesForSegment,
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
    prevActiveSynapsesForSegment = {0: set([0, 1]),
                                    1: set([3])}
    winnerCells = set([0])
    prevWinnerCells = set([10, 11, 12, 13, 14])

    tm.learnOnSegments(prevActiveSegments,
                       learningSegments,
                       prevActiveSynapsesForSegment,
                       winnerCells,
                       prevWinnerCells,
                       connections)

    # Check segment 0
    (_, _, permanence) = connections.dataForSynapse(0)
    self.assertAlmostEqual(permanence, 0.7)

    (_, _, permanence) = connections.dataForSynapse(1)
    self.assertAlmostEqual(permanence, 0.5)

    (_, _, permanence) = connections.dataForSynapse(2)
    self.assertAlmostEqual(permanence, 0.8)

    # Check segment 1
    (_, _, permanence) = connections.dataForSynapse(3)
    self.assertAlmostEqual(permanence, 0.8)

    self.assertEqual(len(connections.synapsesForSegment(1)), 2)

    # Check segment 2
    (_, _, permanence) = connections.dataForSynapse(4)
    self.assertAlmostEqual(permanence, 0.9)

    self.assertEqual(len(connections.synapsesForSegment(2)), 1)

    # Check segment 3
    self.assertEqual(len(connections.synapsesForSegment(3)), 2)


  def testComputePredictiveCells(self):
    tm = TemporalMemory(activationThreshold=2)

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

    activeSynapsesForSegment = {0: set([0, 1]),
                                1: set([3, 4]),
                                2: set([5])}

    (activeSegments,
     predictiveCells) = tm.computePredictiveCells(activeSynapsesForSegment,
                                                  connections)
    self.assertEqual(activeSegments, set([0]))
    self.assertEqual(predictiveCells, set([0]))


  def testComputeActiveSynapses(self):
    tm = self.tm

    connections = tm.connections
    connections.createSegment(0)
    connections.createSynapse(0, 23, 0.6)
    connections.createSynapse(0, 37, 0.4)
    connections.createSynapse(0, 477, 0.9)

    connections.createSegment(1)
    connections.createSynapse(1, 733, 0.7)

    connections.createSegment(8)
    connections.createSynapse(2, 486, 0.9)

    activeCells = set([23, 37, 733, 4973])

    self.assertEqual(tm.computeActiveSynapses(activeCells, connections),
                     {0: set([0, 1]),
                      1: set([3])})


  def testGetBestMatchingCell(self):
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

    activeSynapsesForSegment = {
      0: set([0, 1]),
      1: set([3]),
      2: set([5])
    }

    self.assertEqual(tm.getBestMatchingCell(connections.cellsForColumn(0),
                                            activeSynapsesForSegment,
                                            connections),
                     (0, 0))

    self.assertEqual(tm.getBestMatchingCell(connections.cellsForColumn(3),  # column containing cell 108
                                            activeSynapsesForSegment,
                                            connections),
                     (96, None))  # Random cell from column

    self.assertEqual(tm.getBestMatchingCell(connections.cellsForColumn(999),
                                            activeSynapsesForSegment,
                                            connections),
                     (31972, None))  # Random cell from column


  def testGetBestMatchingCellFewestSegments(self):
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
      (cell, _) = tm.getBestMatchingCell(connections.cellsForColumn(0),
                                         activeSynapsesForSegment,
                                         connections)
      self.assertEqual(cell, 1)


  def testGetBestMatchingSegment(self):
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

    activeSynapsesForSegment = {
      0: set([0, 1]),
      1: set([3]),
      2: set([5])
    }

    self.assertEqual(tm.getBestMatchingSegment(0,
                                               activeSynapsesForSegment,
                                               connections),
                     (0, set([0, 1])))

    self.assertEqual(tm.getBestMatchingSegment(1,
                                               activeSynapsesForSegment,
                                               connections),
                     (2, set([5])))

    self.assertEqual(tm.getBestMatchingSegment(8,
                                               activeSynapsesForSegment,
                                               connections),
                     (None, None))

    self.assertEqual(tm.getBestMatchingSegment(100,
                                               activeSynapsesForSegment,
                                               connections),
                     (None, None))


  def testGetLeastUsedCell(self):
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
      self.assertEqual(tm.getLeastUsedCell(connections.cellsForColumn(0),
                                           connections),
                       1)


  def testComputeActiveSynapsesNoActivity(self):
    tm = self.tm

    connections = tm.connections
    connections.createSegment(0)
    connections.createSynapse(0, 23, 0.6)
    connections.createSynapse(0, 37, 0.4)
    connections.createSynapse(0, 477, 0.9)

    connections.createSegment(1)
    connections.createSynapse(1, 733, 0.7)

    connections.createSegment(8)
    connections.createSynapse(2, 486, 0.9)

    activeCells = set()

    self.assertEqual(tm.computeActiveSynapses(activeCells, connections),
                     dict())


  def testGetConnectedActiveSynapsesForSegment(self):
    tm = self.tm

    connections = tm.connections
    connections.createSegment(0)
    connections.createSynapse(0, 23, 0.6)
    connections.createSynapse(0, 37, 0.4)
    connections.createSynapse(0, 477, 0.9)

    connections.createSegment(1)
    connections.createSynapse(1, 733, 0.7)

    connections.createSegment(8)
    connections.createSynapse(2, 486, 0.9)

    activeSynapsesForSegment = {
      0: set([0, 1]),
      1: set([3])
    }

    self.assertEqual(
      tm.getConnectedActiveSynapsesForSegment(0,
                                              activeSynapsesForSegment,
                                              0.5,
                                              connections),
      set([0]))

    self.assertEqual(
      tm.getConnectedActiveSynapsesForSegment(1,
                                              activeSynapsesForSegment,
                                              0.5,
                                              connections),
      set([3]))


  def testAdaptSegment(self):
    tm = self.tm

    connections = tm.connections
    connections.createSegment(0)
    connections.createSynapse(0, 23, 0.6)
    connections.createSynapse(0, 37, 0.4)
    connections.createSynapse(0, 477, 0.9)

    tm.adaptSegment(0, set([0, 1]), connections)

    (_, _, permanence) = connections.dataForSynapse(0)
    self.assertAlmostEqual(permanence, 0.7)

    (_, _, permanence) = connections.dataForSynapse(1)
    self.assertAlmostEqual(permanence, 0.5)

    (_, _, permanence) = connections.dataForSynapse(2)
    self.assertAlmostEqual(permanence, 0.8)


  def testAdaptSegmentToMax(self):
    tm = self.tm

    connections = tm.connections
    connections.createSegment(0)
    connections.createSynapse(0, 23, 0.9)

    tm.adaptSegment(0, set([0]), connections)
    (_, _, permanence) = connections.dataForSynapse(0)
    self.assertAlmostEqual(permanence, 1.0)

    # Now permanence should be at max
    tm.adaptSegment(0, set([0]), connections)
    (_, _, permanence) = connections.dataForSynapse(0)
    self.assertAlmostEqual(permanence, 1.0)


  def testAdaptSegmentToMin(self):
    tm = self.tm

    connections = tm.connections
    connections.createSegment(0)
    connections.createSynapse(0, 23, 0.1)

    tm.adaptSegment(0, set(), connections)
    (_, _, permanence) = connections.dataForSynapse(0)
    self.assertAlmostEqual(permanence, 0.0)

    # Now permanence should be at min
    tm.adaptSegment(0, set(), connections)
    (_, _, permanence) = connections.dataForSynapse(0)
    self.assertAlmostEqual(permanence, 0.0)


  def testPickCellsToLearnOn(self):
    tm = TemporalMemory(seed=42)

    connections = tm.connections
    connections.createSegment(0)

    winnerCells = set([4, 47, 58, 93])

    self.assertEqual(tm.pickCellsToLearnOn(2, 0, winnerCells, connections),
                     set([4, 58]))  # randomly picked

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


class ConnectionsTest(unittest.TestCase):


  def setUp(self):
    self.connections = Connections([2048], 32)


  def testInit(self):
    columnDimensions = [2048]
    cellsPerColumn = 32

    connections = Connections(columnDimensions, cellsPerColumn)
    self.assertEqual(connections.columnDimensions, columnDimensions)
    self.assertEqual(connections.cellsPerColumn, cellsPerColumn)


  def testInitInvalidParams(self):
    # Invalid columnDimensions
    args = [[], 32]
    self.assertRaises(ValueError, Connections, *args)

    # Invalid cellsPerColumn
    args = [[2048], 0]
    self.assertRaises(ValueError, Connections, *args)
    args = [[2048], -10]
    self.assertRaises(ValueError, Connections, *args)


  def testColumnForCell1D(self):
    connections = Connections([2048], 5)
    self.assertEqual(connections.columnForCell(0), 0)
    self.assertEqual(connections.columnForCell(4), 0)
    self.assertEqual(connections.columnForCell(5), 1)
    self.assertEqual(connections.columnForCell(10239), 2047)


  def testColumnForCell2D(self):
    connections = Connections([64, 64], 4)
    self.assertEqual(connections.columnForCell(0), 0)
    self.assertEqual(connections.columnForCell(3), 0)
    self.assertEqual(connections.columnForCell(4), 1)
    self.assertEqual(connections.columnForCell(16383), 4095)


  def testColumnForCellInvalidCell(self):
    connections = Connections([64, 64], 4)

    try:
      connections.columnForCell(16383)
    except IndexError:
      self.fail("IndexError raised unexpectedly")

    args = [16384]
    self.assertRaises(IndexError, connections.columnForCell, *args)

    args = [-1]
    self.assertRaises(IndexError, connections.columnForCell, *args)


  def testCellsForColumn1D(self):
    connections = Connections([2048], 5)
    expectedCells = set([5, 6, 7, 8, 9])
    self.assertEqual(connections.cellsForColumn(1), expectedCells)


  def testCellsForColumn2D(self):
    connections = Connections([64, 64], 4)
    expectedCells = set([256, 257, 258, 259])
    self.assertEqual(connections.cellsForColumn(64), expectedCells)


  def testCellsForColumnInvalidColumn(self):
    connections = Connections([64, 64], 4)

    try:
      connections.cellsForColumn(4095)
    except IndexError:
      self.fail("IndexError raised unexpectedly")

    args = [4096]
    self.assertRaises(IndexError, connections.cellsForColumn, *args)

    args = [-1]
    self.assertRaises(IndexError, connections.cellsForColumn, *args)


  def testCreateSegment(self):
    connections = self.connections

    self.assertEqual(connections.segmentsForCell(0), set())

    self.assertEqual(connections.createSegment(0), 0)
    self.assertEqual(connections.createSegment(0), 1)
    self.assertEqual(connections.createSegment(10), 2)

    self.assertEqual(connections.cellForSegment(0), 0)
    self.assertEqual(connections.cellForSegment(2), 10)

    self.assertEqual(connections.segmentsForCell(0), set([0, 1]))


  def testCreateSegmentInvalidCell(self):
    connections = self.connections

    try:
      connections.createSegment(65535)
    except IndexError:
      self.fail("IndexError raised unexpectedly")

    args = [65536]
    self.assertRaises(IndexError, connections.createSegment, *args)

    args = [-1]
    self.assertRaises(IndexError, connections.createSegment, *args)


  def testCellForSegmentInvalidSegment(self):
    connections = self.connections

    connections.createSegment(0)

    args = [1]
    self.assertRaises(KeyError, connections.cellForSegment, *args)


  def testSegmentsForCellInvalidCell(self):
    connections = self.connections

    args = [65536]
    self.assertRaises(IndexError, connections.segmentsForCell, *args)

    args = [-1]
    self.assertRaises(IndexError, connections.segmentsForCell, *args)


  def testCreateSynapse(self):
    connections = self.connections

    connections.createSegment(0)
    self.assertEqual(connections.synapsesForSegment(0), set())

    self.assertEqual(connections.createSynapse(0, 254, 0.1173), 0)
    self.assertEqual(connections.createSynapse(0, 477, 0.3253), 1)

    self.assertEqual(connections.dataForSynapse(0), (0, 254, 0.1173))

    self.assertEqual(connections.synapsesForSegment(0), set([0, 1]))

    self.assertEqual(connections.synapsesForSourceCell(174), set())
    self.assertEqual(connections.synapsesForSourceCell(254), set([0]))


  def testCreateSynapseInvalidParams(self):
    connections = self.connections

    connections.createSegment(0)

    # Invalid segment
    args = [1, 48, 0.124]
    self.assertRaises(IndexError, connections.createSynapse, *args)

    # Invalid sourceCell
    args = [0, 65536, 0.124]
    self.assertRaises(IndexError, connections.createSynapse, *args)

    # Invalid permanence
    args = [0, 48, 1.124]
    self.assertRaises(ValueError, connections.createSynapse, *args)
    args = [0, 48, -0.124]
    self.assertRaises(ValueError, connections.createSynapse, *args)


  def testDataForSynapseInvalidSynapse(self):
    connections = self.connections

    connections.createSegment(0)
    connections.createSynapse(0, 834, 0.1284)

    args = [1]
    self.assertRaises(KeyError, connections.dataForSynapse, *args)


  def testSynapsesForSegmentInvalidSegment(self):
    connections = self.connections

    connections.createSegment(0)

    args = [1]
    self.assertRaises(IndexError, connections.synapsesForSegment, *args)


  def testSynapsesForSourceCellInvalidCell(self):
    connections = self.connections

    args = [65536]
    self.assertRaises(IndexError, connections.synapsesForSourceCell, *args)

    args = [-1]
    self.assertRaises(IndexError, connections.synapsesForSourceCell, *args)


  def testUpdateSynapsePermanence(self):
    connections = self.connections

    connections.createSegment(0)
    connections.createSynapse(0, 483, 0.1284)

    connections.updateSynapsePermanence(0, 0.2496)
    self.assertEqual(connections.dataForSynapse(0), (0, 483, 0.2496))


  def testUpdateSynapsePermanenceInvalidParams(self):
    connections = self.connections

    connections.createSegment(0)
    connections.createSynapse(0, 483, 0.1284)

    # Invalid synapse
    args = [1, 0.4374]
    self.assertRaises(KeyError, connections.updateSynapsePermanence, *args)

    # Invalid permanence
    args = [0, 1.4374]
    self.assertRaises(ValueError, connections.updateSynapsePermanence, *args)
    args = [0, -0.4374]
    self.assertRaises(ValueError, connections.updateSynapsePermanence, *args)


  def testNumberOfColumns(self):
    connections = Connections([64, 64], 32)
    self.assertEqual(connections.numberOfColumns(), 64 * 64)


  def testNumberOfCells(self):
    connections = Connections([64, 64], 32)
    self.assertEqual(connections.numberOfCells(), 64 * 64 * 32)


  def testMapCellsToColumns(self):
    connections = Connections([100], 4)
    columnsForCells = connections.mapCellsToColumns(set([0, 1, 2, 5, 399]))
    self.assertEqual(columnsForCells[0], set([0, 1, 2]))
    self.assertEqual(columnsForCells[1], set([5]))
    self.assertEqual(columnsForCells[99], set([399]))



if __name__ == '__main__':
  unittest.main()
