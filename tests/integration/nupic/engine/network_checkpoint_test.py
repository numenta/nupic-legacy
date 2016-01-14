#!/usr/bin/env python
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
import unittest

from pkg_resources import resource_filename

import numpy

from nupic.data.file_record_stream import FileRecordStream
from nupic.engine import Network
from nupic.encoders import MultiEncoder, ScalarEncoder, DateEncoder
from nupic.regions.RecordSensor import RecordSensor
from nupic.regions.SPRegion import SPRegion
from nupic.regions.TPRegion import TPRegion

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
_NUM_RECORDS = 2000

# Config field for SPRegion
SP_PARAMS = {
    "spVerbosity": _VERBOSITY,
    "spatialImp": "cpp",
    "globalInhibition": 1,
    "columnCount": 2048,
    # This must be set before creating the SPRegion
    "inputWidth": 0,
    "numActiveColumnsPerInhArea": 40,
    "seed": 1956,
    "potentialPct": 0.8,
    "synPermConnected": 0.1,
    "synPermActiveInc": 0.0001,
    "synPermInactiveDec": 0.0005,
    "maxBoost": 1.0,
}

# Config field for TPRegion
TP_PARAMS = {
    "verbosity": _VERBOSITY,
    "columnCount": 2048,
    "cellsPerColumn": 32,
    "inputWidth": 2048,
    "seed": 1960,
    "temporalImp": "tm_py",
    "newSynapseCount": 20,
    "maxSynapsesPerSegment": 32,
    "maxSegmentsPerCell": 128,
    "initialPerm": 0.21,
    "permanenceInc": 0.1,
    "permanenceDec": 0.1,
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



def createNetwork(dataSource, enableTP=False):
  """Create the Network instance.

  The network has a sensor region reading data from `dataSource` and passing
  the encoded representation to an SPRegion. The SPRegion output is passed to
  a TPRegion.

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
    # Add the TPRegion on top of the SPRegion
    network.addRegion("temporalPoolerRegion", "py.TPRegion",
                      json.dumps(TP_PARAMS))

    network.link("spatialPoolerRegion", "temporalPoolerRegion", "UniformLink", "")
    network.link("temporalPoolerRegion", "spatialPoolerRegion", "UniformLink", "",
                 srcOutput="topDownOut", destInput="topDownIn")

  spatialPoolerRegion = network.regions["spatialPoolerRegion"]

  # Make sure learning is enabled
  spatialPoolerRegion.setParameter("learningMode", True)
  # We want temporal anomalies so disable anomalyMode in the SP. This mode is
  # used for computing anomalies in a non-temporal model.
  spatialPoolerRegion.setParameter("anomalyMode", False)

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
                        enableTP=False):
    dataSource = FileRecordStream(streamID=_INPUT_FILE_PATH)

    network = createNetwork(dataSource, enableTP=enableTP)
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



class NetworkCheckpointTest(unittest.TestCase):

  # @unittest.skipUnless(
  #     capnp, "pycapnp is not installed, skipping serialization test.")
  @unittest.skip("")
  def testSensorRegion(self):
    results1 = createAndRunNetwork(RecordSensor, "dataOut")

    results2 = createAndRunNetwork(RecordSensor, "dataOut",
                                   checkpointMidway=True)

    self.compareArrayResults(results1, results2)


  # @unittest.skipUnless(
  #     capnp, "pycapnp is not installed, skipping serialization test.")
  @unittest.skip("")
  def testSPRegion(self):
    results1 = createAndRunNetwork(SPRegion, "bottomUpOut")

    results2 = createAndRunNetwork(SPRegion, "bottomUpOut",
                                   checkpointMidway=True)

    self.assertEqual(len(results1), len(results2))

    for i in xrange(len(results1)):
      result1 = list(results1[i].nonzero()[0])
      result2 = list(results2[i].nonzero()[0])
      self.assertEqual(result1, result2,
        "Row {0} not equal: {1} vs. {2}".format(i, result1, result2))


  @unittest.skipUnless(
      capnp, "pycapnp is not installed, skipping serialization test.")
  def testTPRegion(self):
    results1 = createAndRunNetwork(TPRegion, "bottomUpOut",
                                   enableTP=True)

    results2 = createAndRunNetwork(TPRegion, "bottomUpOut",
                                   enableTP=True,
                                   checkpointMidway=True)

    self.assertEqual(len(results1), len(results2))

    for i in xrange(len(results1)):
      result1 = list(results1[i].nonzero()[0])
      result2 = list(results2[i].nonzero()[0])
      self.assertEqual(result1, result2,
        "Row {0} not equal: {1} vs. {2}".format(i, result1, result2))


  def compareArrayResults(self, results1, results2):
    self.assertEqual(len(results1), len(results2))

    for i in xrange(len(results1)):
      result1 = list(results1[i].nonzero()[0])
      result2 = list(results2[i].nonzero()[0])

      self.assertEqual(result1, result2,
        "Row {0} not equal: {1} vs. {2}".format(i, result1, result2))



if __name__ == "__main__":
  unittest.main()
