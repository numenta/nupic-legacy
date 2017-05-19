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
This file tests that we can learn and predict the particularly vexing case of a
single constant signal!
"""

import numpy as np
import unittest2 as unittest

from nupic.algorithms import fdrutilities as fdrutils
from nupic.algorithms.backtracking_tm import BacktrackingTM
from nupic.algorithms.backtracking_tm_cpp import BacktrackingTMCPP
from nupic.support.unittesthelpers.testcasebase import (TestCaseBase,
                                                        TestOptionParser)


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
                            seed=SEED, verbosity=VERBOSITY,
                            checkSynapseConsistency=True,
                            pamLength=1000)

  # Ensure we are copying over learning states for TPDiff
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
                        seed=SEED, verbosity=VERBOSITY,
                        pamLength=1000)

  return cppTm, pyTm

class TMConstantTest(TestCaseBase):

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

    print "TMConstantTest ok"

  def testCppTmBasic(self):
    self._basicTest(self.cppTm)

  def testPyTmBasic(self):
    self._basicTest(self.pyTm)

  def testIdenticalTms(self):
    self.assertTrue(fdrutils.tmDiff2(self.cppTm, self.pyTm))


if __name__=="__main__":
  parser = TestOptionParser()
  options, _ = parser.parse_args()
  SEED = options.seed
  VERBOSITY = options.verbosity

  np.random.seed(SEED)

  unittest.main()
