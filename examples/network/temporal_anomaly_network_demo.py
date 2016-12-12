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
"""
Demonstrates common_networks using hotgym example. Outputs
network-demo2-output.csv, which should be identical to the csv
outputted by network-api-demo.py (which does not use common_networks).
"""

import csv
import os

from pkg_resources import resource_filename
from nupic.engine import common_networks

_INPUT_FILE_PATH = resource_filename(
  "nupic.datafiles", "extra/hotgym/rec-center-hourly.csv"
)
_OUTPUT_PATH = "network-demo2-output.csv"
_NUM_RECORDS = 2000



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
    anomalyScore = temporalPoolerRegion.getOutputData("rawAnomalyScore")[0]
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

  network = common_networks.createTemporalAnomaly(recordParams)

  outputPath = os.path.join(os.path.dirname(__file__), _OUTPUT_PATH)
  with open(outputPath, "w") as outputFile:
    writer = csv.writer(outputFile)
    print "Writing output to %s" % outputPath
    runNetwork(network, writer)
