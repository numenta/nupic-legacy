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

import sys
import os
import time
import copy
import csv
import numpy as np
from nupic.research.spatial_pooler import SpatialPooler
from nupic.bindings.math import GetNTAReal

import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt

realDType = GetNTAReal()



def generatePlot(outputs, origData):
  """ Generates a table where each cell represent a frequency of pairs 
  as described below.
  x coordinate is the % difference between input records (origData list),
  y coordinate is the % difference between corresponding output records.
  """
  
  PLOT_PRECISION = 100
  
  distribMatrix = np.zeros((PLOT_PRECISION+1,PLOT_PRECISION+1))
    
  outputSize = len(outputs)
 
  for i in range(0,outputSize):
    for j in range(i+1,outputSize):
      
      in1 = outputs[i]
      in2 = outputs[j]
      dist = (abs(in1-in2) > 0.1)
      intDist = int(dist.sum()/2+0.1)

      orig1 = origData[i]
      orig2 = origData[j]
      origDist = (abs(orig1-orig2) > 0.1)
      intOrigDist = int(origDist.sum()/2+0.1)
  
      if intDist < 2 and intOrigDist > 10:
        print 'Elements %d,%d has very small SP distance: %d' % (i, j, intDist)
        print 'Input elements distance is %d' % intOrigDist
              
      x = int(PLOT_PRECISION*intDist/40.0)
      y = int(PLOT_PRECISION*intOrigDist/42.0)
      if distribMatrix[x, y] < 0.1:
        distribMatrix[x, y] = 3
      else:
        if distribMatrix[x, y] < 10:
          distribMatrix[x, y] += 1

  # Add some elements for the scale drawing
  distribMatrix[4, 50] = 3
  distribMatrix[4, 52] = 4
  distribMatrix[4, 54] = 5
  distribMatrix[4, 56] = 6
  distribMatrix[4, 58] = 7
  distribMatrix[4, 60] = 8
  distribMatrix[4, 62] = 9
  distribMatrix[4, 64] = 10

  return distribMatrix



def generateRandomInput(numRecords, elemSize = 400, numSet = 42):
  """ Generates a set of input record 
  
  Params:
          numRecords - how many records to generate
          elemSize - the size of each record (num 0s or 1s)
          numSet - how many 1s in each record
  
  Returns: a list of inputs
  """
  
  inputs = []
  
  for _ in xrange(numRecords):
    
    input = np.zeros(elemSize, dtype=realDType)
    for _ in range(0,numSet):
      ind = np.random.random_integers(0, elemSize-1, 1)[0]
      input[ind] = 1
    while abs(input.sum() - numSet) > 0.1:
      ind = np.random.random_integers(0, elemSize-1, 1)[0]
      input[ind] = 1
    
    inputs.append(input)  
  
  return inputs



def appendInputWithSimilarValues(inputs):
  """ Creates an 'one-off' record for each record in the inputs. Appends new
  records to the same inputs list.
  """
  numInputs = len(inputs)
  for i in xrange(numInputs):
    input = inputs[i]
    for j in xrange(len(input)-1):
      if input[j] == 1 and input[j+1] == 0:
        newInput = copy.deepcopy(input)
        newInput[j] = 0
        newInput[j+1] = 1
        inputs.append(newInput)
        break
        


def appendInputWithNSimilarValues(inputs, numNear = 10):
  """ Creates a neighboring record for each record in the inputs and adds
  new records at the end of the inputs list
  """
  numInputs = len(inputs)
  skipOne = False
  for i in xrange(numInputs):
    input = inputs[i]
    numChanged = 0
    newInput = copy.deepcopy(input)
    for j in xrange(len(input)-1):
      if skipOne:
        skipOne = False
        continue
      if input[j] == 1 and input[j+1] == 0:
        newInput[j] = 0
        newInput[j+1] = 1
        inputs.append(newInput)
        newInput = copy.deepcopy(newInput)
        #print input
        #print newInput
        numChanged += 1
        skipOne = True
        if numChanged == numNear:
          break



