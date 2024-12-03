# Copyright 2014-2016 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

from abc import ABCMeta, abstractmethod

from nupic.algorithms.monitor_mixin.temporal_memory_monitor_mixin import (
  TemporalMemoryMonitorMixin)
from nupic.data.generators.sequence_machine import SequenceMachine



class AbstractTemporalMemoryTest(object):
  __metaclass__ = ABCMeta

  VERBOSITY = 1

  @abstractmethod
  def getTMClass(self):
    """
    Implement this method to specify the Temporal Memory class.
    """

  @abstractmethod
  def getPatternMachine(self):
    """
    Implement this method to provide the pattern machine.
    """

  def getDefaultTMParams(self):
    """
    Override this method to set the default TM params for `self.tm`.
    """
    return {}

  def setUp(self):
    self.tm = None
    self.patternMachine = self.getPatternMachine()
    self.sequenceMachine = SequenceMachine(self.patternMachine)


  def init(self, overrides=None):
    """
    Initialize Temporal Memory, and other member variables.

    :param overrides: overrides for default Temporal Memory parameters
    """
    params = self._computeTMParams(overrides)

    class MonitoredTemporalMemory(TemporalMemoryMonitorMixin,
                                  self.getTMClass()): pass
    self.tm = MonitoredTemporalMemory(**params)


  def feedTM(self, sequence, learn=True, num=1):
    repeatedSequence = sequence * num

    self.tm.mmClearHistory()

    for pattern in repeatedSequence:
      if pattern is None:
        self.tm.reset()
      else:
        self.tm.compute(pattern, learn=learn)


  # ==============================
  # Helper functions
  # ==============================

  def _computeTMParams(self, overrides):
    params = dict(self.getDefaultTMParams())
    params.update(overrides or {})
    return params
