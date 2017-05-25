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
Sequence Likelihood Tests
=========================

LI1) Present three sequences

Seq#1: A-B-C-D-E
Seq#2: A-B-C-D-F
Seq#3: A-B-C-D-G

with the relative frequencies, such as [0.1,0.7,0.2]

Test: after presenting A-B-C-D, prediction scores should reflect the transition
probabilities for E, F and G, i.e. Run the test for several different
probability combinations.

LI2) Given a TM trained with LI1, compute the prediction score across a
list of sequences.

LI3) Given the following sequence and a one cell per column TM:

Seq1: a-b-b-c-d

There should be four segments a-b
"""

import numpy
import unittest2 as unittest

from nupic.algorithms.backtracking_tm import BacktrackingTM
from nupic.algorithms.backtracking_tm_cpp import BacktrackingTMCPP
from nupic.support.unittesthelpers import testcasebase

SEED = 42
VERBOSITY = 1
LONG = True

_RGEN = numpy.random.RandomState(SEED)


def _getSimplePatterns(numOnes, numPatterns):
  """Very simple patterns. Each pattern has numOnes consecutive
  bits on. There are numPatterns*numOnes bits in the vector."""

  numCols = numOnes * numPatterns
  p = []
  for i in xrange(numPatterns):
    x = numpy.zeros(numCols, dtype='float32')
    x[i*numOnes:(i+1)*numOnes] = 1
    p.append(x)

  return p

def _buildLikelihoodTrainingSet(numOnes=5, relativeFrequencies=None):

  """Two very simple high order sequences for debugging. Each pattern in the
  sequence has a series of 1's in a specific set of columns."""

  numPatterns = 7
  p = _getSimplePatterns(numOnes, numPatterns)
  s1 = [p[0], p[1], p[2], p[3], p[4]]
  s2 = [p[0], p[1], p[2], p[3], p[5]]
  s3 = [p[0], p[1], p[2], p[3], p[6]]
  trainingSequences = [s1, s2, s3]

  allPatterns = p

  return (trainingSequences, relativeFrequencies, allPatterns)

def _createTMs(numCols, cellsPerColumn=4, checkSynapseConsistency=True):
  """Create TM and BacktrackingTMCPP instances with identical parameters. """

  # Keep these fixed for both TM's:
  minThreshold = 4
  activationThreshold = 4
  newSynapseCount = 5
  initialPerm = 0.6
  connectedPerm = 0.5
  permanenceInc = 0.1
  permanenceDec = 0.001
  globalDecay = 0.0

  if VERBOSITY > 1:
    print "Creating BacktrackingTMCPP instance"

  cppTm = BacktrackingTMCPP(numberOfCols=numCols, cellsPerColumn=cellsPerColumn,
                            initialPerm=initialPerm, connectedPerm=connectedPerm,
                            minThreshold=minThreshold, newSynapseCount=newSynapseCount,
                            permanenceInc=permanenceInc, permanenceDec=permanenceDec,
                            activationThreshold=activationThreshold,
                            globalDecay=globalDecay, burnIn=1,
                            seed=SEED, verbosity=VERBOSITY,
                            checkSynapseConsistency=checkSynapseConsistency,
                            pamLength=1000)

  if VERBOSITY > 1:
    print "Creating PY TM instance"

  pyTm = BacktrackingTM(numberOfCols=numCols, cellsPerColumn=cellsPerColumn,
                        initialPerm=initialPerm, connectedPerm=connectedPerm,
                        minThreshold=minThreshold, newSynapseCount=newSynapseCount,
                        permanenceInc=permanenceInc, permanenceDec=permanenceDec,
                        activationThreshold=activationThreshold,
                        globalDecay=globalDecay, burnIn=1,
                        seed=SEED, verbosity=VERBOSITY,
                        pamLength=1000)

  return cppTm, pyTm


