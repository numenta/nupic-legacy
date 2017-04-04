import csv
import datetime

import numpy

from nupic.encoders.date import DateEncoder
from nupic.encoders.random_distributed_scalar import \
    RandomDistributedScalarEncoder
from nupic.research.spatial_pooler import SpatialPooler
from nupic.research.temporal_memory import TemporalMemory
from nupic.algorithms.sdr_classifier_factory import SDRClassifierFactory

_INPUT_FILE_PATH = "../data/gymdata.csv"

def runHotgym():

  timeOfDayEncoder = DateEncoder(timeOfDay=(21,1))
  weekendEncoder = DateEncoder(weekend=21)
  scalarEncoder = RandomDistributedScalarEncoder(0.88)

  encodingWidth = timeOfDayEncoder.getWidth() \
    + weekendEncoder.getWidth() \
    + scalarEncoder.getWidth()

  sp = SpatialPooler(
    # How large the input encoding will be.
    inputDimensions=(encodingWidth),
    # How many mini-columns will be in the Spatial Pooler.
    columnDimensions=(2048),
    # What percent of the columns's receptive field is available for potential
    # synapses?
    potentialPct=0.85,
    # This means that the input space has no topology.
    globalInhibition=True,
    localAreaDensity=-1.0,
    # Roughly 2%, giving that there is only one inhibition area because we have
    # turned on globalInhibition (40 / 2048 = 0.0195)
    numActiveColumnsPerInhArea=40.0,
    # How quickly synapses grow and degrade.
    synPermInactiveDec=0.005,
    synPermActiveInc=0.04,
    synPermConnected=0.1,
    # boostStrength controls the strength of boosting. Boosting encourages
    # efficient usage of SP columns.
    boostStrength=3.0,
    # Random number generator seed.
    seed=1956,
    # Determines if inputs at the beginning and end of an input dimension should
    # be considered neighbors when mapping columns to inputs.
    wrapAround=False
  )

  tm = TemporalMemory(
    # Must be the same dimensions as the SP
    columnDimensions=(2048, ),
    # How many cells in each mini-column.
    cellsPerColumn=32,
    # A segment is active if it has >= activationThreshold connected synapses
    # that are active due to infActiveState
    activationThreshold=16,
    initialPermanence=0.21,
    connectedPermanence=0.5,
    # Minimum number of active synapses for a segment to be considered during
    # search for the best-matching segments.
    minThreshold=12,
    # The max number of synapses added to a segment during learning
    maxNewSynapseCount=20,
    permanenceIncrement=0.1,
    permanenceDecrement=0.1,
    predictedSegmentDecrement=0.0,
    maxSegmentsPerCell=128,
    maxSynapsesPerSegment=32,
    seed=1960
  )

  classifier = SDRClassifierFactory.create()

  with open (_INPUT_FILE_PATH) as fin:
    reader = csv.reader(fin)
    headers = reader.next()
    reader.next()
    reader.next()

    for count, record in enumerate(reader):
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
      activeColumns = numpy.zeros(2048)

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
      probability, value = sorted(
        zip(classifierResult[1], classifierResult["actualValues"]),
        reverse=True
      )[0]
      print("1-step: {:16} ({:4.4}%)".format(value, probability * 100))


if __name__ == "__main__":
  runHotgym()
