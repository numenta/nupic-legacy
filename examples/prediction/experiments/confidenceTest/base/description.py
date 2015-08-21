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
import imp

from nupic.encoders import (LogEncoder,
                          DateEncoder,
                          MultiEncoder, 
                          CategoryEncoder,
                          SDRCategoryEncoder, 
                          ScalarEncoder)

from nupic.data.file_record_stream import FileRecordStream
from nupic.frameworks.prediction.callbacks import (printSPCoincidences,
                                                   printTPCells,
                                                   printTPTiming,
                                                   displaySPCoincidences,
                                                   setAttribute,
                                                   sensorRewind,
                                                   sensorOpen)

from nupic.frameworks.prediction.helpers import updateConfigFromSubConfig


# ----------------------------------------------------------------------
# Define this experiment's base configuration, and adjust for any modifications
# if imported from a sub-experiment. 
config = dict(
  sensorVerbosity = 0,
  spVerbosity = 0,
  tpVerbosity = 0,
  ppVerbosity = 0,
  
  dataSetPackage = None,  # This can be specified in place of the next 6:
  
  filenameTrain = 'confidence/confidence1.csv',
  filenameTest = 'confidence/confidence1.csv',
  filenameCategory = None,
  dataGenScript = None,
  dataDesc = None,
  dataGenNumCategories = None,
  dataGenNumTraining = None,
  dataGenNumTesting = None,
  
  noiseAmts = [],

  iterationCountTrain = None,
  iterationCountTest = None,
  evalTrainingSetNumIterations = 10000, # Set to 0 to disable completely
  trainSP = True,
  trainTP = True,
  trainTPRepeats = 1,

  computeTopDown = 1,

  # Encoder
  overlappingPatterns = 0,
  
  # SP params
  disableSpatial = 1,
  spPrintPeriodicStats = 0,   # An integer N: print stats every N iterations
  spCoincCount = 200,
  spNumActivePerInhArea = 3,

  # TP params
  tpNCellsPerCol = 20,
  tpInitialPerm = 0.6,
  tpPermanenceInc = 0.1,
  tpPermanenceDec = 0.000,
  tpGlobalDecay = 0.0,
  tpPAMLength = 1,
  tpMaxSeqLength = 0,
  tpMaxAge = 1,
  tpTimingEvery = 0,
  temporalImp = 'cpp',
  )

updateConfigFromSubConfig(config)

# ==========================================================================
# Was a complete dataset package specified? This is an alternate way to
#   specify a bunch of dataset related config parameters at once. They are
#  especially helpful when running permutations - it keeps the permutations
#  directory names shorter.
if config['dataSetPackage'] is not None:
  assert (config['filenameTrain'] == 'confidence/confidence1.csv')
  assert (config['filenameTest'] == 'confidence/confidence1.csv')
  assert (config['filenameCategory'] == None)
  assert (config['dataGenScript'] == None)
  assert (config['dataDesc'] == None)
  assert (config['dataGenNumCategories'] == None)
  assert (config['dataGenNumTraining'] == None)
  assert (config['dataGenNumTesting'] == None)
  
  if config['dataSetPackage'] == 'firstOrder':
    config['filenameTrain'] = 'extra/firstOrder/fo_1000_10_train_resets.csv'
    config['filenameTest'] = 'extra/firstOrder/fo_10000_10_test_resets.csv'
    config['filenameCategory'] = 'extra/firstOrder/categories.txt'
    
  elif config['dataSetPackage'] == 'secondOrder0':
    config['filenameTrain'] = None
    config['filenameTest'] = None
    config['filenameCategory'] = None
    config['dataGenScript'] = 'extra/secondOrder/makeDataset.py'
    config['dataDesc'] = 'model0'
    config['dataGenNumCategories'] = 20
    config['dataGenNumTraining'] = 5000
    config['dataGenNumTesting'] = 1000
    
  elif config['dataSetPackage'] == 'secondOrder1':
    config['filenameTrain'] = None
    config['filenameTest'] = None
    config['filenameCategory'] = None
    config['dataGenScript'] = 'extra/secondOrder/makeDataset.py'
    config['dataDesc'] = 'model1'
    config['dataGenNumCategories'] = 25
    config['dataGenNumTraining'] = 5000
    config['dataGenNumTesting'] = 1000
    
  elif config['dataSetPackage'] == 'secondOrder2':
    config['filenameTrain'] = None
    config['filenameTest'] = None
    config['filenameCategory'] = None
    config['dataGenScript'] = 'extra/secondOrder/makeDataset.py'
    config['dataDesc'] = 'model2'
    config['dataGenNumCategories'] = 5
    config['dataGenNumTraining'] = 5000
    config['dataGenNumTesting'] = 1000
    
  else:
    assert False



