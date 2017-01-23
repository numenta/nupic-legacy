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
import unittest

from nupic.data.generators.pattern_machine import (PatternMachine,
                                                   ConsecutivePatternMachine)



class PatternMachineTest(unittest.TestCase):


  def setUp(self):
    self.patternMachine = PatternMachine(10000, 5, num=50)


  def testGet(self):
    patternA = self.patternMachine.get(48)
    self.assertEqual(len(patternA), 5)

    patternB = self.patternMachine.get(49)
    self.assertEqual(len(patternB), 5)

    self.assertEqual(patternA & patternB, set())


  def testGetOutOfBounds(self):
    args = [50]
    self.assertRaises(IndexError, self.patternMachine.get, *args)


  def testAddNoise(self):
    patternMachine = PatternMachine(10000, 1000, num=1)
    pattern = patternMachine.get(0)

    noisy = patternMachine.addNoise(pattern, 0.0)
    self.assertEqual(len(pattern & noisy), 1000)

    noisy = patternMachine.addNoise(pattern, 0.5)
    self.assertTrue(400 < len(pattern & noisy) < 600)

    noisy = patternMachine.addNoise(pattern, 1.0)
    self.assertTrue(50 < len(pattern & noisy) < 150)


  def testNumbersForBit(self):
    pattern = self.patternMachine.get(49)

    for bit in pattern:
      self.assertEqual(self.patternMachine.numbersForBit(bit), set([49]))


  def testNumbersForBitOutOfBounds(self):
    args = [10000]
    self.assertRaises(IndexError, self.patternMachine.numbersForBit, *args)


  def testNumberMapForBits(self):
    pattern = self.patternMachine.get(49)
    numberMap = self.patternMachine.numberMapForBits(pattern)

    self.assertEqual(numberMap.keys(), [49])
    self.assertEqual(numberMap[49], pattern)


  def testWList(self):
    w = [4, 7, 11]
    patternMachine = PatternMachine(100, w, num=50)
    widths = dict((el, 0) for el in w)

    for i in range(50):
      pattern = patternMachine.get(i)
      width = len(pattern)
      self.assertTrue(width in w)
      widths[len(pattern)] += 1

    for i in w:
      self.assertTrue(widths[i] > 0)


class ConsecutivePatternMachineTest(unittest.TestCase):


  def setUp(self):
    self.patternMachine = ConsecutivePatternMachine(100, 5)


  def testGet(self):
    pattern = self.patternMachine.get(18)
    self.assertEqual(len(pattern), 5)
    self.assertEqual(pattern, set([90, 91, 92, 93, 94]))

    pattern = self.patternMachine.get(19)
    self.assertEqual(len(pattern), 5)
    self.assertEqual(pattern, set([95, 96, 97, 98, 99]))


  def testGetOutOfBounds(self):
    args = [20]
    self.assertRaises(IndexError, self.patternMachine.get, *args)



if __name__ == '__main__':
  unittest.main()
