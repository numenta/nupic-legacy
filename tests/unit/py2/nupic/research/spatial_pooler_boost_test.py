#! /usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

import time
import numpy
import unittest2 as unittest

from nupic.support.unittesthelpers.algorithm_test_helpers \
     import getNumpyRandomGenerator, convertSP, CreateSP
from nupic.bindings.math import (count_gte,
                                 GetNTAReal,
                                 SM_01_32_32 as SparseBinaryMatrix,
                                 SM32 as SparseMatrix)
from nupic.research.spatial_pooler import SpatialPooler

uintType = "uint32"

# set a single seed for running both implementations
SEED = int((time.time()%10000)*10)


def ComputeOverlap(x,y):
  """
  Given two binary arrays, compute their overlap. The overlap is the number
  of bits where x[i] and y[i] are both 1
  """
  return ((x + y) == 2).sum()

def AreAllSDRsUnique(sdrDict):
  """Return True iff all the SDR's in the dict are unique."""
  for k1,v1 in sdrDict.iteritems():
    for k2,v2 in sdrDict.iteritems():
      # Return false if two different keys have identical SDR's
      if (k2 != k1) and ((v1 == v2).sum() == v1.size):
        return False
      
  return True


class SpatialPoolerBoostTest(unittest.TestCase):
  """
  Test boosting.
  
  The test is constructed as follows: we construct a set of 5 known inputs. Two
  of the input patterns have 50% overlap while all other combinations have 0%
  overlap. Each input pattern has at least 20 bits on to ensure reasonable
  overlap with almost all columns.

  SP parameters: the minActiveDutyCycle is set to 1 in 10. This allows us to
  test boosting with a small number of iterations. The SP is set to have 200
  columns with 10% output sparsity. This ensures that the 5 inputs cannot use up
  all the columns. Yet we still can have a reasonable number of winning columns
  at each step in order to test overlap properties. maxBoost is set to 10 so
  that some boosted columns are guaranteed to win eventually but not necessarily
  quickly. potentialPct is set to 0.75 to ensure all columns have at least some
  overlap with at least one input bit. Thus, when sufficiently boosted, every
  column should become a winner at some point.
  
  Phase 1: As learning progresses through the first 5 iterations, the first 5
  patterns should get distinct output SDRs. The two overlapping input patterns
  should have reasonably overlapping output SDRs. The other pattern
  combinations should have very little overlap. The boost factor for all
  columns should be at 1. At this point least half of the columns should have
  never become active and these columns should have duty cycle of 0. Any
  columns which have won, should have duty cycles >= 0.2.
  
  Phase 2: Over the next 45 iterations, boosting should stay at 1 for all
  columns since minActiveDutyCycle is only calculated after 50 iterations. The
  winning columns should be very similar (identical?) to the columns that won
  before. About half of the columns should never become active. At the end of
  the this phase, most of these columns should have activity level around 0.2.
  It's ok for some columns to have higher activity levels.
  
  Phase 3: Over the next 5 iterations boosting should start to increase
  gradually for almost half of the columns. At this point boosting should
  be less than maxBoost for all columns.
  
  Phase 4: Boost factor should continue to increase until some new columns
  start to win. As soon as a new column wins, the boost value for that column
  should be set back to 1 and its activity level should go back to 1.
  
  Phase 5: After a bunch of iterations, every column should have won at least
  once.
  
  Phase 6: Run for 10 iterations without learning on. Boost values and winners
  should not change.
  
  """

  def setUp(self):
    """
    Set various constants. Create the input patterns and the spatial pooler
    """
    self.inputSize = 90
    self.columnDimensions = 200

    # Create a set of input vectors, x
    # B,C,D don't overlap at all with other patterns
    self.x = numpy.zeros((5,self.inputSize), dtype=uintType)
    self.x[0,0:20]  = 1   # Input pattern A
    self.x[1,10:30] = 1   # Input pattern A' (half the bits overlap with A)
    self.x[2,30:50] = 1   # Input pattern B  (no overlap with others)
    self.x[3,50:70] = 1   # Input pattern C  (no overlap with others)
    self.x[4,70:90] = 1   # Input pattern D  (no overlap with others)

    # For each column, this will contain the last iteration number where that
    # column was a winner
    self.winningIteration = numpy.zeros(self.columnDimensions)
    
    # For each input vector i, lastSDR[i] contains the most recent SDR output
    # by the SP.
    self.lastSDR = {}
    
    self.spImplementation = "None"


    # Setup the SP creation parameters we will use
    self.params = {
      'inputDimensions':            [self.inputSize],
      'columnDimensions':           [self.columnDimensions],
      'potentialRadius':            self.inputSize,
      'potentialPct':               0.75,
      'numActiveColumnsPerInhArea': 20,
      'minPctActiveDutyCycle':      0.1,
      'dutyCyclePeriod':            10,
      'maxBoost':                   10.0,  # TEMP FOR DEBUGGING
      'seed':                       SEED,
    }
    print "SP seed set to:",self.params['seed']

  def debugPrint(self):
    """
    Helpful debug print statements while debugging this test.
    """

    minDutyCycle = numpy.zeros(self.columnDimensions, dtype = GetNTAReal())
    self.sp.getMinActiveDutyCycles(minDutyCycle)
    
    activeDutyCycle = numpy.zeros(self.columnDimensions, dtype = GetNTAReal())
    self.sp.getActiveDutyCycles(activeDutyCycle)
    
    boost = numpy.zeros(self.columnDimensions, dtype = GetNTAReal())
    self.sp.getBoostFactors(boost)
    print "SP implementation:", self.spImplementation
    print "Learning iteration:", self.sp.getIterationNum()
    print "Min duty cycles:",minDutyCycle[0]
    print "Active duty cycle", activeDutyCycle
    print "Average non-zero active duty cycle:", (
      activeDutyCycle[activeDutyCycle>0].mean() )
    print
    print "Boost factor for sp:",boost
    print
    print "Last winning iteration for each column"
    print self.winningIteration
    print "Number of winning columns:", (
      self.columnDimensions - (self.winningIteration==0).sum() )
    
    
  def boostTestPhase1(self):
    
    y = numpy.zeros(self.columnDimensions, dtype = uintType)

    # Do one training batch through the input patterns
    for idx,v in enumerate(self.x):
      y.fill(0)
      self.sp.compute(v, True, y)
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
    
    # All the never-active columns should have duty cycle of 0
    # All the at-least-once-active columns should have duty cycle >= 0.2
    dutyCycles = numpy.zeros(self.columnDimensions, dtype = GetNTAReal())
    self.sp.getActiveDutyCycles(dutyCycles)
    self.assertEqual(dutyCycles[self.winningIteration == 0].sum(),0,
                     "Inactive columns have positive duty cycle.")
    self.assertGreaterEqual(dutyCycles[self.winningIteration > 0].min(),
                            0.2,
                            "Active columns have duty cycle that is too low.")

    # Verify that all SDR's are unique
    self.assertTrue(AreAllSDRsUnique(self.lastSDR), "All SDR's are not unique")
    
    # Verify that the first two SDR's have reasonable overlap
    self.assertGreater(ComputeOverlap(self.lastSDR[0], self.lastSDR[1]), 4,
                       "First two SDR's don't overlap much")
    
    # Verify the last three SDR's have low overlap with everyone else
    for i in [2, 3, 4]:
      for j in range(5):
        if (i!=j):
          self.assertLess( ComputeOverlap(self.lastSDR[i], self.lastSDR[j]),
                          2, "One of the last three SDRs has high overlap")
    

  def boostTestPhase2(self):
    
    y = numpy.zeros(self.columnDimensions, dtype = uintType)

    # Do 9 training batch through the input patterns
    for i in range(9):
      for idx,v in enumerate(self.x):
        y.fill(0)
        self.sp.compute(v, True, y)
        self.winningIteration[y.nonzero()[0]] = self.sp.getIterationLearnNum()
        self.lastSDR[idx] = y.copy()
        
    # The boost factor for all columns should be at 1.
    boost = numpy.zeros(self.columnDimensions, dtype = GetNTAReal())
    self.sp.getBoostFactors(boost)
    self.assertEqual((boost==1).sum(), self.columnDimensions,
      "Boost factors are not all 1")
    
    # Roughly half of the columns should have never been active.
    self.assertGreaterEqual((self.winningIteration==0).sum(),
      0.4*self.columnDimensions,
      "More than 60% of the columns have been active")
    
    # All the never-active columns should have duty cycle of 0
    dutyCycles = numpy.zeros(self.columnDimensions, dtype = GetNTAReal())
    self.sp.getActiveDutyCycles(dutyCycles)
    self.assertEqual(dutyCycles[self.winningIteration == 0].sum(),0,
                     "Inactive columns have positive duty cycle.")

    # The average at-least-once-active columns should have duty cycle >= 0.15
    # and <= 0.25
    avg = (dutyCycles[dutyCycles>0].mean() )
    self.assertGreaterEqual(avg, 0.15,
                "Average on-columns duty cycle is too low.")
    self.assertLessEqual(avg, 0.25,
                "Average on-columns duty cycle is too high.")

    # Verify that all SDR's are unique
    self.assertTrue(AreAllSDRsUnique(self.lastSDR), "All SDR's are not unique")
    
    # Verify that the first two SDR's have reasonable overlap
    self.assertGreater(ComputeOverlap(self.lastSDR[0], self.lastSDR[1]), 4,
                       "First two SDR's don't overlap much")

    # Verify the last three SDR's have low overlap with everyone else
    for i in [2, 3, 4]:
      for j in range(5):
        if (i!=j):
          self.assertLess( ComputeOverlap(self.lastSDR[i], self.lastSDR[j]),
                          2, "One of the last three SDRs has high overlap")


  def boostTestLoop(self, imp):
    """Main test loop."""
    self.sp = CreateSP(imp,self.params)
    self.spImplementation = imp
    self.winningIteration.fill(0)
    self.lastSDR = {}
    
    self.boostTestPhase1()
    self.boostTestPhase2()

  def testBoostingPY(self):
    self.boostTestLoop("py")


  def testBoostingCPP(self):
    self.boostTestLoop("cpp")





if __name__ == "__main__":
  unittest.main()
