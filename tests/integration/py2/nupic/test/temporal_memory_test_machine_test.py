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
import unittest

from nupic.data.pattern_machine import ConsecutivePatternMachine
from nupic.data.sequence_machine import SequenceMachine
from nupic.test.temporal_memory_test_machine import TemporalMemoryTestMachine
from nupic.research.temporal_memory import TemporalMemory



class TemporalMemoryTestMachineTest(unittest.TestCase):


  def setUp(self):
    self.patternMachine = ConsecutivePatternMachine(100, 5)
    self.sequenceMachine = SequenceMachine(self.patternMachine)

    self.tm = TemporalMemory(columnDimensions=[100],
                             cellsPerColumn=4,
                             initialPermanence=0.4,
                             connectedPermanence=0.5,
                             minThreshold=1,
                             maxNewSynapseCount=6,
                             permanenceIncrement=0.1,
                             permanenceDecrement=0.05,
                             activationThreshold=1)

    self.tmTestMachine = TemporalMemoryTestMachine(self.tm)


  def testFeedSequence(self):
    sequence = self._generateSequence()
    results = self.tmTestMachine.feedSequence(sequence)

    self.assertEqual(len(results), len(sequence))
    self.assertEqual(len(results[-2]), 5)
    self.assertEqual(len(results[-1]), 0)


  def testComputeDetailedResults(self):
    sequence = self._generateSequence()

    # Replace last pattern with an unpredicted one
    sequence[-1] = self.patternMachine.get(4)

    results = self.tmTestMachine.feedSequence(sequence)

    detailedResults = self.tmTestMachine.computeDetailedResults(results,
                                                                sequence)
    (
    predictedActiveCellsList,
    predictedInactiveCellsList,
    predictedActiveColumnsList,
    predictedInactiveColumnsList,
    unpredictedActiveColumnsList
    ) = detailedResults

    self.assertEqual(len(predictedActiveCellsList), len(sequence))
    self.assertEqual(len(predictedInactiveCellsList), len(sequence))
    self.assertEqual(len(predictedActiveColumnsList), len(sequence))
    self.assertEqual(len(predictedInactiveColumnsList), len(sequence))
    self.assertEqual(len(unpredictedActiveColumnsList), len(sequence))

    self.assertEqual(len(predictedActiveCellsList[-1]), 0)
    self.assertEqual(len(predictedInactiveCellsList[-1]), 5)
    self.assertEqual(len(predictedActiveColumnsList[-1]), 0)
    self.assertEqual(len(predictedInactiveColumnsList[-1]), 5)
    self.assertEqual(len(unpredictedActiveColumnsList[-1]), 5)


  def testComputeStatistics(self):
    sequence = self._generateSequence()

    results = self.tmTestMachine.feedSequence(sequence)
    detailedResults = self.tmTestMachine.computeDetailedResults(results,
                                                                sequence)
    stats = self.tmTestMachine.computeStatistics(detailedResults, sequence)

    self.assertEqual(len(stats), 5)
    self.assertEqual(stats[1][2], 0)
    self.assertEqual(stats[3][2], 0)


  # ==============================
  # Helper functions
  # ==============================

  def _generateSequence(self):
    numbers = range(0, 10)
    sequence = self.sequenceMachine.generateFromNumbers(numbers)
    sequence = ([None] + sequence) * 3

    return sequence



if __name__ == '__main__':
  unittest.main()
