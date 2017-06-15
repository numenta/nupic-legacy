import csv
import datetime
import numpy
import os
import yaml

from nupic.algorithms.sdr_classifier_factory import SDRClassifierFactory
from nupic.algorithms.spatial_pooler import SpatialPooler
from nupic.algorithms.temporal_memory import TemporalMemory
from nupic.encoders.date import DateEncoder
from nupic.encoders.random_distributed_scalar import \
  RandomDistributedScalarEncoder

_NUM_RECORDS = 3000
_EXAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))
_INPUT_FILE_PATH = os.path.join(_EXAMPLE_DIR, os.pardir, "data", "gymdata.csv")
_PARAMS_PATH = os.path.join(_EXAMPLE_DIR, os.pardir, "params", "model.yaml")



def runHotgym(numRecords):
  with open(_PARAMS_PATH, "r") as f:
    modelParams = yaml.safe_load(f)["modelParams"]
    enParams = modelParams["sensorParams"]["encoders"]
    spParams = modelParams["spParams"]
    tmParams = modelParams["tmParams"]

  timeOfDayEncoder = DateEncoder(
    timeOfDay=enParams["timestamp_timeOfDay"]["timeOfDay"])
  weekendEncoder = DateEncoder(
    weekend=enParams["timestamp_weekend"]["weekend"])
  scalarEncoder = RandomDistributedScalarEncoder(
    enParams["consumption"]["resolution"])

  encodingWidth = (timeOfDayEncoder.getWidth()
                   + weekendEncoder.getWidth()
                   + scalarEncoder.getWidth())

  sp = SpatialPooler(
    # How large the input encoding will be.
    inputDimensions=(encodingWidth,),
    # How many mini-columns will be in the Spatial Pooler.
    columnDimensions=(spParams["columnCount"],),
    # What percent of the columns"s receptive field is available for potential
    # synapses?
    potentialPct=spParams["potentialPct"],
    # Potential radius should be set to the input size if there is global
    # inhibition.
    potentialRadius=encodingWidth,
    # This means that the input space has no topology.
    globalInhibition=spParams["globalInhibition"],
    localAreaDensity=spParams["localAreaDensity"],
    # Roughly 2%, giving that there is only one inhibition area because we have
    # turned on globalInhibition (40 / 2048 = 0.0195)
    numActiveColumnsPerInhArea=spParams["numActiveColumnsPerInhArea"],
    # How quickly synapses grow and degrade.
    synPermInactiveDec=spParams["synPermInactiveDec"],
    synPermActiveInc=spParams["synPermActiveInc"],
    synPermConnected=spParams["synPermConnected"],
    # boostStrength controls the strength of boosting. Boosting encourages
    # efficient usage of SP columns.
    boostStrength=spParams["boostStrength"],
    # Random number generator seed.
    seed=spParams["seed"],
    # TODO: is this useful?
    # Determines if inputs at the beginning and end of an input dimension should
    # be considered neighbors when mapping columns to inputs.
    wrapAround=True
  )

  tm = TemporalMemory(
    # Must be the same dimensions as the SP
    columnDimensions=(tmParams["columnCount"],),
    # How many cells in each mini-column.
    cellsPerColumn=tmParams["cellsPerColumn"],
    # A segment is active if it has >= activationThreshold connected synapses
    # that are active due to infActiveState
    activationThreshold=tmParams["activationThreshold"],
    initialPermanence=tmParams["initialPerm"],
    # TODO: This comes from the SP params, is this normal
    connectedPermanence=spParams["synPermConnected"],
    # Minimum number of active synapses for a segment to be considered during
    # search for the best-matching segments.
    minThreshold=tmParams["minThreshold"],
    # The max number of synapses added to a segment during learning
    maxNewSynapseCount=tmParams["newSynapseCount"],
    permanenceIncrement=tmParams["permanenceInc"],
    permanenceDecrement=tmParams["permanenceDec"],
    predictedSegmentDecrement=0.0,
    maxSegmentsPerCell=tmParams["maxSegmentsPerCell"],
    maxSynapsesPerSegment=tmParams["maxSynapsesPerSegment"],
    seed=tmParams["seed"]
  )

  classifier = SDRClassifierFactory.create()
  results = []
  with open(_INPUT_FILE_PATH, "r") as fin:
    reader = csv.reader(fin)
    headers = reader.next()
    reader.next()
    reader.next()

    for count, record in enumerate(reader):

      if count >= numRecords: break

      # Convert data string into Python date object.
      dateString = datetime.datetime.strptime(record[0], "%m/%d/%y %H:%M")
      # Convert data value string into float.
      consumption = float(record[1])

      # To encode, we need to provide zero-filled numpy arrays for the encoders
      # to populate.
      timeOfDayBits = numpy.zeros(timeOfDayEncoder.getWidth())
      weekendBits = numpy.zeros(weekendEncoder.getWidth())
      consumptionBits = numpy.zeros(scalarEncoder.getWidth())

      # Now we call the encoders create bit representations for each value.
      timeOfDayEncoder.encodeIntoArray(dateString, timeOfDayBits)
      weekendEncoder.encodeIntoArray(dateString, weekendBits)
      scalarEncoder.encodeIntoArray(consumption, consumptionBits)

      # Concatenate all these encodings into one large encoding for Spatial
      # Pooling.
      encoding = numpy.concatenate(
        [timeOfDayBits, weekendBits, consumptionBits]
      )

      # Create an array to represent active columns, all initially zero. This
      # will be populated by the compute method below. It must have the same
      # dimensions as the Spatial Pooler.
      activeColumns = numpy.zeros(spParams["columnCount"])

      # Execute Spatial Pooling algorithm over input space.
      sp.compute(encoding, True, activeColumns)
      activeColumnIndices = numpy.nonzero(activeColumns)[0]

      # Execute Temporal Memory algorithm over active mini-columns.
      tm.compute(activeColumnIndices, learn=True)

      activeCells = tm.getActiveCells()

      # Get the bucket info for this input value for classification.
      bucketIdx = scalarEncoder.getBucketIndices(consumption)[0]

      # Run classifier to translate active cells back to scalar value.
      classifierResult = classifier.compute(
        recordNum=count,
        patternNZ=activeCells,
        classification={
          "bucketIdx": bucketIdx,
          "actValue": consumption
        },
        learn=True,
        infer=True
      )

      # Print the best prediction for 1 step out.
      oneStepConfidence, oneStep = sorted(
        zip(classifierResult[1], classifierResult["actualValues"]),
        reverse=True
      )[0]
      print("1-step: {:16} ({:4.4}%)".format(oneStep, oneStepConfidence * 100))
      results.append([oneStep, oneStepConfidence * 100, None, None])

    return results


if __name__ == "__main__":
  runHotgym(_NUM_RECORDS)