def _computeTMMetric(tm=None, sequences=None, useResets=True, verbosity=1):
  """Given a trained TM and a list of sequences, compute the temporal memory
  performance metric on those sequences.

  Parameters:
  ===========
  tm:               A trained temporal memory.
  sequences:        A list of sequences. Each sequence is a list of numpy
                    vectors.
  useResets:        If True, the TM's reset method will be called before the
                    the start of each new sequence.
  verbosity:        An integer controlling the level of printouts. The higher
                    the number the more debug printouts.

  Return value:
  ============
  The following pair is returned:  (score, numPredictions)

  score:            The average prediction score per pattern.
  numPredictions:   The total number of predictions that were made.

  """
  datasetScore = 0
  numPredictions = 0

  tm.resetStats()

  for seqIdx, seq in enumerate(sequences):
    # Feed in a reset
    if useResets:
      tm.reset()

    seq = numpy.array(seq, dtype='uint32')
    if verbosity > 2:
      print "--------------------------------------------------------"
    for i, inputPattern in enumerate(seq):
      if verbosity > 2:
        print "sequence %d, element %d," % (seqIdx, i),
        print "pattern", inputPattern


      # Feed this input to the TM and get the stats
      y = tm.infer(inputPattern)

      if verbosity > 2:
        stats = tm.getStats()
        if stats['curPredictionScore'] > 0:
          print "   patternConfidence=", stats['curPredictionScore2']


      # Print some diagnostics for debugging
      if verbosity > 3:
        print "\n\n"
        predOut = numpy.sum(tm.predictedState['t'], axis=1)
        actOut  = numpy.sum(tm.activeState['t'], axis=1)
        outout  = numpy.sum(y.reshape(tm.activeState['t'].shape), axis=1)
        print "Prediction non-zeros: ", predOut.nonzero()
        print "Activestate non-zero: ", actOut.nonzero()
        print "input non-zeros:      ", inputPattern.nonzero()
        print "Output non-zeros:     ", outout.nonzero()

  # Print and return final stats
  stats = tm.getStats()
  datasetScore = stats['predictionScoreAvg2']
  numPredictions = stats['nPredictions']
  print "Final results: datasetScore=", datasetScore,
  print "numPredictions=", numPredictions

  return datasetScore, numPredictions


def _createDataset(numSequences, originalSequences, relativeFrequencies):
  """Given a set of sequences, create a dataset consisting of numSequences
  sequences. The i'th pattern in this dataset is chosen from originalSequences
  according to the relative frequencies specified in relativeFrequencies."""

  dataSet = []
  trainingCummulativeFrequencies = numpy.cumsum(relativeFrequencies)
  for _ in xrange(numSequences):
    # Pick a training sequence to present, based on the given training
    # frequencies.
    whichSequence = numpy.searchsorted(trainingCummulativeFrequencies,
                                       _RGEN.random_sample())
    dataSet.append(originalSequences[whichSequence])

  return dataSet


