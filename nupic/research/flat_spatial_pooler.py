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

"""Implements the flat spatial pooler."""

import numpy

from nupic.bindings.math import GetNTAReal
from nupic.research.spatial_pooler import SpatialPooler

realDType = GetNTAReal()



class FlatSpatialPooler(SpatialPooler):
  """
  This class implements the flat spatial pooler. This version of the spatial 
  pooler contains no toplogy information. It uses global coverage and global
  inhibition. It implements 'high tier' learning.
  
  High tier learning gives preference to unlearned columns. An unlearned
  column will always win unless another column has learned to perfectly
  represent an input pattern.  Once this initial phase has passed, it should
  behave like the normal spatial pooler. This option is useful if you might
  encounter very small datasets where you might want a unique representation
  for every input, regardless of similarity.
  
  The randomSP option allows you to use a flat spatial pooler without invoking
  any learning. This is extremely useful for understanding the properties of a
  basic SP that is initialized with random permanences. A randomSP will give
  reasonable SDR's and is easier to analyze and reason about. (A properly
  trained SP should give even better SDR's.) You can't achieve this function
  with SpatialPooler because it normally strips out unlearned columns when
  learning is turned off. If the randomSP functionality is generally useful, we
  might move this option to SpatialPooler.
  """


  def setMinDistance(self, minDistance):
    self._minDistance = minDistance

  
  def getMinDistance(self):
    return self._minDistance


  def setRandomSP(self, randomSP):
    self._randomSP = randomSP


  def getRandomSP(self):
    return self._randomSP


  def __init__(self,
               inputShape=(32, 32),
               inputBorder=8,
               inputDensity=1.0,
               coincidencesShape=(48, 48),
               coincInputRadius=16,
               coincInputPoolPct=0.5,
               gaussianDist=False,
               commonDistributions=False,
               localAreaDensity=-1.0,
               numActivePerInhArea=10.0,
               stimulusThreshold=0,
               synPermInactiveDec=0.01,
               synPermActiveInc=0.1,
               synPermActiveSharedDec=0.0,
               synPermOrphanDec=0.0,
               synPermConnected=0.10,
               minPctDutyCycleBeforeInh=0.001,
               minPctDutyCycleAfterInh=0.001,
               dutyCyclePeriod=1000,
               maxFiringBoost=10.0,
               maxSSFiringBoost=2.0,
               maxSynPermBoost=10.0,
               minDistance=0.0,
               cloneMap=None,
               numCloneMasters=-1,
               seed=-1,
               spVerbosity=0,
               printPeriodicStats=0,
               testMode=False,
               globalInhibition=False,
               spReconstructionParam="unweighted_mean",
               useHighTier=True,
               randomSP=False,
              ):

    assert useHighTier, "useHighTier must be True in flat_spatial_pooler"

    numInputs = numpy.array(inputShape).prod()
    numColumns = numpy.array(coincidencesShape).prod()
    super(FlatSpatialPooler, self).__init__(
      inputDimensions=numpy.array(inputShape),
      columnDimensions=numpy.array(coincidencesShape),
      potentialRadius=numInputs,
      potentialPct=coincInputPoolPct,
      globalInhibition=True, # Global inhibition always true in the flat pooler
      localAreaDensity=localAreaDensity,
      numActiveColumnsPerInhArea=numActivePerInhArea,
      stimulusThreshold=stimulusThreshold,
      synPermInactiveDec=synPermInactiveDec,
      synPermActiveInc=synPermActiveInc,
      synPermConnected=synPermConnected,
      minPctOverlapDutyCycle=minPctDutyCycleBeforeInh,
      minPctActiveDutyCycle=minPctDutyCycleAfterInh,
      dutyCyclePeriod=dutyCyclePeriod,
      maxBoost=maxFiringBoost,
      seed=seed,
      spVerbosity=spVerbosity,
    )

    # save arguments
    self._numInputs = numpy.prod(numpy.array(inputShape))
    self._numColumns = numpy.prod(numpy.array(coincidencesShape))
    self._minDistance = minDistance
    self._randomSP = randomSP

    #set active duty cycles to ones, because they set anomaly scores to 0
    self._activeDutyCycles = numpy.ones(self._numColumns)

    # set of columns to be 'hungry' for learning
    self._boostFactors *= maxFiringBoost
    
    # For high tier to work we need to set the min duty cycles to be non-zero
    # This will ensure that columns with 0 active duty cycle get high boost
    # in the beginning.
    self._minOverlapDutyCycles.fill(1e-6)
    self._minActiveDutyCycles.fill(1e-6)
    
    if self._spVerbosity > 0:
      self.printFlatParameters()


  def compute(self, inputArray, learn, activeArray, stripNeverLearned=True):
    """
    This is the primary public method of the SpatialPooler class. This function
    takes a input vector and outputs the indices of the active columns. If
    'learn' is set to True, and randomSP is set to false, this method also
    updates the permanences of the columns.

    Parameters:
    ----------------------------
    inputVector:    a numpy array of 0's and 1's thata comprises the input to 
                    the spatial pooler. The array will be treated as a one
                    dimensional array, therefore the dimensions of the array
                    do not have to much the exact dimensions specified in the 
                    class constructor. In fact, even a list would suffice. 
                    The number of input bits in the vector must, however, 
                    match the number of bits specified by the call to the 
                    constructor. Therefore there must be a '0' or '1' in the
                    array for every input bit.
    learn:          a boolean value indicating whether learning should be 
                    performed. Learning entails updating the  permanence 
                    values of the synapses, and hence modifying the 'state' 
                    of the model. Setting learning to 'off' freezes the SP
                    and has many uses. For example, you might want to feed in
                    various inputs and examine the resulting SDR's.
    :param stripNeverLearned: If True and learn=False, then columns that
        have never learned will be stripped out of the active columns. This
        should be set to False when using a random SP with learning disabled.
        NOTE: This parameter should be set explicitly as the default will
        likely be changed to False in the near future and if you want to retain
        the current behavior you should additionally pass the resulting
        activeArray to the stripUnlearnedColumns method manually.
    """
    if self._randomSP:
      learn=False

    assert (numpy.size(inputArray) == self._numInputs)
    self._updateBookeepingVars(learn)
    inputVector = numpy.array(inputArray, dtype=realDType)
    overlaps = self._calculateOverlap(inputVector)
    overlapsPct = self._calculateOverlapPct(overlaps)
    highTierColumns = self._selectHighTierColumns(overlapsPct)
    virginColumns = self._selectVirginColumns()
    
    if learn:
      vipOverlaps = self._boostFactors * overlaps
    else:
      vipOverlaps = overlaps.copy()

    # Ensure one of the high tier columns win
    # If learning is on, ensure an unlearned column wins
    vipBonus = max(vipOverlaps) + 1.0
    if learn:
      vipOverlaps[virginColumns] = vipBonus
    vipOverlaps[highTierColumns] += vipBonus

    activeColumns = self._inhibitColumns(vipOverlaps)

    if learn:
      self._adaptSynapses(inputVector, activeColumns)
      self._updateDutyCycles(overlaps, activeColumns)
      self._bumpUpWeakColumns() 
      self._updateBoostFactors()

      if self._isUpdateRound():
        self._updateInhibitionRadius()
        self._updateMinDutyCycles()
    elif stripNeverLearned:
      activeColumns = self.stripUnlearnedColumns(activeColumns)

    activeArray.fill(0)
    if activeColumns.size > 0:
      activeArray[activeColumns] = 1



  def _selectVirginColumns(self):
    """
    returns a set of virgin columns. Virgin columns are columns that have never 
    been active.
    """
    return numpy.where(self._activeDutyCycles == 0)[0]


  def _selectHighTierColumns(self, overlapsPct):
    """
    returns the set of high tier columns. High tier columns are columns who 
    have learned to represent a particular input pattern. How well a column 
    represents an input pattern is represented by the percent of connected 
    synapses connected to inputs bits which are turned on. 'self._minDistance'
    determines with how much precision a column must learn to represent an 
    input pattern in order to be considered a 'high tier' column.
    """
    return numpy.where(overlapsPct >= (1.0 - self._minDistance))[0]


  def printFlatParameters(self):
    """Print parameters specific to this class."""
    print "            PY FlatSpatialPooler Parameters"
    print "minDistance                = ", self.getMinDistance()
    print "randomSP                   = ", self.getRandomSP()
