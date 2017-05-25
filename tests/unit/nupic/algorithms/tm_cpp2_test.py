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

"""Tests for the C++ implementation of the temporal memory."""

import cPickle as pickle
import numpy
import unittest2 as unittest
from nupic.bindings.math import Random

from nupic.algorithms import fdrutilities as fdrutils
from nupic.algorithms.backtracking_tm import BacktrackingTM
from nupic.algorithms.backtracking_tm_cpp import BacktrackingTMCPP

VERBOSITY = 0  # how chatty the unit tests should be
INFERENCE_VERBOSITY = 0  # Chattiness during inference test
SEED = 12
_RGEN = Random(SEED)



def checkCell0(tm):
  """Check that cell 0 has no incoming segments"""
  for c in range(tm.numberOfCols):
    assert tm.getNumSegmentsInCell(c, 0) == 0



def setVerbosity(verbosity, tm, tmPy):
  """Set verbosity levels of the TM's"""
  tm.cells4.setVerbosity(verbosity)
  tm.verbosity = verbosity
  tmPy.verbosity = verbosity



class BacktrackingTMCPP2Test(unittest.TestCase):


  def basicTest(self):
    """Basic test (creation, pickling, basic run of learning and inference)"""
    # Create TM object
    tm = BacktrackingTMCPP(numberOfCols=10, cellsPerColumn=3,
                           initialPerm=.2, connectedPerm= 0.8,
                           minThreshold=2, newSynapseCount=5,
                           permanenceInc=.1, permanenceDec= .05,
                           permanenceMax=1, globalDecay=.05,
                           activationThreshold=4, doPooling=False,
                           segUpdateValidDuration=5, seed=SEED,
                           verbosity=VERBOSITY)
    tm.retrieveLearningStates = True

    # Save and reload
    tm.makeCells4Ephemeral = False
    pickle.dump(tm, open("test_tm_cpp.pkl", "wb"))
    tm2 = pickle.load(open("test_tm_cpp.pkl"))

    self.assertTrue(fdrutils.tmDiff2(tm, tm2, VERBOSITY, checkStates=False))

    # Learn
    for i in xrange(5):
      x = numpy.zeros(tm.numberOfCols, dtype='uint32')
      _RGEN.initializeUInt32Array(x, 2)
      tm.learn(x)

    # Save and reload after learning
    tm.reset()
    tm.makeCells4Ephemeral = False
    pickle.dump(tm, open("test_tm_cpp.pkl", "wb"))
    tm2 = pickle.load(open("test_tm_cpp.pkl"))
    self.assertTrue(fdrutils.tmDiff2(tm, tm2, VERBOSITY))

    ## Infer
    patterns = numpy.zeros((4, tm.numberOfCols), dtype='uint32')
    for i in xrange(4):
      _RGEN.initializeUInt32Array(patterns[i], 2)

    for i in xrange(10):
      x = numpy.zeros(tm.numberOfCols, dtype='uint32')
      _RGEN.initializeUInt32Array(x, 2)
      tm.infer(x)
      if i > 0:
        tm._checkPrediction(patterns)


  def basicTest2(self, tm, numPatterns=100, numRepetitions=3, activity=15,
                 testTrimming=False, testRebuild=False):
    """Basic test (basic run of learning and inference)"""
    # Create PY TM object that mirrors the one sent in.
    tmPy = BacktrackingTM(numberOfCols=tm.numberOfCols,
                          cellsPerColumn=tm.cellsPerColumn,
                          initialPerm=tm.initialPerm,
                          connectedPerm=tm.connectedPerm,
                          minThreshold=tm.minThreshold,
                          newSynapseCount=tm.newSynapseCount,
                          permanenceInc=tm.permanenceInc,
                          permanenceDec=tm.permanenceDec,
                          permanenceMax=tm.permanenceMax,
                          globalDecay=tm.globalDecay,
                          activationThreshold=tm.activationThreshold,
                          doPooling=tm.doPooling,
                          segUpdateValidDuration=tm.segUpdateValidDuration,
                          pamLength=tm.pamLength, maxAge=tm.maxAge,
                          maxSeqLength=tm.maxSeqLength,
                          maxSegmentsPerCell=tm.maxSegmentsPerCell,
                          maxSynapsesPerSegment=tm.maxSynapsesPerSegment,
                          seed=tm.seed, verbosity=tm.verbosity)

    # Ensure we are copying over learning states for TMDiff
    tm.retrieveLearningStates = True

    verbosity = VERBOSITY

    # Learn

    # Build up sequences
    sequence = fdrutils.generateCoincMatrix(nCoinc=numPatterns,
                                            length=tm.numberOfCols,
                                            activity=activity)
    for r in xrange(numRepetitions):
      for i in xrange(sequence.nRows()):

        #if i > 11:
        #  setVerbosity(6, tm, tmPy)

        if i % 10 == 0:
          tm.reset()
          tmPy.reset()

        if verbosity >= 2:
          print "\n\n    ===================================\nPattern:",
          print i, "Round:", r, "input:", sequence.getRow(i)

        y1 = tm.learn(sequence.getRow(i))
        y2 = tmPy.learn(sequence.getRow(i))

        # Ensure everything continues to work well even if we continuously
        # rebuild outSynapses structure
        if testRebuild:
          tm.cells4.rebuildOutSynapses()

        if testTrimming:
          tm.trimSegments()
          tmPy.trimSegments()

        if verbosity > 2:
          print "\n   ------  CPP states  ------ ",
          tm.printStates()
          print "\n   ------  PY states  ------ ",
          tmPy.printStates()
          if verbosity > 6:
            print "C++ cells: "
            tm.printCells()
            print "PY cells: "
            tmPy.printCells()

        if verbosity >= 3:
          print "Num segments in PY and C++", tmPy.getNumSegments(), \
              tm.getNumSegments()

        # Check if the two TM's are identical or not. This check is slow so
        # we do it every other iteration. Make it every iteration for debugging
        # as needed.
        self.assertTrue(fdrutils.tmDiff2(tm, tmPy, verbosity, False))

        # Check that outputs are identical
        self.assertLess(abs((y1 - y2).sum()), 3)

    print "Learning completed"

    self.assertTrue(fdrutils.tmDiff2(tm, tmPy, verbosity))

    # TODO: Need to check - currently failing this
    #checkCell0(tmPy)

    # Remove unconnected synapses and check TM's again

    # Test rebuild out synapses
    print "Rebuilding outSynapses"
    tm.cells4.rebuildOutSynapses()
    self.assertTrue(fdrutils.tmDiff2(tm, tmPy, VERBOSITY))

    print "Trimming segments"
    tm.trimSegments()
    tmPy.trimSegments()
    self.assertTrue(fdrutils.tmDiff2(tm, tmPy, VERBOSITY))

    # Save and reload after learning
    print "Pickling and unpickling"
    tm.makeCells4Ephemeral = False
    pickle.dump(tm, open("test_tm_cpp.pkl", "wb"))
    tm2 = pickle.load(open("test_tm_cpp.pkl"))
    self.assertTrue(fdrutils.tmDiff2(tm, tm2, VERBOSITY, checkStates=False))

    # Infer
    print "Testing inference"

    # Setup for inference
    tm.reset()
    tmPy.reset()
    setVerbosity(INFERENCE_VERBOSITY, tm, tmPy)

    patterns = numpy.zeros((40, tm.numberOfCols), dtype='uint32')
    for i in xrange(4):
      _RGEN.initializeUInt32Array(patterns[i], 2)

    for i, x in enumerate(patterns):

      x = numpy.zeros(tm.numberOfCols, dtype='uint32')
      _RGEN.initializeUInt32Array(x, 2)
      y = tm.infer(x)
      yPy = tmPy.infer(x)

      self.assertTrue(fdrutils.tmDiff2(tm, tmPy, VERBOSITY, checkLearn=False))
      if abs((y - yPy).sum()) > 0:
        print "C++ output", y
        print "Py output", yPy
        assert False

      if i > 0:
        tm._checkPrediction(patterns)
        tmPy._checkPrediction(patterns)

    print "Inference completed"
    print "===================================="

    return tm, tmPy


  def testTMs(self, short=True):
    """Call basicTest2 with multiple parameter settings and ensure the C++ and
    PY versions are identical throughout."""

    if short == True:
      print "Testing short version"
    else:
      print "Testing long version"

    if short:
      print "\nTesting with fixed resource CLA - test max segment and synapses"
      tm = BacktrackingTMCPP(numberOfCols=30, cellsPerColumn=5,
                             initialPerm=.5, connectedPerm= 0.5,
                             permanenceMax=1,
                             minThreshold=8, newSynapseCount=10,
                             permanenceInc=0.1, permanenceDec=0.01,
                             globalDecay=.0, activationThreshold=8,
                             doPooling=False, segUpdateValidDuration=5,
                             seed=SEED, verbosity=VERBOSITY,
                             maxAge=0,
                             maxSegmentsPerCell=2, maxSynapsesPerSegment=10,
                             checkSynapseConsistency=True)
      tm.cells4.setCellSegmentOrder(True)
      self.basicTest2(tm, numPatterns=15, numRepetitions=1)

    if not short:
      print "\nTesting with fixed resource CLA - test max segment and synapses"
      tm = BacktrackingTMCPP(numberOfCols=30, cellsPerColumn=5,
                             initialPerm = .5, connectedPerm= 0.5,
                             permanenceMax = 1,
                             minThreshold = 8, newSynapseCount = 10,
                             permanenceInc = .1, permanenceDec= .01,
                             globalDecay = .0, activationThreshold = 8,
                             doPooling = False, segUpdateValidDuration = 5,
                             seed=SEED, verbosity = VERBOSITY,
                             maxAge = 0,
                             maxSegmentsPerCell = 2, maxSynapsesPerSegment = 10,
                             checkSynapseConsistency = True)
      tm.cells4.setCellSegmentOrder(1)
      self.basicTest2(tm, numPatterns=30, numRepetitions=2)

      print "\nTesting with permanenceInc = 0 and Dec = 0"
      tm = BacktrackingTMCPP(numberOfCols=30, cellsPerColumn=5,
                             initialPerm = .5, connectedPerm= 0.5,
                             minThreshold = 3, newSynapseCount = 3,
                             permanenceInc = 0.0, permanenceDec= 0.00,
                             permanenceMax = 1,
                             globalDecay = .0, activationThreshold = 3,
                             doPooling = False, segUpdateValidDuration = 5,
                             seed=SEED, verbosity = VERBOSITY,
                             checkSynapseConsistency = False)
      tm.printParameters()
      self.basicTest2(tm, numPatterns = 30, numRepetitions = 3)

      print "Testing with permanenceInc = 0 and Dec = 0 and 1 cell per column"
      tm = BacktrackingTMCPP(numberOfCols=30, cellsPerColumn=1,
                             initialPerm = .5, connectedPerm= 0.5,
                             minThreshold = 3, newSynapseCount = 3,
                             permanenceInc = 0.0, permanenceDec= 0.0,
                             permanenceMax = 1,
                             globalDecay = .0, activationThreshold = 3,
                             doPooling = False, segUpdateValidDuration = 5,
                             seed=SEED, verbosity = VERBOSITY,
                             checkSynapseConsistency = False)
      self.basicTest2(tm)

      print "Testing with permanenceInc = 0.1 and Dec = .0"
      tm = BacktrackingTMCPP(numberOfCols=30, cellsPerColumn=5,
                             initialPerm = .5, connectedPerm= 0.5,
                             minThreshold = 3, newSynapseCount = 3,
                             permanenceInc = .1, permanenceDec= .0,
                             permanenceMax = 1,
                             globalDecay = .0, activationThreshold = 3,
                             doPooling = False, segUpdateValidDuration = 5,
                             seed=SEED, verbosity = VERBOSITY,
                             checkSynapseConsistency = False)
      self.basicTest2(tm)

      print ("Testing with permanenceInc = 0.1, Dec = .01 and higher synapse "
             "count")
      tm = BacktrackingTMCPP(numberOfCols=30, cellsPerColumn=2,
                             initialPerm = .5, connectedPerm= 0.5,
                             minThreshold = 3, newSynapseCount = 5,
                             permanenceInc = .1, permanenceDec= .01,
                             permanenceMax = 1,
                             globalDecay = .0, activationThreshold = 3,
                             doPooling = False, segUpdateValidDuration = 5,
                             seed=SEED, verbosity = VERBOSITY,
                             checkSynapseConsistency = True)
      self.basicTest2(tm, numPatterns=10, numRepetitions=2)

      print "Testing age based global decay"
      tm = BacktrackingTMCPP(numberOfCols=30, cellsPerColumn=5,
                             initialPerm = .4, connectedPerm= 0.5,
                             minThreshold = 3, newSynapseCount = 3,
                             permanenceInc = 0.1, permanenceDec= 0.1,
                             permanenceMax = 1,
                             globalDecay = .25, activationThreshold = 3,
                             doPooling = False, segUpdateValidDuration = 5,
                             pamLength = 2, maxAge = 20,
                             seed=SEED, verbosity = VERBOSITY,
                             checkSynapseConsistency = True)
      tm.cells4.setCellSegmentOrder(1)
      self.basicTest2(tm)

      print "\nTesting with fixed size CLA, max segments per cell"
      tm = BacktrackingTMCPP(numberOfCols=30, cellsPerColumn=5,
                             initialPerm = .5, connectedPerm= 0.5, permanenceMax = 1,
                             minThreshold = 8, newSynapseCount = 10,
                             permanenceInc = .1, permanenceDec= .01,
                             globalDecay = .0, activationThreshold = 8,
                             doPooling = False, segUpdateValidDuration = 5,
                             seed=SEED, verbosity = VERBOSITY,
                             maxAge = 0,
                             maxSegmentsPerCell = 2, maxSynapsesPerSegment = 100,
                             checkSynapseConsistency = True)
      tm.cells4.setCellSegmentOrder(1)
      self.basicTest2(tm, numPatterns=30, numRepetitions=2)



if __name__ == '__main__':
  unittest.main()
