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
import argparse
import random

from pkg_resources import resource_filename

from nupic.encoders.random_distributed_scalar import RandomDistributedScalarEncoder


HOTGYM_PATH = resource_filename(
  "nupic.datafiles", "extra/hotgym/rec-center-hourly.csv"
)
HOTGYM_LENGTH = 4391


def printProgressBar(completed, total, nDots):
  numberOfDots = lambda n: (n * nDots) // total
  completedDots = numberOfDots(completed)
  if completedDots != numberOfDots(completed - 1):
    print "\r|" + ("." * completedDots) + (" " * (nDots - completedDots)) + "|",
    sys.stdout.flush()


def clearProgressBar(nDots):
  print "\r" + (" " * (nDots + 2))


class TemporalMemoryPerformanceBenchmark(object):

  def __init__(self):
    self.contestants = []


  def addContestant(self, constructor, paramsFn, computeFn, name):
    c = (constructor,
         paramsFn,
         computeFn,
         name)
    self.contestants.append(c)


  def _createInstances(self, cellsPerColumn):
    instances = []

    for i in xrange(len(self.contestants)):
      (constructor,
       paramsFn,
       computeFn,
       name) = self.contestants[i]

      params = paramsFn(cellsPerColumn=cellsPerColumn)

      tmInstance = constructor(**params)

      instances.append(tmInstance)

    return instances


  def runSimpleSequence(self, resets, repetitions=1):
    scalarEncoder = RandomDistributedScalarEncoder(0.88, n=2048, w=41)

    instances = self._createInstances(cellsPerColumn=32)
    times = [0.0] * len(self.contestants)

    duration = 10000 * repetitions
    increment = 4
    sequenceLength = 25
    sequence = (i % (sequenceLength * 4)
                for i in xrange(0, duration * increment, increment))
    t = 0

    encodedValue = numpy.zeros(2048, dtype=numpy.int32)

    for value in sequence:
      scalarEncoder.encodeIntoArray(value, output=encodedValue)
      activeBits = encodedValue.nonzero()[0]

      for i in xrange(len(self.contestants)):
        tmInstance = instances[i]
        computeFn = self.contestants[i][2]

        if resets:
          if value == 0:
            tmInstance.reset()

        start = time.clock()
        computeFn(tmInstance, encodedValue, activeBits)
        times[i] += time.clock() - start

      printProgressBar(t, duration, 50)
      t += 1

    clearProgressBar(50)

    results = []
    for i in xrange(len(self.contestants)):
      name = self.contestants[i][3]
      results.append((name,
                      times[i],))

    return results


  def runHotgym(self, cellsPerColumn, repetitions=1):
    scalarEncoder = RandomDistributedScalarEncoder(0.88, n=2048, w=41)

    instances = self._createInstances(cellsPerColumn=cellsPerColumn)
    times = [0.0] * len(self.contestants)

    t = 0
    duration = HOTGYM_LENGTH * repetitions

    for _ in xrange(repetitions):
      with open(HOTGYM_PATH) as fin:
        reader = csv.reader(fin)
        reader.next()
        reader.next()
        reader.next()

        encodedValue = numpy.zeros(2048, dtype=numpy.int32)

        for timeStr, valueStr in reader:
          value = float(valueStr)
          scalarEncoder.encodeIntoArray(value, output=encodedValue)
          activeBits = encodedValue.nonzero()[0]

          for i in xrange(len(self.contestants)):
            tmInstance = instances[i]
            computeFn = self.contestants[i][2]

            start = time.clock()
            computeFn(tmInstance, encodedValue, activeBits)
            times[i] += time.clock() - start

          printProgressBar(t, duration, 50)
          t += 1

    clearProgressBar(50)

    results = []
    for i in xrange(len(self.contestants)):
      name = self.contestants[i][3]
      results.append((name,
                      times[i],))

    return results


  def runRandom(self, repetitions=1):
    scalarEncoder = RandomDistributedScalarEncoder(0.88, n=2048, w=41)

    instances = self._createInstances(cellsPerColumn=32)
    times = [0.0] * len(self.contestants)

    duration = 1000 * repetitions
    t = 0

    encodedValue = numpy.zeros(2048, dtype=numpy.int32)

    for _ in xrange(duration):
      activeBits = random.sample(xrange(2048), 40)
      encodedValue = numpy.zeros(2048, dtype=numpy.int32)
      encodedValue[activeBits] = 1

      for i in xrange(len(self.contestants)):
        tmInstance = instances[i]
        computeFn = self.contestants[i][2]

        start = time.clock()
        computeFn(tmInstance, encodedValue, activeBits)
        times[i] += time.clock() - start

      printProgressBar(t, duration, 50)
      t += 1

    clearProgressBar(50)

    results = []
    for i in xrange(len(self.contestants)):
      name = self.contestants[i][3]
      results.append((name,
                      times[i],))

    return results


# Some tests might change certain model parameters like cellsPerColumn. Add
# other arguments to these paramsFns as we add tests that specify other params.

def tmParamsFn(cellsPerColumn):
  return {
    "columnDimensions": [2048],
    "cellsPerColumn": cellsPerColumn,
    "initialPermanence": 0.5,
    "connectedPermanence": 0.8,
    "minThreshold": 10,
    "maxNewSynapseCount": 12,
    "permanenceIncrement": 0.1,
    "permanenceDecrement": 0.05,
    "activationThreshold": 15
  }


