# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""
This is a legacy test from trunk and may replicate spatial pooler tests.

The allocation of cells to new patterns is explored. After all the cells
have been allocated, cells must be reused. This test makes sure that the
allocation of new cells is such that we achieve maximum generality and
predictive power.

Note: Since the sp pooler has 2048 cells with a sparsity of 40 cells active
per iteration, 100% allocation is reached at the 51st unique pattern.
"""

import unittest2 as unittest
import random as rnd
import time

import numpy

from nupic.bindings.math import GetNTAReal
from nupic.encoders import scalar

from nupic.bindings.algorithms import SpatialPooler

realDType = GetNTAReal()

SEED = 42



class TestSPFrequency(unittest.TestCase):


  def testCategory(self):
    """Test that the most frequent possible option is chosen for a scalar
    encoded field """
    self.frequency(n=100, w=21, seed=SEED, numColors=90, encoder = 'scalar')


  def testScalar(self):
    """Test that the most frequent possible option is chosen for a category
    encoded field """
    self.frequency(n=30, w=21, seed=SEED, numColors=90, encoder = 'category')


  @unittest.skip("Not working...")
  def testScalarLong(self):
    """Test that the most frequent possible option is chosen for a scalar
    encoded field. Run through many different numbers of patterns and random
    seeds"""
    for n in [52, 70, 80, 90, 100, 110]:
      self.frequency(n=100, w=21, seed=SEED, numColors=n, encoder='scalar')


  @unittest.skip("Not working...")
  def testCategoryLong(self):
    """Test that the most frequent possible option is chosen for a category
    encoded field. Run through many different numbers of patterns and random
    seeds"""
    for n in [52, 70, 80, 90, 100, 110]:
      self.frequency(n=100, w=21, seed=SEED, numColors=n)


  def frequency(self,
                n=15,
                w=7,
                columnDimensions = 2048,
                numActiveColumnsPerInhArea = 40,
                stimulusThreshold = 0,
                spSeed = 1,
                spVerbosity = 0,
                numColors = 2,
                seed=42,
                minVal=0,
                maxVal=10,
                encoder = 'category',
                forced=True):

    """ Helper function that tests whether the SP predicts the most
    frequent record """

    print "\nRunning SP overlap test..."
    print encoder, 'encoder,', 'Random seed:', seed, 'and', numColors, 'colors'
    #Setting up SP and creating training patterns

    # Instantiate Spatial Pooler
    spImpl = SpatialPooler(
                           columnDimensions=(columnDimensions, 1),
                           inputDimensions=(1, n),
                           potentialRadius=n/2,
                           numActiveColumnsPerInhArea=numActiveColumnsPerInhArea,
                           spVerbosity=spVerbosity,
                           stimulusThreshold=stimulusThreshold,
                           potentialPct=0.5,
                           seed=spSeed,
                           globalInhibition=True,
                           )
    rnd.seed(seed)
    numpy.random.seed(seed)

    colors = []
    coincs = []
    reUsedCoincs = []
    spOutput = []
    patterns = set([])

    # Setting up the encodings
    if encoder=='scalar':
      enc = scalar.ScalarEncoder(name='car', w=w, n=n, minval=minVal,
                                 maxval=maxVal, periodic=False, forced=True) # forced: it's strongly recommended to use w>=21, in the example we force skip the check for readibility
      for y in xrange(numColors):
        temp = enc.encode(rnd.random()*maxVal)
        colors.append(numpy.array(temp, dtype=numpy.uint32))
    else:
      for y in xrange(numColors):
        sdr = numpy.zeros(n, dtype=numpy.uint32)
        # Randomly setting w out of n bits to 1
        sdr[rnd.sample(xrange(n), w)] = 1
        colors.append(sdr)

    # Training the sp
    print 'Starting to train the sp on', numColors, 'patterns'
    startTime = time.time()
    for i in xrange(numColors):
      # TODO: See https://github.com/numenta/nupic/issues/2072
      spInput = colors[i]
      onCells = numpy.zeros(columnDimensions, dtype=numpy.uint32)
      spImpl.compute(spInput, True, onCells)
      spOutput.append(onCells.tolist())
      activeCoincIndices = set(onCells.nonzero()[0])

      # Checking if any of the active cells have been previously active
      reUsed = activeCoincIndices.intersection(patterns)

      if len(reUsed) == 0:
        # The set of all coincidences that have won at least once
        coincs.append((i, activeCoincIndices, colors[i]))
      else:
        reUsedCoincs.append((i, activeCoincIndices, colors[i]))

      # Adding the active cells to the set of coincs that have been active at
      # least once
      patterns.update(activeCoincIndices)

      if (i + 1) % 100 == 0:
        print 'Record number:', i + 1

        print "Elapsed time: %.2f seconds" % (time.time() - startTime)
        print len(reUsedCoincs), "re-used coinc(s),"

    # Check if results match expectations
    summ = []
    for z in coincs:
      summ.append(sum([len(z[1].intersection(y[1])) for y in reUsedCoincs]))

    zeros = len([x for x in summ if x==0])
    factor = max(summ)*len(summ)/sum(summ)
    if len(reUsed) < 10:
      self.assertLess(factor, 41,
                      "\nComputed factor: %d\nExpected Less than %d" % (
                          factor, 41))
      self.assertLess(zeros, 0.99*len(summ),
                      "\nComputed zeros: %d\nExpected Less than %d" % (
                          zeros, 0.99*len(summ)))

    else:
      self.assertLess(factor, 8,
                      "\nComputed factor: %d\nExpected Less than %d" % (
                          factor, 8))
      self.assertLess(zeros, 12,
                      "\nComputed zeros: %d\nExpected Less than %d" % (
                          zeros, 12))


def hammingDistance(s1, s2):
  assert len(s1) == len(s2)
  return sum(ch1 != ch2 for ch1, ch2 in zip(s1, s2))



if __name__ == '__main__':
  unittest.main()
