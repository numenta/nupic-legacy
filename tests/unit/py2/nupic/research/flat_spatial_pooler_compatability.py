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

from nupic.research.flat_spatial_pooler import (
  FlatSpatialPooler as PyFlatSpatialPooler)
from nupic.bindings.algorithms import FlatSpatialPooler as CPPFlatSpatialPooler
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
    cppSp = CPPFlatSpatialPooler(inputShape=inputDim,
      coincidencesShape=columnDim)
    cppSp.setPotentialRadius(pySp.getPotentialRadius())
    cppSp.setPotentialPct(pySp.getPotentialPct())
    cppSp.setGlobalInhibition(pySp.getGlobalInhibition())

    numActiveColumnsPerInhArea = pySp.getNumActiveColumnsPerInhArea()
    localAreaDensity = pySp.getLocalAreaDensity()
    if (localAreaDensity > 0):
      cppSp.setLocalAreaDensity(localAreaDensity)
    else:
      cppSp.setNumActiveColumnsPerInhArea(numActiveColumnsPerInhArea)
    
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
    cppSp.setMinDistance(pySp.getMinDistance())
    cppSp.setRandomSP(pySp.getRandomSP())
    
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
      spClass = PyFlatSpatialPooler
    elif (imp == "cpp"):
      spClass = CPPFlatSpatialPooler
    else:
      raise RuntimeError("unrecognized implementation")

    sp = spClass(
      inputShape=params['inputShape'],
      coincidencesShape=params['coincidencesShape'],
      localAreaDensity=params['localAreaDensity'],
      numActivePerInhArea=params['numActivePerInhArea'],
      stimulusThreshold=params['stimulusThreshold'],
      synPermInactiveDec=params['synPermInactiveDec'],
      synPermActiveInc=params['synPermActiveInc'],
      synPermConnected=params['synPermConnected'],
      minPctDutyCycleBeforeInh=params['minPctDutyCycleBeforeInh'],
      minPctDutyCycleAfterInh=params['minPctDutyCycleAfterInh'],
      dutyCyclePeriod=params['dutyCyclePeriod'],
      maxFiringBoost=params['maxFiringBoost'],
      minDistance=params['minDistance'],
      seed=params['seed'],
      spVerbosity=params['spVerbosity'],
      randomSP=params['randomSP']
    )    

    return sp


  def runSideBySide(self, params):
    pySp = self.createSp("py",params)
    numColumns = pySp.getNumColumns() 
    numInputs = pySp.getNumInputs()
    cppSp = self.createSp("cpp",params)
    self.compare(pySp,cppSp)
    threshold = 0.8
    inputMatrix = (numpy.random.rand(numRecords,numInputs) > 
      threshold).astype(uintType)
    learn = True
    randomSP = True
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
      'inputShape' : 20,
      'coincidencesShape' : 21,
      'localAreaDensity' : 0,
      'numActivePerInhArea' : 7,
      'stimulusThreshold' : 0,
      'synPermInactiveDec' : 0.01,
      'synPermActiveInc' : 0.1,
      'synPermConnected' : 0.10,
      'minPctDutyCycleBeforeInh' : 0.001,
      'minPctDutyCycleAfterInh' : 0.001,
      'dutyCyclePeriod' : 30,
      'maxFiringBoost' : 10.0,
      'minDistance' : 0.0,
      'seed' : 3,
      'spVerbosity' : 0,
      'randomSP' : False
    }
    self.runSideBySide(params)


  def testCompatability2(self):
    params = {
      'inputShape' : 15,
      'coincidencesShape' : 36,
      'localAreaDensity' : 0.2,
      'numActivePerInhArea' : 0,
      'stimulusThreshold' : 2,
      'synPermInactiveDec' : 0.025,
      'synPermActiveInc' : 0.2,
      'synPermConnected' : 0.13,
      'minPctDutyCycleBeforeInh' : 0.031,
      'minPctDutyCycleAfterInh' : 0.032,
      'dutyCyclePeriod' : 30,
      'maxFiringBoost' : 10.0,
      'minDistance' : 0.2,
      'seed' : 7,
      'spVerbosity' : 0,
      'randomSP' : False
    }
    self.runSideBySide(params)


  def testCompatability3(self):
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
    self.runSideBySide(params)



if __name__ == "__main__":
  unittest.main()
