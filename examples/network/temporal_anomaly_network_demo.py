# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015-2017, Numenta, Inc.  Unless you have an agreement
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

import csv
import json
import os
from pkg_resources import resource_filename

from nupic.data.file_record_stream import FileRecordStream
from nupic.engine import Network
from nupic.encoders import MultiEncoder, ScalarEncoder, DateEncoder

_VERBOSITY = 0

# Default config fields for SPRegion
_SP_PARAMS = {
    "spVerbosity": _VERBOSITY,
    "spatialImp": "cpp",
    "globalInhibition": 1,
    "columnCount": 2048,
    "inputWidth": 0,
    "numActiveColumnsPerInhArea": 40,
    "seed": 1956,
    "potentialPct": 0.8,
    "synPermConnected": 0.1,
    "synPermActiveInc": 0.0001,
    "synPermInactiveDec": 0.0005,
    "boostStrength": 0.0,
}

# Default config fields for TPRegion
_TM_PARAMS = {
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
    "globalDecay": 0.0,
    "maxAge": 0,
    "minThreshold": 9,
    "activationThreshold": 12,
    "outputType": "normal",
    "pamLength": 3,
}

_INPUT_FILE_PATH = resource_filename(
  "nupic.datafiles", "extra/hotgym/rec-center-hourly.csv"
)
_OUTPUT_PATH = "network-demo2-output.csv"
_NUM_RECORDS = 2000



def createTemporalAnomaly(recordParams, spatialParams=_SP_PARAMS,
                          temporalParams=_TM_PARAMS,
                          verbosity=_VERBOSITY):


  """Generates a Network with connected RecordSensor, SP, TM.

  This function takes care of generating regions and the canonical links.
  The network has a sensor region reading data from a specified input and
  passing the encoded representation to an SPRegion.
  The SPRegion output is passed to a TMRegion.

  Note: this function returns a network that needs to be initialized. This
  allows the user to extend the network by adding further regions and
  connections.

  :param recordParams: a dict with parameters for creating RecordSensor region.
  :param spatialParams: a dict with parameters for creating SPRegion.
  :param temporalParams: a dict with parameters for creating TMRegion.
  :param verbosity: an integer representing how chatty the network will be.
  """
  inputFilePath = recordParams["inputFilePath"]
  scalarEncoderArgs = recordParams["scalarEncoderArgs"]
  dateEncoderArgs = recordParams["dateEncoderArgs"]

  scalarEncoder = ScalarEncoder(**scalarEncoderArgs)
  dateEncoder = DateEncoder(**dateEncoderArgs)

  encoder = MultiEncoder()
  encoder.addEncoder(scalarEncoderArgs["name"], scalarEncoder)
  encoder.addEncoder(dateEncoderArgs["name"], dateEncoder)

  network = Network()

  network.addRegion("sensor", "py.RecordSensor",
                    json.dumps({"verbosity": verbosity}))

  sensor = network.regions["sensor"].getSelf()
  sensor.encoder = encoder
  sensor.dataSource = FileRecordStream(streamID=inputFilePath)

  # Create the spatial pooler region
  spatialParams["inputWidth"] = sensor.encoder.getWidth()
  network.addRegion("spatialPoolerRegion", "py.SPRegion",
                    json.dumps(spatialParams))

  # Link the SP region to the sensor input
  network.link("sensor", "spatialPoolerRegion", "UniformLink", "")
  network.link("sensor", "spatialPoolerRegion", "UniformLink", "",
               srcOutput="resetOut", destInput="resetIn")
  network.link("spatialPoolerRegion", "sensor", "UniformLink", "",
               srcOutput="spatialTopDownOut", destInput="spatialTopDownIn")
  network.link("spatialPoolerRegion", "sensor", "UniformLink", "",
               srcOutput="temporalTopDownOut", destInput="temporalTopDownIn")

  # Add the TPRegion on top of the SPRegion
  network.addRegion("temporalPoolerRegion", "py.TMRegion",
                    json.dumps(temporalParams))

  network.link("spatialPoolerRegion", "temporalPoolerRegion", "UniformLink", "")
  network.link("temporalPoolerRegion", "spatialPoolerRegion", "UniformLink", "",
               srcOutput="topDownOut", destInput="topDownIn")

  spatialPoolerRegion = network.regions["spatialPoolerRegion"]

  # Make sure learning is enabled
  spatialPoolerRegion.setParameter("learningMode", True)
  # We want temporal anomalies so disable anomalyMode in the SP. This mode is
  # used for computing anomalies in a non-temporal model.
  spatialPoolerRegion.setParameter("anomalyMode", False)

  temporalPoolerRegion = network.regions["temporalPoolerRegion"]

  # Enable topDownMode to get the predicted columns output
  temporalPoolerRegion.setParameter("topDownMode", True)
  # Make sure learning is enabled (this is the default)
  temporalPoolerRegion.setParameter("learningMode", True)
  # Enable inference mode so we get predictions
  temporalPoolerRegion.setParameter("inferenceMode", True)
  # Enable anomalyMode to compute the anomaly score.
  temporalPoolerRegion.setParameter("anomalyMode", True)

  return network



def runNetwork(network, writer):
  """Run the network and write output to writer.

  :param network: a Network instance to run
  :param writer: a csv.writer instance to write output to
  """
  sensorRegion = network.regions["sensor"]
  temporalPoolerRegion = network.regions["temporalPoolerRegion"]

  for i in xrange(_NUM_RECORDS):
    # Run the network for a single iteration
    network.run(1)

    # Write out the anomaly score along with the record number and consumption
    # value.
    anomalyScore = temporalPoolerRegion.getOutputData("anomalyScore")[0]
    consumption = sensorRegion.getOutputData("sourceOut")[0]
    writer.writerow((i, consumption, anomalyScore))


if __name__ == "__main__":
  inputFilePath = resource_filename(
    "nupic.datafiles", "extra/hotgym/rec-center-hourly.csv"
  )

  scalarEncoderArgs = {
    "w": 21,
    "minval": 0.0,
    "maxval": 100.0,
    "periodic": False,
    "n": 50,
    "radius": 0,
    "resolution": 0,
    "name": "consumption",
    "verbosity": 0,
    "clipInput": True,
    "forced": False,
  }

  dateEncoderArgs = {
    "season": 0,
    "dayOfWeek": 0,
    "weekend": 0,
    "holiday": 0,
    "timeOfDay": (21, 9.5),
    "customDays": 0,
    "name": "timestamp",
    "forced": True
  }

  recordParams = {
    "inputFilePath": _INPUT_FILE_PATH,
    "scalarEncoderArgs": scalarEncoderArgs,
    "dateEncoderArgs": dateEncoderArgs,
  }

  network = createTemporalAnomaly(recordParams)

  outputPath = os.path.join(os.path.dirname(__file__), _OUTPUT_PATH)
  with open(outputPath, "w") as outputFile:
    writer = csv.writer(outputFile)
    print "Writing output to %s" % outputPath
    runNetwork(network, writer)
