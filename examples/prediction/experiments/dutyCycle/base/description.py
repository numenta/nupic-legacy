# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

import os
import random
from nupic.frameworks.prediction.helpers import (updateConfigFromSubConfig, 
                                                 getSubExpDir)
from nupic.encoders import (LogEncoder,
                                                  DateEncoder,
                                                  MultiEncoder, 
                                                  CategoryEncoder, 
                                                  ScalarEncoder,
                                                  SDRCategoryEncoder)
#from nupic.data import TextFileSource
from nupic.data.file_record_stream import FileRecordStream
from nupic.frameworks.prediction.callbacks import (printSPCoincidences,
                                                   displaySPCoincidences,
                                                   setAttribute,
                                                   sensorOpen)
from nupic.regions.RecordSensorFilters.ModifyFields import ModifyFields





# ========================================================================
# Define this experiment's base configuration, and adjust for any modifications
# if imported from a sub-experiment. 
config = dict(
  sensorVerbosity = 0,
  spVerbosity = 0,
  ppVerbosity = 0,

  spPeriodicStats = 500,
  spNumActivePerInhArea = 11,
  spSynPermInactiveDec = 0.005,
  spCoincCount = 300,
  spMinPctDutyCycleAfterInh = 0.001,
  
  tpActivationThresholds = None,

  trainSP = True,
  iterationCount = 50000,
  #iterationCount = 100,

  trainingSet = "trainingData.csv",
  testingSet = "testingData.csv",
  
  # Data set and encoding 
  numAValues = 25,
  numBValues = 25,
  b0Likelihood = 0.90,    # Likelihood of getting 0 out of field B. None means
                          #  not any more likely than any other B value. 
  testSetPct = 0.0,       # What percent of unique combinations to reserve
  
  encodingFieldStyleA = 'sdr',   # contiguous, sdr
  encodingFieldWidthA = 50,
  encodingOnBitsA = 21,

  encodingFieldStyleB = 'sdr',   # contiguous, sdr
  encodingFieldWidthB = 50,     # 15, None means set same as A
  encodingOnBitsB = 23,          # 3, None means set same as A
  )

updateConfigFromSubConfig(config)

if config['encodingFieldWidthB'] is None:
  config['encodingFieldWidthB'] = config['encodingFieldWidthA'] 
if config['encodingOnBitsB'] is None:
  config['encodingOnBitsB'] = config['encodingOnBitsA'] 

if config['tpActivationThresholds'] is None:
  config['tpActivationThresholds'] = range(8, config['spNumActivePerInhArea']+1)


def getBaseDatasets():
  # we generate all of our data
  return dict()

