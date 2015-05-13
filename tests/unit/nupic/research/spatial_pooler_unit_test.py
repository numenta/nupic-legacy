#! /usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
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

# Disable since test code accesses private members in the class to be tested
# pylint: disable=W0212

import numbers
import tempfile
import unittest
from copy import copy

import capnp
from mock import Mock
import numpy

from nupic.support.unittesthelpers.algorithm_test_helpers import (
  getNumpyRandomGenerator, getSeed)
from nupic.bindings.math import (SM_01_32_32 as SparseBinaryMatrix,
                                 SM32 as SparseMatrix,
                                 GetNTAReal,
                                 Random)
from nupic.bindings.proto import SpatialPoolerProto_capnp
from nupic.research.spatial_pooler import SpatialPooler

uintDType = "uint32"
realDType = GetNTAReal()

class SpatialPoolerTest(unittest.TestCase):
  """Unit Tests for SpatialPooler class."""


  def setUp(self):

    self._params = {
      "inputDimensions": [5],
      "columnDimensions": [5],
      "potentialRadius": 5,
      "potentialPct": 0.5,
      "globalInhibition": False,
      "localAreaDensity": -1.0,
      "numActiveColumnsPerInhArea": 3,
      "stimulusThreshold": 0,
      "synPermInactiveDec": 0.01,
      "synPermActiveInc": 0.1,
      "synPermConnected": 0.10,
      "minPctOverlapDutyCycle": 0.1,
      "minPctActiveDutyCycle": 0.1,
      "dutyCyclePeriod": 10,
      "maxBoost": 10.0,
      "seed": getSeed(),
      "spVerbosity": 0
    }

    self._sp = SpatialPooler(**self._params)


  def testCompute1(self):
    """Checks that feeding in the same input vector leads to polarized
    permanence values: either zeros or ones, but no fractions"""

    sp = SpatialPooler(
        inputDimensions=[9],
        columnDimensions=[5],
        potentialRadius=3,
        potentialPct=0.5,
        globalInhibition=False,
        localAreaDensity=-1.0,
        numActiveColumnsPerInhArea=3,
        stimulusThreshold=1,
        synPermInactiveDec=0.01,
        synPermActiveInc=0.1,
        synPermConnected=0.10,
        minPctOverlapDutyCycle=0.1,
        minPctActiveDutyCycle=0.1,
        dutyCyclePeriod=10,
        maxBoost=10.0,
        seed=getSeed(),
        spVerbosity=0)

    sp._potentialPools = SparseBinaryMatrix(
      numpy.ones([sp._numColumns, sp._numInputs]))
    sp._inhibitColumns = Mock(return_value = numpy.array(range(5)))

    inputVector = numpy.array([1, 0, 1, 0, 1, 0, 0, 1, 1])
    activeArray = numpy.zeros(5)
    for i in xrange(20):
      sp.compute(inputVector, True, activeArray)

    for i in xrange(sp._numColumns):
      perm = sp._permanences.getRow(i)
      self.assertEqual(list(perm), list(inputVector))


  def testCompute2(self):
    """Checks that columns only change the permanence values for 
       inputs that are within their potential pool"""

    sp = SpatialPooler(
        inputDimensions=[10],
        columnDimensions=[5],
        potentialRadius=3,
        potentialPct=0.5,
        globalInhibition=False,
        localAreaDensity=-1.0,
        numActiveColumnsPerInhArea=3,
        stimulusThreshold=1,
        synPermInactiveDec=0.01,
        synPermActiveInc=0.1,
        synPermConnected=0.10,
        minPctOverlapDutyCycle=0.1,
        minPctActiveDutyCycle=0.1,
        dutyCyclePeriod=10,
        maxBoost=10.0,
        seed=getSeed(),
        spVerbosity=0)

    sp._inhibitColumns = Mock(return_value = numpy.array(range(5)))

    inputVector = numpy.ones(sp._numInputs)
    activeArray = numpy.zeros(5)
    for i in xrange(20):
      sp.compute(inputVector, True, activeArray)

    for i in xrange(sp._numColumns):
      potential = sp._potentialPools.getRow(i)
      perm = sp._permanences.getRow(i)
      self.assertEqual(list(perm), list(potential))


  def testExactOutput(self):
    """
    Given a specific input and initialization params the SP should return this
    exact output.

    Previously output varied between platforms (OSX/Linux etc)
    """

    expectedOutput = [32, 223, 295, 307, 336, 381, 385, 428, 498, 543, 624,
                      672, 687, 731, 733, 751, 760, 790, 791, 797, 860, 955,
                      1024, 1037, 1184, 1303, 1347, 1454, 1475, 1483, 1494,
                      1497, 1580, 1671, 1701, 1774, 1787, 1830, 1868, 1878]

    sp = SpatialPooler(
      inputDimensions = [1,188],
      columnDimensions = [2048, 1],
      potentialRadius = 94,
      potentialPct = 0.5,
      globalInhibition = 1,
      localAreaDensity = -1.0,
      numActiveColumnsPerInhArea = 40.0,
      stimulusThreshold = 0,
      synPermInactiveDec = 0.01,
      synPermActiveInc = 0.1,
      synPermConnected = 0.1,
      minPctOverlapDutyCycle=0.001,
      minPctActiveDutyCycle=0.001,
      dutyCyclePeriod = 1000,
      maxBoost = 10.0,
      seed = 1956,
      spVerbosity = 0
      
    )
    

    inputVector = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0,
                   1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0,
                   1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                   1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0,
                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    
    inputArray = numpy.array(inputVector).astype(realDType)
    
    activeArray = numpy.zeros(2048)
    
    sp.compute(inputArray, 1, activeArray)
    
    # Get only the active column indices
    spOutput = [i for i, v in enumerate(activeArray) if v != 0]
    self.assertEqual(spOutput, expectedOutput)


  def testStripNeverLearned(self):
    sp = self._sp
    
    sp._activeDutyCycles = numpy.array([0.5, 0.1, 0, 0.2, 0.4, 0])
    activeColumns = numpy.array([0, 1, 2, 4])
    stripped = sp.stripUnlearnedColumns(activeColumns)
    trueStripped = [0, 1, 4]
    self.assertListEqual(trueStripped, list(stripped))

    sp._activeDutyCycles = numpy.array([0.9, 0, 0, 0, 0.4, 0.3])
    activeColumns = numpy.array(range(6))
    stripped = sp.stripUnlearnedColumns(activeColumns)
    trueStripped = [0, 4, 5]
    self.assertListEqual(trueStripped, list(stripped))

    sp._activeDutyCycles = numpy.array([0, 0, 0, 0, 0, 0])
    activeColumns = numpy.array(range(6))
    stripped = sp.stripUnlearnedColumns(activeColumns)
    trueStripped = []
    self.assertListEqual(trueStripped, list(stripped))

    sp._activeDutyCycles = numpy.ones(6)
    activeColumns = numpy.array(range(6))
    stripped = sp.stripUnlearnedColumns(activeColumns)
    trueStripped = range(6)
    self.assertListEqual(trueStripped, list(stripped))


  def testMapColumn(self):
    params = self._params.copy()

    # Test 1D
    params.update({
      "columnDimensions": [4],
      "inputDimensions": [12]
    })
    sp = SpatialPooler(**params)

    self.assertEqual(sp._mapColumn(0), 1)
    self.assertEqual(sp._mapColumn(1), 4)
    self.assertEqual(sp._mapColumn(2), 7)
    self.assertEqual(sp._mapColumn(3), 10)

    # Test 1D with same dimensions of columns and inputs
    params.update({
      "columnDimensions": [4],
      "inputDimensions": [4]
    })
    sp = SpatialPooler(**params)

    self.assertEqual(sp._mapColumn(0), 0)
    self.assertEqual(sp._mapColumn(1), 1)
    self.assertEqual(sp._mapColumn(2), 2)
    self.assertEqual(sp._mapColumn(3), 3)

    # Test 1D with dimensions of length 1
    params.update({
      "columnDimensions": [1],
      "inputDimensions": [1]
    })
    sp = SpatialPooler(**params)

    self.assertEqual(sp._mapColumn(0), 0)

    # Test 2D
    params.update({
      "columnDimensions": [12, 4],
      "inputDimensions": [36, 12]
    })
    sp = SpatialPooler(**params)

    self.assertEqual(sp._mapColumn(0), 13)
    self.assertEqual(sp._mapColumn(4), 49)
    self.assertEqual(sp._mapColumn(5), 52)
    self.assertEqual(sp._mapColumn(7), 58)
    self.assertEqual(sp._mapColumn(47), 418)


  def testMapPotential1D(self):
    params = self._params.copy()
    params.update({
      "inputDimensions": [12],
      "columnDimensions": [4],
      "potentialRadius": 2
    })

    # Test without wrapAround and potentialPct = 1
    params["potentialPct"] = 1
    sp = SpatialPooler(**params)

    expectedMask = [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0]
    mask = sp._mapPotential(0, wrapAround=False)
    self.assertListEqual(mask.tolist(), expectedMask)

    expectedMask = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0]
    mask = sp._mapPotential(2, wrapAround=False)
    self.assertListEqual(mask.tolist(), expectedMask)

    # Test with wrapAround and potentialPct = 1
    params["potentialPct"] = 1
    sp = SpatialPooler(**params)

    expectedMask = [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1]
    mask = sp._mapPotential(0, wrapAround=True)
    self.assertListEqual(mask.tolist(), expectedMask)

    expectedMask = [1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1]
    mask = sp._mapPotential(3, wrapAround=True)
    self.assertListEqual(mask.tolist(), expectedMask)

    # Test with potentialPct < 1
    params["potentialPct"] = 0.5
    sp = SpatialPooler(**params)

    supersetMask = numpy.array([1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1])
    mask = sp._mapPotential(0, wrapAround=True)
    self.assertEqual(numpy.sum(mask), 3)
    unionMask = supersetMask | mask.astype(int)
    self.assertListEqual(unionMask.tolist(), supersetMask.tolist())


  def testMapPotential2D(self):
    params = self._params.copy()
    params.update({
      "columnDimensions": [2, 4],
      "inputDimensions": [6, 12],
      "potentialRadius": 1,
      "potentialPct": 1
    })

    # Test without wrapAround
    sp = SpatialPooler(**params)

    trueIndicies = [0, 12, 24,
                    1, 13, 25,
                    2, 14, 26]
    mask = sp._mapPotential(0, wrapAround=False)
    self.assertSetEqual(set(numpy.flatnonzero(mask).tolist()), set(trueIndicies))

    trueIndicies = [6, 18, 30,
                    7, 19, 31,
                    8, 20, 32]
    mask = sp._mapPotential(2, wrapAround=False)
    self.assertSetEqual(set(numpy.flatnonzero(mask).tolist()), set(trueIndicies))

    # Test with wrapAround
    params.update({
      "potentialRadius": 2,
    })
    sp = SpatialPooler(**params)

    trueIndicies = [71, 11, 23, 35, 47,
                    60,  0, 12, 24, 36,
                    61,  1, 13, 25, 37,
                    62,  2, 14, 26, 38,
                    63,  3, 15, 27, 39]
    mask = sp._mapPotential(0, wrapAround=True)
    self.assertSetEqual(set(numpy.flatnonzero(mask).tolist()), set(trueIndicies))

    trueIndicies = [68,  8, 20, 32, 44,
                    69,  9, 21, 33, 45,
                    70, 10, 22, 34, 46,
                    71, 11, 23, 35, 47,
                    60,  0, 12, 24, 36]
    mask = sp._mapPotential(3, wrapAround=True)
    self.assertSetEqual(set(numpy.flatnonzero(mask).tolist()), set(trueIndicies))


  def testMapPotential1Column1Input(self):
    params = self._params.copy()
    params.update({
      "inputDimensions": [1],
      "columnDimensions": [1],
      "potentialRadius": 2
    })

    # Test without wrapAround and potentialPct = 1
    params["potentialPct"] = 1
    sp = SpatialPooler(**params)

    expectedMask = [1]
    mask = sp._mapPotential(0, wrapAround=False)
    self.assertListEqual(mask.tolist(), expectedMask)


  def testInhibitColumns(self):
    sp = self._sp
    sp._inhibitColumnsGlobal = Mock(return_value = 1)
    sp._inhibitColumnsLocal = Mock(return_value = 2)
    randomState = getNumpyRandomGenerator()
    sp._numColumns = 5
    sp._inhibitionRadius = 10
    sp._columnDimensions = [5]
    overlaps = randomState.random_sample(sp._numColumns)

    sp._inhibitColumnsGlobal.reset_mock()
    sp._inhibitColumnsLocal.reset_mock()
    sp._numActiveColumnsPerInhArea = 5
    sp._localAreaDensity = 0.1
    sp._globalInhibition = True
    sp._inhibitionRadius = 5
    trueDensity = sp._localAreaDensity
    sp._inhibitColumns(overlaps)
    self.assertEqual(True, sp._inhibitColumnsGlobal.called)
    self.assertEqual(False, sp._inhibitColumnsLocal.called)
    density = sp._inhibitColumnsGlobal.call_args[0][1]
    self.assertEqual(trueDensity, density)

    sp._inhibitColumnsGlobal.reset_mock()
    sp._inhibitColumnsLocal.reset_mock()
    sp._numColumns = 500
    sp._tieBreaker = numpy.zeros(500)
    sp._columnDimensions = numpy.array([50, 10])
    sp._numActiveColumnsPerInhArea = -1
    sp._localAreaDensity = 0.1
    sp._globalInhibition = False
    sp._inhibitionRadius = 7
    # 0.1 * (2*9+1)**2 = 22.5
    trueDensity = sp._localAreaDensity
    overlaps = randomState.random_sample(sp._numColumns)
    sp._inhibitColumns(overlaps)
    self.assertEqual(False, sp._inhibitColumnsGlobal.called)
    self.assertEqual(True, sp._inhibitColumnsLocal.called)    
    self.assertEqual(trueDensity, density)

    # Test translation of numColumnsPerInhArea into local area density
    sp._numColumns = 1000
    sp._tieBreaker = numpy.zeros(1000)
    sp._columnDimensions = numpy.array([100, 10])
    sp._inhibitColumnsGlobal.reset_mock()
    sp._inhibitColumnsLocal.reset_mock()
    sp._numActiveColumnsPerInhArea = 3
    sp._localAreaDensity = -1
    sp._globalInhibition = False
    sp._inhibitionRadius = 4
    trueDensity = 3.0/81.0
    overlaps = randomState.random_sample(sp._numColumns)
    # 3.0 / (((2*4) + 1) ** 2)
    sp._inhibitColumns(overlaps)
    self.assertEqual(False, sp._inhibitColumnsGlobal.called)
    self.assertEqual(True, sp._inhibitColumnsLocal.called)
    density = sp._inhibitColumnsLocal.call_args[0][1]
    self.assertEqual(trueDensity, density)


    # Test clipping of local area density to 0.5
    sp._numColumns = 1000
    sp._tieBreaker = numpy.zeros(1000)
    sp._columnDimensions = numpy.array([100, 10])
    sp._inhibitColumnsGlobal.reset_mock()
    sp._inhibitColumnsLocal.reset_mock()
    sp._numActiveColumnsPerInhArea = 7
    sp._localAreaDensity = -1
    sp._globalInhibition = False
    sp._inhibitionRadius = 1
    trueDensity = 0.5
    overlaps = randomState.random_sample(sp._numColumns)
    sp._inhibitColumns(overlaps)
    self.assertEqual(False, sp._inhibitColumnsGlobal.called)
    self.assertEqual(True, sp._inhibitColumnsLocal.called)
    density = sp._inhibitColumnsLocal.call_args[0][1]
    self.assertEqual(trueDensity, density)


  def testUpdateBoostFactors(self):
    sp = self._sp
    sp._maxBoost = 10.0
    sp._numColumns = 6
    sp._minActiveDutyCycles = numpy.zeros(sp._numColumns) + 1e-6
    sp._activeDutyCycles = numpy.array([0.1, 0.3, 0.02, 0.04, 0.7, 0.12])
    sp._boostFactors = numpy.zeros(sp._numColumns)
    trueBoostFactors = [1, 1, 1, 1, 1, 1]
    sp._updateBoostFactors()
    for i in range(sp._boostFactors.size):
      self.assertAlmostEqual(trueBoostFactors[i], sp._boostFactors[i])

    sp._maxBoost = 10.0
    sp._numColumns = 6
    sp._minActiveDutyCycles = numpy.array([0.1, 0.3, 0.02, 0.04, 0.7, 0.12])
    sp._activeDutyCycles = numpy.array([0.1, 0.3, 0.02, 0.04, 0.7, 0.12])
    trueBoostFactors = [1, 1, 1, 1, 1, 1]
    sp._updateBoostFactors()
    for i in range(sp._boostFactors.size):
      self.assertLessEqual(abs(trueBoostFactors[i] - sp._boostFactors[i]), 1e-6)

    sp._maxBoost = 10.0
    sp._numColumns = 6
    sp._minActiveDutyCycles = numpy.array([0.1, 0.2, 0.02, 0.03, 0.7, 0.12])
    sp._activeDutyCycles = numpy.array([0.01, 0.02, 0.002, 0.003, 0.07, 0.012])
    trueBoostFactors = [9.1, 9.1, 9.1, 9.1, 9.1, 9.1]
    sp._updateBoostFactors()
    for i in range(sp._boostFactors.size):
      self.assertLessEqual(abs(trueBoostFactors[i] - sp._boostFactors[i]), 1e-6)

    sp._maxBoost = 10.0
    sp._numColumns = 6
    sp._minActiveDutyCycles = numpy.array([0.1, 0.2, 0.02, 0.03, 0.7, 0.12])
    sp._activeDutyCycles = numpy.zeros(sp._numColumns)
    trueBoostFactors = 6*[sp._maxBoost]
    sp._updateBoostFactors()
    for i in range(sp._boostFactors.size):
      self.assertLessEqual(abs(trueBoostFactors[i] - sp._boostFactors[i]), 1e-6)


  def testUpdateInhibitionRadius(self):
    sp = self._sp

    # Test global inhibition case
    sp._globalInhibition = True
    sp._columnDimensions = numpy.array([57, 31, 2])
    sp._updateInhibitionRadius()
    self.assertEqual(sp._inhibitionRadius, 57)

    sp._globalInhibition = False
    sp._avgConnectedSpanForColumnND = Mock(return_value = 3)
    sp._avgColumnsPerInput = Mock(return_value = 4)
    trueInhibitionRadius = 6
    # ((3 * 4) - 1) / 2 => round up
    sp._updateInhibitionRadius()
    self.assertEqual(trueInhibitionRadius, sp._inhibitionRadius)

    # Test clipping at 1.0
    sp._globalInhibition = False
    sp._avgConnectedSpanForColumnND = Mock(return_value = 0.5)
    sp._avgColumnsPerInput = Mock(return_value = 1.2)
    trueInhibitionRadius = 1
    sp._updateInhibitionRadius()
    self.assertEqual(trueInhibitionRadius, sp._inhibitionRadius)

    # Test rounding up
    sp._globalInhibition = False
    sp._avgConnectedSpanForColumnND = Mock(return_value = 2.4)
    sp._avgColumnsPerInput = Mock(return_value = 2)
    trueInhibitionRadius = 2
    # ((2 * 2.4) - 1) / 2.0 => round up
    sp._updateInhibitionRadius()
    self.assertEqual(trueInhibitionRadius, sp._inhibitionRadius)


  def testAvgColumnsPerInput(self):
    sp = self._sp
    sp._columnDimensions = numpy.array([2, 2, 2, 2])
    sp._inputDimensions = numpy.array([4, 4, 4, 4])
    self.assertEqual(sp._avgColumnsPerInput(), 0.5)

    sp._columnDimensions = numpy.array([2, 2, 2, 2])
    sp._inputDimensions = numpy.array( [7, 5, 1, 3])
                                    #  2/7 0.4 2 0.666
    trueAvgColumnPerInput = (2.0/7 + 2.0/5 + 2.0/1 + 2/3.0) / 4
    self.assertEqual(sp._avgColumnsPerInput(), trueAvgColumnPerInput)

    sp._columnDimensions = numpy.array([3, 3])
    sp._inputDimensions = numpy.array( [3, 3])
                                    #   1  1
    trueAvgColumnPerInput = 1
    self.assertEqual(sp._avgColumnsPerInput(), trueAvgColumnPerInput)        

    sp._columnDimensions = numpy.array([25])
    sp._inputDimensions = numpy.array( [5])
                                    #   5
    trueAvgColumnPerInput = 5
    self.assertEqual(sp._avgColumnsPerInput(), trueAvgColumnPerInput)

    sp._columnDimensions = numpy.array([3, 3, 3, 5, 5, 6, 6])
    sp._inputDimensions = numpy.array( [3, 3, 3, 5, 5, 6, 6])
                                    #   1  1  1  1  1  1  1
    trueAvgColumnPerInput = 1
    self.assertEqual(sp._avgColumnsPerInput(), trueAvgColumnPerInput)

    sp._columnDimensions = numpy.array([3, 6, 9, 12])
    sp._inputDimensions = numpy.array( [3, 3, 3 , 3])
                                    #   1  2  3   4
    trueAvgColumnPerInput = 2.5
    self.assertEqual(sp._avgColumnsPerInput(), trueAvgColumnPerInput)


  def testAvgConnectedSpanForColumn1D(self):
    sp = self._sp
    sp._numColumns = 9
    sp._columnDimensions = numpy.array([9])
    sp._inputDimensions = numpy.array([12])
    sp._connectedSynapses = (
        SparseBinaryMatrix([[0, 1, 0, 1, 0, 1, 0, 1],
                            [0, 0, 0, 1, 0, 0, 0, 1],
                            [0, 0, 0, 0, 0, 0, 1, 0],
                            [0, 0, 1, 0, 0, 0, 1, 0],
                            [0, 0, 0, 0, 0, 0, 0, 0],
                            [0, 1, 1, 0, 0, 0, 0, 0],
                            [0, 0, 1, 1, 1, 0, 0, 0],
                            [0, 0, 1, 0, 1, 0, 0, 0],
                            [1, 1, 1, 1, 1, 1, 1, 1]]))

    trueAvgConnectedSpan = [7, 5, 1, 5, 0, 2, 3, 3, 8]
    for i in xrange(sp._numColumns):
      connectedSpan = sp._avgConnectedSpanForColumn1D(i)
      self.assertEqual(trueAvgConnectedSpan[i], connectedSpan)


  def testAvgConnectedSpanForColumn2D(self):
    sp = self._sp
    sp._numColumns = 9
    sp._columnDimensions = numpy.array([9])
    sp._numInpts = 8
    sp._inputDimensions = numpy.array([8])
    sp._connectedSynapses = SparseBinaryMatrix([
        [0, 1, 0, 1, 0, 1, 0, 1],
        [0, 0, 0, 1, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 1, 0],
        [0, 0, 1, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 0, 0, 0, 0, 0],
        [0, 0, 1, 1, 1, 0, 0, 0],
        [0, 0, 1, 0, 1, 0, 0, 0],
        [1, 1, 1, 1, 1, 1, 1, 1]])

    trueAvgConnectedSpan = [7, 5, 1, 5, 0, 2, 3, 3, 8]
    for i in xrange(sp._numColumns):
      connectedSpan = sp._avgConnectedSpanForColumn1D(i)
      self.assertEqual(trueAvgConnectedSpan[i], connectedSpan)

    sp._numColumns = 7
    sp._columnDimensions = numpy.array([7])
    sp._numInputs = 20
    sp._inputDimensions = numpy.array([5, 4])
    sp._connectedSynapses = SparseBinaryMatrix(sp._numInputs)
    sp._connectedSynapses.resize(sp._numColumns, sp._numInputs)

    connected = numpy.array([
      [[0, 1, 1, 1],
       [0, 1, 1, 1],
       [0, 1, 1, 1],
       [0, 0, 0, 0],
       [0, 0, 0, 0]],
      # rowspan = 3, colspan = 3, avg = 3

      [[1, 1, 1, 1],
       [0, 0, 1, 1],
       [0, 0, 0, 0],
       [0, 0, 0, 0],
       [0, 0, 0, 0]],
      # rowspan = 2 colspan = 4, avg = 3

      [[1, 0, 0, 0],
       [0, 0, 0, 0],
       [0, 0, 0, 0],
       [0, 0, 0, 0],
       [0, 0, 0, 1]],
      # row span = 5, colspan = 4, avg = 4.5

      [[0, 1, 0, 0],
       [0, 0, 0, 0],
       [0, 0, 0, 0],
       [0, 1, 0, 0],
       [0, 1, 0, 0]],
      # rowspan = 5, colspan = 1, avg = 3

      [[0, 0, 0, 0],
       [1, 0, 0, 1],
       [0, 0, 0, 0],
       [0, 0, 0, 0],
       [0, 0, 0, 0]],
      # rowspan = 1, colspan = 4, avg = 2.5

      [[0, 0, 0, 0],
       [0, 0, 0, 0],
       [0, 0, 0, 0],
       [0, 0, 1, 0],
       [0, 0, 0, 1]],
      # rowspan = 2, colspan = 2, avg = 2

      [[0, 0, 0, 0],
       [0, 0, 0, 0],
       [0, 0, 0, 0],
       [0, 0, 0, 0],
       [0, 0, 0, 0]]
      # rowspan = 0, colspan = 0, avg = 0

      ])

    trueAvgConnectedSpan = [3, 3, 4.5, 3, 2.5, 2, 0]
    for i in xrange(sp._numColumns):
      sp._connectedSynapses.replaceSparseRow(
        i, connected[i].reshape(-1).nonzero()[0]
      )

    for i in xrange(sp._numColumns):
      connectedSpan = sp._avgConnectedSpanForColumn2D(i)
      self.assertEqual(trueAvgConnectedSpan[i], connectedSpan)     


  def testAvgConnectedSpanForColumnND(self):
    sp = self._sp
    sp._inputDimensions = numpy.array([4, 4, 2, 5])
    sp._numInputs = numpy.prod(sp._inputDimensions)
    sp._numColumns = 5
    sp._columnDimensions = numpy.array([5])
    sp._connectedSynapses = SparseBinaryMatrix(sp._numInputs)
    sp._connectedSynapses.resize(sp._numColumns, sp._numInputs)

    connected = numpy.zeros(sp._numInputs).reshape(sp._inputDimensions)
    connected[1][0][1][0] = 1
    connected[1][0][1][1] = 1
    connected[3][2][1][0] = 1
    connected[3][0][1][0] = 1
    connected[1][0][1][3] = 1
    connected[2][2][1][0] = 1
    # span:   3  3  1  4, avg = 11/4
    sp._connectedSynapses.replaceSparseRow(
      0, connected.reshape(-1).nonzero()[0]
    )

    connected = numpy.zeros(sp._numInputs).reshape(sp._inputDimensions)
    connected[2][0][1][0] = 1
    connected[2][0][0][0] = 1
    connected[3][0][0][0] = 1
    connected[3][0][1][0] = 1
    # spn:    2  1  2  1, avg = 6/4
    sp._connectedSynapses.replaceSparseRow(
      1, connected.reshape(-1).nonzero()[0]
    )

    connected = numpy.zeros(sp._numInputs).reshape(sp._inputDimensions)
    connected[0][0][1][4] = 1
    connected[0][0][0][3] = 1
    connected[0][0][0][1] = 1
    connected[1][0][0][2] = 1
    connected[0][0][1][1] = 1
    connected[3][3][1][1] = 1
    # span:   4  4  2  4, avg = 14/4
    sp._connectedSynapses.replaceSparseRow(
      2, connected.reshape(-1).nonzero()[0]
    )

    connected = numpy.zeros(sp._numInputs).reshape(sp._inputDimensions)
    connected[3][3][1][4] = 1
    connected[0][0][0][0] = 1
    # span:   4  4  2  5, avg = 15/4
    sp._connectedSynapses.replaceSparseRow(
      3, connected.reshape(-1).nonzero()[0]
    )

    connected = numpy.zeros(sp._numInputs).reshape(sp._inputDimensions)
    # span:   0  0  0  0, avg = 0
    sp._connectedSynapses.replaceSparseRow(
      4, connected.reshape(-1).nonzero()[0]
    )

    trueAvgConnectedSpan = [11.0/4, 6.0/4, 14.0/4, 15.0/4, 0]

    for i in xrange(sp._numColumns):
      connectedSpan = sp._avgConnectedSpanForColumnND(i)
      self.assertAlmostEqual(trueAvgConnectedSpan[i], connectedSpan)


  def testBumpUpWeakColumns(self):
    sp = SpatialPooler(inputDimensions=[8],
                      columnDimensions=[5])

    sp._synPermBelowStimulusInc = 0.01
    sp._synPermTrimThreshold = 0.05
    sp._overlapDutyCycles = numpy.array([0, 0.009, 0.1, 0.001, 0.002])
    sp._minOverlapDutyCycles = numpy.array(5*[0.01])

    sp._potentialPools = SparseBinaryMatrix(
       [[1, 1, 1, 1, 0, 0, 0, 0],
        [1, 0, 0, 0, 1, 1, 0, 1],
        [0, 0, 1, 0, 1, 1, 1, 0],
        [1, 1, 1, 0, 0, 0, 1, 0],
        [1, 1, 1, 1, 1, 1, 1, 1]])

    sp._permanences = SparseMatrix(
      [[0.200, 0.120, 0.090, 0.040, 0.000, 0.000, 0.000, 0.000],
       [0.150, 0.000, 0.000, 0.000, 0.180, 0.120, 0.000, 0.450],
       [0.000, 0.000, 0.014, 0.000, 0.032, 0.044, 0.110, 0.000],
       [0.041, 0.000, 0.000, 0.000, 0.000, 0.000, 0.178, 0.000],
       [0.100, 0.738, 0.045, 0.002, 0.050, 0.008, 0.208, 0.034]])

    truePermanences = [
      [0.210, 0.130, 0.100, 0.000, 0.000, 0.000, 0.000, 0.000],
  #    Inc    Inc    Inc    Trim    -     -     -    -
      [0.160, 0.000, 0.000, 0.000, 0.190, 0.130, 0.000, 0.460],
  #    Inc   -     -    -     Inc   Inc    -     Inc
      [0.000, 0.000, 0.014, 0.000, 0.032, 0.044, 0.110, 0.000], #unchanged
  #    -    -     -    -     -    -     -    -
      [0.051, 0.000, 0.000, 0.000, 0.000, 0.000, 0.188, 0.000],
  #    Inc   Trim    Trim    -     -    -    Inc     -
      [0.110, 0.748, 0.055, 0.000, 0.060, 0.000, 0.218, 0.000]]

    sp._bumpUpWeakColumns()
    for i in xrange(sp._numColumns):
      perm = list(sp._permanences.getRow(i))
      for j in xrange(sp._numInputs):
        self.assertAlmostEqual(truePermanences[i][j], perm[j])


  def testUpdateMinDutyCycleLocal(self):
    sp = self._sp

    # Replace the get neighbors function with a mock to know exactly
    # the neighbors of each column.
    sp._numColumns = 5
    sp._getNeighborsND = Mock(side_effect=[[0, 1, 2],
                                           [1, 2, 3],
                                           [2, 3, 4],
                                           [0, 2, 4],
                                           [0, 1, 3]])

    sp._minPctOverlapDutyCycles = 0.04
    sp._overlapDutyCycles = numpy.array([1.4, 0.5, 1.2, 0.8, 0.1])
    trueMinOverlapDutyCycles = [0.04*1.4, 0.04*1.2, 0.04*1.2, 0.04*1.4,
                                0.04*1.4]

    sp._minPctActiveDutyCycles = 0.02
    sp._activeDutyCycles = numpy.array([0.4, 0.5, 0.2, 0.18, 0.1])
    trueMinActiveDutyCycles = [0.02*0.5, 0.02*0.5, 0.02*0.2, 0.02*0.4,
                               0.02*0.5]

    sp._minOverlapDutyCycles = numpy.zeros(sp._numColumns)
    sp._minActiveDutyCycles = numpy.zeros(sp._numColumns)
    sp._updateMinDutyCyclesLocal()
    self.assertListEqual(trueMinOverlapDutyCycles,
                         list(sp._minOverlapDutyCycles))
    self.assertListEqual(trueMinActiveDutyCycles, list(sp._minActiveDutyCycles))

    sp._numColumns = 8
    sp._getNeighborsND = Mock(side_effect= [[0, 1, 2, 3, 4],
                                            [1, 2, 3, 4, 5],
                                            [2, 3, 4, 6, 7],
                                            [0, 2, 4, 6],
                                            [1, 6],
                                            [3, 5, 7],
                                            [1, 4, 5, 6],
                                            [2, 3, 6, 7]])

    sp._minPctOverlapDutyCycles = 0.01
    sp._overlapDutyCycles = numpy.array(
        [1.2, 2.7, 0.9, 1.1, 4.3, 7.1, 2.3, 0.0])
    trueMinOverlapDutyCycles = [0.01*4.3, 0.01*7.1, 0.01*4.3, 0.01*4.3,
                                0.01*4.3, 0.01*7.1, 0.01*7.1, 0.01*2.3]

    sp._minPctActiveDutyCycles = 0.03
    sp._activeDutyCycles = numpy.array(
        [0.14, 0.25, 0.125, 0.33, 0.27, 0.11, 0.76, 0.31])
    trueMinActiveDutyCycles = [0.03*0.33, 0.03*0.33, 0.03*0.76, 0.03*0.76,
                               0.03*0.76, 0.03*0.33, 0.03*0.76, 0.03*0.76]
    sp._minOverlapDutyCycles = numpy.zeros(sp._numColumns)
    sp._minActiveDutyCycles = numpy.zeros(sp._numColumns)
    sp._updateMinDutyCyclesLocal()
    self.assertListEqual(trueMinOverlapDutyCycles,
                         list(sp._minOverlapDutyCycles))
    self.assertListEqual(trueMinActiveDutyCycles, list(sp._minActiveDutyCycles))


  def testUpdateMinDutyCyclesGlobal(self):
    sp = self._sp
    sp._minPctOverlapDutyCycles = 0.01
    sp._minPctActiveDutyCycles = 0.02
    sp._numColumns = 5
    sp._overlapDutyCycles = numpy.array([0.06, 1, 3, 6, 0.5])
    sp._activeDutyCycles = numpy.array([0.6, 0.07, 0.5, 0.4, 0.3])
    sp._updateMinDutyCyclesGlobal()
    trueMinActiveDutyCycles = sp._numColumns*[0.02*0.6]
    trueMinOverlapDutyCycles = sp._numColumns*[0.01*6]
    for i in xrange(sp._numColumns):
      self.assertAlmostEqual(trueMinActiveDutyCycles[i], 
                             sp._minActiveDutyCycles[i])
      self.assertAlmostEqual(trueMinOverlapDutyCycles[i],
                             sp._minOverlapDutyCycles[i])

    sp._minPctOverlapDutyCycles = 0.015
    sp._minPctActiveDutyCycles = 0.03
    sp._numColumns = 5
    sp._overlapDutyCycles = numpy.array([0.86, 2.4, 0.03, 1.6, 1.5])
    sp._activeDutyCycles = numpy.array([0.16, 0.007, 0.15, 0.54, 0.13])
    sp._updateMinDutyCyclesGlobal()
    trueMinOverlapDutyCycles = sp._numColumns*[0.015*2.4]
    for i in xrange(sp._numColumns):
      self.assertAlmostEqual(trueMinOverlapDutyCycles[i],
                             sp._minOverlapDutyCycles[i])

    sp._minPctOverlapDutyCycles = 0.015
    sp._minPctActiveDutyCycles= 0.03
    sp._numColumns = 5
    sp._overlapDutyCycles = numpy.zeros(5)
    sp._activeDutyCycles = numpy.zeros(5)
    sp._updateMinDutyCyclesGlobal()
    trueMinOverlapDutyCycles = sp._numColumns * [0]
    trueMinActiveDutyCycles = sp._numColumns * [0]
    for i in xrange(sp._numColumns):
      self.assertAlmostEqual(trueMinActiveDutyCycles[i], 
                             sp._minActiveDutyCycles[i])
      self.assertAlmostEqual(trueMinOverlapDutyCycles[i],
                             sp._minOverlapDutyCycles[i])


  def testIsUpdateRound(self):
    sp = self._sp
    sp._updatePeriod = 50
    sp._iterationNum = 1
    self.assertEqual(sp._isUpdateRound(), False)
    sp._iterationNum = 39
    self.assertEqual(sp._isUpdateRound(), False)
    sp._iterationNum = 50
    self.assertEqual(sp._isUpdateRound(), True)
    sp._iterationNum = 1009
    self.assertEqual(sp._isUpdateRound(), False)
    sp._iterationNum = 1250
    self.assertEqual(sp._isUpdateRound(), True)

    sp._updatePeriod = 125
    sp._iterationNum = 0
    self.assertEqual(sp._isUpdateRound(), True)
    sp._iterationNum = 200
    self.assertEqual(sp._isUpdateRound(), False)
    sp._iterationNum = 249
    self.assertEqual(sp._isUpdateRound(), False)
    sp._iterationNum = 1330
    self.assertEqual(sp._isUpdateRound(), False)
    sp._iterationNum = 1249
    self.assertEqual(sp._isUpdateRound(), False)
    sp._iterationNum = 1375
    self.assertEqual(sp._isUpdateRound(), True)


  def testAdaptSynapses(self):
    sp = SpatialPooler(inputDimensions=[8],
                       columnDimensions=[4],
                       synPermInactiveDec=0.01,
                       synPermActiveInc=0.1)
    sp._synPermTrimThreshold = 0.05

    sp._potentialPools = SparseBinaryMatrix(
        [[1, 1, 1, 1, 0, 0, 0, 0],
         [1, 0, 0, 0, 1, 1, 0, 1],
         [0, 0, 1, 0, 0, 0, 1, 0],
         [1, 0, 0, 0, 0, 0, 1, 0]])

    inputVector = numpy.array([1, 0, 0, 1, 1, 0, 1, 0])
    activeColumns = numpy.array([0, 1, 2])

    sp._permanences = SparseMatrix(
        [[0.200, 0.120, 0.090, 0.040, 0.000, 0.000, 0.000, 0.000],
         [0.150, 0.000, 0.000, 0.000, 0.180, 0.120, 0.000, 0.450],
         [0.000, 0.000, 0.014, 0.000, 0.000, 0.000, 0.110, 0.000],
         [0.040, 0.000, 0.000, 0.000, 0.000, 0.000, 0.178, 0.000]])

    truePermanences = [
        [0.300, 0.110, 0.080, 0.140, 0.000, 0.000, 0.000, 0.000],
      #   Inc     Dec   Dec    Inc      -      -      -     -
        [0.250, 0.000, 0.000, 0.000, 0.280, 0.110, 0.000, 0.440],
      #   Inc      -      -     -      Inc    Dec    -     Dec  
        [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.210, 0.000],
      #   -      -     Trim     -     -     -       Inc   - 
        [0.040, 0.000, 0.000, 0.000, 0.000, 0.000, 0.178, 0.000]]
      #    -      -      -      -      -      -      -       -   

    sp._adaptSynapses(inputVector, activeColumns)
    for i in xrange(sp._numColumns):
      perm = list(sp._permanences.getRow(i))
      for j in xrange(sp._numInputs):
        self.assertAlmostEqual(truePermanences[i][j], perm[j])

    sp._potentialPools = SparseBinaryMatrix(
        [[1, 1, 1, 0, 0, 0, 0, 0],
         [0, 1, 1, 1, 0, 0, 0, 0],
         [0, 0, 1, 1, 1, 0, 0, 0],
         [1, 0, 0, 0, 0, 0, 1, 0]])

    inputVector = numpy.array([1, 0, 0, 1, 1, 0, 1, 0])
    activeColumns = numpy.array([0, 1, 2])

    sp._permanences = SparseMatrix(
        [[0.200, 0.120, 0.090, 0.000, 0.000, 0.000, 0.000, 0.000],
         [0.000, 0.017, 0.232, 0.400, 0.000, 0.000, 0.000, 0.000],
         [0.000, 0.000, 0.014, 0.051, 0.730, 0.000, 0.000, 0.000],
         [0.170, 0.000, 0.000, 0.000, 0.000, 0.000, 0.380, 0.000]])

    truePermanences = [
        [0.30, 0.110, 0.080, 0.000, 0.000, 0.000, 0.000, 0.000],
        #  Inc    Dec     Dec     -       -    -    -    -
        [0.000, 0.000, 0.222, 0.500, 0.000, 0.000, 0.000, 0.000],
        #  -     Trim    Dec    Inc    -       -      -      -
        [0.000, 0.000, 0.000, 0.151, 0.830, 0.000, 0.000, 0.000],
        #   -      -    Trim   Inc    Inc     -     -     -
        [0.170, 0.000, 0.000, 0.000, 0.000, 0.000, 0.380, 0.000]]
        #  -    -      -      -      -       -       -     -

    sp._adaptSynapses(inputVector, activeColumns)
    for i in xrange(sp._numColumns):
      perm = list(sp._permanences.getRow(i))
      for j in xrange(sp._numInputs):
        self.assertAlmostEqual(truePermanences[i][j], perm[j])


  def testRaisePermanenceThreshold(self):
    sp = self._sp
    sp._inputDimensions=numpy.array([5])
    sp._columnDimensions=numpy.array([5])
    sp._synPermConnected=0.1
    sp._stimulusThreshold=3
    sp._synPermBelowStimulusInc = 0.01
    sp._permanences = SparseMatrix(
        [[0.0, 0.11, 0.095, 0.092, 0.01],
         [0.12, 0.15, 0.02, 0.12, 0.09],
         [0.51, 0.081, 0.025, 0.089, 0.31],
         [0.18, 0.0601, 0.11, 0.011, 0.03],
         [0.011, 0.011, 0.011, 0.011, 0.011]])

    sp._connectedSynapses = SparseBinaryMatrix(
        [[0, 1, 0, 0, 0],
         [1, 1, 0, 1, 0],
         [1, 0, 0, 0, 1],
         [1, 0, 1, 0, 0],
         [0, 0, 0, 0, 0]])

    sp._connectedCounts = numpy.array([1, 3, 2, 2, 0])

    truePermanences = [
        [0.01, 0.12, 0.105, 0.102, 0.02],  # incremented once
        [0.12, 0.15, 0.02, 0.12, 0.09],  # no change
        [0.53, 0.101, 0.045, 0.109, 0.33],  # increment twice
        [0.22, 0.1001, 0.15, 0.051, 0.07],  # increment four times
        [0.101, 0.101, 0.101, 0.101, 0.101]]  #increment 9 times

    maskPP = numpy.array(range(5))
    for i in xrange(sp._numColumns):
      perm = sp._permanences.getRow(i)
      sp._raisePermanenceToThreshold(perm, maskPP)
      for j in xrange(sp._numInputs):
        self.assertAlmostEqual(truePermanences[i][j], perm[j])


  def testUpdatePermanencesForColumn(self):
    sp = SpatialPooler(inputDimensions=[5],
                       columnDimensions=[5],
                       synPermConnected=0.1)
    sp._synPermTrimThreshold = 0.05
    permanences = numpy.array([
        [-0.10, 0.500, 0.400, 0.010, 0.020],
        [0.300, 0.010, 0.020, 0.120, 0.090],
        [0.070, 0.050, 1.030, 0.190, 0.060],
        [0.180, 0.090, 0.110, 0.010, 0.030],
        [0.200, 0.101, 0.050, -0.09, 1.100]])

    # These are the 'true permanences' reflected in trueConnectedSynapses
    # truePermanences = SparseMatrix(
    #  [[0.000, 0.500, 0.400, 0.000, 0.000],
    #    Clip     -     -      Trim   Trim
    #   [0.300, 0.000, 0.000, 0.120, 0.090],
    #      -    Trim   Trim   -     -
    #   [0.070, 0.050, 1.000, 0.190, 0.060],
    #       -     -   Clip      -     -
    #   [0.180, 0.090, 0.110, 0.000, 0.000],
    #      -     -      -      Trim   Trim
    #   [0.200, 0.101, 0.050, 0.000, 1.000]])
    #     -      -     -      Clip   Clip

    trueConnectedSynapses = [
      [0, 1, 1, 0, 0],
      [1, 0, 0, 1, 0],
      [0, 0, 1, 1, 0],
      [1, 0, 1, 0, 0],
      [1, 1, 0, 0, 1]]

    trueConnectedCounts = [2, 2, 2, 2, 3]
    for i in xrange(sp._numColumns):
      sp._updatePermanencesForColumn(permanences[i], i)
      self.assertListEqual(
        trueConnectedSynapses[i],
        list(sp._connectedSynapses.getRow(i))
      )
    self.assertListEqual(trueConnectedCounts, list(sp._connectedCounts))


  def testCalculateOverlap(self):
    """
    Test that column computes overlap and percent overlap correctly.
    """
    sp = SpatialPooler(inputDimensions = [10],
                       columnDimensions = [5])
    sp._connectedSynapses = SparseBinaryMatrix(
      [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
       [0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
       [0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
       [0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
       [0, 0, 0, 0, 0, 0, 0, 0, 1, 1]])
    sp._connectedCounts = numpy.array([10.0, 8.0, 6.0, 4.0, 2.0])
    inputVector = numpy.zeros(sp._numInputs, dtype='float32')
    overlaps = sp._calculateOverlap(inputVector)
    overlapsPct = sp._calculateOverlapPct(overlaps)
    trueOverlaps = list(numpy.array([0, 0, 0, 0, 0]))
    trueOverlapsPct = list(numpy.array([0, 0, 0, 0, 0]))
    self.assertListEqual(list(overlaps), trueOverlaps)
    self.assertListEqual(list(overlapsPct), trueOverlapsPct)

    sp._connectedSynapses = SparseBinaryMatrix(
      [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
       [0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
       [0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
       [0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
       [0, 0, 0, 0, 0, 0, 0, 0, 1, 1]])
    sp._connectedCounts = numpy.array([10.0, 8.0, 6.0, 4.0, 2.0])
    inputVector = numpy.ones(sp._numInputs, dtype='float32')
    overlaps = sp._calculateOverlap(inputVector)
    overlapsPct = sp._calculateOverlapPct(overlaps)
    trueOverlaps = list(numpy.array([10, 8, 6, 4, 2]))
    trueOverlapsPct = list(numpy.array([1, 1, 1, 1, 1]))
    self.assertListEqual(list(overlaps), trueOverlaps)
    self.assertListEqual(list(overlapsPct), trueOverlapsPct)

    sp._connectedSynapses = SparseBinaryMatrix(
      [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
       [0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
       [0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
       [0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
       [0, 0, 0, 0, 0, 0, 0, 0, 1, 1]])
    sp._connectedCounts = numpy.array([10.0, 8.0, 6.0, 4.0, 2.0])
    inputVector = numpy.zeros(sp._numInputs, dtype='float32')
    inputVector[9] = 1
    overlaps = sp._calculateOverlap(inputVector)
    overlapsPct = sp._calculateOverlapPct(overlaps)
    trueOverlaps = list(numpy.array([1, 1, 1, 1, 1]))
    trueOverlapsPct = list(numpy.array([0.1, 0.125, 1.0/6, 0.25, 0.5]))
    self.assertListEqual(list(overlaps), trueOverlaps)
    self.assertListEqual(list(overlapsPct), trueOverlapsPct)

    # Zig-zag
    sp._connectedSynapses = SparseBinaryMatrix(
      [[1, 0, 0, 0, 0, 1, 0, 0, 0, 0],
       [0, 1, 0, 0, 0, 0, 1, 0, 0, 0],
       [0, 0, 1, 0, 0, 0, 0, 1, 0, 0],
       [0, 0, 0, 1, 0, 0, 0, 0, 1, 0],
       [0, 0, 0, 0, 1, 0, 0, 0, 0, 1]])
    sp._connectedCounts = numpy.array([2.0, 2.0, 2.0, 2.0, 2.0])
    inputVector = numpy.zeros(sp._numInputs, dtype='float32')
    inputVector[range(0, 10, 2)] = 1
    overlaps = sp._calculateOverlap(inputVector)
    overlapsPct = sp._calculateOverlapPct(overlaps)
    trueOverlaps = list(numpy.array([1, 1, 1, 1, 1]))
    trueOverlapsPct = list(numpy.array([0.5, 0.5, 0.5, 0.5, 0.5]))
    self.assertListEqual(list(overlaps), trueOverlaps)
    self.assertListEqual(list(overlapsPct), trueOverlapsPct)


  def testInitPermanence1(self):
    """
    test initial permanence generation. ensure that
    a correct amount of synapses are initialized in 
    a connected state, with permanence values drawn from
    the correct ranges
    """
    sp = self._sp
    sp._inputDimensions = numpy.array([10])
    sp._numInputs = 10
    sp._raisePermanenceToThreshold = Mock()

    sp._potentialRadius = 2
    connectedPct = 1
    mask = numpy.array([1, 1, 1, 0, 0, 0, 0, 0, 1, 1])
    perm = sp._initPermanence(mask, connectedPct)
    connected = (perm >= sp._synPermConnected).astype(int)
    numcon = (connected.nonzero()[0]).size
    self.assertEqual(numcon, 5)
    maxThresh = sp._synPermConnected + sp._synPermActiveInc/4
    self.assertEqual((perm <= maxThresh).all(), True)

    connectedPct = 0
    perm = sp._initPermanence(mask, connectedPct)
    connected = (perm >= sp._synPermConnected).astype(int)
    numcon = (connected.nonzero()[0]).size
    self.assertEqual(numcon, 0)

    connectedPct = 0.5
    sp._potentialRadius = 100
    sp._numInputs = 100
    mask = numpy.ones(100)
    perm = sp._initPermanence(mask, connectedPct)
    connected = (perm >= sp._synPermConnected).astype(int)
    numcon = (connected.nonzero()[0]).size
    self.assertGreater(numcon, 0)
    self.assertLess(numcon, sp._numInputs)

    minThresh = sp._synPermActiveInc / 2.0
    connThresh = sp._synPermConnected
    self.assertEqual(numpy.logical_and((perm >= minThresh),
                                       (perm < connThresh)).any(), True)


  def testInitPermanence2(self):
    """
    Test initial permanence generation. ensure that permanence values
    are only assigned to bits within a column's potential pool.
    """
    sp = self._sp
    sp._raisePermanenceToThreshold = Mock()

    sp._numInputs = 10
    connectedPct = 1
    mask = numpy.array([1, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    perm = sp._initPermanence(mask, connectedPct)
    connected = list((perm > 0).astype(int))
    trueConnected = [1, 1, 0, 0, 0, 0, 0, 0, 0, 0]
    self.assertListEqual(connected, trueConnected)

    sp._numInputs = 10
    connectedPct = 1
    mask = numpy.array([0, 0, 0, 0, 1, 1, 1, 0, 0, 0])
    perm = sp._initPermanence(mask, connectedPct)
    connected = list((perm > 0).astype(int))
    trueConnected = [0, 0, 0, 0, 1, 1, 1, 0, 0, 0]
    self.assertListEqual(connected, trueConnected)

    sp._numInputs = 10
    connectedPct = 1
    mask = numpy.array([0, 0, 0, 0, 0, 0, 0, 0, 1, 1])
    perm = sp._initPermanence(mask, connectedPct)
    connected = list((perm > 0).astype(int))
    trueConnected = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1]
    self.assertListEqual(connected, trueConnected)

    sp._numInputs = 10
    connectedPct = 1
    mask = numpy.array([1, 1, 1, 1, 1, 1, 1, 0, 1, 1])
    perm = sp._initPermanence(mask, connectedPct)
    connected = list((perm > 0).astype(int))
    trueConnected = [1, 1, 1, 1, 1, 1, 1, 0, 1, 1]
    self.assertListEqual(connected, trueConnected)


  def testUpdateDutyCycleHelper(self):
    """
    Tests that duty cycles are updated properly according
    to the mathematical formula. also check the effects of
    supplying a maxPeriod to the function.
    """
    dc = numpy.zeros(5)
    dc = numpy.array([1000.0, 1000.0, 1000.0, 1000.0, 1000.0])
    period = 1000
    newvals = numpy.zeros(5)
    newDc = SpatialPooler._updateDutyCyclesHelper(dc, newvals, period)
    trueNewDc = [999, 999, 999, 999, 999]
    self.assertListEqual(list(newDc), trueNewDc)

    dc = numpy.array([1000.0, 1000.0, 1000.0, 1000.0, 1000.0])
    period = 1000
    newvals = numpy.zeros(5)
    newvals.fill(1000)
    newDc = SpatialPooler._updateDutyCyclesHelper(dc, newvals, period)
    trueNewDc = list(dc)
    self.assertListEqual(list(newDc), trueNewDc)

    dc = numpy.array([1000, 1000, 1000, 1000, 1000])
    newvals = numpy.array([2000, 4000, 5000, 6000, 7000])
    period = 1000
    newDc = SpatialPooler._updateDutyCyclesHelper(dc, newvals, period)
    trueNewDc = [1001, 1003, 1004, 1005, 1006]
    self.assertListEqual(list(newDc), trueNewDc)

    dc = numpy.array([1000, 800, 600, 400, 2000])
    newvals = numpy.zeros(5)
    period = 2
    newDc = SpatialPooler._updateDutyCyclesHelper(dc, newvals, period)
    trueNewDc = [500, 400, 300, 200, 1000]
    self.assertListEqual(list(newDc), trueNewDc)


  def testInhibitColumnsGlobal(self):
    """
    Tests that global inhibition correctly picks the
    correct top number of overlap scores as winning columns.
    """
    sp = self._sp
    density = 0.3
    sp._numColumns = 10
    overlaps = numpy.array([1, 2, 1, 4, 8, 3, 12, 5, 4, 1])
    active = list(sp._inhibitColumnsGlobal(overlaps, density))
    trueActive = numpy.zeros(sp._numColumns)
    trueActive = [4, 6, 7]
    self.assertListEqual(list(trueActive), active)

    density = 0.5
    sp._numColumns = 10
    overlaps = numpy.array(range(10))
    active = list(sp._inhibitColumnsGlobal(overlaps, density))
    trueActive = numpy.zeros(sp._numColumns)
    trueActive = range(5, 10)
    self.assertListEqual(trueActive, active)


  def testInhibitColumnsLocal(self):
    sp = self._sp
    density = 0.5
    sp._numColumns = 10
    sp._columnDimensions = numpy.array([sp._numColumns])
    sp._inhibitionRadius = 2
    overlaps = numpy.array([1, 2, 7, 0, 3, 4, 16, 1, 1.5, 1.7])
                        #   L  W  W  L  L  W  W   L   L    W
    trueActive = [1, 2, 5, 6, 9]
    active = list(sp._inhibitColumnsLocal(overlaps, density))
    self.assertListEqual(trueActive, active)

    density = 0.5
    sp._numColumns = 10
    sp._columnDimensions = numpy.array([sp._numColumns])
    sp._inhibitionRadius = 3
    overlaps = numpy.array([1, 2, 7, 0, 3, 4, 16, 1, 1.5, 1.7])
                        #   L  W  W  L  L  W  W   L   L    L
    trueActive = [1, 2, 5, 6]
    active = list(sp._inhibitColumnsLocal(overlaps, density))
    # self.assertListEqual(trueActive, active)

    # Test add to winners
    density = 0.3333
    sp._numColumns = 10
    sp._columnDimensions = numpy.array([sp._numColumns])
    sp._inhibitionRadius = 3
    overlaps = numpy.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
                        #   W  W  L  L  W  W  L  L  L  W
    trueActive = [0, 1, 4, 5, 8]
    active = list(sp._inhibitColumnsLocal(overlaps, density))
    self.assertListEqual(trueActive, active)


  def testGetNeighbors1D(self):
    """
    Test that _getNeighbors static method correctly computes
    the neighbors of a column
    """
    sp = self._sp

    layout = numpy.array([0, 0, 1, 0, 1, 0, 0,  0])
    layout1D = layout.reshape(-1)
    columnIndex = 3
    dimensions = numpy.array([8])
    radius = 1
    mask = sp._getNeighbors1D(columnIndex, dimensions, radius, wrapAround=True)
    negative = set(range(dimensions.prod())) - set(mask)
    self.assertEqual(layout1D[mask].all(), True)
    self.assertEqual(layout1D[list(negative)].any(), False)

    mask = sp._getNeighbors1D(columnIndex, dimensions, radius, wrapAround=False)
    negative = set(range(dimensions.prod())) - set(mask)
    self.assertEqual(layout1D[mask].all(), True)
    self.assertEqual(layout1D[list(negative)].any(), False)


    layout = numpy.array([0, 1, 1, 0, 1, 1, 0,  0])
    layout1D = layout.reshape(-1)
    columnIndex = 3
    dimensions = numpy.array([8])
    radius = 2
    mask = sp._getNeighbors1D(columnIndex, dimensions, radius, wrapAround=True)
    negative = set(range(dimensions.prod())) - set(mask)
    self.assertEqual(layout1D[mask].all(), True)
    self.assertEqual(layout1D[list(negative)].any(), False)

    mask = sp._getNeighbors1D(columnIndex, dimensions, radius, wrapAround=False)
    negative = set(range(dimensions.prod())) - set(mask)
    self.assertEqual(layout1D[mask].all(), True)
    self.assertEqual(layout1D[list(negative)].any(), False)

    layout = numpy.array([0, 1, 1, 0, 0, 0, 1,  1])
    layout1D = layout.reshape(-1)
    columnIndex = 0
    dimensions = numpy.array([8])
    radius = 2
    mask = sp._getNeighbors1D(columnIndex, dimensions, radius, wrapAround=True)
    negative = set(range(dimensions.prod())) - set(mask)
    self.assertEqual(layout1D[mask].all(), True)
    self.assertEqual(layout1D[list(negative)].any(), False)

    layout = numpy.array([0, 1, 1, 0, 0, 0, 0,  0])
    layout1D = layout.reshape(-1)
    columnIndex = 0
    dimensions = numpy.array([8])
    radius = 2
    mask = sp._getNeighbors1D(columnIndex, dimensions, radius, wrapAround=False)
    negative = set(range(dimensions.prod())) - set(mask)
    self.assertEqual(layout1D[mask].all(), True)
    self.assertEqual(layout1D[list(negative)].any(), False)

    # Radius to big
    layout = numpy.array([1, 1, 1, 1, 1, 1, 0, 1])
    layout1D = layout.reshape(-1)
    columnIndex = 6
    dimensions = numpy.array([8])
    radius = 20
    mask = sp._getNeighbors1D(columnIndex, dimensions, radius, wrapAround=True)
    negative = set(range(dimensions.prod())) - set(mask)
    self.assertEqual(layout1D[mask].all(), True)
    self.assertEqual(layout1D[list(negative)].any(), False)

    layout = numpy.array([1, 1, 1, 1, 1, 1, 0,  1])
    layout1D = layout.reshape(-1)
    columnIndex = 6
    dimensions = numpy.array([8])
    radius = 20
    mask = sp._getNeighbors1D(columnIndex, dimensions, radius, wrapAround=False)
    negative = set(range(dimensions.prod())) - set(mask)
    self.assertEqual(layout1D[mask].all(), True)
    self.assertEqual(layout1D[list(negative)].any(), False)


  def testGetNeighbors2D(self):
    """
    Test that _getNeighbors static method correctly computes
    the neighbors of a column and maps them from 2D back to 1D
    """
    sp = self._sp
    layout = numpy.array([
      [0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0],
      [0, 1, 1, 1, 0],
      [0, 1, 0, 1, 0],
      [0, 1, 1, 1, 0],
      [0, 0, 0, 0, 0]])

    layout1D = layout.reshape(-1)
    columnIndex = 3*5+ 2
    dimensions = numpy.array([6, 5])
    radius = 1
    mask = sp._getNeighbors2D(columnIndex, dimensions, radius, wrapAround=True)
    negative = set(range(dimensions.prod())) - set(mask)
    self.assertEqual(layout1D[mask].all(), True)
    self.assertEqual(layout1D[list(negative)].any(), False)

    mask = sp._getNeighbors2D(columnIndex, dimensions, radius, wrapAround=False)
    negative = set(range(dimensions.prod())) - set(mask)
    self.assertEqual(layout1D[mask].all(), True)
    self.assertEqual(layout1D[list(negative)].any(), False)

    layout = numpy.array(
      [[0, 0, 0, 0, 0],
       [1, 1, 1, 1, 1],
       [1, 1, 1, 1, 1],
       [1, 1, 0, 1, 1],
       [1, 1, 1, 1, 1],
       [1, 1, 1, 1, 1]])

    layout1D = layout.reshape(-1)
    columnIndex = 3*5+ 2
    dimensions = numpy.array([6, 5])
    radius = 2
    mask = sp._getNeighbors2D(columnIndex, dimensions, radius, wrapAround=True)
    negative = set(range(dimensions.prod())) - set(mask)
    self.assertEqual(layout1D[mask].all(), True)
    self.assertEqual(layout1D[list(negative)].any(), False)

    mask = sp._getNeighbors2D(columnIndex, dimensions, radius, wrapAround=False)
    negative = set(range(dimensions.prod())) - set(mask)
    self.assertEqual(layout1D[mask].all(), True)
    self.assertEqual(layout1D[list(negative)].any(), False)

    # Radius too big
    layout = numpy.array(
      [[1, 1, 1, 1, 1],
       [1, 1, 1, 1, 1],
       [1, 1, 1, 1, 1],
       [1, 1, 0, 1, 1],
       [1, 1, 1, 1, 1],
       [1, 1, 1, 1, 1]])

    layout1D = layout.reshape(-1)
    columnIndex = 3*5+ 2
    dimensions = numpy.array([6, 5])
    radius = 7
    mask = sp._getNeighbors2D(columnIndex, dimensions, radius, wrapAround=True)
    negative = set(range(dimensions.prod())) - set(mask)
    self.assertEqual(layout1D[mask].all(), True)
    self.assertEqual(layout1D[list(negative)].any(), False)

    mask = sp._getNeighbors2D(columnIndex, dimensions, radius, wrapAround=False)
    negative = set(range(dimensions.prod())) - set(mask)
    self.assertEqual(layout1D[mask].all(), True)
    self.assertEqual(layout1D[list(negative)].any(), False)

    # Wrap-around
    layout = numpy.array(
      [[1, 0, 0, 1, 1],
       [0, 0, 0, 0, 0],
       [0, 0, 0, 0, 0],
       [0, 0, 0, 0, 0],
       [1, 0, 0, 1, 1],
       [1, 0, 0, 1, 0]])

    layout1D = layout.reshape(-1)
    dimensions = numpy.array([6, 5])
    columnIndex = dimensions.prod() -1
    radius = 1
    mask = sp._getNeighbors2D(columnIndex, dimensions, radius, wrapAround=True)
    negative = set(range(dimensions.prod())) - set(mask)
    self.assertEqual(layout1D[mask].all(), True)
    self.assertEqual(layout1D[list(negative)].any(), False)

    layout = numpy.array(
      [[0, 0, 0, 0, 0],
       [0, 0, 0, 0, 0],
       [0, 0, 0, 0, 0],
       [0, 0, 0, 0, 0],
       [0, 0, 0, 1, 1],
       [0, 0, 0, 1, 0]])

    layout1D = layout.reshape(-1)
    dimensions = numpy.array([6, 5])
    columnIndex = dimensions.prod() -1
    radius = 1
    mask = sp._getNeighbors2D(columnIndex, dimensions, radius, wrapAround=False)
    negative = set(range(dimensions.prod())) - set(mask)
    self.assertEqual(layout1D[mask].all(), True)
    self.assertEqual(layout1D[list(negative)].any(), False)


  def testGetNeighborsND(self):
    sp = self._sp

    dimensions = numpy.array([5, 7, 2])
    layout1D = numpy.array(range(numpy.prod(dimensions)))
    layout = numpy.reshape(layout1D, dimensions)
    radius = 1
    x = 1
    y = 3
    z = 2
    columnIndex = layout[z][y][x]
    neighbors = sp._getNeighborsND(columnIndex, dimensions, radius,
                                   wrapAround=True)
    trueNeighbors = set()
    for i in range(-radius, radius+1):
      for j in range(-radius, radius+1):
        for k in range(-radius, radius+1):
          zprime = (z + i) % dimensions[0]
          yprime = (y + j) % dimensions[1]
          xprime = (x + k) % dimensions[2]
          trueNeighbors.add(
            layout[zprime][yprime][xprime]
          )
    trueNeighbors.remove(columnIndex)
    self.assertListEqual(sorted(list(trueNeighbors)),
                         sorted(list(neighbors)))

    dimensions = numpy.array([5, 7, 9])
    layout1D = numpy.array(range(numpy.prod(dimensions)))
    layout = numpy.reshape(layout1D, dimensions)
    radius = 3
    x = 0
    y = 0
    z = 3
    columnIndex = layout[z][y][x]
    neighbors = sp._getNeighborsND(columnIndex, dimensions, radius,
                                   wrapAround=True)
    trueNeighbors = set()
    for i in range(-radius, radius+1):
      for j in range(-radius, radius+1):
        for k in range(-radius, radius+1):
          zprime = (z + i) % dimensions[0]
          yprime = (y + j) % dimensions[1]
          xprime = (x + k) % dimensions[2]
          trueNeighbors.add(
            layout[zprime][yprime][xprime]
          )
    trueNeighbors.remove(columnIndex)
    self.assertListEqual(sorted(list(trueNeighbors)),
                         sorted(list(neighbors)))

    dimensions = numpy.array([5, 10, 7, 6])
    layout1D = numpy.array(range(numpy.prod(dimensions)))
    layout = numpy.reshape(layout1D, dimensions)
    radius = 4
    w = 2
    x = 5
    y = 6
    z = 2
    columnIndex = layout[z][y][x][w]
    neighbors = sp._getNeighborsND(columnIndex, dimensions, radius,
                                   wrapAround=True)
    trueNeighbors = set()
    for i in range(-radius, radius+1):
      for j in range(-radius, radius+1):
        for k in range(-radius, radius+1):
          for m in range(-radius, radius+1):
            zprime = (z + i) % dimensions[0]
            yprime = (y + j) % dimensions[1]
            xprime = (x + k) % dimensions[2]
            wprime = (w + m) % dimensions[3]
            trueNeighbors.add(layout[zprime][yprime][xprime][wprime])
    trueNeighbors.remove(columnIndex)
    self.assertListEqual(sorted(list(trueNeighbors)), sorted(list(neighbors)))

    # These are all the same tests from 1D
    layout = numpy.array([0, 0, 1, 0, 1, 0, 0,  0])
    layout1D = layout.reshape(-1)
    columnIndex = 3
    dimensions = numpy.array([8])
    radius = 1
    mask = sp._getNeighborsND(columnIndex, dimensions, radius, wrapAround=True)
    negative = set(range(dimensions.prod())) - set(mask)
    self.assertEqual(layout1D[mask].all(), True)
    self.assertEqual(layout1D[list(negative)].any(), False)

    layout = numpy.array([0, 1, 1, 0, 1, 1, 0,  0])
    layout1D = layout.reshape(-1)
    columnIndex = 3
    dimensions = numpy.array([8])
    radius = 2
    mask = sp._getNeighborsND(columnIndex, dimensions, radius, wrapAround=True)
    negative = set(range(dimensions.prod())) - set(mask)
    self.assertEqual(layout1D[mask].all(), True)
    self.assertEqual(layout1D[list(negative)].any(), False)

    # Wrap around
    layout = numpy.array([0, 1, 1, 0, 0, 0, 1,  1])
    layout1D = layout.reshape(-1)
    columnIndex = 0
    dimensions = numpy.array([8])
    radius = 2
    mask = sp._getNeighborsND(columnIndex, dimensions, radius, wrapAround=True)
    negative = set(range(dimensions.prod())) - set(mask)
    self.assertEqual(layout1D[mask].all(), True)
    self.assertEqual(layout1D[list(negative)].any(), False)

    # Radius too big
    layout = numpy.array([1, 1, 1, 1, 1, 1, 0,  1])
    layout1D = layout.reshape(-1)
    columnIndex = 6
    dimensions = numpy.array([8])
    radius = 20
    mask = sp._getNeighborsND(columnIndex, dimensions, radius, wrapAround=True)
    negative = set(range(dimensions.prod())) - set(mask)
    self.assertEqual(layout1D[mask].all(), True)
    self.assertEqual(layout1D[list(negative)].any(), False)


    # These are all the same tests from 2D
    layout = numpy.array([[0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0],
                    [0, 1, 1, 1, 0],
                    [0, 1, 0, 1, 0],
                    [0, 1, 1, 1, 0],
                    [0, 0, 0, 0, 0]])

    layout1D = layout.reshape(-1)
    columnIndex = 3*5 + 2
    dimensions = numpy.array([6, 5])
    radius = 1
    mask = sp._getNeighborsND(columnIndex, dimensions, radius, wrapAround=True)
    negative = set(range(dimensions.prod())) - set(mask)
    self.assertEqual(layout1D[mask].all(), True)
    self.assertEqual(layout1D[list(negative)].any(), False)

    layout = numpy.array([[0, 0, 0, 0, 0],
                          [1, 1, 1, 1, 1],
                          [1, 1, 1, 1, 1],
                          [1, 1, 0, 1, 1],
                          [1, 1, 1, 1, 1],
                          [1, 1, 1, 1, 1]])

    layout1D = layout.reshape(-1)
    columnIndex = 3*5+ 2
    dimensions = numpy.array([6, 5])
    radius = 2
    mask = sp._getNeighbors2D(columnIndex, dimensions, radius, wrapAround=True)
    negative = set(range(dimensions.prod())) - set(mask)
    self.assertEqual(layout1D[mask].all(), True)
    self.assertEqual(layout1D[list(negative)].any(), False)

    # Radius too big
    layout = numpy.array([[1, 1, 1, 1, 1],
                          [1, 1, 1, 1, 1],
                          [1, 1, 1, 1, 1],
                          [1, 1, 0, 1, 1],
                          [1, 1, 1, 1, 1],
                          [1, 1, 1, 1, 1]])

    layout1D = layout.reshape(-1)
    columnIndex = 3*5+ 2
    dimensions = numpy.array([6, 5])
    radius = 7
    mask = sp._getNeighborsND(columnIndex, dimensions, radius, wrapAround=True)
    negative = set(range(dimensions.prod())) - set(mask)
    self.assertEqual(layout1D[mask].all(), True)
    self.assertEqual(layout1D[list(negative)].any(), False)

    # Wrap-around
    layout = numpy.array([[1, 0, 0, 1, 1],
                          [0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0],
                          [1, 0, 0, 1, 1],
                          [1, 0, 0, 1, 0]])

    layout1D = layout.reshape(-1)
    dimensions = numpy.array([6, 5])
    columnIndex = dimensions.prod() -1
    radius = 1
    mask = sp._getNeighborsND(columnIndex, dimensions, radius, wrapAround=True)
    negative = set(range(dimensions.prod())) - set(mask)
    self.assertEqual(layout1D[mask].all(), True)
    self.assertEqual(layout1D[list(negative)].any(), False)


  def testWrite(self):
    sp1 = SpatialPooler(
        inputDimensions=[9],
        columnDimensions=[5],
        potentialRadius=3,
        potentialPct=0.5,
        globalInhibition=False,
        localAreaDensity=-1.0,
        numActiveColumnsPerInhArea=3,
        stimulusThreshold=1,
        synPermInactiveDec=0.01,
        synPermActiveInc=0.1,
        synPermConnected=0.10,
        minPctOverlapDutyCycle=0.1,
        minPctActiveDutyCycle=0.1,
        dutyCyclePeriod=10,
        maxBoost=10.0,
        seed=42,
        spVerbosity=0)
    sp2 = SpatialPooler(
        inputDimensions=[3, 3],
        columnDimensions=[2, 2],
        potentialRadius=5,
        potentialPct=0.4,
        globalInhibition=True,
        localAreaDensity=1.0,
        numActiveColumnsPerInhArea=4,
        stimulusThreshold=2,
        synPermInactiveDec=0.05,
        synPermActiveInc=0.2,
        synPermConnected=0.15,
        minPctOverlapDutyCycle=0.2,
        minPctActiveDutyCycle=0.2,
        dutyCyclePeriod=11,
        maxBoost=14.0,
        seed=10,
        spVerbosity=0)

    # Run a record through before serializing
    inputVector = numpy.array([1, 0, 1, 0, 1, 0, 0, 1, 1])
    activeArray1 = numpy.zeros(5)
    sp1.compute(inputVector, True, activeArray1)

    proto1 = SpatialPoolerProto_capnp.SpatialPoolerProto.new_message()
    sp1.write(proto1)

    # Write the proto to a temp file and read it back into a new proto
    with tempfile.TemporaryFile() as f:
      proto1.write(f)
      f.seek(0)
      proto2 = SpatialPoolerProto_capnp.SpatialPoolerProto.read(f)

    # Load the deserialized proto
    sp2.read(proto2)

    # Check that the two spatial poolers have the same attributes
    self.assertSetEqual(set(sp1.__dict__.keys()), set(sp2.__dict__.keys()))
    for k, v1 in sp1.__dict__.iteritems():
      v2 = getattr(sp2, k)
      if isinstance(v1, numpy.ndarray):
        self.assertEqual(v1.dtype, v2.dtype,
                         "Key %s has differing dtypes: %s vs %s" % (
                             k, v1.dtype, v2.dtype))
        self.assertTrue(numpy.isclose(v1, v2).all(), k)
      elif isinstance(v1, Random) or isinstance(v1, SparseBinaryMatrix):
        pass
      elif isinstance(v1, float):
        self.assertAlmostEqual(v1, v2)
      elif isinstance(v1, numbers.Integral):
        self.assertEqual(long(v1), long(v2), k)
      else:
        self.assertEqual(type(v1), type(v2), k)
        self.assertEqual(v1, v2, k)

    # Run a record through after deserializing and check results match
    activeArray2 = numpy.zeros(5)
    sp1.compute(inputVector, True, activeArray1)
    sp2.compute(inputVector, True, activeArray2)
    indices1 = set(activeArray1.nonzero()[0])
    indices2 = set(activeArray2.nonzero()[0])
    self.assertSetEqual(indices1, indices2)


  def testRandomSPDoesNotLearn(self):

    sp = SpatialPooler(inputDimensions=[5],
                       columnDimensions=[10])
    inputArray = (numpy.random.rand(5) > 0.5).astype(uintDType)
    activeArray = numpy.zeros(sp._numColumns).astype(realDType)
    # Should start off at 0
    self.assertEqual(sp._iterationNum, 0)
    self.assertEqual(sp._iterationLearnNum, 0)

    # Store the initialized state
    initialPerms = copy(sp._permanences)

    sp.compute(inputArray, False, activeArray)
    # Should have incremented general counter but not learning counter
    self.assertEqual(sp._iterationNum, 1)
    self.assertEqual(sp._iterationLearnNum, 0)

    # Check the initial perm state was not modified either
    self.assertEqual(sp._permanences, initialPerms)


  @unittest.skip("Ported from the removed FlatSpatialPooler but fails. \
                  See: https://github.com/numenta/nupic/issues/1897")
  def testActiveColumnsEqualNumActive(self):
    '''
    After feeding in a record the number of active columns should
    always be equal to numActivePerInhArea
    '''

    for i in [1, 10, 50]:
      numActive = i
      inputShape = 10
      sp = SpatialPooler(inputDimensions=[inputShape],
                         columnDimensions=[100],
                         numActiveColumnsPerInhArea=numActive)
      inputArray = (numpy.random.rand(inputShape) > 0.5).astype(uintDType)
      inputArray2 = (numpy.random.rand(inputShape) > 0.8).astype(uintDType)
      activeArray = numpy.zeros(sp._numColumns).astype(realDType)

      # Default, learning on
      sp.compute(inputArray, True, activeArray)
      sp.compute(inputArray2, True, activeArray)
      self.assertEqual(sum(activeArray), numActive)

      # learning OFF
      sp.compute(inputArray, False, activeArray)
      sp.compute(inputArray2, False, activeArray)
      self.assertEqual(sum(activeArray), numActive)


if __name__ == "__main__":
  unittest.main()
