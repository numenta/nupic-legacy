from nupic.encoders import (LogEncoder, DateEncoder, MultiEncoder, ScalarEncoder)

from nupic.data import FunctionSource
from nupic.frameworks.prediction.callbacks import displaySPCoincidences, printSPCoincidences
from nupic.data.dict_utils import DictObj


nCoincidences = 30
iterationCount = 10000

nRandomFields = 1
randomFieldWidth = 66

# Controls behavior of iteration callback
showSPCoincs = True


def generateFunction(info):
  # This function needs to be self-contained so that it can work
  # after de-serialization.
  # These imports shouldn't be too slow after the first import
  import datetime
  import random
  d = DictObj()

  # Generate a random time in a one-month period
  t = datetime.datetime.fromtimestamp(1289409426 + random.randint(0, 30*86000))

  # Amount varies as follows:
  # Most of the day, it has a 90% chance of being between 1 and 10.00
  # and a 10% chance of being between 100 and 1000)
  # between 8PM and 11PM, the probabilities are reversed
  # p = probability of high value
  p = 1.0
  if 20 <= t.hour < 23:
    p = 1.0 - p
  if random.random() < p:
    amount = random.randint(100, 1000)
  else:
    amount = random.randint(1, 10)

  # Dictionary keys must match the names in the multiencoder
  d["date"] = t
  d["amount"] = amount
  for i in xrange(info['nRandomFields']):
    d["random%d" %i] = random.randint(0, info['randomFieldWidth'])
  return d


def getBaseDatasets():
  return dict()

def getDatasets(baseDatasets, generate=False):
  return baseDatasets

def getDescription(datasets):
  encoder = MultiEncoder()
  encoder.addEncoder("date", DateEncoder(timeOfDay=3))
  encoder.addEncoder("amount", LogEncoder(name="amount", maxval=1000))
  for i in xrange(0, nRandomFields):
    s = ScalarEncoder(name="scalar", minval=0, maxval=randomFieldWidth, resolution=1, w=3)
    encoder.addEncoder("random%d" % i, s)

  dataSource = FunctionSource(generateFunction, dict(nRandomFields=nRandomFields,
                                                 randomFieldWidth=randomFieldWidth))

  inputDimensions = (1, encoder.getWidth())

  # Layout the coincidences vertically stacked on top of each other, each
  # looking at the entire input field.
  columnDimensions = (nCoincidences, 1)


  nodeParams = dict()

  spParams = dict(
        commonDistributions=0,
        inputDimensions = inputDimensions,
        columnDimensions = columnDimensions,
        potentialRadius = inputDimensions[1]/2,
        potentialPct = 0.75,
        gaussianDist = 0,
        localAreaDensity = 0.10,
        # localAreaDensity = 0.04,
        numActiveColumnsPerInhArea = -1,
        dutyCyclePeriod = 1000,
        stimulusThreshold = 5,
        synPermInactiveDec=0.08,
        # synPermInactiveDec=0.02,
        synPermActiveInc=0.02,
        synPermActiveSharedDec=0.0,
        synPermOrphanDec = 0.0,
        minPctDutyCycleBeforeInh = 0.05,
        # minPctDutyCycleAfterInh = 0.1,
        # minPctDutyCycleBeforeInh = 0.05,
        minPctDutyCycleAfterInh = 0.05,
        # minPctDutyCycleAfterInh = 0.4,
        seed = 1,
  )

  otherParams = dict(
    disableTemporal=1,
    trainingStep='spatial',

  )

  nodeParams.update(spParams)
  nodeParams.update(otherParams)

  def mySetupCallback(experiment):
    print "Setup function called"

  description = dict(
    options = dict(
      logOutputsDuringInference = False,
    ),

    network = dict(
      sensorDataSource = dataSource,
      sensorEncoder = encoder,
      CLAType = "py.CLARegion",
      CLAParams = nodeParams,
      classifierType = None,
      classifierParams = None),

    # step
    spTrain = dict(
      name="phase1",
      setup=mySetupCallback,
      iterationCount=5000,
      #iter=displaySPCoincidences(100),
      finish=printSPCoincidences()),

    tpTrain = None,        # same format as sptrain if non-empty

    infer = None,          # same format as sptrain if non-empty

  )

  return description
