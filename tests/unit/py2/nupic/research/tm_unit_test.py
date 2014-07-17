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
TODO: Move all duplicate connections logic into shared function.
"""

import unittest

from nupic.research.TM import Connections, TM



class TMTest(unittest.TestCase):


  def setUp(self):
    self.tm = TM()


  def testActivateCorrectlyPredictiveCells(self):
    tm = self.tm

    prevPredictiveCells = {0, 237, 1026, 26337, 26339, 55536}
    activeColumns = {32, 47, 823}

    (activeCells,
    winnerCells,
    predictedColumns) = tm.activateCorrectlyPredictiveCells(prevPredictiveCells,
                                                            activeColumns,
                                                            tm.connections)

    self.assertEqual(activeCells, {1026, 26337, 26339})
    self.assertEqual(winnerCells, {1026, 26337, 26339})
    self.assertEqual(predictedColumns, {32, 823})


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
    activeColumns = {32, 47, 823}

    (activeCells,
    winnerCells,
    predictedColumns) = tm.activateCorrectlyPredictiveCells(prevPredictiveCells,
                                                            activeColumns,
                                                            tm.connections)

    self.assertEqual(activeCells,      set())
    self.assertEqual(winnerCells,      set())
    self.assertEqual(predictedColumns, set())

    # No active columns

    prevPredictiveCells = {0, 237, 1026, 26337, 26339, 55536}
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
    tm = TM(
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

    activeColumns    = {0, 1, 26}
    predictedColumns = {26}
    prevActiveSynapsesForSegment = {
      0: {0, 1},
      1: {3},
      2: {5}
    }

    (activeCells,
     winnerCells,
     learningSegments) = tm.burstColumns(activeColumns,
                                         predictedColumns,
                                         prevActiveSynapsesForSegment,
                                         connections)

    self.assertEqual(activeCells,      {0, 1, 2, 3, 4, 5, 6, 7})
    self.assertEqual(winnerCells,      {0, 6})  # 6 is randomly chosen cell
    self.assertEqual(learningSegments, {0, 4})  # 4 is new segment created

    # Check that new segment was added to winner cell (6) in column 1
    self.assertEqual(connections.segmentsForCell(6), {4})


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

    activeCells = {23, 37, 733, 4973}

    self.assertEqual(tm.computeActiveSynapses(activeCells, connections),
                     {0: {0, 1},
                      1: {3}})


  def testGetBestMatchingCell(self):
    tm = TM(
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
      0: {0, 1},
      1: {3},
      2: {5}
    }

    self.assertEqual(tm.getBestMatchingCell(0,
                                            activeSynapsesForSegment,
                                            connections),
                     (0, 0))

    self.assertEqual(tm.getBestMatchingCell(108,
                                            activeSynapsesForSegment,
                                            connections),
                     (3462, None))  # Random cell from column

    self.assertEqual(tm.getBestMatchingCell(999,
                                            activeSynapsesForSegment,
                                            connections),
                     (31972, None))  # Random cell from column


  def testGetBestMatchingSegment(self):
    tm = TM(
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
      0: {0, 1},
      1: {3},
      2: {5}
    }

    self.assertEqual(tm.getBestMatchingSegment(0,
                                               activeSynapsesForSegment,
                                               connections),
                     (0, {0, 1}))

    self.assertEqual(tm.getBestMatchingSegment(1,
                                               activeSynapsesForSegment,
                                               connections),
                     (2, {5}))

    self.assertEqual(tm.getBestMatchingSegment(8,
                                               activeSynapsesForSegment,
                                               connections),
                     (None, None))

    self.assertEqual(tm.getBestMatchingSegment(100,
                                               activeSynapsesForSegment,
                                               connections),
                     (None, None))


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
      0: {0, 1},
      1: {3}
    }

    self.assertEqual(
      tm.getConnectedActiveSynapsesForSegment(0,
                                              activeSynapsesForSegment,
                                              0.5,
                                              connections),
      {0})

    self.assertEqual(
      tm.getConnectedActiveSynapsesForSegment(1,
                                              activeSynapsesForSegment,
                                              0.5,
                                              connections),
      {3})


  def testAdaptSegment(self):
    tm = self.tm

    connections = tm.connections
    connections.createSegment(0)
    connections.createSynapse(0, 23, 0.6)
    connections.createSynapse(0, 37, 0.4)
    connections.createSynapse(0, 477, 0.9)

    tm.adaptSegment(0, {0, 1}, connections)

    (_, _, permanence) = connections.dataForSynapse(0)
    self.assertEqual(permanence, 0.7)

    (_, _, permanence) = connections.dataForSynapse(1)
    self.assertEqual(permanence, 0.5)

    (_, _, permanence) = connections.dataForSynapse(2)
    self.assertEqual(permanence, 0.8)


  def testPickCellsToLearnOn(self):
    tm = TM(seed=42)

    connections = tm.connections
    winnerCells = {4, 47, 58, 93}

    self.assertEqual(tm.pickCellsToLearnOn(2, 0, winnerCells, connections),
                     {4, 58})  # randomly picked

    self.assertEqual(tm.pickCellsToLearnOn(100, 0, winnerCells, connections),
                     {4, 47, 58, 93})

    self.assertEqual(tm.pickCellsToLearnOn(0, 0, winnerCells, connections),
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
    expectedCells = {5, 6, 7, 8, 9}
    self.assertEqual(connections.cellsForColumn(1), expectedCells)


  def testCellsForColumn2D(self):
    connections = Connections([64, 64], 4)
    expectedCells = {256, 257, 258, 259}
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

    self.assertEqual(connections.segmentsForCell(0), {0, 1})


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
    self.assertRaises(IndexError, connections.cellForSegment, *args)


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

    self.assertEqual(connections.synapsesForSegment(0), {0, 1})

    self.assertEqual(connections.synapsesForSourceCell(174), set())
    self.assertEqual(connections.synapsesForSourceCell(254), {0})


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
    self.assertRaises(IndexError, connections.dataForSynapse, *args)


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
    self.assertRaises(IndexError, connections.updateSynapsePermanence, *args)

    # Invalid permanence
    args = [0, 1.4374]
    self.assertRaises(ValueError, connections.updateSynapsePermanence, *args)
    args = [0, -0.4374]
    self.assertRaises(ValueError, connections.updateSynapsePermanence, *args)



if __name__ == '__main__':
  unittest.main()
