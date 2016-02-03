#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014-2016, Numenta, Inc.  Unless you have an agreement
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

import csv
import time
import unittest
import numpy

from pkg_resources import resource_filename

from nupic.research.temporal_memory import TemporalMemory as TemporalMemoryPy
from nupic.bindings.algorithms import TemporalMemory as TemporalMemoryCPP
from nupic.research.TP import TP
from nupic.research.TP10X2 import TP10X2

from nupic.encoders.random_distributed_scalar import RandomDistributedScalarEncoder


_INPUT_FILE_PATH = resource_filename(
  "nupic.datafiles", "extra/hotgym/rec-center-hourly.csv"
)

NUM_PATTERNS = 2000


# ==============================
# Tests
# ==============================

class TemporalMemoryPerformanceTest(unittest.TestCase):

  def setUp(self):
    self.tmPy = TemporalMemoryPy(columnDimensions=[2048],
                                 cellsPerColumn=32,
                                 initialPermanence=0.5,
                                 connectedPermanence=0.8,
                                 minThreshold=10,
                                 maxNewSynapseCount=12,
                                 permanenceIncrement=0.1,
                                 permanenceDecrement=0.05,
                                 activationThreshold=15)

    self.tmCPP = TemporalMemoryCPP(columnDimensions=[2048],
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

    self.scalarEncoder = RandomDistributedScalarEncoder(0.88)


  def testSingleSequence(self):
    print "Test: Single sequence"

    sequence = self._generateSequence()
    times = self._feedAll(sequence)

    self.assertTrue(times[1] < times[0])
    self.assertTrue(times[3] < times[2])


  # ==============================
  # Helper functions
  # ==============================

  def _generateSequence(self):
    sequence = []    
    with open (_INPUT_FILE_PATH) as fin:
      reader = csv.reader(fin)
      reader.next()
      reader.next()
      reader.next()
      for _ in xrange(NUM_PATTERNS):
        record = reader.next()
        value = float(record[1])
        encodedValue = self.scalarEncoder.encode(value)
        activeBits = set(encodedValue.nonzero()[0])
        sequence.append(activeBits)
    return sequence


  def _feedAll(self, sequence, learn=True, num=1):
    repeatedSequence = sequence * num

    def tmComputeFn(pattern, instance):
      instance.compute(pattern, learn)

    def tpComputeFn(pattern, instance):
      array = self._patternToNumpyArray(pattern)
      instance.compute(array, enableLearn=learn, computeInfOutput=True)

    modelParams = [
      (self.tmPy, tmComputeFn),
      (self.tmCPP, tmComputeFn),
      (self.tp, tpComputeFn),
      (self.tp10x2, tpComputeFn)
    ]
    times = [0] * len(modelParams)

    for patNum, pattern in enumerate(repeatedSequence):
      for ix, params in enumerate(modelParams):
        times[ix] += self._feedOne(pattern, *params)

    print "TM (py):\t{0}s".format(times[0])
    print "TM (C++):\t{0}s".format(times[1])
    print "TP:\t\t{0}s".format(times[2])
    print "TP10X2:\t\t{0}s".format(times[3])

    return times


  @staticmethod
  def _feedOne(pattern, instance, computeFn):
    start = time.clock()

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
# Main
# ==============================

if __name__ == "__main__":
  unittest.main()
