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
"""

import tempfile
import unittest

import capnp

#from nupic.bindings.proto import TemporalMemoryProto_capnp
from nupic.network.layer import Layer
from nupic.research.temporal_memory import TemporalMemory

from nupic.data.generators.pattern_machine import PatternMachine
from nupic.data.generators.sequence_machine import SequenceMachine



class TemporalMemoryTest(unittest.TestCase):


  def testInitInvalidParams(self):
    # Invalid layer
    kwargs = {"layer": None}
    self.assertRaises(ValueError, TemporalMemory, **kwargs)


  def testActivateCorrectlyPredictiveCells(self):
    tm = TemporalMemory()

    prevPredictiveCells = set([tm.layer.columns[0].cells[0],
                               tm.layer.columns[7].cells[13],
                               tm.layer.columns[32].cells[2],
                               tm.layer.columns[823].cells[1],
                               tm.layer.columns[823].cells[3],
                               tm.layer.columns[1735].cells[16]])
    activeColumns = set([tm.layer.columns[32],
                         tm.layer.columns[47],
                         tm.layer.columns[823]])
    prevMatchingCells = set()

    (activeCells,
    winnerCells,
    predictedColumns,
    predictedInactiveCells) = tm.activateCorrectlyPredictiveCells(prevPredictiveCells,
                                                                  prevMatchingCells,
                                                                  activeColumns)

    self.assertEqual(activeCells, set([tm.layer.columns[32].cells[2],
                                       tm.layer.columns[823].cells[1],
                                       tm.layer.columns[823].cells[3]]))
    self.assertEqual(winnerCells, set([tm.layer.columns[32].cells[2],
                                       tm.layer.columns[823].cells[1],
                                       tm.layer.columns[823].cells[3]]))
    self.assertEqual(predictedColumns, set([tm.layer.columns[32],
                                            tm.layer.columns[823]]))
    self.assertEqual(predictedInactiveCells, set())


  def testActivateCorrectlyPredictiveCellsEmpty(self):
    tm = TemporalMemory()

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
    activeColumns = set([tm.layer.columns[32],
                         tm.layer.columns[47],
                         tm.layer.columns[823]])
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

    prevPredictiveCells = set([tm.layer.columns[0].cells[0],
                               tm.layer.columns[7].cells[13],
                               tm.layer.columns[32].cells[2],
                               tm.layer.columns[823].cells[1],
                               tm.layer.columns[823].cells[3],
                               tm.layer.columns[1735].cells[16]])
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
    tm = TemporalMemory()

    tm.predictedSegmentDecrement = 0.001
    prevPredictiveCells = set([])
    activeColumns = set([tm.layer.columns[32],
                         tm.layer.columns[47],
                         tm.layer.columns[823]])
    prevMatchingCells = set([tm.layer.columns[1].cells[0],
                             tm.layer.columns[1].cells[15]])

    (activeCells,
    winnerCells,
    predictedColumns,
    predictedInactiveCells) = tm.activateCorrectlyPredictiveCells(prevPredictiveCells,
                                                                  prevMatchingCells,
                                                                  activeColumns)

    self.assertEqual(activeCells, set([]))
    self.assertEqual(winnerCells, set([]))
    self.assertEqual(predictedColumns, set([]))
    self.assertEqual(predictedInactiveCells, set([tm.layer.columns[1].cells[0],
                                                  tm.layer.columns[1].cells[15]]))

  def testBurstColumns(self):
    tm = TemporalMemory(
      layer=Layer(numCellsPerColumn=4),
      connectedPermanence=0.50,
      minThreshold=1,
      seed=42
    )

    segment1 = tm.layer.columns[0].cells[0].createSegment()
    segment1.createSynapse(presynapticCell=tm.layer.columns[5].cells[3], permanence=0.6)
    segment1.createSynapse(presynapticCell=tm.layer.columns[9].cells[1], permanence=0.4)
    segment1.createSynapse(presynapticCell=tm.layer.columns[119].cells[1], permanence=0.9)

    segment2 = tm.layer.columns[0].cells[0].createSegment()
    segment2.createSynapse(presynapticCell=tm.layer.columns[12].cells[1], permanence=0.9)
    segment2.createSynapse(presynapticCell=tm.layer.columns[0].cells[3], permanence=0.8)

    segment3 = tm.layer.columns[0].cells[1].createSegment()
    segment3.createSynapse(presynapticCell=tm.layer.columns[183].cells[1], permanence=0.7)

    segment4 = tm.layer.columns[27].cells[0].createSegment()
    segment4.createSynapse(presynapticCell=tm.layer.columns[121].cells[2], permanence=0.9)

    activeColumns = set([tm.layer.columns[0],
                         tm.layer.columns[1],
                         tm.layer.columns[26]])
    predictedColumns = set([tm.layer.columns[26]])
    prevActiveCells = set([tm.layer.columns[5].cells[3],
                           tm.layer.columns[9].cells[1],
                           tm.layer.columns[12].cells[1],
                           tm.layer.columns[183].cells[1]])
    prevWinnerCells = set([tm.layer.columns[5].cells[3],
                           tm.layer.columns[9].cells[1],
                           tm.layer.columns[12].cells[1],
                           tm.layer.columns[183].cells[1]])

    (activeCells,
     winnerCells,
     learningSegments) = tm.burstColumns(activeColumns,
                                         predictedColumns,
                                         prevActiveCells,
                                         prevWinnerCells)

    # 5 is the new segment was added to winner cell (6) in column 1
    segment5 = list(tm.layer.columns[1].cells[2].segments)[0]

    self.assertEqual(activeCells, set([tm.layer.columns[0].cells[0],
                                       tm.layer.columns[0].cells[1],
                                       tm.layer.columns[0].cells[2],
                                       tm.layer.columns[0].cells[3],
                                       tm.layer.columns[1].cells[0],
                                       tm.layer.columns[1].cells[1],
                                       tm.layer.columns[1].cells[2],
                                       tm.layer.columns[1].cells[3]]))
    self.assertEqual(winnerCells, set([tm.layer.columns[0].cells[0],
                                       tm.layer.columns[1].cells[2]]))  # 6 is randomly chosen cell
    self.assertEqual(learningSegments, set([segment1, segment5]))


  def testBurstColumnsEmpty(self):
    tm = TemporalMemory()

    activeColumns    = set()
    predictedColumns = set()
    prevActiveCells = set()
    prevWinnerCells = set()

    (activeCells,
     winnerCells,
     learningSegments) = tm.burstColumns(activeColumns,
                                         predictedColumns,
                                         prevActiveCells,
                                         prevWinnerCells)

    self.assertEqual(activeCells,      set())
    self.assertEqual(winnerCells,      set())
    self.assertEqual(learningSegments, set())


  def testLearnOnSegments(self):
    tm = TemporalMemory(maxNewSynapseCount=2)

    segment1 = tm.layer.columns[0].cells[0].createSegment()
    synapse1 = segment1.createSynapse(presynapticCell=tm.layer.columns[0].cells[23], permanence=0.6)
    synapse2 = segment1.createSynapse(presynapticCell=tm.layer.columns[1].cells[5], permanence=0.4)
    synapse3 = segment1.createSynapse(presynapticCell=tm.layer.columns[14].cells[29], permanence=0.9)

    segment2 = tm.layer.columns[0].cells[1].createSegment()
    synapse4 = segment2.createSynapse(presynapticCell=tm.layer.columns[22].cells[29], permanence=0.7)

    segment3 = tm.layer.columns[0].cells[8].createSegment()
    synapse5 = segment3.createSynapse(presynapticCell=tm.layer.columns[15].cells[6], permanence=0.9)

    segment4 = tm.layer.columns[3].cells[4].createSegment()

    prevActiveSegments = set([segment1, segment3])
    learningSegments = set([segment2, segment4])
    prevActiveCells = set([tm.layer.columns[0].cells[23],
                           tm.layer.columns[1].cells[5],
                           tm.layer.columns[22].cells[29]])
    winnerCells = set([tm.layer.columns[0].cells[0]])
    prevWinnerCells = set([tm.layer.columns[0].cells[10],
                           tm.layer.columns[0].cells[11],
                           tm.layer.columns[0].cells[12],
                           tm.layer.columns[0].cells[13],
                           tm.layer.columns[0].cells[14]])
    predictedInactiveCells = set()
    prevMatchingSegments = set()

    tm.learnOnSegments(prevActiveSegments,
                       learningSegments,
                       prevActiveCells,
                       winnerCells,
                       prevWinnerCells,
                       predictedInactiveCells,
                       prevMatchingSegments)

    # Check segment 1
    self.assertAlmostEqual(synapse1.permanence, 0.7)
    self.assertAlmostEqual(synapse2.permanence, 0.5)
    self.assertAlmostEqual(synapse3.permanence, 0.8)

    # Check segment 2
    self.assertAlmostEqual(synapse4.permanence, 0.8)
    self.assertEqual(len(segment2.synapses), 2)

    # Check segment 3
    self.assertAlmostEqual(synapse5.permanence, 0.9)
    self.assertEqual(len(segment3.synapses), 1)

    # Check segment 4
    self.assertEqual(len(segment4.synapses), 2)


  def testComputePredictiveCells(self):
    tm = TemporalMemory(
      layer=Layer(columnDimensions=[2048], numCellsPerColumn=32),
      activationThreshold=2,
      minThreshold=2,
      predictedSegmentDecrement=0.004)

    segment1 = tm.layer.columns[0].cells[0].createSegment()
    segment1.createSynapse(presynapticCell=tm.layer.columns[0].cells[23], permanence=0.6)
    segment1.createSynapse(presynapticCell=tm.layer.columns[1].cells[5], permanence=0.5)
    segment1.createSynapse(presynapticCell=tm.layer.columns[14].cells[29], permanence=0.9)

    segment2 = tm.layer.columns[0].cells[1].createSegment()
    segment2.createSynapse(presynapticCell=tm.layer.columns[22].cells[29], permanence=0.7)
    segment2.createSynapse(presynapticCell=tm.layer.columns[22].cells[29], permanence=0.4)

    segment3 = tm.layer.columns[0].cells[1].createSegment()
    segment3.createSynapse(presynapticCell=tm.layer.columns[30].cells[14], permanence=0.9)

    segment4 = tm.layer.columns[0].cells[8].createSegment()
    segment4.createSynapse(presynapticCell=tm.layer.columns[15].cells[6], permanence=0.9)

    segment5 = tm.layer.columns[3].cells[4].createSegment()

    activeCells = set([tm.layer.columns[0].cells[23],
                       tm.layer.columns[1].cells[5],
                       tm.layer.columns[22].cells[29],
                       tm.layer.columns[30].cells[14]])

    (activeSegments,
     predictiveCells,
     matchingSegments,
     matchingCells) = tm.computePredictiveCells(activeCells)
    self.assertEqual(activeSegments, set([segment1]))
    self.assertEqual(predictiveCells, set([tm.layer.columns[0].cells[0]]))
    self.assertEqual(matchingSegments, set([segment1, segment2]))
    self.assertEqual(matchingCells, set([tm.layer.columns[0].cells[0],
                                         tm.layer.columns[0].cells[1]]))


  def testBestMatchingCell(self):
    tm = TemporalMemory(
      connectedPermanence=0.50,
      minThreshold=1,
      seed=42
    )

    segment1 = tm.layer.columns[0].cells[0].createSegment()
    segment1.createSynapse(presynapticCell=tm.layer.columns[0].cells[23], permanence=0.6)
    segment1.createSynapse(presynapticCell=tm.layer.columns[1].cells[5], permanence=0.4)
    segment1.createSynapse(presynapticCell=tm.layer.columns[14].cells[29], permanence=0.9)

    segment2 = tm.layer.columns[0].cells[0].createSegment()
    segment2.createSynapse(presynapticCell=tm.layer.columns[1].cells[17], permanence=0.9)
    segment2.createSynapse(presynapticCell=tm.layer.columns[0].cells[3], permanence=0.8)

    segment3 = tm.layer.columns[0].cells[1].createSegment()
    segment3.createSynapse(presynapticCell=tm.layer.columns[22].cells[29], permanence=0.7)

    segment4 = tm.layer.columns[3].cells[12].createSegment()
    segment4.createSynapse(presynapticCell=tm.layer.columns[15].cells[6], permanence=0.9)

    activeCells = set([tm.layer.columns[0].cells[23],
                       tm.layer.columns[1].cells[5],
                       tm.layer.columns[1].cells[17],
                       tm.layer.columns[22].cells[29]])

    self.assertEqual(tm.bestMatchingCell(tm.layer.columns[0].cells,
                                         activeCells),
                     (tm.layer.columns[0].cells[0], segment1))

    self.assertEqual(tm.bestMatchingCell(tm.layer.columns[3].cells,  # column containing cell 108
                                         activeCells),
                     (tm.layer.columns[3].cells[0], None))  # Random cell from column

    self.assertEqual(tm.bestMatchingCell(tm.layer.columns[999].cells,
                                         activeCells),
                     (tm.layer.columns[999].cells[4], None))  # Random cell from column


  def testBestMatchingCellFewestSegments(self):
    tm = TemporalMemory(
      layer=Layer(columnDimensions=[2], numCellsPerColumn=2),
      connectedPermanence=0.50,
      minThreshold=1,
      seed=42
    )

    segment1 = tm.layer.columns[0].cells[0].createSegment()
    segment1.createSynapse(presynapticCell=tm.layer.columns[1].cells[1], permanence=0.3)

    activeSynapsesForSegment = set([])

    for _ in range(100):
      # Never pick cell 0, always pick cell 1
      (cell, _) = tm.bestMatchingCell(tm.layer.columns[0].cells,
                                      activeSynapsesForSegment)
      self.assertEqual(cell, tm.layer.columns[0].cells[1])


  def testBestMatchingSegment(self):
    tm = TemporalMemory(
      layer=Layer(columnDimensions=[2048], numCellsPerColumn=32),
      connectedPermanence=0.50,
      minThreshold=1
    )

    segment1 = tm.layer.columns[0].cells[0].createSegment()
    segment1.createSynapse(presynapticCell=tm.layer.columns[0].cells[23], permanence=0.6)
    segment1.createSynapse(presynapticCell=tm.layer.columns[1].cells[5], permanence=0.4)
    segment1.createSynapse(presynapticCell=tm.layer.columns[14].cells[29], permanence=0.9)

    segment2 = tm.layer.columns[0].cells[0].createSegment()
    segment2.createSynapse(presynapticCell=tm.layer.columns[1].cells[17], permanence=0.9)
    segment2.createSynapse(presynapticCell=tm.layer.columns[0].cells[3], permanence=0.8)

    segment3 = tm.layer.columns[0].cells[1].createSegment()
    segment3.createSynapse(presynapticCell=tm.layer.columns[22].cells[29], permanence=0.7)

    segment4 = tm.layer.columns[0].cells[8].createSegment()
    segment4.createSynapse(presynapticCell=tm.layer.columns[15].cells[6], permanence=0.9)

    activeCells = set([tm.layer.columns[0].cells[23],
                       tm.layer.columns[1].cells[5],
                       tm.layer.columns[1].cells[17],
                       tm.layer.columns[22].cells[29]])

    self.assertEqual(tm.bestMatchingSegment(tm.layer.columns[0].cells[0],
                                            activeCells),
                     (segment1, 2))

    self.assertEqual(tm.bestMatchingSegment(tm.layer.columns[0].cells[1],
                                            activeCells),
                     (segment3, 1))

    self.assertEqual(tm.bestMatchingSegment(tm.layer.columns[0].cells[8],
                                            activeCells),
                     (None, None))

    self.assertEqual(tm.bestMatchingSegment(tm.layer.columns[3].cells[4],
                                            activeCells),
                     (None, None))


  def testLeastUsedCell(self):
    tm = TemporalMemory(
      layer=Layer(columnDimensions=[2], numCellsPerColumn=2),
      seed=42
    )

    segment1 = tm.layer.columns[0].cells[0].createSegment()
    segment1.createSynapse(presynapticCell=tm.layer.columns[1].cells[1], permanence=0.3)

    for _ in range(100):
      # Never pick cell 0, always pick cell 1
      self.assertEqual(tm.leastUsedCell(tm.layer.columns[0].cells),
                       tm.layer.columns[0].cells[1])


  def testAdaptSegment(self):
    tm = TemporalMemory(
      layer=Layer(columnDimensions=[2048], numCellsPerColumn=32)
    )

    segment1 = tm.layer.columns[0].cells[0].createSegment()
    synapse1 = segment1.createSynapse(presynapticCell=tm.layer.columns[0].cells[23], permanence=0.6)
    synapse2 = segment1.createSynapse(presynapticCell=tm.layer.columns[1].cells[5], permanence=0.4)
    synapse3 = segment1.createSynapse(presynapticCell=tm.layer.columns[14].cells[29], permanence=0.9)

    tm.adaptSegment(segment1, set([synapse1, synapse2]),
                    tm.permanenceIncrement,
                    tm.permanenceDecrement)

    self.assertAlmostEqual(synapse1.permanence, 0.7)
    self.assertAlmostEqual(synapse2.permanence, 0.5)
    self.assertAlmostEqual(synapse3.permanence, 0.8)


  def testAdaptSegmentToMax(self):
    tm = TemporalMemory()

    segment1 = tm.layer.columns[0].cells[0].createSegment()
    synapse1 = segment1.createSynapse(presynapticCell=tm.layer.columns[0].cells[23], permanence=0.9)

    tm.adaptSegment(segment1, set([synapse1]),
                    tm.permanenceIncrement,
                    tm.permanenceDecrement)
    self.assertAlmostEqual(synapse1.permanence, 1.0)

    # Now permanence should be at max
    tm.adaptSegment(segment1, set([synapse1]),
                    tm.permanenceIncrement,
                    tm.permanenceDecrement)
    self.assertAlmostEqual(synapse1.permanence, 1.0)


  def testAdaptSegmentToMin(self):
    tm = TemporalMemory()

    segment1 = tm.layer.columns[0].cells[0].createSegment()
    synapse1 = segment1.createSynapse(presynapticCell=tm.layer.columns[0].cells[23], permanence=0.1)

    tm.adaptSegment(segment1, set(),
                    tm.permanenceIncrement,
                    tm.permanenceDecrement)

    synapses = segment1.synapses
    self.assertFalse(synapse1 in synapses)


  def testPickCellsToLearnOn(self):
    tm = TemporalMemory(seed=42)

    segment1 = tm.layer.columns[0].cells[0].createSegment()

    winnerCells = set([tm.layer.columns[0].cells[4],
                       tm.layer.columns[1].cells[15],
                       tm.layer.columns[1].cells[26],
                       tm.layer.columns[2].cells[29]])

    self.assertEqual(tm.pickCellsToLearnOn(2, segment1, winnerCells),
                     set([tm.layer.columns[2].cells[29],
                          tm.layer.columns[1].cells[26]]))  # randomly picked

    self.assertEqual(tm.pickCellsToLearnOn(100, segment1, winnerCells),
                     set([tm.layer.columns[0].cells[4],
                          tm.layer.columns[1].cells[15],
                          tm.layer.columns[1].cells[26],
                          tm.layer.columns[2].cells[29]]))

    self.assertEqual(tm.pickCellsToLearnOn(0, segment1, winnerCells),
                     set())


  def testPickCellsToLearnOnAvoidDuplicates(self):
    tm = TemporalMemory(seed=42)

    segment1 = tm.layer.columns[0].cells[0].createSegment()
    segment1.createSynapse(presynapticCell=tm.layer.columns[0].cells[23], permanence=0.6)

    winnerCells = set([tm.layer.columns[0].cells[23]])

    # Ensure that no additional (duplicate) cells were picked
    self.assertEqual(tm.pickCellsToLearnOn(2, segment1, winnerCells),
                     set())


  @unittest.skip("Remove this skip")
  def testWrite(self):
    tm1 = TemporalMemory(
      layer=Layer(columnDimensions=[100], numCellsPerColumn=4),
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
    self.assertEqual(tm1.activeCells, tm2.activeCells)
    self.assertEqual(tm1.predictiveCells, tm2.predictiveCells)
    self.assertEqual(tm1.winnerCells, tm2.winnerCells)

    tm1.compute(self.patternMachine.get(3))
    tm2.compute(self.patternMachine.get(3))
    self.assertEqual(tm1.activeCells, tm2.activeCells)
    self.assertEqual(tm1.predictiveCells, tm2.predictiveCells)
    self.assertEqual(tm1.winnerCells, tm2.winnerCells)



if __name__ == '__main__':
  unittest.main()
