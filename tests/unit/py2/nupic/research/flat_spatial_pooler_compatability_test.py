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

import cPickle as pickle
import numpy
import unittest2 as unittest

from nupic.support.unittesthelpers.algorithm_test_helpers import (
  getNumpyRandomGenerator, convertPermanences )

from nupic.bindings.algorithms import FlatSpatialPooler as CPPFlatSpatialPooler
from nupic.bindings.math import GetNTAReal, Random
from nupic.research.flat_spatial_pooler import (
  FlatSpatialPooler as PyFlatSpatialPooler)

realType = GetNTAReal()
uintType = "uint32"
NUM_RECORDS = 100



class FlatSpatialPoolerCompatabilityTest(unittest.TestCase):

  def setUp(self):
    # Set to 1 for more verbose debugging output
    self.verbosity = 0
    

  def assertListAlmostEqual(self, alist, blist):
    self.assertEqual(len(alist), len(blist),
                     "Lists have different length")
    for idx, val in enumerate(alist):
      self.assertAlmostEqual(
        val,
        blist[idx],
        places = 3,
        msg = "Lists different at index %d with values %g and %g"
              % (idx, val, blist[idx]))


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
    self.assertAlmostEqual(pySp.getMaxBoost(),
                           cppSp.getMaxBoost())

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
    self.assertAlmostEqual(pySp.getMinPctActiveDutyCycles(),
                           cppSp.getMinPctActiveDutyCycles())

    numColumns = pySp.getNumColumns()
    numInputs = pySp.getNumInputs()

    pyBoost = numpy.zeros(numColumns).astype(realType)
    cppBoost = numpy.zeros(numColumns).astype(realType)
    pySp.getBoostFactors(pyBoost)
    cppSp.getBoostFactors(cppBoost)
    self.assertListAlmostEqual(list(pyBoost), list(cppBoost))
    
    self.assertEqual(pySp.getRandomSP(), cppSp.getRandomSP())

    pyOverlap = numpy.zeros(numColumns).astype(realType)
    cppOverlap = numpy.zeros(numColumns).astype(realType)
    pySp.getOverlapDutyCycles(pyOverlap)
    cppSp.getOverlapDutyCycles(cppOverlap)
    self.assertListAlmostEqual(list(pyOverlap), list(cppOverlap))

    pyActive = numpy.zeros(numColumns).astype(realType)
    cppActive = numpy.zeros(numColumns).astype(realType)
    pySp.getActiveDutyCycles(pyActive)
    cppSp.getActiveDutyCycles(cppActive)
    self.assertListAlmostEqual(pyActive, cppActive)

    pyMinOverlap = numpy.zeros(numColumns).astype(realType)
    cppMinOverlap = numpy.zeros(numColumns).astype(realType)
    pySp.getMinOverlapDutyCycles(pyMinOverlap)
    cppSp.getMinOverlapDutyCycles(cppMinOverlap)
    self.assertListAlmostEqual(list(pyMinOverlap), list(cppMinOverlap))

    pyMinActive = numpy.zeros(numColumns).astype(realType)
    cppMinActive = numpy.zeros(numColumns).astype(realType)
    pySp.getMinActiveDutyCycles(pyMinActive)
    cppSp.getMinActiveDutyCycles(cppMinActive)
    self.assertListAlmostEqual(list(pyMinActive), list(cppMinActive))

    for i in xrange(pySp.getNumColumns()):
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


  def debugPrint(self, sp, name):
    """
    Helpful debug print statements while debugging this test.
    """
    minDutyCycle = numpy.zeros(sp.getNumColumns(), dtype = GetNTAReal())
    sp.getMinActiveDutyCycles(minDutyCycle)
    
    activeDutyCycle = numpy.zeros(sp.getNumColumns(), dtype = GetNTAReal())
    sp.getActiveDutyCycles(activeDutyCycle)
    
    boost = numpy.zeros(sp.getNumColumns(), dtype = GetNTAReal())
    sp.getBoostFactors(boost)
    print "====================\n",name
    print "Learning iteration:", sp.getIterationNum()
    print "Min duty cycles:",minDutyCycle[0]
    print "Active duty cycle", activeDutyCycle
    print
    print "Boost factor for sp:",boost


  def createSp(self, imp, params):
    """
    Create the SP implementation according to the parameters. Validate that
    the SP created properly.
    """
    if (imp == "py"):
      spClass = PyFlatSpatialPooler
    elif (imp == "cpp"):
      spClass = CPPFlatSpatialPooler
    else:
      raise RuntimeError("unrecognized implementation")

    sp = spClass(
      inputShape=params["inputShape"],
      coincidencesShape=params["coincidencesShape"],
      localAreaDensity=params["localAreaDensity"],
      numActivePerInhArea=params["numActivePerInhArea"],
      stimulusThreshold=params["stimulusThreshold"],
      synPermInactiveDec=params["synPermInactiveDec"],
      synPermActiveInc=params["synPermActiveInc"],
      synPermConnected=params["synPermConnected"],
      minPctDutyCycleBeforeInh=params["minPctDutyCycleBeforeInh"],
      minPctDutyCycleAfterInh=params["minPctDutyCycleAfterInh"],
      dutyCyclePeriod=params["dutyCyclePeriod"],
      maxFiringBoost=params["maxFiringBoost"],
      minDistance=params["minDistance"],
      seed=params["seed"],
      spVerbosity=params["spVerbosity"],
      randomSP=params["randomSP"],
      coincInputPoolPct=params.get("coincInputPoolPct",0.5),
    )
    
    self.assertEqual(params["randomSP"], sp.getRandomSP())
    self.assertEqual(params["spVerbosity"], sp.getSpVerbosity())
    self.assertAlmostEqual(params["minDistance"], sp.getMinDistance())
    self.assertAlmostEqual(params.get("coincInputPoolPct",0.5),
                           sp.getPotentialPct())

    return sp
  

  def runSideBySide(self, params, seed = None,
                    learnMode = None,
                    convertEveryIteration = False,
                    numRecords = None):
    """
    Run the PY and CPP implementations side by side on random inputs.
    If seed is None a random seed will be chosen based on time, otherwise
    the fixed seed will be used.
    
    If learnMode is None learning will be randomly turned on and off.
    If it is False or True then set it accordingly.
    
    If convertEveryIteration is True, the CPP will be copied from the PY
    instance on every iteration just before each compute.
    
    If numRecords is None, use the default global value NUM_RECORDS
    """
    if numRecords is None:
      numRecords = NUM_RECORDS
    randomState = getNumpyRandomGenerator(seed)
    pySp = self.createSp("py", params)
    numColumns = pySp.getNumColumns()
    numInputs = pySp.getNumInputs()
    cppSp = self.createSp("cpp", params)
    self.compare(pySp, cppSp)
    threshold = 0.8
    # Create numRecords records, each numInputs long, where each input
    # is an unsigned 32 bit integer of either 0 or 1
    inputMatrix = (
      randomState.rand(numRecords,numInputs) > threshold).astype(uintType)
    for i,inputVector in enumerate(inputMatrix):
      if learnMode is None:
        learn = (randomState.rand() > 0.5)
      else:
        learn = learnMode
      if self.verbosity > 1:
        print "\nIteration:",i,"learn=",learn
      PyActiveArray = numpy.zeros(numColumns).astype(uintType)
      CppActiveArray = numpy.zeros(numColumns).astype(uintType)
      pySp.compute(inputVector, learn, PyActiveArray)
      cppSp.compute(inputVector, learn, CppActiveArray)
      self.compare(pySp, cppSp)
      self.assertListEqual(list(PyActiveArray), list(CppActiveArray))

      # The permanence values for the two implementations drift ever so slowly
      # over time due to numerical precision issues. This occasionally causes
      # different permanences to be connected. By transferring the permanence
      # values every so often, we can avoid this drift but still check that
      # the logic is applied equally for both implementations.
      if convertEveryIteration or ((i+1)%10 == 0):
        convertPermanences(pySp, cppSp)



  def runSerialize(self, imp, params,
                   learnMode = None,
                   seed = None,
                   numRecords = None):
    """
    Create an SP instance. Run it for half the iterations and then pickle it.
    Then unpickle it and run for the rest of the iterations. Ensure output
    is identical to the unpickled instance.
    """
    if numRecords is None:
      numRecords = NUM_RECORDS
    randomState = getNumpyRandomGenerator(seed)
    sp1 = self.createSp(imp, params)
    numColumns = sp1.getNumColumns() 
    numInputs = sp1.getNumInputs()
    threshold = 0.8
    inputMatrix = (
      randomState.rand(numRecords,numInputs) > threshold).astype(uintType)

    for i in xrange(numRecords/2):
      activeArray = numpy.zeros(numColumns).astype(uintType)
      inputVector = inputMatrix[i,:]  
      if learnMode is None:
        learn = (randomState.rand() > 0.5)
      else:
        learn = learnMode
      if self.verbosity > 1:
        print "\nIteration:",i,"learn=",learn
      sp1.compute(inputVector, learn, activeArray)

    sp2 = pickle.loads(pickle.dumps(sp1))
    self.compare(sp1, sp2)
    for i in xrange(numRecords/2+1,numRecords):
      activeArray1 = numpy.zeros(numColumns).astype(uintType)
      activeArray2 = numpy.zeros(numColumns).astype(uintType)
      inputVector = inputMatrix[i,:]
      if learnMode is None:
        learn = (randomState.rand() > 0.5)
      else:
        learn = learnMode
      if self.verbosity > 1:
        print "\nIteration:",i,"learn=",learn
      sp1.compute(inputVector, learn, activeArray1)
      sp2.compute(inputVector, learn, activeArray2)
      self.compare(sp1, sp2)
      self.assertListEqual(list(activeArray1), list(activeArray2))


  def testCompatability1(self):
    params = {
      "inputShape" : 20,
      "coincidencesShape" : 21,
      "localAreaDensity" : 0,
      "numActivePerInhArea" : 7,
      "stimulusThreshold" : 0,
      "synPermInactiveDec" : 0.01,
      "synPermActiveInc" : 0.1,
      "synPermConnected" : 0.10,
      "minPctDutyCycleBeforeInh" : 0.001,
      "minPctDutyCycleAfterInh" : 0.001,
      "dutyCyclePeriod" : 30,
      "maxFiringBoost" : 10.0,
      "minDistance" : 0.0,
      "seed" : 3,
      "spVerbosity" : 0,
      "randomSP" : False
    }
    # We test a few combinations
    self.runSideBySide(params, learnMode=False)
    self.runSideBySide(params, convertEveryIteration = True)


  def testCompatability2(self):
    params = {
      "inputShape" : 15,
      "coincidencesShape" : 36,
      "localAreaDensity" : 0.2,
      "numActivePerInhArea" : 0,
      "stimulusThreshold" : 2,
      "synPermInactiveDec" : 0.025,
      "synPermActiveInc" : 0.2,
      "synPermConnected" : 0.13,
      "minPctDutyCycleBeforeInh" : 0.031,
      "minPctDutyCycleAfterInh" : 0.032,
      "dutyCyclePeriod" : 30,
      "maxFiringBoost" : 10.0,
      "minDistance" : 0.2,
      "seed" : 7,
      "spVerbosity" : 0,
      "randomSP" : False
    }
    self.runSideBySide(params, convertEveryIteration = True)


  def testCompatability3(self):
    params = {
      "inputShape" : 27,
      "coincidencesShape" : 63,
      "localAreaDensity" : 0.4,
      "numActivePerInhArea" : 0,
      "stimulusThreshold" : 2,
      "synPermInactiveDec" : 0.02,
      "synPermActiveInc" : 0.1,
      "synPermConnected" : 0.15,
      "minPctDutyCycleBeforeInh" : 0.001,
      "minPctDutyCycleAfterInh" : 0.002,
      "dutyCyclePeriod" : 31,
      "maxFiringBoost" : 14.0,
      "minDistance" : 0.4,
      "seed" : 19,
      "spVerbosity" : 0,
      "randomSP" : True
    }
    self.runSideBySide(params)


  def testCompatability3NoLearn(self):
    params = {
      "inputShape" : 27,
      "coincidencesShape" : 63,
      "localAreaDensity" : 0.4,
      "numActivePerInhArea" : 0,
      "stimulusThreshold" : 2,
      "synPermInactiveDec" : 0.02,
      "synPermActiveInc" : 0.1,
      "synPermConnected" : 0.15,
      "minPctDutyCycleBeforeInh" : 0.001,
      "minPctDutyCycleAfterInh" : 0.002,
      "dutyCyclePeriod" : 31,
      "maxFiringBoost" : 14.0,
      "minDistance" : 0.4,
      "seed" : 19,
      "spVerbosity" : self.verbosity,
      "randomSP" : True
    }
    self.runSideBySide(params, learnMode = False)


  def testNormalParams(self):
    """
    Larger parameters more representative of problems such as hotgym
    """
    params = {
      "inputShape" : 45,
      "coincidencesShape" : 2048,
      "localAreaDensity" : 0,
      "numActivePerInhArea" : 40,
      "stimulusThreshold" : 2,
      "synPermInactiveDec" : 0.02,
      "synPermActiveInc" : 0.1,
      "synPermConnected" : 0.15,
      "minPctDutyCycleBeforeInh" : 0.001,
      "minPctDutyCycleAfterInh" : 0.002,
      "dutyCyclePeriod" : 31,
      "maxFiringBoost" : 14.0,
      "minDistance" : 0.0,
      "seed" : 19,
      "spVerbosity" : self.verbosity,
      "randomSP" : True,
      "coincInputPoolPct": 0.5,
    }
    self.runSideBySide(params, learnMode = False, numRecords = 5)


  def testSmallerPoolPct(self):
    params = {
      "inputShape" : 78,
      "coincidencesShape" : 63,
      "localAreaDensity" : 0.0,
      "numActivePerInhArea" : 10,
      "stimulusThreshold" : 2,
      "synPermInactiveDec" : 0.02,
      "synPermActiveInc" : 0.1,
      "synPermConnected" : 0.15,
      "minPctDutyCycleBeforeInh" : 0.001,
      "minPctDutyCycleAfterInh" : 0.002,
      "dutyCyclePeriod" : 31,
      "maxFiringBoost" : 14.0,
      "minDistance" : 0.4,
      "seed" : 19,
      "spVerbosity" : self.verbosity,
      "randomSP" : True,
      "coincInputPoolPct": 0.3,
    }
    self.runSideBySide(params, learnMode = False)
    self.runSideBySide(params, convertEveryIteration = True)


  def testSerialization(self):
    params = {
      'inputShape' : 27,
      'coincidencesShape' : 63,
      'localAreaDensity' : 0.4,
      'numActivePerInhArea' : 0,
      'stimulusThreshold' : 2,
      'synPermInactiveDec' : 0.02,
      'synPermActiveInc' : 0.1,
      'synPermConnected' : 0.15,
      'minPctDutyCycleBeforeInh' : 0.001,
      'minPctDutyCycleAfterInh' : 0.002,
      'dutyCyclePeriod' : 31,
      'maxFiringBoost' : 14.0,
      'minDistance' : 0.4,
      'seed' : 19,
      'spVerbosity' : 0,
      'randomSP' : True
    }
    sppy1 = self.createSp("py", params)
    sppy2 = pickle.loads(pickle.dumps(sppy1))
    self.compare(sppy1, sppy2)

    spcpp1 = self.createSp("cpp", params)
    spcpp2 = pickle.loads(pickle.dumps(spcpp1))
    self.compare(spcpp1, spcpp2)
    
    # Now compare the original PY instance with the unpickled CPP instance
    self.compare(sppy1, spcpp2)


  def testSerializationRun(self):
    params = {
      'inputShape' : 27,
      'coincidencesShape' : 63,
      'localAreaDensity' : 0.4,
      'numActivePerInhArea' : 0,
      'stimulusThreshold' : 2,
      'synPermInactiveDec' : 0.02,
      'synPermActiveInc' : 0.1,
      'synPermConnected' : 0.15,
      'minPctDutyCycleBeforeInh' : 0.001,
      'minPctDutyCycleAfterInh' : 0.002,
      'dutyCyclePeriod' : 31,
      'maxFiringBoost' : 14.0,
      'minDistance' : 0.4,
      'seed' : 19,
      'spVerbosity' : 0,
      'randomSP' : False
    }
    self.runSerialize("py", params)
    self.runSerialize("cpp", params)
    params['randomSP'] = True
    self.runSerialize("cpp", params)
    self.runSerialize("py", params)




if __name__ == "__main__":
  unittest.main()
