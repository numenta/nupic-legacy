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

from nupic.research import fdrutilities as fdrutils
from nupic.research.TP import TP
from nupic.research.TP10X2 import TP10X2

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


def _createTps(numCols):
  """Create two instances of temporal poolers (TP.py and TP10X2.py) with
  identical parameter settings."""

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

  cppTp = TP10X2(numberOfCols=numCols, cellsPerColumn=cellsPerColumn,
                  initialPerm=initialPerm, connectedPerm=connectedPerm,
                  minThreshold=minThreshold, newSynapseCount=newSynapseCount,
                  permanenceInc=permanenceInc, permanenceDec=permanenceDec,
                  activationThreshold=activationThreshold,
                  globalDecay=globalDecay, burnIn=1,
                  seed=_SEED, verbosity=VERBOSITY,
                  checkSynapseConsistency=True,
                  pamLength=1000)

  # Ensure we are copying over learning states for TPDiff
  cppTp.retrieveLearningStates = True

  pyTp = TP(numberOfCols=numCols, cellsPerColumn=cellsPerColumn,
             initialPerm=initialPerm, connectedPerm=connectedPerm,
             minThreshold=minThreshold, newSynapseCount=newSynapseCount,
             permanenceInc=permanenceInc, permanenceDec=permanenceDec,
             activationThreshold=activationThreshold,
             globalDecay=globalDecay, burnIn=1,
             seed=_SEED, verbosity=VERBOSITY,
             pamLength=1000)

  return cppTp, pyTp


class TPConstantTest(unittest.TestCase):


  def setUp(self):
    self.cppTp, self.pyTp = _createTps(100)


  def _basicTest(self, tp=None):
    """Test creation, pickling, and basic run of learning and inference."""

    trainingSet = _getSimplePatterns(10, 10)

    # Learn on several constant sequences, with a reset in between
    for _ in range(2):
      for seq in trainingSet[0:5]:
        for _ in range(10):
          tp.learn(seq)
        tp.reset()

    print "Learning completed"

    # Infer
    print "Running inference"

    tp.collectStats = True
    for seq in trainingSet[0:5]:
      tp.reset()
      tp.resetStats()
      for _ in range(10):
        tp.infer(seq)
        if VERBOSITY > 1 :
          print
          _printOneTrainingVector(seq)
          tp.printStates(False, False)
          print
          print
      if VERBOSITY > 1:
        print tp.getStats()

      # Ensure our predictions are accurate for each sequence
      self.assertGreater(tp.getStats()['predictionScoreAvg2'], 0.8)
      print ("tp.getStats()['predictionScoreAvg2'] = ",
             tp.getStats()['predictionScoreAvg2'])

    print "TPConstant basicTest ok"


  def testCppTpBasic(self):
    self._basicTest(self.cppTp)


  def testPyTpBasic(self):
    self._basicTest(self.pyTp)


  def testIdenticalTps(self):
    self.assertTrue(fdrutils.tpDiff2(self.cppTp, self.pyTp))



if __name__=="__main__":
  unittest.main()
