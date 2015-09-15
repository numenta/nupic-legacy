#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have an agreement
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

import json

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
    "maxBoost": 1.0,
}

# Default config fields for TPRegion
_TP_PARAMS = {
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

def createTemporalAnomaly(recordParams, spatialParams=_SP_PARAMS,
                          temporalParams=_TP_PARAMS,
                          verbosity=_VERBOSITY):
  """Generates a Network with connected RecordSensor, SP, TP, Anomaly regions.

  This function takes care of generating regions and the canonical links.
  The network has a sensor region reading data from a specified input and
  passing the encoded representation to an SPRegion.
  The SPRegion output is passed to a TPRegion.

  Note: this function returns a network that needs to be initialized. This
  allows the user to extend the network by adding further regions and
  connections.

  :param recordParams: a dict with parameters for creating RecordSensor region.
  :param spatialParams: a dict with parameters for creating SPRegion.
  :param temporalParams: a dict with parameters for creating TPRegion.
  :param verbosity: an integer representing how chatty the network will be.
  """
  inputFilePath= recordParams["inputFilePath"]
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
  network.addRegion("temporalPoolerRegion", "py.TPRegion",
                    json.dumps(temporalParams))

  network.link("spatialPoolerRegion", "temporalPoolerRegion", "UniformLink", "")
  network.link("temporalPoolerRegion", "spatialPoolerRegion", "UniformLink", "",
               srcOutput="topDownOut", destInput="topDownIn")

  # Add the AnomalyRegion on top of the TPRegion
  network.addRegion("anomalyRegion", "py.AnomalyRegion", json.dumps({}))

  network.link("spatialPoolerRegion", "anomalyRegion", "UniformLink", "",
               srcOutput="bottomUpOut", destInput="activeColumns")
  network.link("temporalPoolerRegion", "anomalyRegion", "UniformLink", "",
               srcOutput="topDownOut", destInput="predictedColumns")

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
  # Enable anomalyMode to compute the anomaly score. This actually doesn't work
  # now so doesn't matter. We instead compute the anomaly score based on
  # topDownOut (predicted columns) and SP bottomUpOut (active columns).
  temporalPoolerRegion.setParameter("anomalyMode", True)

  return network

