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
    activationThreshold = 11

  Note: this is not a high order sequence, so one cell per column is fine.

  Input Sequence: We train with M input sequences, each consisting of N random
  patterns. Each pattern consists of a random number of bits on. The number of
  1's in each pattern should be between 21 and 25 columns.

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

  B4) N=100, M=3, P=1. (See how high we can go with N*M)

  B5) Like B1 but with cellsPerColumn = 4. First order sequences should still
  work just fine.

  B6) Like B1 but with slower learning. Set the following parameters differently:

      initialPermanence = 0.2
      connectedPermanence = 0.7
      permanenceIncrement = 0.2

  Now we train the TP with the B1 sequence 4 times (P=4). This will increment
  the permanences to be above 0.8 and at that point the inference will be correct.
  This test will ensure the basic match function and segment activation rules are
  working correctly.

  B7) Like B6 but with 4 cells per column. Should still work.

  B8) Like B6 but present the sequence less than 4 times: the inference should be
  incorrect.

  B9) Like B2, except that cells per column = 4. Should still add zero additional
  synapses. [TODO]


  ===============================================================================
                  High Order Sequences
  ===============================================================================

  These tests ensure that high order sequences can be learned in a multiple cells
  per column instantiation.

  Parameters: Same as Basic First Order Tests above, but with varying cells per
  column.

  Input Sequence: We train with M input sequences, each consisting of N random
  patterns. Each pattern consists of a random number of bits on. The number of
  1's in each pattern should be between 21 and 25 columns. The sequences are
  constructed to contain shared subsequences, such as:

  A B C D E F G H I J
  K L M D E F N O P Q

  The position and length of shared subsequences are parameters in the tests.

  Training: Identical to basic first order tests above.

  Testing: Identical to basic first order tests above unless noted.

  We can also calculate the number of segments and synapses that should be
  learned. We raise an error if too many or too few were learned.

  H1) Learn two sequences with a short shared pattern. Parameters
  should be the same as B1. This test will FAIL since cellsPerCol == 1. No
  consecutive patterns share any column. [TODO]

  H2) As above but with cellsPerCol == 4. This test should PASS. No consecutive
  patterns share any column. [TODO]

  H2a) Same as above, except P=2. Test that permanences go up and that no
  additional synapses or segments are learned. [TODO]

  H3) Same parameters as H.2 except sequences are created such that they share a
  single significant sub-sequence. Subsequences should be reasonably long and in
  the middle of sequences. No consecutive patterns share any column. [TODO]

  H4) Like H.3, except the shared subsequence is in the beginning. (e.g.
  "ABCDEF" and "ABCGHIJ". At the point where the shared subsequence ends, all
  possible next patterns should be predicted. As soon as you see the first unique
  pattern, the predictions should collapse to be a perfect prediction. [TODO]

  H5) Shared patterns. Similar to H3 except that patterns are shared between
  sequences.  All sequences are different shufflings of the same set of N
  patterns (there is no shared subsequence). Care should be taken such that the
  same three patterns never follow one another in two sequences. [TODO]

  H6) Combination of H5) and H3). Shared patterns in different sequences, with a
  shared subsequence. [TODO]

  H7) Stress test: every other pattern is shared. [TODO]

  H8) Start predicting in the middle of a sequence. [TODO]

  H9) Hub capacity. How many patterns can use that hub? [TODO]

  H10) Sensitivity to small amounts of noise during inference. [TODO]

  H11) Higher order patterns with alternating elements.

  Create the following 4 sequences:

       A B A B A C
       A B A B D E
       A B F G H I
       A J K L M N

  After training we should verify that the expected transitions are in the
  model. Prediction accuracy should be perfect. In addition, during inference,
  after the first element is presented, the columns should not burst any more.
  Need to verify, for the first sequence, that the high order representation
  when presented with the second A and B is different from the representation
  in the first presentation. [TODO]
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
    "activationThreshold": 11
  }
  PATTERN_MACHINE = PatternMachine(100, range(21, 26), num=300)


  def testB1(self):
    """Basic sequence learner.  M=1, N=100, P=1."""
    self.init()

    numbers = range(100)
    shuffle(numbers)
    sequence = self.sequenceMachine.generateFromNumbers(numbers)
    sequence.append(None)

    self.feedTM(sequence)

    _, stats = self._testTM(sequence)

    self.assertAllActiveWerePredicted(stats)
    self.assertAllInactiveWereUnpredicted(stats)


  def testB3(self):
    """N=300, M=1, P=1. (See how high we can go with N)"""
    self.init()

    numbers = range(300)
    shuffle(numbers)
    sequence = self.sequenceMachine.generateFromNumbers(numbers)
    sequence.append(None)

    self.feedTM(sequence)

    _, stats = self._testTM(sequence)

    self.assertAllActiveWerePredicted(stats)
    self.assertAllInactiveWereUnpredicted(stats)


  def testB4(self):
    """N=100, M=3, P=1. (See how high we can go with N*M)"""
    self.init()

    sequence = []
    for _ in xrange(3):
      numbers = range(100)
      shuffle(numbers)
      sequence += self.sequenceMachine.generateFromNumbers(numbers)
      sequence.append(None)

    self.feedTM(sequence)

    _, stats = self._testTM(sequence)

    self.assertAllActiveWerePredicted(stats)


  def testB5(self):
    """Like B1 but with cellsPerColumn = 4.
    First order sequences should still work just fine."""
    self.init({"cellsPerColumn": 4})

    numbers = range(100)
    shuffle(numbers)
    sequence = self.sequenceMachine.generateFromNumbers(numbers)
    sequence.append(None)

    self.feedTM(sequence)

    _, stats = self._testTM(sequence)

    self.assertAllActiveWerePredicted(stats)
    self.assertAllInactiveWereUnpredicted(stats)


  def testB6(self):
    """Like B1 but with slower learning.

    Set the following parameters differently:

      initialPermanence = 0.2
      connectedPermanence = 0.7
      permanenceIncrement = 0.2

    Now we train the TP with the B1 sequence 4 times (P=4). This will increment
    the permanences to be above 0.8 and at that point the inference will be correct.
    This test will ensure the basic match function and segment activation rules are
    working correctly.
    """
    self.init({"initialPermanence": 0.2,
               "connectedPermanence": 0.7,
               "permanenceIncrement": 0.2})

    numbers = range(100)
    shuffle(numbers)
    sequence = self.sequenceMachine.generateFromNumbers(numbers)
    sequence.append(None)

    for _ in xrange(4):
      self.feedTM(sequence)

    _, stats = self._testTM(sequence)

    self.assertAllActiveWerePredicted(stats)
    self.assertAllInactiveWereUnpredicted(stats)


  def testB7(self):
    """Like B6 but with 4 cells per column.
    Should still work."""
    self.init({"initialPermanence": 0.2,
               "connectedPermanence": 0.7,
               "permanenceIncrement": 0.2,
               "cellsPerColumn": 4})

    numbers = range(100)
    shuffle(numbers)
    sequence = self.sequenceMachine.generateFromNumbers(numbers)
    sequence.append(None)

    for _ in xrange(4):
      self.feedTM(sequence)

    _, stats = self._testTM(sequence)

    self.assertAllActiveWerePredicted(stats)
    self.assertAllInactiveWereUnpredicted(stats)


  def testB8(self):
    """Like B6 but present the sequence less than 4 times.
    The inference should be incorrect."""
    self.init({"initialPermanence": 0.2,
               "connectedPermanence": 0.7,
               "permanenceIncrement": 0.2})

    numbers = range(100)
    shuffle(numbers)
    sequence = self.sequenceMachine.generateFromNumbers(numbers)
    sequence.append(None)

    for _ in xrange(3):
      self.feedTM(sequence)

    _, stats = self._testTM(sequence)

    self.assertAllActiveWereUnpredicted(stats)


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


  def setUp(self):
    super(ExtensiveTemporalMemoryTest, self).setUp()

    if self.VERBOSITY >= 2:
      print ("\n"
             "======================================================\n"
             "Test: {0} \n"
             "{1}\n"
             "======================================================\n"
      ).format(self.id(), self.shortDescription())


  def feedTM(self, sequence, learn=True, num=1):
    detailedResults = super(ExtensiveTemporalMemoryTest,
                            self).feedTM(sequence, learn=learn, num=num)

    if self.VERBOSITY >= 2:
      print self.tmTestMachine.prettyPrintDetailedResults(
        detailedResults,
        sequence,
        self.patternMachine)
      print

    if learn and self.VERBOSITY >= 3:
      print self.tmTestMachine.prettyPrintConnections()

    return detailedResults


  # ==============================
  # Helper functions
  # ==============================

  def _testTM(self, sequence):
    detailedResults = self.feedTM(sequence, learn=False)
    stats = self.tmTestMachine.computeStatistics(detailedResults, sequence)

    self.allStats.append((self.id(), stats))

    return detailedResults, stats


  def assertAllActiveWerePredicted(self, stats):
    sumUnpredictedActiveColumns = stats[4][2]
    self.assertEqual(sumUnpredictedActiveColumns, 0)

    minPredictedActiveColumns = stats[2][0]
    self.assertEqual(minPredictedActiveColumns, 21)
    maxPredictedActiveColumns = stats[2][1]
    self.assertEqual(maxPredictedActiveColumns, 25)


  def assertAllInactiveWereUnpredicted(self, stats):
    sumPredictedInactiveColumns = stats[1][2]
    self.assertEqual(sumPredictedInactiveColumns, 0)


  def assertAllActiveWereUnpredicted(self, stats):
    sumPredictedActiveColumns = stats[2][2]
    self.assertEqual(sumPredictedActiveColumns, 0)

    minUnpredictedActiveColumns = stats[4][0]
    self.assertEqual(minUnpredictedActiveColumns, 21)
    maxUnpredictedActiveColumns = stats[4][1]
    self.assertEqual(maxUnpredictedActiveColumns, 25)



if __name__ == "__main__":
  unittest.main()

