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

import pprint
import unittest
from abc import ABCMeta

import nupic.bindings.algorithms
import nupic.research.temporal_memory
from nupic.data.generators.pattern_machine import ConsecutivePatternMachine

from nupic.support.unittesthelpers.abstract_temporal_memory_test import AbstractTemporalMemoryTest



class TutorialTemporalMemoryTest(AbstractTemporalMemoryTest):
  __metaclass__ = ABCMeta

  VERBOSITY = 1

  def getPatternMachine(self):
    return ConsecutivePatternMachine(6, 1)

  def getDefaultTMParams(self):
    return {
      "columnDimensions": (6,),
      "cellsPerColumn": 4,
      "initialPermanence": 0.3,
      "connectedPermanence": 0.5,
      "minThreshold": 1,
      "maxNewSynapseCount": 6,
      "permanenceIncrement": 0.1,
      "permanenceDecrement": 0.05,
      "activationThreshold": 1,
    }

  def testFirstOrder(self):
    """Basic first order sequences"""
    self.init()

    sequence = self.sequenceMachine.generateFromNumbers([0, 1, 2, 3, None])

    self.feedTM(sequence)
    self.assertEqual(len(self.tm.mmGetTracePredictedActiveColumns().data[3]), 0)

    self.feedTM(sequence, num=2)

    self.feedTM(sequence)
    self.assertEqual(len(self.tm.mmGetTracePredictedActiveColumns().data[3]), 1)

    self.feedTM(sequence, num=4)

    self.feedTM(sequence)
    self.assertEqual(len(self.tm.mmGetTracePredictedActiveColumns().data[3]), 1)


  def testHighOrder(self):
    """High order sequences (in order)"""
    self.init()

    sequenceA = self.sequenceMachine.generateFromNumbers([0, 1, 2, 3, None])
    sequenceB = self.sequenceMachine.generateFromNumbers([4, 1, 2, 5, None])

    self.feedTM(sequenceA, num=5)

    self.feedTM(sequenceA, learn=False)
    self.assertEqual(len(self.tm.mmGetTracePredictedActiveColumns().data[3]), 1)

    self.feedTM(sequenceB)

    self.feedTM(sequenceB, num=2)

    self.feedTM(sequenceB, learn=False)
    self.assertEqual(len(self.tm.mmGetTracePredictedActiveColumns().data[1]), 1)

    self.feedTM(sequenceB, num=3)

    self.feedTM(sequenceB, learn=False)
    self.assertEqual(len(self.tm.mmGetTracePredictedActiveColumns().data[2]), 1)

    self.feedTM(sequenceB, num=3)

    self.feedTM(sequenceB, learn=False)
    self.assertEqual(len(self.tm.mmGetTracePredictedActiveColumns().data[3]), 1)

    self.feedTM(sequenceA, learn=False)
    self.assertEqual(len(self.tm.mmGetTracePredictedActiveColumns().data[3]), 1)
    self.assertEqual(len(self.tm.mmGetTracePredictedInactiveColumns().data[3]), 1)

    self.feedTM(sequenceA, num=10)
    self.feedTM(sequenceA, learn=False)
    self.assertEqual(len(self.tm.mmGetTracePredictedActiveColumns().data[3]), 1)
    # TODO: Requires some form of synaptic decay to forget the ABC=>Y
    # transition that's initially formed
    # self.assertEqual(len(self.tm.mmGetTracePredictedInactiveColumns().data[3]), 0)


  def testHighOrderAlternating(self):
    """High order sequences (alternating)"""
    self.init()

    sequence  = self.sequenceMachine.generateFromNumbers([0, 1, 2, 3, None])
    sequence += self.sequenceMachine.generateFromNumbers([4, 1, 2, 5, None])

    self.feedTM(sequence)

    self.feedTM(sequence, num=10)

    self.feedTM(sequence, learn=False)

    # TODO: Requires some form of synaptic decay to forget the
    # ABC=>Y and XBC=>D transitions that are initially formed
    self.assertEqual(len(self.tm.mmGetTracePredictedActiveColumns().data[3]), 1)
    # self.assertEqual(len(self.tm.mmGetTracePredictedInactiveColumns().data[3]), 0)

    self.assertEqual(len(self.tm.mmGetTracePredictedActiveColumns().data[7]), 1)
    # self.assertEqual(len(self.tm.mmGetTracePredictedInactiveColumns().data[7]), 0)


  def testEndlesslyRepeating(self):
    """Endlessly repeating sequence of 2 elements"""
    self.init({"columnDimensions": [2]})

    sequence = self.sequenceMachine.generateFromNumbers([0, 1])

    for _ in xrange(7):
      self.feedTM(sequence)

    self.feedTM(sequence, num=50)


  def testEndlesslyRepeatingWithNoNewSynapses(self):
    """Endlessly repeating sequence of 2 elements with maxNewSynapseCount=1"""
    self.init({"columnDimensions": [2],
               "maxNewSynapseCount": 1,
               "cellsPerColumn": 10})

    sequence = self.sequenceMachine.generateFromNumbers([0, 1])

    for _ in xrange(7):
      self.feedTM(sequence)

    self.feedTM(sequence, num=100)


  def testLongRepeatingWithNovelEnding(self):
    """Long repeating sequence with novel pattern at the end"""
    self.init({"columnDimensions": [3]})

    sequence = self.sequenceMachine.generateFromNumbers([0, 1])
    sequence *= 10
    sequence += [self.patternMachine.get(2), None]

    for _ in xrange(4):
      self.feedTM(sequence)

    self.feedTM(sequence, num=10)


  def testSingleEndlesslyRepeating(self):
    """A single endlessly repeating pattern"""
    self.init({"columnDimensions": [1]})

    sequence = [self.patternMachine.get(0)]

    for _ in xrange(4):
      self.feedTM(sequence)

    for _ in xrange(2):
      self.feedTM(sequence, num=10)


  # ==============================
  # Overrides
  # ==============================

  def setUp(self):
    super(TutorialTemporalMemoryTest, self).setUp()

    print ("\n"
           "======================================================\n"
           "Test: {0} \n"
           "{1}\n"
           "======================================================\n"
    ).format(self.id(), self.shortDescription())


  def init(self, *args, **kwargs):
    super(TutorialTemporalMemoryTest, self).init(*args, **kwargs)

    print "Initialized new TM with parameters:"
    print pprint.pformat(self._computeTMParams(kwargs.get("overrides")))
    print


  def feedTM(self, sequence, learn=True, num=1):
    self._showInput(sequence, learn=learn, num=num)

    super(TutorialTemporalMemoryTest, self).feedTM(
      sequence, learn=learn, num=num)

    print self.tm.mmPrettyPrintTraces(self.tm.mmGetDefaultTraces(verbosity=2),
                                    breakOnResets=self.tm.mmGetTraceResets())
    print

    if learn:
      self._printConnections()


  # ==============================
  # Helper functions
  # ==============================

  def _printConnections(self):
    # This is in a helper so that it can be overridden.
    print self.tm.mmPrettyPrintConnections()


  def _showInput(self, sequence, learn=True, num=1):
    sequenceText = self.sequenceMachine.prettyPrintSequence(
      sequence,
      verbosity=self.VERBOSITY)
    learnText = "(learning {0})".format("enabled" if learn else "disabled")
    numText = " [{0} times]".format(num) if num > 1 else ""
    print "Feeding sequence {0}{1}:\n{2}".format(
      learnText, numText, sequenceText)
    print



class TutorialTemporalMemoryTestsCPP(TutorialTemporalMemoryTest, unittest.TestCase):
  def getTMClass(self):
    return nupic.bindings.algorithms.TemporalMemory

  def _printConnections(self):
    # Can't call segmentsForCell on C++ connections class (yet).
    pass



class TutorialTemporalMemoryTestsPY(TutorialTemporalMemoryTest, unittest.TestCase):
  def getTMClass(self):
    return nupic.research.temporal_memory.TemporalMemory



if __name__ == "__main__":
  unittest.main()
