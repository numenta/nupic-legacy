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

"""
Overlapping sequences test
===========================

Test learning of sequences with shared (overlapping) subsequences.

Test 1 - Test with fast learning, make sure PAM allows us to train with fewer
repeats of the training data.

Test 2 - Test with slow learning, make sure PAM allows us to train with fewer
repeats of the training data.

Test 3 - Test with slow learning, some overlap in the patterns, and TM
thresholds of 80% of newSynapseCount

Test 4 - Test with "Forbes-like" data. A bunch of sequences of lengths between 2
and 10 elements long.

"""

import numpy
import pprint
import random
import sys
import unittest2 as unittest
from optparse import OptionParser

from nupic.algorithms import fdrutilities as fdrutils
from nupic.algorithms.backtracking_tm import BacktrackingTM
from nupic.algorithms.backtracking_tm_cpp import BacktrackingTMCPP
from nupic.support.unittesthelpers import testcasebase

VERBOSITY = 0         # how chatty the unit tests should be
SEED = 35             # the random seed used throughout
# Whether to only run the short tests.
SHORT = True

# If set to 0 the CPP TM will not be tested
INCLUDE_CPP_TM = 1    # Also test with CPP TM



def printOneTrainingVector(x):
  "Print a single vector succinctly."
  print ''.join('1' if k != 0 else '.' for k in x)



def printAllTrainingSequences(trainingSequences, upTo = 99999):
  for i,trainingSequence in enumerate(trainingSequences):
    print "============= Sequence",i,"================="
    for j,pattern in enumerate(trainingSequence):
      printOneTrainingVector(pattern)



def getSimplePatterns(numOnes, numPatterns, patternOverlap=0):
  """Very simple patterns. Each pattern has numOnes consecutive
  bits on. The amount of overlap between consecutive patterns is
  configurable, via the patternOverlap parameter.

  Parameters:
  -----------------------------------------------------------------------
  numOnes:        Number of bits ON in each pattern
  numPatterns:    Number of unique patterns to generate
  patternOverlap: Number of bits of overlap between each successive pattern
  retval:         patterns
  """

  assert (patternOverlap < numOnes)

  # How many new bits are introduced in each successive pattern?
  numNewBitsInEachPattern = numOnes - patternOverlap
  numCols = numNewBitsInEachPattern * numPatterns + patternOverlap

  p = []
  for i in xrange(numPatterns):
    x = numpy.zeros(numCols, dtype='float32')

    startBit = i*numNewBitsInEachPattern
    nextStartBit = startBit + numOnes
    x[startBit:nextStartBit] = 1

    p.append(x)

  return p



def buildOverlappedSequences( numSequences = 2,
                              seqLen = 5,
                              sharedElements = [3,4],
                              numOnBitsPerPattern = 3,
                              patternOverlap = 0,
                              seqOverlap = 0,
                              **kwargs
                              ):
  """ Create training sequences that share some elements in the middle.

  Parameters:
  -----------------------------------------------------
  numSequences:         Number of unique training sequences to generate
  seqLen:               Overall length of each sequence
  sharedElements:       Which element indices of each sequence are shared. These
                          will be in the range between 0 and seqLen-1
  numOnBitsPerPattern:  Number of ON bits in each TM input pattern
  patternOverlap:       Max number of bits of overlap between any 2 patterns
  retval:               (numCols, trainingSequences)
                          numCols - width of the patterns
                          trainingSequences - a list of training sequences

  """

  # Total number of patterns used to build the sequences
  numSharedElements = len(sharedElements)
  numUniqueElements = seqLen - numSharedElements
  numPatterns = numSharedElements + numUniqueElements * numSequences

  # Create the table of patterns
  patterns = getSimplePatterns(numOnBitsPerPattern, numPatterns, patternOverlap)

  # Total number of columns required
  numCols = len(patterns[0])


  # -----------------------------------------------------------------------
  # Create the training sequences
  trainingSequences = []

  uniquePatternIndices = range(numSharedElements, numPatterns)
  for i in xrange(numSequences):
    sequence = []

    # pattern indices [0 ... numSharedElements-1] are reserved for the shared
    #  middle
    sharedPatternIndices = range(numSharedElements)

    # Build up the sequence
    for j in xrange(seqLen):
      if j in sharedElements:
        patIdx = sharedPatternIndices.pop(0)
      else:
        patIdx = uniquePatternIndices.pop(0)
      sequence.append(patterns[patIdx])

    trainingSequences.append(sequence)


  if VERBOSITY >= 3:
    print "\nTraining sequences"
    printAllTrainingSequences(trainingSequences)

  return (numCols, trainingSequences)



