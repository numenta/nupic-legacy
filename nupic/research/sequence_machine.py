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
Utilities for generating and manipulating sequences, for use in
experimentation and tests.
"""

import random



class SequenceMachine(object):
  """
  Base sequence machine class.
  """

  def __init__(self,
               patternMachine,
               seed=42):
    """
    @param patternMachine (PatternMachine) Pattern machine instance
    @param seed           (int)            Seed for random number generator
    """
    # Save member variables
    self.patternMachine = patternMachine

    # Initialize member variables
    random.seed(seed)


  def generateFromNumbers(self, numbers):
    """
    TODO
    """
    sequence = []

    for number in numbers:
      if number == None:
        sequence.append(number)
      else:
        pattern = self.patternMachine.get(number)
        sequence.append(pattern)

    return sequence


  def prettyPrintSequence(self, sequence, verbosity=1):
    """
    TODO
    """
    text = ""

    for pattern in sequence:
      if pattern == None:
        text += "<reset>\n"
      else:
        text += self.patternMachine.prettyPrintPattern(pattern,
                                                       verbosity=verbosity)

    return text
