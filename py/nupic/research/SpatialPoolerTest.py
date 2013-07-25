
import unittest2 as unittest
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
               maxFiringBoost = 10.0,
               maxSSFiringBoost = 2.0,
               maxSynPermBoost = 10.0,
               seed = -1,
               verbosityLevel = 0,
			)



	# def test_orphan(self):
	# 	c = self._column
	# 	c._active = True
	# 	c._overlapPct = 0.2
	# 	self.assertEqual(c.isOrphan(),False)

	# 	c._active = True
	# 	c._overlapPct = 1
	# 	self.assertEqual(c.isOrphan(),False)

	# 	c._active = False
	# 	c._overlapPct = 0.2
	# 	self.assertEqual(c.isOrphan(),False)

	# 	c._active = False
	# 	c._overlapPct = 1
	# 	self.assertEqual(c.isOrphan(),True)

	def test_updateConnectedSynapses(self):
		pass

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
		sp._calculateOverlap(inputVector)
		trueOverlaps = list(numpy.array([0, 0, 0, 0, 0]))
		trueOverlapsPct = list(numpy.array([0, 0, 0, 0, 0]))
		overlaps = list(sp._overlaps)
		overlapsPct = list(sp._overlapsPct)
		self.assertListEqual(overlaps,trueOverlaps)
		self.assertListEqual(overlapsPct,trueOverlapsPct)

		sp._connectedSynapses = \
			SparseBinaryMatrix([[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
								[0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
								[0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
								[0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
								[0, 0, 0, 0, 0, 0, 0, 0, 1, 1]])
		sp._connectedCounts = numpy.array([10.0, 8.0, 6.0, 4.0, 2.0])
		inputVector = numpy.ones(sp._numInputs, dtype='float32')
		sp._calculateOverlap(inputVector)
		trueOverlaps = list(numpy.array([10, 8, 6, 4, 2]))
		trueOverlapsPct = list(numpy.array([1, 1, 1, 1, 1]))
		overlaps = list(sp._overlaps)
		overlapsPct = list(sp._overlapsPct)
		self.assertListEqual(overlaps,trueOverlaps)
		self.assertListEqual(overlapsPct,trueOverlapsPct)

		sp._connectedSynapses = \
			SparseBinaryMatrix([[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
								[0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
								[0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
								[0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
								[0, 0, 0, 0, 0, 0, 0, 0, 1, 1]])
		sp._connectedCounts = numpy.array([10.0, 8.0, 6.0, 4.0, 2.0])
		inputVector = numpy.zeros(sp._numInputs, dtype='float32')
		inputVector[9] = 1
		sp._calculateOverlap(inputVector)
		trueOverlaps = list(numpy.array([1, 1, 1, 1, 1]))
		trueOverlapsPct = list(numpy.array([0.1, 0.125, 1.0/6, 0.25, 0.5]))
		overlaps = list(sp._overlaps)
		overlapsPct = list(sp._overlapsPct)
		self.assertListEqual(overlaps,trueOverlaps)
		self.assertListEqual(overlapsPct,trueOverlapsPct)

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
		sp._calculateOverlap(inputVector)
		trueOverlaps = list(numpy.array([1, 1, 1, 1, 1]))
		trueOverlapsPct = list(numpy.array([0.5, 0.5, 0.5, 0.5, 0.5]))
		overlaps = list(sp._overlaps)
		overlapsPct = list(sp._overlapsPct)
		self.assertListEqual(overlaps,trueOverlaps)
		self.assertListEqual(overlapsPct,trueOverlapsPct)


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

	def test_dutyCycle1(self):
		"""
		tests that duty cycles are updated properly according
		to the mathematical formula. also check the effects of
		supplying a maxPeriod to the function.
		"""
		dc = numpy.zeros(5)
		dc = numpy.array([1000.0, 1000.0, 1000.0, 1000.0, 1000.0])
		period = 1000
		newvals = numpy.zeros(5)
		newDc = SpatialPooler._updateDutyCycle(dc, newvals, period)
		trueNewDc = [999, 999, 999, 999, 999]
		self.assertListEqual(list(newDc),trueNewDc)

		dc = numpy.array([1000.0, 1000.0, 1000.0, 1000.0, 1000.0])
		period = 1000
		newvals = numpy.zeros(5)
		newvals.fill(1000)
		newDc = SpatialPooler._updateDutyCycle(dc, newvals, period)
		trueNewDc = list(dc)
		self.assertListEqual(list(newDc),trueNewDc)

		dc = numpy.array([1000, 1000, 1000, 1000, 1000])
		newvals = numpy.array([2000, 4000, 5000, 6000, 7000])
		period = 1000
		newDc = SpatialPooler._updateDutyCycle(dc, newvals, period)
		trueNewDc = [1001, 1003, 1004, 1005, 1006]
		self.assertListEqual(list(newDc),trueNewDc)

		dc = numpy.array([1000, 800, 600, 400, 2000])
		newvals = numpy.zeros(5)
		period = 2
		newDc = SpatialPooler._updateDutyCycle(dc, newvals, period)
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
		active = sp._inhibitColumnsGlobal(overlaps,numActive)
		winnerMask = set([4,6,7])
		loserMask = set(range(sp._numColumns)) - winnerMask
		self.assertEqual(active[list(winnerMask)].all(), True)
		self.assertEqual(active[list(loserMask)].any(), False)

		numActive = 5
		sp._numColumns = 10
		overlaps = numpy.array(range(10))
		active = sp._inhibitColumnsGlobal(overlaps,numActive)
		winnerMask = set(range(5,10))
		loserMask = set(range(sp._numColumns)) - winnerMask
		self.assertEqual(active[list(winnerMask)].all(), True)
		self.assertEqual(active[list(loserMask)].any(), False)


	def test_inhibitColumnsLocal(self):
		sp = self._sp
		numActive = 2
		sp._numColumns = 10
		sp._columnDimensions = [sp._numColumns]
		sp._inhibitionRadius = 1
		overlaps = numpy.array([1,2,7,0,3,4,16,1,1.5,1.7])
							#   L W W L W W W  L  W   W
		active = sp._inhibitColumnsLocal(overlaps,numActive)
		loserMask = set([0,3,7])
		winnerMask = set(range(sp._numColumns)) - loserMask
		self.assertEqual(active[list(winnerMask)].all(), True)
		self.assertEqual(active[list(loserMask)].any(), False)


		numActive = 2
		sp._numColumns = 10
		sp._columnDimensions = [sp._numColumns]
		sp._inhibitionRadius = 2
		overlaps = numpy.array([1,2,7,0,3,4,16,1,1.5,1.7])
							#   L W W L L W W  L  L   W
		active = sp._inhibitColumnsLocal(overlaps,numActive)
		winnerMask = set([1,2,5,6,9])
		loserMask = set(range(sp._numColumns)) - winnerMask
		self.assertEqual(active[list(winnerMask)].all(), True)
		self.assertEqual(active[list(loserMask)].any(), False)

		# test add to winners
		numActive = 2
		sp._numColumns = 10
		sp._columnDimensions = [sp._numColumns]
		sp._inhibitionRadius = 3
		overlaps = numpy.array([1,1,1,1,1,1,1,1,1,1])
							#   W W L L W W L L L L
		active = sp._inhibitColumnsLocal(overlaps,numActive)
		winnerMask = set([0,1,4,5])
		loserMask = set(range(sp._numColumns)) - winnerMask
		self.assertEqual(active[list(winnerMask)].all(), True)
		self.assertEqual(active[list(loserMask)].any(), False)


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
		mask = sp._getNeighbors2D(columnIndex, dimensions, radius)
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
		mask = sp._getNeighbors2D(columnIndex, dimensions, radius)
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
		mask = sp._getNeighbors2D(columnIndex, dimensions, radius)
		negative = set(range(dimensions.prod())) - set(mask)
		self.assertEqual(layout1D[mask].all(), True)
		self.assertEqual(layout1D[list(negative)].any(),False)


if __name__ == '__main__':
  unittest.main()

