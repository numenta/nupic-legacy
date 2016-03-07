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
from datetime import datetime

from pkg_resources import resource_filename

from nupic.data.file_record_stream import FileRecordStream
from nupic.engine import Network
from nupic.encoders import DateEncoder
from nupic.regions.SPRegion import SPRegion
from nupic.regions.TPRegion import TPRegion


def createNetwork():
    network = Network()

    #
    # Sensors
    #

    # C++
    network.addRegion('consumptionSensor', 'FloatSensor',
                      json.dumps({'type': 'ScalarEncoder',
                                  'n': 120,
                                  'w': 21,
                                  'minValue': 0.0,
                                  'maxValue': 100.0,
                                  'clipInput': True}))

    # Python

    # TODO: Instead of inserting an encoder into the ValueSensor, we should pass in
    # an encoder description and let it construct the encoder. This will match the
    # C++ pattern, it will fit well into a CLAModel, and the ValueSensor can be made
    # extensible to custom encoders. Then the CLAModel will support custom encoders.
    #
    # The barrier here: When you call network.addRegion, the nodeParams string is
    # parsed according to the region's spec, and then the region's __init__ method
    # is called with pre-parsed params. This means that every single Python
    # encoder's parameters would have to be listed in the ValueSensor's spec. This
    # would be ugly, and it would block a lot of custom encoder flexibility, since
    # the spec remains constant.
    #
    # If a RegionImpl constructor / __init__ method were called with the raw
    # nodeParams string, it would make this possible. Many regions would immediately
    # parse them according to their spec, calling the same parse function that's
    # currently called automatically on their behalf. Other regions would handle it
    # differently, maybe using per-encoder specs, or in the Python case just parsing
    # the JSON with Python's `json.loads`.

    timestampSensor = network.addRegion("timestampSensor", 'py.ValueSensor', "")
    timestampSensor.getSelf().encoder = DateEncoder(timeOfDay=(21, 9.5),
                                                    name="timestamp_timeOfDay")

    #
    # Add a SPRegion, a region containing a spatial pooler
    #

    # TODO: The SPRegion should not require an inputWidth parameter. It should infer
    # this width during initialization.
    consumptionEncoderN = 100
    timestampEncoderN = timestampSensor.getSelf().encoder.getWidth()
    inputWidth = consumptionEncoderN + timestampEncoderN

    network.addRegion("sp", "py.SPRegion",
                      json.dumps({
                          "spatialImp": "cpp",
                          "globalInhibition": 1,
                          "columnCount": 2048,
                          "inputWidth": inputWidth,
                          "numActiveColumnsPerInhArea": 40,
                          "seed": 1956,
                          "potentialPct": 0.8,
                          "synPermConnected": 0.1,
                          "synPermActiveInc": 0.0001,
                          "synPermInactiveDec": 0.0005,
                          "maxBoost": 1.0,
                      }))

    #
    # Input to the Spatial Pooler
    #
    network.link("consumptionSensor", "sp", "UniformLink", "")
    network.link("timestampSensor", "sp", "UniformLink", "")

    #
    # Add a TPRegion, a region containing a Temporal Memory
    #
    network.addRegion("tm", "py.TPRegion",
                      json.dumps({
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
                      }))

    network.link("sp", "tm", "UniformLink", "")
    network.link("tm", "sp", "UniformLink", "", srcOutput="topDownOut", destInput="topDownIn")

    # Add the AnomalyRegion on top of the TPRegion
    network.addRegion("anomalyRegion", "py.AnomalyRegion", json.dumps({}))

    network.link("sp", "anomalyRegion", "UniformLink", "",
                 srcOutput="bottomUpOut", destInput="activeColumns")
    network.link("tm", "anomalyRegion", "UniformLink", "",
                 srcOutput="topDownOut", destInput="predictedColumns")

    # Enable topDownMode to get the predicted columns output
    network.regions['tm'].setParameter("topDownMode", True)
    # Enable inference mode so we get predictions
    network.regions['tm'].setParameter("inferenceMode", True)

    return network

def runNetwork(network):
    consumptionSensor = network.regions['consumptionSensor']
    timestampSensor = network.regions['timestampSensor']
    anomalyRegion = network.regions['anomalyRegion']

    filename = resource_filename("nupic.datafiles", "extra/hotgym/rec-center-hourly.csv")
    csvReader = csv.reader(open(filename, 'r'))
    csvReader.next()
    csvReader.next()
    csvReader.next()
    for row in csvReader:
        timestampStr, consumptionStr = row

        # For core encoders, use the network API.
        consumptionSensor.setParameter('sensedValue', float(consumptionStr))

        # For Python encoders, circumvent the Network API.
        # The inputs are often crazy Python types, for example:
        t = datetime.strptime(timestampStr, "%m/%d/%y %H:%M")
        timestampSensor.getSelf().setSensedValue(t)

        network.run(1)

        anomalyScore = anomalyRegion.getOutputData('rawAnomalyScore')[0]
        print "Consumption: %s, Anomaly score: %f" % (consumptionStr, anomalyScore)

if __name__ == "__main__":
    network = createNetwork()
    runNetwork(network)
