# Copyright 2015 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""
Shows how to use the simple_server.py NuPIC server using data from the
hotgym dataset.

To run this demo, make sure simple server is running (on port 8888) using the command:
$ ./nupic/simple_server.py 8888
Then run this demo in another terminal window.
"""

import json
import logging
from optparse import OptionParser
import sys

import requests
from pkg_resources import resource_filename

from nupic.data.file_record_stream import FileRecordStream

import model_params



_LOGGER = logging.getLogger(__name__)

_INPUT_FILE_PATH = resource_filename(
  "nupic.datafiles", "extra/hotgym/rec-center-hourly.csv"
)

_NUM_RECORDS = 1000



def createModel(server, port):
  data = {"modelParams": model_params.MODEL_PARAMS,
          "predictedFieldName": "consumption"}
  requests.post("http://{server}:{port}/models/demo".format(server=server,
                                                            port=port),
                json.dumps(data))



def runDemo(server, port):
  createModel(server, port)

  with FileRecordStream(_INPUT_FILE_PATH) as f:
    headers = f.getFieldNames()

    for i in range(_NUM_RECORDS):
      record = f.getNextRecord()
      modelInput = dict(zip(headers, record))
      modelInput["consumption"] = float(modelInput["consumption"])
      modelInput["timestamp"] = modelInput["timestamp"].strftime("%m/%d/%y %H:%M")

      res = requests.post(
          "http://{server}:{port}/models/demo/run".format(server=server, port=port),
          json.dumps(modelInput))
      print "result = %s" % res.text

      isLast = i == _NUM_RECORDS
      if isLast:
        break



if __name__ == "__main__":
  parser = OptionParser()
  parser.add_option("-s", help="Server url (default: %default)",
                    dest="server", default="http://localhost")
  parser.add_option("-p", help="Server port (default: %default",
                    dest="port", default=8888)
  opt, arg = parser.parse_args(sys.argv[1:])

  runDemo(opt.server, opt.port)
