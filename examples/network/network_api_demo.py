#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

import json
import copy

from nupic.algorithms.anomaly import computeAnomalyScore
from nupic.data.datasethelpers import findDataset
from nupic.data.file_record_stream import FileRecordStream
from nupic.engine import Network
from nupic.encoders import MultiEncoder


_VERBOSITY = 0         # how chatty the demo should be
_SEED = 1956             # the random seed used throughout
_DATA_PATH = "../prediction/data/extra/hotgym/rec-center-hourly.csv"
_OUTPUT_PATH = "test_output.csv"


# Config field for SPRegion
g_spRegionConfig = dict(
  spVerbosity = _VERBOSITY,
  spatialImp = 'cpp',
  globalInhibition = 1,
  columnCount = 2048,
  inputWidth   = 0,
  numActivePerInhArea = 40,
  seed = 1956,
  potentialPct = 0.8,
  synPermConnected = 0.1,
  synPermActiveInc = 0.0001,
  synPermInactiveDec = 0.0005,
  maxBoost = 1.0
  )


# Config field for TPRegion
g_tpRegionConfig = dict(
  verbosity = _VERBOSITY,
  columnCount = 2048,
  cellsPerColumn = 32,
  inputWidth   = 2048,
  seed = 1960,
  temporalImp = 'cpp',
  newSynapseCount = 20,
  maxSynapsesPerSegment = 32,
  maxSegmentsPerCell = 128,
  initialPerm = 0.21,
  permanenceInc = 0.1,
  permanenceDec = 0.1,
  globalDecay = 0.0,
  maxAge = 0,
  minThreshold = 9,
  activationThreshold = 12,
  outputType = 'normal',
  pamLength = 3
  )


def createEncoder():
  """Create the encoder instance for our test and return it."""
  encoder = MultiEncoder()
  encoder.addMultipleEncoders({
    'timestamp': dict(fieldname='timestamp',
                      type='DateEncoder',
                      timeOfDay=(21, 9.5)),

    'consumption': dict(clipInput=True,
                        fieldname='consumption',
                        maxval = 100.0,
                        minval = 0.0,
                        n=50,
                        type='ScalarEncoder',
                        name='consumption',
                        w=21),
    })

  return encoder

"""         _________________
 Input --> |                 |
           | Spatial Pooler  |
           |                 |
           |vvvvvvvvvvvvvvvvv|
           |                 |
           | Temporal Pooler |
           |_________________|
                   |
                   '------> Output
"""


def createNetwork():
  print "Creating network..."

  encoder = createEncoder()
  trainFile = findDataset(_DATA_PATH)
  print (trainFile)
  dataSource = FileRecordStream(streamID=trainFile)
  #dataSource.setAutoRewind(True)

  network = Network()

  # Our input is sensor data from the gym.csv file
  network.addRegion("sensor", "py.RecordSensor", json.dumps(dict(verbosity = _VERBOSITY)))
  sensor = network.regions['sensor'].getSelf()
  sensor.encoder = encoder
  sensor.dataSource = dataSource

  # |sensor| -> |spatialPoolerRegion|
  # Create the spatial pooler region
  g_spRegionConfig['inputWidth'] = encoder.getWidth()
  network.addRegion("spatialPoolerRegion", "py.SPRegion", json.dumps(g_spRegionConfig))

  # Link the SP region to the sensor input
  network.link("sensor", "spatialPoolerRegion", "UniformLink", "")
  network.link("sensor", "spatialPoolerRegion", "UniformLink", "",
               srcOutput="resetOut", destInput="resetIn")
  network.link("spatialPoolerRegion", "sensor", "UniformLink", "",
               srcOutput="spatialTopDownOut", destInput="spatialTopDownIn")
  network.link("spatialPoolerRegion", "sensor", "UniformLink", "",
               srcOutput="temporalTopDownOut", destInput="temporalTopDownIn")

  # |sensor| -> |spatialPoolerRegion| -> |temporalPoolerRegion|
  # Add the Temporal Pooler Region on top of the existing network
  g_tpRegionConfig['inputWidth'] = g_spRegionConfig['columnCount']
  network.addRegion("temporalPoolerRegion", "py.TPRegion", json.dumps(g_tpRegionConfig))

  network.link("spatialPoolerRegion", "temporalPoolerRegion", "UniformLink", "")
  network.link("temporalPoolerRegion", "spatialPoolerRegion", "UniformLink", "",
               srcOutput="topDownOut", destInput="topDownIn")
  network.link("sensor", "temporalPoolerRegion", "UniformLink", "",
               srcOutput="resetOut", destInput="resetIn")

  return network


def runNetwork(network):

  network.initialize()

  spatialPoolerRegion = network.regions['spatialPoolerRegion']
  spatialPoolerRegion.setParameter('learningMode', 1)
  #spatialPoolerRegion.setParameter('inferenceMode', 0)

  #network.run(500)
  #spatialPoolerRegion.setParameter('learningMode', 0)
  spatialPoolerRegion.setParameter('inferenceMode', 1)
  spatialPoolerRegion.setParameter('anomalyMode', 0)

  temporalPoolerRegion = network.regions['temporalPoolerRegion']
  temporalPoolerRegion.setParameter('learningMode', 1)
  temporalPoolerRegion.setParameter('inferenceMode', 1)
  temporalPoolerRegion.setParameter('anomalyMode', 1)
  temporalPoolerRegion.setParameter('topDownMode', 1)
  network.setMaxEnabledPhase(network.maxPhase)

  prevPredictedColumns = []

  #"""
  for _ in xrange(50):
    # Run the network for a single iteration
    network.run(1)

    activeColumns = spatialPoolerRegion.getOutputData("bottomUpOut").nonzero()[0]

    # Calculate the anomaly score using the active columns
    # and previous predicted columns
    anomalyScore = computeAnomalyScore(activeColumns, prevPredictedColumns)

    # Store the predicted columns for the next timestep
    predictedColumns = temporalPoolerRegion.getOutputData("topDownOut").nonzero()[0]
    prevPredictedColumns = copy.deepcopy(predictedColumns)

    print anomalyScore
  """

  # Run inference on the network for 100 iterations"
  with open(_DATA_PATH, "rb") as inputCSV:
    with open(_OUTPUT_PATH, "wb") as outputCSV:

      reader = csv.reader(inputCSV)
      # Skip the header lines
      reader.next()
      reader.next()
      reader.next()

      writer = csv.writer(outputCSV)
      # Write the column titles for the output file
      writer.writerow(["timestamp", "consumption", "anomaly_score"])

      for index, inputRow in enumerate(reader):
        if index % 1000 == 0 and index != 0:
          print ("read %s lines" % index)

        if index > 5000:
          break

        # Run the network for a single iteration
        network.run(1)

        activeColumns = spatialPoolerRegion.getOutputData("bottomUpOut").nonzero()[0]

        # Calculate the anomaly score using the active columns
        # and previous predicted columns
        anomalyScore = computeAnomalyScore(activeColumns, prevPredictedColumns)

        # Store the predicted columns for the next timestep
        predictedColumns = temporalPoolerRegion.getOutputData("bottomUpOut").nonzero()[0]
        prevPredictedColumns = copy.deepcopy(predictedColumns)

        # Write the anomaly as "timestamp, consumption, anomaly"
        writer.writerow([str(inputRow[0]), inputRow[1], anomalyScore])
  #"""

if __name__ == "__main__":
  network = createNetwork()
  runNetwork(network)
