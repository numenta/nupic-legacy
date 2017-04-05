import csv
import json
import yaml

from nupic.engine import Network
from nupic.encoders import MultiEncoder
from nupic.data.file_record_stream import FileRecordStream

_NUM_RECORDS = 3000
_INPUT_FILE_PATH = '../data/gymdata.csv'
_OUTPUT_FILE_PATH = 'predictions.csv'
_PARAMS_PATH = '../params/model.yaml'



def createDataOutLink(network, sensorRegionName, regionName):
  """Link sensor region to other region so that it can pass it data."""
  network.link(sensorRegionName, regionName, "UniformLink", "",
               srcOutput="dataOut", destInput="bottomUpIn")



def createFeedForwardLink(network, regionName1, regionName2):
  """Create a feed-forward link between 2 regions: regionName1 -> regionName2"""
  network.link(regionName1, regionName2, 'UniformLink', '',
               srcOutput='bottomUpOut', destInput='bottomUpIn')



def createResetLink(network, sensorRegionName, regionName):
  """Create a reset link from a sensor region: sensorRegionName -> regionName"""
  network.link(sensorRegionName, regionName, 'UniformLink', '',
               srcOutput='resetOut', destInput='resetIn')



def createCategoryLink(network, sensorRegionName, classifierRegionName):
  """Create a category link from a sensor region to a classifier region."""
  network.link(sensorRegionName, classifierRegionName, 'UniformLink', '',
               srcOutput='categoryOut', destInput='categoryIn')



def createEncoder(encoderParams):
  """Create a multi-encoder from params."""
  encoder = MultiEncoder()
  encoder.addMultipleEncoders(encoderParams)
  return encoder



def createNetwork(dataSource):
  """Create and initialize a network."""
  with open(_PARAMS_PATH, 'r') as f:
    model_params = yaml.safe_load(f)['modelParams']

  # Create a network that will hold the regions.
  network = Network()

  # Add a sensor region, set its encoder and data source.
  network.addRegion('sensor', 'py.RecordSensor', json.dumps({'verbosity': 0}))
  sensorRegion = network.regions['sensor'].getSelf()
  sensorRegion.encoder = createEncoder(model_params['sensorParams']['encoders'])
  sensorRegion.dataSource = dataSource

  # Make sure the SP input width matches the sensor region output width.
  model_params['spParams']['inputWidth'] = sensorRegion.encoder.getWidth()

  # Add the SP and TM regions.
  network.addRegion('SP', 'py.SPRegion', json.dumps(model_params['spParams']))
  network.addRegion('TM', 'py.TPRegion', json.dumps(model_params['tpParams']))

  # Add the classifier.
  clParams = model_params['clParams']
  clName = clParams.pop('regionName')
  network.addRegion('classifier', 'py.' + clName, json.dumps(clParams))

  # Link the sensor region to the SP region so that it can pass it data.
  createDataOutLink(network, 'sensor', 'SP')

  # Create feed-forward links between regions.
  createFeedForwardLink(network, 'SP', 'TM')
  createFeedForwardLink(network, 'TM', 'classifier')

  # Propagate reset signals to SP and TM regions.
  # Optional if you know that your sensor regions does not send resets.
  createResetLink(network, 'sensor', 'SP')
  createResetLink(network, 'sensor', 'TM')

  # FIXME NUP-2396: replace this by new link(s) after changes.
  createCategoryLink(network, 'sensor', 'classifier')

  # Make sure all objects are initialized.
  network.initialize()

  return network



# FIXME NUP-2396: delete after changes
def runClassifier(classifier, sensorRegion, tmRegion, recordNumber):
  """Call classifier manually, not using network."""

  # Obtain input, its encoding, and the TM output for classification
  actualInput = float(sensorRegion.getOutputData("sourceOut")[0])
  scalarEncoder = sensorRegion.getSelf().encoder.encoders[0][1]
  bucketIndex = scalarEncoder.getBucketIndices(actualInput)[0]
  tmOutput = tmRegion.getOutputData("bottomUpOut").nonzero()[0]
  classDict = {"actValue": actualInput, "bucketIdx": bucketIndex}

  # Call classifier
  classifier.getSelf()._computeFlag = False
  classifier.setParameter('learningMode', 1)
  classifier.setParameter('inferenceMode', 1)
  results = classifier.getSelf().customCompute(recordNum=recordNumber,
                                               patternNZ=tmOutput,
                                               classification=classDict)
  classifier.setParameter('learningMode', 0)
  classifier.setParameter('inferenceMode', 0)

  # Sort results by prediction confidence taking most confident prediction
  mostLikelyResult = sorted(zip(results[1], results["actualValues"]))[-1]
  predictionConfidence = mostLikelyResult[0]
  predictedValue = mostLikelyResult[1]
  return actualInput, predictedValue, predictionConfidence



def runHotGym():
  """Run the Hot Gym example."""

  # Create a data source for the network.
  dataSource = FileRecordStream(streamID=_INPUT_FILE_PATH)
  numRecords = dataSource.getDataRowCount()

  network = createNetwork(dataSource)

  # Enable learning for all regions.
  network.regions['SP'].setParameter('learningMode', 1)
  network.regions['TM'].setParameter('learningMode', 1)
  # FIXME NUP-2396: reintroduce after changes
  # network.regions['classifier'].setParameter('learningMode', 1)

  # Enable inference for all regions.
  network.regions['SP'].setParameter('inferenceMode', 1)
  network.regions['TM'].setParameter('inferenceMode', 1)
  # FIXME NUP-2396: reintroduce after changes
  # network.regions['classifier'].setParameter('inferenceMode', 1)

  with open(_OUTPUT_FILE_PATH, 'w') as of:
    writer = csv.writer(of)
    writer.writerow(['input', 'prediction', 'confidence'])

    # Run the network, 1 iteration at a time.
    for iteration in range(numRecords):
      network.run(1)
      (actualInput,
       predictedValue,
       predictionConfidence) = runClassifier(network.regions['classifier'],
                                             network.regions['sensor'],
                                             network.regions['TM'],
                                             iteration)

      # Print and save the best prediction for 1 step out.
      print("1-step: {:16} ({:4.4}%)".format(predictedValue,
                                             predictionConfidence * 100))
      writer.writerow(['%.5f' % actualInput,
                       '%.5f' % predictedValue,
                       '%.5f' % predictionConfidence])



if __name__ == '__main__':
  runHotGym()
