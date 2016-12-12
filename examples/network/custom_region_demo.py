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

import copy
import csv
import json
import os
import sys

from pkg_resources import resource_filename

from nupic.data.file_record_stream import FileRecordStream
from nupic.encoders import MultiEncoder, ScalarEncoder, DateEncoder
from nupic.engine import Network

_VERBOSITY = 0  # how chatty the demo should be
_SEED = 1956  # the random seed used throughout
_INPUT_FILE_PATH = resource_filename(
  "nupic.datafiles", "extra/hotgym/rec-center-hourly.csv"
)
_OUTPUT_PATH = "network-demo-output.csv"
_NUM_RECORDS = 2000


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
  the encoded representation to an Identity Region.

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

  # CUSTOM REGION
  # Add path to custom region to PYTHONPATH
  # NOTE: Before using a custom region, please modify your PYTHONPATH
  # export PYTHONPATH="<path to custom region module>:$PYTHONPATH"
  # In this demo, we have modified it using sys.path.append since we need it to
  # have an effect on this program.
  sys.path.append(os.path.dirname(os.path.abspath(__file__)))
  
  from custom_region.identity_region import IdentityRegion

  # Add custom region class to the network
  Network.registerRegion(IdentityRegion)

  # Create a custom region
  network.addRegion("identityRegion", "py.IdentityRegion",
                    json.dumps({
                      "dataWidth": sensor.encoder.getWidth(),
                    }))

  # Link the Identity region to the sensor output
  network.link("sensor", "identityRegion", "UniformLink", "")

  network.initialize()

  return network


def runNetwork(network, writer):
  """Run the network and write output to writer.

  :param network: a Network instance to run
  :param writer: a csv.writer instance to write output to
  """
  identityRegion = network.regions["identityRegion"]

  for i in xrange(_NUM_RECORDS):
    # Run the network for a single iteration
    network.run(1)

    # Write out the record number and encoding
    encoding = identityRegion.getOutputData("out")
    writer.writerow((i, encoding))



if __name__ == "__main__":
  dataSource = FileRecordStream(streamID=_INPUT_FILE_PATH)

  network = createNetwork(dataSource)
  outputPath = os.path.join(os.path.dirname(__file__), _OUTPUT_PATH)
  with open(outputPath, "w") as outputFile:
    writer = csv.writer(outputFile)
    print "Writing output to %s" % outputPath
    runNetwork(network, writer)
