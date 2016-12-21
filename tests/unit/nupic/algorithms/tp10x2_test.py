# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
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

"""Tests for the C++ implementation of the temporal pooler."""

import cPickle as pickle
import unittest2 as unittest

import numpy

from nupic.bindings.math import Random
from nupic.research import fdrutilities as fdrutils
from nupic.research.TP import TP
from nupic.research.TP10X2 import TP10X2

VERBOSITY = 0  # how chatty the unit tests should be
INFERENCE_VERBOSITY = 0  # Chattiness during inference test
SEED = 12
_RGEN = Random(SEED)



def checkCell0(tp):
  """Check that cell 0 has no incoming segments"""
  for c in range(tp.numberOfCols):
    assert tp.getNumSegmentsInCell(c, 0) == 0



def setVerbosity(verbosity, tp, tpPy):
  """Set verbosity levels of the TP's"""
  tp.cells4.setVerbosity(verbosity)
  tp.verbosity = verbosity
  tpPy.verbosity = verbosity



class TP10X2Test(unittest.TestCase):


  def basicTest(self):
    """Basic test (creation, pickling, basic run of learning and inference)"""
    # Create TP object
    tp = TP10X2(numberOfCols=10, cellsPerColumn=3, initialPerm=.2,
                connectedPerm= 0.8, minThreshold=2, newSynapseCount=5,
                permanenceInc=.1, permanenceDec= .05, permanenceMax=1,
                globalDecay=.05, activationThreshold=4, doPooling=False,
                segUpdateValidDuration=5, seed=SEED, verbosity=VERBOSITY)
    tp.retrieveLearningStates = True

    # Save and reload
    tp.makeCells4Ephemeral = False
    pickle.dump(tp, open("test_tp10x.pkl", "wb"))
    tp2 = pickle.load(open("test_tp10x.pkl"))

    self.assertTrue(fdrutils.tpDiff2(tp, tp2, VERBOSITY, checkStates=False))

    # Learn
    for i in xrange(5):
      x = numpy.zeros(tp.numberOfCols, dtype='uint32')
      _RGEN.initializeUInt32Array(x, 2)
      tp.learn(x)

    # Save and reload after learning
    tp.reset()
    tp.makeCells4Ephemeral = False
    pickle.dump(tp, open("test_tp10x.pkl", "wb"))
    tp2 = pickle.load(open("test_tp10x.pkl"))
    self.assertTrue(fdrutils.tpDiff2(tp, tp2, VERBOSITY))

    ## Infer
    patterns = numpy.zeros((4, tp.numberOfCols), dtype='uint32')
    for i in xrange(4):
      _RGEN.initializeUInt32Array(patterns[i], 2)

    for i in xrange(10):
      x = numpy.zeros(tp.numberOfCols, dtype='uint32')
      _RGEN.initializeUInt32Array(x, 2)
      tp.infer(x)
      if i > 0:
        tp.checkPrediction2(patterns)


  def basicTest2(self, tp, numPatterns=100, numRepetitions=3, activity=15,
                 testTrimming=False, testRebuild=False):
    """Basic test (basic run of learning and inference)"""
    # Create PY TP object that mirrors the one sent in.
    tpPy = TP(numberOfCols=tp.numberOfCols, cellsPerColumn=tp.cellsPerColumn,
              initialPerm=tp.initialPerm, connectedPerm=tp.connectedPerm,
              minThreshold=tp.minThreshold, newSynapseCount=tp.newSynapseCount,
              permanenceInc=tp.permanenceInc, permanenceDec=tp.permanenceDec,
              permanenceMax=tp.permanenceMax, globalDecay=tp.globalDecay,
              activationThreshold=tp.activationThreshold,
              doPooling=tp.doPooling,
              segUpdateValidDuration=tp.segUpdateValidDuration,
              pamLength=tp.pamLength, maxAge=tp.maxAge,
              maxSeqLength=tp.maxSeqLength,
              maxSegmentsPerCell=tp.maxSegmentsPerCell,
              maxSynapsesPerSegment=tp.maxSynapsesPerSegment,
              seed=tp.seed, verbosity=tp.verbosity)

    # Ensure we are copying over learning states for TPDiff
    tp.retrieveLearningStates = True

    verbosity = VERBOSITY

    # Learn

    # Build up sequences
    sequence = fdrutils.generateCoincMatrix(nCoinc=numPatterns,
                                            length=tp.numberOfCols,
                                            activity=activity)
    for r in xrange(numRepetitions):
      for i in xrange(sequence.nRows()):

        #if i > 11:
        #  setVerbosity(6, tp, tpPy)

        if i % 10 == 0:
          tp.reset()
          tpPy.reset()

        if verbosity >= 2:
          print "\n\n    ===================================\nPattern:",
          print i, "Round:", r, "input:", sequence.getRow(i)

        y1 = tp.learn(sequence.getRow(i))
        y2 = tpPy.learn(sequence.getRow(i))

        # Ensure everything continues to work well even if we continuously
        # rebuild outSynapses structure
        if testRebuild:
          tp.cells4.rebuildOutSynapses()

        if testTrimming:
          tp.trimSegments()
          tpPy.trimSegments()

        if verbosity > 2:
          print "\n   ------  CPP states  ------ ",
          tp.printStates()
          print "\n   ------  PY states  ------ ",
          tpPy.printStates()
          if verbosity > 6:
            print "C++ cells: "
            tp.printCells()
            print "PY cells: "
            tpPy.printCells()

        if verbosity >= 3:
          print "Num segments in PY and C++", tpPy.getNumSegments(), \
              tp.getNumSegments()

        # Check if the two TP's are identical or not. This check is slow so
        # we do it every other iteration. Make it every iteration for debugging
        # as needed.
        self.assertTrue(fdrutils.tpDiff2(tp, tpPy, verbosity, False))

        # Check that outputs are identical
        self.assertLess(abs((y1 - y2).sum()), 3)

    print "Learning completed"

    self.assertTrue(fdrutils.tpDiff2(tp, tpPy, verbosity))

    # TODO: Need to check - currently failing this
    #checkCell0(tpPy)

    # Remove unconnected synapses and check TP's again

    # Test rebuild out synapses
    print "Rebuilding outSynapses"
    tp.cells4.rebuildOutSynapses()
    self.assertTrue(fdrutils.tpDiff2(tp, tpPy, VERBOSITY))

    print "Trimming segments"
    tp.trimSegments()
    tpPy.trimSegments()
    self.assertTrue(fdrutils.tpDiff2(tp, tpPy, VERBOSITY))

    # Save and reload after learning
    print "Pickling and unpickling"
    tp.makeCells4Ephemeral = False
    pickle.dump(tp, open("test_tp10x.pkl", "wb"))
    tp2 = pickle.load(open("test_tp10x.pkl"))
    self.assertTrue(fdrutils.tpDiff2(tp, tp2, VERBOSITY, checkStates=False))

    # Infer
    print "Testing inference"

    # Setup for inference
    tp.reset()
    tpPy.reset()
    setVerbosity(INFERENCE_VERBOSITY, tp, tpPy)

    patterns = numpy.zeros((40, tp.numberOfCols), dtype='uint32')
    for i in xrange(4):
      _RGEN.initializeUInt32Array(patterns[i], 2)

    for i, x in enumerate(patterns):

      x = numpy.zeros(tp.numberOfCols, dtype='uint32')
      _RGEN.initializeUInt32Array(x, 2)
      y = tp.infer(x)
      yPy = tpPy.infer(x)

      self.assertTrue(fdrutils.tpDiff2(tp, tpPy, VERBOSITY, checkLearn=False))
      if abs((y - yPy).sum()) > 0:
        print "C++ output", y
        print "Py output", yPy
        assert False

      if i > 0:
        tp.checkPrediction2(patterns)
        tpPy.checkPrediction2(patterns)

    print "Inference completed"
    print "===================================="

    return tp, tpPy


  def testTPs(self, short=True):
    """Call basicTest2 with multiple parameter settings and ensure the C++ and
    PY versions are identical throughout."""

    if short == True:
      print "Testing short version"
    else:
      print "Testing long version"

    if short:
      print "\nTesting with fixed resource CLA - test max segment and synapses"
      tp = TP10X2(numberOfCols=30, cellsPerColumn=5,
             initialPerm=.5, connectedPerm= 0.5, permanenceMax=1,
             minThreshold=8, newSynapseCount=10,
             permanenceInc=0.1, permanenceDec=0.01,
             globalDecay=.0, activationThreshold=8,
             doPooling=False, segUpdateValidDuration=5,
             seed=SEED, verbosity=VERBOSITY,
             maxAge=0,
             maxSegmentsPerCell=2, maxSynapsesPerSegment=10,
             checkSynapseConsistency=True)
      tp.cells4.setCellSegmentOrder(True)
      self.basicTest2(tp, numPatterns=15, numRepetitions=1)

    if not short:
      print "\nTesting with fixed resource CLA - test max segment and synapses"
      tp = TP10X2(numberOfCols=30, cellsPerColumn=5,
             initialPerm = .5, connectedPerm= 0.5, permanenceMax = 1,
             minThreshold = 8, newSynapseCount = 10,
             permanenceInc = .1, permanenceDec= .01,
             globalDecay = .0, activationThreshold = 8,
             doPooling = False, segUpdateValidDuration = 5,
             seed=SEED, verbosity = VERBOSITY,
             maxAge = 0,
             maxSegmentsPerCell = 2, maxSynapsesPerSegment = 10,
             checkSynapseConsistency = True)
      tp.cells4.setCellSegmentOrder(1)
      self.basicTest2(tp, numPatterns=30, numRepetitions=2)

      print "\nTesting with permanenceInc = 0 and Dec = 0"
      tp = TP10X2(numberOfCols=30, cellsPerColumn=5,
              initialPerm = .5, connectedPerm= 0.5,
              minThreshold = 3, newSynapseCount = 3,
              permanenceInc = 0.0, permanenceDec= 0.00,
              permanenceMax = 1,
              globalDecay = .0, activationThreshold = 3,
              doPooling = False, segUpdateValidDuration = 5,
              seed=SEED, verbosity = VERBOSITY,
              checkSynapseConsistency = False)
      tp.printParameters()
      self.basicTest2(tp, numPatterns = 30, numRepetitions = 3)

      print "Testing with permanenceInc = 0 and Dec = 0 and 1 cell per column"
      tp = TP10X2(numberOfCols=30, cellsPerColumn=1,
              initialPerm = .5, connectedPerm= 0.5,
              minThreshold = 3, newSynapseCount = 3,
              permanenceInc = 0.0, permanenceDec= 0.0,
              permanenceMax = 1,
              globalDecay = .0, activationThreshold = 3,
              doPooling = False, segUpdateValidDuration = 5,
              seed=SEED, verbosity = VERBOSITY,
              checkSynapseConsistency = False)
      self.basicTest2(tp)

      print "Testing with permanenceInc = 0.1 and Dec = .0"
      tp = TP10X2(numberOfCols=30, cellsPerColumn=5,
             initialPerm = .5, connectedPerm= 0.5,
             minThreshold = 3, newSynapseCount = 3,
             permanenceInc = .1, permanenceDec= .0,
             permanenceMax = 1,
             globalDecay = .0, activationThreshold = 3,
             doPooling = False, segUpdateValidDuration = 5,
             seed=SEED, verbosity = VERBOSITY,
             checkSynapseConsistency = False)
      self.basicTest2(tp)

      print ("Testing with permanenceInc = 0.1, Dec = .01 and higher synapse "
             "count")
      tp = TP10X2(numberOfCols=30, cellsPerColumn=2,
             initialPerm = .5, connectedPerm= 0.5,
             minThreshold = 3, newSynapseCount = 5,
             permanenceInc = .1, permanenceDec= .01,
             permanenceMax = 1,
             globalDecay = .0, activationThreshold = 3,
             doPooling = False, segUpdateValidDuration = 5,
             seed=SEED, verbosity = VERBOSITY,
             checkSynapseConsistency = True)
      self.basicTest2(tp, numPatterns=10, numRepetitions=2)

      print "Testing age based global decay"
      tp = TP10X2(numberOfCols=30, cellsPerColumn=5,
              initialPerm = .4, connectedPerm= 0.5,
              minThreshold = 3, newSynapseCount = 3,
              permanenceInc = 0.1, permanenceDec= 0.1,
              permanenceMax = 1,
              globalDecay = .25, activationThreshold = 3,
              doPooling = False, segUpdateValidDuration = 5,
              pamLength = 2, maxAge = 20,
              seed=SEED, verbosity = VERBOSITY,
              checkSynapseConsistency = True)
      tp.cells4.setCellSegmentOrder(1)
      self.basicTest2(tp)

      print "\nTesting with fixed size CLA, max segments per cell"
      tp = TP10X2(numberOfCols=30, cellsPerColumn=5,
             initialPerm = .5, connectedPerm= 0.5, permanenceMax = 1,
             minThreshold = 8, newSynapseCount = 10,
             permanenceInc = .1, permanenceDec= .01,
             globalDecay = .0, activationThreshold = 8,
             doPooling = False, segUpdateValidDuration = 5,
             seed=SEED, verbosity = VERBOSITY,
             maxAge = 0,
             maxSegmentsPerCell = 2, maxSynapsesPerSegment = 100,
             checkSynapseConsistency = True)
      tp.cells4.setCellSegmentOrder(1)
      self.basicTest2(tp, numPatterns=30, numRepetitions=2)



if __name__ == '__main__':
  unittest.main()
