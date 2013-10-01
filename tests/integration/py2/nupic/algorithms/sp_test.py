#  Copyright (C) 2010 Numenta Inc. All rights reserved.
#
#  The information and source code contained herein is the
#  exclusive property of Numenta Inc. No part of this software
#  may be used, reproduced, stored or distributed in any form,
#  without explicit written authorization from Numenta Inc.
#   Author: Surabhi Gupta
# -----------------------------------------------------------------------------

import numpy as np
import sys
import random as r
import time
from nupic.bindings.math import GetNTAReal
from numpy.random import shuffle
from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA

from nupic.research import FDRCSpatial2, DataGenerator, distributions
from operator import itemgetter

realDType = GetNTAReal()

class TestSP:
  """This class is used for testing the performance of the spatial pooler """

  ############################################################################
  def __init__(self, n=150, w=21, seed=42, coincInputPoolPct=1.0):

    assert n>w
    self.n = n
    self.w = w
    self.seed = seed
    self.numCoincs = 2048
    self.numActivePerInhArea = 40
    self.coincInputPoolPct = coincInputPoolPct

    r.seed(seed)
    np.random.seed(seed)

  ############################################################################
  def initializeSP(self):

    self.sp = FDRCSpatial2.FDRCSpatial2(
                          coincidencesShape=(self.numCoincs, 1),
                          inputShape = (1, self.n),
                          inputBorder = self.n/2-1,
                          coincInputRadius = self.n/2,
                          numActivePerInhArea = self.numActivePerInhArea,
                          spVerbosity = 0,
                          stimulusThreshold = 0,
                          seed = 1,
                          coincInputPoolPct = .5,
                          )

  ############################################################################
  def compute(self, inputs, learn, infer):
    """Perform learning and/or inference on inputs.
    Returns the activation of the coincidences in the SP for each input
    Parameters:
    --------------------------------------------------------------------
    inputs:                   list of records
    learn:                    True if learning is on, otherwise off
    infer                     True if inference is on, otherwise off
    """

    outputs = np.zeros((len(inputs),self.numCoincs))
    for i in xrange(len(inputs)):
      outputs[i] = self.sp.compute(inputs[i], learn=learn, infer=infer)

      if (i+1)%100==0:
        print 'Record number:', i+1

    return outputs

  ############################################################################
  def topDownCompute(self, topDownIn):
    """See topDownCompute in FDRCSpatial2"""

    topDownOut = self.sp.topDownCompute(topDownIn)

    return topDownOut

class SPFrequencyTest():
  """Testing whether the spatial pooler is able to predict the most frequent
    record.

    For example, if we have two fields with the following records:
    car    red
    car    blue
    car    blue
    car    green
    car    blue

  SP should predict blue for car.
  """
  def __init__(self, encoderParams, numColors=10, patternsPerColor=30,
               seed=42, **kwargs):
    """Initialize a new frequency test. This involves setting up the encoders,
    and defining a Spatial Pooler.
    """
    encoderw=21
    encodern = 150
    self.numRecords=numColors*patternsPerColor
    assert 'encoderType' in encoderParams
    self.encoderType = encoderParams['encoderType']

    self.data=DataGenerator.DataGenerator()

    self.data.defineField(name='object', encoderParams=dict(encoderType='category',w=encoderw,n=encodern))

    if self.encoderType=='category':
      self.data.addField(name='color', fieldParams=dict(type='RandomCategories', \
        numOfValues=self.numRecords,w=encoderw,n=encodern), encoderParams=encoderParams)
    else:
      self.data.addField(name='color', fieldParams=dict(type='GaussianDistribution', \
          numOfValues=self.numRecords,w=encoderw,n=encodern), encoderParams=encoderParams)

    self.model = TestSP(seed=seed, n=self.data.getTotaln(),\
                   w=self.data.getTotalw())

  ################################################################################
  def _createValues(self, numColors):
    """Creating unique input patterns for all .

    Parameters:
    --------------------------------------------------------------------
    numValues:           number of unique values to be created
    """
    if self.encoderType=='scalar':
      Gaussian=distributions.GaussianDistribution(dict(numOfValues=numColors,mean=50,std=15))
      colors = Gaussian.getData()
    else:
      randomCategory = distributions.RandomCategories()
      colors = randomCategory.getData(numColors)

    return colors

  ############################################################################
  def _createTrainingSet(self, numTrainingRecords, uniqueInputs): #rename
    """Creating the training set. The predicted field is populated with a single,'
    repeating value of type category -- 'car'. Other scalar and category fields
    are populated with a gaussian distribution and/or randomly generated unique
    strings respectively. Each unique input pattern repeats for x% of the training
    set, ordered randomly. The number of occurances of input i in the dataset is
    freq[i].
    Parameters:
    --------------------------------------------------------------------
    numTrainingRecords:         total number of records in the training set
    uniqueInputs:               number of unique records

    The frequency of each unique record is returned
    """
    buffer = 0.9
    if numTrainingRecords > 500:
      buffer = 0.95
    trainingSet = []
    count = 2

    #Ensuring that there is a single, unique record with the highest frequency

    while(count>1):
      #Random sampling without replacement
      temp = sorted(r.sample(xrange(1, numTrainingRecords), len(uniqueInputs)-1))
      temp.append(numTrainingRecords)
      freq = [temp[0]]
      for z in xrange(1,len(temp)):
        freq.append(temp[z]-temp[z-1])
      count=0
      for x in freq:
        if abs(x-max(freq))<(1-buffer)*max(freq):
          count+=1

    for x in xrange(len(uniqueInputs)):
      for y in xrange(freq[x]):
        trainingSet.append(uniqueInputs[x])
    shuffle(trainingSet)

    return trainingSet, freq

  ############################################################################
  def freqTest(self, numColors, patternsPerColor=30, seed=42):
    """
    Parameters:
    --------------------------------------------------------------------
    numColors:        The number of unique records to be added to all fields
                      except the predicted field
    patternsPerColor: numColors is to be multiplied by patternsPerColor to
                      calculate the number of training records
    seed:             Setting the random seeds
    """
    print "Running the Frequency Test on the Spatial Pooler"

    self.model.initializeSP()
    self.data.setSeed(seed)
    numTrainingRecords = max(100, numColors*patternsPerColor)

    #Create unique input patterns and a training set
    colors = self._createValues(numColors)

    trainingSet, freq = self._createTrainingSet(numTrainingRecords, colors)

    inputcount= 0
    for input in trainingSet:
      self.data.generateRecord(['car', input])
      if input == colors[freq.index(max(freq))] and inputcount>=0:
        print "First occurence of max freq at:%d" % inputcount
        inputcount = -100000
      inputcount+=1
    #Add the most popular record as the last record, so can be visualized easily.
