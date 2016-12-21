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

# Disable since test code accesses private members in the class to be tested
# pylint: disable=W0212

import numbers
import tempfile
import unittest
from copy import copy

from mock import Mock
import numpy

from nupic.support.unittesthelpers.algorithm_test_helpers import (
  getNumpyRandomGenerator, getSeed)
from nupic.bindings.math import GetNTAReal, Random
from nupic.research.spatial_pooler import (BinaryCorticalColumns,
                                           CorticalColumns,
                                           SpatialPooler)

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.proto import SpatialPoolerProto_capnp

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
      "dutyCyclePeriod": 10,
      "boostStrength": 10.0,
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
        synPermInactiveDec=0.1,
        synPermActiveInc=0.1,
        synPermConnected=0.10,
        minPctOverlapDutyCycle=0.1,
        dutyCyclePeriod=10,
        boostStrength=10.0,
        seed=getSeed(),
        spVerbosity=0)

    sp._potentialPools = BinaryCorticalColumns(numpy.ones([sp._numColumns,
                                                           sp._numInputs]))
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
        dutyCyclePeriod=10,
        boostStrength=10.0,
        seed=getSeed(),
        spVerbosity=0)

    sp._inhibitColumns = Mock(return_value = numpy.array(range(5)))

    inputVector = numpy.ones(sp._numInputs)
    activeArray = numpy.zeros(5)
    for i in xrange(20):
      sp.compute(inputVector, True, activeArray)

    for columnIndex in xrange(sp._numColumns):
      potential = sp._potentialPools[columnIndex]
      perm = sp._permanences.getRow(columnIndex)
      self.assertEqual(list(perm), list(potential))


  def testZeroOverlap_NoStimulusThreshold_GlobalInhibition(self):
    """When stimulusThreshold is 0, allow columns without any overlap to become
    active. This test focuses on the global inhibition code path."""
    inputSize = 10
    nColumns = 20
    sp = SpatialPooler(inputDimensions=[inputSize],
                       columnDimensions=[nColumns],
                       potentialRadius=10,
                       globalInhibition=True,
                       numActiveColumnsPerInhArea=3,
                       stimulusThreshold=0,
                       seed=getSeed())

    inputVector = numpy.zeros(inputSize)
    activeArray = numpy.zeros(nColumns)
    sp.compute(inputVector, True, activeArray)

    self.assertEqual(3, len(activeArray.nonzero()[0]))


  def testZeroOverlap_StimulusThreshold_GlobalInhibition(self):
    """When stimulusThreshold is > 0, don't allow columns without any overlap to
    become active. This test focuses on the global inhibition code path."""
    inputSize = 10
    nColumns = 20
    sp = SpatialPooler(inputDimensions=[inputSize],
                       columnDimensions=[nColumns],
                       potentialRadius=10,
                       globalInhibition=True,
                       numActiveColumnsPerInhArea=3,
                       stimulusThreshold=1,
                       seed=getSeed())

    inputVector = numpy.zeros(inputSize)
    activeArray = numpy.zeros(nColumns)
    sp.compute(inputVector, True, activeArray)

    self.assertEqual(0, len(activeArray.nonzero()[0]))


  def testZeroOverlap_NoStimulusThreshold_LocalInhibition(self):
    """When stimulusThreshold is 0, allow columns without any overlap to become
    active. This test focuses on the local inhibition code path."""
    inputSize = 10
    nColumns = 20
    sp = SpatialPooler(inputDimensions=[inputSize],
                       columnDimensions=[nColumns],
                       potentialRadius=5,
                       globalInhibition=False,
                       numActiveColumnsPerInhArea=1,
                       stimulusThreshold=0,
                       seed=getSeed())

    # This exact number of active columns is determined by the inhibition
    # radius, which changes based on the random synapses (i.e. weird math).
    # Force it to a known number.
    sp.setInhibitionRadius(2);

    inputVector = numpy.zeros(inputSize)
    activeArray = numpy.zeros(nColumns)
    sp.compute(inputVector, True, activeArray)

    self.assertEqual(len(activeArray.nonzero()[0]), 6)


  def testZeroOverlap_StimulusThreshold_LocalInhibition(self):
    """When stimulusThreshold is > 0, don't allow columns without any overlap to
    become active. This test focuses on the local inhibition code path."""
    inputSize = 10
    nColumns = 20
    sp = SpatialPooler(inputDimensions=[inputSize],
                       columnDimensions=[nColumns],
                       potentialRadius=10,
                       globalInhibition=False,
                       numActiveColumnsPerInhArea=3,
                       stimulusThreshold=1,
                       seed=getSeed())

    inputVector = numpy.zeros(inputSize)
    activeArray = numpy.zeros(nColumns)
    sp.compute(inputVector, True, activeArray)

    self.assertEqual(0, len(activeArray.nonzero()[0]))


  def testOverlapsOutput(self):
    """Checks that overlaps and boostedOverlaps are correctly returned"""

    sp = SpatialPooler(inputDimensions=[5],
                       columnDimensions=[3],
                       potentialRadius=5,
                       numActiveColumnsPerInhArea=5,
                       globalInhibition=True,
                       seed=1,
                       synPermActiveInc=0.1,
                       synPermInactiveDec=0.1)

    inputVector = numpy.ones(5)
    activeArray = numpy.zeros(3)

    expOutput = numpy.array([2, 0, 0], dtype=realDType)
    boostFactors = 2.0 * numpy.ones(3)
    sp.setBoostFactors(boostFactors)
    sp.compute(inputVector, True, activeArray)
    overlaps = sp.getOverlaps()
    boostedOverlaps = sp.getBoostedOverlaps()

    for i in range(sp.getNumColumns()):
      self.assertEqual(overlaps[i], expOutput[i])

    for i in range(sp.getNumColumns()):
      self.assertEqual(boostedOverlaps[i], (2 * expOutput[i]))


  def testExactOutput(self):
    """
    Given a specific input and initialization params the SP should return this
    exact output.

    Previously output varied between platforms (OSX/Linux etc)
    """

    expectedOutput = [57, 80, 135, 215, 281, 350, 431, 534, 556, 565, 574, 595,
                      663, 759, 777, 823, 932, 933, 1031, 1126, 1184, 1262,
                      1468, 1479, 1516, 1531, 1585, 1672, 1793, 1807, 1906,
                      1927, 1936, 1939, 1940, 1944, 1957, 1978, 2040, 2047]

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
      dutyCyclePeriod = 1000,
      boostStrength = 10.0,
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
    self.assertEqual(sorted(spOutput), expectedOutput)


  def testStripNeverLearned(self):
    sp = self._sp

    sp._activeDutyCycles = numpy.array([0.5, 0.1, 0, 0.2, 0.4, 0])
    activeArray = numpy.array([1, 1, 1, 0, 1, 0])
    sp.stripUnlearnedColumns(activeArray)
    stripped = numpy.where(activeArray == 1)[0]
    trueStripped = [0, 1, 4]
    self.assertListEqual(trueStripped, list(stripped))

    sp._activeDutyCycles = numpy.array([0.9, 0, 0, 0, 0.4, 0.3])
    activeArray = numpy.ones(6)
    sp.stripUnlearnedColumns(activeArray)
    stripped = numpy.where(activeArray == 1)[0]
    trueStripped = [0, 4, 5]
    self.assertListEqual(trueStripped, list(stripped))

    sp._activeDutyCycles = numpy.array([0, 0, 0, 0, 0, 0])
    activeArray = numpy.ones(6)
    sp.stripUnlearnedColumns(activeArray)
    stripped = numpy.where(activeArray == 1)[0]
    trueStripped = []
    self.assertListEqual(trueStripped, list(stripped))

    sp._activeDutyCycles = numpy.ones(6)
    activeArray = numpy.ones(6)
    sp.stripUnlearnedColumns(activeArray)
    stripped = numpy.where(activeArray == 1)[0]
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

    # Test 2D with some input dimensions smaller than column dimensions.
    params.update({
      "columnDimensions": [4, 4],
      "inputDimensions": [3, 5]
    })

    sp = SpatialPooler(**params)

    self.assertEqual(sp._mapColumn(0), 0)
    self.assertEqual(sp._mapColumn(3), 4)
    self.assertEqual(sp._mapColumn(15), 14)


  def testMapPotential1D(self):
    params = self._params.copy()
    params.update({
      "inputDimensions": [12],
      "columnDimensions": [4],
      "potentialRadius": 2,
      "wrapAround": False
    })

    # Test without wrapAround and potentialPct = 1
    params["potentialPct"] = 1
    sp = SpatialPooler(**params)

    expectedMask = [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0]
    mask = sp._mapPotential(0)
    self.assertListEqual(mask.tolist(), expectedMask)

    expectedMask = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0]
    mask = sp._mapPotential(2)
    self.assertListEqual(mask.tolist(), expectedMask)

    # Test with wrapAround and potentialPct = 1
    params["potentialPct"] = 1
    params["wrapAround"] = True
    sp = SpatialPooler(**params)

    expectedMask = [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1]
    mask = sp._mapPotential(0)
    self.assertListEqual(mask.tolist(), expectedMask)

    expectedMask = [1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1]
    mask = sp._mapPotential(3)
    self.assertListEqual(mask.tolist(), expectedMask)

    # Test with potentialPct < 1
    params["potentialPct"] = 0.5
    sp = SpatialPooler(**params)

    supersetMask = numpy.array([1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1])
    mask = sp._mapPotential(0)
    self.assertEqual(numpy.sum(mask), 3)
    unionMask = supersetMask | mask.astype(int)
    self.assertListEqual(unionMask.tolist(), supersetMask.tolist())


  def testMapPotential2D(self):
    params = self._params.copy()
    params.update({
      "columnDimensions": [2, 4],
      "inputDimensions": [6, 12],
      "potentialRadius": 1,
      "potentialPct": 1,
      "wrapAround": False,
    })

    # Test without wrapAround
    sp = SpatialPooler(**params)

    trueIndicies = [0, 12, 24,
                    1, 13, 25,
                    2, 14, 26]
    mask = sp._mapPotential(0)
    self.assertSetEqual(set(numpy.flatnonzero(mask).tolist()), set(trueIndicies))

    trueIndicies = [6, 18, 30,
                    7, 19, 31,
                    8, 20, 32]
    mask = sp._mapPotential(2)
    self.assertSetEqual(set(numpy.flatnonzero(mask).tolist()), set(trueIndicies))

    # Test with wrapAround
    params.update({
      "potentialRadius": 2,
      "wrapAround": True,
    })
    sp = SpatialPooler(**params)

    trueIndicies = [71, 11, 23, 35, 47,
                    60,  0, 12, 24, 36,
                    61,  1, 13, 25, 37,
                    62,  2, 14, 26, 38,
                    63,  3, 15, 27, 39]
    mask = sp._mapPotential(0)
    self.assertSetEqual(set(numpy.flatnonzero(mask).tolist()), set(trueIndicies))

    trueIndicies = [68,  8, 20, 32, 44,
                    69,  9, 21, 33, 45,
                    70, 10, 22, 34, 46,
                    71, 11, 23, 35, 47,
                    60,  0, 12, 24, 36]
    mask = sp._mapPotential(3)
    self.assertSetEqual(set(numpy.flatnonzero(mask).tolist()), set(trueIndicies))


  def testMapPotential1Column1Input(self):
    params = self._params.copy()
    params.update({
      "inputDimensions": [1],
      "columnDimensions": [1],
      "potentialRadius": 2,
      "wrapAround": False,
    })

    # Test without wrapAround and potentialPct = 1
    params["potentialPct"] = 1
    sp = SpatialPooler(**params)

    expectedMask = [1]
    mask = sp._mapPotential(0)
    self.assertListEqual(mask.tolist(), expectedMask)


  def testInhibitColumns(self):
    sp = self._sp
    sp._inhibitColumnsGlobal = Mock(return_value = 1)
    sp._inhibitColumnsLocal = Mock(return_value = 2)
    randomState = getNumpyRandomGenerator()
    sp._numColumns = 5
    sp._inhibitionRadius = 10
    sp._columnDimensions = [5]
    overlaps = randomState.random_sample(sp._numColumns).astype(realDType)

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
    overlaps = randomState.random_sample(sp._numColumns).astype(realDType)
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
    overlaps = randomState.random_sample(sp._numColumns).astype(realDType)
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
    overlaps = randomState.random_sample(sp._numColumns).astype(realDType)
    sp._inhibitColumns(overlaps)
    self.assertEqual(False, sp._inhibitColumnsGlobal.called)
    self.assertEqual(True, sp._inhibitColumnsLocal.called)
    density = sp._inhibitColumnsLocal.call_args[0][1]
    self.assertEqual(trueDensity, density)


  def testUpdateBoostFactors(self):
    sp = self._sp
    sp._boostStrength = 10.0
    sp._numColumns = 6
    sp._activeDutyCycles = numpy.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1])
    sp._boostFactors = numpy.zeros(sp._numColumns)
    sp._updateBoostFactors()
    numpy.testing.assert_almost_equal(
      sp._boostFactors, [1.0, 1.0, 1.0, 1.0, 1.0, 1.0])

    sp._boostStrength = 10.0
    sp._numColumns = 6
    sp._columnDimensions = numpy.array([6])
    sp._numActiveColumnsPerInhArea = 1
    sp._inhibitionRadius = 5
    sp._wrapAround = True
    sp._activeDutyCycles = numpy.array([0.1, 0.3, 0.02, 0.04, 0.7, 0.12])
    sp._updateBoostFactors()
    numpy.testing.assert_almost_equal(
      sp._boostFactors,
      [3.1059927, 0.4203504, 6.912514, 5.6594878, 0.007699, 2.5429718])

    sp._boostStrength = 2.0
    sp._numColumns = 6
    sp._activeDutyCycles = numpy.array([0.1, 0.3, 0.02, 0.04, 0.7, 0.12])
    sp._updateBoostFactors()
    numpy.testing.assert_almost_equal(
      sp._boostFactors,
      [1.2544117, 0.8408573, 1.4720657, 1.4143452, 0.3778215, 1.2052255])

    sp._globalInhibition = True
    sp._boostStrength = 10.0
    sp._numColumns = 6
    sp._numActiveColumnsPerInhArea = 1
    sp._inhibitionRadius = 3
    sp._activeDutyCycles = numpy.array([0.1, 0.3, 0.02, 0.04, 0.7, 0.12])
    sp._updateBoostFactors()

    numpy.testing.assert_almost_equal(
      sp._boostFactors,
      [1.947734, 0.2635971, 4.3347618, 3.5490028, 0.0048279, 1.5946698])


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
      BinaryCorticalColumns([[0, 1, 0, 1, 0, 1, 0, 1],
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
    sp._connectedSynapses = (
      BinaryCorticalColumns([[0, 1, 0, 1, 0, 1, 0, 1],
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

    sp._numColumns = 7
    sp._columnDimensions = numpy.array([7])
    sp._numInputs = 20
    sp._inputDimensions = numpy.array([5, 4])
    sp._connectedSynapses = BinaryCorticalColumns(sp._numInputs)
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
    for columnIndex in xrange(sp._numColumns):
      sp._connectedSynapses.replace(
        columnIndex, connected[columnIndex].reshape(-1).nonzero()[0]
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
    sp._connectedSynapses = BinaryCorticalColumns(sp._numInputs)
    sp._connectedSynapses.resize(sp._numColumns, sp._numInputs)

    connected = numpy.zeros(sp._numInputs).reshape(sp._inputDimensions)
    connected[1][0][1][0] = 1
    connected[1][0][1][1] = 1
    connected[3][2][1][0] = 1
    connected[3][0][1][0] = 1
    connected[1][0][1][3] = 1
    connected[2][2][1][0] = 1
    # span:   3  3  1  4, avg = 11/4
    sp._connectedSynapses.replace(0, connected.reshape(-1).nonzero()[0])

    connected = numpy.zeros(sp._numInputs).reshape(sp._inputDimensions)
    connected[2][0][1][0] = 1
    connected[2][0][0][0] = 1
    connected[3][0][0][0] = 1
    connected[3][0][1][0] = 1
    # spn:    2  1  2  1, avg = 6/4
    sp._connectedSynapses.replace(1, connected.reshape(-1).nonzero()[0])

    connected = numpy.zeros(sp._numInputs).reshape(sp._inputDimensions)
    connected[0][0][1][4] = 1
    connected[0][0][0][3] = 1
    connected[0][0][0][1] = 1
    connected[1][0][0][2] = 1
    connected[0][0][1][1] = 1
    connected[3][3][1][1] = 1
    # span:   4  4  2  4, avg = 14/4
    sp._connectedSynapses.replace(2, connected.reshape(-1).nonzero()[0])

    connected = numpy.zeros(sp._numInputs).reshape(sp._inputDimensions)
    connected[3][3][1][4] = 1
    connected[0][0][0][0] = 1
    # span:   4  4  2  5, avg = 15/4
    sp._connectedSynapses.replace(3, connected.reshape(-1).nonzero()[0])

    connected = numpy.zeros(sp._numInputs).reshape(sp._inputDimensions)
    # span:   0  0  0  0, avg = 0
    sp._connectedSynapses.replace(4, connected.reshape(-1).nonzero()[0])

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

    sp._potentialPools = BinaryCorticalColumns(
       [[1, 1, 1, 1, 0, 0, 0, 0],
        [1, 0, 0, 0, 1, 1, 0, 1],
        [0, 0, 1, 0, 1, 1, 1, 0],
        [1, 1, 1, 0, 0, 0, 1, 0],
        [1, 1, 1, 1, 1, 1, 1, 1]])

    sp._permanences = CorticalColumns(
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
    # wrapAround=False
    sp = SpatialPooler(inputDimensions=(5,),
                       columnDimensions=(8,),
                       globalInhibition=False,
                       wrapAround=False)

    sp.setInhibitionRadius(1)
    sp.setOverlapDutyCycles([0.7, 0.1, 0.5, 0.01, 0.78, 0.55, 0.1, 0.001])
    sp.setActiveDutyCycles([0.9, 0.3, 0.5, 0.7, 0.1, 0.01, 0.08, 0.12])
    sp.setMinPctOverlapDutyCycles(0.2);
    sp._updateMinDutyCyclesLocal()

    resultMinOverlapDutyCycles = numpy.zeros(sp.getNumColumns())
    sp.getMinOverlapDutyCycles(resultMinOverlapDutyCycles)
    for actual, expected in zip(resultMinOverlapDutyCycles,
                                [0.14, 0.14, 0.1, 0.156, 0.156, 0.156, 0.11, 0.02]):
      self.assertAlmostEqual(actual, expected)

    # wrapAround=True
    sp = SpatialPooler(inputDimensions=(5,),
                       columnDimensions=(8,),
                       globalInhibition=False,
                       wrapAround=True)

    sp.setInhibitionRadius(1)
    sp.setOverlapDutyCycles([0.7, 0.1, 0.5, 0.01, 0.78, 0.55, 0.1, 0.001])
    sp.setActiveDutyCycles([0.9, 0.3, 0.5, 0.7, 0.1, 0.01, 0.08, 0.12])
    sp.setMinPctOverlapDutyCycles(0.2);
    sp._updateMinDutyCyclesLocal()

    resultMinOverlapDutyCycles = numpy.zeros(sp.getNumColumns())
    sp.getMinOverlapDutyCycles(resultMinOverlapDutyCycles)
    for actual, expected in zip(resultMinOverlapDutyCycles,
                                [0.14, 0.14, 0.1, 0.156, 0.156, 0.156, 0.11, 0.14]):
      self.assertAlmostEqual(actual, expected)


  def testUpdateMinDutyCyclesGlobal(self):
    sp = self._sp
    sp._minPctOverlapDutyCycles = 0.01
    sp._numColumns = 5
    sp._overlapDutyCycles = numpy.array([0.06, 1, 3, 6, 0.5])
    sp._activeDutyCycles = numpy.array([0.6, 0.07, 0.5, 0.4, 0.3])
    sp._updateMinDutyCyclesGlobal()
    trueMinOverlapDutyCycles = sp._numColumns*[0.01*6]
    for i in xrange(sp._numColumns):
      self.assertAlmostEqual(trueMinOverlapDutyCycles[i],
                             sp._minOverlapDutyCycles[i])

    sp._minPctOverlapDutyCycles = 0.015
    sp._numColumns = 5
    sp._overlapDutyCycles = numpy.array([0.86, 2.4, 0.03, 1.6, 1.5])
    sp._activeDutyCycles = numpy.array([0.16, 0.007, 0.15, 0.54, 0.13])
    sp._updateMinDutyCyclesGlobal()
    trueMinOverlapDutyCycles = sp._numColumns*[0.015*2.4]
    for i in xrange(sp._numColumns):
      self.assertAlmostEqual(trueMinOverlapDutyCycles[i],
                             sp._minOverlapDutyCycles[i])

    sp._minPctOverlapDutyCycles = 0.015
    sp._numColumns = 5
    sp._overlapDutyCycles = numpy.zeros(5)
    sp._activeDutyCycles = numpy.zeros(5)
    sp._updateMinDutyCyclesGlobal()
    trueMinOverlapDutyCycles = sp._numColumns * [0]
    for i in xrange(sp._numColumns):
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

    sp._potentialPools = BinaryCorticalColumns(
        [[1, 1, 1, 1, 0, 0, 0, 0],
         [1, 0, 0, 0, 1, 1, 0, 1],
         [0, 0, 1, 0, 0, 0, 1, 0],
         [1, 0, 0, 0, 0, 0, 1, 0]])

    inputVector = numpy.array([1, 0, 0, 1, 1, 0, 1, 0])
    activeColumns = numpy.array([0, 1, 2])

    sp._permanences = CorticalColumns(
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

    sp._potentialPools = BinaryCorticalColumns(
        [[1, 1, 1, 0, 0, 0, 0, 0],
         [0, 1, 1, 1, 0, 0, 0, 0],
         [0, 0, 1, 1, 1, 0, 0, 0],
         [1, 0, 0, 0, 0, 0, 1, 0]])

    inputVector = numpy.array([1, 0, 0, 1, 1, 0, 1, 0])
    activeColumns = numpy.array([0, 1, 2])

    sp._permanences = CorticalColumns(
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
    sp._permanences = CorticalColumns(
        [[0.0, 0.11, 0.095, 0.092, 0.01],
         [0.12, 0.15, 0.02, 0.12, 0.09],
         [0.51, 0.081, 0.025, 0.089, 0.31],
         [0.18, 0.0601, 0.11, 0.011, 0.03],
         [0.011, 0.011, 0.011, 0.011, 0.011]])

    sp._connectedSynapses = BinaryCorticalColumns([[0, 1, 0, 0, 0],
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
    for columnIndex in xrange(sp._numColumns):
      sp._updatePermanencesForColumn(permanences[columnIndex], columnIndex)
      self.assertListEqual(
        trueConnectedSynapses[columnIndex],
        list(sp._connectedSynapses[columnIndex])
      )
    self.assertListEqual(trueConnectedCounts, list(sp._connectedCounts))


  def testCalculateOverlap(self):
    """
    Test that column computes overlap and percent overlap correctly.
    """
    sp = SpatialPooler(inputDimensions = [10],
                       columnDimensions = [5])
    sp._connectedSynapses = (
      BinaryCorticalColumns([[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                             [0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
                             [0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
                             [0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
                             [0, 0, 0, 0, 0, 0, 0, 0, 1, 1]]))
    sp._connectedCounts = numpy.array([10.0, 8.0, 6.0, 4.0, 2.0])
    inputVector = numpy.zeros(sp._numInputs, dtype='float32')
    overlaps = sp._calculateOverlap(inputVector)
    overlapsPct = sp._calculateOverlapPct(overlaps)
    trueOverlaps = list(numpy.array([0, 0, 0, 0, 0], dtype=realDType))
    trueOverlapsPct = list(numpy.array([0, 0, 0, 0, 0]))
    self.assertListEqual(list(overlaps), trueOverlaps)
    self.assertListEqual(list(overlapsPct), trueOverlapsPct)

    sp._connectedSynapses = (
      BinaryCorticalColumns([[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                             [0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
                             [0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
                             [0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
                             [0, 0, 0, 0, 0, 0, 0, 0, 1, 1]]))
    sp._connectedCounts = numpy.array([10.0, 8.0, 6.0, 4.0, 2.0])
    inputVector = numpy.ones(sp._numInputs, dtype='float32')
    overlaps = sp._calculateOverlap(inputVector)
    overlapsPct = sp._calculateOverlapPct(overlaps)
    trueOverlaps = list(numpy.array([10, 8, 6, 4, 2], dtype=realDType))
    trueOverlapsPct = list(numpy.array([1, 1, 1, 1, 1]))
    self.assertListEqual(list(overlaps), trueOverlaps)
    self.assertListEqual(list(overlapsPct), trueOverlapsPct)

    sp._connectedSynapses = (
      BinaryCorticalColumns([[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                             [0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
                             [0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
                             [0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
                             [0, 0, 0, 0, 0, 0, 0, 0, 1, 1]]))
    sp._connectedCounts = numpy.array([10.0, 8.0, 6.0, 4.0, 2.0])
    inputVector = numpy.zeros(sp._numInputs, dtype='float32')
    inputVector[9] = 1
    overlaps = sp._calculateOverlap(inputVector)
    overlapsPct = sp._calculateOverlapPct(overlaps)
    trueOverlaps = list(numpy.array([1, 1, 1, 1, 1], dtype=realDType))
    trueOverlapsPct = list(numpy.array([0.1, 0.125, 1.0/6, 0.25, 0.5]))
    self.assertListEqual(list(overlaps), trueOverlaps)
    self.assertListEqual(list(overlapsPct), trueOverlapsPct)

    # Zig-zag
    sp._connectedSynapses = (
      BinaryCorticalColumns([[1, 0, 0, 0, 0, 1, 0, 0, 0, 0],
                             [0, 1, 0, 0, 0, 0, 1, 0, 0, 0],
                             [0, 0, 1, 0, 0, 0, 0, 1, 0, 0],
                             [0, 0, 0, 1, 0, 0, 0, 0, 1, 0],
                             [0, 0, 0, 0, 1, 0, 0, 0, 0, 1]]))
    sp._connectedCounts = numpy.array([2.0, 2.0, 2.0, 2.0, 2.0])
    inputVector = numpy.zeros(sp._numInputs, dtype='float32')
    inputVector[range(0, 10, 2)] = 1
    overlaps = sp._calculateOverlap(inputVector)
    overlapsPct = sp._calculateOverlapPct(overlaps)
    trueOverlaps = list(numpy.array([1, 1, 1, 1, 1], dtype=realDType))
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

    minThresh = 0.0
    maxThresh = sp._synPermMax
    self.assertEqual(numpy.logical_and((perm >= minThresh),
                                       (perm <= maxThresh)).all(), True)


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
    overlaps = numpy.array([1, 2, 1, 4, 8, 3, 12, 5, 4, 1], dtype=realDType)
    active = list(sp._inhibitColumnsGlobal(overlaps, density))
    trueActive = numpy.zeros(sp._numColumns)
    trueActive = [4, 6, 7]
    self.assertListEqual(list(trueActive), sorted(active)) # ignore order of columns

    density = 0.5
    sp._numColumns = 10
    overlaps = numpy.array(range(10), dtype=realDType)
    active = list(sp._inhibitColumnsGlobal(overlaps, density))
    trueActive = numpy.zeros(sp._numColumns)
    trueActive = range(5, 10)
    self.assertListEqual(trueActive, sorted(active))


  def testInhibitColumnsLocal(self):
    sp = self._sp
    density = 0.5
    sp._numColumns = 10
    sp._columnDimensions = numpy.array([sp._numColumns])
    sp._inhibitionRadius = 2
    overlaps = numpy.array([1, 2, 7, 0, 3, 4, 16, 1, 1.5, 1.7], dtype=realDType)
                        #   L  W  W  L  L  W  W   L   W    W (wrapAround=True)
                        #   L  W  W  L  L  W  W   L   L    W (wrapAround=False)

    sp._wrapAround = True
    trueActive = [1, 2, 5, 6, 8, 9]
    active = list(sp._inhibitColumnsLocal(overlaps, density))
    self.assertListEqual(trueActive, sorted(active))

    sp._wrapAround = False
    trueActive = [1, 2, 5, 6, 9]
    active = list(sp._inhibitColumnsLocal(overlaps, density))
    self.assertListEqual(trueActive, sorted(active))

    density = 0.5
    sp._numColumns = 10
    sp._columnDimensions = numpy.array([sp._numColumns])
    sp._inhibitionRadius = 3
    overlaps = numpy.array([1, 2, 7, 0, 3, 4, 16, 1, 1.5, 1.7], dtype=realDType)
                        #   L  W  W  L  W  W  W   L   L    W (wrapAround=True)
                        #   L  W  W  L  W  W  W   L   L    L (wrapAround=False)
    sp._wrapAround = True
    trueActive = [1, 2, 4, 5, 6, 9]
    active = list(sp._inhibitColumnsLocal(overlaps, density))
    self.assertListEqual(trueActive, active)

    sp._wrapAround = False
    trueActive = [1, 2, 4, 5, 6, 9]
    active = list(sp._inhibitColumnsLocal(overlaps, density))
    self.assertListEqual(trueActive, active)

    # Test add to winners
    density = 0.3333
    sp._numColumns = 10
    sp._columnDimensions = numpy.array([sp._numColumns])
    sp._inhibitionRadius = 3
    overlaps = numpy.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1], dtype=realDType)
                        #   W  W  L  L  W  W  L  L  L  L (wrapAround=True)
                        #   W  W  L  L  W  W  L  L  W  L (wrapAround=False)

    sp._wrapAround = True
    trueActive = [0, 1, 4, 5]
    active = list(sp._inhibitColumnsLocal(overlaps, density))
    self.assertListEqual(trueActive, sorted(active))

    sp._wrapAround = False
    trueActive = [0, 1, 4, 5, 8]
    active = list(sp._inhibitColumnsLocal(overlaps, density))
    self.assertListEqual(trueActive, sorted(active))


  @unittest.skipUnless(
      capnp, "pycapnp is not installed, skipping serialization test.")
  def testWriteRead(self):
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
        dutyCyclePeriod=10,
        boostStrength=10.0,
        seed=42,
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
    sp2 = SpatialPooler.read(proto2)

    ephemeral = set(["_boostedOverlaps", "_overlaps"])

    # Check that the two spatial poolers have the same attributes
    self.assertSetEqual(set(sp1.__dict__.keys()), set(sp2.__dict__.keys()))
    for k, v1 in sp1.__dict__.iteritems():
      v2 = getattr(sp2, k)
      if k in ephemeral:
        continue
      if isinstance(v1, numpy.ndarray):
        self.assertEqual(v1.dtype, v2.dtype,
                         "Key %s has differing dtypes: %s vs %s" % (
                             k, v1.dtype, v2.dtype))
        self.assertTrue(numpy.isclose(v1, v2).all(), k)
      elif isinstance(v1, Random) or isinstance(v1, BinaryCorticalColumns):
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