def buildSequencePool(numSequences = 10,
                      seqLen = [2,3,4],
                      numPatterns = 5,
                      numOnBitsPerPattern = 3,
                      patternOverlap = 0,
                      **kwargs
                      ):
  """ Create a bunch of sequences of various lengths, all built from
  a fixed set of patterns.

  Parameters:
  -----------------------------------------------------
  numSequences:         Number of training sequences to generate
  seqLen:               List of possible sequence lengths
  numPatterns:          How many possible patterns there are to use within
                          sequences
  numOnBitsPerPattern:  Number of ON bits in each TM input pattern
  patternOverlap:       Max number of bits of overlap between any 2 patterns
  retval:               (numCols, trainingSequences)
                          numCols - width of the patterns
                          trainingSequences - a list of training sequences

  """


  # Create the table of patterns
  patterns = getSimplePatterns(numOnBitsPerPattern, numPatterns, patternOverlap)

  # Total number of columns required
  numCols = len(patterns[0])


  # -----------------------------------------------------------------------
  # Create the training sequences
  trainingSequences = []
  for i in xrange(numSequences):

    # Build it up from patterns
    sequence = []
    length = random.choice(seqLen)
    for j in xrange(length):
      patIdx = random.choice(xrange(numPatterns))
      sequence.append(patterns[patIdx])

    # Put it in
    trainingSequences.append(sequence)


  if VERBOSITY >= 3:
    print "\nTraining sequences"
    printAllTrainingSequences(trainingSequences)

  return (numCols, trainingSequences)



def createTMs(includeCPP = True,
              includePy = True,
              numCols = 100,
              cellsPerCol = 4,
              activationThreshold = 3,
              minThreshold = 3,
              newSynapseCount = 3,
              initialPerm = 0.6,
              permanenceInc = 0.1,
              permanenceDec = 0.0,
              globalDecay = 0.0,
              pamLength = 0,
              checkSynapseConsistency = True,
              maxInfBacktrack = 0,
              maxLrnBacktrack = 0,
              **kwargs
              ):

  """Create one or more TM instances, placing each into a dict keyed by
  name.

  Parameters:
  ------------------------------------------------------------------
  retval:   tms - dict of TM instances
  """

  # Keep these fixed:
  connectedPerm = 0.5

  tms = dict()

  if includeCPP:
    if VERBOSITY >= 2:
      print "Creating BacktrackingTMCPP instance"

    cpp_tm = BacktrackingTMCPP(numberOfCols = numCols, cellsPerColumn = cellsPerCol,
                               initialPerm = initialPerm, connectedPerm = connectedPerm,
                               minThreshold = minThreshold, newSynapseCount = newSynapseCount,
                               permanenceInc = permanenceInc, permanenceDec = permanenceDec,
                               activationThreshold = activationThreshold,
                               globalDecay = globalDecay, burnIn = 1,
                               seed=SEED, verbosity=VERBOSITY,
                               checkSynapseConsistency = checkSynapseConsistency,
                               collectStats = True,
                               pamLength = pamLength,
                               maxInfBacktrack = maxInfBacktrack,
                               maxLrnBacktrack = maxLrnBacktrack,
                               )

    # Ensure we are copying over learning states for TMDiff
    cpp_tm.retrieveLearningStates = True

    tms['CPP'] = cpp_tm


  if includePy:
    if VERBOSITY >= 2:
      print "Creating PY TM instance"

    py_tm = BacktrackingTM(numberOfCols = numCols, cellsPerColumn = cellsPerCol,
                           initialPerm = initialPerm, connectedPerm = connectedPerm,
                           minThreshold = minThreshold, newSynapseCount = newSynapseCount,
                           permanenceInc = permanenceInc, permanenceDec = permanenceDec,
                           activationThreshold = activationThreshold,
                           globalDecay = globalDecay, burnIn = 1,
                           seed=SEED, verbosity=VERBOSITY,
                           collectStats = True,
                           pamLength = pamLength,
                           maxInfBacktrack = maxInfBacktrack,
                           maxLrnBacktrack = maxLrnBacktrack,
                           )


    tms['PY '] = py_tm

  return tms