def modifyBits(inputVal, maxChanges):
  """ Modifies up to maxChanges number of bits in the inputVal
  """
  changes = np.random.random_integers(0, maxChanges, 1)[0]
  
  if changes == 0:
    return inputVal
  
  inputWidth = len(inputVal)
  
  whatToChange = np.random.random_integers(0, 41, changes)
  
  runningIndex = -1
  numModsDone = 0
  for i in xrange(inputWidth):
    if numModsDone >= changes:
      break
    if inputVal[i] == 1:
      runningIndex += 1
      if runningIndex in whatToChange:
        if i != 0 and inputVal[i-1] == 0:
          inputVal[i-1] = 1
          inputVal[i] = 0
  
  return inputVal



def getRandomWithMods(inputSpace, maxChanges):
  """ Returns a random selection from the inputSpace with randomly modified 
  up to maxChanges number of bits.
  """
  size = len(inputSpace)
  ind = np.random.random_integers(0, size-1, 1)[0]
  
  value = copy.deepcopy(inputSpace[ind])
  
  if maxChanges == 0:
    return value 
  
  return modifyBits(value, maxChanges)
  


def testSP():
  """ Run a SP test
  """
  
  elemSize = 400
  numSet = 42
  
  addNear = True
  numRecords = 2

  wantPlot = True

  poolPct = 0.5
  itr = 1
  doLearn = True

  while numRecords < 3:
    
    # Setup a SP
    sp = SpatialPooler(
           columnDimensions=(2048, 1),
           inputDimensions=(1, elemSize),
           potentialRadius=elemSize/2,
           numActiveColumnsPerInhArea=40,
           spVerbosity=0,
           stimulusThreshold=0,
           seed=1,
           potentialPct=poolPct,
           globalInhibition=True
           )
    
    # Generate inputs using rand() 
    inputs = generateRandomInput(numRecords, elemSize, numSet)
    if addNear:
      # Append similar entries (distance of 1)
      appendInputWithNSimilarValues(inputs, 42)
    
    inputSize = len(inputs)
    print 'Num random records = %d, inputs to process %d' % (numRecords, inputSize)  
    
    # Run a number of iterations, with learning on or off,
    # retrieve results from the last iteration only
    outputs = np.zeros((inputSize,2048))
    
    numIter = 1
    if doLearn:
      numIter = itr
  
    for iter in xrange(numIter):
      for i in xrange(inputSize):
        time.sleep(0.001)
        if iter == numIter - 1:
          # TODO: See https://github.com/numenta/nupic/issues/2072
          sp.compute(inputs[i], learn=doLearn, activeArray=outputs[i])
          #print outputs[i].sum(), outputs[i]
        else:
          # TODO: See https://github.com/numenta/nupic/issues/2072
          output = np.zeros(2048)
          sp.compute(inputs[i], learn=doLearn, activeArray=output)
      
    # Build a plot from the generated input and output and display it  
    distribMatrix = generatePlot(outputs, inputs)
    
    # If we don't want a plot, just continue  
    if wantPlot:
      plt.imshow(distribMatrix, origin='lower', interpolation = "nearest")
      plt.ylabel('SP (2048/40) distance in %')
      plt.xlabel('Input (400/42) distance in %')
      
      title = 'SP distribution'
      if doLearn:
        title += ', leaning ON'
      else:
        title +=  ', learning OFF'
        
      title += ', inputs = %d' % len(inputs)
      title += ', iterations = %d' % numIter
      title += ', poolPct =%f' % poolPct
      
      plt.suptitle(title, fontsize=12)
      plt.show()
      #plt.savefig(os.path.join('~/Desktop/ExperimentResults/videos5', '%s' % numRecords))
      #plt.clf()

    numRecords += 1
    
  return



