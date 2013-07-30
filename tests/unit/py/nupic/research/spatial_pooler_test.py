#!/usr/bin/env python
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
from mock import Mock, patch, ANY, call
import unittest2 as unittest
from nupic.bindings.math import SM32 as SparseMatrix, \
                                SM_01_32_32 as SparseBinaryMatrix, \
                                count_gte, GetNTAReal
from nupic.research.spatial_pooler import SpatialPooler


class SpatialPoolerTest(unittest.TestCase):
	"""Unit Tests for SpatialPooler class"""

	def setUp(self):
		self._sp = SpatialPooler(
				inputDimensions = [5],
       	columnDimensions = [5],
       	potentialRadius = 3,
       	potentialPct = 0.5,
       	globalInhibition = False,
       	localAreaDensity = -1.0,
       	numActiveColumnsPerInhArea = 3,
       	stimulusThreshold=1,
       	synPermInactiveDec=0.01,
       	synPermActiveInc = 0.1,
       	synPermActiveSharedDec = 0.04,
       	synPermOrphanDec = 0.05,
       	synPermConnected = 0.10,
       	minPctOverlapDutyCycle = 0.1,
       	minPctActiveDutyCycle = 0.1,
       	dutyCyclePeriod = 10,
       	maxBoost = 10.0,
       	seed = -1,
       	spVerbosity = 0,
			)

	def testCompute(self):
		"""
		Tests that compute gets called smoothly with no errors
		"""
		sp = self._sp
		for i in xrange(100):
			inputVector = (
					numpy.random.random(sp._numInputs) > 0.3
				).astype('int')
			sp.compute(inputVector,True)


	#test this and initPermanence with too big of a radius
	def testMapPotential(self):
		pass


	def testInhibitColumns(self):
		sp = self._sp
		sp._inhibitColumnsGlobal = Mock(return_value = 1)
		sp._inhibitColumnsLocal = Mock(return_value = 2)
		overlaps = numpy.random.rand(sp._numColumns)
		numpy.random.rand = Mock(return_value = 0)
		sp._numColumns = 5
		sp._inhibitionRadius = 10
		sp._columnDimensions = [32, 64]

		sp._inhibitColumnsGlobal.reset_mock()
		sp._inhibitColumnsLocal.reset_mock()
		sp._numActiveColumnsPerInhArea = 5
		sp._localAreaDensity = 0.1
		sp._globalInhibition = True
		sp._inhibitionRadius = 5
		trueNumActive = sp._numActiveColumnsPerInhArea
		sp._inhibitColumns(overlaps)
		self.assertEqual(True,sp._inhibitColumnsGlobal.called)
		self.assertEqual(False,sp._inhibitColumnsLocal.called)		
		numActive = sp._inhibitColumnsGlobal.call_args[0][1]
		self.assertEqual(trueNumActive, numActive)
		

		sp._inhibitColumnsGlobal.reset_mock()
		sp._inhibitColumnsLocal.reset_mock()
		sp._numColumns = 500
		sp._columnDimensions = numpy.array([50, 10])
		sp._numActiveColumnsPerInhArea = -1
		sp._localAreaDensity = 0.1
		sp._globalInhibition = False
		sp._inhibitionRadius = 19
		# 0.1 * (19+1)**2
		trueNumActive = 40 
		sp._inhibitColumns(overlaps)
		self.assertEqual(False,sp._inhibitColumnsGlobal.called)
		self.assertEqual(True,sp._inhibitColumnsLocal.called)		
		numActive = sp._inhibitColumnsLocal.call_args[0][1]
		self.assertEqual(trueNumActive, numActive)

		#test inhibition radius too big leads to global inhibition
		sp._inhibitColumnsGlobal.reset_mock()
		sp._inhibitColumnsLocal.reset_mock()
		sp._numActiveColumnsPerInhArea = 11
		sp._localAreaDensity = 0.1
		sp._globalInhibition = False
		sp._inhibitionRadius = 70
		trueNumActive = 11 
		sp._inhibitColumns(overlaps)
		self.assertEqual(True,sp._inhibitColumnsGlobal.called)
		self.assertEqual(False,sp._inhibitColumnsLocal.called)		
		numActive = sp._inhibitColumnsGlobal.call_args[0][1]
		self.assertEqual(trueNumActive, numActive)



	def testUpdateBoostFactors(self):
		sp = self._sp
		sp._maxBoost = 10.0
		sp._numColumns = 6
		sp._minActiveDutyCycles = numpy.zeros(sp._numColumns) + 1e-6
		sp._activeDutyCycles = \
			numpy.array([0.1, 0.3, 0.02, 0.04, 0.7, 0.12])
		trueBoostFactors = [1, 1, 1, 1, 1, 1]
		sp._updateBoostFactors()
		self.assertListEqual(trueBoostFactors, list(sp._boostFactors))

		sp._maxBoost = 10.0
		sp._numColumns = 6
		sp._minActiveDutyCycles = \
			numpy.array([0.1, 0.3, 0.02, 0.04, 0.7, 0.12])
		sp._activeDutyCycles = \
			numpy.array([0.1, 0.3, 0.02, 0.04, 0.7, 0.12])
		trueBoostFactors = [1, 1, 1, 1, 1, 1]
		sp._updateBoostFactors()
		self.assertListEqual(trueBoostFactors, list(sp._boostFactors))

		sp._maxBoost = 10.0
		sp._numColumns = 6
		sp._minActiveDutyCycles = \
			numpy.array([0.1, 0.2, 0.02, 0.03, 0.7, 0.12])
		sp._activeDutyCycles = \
			numpy.array([0.01, 0.02, 0.002, 0.003, 0.07, 0.012])
		trueBoostFactors = [9.1, 9.1, 9.1, 9.1, 9.1, 9.1]
		sp._updateBoostFactors()
		self.assertListEqual(trueBoostFactors, list(sp._boostFactors))

		sp._maxBoost = 10.0
		sp._numColumns = 6
		sp._minActiveDutyCycles = \
			numpy.array([0.1, 0.2, 0.02, 0.03, 0.7, 0.12])
		sp._activeDutyCycles = \
			numpy.zeros(sp._numColumns)
		trueBoostFactors = 6*[sp._maxBoost]
		sp._updateBoostFactors()
		self.assertListEqual(trueBoostFactors, list(sp._boostFactors))


	def testUpdateInhibitionRadius(self):
		sp = self._sp

		# test global inhibition case
		sp._globalInhibition = True
		sp._numColumns = 57
		sp._updateInhibitionRadius()
		self.assertEqual(sp._inhibitionRadius, sp._numColumns)

		sp._globalInhibition = False
		sp._avgConnectedSpanForColumn1D = Mock(return_value = 3)
		sp._avgColumnsPerInput = Mock(return_value = 4)
		trueInhibitionRadius = 12
		sp._updateInhibitionRadius()
		self.assertEqual(trueInhibitionRadius, sp._inhibitionRadius)

		# test clipping at 1.0
		sp._globalInhibition = False
		sp._avgConnectedSpanForColumn1D = Mock(return_value = 0.5)
		sp._avgColumnsPerInput = Mock(return_value = 1.2)
		trueInhibitionRadius = 1
		sp._updateInhibitionRadius()
		self.assertEqual(trueInhibitionRadius, sp._inhibitionRadius)

		#test rounding up
		sp._globalInhibition = False
		sp._avgConnectedSpanForColumn1D = Mock(return_value = 2.4)
		sp._avgColumnsPerInput = Mock(return_value = 2)
		trueInhibitionRadius = 5
		sp._updateInhibitionRadius()
		self.assertEqual(trueInhibitionRadius, sp._inhibitionRadius)


	def testAvgColumnsPerInput(self):
		sp = self._sp
		sp._columnDimensions = numpy.array([2,2,2,2])
		sp._inputDimensions = numpy.array([4,4,4,4])
		self.assertEqual(sp._avgColumnsPerInput(),0.5)

		sp._columnDimensions = numpy.array([2, 2, 2, 2])
		sp._inputDimensions = numpy.array( [7, 5, 1, 3])
										#  2/7 0.4 2 0.666  
		trueAvgColumnPerInput = (2.0/7 + 2.0/5 + 2.0/1 + 2/3.0) / 4
		self.assertEqual(sp._avgColumnsPerInput(), trueAvgColumnPerInput)

		sp._columnDimensions = numpy.array([3, 3])
		sp._inputDimensions = numpy.array( [3, 3])
										#   1  1
		trueAvgColumnPerInput = 1
		self.assertEqual(sp._avgColumnsPerInput(), trueAvgColumnPerInput)				

		sp._columnDimensions = numpy.array([25])
		sp._inputDimensions = numpy.array( [5])
										#   5
		trueAvgColumnPerInput = 5
		self.assertEqual(sp._avgColumnsPerInput(), trueAvgColumnPerInput)

		sp._columnDimensions = numpy.array([3, 3, 3, 5, 5, 6, 6])
		sp._inputDimensions = numpy.array( [3, 3, 3, 5, 5, 6, 6])
										#   1  1  1  1  1  1  1
		trueAvgColumnPerInput = 1
		self.assertEqual(sp._avgColumnsPerInput(), trueAvgColumnPerInput)

		sp._columnDimensions = numpy.array([3, 6, 9, 12])
		sp._inputDimensions = numpy.array( [3, 3, 3 , 3])
										#   1  2  3   4
		trueAvgColumnPerInput = 2.5
		self.assertEqual(sp._avgColumnsPerInput(), trueAvgColumnPerInput)


	def testAvgConnectedSpanForColumn1D(self):
		sp = self._sp
		sp._numColumns = 9
		sp._columnDimensions = numpy.array([9])
		sp._inputDimensions = numpy.array([12])
		sp._connectedSynapses = \
			SparseBinaryMatrix([[0, 1, 0, 1, 0, 1, 0, 1],
								[0, 0, 0, 1, 0, 0, 0, 1],
								[0, 0, 0, 0, 0, 0, 1, 0],
								[0, 0, 1, 0, 0, 0, 1, 0],
								[0, 0, 0, 0, 0, 0, 0, 0],
								[0, 1, 1, 0, 0, 0, 0, 0],
								[0, 0, 1, 1, 1, 0, 0, 0],
								[0, 0, 1, 0, 1, 0, 0, 0],
								[1, 1, 1, 1, 1, 1, 1, 1]])
		
		trueAvgConnectedSpan = [6, 4, 0, 4, 0, 1, 2, 2, 7]
		for i in xrange(sp._numColumns):
			connectedSpan = sp._avgConnectedSpanForColumn1D(i)
			self.assertEqual(trueAvgConnectedSpan[i], connectedSpan)


	def testAvgConnectedSpanForColumn2D(self):
		sp = self._sp
		sp._numColumns = 9
		sp._columnDimensions = numpy.array([9])
		sp._numInpts = 8
		sp._inputDimensions = numpy.array([8])
		sp._connectedSynapses = SparseBinaryMatrix(
			[[0, 1, 0, 1, 0, 1, 0, 1],
			 [0, 0, 0, 1, 0, 0, 0, 1],
			 [0, 0, 0, 0, 0, 0, 1, 0],
			 [0, 0, 1, 0, 0, 0, 1, 0],
			 [0, 0, 0, 0, 0, 0, 0, 0],
			 [0, 1, 1, 0, 0, 0, 0, 0],
			 [0, 0, 1, 1, 1, 0, 0, 0],
			 [0, 0, 1, 0, 1, 0, 0, 0],
			 [1, 1, 1, 1, 1, 1, 1, 1]])
		
		trueAvgConnectedSpan = [6, 4, 0, 4, 0, 1, 2, 2, 7]
		for i in xrange(sp._numColumns):
			connectedSpan = sp._avgConnectedSpanForColumn1D(i)
			self.assertEqual(trueAvgConnectedSpan[i], connectedSpan)


	def testAvgConnectedSpanForColumn2D(self):
		sp = self._sp
		sp._numColumns = 7
		sp._columnDimensions = numpy.array([7])
		sp._numInputs = 20
		sp._inputDimensions = numpy.array([5, 4])
		sp._connectedSynapses = SparseBinaryMatrix(sp._numInputs)
		sp._connectedSynapses.resize(sp._numColumns, sp._numInputs)

		connected = numpy.array([
			[[0, 1, 1, 1],
			 [0, 1, 1, 1],
			 [0, 1, 1, 1],
			 [0, 0, 0, 0],
			 [0, 0, 0, 0]],
			 # rowspan = 2, colspan = 2, avg = 2
			 
			[[1, 1, 1, 1],
			 [0, 0, 1, 1],
			 [0, 0, 0, 0],
			 [0, 0, 0, 0],
			 [0, 0, 0, 0]],
			 #rowspan = 1 colspan = 3, avg = 2

			[[1, 0, 0, 0],
			 [0, 0, 0, 0],
			 [0, 0, 0, 0],
			 [0, 0, 0, 0],
			 [0, 0, 0, 1]],
			 #row span = 4, colspan = 3, avg = 3.5

			[[0, 1, 0, 0],
			 [0, 0, 0, 0],
			 [0, 0, 0, 0],
			 [0, 1, 0, 0],
			 [0, 1, 0, 0]],
			#rowspan = 4, colspan = 0, avg = 2

			[[0, 0, 0, 0],
			 [1, 0, 0, 1],
			 [0, 0, 0, 0],
			 [0, 0, 0, 0],
			 [0, 0, 0, 0]],
			#rowspan = 0, colspan = 3, avg = 1.5

			[[0, 0, 0, 0],
			 [0, 0, 0, 0],
			 [0, 0, 0, 0],
			 [0, 0, 1, 0],
			 [0, 0, 0, 1]],
			#rowspan = 1, colspan = 1, avg = 1

			[[0, 0, 0, 0],
			 [0, 0, 0, 0],
			 [0, 0, 0, 0],
			 [0, 0, 0, 0],
			 [0, 0, 0, 0]]
			#rowspan = 0, colspan = 0, avg = 0

			])

		trueAvgConnectedSpan = [2, 2, 3.5, 2, 1.5, 1, 0]
		for i in xrange(sp._numColumns):
			sp._connectedSynapses.replaceSparseRow(
				i,connected[i].reshape(-1).nonzero()[0]
			)

		for i in xrange(sp._numColumns):
			connectedSpan = sp._avgConnectedSpanForColumn2D(i)
			#import pdb; pdb.set_trace()
			self.assertEqual(trueAvgConnectedSpan[i], connectedSpan)		 


	def testAvgConnectedSpanForColumnND(self):
		sp = self._sp
		sp._inputDimensions = numpy.array([4,4,2,5])
		sp._numInputs = numpy.prod(sp._inputDimensions)
		sp._numColumns = 5
		sp._columnDimensions = numpy.array([5])
		sp._connectedSynapses = SparseBinaryMatrix(sp._numInputs)
		sp._connectedSynapses.resize(sp._numColumns, sp._numInputs)

		
		connected = numpy.zeros(sp._numInputs).reshape(sp._inputDimensions)
		connected[1][0][1][0] = 1
		connected[1][0][1][1] = 1
		connected[3][2][1][0] = 1
		connected[3][0][1][0] = 1
		connected[1][0][1][3] = 1
		connected[2][2][1][0] = 1
		# span:   2  2  0  3, avg = 7/4
		sp._connectedSynapses.replaceSparseRow(
			0,connected.reshape(-1).nonzero()[0]
		)

		connected = numpy.zeros(sp._numInputs).reshape(sp._inputDimensions)
		connected[2][0][1][0] = 1
		connected[2][0][0][0] = 1
		conncted[3][0][0][0] = 1
		connected[3][0][1][0] = 1
		# spn:   1  0  1  0, avg = 2/4
		sp._connectedSynapses.replaceSparseRow(
			1,connected.reshape(-1).nonzero()[0]
		)		

		connected = numpy.zeros(sp._numInputs).reshape(sp._inputDimensions)
		connected[0][0][1][4] = 1
		connected[0][0][0][3] = 1
		connected[0][0][0][1] = 1
		connected[1][0][0][2] = 1
		connected[0][0][1][1] = 1
		connected[3][3][1][1] = 1
		# span:   3  3  1  3, avg = 10/4
		sp._connectedSynapses.replaceSparseRow(
			2,connected.reshape(-1).nonzero()[0]
		)		

		connected = numpy.zeros(sp._numInputs).reshape(sp._inputDimensions)
		connected[3][3][1][4] = 1
		connected[0][0][0][0] = 1
		# span:   3  3  1  4, avg = 11/4
		sp._connectedSynapses.replaceSparseRow(
			3,connected.reshape(-1).nonzero()[0]
		)		

		connected = numpy.zeros(sp._numInputs).reshape(sp._inputDimensions)
		# span:   0  0  0  0, avg = 0
		sp._connectedSynapses.replaceSparseRow(
			4,connected.reshape(-1).nonzero()[0]
		)		

		trueAvgConnectedSpan = [7.0/4, 2.0/4, 10.0/4, 11.0/4, 0]			

		for i in xrange(sp._numColumns):
			connectedSpan = sp._avgConnectedSpanForColumnND(i)
			self.assertAlmostEqual(trueAvgConnectedSpan[i], connectedSpan)


	def testBumpUpWeakColumns(self):
	 	sp = SpatialPooler(inputDimensions = 8,
						   columnDimensions = 5)

	 	sp._synPermBelowStimulusInc = 0.01
	 	sp._synPermTrimThreshold = 0.05
	 	sp._overlapDutyCycles = numpy.array([0, 0.009, 0.1, 0.001, 0.002])
	 	sp._minOverlapDutyCycles = numpy.array(5*[0.01])

	 	sp._potentialPools = SparseBinaryMatrix(
	 		[[1, 1, 1, 1, 0, 0, 0, 0],
			 [1, 0, 0, 0, 1, 1, 0, 1],
	    	 [0, 0, 1, 0, 1, 1, 1, 0],
			 [1, 1, 1, 0, 0, 0, 1, 0],
			 [1, 1, 1, 1, 1, 1, 1, 1]])

		sp._permanences = SparseMatrix(
			[[0.200, 0.120, 0.090, 0.040, 0.000, 0.000, 0.000, 0.000],	
			 [0.150, 0.000, 0.000, 0.000, 0.180, 0.120, 0.000, 0.450], 
	 		 [0.000, 0.000, 0.014, 0.000, 0.032, 0.044, 0.110, 0.000],
	 	  	 [0.041, 0.000, 0.000, 0.000, 0.000, 0.000, 0.178, 0.000],
	 	  	 [0.100, 0.738, 0.045, 0.002, 0.050, 0.008, 0.208, 0.034]])

		truePermanences = \
			[[0.210, 0.130, 0.100, 0.000, 0.000, 0.000, 0.000, 0.000], 	
		#		Inc    Inc    Inc    Trim 	 - 		-	   -	  -
			[0.160, 0.000, 0.000, 0.000, 0.190, 0.130, 0.000, 0.460], 
		#		Inc 	-	   -	  -		 Inc 	Inc    -  	 Inc
	    	[0.000, 0.000, 0.014, 0.000, 0.032, 0.044, 0.110, 0.000], #unchanged
		#		-		-	   -	  -		 -		-	   -	  -
		 	[0.051, 0.000, 0.000, 0.000, 0.000, 0.000, 0.188, 0.000],
		#		Inc   Trim 	 Trim 	 -		 -		-	  Inc 	  -
		    [0.110, 0.748, 0.055, 0.000, 0.060, 0.000, 0.218, 0.000]]
	    #		Inc 	Inc   Inc 	 Trim 	 Inc   Trim   Inc 	 Trim

		sp._bumpUpWeakColumns()
		for i in xrange(sp._numColumns):
			perm = list(sp._permanences.getRow(i))
			for j in xrange(sp._numInputs):
				self.assertAlmostEqual(truePermanences[i][j], perm[j])


	def testUpdateMinDutyCycleLocal(self):
		sp = self._sp

		#replace the get neighbors function with
		#a mock to know exactly the neighbors 
		#of each column
		sp._numColumns = 5
		sp._getNeighborsND = Mock(side_effect= \
			[[0,1,2],
			 [1,2,3],
			 [2,3,4],
			 [0,2,4],
			 [0,1,3]])

		sp._minPctOverlapDutyCycles = 0.04
		sp._overlapDutyCycles = numpy.array([1.4, 0.5, 1.2, 0.8, 0.1])
		trueMinOverlapDutyCycles = [0.04*1.4, 0.04*1.2, 0.04*1.2, 0.04*1.4, 
									0.04*1.4]

		sp._minPctActiveDutyCycles = 0.02
		sp._activeDutyCycles = numpy.array([0.4, 0.5, 0.2, 0.18, 0.1])
		trueMinActiveDutyCycles = [0.02*0.5, 0.02*0.5, 0.02*0.2, 0.02*0.4, 
								   0.02*0.5]

		sp._minOverlapDutyCycles = numpy.zeros(sp._numColumns)
		sp._minActiveDutyCycles = numpy.zeros(sp._numColumns)
		sp._updateMinDutyCyclesLocal()
		self.assertListEqual(trueMinOverlapDutyCycles, \
							list(sp._minOverlapDutyCycles))
		self.assertListEqual(trueMinActiveDutyCycles, \
							list(sp._minActiveDutyCycles))

		sp._numColumns = 8
		sp._getNeighborsND = Mock(side_effect= \
			[[0,1,2,3,4],
			 [1,2,3,4,5],
			 [2,3,4,6,7],
			 [0,2,4,6],
			 [1,6],
			 [3,5,7],
			 [1,4,5,6],
			 [2,3,6,7]])

		sp._minPctOverlapDutyCycles = 0.01
		sp._overlapDutyCycles = numpy.array( \
			[1.2, 2.7, 0.9, 1.1, 4.3, 7.1, 2.3, 0.0])
		trueMinOverlapDutyCycles = \
			[0.01*4.3, 0.01*7.1, 0.01*4.3, 0.01*4.3, 0.01*2.7, \
			 0.01*7.1, 0.01*7.1, 0.01*2.3]

		sp._minPctActiveDutyCycles = 0.03
		sp._activeDutyCycles = numpy.array( \
			[0.14, 0.25, 0.125, 0.33, 0.27, 0.11, 0.76, 0.31])
		trueMinActiveDutyCycles = \
			[0.03*0.33, 0.03*0.33, 0.03*0.76, 0.03*0.76, 0.03*0.76, \
			 0.03*0.33, 0.03*0.76, 0.03*0.76]
		sp._minOverlapDutyCycles = numpy.zeros(sp._numColumns)
		sp._minActiveDutyCycles = numpy.zeros(sp._numColumns)
		sp._updateMinDutyCyclesLocal()
		self.assertListEqual(trueMinOverlapDutyCycles, \
							list(sp._minOverlapDutyCycles))
		self.assertListEqual(trueMinActiveDutyCycles, \
							list(sp._minActiveDutyCycles))


	def testUpdateMinDutyCyclesGlobal(self):
		sp = self._sp
		sp._minPctOverlapDutyCycles = 0.01
		sp._minPctActiveDutyCycles = 0.02
		sp._numColumns = 5
		sp._overlapDutyCycles = numpy.array([0.06, 1, 3, 6, 0.5])
		sp._activeDutyCycles = numpy.array([0.6, 0.07, 0.5, 0.4, 0.3])
		sp._updateMinDutyCyclesGlobal()
		trueMinActiveDutyCycles = sp._numColumns*[0.02*0.6]
		trueMinOverlapDutyCycles = sp._numColumns*[0.01*6]
		self.assertListEqual(trueMinActiveDutyCycles,
							 list(sp._minActiveDutyCycles))
		self.assertListEqual(trueMinOverlapDutyCycles,
							 list(sp._minOverlapDutyCycles))

		sp._minPctOverlapDutyCycles = 0.015
		sp._minPctActiveDutyCycles = 0.03
		sp._numColumns = 5
		sp._overlapDutyCycles = numpy.array([0.86, 2.4, 0.03, 1.6, 1.5])
		sp._activeDutyCycles = numpy.array([0.16, 0.007, 0.15, 0.54, 0.13])
		sp._updateMinDutyCyclesGlobal()
		trueMinOverlapDutyCycles = sp._numColumns*[0.015*2.4]
		trueMinActiveDutyCycles = sp._numColumns*[0.03*0.54]
		self.assertListEqual(trueMinOverlapDutyCycles,
							 list(sp._minOverlapDutyCycles))
		self.assertListEqual(trueMinActiveDutyCycles,
							 list(sp._minActiveDutyCycles))

		sp._minPctOverlapDutyCycles = 0.015
		sp._minPctActiveDutyCycles= 0.03
		sp._numColumns = 5
		sp._overlapDutyCycles = numpy.zeros(5)
		sp._activeDutyCycles = numpy.zeros(5)
		sp._updateMinDutyCyclesGlobal()
		trueMinOverlapDutyCycles = sp._numColumns*[0]
		trueMinActiveDutyCycles = sp._numColumns*[0]
		self.assertListEqual(trueMinOverlapDutyCycles,
							 list(sp._minOverlapDutyCycles))
		self.assertListEqual(trueMinActiveDutyCycles,
							 list(sp._minActiveDutyCycles))


	def testIsUpdateRound(self):
		sp = self._sp
		sp._updatePeriod = 50
		sp._iterationNum = 0
		self.assertEqual(sp._isUpdateRound(),False)
		sp._iterationNum = 39
		self.assertEqual(sp._isUpdateRound(),False)
		sp._iterationNum = 49
		self.assertEqual(sp._isUpdateRound(),True)
		sp._iterationNum = 1009
		self.assertEqual(sp._isUpdateRound(),False)
		sp._iterationNum = 1249
		self.assertEqual(sp._isUpdateRound(),True)

		sp._updatePeriod = 125
		sp._iterationNum = 0
		self.assertEqual(sp._isUpdateRound(),False)
		sp._iterationNum = 200
		self.assertEqual(sp._isUpdateRound(),False)
		sp._iterationNum = 249
		self.assertEqual(sp._isUpdateRound(),True)
		sp._iterationNum = 1330
		self.assertEqual(sp._isUpdateRound(),False)
		sp._iterationNum = 1249
		self.assertEqual(sp._isUpdateRound(),True)
		sp._iterationNum = 1374
		self.assertEqual(sp._isUpdateRound(),True)


	def testCalculateAnomalyScore(self):
		sp = self._sp
		overlaps = numpy.array([5, 4, 3, 2, 1])
		activeColumns = numpy.array([0,2,3,4])
		sp._activeDutyCycles = numpy.array([50, 40, 30, 20, 10])
		anomalyScore = sp._calculateAnomalyScore(overlaps, activeColumns)
		trueAnomalyScore = 1.0/(5*50 + 3*30 + 2*20 + 10 + 1)
		self.assertEqual(trueAnomalyScore,anomalyScore)

		overlaps = numpy.array([5, 4, 3, 2, 1])
		activeColumns = numpy.array([0])
		sp._activeDutyCycles = numpy.array([50, 40, 30, 20, 10])
		anomalyScore = sp._calculateAnomalyScore(overlaps, activeColumns)
		trueAnomalyScore = 1.0/(5*50 + 1)
		self.assertEqual(trueAnomalyScore,anomalyScore)

		overlaps = numpy.array([5, 4, 3, 2, 1])
		activeColumns = numpy.array([])
		sp._activeDutyCycles = numpy.array([50, 40, 30, 20, 10])
		anomalyScore = sp._calculateAnomalyScore(overlaps, activeColumns)
		trueAnomalyScore = 1.0
		self.assertEqual(trueAnomalyScore,anomalyScore)

	def testAdaptSynapses(self):
		sp = SpatialPooler(inputDimensions = 8,
						   columnDimensions = 4,
               			   synPermInactiveDec=0.01,
               			   synPermActiveInc = 0.1,
               			   synPermActiveSharedDec = 0.02,
               			   synPermOrphanDec = 0.03)
		sp._synPermTrimThreshold = 0.05

		sp._potentialPools = SparseBinaryMatrix(
			[[1, 1, 1, 1, 0, 0, 0, 0],
			 [1, 0, 0, 0, 1, 1, 0, 1],
			 [0, 0, 1, 0, 0, 0, 1, 0],
			 [1, 0, 0, 0, 0, 0, 1, 0]])

		inputVector = numpy.array([1, 0, 0, 1, 1, 0, 1, 0])
		sharedInputs = numpy.where(numpy.array(
								[1, 0, 0, 0, 0, 0, 1, 0]) > 0)[0]
		orphanColumns = numpy.array([])

		sp._permanences = SparseMatrix(
			[[0.200, 0.120, 0.090, 0.040, 0.000, 0.000, 0.000, 0.000],
			 [0.150, 0.000, 0.000, 0.000, 0.180, 0.120, 0.000, 0.450],
	    	 [0.000, 0.000, 0.014, 0.000, 0.000, 0.000, 0.110, 0.000],
	    	 [0.040, 0.000, 0.000, 0.000, 0.000, 0.000, 0.178, 0.000]])

		truePermanences = \
			[[0.280, 0.110, 0.080, 0.140, 0.000, 0.000, 0.000, 0.000],
			#  Inc/Sh 	Dec	   Dec 	 Inc	 -		-		-	-
		  	 [0.230, 0.000, 0.000, 0.000, 0.280, 0.110, 0.000, 0.440],
		 	#  Inc/Sh 	 -		-	   -	Inc    Dec 	   -      Dec	
	    	 [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.190, 0.000],
		  	#   -  		- 	  Trim 	  -		 - 		-	  Inc/Sh   - 
  		     [0.120, 0.000, 0.000, 0.000, 0.000, 0.000, 0.258, 0.000]]
			#  Inc/Sh 	- 	   -	  -		  -		-	  Inc/Sh   -	

		sp._adaptSynapses(inputVector,sharedInputs, orphanColumns)
		for i in xrange(sp._numColumns):
			perm = list(sp._permanences.getRow(i))
			for j in xrange(sp._numInputs):
				self.assertAlmostEqual(truePermanences[i][j], perm[j])

		# test orphan columns
		sp._potentialPools = \
			SparseBinaryMatrix([[1, 1, 1, 0, 0, 0, 0, 0],
								[0, 1, 1, 1, 0, 0, 0, 0],
								[0, 0, 1, 1, 1, 0, 0, 0],
								[1, 0, 0, 0, 0, 0, 1, 0]])

		inputVector = numpy.array( \
								[1, 0, 0, 1, 1, 0, 1, 0])
		sharedInputs = numpy.where(numpy.array(
								[1, 0, 0, 1, 0, 0, 0, 0]) > 0)[0]
		orphanColumns = numpy.array([3])

		sp._permanences = SparseMatrix(
			[[0.200, 0.120, 0.090, 0.000, 0.000, 0.000, 0.000, 0.000],
			 [0.000, 0.017, 0.232, 0.400, 0.000, 0.000, 0.000, 0.000],
	    	 [0.000, 0.000, 0.014, 0.051, 0.730, 0.000, 0.000, 0.000],
	    	 [0.170, 0.000, 0.000, 0.000, 0.000, 0.000, 0.380, 0.000]])

		truePermanences = [
			 [0.280, 0.110, 0.080, 0.000, 0.000, 0.000, 0.000, 0.000],
		    #  Inc/Sh  	Dec	   Dec 	  -	     -		-		-		-
			 [0.000, 0.000, 0.222, 0.480, 0.000, 0.000, 0.000, 0.000],
			#  	 - 	   Trim	   Dec	Inc/Sh	 -     	- 	   -      -	
	    	 [0.000, 0.000, 0.000, 0.131, 0.830, 0.000, 0.000, 0.000],
	    	#   -  		- 	   Trim Inc/Sh	Inc	 	- 		-	   - 
			 [0.220, 0.000, 0.000, 0.000, 0.000, 0.000, 0.450, 0.000]]
			#	Inc/Sh/Orph	- 	   -	  -		  -		-	Inc/Orph   -	

		sp._adaptSynapses(inputVector,sharedInputs, orphanColumns)
		for i in xrange(sp._numColumns):
			perm = list(sp._permanences.getRow(i))
			for j in xrange(sp._numInputs):
				self.assertAlmostEqual(truePermanences[i][j], perm[j])


	def testCalculateSharedInputs(self):
		pass

	def testCalculateOrpanColumns(self):
		sp = self._sp
		
		activeColumns = numpy.array([])
		overlapsPct = numpy.array(
			[1, 0.12, 0.15, 0.92, 0.4, 1, 1, 0.88, 1, 0.1]
		)
		orphanColumns = sp._calculateOrphanColumns(activeColumns, overlapsPct)
		trueOrphanColumns = []
		self.assertListEqual(trueOrphanColumns, list(orphanColumns))

		activeColumns = numpy.array(range(10))
		overlapsPct = numpy.array(
			[0.98, 0.12, 0.15, 0.92, 0.4, 0.41, 0.61, 0.88, 0.01, 0.1]
		)
		orphanColumns = sp._calculateOrphanColumns(activeColumns, overlapsPct)
		trueOrphanColumns = []
		self.assertListEqual(trueOrphanColumns, list(orphanColumns))

		activeColumns = numpy.array([5,6,7])
		overlapsPct = numpy.array(
			[1, 0.12, 0.15, 0.92, 0.4, 1, 1, 0.88, 1, 0.1]
		)
		orphanColumns = sp._calculateOrphanColumns(activeColumns, overlapsPct)
		trueOrphanColumns = [5,6]
		self.assertListEqual(trueOrphanColumns, list(orphanColumns))

		activeColumns = numpy.array([1,2,3,6,7])
		overlapsPct = numpy.array([1, 0.12, 1, 0.92, 1, 0.4, 1, 0.88, 1, 0.1])
		orphanColumns = sp._calculateOrphanColumns(activeColumns, overlapsPct)
		trueOrphanColumns = [2,6]
		self.assertListEqual(trueOrphanColumns, list(orphanColumns))

	def testRaisePermanenceThreshold(self):
		sp = SpatialPooler(inputDimensions = 5, 
						   columnDimensions=5, 
						   synPermConnected=0.1,
						   stimulusThreshold=3)
		sp._synPermBelowStimulusInc = 0.01
		sp._permanences = SparseMatrix(
			[[0.0, 0.11, 0.095, 0.092, 0.01],
			 [0.12, 0.15, 0.02, 0.12, 0.09],
	    	 [0.51, 0.081, 0.025, 0.089, 0.31],
			 [0.18, 0.0601, 0.11, 0.011, 0.03],
			 [0.011, 0.011, 0.011, 0.011, 0.011]])
		
		sp._connectedSynapses = SparseBinaryMatrix(
			[[0, 1, 0, 0, 0],
			 [1, 1, 0, 1, 0],
	    	 [1, 0, 0, 0, 1],
			 [1, 0, 1, 0, 0],
			 [0, 0, 0, 0, 0]])
		
		sp._connectedCounts = numpy.array([1, 3, 2, 2, 0])

		truePermanences = [
					[0.0, 0.12, 0.105, 0.102, 0.0],	# incremented once
					[0.12, 0.15, 0.02, 0.12, 0.09],	# no change
	    			[0.53, 0.101, 0.0, 0.109, 0.33],	# increment twice 
			   		[0.22, 0.1001, 0.15, 0.051, 0.07],	# increment four times
			   		[0.101, 0.101, 0.101, 0.101, 0.101]]	#increment 9 times


		trueConnectedSynapses = [
			[0, 1, 1, 1, 0],
			[1, 1, 0, 1, 0],
			[1, 1, 0, 1, 1],
			[1, 1, 1, 0, 0],
			[1, 1, 1, 1, 1]]

		trueConnectedCounts = [3, 3, 4, 3, 5]
		sp._raisePermanenceToThreshold()
		for i in xrange(sp._numColumns):
			perm = list(sp._permanences.getRow(i))
			for j in xrange(sp._numInputs):
				self.assertAlmostEqual(truePermanences[i][j],perm[j])
			self.assertListEqual(
				trueConnectedSynapses[i],
				list(sp._connectedSynapses.getRow(i))
			)
			self.assertEqual(trueConnectedCounts[i], sp._connectedCounts[i])


	def testUpdatePermanencesForColumn(self):
		sp = SpatialPooler(inputDimensions = 5, 
						   columnDimensions=5, 
						   synPermConnected=0.1)
		sp._synPermTrimThreshold = 0.05
		permanences = numpy.array(	   
			[[-0.10, 0.500, 0.400, 0.010, 0.020],
			 [0.300, 0.010, 0.020, 0.120, 0.090],
			 [0.070, 0.050, 1.030, 0.190, 0.060],
			 [0.180, 0.090, 0.110, 0.010, 0.030],
			 [0.200, 0.101, 0.050, -0.09, 1.100]])

		truePermanences = SparseMatrix(
			[[0.000, 0.500, 0.400, 0.000, 0.000],
			#		  Clip 	  -		 - 	   Trim   Trim
			 [0.300, 0.000, 0.000, 0.120, 0.090],
			#		   - 	 Trim 	Trim 	- 		-
			 [0.070, 0.050, 1.000, 0.190, 0.060],
			# 		   - 	  - 	Clip 	- 		-
			 [0.180, 0.090, 0.110, 0.000, 0.000],
			# 			- 	  - 	 - 	   Trim   Trim
			 [0.200, 0.101, 0.050, 0.000, 1.000]])
			#		   -  	  -  	 - 	   Clip   Clip

		trueConnectedSynapses = [
			[0, 1, 1, 0, 0],
			[1, 0, 0, 1, 0],
			[0, 0, 1, 1, 0],
			[1, 0, 1, 0, 0],
			[1, 1, 0, 0, 1]]

		trueConnectedCounts = [2,2,2,2,3]
		for i in xrange(sp._numColumns):
			sp._updatePermanencesForColumn(permanences[i],i)
			self.assertListEqual(
				trueConnectedSynapses[i],
				list(sp._connectedSynapses.getRow(i))
			)
		self.assertListEqual(trueConnectedCounts, list(sp._connectedCounts))
		

	def testCalculateSharedInputs(self):
		sp = SpatialPooler(inputDimensions = 8, 
						   columnDimensions=5)
		sp._connectedSynapses = SparseBinaryMatrix(
			[[0, 1, 0, 1, 0, 1, 0, 1],
			 [0, 0, 0, 1, 0, 0, 0, 1],
			 [0, 0, 0, 0, 0, 0, 1, 0],
			 [0, 0, 1, 0, 0, 0, 1, 0],
			 [1, 0, 0, 0, 1, 0, 0, 0]])
		inputVector = numpy.array(
			 [1, 1, 1, 1, 0, 0, 0, 0])
		activeColumns = range(5)
		sharedTrue = set([3])
		shared = set(sp._calculateSharedInputs(inputVector, activeColumns))
		self.assertSetEqual(shared, sharedTrue)

		sp._connectedSynapses = SparseBinaryMatrix(
			[[0, 1, 0, 1, 0, 1, 0, 1],
			 [0, 0, 0, 1, 0, 0, 0, 1],
			 [0, 0, 0, 0, 0, 0, 1, 0],
			 [0, 0, 1, 0, 0, 0, 1, 0],
			 [1, 0, 0, 0, 1, 0, 0, 0]])
		inputVector = numpy.array(
			 [1, 1, 1, 0, 1, 1, 1, 1])
		activeColumns = range(5)
		sharedTrue = set([6,7])
		shared = set(sp._calculateSharedInputs(inputVector, activeColumns))
		self.assertSetEqual(shared, sharedTrue)

		sp._connectedSynapses = SparseBinaryMatrix(
			[[0, 1, 0, 1, 0, 1, 0, 1],
			 [0, 0, 0, 1, 0, 0, 0, 1],
			 [0, 0, 0, 0, 0, 0, 1, 0],
			 [0, 0, 1, 0, 0, 0, 1, 0],
			 [1, 0, 0, 0, 1, 0, 0, 0]])
		inputVector = numpy.array(
			 [0, 0, 0, 0, 0, 0, 0, 0])

		activeColumns = range(5)
		sharedTrue = set([])
		shared = set(sp._calculateSharedInputs(inputVector, activeColumns))
		self.assertSetEqual(shared, sharedTrue)

		sp._connectedSynapses = SparseBinaryMatrix(
			[[0, 1, 0, 1, 0, 1, 0, 1],
			 [0, 0, 0, 1, 0, 0, 0, 1],
			 [0, 0, 0, 0, 0, 0, 1, 0],
			 [0, 0, 1, 0, 0, 0, 1, 0],
			 [1, 0, 0, 0, 1, 0, 0, 0]])
		inputVector = numpy.array(
			 [1, 0, 1, 0, 1, 1, 1, 0])

		activeColumns = [1,2,3]
		sharedTrue = set([6])
		shared = set(sp._calculateSharedInputs(inputVector, activeColumns))
		self.assertSetEqual(shared, sharedTrue)
		
		sp._connectedSynapses = SparseBinaryMatrix(
			[[0, 1, 0, 1, 0, 1, 0, 1],
			 [0, 0, 0, 1, 0, 0, 0, 1],
			 [0, 0, 0, 0, 0, 0, 1, 0],
			 [0, 0, 1, 0, 0, 0, 1, 0],
			 [1, 0, 0, 0, 1, 0, 0, 0]])
		inputVector = numpy.array(
			 [1, 0, 1, 1, 1, 1, 1, 1])
		activeColumns = [0,1,3,4]
		sharedTrue = set([3,7])
		shared = set(sp._calculateSharedInputs(inputVector, activeColumns))
		self.assertSetEqual(shared, sharedTrue)



	def testCalculateOverlap(self):
		"""
		test that column computes overlap and percent overlap correctly
		"""
		sp = SpatialPooler(inputDimensions = 10, 
						   columnDimensions=5)
		sp._connectedSynapses = SparseBinaryMatrix(
			[[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
			 [0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
			 [0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
			 [0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
			 [0, 0, 0, 0, 0, 0, 0, 0, 1, 1]])
		sp._connectedCounts = numpy.array([10.0, 8.0, 6.0, 4.0, 2.0])
		inputVector = numpy.zeros(sp._numInputs, dtype='float32')
		overlaps, overlapsPct = sp._calculateOverlap(inputVector)
		trueOverlaps = list(numpy.array([0, 0, 0, 0, 0]))
		trueOverlapsPct = list(numpy.array([0, 0, 0, 0, 0]))
		self.assertListEqual(list(overlaps), trueOverlaps)
		self.assertListEqual(list(overlapsPct), trueOverlapsPct)

		sp._connectedSynapses = SparseBinaryMatrix(
			[[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
			 [0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
			 [0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
			 [0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
			 [0, 0, 0, 0, 0, 0, 0, 0, 1, 1]])
		sp._connectedCounts = numpy.array([10.0, 8.0, 6.0, 4.0, 2.0])
		inputVector = numpy.ones(sp._numInputs, dtype='float32')
		overlaps, overlapsPct = sp._calculateOverlap(inputVector)
		trueOverlaps = list(numpy.array([10, 8, 6, 4, 2]))
		trueOverlapsPct = list(numpy.array([1, 1, 1, 1, 1]))
		self.assertListEqual(list(overlaps), trueOverlaps)
		self.assertListEqual(list(overlapsPct), trueOverlapsPct)

		sp._connectedSynapses = SparseBinaryMatrix(
			[[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
			 [0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
			 [0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
			 [0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
			 [0, 0, 0, 0, 0, 0, 0, 0, 1, 1]])
		sp._connectedCounts = numpy.array([10.0, 8.0, 6.0, 4.0, 2.0])
		inputVector = numpy.zeros(sp._numInputs, dtype='float32')
		inputVector[9] = 1
		overlaps, overlapsPct = sp._calculateOverlap(inputVector)
		trueOverlaps = list(numpy.array([1, 1, 1, 1, 1]))
		trueOverlapsPct = list(numpy.array([0.1, 0.125, 1.0/6, 0.25, 0.5]))
		self.assertListEqual(list(overlaps), trueOverlaps)
		self.assertListEqual(list(overlapsPct), trueOverlapsPct)

		#zig-zag
		sp._connectedSynapses = SparseBinaryMatrix(
			[[1, 0, 0, 0, 0, 1, 0, 0, 0, 0],
			 [0, 1, 0, 0, 0, 0, 1, 0, 0, 0],
			 [0, 0, 1, 0, 0, 0, 0, 1, 0, 0],
			 [0, 0, 0, 1, 0, 0, 0, 0, 1, 0],
			 [0, 0, 0, 0, 1, 0, 0, 0, 0, 1]])
		sp._connectedCounts = numpy.array([2.0, 2.0, 2.0, 2.0, 2.0])
		inputVector = numpy.zeros(sp._numInputs, dtype='float32')
		inputVector[range(0,10,2)] = 1
		overlaps, overlapsPct = sp._calculateOverlap(inputVector)
		trueOverlaps = list(numpy.array([1, 1, 1, 1, 1]))
		trueOverlapsPct = list(numpy.array([0.5, 0.5, 0.5, 0.5, 0.5]))
		self.assertListEqual(list(overlaps), trueOverlaps)
		self.assertListEqual(list(overlapsPct), trueOverlapsPct)


	def testInitPermanence1(self):
		"""
		test initial permanence generation. ensure that
		a correct amount of synapses are initialized in 
		a connected state, with permanence values drawn from
		the correct ranges
		"""

		sp = self._sp
		sp._potentialRadius = 2
		sp._potentialPct = 1
		perm = sp._initPermanence(0)
		connected = (perm > sp._synPermConnected).astype(int)
		numcon = (connected.nonzero()[0]).size
		self.assertEqual(numcon, sp._numInputs)
		maxThresh = sp._synPermConnected + sp._synPermActiveInc/4
		self.assertEqual((perm <= maxThresh).all(),True)

		sp._potentialPct = 0
		perm = sp._initPermanence(0)
		connected = (perm > sp._synPermConnected).astype(int)
		numcon = (connected.nonzero()[0]).size
		self.assertEqual(numcon, 0)

		sp._potentialPct = 0.5
		sp._potentialRadius = 100
		sp._numInputs = 100
		perm = sp._initPermanence(0)
		connected = (perm > sp._synPermConnected).astype(int)
		numcon = (connected.nonzero()[0]).size
		self.assertGreater(numcon, 0)
		self.assertLess(numcon, sp._numInputs)

		minThresh = sp._synPermActiveInc / 2.0
		connThresh = sp._synPermConnected
		self.assertEqual(numpy.logical_and((perm >= minThresh),
			(perm <= connThresh)).any(),True)


	def testInitPermanence2(self):
		"""
		test initial permanence generation. ensure that
		permanence values are only assigned to bits within
		a column's potential pct
		"""
		sp = self._sp

		sp._numInputs = 10
		sp._potentialRadius = 1
		index = 0
		sp._potentialPct = 1
		#import pdb; pdb.set_trace()
		perm = sp._initPermanence(index)
  		connected = list((perm > 0).astype(int))
		trueConnected = [1,1,0,0,0,0,0,0,0,1]
		self.assertListEqual(connected, trueConnected)

		sp._potentialRadius = 1
		sp._potentialPct = 1
		index = 5
		perm = sp._initPermanence(index)
  		connected = list((perm > 0).astype(int))
		trueConnected = [0,0,0,0,1,1,1,0,0,0]
		self.assertListEqual(connected, trueConnected)


		sp._potentialRadius = 1
		sp._potentialPct = 1
		index = 9
		perm = sp._initPermanence(index)
  		connected = list((perm > 0).astype(int))
		trueConnected = [1,0,0,0,0,0,0,0,1,1]
		self.assertListEqual(connected, trueConnected)

		sp._potentialRadius = 4
		sp._potentialPct = 1
		index = 2
		perm = sp._initPermanence(index)
  		connected = list((perm > 0).astype(int))
		trueConnected = [1,1,1,1,1,1,1,0,1,1]
		self.assertListEqual(connected, trueConnected)

	def testInitPermanence3(self):
		"""
		TODO: implement tests for region-wide permanence initialization
		"""
		pass

	def testUpdateDutyCycleHelper(self):
		"""
		tests that duty cycles are updated properly according
		to the mathematical formula. also check the effects of
		supplying a maxPeriod to the function.
		"""
		dc = numpy.zeros(5)
		dc = numpy.array([1000.0, 1000.0, 1000.0, 1000.0, 1000.0])
		period = 1000
		newvals = numpy.zeros(5)
		newDc = SpatialPooler._updateDutyCyclesHelper(dc, newvals, period)
		trueNewDc = [999, 999, 999, 999, 999]
		self.assertListEqual(list(newDc),trueNewDc)

		dc = numpy.array([1000.0, 1000.0, 1000.0, 1000.0, 1000.0])
		period = 1000
		newvals = numpy.zeros(5)
		newvals.fill(1000)
		newDc = SpatialPooler._updateDutyCyclesHelper(dc, newvals, period)
		trueNewDc = list(dc)
		self.assertListEqual(list(newDc), trueNewDc)

		dc = numpy.array([1000, 1000, 1000, 1000, 1000])
		newvals = numpy.array([2000, 4000, 5000, 6000, 7000])
		period = 1000
		newDc = SpatialPooler._updateDutyCyclesHelper(dc, newvals, period)
		trueNewDc = [1001, 1003, 1004, 1005, 1006]
		self.assertListEqual(list(newDc),trueNewDc)

		dc = numpy.array([1000, 800, 600, 400, 2000])
		newvals = numpy.zeros(5)
		period = 2
		newDc = SpatialPooler._updateDutyCyclesHelper(dc, newvals, period)
		trueNewDc = [500, 400, 300, 200, 1000]
		self.assertListEqual(list(newDc), trueNewDc)
		

	def testInhibitColumnsGlobal(self):
		"""
		tests that global inhibition correctly picks the 
		correct top number of overlap scores as winning columns
		"""
		sp = self._sp
		numActive = 3
		sp._numColumns = 10
		overlaps = numpy.array([1,2,1,4,8,3,12,5,4,1])
		active = list(sp._inhibitColumnsGlobal(overlaps, numActive))
		trueActive = numpy.zeros(sp._numColumns)
		trueActive = [4,6,7]
		self.assertListEqual(list(trueActive), active)

		numActive = 5
		sp._numColumns = 10
		overlaps = numpy.array(range(10))
		active = list(sp._inhibitColumnsGlobal(overlaps, numActive))
		trueActive = numpy.zeros(sp._numColumns)
		trueActive = range(5,10)
		self.assertListEqual(trueActive, active)


	def testInhibitColumnsLocal(self):
		sp = self._sp
		numActive = 2
		sp._numColumns = 10
		sp._columnDimensions = numpy.array([sp._numColumns])
		sp._inhibitionRadius = 1
		overlaps = numpy.array([1,2,7,0,3,4,16,1,1.5,1.7])
							#   L W W L W W W  L  W   W
		trueActive = [1,2,4,5,6,8,9]
		active = list(sp._inhibitColumnsLocal(overlaps, numActive))
		self.assertListEqual(trueActive, active)

		numActive = 2
		sp._numColumns = 10
		sp._columnDimensions = numpy.array([sp._numColumns])
		sp._inhibitionRadius = 2
		overlaps = numpy.array([1,2,7,0,3,4,16,1,1.5,1.7])
							#   L W W L L W W  L  L   W
		trueActive = [1,2,5,6,9]
		active = list(sp._inhibitColumnsLocal(overlaps,numActive))
		self.assertListEqual(trueActive, active)

		# test add to winners
		numActive = 2
		sp._numColumns = 10
		sp._columnDimensions = numpy.array([sp._numColumns])
		sp._inhibitionRadius = 3
		overlaps = numpy.array([1,1,1,1,1,1,1,1,1,1])
							#   W W L L W W L L L L
		trueActive = 		   [0,1,4,5]
		active = list(sp._inhibitColumnsLocal(overlaps, numActive))
		self.assertListEqual(trueActive, active)


	def testGetNeighbors1D(self):
		"""
		Test that _getNeighbors static method correctly computes
		the neighbors of a column
		"""
		sp = self._sp

		layout = numpy.array([0, 0, 1, 0, 1, 0, 0,  0])
		layout1D = layout.reshape(-1)
		columnIndex = 3
		dimensions = numpy.array([8])
		radius = 1
		mask = sp._getNeighbors1D(columnIndex, dimensions, radius)
		negative = set(range(dimensions.prod())) - set(mask)
		self.assertEqual(layout1D[mask].all(), True)
		self.assertEqual(layout1D[list(negative)].any(),False)

		layout = numpy.array([0, 1, 1, 0, 1, 1, 0,  0])
		layout1D = layout.reshape(-1)
		columnIndex = 3
		dimensions = numpy.array([8])
		radius = 2
		mask = sp._getNeighbors1D(columnIndex, dimensions, radius)
		negative = set(range(dimensions.prod())) - set(mask)
		self.assertEqual(layout1D[mask].all(), True)
		self.assertEqual(layout1D[list(negative)].any(),False)

		#wrap around
		layout = numpy.array([0, 1, 1, 0, 0, 0, 1,  1])
		layout1D = layout.reshape(-1)
		columnIndex = 0
		dimensions = numpy.array([8])
		radius = 2
		mask = sp._getNeighbors1D(columnIndex, dimensions, radius)
		negative = set(range(dimensions.prod())) - set(mask)
		#import pdb; pdb.set_trace()
		self.assertEqual(layout1D[mask].all(), True)
		self.assertEqual(layout1D[list(negative)].any(),False)

		#radius to big
		layout = numpy.array([1, 1, 1, 1, 1, 1, 0,  1])
		layout1D = layout.reshape(-1)
		columnIndex = 6
		dimensions = numpy.array([8])
		radius = 20
		mask = sp._getNeighbors1D(columnIndex, dimensions, radius)
		negative = set(range(dimensions.prod())) - set(mask)
		self.assertEqual(layout1D[mask].all(), True)
		self.assertEqual(layout1D[list(negative)].any(),False)


	def testGetNeighbors2D(self):
		"""
		Test that _getNeighbors static method correctly computes
		the neighbors of a column and maps them from 2D back to 1D
		"""
		sp = self._sp
		layout = numpy.array([
			[0, 0, 0, 0, 0],
		  [0, 0, 0, 0, 0],
		  [0, 1, 1, 1, 0],
		  [0, 1, 0, 1, 0],
		  [0, 1, 1, 1, 0],
		  [0, 0, 0, 0, 0]])

		layout1D = layout.reshape(-1)
		columnIndex = 3*5+ 2
		dimensions = numpy.array([6, 5])
		radius = 1
		mask = sp._getNeighbors2D(columnIndex, dimensions, radius)
		negative = set(range(dimensions.prod())) - set(mask)
		self.assertEqual(layout1D[mask].all(), True)
		self.assertEqual(layout1D[list(negative)].any(),False)

		layout = numpy.array(
			[[0, 0, 0, 0, 0],
		   [1, 1, 1, 1, 1],
		   [1, 1, 1, 1, 1],
		   [1, 1, 0, 1, 1],
		   [1, 1, 1, 1, 1],
		   [1, 1, 1, 1, 1]])

		layout1D = layout.reshape(-1)
		columnIndex = 3*5+ 2
		dimensions = numpy.array([6, 5])
		radius = 2
		mask = sp._getNeighbors2D(columnIndex, dimensions, radius)
		negative = set(range(dimensions.prod())) - set(mask)
		self.assertEqual(layout1D[mask].all(), True)
		self.assertEqual(layout1D[list(negative)].any(),False)

		# radius to big
		layout = numpy.array(
			[[1, 1, 1, 1, 1],
		   [1, 1, 1, 1, 1],
		   [1, 1, 1, 1, 1],
		   [1, 1, 0, 1, 1],
		   [1, 1, 1, 1, 1],
		   [1, 1, 1, 1, 1]])

		layout1D = layout.reshape(-1)
		columnIndex = 3*5+ 2
		dimensions = numpy.array([6, 5])
		radius = 7
		mask = sp._getNeighbors2D(columnIndex, dimensions, radius)
		negative = set(range(dimensions.prod())) - set(mask)
		self.assertEqual(layout1D[mask].all(), True)
		self.assertEqual(layout1D[list(negative)].any(),False)

		# wrap-around
		layout = numpy.array(
			[[1, 0, 0, 1, 1],
		   [0, 0, 0, 0, 0],
		   [0, 0, 0, 0, 0],
		   [0, 0, 0, 0, 0],
		   [1, 0, 0, 1, 1],
		   [1, 0, 0, 1, 0]])

		layout1D = layout.reshape(-1)
		dimensions = numpy.array([6, 5])
		columnIndex = dimensions.prod() -1 
		radius = 1
		mask = sp._getNeighbors2D(columnIndex, dimensions, radius)
		negative = set(range(dimensions.prod())) - set(mask)
		self.assertEqual(layout1D[mask].all(), True)
		self.assertEqual(layout1D[list(negative)].any(),False)


	def testGetNeighborsND(self):
		sp = self._sp

		dimensions = numpy.array([5, 7, 2])
		layout1D = numpy.array(range(numpy.prod(dimensions)))
		layout = numpy.reshape(layout1D,dimensions)
		radius = 1
		x = 1
		y = 3
		z = 2
		columnIndex = layout[z][y][x]
		neighbors = sp._getNeighborsND(columnIndex, dimensions, radius)
		trueNeighbors = set()
		for i in range(-radius,radius+1):
			for j in range(-radius,radius+1):
				for k in range(-radius,radius+1):
					zprime = (z + i) % dimensions[0]
					yprime = (y + j) % dimensions[1]
					xprime = (x + k) % dimensions[2]
					trueNeighbors.add( \
						layout[zprime][yprime][xprime]
					)
		trueNeighbors.remove(columnIndex)
		self.assertListEqual(sorted(list(trueNeighbors)), \
							 sorted(list(neighbors)))

		dimensions = numpy.array([5, 7, 9])
		layout1D = numpy.array(range(numpy.prod(dimensions)))
		layout = numpy.reshape(layout1D, dimensions)
		radius = 3
		x = 0
		y = 0
		z = 3
		columnIndex = layout[z][y][x]
		neighbors = sp._getNeighborsND(columnIndex, dimensions, radius)
		trueNeighbors = set()
		for i in range(-radius,radius+1):
			for j in range(-radius,radius+1):
				for k in range(-radius,radius+1):
					zprime = (z + i) % dimensions[0]
					yprime = (y + j) % dimensions[1]
					xprime = (x + k) % dimensions[2]
					trueNeighbors.add( \
						layout[zprime][yprime][xprime]
					)
		trueNeighbors.remove(columnIndex)
		self.assertListEqual(sorted(list(trueNeighbors)), \
							 sorted(list(neighbors)))

		dimensions = numpy.array([5, 10, 7, 6])
		layout1D = numpy.array(range(numpy.prod(dimensions)))
		layout = numpy.reshape(layout1D, dimensions)
		radius = 4
		w = 2
		x = 5
		y = 6
		z = 2
		columnIndex = layout[z][y][x][w]
		neighbors = sp._getNeighborsND(columnIndex, dimensions, radius)
		trueNeighbors = set()
		for i in range(-radius,radius+1):
			for j in range(-radius,radius+1):
				for k in range(-radius,radius+1):
					for m in range(-radius,radius+1):
						zprime = (z + i) % dimensions[0]
						yprime = (y + j) % dimensions[1]
						xprime = (x + k) % dimensions[2]
						wprime = (w + m) % dimensions[3]
						trueNeighbors.add( \
							layout[zprime][yprime][xprime][wprime]
						)
		trueNeighbors.remove(columnIndex)
		self.assertListEqual(sorted(list(trueNeighbors)), \
							 sorted(list(neighbors)))

		#these are all the same tests from 1D
		layout = numpy.array([0, 0, 1, 0, 1, 0, 0,  0])
		layout1D = layout.reshape(-1)
		columnIndex = 3
		dimensions = numpy.array([8])
		radius = 1
		mask = sp._getNeighborsND(columnIndex, dimensions, radius)
		negative = set(range(dimensions.prod())) - set(mask)
		self.assertEqual(layout1D[mask].all(), True)
		self.assertEqual(layout1D[list(negative)].any(),False)

		layout = numpy.array([0, 1, 1, 0, 1, 1, 0,  0])
		layout1D = layout.reshape(-1)
		columnIndex = 3
		dimensions = numpy.array([8])
		radius = 2
		mask = sp._getNeighborsND(columnIndex, dimensions, radius)
		negative = set(range(dimensions.prod())) - set(mask)
		self.assertEqual(layout1D[mask].all(), True)
		self.assertEqual(layout1D[list(negative)].any(),False)

		#wrap around
		layout = numpy.array([0, 1, 1, 0, 0, 0, 1,  1])
		layout1D = layout.reshape(-1)
		columnIndex = 0
		dimensions = numpy.array([8])
		radius = 2
		mask = sp._getNeighborsND(columnIndex, dimensions, radius)
		negative = set(range(dimensions.prod())) - set(mask)
		self.assertEqual(layout1D[mask].all(), True)
		self.assertEqual(layout1D[list(negative)].any(),False)

		#radius to big
		layout = numpy.array([1, 1, 1, 1, 1, 1, 0,  1])
		layout1D = layout.reshape(-1)
		columnIndex = 6
		dimensions = numpy.array([8])
		radius = 20
		mask = sp._getNeighborsND(columnIndex, dimensions, radius)
		negative = set(range(dimensions.prod())) - set(mask)
		self.assertEqual(layout1D[mask].all(), True)
		self.assertEqual(layout1D[list(negative)].any(),False)


		#these are all the same tests from 2D
		layout = numpy.array([[0, 0, 0, 0, 0],
		    	  			  [0, 0, 0, 0, 0],
		    	  			  [0, 1, 1, 1, 0],
		    	  			  [0, 1, 0, 1, 0],
		    	  			  [0, 1, 1, 1, 0],
		    	  			  [0, 0, 0, 0, 0]])

		layout1D = layout.reshape(-1)
		columnIndex = 3*5+ 2
		dimensions = numpy.array([6, 5])
		radius = 1
		mask = sp._getNeighborsND(columnIndex, dimensions, radius)
		negative = set(range(dimensions.prod())) - set(mask)
		self.assertEqual(layout1D[mask].all(), True)
		self.assertEqual(layout1D[list(negative)].any(),False)

		layout = numpy.array([[0, 0, 0, 0, 0],
		    	  			  [1, 1, 1, 1, 1],
		    	  			  [1, 1, 1, 1, 1],
		    	  			  [1, 1, 0, 1, 1],
		    	  			  [1, 1, 1, 1, 1],
		    	  			  [1, 1, 1, 1, 1]])

		layout1D = layout.reshape(-1)
		columnIndex = 3*5+ 2
		dimensions = numpy.array([6, 5])
		radius = 2
		mask = sp._getNeighbors2D(columnIndex, dimensions, radius)
		negative = set(range(dimensions.prod())) - set(mask)
		self.assertEqual(layout1D[mask].all(), True)
		self.assertEqual(layout1D[list(negative)].any(),False)

		# radius to big
		layout = numpy.array([[1, 1, 1, 1, 1],
		    	  			  [1, 1, 1, 1, 1],
		    	  			  [1, 1, 1, 1, 1],
		    	  			  [1, 1, 0, 1, 1],
		    	  			  [1, 1, 1, 1, 1],
		    	  			  [1, 1, 1, 1, 1]])

		layout1D = layout.reshape(-1)
		columnIndex = 3*5+ 2
		dimensions = numpy.array([6, 5])
		radius = 7
		mask = sp._getNeighborsND(columnIndex, dimensions, radius)
		negative = set(range(dimensions.prod())) - set(mask)
		self.assertEqual(layout1D[mask].all(), True)
		self.assertEqual(layout1D[list(negative)].any(),False)

		# wrap-around
		layout = numpy.array([[1, 0, 0, 1, 1],
		    	  			  [0, 0, 0, 0, 0],
		    	  			  [0, 0, 0, 0, 0],
		    	  			  [0, 0, 0, 0, 0],
		    	  			  [1, 0, 0, 1, 1],
		    	  			  [1, 0, 0, 1, 0]])

		layout1D = layout.reshape(-1)
		dimensions = numpy.array([6, 5])
		columnIndex = dimensions.prod() -1 
		radius = 1
		mask = sp._getNeighborsND(columnIndex, dimensions, radius)
		negative = set(range(dimensions.prod())) - set(mask)
		self.assertEqual(layout1D[mask].all(), True)
		self.assertEqual(layout1D[list(negative)].any(),False)



if __name__ == "__main__":
  unittest.main()
