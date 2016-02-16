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

import collections
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


  @classmethod
  def setUp(cls):
    tmPy = TemporalMemoryPy(columnDimensions=[2048],
                            cellsPerColumn=32,
                            initialPermanence=0.5,
                            connectedPermanence=0.8,
                            minThreshold=10,
                            maxNewSynapseCount=12,
                            permanenceIncrement=0.1,
                            permanenceDecrement=0.05,
                            activationThreshold=15)

    tmCPP = TemporalMemoryCPP(columnDimensions=[2048],
                              cellsPerColumn=32,
                              initialPermanence=0.5,
                              connectedPermanence=0.8,
                              minThreshold=10,
                              maxNewSynapseCount=12,
                              permanenceIncrement=0.1,
                              permanenceDecrement=0.05,
                              activationThreshold=15)

    tp = TP(numberOfCols=2048,
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

    tp10x2 = TP10X2(numberOfCols=2048,
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

    def tmComputeFn(pattern, instance):
      instance.compute(pattern, True)

    def tpComputeFn(pattern, instance):
      array = cls._patternToNumpyArray(pattern)
      instance.compute(array, enableLearn=True, computeInfOutput=True)

    return (
        ("TM (py)", tmPy, tmComputeFn),
        ("TM (C++)", tmCPP, tmComputeFn),
        ("TP", tp, tpComputeFn),
        ("TP10X2", tp10x2, tpComputeFn),
    )


  @classmethod
  def runAll(cls):
    impls = cls.setUp()
    sequence = cls._generateSequence()
    times = cls._feedAll(impls, sequence)
    return times


  @staticmethod
  def _generateSequence():
    scalarEncoder = RandomDistributedScalarEncoder(0.88)
    sequence = []
    with open (_INPUT_FILE_PATH) as fin:
      reader = csv.reader(fin)
      reader.next()
      reader.next()
      reader.next()
      for _ in xrange(NUM_PATTERNS):
        record = reader.next()
        value = float(record[1])
        encodedValue = scalarEncoder.encode(value)
        activeBits = set(encodedValue.nonzero()[0])
        sequence.append(activeBits)
    return sequence


  @classmethod
  def _feedAll(cls, impls, sequence):
    repeatedSequence = sequence

    times = collections.defaultdict(float)

    for patNum, pattern in enumerate(repeatedSequence):
      for name, impl, fn in impls:
        times[name] += cls._feedOne(pattern, impl, fn)
      cls._printProgressBar(patNum, len(repeatedSequence), 50)

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


  @staticmethod
  def _printProgressBar(completed, total, nDots):
    def numberOfDots(n):
      return (n * nDots) // total
    completedDots = numberOfDots(completed)
    if completedDots != numberOfDots(completed - 1):
      print "\r|" + ("." * completedDots) + (" " * (nDots - completedDots)) + "|",
      sys.stdout.flush()



if __name__ == "__main__":
  times = TemporalMemoryPerformanceBenchmark().runAll()
  sortedTimes = sorted(times.iteritems(), key=lambda x: x[1])
  print
  for impl, t in sortedTimes:
    print "{}: {}s".format(impl, t)