def getDatasets(baseDatasets, generate=False):
  # We're going to put datasets in data/dutyCycle/expname_<file>.csv
  
  expDir = getSubExpDir()
  if expDir is None:
    name = "base"
  else:
    name = os.path.basename(expDir)

  dataDir = "data/dutyCycle"

  trainingFilename = os.path.join(dataDir, name + "_" + config['trainingSet'])
  datasets = dict(trainingFilename=trainingFilename)

  numUnique = config['numAValues'] * config['numBValues']
  testSetSize = int(config['testSetPct'] * numUnique)    
  if testSetSize > 0:
    testingFilename = os.path.join(dataDir, config['testingSet'])
    datasets['testingFilename'] = testingFilename
  else:
    testingFilename = None

  
  if not generate:
    return datasets

  # ========================================================================
  # Create the data files. We create a training set and a testing set. The
  #  testing set contains combinations of A and B that do not appear in the
  #  training set
  #
  
  if not os.path.exists(dataDir):
    os.makedirs(dataDir)

  if (not os.path.exists(trainingFilename)) or \
     (testingFilename is not None and not os.path.exists(testingFilename)):
    print "====================================================================="
    print "Creating data set..."

    # Create the pool of A values
    aValues = range(config['numAValues'])
    # Create the pool of B values, allowing for unequal distribution
    bValues = range(config['numBValues'])

    # Pick a random A and B value
    random.seed(42)
    def generateSample():
      a = random.sample(aValues, 1)[0]
      b = random.sample(bValues, 1)[0]
      return (a, b)

    if config['b0Likelihood'] is not None:
      print "In the B dataset, there is a %d%% chance of getting a B value of 0" \
            % (int(100 * config['b0Likelihood']))
      # likelihood of B0 is: (numB0) / (numB0 + numBvalues)
      # solving for numB0 = numBValues / (1 - likelihood)
      numB0Values = int(round(len(bValues) / (1.0 - config['b0Likelihood'])))
      bValues.extend([0]*numB0Values)   # 90% chance of getting first B value
    else:
      print "All values in B are equally likely"
    print

    # -----------------------------------------------------------------------
    fields = [('fieldA', 'int', ''), ('fieldB', 'int', '')]
    # Generate the test set
    testSet = set()
    if testSetSize > 0:
      # Hold back 10% of the possible combinations for the test set
      while len(testSet) < testSetSize:
        testSet.add(generateSample())
      testList = list(testSet)
      testList.sort()
      print "These (A,B) combinations are reserved for the test set:", testList
      print

      # Write out the test set
      print "Creating test set: %s..." % (testingFilename)
      print "Contains %d unique combinations of A and B chosen from the %d possible" \
              % (testSetSize, numUnique)
      with File(testingFilename, fields=fields) as o:
        numSamples = 0
        while numSamples < config['iterationCount']:
          sample = generateSample()
          if sample in testSet:
            o.write(list(sample))
            #print >>fd, "%d, %d" % (sample[0], sample[1])

            numSamples += 1
      print

    # ------------------------------------------------------------------------
    # Write out the training set
    print "Creating training set: %s..." % (trainingFilename)
    if len(testSet) > 0:
      print "Contains %d samples, chosen from %d of the possible %d combinations " \
            "that are not in the test set" % (config['iterationCount'], 
            numUnique - testSetSize, numUnique)
    else:
      print "Contains %d samples" % (config['iterationCount'])
    print
    with FileRecordStream(trainingFilename, write=True, fields=fields) as o:
      numSamples = 0
      while numSamples < config['iterationCount']:
        sample = generateSample()
        if sample in testSet:
          continue
        #print >>fd, "%d, %d" % (sample[0], sample[1])
        o.appendRecord(list(sample))
        numSamples += 1
 
  return datasets

