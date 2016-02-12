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
import numpy
import sys

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

class TemporalMemoryPerformanceBenchmark(object):


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


  def runAll(self):
    self.setUp()
    sequence = self._generateSequence()
    times = self._feedAll(sequence)
    return times


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
      self._printProgressBar(patNum, len(repeatedSequence), 50)

    return {"TM (py)": times[0],
            "TM (C++)": times[1],
            "TP.py": times[2],
            "TP10X2": times[3]}


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


  @staticmethod
  def _printProgressBar(completed, total, nDots):
    def numberOfDots(n):
      return (n * nDots) // total
    completedDots = numberOfDots(completed)
    if completedDots != numberOfDots(completed - 1):
      print "\r|" + ("." * completedDots) + (" " * (nDots - completedDots)) + "|",
      sys.stdout.flush()



def main():
  """Command-line entry point for TM performance benchmark."""
  times = TemporalMemoryPerformanceBenchmark().runAll()
  sortedTimes = sorted(times.iteritems(), key=lambda x: x[1])
  print
  for impl, t in sortedTimes:
    print "{}:\t{}s".format(impl, t)
