#! /usr/bin/env python

import numpy
import unittest
import sys

from nupic.bindings.math import GetNTAReal
from nupic.research.FDRCSpatial2 import FDRCSpatial2 as SpatialPooler

realDType = GetNTAReal()

class SPOutputTestCase(unittest.TestCase):
  
  def testExactSPOutput(self):
    '''
    Given a specific input and initialization params the SP should return this
    exact output.
    
    This test replicates mer-960 where the output differed between OSX and Linux
    '''
    
    print "Float: ", sys.float_info
    print "Flags: ", sys.flags
    print "Version: ", sys.version
    print "Platform: ", sys.platform
    
    expectedOutput = [65, 155, 188, 221, 284, 314, 315, 332, 385, 450, 495, 546, 551, 569, 599, 651, 824, 884, 947, 966, 971, 1002, 1073, 1118, 1230, 1270, 1279, 1285, 1321, 1390, 1407, 1459, 1497, 1546, 1661, 1722, 1746, 1891, 1915, 1989]

    sp = SpatialPooler(            
                inputShape = (1, 188),
                inputBorder = 93,
                inputDensity = 1.0,
                coincidencesShape = (2048, 1),
                coincInputRadius = 94,
                coincInputPoolPct = 0.5,
                gaussianDist = False,
                commonDistributions = False,
                localAreaDensity = -1.0,
                numActivePerInhArea = 40.0,
                stimulusThreshold = 0,
                synPermInactiveDec = 0.01,
                synPermActiveInc = 0.1,
                synPermActiveSharedDec = 0.0,
                synPermOrphanDec = 0.0,
                synPermConnected = 0.1,
                minPctDutyCycleBeforeInh = 0.001,
                minPctDutyCycleAfterInh = 0.001,
                dutyCyclePeriod = 1000,
                maxFiringBoost = 10.0,
                maxSSFiringBoost = 2.0,
                maxSynPermBoost = 10.0,
                minDistance = 0.0,
                spVerbosity = 0,
                printPeriodicStats = 0,
                testMode = False,
                numCloneMasters = 2048,
                globalInhibition = 1,
                useHighTier = True,
                randomSP =  True,
                seed = 1956)
    

    inputVector = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    inputArray = numpy.array(inputVector).astype(realDType)
    
    sp.compute(inputArray, 1, 1)
    
    spOutput = [v for v in sp._onCellIndices if v != 0]
    self.assertEqual(spOutput, expectedOutput)
    
if __name__ == '__main__':
  unittest.main()