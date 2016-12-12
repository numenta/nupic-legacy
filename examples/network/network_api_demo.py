# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015-2016, Numenta, Inc.  Unless you have an agreement
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

from pkg_resources import resource_filename

from nupic.data.file_record_stream import FileRecordStream
from nupic.engine import Network
from nupic.encoders import MultiEncoder, ScalarEncoder, DateEncoder
from nupic.regions.SPRegion import SPRegion
from nupic.regions.TPRegion import TPRegion

_VERBOSITY = 0  # how chatty the demo should be
_SEED = 1956  # the random seed used throughout
_INPUT_FILE_PATH = resource_filename(
  "nupic.datafiles", "extra/hotgym/rec-center-hourly.csv"
)
_OUTPUT_PATH = "network-demo-anomaly-output.csv"
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
    "boostStrength": 0.0,
}

# Config field for TPRegion
TP_PARAMS = {
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



def createEncoder():
  """Create the encoder instance for our test and return it."""
  consumption_encoder = ScalarEncoder(21, 0.0, 100.0, n=50, name="consumption",
      clipInput=True)
  time_encoder = DateEncoder(timeOfDay=(21, 9.5), name="timestamp_timeOfDay")

  encoder = MultiEncoder()
  encoder.addEncoder("consumption", consumption_encoder)
  encoder.addEncoder("timestamp", time_encoder)

  return encoder



def createNetwork(dataSource):
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

  # Add the TPRegion on top of the SPRegion
  network.addRegion("temporalPoolerRegion", "py.TPRegion",
                    json.dumps(TP_PARAMS))

  network.link("spatialPoolerRegion", "temporalPoolerRegion", "UniformLink", "")
  network.link("temporalPoolerRegion", "spatialPoolerRegion", "UniformLink", "",
               srcOutput="topDownOut", destInput="topDownIn")

  # Add the AnomalyLikelihoodRegion on top of the TPRegion
  network.addRegion("anomalyLikelihoodRegion", "py.AnomalyLikelihoodRegion",
    json.dumps({}))
  
  network.link("temporalPoolerRegion", "anomalyLikelihoodRegion", "UniformLink",
               "", srcOutput="anomalyScore", destInput="rawAnomalyScore")
  network.link("sensor", "anomalyLikelihoodRegion", "UniformLink", "",
               srcOutput="sourceOut", destInput="metricValue")
  

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
  # Enable anomalyMode to compute the anomaly score to be passed to the anomaly
  # likelihood region. 
  temporalPoolerRegion.setParameter("anomalyMode", True)

  return network


def runNetwork(network, writer):
  """Run the network and write output to writer.

  :param network: a Network instance to run
  :param writer: a csv.writer instance to write output to
  """
  sensorRegion = network.regions["sensor"]
  spatialPoolerRegion = network.regions["spatialPoolerRegion"]
  temporalPoolerRegion = network.regions["temporalPoolerRegion"]
  anomalyLikelihoodRegion = network.regions["anomalyLikelihoodRegion"]

  prevPredictedColumns = []

  for i in xrange(_NUM_RECORDS):
    # Run the network for a single iteration
    network.run(1)

    # Write out the anomaly likelihood along with the record number and consumption
    # value.
    consumption = sensorRegion.getOutputData("sourceOut")[0]
    anomalyScore = temporalPoolerRegion.getOutputData("anomalyScore")[0]
    anomalyLikelihood = anomalyLikelihoodRegion.getOutputData("anomalyLikelihood")[0]
    writer.writerow((i, consumption, anomalyScore, anomalyLikelihood))


if __name__ == "__main__":
  dataSource = FileRecordStream(streamID=_INPUT_FILE_PATH)

  network = createNetwork(dataSource)
  network.initialize()

  spRegion = network.getRegionsByType(SPRegion)[0]
  sp = spRegion.getSelf().getAlgorithmInstance()
  print "spatial pooler region inputs: {0}".format(spRegion.getInputNames())
  print "spatial pooler region outputs: {0}".format(spRegion.getOutputNames())
  print "# spatial pooler columns: {0}".format(sp.getNumColumns())
  print

  tmRegion = network.getRegionsByType(TPRegion)[0]
  tm = tmRegion.getSelf().getAlgorithmInstance()
  print "temporal memory region inputs: {0}".format(tmRegion.getInputNames())
  print "temporal memory region outputs: {0}".format(tmRegion.getOutputNames())
  print "# temporal memory columns: {0}".format(tm.numberOfCols)
  print

  outputPath = os.path.join(os.path.dirname(__file__), _OUTPUT_PATH)
  with open(outputPath, "w") as outputFile:
    writer = csv.writer(outputFile)
    print "Writing output to %s" % outputPath
    runNetwork(network, writer)
