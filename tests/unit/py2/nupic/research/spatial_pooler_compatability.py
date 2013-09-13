#! /usr/bin/env python

import unittest2 as unittest

import numpy

from nupic.research.spatial_pooler import SpatialPooler as PySpatialPooler
from nupic.bindings.algorithms import SpatialPooler as CPPSpatialPooler


class SpatialPoolerCompatabilityTest(unittest.TestCase):

  def compare(self, PySp, CppSp):
    self.assertEqual(PySp.getNumColumns(), CppSp.getNumColumns())
    self.assertEqual(PySp.getNumInputs(), CppSp.getNumInputs())
    self.assertEqual(PySp.getPotentialRadius(), CppSp.getPotentialRadius())
    self.assertEqual(PySp.getPotentialPct(), CppSp.getPotentialPct())
    self.assertEqual(PySp.getGlobalInhibition(), CppSp.getGlobalInhibition())
    self.assertEqual(PySp.getNumActiveColumnsPerInhArea(), CppSp.getNumActiveColumnsPerInhArea())
    self.assertEqual(PySp.getLocalAreaDensity(), CppSp.getLocalAreaDensity())
    self.assertEqual(PySp.getStimulusThreshold(), CppSp.getStimulusThreshold())
    self.assertEqual(PySp.getInhibitionRadius(), CppSp.getInhibitionRadius())
    self.assertEqual(PySp.getDutyCyclePeriod(), CppSp.getDutyCyclePeriod())
    self.assertEqual(PySp.getMaxBoost(), CppSp.getMaxBoost())
    self.assertEqual(PySp.getIterationNum(), CppSp.getIterationNum())
    self.assertEqual(PySp.getIterationLearnNum(), CppSp.getIterationLearnNum())
    self.assertEqual(PySp.getSpVerbosity(), CppSp.getSpVerbosity())
    self.assertEqual(PySp.getUpdatePeriod(), CppSp.getUpdatePeriod())
    self.assertEqual(PySp.getSynPermTrimThreshold(), CppSp.getSynPermTrimThreshold())
    self.assertEqual(PySp.getSynPermActiveInc(), CppSp.getSynPermActiveInc())
    self.assertEqual(PySp.getSynPermInactiveDec(), CppSp.getSynPermInactiveDec())
    self.assertEqual(PySp.getSynPermBelowStimulusInc(), CppSp.getSynPermBelowStimulusInc())
    self.assertEqual(PySp.getSynPermConnected(), CppSp.getSynPermConnected())
    self.assertEqual(PySp.getMinPctOverlapDutyCycles(), CppSp.getMinPctOverlapDutyCycles())
    self.assertEqual(PySp.getMinPctActiveDutyCycles(), CppSp.getMinPctActiveDutyCycles())

    numColumns = PySp.getNumColumns()
    numInputs = PySp.getNumInputs()
    
    pyBoost = numpy.zeros(numColumns)
    cppBoost = numpy.zeros(numColumns)
    PySp.getBoostFactors(pyBoost)
    CppSp.getBoostFactors(cppBoost)
    self.assertListEqual(list(pyBoost), list(cppBoost))

    pyOverlap = numpy.zeros(numColumns)
    cppOverlap = numpy.zeros(numColumns)
    PySp.getOverlapDutyCycles(pyOverlap)
    CppSp.getOverlapDutyCycles(cppOverlap)
    self.assertListEqual(list(pyOverlap), list(cppOverlap))

    pyActive = numpy.zeros(numColumns)
    cppActive = numpy.zeros(numColumns)
    PySp.getActiveDutyCycles(pyActive)
    CppSp.getActiveDutyCycles(cppActive)
    self.assertListEqual(list(pyActive), list(cppActive))  

    pyOverlap = numpy.zeros(numColumns)
    cppOverlap = numpy.zeros(numColumns)
    PySp.getMinOverlapDutyCycles(pyOverlap)
    CppSp.getMinOverlapDutyCycles(cppOverlap)
    self.assertListEqual(list(pyOverlap), list(cppOverlap))

    pyActive = numpy.zeros(numColumns)
    cppActive = numpy.zeros(numColumns)
    PySp.getMinActiveDutyCycles(pyActive)
    CppSp.getMinActiveDutyCycles(cppActive)
    self.assertListEqual(list(pyActive), list(cppActive))  

    for i in xrange(PySp.getNumColumns()):

      pyPot = numpy.zeros(numInputs)
      cppPot = numpy.zeros(numInputs)
      PySp.getPotential(i, pyPot)
      CppSp.getPotential(i, cppPot)
      self.assertListEqual(list(pyPot),list(cppPot))

      pyPerm = numpy.zeros(numInputs)
      cppPerm = numpy.zeros(numInputs)
      PySp.getPermanence(i, pyPerm)
      CppSp.getPermanence(i, cppPerm)
      self.assertListEqual(list(pyPerm),list(cppPerm))

      pyCon = numpy.zeros(numInputs)
      cppCon = numpy.zeros(numInputs)
      PySp.getConnectedSynapses(i, pyCon)
      CppSp.getConnectedSynapses(i, cppCon)
      self.assertListEqual(list(pyCon), list(cppCon))

    self.assertEqual(list(PySp.getConnectedCounts()), list(CppSp.getConnectedCounts()))


  def convertSP(self, PySp):
    numColumns = PySp.getNumColumns()
    numInputs = PySp.getNumInputs()
    CppSp = CPPSpatialPooler([numInputs],[numColumns])
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
    
    boostFactors = numpy.zeros(numColumns)
    PySp.getBoostFactors(boostFactors)
    CppSp.setBoostFactors(boostFactors)

    overlapDuty = numpy.zeros(numColumns)
    PySp.getOverlapDutyCycles(overlapDuty)
    CppSp.setOverlapDutyCycles(overlapDuty)

    activeDuty = numpy.zeros(numColumns)
    PySp.getActiveDutyCycles(activeDuty)
    CppSp.setActiveDutyCycles(activeDuty)

    minOverlapDuty = numpy.zeros(numColumns)
    PySp.getMinOverlapDutyCycles(minOverlapDuty)
    CppSp.setMinOverlapDutyCycles(minOverlapDuty)

    minActiveDuty = numpy.zeros(numColumns)
    PySp.getMinActiveDutyCycles(minActiveDuty)
    CppSp.setMinActiveDutyCycles(minActiveDuty)

    for i in xrange(numColumns):
      potential = numpy.zeros(numInputs)
      PySp.getPotential(i, potential)
      CppSp.setPotential(i, potential)

      perm = numpy.zeros(numInputs)
      PySp.getPermanence(i, perm)
      CppSp.setPermanence(i, perm)

    return CppSp


  def testCompatability(self):
    N = 500
    numColumns = 20 
    numInputs = 10
    inputMatrix = numpy.random.rand(N,numInputs)
    learn = True
    PySp = PySpatialPooler([numInputs],[numColumns])
    
    for i in xrange(N):
      PyActiveArray = numpy.zeros(numColumns)
      CppActiveArray = numpy.zeros(numColumns)
      inputVector = inputMatrix[i,:]  
      CppSp = self.convertSP(PySp)
      import pdb; pdb.set_trace()
      PySp.compute(inputVector, learn, PyActiveArray)
      CppSp.compute(inputVector, learn, CppActiveArray)
      self.assertListEqual(list(PyActiveArray), list(CppActiveArray))
      self.compare(PySp,CppSp)



if __name__ == "__main__":
  unittest.main()