def getBaseDatasets():
  datasets = dict()
  for name in ['filenameTrain', 'filenameTest', 'filenameCategory',
                 'dataGenScript']:
    if config[name] is not None:
      datasets[name] = config[name]
  return datasets



def getDatasets(baseDatasets, generate=False):
  # nothing to generate if no script
  if not 'dataGenScript' in baseDatasets:
    return baseDatasets

  # -------------------------------------------------------------------
  # Form the path to each dataset
  datasets = dict(baseDatasets)
  dataPath = os.path.dirname(baseDatasets['dataGenScript'])

  # At some point, this prefix will be modified to be unique for each 
  #   possible variation of parameters into the data generation script. 
  prefix = '%s' % (config['dataDesc'])
  datasets['filenameTrain'] = os.path.join(dataPath, 
                                           '%s_train.csv' % prefix)
  datasets['filenameTest'] = os.path.join(dataPath, 
                                           '%s_test.csv' % prefix)
  datasets['filenameCategory'] = os.path.join(dataPath, 
                                            '%s_categories.txt' % prefix)
  
  if not generate:
    return datasets

  # -------------------------------------------------------------------
  # Generate our data
  makeDataset = imp.load_source('makeDataset', baseDatasets['dataGenScript'])
  makeDataset.generate(model = config['dataDesc'], 
                       filenameTrain = datasets['filenameTrain'], 
                       filenameTest = datasets['filenameTest'],
                       filenameCategory = datasets['filenameCategory'],
                       numCategories=config['dataGenNumCategories'], 
                       numTrainingRecords=config['dataGenNumTraining'],
                       numTestingRecords=config['dataGenNumTesting'], 
                       numNoise=0, resetsEvery=None)

  return datasets
  


