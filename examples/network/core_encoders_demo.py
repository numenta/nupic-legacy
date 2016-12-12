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

import csv
import json
from datetime import datetime

from pkg_resources import resource_filename

from nupic.engine import Network
from nupic.encoders import DateEncoder


def createNetwork():
  network = Network()

  #
  # Sensors
  #

  # C++
  consumptionSensor = network.addRegion('consumptionSensor', 'ScalarSensor',
                                        json.dumps({'n': 120,
                                                    'w': 21,
                                                    'minValue': 0.0,
                                                    'maxValue': 100.0,
                                                    'clipInput': True}))

  # Python
  timestampSensor = network.addRegion("timestampSensor",
                                      'py.PluggableEncoderSensor', "")
  timestampSensor.getSelf().encoder = DateEncoder(timeOfDay=(21, 9.5),
                                                  name="timestamp_timeOfDay")

  #
  # Add a SPRegion, a region containing a spatial pooler
  #
  consumptionEncoderN = consumptionSensor.getParameter('n')
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
                      "boostStrength": 0.0,
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
  network.link("tm", "sp", "UniformLink", "", srcOutput="topDownOut",
               destInput="topDownIn")

  # Enable anomalyMode so the tm calculates anomaly scores
  network.regions['tm'].setParameter("anomalyMode", True)
  # Enable inference mode to be able to get predictions
  network.regions['tm'].setParameter("inferenceMode", True)

  return network

def runNetwork(network):
  consumptionSensor = network.regions['consumptionSensor']
  timestampSensor = network.regions['timestampSensor']
  tmRegion = network.regions['tm']

  filename = resource_filename("nupic.datafiles",
                               "extra/hotgym/rec-center-hourly.csv")
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

    anomalyScore = tmRegion.getOutputData('anomalyScore')[0]
    print "Consumption: %s, Anomaly score: %f" % (consumptionStr, anomalyScore)

if __name__ == "__main__":
  network = createNetwork()
  runNetwork(network)