def tpParamsFn(cellsPerColumn):
  return {
    "numberOfCols": 2048,
    "cellsPerColumn": cellsPerColumn,
    "initialPerm": 0.5,
    "connectedPerm": 0.8,
    "minThreshold": 10,
    "newSynapseCount": 12,
    "permanenceInc": 0.1,
    "permanenceDec": 0.05,
    "activationThreshold": 15,
    "globalDecay": 0,
    "burnIn": 1,
    "checkSynapseConsistency": False,
    "pamLength": 1,
  }


def tmComputeFn(instance, encoding, activeBits):
  instance.compute(activeBits, learn=True)


def tpComputeFn(instance, encoding, activeBits):
  instance.compute(encoding, enableLearn=True, computeInfOutput=True)


def before(args, printMe):
  print printMe
  if args.pause:
    raw_input("Press enter to continue. ")


def after(results):
  for impl, t in sorted(results, key=lambda x: x[1]):
    print "%s: %fs" % (impl, t)
  print
  print


if __name__ == "__main__":
  parser = argparse.ArgumentParser()

  impNames = ["tm_cpp", "tm_py", "tp_py", "tp_cpp"]
  testNames = ["simple_sequence", "simple_sequence_no_resets",
               "hotgym", "hotgym_1_cell", "random", "5_random",
               "20_simple_sequence", "20_simple_sequence_no_resets",
               "20_hotgym", "20_hotgym_1_cell"]

  parser.add_argument("-i", "--implementations",
                      nargs="*",
                      type=str,
                      help=("Which temporal memory implementations to use. " +
                            "Options: %s" % ", ".join(impNames)),
                      default=["tm_cpp"])

  parser.add_argument("-t", "--tests",
                      nargs="*",
                      type=str,
                      help=("The tests to run. Options: %s"
                            % ", ".join(testNames)),
                      default=testNames)

  parser.add_argument("--pause",
                      help="Pause before each test.",
                      default=False,
                      action="store_true")

  args = parser.parse_args()

  # Handle comma-seperated list argument.
  if len(args.implementations) == 1:
    args.implementations = args.implementations[0].split(",")
  if len(args.tests) == 1:
    args.tests = args.tests[0].split(",")

  benchmark = TemporalMemoryPerformanceBenchmark()

  if "tm_cpp" in args.implementations:
    import nupic.bindings.algorithms
    benchmark.addContestant(
      nupic.bindings.algorithms.TemporalMemory,
      paramsFn=tmParamsFn,
      computeFn=tmComputeFn,
      name="TM (C++)")

  if "tm_py" in args.implementations:
    import nupic.research.temporal_memory
    benchmark.addContestant(
      nupic.research.temporal_memory.TemporalMemory,
      paramsFn=tmParamsFn,
      computeFn=tmComputeFn,
      name="TM (py)")

  if "tp_py" in args.implementations:
    import nupic.research.TP
    benchmark.addContestant(
      nupic.research.TP.TP,
      paramsFn=tpParamsFn,
      computeFn=tpComputeFn,
      name="TP")

  if "tp_cpp" in args.implementations:
    import nupic.research.TP10X2
    benchmark.addContestant(
      nupic.research.TP10X2.TP10X2,
      paramsFn=tpParamsFn,
      computeFn=tpComputeFn,
      name="TP10X2")


  if "simple_sequence" in args.tests:
    before(args, "Test: simple repeating sequence")
    results = benchmark.runSimpleSequence(resets=True)
    after(results)


  if "simple_sequence_no_resets" in args.tests:
    before(args, "Test: simple repeating sequence (no resets)")
    results = benchmark.runSimpleSequence(resets=False)
    after(results)


  if "20_simple_sequence" in args.tests:
    before(args, "Test: simple repeating sequence, times 20")
    results = benchmark.runSimpleSequence(repetitions=20, resets=True)
    after(results)


  if "20_simple_sequence_no_resets" in args.tests:
    before(args, "Test: simple repeating sequence, times 20 (no resets)")
    results = benchmark.runSimpleSequence(repetitions=20, resets=False)
    after(results)


  if "hotgym" in args.tests:
    before(args, "Test: hotgym")
    results = benchmark.runHotgym(cellsPerColumn=32)
    after(results)


  if "hotgym_1_cell" in args.tests:
    before(args, "Test: hotgym (1 cell per column)")
    results = benchmark.runHotgym(cellsPerColumn=1)
    after(results)


  if "20_hotgym" in args.tests:
    before(args, "Test: hotgym, 20 times")
    results = benchmark.runHotgym(cellsPerColumn=32,
                                  repetitions=20)
    after(results)


  if "20_hotgym_1_cell" in args.tests:
    before(args, "Test: hotgym, 20 times (1 cell per column)")
    results = benchmark.runHotgym(cellsPerColumn=1,
                                  repetitions=20)
    after(results)


  if "random" in args.tests:
    before(args, "Test: random column SDRs")
    results = benchmark.runRandom(repetitions=1)
    after(results)


  if "5_random" in args.tests:
    before(args, "Test: random column SDRs, times 5")
    results = benchmark.runRandom(repetitions=5)
    after(results)
