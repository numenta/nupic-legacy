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

import numpy
import unittest2 as unittest

from nupic.research.spatial_pooler import SpatialPooler as PySpatialPooler
from nupic.bindings.algorithms import SpatialPooler as CPPSpatialPooler
from nupic.bindings.math import GetNTAReal, Random as NupicRandom

realType = GetNTAReal()
uintType = 'uint32'
numRecords = 100



class SpatialPoolerCompatabilityTest(unittest.TestCase):


  def assertListAlmostEqual(self, alist, blist):
    self.assertEqual(len(alist), len(blist))
    for (a,b) in zip(alist,blist):
      diff = abs(a - b)
      self.assertLess(diff,1e-5)


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


  def convertSP(self, pySp, newSeed):
    columnDim = pySp._columnDimensions
    inputDim = pySp._inputDimensions
    numInputs = pySp.getNumInputs()
    numColumns = pySp.getNumColumns()
    cppSp = CPPSpatialPooler(inputDim,columnDim)
    cppSp.setPotentialRadius(pySp.getPotentialRadius())
    cppSp.setPotentialPct(pySp.getPotentialPct())
    cppSp.setGlobalInhibition(pySp.getGlobalInhibition())

    numActiveColumnsPerInhArea = pySp.getNumActiveColumnsPerInhArea()
    localAreaDensity = pySp.getLocalAreaDensity()
    if (numActiveColumnsPerInhArea > 0):
      cppSp.setNumActiveColumnsPerInhArea(numActiveColumnsPerInhArea)
    else:
      cppSp.setLocalAreaDensity(localAreaDensity)
    
    cppSp.setStimulusThreshold(pySp.getStimulusThreshold())
    cppSp.setInhibitionRadius(pySp.getInhibitionRadius())
    cppSp.setDutyCyclePeriod(pySp.getDutyCyclePeriod())
    cppSp.setMaxBoost(pySp.getMaxBoost())
    cppSp.setIterationNum(pySp.getIterationNum())
    cppSp.setIterationLearnNum(pySp.getIterationLearnNum())
    cppSp.setSpVerbosity(pySp.getSpVerbosity())
    cppSp.setUpdatePeriod(pySp.getUpdatePeriod())
    cppSp.setSynPermTrimThreshold(pySp.getSynPermTrimThreshold())
    cppSp.setSynPermActiveInc(pySp.getSynPermActiveInc())
    cppSp.setSynPermInactiveDec(pySp.getSynPermInactiveDec())
    cppSp.setSynPermBelowStimulusInc(pySp.getSynPermBelowStimulusInc())
    cppSp.setSynPermConnected(pySp.getSynPermConnected())
    cppSp.setMinPctOverlapDutyCycles(pySp.getMinPctOverlapDutyCycles())
    cppSp.setMinPctActiveDutyCycles(pySp.getMinPctActiveDutyCycles())
    
    boostFactors = numpy.zeros(numColumns).astype(realType)
    pySp.getBoostFactors(boostFactors)
    cppSp.setBoostFactors(boostFactors)

    overlapDuty = numpy.zeros(numColumns).astype(realType)
    pySp.getOverlapDutyCycles(overlapDuty)
    cppSp.setOverlapDutyCycles(overlapDuty)

    activeDuty = numpy.zeros(numColumns).astype(realType)
    pySp.getActiveDutyCycles(activeDuty)
    cppSp.setActiveDutyCycles(activeDuty)

    minOverlapDuty = numpy.zeros(numColumns).astype(realType)
    pySp.getMinOverlapDutyCycles(minOverlapDuty)
    cppSp.setMinOverlapDutyCycles(minOverlapDuty)

    minActiveDuty = numpy.zeros(numColumns).astype(realType)
    pySp.getMinActiveDutyCycles(minActiveDuty)
    cppSp.setMinActiveDutyCycles(minActiveDuty)

    for i in xrange(numColumns):
      potential = numpy.zeros(numInputs).astype(uintType)
      pySp.getPotential(i, potential)
      cppSp.setPotential(i, potential)

      perm = numpy.zeros(numInputs).astype(realType)
      pySp.getPermanence(i, perm)
      cppSp.setPermanence(i, perm)

    pySp._random = NupicRandom(newSeed)
    cppSp.seed_(newSeed)
    return cppSp


  def createSp(self, imp, params):
    if (imp == "py"):
      spClass = PySpatialPooler
    elif (imp == "cpp"):
      spClass = CPPSpatialPooler
    else:
      raise RuntimeError("unrecognized implementation")
    
    sp = spClass(
      inputDimensions=params['inputDimensions'],
      columnDimensions=params['columnDimensions'],
      potentialRadius=params['potentialRadius'],
      potentialPct=params['potentialPct'],
      globalInhibition=params['globalInhibition'],
      localAreaDensity=params['localAreaDensity'],
      numActiveColumnsPerInhArea=params['numActiveColumnsPerInhArea'],
      stimulusThreshold=params['stimulusThreshold'],
      synPermInactiveDec=params['synPermInactiveDec'],
      synPermActiveInc=params['synPermActiveInc'],
      synPermConnected=params['synPermConnected'],
      minPctOverlapDutyCycle=params['minPctOverlapDutyCycle'],
      minPctActiveDutyCycle=params['minPctActiveDutyCycle'],
      dutyCyclePeriod=params['dutyCyclePeriod'],
      maxBoost=params['maxBoost'],
      seed=params['seed'],
      spVerbosity=params['spVerbosity']
    )
    return sp


  def runSideBySide(self, params):
    seed = 5
    pySp = self.createSp("py", params)
    cppSp = self.createSp("cpp", params)
    self.compare(pySp, cppSp)
    numColumns = pySp.getNumColumns() 
    numInputs = pySp.getNumInputs()
    threshold = 0.8
    inputMatrix = (
      numpy.random.rand(numRecords,numInputs) > threshold).astype(uintType)
    learn = True
    for i in xrange(numRecords):
      PyActiveArray = numpy.zeros(numColumns).astype(uintType)
      CppActiveArray = numpy.zeros(numColumns).astype(uintType)
      inputVector = inputMatrix[i,:]  
      cppSp = self.convertSP(pySp, i+1)
      pySp.compute(inputVector, learn, PyActiveArray)
      cppSp.compute(inputVector, learn, CppActiveArray)
      self.assertListEqual(list(PyActiveArray), list(CppActiveArray))
      self.compare(pySp,cppSp)


  def testCompatability1(self):
    params = {
      'inputDimensions' : [4,4],
      'columnDimensions' : [5,3],
      'potentialRadius' : 20,
      'potentialPct' : 0.5,
      'globalInhibition' : True,
      'localAreaDensity' : 0,
      'numActiveColumnsPerInhArea' : 5,
      'stimulusThreshold' : 0,
      'synPermInactiveDec' : 0.01,
      'synPermActiveInc' : 0.1,
      'synPermConnected' : 0.10,
      'minPctOverlapDutyCycle' : 0.001,
      'minPctActiveDutyCycle' : 0.001,
      'dutyCyclePeriod' : 30,
      'maxBoost' : 10.0,
      'seed' : 4,
      'spVerbosity' : 0
    }
    self.runSideBySide(params)


  def testCompatability2(self):
    params = {
      'inputDimensions' : [12,7],
      'columnDimensions' : [4,15],
      'potentialRadius' : 22,
      'potentialPct' : 0.3,
      'globalInhibition' : False,
      'localAreaDensity' : 0,
      'numActiveColumnsPerInhArea' : 5,
      'stimulusThreshold' : 2,
      'synPermInactiveDec' : 0.04,
      'synPermActiveInc' : 0.14,
      'synPermConnected' : 0.178,
      'minPctOverlapDutyCycle' : 0.021,
      'minPctActiveDutyCycle' : 0.0012,
      'dutyCyclePeriod' : 20,
      'maxBoost' : 11.0,
      'seed' : 6,
      'spVerbosity' : 0
    }
    self.runSideBySide(params)


  def testCompatability3(self):
    params = {
      'inputDimensions' : [2,4,5,2],
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
      'minPctActiveDutyCycle' : 0.052,
      'dutyCyclePeriod' : 25,
      'maxBoost' : 11.0,
      'seed' : 19,
      'spVerbosity' : 0
    }
    self.runSideBySide(params)



if __name__ == "__main__":
  unittest.main()
