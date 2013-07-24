
import unittest2 as unittest
from SpatialPooler import SpatialPooler, Column, ColumnParams
from nupic.bindings.math import SM32 as SparseMatrix, \
                                SM_01_32_32 as SparseBinaryMatrix, \
                                count_gte, GetNTAReal
import numpy

class SpatialPoolerTest(unittest.TestCase):
	"""Unit Tests for SpatialPooler class"""

	def setUp(self):
		print "set up called"
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

		self._columnParams = ColumnParams(
               stimulusThreshold = 1,
               synPermInactiveDec = 0.01,
               synPermActiveInc = 0.1,
               synPermActiveSharedDec = 0.04,
               synPermOrphanDec = 0.05,
               synPermConnected = 0.10,
               minPctDutyCycleBeforeInh = 0.001,
               minPctDutyCycleAfterInh = 0.001,
               dutyCyclePeriod = 1000,
               maxFiringBoost = 10.0,
               maxSSFiringBoost = 2.0,
               maxSynPermBoost = 10.0,
            )

		self._column = Column(
				numInputs = 5,
            	columnParams = self._columnParams,
            	initialPermanence = [ 0.095, 0.015,0.1,0.95,0.95],
            	receptiveField = range(5)
			)

	def test_computeOverlap(self):
		"""
		test that column computes overlap and percent overlap correctly
		"""
		c = self._column
		c._numInputs = 10
		c._connectedSynapses = SparseBinaryMatrix([numpy.ones(c._numInputs)])
		inputVector = numpy.zeros(c._numInputs, dtype='float32')
		overlap, overlapPct = c.computeOverlap(inputVector)
		self.assertEqual(overlap,0)
		self.assertEqual(overlapPct,0)

		inputVector = numpy.ones(c._numInputs, dtype='float32')
		overlap, overlapPct = c.computeOverlap(inputVector)
		self.assertEqual(overlap,10)
		self.assertEqual(overlapPct,1)

		inputVector = numpy.zeros(c._numInputs, dtype='float32')
		inputVector[0] = 1
		overlap, overlapPct = c.computeOverlap(inputVector)
		self.assertEqual(overlap,1)
		self.assertAlmostEqual(overlapPct,0.1)

		#zig-zag
		connectedSynapses = numpy.zeros(10)
		connectedSynapses[range(0,10,2)] = 1
		c._connectedSynapses = SparseBinaryMatrix([connectedSynapses])
		inputVector = numpy.zeros(10, dtype='float32')
		inputVector[range(1,10,2)] = 1
		overlap, overlapPct = c.computeOverlap(inputVector)
		self.assertEqual(overlap,0)
		self.assertEqual(overlapPct,0)

		connectedSynapses = numpy.zeros(10)
		connectedSynapses[range(0,7)] = 1
		c._connectedSynapses = SparseBinaryMatrix([connectedSynapses])
		inputVector = numpy.zeros(10, dtype='float32')
		inputVector[range(5,7)] = 1
		overlap, overlapPct = c.computeOverlap(inputVector)
		self.assertEqual(overlap,2)
		self.assertAlmostEqual(overlapPct,2.0/7.0)



	def test_initPermanence1(self):
		"""
		test initial permanence generation. ensure that
		a correct amount of synapses are initialized in 
		a connected state, with permanence values drawn from
		the correct ranges
		"""

		sp = self._sp
		cp = sp._columnParams
		sp._receptiveFieldRadius = 2
		sp._receptiveFieldPctPotential = 1
		perm = sp._initPermanence(0)
		connected = (perm > cp.synPermConnected).astype(int)
		numcon = (connected.nonzero()[0]).size
		self.assertEqual(numcon, sp._numInputs)
		maxThresh = cp.synPermConnected + cp.synPermActiveInc/4
		self.assertEqual((perm <= maxThresh).all(),True)

		sp._receptiveFieldPctPotential = 0
		perm = sp._initPermanence(0)
		connected = (perm > cp.synPermConnected).astype(int)
		numcon = (connected.nonzero()[0]).size
		self.assertEqual(numcon, 0)

		sp._receptiveFieldPctPotential = 0.5
		sp._receptiveFieldRadius = 100
		sp._numInputs = 100
		perm = sp._initPermanence(0)
		connected = (perm > cp.synPermConnected).astype(int)
		numcon = (connected.nonzero()[0]).size
		self.assertGreater(numcon, 0)
		self.assertLess(numcon,sp._numInputs)

		minThresh = cp.synPermActiveInc / 2.0
		connThresh = cp.synPermConnected
		self.assertEqual(numpy.logical_and((perm >= minThresh),
			(perm <= connThresh)).any(),True)


	def test_initPermanence2(self):
		"""
		test initial permanence generation. ensure that
		permanence values are only assigned to bits within
		a column's receptive field
		"""
		sp = self._sp
		cp = sp._columnParams

		sp._numInputs = 10
		sp._receptiveFieldRadius = 1
		index = 0
		sp._receptiveFieldPctPotential = 1
		perm = sp._initPermanence(index)
  		permNonZero = (perm > 0).astype(int)
		allInputs = set(range(sp._numInputs))
		connMask = set([0,1,9])
		unconnMask = allInputs - connMask
		self.assertEqual((perm[list(connMask)]).all() ,True)
		self.assertEqual((perm[list(unconnMask)]).any(), False)

		sp._receptiveFieldRadius = 1
		sp._receptiveFieldPctPotential = 1
		index = 5
		perm = sp._initPermanence(index)
  		permNonZero = (perm > 0).astype(int)
		allInputs = set(range(sp._numInputs))
		connMask = set([4,5,6])
		unconnMask = allInputs - connMask
		self.assertEqual((perm[list(connMask)]).all() ,True)
		self.assertEqual((perm[list(unconnMask)]).any(), False)


		sp._receptiveFieldRadius = 1
		sp._receptiveFieldPctPotential = 1
		index = 9
		perm = sp._initPermanence(index)
  		permNonZero = (perm > 0).astype(int)
		allInputs = set(range(sp._numInputs))
		connMask = set([0,8,9])
		unconnMask = allInputs - connMask
		self.assertEqual((perm[list(connMask)]).all() ,True)
		self.assertEqual((perm[list(unconnMask)]).any(), False)

		sp._receptiveFieldRadius = 4
		sp._receptiveFieldPctPotential = 1
		index = 2
		perm = sp._initPermanence(index)
  		permNonZero = (perm > 0).astype(int)
		allInputs = set(range(sp._numInputs))
		connMask = allInputs - set([7])
		unconnMask = allInputs - connMask
		self.assertEqual((perm[list(connMask)]).all() ,True)
		self.assertEqual((perm[list(unconnMask)]).any(), False)

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
		dc = 1000.0
		period = 1000
		maxperiod = -1
		newval = 0
		dc = Column._updateDutyCycle(dc, newval, period, maxperiod)
		self.assertEqual(dc,999)

		dc = 1000.0
		period = 1000
		maxperiod = -1
		newval = 1000
		dc = Column._updateDutyCycle(dc, newval, period, maxperiod)
		self.assertEqual(dc,1000)

		dc = 1000.0
		period = 1000
		maxperiod = -1
		newval = 2000
		dc = Column._updateDutyCycle(dc, newval, period, maxperiod)
		self.assertEqual(dc,1001)

		#test effeects of max period
		dc = 1000.0
		period = 1000
		maxperiod = 2
		newval = 500
		dc = Column._updateDutyCycle(dc, newval, period, maxperiod)
		self.assertEqual(dc,750)

		dc = 1000.0
		period = 1000
		maxperiod = 10
		newval = 500
		dc = Column._updateDutyCycle(dc, newval, period, maxperiod)
		self.assertEqual(dc,950)				

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

