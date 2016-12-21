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

from mock import Mock, patch, ANY, call
import numpy
import cPickle as pickle
import unittest2 as unittest

from nupic.bindings.math import GetNTAReal
from nupic.bindings.algorithms import SpatialPooler

realType = GetNTAReal()
uintType = "uint32"



class SpatialPoolerAPITest(unittest.TestCase):
  """Tests for SpatialPooler public API"""


  def setUp(self):
    self.sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])


  def testCompute(self):
    # Check that there are no errors in call to compute
    inputVector = numpy.ones(5)
    activeArray = numpy.zeros(5)
    self.sp.compute(inputVector, True, activeArray)


  def testGetUpdatePeriod(self):
    inParam = 1234
    self.sp.setUpdatePeriod(inParam)
    outParam = self.sp.getUpdatePeriod()
    self.assertEqual(inParam, outParam)


  def testGetPotentialRadius(self):
    inParam = 56
    self.sp.setPotentialRadius(inParam)
    outParam = self.sp.getPotentialRadius()
    self.assertEqual(inParam, outParam)


  def testGetPotentialPct(self):
    inParam = 0.4
    self.sp.setPotentialPct(inParam)
    outParam = self.sp.getPotentialPct()
    self.assertAlmostEqual(inParam, outParam)


  def testGetGlobalInhibition(self):
    inParam = True
    self.sp.setGlobalInhibition(inParam)
    outParam = self.sp.getGlobalInhibition()
    self.assertEqual(inParam, outParam)

    inParam = False
    self.sp.setGlobalInhibition(inParam)
    outParam = self.sp.getGlobalInhibition()
    self.assertEqual(inParam, outParam)


  def testGetNumActiveColumnsPerInhArea(self):
    inParam = 7
    self.sp.setNumActiveColumnsPerInhArea(inParam)
    outParam = self.sp.getNumActiveColumnsPerInhArea()
    self.assertEqual(inParam, outParam)


  def testGetLocalAreaDensity(self):
    inParam = 0.4
    self.sp.setLocalAreaDensity(inParam)
    outParam = self.sp.getLocalAreaDensity()
    self.assertAlmostEqual(inParam, outParam)


  def testGetStimulusThreshold(self):
    inParam = 89
    self.sp.setStimulusThreshold(inParam)
    outParam = self.sp.getStimulusThreshold()
    self.assertEqual(inParam, outParam)


  def testGetInhibitionRadius(self):
    inParam = 4
    self.sp.setInhibitionRadius(inParam)
    outParam = self.sp.getInhibitionRadius()
    self.assertEqual(inParam, outParam)


  def testGetDutyCyclePeriod(self):
    inParam = 2020
    self.sp.setDutyCyclePeriod(inParam)
    outParam = self.sp.getDutyCyclePeriod()
    self.assertEqual(inParam, outParam)


  def testGetBoostStrength(self):
    inParam = 78
    self.sp.setBoostStrength(inParam)
    outParam = self.sp.getBoostStrength()
    self.assertEqual(inParam, outParam)


  def testGetIterationNum(self):
    inParam = 999
    self.sp.setIterationNum(inParam)
    outParam = self.sp.getIterationNum()
    self.assertEqual(inParam, outParam)


  def testGetIterationLearnNum(self):
    inParam = 666
    self.sp.setIterationLearnNum(inParam)
    outParam = self.sp.getIterationLearnNum()
    self.assertEqual(inParam, outParam)


  def testGetSpVerbosity(self):
    inParam = 2
    self.sp.setSpVerbosity(inParam)
    outParam = self.sp.getSpVerbosity()
    self.assertEqual(inParam, outParam)


  def testGetSynPermTrimThreshold(self):
    inParam = 0.7
    self.sp.setSynPermTrimThreshold(inParam)
    outParam = self.sp.getSynPermTrimThreshold()
    self.assertAlmostEqual(inParam, outParam)


  def testGetSynPermActiveInc(self):
    inParam = 0.567
    self.sp.setSynPermActiveInc(inParam)
    outParam = self.sp.getSynPermActiveInc()
    self.assertAlmostEqual(inParam, outParam)


  def testGetSynPermInactiveDec(self):
    inParam = 0.123
    self.sp.setSynPermInactiveDec(inParam)
    outParam = self.sp.getSynPermInactiveDec()
    self.assertAlmostEqual(inParam, outParam)


  def testGetSynPermBelowStimulusInc(self):
    inParam = 0.0898
    self.sp.setSynPermBelowStimulusInc(inParam)
    outParam = self.sp.getSynPermBelowStimulusInc()
    self.assertAlmostEqual(inParam, outParam)


  def testGetSynPermConnected(self):
    inParam = 0.514
    self.sp.setSynPermConnected(inParam)
    outParam = self.sp.getSynPermConnected()
    self.assertAlmostEqual(inParam, outParam)


  def testGetMinPctOverlapDutyCycles(self):
    inParam = 0.11122
    self.sp.setMinPctOverlapDutyCycles(inParam)
    outParam = self.sp.getMinPctOverlapDutyCycles()
    self.assertAlmostEqual(inParam, outParam)


  def testGetPermanence(self):
    numInputs = 5
    numColumns = 5
    self.sp.initialize(columnDimensions=[numInputs], 
                       inputDimensions=[numColumns], 
                       potentialRadius=1, 
                       potentialPct=1)
    inParam = numpy.array(
      [0.06, 0.07, 0.08, 0.12, 0.13]).astype(realType)
    self.sp.setPermanence(0,inParam)
    outParam = numpy.zeros(numInputs).astype(realType)
    self.sp.getPermanence(0, outParam)
    self.assertListEqual(list(inParam),list(outParam))


  def testGetBoostFactors(self):
    numInputs = 3
    numColumns = 3
    self.sp.initialize(columnDimensions=[numInputs], 
                       inputDimensions=[numColumns])
    inParam = numpy.array([1, 1.2, 1.3, ]).astype(realType)
    self.sp.setBoostFactors(inParam)
    outParam = numpy.zeros(numInputs).astype(realType)
    self.sp.getBoostFactors(outParam)
    self.assertListEqual(list(inParam),list(outParam))


  def testGetOverlapDutyCycles(self):
    numInputs = 3
    numColumns = 3
    self.sp.initialize(columnDimensions=[numInputs], 
                       inputDimensions=[numColumns])
    inParam = numpy.array([0.9, 0.3, 0.1]).astype(realType)
    self.sp.setOverlapDutyCycles(inParam)
    outParam = numpy.zeros(numInputs).astype(realType)
    self.sp.getOverlapDutyCycles(outParam)
    self.assertListEqual(list(inParam),list(outParam))


  def testGetActiveDutyCycles(self):
    numInputs = 3
    numColumns = 3
    self.sp.initialize(columnDimensions=[numInputs], 
                       inputDimensions=[numColumns])
    inParam = numpy.array([0.9, 0.99, 0.999, ]).astype(realType)
    self.sp.setActiveDutyCycles(inParam)
    outParam = numpy.zeros(numInputs).astype(realType)
    self.sp.getActiveDutyCycles(outParam)
    self.assertListEqual(list(inParam),list(outParam))


  def testGetMinOverlapDutyCycles(self):
    numInputs = 3
    numColumns = 3
    self.sp.initialize(columnDimensions=[numInputs], 
                       inputDimensions=[numColumns])
    inParam = numpy.array([0.01, 0.02, 0.035, ]).astype(realType)
    self.sp.setMinOverlapDutyCycles(inParam)
    outParam = numpy.zeros(numInputs).astype(realType)
    self.sp.getMinOverlapDutyCycles(outParam)
    self.assertListEqual(list(inParam),list(outParam))


  def testGetPotential(self):
    self.sp.initialize(columnDimensions=[3], inputDimensions=[3])
    numInputs = 3
    numColumns = 3
    self.sp.initialize(columnDimensions=[numInputs], 
                       inputDimensions=[numColumns])
    inParam1 = numpy.array([1, 0, 1]).astype(uintType)
    self.sp.setPotential(0, inParam1)
    inParam2 = numpy.array([1, 1, 0]).astype(uintType)
    self.sp.setPotential(1, inParam2)

    outParam1 = numpy.zeros(numInputs).astype(uintType)
    outParam2 = numpy.zeros(numInputs).astype(uintType)
    self.sp.getPotential(0, outParam1)
    self.sp.getPotential(1, outParam2)

    self.assertListEqual(list(inParam1),list(outParam1))
    self.assertListEqual(list(inParam2),list(outParam2))


  def testGetConnectedSynapses(self):
    numInputs = 5
    numColumns = 5
    self.sp.initialize(columnDimensions=[numInputs], 
                       inputDimensions=[numColumns], 
                       potentialRadius=1, 
                       potentialPct=1)
    inParam = numpy.array(
      [0.06, 0.07, 0.08, 0.12, 0.13]).astype(realType)
    trueConnected = numpy.array([0, 0, 0, 1, 1])
    self.sp.setSynPermConnected(0.1)
    self.sp.setPermanence(0,inParam)
    outParam = numpy.zeros(numInputs).astype(uintType)
    self.sp.getConnectedSynapses(0, outParam)
    self.assertListEqual(list(trueConnected),list(outParam))


  def testGetConnectedCounts(self):
    numInputs = 5
    numColumns = 5
    self.sp.initialize(columnDimensions=[numInputs], 
                       inputDimensions=[numColumns], 
                       potentialRadius=1, 
                       potentialPct=1)
    inParam = numpy.array(
      [0.06, 0.07, 0.08, 0.12, 0.11]).astype(realType)
    trueConnectedCount = 2
    self.sp.setSynPermConnected(0.1)
    self.sp.setPermanence(0, inParam)
    outParam = numpy.zeros(numInputs).astype(uintType)
    self.sp.getConnectedCounts(outParam)
    self.assertEqual(trueConnectedCount, outParam[0])


  def assertListAlmostEqual(self, alist, blist):
    self.assertEqual(len(alist), len(blist))
    for (a,b) in zip(alist,blist):
      diff = abs(a - b)
      self.assertLess(diff,1e-5)



if __name__ == "__main__":
  unittest.main()