def testSPNew():
  """ New version of the test"""

  elemSize = 400
  numSet = 42
  
  addNear = True
  numRecords = 1000

  wantPlot = False

  poolPct = 0.5
  itr = 5
  
  pattern = [60, 1000]
  doLearn = True
  start = 1
  learnIter = 0
  noLearnIter = 0
  
  numLearns = 0
  numTests = 0


  numIter = 1
  
  numGroups = 1000


  PLOT_PRECISION = 100.0
  distribMatrix = np.zeros((PLOT_PRECISION+1,PLOT_PRECISION+1))

  inputs = generateRandomInput(numGroups, elemSize, numSet)
  
  
  # Setup a SP
  sp = SpatialPooler(
         columnDimensions=(2048, 1),
         inputDimensions=(1, elemSize),
         potentialRadius=elemSize/2,
         numActiveColumnsPerInhArea=40,
         spVerbosity=0,
         stimulusThreshold=0,
         synPermConnected=0.12,
         seed=1,
         potentialPct=poolPct,
         globalInhibition=True
         )
  
  cleanPlot = False
      
  for i in xrange(numRecords):
    input1 = getRandomWithMods(inputs, 4)
    if i % 2 == 0:
      input2 = getRandomWithMods(inputs, 4)
    else:
      input2 = input1.copy()
      input2 = modifyBits(input2, 21)

    inDist = (abs(input1-input2) > 0.1)
    intInDist = int(inDist.sum()/2+0.1)
    #print intInDist
    
    if start == 0:
      doLearn = True
      learnIter += 1
      if learnIter == pattern[start]:
        numLearns += 1
        start = 1
        noLearnIter = 0
    elif start == 1:
      doLearn = False
      noLearnIter += 1
      if noLearnIter == pattern[start]:
        numTests += 1
        start = 0
        learnIter = 0
        cleanPlot = True

    # TODO: See https://github.com/numenta/nupic/issues/2072
    sp.compute(input1, learn=doLearn, activeArray=output1)
    sp.compute(input2, learn=doLearn, activeArray=output2)
    time.sleep(0.001)
    
    outDist = (abs(output1-output2) > 0.1)
    intOutDist = int(outDist.sum()/2+0.1)
  
    if not doLearn and intOutDist < 2 and intInDist > 10:
      """
      sp.spVerbosity = 10
      # TODO: See https://github.com/numenta/nupic/issues/2072
      sp.compute(input1, learn=doLearn, activeArray=output1)
      sp.compute(input2, learn=doLearn, activeArray=output2)
      sp.spVerbosity = 0

      
      print 'Elements has very small SP distance: %d' % intOutDist
      print output1.nonzero()
      print output2.nonzero()
      print sp._firingBoostFactors[output1.nonzero()[0]]
      print sp._synPermBoostFactors[output1.nonzero()[0]]
      print 'Input elements distance is %d' % intInDist
      print input1.nonzero()
      print input2.nonzero()
      sys.stdin.readline()
      """
            
    if not doLearn:
      x = int(PLOT_PRECISION*intOutDist/40.0)
      y = int(PLOT_PRECISION*intInDist/42.0)
      if distribMatrix[x, y] < 0.1:
        distribMatrix[x, y] = 3
      else:
        if distribMatrix[x, y] < 10:
          distribMatrix[x, y] += 1

    #print i

    # If we don't want a plot, just continue  
    if wantPlot and cleanPlot:
      plt.imshow(distribMatrix, origin='lower', interpolation = "nearest")
      plt.ylabel('SP (2048/40) distance in %')
      plt.xlabel('Input (400/42) distance in %')
      
      title = 'SP distribution'
      
      #if doLearn:
      #  title += ', leaning ON'
      #else:
      #  title +=  ', learning OFF'
        
      title += ', learn sets = %d' % numLearns
      title += ', test sets = %d' % numTests
      title += ', iter = %d' % numIter
      title += ', groups = %d' % numGroups
      title += ', Pct =%f' % poolPct
      
      plt.suptitle(title, fontsize=12)
      #plt.show()
      
      plt.savefig(os.path.join('~/Desktop/ExperimentResults/videosNew', '%s' % i))
      
      plt.clf()
      distribMatrix = np.zeros((PLOT_PRECISION+1,PLOT_PRECISION+1))
      cleanPlot = False
    


