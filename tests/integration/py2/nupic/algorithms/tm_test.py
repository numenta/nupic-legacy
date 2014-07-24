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

import pprint
from random import shuffle
import unittest2 as unittest

from nupic.data.pattern_machine import PatternMachine, ConsecutivePatternMachine
from nupic.data.sequence_machine import SequenceMachine
from nupic.test.tm_test_machine import TMTestMachine
from nupic.research.TM import TM



class AbstractTemporalMemoryTest(unittest.TestCase):

  def setUp(self):
    self.defaultTMParams = None
    self.tm = None
    self.patternMachine = None
    self.sequenceMachine = None
    self.tmTestMachine = None

    print ("\n"
           "======================================================\n"
           "Test: {0} \n"
           "{1}\n"
           "======================================================\n"
    ).format(self.id(), self.shortDescription())


  def initTM(self, overrides=None):
    params = self.defaultTMParams
    params.update(overrides or {})
    self.tm = TM(**params)

    print "Initialized new TM with parameters:"
    print pprint.pformat(params)
    print


  def finishSetUp(self, patternMachine):
    self.patternMachine = patternMachine
    self.sequenceMachine = SequenceMachine(self.patternMachine)
    self.tmTestMachine = TMTestMachine(self.tm)


  # ==============================
  # Helper functions
  # ==============================

  def feedTM(self, sequence, learn=True, num=1):
    self.showInput(sequence, learn=learn, num=num)

    repeatedSequence = sequence * num
    results = self.tmTestMachine.feedSequence(repeatedSequence, learn=learn)

    detailedResults = self.tmTestMachine.computeDetailedResults(
      results,
      repeatedSequence)

    print self.tmTestMachine.prettyPrintDetailedResults(detailedResults,
                                                        repeatedSequence,
                                                        self.patternMachine)
    print

    if learn:
      print self.tmTestMachine.prettyPrintConnections()

    return detailedResults


  def showInput(self, sequence, learn=True, num=1):
    sequenceText = self.sequenceMachine.prettyPrintSequence(sequence)
    learnText = "(learning {0})".format("enabled" if learn else "disabled")
    numText = " [{0} times]".format(num) if num > 1 else ""
    print "Feeding sequence {0}{1}:\n{2}".format(
      learnText, numText, sequenceText)
    print



