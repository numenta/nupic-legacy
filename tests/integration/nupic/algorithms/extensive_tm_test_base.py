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

import numpy
import unittest
from abc import ABCMeta

from nupic.data.generators.pattern_machine import PatternMachine

from nupic.support.unittesthelpers.abstract_temporal_memory_test import AbstractTemporalMemoryTest



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

  Each input pattern can optionally have an amount of spatial noise represented
  by X, where X is the probability of switching an on bit with a random bit.

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

  B6) Like B4 but with cellsPerColumn = 4. First order sequences should still
  work just fine.

  B7) Like B1 but with slower learning. Set the following parameters differently:

      initialPermanence = 0.2
      connectedPermanence = 0.7
      permanenceIncrement = 0.2

  Now we train the TP with the B1 sequence 4 times (P=4). This will increment
  the permanences to be above 0.8 and at that point the inference will be correct.
  This test will ensure the basic match function and segment activation rules are
  working correctly.

  B8) Like B7 but with 4 cells per column. Should still work.

  B9) Like B7 but present the sequence less than 4 times: the inference should be
  incorrect.

  B10) Like B2, except that cells per column = 4. Should still add zero additional
  synapses. [TODO]

  B11) Like B5, but with activationThreshold = 8 and with each pattern
  corrupted by a small amount of spatial noise (X = 0.05).

  B12) Test accessors.

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

  Each input pattern can optionally have an amount of spatial noise represented
  by X, where X is the probability of switching an on bit with a random bit.

  Training: Identical to basic first order tests above.

  Testing: Identical to basic first order tests above unless noted.

  We can also calculate the number of segments and synapses that should be
  learned. We raise an error if too many or too few were learned.

  H1) Learn two sequences with a shared subsequence in the middle. Parameters
  should be the same as B1. Since cellsPerColumn == 1, it should make more
  predictions than necessary.

  H2) Same as H1, but with cellsPerColumn == 4, and train multiple times.
  It should make just the right number of predictions.

  H3) Like H2, except the shared subsequence is in the beginning (e.g.
  "ABCDEF" and "ABCGHIJ"). At the point where the shared subsequence ends, all
  possible next patterns should be predicted. As soon as you see the first unique
  pattern, the predictions should collapse to be a perfect prediction.

  H4) Shared patterns. Similar to H2 except that patterns are shared between
  sequences.  All sequences are different shufflings of the same set of N
  patterns (there is no shared subsequence).

  H5) Combination of H4) and H2). Shared patterns in different sequences, with a
  shared subsequence.

  H6) Stress test: every other pattern is shared. [TODO]

  H7) Start predicting in the middle of a sequence. [TODO]

  H8) Hub capacity. How many patterns can use that hub? [TODO]

  H9) Sensitivity to small amounts of spatial noise during inference (X = 0.05).
  Parameters the same as B11, and sequences like H2.

  H10) Higher order patterns with alternating elements.

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
  __metaclass__ = ABCMeta

  VERBOSITY = 1

  def getPatternMachine(self):
    return PatternMachine(100, range(21, 26), num=300)

  def getDefaultTMParams(self):
    return {
      "columnDimensions": (100,),
      "cellsPerColumn": 1,
      "initialPermanence": 0.8,
      "connectedPermanence": 0.7,
      "minThreshold": 11,
      "maxNewSynapseCount": 11,
      "permanenceIncrement": 0.4,
      "permanenceDecrement": 0,
      "activationThreshold": 11,
      "seed": 42,
    }

  def testB1(self):
    """Basic sequence learner.  M=1, N=100, P=1."""
    self.init()

    numbers = self.sequenceMachine.generateNumbers(1, 100)
    sequence = self.sequenceMachine.generateFromNumbers(numbers)

    self.feedTM(sequence)

    self._testTM(sequence)
    self.assertAllActiveWerePredicted()
    self.assertAllInactiveWereUnpredicted()


  def testB3(self):
    """N=300, M=1, P=1. (See how high we can go with N)"""
    self.init()

    numbers = self.sequenceMachine.generateNumbers(1, 300)
    sequence = self.sequenceMachine.generateFromNumbers(numbers)

    self.feedTM(sequence)

    self._testTM(sequence)
    self.assertAllActiveWerePredicted()
    self.assertAllInactiveWereUnpredicted()


  def testB4(self):
    """N=100, M=3, P=1. (See how high we can go with N*M)"""
    self.init()

    numbers = self.sequenceMachine.generateNumbers(3, 100)
    sequence = self.sequenceMachine.generateFromNumbers(numbers)

    self.feedTM(sequence)

    self._testTM(sequence)
    self.assertAllActiveWerePredicted()


  def testB5(self):
    """Like B1 but with cellsPerColumn = 4.
    First order sequences should still work just fine."""
    self.init({"cellsPerColumn": 4})

    numbers = self.sequenceMachine.generateNumbers(1, 100)
    sequence = self.sequenceMachine.generateFromNumbers(numbers)

    self.feedTM(sequence)

    self._testTM(sequence)
    self.assertAllActiveWerePredicted()
    self.assertAllInactiveWereUnpredicted()


  def testB6(self):
    """Like B4 but with cellsPerColumn = 4.
    First order sequences should still work just fine."""
    self.init({"cellsPerColumn": 4})

    numbers = self.sequenceMachine.generateNumbers(3, 100)
    sequence = self.sequenceMachine.generateFromNumbers(numbers)

    self.feedTM(sequence)

    self._testTM(sequence)
    self.assertAllActiveWerePredicted()
    self.assertAllInactiveWereUnpredicted()


  def testB7(self):
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

    numbers = self.sequenceMachine.generateNumbers(1, 100)
    sequence = self.sequenceMachine.generateFromNumbers(numbers)

    for _ in xrange(4):
      self.feedTM(sequence)

    self._testTM(sequence)
    self.assertAllActiveWerePredicted()
    self.assertAllInactiveWereUnpredicted()


  def testB8(self):
    """Like B7 but with 4 cells per column.
    Should still work."""
    self.init({"initialPermanence": 0.2,
               "connectedPermanence": 0.7,
               "permanenceIncrement": 0.2,
               "cellsPerColumn": 4})

    numbers = self.sequenceMachine.generateNumbers(1, 100)
    sequence = self.sequenceMachine.generateFromNumbers(numbers)

    for _ in xrange(4):
      self.feedTM(sequence)

    self._testTM(sequence)
    self.assertAllActiveWerePredicted()
    self.assertAllInactiveWereUnpredicted()


  def testB9(self):
    """Like B7 but present the sequence less than 4 times.
    The inference should be incorrect."""
    self.init({"initialPermanence": 0.2,
               "connectedPermanence": 0.7,
               "permanenceIncrement": 0.2})

    numbers = self.sequenceMachine.generateNumbers(1, 100)
    sequence = self.sequenceMachine.generateFromNumbers(numbers)

    for _ in xrange(3):
      self.feedTM(sequence)

    self._testTM(sequence)
    self.assertAllActiveWereUnpredicted()


  def testB11(self):
    """Like B5, but with activationThreshold = 8 and with each pattern
    corrupted by a small amount of spatial noise (X = 0.05)."""
    self.init({"cellsPerColumn": 4,
               "activationThreshold": 8,
               "minThreshold": 8})

    numbers = self.sequenceMachine.generateNumbers(1, 100)
    sequence = self.sequenceMachine.generateFromNumbers(numbers)

    self.feedTM(sequence)

    sequence = self.sequenceMachine.addSpatialNoise(sequence, 0.05)

    self._testTM(sequence)
    unpredictedActiveColumnsMetric = self.tm.mmGetMetricFromTrace(
      self.tm.mmGetTraceUnpredictedActiveColumns())
    self.assertTrue(unpredictedActiveColumnsMetric.mean < 1)


  def testH1(self):
    """Learn two sequences with a short shared pattern.
    Parameters should be the same as B1.
    Since cellsPerColumn == 1, it should make more predictions than necessary.
    """
    self.init()

    numbers = self.sequenceMachine.generateNumbers(2, 20, (10, 15))
    sequence = self.sequenceMachine.generateFromNumbers(numbers)

    self.feedTM(sequence)

    self._testTM(sequence)
    self.assertAllActiveWerePredicted()

    predictedInactiveColumnsMetric = self.tm.mmGetMetricFromTrace(
      self.tm.mmGetTracePredictedInactiveColumns())
    self.assertTrue(predictedInactiveColumnsMetric.mean > 0)

    # At the end of both shared sequences, there should be
    # predicted but inactive columns
    self.assertTrue(
      len(self.tm.mmGetTracePredictedInactiveColumns().data[15]) > 0)
    self.assertTrue(
      len(self.tm.mmGetTracePredictedInactiveColumns().data[35]) > 0)


  def testH2(self):
    """Same as H1, but with cellsPerColumn == 4, and train multiple times.
    It should make just the right number of predictions."""
    self.init({"cellsPerColumn": 4})

    numbers = self.sequenceMachine.generateNumbers(2, 20, (10, 15))
    sequence = self.sequenceMachine.generateFromNumbers(numbers)

    for _ in xrange(10):
      self.feedTM(sequence)

    self._testTM(sequence)
    self.assertAllActiveWerePredicted()

    # Without some kind of decay, expect predicted inactive columns at the
    # end of the first shared sequence
    predictedInactiveColumnsMetric = self.tm.mmGetMetricFromTrace(
      self.tm.mmGetTracePredictedInactiveColumns())
    self.assertTrue(predictedInactiveColumnsMetric.sum < 26)

    # At the end of the second shared sequence, there should be no
    # predicted but inactive columns
    self.assertEqual(
      len(self.tm.mmGetTracePredictedInactiveColumns().data[36]), 0)


  def testH3(self):
    """Like H2, except the shared subsequence is in the beginning.
    (e.g. "ABCDEF" and "ABCGHIJ") At the point where the shared subsequence
    ends, all possible next patterns should be predicted. As soon as you see
    the first unique pattern, the predictions should collapse to be a perfect
    prediction."""
    self.init({"cellsPerColumn": 4})

    numbers = self.sequenceMachine.generateNumbers(2, 20, (0, 5))
    sequence = self.sequenceMachine.generateFromNumbers(numbers)

    self.feedTM(sequence)

    self._testTM(sequence)
    self.assertAllActiveWerePredicted()

    predictedInactiveColumnsMetric = self.tm.mmGetMetricFromTrace(
      self.tm.mmGetTracePredictedInactiveColumns())
    self.assertTrue(predictedInactiveColumnsMetric.sum < 26 * 2)

    # At the end of each shared sequence, there should be
    # predicted but inactive columns
    self.assertTrue(
      len(self.tm.mmGetTracePredictedInactiveColumns().data[5]) > 0)
    self.assertTrue(
      len(self.tm.mmGetTracePredictedInactiveColumns().data[25]) > 0)


  def testH4(self):
    """Shared patterns. Similar to H2 except that patterns are shared between
    sequences.  All sequences are different shufflings of the same set of N
    patterns (there is no shared subsequence)."""
    self.init({"cellsPerColumn": 4})

    numbers = []
    for _ in xrange(2):
      numbers += self.sequenceMachine.generateNumbers(1, 20)

    sequence = self.sequenceMachine.generateFromNumbers(numbers)

    for _ in xrange(20):
      self.feedTM(sequence)

    self._testTM(sequence)
    self.assertAllActiveWerePredicted()

    predictedInactiveColumnsMetric = self.tm.mmGetMetricFromTrace(
      self.tm.mmGetTracePredictedInactiveColumns())
    self.assertTrue(predictedInactiveColumnsMetric.mean < 3)


  def testH5(self):
    """Combination of H4) and H2).
    Shared patterns in different sequences, with a shared subsequence."""
    self.init({"cellsPerColumn": 4})

    numbers = []
    shared = self.sequenceMachine.generateNumbers(1, 5)[:-1]
    for _ in xrange(2):
      sublist = self.sequenceMachine.generateNumbers(1, 20)
      sublist = [x for x in sublist if x not in xrange(5)]
      numbers += sublist[0:10] + shared + sublist[10:]

    sequence = self.sequenceMachine.generateFromNumbers(numbers)

    for _ in xrange(20):
      self.feedTM(sequence)

    self._testTM(sequence)
    self.assertAllActiveWerePredicted()

    predictedInactiveColumnsMetric = self.tm.mmGetMetricFromTrace(
      self.tm.mmGetTracePredictedInactiveColumns())
    self.assertTrue(predictedInactiveColumnsMetric.mean < 3)


  def testH9(self):
    """Sensitivity to small amounts of spatial noise during inference
    (X = 0.05). Parameters the same as B11, and sequences like H2."""
    self.init({"cellsPerColumn": 4,
               "activationThreshold": 8,
               "minThreshold": 8})

    numbers = self.sequenceMachine.generateNumbers(2, 20, (10, 15))
    sequence = self.sequenceMachine.generateFromNumbers(numbers)

    for _ in xrange(10):
      self.feedTM(sequence)

    sequence = self.sequenceMachine.addSpatialNoise(sequence, 0.05)

    self._testTM(sequence)
    unpredictedActiveColumnsMetric = self.tm.mmGetMetricFromTrace(
      self.tm.mmGetTraceUnpredictedActiveColumns())
    self.assertTrue(unpredictedActiveColumnsMetric.mean < 3)


  def testH10(self):
    """Orphan Decay mechanism reduce predicted inactive cells (extra predictions).
    Test feeds in noisy sequences (X = 0.05) to TM with and without orphan decay.
    TM with orphan decay should has many fewer predicted inactive columns.
    Parameters the same as B11, and sequences like H9."""

    # train TM on noisy sequences with orphan decay turned off
    self.init({"cellsPerColumn": 4,
               "activationThreshold": 8,
               "minThreshold": 8})

    numbers = self.sequenceMachine.generateNumbers(2, 20, (10, 15))
    sequence = self.sequenceMachine.generateFromNumbers(numbers)

    sequenceNoisy = dict()
    for i in xrange(10):
      sequenceNoisy[i] = self.sequenceMachine.addSpatialNoise(sequence, 0.05)
      self.feedTM(sequenceNoisy[i])
    self.tm.mmClearHistory()

    self._testTM(sequence)

    predictedInactiveColumnsMetric = self.tm.mmGetMetricFromTrace(
      self.tm.mmGetTracePredictedInactiveColumns())
    predictedActiveColumnsMetric = self.tm.mmGetMetricFromTrace(
      self.tm.mmGetTracePredictedActiveColumns())

    predictedInactiveColumnsMeanNoOrphanDecay = predictedInactiveColumnsMetric.mean
    predictedActiveColumnsMeanNoOrphanDecay = predictedActiveColumnsMetric.mean

    # train TM on the same set of noisy sequences with orphan decay turned on
    self.init({"cellsPerColumn": 4,
               "activationThreshold": 8,
               "minThreshold": 8,
               "predictedSegmentDecrement": 0.04})

    for i in xrange(10):
      self.feedTM(sequenceNoisy[i])
    self.tm.mmClearHistory()

    self._testTM(sequence)

    predictedInactiveColumnsMetric = self.tm.mmGetMetricFromTrace(
      self.tm.mmGetTracePredictedInactiveColumns())
    predictedActiveColumnsMetric = self.tm.mmGetMetricFromTrace(
      self.tm.mmGetTracePredictedActiveColumns())

    predictedInactiveColumnsMeanOrphanDecay = predictedInactiveColumnsMetric.mean
    predictedActiveColumnsMeanOrphanDecay = predictedActiveColumnsMetric.mean

    self.assertGreater(predictedInactiveColumnsMeanNoOrphanDecay, 0)
    self.assertGreater(predictedInactiveColumnsMeanNoOrphanDecay, predictedInactiveColumnsMeanOrphanDecay)
    self.assertAlmostEqual(predictedActiveColumnsMeanNoOrphanDecay, predictedActiveColumnsMeanOrphanDecay)

  # ==============================
  # Overrides
  # ==============================

  def setUp(self):
    super(ExtensiveTemporalMemoryTest, self).setUp()

    print ("\n"
           "======================================================\n"
           "Test: {0} \n"
           "{1}\n"
           "======================================================\n"
    ).format(self.id(), self.shortDescription())


  def feedTM(self, sequence, learn=True, num=1):
    super(ExtensiveTemporalMemoryTest, self).feedTM(
      sequence, learn=learn, num=num)

    if self.VERBOSITY >= 2:
      print self.tm.mmPrettyPrintTraces(
        self.tm.mmGetDefaultTraces(verbosity=self.VERBOSITY-1))
      print

    if learn and self.VERBOSITY >= 3:
      print self.tm.mmPrettyPrintConnections()


  # ==============================
  # Helper functions
  # ==============================

  def _testTM(self, sequence):
    self.feedTM(sequence, learn=False)

    print self.tm.mmPrettyPrintMetrics(self.tm.mmGetDefaultMetrics())


  def assertAllActiveWerePredicted(self):
    unpredictedActiveColumnsMetric = self.tm.mmGetMetricFromTrace(
      self.tm.mmGetTraceUnpredictedActiveColumns())
    predictedActiveColumnsMetric = self.tm.mmGetMetricFromTrace(
      self.tm.mmGetTracePredictedActiveColumns())

    self.assertEqual(unpredictedActiveColumnsMetric.sum, 0)

    self.assertEqual(predictedActiveColumnsMetric.min, 21)
    self.assertEqual(predictedActiveColumnsMetric.max, 25)


  def assertAllInactiveWereUnpredicted(self):
    predictedInactiveColumnsMetric = self.tm.mmGetMetricFromTrace(
      self.tm.mmGetTracePredictedInactiveColumns())

    self.assertEqual(predictedInactiveColumnsMetric.sum, 0)


  def assertAllActiveWereUnpredicted(self):
    unpredictedActiveColumnsMetric = self.tm.mmGetMetricFromTrace(
      self.tm.mmGetTraceUnpredictedActiveColumns())
    predictedActiveColumnsMetric = self.tm.mmGetMetricFromTrace(
      self.tm.mmGetTracePredictedActiveColumns())

    self.assertEqual(predictedActiveColumnsMetric.sum, 0)

    self.assertEqual(unpredictedActiveColumnsMetric.min, 21)
    self.assertEqual(unpredictedActiveColumnsMetric.max, 25)
