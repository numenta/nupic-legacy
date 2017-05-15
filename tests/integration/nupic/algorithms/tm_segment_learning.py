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
Segment Learning Tests
======================

Multi-attribute sequence tests.

SL1) Train the TM repeatedly using a single sequence plus noise. The sequence
can be relatively short, say 5 patterns. Add random noise each time a pattern is
presented. The noise should be different for each presentation and can be equal
to the number of on bits in the pattern.

Simplified patterns will be used, where each pattern consists of consecutive
bits and no two patterns share columns. The patterns that belong to the sequence
will be in the left half of the input vector. The noise bits will be in the
right half of the input vector.

After several iterations of each sequence, the TM should should achieve perfect
inference on the true sequence. There should be resets between each presentation
of the sequence. Check predictions in the sequence part only (it's ok to predict
random bits in the right half of the column space), and test with clean
sequences.

SL2) As above but train with 3 different inter-leaved sequences.

SL3)  Vary percentage of bits that are signal vs noise.

SL4) Noise can be a fixed alphabet instead of being randomly generated.

SL5) Have two independent sequences, one in the left half, and one in the
right half. Both should be learned well.


"""

import numpy
import unittest2 as unittest

from nupic.algorithms import fdrutilities as fdrutils
from nupic.algorithms.backtracking_tm import BacktrackingTM
from nupic.algorithms.backtracking_tm_cpp import BacktrackingTMCPP
from nupic.support.unittesthelpers import testcasebase

g_testCPPTM = True



class ExperimentTestBaseClass(testcasebase.TestCaseBase):
  """ The base class for all of our tests in this module"""


  def __init__(self, testMethodName, *args, **kwargs):
    # Construct the base-class instance
    super(ExperimentTestBaseClass, self).__init__(testMethodName, *args,
                                                  **kwargs)

    # Module specific instance variables
    self._rgen = numpy.random.RandomState(g_options.seed)


  def _printOneTrainingVector(self, x):
    """Print a single vector succinctly."""
    print ''.join('1' if k != 0 else '.' for k in x)


  def _printAllTrainingSequences(self, trainingSequences):
    """Print all vectors"""
    for i, trainingSequence in enumerate(trainingSequences):
      print "============= Sequence", i, "================="
      for pattern in trainingSequence:
        self._printOneTrainingVector(pattern)


  def _setVerbosity(self, verbosity, tm, tmPy):
    """Set verbosity level on the TM"""
    tm.cells4.setVerbosity(verbosity)
    tm.verbosity = verbosity
    tmPy.verbosity = verbosity


  def _createTMs(self, numCols, fixedResources=False,
                 checkSynapseConsistency = True):
    """Create an instance of the appropriate temporal memory. We isolate
    all parameters as constants specified here."""

    # Keep these fixed:
    minThreshold = 4
    activationThreshold = 8
    newSynapseCount = 15
    initialPerm = 0.3
    connectedPerm = 0.5
    permanenceInc = 0.1
    permanenceDec = 0.05

    if fixedResources:
      permanenceDec = 0.1
      maxSegmentsPerCell = 5
      maxSynapsesPerSegment = 15
      globalDecay = 0
      maxAge = 0
    else:
      permanenceDec = 0.05
      maxSegmentsPerCell = -1
      maxSynapsesPerSegment = -1
      globalDecay = 0.0001
      maxAge = 1


    if g_testCPPTM:
      if g_options.verbosity > 1:
        print "Creating BacktrackingTMCPP instance"

      cppTM = BacktrackingTMCPP(numberOfCols = numCols, cellsPerColumn = 4,
                                initialPerm = initialPerm, connectedPerm = connectedPerm,
                                minThreshold = minThreshold,
                                newSynapseCount = newSynapseCount,
                                permanenceInc = permanenceInc,
                                permanenceDec = permanenceDec,
                                activationThreshold = activationThreshold,
                                globalDecay = globalDecay, maxAge=maxAge, burnIn = 1,
                                seed=g_options.seed, verbosity=g_options.verbosity,
                                checkSynapseConsistency = checkSynapseConsistency,
                                pamLength = 1000,
                                maxSegmentsPerCell = maxSegmentsPerCell,
                                maxSynapsesPerSegment = maxSynapsesPerSegment,
                                )
      # Ensure we are copying over learning states for TMDiff
      cppTM.retrieveLearningStates = True

    else:
      cppTM = None

    if g_options.verbosity > 1:
      print "Creating PY TM instance"
    pyTM = BacktrackingTM(numberOfCols = numCols, cellsPerColumn = 4,
                          initialPerm = initialPerm,
                          connectedPerm = connectedPerm,
                          minThreshold = minThreshold,
                          newSynapseCount = newSynapseCount,
                          permanenceInc = permanenceInc,
                          permanenceDec = permanenceDec,
                          activationThreshold = activationThreshold,
                          globalDecay = globalDecay, maxAge=maxAge, burnIn = 1,
                          seed=g_options.seed, verbosity=g_options.verbosity,
                          pamLength = 1000,
                          maxSegmentsPerCell = maxSegmentsPerCell,
                          maxSynapsesPerSegment = maxSynapsesPerSegment,
                          )

    return cppTM, pyTM


  def _getSimplePatterns(self, numOnes, numPatterns):
    """Very simple patterns. Each pattern has numOnes consecutive
    bits on. There are numPatterns*numOnes bits in the vector. These patterns
    are used as elements of sequences when building up a training set."""

    numCols = numOnes * numPatterns
    p = []
    for i in xrange(numPatterns):
      x = numpy.zeros(numCols, dtype='float32')
      x[i*numOnes:(i+1)*numOnes] = 1
      p.append(x)

    return p


  def _buildSegmentLearningTrainingSet(self, numOnes=10, numRepetitions= 10):
    """A simple sequence of 5 patterns. The left half of the vector contains
    the pattern elements, each with numOnes consecutive bits. The right half
    contains numOnes random bits. The function returns a pair:

    trainingSequences:    A list containing numRepetitions instances of the
                          above sequence
    testSequence:         A single clean test sequence containing the 5 patterns
                          but with no noise on the right half

    """

    numPatterns = 5
    numCols = 2 * numPatterns * numOnes
    halfCols = numPatterns * numOnes
    numNoiseBits = numOnes
    p = self._getSimplePatterns(numOnes, numPatterns)

    # Create noisy training sequence
    trainingSequences = []
    for i in xrange(numRepetitions):
      sequence = []
      for j in xrange(numPatterns):

        # Make left half
        v = numpy.zeros(numCols)
        v[0:halfCols] = p[j]

        # Select numOnes noise bits
        noiseIndices = (self._rgen.permutation(halfCols)
                            + halfCols)[0:numNoiseBits]
        v[noiseIndices] = 1
        sequence.append(v)
      trainingSequences.append(sequence)

    # Create a single clean test sequence
    testSequence = []
    for j in xrange(numPatterns):
      # Make only left half
      v = numpy.zeros(numCols, dtype='float32')
      v[0:halfCols] = p[j]
      testSequence.append(v)

    if g_options.verbosity > 1:
      print "\nTraining sequences"
      self.printAllTrainingSequences(trainingSequences)
      print "\nTest sequence"
      self.printAllTrainingSequences([testSequence])

    return (trainingSequences, [testSequence])


  def _buildSL2TrainingSet(self, numOnes=10, numRepetitions= 10):
    """Three simple sequences, composed of the same 5 static patterns. The left
    half of the vector contains the pattern elements, each with numOnes
    consecutive bits. The right half contains numOnes random bits.

    Sequence 1 is: p0, p1, p2, p3, p4
    Sequence 2 is: p4, p3, p2, p1, p0
    Sequence 3 is: p2, p0, p4, p1, p3

    The function returns a pair:

    trainingSequences:    A list containing numRepetitions instances of the
                          above sequences
    testSequence:         Clean test sequences with no noise on the right half

    """

    numPatterns = 5
    numCols = 2 * numPatterns * numOnes
    halfCols = numPatterns * numOnes
    numNoiseBits = numOnes
    p = self._getSimplePatterns(numOnes, numPatterns)

    # Indices of the patterns in the underlying sequences
    numSequences = 3
    indices = [
      [0, 1, 2, 3, 4],
      [4, 3, 2, 1, 0],
      [2, 0, 4, 1, 3],
    ]

    # Create the noisy training sequence
    trainingSequences = []
    for i in xrange(numRepetitions*numSequences):
      sequence = []
      for j in xrange(numPatterns):

        # Make left half
        v = numpy.zeros(numCols, dtype='float32')
        v[0:halfCols] = p[indices[i % numSequences][j]]

        # Select numOnes noise bits
        noiseIndices = (self._rgen.permutation(halfCols)
                        + halfCols)[0:numNoiseBits]
        v[noiseIndices] = 1
        sequence.append(v)
      trainingSequences.append(sequence)

    # Create the clean test sequences
    testSequences = []
    for i in xrange(numSequences):
      sequence = []
      for j in xrange(numPatterns):
        # Make only left half
        v = numpy.zeros(numCols, dtype='float32')
        v[0:halfCols] = p[indices[i % numSequences][j]]
        sequence.append(v)
      testSequences.append(sequence)

    if g_options.verbosity > 1:
      print "\nTraining sequences"
      self.printAllTrainingSequences(trainingSequences)
      print "\nTest sequences"
      self.printAllTrainingSequences(testSequences)

    return (trainingSequences, testSequences)


  def _testSegmentLearningSequence(self, tms,
                                   trainingSequences,
                                   testSequences,
                                   doResets = True):

    """Train the given TM once on the entire training set. on the Test a single
    set of sequences once and check that individual predictions reflect the true
    relative frequencies. Return a success code. Success code is 1 for pass, 0
    for fail."""

    # If no test sequence is specified, use the first training sequence
    if testSequences == None:
      testSequences = trainingSequences

    cppTM, pyTM = tms[0], tms[1]

    if cppTM is not None:
      assert fdrutils.tmDiff2(cppTM, pyTM, g_options.verbosity) == True

    #--------------------------------------------------------------------------
    # Learn
    if g_options.verbosity > 0:
      print "============= Training ================="
      print "TM parameters:"
      print "CPP"
      if cppTM is not None:
        print cppTM.printParameters()
      print "\nPY"
      print pyTM.printParameters()

    for sequenceNum, trainingSequence in enumerate(trainingSequences):

      if g_options.verbosity > 1:
        print "============= New sequence ================="

      if doResets:
        if cppTM is not None:
          cppTM.reset()
        pyTM.reset()

      for t, x in enumerate(trainingSequence):

        if g_options.verbosity > 1:
          print "Time step", t, "sequence number", sequenceNum
          print "Input: ", pyTM.printInput(x)
          print "NNZ:", x.nonzero()

        x = numpy.array(x).astype('float32')
        if cppTM is not None:
          cppTM.learn(x)
        pyTM.learn(x)

        if cppTM is not None:
          assert fdrutils.tmDiff2(cppTM, pyTM, g_options.verbosity,
                                  relaxSegmentTests = False) == True

        if g_options.verbosity > 2:
          if cppTM is not None:
            print "CPP"
            cppTM.printStates(printPrevious = (g_options.verbosity > 4))
          print "\nPY"
          pyTM.printStates(printPrevious = (g_options.verbosity > 4))
          print

      if g_options.verbosity > 4:
        print "Sequence finished. Complete state after sequence"
        if cppTM is not None:
          print "CPP"
          cppTM.printCells()
        print "\nPY"
        pyTM.printCells()
        print

    if g_options.verbosity > 2:
      print "Calling trim segments"

    if cppTM is not None:
      nSegsRemovedCPP, nSynsRemovedCPP = cppTM.trimSegments()
    nSegsRemoved, nSynsRemoved = pyTM.trimSegments()
    if cppTM is not None:
      assert nSegsRemovedCPP == nSegsRemoved
      assert nSynsRemovedCPP == nSynsRemoved

    if cppTM is not None:
      assert fdrutils.tmDiff2(cppTM, pyTM, g_options.verbosity) == True

    print "Training completed. Stats:"
    info = pyTM.getSegmentInfo()
    print "  nSegments:", info[0]
    print "  nSynapses:", info[1]
    if g_options.verbosity > 3:
      print "Complete state:"
      if cppTM is not None:
        print "CPP"
        cppTM.printCells()
      print "\nPY"
      pyTM.printCells()

    #---------------------------------------------------------------------------
    # Infer
    if g_options.verbosity > 1:
      print "============= Inference ================="

    if cppTM is not None:
      cppTM.collectStats = True
    pyTM.collectStats = True

    nPredictions = 0
    cppNumCorrect, pyNumCorrect = 0, 0

    for sequenceNum, testSequence in enumerate(testSequences):

      if g_options.verbosity > 1:
        print "============= New sequence ================="

      slen = len(testSequence)

      if doResets:
        if cppTM is not None:
          cppTM.reset()
        pyTM.reset()

      for t, x in enumerate(testSequence):

        if g_options.verbosity >= 2:
          print "Time step", t, '\nInput:'
          pyTM.printInput(x)

        if cppTM is not None:
          cppTM.infer(x)
        pyTM.infer(x)

        if cppTM is not None:
          assert fdrutils.tmDiff2(cppTM, pyTM, g_options.verbosity) == True

        if g_options.verbosity > 2:
          if cppTM is not None:
            print "CPP"
            cppTM.printStates(printPrevious = (g_options.verbosity > 4),
                           printLearnState = False)
          print "\nPY"
          pyTM.printStates(printPrevious = (g_options.verbosity > 4),
                         printLearnState = False)

        if cppTM is not None:
          cppScores = cppTM.getStats()
        pyScores = pyTM.getStats()

        if g_options.verbosity >= 2:
          if cppTM is not None:
            print "CPP"
            print cppScores
          print "\nPY"
          print pyScores

        if t < slen-1 and t > pyTM.burnIn:
          nPredictions += 1
          if cppTM is not None:
            if cppScores['curPredictionScore2'] > 0.3:
              cppNumCorrect += 1
          if pyScores['curPredictionScore2'] > 0.3:
            pyNumCorrect += 1

    # Check that every inference was correct, excluding the very last inference
    if cppTM is not None:
      cppScores = cppTM.getStats()
    pyScores = pyTM.getStats()

    passTest = False
    if cppTM is not None:
      if cppNumCorrect == nPredictions and pyNumCorrect == nPredictions:
        passTest = True
    else:
      if pyNumCorrect == nPredictions:
        passTest = True

    if not passTest:
      print "CPP correct predictions:", cppNumCorrect
      print "PY correct predictions:", pyNumCorrect
      print "Total predictions:", nPredictions

    return passTest


  def _testSL1(self, numOnes = 10, numRepetitions = 6, fixedResources = False,
            checkSynapseConsistency = True):
    """Test segment learning"""

    if fixedResources:
      testName = "TestSL1_FS"
    else:
      testName = "TestSL1"

    print "\nRunning %s..." % testName

    trainingSet, testSet = self._buildSegmentLearningTrainingSet(numOnes,
                                                                 numRepetitions)
    numCols = len(trainingSet[0][0])

    tms = self._createTMs(numCols = numCols, fixedResources=fixedResources,
                          checkSynapseConsistency = checkSynapseConsistency)

    testResult = self._testSegmentLearningSequence(tms, trainingSet, testSet)

    if testResult:
      print "%s PASS" % testName
      return 1
    else:
      print "%s FAILED" % testName
      return 0


  def _testSL2(self, numOnes = 10, numRepetitions = 10, fixedResources = False,
              checkSynapseConsistency = True):
    """Test segment learning"""

    if fixedResources:
      testName = "TestSL2_FS"
    else:
      testName = "TestSL2"

    print "\nRunning %s..." % testName

    trainingSet, testSet = self._buildSL2TrainingSet(numOnes, numRepetitions)
    numCols = len(trainingSet[0][0])

    tms = self._createTMs(numCols = numCols, fixedResources=fixedResources,
                          checkSynapseConsistency = checkSynapseConsistency)

    testResult = self._testSegmentLearningSequence(tms, trainingSet, testSet)

    if testResult:
      print "%s PASS" % testName
      return 1
    else:
      print "%s FAILED" % testName
      return 0



class TMSegmentLearningTests(ExperimentTestBaseClass):
  """Our high level tests"""


  def test_SL1NoFixedResources(self):
    """Test segment learning without fixed resources"""

    self._testSL1(fixedResources=False,
                  checkSynapseConsistency=g_options.long)


  def test_SL1WithFixedResources(self):
    """Test segment learning with fixed resources"""

    if not g_options.long:
      print "Test %s only enabled with the --long option" % \
                                (self._testMethodName)
      return

    self._testSL1(fixedResources=True,
                  checkSynapseConsistency=g_options.long)


  def test_SL2NoFixedResources(self):
    """Test segment learning without fixed resources"""

    if not g_options.long:
      print "Test %s only enabled with the --long option" % \
                                (self._testMethodName)
      return

    self._testSL2(fixedResources=False,
                  checkSynapseConsistency=g_options.long)


  def test_SL2WithFixedResources(self):
    """Test segment learning with fixed resources"""

    if not g_options.long:
      print "Test %s only enabled with the --long option" % \
                                (self._testMethodName)
      return

    self._testSL2(fixedResources=True,
                  checkSynapseConsistency=g_options.long)



if __name__ == "__main__":

  # Process command line arguments
  parser = testcasebase.TestOptionParser()

  # Make the default value of the random seed 35
  parser.remove_option('--seed')
  parser.add_option('--seed', default=35, type='int',
                    help='Seed to use for random number generators '
                       '[default: %default].')

  g_options, _ = parser.parse_args()

  # Run the tests
  unittest.main(verbosity=g_options.verbosity)
