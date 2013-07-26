

import unittest2 as unittest
from mock import Mock, patch, ANY, call
from SpatialPooler import SpatialPooler
from nupic.bindings.math import SM32 as SparseMatrix, \
                                SM_01_32_32 as SparseBinaryMatrix, \
                                count_gte, GetNTAReal
import numpy

class SpatialPoolerTest(unittest.TestCase):
	"""Unit Tests for SpatialPooler class"""

	def setUp(self):
		self._sp = SpatialPooler(numInputs = 5,
               numColumns = 5,
               receptiveFieldRadius = 3,
               receptiveFieldPctPotential = 0.5,
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
               verbosityLevel = 0,
			)

	# def test_updateBoostFactors(self):
	# 	self.assertEqual(True,False)


	def test_updateMinDutyCycleLocal(self):
		sp = self._sp

		#replace the get neighbors function with
		#a mock to know exactly the neighbors 
		#of each column
		sp._numColumns = 5
		sp._getNeighbors = Mock(side_effect= \
			[[0,1,2],
			 [1,2,3],
			 [2,3,4],
			 [0,2,4],
			 [0,1,3]])

		sp._minPctOverlapDutyCycles = 0.04
		sp._overlapDutyCycles = numpy.array([1.4, 0.5, 1.2, 0.8, 0.1])
		trueMinOverlapDutyCycles = [0.04*1.4, 0.04*1.2, 0.04*1.2, 0.04*1.4, 0.04*1.4]

		sp._minPctActiveDutyCycles = 0.02
		sp._activeDutyCycles = numpy.array([0.4, 0.5, 0.2, 0.18, 0.1])
		trueMinActiveDutyCycles = [0.02*0.5, 0.02*0.5, 0.02*0.2, 0.02*0.4, 0.02*0.5]

		sp._minOverlapDutyCycles = numpy.zeros(sp._numColumns)
		sp._minActiveDutyCycles = numpy.zeros(sp._numColumns)
		sp._updateMinDutyCyclesLocal()
		self.assertListEqual(trueMinOverlapDutyCycles, \
							list(sp._minOverlapDutyCycles))
		self.assertListEqual(trueMinActiveDutyCycles, \
							list(sp._minActiveDutyCycles))


		sp._numColumns = 8
		sp._getNeighbors = Mock(side_effect= \
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


	def test_updateMinDutyCyclesGlobal(self):
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


	def test_isUpdateRound(self):
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


	def test_calculateAnomalyScore(self):
		sp = self._sp
		overlaps = numpy.array([5, 4, 3, 2, 1])
		activeColumns = numpy.array([0,2,3,4])
		sp._activeDutyCycles = numpy.array([50, 40, 30, 20, 10])
		anomalyScore = sp._calculateAnomalyScore(overlaps,activeColumns)
		trueAnomalyScore = 1.0/(5*50 + 3*30 + 2*20 + 10 + 1)
		self.assertEqual(trueAnomalyScore,anomalyScore)

		overlaps = numpy.array([5, 4, 3, 2, 1])
		activeColumns = numpy.array([0])
		sp._activeDutyCycles = numpy.array([50, 40, 30, 20, 10])
		anomalyScore = sp._calculateAnomalyScore(overlaps,activeColumns)
		trueAnomalyScore = 1.0/(5*50 + 1)
		self.assertEqual(trueAnomalyScore,anomalyScore)

		overlaps = numpy.array([5, 4, 3, 2, 1])
		activeColumns = numpy.array([])
		sp._activeDutyCycles = numpy.array([50, 40, 30, 20, 10])
		anomalyScore = sp._calculateAnomalyScore(overlaps,activeColumns)
		trueAnomalyScore = 1.0
		self.assertEqual(trueAnomalyScore,anomalyScore)

	def test_adaptSynapses(self):
		sp = SpatialPooler(numInputs = 8,
						   numColumns = 4,
               			   synPermInactiveDec=0.01,
               			   synPermActiveInc = 0.1,
               			   synPermActiveSharedDec = 0.02,
               			   synPermOrphanDec = 0.03)

		sp._receptiveFields = \
			SparseBinaryMatrix([[1, 1, 1, 1, 0, 0, 0, 0],
								[1, 0, 0, 0, 1, 1, 0, 1],
								[0, 0, 1, 0, 0, 0, 1, 0],
								[1, 0, 0, 0, 0, 0, 1, 0]])

		inputVector = numpy.array( \
								[1, 0, 0, 1, 1, 0, 1, 0])
		sharedInputs = numpy.where(numpy.array(
								[1, 0, 0, 0, 0, 0, 1, 0]) > 0)[0]
		orphanColumns = numpy.array([])

		sp._permanences = \
			SparseMatrix([[0.200, 0.120, 0.090, 0.040, 0.000, 0.000, 0.000, 0.000],
					 	  [0.150, 0.000, 0.000, 0.000, 0.180, 0.120, 0.000, 0.450],
	    			  	  [0.000, 0.000, 0.014, 0.000, 0.000, 0.000, 0.110, 0.000],
	    			  	  [0.040, 0.000, 0.000, 0.000, 0.000, 0.000, 0.178, 0.000]])

		truePermanences = \
						 [[0.280, 0.110, 0.080, 0.140, 0.000, 0.000, 0.000, 0.000],
						#  Inc/Sh 	Dec	   Dec 	 Inc	 -		-		-		-
					 	  [0.230, 0.000, 0.000, 0.000, 0.280, 0.110, 0.000, 0.440],
					 	#  Inc/Sh 	 -		-	   -	Inc    Dec 	   -      Dec	
	    			  	  [0.000, 0.000, 0.004, 0.000, 0.000, 0.000, 0.190, 0.000],
	    			  	#   -  		- 	  Dec 	  -		 - 		-	  Inc/Sh 	  - 
			   		  	  [0.120, 0.000, 0.000, 0.000, 0.000, 0.000, 0.258, 0.000]]
						#  Inc/Sh 	- 	   -	  -		  -		-	  Inc/Sh   -	

		sp._adaptSynapses(inputVector,sharedInputs,orphanColumns)
		for i in xrange(sp._numColumns):
			perm = list(sp._permanences.getRow(i))
			for j in xrange(sp._numInputs):
				self.assertAlmostEqual(truePermanences[i][j],perm[j])

		# test orphan columns
		sp._receptiveFields = \
			SparseBinaryMatrix([[1, 1, 1, 0, 0, 0, 0, 0],
								[0, 1, 1, 1, 0, 0, 0, 0],
								[0, 0, 1, 1, 1, 0, 0, 0],
								[1, 0, 0, 0, 0, 0, 1, 0]])

		inputVector = numpy.array( \
								[1, 0, 0, 1, 1, 0, 1, 0])
		sharedInputs = numpy.where(numpy.array(
								[1, 0, 0, 1, 0, 0, 0, 0]) > 0)[0]
		orphanColumns = numpy.array([3])

		sp._permanences = \
			SparseMatrix([[0.200, 0.120, 0.090, 0.000, 0.000, 0.000, 0.000, 0.000],
					 	  [0.000, 0.017, 0.232, 0.400, 0.000, 0.000, 0.000, 0.000],
	    			  	  [0.000, 0.000, 0.014, 0.051, 0.730, 0.000, 0.000, 0.000],
	    			  	  [0.170, 0.000, 0.000, 0.000, 0.000, 0.000, 0.380, 0.000]])

		truePermanences = \
						 [[0.280, 0.110, 0.080, 0.000, 0.000, 0.000, 0.000, 0.000],
						#  Inc/Sh  	Dec	   Dec 	  -	     -		-		-		-
					 	  [0.000, 0.007, 0.222, 0.480, 0.000, 0.000, 0.000, 0.000],
					 	#  	 - 	 	Dec	   Dec	Inc/Sh	 -     	- 	   -      -	
	    			  	  [0.000, 0.000, 0.004, 0.131, 0.830, 0.000, 0.000, 0.000],
	    			  	#   -  		- 	   Dec 	Inc/Sh	Inc	 	- 		-	   - 
			   		  	  [0.220, 0.000, 0.000, 0.000, 0.000, 0.000, 0.450, 0.000]]
					#	Inc/Sh/Orph	- 	   -	  -		  -		-	Inc/Orph   -	

		sp._adaptSynapses(inputVector,sharedInputs,orphanColumns)
		for i in xrange(sp._numColumns):
			perm = list(sp._permanences.getRow(i))
			for j in xrange(sp._numInputs):
				self.assertAlmostEqual(truePermanences[i][j],perm[j])


	def test_calculateSharedInputs(self):
		pass

	def test_calculateOrpanColumns(self):
		sp = self._sp
		
		activeColumns = numpy.array([])
		overlapsPct = numpy.array([1, 0.12, 0.15, 0.92, 0.4, 1, 1, 0.88, 1, 0.1])
		orphanColumns = sp._calculateOrphanColumns(activeColumns,overlapsPct)
		trueOrphanColumns = []
		self.assertListEqual(trueOrphanColumns,list(orphanColumns))

		activeColumns = numpy.array(range(10))
		overlapsPct = numpy.array([0.98, 0.12, 0.15, 0.92, 0.4, 0.41, 0.61, 0.88, 0.01, 0.1])
		orphanColumns = sp._calculateOrphanColumns(activeColumns,overlapsPct)
		trueOrphanColumns = []
		self.assertListEqual(trueOrphanColumns,list(orphanColumns))

		activeColumns = numpy.array([5,6,7])
		overlapsPct = numpy.array([1, 0.12, 0.15, 0.92, 0.4, 1, 1, 0.88, 1, 0.1])
		orphanColumns = sp._calculateOrphanColumns(activeColumns,overlapsPct)
		trueOrphanColumns = [5,6]
		self.assertListEqual(trueOrphanColumns,list(orphanColumns))

		activeColumns = numpy.array([1,2,3,6,7])
		overlapsPct = numpy.array([1, 0.12, 1, 0.92, 1, 0.4, 1, 0.88, 1, 0.1])
		orphanColumns = sp._calculateOrphanColumns(activeColumns,overlapsPct)
		trueOrphanColumns = [2,6]
		self.assertListEqual(trueOrphanColumns,list(orphanColumns))

	def test_raisePermanenceThreshold(self):
		sp = SpatialPooler(numInputs = 5, 
						   numColumns=5, 
						   synPermConnected=0.1,
						   stimulusThreshold=3)
		sp._synPermBelowStimulusInc = 0.01
		sp._permanences = \
		SparseMatrix([[0.0, 0.11, 0.095, 0.092, 0.01],
					  [0.12, 0.15, 0.02, 0.12, 0.09],
	    			  [0.51, 0.081, 0.025, 0.089, 0.31],
			   		  [0.18, 0.0601, 0.11, 0.011, 0.03],
			   		  [0.011, 0.011, 0.011, 0.011, 0.011]])
		sp._connectedCounts = numpy.array([1, 3, 2, 2, 0])


		truePermanences = \
					[[0.0, 0.12, 0.105, 0.102, 0.0],		# incremented once
					 [0.12, 0.15, 0.02, 0.12, 0.09],		# no change
	    			 [0.53, 0.101, 0.0, 0.109, 0.33],		# increment twice 
			   		 [0.22, 0.1001, 0.15, 0.051, 0.07],		# increment four times
			   		 [0.101, 0.101, 0.101, 0.101, 0.101]]	#increment 9 times


		trueConnectedSynapses = [[0, 1, 1, 1, 0],
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
			self.assertListEqual(trueConnectedSynapses[i],list(sp._connectedSynapses.getRow(i)))
			self.assertEqual(trueConnectedCounts[i],sp._connectedCounts[i])



	def test_updateConnectedSynapses(self):
		sp = SpatialPooler(numInputs = 5, numColumns=5, synPermConnected=0.1)
		sp._permanences = SparseMatrix([[0.0, 0.5, 0.4, 0.01, 0.02],
										[0.3, 0.01, 0.02, 0.12, 0.09],
										[0.07, 0.05, 0.03, 0.19, 0.06],
										[0.18, 0.09, 0.11, 0.01, 0.03],
										[0.20, 0.1001, 0.05, 0.09, 1]])
		trueConnectedSynapses = [[0, 1, 1, 0, 0],
						  		[1, 0, 0, 1, 0],
								[0, 0, 0, 1, 0],
								[1, 0, 1, 0, 0],
								[1, 1, 0, 0, 1]]
		trueConnectedCounts = [2,2,1,2,3]
		sp._updateConnectedSynapses()
		for i in xrange(sp._numColumns):
			self.assertListEqual(trueConnectedSynapses[i],list(sp._connectedSynapses.getRow(i)))
		self.assertListEqual(trueConnectedCounts, list(sp._connectedCounts))

		

	def test_calculateSharedInputs(self):
		sp = SpatialPooler(numInputs = 8, numColumns=5)
		sp._connectedSynapses = SparseBinaryMatrix([[0, 1, 0, 1, 0, 1, 0, 1],
													[0, 0, 0, 1, 0, 0, 0, 1],
													[0, 0, 0, 0, 0, 0, 1, 0],
													[0, 0, 1, 0, 0, 0, 1, 0],
													[1, 0, 0, 0, 1, 0, 0, 0]])
		inputVector =					numpy.array([1, 1, 1, 1, 0, 0, 0, 0])
		activeColumns = range(5)
		sharedTrue = set([3])
		shared = set(sp._calculateSharedInputs(inputVector, activeColumns))
		self.assertSetEqual(shared, sharedTrue)

		sp._connectedSynapses = SparseBinaryMatrix([[0, 1, 0, 1, 0, 1, 0, 1],
													[0, 0, 0, 1, 0, 0, 0, 1],
													[0, 0, 0, 0, 0, 0, 1, 0],
													[0, 0, 1, 0, 0, 0, 1, 0],
													[1, 0, 0, 0, 1, 0, 0, 0]])
		inputVector =					numpy.array([1, 1, 1, 0, 1, 1, 1, 1])
		activeColumns = range(5)
		sharedTrue = set([6,7])
		shared = set(sp._calculateSharedInputs(inputVector, activeColumns))
		self.assertSetEqual(shared, sharedTrue)

		sp._connectedSynapses = SparseBinaryMatrix([[0, 1, 0, 1, 0, 1, 0, 1],
													[0, 0, 0, 1, 0, 0, 0, 1],
													[0, 0, 0, 0, 0, 0, 1, 0],
													[0, 0, 1, 0, 0, 0, 1, 0],
													[1, 0, 0, 0, 1, 0, 0, 0]])
		inputVector =					numpy.array([0, 0, 0, 0, 0, 0, 0, 0])
		activeColumns = range(5)
		sharedTrue = set([])
		shared = set(sp._calculateSharedInputs(inputVector, activeColumns))
		self.assertSetEqual(shared, sharedTrue)


		sp._connectedSynapses = SparseBinaryMatrix([[0, 1, 0, 1, 0, 1, 0, 1],
													[0, 0, 0, 1, 0, 0, 0, 1],
													[0, 0, 0, 0, 0, 0, 1, 0],
													[0, 0, 1, 0, 0, 0, 1, 0],
													[1, 0, 0, 0, 1, 0, 0, 0]])
		inputVector =					numpy.array([1, 0, 1, 0, 1, 1, 1, 0])
		activeColumns = [1,2,3]
		sharedTrue = set([6])
		shared = set(sp._calculateSharedInputs(inputVector, activeColumns))
		self.assertSetEqual(shared, sharedTrue)
		
		sp._connectedSynapses = SparseBinaryMatrix([[0, 1, 0, 1, 0, 1, 0, 1],
													[0, 0, 0, 1, 0, 0, 0, 1],
													[0, 0, 0, 0, 0, 0, 1, 0],
													[0, 0, 1, 0, 0, 0, 1, 0],
													[1, 0, 0, 0, 1, 0, 0, 0]])
		inputVector =					numpy.array([1, 0, 1, 1, 1, 1, 1, 1])
		activeColumns = [0,1,3,4]
		sharedTrue = set([3,7])
		shared = set(sp._calculateSharedInputs(inputVector, activeColumns))
		self.assertSetEqual(shared, sharedTrue)



	def test_calculateOverlap(self):
		"""
		test that column computes overlap and percent overlap correctly
		"""
		sp = SpatialPooler(numInputs = 10, numColumns=5)
		sp._connectedSynapses = \
			SparseBinaryMatrix([[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
								[0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
								[0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
								[0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
								[0, 0, 0, 0, 0, 0, 0, 0, 1, 1]])
		sp._connectedCounts = numpy.array([10.0, 8.0, 6.0, 4.0, 2.0])
		inputVector = numpy.zeros(sp._numInputs, dtype='float32')
		overlaps, overlapsPct = sp._calculateOverlap(inputVector)
		trueOverlaps = list(numpy.array([0, 0, 0, 0, 0]))
		trueOverlapsPct = list(numpy.array([0, 0, 0, 0, 0]))
		self.assertListEqual(list(overlaps),trueOverlaps)
		self.assertListEqual(list(overlapsPct),trueOverlapsPct)

		sp._connectedSynapses = \
			SparseBinaryMatrix([[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
								[0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
								[0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
								[0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
								[0, 0, 0, 0, 0, 0, 0, 0, 1, 1]])
		sp._connectedCounts = numpy.array([10.0, 8.0, 6.0, 4.0, 2.0])
		inputVector = numpy.ones(sp._numInputs, dtype='float32')
		overlaps, overlapsPct = sp._calculateOverlap(inputVector)
		trueOverlaps = list(numpy.array([10, 8, 6, 4, 2]))
		trueOverlapsPct = list(numpy.array([1, 1, 1, 1, 1]))
		self.assertListEqual(list(overlaps),trueOverlaps)
		self.assertListEqual(list(overlapsPct),trueOverlapsPct)

		sp._connectedSynapses = \
			SparseBinaryMatrix([[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
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
		self.assertListEqual(list(overlaps),trueOverlaps)
		self.assertListEqual(list(overlapsPct),trueOverlapsPct)

		#zig-zag
		sp._connectedSynapses = \
			SparseBinaryMatrix([[1, 0, 0, 0, 0, 1, 0, 0, 0, 0],
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
		self.assertListEqual(list(overlaps),trueOverlaps)
		self.assertListEqual(list(overlapsPct),trueOverlapsPct)


	def test_initPermanence1(self):
		"""
		test initial permanence generation. ensure that
		a correct amount of synapses are initialized in 
		a connected state, with permanence values drawn from
		the correct ranges
		"""

		sp = self._sp
		sp._receptiveFieldRadius = 2
		sp._receptiveFieldPctPotential = 1
		perm = sp._initPermanence(0)
		connected = (perm > sp._synPermConnected).astype(int)
		numcon = (connected.nonzero()[0]).size
		self.assertEqual(numcon, sp._numInputs)
		maxThresh = sp._synPermConnected + sp._synPermActiveInc/4
		self.assertEqual((perm <= maxThresh).all(),True)

		sp._receptiveFieldPctPotential = 0
		perm = sp._initPermanence(0)
		connected = (perm > sp._synPermConnected).astype(int)
		numcon = (connected.nonzero()[0]).size
		self.assertEqual(numcon, 0)

		sp._receptiveFieldPctPotential = 0.5
		sp._receptiveFieldRadius = 100
		sp._numInputs = 100
		perm = sp._initPermanence(0)
		connected = (perm > sp._synPermConnected).astype(int)
		numcon = (connected.nonzero()[0]).size
		self.assertGreater(numcon, 0)
		self.assertLess(numcon,sp._numInputs)

		minThresh = sp._synPermActiveInc / 2.0
		connThresh = sp._synPermConnected
		self.assertEqual(numpy.logical_and((perm >= minThresh),
			(perm <= connThresh)).any(),True)


	def test_initPermanence2(self):
		"""
		test initial permanence generation. ensure that
		permanence values are only assigned to bits within
		a column's receptive field
		"""
		sp = self._sp

		sp._numInputs = 10
		sp._receptiveFieldRadius = 1
		index = 0
		sp._receptiveFieldPctPotential = 1
		#import pdb; pdb.set_trace()
		perm = sp._initPermanence(index)
  		connected = list((perm > 0).astype(int))
		trueConnected = [1,1,0,0,0,0,0,0,0,1]
		self.assertListEqual(connected,trueConnected)

		sp._receptiveFieldRadius = 1
		sp._receptiveFieldPctPotential = 1
		index = 5
		perm = sp._initPermanence(index)
  		connected = list((perm > 0).astype(int))
		trueConnected = [0,0,0,0,1,1,1,0,0,0]
		self.assertListEqual(connected,trueConnected)


		sp._receptiveFieldRadius = 1
		sp._receptiveFieldPctPotential = 1
		index = 9
		perm = sp._initPermanence(index)
  		connected = list((perm > 0).astype(int))
		trueConnected = [1,0,0,0,0,0,0,0,1,1]
		self.assertListEqual(connected,trueConnected)

		sp._receptiveFieldRadius = 4
		sp._receptiveFieldPctPotential = 1
		index = 2
		perm = sp._initPermanence(index)
  		connected = list((perm > 0).astype(int))
		trueConnected = [1,1,1,1,1,1,1,0,1,1]
		self.assertListEqual(connected,trueConnected)

	def test_initPermanence3(self):
		"""
		TODO: implement tests for region-wide permanence initialization
		"""
		pass

	def test_updateDutyCycleHelper(self):
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
		self.assertListEqual(list(newDc),trueNewDc)

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
		self.assertListEqual(list(newDc),trueNewDc)
		

	# def test_compute1(self):
	# 	sp = self._sp
	# 	inputVector = (numpy.random.random(sp._numInputs) > 0.3).astype('float32')
	# 	cols = sp.compute(inputVector,True,True)
	# 	self.assertEqual(cols,5)

	def test_inhibitColumnsGlobal(self):
		"""
		tests that global inhibition correctly picks the 
		correct top number of overlap scores as winning columns
		"""
		sp = self._sp
		numActive = 3
		sp._numColumns = 10
		overlaps = numpy.array([1,2,1,4,8,3,12,5,4,1])
		active = list(sp._inhibitColumnsGlobal(overlaps,numActive))
		trueActive = numpy.zeros(sp._numColumns)
		winnerMask = [4,6,7]
		trueActive[winnerMask] = 1
		self.assertListEqual(list(trueActive), active)

		numActive = 5
		sp._numColumns = 10
		overlaps = numpy.array(range(10))
		active = list(sp._inhibitColumnsGlobal(overlaps,numActive))
		trueActive = numpy.zeros(sp._numColumns)
		winnerMask = range(5,10)
		trueActive[winnerMask] = 1
		self.assertListEqual(list(trueActive), active)


	def test_inhibitColumnsLocal(self):
		sp = self._sp
		numActive = 2
		sp._numColumns = 10
		sp._columnDimensions = numpy.array([sp._numColumns])
		sp._inhibitionRadius = 1
		overlaps = numpy.array([1,2,7,0,3,4,16,1,1.5,1.7])
							#   L W W L W W W  L  W   W
		trueActive = [1,2,4,5,6,8,9]
		active = list(sp._inhibitColumnsLocal(overlaps,numActive))
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
		active = list(sp._inhibitColumnsLocal(overlaps,numActive))
		self.assertListEqual(trueActive, active)


	def test_getNeighbors1D(self):
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
		mask = sp._getNeighbors(columnIndex, dimensions, radius)
		negative = set(range(dimensions.prod())) - set(mask)
		self.assertEqual(layout1D[mask].all(), True)
		self.assertEqual(layout1D[list(negative)].any(),False)

		layout = numpy.array([0, 1, 1, 0, 1, 1, 0,  0])
		layout1D = layout.reshape(-1)
		columnIndex = 3
		dimensions = numpy.array([8])
		radius = 2
		mask = sp._getNeighbors(columnIndex, dimensions, radius)
		negative = set(range(dimensions.prod())) - set(mask)
		self.assertEqual(layout1D[mask].all(), True)
		self.assertEqual(layout1D[list(negative)].any(),False)

		#wrap around
		layout = numpy.array([0, 1, 1, 0, 0, 0, 1,  1])
		layout1D = layout.reshape(-1)
		columnIndex = 0
		dimensions = numpy.array([8])
		radius = 2
		mask = sp._getNeighbors(columnIndex, dimensions, radius)
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
		mask = sp._getNeighbors(columnIndex, dimensions, radius)
		negative = set(range(dimensions.prod())) - set(mask)
		self.assertEqual(layout1D[mask].all(), True)
		self.assertEqual(layout1D[list(negative)].any(),False)

	def test_getNeighbors2D(self):
		"""
		Test that _getNeighbors static method correctly computes
		the neighbors of a column and maps them from 2D back to 1D
		"""
		sp = self._sp
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
		mask = sp._getNeighborsND(columnIndex, dimensions, radius)
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


	def test_getNeighborsND(self):
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
		layout = numpy.reshape(layout1D,dimensions)
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
		layout = numpy.reshape(layout1D,dimensions)
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
		#import pdb; pdb.set_trace()
		self.assertListEqual(sorted(list(trueNeighbors)), \
							 sorted(list(neighbors)))
		



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




if __name__ == '__main__':
  unittest.main()