class BasicTemporalMemoryTest(AbstractTemporalMemoryTest):

  def setUp(self):
    super(BasicTemporalMemoryTest, self).setUp()

    self.defaultTMParams = {
      "columnDimensions": [6],
      "cellsPerColumn": 4,
      "initialPermanence": 0.3,
      "connectedPermanence": 0.5,
      "minThreshold": 1,
      "maxNewSynapseCount": 6,
      "permanenceIncrement": 0.1,
      "permanenceDecrement": 0.05,
      "activationThreshold": 1
    }


  def testA(self):
    """Basic first order sequences"""
    self.initTM()
    self.finishSetUp(ConsecutivePatternMachine(
                       self.tm.connections.numberOfColumns(), 1))

    sequence = self.sequenceMachine.generateFromNumbers([0, 1, 2, 3, None])

    (_, _, predictedActiveColumnsList, _, _) = self.feedTM(sequence)
    self.assertEqual(len(predictedActiveColumnsList[3]), 0)

    self.feedTM(sequence, num=2)

    (_, _, predictedActiveColumnsList, _, _) = self.feedTM(sequence)
    self.assertEqual(len(predictedActiveColumnsList[3]), 1)

    self.feedTM(sequence, num=4)

    (_, _, predictedActiveColumnsList, _, _) = self.feedTM(sequence)
    self.assertEqual(len(predictedActiveColumnsList[3]), 1)


  @unittest.skip("Requires some form of synaptic decay to forget "
                 "the ABC=>Y transition that's initially formed.")
  def testB(self):
    """High order sequences (in order)"""
    self.initTM()
    self.finishSetUp(ConsecutivePatternMachine(
      self.tm.connections.numberOfColumns(), 1))

    sequenceA = self.sequenceMachine.generateFromNumbers([0, 1, 2, 3, None])
    sequenceB = self.sequenceMachine.generateFromNumbers([4, 1, 2, 5, None])

    self.feedTM(sequenceA, num=5)

    (_, _, predictedActiveColumnsList, _, _) = self.feedTM(sequenceA,
                                                            learn=False)
    self.assertEqual(len(predictedActiveColumnsList[3]), 1)

    self.feedTM(sequenceB)

    self.feedTM(sequenceB, num=2)

    (_, _, predictedActiveColumnsList, _, _) = self.feedTM(sequenceB,
                                                            learn=False)
    self.assertEqual(len(predictedActiveColumnsList[1]), 1)

    self.feedTM(sequenceB, num=3)

    (_, _, predictedActiveColumnsList, _, _) = self.feedTM(sequenceB,
                                                            learn=False)
    self.assertEqual(len(predictedActiveColumnsList[2]), 1)

    self.feedTM(sequenceB, num=3)

    (_, _, predictedActiveColumnsList, _, _) = self.feedTM(sequenceB,
                                                            learn=False)
    self.assertEqual(len(predictedActiveColumnsList[3]), 1)

    (_, _, predictedActiveColumnsList,
           predictedInactiveColumnsList, _) = self.feedTM(sequenceA,
                                                            learn=False)
    self.assertEqual(len(predictedActiveColumnsList[3]), 1)
    self.assertEqual(len(predictedInactiveColumnsList[3]), 1)

    self.feedTM(sequenceA, num=10)
    (_, _, predictedActiveColumnsList,
           predictedInactiveColumnsList, _) = self.feedTM(sequenceA,
                                                            learn=False)
    self.assertEqual(len(predictedActiveColumnsList[3]), 1)
    self.assertEqual(len(predictedInactiveColumnsList[3]), 0)


  @unittest.skip("Requires some form of synaptic decay to forget the "
                 "ABC=>Y and XBC=>D transitions that are initially formed.")
  def testC(self):
    """High order sequences (alternating)"""
    self.initTM()
    self.finishSetUp(ConsecutivePatternMachine(
      self.tm.connections.numberOfColumns(), 1))

    sequence  = self.sequenceMachine.generateFromNumbers([0, 1, 2, 3, None])
    sequence += self.sequenceMachine.generateFromNumbers([4, 1, 2, 5, None])

    self.feedTM(sequence)

    self.feedTM(sequence, num=10)

    (_, _, predictedActiveColumnsList,
           predictedInactiveColumnsList, _) = self.feedTM(sequence,
                                                            learn=False)

    self.assertEqual(len(predictedActiveColumnsList[3]), 1)
    self.assertEqual(len(predictedInactiveColumnsList[3]), 0)

    self.assertEqual(len(predictedActiveColumnsList[8]), 1)
    self.assertEqual(len(predictedInactiveColumnsList[8]), 0)


  def testD(self):
    """Endlessly repeating sequence of 2 elements"""
    self.initTM({"columnDimensions": [2]})
    self.finishSetUp(ConsecutivePatternMachine(
      self.tm.connections.numberOfColumns(), 1))

    sequence = self.sequenceMachine.generateFromNumbers([0, 1])

    for _ in xrange(7):
      self.feedTM(sequence)

    self.feedTM(sequence, num=50)


  def testE(self):
    """Endlessly repeating sequence of 2 elements with maxNewSynapseCount=1"""
    self.initTM({"columnDimensions": [2],
                 "maxNewSynapseCount": 1,
                 "cellsPerColumn": 10})
    self.finishSetUp(ConsecutivePatternMachine(
      self.tm.connections.numberOfColumns(), 1))

    sequence = self.sequenceMachine.generateFromNumbers([0, 1])

    for _ in xrange(7):
      self.feedTM(sequence)

    self.feedTM(sequence, num=100)


  def testF(self):
    """Long repeating sequence with novel pattern at the end"""
    self.initTM({"columnDimensions": [3]})
    self.finishSetUp(ConsecutivePatternMachine(
      self.tm.connections.numberOfColumns(), 1))

    sequence = self.sequenceMachine.generateFromNumbers([0, 1])
    sequence *= 10
    sequence += [self.patternMachine.get(2), None]

    for _ in xrange(4):
      self.feedTM(sequence)

    self.feedTM(sequence, num=10)


  def testG(self):
    """A single endlessly repeating pattern"""
    self.initTM({"columnDimensions": [1]})
    self.finishSetUp(ConsecutivePatternMachine(
      self.tm.connections.numberOfColumns(), 1))

    sequence = [self.patternMachine.get(0)]

    for _ in xrange(4):
      self.feedTM(sequence)

    self.feedTM(sequence, num=10)



class ExtensiveTemporalMemoryTest(AbstractTemporalMemoryTest):
  """
===============================================================================
                Basic First Order Sequences
===============================================================================

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
additional synapses are learned.

B3) N=300, M=1, P=1. (See how high we can go with M)

B4) N=100, M=3, P=1. (See how high we can go with N*M)

B5) Like B1 but with cellsPerColumn = 4. First order sequences should still
work just fine.

B6) Like B1 but with slower learning. Set the following parameters differently:

    activationThreshold = newSynapseCount
    minThreshold = activationThreshold
    initialPerm = 0.2
    connectedPerm = 0.7
    permanenceInc = 0.2

Now we train the TP with the B1 sequence 4 times (P=4). This will increment
the permanences to be above 0.8 and at that point the inference will be correct.
This test will ensure the basic match function and segment activation rules are
working correctly.

B7) Like B6 but with 4 cells per column. Should still work.

B8) Like B6 but present the sequence less than 4 times: the inference should be
incorrect.

B9) Like B2, except that cells per column = 4. Should still add zero additional
synapses.
  """

  def setUp(self):
    super(ExtensiveTemporalMemoryTest, self).setUp()

    self.defaultTMParams = {
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

    (_,
     predictedInactiveCellsList,
     predictedActiveColumnsList,
     _,
     unpredictedActiveColumnsList) = self.feedTM(sequence,
                                                 learn=False)

    numUnpredictedActiveColumns = sum(
      [len(x) for x in unpredictedActiveColumnsList])
    self.assertEqual(numUnpredictedActiveColumns, 0)

    for i in range(1, len(predictedActiveColumnsList) - 1):
      self.assertEqual(len(predictedActiveColumnsList[i]), 23)

    for i in range(1, len(predictedInactiveCellsList) - 1):
      self.assertTrue(len(predictedInactiveCellsList[i]) < 5)



if __name__ == "__main__":
  unittest.main()