#    self.data.generateRecord(['car',colors[freq.index(max(freq))]])

    uniqueRecords = [['car', x] for x in colors]
    self.data.encodeAllRecords()

    colorEncodings = [np.concatenate(d) for d in self.data.encodeAllRecords(uniqueRecords,\
                                                              toBeAdded=False)]
    #Learn and infer
    outputs = self.model.compute(self.data.getAllEncodings(), learn=True, infer=False)

    testPattern=[self.data.getZeroedOutEncoding(index) for index in [0]]
    spatialPoolerOutput = self.model.compute(testPattern, learn=False, infer=True)

    reconstructedInput = self.model.topDownCompute(None)

    #Check whether the predicted record is the most frequent one
    fail = self._checkResultSPFrequency(colorEncodings, freq, reconstructedInput)

    return fail

  ############################################################################
  def rarePairTest(self,numColors,numPatterns, seed=42):
    """
    Parameters:
    --------------------------------------------------------------------
    numColors:        The number of unique records to be added to all fields
                      except the predicted field
    patternsPerColor: numColors is to be multiplied by patternsPerColor to
                      calculate the number of training records
    seed:             Setting the random seeds
    """
    print "Running the rare pair frequency test on the Spatial Pooler"
    numTrainingRecords = max(100,numColors*numPatterns)
    self.model.initializeSP()
    self.data.setSeed(seed)

    #Create unique input patterns and a training set
    colors = self._createValues(numColors+1)

    trainingSet, freq = self._createTrainingSet(numTrainingRecords, colors[0:numColors])

    #append a record with a different field 1 to the beginning so that it gets captured as a unique pattern
    self.data.generateRecord(['dog', colors[numColors]])


    for input in trainingSet:
      self.data.generateRecord(['car', input])
    uniqueRecords = [['car', x] for x in colors[0:numColors]]
    uniqueRecords +=[['dog', colors[numColors]]]
    self.data.encodeAllRecords()

    colorEncodings = [np.concatenate(d) for d in self.data.encodeAllRecords(uniqueRecords,\
                                                              toBeAdded=False)]
    #Learn and infer
    outputs = self.model.compute(self.data.getAllEncodings(), learn=True, infer=False)

    testPattern=[self.data.getZeroedOutEncoding(index) for index in [0]]
    spatialPoolerOutput = self.model.compute(testPattern, learn=False, infer=True)

    reconstructedInput = self.model.topDownCompute(spatialPoolerOutput[0])
    dotProducts = [np.dot(c,reconstructedInput) for c in colorEncodings]

    reconstructedColor=dotProducts.index(max(dotProducts))
    fail =  (not reconstructedColor == numColors)


    return fail
  ################################################################################
  def _checkResultSPFrequency(self, colors, freq, spReconstructedInput):
    """ Compare the results and return True if success, False if failure

    Parameters:
    --------------------------------------------------------------------
    colors:                   input representations corresponding to the colors
    spReconstructedInput:     SP reconstructed input
    """
    fail = 1
    dotProducts = [np.dot(c,spReconstructedInput) for c in colors]
    print "Dot Products: %s" % str(dotProducts)

    #The color(s) with max dotproducts are reconstructed
    reconstructedColor=np.where(dotProducts==max(dotProducts))

    #Get the top three color frequencies
    freqInd = range(len(freq))
    zippedFreq = zip(freqInd,freq)
    topThreeColors = sorted(zippedFreq,key=itemgetter(1))[-3:]
    topThreeColors = [tup[0] for tup in topThreeColors]

    #The most frequent color is expected to be predicted
    expectedColor = freq.index(max(freq))

    #If more than 10 colors only make sure that the matching color is in
    #top 3 most frequent colors
    if(len(freq)>10):
      colorsToMatch = topThreeColors
    else:
      colorsToMatch = [expectedColor]



    print 'Frequency of', len(freq), 'colors in the testing data:', freq

    if reconstructedColor[0][0] not in colorsToMatch:
      print 'Test Failed!'
      print 'Dot product for:'
      print 'The most frequent color', expectedColor+1, 'with frequency', \
              max(freq), ':', dotProducts[expectedColor]
      print 'The reconstructed color(s)', ', '.join(str(z+1) for z in \
            reconstructedColor[0]), 'with frequencies', ', '.join(str(freq[x]) \
                        for x in reconstructedColor[0]), ':', max(dotProducts)
    else:
      print 'Test Passed!'
      print 'The most frequent color', expectedColor+1, 'with frequency', max(freq), \
              'was reconstructed with dot product:', max(dotProducts)
      fail = 0
    return fail

