# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""This script contains helper routines for testing algorithms"""

import numpy
import time
import traceback
from nupic.bindings.algorithms import SpatialPooler as CPPSpatialPooler
from nupic.bindings.math import GetNTAReal, Random as NupicRandom

from nupic.algorithms.spatial_pooler import SpatialPooler as PySpatialPooler

realType = GetNTAReal()
uintType = "uint32"


def getNumpyRandomGenerator(seed = None):
  """
  Return a numpy random number generator with the given seed.
  If seed is None, set it randomly based on time. Regardless we log
  the actual seed and stack trace so that test failures are replicable.
  """
  if seed is None:
    seed = int((time.time()%10000)*10)
  print "Numpy seed set to:", seed, "called by",
  callStack = traceback.extract_stack(limit=3)
  print callStack[0][2], "line", callStack[0][1], "->", callStack[1][2]
  return numpy.random.RandomState(seed)


def convertPermanences(sourceSP, destSP):
  """
  Transfer the permanences from source to dest SP's. This is used in test
  routines to counteract some drift between implementations.
  We assume the two SP's have identical configurations/parameters.
  """
  numColumns = sourceSP.getNumColumns()
  numInputs = sourceSP.getNumInputs()
  for i in xrange(numColumns):
    potential = numpy.zeros(numInputs).astype(uintType)
    sourceSP.getPotential(i, potential)
    destSP.setPotential(i, potential)

    perm = numpy.zeros(numInputs).astype(realType)
    sourceSP.getPermanence(i, perm)
    destSP.setPermanence(i, perm)



def getSeed():
  """Generate and log a 32-bit compatible seed value."""
  seed = int((time.time()%10000)*10)
  print "New seed generated as:", seed, "called by",
  callStack = traceback.extract_stack(limit=3)
  print callStack[0][2], "line", callStack[0][1], "->", callStack[1][2]
  return seed



def convertSP(pySp, newSeed):
  """
  Given an instance of a python spatial_pooler return an instance of the CPP
  spatial_pooler with identical parameters.
  """
  columnDim = pySp._columnDimensions
  inputDim = pySp._inputDimensions
  numInputs = pySp.getNumInputs()
  numColumns = pySp.getNumColumns()
  cppSp = CPPSpatialPooler(inputDim, columnDim)
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
  cppSp.setBoostStrength(pySp.getBoostStrength())
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



def CreateSP(imp, params):
  """
  Helper class for creating an instance of the appropriate spatial pooler using
  given parameters.

  Parameters:
  ----------------------------
  imp:       Either 'py' or 'cpp' for creating the appropriate instance.
  params:    A dict for overriding constructor parameters. The keys must
             correspond to contructor parameter names.

  Returns the SP object.
  """
  if (imp == "py"):
    spClass = PySpatialPooler
  elif (imp == "cpp"):
    spClass = CPPSpatialPooler
  else:
    raise RuntimeError("unrecognized implementation")

  print params
  sp = spClass(**params)

  return sp