def getDescription(datasets):

  # ========================================================================
  # Network definition

  # Encoder for the sensor
  encoder = MultiEncoder()  
  if 'filenameCategory' in datasets:
    categories = [x.strip() for x in 
                              open(datasets['filenameCategory']).xreadlines()]
  else:
    categories = [chr(x+ord('a')) for x in range(26)]

  if config['overlappingPatterns']:
    encoder.addEncoder("name", SDRCategoryEncoder(n=200, 
      w=config['spNumActivePerInhArea'], categoryList=categories, name="name"))
  else:
    encoder.addEncoder("name", CategoryEncoder(w=config['spNumActivePerInhArea'], 
                        categoryList=categories, name="name"))


  # ------------------------------------------------------------------
  # Node params
  # The inputs are long, horizontal vectors
  inputDimensions = (1, encoder.getWidth())

  # Layout the coincidences vertically stacked on top of each other, each
  # looking at the entire input field. 
  columnDimensions = (config['spCoincCount'], 1)

  # If we have disableSpatial, then set the number of "coincidences" to be the
  #  same as the encoder width
  if config['disableSpatial']:
    columnDimensions = (encoder.getWidth(), 1)
    config['trainSP'] = 0

  sensorParams = dict(
    # encoder/datasource are not parameters so don't include here
    verbosity=config['sensorVerbosity']
  )

  CLAParams = dict(
    # SP params
    disableSpatial = config['disableSpatial'],
    inputDimensions = inputDimensions,
    columnDimensions = columnDimensions,
    potentialRadius = inputDimensions[1]/2,
    potentialPct = 1.00,
    gaussianDist = 0,
    commonDistributions = 0,    # should be False if possibly not training
    localAreaDensity = -1, #0.05, 
    numActiveColumnsPerInhArea = config['spNumActivePerInhArea'], 
    dutyCyclePeriod = 1000,
    stimulusThreshold = 1,
    synPermInactiveDec=0.11,
    synPermActiveInc=0.11,
    synPermActiveSharedDec=0.0,
    synPermOrphanDec = 0.0,
    minPctDutyCycleBeforeInh = 0.001,
    minPctDutyCycleAfterInh = 0.001,
    spVerbosity = config['spVerbosity'],
    spSeed = 1,
    printPeriodicStats = int(config['spPrintPeriodicStats']),


    # TP params
    tpSeed = 1,
    disableTemporal = 0 if config['trainTP'] else 1,
    temporalImp = config['temporalImp'],
    nCellsPerCol = config['tpNCellsPerCol'] if config['trainTP'] else 1,

    collectStats = 1,
    burnIn = 2,
    verbosity = config['tpVerbosity'],

    newSynapseCount = config['spNumActivePerInhArea'],
    minThreshold = config['spNumActivePerInhArea'],
    activationThreshold = config['spNumActivePerInhArea'],

    initialPerm = config['tpInitialPerm'],
    connectedPerm = 0.5,
    permanenceInc = config['tpPermanenceInc'],
    permanenceDec = config['tpPermanenceDec'],  # perhaps tune this
    globalDecay = config['tpGlobalDecay'],

    pamLength = config['tpPAMLength'],
    maxSeqLength = config['tpMaxSeqLength'],
    maxAge = config['tpMaxAge'],


    # General params
    computeTopDown = config['computeTopDown'],
    trainingStep = 'spatial',
    )


  dataSource = FileRecordStream(datasets['filenameTrain'])

  description = dict(
    options = dict(
      logOutputsDuringInference = False,
    ),

    network = dict(
      sensorDataSource = dataSource,
      sensorEncoder = encoder, 
      sensorParams = sensorParams,

      CLAType = 'py.CLARegion',
      CLAParams = CLAParams,

      classifierType = None,
      classifierParams = None),
  )

  if config['trainSP']:
    description['spTrain'] = dict(
      iterationCount=config['iterationCountTrain'], 
      #iter=displaySPCoincidences(50),
      #finish=printSPCoincidences()
      ),
  else:
    description['spTrain'] = dict(
      # need to train with one iteration just to initialize data structures
      iterationCount=1)

  if config['trainTP']:
    description['tpTrain'] = []
    for i in xrange(config['trainTPRepeats']):
      stepDict = dict(name='step_%d' % (i), 
                      setup=sensorRewind, 
                      iterationCount=config['iterationCountTrain'],
                      )
      if config['tpTimingEvery'] > 0:
        stepDict['iter'] = printTPTiming(config['tpTimingEvery'])
        stepDict['finish'] = [printTPTiming(), printTPCells]

      description['tpTrain'].append(stepDict)


  # ----------------------------------------------------------------------------
  # Inference tests
  inferSteps = []

  if config['evalTrainingSetNumIterations'] > 0:
    # The training set. Used to train the n-grams. 
    inferSteps.append(
      dict(name = 'confidenceTrain_baseline', 
           iterationCount = min(config['evalTrainingSetNumIterations'], 
                                config['iterationCountTrain']),
           ppOptions = dict(verbosity=config['ppVerbosity'],
                            printLearnedCoincidences=True,
                            nGrams='train',
                            #ipsDetailsFor = "name,None,2",
                            ),
             #finish=printTPCells,
          )
      )

    # Testing the training set on both the TP and n-grams. 
    inferSteps.append(
      dict(name = 'confidenceTrain_nonoise', 
             iterationCount = min(config['evalTrainingSetNumIterations'], 
                                  config['iterationCountTrain']),
             setup = [sensorOpen(datasets['filenameTrain'])],
             ppOptions = dict(verbosity=config['ppVerbosity'],
                              printLearnedCoincidences=False,
                              nGrams='test',
                              burnIns = [1,2,3,4],
                              #ipsDetailsFor = "name,None,2",
                              #ipsAt = [1,2,3,4],
                              ),
            )
        )

    # The test set
  if True:
    if datasets['filenameTest'] != datasets['filenameTrain']:
      inferSteps.append(
        dict(name = 'confidenceTest_baseline', 
             iterationCount = config['iterationCountTest'],
             setup = [sensorOpen(datasets['filenameTest'])],
             ppOptions = dict(verbosity=config['ppVerbosity'],
                              printLearnedCoincidences=False,
                              nGrams='test',
                              burnIns = [1,2,3,4],
                              #ipsAt = [1,2,3,4],
                              ipsDetailsFor = "name,None,2",
                              ),
            )
        )


  description['infer'] = inferSteps

  return description