def assertNoTMDiffs(tms):
  """
  Check for diffs among the TM instances in the passed in tms dict and
  raise an assert if any are detected

  Parameters:
  ---------------------------------------------------------------------
  tms:                  dict of TM instances
  """

  if len(tms) == 1:
    return
  if len(tms) > 2:
    raise "Not implemented for more than 2 TMs"

  same = fdrutils.tmDiff2(*tms.values(), verbosity=VERBOSITY)
  assert(same)
  return



def evalSequences(tms,
                  trainingSequences,
                  testSequences = None,
                  nTrainRepetitions = 1,
                  doResets = True,
                  **kwargs):

  """Train the TMs on the entire training set for nTrainRepetitions in a row.
  Then run the test set through inference once and return the inference stats.

  Parameters:
  ---------------------------------------------------------------------
  tms:                  dict of TM instances
  trainingSequences:    list of training sequences. Each sequence is a list
                        of TM input patterns
  testSequences:        list of test sequences. If None, we will test against
                        the trainingSequences
  nTrainRepetitions:    Number of times to run the training set through the TM
  doResets:             If true, send a reset to the TM between each sequence
  """

  # If no test sequence is specified, use the first training sequence
  if testSequences == None:
    testSequences = trainingSequences

  # First TM instance is used by default for verbose printing of input values,
  #  etc.
  firstTP = tms.values()[0]

  assertNoTMDiffs(tms)

  # =====================================================================
  # Loop through the training set nTrainRepetitions times
  # ==========================================================================
  for trainingNum in xrange(nTrainRepetitions):
    if VERBOSITY >= 2:
      print "\n##############################################################"
      print "################# Training round #%d of %d #################" \
                % (trainingNum, nTrainRepetitions)
      for (name,tm) in tms.iteritems():
        print "TM parameters for %s: " % (name)
        print "---------------------"
        tm.printParameters()
        print

    # ======================================================================
    # Loop through the sequences in the training set
    numSequences = len(testSequences)
    for sequenceNum, trainingSequence in enumerate(trainingSequences):
      numTimeSteps = len(trainingSequence)

      if VERBOSITY >= 2:
        print "\n================= Sequence #%d of %d ================" \
                  % (sequenceNum, numSequences)

      if doResets:
        for tm in tms.itervalues():
          tm.reset()

      # --------------------------------------------------------------------
      # Train each element of the sequence
      for t, x in enumerate(trainingSequence):

        # Print Verbose info about this element
        if VERBOSITY >= 2:
          print
          if VERBOSITY >= 3:
            print "------------------------------------------------------------"
          print "--------- sequence: #%d of %d, timeStep: #%d of %d -----------" \
                  % (sequenceNum, numSequences, t, numTimeSteps)
          firstTP.printInput(x)
          print "input nzs:", x.nonzero()

        # Train in this element
        x = numpy.array(x).astype('float32')
        for tm in tms.itervalues():
          tm.learn(x, enableInference=True)

        # Print the input and output states
        if VERBOSITY >= 3:
          for (name,tm) in tms.iteritems():
            print "I/O states of %s TM:" % (name)
            print "-------------------------------------",
            tm.printStates(printPrevious = (VERBOSITY >= 5))
            print

        assertNoTMDiffs(tms)

        # Print out number of columns that weren't predicted
        if VERBOSITY >= 2:
          for (name,tm) in tms.iteritems():
            stats = tm.getStats()
            print "# of unpredicted columns for %s TM: %d of %d" \
                % (name, stats['curMissing'], x.sum())
            numBurstingCols = tm.infActiveState['t'].min(axis=1).sum()
            print "# of bursting columns for %s TM: %d of %d" \
                % (name, numBurstingCols, x.sum())


      # Print the trained cells
      if VERBOSITY >= 4:
        print "Sequence %d finished." % (sequenceNum)
        for (name,tm) in tms.iteritems():
          print "All cells of %s TM:" % (name)
          print "-------------------------------------",
          tm.printCells()
          print

    # --------------------------------------------------------------------
    # Done training all sequences in this round, print the total number of
    #  missing, extra columns and make sure it's the same among the TMs
    if VERBOSITY >= 2:
      print
    prevResult = None
    for (name,tm) in tms.iteritems():
      stats = tm.getStats()
      if VERBOSITY >= 1:
        print "Stats for %s TM over all sequences for training round #%d of %d:" \
                % (name, trainingNum, nTrainRepetitions)
        print "   total missing:", stats['totalMissing']
        print "   total extra:", stats['totalExtra']

      if prevResult is None:
        prevResult = (stats['totalMissing'], stats['totalExtra'])
      else:
        assert (stats['totalMissing'] == prevResult[0])
        assert (stats['totalExtra'] == prevResult[1])

      tm.resetStats()


  # =====================================================================
  # Finish up learning
  if VERBOSITY >= 3:
    print "Calling trim segments"
  prevResult = None
  for tm in tms.itervalues():
    nSegsRemoved, nSynsRemoved = tm.trimSegments()
    if prevResult is None:
      prevResult = (nSegsRemoved, nSynsRemoved)
    else:
      assert (nSegsRemoved == prevResult[0])
      assert (nSynsRemoved == prevResult[1])

  assertNoTMDiffs(tms)

  if VERBOSITY >= 4:
    print "Training completed. Complete state:"
    for (name,tm) in tms.iteritems():
      print "%s:" % (name)
      tm.printCells()
      print


  # ==========================================================================
  # Infer
  # ==========================================================================
  if VERBOSITY >= 2:
    print "\n##############################################################"
    print "########################## Inference #########################"

  # Reset stats in all TMs
  for tm in tms.itervalues():
    tm.resetStats()

  # -------------------------------------------------------------------
  # Loop through the test sequences
  numSequences = len(testSequences)
  for sequenceNum, testSequence in enumerate(testSequences):
    numTimeSteps = len(testSequence)

    # Identify this sequence
    if VERBOSITY >= 2:
      print "\n================= Sequence %d of %d ================" \
                % (sequenceNum, numSequences)

    # Send in the rest
    if doResets:
      for tm in tms.itervalues():
        tm.reset()

    # -------------------------------------------------------------------
    # Loop through the elements of this sequence
    for t,x in enumerate(testSequence):

      # Print verbose info about this element
      if VERBOSITY >= 2:
        print
        if VERBOSITY >= 3:
          print "------------------------------------------------------------"
        print "--------- sequence: #%d of %d, timeStep: #%d of %d -----------" \
                % (sequenceNum, numSequences, t, numTimeSteps)
        firstTP.printInput(x)
        print "input nzs:", x.nonzero()

      # Infer on this element
      for tm in tms.itervalues():
        tm.infer(x)

      assertNoTMDiffs(tms)

      # Print out number of columns that weren't predicted
      if VERBOSITY >= 2:
        for (name,tm) in tms.iteritems():
          stats = tm.getStats()
          print "# of unpredicted columns for %s TM: %d of %d" \
              % (name, stats['curMissing'], x.sum())

      # Debug print of internal state
      if VERBOSITY >= 3:
        for (name,tm) in tms.iteritems():
          print "I/O states of %s TM:" % (name)
          print "-------------------------------------",
          tm.printStates(printPrevious = (VERBOSITY >= 5),
                         printLearnState = False)
          print

    # Done with this sequence
    # Debug print of all stats of the TMs
    if VERBOSITY >= 4:
      print
      for (name,tm) in tms.iteritems():
        print "Interim internal stats for %s TM:" % (name)
        print "---------------------------------"
        pprint.pprint(tm.getStats())
        print


  if VERBOSITY >= 2:
    print "\n##############################################################"
    print "####################### Inference Done #######################"

  # Get the overall stats for each TM and return them
  tpStats = dict()
  for (name,tm) in tms.iteritems():
    tpStats[name] = stats = tm.getStats()
    if VERBOSITY >= 2:
      print "Stats for %s TM over all sequences:" % (name)
      print "   total missing:", stats['totalMissing']
      print "   total extra:", stats['totalExtra']

  for (name,tm) in tms.iteritems():
    if VERBOSITY >= 3:
      print "\nAll internal stats for %s TM:" % (name)
      print "-------------------------------------",
      pprint.pprint(tpStats[name])
      print

  return tpStats



