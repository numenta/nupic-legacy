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

import tempfile
import unittest
import copy

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
    tm = TemporalMemory(
      columnDimensions=[32],
      cellsPerColumn=4,
      activationThreshold=3,
      initialPermanence=.21,
      connectedPermanence=.5,
      minThreshold=2,
      maxNewSynapseCount=3,
      permanenceIncrement=.10,
      permanenceDecrement=.10,
      predictedSegmentDecrement=0.0,
      seed=42)

    previousActiveColumns = [0]
    activeColumns = [1]
    previousActiveCells = [0,1,2,3]
    expectedActiveCells = [4]

    activeSegment = tm.connections.createSegment(expectedActiveCells[0])
    tm.connections.createSynapse(activeSegment, previousActiveCells[0], .5)
    tm.connections.createSynapse(activeSegment, previousActiveCells[1], .5)
    tm.connections.createSynapse(activeSegment, previousActiveCells[2], .5)
    tm.connections.createSynapse(activeSegment, previousActiveCells[3], .5)

    tm.compute(previousActiveColumns, True)
    self.assertEqual(expectedActiveCells, tm.getPredictiveCells())
    tm.compute(activeColumns, True)
    self.assertEqual(expectedActiveCells, tm.getActiveCells())


  def testBurstUnpredictedColumns(self):
    tm = TemporalMemory(
      columnDimensions=[32],
      cellsPerColumn=4,
      activationThreshold=3,
      initialPermanence=.21,
      connectedPermanence=.5,
      minThreshold=2,
      maxNewSynapseCount=3,
      permanenceIncrement=.10,
      permanenceDecrement=.10,
      predictedSegmentDecrement=0.0,
      seed=42)

    activeColumns = [0]
    burstingCells = [0, 1, 2, 3]

    tm.compute(activeColumns, True)

    self.assertEqual(burstingCells, tm.getActiveCells())


  def testZeroActiveColumns(self):
    tm = TemporalMemory(
      columnDimensions=[32],
      cellsPerColumn=4,
      activationThreshold=3,
      initialPermanence=.21,
      connectedPermanence=.5,
      minThreshold=2,
      maxNewSynapseCount=3,
      permanenceIncrement=.10,
      permanenceDecrement=.10,
      predictedSegmentDecrement=0.0,
      seed=42)

    previousActiveColumns = [0]
    previousActiveCells = [0, 1, 2, 3]
    expectedActiveCells = [4]

    segment = tm.connections.createSegment(expectedActiveCells[0])
    tm.connections.createSynapse(segment, previousActiveCells[0], .5)
    tm.connections.createSynapse(segment, previousActiveCells[1], .5)
    tm.connections.createSynapse(segment, previousActiveCells[2], .5)
    tm.connections.createSynapse(segment, previousActiveCells[3], .5)

    tm.compute(previousActiveColumns, True)
    self.assertFalse(len(tm.getActiveCells()) == 0)
    self.assertFalse(len(tm.getWinnerCells()) == 0)
    self.assertFalse(len(tm.getPredictiveCells()) == 0)

    zeroColumns = []
    tm.compute(zeroColumns, True)

    self.assertTrue(len(tm.getActiveCells()) == 0)
    self.assertTrue(len(tm.getWinnerCells()) == 0)
    self.assertTrue(len(tm.getPredictiveCells()) == 0)


  def testPredictedActiveCellsAreAlwaysWinners(self):
    tm = TemporalMemory(
      columnDimensions=[32],
      cellsPerColumn=4,
      activationThreshold=3,
      initialPermanence=.21,
      connectedPermanence=.5,
      minThreshold=2,
      maxNewSynapseCount=3,
      permanenceIncrement=.10,
      permanenceDecrement=.10,
      predictedSegmentDecrement=0.0,
      seed=42)

    previousActiveColumns = [0]
    activeColumns = [1]
    previousActiveCells = [0, 1, 2, 3]
    expectedWinnerCells = [4, 6]

    activeSegment1 = tm.connections.createSegment(expectedWinnerCells[0])
    tm.connections.createSynapse(activeSegment1, previousActiveCells[0], .5)
    tm.connections.createSynapse(activeSegment1, previousActiveCells[1], .5)
    tm.connections.createSynapse(activeSegment1, previousActiveCells[2], .5)

    activeSegment2 = tm.connections.createSegment(expectedWinnerCells[1])
    tm.connections.createSynapse(activeSegment2, previousActiveCells[0], .5)
    tm.connections.createSynapse(activeSegment2, previousActiveCells[1], .5)
    tm.connections.createSynapse(activeSegment2, previousActiveCells[2], .5)

    tm.compute(previousActiveColumns, False)
    tm.compute(activeColumns, False)

    self.assertEqual(expectedWinnerCells, tm.getWinnerCells())


  def testReinforceCorrectlyActiveSegments(self):
    tm = TemporalMemory(
      columnDimensions=[32],
      cellsPerColumn=4,
      activationThreshold=3,
      initialPermanence=.2,
      connectedPermanence=.50,
      minThreshold=2,
      maxNewSynapseCount=4,
      permanenceIncrement=.10,
      permanenceDecrement=.08,
      predictedSegmentDecrement=0.02,
      seed=42)

    prevActiveColumns = [0]
    prevActiveCells = [0,1,2,3]
    activeColumns = [1]
    activeCell = 5

    activeSegment = tm.connections.createSegment(activeCell)
    as1 = tm.connections.createSynapse(activeSegment, prevActiveCells[0], .5)
    as2 = tm.connections.createSynapse(activeSegment, prevActiveCells[1], .5)
    as3 = tm.connections.createSynapse(activeSegment, prevActiveCells[2], .5)
    is1 = tm.connections.createSynapse(activeSegment, 81, .5) #inactive synapse

    tm.compute(prevActiveColumns, True)
    tm.compute(activeColumns, True)

    self.assertAlmostEqual(.6, tm.connections.dataForSynapse(as1).permanence)
    self.assertAlmostEqual(.6, tm.connections.dataForSynapse(as2).permanence)
    self.assertAlmostEqual(.6, tm.connections.dataForSynapse(as3).permanence)
    self.assertAlmostEqual(.42, tm.connections.dataForSynapse(is1).permanence)


  def testReinforceSelectedMatchingSegmentInBurstingColumn(self):
    tm = TemporalMemory(
      columnDimensions=[32],
      cellsPerColumn=4,
      activationThreshold=3,
      initialPermanence=.21,
      connectedPermanence=.50,
      minThreshold=2,
      maxNewSynapseCount=3,
      permanenceIncrement=.10,
      permanenceDecrement=.08,
      predictedSegmentDecrement=0.0,
      seed=42)

    previousActiveColumns = [0]
    previousActiveCells = [0,1,2,3]
    activeColumns = [1]
    burstingCells = [4,5,6,7]

    selectedMatchingSegment = tm.connections.createSegment(burstingCells[0])
    as1 = tm.connections.createSynapse(selectedMatchingSegment,
                                       previousActiveCells[0], .3)
    as2 = tm.connections.createSynapse(selectedMatchingSegment,
                                       previousActiveCells[1], .3)
    as3 = tm.connections.createSynapse(selectedMatchingSegment,
                                       previousActiveCells[2], .3)
    is1 = tm.connections.createSynapse(selectedMatchingSegment, 81, .3)

    otherMatchingSegment = tm.connections.createSegment(burstingCells[1])
    tm.connections.createSynapse(otherMatchingSegment,
                                 previousActiveCells[0], .3)
    tm.connections.createSynapse(otherMatchingSegment,
                                 previousActiveCells[1], .3)
    tm.connections.createSynapse(otherMatchingSegment, 81, .3)

    tm.compute(previousActiveColumns, True)
    tm.compute(activeColumns, True)

    self.assertAlmostEqual(.4, tm.connections.dataForSynapse(as1).permanence)
    self.assertAlmostEqual(.4, tm.connections.dataForSynapse(as2).permanence)
    self.assertAlmostEqual(.4, tm.connections.dataForSynapse(as3).permanence)
    self.assertAlmostEqual(.22, tm.connections.dataForSynapse(is1).permanence)


  def testNoChangeToNonselectedMatchingSegmentsInBurstingColumn(self):
    tm = TemporalMemory(
      columnDimensions=[32],
      cellsPerColumn=4,
      activationThreshold=3,
      initialPermanence=.21,
      connectedPermanence=.50,
      minThreshold=2,
      maxNewSynapseCount=3,
      permanenceIncrement=.10,
      permanenceDecrement=.08,
      predictedSegmentDecrement=0.0,
      seed=42)

    previousActiveColumns = [0]
    previousActiveCells = [0,1,2,3]
    activeColumns = [1]
    burstingCells = [4,5,6,7]

    selectedMatchingSegment = tm.connections.createSegment(burstingCells[0])
    tm.connections.createSynapse(selectedMatchingSegment,
                                 previousActiveCells[0], .3)
    tm.connections.createSynapse(selectedMatchingSegment,
                                 previousActiveCells[1], .3)
    tm.connections.createSynapse(selectedMatchingSegment,
                                 previousActiveCells[2], .3)
    tm.connections.createSynapse(selectedMatchingSegment, 81, .3)

    otherMatchingSegment = tm.connections.createSegment(burstingCells[1])
    as1 = tm.connections.createSynapse(otherMatchingSegment,
                                       previousActiveCells[0], .3)
    as2 = tm.connections.createSynapse(otherMatchingSegment,
                                       previousActiveCells[1], .3)
    is1 = tm.connections.createSynapse(otherMatchingSegment, 81, .3)

    tm.compute(previousActiveColumns, True)
    tm.compute(activeColumns, True)

    self.assertAlmostEqual(.3, tm.connections.dataForSynapse(as1).permanence)
    self.assertAlmostEqual(.3, tm.connections.dataForSynapse(as2).permanence)
    self.assertAlmostEqual(.3, tm.connections.dataForSynapse(is1).permanence)


  def testNoChangeToMatchingSegmentsInPredictedActiveColumn(self):
    tm = TemporalMemory(
      columnDimensions=[32],
      cellsPerColumn=4,
      activationThreshold=3,
      initialPermanence=.21,
      connectedPermanence=.50,
      minThreshold=2,
      maxNewSynapseCount=3,
      permanenceIncrement=.10,
      permanenceDecrement=.10,
      predictedSegmentDecrement=0.0,
      seed=42)

    previousActiveColumns = [0]
    activeColumns = [1]
    previousActiveCells = [0,1,2,3]
    expectedActiveCells = [4]
    otherburstingCells = [5,6,7]

    activeSegment = tm.connections.createSegment(expectedActiveCells[0])
    tm.connections.createSynapse(activeSegment, previousActiveCells[0], .5)
    tm.connections.createSynapse(activeSegment, previousActiveCells[1], .5)
    tm.connections.createSynapse(activeSegment, previousActiveCells[2], .5)
    tm.connections.createSynapse(activeSegment, previousActiveCells[3], .5)

    matchingSegmentOnSameCell = tm.connections.createSegment(
      expectedActiveCells[0])
    s1 = tm.connections.createSynapse(matchingSegmentOnSameCell,
                                      previousActiveCells[0], .3)
    s2 = tm.connections.createSynapse(matchingSegmentOnSameCell,
                                      previousActiveCells[1], .3)

    matchingSegmentOnOtherCell = tm.connections.createSegment(
      otherburstingCells[0])
    s3 = tm.connections.createSynapse(matchingSegmentOnOtherCell,
                                      previousActiveCells[0], .3)
    s4 = tm.connections.createSynapse(matchingSegmentOnOtherCell,
                                      previousActiveCells[1], .3)


    tm.compute(previousActiveColumns, True)
    self.assertEqual(expectedActiveCells, tm.getPredictiveCells())
    tm.compute(activeColumns, True)

    self.assertAlmostEqual(.3, tm.connections.dataForSynapse(s1).permanence)
    self.assertAlmostEqual(.3, tm.connections.dataForSynapse(s2).permanence)
    self.assertAlmostEqual(.3, tm.connections.dataForSynapse(s3).permanence)
    self.assertAlmostEqual(.3, tm.connections.dataForSynapse(s4).permanence)


  def testNoNewSegmentIfNotEnoughWinnerCells(self):
    tm = TemporalMemory(
      columnDimensions=[32],
      cellsPerColumn=4,
      activationThreshold=3,
      initialPermanence=.21,
      connectedPermanence=.50,
      minThreshold=2,
      maxNewSynapseCount=3,
      permanenceIncrement=.10,
      permanenceDecrement=.10,
      predictedSegmentDecrement=0.0,
      seed=42)

    zeroColumns = []
    activeColumns = [0]

    tm.compute(zeroColumns, True)
    tm.compute(activeColumns, True)

    self.assertEqual(0, tm.connections.numSegments())


  def testNewSegmentAddSynapsesToSubsetOfWinnerCells(self):
    tm = TemporalMemory(
      columnDimensions=[32],
      cellsPerColumn=4,
      activationThreshold=3,
      initialPermanence=.21,
      connectedPermanence=.50,
      minThreshold=2,
      maxNewSynapseCount=2,
      permanenceIncrement=.10,
      permanenceDecrement=.10,
      predictedSegmentDecrement=0.0,
      seed=42)

    previousActiveColumns = [0, 1, 2]
    activeColumns = [4]

    tm.compute(previousActiveColumns, True)

    prevWinnerCells = tm.getWinnerCells() #[0, 8, 7]
    self.assertEqual(3, len(prevWinnerCells))

    tm.compute(activeColumns, True)

    winnerCells = tm.getWinnerCells() #[18]
    self.assertEqual(1, len(winnerCells))
    segments = list(tm.connections.segmentsForCell(winnerCells[0]))
    self.assertEqual(1, len(segments))
    synapses = list(tm.connections.synapsesForSegment(segments[0]))
    self.assertEqual(2, len(synapses))

    for synapse in synapses:
      synapseData = tm.connections.dataForSynapse(synapse)
      self.assertAlmostEqual(.21, synapseData.permanence)
      self.assertTrue(synapseData.presynapticCell in prevWinnerCells)


  def testNewSegmentAddSynapsesToAllWinnerCells(self):
    tm = TemporalMemory(
      columnDimensions=[32],
      cellsPerColumn=4,
      activationThreshold=3,
      initialPermanence=.21,
      connectedPermanence=.50,
      minThreshold=2,
      maxNewSynapseCount=4,
      permanenceIncrement=.10,
      permanenceDecrement=.10,
      predictedSegmentDecrement=0.0,
      seed=42)

    previousActiveColumns = [0, 1, 2]
    activeColumns = [4]

    tm.compute(previousActiveColumns)
    prevWinnerCells = sorted(tm.getWinnerCells())
    self.assertEqual(3, len(prevWinnerCells))

    tm.compute(activeColumns)

    winnerCells = tm.getWinnerCells()
    self.assertEqual(1, len(winnerCells))
    segments = list(tm.connections.segmentsForCell(winnerCells[0]))
    self.assertEqual(1, len(segments))
    synapses = list(tm.connections.synapsesForSegment(segments[0]))
    self.assertEqual(3, len(synapses))

    presynapticCells = []
    for synapse in synapses:
      synapseData = tm.connections.dataForSynapse(synapse)
      self.assertAlmostEqual(.21, synapseData.permanence)
      presynapticCells.append(synapseData.presynapticCell)

    presynapticCells = sorted(presynapticCells)
    self.assertEqual(prevWinnerCells, presynapticCells)


  def testMatchingSegmentAddSynapsesToSubsetOfWinnerCells(self):
    tm = TemporalMemory(
      columnDimensions=[32],
      cellsPerColumn=1,
      activationThreshold=3,
      initialPermanence=.21,
      connectedPermanence=.50,
      minThreshold=1,
      maxNewSynapseCount=3,
      permanenceIncrement=.10,
      permanenceDecrement=.10,
      predictedSegmentDecrement=0.0,
      seed=42)

    previousActiveColumns = [0, 1, 2, 3]
    prevWinnerCells = [0, 1, 2, 3]
    activeColumns = [4]

    matchingSegment = tm.connections.createSegment(4)
    tm.connections.createSynapse(matchingSegment, 0, .5)

    tm.compute(previousActiveColumns, True)
    self.assertEqual(prevWinnerCells, tm.getWinnerCells())
    tm.compute(activeColumns, True)

    synapses = tm.connections.synapsesForSegment(matchingSegment)
    self.assertEqual(3, len(synapses))

    for synapse in synapses:
      synapseData = tm.connections.dataForSynapse(synapse)
      if synapseData.presynapticCell != 0:
        self.assertAlmostEqual(.21, synapseData.permanence)
        self.assertTrue(synapseData.presynapticCell == prevWinnerCells[1] or
                        synapseData.presynapticCell == prevWinnerCells[2] or
                        synapseData.presynapticCell == prevWinnerCells[3])


  def testMatchingSegmentAddSynapsesToAllWinnerCells(self):
    tm = TemporalMemory(
      columnDimensions=[32],
      cellsPerColumn=1,
      activationThreshold=3,
      initialPermanence=.21,
      connectedPermanence=.50,
      minThreshold=1,
      maxNewSynapseCount=3,
      permanenceIncrement=.10,
      permanenceDecrement=.10,
      predictedSegmentDecrement=0.0,
      seed=42)

    previousActiveColumns = [0, 1]
    prevWinnerCells = [0, 1]
    activeColumns = [4]

    matchingSegment = tm.connections.createSegment(4)
    tm.connections.createSynapse(matchingSegment, 0, .5)

    tm.compute(previousActiveColumns, True)
    self.assertEqual(prevWinnerCells, tm.getWinnerCells())

    tm.compute(activeColumns)

    synapses = tm.connections.synapsesForSegment(matchingSegment)
    self.assertEqual(2, len(synapses))

    for synapse in synapses:
      synapseData = tm.connections.dataForSynapse(synapse)
      if synapseData.presynapticCell != 0:
        self.assertAlmostEqual(.21, synapseData.permanence)
        self.assertEqual(prevWinnerCells[1], synapseData.presynapticCell)


  def testActiveSegmentGrowSynapsesAccordingToPotentialOverlap(self):
    """
    When a segment becomes active, grow synapses to previous winner cells.

    The number of grown synapses is calculated from the "matching segment"
    overlap, not the "active segment" overlap.
    """
    tm = TemporalMemory(
      columnDimensions=[32],
      cellsPerColumn=1,
      activationThreshold=2,
      initialPermanence=.21,
      connectedPermanence=.50,
      minThreshold=1,
      maxNewSynapseCount=4,
      permanenceIncrement=.10,
      permanenceDecrement=.10,
      predictedSegmentDecrement=0.0,
      seed=42)

    # Use 1 cell per column so that we have easy control over the winner cells.
    previousActiveColumns = [0, 1, 2, 3, 4]
    prevWinnerCells = [0, 1, 2, 3, 4]
    activeColumns = [5]

    activeSegment = tm.connections.createSegment(5)
    tm.connections.createSynapse(activeSegment, 0, .5)
    tm.connections.createSynapse(activeSegment, 1, .5)
    tm.connections.createSynapse(activeSegment, 2, .2)

    tm.compute(previousActiveColumns, True)
    self.assertEqual(prevWinnerCells, tm.getWinnerCells())
    tm.compute(activeColumns, True)

    presynapticCells = set(synapse.presynapticCell for synapse in
                           tm.connections.synapsesForSegment(activeSegment))
    self.assertTrue(presynapticCells == set([0, 1, 2, 3]) or
                    presynapticCells == set([0, 1, 2, 4]))


  def testDestroyWeakSynapseOnWrongPrediction(self):
    tm = TemporalMemory(
      columnDimensions=[32],
      cellsPerColumn=4,
      activationThreshold=3,
      initialPermanence=.2,
      connectedPermanence=.50,
      minThreshold=2,
      maxNewSynapseCount=4,
      permanenceIncrement=.10,
      permanenceDecrement=.10,
      predictedSegmentDecrement=0.02,
      seed=42)

    previousActiveColumns = [0]
    previousActiveCells = [0, 1, 2, 3]
    activeColumns = [2]
    expectedActiveCells = [5]

    activeSegment = tm.connections.createSegment(expectedActiveCells[0])
    tm.connections.createSynapse(activeSegment, previousActiveCells[0], .5)
    tm.connections.createSynapse(activeSegment, previousActiveCells[1], .5)
    tm.connections.createSynapse(activeSegment, previousActiveCells[2], .5)

    # Weak synapse.
    tm.connections.createSynapse(activeSegment, previousActiveCells[3], .015)

    tm.compute(previousActiveColumns, True)
    tm.compute(activeColumns, True)

    self.assertEqual(3, tm.connections.numSynapses(activeSegment))


  def testDestroyWeakSynapseOnActiveReinforce(self):
    tm = TemporalMemory(
      columnDimensions=[32],
      cellsPerColumn=4,
      activationThreshold=3,
      initialPermanence=.2,
      connectedPermanence=.50,
      minThreshold=2,
      maxNewSynapseCount=4,
      permanenceIncrement=.10,
      permanenceDecrement=.10,
      predictedSegmentDecrement=0.02,
      seed=42)

    previousActiveColumns = [0]
    previousActiveCells = [0, 1, 2, 3]
    activeColumns = [2]
    activeCell = 5

    activeSegment = tm.connections.createSegment(activeCell)
    tm.connections.createSynapse(activeSegment, previousActiveCells[0], .5)
    tm.connections.createSynapse(activeSegment, previousActiveCells[1], .5)
    tm.connections.createSynapse(activeSegment, previousActiveCells[2], .5)

    # Weak inactive synapse.
    tm.connections.createSynapse(activeSegment, previousActiveCells[3], .009)

    tm.compute(previousActiveColumns, True)
    tm.compute(activeColumns, True)

    self.assertEqual(3, tm.connections.numSynapses(activeSegment))


  def testRecycleWeakestSynapseToMakeRoomForNewSynapse(self):
    tm = TemporalMemory(
      columnDimensions=[32],
      cellsPerColumn=1,
      activationThreshold=3,
      initialPermanence=.21,
      connectedPermanence=.50,
      minThreshold=1,
      maxNewSynapseCount=3,
      permanenceIncrement=.02,
      permanenceDecrement=.02,
      predictedSegmentDecrement=0.0,
      seed=42,
      maxSynapsesPerSegment=3)

    prevActiveColumns = [0, 1, 2]
    prevWinnerCells = [0, 1, 2]
    activeColumns = [4]

    matchingSegment = tm.connections.createSegment(4)
    tm.connections.createSynapse(matchingSegment, 81, .6)

    weakestSynapse = tm.connections.createSynapse(matchingSegment, 0, .11)

    tm.compute(prevActiveColumns)
    self.assertEqual(prevWinnerCells, tm.getWinnerCells())
    tm.compute(activeColumns)

    synapses = tm.connections.synapsesForSegment(matchingSegment)
    self.assertEqual(3, len(synapses))
    presynapticCells = set(synapse.presynapticCell for synapse in synapses)
    self.assertFalse(0 in presynapticCells)


  def testRecycleLeastRecentlyActiveSegmentToMakeRoomForNewSegment(self):
    tm = TemporalMemory(
      columnDimensions=[32],
      cellsPerColumn=1,
      activationThreshold=3,
      initialPermanence=.50,
      connectedPermanence=.50,
      minThreshold=2,
      maxNewSynapseCount=3,
      permanenceIncrement=.02,
      permanenceDecrement=.02,
      predictedSegmentDecrement=0.0,
      seed=42,
      maxSegmentsPerCell=2)

    prevActiveColumns1 = [0, 1, 2]
    prevActiveColumns2 = [3, 4, 5]
    prevActiveColumns3 = [6, 7, 8]
    activeColumns = [9]

    tm.compute(prevActiveColumns1)
    tm.compute(activeColumns)

    self.assertEqual(1, tm.connections.numSegments(9))
    oldestSegment = list(tm.connections.segmentsForCell(9))[0]
    tm.reset()
    tm.compute(prevActiveColumns2)
    tm.compute(activeColumns)

    self.assertEqual(2, tm.connections.numSegments(9))

    oldPresynaptic = \
      set(synapse.presynapticCell
          for synapse in tm.connections.synapsesForSegment(oldestSegment))

    tm.reset()
    tm.compute(prevActiveColumns3)
    tm.compute(activeColumns)
    self.assertEqual(2, tm.connections.numSegments(9))

    # Verify none of the segments are connected to the cells the old
    # segment was connected to.

    for segment in tm.connections.segmentsForCell(9):
      newPresynaptic = set(synapse.presynapticCell
                           for synapse
                           in tm.connections.synapsesForSegment(segment))
      self.assertEqual([], list(oldPresynaptic & newPresynaptic))


  def testDestroySegmentsWithTooFewSynapsesToBeMatching(self):
    tm = TemporalMemory(
      columnDimensions=[32],
      cellsPerColumn=4,
      activationThreshold=3,
      initialPermanence=.2,
      connectedPermanence=.50,
      minThreshold=2,
      maxNewSynapseCount=4,
      permanenceIncrement=.10,
      permanenceDecrement=.10,
      predictedSegmentDecrement=0.02,
      seed=42)

    prevActiveColumns = [0]
    prevActiveCells = [0, 1, 2, 3]
    activeColumns = [2]
    expectedActiveCell = 5

    matchingSegment = tm.connections.createSegment(expectedActiveCell)
    tm.connections.createSynapse(matchingSegment, prevActiveCells[0], .015)
    tm.connections.createSynapse(matchingSegment, prevActiveCells[1], .015)
    tm.connections.createSynapse(matchingSegment, prevActiveCells[2], .015)
    tm.connections.createSynapse(matchingSegment, prevActiveCells[3], .015)

    tm.compute(prevActiveColumns, True)
    tm.compute(activeColumns, True)

    self.assertEqual(0, tm.connections.numSegments(expectedActiveCell))


  def testPunishMatchingSegmentsInInactiveColumns(self):
    tm = TemporalMemory(
      columnDimensions=[32],
      cellsPerColumn=4,
      activationThreshold=3,
      initialPermanence=.2,
      connectedPermanence=.50,
      minThreshold=2,
      maxNewSynapseCount=4,
      permanenceIncrement=.10,
      permanenceDecrement=.10,
      predictedSegmentDecrement=0.02,
      seed=42)

    previousActiveColumns = [0]
    previousActiveCells = [0, 1, 2, 3]
    activeColumns = [1]
    previousInactiveCell = 81

    activeSegment = tm.connections.createSegment(42)
    as1 = tm.connections.createSynapse(activeSegment,
                                       previousActiveCells[0], .5)
    as2 = tm.connections.createSynapse(activeSegment,
                                       previousActiveCells[1], .5)
    as3 = tm.connections.createSynapse(activeSegment,
                                       previousActiveCells[2], .5)
    is1 = tm.connections.createSynapse(activeSegment,
                                       previousInactiveCell, .5)

    matchingSegment = tm.connections.createSegment(43)
    as4 = tm.connections.createSynapse(matchingSegment,
                                       previousActiveCells[0], .5)
    as5 = tm.connections.createSynapse(matchingSegment,
                                       previousActiveCells[1], .5)
    is2 = tm.connections.createSynapse(matchingSegment,
                                       previousInactiveCell, .5)

    tm.compute(previousActiveColumns, True)
    tm.compute(activeColumns, True)

    self.assertAlmostEqual(.48, tm.connections.dataForSynapse(as1).permanence)
    self.assertAlmostEqual(.48, tm.connections.dataForSynapse(as2).permanence)
    self.assertAlmostEqual(.48, tm.connections.dataForSynapse(as3).permanence)
    self.assertAlmostEqual(.48, tm.connections.dataForSynapse(as4).permanence)
    self.assertAlmostEqual(.48, tm.connections.dataForSynapse(as5).permanence)
    self.assertAlmostEqual(.50, tm.connections.dataForSynapse(is1).permanence)
    self.assertAlmostEqual(.50, tm.connections.dataForSynapse(is2).permanence)


  def testAddSegmentToCellWithFewestSegments(self):
    grewOnCell1 = False
    grewOnCell2 = False
    for seed in xrange(100):
      tm = TemporalMemory(
        columnDimensions=[32],
        cellsPerColumn=4,
        activationThreshold=3,
        initialPermanence=.2,
        connectedPermanence=.50,
        minThreshold=2,
        maxNewSynapseCount=4,
        permanenceIncrement=.10,
        permanenceDecrement=.10,
        predictedSegmentDecrement=0.02,
        seed=seed)

      prevActiveColumns = [1, 2, 3, 4]
      activeColumns = [0]
      prevActiveCells = [4, 5, 6, 7]
      nonMatchingCells = [0, 3]
      activeCells = [0, 1, 2, 3]

      segment1 = tm.connections.createSegment(nonMatchingCells[0])
      tm.connections.createSynapse(segment1, prevActiveCells[0], .5)
      segment2 = tm.connections.createSegment(nonMatchingCells[1])
      tm.connections.createSynapse(segment2, prevActiveCells[1], .5)

      tm.compute(prevActiveColumns, True)
      tm.compute(activeColumns, True)

      self.assertEqual(activeCells, tm.getActiveCells())

      self.assertEqual(3, tm.connections.numSegments())
      self.assertEqual(1, tm.connections.numSegments(0))
      self.assertEqual(1, tm.connections.numSegments(3))
      self.assertEqual(1, tm.connections.numSynapses(segment1))
      self.assertEqual(1, tm.connections.numSynapses(segment2))

      segments = list(tm.connections.segmentsForCell(1))
      if len(segments) == 0:
        segments2 = list(tm.connections.segmentsForCell(2))
        self.assertFalse(len(segments2) == 0)
        grewOnCell2 = True
        segments.append(segments2[0])
      else:
        grewOnCell1 = True

      self.assertEqual(1, len(segments))
      synapses = list(tm.connections.synapsesForSegment(segments[0]))
      self.assertEqual(4, len(synapses))

      columnChecklist = set(prevActiveColumns)

      for synapse in synapses:
        synapseData = tm.connections.dataForSynapse(synapse)
        self.assertAlmostEqual(.2, synapseData.permanence)

        column = tm.columnForCell(synapseData.presynapticCell)
        self.assertTrue(column in columnChecklist)
        columnChecklist.remove(column)
      self.assertTrue(len(columnChecklist) == 0)

    self.assertTrue(grewOnCell1)
    self.assertTrue(grewOnCell2)


  def testConnectionsNeverChangeWhenLearningDisabled(self):
    tm = TemporalMemory(
      columnDimensions=[32],
      cellsPerColumn=4,
      activationThreshold=3,
      initialPermanence=.2,
      connectedPermanence=.50,
      minThreshold=2,
      maxNewSynapseCount=4,
      permanenceIncrement=.10,
      permanenceDecrement=.10,
      predictedSegmentDecrement=0.02,
      seed=42)

    prevActiveColumns = [0]
    prevActiveCells = [0, 1, 2, 3]
    activeColumns = [1, 2] #1 is predicted, 2 is bursting
    prevInactiveCell = 81
    expectedActiveCells = [4]

    correctActiveSegment = tm.connections.createSegment(expectedActiveCells[0])
    tm.connections.createSynapse(correctActiveSegment, prevActiveCells[0], .5)
    tm.connections.createSynapse(correctActiveSegment, prevActiveCells[1], .5)
    tm.connections.createSynapse(correctActiveSegment, prevActiveCells[2], .5)

    wrongMatchingSegment = tm.connections.createSegment(43)
    tm.connections.createSynapse(wrongMatchingSegment, prevActiveCells[0], .5)
    tm.connections.createSynapse(wrongMatchingSegment, prevActiveCells[1], .5)
    tm.connections.createSynapse(wrongMatchingSegment, prevInactiveCell, .5)

    before = copy.deepcopy(tm.connections)

    tm.compute(prevActiveColumns, False)
    tm.compute(activeColumns, False)

    self.assertEqual(before, tm.connections)


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
    expectedCells = [5, 6, 7, 8, 9]
    self.assertEqual(tm.cellsForColumn(1), expectedCells)


  def testCellsForColumn2D(self):
    tm = TemporalMemory(
      columnDimensions=[64, 64],
      cellsPerColumn=4
    )
    expectedCells = [256, 257, 258, 259]
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


  def testMaxSegmentsPerCellGetter(self):
    tm = TemporalMemory(
      columnDimensions=[64,64],
      cellsPerColumn=32,
      maxSegmentsPerCell=200
    )
    self.assertEqual(tm.getMaxSegmentsPerCell(), 200)

  
  def testMaxSynapsesPerSegmentGetter(self):
    tm = TemporalMemory(
      columnDimensions=[32,32],
      cellsPerColumn=16,
      maxSynapsesPerSegment=150
    )
    self.assertEqual(tm.getMaxSynapsesPerSegment(), 150)


  def serializationTestPrepare(self, tm):
    # Create an active segment and two matching segments.
    # Destroy a few to exercise the code.
    destroyMe1 = tm.connections.createSegment(4)
    tm.connections.destroySegment(destroyMe1)

    activeSegment = tm.connections.createSegment(4)
    tm.connections.createSynapse(activeSegment, 0, 0.5)
    tm.connections.createSynapse(activeSegment, 1, 0.5)
    destroyMe2 = tm.connections.createSynapse(activeSegment, 42, 0.5)
    tm.connections.destroySynapse(destroyMe2)
    tm.connections.createSynapse(activeSegment, 2, 0.5)
    tm.connections.createSynapse(activeSegment, 3, 0.5)

    matchingSegment1 = tm.connections.createSegment(8)
    tm.connections.createSynapse(matchingSegment1, 0, 0.4)
    tm.connections.createSynapse(matchingSegment1, 1, 0.4)
    tm.connections.createSynapse(matchingSegment1, 2, 0.4)

    matchingSegment2 = tm.connections.createSegment(9)
    tm.connections.createSynapse(matchingSegment2, 0, 0.4)
    tm.connections.createSynapse(matchingSegment2, 1, 0.4)
    tm.connections.createSynapse(matchingSegment2, 2, 0.4)
    tm.connections.createSynapse(matchingSegment2, 3, 0.4)

    tm.compute([0])

    self.assertEqual(len(tm.getActiveSegments()), 1)
    self.assertEqual(len(tm.getMatchingSegments()), 3)


  def serializationTestVerify(self, tm):
    # Activate 3 columns. One has an active segment, one has two matching
    # segments, and one has none. One column should be predicted, the others
    # should burst, there should be four segments total, and they should have
    # the correct permanences and synapse counts.
    prevWinnerCells = tm.getWinnerCells()
    self.assertEqual(len(prevWinnerCells), 1)

    tm.compute([1, 2, 3])

    # Verify the correct cells were activated.
    self.assertEqual(tm.getActiveCells(),
                     [4, 8, 9, 10, 11, 12, 13, 14, 15])
    winnerCells = tm.getWinnerCells()
    self.assertEqual(len(winnerCells), 3)
    self.assertEqual(winnerCells[0], 4)
    self.assertEqual(winnerCells[1], 9)

    self.assertEqual(tm.connections.numSegments(), 4)

    # Verify the active segment learned.
    self.assertEqual(tm.connections.numSegments(4), 1)
    activeSegment = tm.connections.segmentsForCell(4)[0]
    syns1 = tm.connections.synapsesForSegment(activeSegment)
    self.assertEqual(set([0, 1, 2, 3]),
                     set(s.presynapticCell for s in syns1))
    for s in syns1:
      self.assertAlmostEqual(s.permanence, 0.6)

    # Verify the non-best matching segment is unchanged.
    self.assertEqual(tm.connections.numSegments(8), 1)
    matchingSegment1 = tm.connections.segmentsForCell(8)[0]
    syns2 = tm.connections.synapsesForSegment(matchingSegment1)
    self.assertEqual(set([0, 1, 2]),
                     set(s.presynapticCell for s in syns2))
    for s in syns2:
      self.assertAlmostEqual(s.permanence, 0.4)

    # Verify the best matching segment learned.
    self.assertEqual(tm.connections.numSegments(9), 1)
    matchingSegment2 = tm.connections.segmentsForCell(9)[0]
    syns3 = tm.connections.synapsesForSegment(matchingSegment2)
    self.assertEqual(set([0, 1, 2, 3]),
                     set(s.presynapticCell for s in syns3))
    for s in syns3:
      self.assertAlmostEqual(s.permanence, 0.5)

    # Verify the winner cell in the last column grew a segment.
    winnerCell = winnerCells[2]
    self.assertGreaterEqual(winnerCell, 12)
    self.assertLess(winnerCell, 16)
    self.assertEqual(tm.connections.numSegments(winnerCell), 1)
    newSegment = tm.connections.segmentsForCell(winnerCell)[0]
    syns4 = tm.connections.synapsesForSegment(newSegment)
    self.assertEqual(set([prevWinnerCells[0]]),
                     set(s.presynapticCell for s in syns4))
    for s in syns4:
      self.assertAlmostEqual(s.permanence, 0.21)


  @unittest.skipUnless(
    capnp, "pycapnp is not installed, skipping serialization test.")
  def testWriteRead(self):
    tm1 = TemporalMemory(
      columnDimensions=(32,),
      cellsPerColumn=4,
      activationThreshold=3,
      initialPermanence=0.21,
      connectedPermanence=0.50,
      minThreshold=2,
      maxNewSynapseCount=3,
      permanenceIncrement=0.1,
      permanenceDecrement=0.1,
      predictedSegmentDecrement=0.0,
      seed=42
    )

    self.serializationTestPrepare(tm1)

    proto1 = TemporalMemoryProto_capnp.TemporalMemoryProto.new_message()
    tm1.write(proto1)

    # Write the proto to a temp file and read it back into a new proto
    with tempfile.TemporaryFile() as f:
      proto1.write(f)
      f.seek(0)
      proto2 = TemporalMemoryProto_capnp.TemporalMemoryProto.read(f)

    # Load the deserialized proto
    tm2 = TemporalMemory.read(proto2)

    self.assertEqual(tm1, tm2)
    self.serializationTestVerify(tm2)


  @unittest.skip("Manually enable this when you want to use it.")
  def testWriteTestFile(self):
    tm = TemporalMemory(
      columnDimensions=(32,),
      cellsPerColumn=4,
      activationThreshold=3,
      initialPermanence=0.21,
      connectedPermanence=0.50,
      minThreshold=2,
      maxNewSynapseCount=3,
      permanenceIncrement=0.1,
      permanenceDecrement=0.1,
      predictedSegmentDecrement=0.0,
      seed=42
    )

    self.serializationTestPrepare(tm)
    proto = TemporalMemoryProto_capnp.TemporalMemoryProto.new_message()
    tm.write(proto)
    with open("TemporalMemorySerializationWrite.tmp", "w") as f:
      proto.write(f)


  @unittest.skip("Manually enable this when you want to use it.")
  def testReadTestFile(self):
    with open("TemporalMemorySerializationWrite.tmp", "r") as f:
      proto = TemporalMemoryProto_capnp.TemporalMemoryProto.read(f)

    # Load the deserialized proto
    tm = TemporalMemory.read(proto)

    self.serializationTestVerify(tm)


if __name__ == '__main__':
  unittest.main()
