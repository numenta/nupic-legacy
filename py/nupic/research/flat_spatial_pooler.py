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
from operator import itemgetter

from nupic.bindings.algorithms import (adjustMasterValidPermanence,
                                       cpp_overlap, cpp_overlap_sbm,
                                       Inhibition2 as Inhibition)
from nupic.bindings.math import (count_gte, GetNTAReal,
                                 Random as NupicRandom,
                                 SM_01_32_32 as SparseBinaryMatrix,
                                 SM32 as SparseMatrix)
from nupic.math.cross import cross
from nupic.research import fdrutilities as fdru
from nupic.research.spatial_pooler import SpatialPooler

realDType = GetNTAReal()



class FlatSpatialPooler(SpatialPooler):
	"""
	This class implements the flat spatial pooler. This version of the spatial 
	pooler contains no toplogy information. It uses global coverage and global
	inhibition
	"""

	def __init__(self,
							 numInputs,
							 numColumns,
							 localAreaDensity=0.1,
							 numActiveColumnsPerInhArea=-1,
							 stimulusThreshold=0,
							 minDistance=0.0,
							 maxBoost=10.0,
							 seed=-1,
							 spVerbosity=0,
							 ):

		super(FlatSpatialPooler,self).__init__(
				inputDimensions=numInputs,
				columnDimensions=numColumns,
				potentialRadius=numInputs,
				potentialPct=0.5,
				globalInhibition=True,
				localAreaDensity=localAreaDensity,
				numActiveColumnsPerInhArea=numActiveColumnsPerInhArea,
				stimulusThreshold=stimulusThreshold,
				seed=seed
			)

		#verify input is valid
		assert(numColumns > 0)
		assert(numInputs > 0)

		# save arguments
		self._numInputs = numInputs
		self._numColumns = numColumns
		self._minDistance = minDistance

		#set active duty cycles to ones, because they set anomaly scores to 0
		self._activeDutyCycles = numpy.ones(self._numColumns)

		# set of columns to be 'hungry' for learning
		self._boostFactors *= maxBoost
	

	def compute(self, inputVector, learn=True):
		assert (numpy.size(inputVector) == self._numInputs)

		self._updateBookeepingVars(learn)

		inputVector = numpy.array(inputVector, dtype=realDType)

		overlaps, overlapsPct = self._calculateOverlap(inputVector)
		vipColumns = self._selectVIPColumns(overlapsPct)
		vipOverlaps = overlaps.copy()
		vipOverlaps[vipColumns] = max(overlaps) + 1.0
		activeColumns = self._inhibitColumns(vipOverlaps)

		# if not learn: - don't let columns that never learned win! ???
		if self._isUpdateRound():
			self._updateMinDutyCycles()

		return numpy.array(activeColumns)


	def _selectVIPColumns(self, overlapsPct):
		return numpy.where(overlapsPct >= (1.0 - self._minDistance))[0]
  