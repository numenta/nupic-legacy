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

"""Implements the flat spatial pooler."""

import copy
import cPickle
import itertools
import numpy

from nupic.bindings.math import GetNTAReal
from nupic.research.spatial_pooler import SpatialPooler

realDType = GetNTAReal()



class FlatSpatialPooler(SpatialPooler):
	"""
	This class implements the flat spatial pooler. This version of the spatial 
	pooler contains no toplogy information. It uses global coverage and global
	inhibition
	"""


	def __init__(self,
               inputShape=(32, 32),
               inputBorder=8,
               inputDensity=1.0,
               coincidencesShape=(48, 48),
               coincInputRadius=16,
               coincInputPoolPct=1.0,
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

		super(FlatSpatialPooler,self).__init__(
				inputDimensions=numpy.array(inputShape),
				columnDimensions=numpy.array(coincidencesShape),
				potentialRadius=coincInputRadius,
				potentialPct=coincInputPoolPct,
				globalInhibition=globalInhibition,
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

	# This constructor is a minimal, stripped down version of the 
	# constructure above. The constructor above is only used to 
	# provid backwards compatibility to the old spatial pooler.
	# def __init__(self,
	# 						 numInputs,
	# 						 numColumns,
	# 						 localAreaDensity=0.1,
	# 						 numActiveColumnsPerInhArea=-1,
	# 						 stimulusThreshold=0,
	# 						 minDistance=0.0,
	# 						 maxBoost=10.0,
	# 						 seed=-1,
	# 						 spVerbosity=0,
	# 						 randomSP=False,
	# 						 ):

	# 	super(FlatSpatialPooler,self).__init__(
	# 			inputDimensions=numInputs,
	# 			columnDimensions=numColumns,
	# 			potentialRadius=numInputs,
	# 			potentialPct=0.5,
	# 			globalInhibition=True,
	# 			localAreaDensity=localAreaDensity,
	# 			numActiveColumnsPerInhArea=numActiveColumnsPerInhArea,
	# 			stimulusThreshold=stimulusThreshold,
	# 			seed=seed
	# 		)

	# 	#verify input is valid
	# 	assert(numColumns > 0)
	# 	assert(numInputs > 0)

	# 	# save arguments
	# 	self._numInputs = numInputs
	# 	self._numColumns = numColumns
	# 	self._minDistance = minDistance
	# 	self._randomSP = randomSP


	# 	#set active duty cycles to ones, because they set anomaly scores to 0
	# 	self._activeDutyCycles = numpy.ones(self._numColumns)

	# 	# set of columns to be 'hungry' for learning
	# 	self._boostFactors *= maxBoost

	def compute(self, inputVector, learn=True):
		if self._randomSP:
			learn=False

		assert (numpy.size(inputVector) == self._numInputs)
		self._updateBookeepingVars(learn)
		inputVector = numpy.array(inputVector, dtype=realDType)
		overlaps = self._calculateOverlap(inputVector)
		overlapsPct = self._calculateOverlapPct(overlaps)
		highTierColumns = self._selectHighTierColumns(overlapsPct)
		virginColumns = self._selectVirginColumns()

		if learn:
			vipOverlaps = self._boostFactors * overlaps
		else:
			vipOverlaps = overlaps.copy()

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
		else:
			activeColumns = self._stripNeverLearned(activeColumns)

		activeArray = numpy.zeros(self._numColumns)
		activeArray[activeColumns] = 1
		return activeArray

	def _selectVirginColumns(self):
		return numpy.where(self._activeDutyCycles == 0)[0]

	def _selectHighTierColumns(self, overlapsPct):
		return numpy.where(overlapsPct >= (1.0 - self._minDistance))[0]

  