################################################################################
def test(long=False):
  """Run all tests"""

  #Define two types of SPFrequency Test
  categoryTest=SPFrequencyTest(dict(encoderType='category', isPredictedField=True))
  scalarTest=SPFrequencyTest(dict(encoderType='scalar', minval=0, maxval=100, \
                                  isPredictedField=True))

  startTime = time.time()
  fail = []
  if long:
    # ============================================================================
    #Run the long version of frequency tests

    for numC in [8, 12, 15, 24, 30, 40, 50]:
      for repeat in range(10):
        categoryTest=SPFrequencyTest(dict(encoderType='category', isPredictedField=True))
        scalarTest=SPFrequencyTest(dict(encoderType='scalar', minval=0, maxval=100, \
                                  isPredictedField=True))
        seed = numC + 5*repeat
        print "Seed - %s" % seed
        fail.append((categoryTest.freqTest(numC,30,seed),seed,numC,'category'))
        categoryTest.data.removeAllRecords()

#        fail.append((scalarTest.freqTest(numC,30,seed),seed,numC,'scalar'))
#        scalarTest.data.removeAllRecords()
        print "******Elapsed time: %.2f seconds******" % (time.time() - startTime)

  # ============================================================================
  # Run the (--short) version of frequency tests

  for numC in [2, 10]:
    seed = numC + 30

    #Testing with a category field
    fail.append((categoryTest.freqTest(numC,30,seed),seed,numC,'category'))
    categoryTest.data.removeAllRecords()

    #Testing with a scalar field:
    fail.append((scalarTest.freqTest(numC,30,seed),seed,numC,'scalar'))
    scalarTest.data.removeAllRecords()
    print "******Elapsed time: %.2f seconds*******" % (time.time() - startTime)


  #Report specs of failed tests (if any)
  anyFailed = sum(fail[x][0] for x in xrange(len(fail)))
  if anyFailed==0:
    print '\nAll tests passed!'
  else:
    print '\nThe following test(s) failed:'
    for g in fail:
      if g[0]<>0:
        print 'Seed:', g[1], 'Number of colors:', g[2], 'Type of encoder:', g[3]
    raise RuntimeError('One or more tests failed')

  #Two Pairs with one having a very high frequency test
  for colors in [2,8,15]:

    for seed in range(3):
      fail = scalarTest.rarePairTest(colors,20,seed)
      scalarTest.data.removeAllRecords()
      if fail:
        raise RuntimeError('Rare Pair Scalar Test Failed with %d colors and seed=%d' % (colors,seed))


      fail = categoryTest.rarePairTest(2,20,seed)
      categoryTest.data.removeAllRecords()
      if fail:
        raise RuntimeError('Rare Pair Category Test Failed with %d colors and seed=%d' % (colors,seed))


################################################################################
if __name__ == '__main__':

  # =========================================================================
  print "Temporarily disabled while SP issues are being resolved"
  sys.exit(0)
  # =========================================================================

  long=False
  if (len(sys.argv) > 1):
    if('--long' in sys.argv):
      long = True
  test(long=long)