def _testConfig(baseParams, expMissingMin=0, expMissingMax=0, **mods):
  """
  Build up a set of sequences, create the TM(s), train them, test them,
  and check that we got the expected number of missing predictions during
  inference.

  Parameters:
  -----------------------------------------------------------------------
  baseParams:     dict of all of the parameters for building sequences,
                      creating the TMs, and training and testing them. This
                      gets updated from 'mods' before we use it.

  expMissingMin:   Minimum number of expected missing predictions during testing.
  expMissingMax:   Maximum number of expected missing predictions during testing.

  mods:           dict of modifications to make to the baseParams.
  """


  # Update the base with the modifications
  params = dict(baseParams)
  params.update(mods)

  # --------------------------------------------------------------------
  # Create the sequences
  func = params['seqFunction']
  (numCols, trainingSequences) = func(**params)

  # --------------------------------------------------------------------
  # Create the TMs
  if params['numCols'] is None:
    params['numCols'] = numCols
  tps = createTMs(**params)

  # --------------------------------------------------------------------
  # Train and get test results
  tpStats = evalSequences(tms= tps,
                          trainingSequences=trainingSequences,
                          testSequences=None,
                          **params)

  # -----------------------------------------------------------------------
  # Make sure there are the expected number of missing predictions
  for (name, stats) in tpStats.iteritems():
    print "Detected %d missing predictions overall during inference" \
              % (stats['totalMissing'])
    if expMissingMin is not None and stats['totalMissing'] < expMissingMin:
      print "FAILURE: Expected at least %d total missing but got %d" \
          % (expMissingMin, stats['totalMissing'])
      assert False
    if expMissingMax is not None and stats['totalMissing'] > expMissingMax:
      print "FAILURE: Expected at most %d total missing but got %d" \
          % (expMissingMax, stats['totalMissing'])
      assert False


  return True


