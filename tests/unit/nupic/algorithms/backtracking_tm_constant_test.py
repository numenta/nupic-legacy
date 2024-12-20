# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""
This file tests that we can learn and predict the particularly vexing case of a
single constant signal!
"""

import numpy as np
import unittest2 as unittest

from nupic.algorithms import fdrutilities as fdrutils
from nupic.algorithms.backtracking_tm import BacktrackingTM
from nupic.algorithms.backtracking_tm_cpp import BacktrackingTMCPP

_SEED = 42
VERBOSITY = 1
np.random.seed(_SEED)



def _printOneTrainingVector(x):
  "Print a single vector succinctly."
  print ''.join('1' if k != 0 else '.' for k in x)


def _getSimplePatterns(numOnes, numPatterns):
  """Very simple patterns. Each pattern has numOnes consecutive
  bits on. There are numPatterns*numOnes bits in the vector. These patterns
  are used as elements of sequences when building up a training set."""

  numCols = numOnes * numPatterns
  p = []
  for i in xrange(numPatterns):
    x = np.zeros(numCols, dtype='float32')
    x[i*numOnes:(i + 1)*numOnes] = 1
    p.append(x)

  return p


def _createTms(numCols):
  """Create two instances of temporal poolers (backtracking_tm.py
  and backtracking_tm_cpp.py) with identical parameter settings."""

  # Keep these fixed:
  minThreshold = 4
  activationThreshold = 5
  newSynapseCount = 7
  initialPerm = 0.3
  connectedPerm = 0.5
  permanenceInc = 0.1
  permanenceDec = 0.05
  globalDecay = 0
  cellsPerColumn = 1

  cppTm = BacktrackingTMCPP(numberOfCols=numCols,
                            cellsPerColumn=cellsPerColumn,
                            initialPerm=initialPerm,
                            connectedPerm=connectedPerm,
                            minThreshold=minThreshold,
                            newSynapseCount=newSynapseCount,
                            permanenceInc=permanenceInc,
                            permanenceDec=permanenceDec,
                            activationThreshold=activationThreshold,
                            globalDecay=globalDecay, burnIn=1,
                            seed=_SEED, verbosity=VERBOSITY,
                            checkSynapseConsistency=True,
                            pamLength=1000)

  # Ensure we are copying over learning states for TMDiff
  cppTm.retrieveLearningStates = True

  pyTm = BacktrackingTM(numberOfCols=numCols,
                        cellsPerColumn=cellsPerColumn,
                        initialPerm=initialPerm,
                        connectedPerm=connectedPerm,
                        minThreshold=minThreshold,
                        newSynapseCount=newSynapseCount,
                        permanenceInc=permanenceInc,
                        permanenceDec=permanenceDec,
                        activationThreshold=activationThreshold,
                        globalDecay=globalDecay, burnIn=1,
                        seed=_SEED, verbosity=VERBOSITY,
                        pamLength=1000)

  return cppTm, pyTm


class TMConstantTest(unittest.TestCase):


  def setUp(self):
    self.cppTm, self.pyTm = _createTms(100)


  def _basicTest(self, tm=None):
    """Test creation, pickling, and basic run of learning and inference."""

    trainingSet = _getSimplePatterns(10, 10)

    # Learn on several constant sequences, with a reset in between
    for _ in range(2):
      for seq in trainingSet[0:5]:
        for _ in range(10):
          tm.learn(seq)
        tm.reset()

    print "Learning completed"

    # Infer
    print "Running inference"

    tm.collectStats = True
    for seq in trainingSet[0:5]:
      tm.reset()
      tm.resetStats()
      for _ in range(10):
        tm.infer(seq)
        if VERBOSITY > 1 :
          print
          _printOneTrainingVector(seq)
          tm.printStates(False, False)
          print
          print
      if VERBOSITY > 1:
        print tm.getStats()

      # Ensure our predictions are accurate for each sequence
      self.assertGreater(tm.getStats()['predictionScoreAvg2'], 0.8)
      print ("tm.getStats()['predictionScoreAvg2'] = ",
             tm.getStats()['predictionScoreAvg2'])

    print "TMConstant basicTest ok"


  def testCppTmBasic(self):
    self._basicTest(self.cppTm)


  def testPyTmBasic(self):
    self._basicTest(self.pyTm)


  def testIdenticalTms(self):
    self.assertTrue(fdrutils.tmDiff2(self.cppTm, self.pyTm))



if __name__=="__main__":
  unittest.main()
