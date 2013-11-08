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

# This script helper routines for testing algorithms

import numpy
import time
import traceback

from nupic.bindings.algorithms import SpatialPooler as CPPSpatialPooler
from nupic.bindings.math import GetNTAReal, Random as NupicRandom

realType = GetNTAReal()
uintType = "uint32"


def getNumpyRandomGenerator(seed):
  """
  Return a numpy random number generator with the given seed.
  If seed is None, set it randomly based on time. Regardless we log
  the actual seed and stack trace so that test failures are replicable.
  """
  if seed is None:
    seed = int(time.time())
  print "Seed set to:",seed,"called by",
  callStack = traceback.extract_stack(limit=3)
  print callStack[0][2],"->",callStack[1][2]
  return numpy.random.RandomState(seed)



def convertSP(pySp, newSeed):
  """
  Given an instance of a python spatial_pooler return an instance of the CPP
  spatial_pooler.
  """
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
