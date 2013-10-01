import unittest2 as unittest
import numpy as np
import sys
import random as rnd
import time
from nupic.bindings.math import GetNTAReal
from nupic.encoders import scalar
#from pylab import *

from nupic.research import FDRCSpatial2
from nupic.support.unittesthelpers import testcasebase
unresolved=True

'''
The allocation of cells to new patterns is explored. After all the cells
have been allocated, cells must be reused. This test makes sure that the
allocation of new cells is such that we achieve maximum generality and predictive
power.

Note: Since the sp pooler has 2048 cells with a sparsity of 40 cells active per iteration,
100% allocation is reached at the 51st unique pattern.
'''
realDType = GetNTAReal()





class TestSPFrequency(testcasebase.TestCaseBase):
  
  def testCategory(self):
    """Test that the most frequent possible option is chosen for a scalar
    encoded field """
    self.frequency(n=100, w=15, seed=SEED, numColors=90, encoder = 'scalar')
  
  def testScalar(self):
    """Test that the most frequent possible option is chosen for a category
    encoded field """
    self.frequency(n=30, w=13, seed=SEED, numColors=90, encoder = 'category')
  
  @testcasebase.longTest
  def testScalarLong(self):
    """Test that the most frequent possible option is chosen for a scalar
    encoded field. Run through many different numbers of patterns and random
    seeds"""
    for n in [52, 70, 80, 90, 100, 110]:
      self.frequency(n=100, w=15, seed=s, numColors=n, encoder='scalar')
      
  @testcasebase.longTest
  def testCategoryLong(self):
    """Test that the most frequent possible option is chosen for a catergory
    encoded field. Run through many different numbers of patterns and random
    seeds"""
    for n in [52, 70, 80, 90, 100, 110]:
      self.frequency(n=100, w=15, seed=SEED, numColors=n)
  
  ##############################################################################
  def frequency(self,
                n=15,
                w=7,
                coincidencesShape = 2048,
                numActivePerInhArea = 40,
                stimulusThreshold = 0,
                spSeed = 1,
                spVerbosity = 0,
                numColors = 2,
                seed=42,
                minVal=0,
                maxVal=10,
                encoder = 'category'):
    
    """ Helper function that tests whether the SP predicts the most
    frequent record """
    
    print "\nRunning SP overlap test..."
    print encoder, 'encoder,', 'Random seed:', seed, 'and', numColors, 'colors'
    # -----------------------------------------------------------------------
    #Setting up SP and creating training patterns
    
    # Instantiate Spatial Pooler
    spImpl = FDRCSpatial2.FDRCSpatial2(
                            coincidencesShape=(coincidencesShape, 1),
                            inputShape = (1, n),
                            inputBorder = (n-2)/2,
                            coincInputRadius = n/2,
                            numActivePerInhArea = numActivePerInhArea,
                            spVerbosity = spVerbosity,
                            stimulusThreshold = stimulusThreshold,
                            coincInputPoolPct = 0.5,
                            seed = spSeed,
                            spReconstructionParam='dutycycle',
                            )
    rnd.seed(seed)
    np.random.seed(seed)
    
    colors = []
    coincs = []
    reUsedCoincs = []
    spOutput = [] 
    patterns = set([])
    
    # -----------------------------------------------------------------------
    #Setting up the encodings
    if encoder=='scalar':
      enc = scalar.ScalarEncoder(name='car',w=w, n=n, minval=minVal, maxval=maxVal, periodic=False)
      for y in xrange(numColors):
        temp = enc.encode(rnd.random()*maxVal)
        colors.append(np.array(temp, dtype=realDType))
    else:
      for y in xrange(numColors):
        sdr = np.zeros(n, dtype=realDType)
        sdr[rnd.sample(xrange(n), w)] = 1       #Randomly setting w out of n bits to 1
        colors.append(sdr)
  
    # -----------------------------------------------------------------------
    # Training the sp
    print 'Starting to train the sp on', numColors, 'patterns'
    startTime = time.time()
    for i in xrange(numColors):
      input = colors[i] 
      onCells = spImpl.compute(input, learn=True, infer=False)
      spOutput.append(onCells.tolist())
      activeCoincIndices = set(onCells.nonzero()[0])
      
      #Checking if any of the active cells have been previously active
      reUsed = activeCoincIndices.intersection(patterns)  
      
      if len(reUsed)==0:
        #The set of all coincidences that have won atleast once
        coincs.append((i,activeCoincIndices,colors[i]))   
      else:
        reUsedCoincs.append((i,activeCoincIndices,colors[i]))
      
      #Adding the active cells to the set of coincs that have been active at least once
      patterns.update(activeCoincIndices)   
  
    if (i+1)%100==0:
      print 'Record number:', i+1
    
      print "Elapsed time: %.2f seconds" % (time.time() - startTime)
      print len(reUsedCoincs),'re-used coinc(s),'
    
    #matrix = zeros([2*w+1,2*numActivePerInhArea+1])
    #drawMatrix(matrix, colors, spOutput)   #Draw the matrix of differences. --needs pylab to be imported 
  
    # -----------------------------------------------------------------------
    #Check if results match expectations
    
    fail = 1
    Summ = []
    for z in coincs:
      Summ.append(sum([len(z[1].intersection(y[1])) for y in reUsedCoincs]))
    
    #print 'Sum (from pattern 52 to', 51+len(reUsed), '):', Summ
    #print 'Max ~', factor, 'X average'
    #print 'Number of zeros:', zeros
    
    zeros = len([x for x in Summ if x==0])
    factor = max(Summ)*len(Summ)/sum(Summ)
    if len(reUsed) < 10:
      self.assertLess(factor, 30,
                      "\nComputed factor: %d\nExpected Less than %d" % \
                      (factor, 30))
      self.assertLess(zeros, 0.99*len(Summ),
                      "\nComputed zeros: %d\nExpected Less than %d" % \
                     (zeros, 0.99*len(Summ)))
      
    else:
      self.assertLess(factor, 8,
                      "\nComputed factor: %d\nExpected Less than %d" % \
                      (factor, 8))
      self.assertLess(zeros, 12,
                      "\nComputed zeros: %d\nExpected Less than %d" % \
                     (zeros, 12))
      
    
  def drawMatrix(matrix, colors, spOutput):
    ''' (i,j)th cell of the diff matrix will have the number of inputs for which the input and output
    pattern differ by i bits and the cells activated differ at j places. '''
    
    for x in xrange(1):
      i = [hamming_distance(colors[x], z) for z in colors]
      j = [hamming_distance(spOutput[x], a) for a in spOutput]
    for p, q in zip(i,j):
    #  import pdb; pdb.set_trace()
      matrix[p,q]+=1
  
    matshow(matrix)
    ylabel('Number of bits different in input and output') 
    xlabel('Number of cells different between input and output')
    title('The difference matrix')
    colorbar() 
    show()

