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

"""
Utilities for generating and manipulating patterns, for use in
experimentation and tests.
"""

import random



class PatternMachine(object):
  """
  Base pattern machine class.
  """

  def __init__(self,
               n,
               w,
               num=100,
               seed=42):
    """
    @param n   (int) Number of available bits in pattern
    @param w   (int) Number of on bits in pattern
    @param num (int) Number of available patterns
    """
    # Save member variables
    self.n = n
    self.w = w
    self.num = num

    # Initialize member variables
    random.seed(seed)
    self.patterns = dict()

    self._generate()


  def get(self, number):
    """
    Return a pattern for a number.

    @param number (int) Number of pattern

    @return (set) Indices of on bits
    """
    if not number in self.patterns:
      raise IndexError("Invalid number")

    return self.patterns[number]


  def numbersForBit(self, bit):
    """
    Return the set of pattern numbers that match a bit.

    @param bit (int) Index of bit

    @return (set) Indices of numbers
    """
    if bit >= self.n:
      raise IndexError("Invalid bit")

    numbers = set()

    for index, pattern in self.patterns.iteritems():
      if bit in pattern:
        numbers.add(index)

    return numbers


  def numberMapForBits(self, bits):
    """
    Return a map from number to matching on bits,
    for all numbers that match a set of bits.

    @param bits (set) Indices of bits

    @return (dict) Mapping from number => on bits.
    """
    numberMap = dict()

    for bit in bits:
      numbers = self.numbersForBit(bit)

      for number in numbers:
        if not number in numberMap:
          numberMap[number] = set()

        numberMap[number].add(bit)

    return numberMap


  def prettyPrintPattern(self, bits, verbosity=1):
    """
    Pretty print a pattern.

    @param bits      (set) Indices of on bits
    @param verbosity (int) Verbosity level

    @return (string) Pretty-printed text
    """
    numberMap = self.numberMapForBits(bits)
    text = ""

    numberList = []

    for number in numberMap.keys():

      if verbosity > 1:
        numberText = "{0} ({1} cells)".format(number, len(numberMap[number]))
      else:
        numberText = str(number)

      numberList.append(numberText)

    text += "[{0}]".format(", ".join(numberList))

    return text


  def _generate(self):
    """
    Generates set of random patterns.
    """
    for i in xrange(self.num):
      pattern = random.sample(xrange(self.n), self.w)
      self.patterns[i] = set(pattern)



class ConsecutivePatternMachine(PatternMachine):
  """
  Pattern machine class that generates patterns with non-overlapping,
  consecutive on bits.
  """

  def _generate(self):
    """
    Generates set of consecutive patterns.
    """
    n = self.n
    w = self.w

    for i in xrange(n / w):
      pattern = set(xrange(i * w, (i+1) * w))
      self.patterns[i] = pattern