def getDescription(datasets):

  # ========================================================================
  # Encoder for the sensor
  encoder = MultiEncoder()

  if config['encodingFieldStyleA'] == 'contiguous':
    encoder.addEncoder('fieldA', ScalarEncoder(w=config['encodingOnBitsA'],
                        n=config['encodingFieldWidthA'], minval=0,
                        maxval=config['numAValues'], periodic=True, name='fieldA'))
  elif config['encodingFieldStyleA'] == 'sdr':
    encoder.addEncoder('fieldA', SDRCategoryEncoder(w=config['encodingOnBitsA'],
                        n=config['encodingFieldWidthA'],
                        categoryList=range(config['numAValues']), name='fieldA'))
  else:
    assert False


  if config['encodingFieldStyleB'] == 'contiguous':
    encoder.addEncoder('fieldB', ScalarEncoder(w=config['encodingOnBitsB'], 
                      n=config['encodingFieldWidthB'], minval=0, 
                      maxval=config['numBValues'], periodic=True, name='fieldB'))
  elif config['encodingFieldStyleB'] == 'sdr':
    encoder.addEncoder('fieldB', SDRCategoryEncoder(w=config['encodingOnBitsB'], 
                      n=config['encodingFieldWidthB'], 
                      categoryList=range(config['numBValues']), name='fieldB'))
  else:
    assert False



  # ========================================================================
  # Network definition


  # ------------------------------------------------------------------
  # Node params
  # The inputs are long, horizontal vectors
  inputDimensions = (1, encoder.getWidth())

  # Layout the coincidences vertically stacked on top of each other, each
  # looking at the entire input field. 
  columnDimensions = (config['spCoincCount'], 1)

  sensorParams = dict(
    # encoder/datasource are not parameters so don't include here
    verbosity=config['sensorVerbosity']
  )

  CLAParams = dict(
    inputDimensions = inputDimensions,
    columnDimensions = columnDimensions,
    potentialRadius = inputDimensions[1]/2,
    potentialPct = 1.0,
    gaussianDist = 0,
    commonDistributions = 0,    # should be False if possibly not training
    localAreaDensity = -1, #0.05, 
    numActiveColumnsPerInhArea = config['spNumActivePerInhArea'],
    dutyCyclePeriod = 1000,
    stimulusThreshold = 1,
    synPermInactiveDec = config['spSynPermInactiveDec'],
    synPermActiveInc = 0.02,
    synPermActiveSharedDec=0.0,
    synPermOrphanDec = 0.0,
    minPctDutyCycleBeforeInh = 0.001,
    minPctDutyCycleAfterInh = config['spMinPctDutyCycleAfterInh'],
    minDistance = 0.05,
    computeTopDown = 1,
    spVerbosity = config['spVerbosity'],
    spSeed = 1,
    printPeriodicStats = int(config['spPeriodicStats']),

    # TP params
    disableTemporal = 1,

    # General params
    trainingStep = 'spatial',
    )

  trainingDataSource = FileRecordStream(datasets['trainingFilename'])


  description = dict(
    options = dict(
      logOutputsDuringInference = False,
    ),

    network = dict(
      sensorDataSource = trainingDataSource,
      sensorEncoder = encoder, 
      sensorParams = sensorParams,

      CLAType = 'py.CLARegion',
      CLAParams = CLAParams,

      classifierType = None,
      classifierParams = None),

  )

  if config['trainSP']:
    description['spTrain'] = dict(
      iterationCount=config['iterationCount'], 
      #iter=displaySPCoincidences(50),
      finish=printSPCoincidences()
      ),
  else:
    description['spTrain'] = dict(
      # need to train with one iteration just to initialize data structures
      iterationCount=1)



  # ============================================================================
  # Inference tests
  inferSteps = []

  # ----------------------------------------
  # Training dataset
  if True:
    datasetName = 'bothTraining'
    inferSteps.append(
      dict(name = '%s_baseline' % datasetName, 
           iterationCount = config['iterationCount'],
           setup = [sensorOpen(datasets['trainingFilename'])],
           ppOptions = dict(printLearnedCoincidences=True),
          )
      )

    inferSteps.append(
      dict(name = '%s_acc' % datasetName, 
           iterationCount = config['iterationCount'],
           setup = [sensorOpen(datasets['trainingFilename'])],
           ppOptions = dict(onlyClassificationAcc=True,
                            tpActivationThresholds=config['tpActivationThresholds'],
                            computeDistances=True,
                            verbosity = 1),
          )
      )

  # ----------------------------------------
  # Testing dataset
  if 'testingFilename' in datasets:
    datasetName = 'bothTesting'
    inferSteps.append(
      dict(name = '%s_baseline' % datasetName, 
           iterationCount = config['iterationCount'],
           setup = [sensorOpen(datasets['testingFilename'])],
           ppOptions = dict(printLearnedCoincidences=False),
          )
      )

    inferSteps.append(
      dict(name = '%s_acc' % datasetName, 
           iterationCount = config['iterationCount'],
           setup = [sensorOpen(datasets['testingFilename'])],
           ppOptions = dict(onlyClassificationAcc=True,
                            tpActivationThresholds=config['tpActivationThresholds']),
          )
      )


  description['infer'] = inferSteps

  return description
