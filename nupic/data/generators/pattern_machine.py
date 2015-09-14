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

"""
Utilities for generating and manipulating patterns, for use in
experimentation and tests.
"""

import numpy as np
from nupic.bindings.math import Random



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
    @param n   (int)      Number of available bits in pattern
    @param w   (int/list) Number of on bits in pattern
                          If list, each pattern will have a `w` randomly
                          selected from the list.
    @param num (int)      Number of available patterns
    """
    # Save member variables
    self._n = n
    self._w = w
    self._num = num

    # Initialize member variables
    self._random = Random(seed)
    self._patterns = dict()

    self._generate()


  def get(self, number):
    """
    Return a pattern for a number.

    @param number (int) Number of pattern

    @return (set) Indices of on bits
    """
    if not number in self._patterns:
      raise IndexError("Invalid number")

    return self._patterns[number]


  def addNoise(self, bits, amount):
    """
    Add noise to pattern.

    @param bits   (set)   Indices of on bits
    @param amount (float) Probability of switching an on bit with a random bit

    @return (set) Indices of on bits in noisy pattern
    """
    newBits = set()

    for bit in bits:
      if self._random.getReal64() < amount:
        newBits.add(self._random.getUInt32(self._n))
      else:
        newBits.add(bit)

    return newBits


  def numbersForBit(self, bit):
    """
    Return the set of pattern numbers that match a bit.

    @param bit (int) Index of bit

    @return (set) Indices of numbers
    """
    if bit >= self._n:
      raise IndexError("Invalid bit")

    numbers = set()

    for index, pattern in self._patterns.iteritems():
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
    numberItems = sorted(numberMap.iteritems(),
                         key=lambda (number, bits): len(bits),
                         reverse=True)

    for number, bits in numberItems:

      if verbosity > 2:
        strBits = [str(n) for n in bits]
        numberText = "{0} (bits: {1})".format(number, ",".join(strBits))
      elif verbosity > 1:
        numberText = "{0} ({1} bits)".format(number, len(bits))
      else:
        numberText = str(number)

      numberList.append(numberText)

    text += "[{0}]".format(", ".join(numberList))

    return text


  def _generate(self):
    """
    Generates set of random patterns.
    """
    candidates = np.array(range(self._n), np.uint32)
    for i in xrange(self._num):
      self._random.shuffle(candidates)
      pattern = candidates[0:self._getW()]
      self._patterns[i] = set(pattern)


  def _getW(self):
    """
    Gets a value of `w` for use in generating a pattern.
    """
    w = self._w

    if type(w) is list:
      return w[self._random.getUInt32(len(w))]
    else:
      return w



class ConsecutivePatternMachine(PatternMachine):
  """
  Pattern machine class that generates patterns with non-overlapping,
  consecutive on bits.
  """

  def _generate(self):
    """
    Generates set of consecutive patterns.
    """
    n = self._n
    w = self._w

    assert type(w) is int, "List for w not supported"

    for i in xrange(n / w):
      pattern = set(xrange(i * w, (i+1) * w))
      self._patterns[i] = pattern
