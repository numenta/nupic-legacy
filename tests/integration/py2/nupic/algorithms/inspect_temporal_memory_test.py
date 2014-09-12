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
from nupic.research.inspect_temporal_memory import InspectTemporalMemory



class InspectTemporalMemoryTest(unittest.TestCase):


  def setUp(self):
    self.patternMachine = ConsecutivePatternMachine(100, 5)
    self.sequenceMachine = SequenceMachine(self.patternMachine)

    self.tm = InspectTemporalMemory(columnDimensions=[100],
                                    cellsPerColumn=4,
                                    initialPermanence=0.6,
                                    connectedPermanence=0.5,
                                    minThreshold=1,
                                    maxNewSynapseCount=6,
                                    permanenceIncrement=0.1,
                                    permanenceDecrement=0.05,
                                    activationThreshold=1)


  def testFeedSequence(self):
    sequence = self._generateSequence()

    # Replace last pattern (before the None) with an unpredicted one
    sequence[-2] = self.patternMachine.get(4)

    self._feedSequence(sequence)

    self.assertEqual(len(self.tm.predictedActiveCellsList), len(sequence))
    self.assertEqual(len(self.tm.predictedInactiveCellsList), len(sequence))
    self.assertEqual(len(self.tm.predictedActiveColumnsList), len(sequence))
    self.assertEqual(len(self.tm.predictedInactiveColumnsList), len(sequence))
    self.assertEqual(len(self.tm.unpredictedActiveColumnsList), len(sequence))

    self.assertEqual(len(self.tm.predictedActiveCellsList[-2]), 0)
    self.assertEqual(len(self.tm.predictedInactiveCellsList[-2]), 5)
    self.assertEqual(len(self.tm.predictedActiveColumnsList[-2]), 0)
    self.assertEqual(len(self.tm.predictedInactiveColumnsList[-2]), 5)
    self.assertEqual(len(self.tm.unpredictedActiveColumnsList[-2]), 5)


  def testComputeStatistics(self):
    sequence = self._generateSequence()

    self._feedSequence(sequence)  # train
    self.tm.clearHistory()
    self._feedSequence(sequence)  # test
    stats = self.tm.getStatistics()

    self.assertEqual(len(stats), 5)
    self.assertEqual(stats[1][2], 0)
    self.assertEqual(stats[3][2], 0)
    self.assertEqual(stats[4][2], 0)


  # ==============================
  # Helper functions
  # ==============================

  def _generateSequence(self):
    numbers = range(0, 10)
    sequence = self.sequenceMachine.generateFromNumbers(numbers)
    sequence.append(None)
    sequence *= 3

    return sequence


  def _feedSequence(self, sequence):
    for pattern in sequence:
      if pattern is None:
        self.tm.reset()
      else:
        self.tm.compute(pattern)



if __name__ == '__main__':
  unittest.main()
