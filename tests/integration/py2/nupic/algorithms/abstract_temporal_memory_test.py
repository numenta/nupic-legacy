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

import unittest2 as unittest

from nupic.data.sequence_machine import SequenceMachine
from nupic.research.inspect_temporal_memory import (
  InspectTemporalMemory as TemporalMemory)
# Uncomment the lines below to run tests with TP10X2 implementation instead
# from nupic.research.inspect_temporal_memory_shim import (
#   InspectTemporalMemoryShim as TemporalMemory)



class AbstractTemporalMemoryTest(unittest.TestCase):

  VERBOSITY = 1
  DEFAULT_TM_PARAMS = {}
  PATTERN_MACHINE = None


  def setUp(self):
    self.tm = None
    self.patternMachine = None
    self.sequenceMachine = None


  def init(self, overrides=None):
    """
    Initialize Temporal Memory, and other member variables.

    :param overrides: overrides for default Temporal Memory parameters
    """
    params = self._computeTMParams(overrides)
    self.tm = TemporalMemory(**params)

    self.patternMachine = self.PATTERN_MACHINE
    self.sequenceMachine = SequenceMachine(self.patternMachine)


  def feedTM(self, sequence, learn=True, num=1):
    repeatedSequence = sequence * num

    self.tm.clearHistory()

    for pattern in repeatedSequence:
      if pattern is None:
        self.tm.reset()
      else:
        self.tm.compute(pattern, learn=learn)


  # ==============================
  # Helper functions
  # ==============================

  def _computeTMParams(self, overrides):
    params = dict(self.DEFAULT_TM_PARAMS)
    params.update(overrides or {})
    return params

