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
import sys
import time
import unittest

import numpy

from nupic.research.pattern_machine import PatternMachine
from nupic.research.sequence_machine import SequenceMachine
from nupic.research.TM import TM
from nupic.research.TP import TP
from nupic.research.TP10X2 import TP10X2



SHOW_ENABLED = False



# ==============================
# Tests
# ==============================

class TemporalMemoryPerformanceTest(unittest.TestCase):

  def setUp(self):
    self.tm = TM(columnDimensions=[2048],
                 cellsPerColumn=32,
                 initialPermanence=0.5,
                 connectedPermanence=0.8,
                 minThreshold=10,
                 maxNewSynapseCount=12,
                 permanenceIncrement=0.1,
                 permanenceDecrement=0.05,
                 activationThreshold=15)

    self.tp = TP(numberOfCols=2048,
                 cellsPerColumn=32,
                 initialPerm=0.5,
                 connectedPerm=0.8,
                 minThreshold=10,
                 newSynapseCount=12,
                 permanenceInc=0.1,
                 permanenceDec=0.05,
                 activationThreshold=15,
                 globalDecay=0, burnIn=1,
                 checkSynapseConsistency=False,
                 pamLength=1)

    self.tp10x2 = TP10X2(numberOfCols=2048,
                         cellsPerColumn=32,
                         initialPerm=0.5,
                         connectedPerm=0.8,
                         minThreshold=10,
                         newSynapseCount=12,
                         permanenceInc=0.1,
                         permanenceDec=0.05,
                         activationThreshold=15,
                         globalDecay=0, burnIn=1,
                         checkSynapseConsistency=False,
                         pamLength=1)

    self.patternMachine = PatternMachine(2048, 40, num=100)
    self.sequenceMachine = SequenceMachine(self.patternMachine)


  def testSingleSequence(self):
    show("Test: Single sequence")
    sequence = self.sequenceMachine.generateFromNumbers(range(50))
    times = self._feedAll(sequence)

    self.assertLess(times[0], times[1])
    self.assertLess(times[2], times[1])
    self.assertLess(times[2], times[0])


  # ==============================
  # Helper functions
  # ==============================

  def _feedAll(self, sequence, learn=True, num=1):
    repeatedSequence = sequence * num
    times = []

    def tmComputeFn(pattern, instance):
      instance.compute(pattern, learn)

    def tpComputeFn(pattern, instance):
      array = self._patternToNumpyArray(pattern)
      instance.compute(array, enableLearn=learn, computeInfOutput=True)

    elapsed = self._feedOne(repeatedSequence, self.tm, tmComputeFn)
    times.append(elapsed)
    show("TM:\t{0}s".format(elapsed))

    elapsed = self._feedOne(repeatedSequence, self.tp, tpComputeFn)
    times.append(elapsed)
    show("TP:\t{0}s".format(elapsed))

    elapsed = self._feedOne(repeatedSequence, self.tp10x2, tpComputeFn)
    times.append(elapsed)
    show("TP10X2:\t{0}s".format(elapsed))

    return times


  @staticmethod
  def _feedOne(sequence, instance, computeFn):
    start = time.clock()

    for pattern in sequence:
      if pattern == None:
        instance.reset()
      else:
        computeFn(pattern, instance)

    elapsed = time.clock() - start

    return elapsed


  @staticmethod
  def _patternToNumpyArray(pattern):
    array = numpy.zeros(2048, dtype='int32')
    array[list(pattern)] = 1

    return array



# ==============================
# Show
# ==============================

def show(text):
  if SHOW_ENABLED:
    print text



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
