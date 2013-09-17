#! /usr/bin/env python

import unittest2 as unittest

import numpy

import pdb

from nupic.research.flat_spatial_pooler import FlatSpatialPooler as PyFlatSpatialPooler
from nupic.bindings.algorithms import FlatSpatialPooler as CPPFlatSpatialPooler
from nupic.bindings.math import GetNTAReal

realType = GetNTAReal()
uintType = 'uint32'

class SpatialPoolerCompatabilityTest(unittest.TestCase):

  def assertListAlmostEqual(self, alist, blist):
    self.assertEqual(len(alist), len(blist))
    for (a,b) in zip(alist,blist):
      diff = abs(a - b)
      self.assertLess(diff,1e-5)

  def compare(self, PySp, CppSp):
    self.assertAlmostEqual(PySp.getNumColumns(), CppSp.getNumColumns())
    self.assertAlmostEqual(PySp.getNumInputs(), CppSp.getNumInputs())
    self.assertAlmostEqual(PySp.getPotentialRadius(), CppSp.getPotentialRadius())
    self.assertAlmostEqual(PySp.getPotentialPct(), CppSp.getPotentialPct())
    self.assertAlmostEqual(PySp.getGlobalInhibition(), CppSp.getGlobalInhibition())
    self.assertAlmostEqual(PySp.getNumActiveColumnsPerInhArea(), CppSp.getNumActiveColumnsPerInhArea())
    self.assertAlmostEqual(PySp.getLocalAreaDensity(), CppSp.getLocalAreaDensity())
    self.assertAlmostEqual(PySp.getStimulusThreshold(), CppSp.getStimulusThreshold())
    self.assertAlmostEqual(PySp.getInhibitionRadius(), CppSp.getInhibitionRadius())
    self.assertAlmostEqual(PySp.getDutyCyclePeriod(), CppSp.getDutyCyclePeriod())
    self.assertAlmostEqual(PySp.getMaxBoost(), CppSp.getMaxBoost())
    self.assertAlmostEqual(PySp.getIterationNum(), CppSp.getIterationNum())
    self.assertAlmostEqual(PySp.getIterationLearnNum(), CppSp.getIterationLearnNum())
    self.assertAlmostEqual(PySp.getSpVerbosity(), CppSp.getSpVerbosity())
    self.assertAlmostEqual(PySp.getUpdatePeriod(), CppSp.getUpdatePeriod())
    self.assertAlmostEqual(PySp.getSynPermTrimThreshold(), CppSp.getSynPermTrimThreshold())
    self.assertAlmostEqual(PySp.getSynPermActiveInc(), CppSp.getSynPermActiveInc())
    self.assertAlmostEqual(PySp.getSynPermInactiveDec(), CppSp.getSynPermInactiveDec())
    self.assertAlmostEqual(PySp.getSynPermBelowStimulusInc(), CppSp.getSynPermBelowStimulusInc())
    self.assertAlmostEqual(PySp.getSynPermConnected(), CppSp.getSynPermConnected())
    self.assertAlmostEqual(PySp.getMinPctOverlapDutyCycles(), CppSp.getMinPctOverlapDutyCycles())
    self.assertAlmostEqual(PySp.getMinPctActiveDutyCycles(), CppSp.getMinPctActiveDutyCycles())

    numColumns = PySp.getNumColumns()
    numInputs = PySp.getNumInputs()
    
    pyBoost = numpy.zeros(numColumns).astype(realType)
    cppBoost = numpy.zeros(numColumns).astype(realType)
    PySp.getBoostFactors(pyBoost)
    CppSp.getBoostFactors(cppBoost)
    self.assertListAlmostEqual(list(pyBoost), list(cppBoost))

    pyOverlap = numpy.zeros(numColumns).astype(realType)
    cppOverlap = numpy.zeros(numColumns).astype(realType)
    PySp.getOverlapDutyCycles(pyOverlap)
    CppSp.getOverlapDutyCycles(cppOverlap)
    self.assertListAlmostEqual(list(pyOverlap), list(cppOverlap))

    pyActive = numpy.zeros(numColumns).astype(realType)
    cppActive = numpy.zeros(numColumns).astype(realType)
    PySp.getActiveDutyCycles(pyActive)
    CppSp.getActiveDutyCycles(cppActive)
    self.assertListAlmostEqual(list(pyActive), list(cppActive))  

    pyMinOverlap = numpy.zeros(numColumns).astype(realType)
    cppMinOverlap = numpy.zeros(numColumns).astype(realType)
    PySp.getMinOverlapDutyCycles(pyMinOverlap)
    CppSp.getMinOverlapDutyCycles(cppMinOverlap)
    self.assertListAlmostEqual(list(pyMinOverlap), list(cppMinOverlap))

    pyMinActive = numpy.zeros(numColumns).astype(realType)
    cppMinActive = numpy.zeros(numColumns).astype(realType)
    PySp.getMinActiveDutyCycles(pyMinActive)
    CppSp.getMinActiveDutyCycles(cppMinActive)
    self.assertListAlmostEqual(list(pyMinActive), list(cppMinActive))  

    for i in xrange(PySp.getNumColumns()):

      pyPot = numpy.zeros(numInputs).astype(uintType)
      cppPot = numpy.zeros(numInputs).astype(uintType)
      PySp.getPotential(i, pyPot)
      CppSp.getPotential(i, cppPot)
      self.assertListEqual(list(pyPot),list(cppPot))

      pyPerm = numpy.zeros(numInputs).astype(realType)
      cppPerm = numpy.zeros(numInputs).astype(realType)
      PySp.getPermanence(i, pyPerm)
      CppSp.getPermanence(i, cppPerm)
      self.assertListAlmostEqual(list(pyPerm),list(cppPerm))

      pyCon = numpy.zeros(numInputs).astype(uintType)
      cppCon = numpy.zeros(numInputs).astype(uintType)
      PySp.getConnectedSynapses(i, pyCon)
      CppSp.getConnectedSynapses(i, cppCon)
      self.assertListEqual(list(pyCon), list(cppCon))

    pyConCounts = numpy.zeros(numColumns).astype(uintType)
    cppConCounts = numpy.zeros(numColumns).astype(uintType)
    PySp.getConnectedCounts(pyConCounts)
    CppSp.getConnectedCounts(cppConCounts)
    self.assertListEqual(list(pyConCounts), list(cppConCounts))


  def convertSP(self, PySp):
    columnDim = PySp._columnDimensions
    inputDim = PySp._inputDimensions
    numInputs = PySp.getNumInputs()
    numColumns = PySp.getNumColumns()
    CppSp = CPPFlatSpatialPooler(inputShape=inputDim,coincidencesShape=columnDim)
    CppSp.setPotentialRadius(PySp.getPotentialRadius())
    CppSp.setPotentialPct(PySp.getPotentialPct())
    CppSp.setGlobalInhibition(PySp.getGlobalInhibition())

    numActiveColumnsPerInhArea = PySp.getNumActiveColumnsPerInhArea()
    localAreaDensity = PySp.getLocalAreaDensity()
    if (numActiveColumnsPerInhArea == -1):
      CppSp.setLocalAreaDensity(localAreaDensity)
    else:
      CppSp.setNumActiveColumnsPerInhArea(numActiveColumnsPerInhArea)
    
    CppSp.setStimulusThreshold(PySp.getStimulusThreshold())
    CppSp.setInhibitionRadius(PySp.getInhibitionRadius())
    CppSp.setDutyCyclePeriod(PySp.getDutyCyclePeriod())
    CppSp.setMaxBoost(PySp.getMaxBoost())
    CppSp.setIterationNum(PySp.getIterationNum())
    CppSp.setIterationLearnNum(PySp.getIterationLearnNum())
    CppSp.setSpVerbosity(PySp.getSpVerbosity())
    CppSp.setUpdatePeriod(PySp.getUpdatePeriod())
    CppSp.setSynPermTrimThreshold(PySp.getSynPermTrimThreshold())
    CppSp.setSynPermActiveInc(PySp.getSynPermActiveInc())
    CppSp.setSynPermInactiveDec(PySp.getSynPermInactiveDec())
    CppSp.setSynPermBelowStimulusInc(PySp.getSynPermBelowStimulusInc())
    CppSp.setSynPermConnected(PySp.getSynPermConnected())
    CppSp.setMinPctOverlapDutyCycles(PySp.getMinPctOverlapDutyCycles())
    CppSp.setMinPctActiveDutyCycles(PySp.getMinPctActiveDutyCycles())
    CppSp.setMinDistance(PySp.getMinDistance())
    CppSp.setRandomSP(PySp.getRandomSP())
    
    boostFactors = numpy.zeros(numColumns).astype(realType)
    PySp.getBoostFactors(boostFactors)
    CppSp.setBoostFactors(boostFactors)

    overlapDuty = numpy.zeros(numColumns).astype(realType)
    PySp.getOverlapDutyCycles(overlapDuty)
    CppSp.setOverlapDutyCycles(overlapDuty)

    activeDuty = numpy.zeros(numColumns).astype(realType)
    PySp.getActiveDutyCycles(activeDuty)
    CppSp.setActiveDutyCycles(activeDuty)

    minOverlapDuty = numpy.zeros(numColumns).astype(realType)
    PySp.getMinOverlapDutyCycles(minOverlapDuty)
    CppSp.setMinOverlapDutyCycles(minOverlapDuty)

    minActiveDuty = numpy.zeros(numColumns).astype(realType)
    PySp.getMinActiveDutyCycles(minActiveDuty)
    CppSp.setMinActiveDutyCycles(minActiveDuty)

    for i in xrange(numColumns):
      potential = numpy.zeros(numInputs).astype(uintType)
      PySp.getPotential(i, potential)
      CppSp.setPotential(i, potential)

      perm = numpy.zeros(numInputs).astype(realType)
      PySp.getPermanence(i, perm)
      CppSp.setPermanence(i, perm)

    return CppSp

  def createSp(self):
    PySp = PyFlatSpatialPooler(
      inputShape=20,
      coincidencesShape=21,
      localAreaDensity=0.2,
      numActivePerInhArea=-1,
      stimulusThreshold=0,
      synPermInactiveDec=0.01,
      synPermActiveInc=0.1,
      synPermConnected=0.10,
      minPctDutyCycleBeforeInh=0.001,
      minPctDutyCycleAfterInh=0.001,
      dutyCyclePeriod=1000,
      maxFiringBoost=10.0,
      minDistance=0.0,
      seed=-1,
      globalInhibition=True,
      spVerbosity=0,
      useHighTier=True,
      randomSP=False
    )
    return PySp


  def testCompatability(self):
    N = 5000
    PySp = self.createSp()
    numColumns = PySp.getNumColumns() 
    numInputs = PySp.getNumInputs()
    threshold = 0.8
    inputMatrix = (numpy.random.rand(N,numInputs) > threshold).astype(uintType)
    learn = True
    randomSP = True
    # CppSp = self.convertSP(PySp)
    for i in xrange(N):
      print "Record " + str(i) + "..."
      PyActiveArray = numpy.zeros(numColumns).astype(uintType)
      CppActiveArray = numpy.zeros(numColumns).astype(uintType)
      inputVector = inputMatrix[i,:]  
      CppSp = self.convertSP(PySp)
      self.compare(PySp, CppSp)
      PySp.compute(inputVector, learn, PyActiveArray)
      CppSp.compute(inputVector, learn, CppActiveArray)
      self.assertListEqual(list(PyActiveArray), list(CppActiveArray))
      self.compare(PySp,CppSp)



if __name__ == "__main__":
  unittest.main()