class TMOverlappingSeqsTest(testcasebase.TestCaseBase):

  def testFastLearning(self):
    """
    Test with fast learning, make sure PAM allows us to train with fewer
    repeats of the training data.
    """

    numOnBitsPerPattern = 3

    # ================================================================
    # Base params
    baseParams = dict(
        # Sequence generation
        seqFunction = buildOverlappedSequences,
        numSequences = 2,
        seqLen = 10,
        sharedElements = [2,3],
        numOnBitsPerPattern = numOnBitsPerPattern,

        # TM construction
        includeCPP = INCLUDE_CPP_TM,
        numCols = None,   # filled in based on generated sequences
        activationThreshold = numOnBitsPerPattern,
        minThreshold = numOnBitsPerPattern,
        newSynapseCount = numOnBitsPerPattern,
        initialPerm = 0.6,
        permanenceInc = 0.1,
        permanenceDec = 0.0,
        globalDecay = 0.0,
        pamLength = 0,

        # Training/testing
        nTrainRepetitions = 8,
        doResets = True,
        )


    # ================================================================
    # Run various configs
    # No PAM, with 3 repetitions, still missing predictions
    print "\nRunning without PAM, 3 repetitions of the training data..."
    self.assertTrue(_testConfig(baseParams=baseParams, expMissingMin=20,
                                expMissingMax=None, pamLength=1,
                                nTrainRepetitions=3))

    # With PAM, with only 3 repetitions, 0 missing predictions
    print "\nRunning with PAM, 3 repetitions of the training data..."
    self.assertTrue(_testConfig(baseParams=baseParams, expMissingMin=0,
                                expMissingMax=0, pamLength=5,
                                nTrainRepetitions=3))

  def testSlowLearning(self):
    """
    Test with slow learning, make sure PAM allows us to train with fewer
    repeats of the training data.
    """

    numOnBitsPerPattern = 3

    # ================================================================
    # Base params
    baseParams = dict(
        # Sequence generation
        seqFunction = buildOverlappedSequences,
        numSequences = 2,
        seqLen = 10,
        sharedElements = [2,3],
        numOnBitsPerPattern = numOnBitsPerPattern,

        # TM construction
        includeCPP = INCLUDE_CPP_TM,
        numCols = None,   # filled in based on generated sequences
        activationThreshold = numOnBitsPerPattern,
        minThreshold = numOnBitsPerPattern,
        newSynapseCount = numOnBitsPerPattern,
        initialPerm = 0.11,
        permanenceInc = 0.1,
        permanenceDec = 0.0,
        globalDecay = 0.0,
        pamLength = 0,

        # Training/testing
        nTrainRepetitions = 8,
        doResets = True,
        )


    # ================================================================
    # Run various configs
    # No PAM, requires 40 repetitions
    # No PAM, with 10 repetitions, still missing predictions
    print "\nRunning without PAM, 10 repetitions of the training data..."
    self.assertTrue(_testConfig(baseParams=baseParams, expMissingMin=10,
                                expMissingMax=None, pamLength=1,
                                nTrainRepetitions=10))

    # With PAM, with only 10 repetitions, 0 missing predictions
    print "\nRunning with PAM, 10 repetitions of the training data..."
    self.assertTrue(_testConfig(baseParams=baseParams, expMissingMin=0,
                                expMissingMax=0, pamLength=6,
                                nTrainRepetitions=10))

  def testSlowLearningWithOverlap(self):
    """
    Test with slow learning, some overlap in the patterns, and TM thresholds
    of 80% of newSynapseCount

    Make sure PAM allows us to train with fewer repeats of the training data.
    """
    # Cannot use skipIf decorator because it reads SHORT before it is set.
    if SHORT:
      self.skipTest("Test skipped by default. Enable with --long.")

    numOnBitsPerPattern = 5

    # ================================================================
    # Base params
    baseParams = dict(
                    # Sequence generation
                    seqFunction = buildOverlappedSequences,
                    numSequences = 2,
                    seqLen = 10,
                    sharedElements = [2,3],
                    numOnBitsPerPattern = numOnBitsPerPattern,
                    patternOverlap = 2,

                    # TM construction
                    includeCPP = INCLUDE_CPP_TM,
                    numCols = None,   # filled in based on generated sequences
                    activationThreshold = int(0.8 * numOnBitsPerPattern),
                    minThreshold = int(0.8 * numOnBitsPerPattern),
                    newSynapseCount = numOnBitsPerPattern,
                    initialPerm = 0.11,
                    permanenceInc = 0.1,
                    permanenceDec = 0.0,
                    globalDecay = 0.0,
                    pamLength = 0,

                    # Training/testing
                    nTrainRepetitions = 8,
                    doResets = True,
                    )


    # ================================================================
    # Run various configs
    # No PAM, with 10 repetitions, still missing predictions
    print "\nRunning without PAM, 10 repetitions of the training data..."
    self.assertTrue(_testConfig(baseParams=baseParams, expMissingMin=10,
                                expMissingMax=None, pamLength=1,
                                nTrainRepetitions=10))

    # With PAM, with only 10 repetitions, 0 missing predictions
    print "\nRunning with PAM, 10 repetitions of the training data..."
    self.assertTrue(_testConfig(baseParams=baseParams, expMissingMin=0,
                                expMissingMax=0, pamLength=6,
                                nTrainRepetitions=10))

  def testForbesLikeData(self):
    """
    Test with "Forbes-like" data. A bunch of sequences of lengths between 2
    and 10 elements long.

    We will test with both fast and slow learning.

    Make sure PAM allows us to train with fewer repeats of the training data.
    """
    # Cannot use skipIf decorator because it reads SHORT before it is set.
    if SHORT:
      self.skipTest("Test skipped by default. Enable with --long.")

    numOnBitsPerPattern = 3

    # ================================================================
    # Base params
    baseParams = dict(
        # Sequence generation
        seqFunction = buildSequencePool,
        numSequences = 20,
        seqLen = [3,10],
        numPatterns = 10,
        numOnBitsPerPattern = numOnBitsPerPattern,
        patternOverlap = 1,

        # TM construction
        includeCPP = INCLUDE_CPP_TM,
        numCols = None,   # filled in based on generated sequences
        activationThreshold = int(0.8 * numOnBitsPerPattern),
        minThreshold = int(0.8 * numOnBitsPerPattern),
        newSynapseCount = numOnBitsPerPattern,
        initialPerm = 0.51,
        permanenceInc = 0.1,
        permanenceDec = 0.0,
        globalDecay = 0.0,
        pamLength = 0,
        checkSynapseConsistency = False,

        # Training/testing
        nTrainRepetitions = 8,
        doResets = True,
        )


    # ================================================================
    # Run various configs
    # Fast mode, no PAM
    # Fast mode, with PAM
    print "\nRunning without PAM, fast learning, 2 repetitions of the " \
          "training data..."
    self.assertTrue(_testConfig(baseParams=baseParams, expMissingMin=50,
                                expMissingMax=None, pamLength=1,
                                nTrainRepetitions=2))

    # Fast mode, with PAM
    print "\nRunning with PAM, fast learning, 2 repetitions of the " \
          "training data..."
    self.assertTrue(_testConfig(baseParams=baseParams, expMissingMin=0,
                                expMissingMax=0, pamLength=5,
                                nTrainRepetitions=2))

    # Slow mode, no PAM
    print "\nRunning without PAM, slow learning, 8 repetitions of the " \
          "training data..."
    self.assertTrue(_testConfig(baseParams=baseParams, expMissingMin=1,
                                expMissingMax=None, initialPerm=0.31,
                                pamLength=1, nTrainRepetitions=8))

    # Fast mode, with PAM
    print "\nRunning with PAM, slow learning, 8 repetitions of the " \
          "training data..."
    self.assertTrue(_testConfig(baseParams=baseParams, expMissingMin=0,
                                expMissingMax=0, initialPerm=0.31, pamLength=5,
                                nTrainRepetitions=8))


if __name__=="__main__":
  # Process command line arguments
  parser = OptionParser()
  parser.add_option(
      "--verbosity", default=VERBOSITY, type="int",
      help="Verbosity level, either 0, 1, 2, or 3 [default: %default].")
  parser.add_option("--seed", default=SEED, type="int",
                    help="Random seed to use [default: %default].")
  parser.add_option("--short", action="store_true", default=True,
                    help="Run short version of the tests [default: %default].")
  parser.add_option("--long", action="store_true", default=False,
                    help="Run long version of the tests [default: %default].")

  (options, args) = parser.parse_args()
  SEED = options.seed
  VERBOSITY = options.verbosity
  SHORT = not options.long

  # Seed the random number generators
  rgen = numpy.random.RandomState(SEED)
  random.seed(SEED)

  if not INCLUDE_CPP_TM:
    print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    print "!!  WARNING: C++ TM testing is DISABLED until it can be updated."
    print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"

  # Form the command line for the unit test framework.
  args = [sys.argv[0]] + args

  unittest.main(argv=args, verbosity=VERBOSITY)
