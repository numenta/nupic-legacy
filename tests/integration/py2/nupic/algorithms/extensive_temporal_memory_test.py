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

from prettytable import PrettyTable
from random import shuffle
import unittest2 as unittest

from nupic.data.pattern_machine import PatternMachine

from abstract_temporal_memory_test import AbstractTemporalMemoryTest



class ExtensiveTemporalMemoryTest(AbstractTemporalMemoryTest):
  """
  ==============================================================================
                  Basic First Order Sequences
  ==============================================================================

  These tests ensure the most basic (first order) sequence learning mechanism is
  working.

  Parameters: Use a "fast learning mode": initPerm should be greater than
  connectedPerm and permanenceDec should be zero. With these settings sequences
  should be learned in one pass:

    minThreshold = newSynapseCount
    initialPermanence = 0.8
    connectedPermanence = 0.7
    permanenceDecrement = 0
    permanenceIncrement = 0.4

  Other Parameters:
    columnDimensions = [100]
    cellsPerColumn = 1
    newSynapseCount = 11
    activationThreshold = 8

  Note: this is not a high order sequence, so one cell per column is fine.

  Input Sequence: We train with M input sequences, each consisting of N random
  patterns. Each pattern consists of a 2 bits on.

  Training: The TP is trained with P passes of the M sequences. There
  should be a reset between sequences. The total number of iterations during
  training is P*N*M.

  Testing: Run inference through the same set of sequences, with a reset before
  each sequence. For each sequence the system should accurately predict the
  pattern at the next time step up to and including the N-1'st pattern. The number
  of predicted inactive cells at each time step should be reasonably low.

  We can also calculate the number of synapses that should be
  learned. We raise an error if too many or too few were learned.

  B1) Basic sequence learner.  M=1, N=100, P=1.

  B2) Same as above, except P=2. Test that permanences go up and that no
  additional synapses are learned. [TODO]

  B3) N=300, M=1, P=1. (See how high we can go with N)

  B4) N=100, M=3, P=1. (See how high we can go with N*M) [TODO]

  B5) Like B1 but with cellsPerColumn = 4. First order sequences should still
  work just fine. [TODO]

  B6) Like B1 but with slower learning. Set the following parameters differently:

      activationThreshold = newSynapseCount
      minThreshold = activationThreshold
      initialPerm = 0.2
      connectedPerm = 0.7
      permanenceInc = 0.2

  Now we train the TP with the B1 sequence 4 times (P=4). This will increment
  the permanences to be above 0.8 and at that point the inference will be correct.
  This test will ensure the basic match function and segment activation rules are
  working correctly. [TODO]

  B7) Like B6 but with 4 cells per column. Should still work. [TODO]

  B8) Like B6 but present the sequence less than 4 times: the inference should be
  incorrect. [TODO]

  B9) Like B2, except that cells per column = 4. Should still add zero additional
  synapses. [TODO]
  """

  DEFAULT_TM_PARAMS = {
    "columnDimensions": [100],
    "cellsPerColumn": 1,
    "initialPermanence": 0.8,
    "connectedPermanence": 0.7,
    "minThreshold": 11,
    "maxNewSynapseCount": 11,
    "permanenceIncrement": 0.4,
    "permanenceDecrement": 0,
    "activationThreshold": 8
  }


  def testB1(self):
    """Basic sequence learner.  M=1, N=100, P=1."""
    self.initTM()
    self.finishSetUp(PatternMachine(
      self.tm.connections.numberOfColumns(), 23))

    numbers = range(100)
    shuffle(numbers)
    sequence = self.sequenceMachine.generateFromNumbers(numbers)
    sequence.append(None)

    self.feedTM(sequence)

    _, stats = self._testTM(sequence)

    sumUnpredictedActiveColumns = stats[4][2]
    self.assertEqual(sumUnpredictedActiveColumns, 0)

    averagePredictedActiveColumns = stats[2][3]
    self.assertEqual(averagePredictedActiveColumns, 23)

    maxPredictedInactiveColumns = stats[1][1]
    self.assertTrue(maxPredictedInactiveColumns < 3)


  def testB3(self):
    """N=300, M=1, P=1. (See how high we can go with N)"""
    self.initTM()
    self.finishSetUp(PatternMachine(
      self.tm.connections.numberOfColumns(), 23, num=300))

    numbers = range(300)
    shuffle(numbers)
    sequence = self.sequenceMachine.generateFromNumbers(numbers)
    sequence.append(None)

    self.feedTM(sequence)

    _, stats = self._testTM(sequence)

    sumUnpredictedActiveColumns = stats[4][2]
    self.assertEqual(sumUnpredictedActiveColumns, 0)

    averagePredictedActiveColumns = stats[2][3]
    self.assertEqual(averagePredictedActiveColumns, 23)

    maxPredictedInactiveColumns = stats[1][1]
    self.assertTrue(maxPredictedInactiveColumns < 15)


  # ==============================
  # Overrides
  # ==============================

  @classmethod
  def setUpClass(cls):
    cls.allStats = []


  @classmethod
  def tearDownClass(cls):
    cols = ["Test",
            "predicted active cells (stats)",
            "predicted inactive cells (stats)",
            "predicted active columns (stats)",
            "predicted inactive columns (stats)",
            "unpredicted active columns (stats)"]

    table = PrettyTable(cols)

    for stats in cls.allStats:
      row = [stats[0]] + list(stats[1])
      table.add_row(row)

    print table
    print "(stats) => (min, max, sum, average, standard deviation)"


  # ==============================
  # Helper functions
  # ==============================

  def _testTM(self, sequence):
    detailedResults = self.feedTM(sequence, learn=False)
    stats = self.tmTestMachine.computeStatistics(detailedResults, sequence)

    self.allStats.append((self.id(), stats))

    return detailedResults, stats



if __name__ == "__main__":
  unittest.main()

