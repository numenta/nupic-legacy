import json
import os
import yaml

from nupic.engine import Network
from nupic.encoders import MultiEncoder
from nupic.data.file_record_stream import FileRecordStream

_NUM_RECORDS = 3000
_EXAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))
_INPUT_FILE_PATH = os.path.join(_EXAMPLE_DIR, os.pardir, "data", "gymdata.csv")
_PARAMS_PATH = os.path.join(_EXAMPLE_DIR, os.pardir, "params", "model.yaml")



def createDataOutLink(network, sensorRegionName, regionName):
  """Link sensor region to other region so that it can pass it data."""
  network.link(sensorRegionName, regionName, "UniformLink", "",
               srcOutput="dataOut", destInput="bottomUpIn")


def createFeedForwardLink(network, regionName1, regionName2):
  """Create a feed-forward link between 2 regions: regionName1 -> regionName2"""
  network.link(regionName1, regionName2, "UniformLink", "",
               srcOutput="bottomUpOut", destInput="bottomUpIn")


def createResetLink(network, sensorRegionName, regionName):
  """Create a reset link from a sensor region: sensorRegionName -> regionName"""
  network.link(sensorRegionName, regionName, "UniformLink", "",
               srcOutput="resetOut", destInput="resetIn")


def createSensorToClassifierLinks(network, sensorRegionName,
                                  classifierRegionName):
  """Create required links from a sensor region to a classifier region."""
  network.link(sensorRegionName, classifierRegionName, "UniformLink", "",
               srcOutput="bucketIdxOut", destInput="bucketIdxIn")
  network.link(sensorRegionName, classifierRegionName, "UniformLink", "",
               srcOutput="actValueOut", destInput="actValueIn")
  network.link(sensorRegionName, classifierRegionName, "UniformLink", "",
               srcOutput="categoryOut", destInput="categoryIn")


def createEncoder(encoderParams):
  """Create a multi-encoder from params."""
  encoder = MultiEncoder()
  encoder.addMultipleEncoders(encoderParams)
  return encoder


def createNetwork(dataSource):
  """Create and initialize a network."""
  with open(_PARAMS_PATH, "r") as f:
    modelParams = yaml.safe_load(f)["modelParams"]

  # Create a network that will hold the regions.
  network = Network()

  # Add a sensor region.
  network.addRegion("sensor", "py.RecordSensor", '{}')

  # Set the encoder and data source of the sensor region.
  sensorRegion = network.regions["sensor"].getSelf()
  sensorRegion.encoder = createEncoder(modelParams["sensorParams"]["encoders"])
  sensorRegion.dataSource = dataSource

  # Make sure the SP input width matches the sensor region output width.
  modelParams["spParams"]["inputWidth"] = sensorRegion.encoder.getWidth()

  # Add SP and TM regions.
  network.addRegion("SP", "py.SPRegion", json.dumps(modelParams["spParams"]))
  network.addRegion("TM", "py.TMRegion", json.dumps(modelParams["tmParams"]))

  # Add a classifier region.
  clName = "py.%s" % modelParams["clParams"].pop("regionName")
  network.addRegion("classifier", clName, json.dumps(modelParams["clParams"]))

  # Add all links
  createSensorToClassifierLinks(network, "sensor", "classifier")
  createDataOutLink(network, "sensor", "SP")
  createFeedForwardLink(network, "SP", "TM")
  createFeedForwardLink(network, "TM", "classifier")
  # Reset links are optional, since the sensor region does not send resets.
  createResetLink(network, "sensor", "SP")
  createResetLink(network, "sensor", "TM")

  # Make sure all objects are initialized.
  network.initialize()

  return network


def getPredictionResults(network, clRegionName):
  """Get prediction results for all prediction steps."""
  classifierRegion = network.regions[clRegionName]
  actualValues = classifierRegion.getOutputData("actualValues")
  probabilities = classifierRegion.getOutputData("probabilities")
  steps = classifierRegion.getSelf().stepsList
  N = classifierRegion.getSelf().maxCategoryCount
  results = {step: {} for step in steps}
  for i in range(len(steps)):
    # stepProbabilities are probabilities for this prediction step only.
    stepProbabilities = probabilities[i * N:(i + 1) * N - 1]
    mostLikelyCategoryIdx = stepProbabilities.argmax()
    predictedValue = actualValues[mostLikelyCategoryIdx]
    predictionConfidence = stepProbabilities[mostLikelyCategoryIdx]
    results[steps[i]]["predictedValue"] = predictedValue
    results[steps[i]]["predictionConfidence"] = predictionConfidence
  return results


def runHotgym(numRecords):
  """Run the Hot Gym example."""

  # Create a data source for the network.
  dataSource = FileRecordStream(streamID=_INPUT_FILE_PATH)
  numRecords = min(numRecords, dataSource.getDataRowCount())
  network = createNetwork(dataSource)

  # Set predicted field
  network.regions["sensor"].setParameter("predictedField", "consumption")

  # Enable learning for all regions.
  network.regions["SP"].setParameter("learningMode", 1)
  network.regions["TM"].setParameter("learningMode", 1)
  network.regions["classifier"].setParameter("learningMode", 1)

  # Enable inference for all regions.
  network.regions["SP"].setParameter("inferenceMode", 1)
  network.regions["TM"].setParameter("inferenceMode", 1)
  network.regions["classifier"].setParameter("inferenceMode", 1)

  results = []
  N = 1  # Run the network, N iterations at a time.
  for iteration in range(0, numRecords, N):
    network.run(N)

    predictionResults = getPredictionResults(network, "classifier")
    oneStep = predictionResults[1]["predictedValue"]
    oneStepConfidence = predictionResults[1]["predictionConfidence"]
    fiveStep = predictionResults[5]["predictedValue"]
    fiveStepConfidence = predictionResults[5]["predictionConfidence"]

    result = (oneStep, oneStepConfidence * 100,
              fiveStep, fiveStepConfidence * 100)
    print "1-step: {:16} ({:4.4}%)\t 5-step: {:16} ({:4.4}%)".format(*result)
    results.append(result)

  return results

if __name__ == "__main__":
  runHotgym(_NUM_RECORDS)
