# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2016, Numenta, Inc.  Unless you have an agreement
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

import copy
import csv
import json
import os
import tempfile
from pkg_resources import resource_filename

from nupic.data.file_record_stream import FileRecordStream
from nupic.engine import Network
from nupic.encoders import MultiEncoder, ScalarEncoder, DateEncoder
from nupic.regions.record_sensor import RecordSensor
from nupic.regions.sp_region import SPRegion
from nupic.regions.tm_region import TMRegion

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.proto import NetworkProto_capnp


_VERBOSITY = 0  # how chatty the test should be
_SEED = 1956  # the random seed used throughout
_INPUT_FILE_PATH = resource_filename(
  "nupic.datafiles", "extra/hotgym/rec-center-hourly.csv"
)
_NUM_RECORDS = 1000

# Config field for SPRegion
SP_PARAMS = {
    "spVerbosity": _VERBOSITY,
    "spatialImp": "cpp",
    "globalInhibition": 1,
    "columnCount": 2048,
    # This must be set before creating the SPRegion
    "inputWidth": 0,
    "numActiveColumnsPerInhArea": 40,
    "seed": 42,
    "potentialPct": 0.8,
    "synPermConnected": 0.1,
    "synPermActiveInc": 0.0001,
    "synPermInactiveDec": 0.0005,
    "boostStrength": 0.0,
}

# Config field for TMRegion
TM_PARAMS = {
    "verbosity": _VERBOSITY,
    "columnCount": 2048,
    "cellsPerColumn": 32,
    "inputWidth": 2048,
    "seed": 1960,
    "temporalImp": "cpp",
    "newSynapseCount": 20,
    "maxSynapsesPerSegment": 32,
    "maxSegmentsPerCell": 128,
    "initialPerm": 0.21,
    "permanenceInc": 0.1,
    "permanenceDec": 0.1,
    "predictedSegmentDecrement": .01,
    "globalDecay": 0.0,
    "maxAge": 0,
    "minThreshold": 9,
    "activationThreshold": 12,
    "outputType": "normal",
    "pamLength": 3,
}



def createEncoder():
  """Create the encoder instance for our test and return it."""
  consumption_encoder = ScalarEncoder(21, 0.0, 100.0, n=50, name="consumption",
      clipInput=True)
  time_encoder = DateEncoder(timeOfDay=(21, 9.5), name="timestamp_timeOfDay")

  encoder = MultiEncoder()
  encoder.addEncoder("consumption", consumption_encoder)
  encoder.addEncoder("timestamp", time_encoder)

  return encoder



def createNetwork(dataSource, enableTP=False, temporalImp="py"):
  """Create the Network instance.

  The network has a sensor region reading data from `dataSource` and passing
  the encoded representation to an SPRegion. The SPRegion output is passed to
  a TMRegion.

  :param dataSource: a RecordStream instance to get data from
  :returns: a Network instance ready to run
  """
  network = Network()

  # Our input is sensor data from the gym file. The RecordSensor region
  # allows us to specify a file record stream as the input source via the
  # dataSource attribute.
  network.addRegion("sensor", "py.RecordSensor",
                    json.dumps({"verbosity": _VERBOSITY}))
  sensor = network.regions["sensor"].getSelf()
  # The RecordSensor needs to know how to encode the input values
  sensor.encoder = createEncoder()
  # Specify the dataSource as a file record stream instance
  sensor.dataSource = dataSource

  # Create the spatial pooler region
  SP_PARAMS["inputWidth"] = sensor.encoder.getWidth()
  network.addRegion("spatialPoolerRegion", "py.SPRegion", json.dumps(SP_PARAMS))

  # Link the SP region to the sensor input
  network.link("sensor", "spatialPoolerRegion", "UniformLink", "")
  network.link("sensor", "spatialPoolerRegion", "UniformLink", "",
               srcOutput="resetOut", destInput="resetIn")
  network.link("spatialPoolerRegion", "sensor", "UniformLink", "",
               srcOutput="spatialTopDownOut", destInput="spatialTopDownIn")
  network.link("spatialPoolerRegion", "sensor", "UniformLink", "",
               srcOutput="temporalTopDownOut", destInput="temporalTopDownIn")

  if enableTP:
    # Add the TMRegion on top of the SPRegion
    TM_PARAMS["temporalImp"] = temporalImp
    network.addRegion("temporalPoolerRegion", "py.TMRegion",
                      json.dumps(TM_PARAMS))

    network.link("spatialPoolerRegion", "temporalPoolerRegion", "UniformLink", "")
    network.link("temporalPoolerRegion", "spatialPoolerRegion", "UniformLink", "",
                 srcOutput="topDownOut", destInput="topDownIn")

  spatialPoolerRegion = network.regions["spatialPoolerRegion"]

  # Make sure learning is enabled
  spatialPoolerRegion.setParameter("learningMode", True)
  # We want temporal anomalies so disable anomalyMode in the SP. This mode is
  # used for computing anomalies in a non-temporal model.
  spatialPoolerRegion.setParameter("anomalyMode", False)

  if enableTP:
    temporalPoolerRegion = network.regions["temporalPoolerRegion"]

    # Enable topDownMode to get the predicted columns output
    temporalPoolerRegion.setParameter("topDownMode", True)
    # Make sure learning is enabled (this is the default)
    temporalPoolerRegion.setParameter("learningMode", True)
    # Enable inference mode so we get predictions
    temporalPoolerRegion.setParameter("inferenceMode", True)
    # Enable anomalyMode to compute the anomaly score. This actually doesn't work
    # now so doesn't matter. We instead compute the anomaly score based on
    # topDownOut (predicted columns) and SP bottomUpOut (active columns).
    temporalPoolerRegion.setParameter("anomalyMode", True)

  return network


def saveAndLoadNetwork(network):
  # Save network
  proto1 = NetworkProto_capnp.NetworkProto.new_message()
  network.write(proto1)

  with tempfile.TemporaryFile() as f:
    proto1.write(f)
    f.seek(0)

    # Load network
    proto2 = NetworkProto_capnp.NetworkProto.read(f)
    loadedNetwork = Network.read(proto2)

    # Set loaded network's datasource
    sensor = network.regions["sensor"].getSelf()
    loadedSensor = loadedNetwork.regions["sensor"].getSelf()
    loadedSensor.dataSource = sensor.dataSource

    # Initialize loaded network
    loadedNetwork.initialize()

  return loadedNetwork


def createAndRunNetwork(testRegionType, testOutputName,
                        checkpointMidway=False,
                        temporalImp=None):
    dataSource = FileRecordStream(streamID=_INPUT_FILE_PATH)

    if temporalImp is None:
      network = createNetwork(dataSource)
    else:
      network = createNetwork(dataSource,
                              enableTP=True,
                              temporalImp=temporalImp)
    network.initialize()

    results = []

    for i in xrange(_NUM_RECORDS):
      if checkpointMidway and i == (_NUM_RECORDS / 2):
        network = saveAndLoadNetwork(network)

      # Run the network for a single iteration
      network.run(1)

      testRegion = network.getRegionsByType(testRegionType)[0]
      output = testRegion.getOutputData(testOutputName).copy()
      results.append(output)

    return results