############################################################################
# Utility functions
############################################################################
def hamming_distance(s1, s2):
  assert len(s1) == len(s2)
  return sum(ch1 != ch2 for ch1, ch2 in zip(s1, s2))

def printOverlaps(comparedTo, coincs, seen):
  """ Compare the results and return True if success, False if failure

  Parameters:
  --------------------------------------------------------------------
  coincs:               Which cells are we comparing?
  comparedTo:           What cells are we comparing it to?
  seen:                 Which of the cells we are comparing to have already been encountered.
                        This helps glue together the unique and reused coincs
  """
  dist = 0
  for y in comparedTo:
    closest = []
    current = set(np.nonzero(y[2])[0])
    if len(seen)>0:
      dist = max([len(seen[m][0].intersection(current)) for m in xrange(len(seen))])
      for m in xrange(len(seen) ):
        if len(seen[m][0].intersection(current))==dist:
          closest.append(seen[m][1])
    print 'Pattern',y[0]+1,':',' '.join(str(len(z[1].intersection(y[1]))).rjust(2) for z in coincs),'Overlap:', dist, '--', len(closest), 'closest patterns:',','.join(str(m+1) for m in closest)
    seen.append((current, y[0]))
  return seen

############################################################################
if __name__ == '__main__':
  parser = testcasebase.TestOptionParser()
  options, _ = parser.parse_args()
  
  SEED = options.seed
  VERBOSITY = options.verbosity
  LONG = options.long
  
  unittest.main(verbosity=VERBOSITY)
