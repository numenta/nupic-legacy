#!/usr/bin/env python
# ----------------------------------------------------------------------
#  Copyright (C) 2011, Numenta Inc. All rights reserved.
#
#  The information and source code contained herein is the
#  exclusive property of Numenta Inc. No part of this software
#  may be used, reproduced, stored or distributed in any form,
#  without explicit written authorization from Numenta Inc.
# ----------------------------------------------------------------------

import sys
import numpy
import os

from nupic.research import FDRCSpatial2

numpy.random.seed(100)

'''
Test if the firing number of coincidences after inhibition equals spatial pooler
numActivePerInhArea.
'''

def testInhibition(n=15,
                   w=100,
                   inputLen = 300,
                   synPermConnected = 0.10,
                   synPermActiveInc = 0.10,
                   connectPct = 0.50,
                   coincidencesShape = 2048,
                   numActivePerInhArea = 40,
                   stimulusThreshold = 0,
                   spSeed = 1956,
                   stimulusThresholdInh = 0.00001,
                   kDutyCycleFactor = 0.01,
                   spVerbosity = 0,
                   testIter = 10):
  '''
  Test if the firing number of coincidences after inhibition
  equals spatial poolernumActivePerInhArea.
  Parameters:
    ----------------------------
  n, w:                 n, w of encoders
  inputLen:             Length of binary input
  synPermConnected:     Spatial pooler synPermConnected
  synPermActiveInc:     Spatial pooler synPermActiveInc
  connectPct:           Initial connect percentage of permanences
  coincidencesShape:    Number of spatial pooler coincidences
  numActivePerInhArea:  Spatial pooler numActivePerInhArea
  stimulusThreshold:    Spatial pooler stimulusThreshold
  spSeed:               Spatial pooler for initial permanences
  stimulusThresholdInh: Parameter for inhibition, default value 0.00001
  kDutyCycleFactor:     kDutyCycleFactor for dutyCycleTieBreaker in Inhibition
  spVerbosity:          Verbosity to print other sp initial parameters
  testIter:             Testing iterations

  '''

  spTest = FDRCSpatial2.FDRCSpatial2(
                              coincidencesShape=(coincidencesShape, 1),
                              inputShape = (1, inputLen),
                              inputBorder = inputLen/2 -1,
                              coincInputRadius = inputLen/2,
                              numActivePerInhArea = numActivePerInhArea,
                              spVerbosity = spVerbosity,
                              stimulusThreshold = stimulusThreshold,
                              seed = spSeed
                              )
  initialPermanence = spTest._initialPermanence()
  spTest._masterPotentialM, spTest._masterPermanenceM = \
      spTest._makeMasterCoincidences(spTest.numCloneMasters, spTest._coincRFShape,
                                   spTest.coincInputPoolPct, initialPermanence,
                                   spTest.random)

  spTest._updateInhibitionObj()
  boostFactors = numpy.ones(coincidencesShape)

  for i in range(testIter):
    spTest._iterNum = i
    # random binary input
    input = numpy.zeros((1,inputLen))
    nonzero =numpy.random.random(inputLen)
    input[0][numpy.where (nonzero < float(w)/float(n))] = 1

    # overlap step
    spTest._computeOverlapsFP(input, stimulusThreshold=spTest.stimulusThreshold)
    spTest._overlaps *= boostFactors
    onCellIndices = numpy.where(spTest._overlaps > 0)
    spTest._onCells.fill(0)
    spTest._onCells[onCellIndices] = 1
    denseOn = spTest._onCells

    # update _dutyCycleBeforeInh
    spTest.dutyCyclePeriod = min(i + 1, 1000)
    spTest._dutyCycleBeforeInh = ((spTest.dutyCyclePeriod-1) \
                    * spTest._dutyCycleBeforeInh + denseOn) / spTest.dutyCyclePeriod
    dutyCycleTieBreaker = spTest._dutyCycleAfterInh.copy()
    dutyCycleTieBreaker *= kDutyCycleFactor

    # inhibition step
    numOn = spTest._inhibitionObj.compute(spTest._overlaps + dutyCycleTieBreaker,
                                        spTest._onCellIndices,
                                        stimulusThresholdInh,  # stimulusThresholdInh
                                        max(spTest._overlaps)/1000,  # addToWinners
                                        )
    # update _dutyCycleAfterInh
    spTest._onCells.fill(0)
    onCellIndices = spTest._onCellIndices[0:numOn]
    spTest._onCells[onCellIndices] = 1
    denseOn = spTest._onCells
    spTest._dutyCycleAfterInh = ((spTest.dutyCyclePeriod-1) \
                    * spTest._dutyCycleAfterInh + denseOn) / spTest.dutyCyclePeriod

    # learning step
    spTest._adaptSynapses(onCellIndices, [], input)

    # update boostFactor
    spTest._updateBoostFactors()
    boostFactors = spTest._firingBoostFactors

    # update dutyCycle and boost
    if ((spTest._iterNum+1) % 50) == 0:
        spTest._updateInhibitionObj()
        spTest._updateMinDutyCycles(spTest._dutyCycleBeforeInh,
                              spTest.minPctDutyCycleBeforeInh, spTest._minDutyCycleBeforeInh)
        spTest._updateMinDutyCycles(spTest._dutyCycleAfterInh,
                              spTest.minPctDutyCycleAfterInh, spTest._minDutyCycleAfterInh)

    # test numOn and spTest.numActivePerInhArea
    success = checkResult(i, numOn, spTest.numActivePerInhArea)
    if not success:
      return
  print 'Inhibition Firing Number Test Passed with',testIter,'iterations.'

def checkResult(i, numOn, numActivePerInhArea):
  """ Compare the results and return True if success, False if failure

  Parameters:
  --------------------------------------------------------------------
  i:        iteration number
  success:
  numOn:                Actural firing number
  numActivePerInhArea:  Expected firing number
  """
  success = 1
  if numOn != numActivePerInhArea:
    success = 0
    print '\nError at input[',i,'], actual numOn are:', numOn, ', numActivePerInhArea is ', numActivePerInhArea
    raise RuntimeError("Test Failed")
  return success


def test():
  testInhibition(n=100, w=15, testIter=100, inputLen = 300)

################################################################################
if __name__=='__main__':

  # Run all tests
  test()