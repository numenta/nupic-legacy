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
import unittest2 as unittest

from nupic.data.pattern_machine import ConsecutivePatternMachine
from nupic.data.sequence_machine import SequenceMachine
from nupic.test.tm_test_machine import TMTestMachine
from nupic.research.TM import TM



# ==============================
# Tests
# ==============================

class TemporalMemoryTest(unittest.TestCase):

  def setUp(self):
    self.tm = None
    self.patternMachine = None
    self.sequenceMachine = None
    self.tmTestMachine = None


  def testA(self):
    showTest("Basic first order sequences")

    tm = newTM()
    self.patternMachine = ConsecutivePatternMachine(
                            tm.connections.numberOfColumns(), 1)
    self.sequenceMachine = SequenceMachine(self.patternMachine)
    self.tmTestMachine = TMTestMachine(tm)

    sequence = self.sequenceMachine.generateFromNumbers([0, 1, 2, 3, None])

    (_, _, predictedActiveColumnsList, _, _) = self._feedTM(sequence)
    self.assertEqual(len(predictedActiveColumnsList[3]), 0)

    self._feedTM(sequence, num=2)

    (_, _, predictedActiveColumnsList, _, _) = self._feedTM(sequence)
    self.assertEqual(len(predictedActiveColumnsList[3]), 1)

    self._feedTM(sequence, num=4)

    (_, _, predictedActiveColumnsList, _, _) = self._feedTM(sequence)
    self.assertEqual(len(predictedActiveColumnsList[3]), 1)


  @unittest.skip("Requires some form of synaptic decay to forget "
                 "the ABC=>Y transition that's initially formed.")
  def testB(self):
    showTest("High order sequences (in order)")

    tm = newTM()
    self.patternMachine = ConsecutivePatternMachine(
                            tm.connections.numberOfColumns(), 1)
    self.sequenceMachine = SequenceMachine(self.patternMachine)
    self.tmTestMachine = TMTestMachine(tm)

    sequenceA = self.sequenceMachine.generateFromNumbers([0, 1, 2, 3, None])
    sequenceB = self.sequenceMachine.generateFromNumbers([4, 1, 2, 5, None])

    self._feedTM(sequenceA, num=5)

    (_, _, predictedActiveColumnsList, _, _) = self._feedTM(sequenceA,
                                                            learn=False)
    self.assertEqual(len(predictedActiveColumnsList[3]), 1)

    self._feedTM(sequenceB)

    self._feedTM(sequenceB, num=2)

    (_, _, predictedActiveColumnsList, _, _) = self._feedTM(sequenceB,
                                                            learn=False)
    self.assertEqual(len(predictedActiveColumnsList[1]), 1)

    self._feedTM(sequenceB, num=3)

    (_, _, predictedActiveColumnsList, _, _) = self._feedTM(sequenceB,
                                                            learn=False)
    self.assertEqual(len(predictedActiveColumnsList[2]), 1)

    self._feedTM(sequenceB, num=3)

    (_, _, predictedActiveColumnsList, _, _) = self._feedTM(sequenceB,
                                                            learn=False)
    self.assertEqual(len(predictedActiveColumnsList[3]), 1)

    (_, _, predictedActiveColumnsList,
           predictedInactiveColumnsList, _) = self._feedTM(sequenceA,
                                                            learn=False)
    self.assertEqual(len(predictedActiveColumnsList[3]), 1)
    self.assertEqual(len(predictedInactiveColumnsList[3]), 1)

    self._feedTM(sequenceA, num=10)
    (_, _, predictedActiveColumnsList,
           predictedInactiveColumnsList, _) = self._feedTM(sequenceA,
                                                            learn=False)
    self.assertEqual(len(predictedActiveColumnsList[3]), 1)
    self.assertEqual(len(predictedInactiveColumnsList[3]), 0)


  @unittest.skip("Requires some form of synaptic decay to forget the "
                 "ABC=>Y and XBC=>D transitions that are initially formed.")
  def testC(self):
    showTest("High order sequences (alternating)")

    tm = newTM()
    self.patternMachine = ConsecutivePatternMachine(
                            tm.connections.numberOfColumns(), 1)
    self.sequenceMachine = SequenceMachine(self.patternMachine)
    self.tmTestMachine = TMTestMachine(tm)

    sequence  = self.sequenceMachine.generateFromNumbers([0, 1, 2, 3, None])
    sequence += self.sequenceMachine.generateFromNumbers([4, 1, 2, 5, None])

    self._feedTM(sequence)

    self._feedTM(sequence, num=10)

    (_, _, predictedActiveColumnsList,
           predictedInactiveColumnsList, _) = self._feedTM(sequence,
                                                            learn=False)

    self.assertEqual(len(predictedActiveColumnsList[3]), 1)
    self.assertEqual(len(predictedInactiveColumnsList[3]), 0)

    self.assertEqual(len(predictedActiveColumnsList[8]), 1)
    self.assertEqual(len(predictedInactiveColumnsList[8]), 0)


  def testD(self):
    showTest("Endlessly repeating sequence of 2 elements")

    tm = newTM({"columnDimensions": [2]})
    self.patternMachine = ConsecutivePatternMachine(
                            tm.connections.numberOfColumns(), 1)
    self.sequenceMachine = SequenceMachine(self.patternMachine)
    self.tmTestMachine = TMTestMachine(tm)

    sequence = self.sequenceMachine.generateFromNumbers([0, 1])

    for _ in xrange(7):
      self._feedTM(sequence)

    self._feedTM(sequence, num=50)


  def testE(self):
    showTest("Endlessly repeating sequence of 2 elements "
             "with maxNewSynapseCount=1")

    tm = newTM({"columnDimensions": [2],
               "maxNewSynapseCount": 1,
               "cellsPerColumn": 10})
    self.patternMachine = ConsecutivePatternMachine(
                            tm.connections.numberOfColumns(), 1)
    self.sequenceMachine = SequenceMachine(self.patternMachine)
    self.tmTestMachine = TMTestMachine(tm)

    sequence = self.sequenceMachine.generateFromNumbers([0, 1])

    for _ in xrange(7):
      self._feedTM(sequence)

    self._feedTM(sequence, num=100)


  def testF(self):
    showTest("Long repeating sequence with novel pattern at the end")

    tm = newTM({"columnDimensions": [3]})
    self.patternMachine = ConsecutivePatternMachine(
                            tm.connections.numberOfColumns(), 1)
    self.sequenceMachine = SequenceMachine(self.patternMachine)
    self.tmTestMachine = TMTestMachine(tm)

    sequence = self.sequenceMachine.generateFromNumbers([0, 1])
    sequence *= 10
    sequence += [self.patternMachine.get(2), None]

    for _ in xrange(4):
      self._feedTM(sequence)

    self._feedTM(sequence, num=10)


  def testG(self):
    showTest("A single endlessly repeating pattern")

    tm = newTM({"columnDimensions": [1]})
    self.patternMachine = ConsecutivePatternMachine(
                            tm.connections.numberOfColumns(), 1)
    self.sequenceMachine = SequenceMachine(self.patternMachine)
    self.tmTestMachine = TMTestMachine(tm)

    sequence = [self.patternMachine.get(0)]

    for _ in xrange(4):
      self._feedTM(sequence)

    self._feedTM(sequence, num=10)


  # ==============================
  # Helper functions
  # ==============================

  def _feedTM(self, sequence, learn=True, num=1):
    self._showInput(sequence, learn=learn, num=num)

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


  def _showInput(self, sequence, learn=True, num=1):
    sequenceText = self.sequenceMachine.prettyPrintSequence(sequence)
    learnText = "(learning {0})".format("enabled" if learn else "disabled")
    numText = " [{0} times]".format(num) if num > 1 else ""
    print "Feeding sequence {0}{1}:\n{2}".format(
            learnText, numText, sequenceText)
    print


# ==============================
# TM
# ==============================

def newTM(overrides=None):
  params = {
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
  params.update(overrides or {})
  tm = TM(**params)

  print "Initialized new TM with parameters:"
  print pprint.pformat(params)
  print

  return tm


# ==============================
# Show
# ==============================

def showTest(text):
  print ("\n"
          "====================================\n"
          "Test: {0}\n"
          "===================================="
        ).format(text)


# ==============================
# Main
# ==============================

if __name__ == "__main__":
  unittest.main()
