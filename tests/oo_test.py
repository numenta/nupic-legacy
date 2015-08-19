import numpy
import random
import time

from nupic.network.region import Region
from nupic.research.spatial_pooler import SpatialPooler as SpatialPooler1
from nupic.research_oo.spatial_pooler import SpatialPooler as SpatialPooler2
from nupic.research.temporal_memory import TemporalMemory as TemporalMemory1
from nupic.research_oo.temporal_memory import TemporalMemory as TemporalMemory2

uintType = "int"
seed = int((time.time()%10000)*10)



def testSP(implDescription, implClass, implParams, inputMatrix):

  startTime = time.time()

  print implDescription, ":"

  sp = implClass(**implParams)

  elapsedTime = time.time() - startTime
  print "  Initialization: ", elapsedTime

  output = numpy.zeros(columnDimensions, dtype = uintType)
  dutyCycles = numpy.zeros(columnDimensions, dtype = uintType)

  startTime = time.time()

  # With learning on we should get the requested number of winners
  for input in inputMatrix:
    output.fill(0)
    sp.compute(input, True, output)

  elapsedTime = time.time() - startTime
  print "  Compute with Learning: ", elapsedTime

  startTime = time.time()

  # With learning off and some prior training we should get the requested
  # number of winners
  for input in inputMatrix:
    output.fill(0)
    sp.compute(input, False, output)

  elapsedTime = time.time() - startTime
  print "  Compute without Learning: ", elapsedTime


def testTM(implDescription, implClass, implParams, inputMatrix):

  startTime = time.time()

  print implDescription, ":"

  tm = implClass(**implParams)

  elapsedTime = time.time() - startTime
  print "  Initialization: ", elapsedTime

  startTime = time.time()

  # With learning on we should get the requested number of winners
  for input in inputMatrix:
    tm.compute(input, True)

  elapsedTime = time.time() - startTime
  print "  Compute with Learning: ", elapsedTime

  startTime = time.time()

  # With learning off and some prior training we should get the requested
  # number of winners
  for input in inputMatrix:
    tm.compute(input, False)

  elapsedTime = time.time() - startTime
  print "  Compute without Learning: ", elapsedTime



if __name__ == '__main__':
  
  # Create a set of input vectors as well as various numpy vectors we will
  # need to retrieve data from the SP
  numRecords = 1000
  
  columnDimensions = 256
  numCellsPerColumn = 4

  startTime = time.time()
  
  region = Region(columnDimensions=[columnDimensions], numCellsPerColumn=numCellsPerColumn)

  elapsedTime = time.time() - startTime
  print "Region Initialization: ", elapsedTime

  inputSize = 30
  numpy.random.seed()
  inputMatrix = (numpy.random.rand(numRecords,inputSize) > 0.8).astype(uintType)
  
  sp1Params = {'inputDimensions': (inputSize),
               'columnDimensions': (columnDimensions),
               'potentialRadius': inputSize,
               'globalInhibition': True,
               'seed': seed}
  testSP("SP original", SpatialPooler1, sp1Params, inputMatrix)

  sp2Params = {'region': region,
               'inputDimensions': (inputSize),
               'potentialRadius': inputSize,
               'globalInhibition': True,
               'seed': seed}
  testSP("SP with OO", SpatialPooler2, sp2Params, inputMatrix)

  numpy.random.seed()
  inputMatrix = (numpy.random.rand(numRecords,columnDimensions) > 0.8).astype(uintType)
  inputList = []
  for input in inputMatrix:
    inputList.append(numpy.nonzero(input))

  inputList1 = []
  for input in inputList:
    columns = set()
    for columnIdx in input[0]:
      columns.add(columnIdx)
    inputList1.append(set(columns))
  tm1Params = {'columnDimensions': (columnDimensions,),
               'cellsPerColumn': numCellsPerColumn,
               'activationThreshold': 7,
               'initialPermanence': 0.37,
               'connectedPermanence': 0.58,
               'minThreshold': 4,
               'maxNewSynapseCount': 18,
               'permanenceIncrement': 0.23,
               'permanenceDecrement': 0.08,
               'seed': seed}
  testTM("TM original", TemporalMemory1, tm1Params, inputList1)
  
  inputList2 = []
  for input in inputList:
    columns = set()
    for columnIdx in input[0]:
      columns.add(region.columns[columnIdx])
    inputList2.append(columns)
  tm2Params = {'region': region,
               'activationThreshold': 7,
               'initialPermanence': 0.37,
               'connectedPermanence': 0.58,
               'minThreshold': 4,
               'maxNewSynapseCount': 18,
               'permanenceIncrement': 0.23,
               'permanenceDecrement': 0.08,
               'seed': seed}
  testTM("TM with OO", TemporalMemory2, tm2Params, inputList2)
