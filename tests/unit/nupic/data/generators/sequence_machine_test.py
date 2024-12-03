# Copyright 2014 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
import unittest

from nupic.data.generators.pattern_machine import (
    PatternMachine, ConsecutivePatternMachine)
from nupic.data.generators.sequence_machine import SequenceMachine



class SequenceMachineTest(unittest.TestCase):


  def setUp(self):
    self.patternMachine = ConsecutivePatternMachine(100, 5)
    self.sequenceMachine = SequenceMachine(self.patternMachine)


  def testGenerateFromNumbers(self):
    numbers = range(0, 10) + [None] + range(10, 19)
    sequence = self.sequenceMachine.generateFromNumbers(numbers)
    self.assertEqual(len(sequence), 20)
    self.assertEqual(sequence[0], self.patternMachine.get(0))
    self.assertEqual(sequence[10], None)
    self.assertEqual(sequence[11], self.patternMachine.get(10))


  def testAddSpatialNoise(self):
    patternMachine = PatternMachine(10000, 1000, num=100)
    sequenceMachine = SequenceMachine(patternMachine)
    numbers = range(0, 100)
    numbers.append(None)

    sequence = sequenceMachine.generateFromNumbers(numbers)
    noisy = sequenceMachine.addSpatialNoise(sequence, 0.5)

    overlap = len(noisy[0] & patternMachine.get(0))
    self.assertTrue(400 < overlap < 600)

    sequence = sequenceMachine.generateFromNumbers(numbers)
    noisy = sequenceMachine.addSpatialNoise(sequence, 0.0)

    overlap = len(noisy[0] & patternMachine.get(0))
    self.assertEqual(overlap, 1000)


  def testGenerateNumbers(self):
    numbers = self.sequenceMachine.generateNumbers(1, 100)
    self.assertEqual(numbers[-1], None)
    self.assertEqual(len(numbers), 101)
    self.assertFalse(numbers[:-1] == range(0, 100))
    self.assertEqual(sorted(numbers[:-1]), range(0, 100))


  def testGenerateNumbersMultipleSequences(self):
    numbers = self.sequenceMachine.generateNumbers(3, 100)
    self.assertEqual(len(numbers), 303)

    self.assertEqual(sorted(numbers[0:100]), range(0, 100))
    self.assertEqual(sorted(numbers[101:201]), range(100, 200))
    self.assertEqual(sorted(numbers[202:302]), range(200, 300))


  def testGenerateNumbersWithShared(self):
    numbers = self.sequenceMachine.generateNumbers(3, 100, (20, 35))
    self.assertEqual(len(numbers), 303)

    shared = range(300, 315)
    self.assertEqual(numbers[20:35], shared)
    self.assertEqual(numbers[20+101:35+101], shared)
    self.assertEqual(numbers[20+202:35+202], shared)



if __name__ == '__main__':
  unittest.main()
