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

SL1) Train the TP repeatedly using a single sequence plus noise. The sequence
can be relatively short, say 5 patterns. Add random noise each time a pattern is
presented. The noise should be different for each presentation and can be equal
to the number of on bits in the pattern.

Simplified patterns will be used, where each pattern consists of consecutive
bits and no two patterns share columns. The patterns that belong to the sequence
will be in the left half of the input vector. The noise bits will be in the
right half of the input vector.

After several iterations of each sequence, the TP should should achieve perfect
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

from nupic.research.TP import TP
from nupic.research.TP10X2 import TP10X2
from nupic.research import fdrutilities as fdrutils
from nupic.support.unittesthelpers import testcasebase


g_testCPPTP = True



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


  def _setVerbosity(self, verbosity, tp, tpPy):
    """Set verbosity level on the TP"""
    tp.cells4.setVerbosity(verbosity)
    tp.verbosity = verbosity
    tpPy.verbosity = verbosity


  def _createTPs(self, numCols, fixedResources=False,
                checkSynapseConsistency = True):
    """Create an instance of the appropriate temporal pooler. We isolate
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


    if g_testCPPTP:
      if g_options.verbosity > 1:
        print "Creating TP10X2 instance"

      cppTP = TP10X2(numberOfCols = numCols, cellsPerColumn = 4,
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
      # Ensure we are copying over learning states for TPDiff
      cppTP.retrieveLearningStates = True

    else:
      cppTP = None

    if g_options.verbosity > 1:
      print "Creating PY TP instance"
    pyTP = TP(numberOfCols = numCols, cellsPerColumn = 4,
               initialPerm = initialPerm, connectedPerm = connectedPerm,
               minThreshold = minThreshold, newSynapseCount = newSynapseCount,
               permanenceInc = permanenceInc, permanenceDec = permanenceDec,
               activationThreshold = activationThreshold,
               globalDecay = globalDecay, maxAge=maxAge, burnIn = 1,
               seed=g_options.seed, verbosity=g_options.verbosity,
               pamLength = 1000,
               maxSegmentsPerCell = maxSegmentsPerCell,
               maxSynapsesPerSegment = maxSynapsesPerSegment,
               )

    return cppTP, pyTP


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
    for _ in xrange(numRepetitions):
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
      self._printAllTrainingSequences(trainingSequences)
      print "\nTest sequence"
      self._printAllTrainingSequences([testSequence])

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
      self._printAllTrainingSequences(trainingSequences)
      print "\nTest sequences"
      self._printAllTrainingSequences(testSequences)

    return (trainingSequences, testSequences)


  def _testSegmentLearningSequence(self, tps,
                                  trainingSequences,
                                  testSequences,
                                  doResets = True):

    """Train the given TP once on the entire training set. on the Test a single
    set of sequences once and check that individual predictions reflect the true
    relative frequencies. Return a success code. Success code is 1 for pass, 0
    for fail."""

    # If no test sequence is specified, use the first training sequence
    if testSequences == None:
      testSequences = trainingSequences

    cppTP, pyTP = tps[0], tps[1]

    if cppTP is not None:
      assert fdrutils.tpDiff2(cppTP, pyTP, g_options.verbosity) == True

    #--------------------------------------------------------------------------
    # Learn
    if g_options.verbosity > 0:
      print "============= Training ================="
      print "TP parameters:"
      print "CPP"
      if cppTP is not None:
        print cppTP.printParameters()
      print "\nPY"
      print pyTP.printParameters()

    for sequenceNum, trainingSequence in enumerate(trainingSequences):

      if g_options.verbosity > 1:
        print "============= New sequence ================="

      if doResets:
        if cppTP is not None:
          cppTP.reset()
        pyTP.reset()

      for t, x in enumerate(trainingSequence):

        if g_options.verbosity > 1:
          print "Time step", t, "sequence number", sequenceNum
          print "Input: ", pyTP.printInput(x)
          print "NNZ:", x.nonzero()

        x = numpy.array(x).astype('float32')
        if cppTP is not None:
          cppTP.learn(x)
        pyTP.learn(x)

        if cppTP is not None:
          assert fdrutils.tpDiff2(cppTP, pyTP, g_options.verbosity,
                                  relaxSegmentTests = False) == True

        if g_options.verbosity > 2:
          if cppTP is not None:
            print "CPP"
            cppTP.printStates(printPrevious = (g_options.verbosity > 4))
          print "\nPY"
          pyTP.printStates(printPrevious = (g_options.verbosity > 4))
          print

      if g_options.verbosity > 4:
        print "Sequence finished. Complete state after sequence"
        if cppTP is not None:
          print "CPP"
          cppTP.printCells()
        print "\nPY"
        pyTP.printCells()
        print

    if g_options.verbosity > 2:
      print "Calling trim segments"

    if cppTP is not None:
      nSegsRemovedCPP, nSynsRemovedCPP = cppTP.trimSegments()
    nSegsRemoved, nSynsRemoved = pyTP.trimSegments()
    if cppTP is not None:
      assert nSegsRemovedCPP == nSegsRemoved
      assert nSynsRemovedCPP == nSynsRemoved

    if cppTP is not None:
      assert fdrutils.tpDiff2(cppTP, pyTP, g_options.verbosity) == True

    print "Training completed. Stats:"
    info = pyTP.getSegmentInfo()
    print "  nSegments:", info[0]
    print "  nSynapses:", info[1]
    if g_options.verbosity > 3:
      print "Complete state:"
      if cppTP is not None:
        print "CPP"
        cppTP.printCells()
      print "\nPY"
      pyTP.printCells()

    #---------------------------------------------------------------------------
    # Infer
    if g_options.verbosity > 1:
      print "============= Inference ================="

    if cppTP is not None:
      cppTP.collectStats = True
    pyTP.collectStats = True

    nPredictions = 0
    cppNumCorrect, pyNumCorrect = 0, 0

    for sequenceNum, testSequence in enumerate(testSequences):

      if g_options.verbosity > 1:
        print "============= New sequence ================="

      slen = len(testSequence)

      if doResets:
        if cppTP is not None:
          cppTP.reset()
        pyTP.reset()

      for t, x in enumerate(testSequence):

        if g_options.verbosity >= 2:
          print "Time step", t, '\nInput:'
          pyTP.printInput(x)

        if cppTP is not None:
          cppTP.infer(x)
        pyTP.infer(x)

        if cppTP is not None:
          assert fdrutils.tpDiff2(cppTP, pyTP, g_options.verbosity) == True

        if g_options.verbosity > 2:
          if cppTP is not None:
            print "CPP"
            cppTP.printStates(printPrevious = (g_options.verbosity > 4),
                           printLearnState = False)
          print "\nPY"
          pyTP.printStates(printPrevious = (g_options.verbosity > 4),
                         printLearnState = False)

        if cppTP is not None:
          cppScores = cppTP.getStats()
        pyScores = pyTP.getStats()

        if g_options.verbosity >= 2:
          if cppTP is not None:
            print "CPP"
            print cppScores
          print "\nPY"
          print pyScores

        if t < slen-1 and t > pyTP.burnIn:
          nPredictions += 1
          if cppTP is not None:
            if cppScores['curPredictionScore2'] > 0.3:
              cppNumCorrect += 1
          if pyScores['curPredictionScore2'] > 0.3:
            pyNumCorrect += 1

    # Check that every inference was correct, excluding the very last inference
    if cppTP is not None:
      cppScores = cppTP.getStats()
    pyScores = pyTP.getStats()

    passTest = False
    if cppTP is not None:
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

    tps = self._createTPs(numCols = numCols, fixedResources=fixedResources,
                    checkSynapseConsistency = checkSynapseConsistency)

    testResult = self._testSegmentLearningSequence(tps, trainingSet, testSet)

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

    tps = self._createTPs(numCols = numCols, fixedResources=fixedResources,
                    checkSynapseConsistency = checkSynapseConsistency)

    testResult = self._testSegmentLearningSequence(tps, trainingSet, testSet)

    if testResult:
      print "%s PASS" % testName
      return 1
    else:
      print "%s FAILED" % testName
      return 0



class TPSegmentLearningTests(ExperimentTestBaseClass):
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
