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
Test if the firing number of coincidences after inhibition equals spatial pooler
numActiveColumnsPerInhArea.

TODO: Fix this up to be more unit testy.
"""

import numpy

import unittest2 as unittest

from nupic.research.spatial_pooler import SpatialPooler

numpy.random.seed(100)



class InhibitionObjectTest(unittest.TestCase):

  @unittest.skip("Currently fails due to switch from FDRCSpatial2 to SpatialPooler."
                 "The new SP doesn't have explicit methods to get inhibition.")
  # TODO: See https://github.com/numenta/nupic/issues/2071
  def testInhibition(self):
    """
    Test if the firing number of coincidences after inhibition
    equals spatial pooler numActiveColumnsPerInhArea.
    """
    # Miscellaneous variables:
    # n, w:                 n, w of encoders
    # inputLen:             Length of binary input
    # synPermConnected:     Spatial pooler synPermConnected
    # synPermActiveInc:     Spatial pooler synPermActiveInc
    # connectPct:           Initial connect percentage of permanences
    # columnDimensions:     Number of spatial pooler coincidences
    # numActiveColumnsPerInhArea:  Spatial pooler numActiveColumnsPerInhArea
    # stimulusThreshold:    Spatial pooler stimulusThreshold
    # spSeed:               Spatial pooler for initial permanences
    # stimulusThresholdInh: Parameter for inhibition, default value 0.00001
    # kDutyCycleFactor:     kDutyCycleFactor for dutyCycleTieBreaker in
    #                       Inhibition
    # spVerbosity:          Verbosity to print other sp initial parameters
    # testIter:             Testing iterations
    n = 100
    w = 15
    inputLen = 300
    columnDimensions = 2048
    numActiveColumnsPerInhArea = 40
    stimulusThreshold = 0
    spSeed = 1956
    stimulusThresholdInh = 0.00001
    kDutyCycleFactor = 0.01
    spVerbosity = 0
    testIter = 100

    spTest = SpatialPooler(
                           columnDimensions=(columnDimensions, 1),
                           inputDimensions=(1, inputLen),
                           potentialRadius=inputLen / 2,
                           numActiveColumnsPerInhArea=numActiveColumnsPerInhArea,
                           spVerbosity=spVerbosity,
                           stimulusThreshold=stimulusThreshold,
                           seed=spSeed
                           )
    initialPermanence = spTest._initialPermanence()
    spTest._masterPotentialM, spTest._masterPermanenceM = (
        spTest._makeMasterCoincidences(spTest.numCloneMasters,
                                       spTest._coincRFShape,
                                       spTest.potentialPct,
                                       initialPermanence,
                                       spTest.random))

    spTest._updateInhibitionObj()
    boostFactors = numpy.ones(columnDimensions)

    for i in range(testIter):
      spTest._iterNum = i
      # random binary input
      input_ = numpy.zeros((1, inputLen))
      nonzero = numpy.random.random(inputLen)
      input_[0][numpy.where (nonzero < float(w)/float(n))] = 1

      # overlap step
      spTest._computeOverlapsFP(input_,
                                stimulusThreshold=spTest.stimulusThreshold)
      spTest._overlaps *= boostFactors
      onCellIndices = numpy.where(spTest._overlaps > 0)
      spTest._onCells.fill(0)
      spTest._onCells[onCellIndices] = 1
      denseOn = spTest._onCells

      # update _dutyCycleBeforeInh
      spTest.dutyCyclePeriod = min(i + 1, 1000)
      spTest._dutyCycleBeforeInh = (
          (spTest.dutyCyclePeriod - 1) *
          spTest._dutyCycleBeforeInh +denseOn) / spTest.dutyCyclePeriod
      dutyCycleTieBreaker = spTest._dutyCycleAfterInh.copy()
      dutyCycleTieBreaker *= kDutyCycleFactor

      # inhibition step
      numOn = spTest._inhibitionObj.compute(
          spTest._overlaps + dutyCycleTieBreaker, spTest._onCellIndices,
          stimulusThresholdInh,  # stimulusThresholdInh
          max(spTest._overlaps)/1000,  # addToWinners
      )
      # update _dutyCycleAfterInh
      spTest._onCells.fill(0)
      onCellIndices = spTest._onCellIndices[0:numOn]
      spTest._onCells[onCellIndices] = 1
      denseOn = spTest._onCells
      spTest._dutyCycleAfterInh = (((spTest.dutyCyclePeriod-1) *
                                    spTest._dutyCycleAfterInh + denseOn) /
                                   spTest.dutyCyclePeriod)

      # learning step
      spTest._adaptSynapses(onCellIndices, [], input_)

      # update boostFactor
      spTest._updateBoostFactors()
      boostFactors = spTest._firingBoostFactors

      # update dutyCycle and boost
      if ((spTest._iterNum+1) % 50) == 0:
        spTest._updateInhibitionObj()
        spTest._updateMinDutyCycles(
            spTest._dutyCycleBeforeInh,
            spTest.minPctDutyCycleBeforeInh,
            spTest._minDutyCycleBeforeInh)
        spTest._updateMinDutyCycles(
            spTest._dutyCycleAfterInh,
            spTest.minPctDutyCycleAfterInh,
            spTest._minDutyCycleAfterInh)

      # test numOn and spTest.numActiveColumnsPerInhArea
      self.assertEqual(numOn, spTest.numActiveColumnsPerInhArea,
                       "Error at input %s, actual numOn are: %i, "
                       "numActivePerInhAre is: %s" % (
                           i, numOn, numActiveColumnsPerInhArea))



if __name__=="__main__":
  unittest.main()
