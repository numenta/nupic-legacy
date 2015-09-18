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
Utilities for generating and manipulating sequences, for use in
experimentation and tests.
"""

import numpy as np
from nupic.bindings.math import Random



class SequenceMachine(object):
  """
  Base sequence machine class.
  """

  def __init__(self,
               patternMachine,
               seed=42):
    """
    @param patternMachine (PatternMachine) Pattern machine instance
    """
    # Save member variables
    self.patternMachine = patternMachine

    # Initialize member variables
    self._random = Random(seed)


  def generateFromNumbers(self, numbers):
    """
    Generate a sequence from a list of numbers.

    Note: Any `None` in the list of numbers is considered a reset.

    @param numbers (list) List of numbers

    @return (list) Generated sequence
    """
    sequence = []

    for number in numbers:
      if number == None:
        sequence.append(number)
      else:
        pattern = self.patternMachine.get(number)
        sequence.append(pattern)

    return sequence


  def addSpatialNoise(self, sequence, amount):
    """
    Add spatial noise to each pattern in the sequence.

    @param sequence (list)  Sequence
    @param amount   (float) Amount of spatial noise

    @return (list) Sequence with spatial noise
    """
    newSequence = []

    for pattern in sequence:
      if pattern is not None:
        pattern = self.patternMachine.addNoise(pattern, amount)
      newSequence.append(pattern)

    return newSequence


  def prettyPrintSequence(self, sequence, verbosity=1):
    """
    Pretty print a sequence.

    @param sequence  (list) Sequence
    @param verbosity (int)  Verbosity level

    @return (string) Pretty-printed text
    """
    text = ""

    for i in xrange(len(sequence)):
      pattern = sequence[i]

      if pattern == None:
        text += "<reset>"
        if i < len(sequence) - 1:
          text += "\n"
      else:
        text += self.patternMachine.prettyPrintPattern(pattern,
                                                       verbosity=verbosity)

    return text


  def generateNumbers(self, numSequences, sequenceLength, sharedRange=None):
    """
    @param numSequences   (int)   Number of sequences to return,
                                  separated by None
    @param sequenceLength (int)   Length of each sequence
    @param sharedRange    (tuple) (start index, end index) indicating range of
                                  shared subsequence in each sequence
                                  (None if no shared subsequences)
    @return (list) Numbers representing sequences
    """
    numbers = []

    if sharedRange:
      sharedStart, sharedEnd = sharedRange
      sharedLength = sharedEnd - sharedStart
      sharedNumbers = range(numSequences * sequenceLength,
                            numSequences * sequenceLength + sharedLength)

    for i in xrange(numSequences):
      start = i * sequenceLength
      newNumbers = np.array(range(start, start + sequenceLength), np.uint32)
      self._random.shuffle(newNumbers)
      newNumbers = list(newNumbers)

      if sharedRange is not None:
        newNumbers[sharedStart:sharedEnd] = sharedNumbers

      numbers += newNumbers
      numbers.append(None)

    return numbers
