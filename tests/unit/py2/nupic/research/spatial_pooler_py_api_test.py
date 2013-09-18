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

from mock import Mock, patch, ANY, call
import numpy
import unittest2 as unittest

from nupic.research.spatial_pooler import SpatialPooler
from nupic.bindings.math import GetNTAReal

realType = GetNTAReal()
uintType = 'uint32'



class SpatialPoolerAPITest(unittest.TestCase):
  """Tests for SpatialPooler public API"""


  def testCompute(self):
    # Check that there are no errors in call to compute
    sp = SpatialPooler(columnDimensions=[5],inputDimensions=[5])
    inputVector = numpy.ones(5)
    activeArray = numpy.zeros(5)
    sp.compute(inputVector, True, activeArray)


  def testGetUpdatePeriod(self):
    sp = SpatialPooler(columnDimensions=[5],inputDimensions=[5])
    inParam = 1234
    sp.setUpdatePeriod(inParam)
    outParam = sp.getUpdatePeriod()
    self.assertEqual(inParam, outParam)


  def testGetPotentialRadius(self):
    sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])
    inParam = 56
    sp.setPotentialRadius(inParam)
    outParam = sp.getPotentialRadius()
    self.assertEqual(inParam, outParam)


  def testGetPotentialPct(self):
    sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])
    inParam = 0.4
    sp.setPotentialPct(inParam)
    outParam = sp.getPotentialPct()
    self.assertAlmostEqual(inParam, outParam)


  def testGetGlobalInhibition(self):
    sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])
    inParam = True 
    sp.setGlobalInhibition(inParam)
    outParam = sp.getGlobalInhibition()
    self.assertEqual(inParam, outParam)

    inParam = False
    sp.setGlobalInhibition(inParam)
    outParam = sp.getGlobalInhibition()
    self.assertEqual(inParam, outParam)


  def testGetNumActiveColumnsPerInhArea(self):
    sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])
    inParam = 7
    sp.setNumActiveColumnsPerInhArea(inParam)
    outParam = sp.getNumActiveColumnsPerInhArea()
    self.assertEqual(inParam, outParam)


  def testGetLocalAreaDensity(self):
    sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])
    inParam = 0.4
    sp.setLocalAreaDensity(inParam)
    outParam = sp.getLocalAreaDensity()
    self.assertAlmostEqual(inParam, outParam)


  def testGetStimulusThreshold(self):
    sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])
    inParam = 89
    sp.setStimulusThreshold(inParam)
    outParam = sp.getStimulusThreshold()
    self.assertEqual(inParam, outParam)


  def testGetInhibitionRadius(self):
    sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])
    inParam = 4
    sp.setInhibitionRadius(inParam)
    outParam = sp.getInhibitionRadius()
    self.assertEqual(inParam, outParam)


  def testGetDutyCyclePeriod(self):
    sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])
    inParam = 2020
    sp.setDutyCyclePeriod(inParam)
    outParam = sp.getDutyCyclePeriod()
    self.assertEqual(inParam, outParam)


  def testGetMaxBoost(self):
    sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])
    inParam = 78
    sp.setMaxBoost(inParam)
    outParam = sp.getMaxBoost()
    self.assertEqual(inParam, outParam)


  def testGetIterationNum(self):
    sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])
    inParam = 999
    sp.setIterationNum(inParam)
    outParam = sp.getIterationNum()
    self.assertEqual(inParam, outParam)


  def testGetIterationLearnNum(self):
    sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])
    inParam = 666
    sp.setIterationLearnNum(inParam)
    outParam = sp.getIterationLearnNum()
    self.assertEqual(inParam, outParam)


  def testGetSpVerbosity(self):
    sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])
    inParam = 2
    sp.setSpVerbosity(inParam)
    outParam = sp.getSpVerbosity()
    self.assertEqual(inParam, outParam)


  def testGetSynPermTrimThreshold(self):
    sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])
    inParam = 0.7
    sp.setSynPermTrimThreshold(inParam)
    outParam = sp.getSynPermTrimThreshold()
    self.assertAlmostEqual(inParam, outParam)


  def testGetSynPermActiveInc(self):
    sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])
    inParam = 0.567
    sp.setSynPermActiveInc(inParam)
    outParam = sp.getSynPermActiveInc()
    self.assertAlmostEqual(inParam, outParam)


  def testGetSynPermInactiveDec(self):
    sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])
    inParam = 0.123
    sp.setSynPermInactiveDec(inParam)
    outParam = sp.getSynPermInactiveDec()
    self.assertAlmostEqual(inParam, outParam)


  def testGetSynPermBelowStimulusInc(self):
    sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])
    inParam = 0.0898
    sp.setSynPermBelowStimulusInc(inParam)
    outParam = sp.getSynPermBelowStimulusInc()
    self.assertAlmostEqual(inParam, outParam)


  def testGetSynPermConnected(self):
    sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])
    inParam = 0.514
    sp.setSynPermConnected(inParam)
    outParam = sp.getSynPermConnected()
    self.assertAlmostEqual(inParam, outParam)


  def testGetMinPctOverlapDutyCycles(self):
    sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])
    inParam = 0.11122
    sp.setMinPctOverlapDutyCycles(inParam)
    outParam = sp.getMinPctOverlapDutyCycles()
    self.assertAlmostEqual(inParam, outParam)


  def testGetMinPctActiveDutyCycles(self):
    sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])
    inParam = 0.444333
    sp.setMinPctActiveDutyCycles(inParam)
    outParam = sp.getMinPctActiveDutyCycles()
    self.assertAlmostEqual(inParam, outParam)


  def testGetPermanence(self):
    sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])
    numInputs = 5
    numColumns = 5
    sp.initialize(columnDimensions=[numInputs], 
                  inputDimensions=[numColumns], 
                  potentialRadius=1, 
                  potentialPct=1)
    inParam = numpy.array(
      [0.06, 0.07, 0.08, 0.12, 0.13]).astype(realType)
    sp.setPermanence(0,inParam)
    outParam = numpy.zeros(numInputs).astype(realType)
    sp.getPermanence(0, outParam)
    self.assertListEqual(list(inParam),list(outParam))


  def testGetBoostFactors(self):
    sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])
    numInputs = 3
    numColumns = 3
    sp.initialize(columnDimensions=[numInputs], 
                  inputDimensions=[numColumns])
    inParam = numpy.array([1, 1.2, 1.3, ]).astype(realType)
    sp.setBoostFactors(inParam)
    outParam = numpy.zeros(numInputs).astype(realType)
    sp.getBoostFactors(outParam)
    self.assertListEqual(list(inParam),list(outParam))


  def testGetOverlapDutyCycles(self):
    sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])
    numInputs = 3
    numColumns = 3
    sp.initialize(columnDimensions=[numInputs], 
                  inputDimensions=[numColumns])
    inParam = numpy.array([0.9, 0.3, 0.1]).astype(realType)
    sp.setOverlapDutyCycles(inParam)
    outParam = numpy.zeros(numInputs).astype(realType)
    sp.getOverlapDutyCycles(outParam)
    self.assertListEqual(list(inParam),list(outParam))


  def testGetActiveDutyCycles(self):
    sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])
    numInputs = 3
    numColumns = 3
    sp.initialize(columnDimensions=[numInputs], 
                  inputDimensions=[numColumns])
    inParam = numpy.array([0.9, 0.99, 0.999, ]).astype(realType)
    sp.setActiveDutyCycles(inParam)
    outParam = numpy.zeros(numInputs).astype(realType)
    sp.getActiveDutyCycles(outParam)
    self.assertListEqual(list(inParam),list(outParam))


  def testGetMinOverlapDutyCycles(self):
    sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])
    numInputs = 3
    numColumns = 3
    sp.initialize(columnDimensions=[numInputs], 
                  inputDimensions=[numColumns])
    inParam = numpy.array([0.01, 0.02, 0.035, ]).astype(realType)
    sp.setMinOverlapDutyCycles(inParam)
    outParam = numpy.zeros(numInputs).astype(realType)
    sp.getMinOverlapDutyCycles(outParam)
    self.assertListEqual(list(inParam),list(outParam))


  def testGetMinActiveDutyCycles(self):
    sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])
    numInputs = 3
    numColumns = 3
    sp.initialize(columnDimensions=[numInputs], 
                  inputDimensions=[numColumns])
    inParam = numpy.array([0.01, 0.02, 0.035, ]).astype(realType)
    sp.setMinActiveDutyCycles(inParam)
    outParam = numpy.zeros(numInputs).astype(realType)
    sp.getMinActiveDutyCycles(outParam)
    self.assertListEqual(list(inParam),list(outParam))


  def testGetPotential(self):
    sp = SpatialPooler(columnDimensions=[3], inputDimensions=[3])
    numInputs = 3
    numColumns = 3
    sp.initialize(columnDimensions=[numInputs], 
                   inputDimensions=[numColumns])
    inParam1 = numpy.array([1, 0, 1]).astype(uintType)
    sp.setPotential(0, inParam1)
    inParam2 = numpy.array([1, 1, 0]).astype(uintType)
    sp.setPotential(1, inParam2)

    outParam1 = numpy.zeros(numInputs).astype(uintType)
    outParam2 = numpy.zeros(numInputs).astype(uintType)
    sp.getPotential(0, outParam1)
    sp.getPotential(1, outParam2)

    self.assertListEqual(list(inParam1),list(outParam1))
    self.assertListEqual(list(inParam2),list(outParam2))


  def testGetConnectedSynapses(self):
    sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])
    numInputs = 5
    numColumns = 5
    sp.initialize(columnDimensions=[numInputs], 
                  inputDimensions=[numColumns], 
                  potentialRadius=1, 
                  potentialPct=1)
    inParam = numpy.array(
      [0.06, 0.07, 0.08, 0.12, 0.13]).astype(realType)
    trueConnected = numpy.array([0, 0, 0, 1, 1])
    sp.setSynPermConnected(0.1)
    sp.setPermanence(0,inParam)
    outParam = numpy.zeros(numInputs).astype(uintType)
    sp.getConnectedSynapses(0, outParam)
    self.assertListEqual(list(trueConnected),list(outParam))


  def testGetConnectedCounts(self):
    sp = SpatialPooler(columnDimensions=[5], inputDimensions=[5])
    numInputs = 5
    numColumns = 5
    sp.initialize(columnDimensions=[numInputs], 
                  inputDimensions=[numColumns], 
                  potentialRadius=1, 
                  potentialPct=1)
    inParam = numpy.array(
      [0.06, 0.07, 0.08, 0.12, 0.11]).astype(realType)
    trueConnectedCount = 2
    sp.setSynPermConnected(0.1)
    sp.setPermanence(0,inParam)
    outParam = numpy.zeros(numInputs).astype(uintType)
    sp.getConnectedCounts(outParam)
    self.assertEqual(trueConnectedCount,outParam[0])



if __name__ == "__main__":
  unittest.main()
