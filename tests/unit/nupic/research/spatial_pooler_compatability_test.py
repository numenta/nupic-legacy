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

import cPickle as pickle
import numpy
import unittest2 as unittest
import time
import traceback

from nupic.support.unittesthelpers.algorithm_test_helpers \
     import getNumpyRandomGenerator, CreateSP, convertPermanences
from nupic.research.spatial_pooler import SpatialPooler as PySpatialPooler
from nupic.bindings.algorithms import SpatialPooler as CPPSpatialPooler
from nupic.bindings.math import GetNTAReal, Random as NupicRandom

realType = GetNTAReal()
uintType = "uint32"
numRecords = 100



class SpatialPoolerCompatibilityTest(unittest.TestCase):
  """
  Tests to ensure that the PY and CPP implementations of the spatial pooler
  are functionally identical.
  """

  def setUp(self):
    # Set to 1 for more verbose debugging output
    self.verbosity = 1


  def assertListAlmostEqual(self, alist, blist):
    self.assertEqual(len(alist), len(blist))
    for a, b in zip(alist, blist):
      diff = abs(a - b)
      self.assertLess(diff, 1e-4)


  def compare(self, pySp, cppSp):
    self.assertAlmostEqual(pySp.getNumColumns(),
                           cppSp.getNumColumns())
    self.assertAlmostEqual(pySp.getNumInputs(),
                           cppSp.getNumInputs())
    self.assertAlmostEqual(pySp.getPotentialRadius(),
                           cppSp.getPotentialRadius())
    self.assertAlmostEqual(pySp.getPotentialPct(),
                           cppSp.getPotentialPct())
    self.assertAlmostEqual(pySp.getGlobalInhibition(),
                           cppSp.getGlobalInhibition())
    self.assertAlmostEqual(pySp.getNumActiveColumnsPerInhArea(),
                           cppSp.getNumActiveColumnsPerInhArea())
    self.assertAlmostEqual(pySp.getLocalAreaDensity(),
                           cppSp.getLocalAreaDensity())
    self.assertAlmostEqual(pySp.getStimulusThreshold(),
                           cppSp.getStimulusThreshold())
    self.assertAlmostEqual(pySp.getInhibitionRadius(),
                           cppSp.getInhibitionRadius())
    self.assertAlmostEqual(pySp.getDutyCyclePeriod(),
                           cppSp.getDutyCyclePeriod())
    self.assertAlmostEqual(pySp.getBoostStrength(),
                           cppSp.getBoostStrength())
    self.assertAlmostEqual(pySp.getIterationNum(),
                           cppSp.getIterationNum())
    self.assertAlmostEqual(pySp.getIterationLearnNum(),
                           cppSp.getIterationLearnNum())
    self.assertAlmostEqual(pySp.getSpVerbosity(),
                           cppSp.getSpVerbosity())
    self.assertAlmostEqual(pySp.getUpdatePeriod(),
                           cppSp.getUpdatePeriod())
    self.assertAlmostEqual(pySp.getSynPermTrimThreshold(),
                           cppSp.getSynPermTrimThreshold())
    self.assertAlmostEqual(pySp.getSynPermActiveInc(),
                           cppSp.getSynPermActiveInc())
    self.assertAlmostEqual(pySp.getSynPermInactiveDec(),
                           cppSp.getSynPermInactiveDec())
    self.assertAlmostEqual(pySp.getSynPermBelowStimulusInc(),
                           cppSp.getSynPermBelowStimulusInc())
    self.assertAlmostEqual(pySp.getSynPermConnected(),
                           cppSp.getSynPermConnected())
    self.assertAlmostEqual(pySp.getMinPctOverlapDutyCycles(),
                           cppSp.getMinPctOverlapDutyCycles())

    numColumns = pySp.getNumColumns()
    numInputs = pySp.getNumInputs()

    pyBoost = numpy.zeros(numColumns).astype(realType)
    cppBoost = numpy.zeros(numColumns).astype(realType)
    pySp.getBoostFactors(pyBoost)
    cppSp.getBoostFactors(cppBoost)
    self.assertListAlmostEqual(list(pyBoost), list(cppBoost))

    pyOverlap = numpy.zeros(numColumns).astype(realType)
    cppOverlap = numpy.zeros(numColumns).astype(realType)
    pySp.getOverlapDutyCycles(pyOverlap)
    cppSp.getOverlapDutyCycles(cppOverlap)
    self.assertListAlmostEqual(list(pyOverlap), list(cppOverlap))

    pyActive = numpy.zeros(numColumns).astype(realType)
    cppActive = numpy.zeros(numColumns).astype(realType)
    pySp.getActiveDutyCycles(pyActive)
    cppSp.getActiveDutyCycles(cppActive)
    self.assertListAlmostEqual(list(pyActive), list(cppActive))

    pyMinOverlap = numpy.zeros(numColumns).astype(realType)
    cppMinOverlap = numpy.zeros(numColumns).astype(realType)
    pySp.getMinOverlapDutyCycles(pyMinOverlap)
    cppSp.getMinOverlapDutyCycles(cppMinOverlap)
    self.assertListAlmostEqual(list(pyMinOverlap), list(cppMinOverlap))

    for i in xrange(pySp.getNumColumns()):
      if self.verbosity > 2: print "Column:",i
      pyPot = numpy.zeros(numInputs).astype(uintType)
      cppPot = numpy.zeros(numInputs).astype(uintType)
      pySp.getPotential(i, pyPot)
      cppSp.getPotential(i, cppPot)
      self.assertListEqual(list(pyPot),list(cppPot))

      pyPerm = numpy.zeros(numInputs).astype(realType)
      cppPerm = numpy.zeros(numInputs).astype(realType)
      pySp.getPermanence(i, pyPerm)
      cppSp.getPermanence(i, cppPerm)
      self.assertListAlmostEqual(list(pyPerm),list(cppPerm))

      pyCon = numpy.zeros(numInputs).astype(uintType)
      cppCon = numpy.zeros(numInputs).astype(uintType)
      pySp.getConnectedSynapses(i, pyCon)
      cppSp.getConnectedSynapses(i, cppCon)
      self.assertListEqual(list(pyCon), list(cppCon))

    pyConCounts = numpy.zeros(numColumns).astype(uintType)
    cppConCounts = numpy.zeros(numColumns).astype(uintType)
    pySp.getConnectedCounts(pyConCounts)
    cppSp.getConnectedCounts(cppConCounts)
    self.assertListEqual(list(pyConCounts), list(cppConCounts))


  def runSideBySide(self, params, seed = None,
                    learnMode = None,
                    convertEveryIteration = False):
    """
    Run the PY and CPP implementations side by side on random inputs.
    If seed is None a random seed will be chosen based on time, otherwise
    the fixed seed will be used.

    If learnMode is None learning will be randomly turned on and off.
    If it is False or True then set it accordingly.

    If convertEveryIteration is True, the CPP will be copied from the PY
    instance on every iteration just before each compute.
    """
    randomState = getNumpyRandomGenerator(seed)
    cppSp = CreateSP("cpp", params)
    pySp = CreateSP("py", params)
    self.compare(pySp, cppSp)
    numColumns = pySp.getNumColumns()
    numInputs = pySp.getNumInputs()
    threshold = 0.8
    inputMatrix = (
      randomState.rand(numRecords,numInputs) > threshold).astype(uintType)

    # Run side by side for numRecords iterations
    for i in xrange(numRecords):
      if learnMode is None:
        learn = (randomState.rand() > 0.5)
      else:
        learn = learnMode
      if self.verbosity > 1:
        print "Iteration:",i,"learn=",learn
      PyActiveArray = numpy.zeros(numColumns).astype(uintType)
      CppActiveArray = numpy.zeros(numColumns).astype(uintType)
      inputVector = inputMatrix[i,:]

      pySp.compute(inputVector, learn, PyActiveArray)
      cppSp.compute(inputVector, learn, CppActiveArray)
      self.assertListEqual(list(PyActiveArray), list(CppActiveArray))
      self.compare(pySp,cppSp)

      # The boost factors were similar enough to get this far.
      # Now make them completely equal so that small variations don't cause
      # columns to have slightly higher boosted overlaps.
      cppBoostFactors = numpy.zeros(numColumns, dtype=realType)
      cppSp.getBoostFactors(cppBoostFactors)
      pySp.setBoostFactors(cppBoostFactors)

      # The permanence values for the two implementations drift ever so slowly
      # over time due to numerical precision issues. This occasionally causes
      # different permanences to be connected. By transferring the permanence
      # values every so often, we can avoid this drift but still check that
      # the logic is applied equally for both implementations.
      if convertEveryIteration or ((i+1)%10 == 0):
        convertPermanences(pySp, cppSp)


  def runSerialize(self, imp, params, seed = None):
    randomState = getNumpyRandomGenerator(seed)
    sp1 = CreateSP(imp, params)
    numColumns = sp1.getNumColumns()
    numInputs = sp1.getNumInputs()
    threshold = 0.8
    inputMatrix = (
      randomState.rand(numRecords,numInputs) > threshold).astype(uintType)

    for i in xrange(numRecords/2):
      activeArray = numpy.zeros(numColumns).astype(uintType)
      inputVector = inputMatrix[i,:]
      learn = (randomState.rand() > 0.5)
      sp1.compute(inputVector, learn, activeArray)

    sp2 = pickle.loads(pickle.dumps(sp1))
    for i in xrange(numRecords/2+1,numRecords):
      activeArray1 = numpy.zeros(numColumns).astype(uintType)
      activeArray2 = numpy.zeros(numColumns).astype(uintType)
      inputVector = inputMatrix[i,:]
      learn = (randomState.rand() > 0.5)
      sp1.compute(inputVector, learn, activeArray1)
      sp2.compute(inputVector, learn, activeArray2)
      self.assertListEqual(list(activeArray1), list(activeArray2))


  def testCompatibility1(self):
    params = {
      "inputDimensions": [4,4],
      "columnDimensions": [5,3],
      "potentialRadius": 20,
      "potentialPct": 0.5,
      "globalInhibition": True,
      "localAreaDensity": 0,
      "numActiveColumnsPerInhArea": 5,
      "stimulusThreshold": 0,
      "synPermInactiveDec": 0.01,
      "synPermActiveInc": 0.1,
      "synPermConnected": 0.10,
      "minPctOverlapDutyCycle": 0.001,
      "dutyCyclePeriod": 30,
      "boostStrength": 10.0,
      "seed": 4,
      "spVerbosity": 0
    }
    # This seed used to cause problems if learnMode is set to None
    self.runSideBySide(params, seed = 63862)

    # These seeds used to fail
    self.runSideBySide(params, seed = 62605)
    self.runSideBySide(params, seed = 30440)
    self.runSideBySide(params, seed = 49457)

    self.runSideBySide(params)


  def testCompatibilityNoLearn(self):
    params = {
      "inputDimensions": [4,4],
      "columnDimensions": [5,3],
      "potentialRadius": 20,
      "potentialPct": 0.5,
      "globalInhibition": True,
      "localAreaDensity": 0,
      "numActiveColumnsPerInhArea": 5,
      "stimulusThreshold": 0,
      "synPermInactiveDec": 0.01,
      "synPermActiveInc": 0.1,
      "synPermConnected": 0.10,
      "minPctOverlapDutyCycle": 0.001,
      "dutyCyclePeriod": 30,
      "boostStrength": 10.0,
      "seed": 4,
      "spVerbosity": 0
    }
    self.runSideBySide(params, seed = None, learnMode = False)


  def testCompatibility2(self):
    params = {
      "inputDimensions": [12,7],
      "columnDimensions": [4,15],
      "potentialRadius": 22,
      "potentialPct": 0.3,
      "globalInhibition": False,
      "localAreaDensity": 0,
      "numActiveColumnsPerInhArea": 5,
      "stimulusThreshold": 2,
      "synPermInactiveDec": 0.04,
      "synPermActiveInc": 0.14,
      "synPermConnected": 0.178,
      "minPctOverlapDutyCycle": 0.021,
      "dutyCyclePeriod": 20,
      "boostStrength": 11.0,
      "seed": 6,
      "spVerbosity": 0
    }
    self.runSideBySide(params, convertEveryIteration=True, seed=63862)


  def testCompatibility3(self):
    params = {
      "inputDimensions": [2,4,5],
      "columnDimensions": [4,3,3],
      "potentialRadius": 30,
      "potentialPct": 0.7,
      "globalInhibition": False,
      "localAreaDensity": 0.23,
      "numActiveColumnsPerInhArea": 0,
      "stimulusThreshold": 2,
      "synPermInactiveDec": 0.02,
      "synPermActiveInc": 0.1,
      "synPermConnected": 0.12,
      "minPctOverlapDutyCycle": 0.011,
      "dutyCyclePeriod": 25,
      "boostStrength": 11.0,
      "seed": 19,
      "spVerbosity": 0
    }
    self.runSideBySide(params, convertEveryIteration=True, seed=63862)


  def testSerialization(self):
    params = {
      'inputDimensions' : [2,4,5],
      'columnDimensions' : [4,3,3],
      'potentialRadius' : 30,
      'potentialPct' : 0.7,
      'globalInhibition' : False,
      'localAreaDensity' : 0.23,
      'numActiveColumnsPerInhArea' : 0,
      'stimulusThreshold' : 2,
      'synPermInactiveDec' : 0.02,
      'synPermActiveInc' : 0.1,
      'synPermConnected' : 0.12,
      'minPctOverlapDutyCycle' : 0.011,
      'dutyCyclePeriod' : 25,
      'boostStrength' : 11.0,
      'seed' : 19,
      'spVerbosity' : 0
    }
    sp1 = CreateSP("py", params)
    sp2 = pickle.loads(pickle.dumps(sp1))
    self.compare(sp1, sp2)

    sp1 = CreateSP("cpp", params)
    sp2 = pickle.loads(pickle.dumps(sp1))
    self.compare(sp1, sp2)


  def testSerializationRun(self):
    params = {
      'inputDimensions' : [2,4,5],
      'columnDimensions' : [4,3,3],
      'potentialRadius' : 30,
      'potentialPct' : 0.7,
      'globalInhibition' : False,
      'localAreaDensity' : 0.23,
      'numActiveColumnsPerInhArea' : 0,
      'stimulusThreshold' : 2,
      'synPermInactiveDec' : 0.02,
      'synPermActiveInc' : 0.1,
      'synPermConnected' : 0.12,
      'minPctOverlapDutyCycle' : 0.011,
      'dutyCyclePeriod' : 25,
      'boostStrength' : 11.0,
      'seed' : 19,
      'spVerbosity' : 0
    }
    self.runSerialize("py", params)
    self.runSerialize("cpp", params)


  def testInhibitColumnsGlobal(self):
    params = {
      "inputDimensions": [512],
      "columnDimensions": [512],
      "globalInhibition": True,
      "numActiveColumnsPerInhArea": 40,
      "seed": 19
    }

    sp1 = CreateSP("py", params)
    sp2 = CreateSP("cpp", params)

    for _ in range(100):
      overlaps = numpy.random.randint(10, size=512).astype(realType)

      columns1 = sp1._inhibitColumns(overlaps)
      columns2 = sp2._inhibitColumns(overlaps)

      self.assertEqual(set(columns1), set(columns2))


  @unittest.skip("Currently fails due to non-fixed randomness in C++ SP.")
  def testCompatibilityCppPyDirectCall1D(self):
    """Check SP implementations have same behavior with 1D input."""

    pySp = PySpatialPooler(
        inputDimensions=[121], columnDimensions=[300])
    cppSp = CPPSpatialPooler(
        inputDimensions=[121], columnDimensions=[300])

    data = numpy.zeros([121], dtype=uintType)
    for i in xrange(21):
      data[i] = 1

    nCols = 300
    d1 = numpy.zeros(nCols, dtype=uintType)
    d2 = numpy.zeros(nCols, dtype=uintType)

    pySp.compute(data, True, d1) # learn
    cppSp.compute(data, True, d2)

    d1 = d1.nonzero()[0].tolist()
    d2 = d2.nonzero()[0].tolist()
    self.assertListEqual(
        d1, d2, "SP outputs are not equal: \n%s \n%s" % (str(d1), str(d2)))


  @unittest.skip("Currently fails due to non-fixed randomness in C++ SP.")
  def testCompatibilityCppPyDirectCall2D(self):
    """Check SP implementations have same behavior with 2D input."""

    pySp = PySpatialPooler(
        inputDimensions=[121, 1], columnDimensions=[30, 30])
    cppSp = CPPSpatialPooler(
        inputDimensions=[121, 1], columnDimensions=[30, 30])

    data = numpy.zeros([121, 1], dtype=uintType)
    for i in xrange(21):
      data[i][0] = 1

    nCols = 900
    d1 = numpy.zeros(nCols, dtype=uintType)
    d2 = numpy.zeros(nCols, dtype=uintType)

    pySp.compute(data, True, d1) # learn
    cppSp.compute(data, True, d2)

    d1 = d1.nonzero()[0].tolist()
    d2 = d2.nonzero()[0].tolist()
    self.assertListEqual(
        d1, d2, "SP outputs are not equal: \n%s \n%s" % (str(d1), str(d2)))



if __name__ == "__main__":
  unittest.main()
