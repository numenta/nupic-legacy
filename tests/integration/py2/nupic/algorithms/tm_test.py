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

import argparse
import pprint
import sys
import unittest

from nupic.research.pattern_machine import ConsecutivePatternMachine
from nupic.research.sequence_machine import SequenceMachine
from nupic.research.tm_test_machine import TMTestMachine
from nupic.research.TM import TM



SHOW_ENABLED = False



# ==============================
# Tests
# ==============================

class TemporalMemoryBehaviorTest(unittest.TestCase):

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

    show(self.tmTestMachine.prettyPrintConnections())
    self._feedTM(sequence)

    (_, _, predictedActiveColumnsList, _, _) = self._feedTM(sequence,
                                                            learn=False)
    self.assertEqual(len(predictedActiveColumnsList[3]), 0)

    self._feedTM(sequence, num=2)

    (_, _, predictedActiveColumnsList, _, _) = self._feedTM(sequence,
                                                            learn=False)
    self.assertEqual(len(predictedActiveColumnsList[3]), 1)

    self._feedTM(sequence, num=5)

    (_, _, predictedActiveColumnsList, _, _) = self._feedTM(sequence,
                                                            learn=False)
    self.assertEqual(len(predictedActiveColumnsList[3]), 1)


  @unittest.skip("Requires some form of synaptic decay to forget "
                 "the ABC=>Y transition that's initially formed.")
  def testB(self):
    showTest("High order sequences")

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

    if learn:
      show(self.tmTestMachine.prettyPrintConnections())
    else:
      show(self.tmTestMachine.prettyPrintDetailedResults(detailedResults,
                                                         repeatedSequence,
                                                         self.patternMachine))
      show("")

    return detailedResults


  def _showInput(self, sequence, learn=True, num=1):
    sequenceText = self.sequenceMachine.prettyPrintSequence(sequence)
    learnText = "(learning {0})".format("enabled" if learn else "disabled")
    numText = " [{0} times]".format(num) if num > 1 else ""
    show("Feeding sequence {0}{1}:\n{2}".format(
         learnText, numText, sequenceText),
         newline=True)


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
  show("Initialized new TM with parameters:")
  show(pprint.pformat(params), newline=True)
  return tm


# ==============================
# Show
# ==============================

def show(text, newline=False):
  if SHOW_ENABLED:
    print text
    if newline:
      print


def showTest(text):
  show(("\n"
        "====================================\n"
        "Test: {0}\n"
        "===================================="
       ).format(text))


# ==============================
# Main
# ==============================

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('--show', default=False, action='store_true')
  parser.add_argument('unittest_args', nargs='*')

  args = parser.parse_args()
  SHOW_ENABLED = args.show

  unitArgv = [sys.argv[0]] + args.unittest_args
  unittest.main(argv=unitArgv)