def testSPFile():
  """ Run test on the data file - the file has records previously encoded.
  """

  spSize = 2048
  spSet = 40

  poolPct = 0.5
  
  pattern = [50, 1000]
  doLearn = True

  PLOT_PRECISION = 100.0
  distribMatrix = np.zeros((PLOT_PRECISION+1,PLOT_PRECISION+1))

  inputs = []


  #file = open('~/Desktop/ExperimentResults/sampleArtificial.csv', 'rb')
  #elemSize = 400
  #numSet = 42
  
  #file = open('~/Desktop/ExperimentResults/sampleDataBasilOneField.csv', 'rb')
  #elemSize = 499
  #numSet = 7

  outdir = '~/Desktop/ExperimentResults/Basil100x21'
  inputFile = outdir+'.csv'
  file = open(inputFile, 'rb')
  
  elemSize = 100
  numSet = 21

  reader = csv.reader(file)

  for row in reader:
    input = np.array(map(float, row), dtype=realDType)
    if len(input.nonzero()[0]) != numSet:
      continue

    inputs.append(input.copy())

  file.close()
  
  # Setup a SP
  sp = SpatialPooler(
         columnDimensions=(spSize, 1),
         inputDimensions=(1, elemSize),
         potentialRadius=elemSize/2,
         numActiveColumnsPerInhArea=spSet,
         spVerbosity=0,
         stimulusThreshold=0,
         synPermConnected=0.10,
         seed=1,
         potentialPct=poolPct,
         globalInhibition=True
         )
  
  cleanPlot = False
  
  
  doLearn = False
  
  print 'Finished reading file, inputs/outputs to process =', len(inputs)
  
  size = len(inputs)

  for iter in xrange(100):
  
    print 'Iteration', iter
    
    # Learn
    if iter != 0:
      for learnRecs in xrange(pattern[0]):

        # TODO: See https://github.com/numenta/nupic/issues/2072
        ind = np.random.random_integers(0, size-1, 1)[0]
        sp.compute(inputs[ind], learn=True, activeArray=outputs[ind]) 

    # Test
    for _ in xrange(pattern[1]):
      rand1 = np.random.random_integers(0, size-1, 1)[0]
      rand2 = np.random.random_integers(0, size-1, 1)[0]
    
      sp.compute(inputs[rand1], learn=False, activeArray=output1)
      sp.compute(inputs[rand2], learn=False, activeArray=output2)
    
      outDist = (abs(output1-output2) > 0.1)
      intOutDist = int(outDist.sum()/2+0.1)
      
      inDist = (abs(inputs[rand1]-inputs[rand2]) > 0.1)
      intInDist = int(inDist.sum()/2+0.1)
      
      if intInDist != numSet or intOutDist != spSet:
        print rand1, rand2, '-', intInDist, intOutDist
  
      x = int(PLOT_PRECISION*intOutDist/spSet)
      y = int(PLOT_PRECISION*intInDist/numSet)
      if distribMatrix[x, y] < 0.1:
        distribMatrix[x, y] = 3
      else:
        if distribMatrix[x, y] < 10:
          distribMatrix[x, y] += 1

    if True:
      plt.imshow(distribMatrix, origin='lower', interpolation = "nearest")
      plt.ylabel('SP (%d/%d) distance in pct' % (spSize, spSet))
      plt.xlabel('Input (%d/%d) distance in pct' % (elemSize, numSet))
      
      title = 'SP distribution'
      title += ', iter = %d' % iter
      title += ', Pct =%f' % poolPct
      
      plt.suptitle(title, fontsize=12)

      #plt.savefig(os.path.join('~/Desktop/ExperimentResults/videosArtData', '%s' % iter))
      plt.savefig(os.path.join(outdir, '%s' % iter))
      
      plt.clf()
      distribMatrix = np.zeros((PLOT_PRECISION+1,PLOT_PRECISION+1))



if __name__ == '__main__':
  
  np.random.seed(83)

  #testSP()  
  #testSPNew()
  testSPFile()
  
