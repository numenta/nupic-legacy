# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""

Generate artificial datasets

"""

import numpy
from nupic.data.file import File



def scaleData(data, newScale=[0,100]):
  
  minVals = data.min(axis=0)
  maxVals = data.max(axis=0)
  
  data = (data-minVals)*(newScale[1]-newScale[0])/(maxVals-minVals) + newScale[0]
 
  return data 



def generatePolyData(numDataPoints=100,
                     coefficients=[1, 0],
                     noiseLevel = 0.1,
                     dataScale = [0,100],):
  
  xvals = numpy.random.random(numDataPoints)
  yvals = numpy.polyval(coefficients, xvals) + \
                                  noiseLevel * numpy.random.randn(numDataPoints)
  
  data = numpy.vstack((yvals, xvals)).transpose()
  scaledData = scaleData(data, newScale=dataScale)

  return scaledData



def generateLinearData(numDataPoints=100,
                       coefficients=[1, 1],
                       noiseLevel = 0.1,
                       dataScale = [0,100],):
 
  xvals = numpy.random.random((numDataPoints, len(coefficients)))
  yvals = (xvals * coefficients).sum(axis=1) + \
                                  noiseLevel * numpy.random.randn(numDataPoints)
  
  data = numpy.hstack((yvals.reshape(-1,1), xvals))
  scaledData = scaleData(data, newScale=dataScale)

  return scaledData



def _generateLinearModel(numTrainingRecords, numTestingRecords,
                          coefficients=[1], noiseLevel=0.1, dataScale=[0,100]):
  """ 
  """ 
  
  data = generateLinearData(numDataPoints=numTrainingRecords+numTestingRecords,
                            coefficients=coefficients,
                            noiseLevel=noiseLevel,
                            dataScale=dataScale,)
  
  trainData = data[:numTrainingRecords]
  testData  = data[numTrainingRecords:]
  
  return trainData, testData



def _generateFile(filename, data):
  """ 
  Parameters:
  ----------------------------------------------------------------
  filename:         name of .csv file to generate
                   
  """
  
  # Create the file
  print "Creating %s..." % (filename)
  numRecords, numFields = data.shape
  
  fields = [('field%d'%(i+1), 'float', '') for i in range(numFields)]
  outFile = File(filename, fields)
  
  for i in xrange(numRecords):
    outFile.write(data[i].tolist())
    
  outFile.close()



def generate(model, filenameTrain, filenameTest,
             numTrainingRecords=10000, numTestingRecords=1000,):
  """
  """
  numpy.random.seed(41)
  
  # ====================================================================
  # Generate the model
  if model == 'linear0':
    trainData, testData = _generateLinearModel(numTrainingRecords,
                                                numTestingRecords,
                                                coefficients=[1],
                                                noiseLevel=0.1)
    #import pylab
    #pylab.figure()
    #pylab.plot(trainData[:,1], trainData[:,0], 'b.')
    ##pylab.figure()
    #pylab.plot(testData[:,1], testData[:,0],'g.')
    #pylab.show()
  elif model == 'linear1':
    trainData, testData = _generateLinearModel(numTrainingRecords,
                                                numTestingRecords,
                                                coefficients=[1,1],
                                                noiseLevel=0.1)  
  elif model == 'linear2':
    trainData, testData = _generateLinearModel(numTrainingRecords,
                                                numTestingRecords,
                                                coefficients=[1,-3])  
  else:
    raise RuntimeError("Unsupported model")
  
  # ====================================================================
  # Generate the training and testing files
  _generateFile(filename=filenameTrain, data=trainData,)
                  
  _generateFile(filename=filenameTest, data=testData,)
                  
                  
  
