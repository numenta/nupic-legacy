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

import time
import numpy
import unittest2 as unittest

from nupic.support.unittesthelpers.algorithm_test_helpers \
     import CreateSP
from nupic.bindings.math import GetNTAReal

uintType = "uint32"

# set a single seed for running both implementations
SEED = int((time.time()%10000)*10)

def _computeOverlap(x, y):
  """
  Given two binary arrays, compute their overlap. The overlap is the number
  of bits where x[i] and y[i] are both 1
  """
  return ((x + y) == 2).sum()



def _areAllSDRsUnique(sdrDict):
  """Return True iff all the SDR's in the dict are unique."""
  for k1, v1 in sdrDict.iteritems():
    for k2, v2 in sdrDict.iteritems():
      # Return false if two different keys have identical SDR's
      if (k2 != k1) and ((v1 == v2).sum() == v1.size):
        return False
      
  return True



class SpatialPoolerBoostTest(unittest.TestCase):
  """
  Test boosting.
  
  The test is constructed as follows: we construct a set of 5 known inputs. Two
  of the input patterns have 50% overlap while all other combinations have 0%
  overlap. Each input pattern has 20 bits on to ensure reasonable overlap with
  almost all columns.

  SP parameters:  The SP is set to have 600 columns with 10% output sparsity.
  This ensures that the 5 inputs cannot use up all the columns. Yet we still can
  have a reasonable number of winning columns at each step in order to test
  overlap properties. boostStrength is set to 10 so that some boosted columns are
  guaranteed to win eventually but not necessarily quickly. potentialPct is set
  to 0.9 to ensure all columns have at least some overlap with at least one
  input bit. Thus, when sufficiently boosted, every column should become a
  winner at some point. We set permanence increment and decrement to 0 so that
  winning columns don't change unless they have been boosted.

  Learning is OFF for Phase 1 & 4 and ON for Phase 2 & 3

  Phase 1: Run spatial pooler on the dataset with learning off to get a baseline
  The boosting factors should be all ones in this phase. A significant fraction
  of the columns will not be used at all. There will be significant overlap
  between the first two inputs.

  Phase 2: Learning is on over the next 10 iterations. During this phase,
  columns that are active frequently will have low boost factors, and columns
  that are not active enough will have high boost factors. All columns should
  be active at some point in phase 2.

  Phase 3: Run one more batch on with learning On. Because of the artificially
  induced thrashing behavior in this test due to boosting, all the inputs should
  now have pretty distinct patterns.
  
  Phase 4: Run spatial pooler with learning off. Make sure boosting factors
  do not change when learning is off
  """

  def setUp(self):
    """
    Set various constants. Create the input patterns and the spatial pooler
    """
    self.inputSize = 90
    self.columnDimensions = 600

    # Create a set of input vectors, x
    # B,C,D don't overlap at all with other patterns
    self.x = numpy.zeros((5, self.inputSize), dtype=uintType)
    self.x[0, 0:20]  = 1   # Input pattern A
    self.x[1, 10:30] = 1   # Input pattern A' (half the bits overlap with A)
    self.x[2, 30:50] = 1   # Input pattern B  (no overlap with others)
    self.x[3, 50:70] = 1   # Input pattern C  (no overlap with others)
    self.x[4, 70:90] = 1   # Input pattern D  (no overlap with others)

    # For each column, this will contain the last iteration number where that
    # column was a winner
    self.winningIteration = numpy.zeros(self.columnDimensions)
    
    # For each input vector i, lastSDR[i] contains the most recent SDR output
    # by the SP.
    self.lastSDR = {}
    
    self.spImplementation = "None"
    
    self.sp = None

    # Setup the SP creation parameters we will use
    self.params = {
      'inputDimensions':            [self.inputSize],
      'columnDimensions':           [self.columnDimensions],
      'potentialRadius':            self.inputSize,
      'potentialPct':               0.9,
      'globalInhibition':           True,
      'numActiveColumnsPerInhArea': 60,
      'synPermActiveInc':           0.0,
      'synPermInactiveDec':         0.0,
      'dutyCyclePeriod':            10,
      'boostStrength':              10.0,
      'seed':                       SEED,
    }
    print "SP seed set to:", self.params['seed']

  def debugPrint(self):
    """
    Helpful debug print statements while debugging this test.
    """

    activeDutyCycle = numpy.zeros(self.columnDimensions, dtype=GetNTAReal())
    self.sp.getActiveDutyCycles(activeDutyCycle)
    
    boost = numpy.zeros(self.columnDimensions, dtype=GetNTAReal())
    self.sp.getBoostFactors(boost)
    print "\n--------- ITERATION", (
      self.sp.getIterationNum() ),"-----------------------"
    print "SP implementation:", self.spImplementation
    print "Learning iteration:",
    print "Max/min active duty cycle:", (
      activeDutyCycle.max(), activeDutyCycle.min() )
    print "Average non-zero active duty cycle:", (
      activeDutyCycle[activeDutyCycle>0].mean() )
    print "Active duty cycle", activeDutyCycle
    print
    print "Boost factor for sp:", boost
    print
    print "Last winning iteration for each column"
    print self.winningIteration
    print "Number of columns that have won at some point:", (
      self.columnDimensions - (self.winningIteration==0).sum() )

    
  def verifySDRProperties(self):
    """
    Verify that all SDRs have the properties desired for this test.
    
    The bounds for checking overlap are set fairly loosely here since there is
    some variance due to randomness and the artificial parameters used in this
    test.
    """
    # Verify that all SDR's are unique
    self.assertTrue(_areAllSDRsUnique(self.lastSDR), "All SDR's are not unique")

    # Verify that the first two SDR's have some overlap.
    self.assertGreater(_computeOverlap(self.lastSDR[0], self.lastSDR[1]), 9,
                       "First two SDR's don't overlap much")
    
    # Verify the last three SDR's have low overlap with everyone else.
    for i in [2, 3, 4]:
      for j in range(5):
        if (i!=j):
          self.assertLess(_computeOverlap(self.lastSDR[i], self.lastSDR[j]),
                          18, "One of the last three SDRs has high overlap")


  def boostTestPhase1(self):
    
    y = numpy.zeros(self.columnDimensions, dtype = uintType)
    # Do one batch through the input patterns while learning is Off
    for idx, v in enumerate(self.x):
      y.fill(0)
      self.sp.compute(v, False, y)
      self.winningIteration[y.nonzero()[0]] = self.sp.getIterationLearnNum()
      self.lastSDR[idx] = y.copy()

    # The boost factor for all columns should be at 1.
    boost = numpy.zeros(self.columnDimensions, dtype = GetNTAReal())
    self.sp.getBoostFactors(boost)
    self.assertEqual((boost==1).sum(), self.columnDimensions,
      "Boost factors are not all 1")
    
    # At least half of the columns should have never been active.
    self.assertGreaterEqual((self.winningIteration==0).sum(),
      self.columnDimensions/2, "More than half of the columns have been active")

    self.verifySDRProperties()
    

  def boostTestPhase2(self):

    y = numpy.zeros(self.columnDimensions, dtype = uintType)
    # Do 9 training batch through the input patterns
    for _ in range(10):
      for idx, v in enumerate(self.x):
        y.fill(0)
        self.sp.compute(v, True, y)
        self.winningIteration[y.nonzero()[0]] = self.sp.getIterationLearnNum()
        self.lastSDR[idx] = y.copy()

    # All the never-active columns should have duty cycle of 0
    dutyCycles = numpy.zeros(self.columnDimensions, dtype = GetNTAReal())
    self.sp.getActiveDutyCycles(dutyCycles)
    self.assertEqual(dutyCycles[self.winningIteration == 0].sum(), 0,
                     "Inactive columns have positive duty cycle.")

    boost = numpy.zeros(self.columnDimensions, dtype=GetNTAReal())
    self.sp.getBoostFactors(boost)
    self.assertLessEqual(numpy.max(boost[numpy.where(dutyCycles>0.1)]), 1.0,
                "Strongly active columns have high boost factors")
    self.assertGreaterEqual(numpy.min(boost[numpy.where(dutyCycles<0.1)]), 1.0,
                "Weakly active columns have low boost factors")

    # By now, every column should have been sufficiently boosted to win at least
    # once. The number of columns that have never won should now be 0
    numLosersAfter = (self.winningIteration == 0).sum()
    self.assertEqual(numLosersAfter, 0)

    # Because of the artificially induced thrashing, even the first two patterns
    # should have low overlap. Verify that the first two SDR's now have little
    # overlap
    self.assertLess(_computeOverlap(self.lastSDR[0], self.lastSDR[1]), 7,
                    "First two SDR's overlap significantly when they "
                    "shouldn't")


  def boostTestPhase3(self):
    # Do one more training batches through the input patterns
    y = numpy.zeros(self.columnDimensions, dtype = uintType)

    for idx, v in enumerate(self.x):
      y.fill(0)
      self.sp.compute(v, True, y)
      self.winningIteration[y.nonzero()[0]] = self.sp.getIterationLearnNum()
      self.lastSDR[idx] = y.copy()

    # By now, every column should have been sufficiently boosted to win at least
    # once. The number of columns that have never won should now be 0
    numLosersAfter = (self.winningIteration==0).sum()
    self.assertEqual(numLosersAfter, 0)

    # Because of the artificially induced thrashing, even the first two patterns
    # should have low overlap. Verify that the first two SDR's now have little
    # overlap
    self.assertLess(_computeOverlap(self.lastSDR[0], self.lastSDR[1]), 7,
                       "First two SDR's overlap significantly when they "
                       "shouldn't")


  def boostTestPhase4(self):
    boostAtBeg = numpy.zeros(self.columnDimensions, dtype=GetNTAReal())
    self.sp.getBoostFactors(boostAtBeg)

    # Do one more iteration through the input patterns with learning OFF
    y = numpy.zeros(self.columnDimensions, dtype=uintType)
    for _, v in enumerate(self.x):
      y.fill(0)
      self.sp.compute(v, False, y)

      boost = numpy.zeros(self.columnDimensions, dtype=GetNTAReal())
      self.sp.getBoostFactors(boost)
      self.assertEqual(boost.sum(), boostAtBeg.sum(),
        "Boost factors changed when learning is off")


  def boostTestLoop(self, imp):
    """Main test loop."""
    self.sp = CreateSP(imp, self.params)
    self.spImplementation = imp
    self.winningIteration.fill(0)
    self.lastSDR = {}
    
    self.boostTestPhase1()
    self.boostTestPhase2()
    self.boostTestPhase3()
    self.boostTestPhase4()

  def testBoostingPY(self):
    self.boostTestLoop("py")


  def testBoostingCPP(self):
    self.boostTestLoop("cpp")



if __name__ == "__main__":
  unittest.main()