class TMLikelihoodTest(testcasebase.TestCaseBase):

  def _testSequence(self,
                    trainingSet,
                    nSequencePresentations=1,
                    tm=None,
                    testSequences=None,
                    doResets=True,
                    relativeFrequencies=None):
    """Test a single set of sequences once and check that individual
    predictions reflect the true relative frequencies. Return a success code
    as well as the trained TM. Success code is 1 for pass, 0 for fail.


    The trainingSet is a set of 3 sequences that share the same first 4
    elements but differ in the 5th element. After feeding in the first 4 elements,
    we want to correctly compute the confidences for the 5th element based on
    the frequency with which each sequence was presented during learning.

    For example:

    trainingSequences[0]: (10% probable)
    pat A: (array([0, 1, 2, 3, 4]),)
    pat B: (array([5, 6, 7, 8, 9]),)
    pat C: (array([10, 11, 12, 13, 14]),)
    pat D: (array([15, 16, 17, 18, 19]),)
    pat E: (array([20, 21, 22, 23, 24]),)

    trainingSequences[1]: (20% probable)
    pat A: (array([0, 1, 2, 3, 4]),)
    pat B: (array([5, 6, 7, 8, 9]),)
    pat C: (array([10, 11, 12, 13, 14]),)
    pat D: (array([15, 16, 17, 18, 19]),)
    pat F: (array([25, 26, 27, 28, 29]),)

    trainingSequences[2]: (70% probable)
    pat A: (array([0, 1, 2, 3, 4]),)
    pat B: (array([5, 6, 7, 8, 9]),)
    pat C: (array([10, 11, 12, 13, 14]),)
    pat D: (array([15, 16, 17, 18, 19]),)
    pat G: (array([30, 31, 32, 33, 34]),)

    allTrainingPatterns:
    pat A: (array([0, 1, 2, 3, 4]),)
    pat B: (array([5, 6, 7, 8, 9]),)
    pat C: (array([10, 11, 12, 13, 14]),)
    pat D: (array([15, 16, 17, 18, 19]),)
    pat E: (array([20, 21, 22, 23, 24]),)
    pat F: (array([25, 26, 27, 28, 29]),)
    pat G: (array([30, 31, 32, 33, 34]),)

    """
    trainingSequences = trainingSet[0]
    trainingFrequencies = trainingSet[1]
    allTrainingPatterns = trainingSet[2]

    trainingCummulativeFrequencies = numpy.cumsum(trainingFrequencies)
    if testSequences == None:
      testSequences = trainingSequences

    # Learn
    if VERBOSITY > 1:
      print "============= Learning ================="

    for r in xrange(nSequencePresentations):

      # Pick a training sequence to present, based on the given training
      # frequencies.
      whichSequence = numpy.searchsorted(trainingCummulativeFrequencies,
                                         _RGEN.random_sample())
      trainingSequence = trainingSequences[whichSequence]

      if VERBOSITY > 2:
        print "=========Presentation #%d Sequence #%d==============" % \
                                              (r, whichSequence)
      if doResets:
        tm.reset()
      for t, x in enumerate(trainingSequence):
        if VERBOSITY > 3:
          print "Time step", t
          print "Input: ", tm.printInput(x)
        tm.learn(x)
        if VERBOSITY > 4:
          tm.printStates(printPrevious=(VERBOSITY > 4))
          print
      if VERBOSITY > 4:
        print "Sequence finished. Complete state after sequence"
        tm.printCells()
        print

    tm.finishLearning()
    if VERBOSITY > 2:
      print "Training completed. Complete state:"
      tm.printCells()
      print
      print "TM parameters:"
      print tm.printParameters()

    # Infer
    if VERBOSITY > 1:
      print "============= Inference ================="

    testSequence = testSequences[0]
    slen = len(testSequence)
    tm.collectStats = True
    tm.resetStats()
    if doResets:
      tm.reset()
    for t, x in enumerate(testSequence):
      if VERBOSITY > 2:
        print "Time step", t, '\nInput:', tm.printInput(x)
      tm.infer(x)
      if VERBOSITY > 3:
        tm.printStates(printPrevious=(VERBOSITY > 4), printLearnState=False)
        print

      # We will exit with the confidence score for the last element
      if t == slen-2:
        tmNonZeros = [pattern.nonzero()[0] for pattern in allTrainingPatterns]
        predictionScore2 = tm._checkPrediction(tmNonZeros)[2]

    if VERBOSITY > 0:
      print "predictionScore:", predictionScore2

    # The following test tests that the prediction scores for each pattern
    # are within 10% of the its relative frequency.  Here we check only
    # the Positive Prediction Score
    patternConfidenceScores = numpy.array([x[1] for x in predictionScore2])
    # Normalize so that the sum is 1.0. This makes us independent of any
    #  potential scaling differences in the column confidence calculations of
    #  various TM implementations.
    patternConfidenceScores /= patternConfidenceScores.sum()

    msg = ('Prediction failed with predictionScore: %s. Expected %s but got %s.'
           % (str(predictionScore2), str(relativeFrequencies),
              str(patternConfidenceScores[4:])))
    self.assertLess(abs(patternConfidenceScores[4]-relativeFrequencies[0]), 0.1,
                    msg=msg)
    self.assertLess(abs(patternConfidenceScores[5]-relativeFrequencies[1]), 0.1,
                    msg=msg)
    self.assertLess(abs(patternConfidenceScores[6]-relativeFrequencies[2]), 0.1,
                    msg=msg)

  def _likelihoodTest1(self, numOnes=5, relativeFrequencies=None,
                       checkSynapseConsistency=True):

    print "Sequence Likelihood test 1 with relativeFrequencies=",
    print relativeFrequencies

    trainingSet = _buildLikelihoodTrainingSet(numOnes, relativeFrequencies)
    cppTm, pyTm = _createTMs(numCols=trainingSet[0][0][0].size,
                             checkSynapseConsistency=checkSynapseConsistency)

    # Test both TM's. Currently the CPP TM has faster confidence estimation
    self._testSequence(trainingSet, nSequencePresentations=200, tm=cppTm,
                       relativeFrequencies=relativeFrequencies)

    self._testSequence(trainingSet, nSequencePresentations=500, tm=pyTm,
                       relativeFrequencies=relativeFrequencies)

  def _likelihoodTest2(self, numOnes=5, relativeFrequencies=None,
                       checkSynapseConsistency=True):
    print "Sequence Likelihood test 2 with relativeFrequencies=",
    print relativeFrequencies

    trainingSet = _buildLikelihoodTrainingSet(numOnes, relativeFrequencies)

    cppTm, pyTm = _createTMs(numCols=trainingSet[0][0][0].size,
                             checkSynapseConsistency=checkSynapseConsistency)

    # Test both TM's
    for tm in [cppTm, pyTm]:
      self._testSequence(trainingSet, nSequencePresentations=500, tm=tm,
                         relativeFrequencies=relativeFrequencies)

      # Create a dataset with the same relative frequencies for testing the
      # metric.
      testDataSet = _createDataset(500, trainingSet[0], relativeFrequencies)
      tm.collectStats = True
      score, _ = _computeTMMetric(tm, testDataSet, verbosity=2)

      # Create a dataset with very different relative frequencies
      # This score should be lower than the one above.
      testDataSet = _createDataset(500, trainingSet[0],
                                   relativeFrequencies = [0.1, 0.1, 0.9])
      score2, _ = _computeTMMetric(tm, testDataSet, verbosity=2)

      self.assertLessEqual(score2, score)

  def testLikelihood1Short(self):
    self._likelihoodTest1(numOnes=5, relativeFrequencies=[0.1, 0.7, 0.2],
                          checkSynapseConsistency=LONG)

  def testLikelihood1Long(self):
    self._likelihoodTest1(numOnes=5, relativeFrequencies=[0.2, 0.5, 0.3])
    self._likelihoodTest1(numOnes=5, relativeFrequencies=[0.5, 0.5, 0.0])
    self._likelihoodTest1(numOnes=5, relativeFrequencies=[0.1, 0.5, 0.4])

  def testLikelihood2Short(self):
    self._likelihoodTest2(numOnes=5, relativeFrequencies=[0.1, 0.7, 0.2],
                          checkSynapseConsistency=LONG)

  def testLikelihood2Long(self):
    self._likelihoodTest2(numOnes=5, relativeFrequencies=[0.2, 0.5, 0.3])
    self._likelihoodTest2(numOnes=5, relativeFrequencies=[0.5, 0.5, 0.0])
    self._likelihoodTest2(numOnes=5, relativeFrequencies=[0.1, 0.5, 0.4])


if __name__ == "__main__":
  unittest.main()
