#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

"""
Shows how to use the simple_server.py NuPIC server using data from the
hotgym dataset.

To run this demo, make sure simple server is running (on port 8888) using the command:
$ ./nupic/simple_server.py 8888
Then run this demo in another terminal window.
"""

import csv
import json
import logging

import requests
from pkg_resources import resource_filename

from nupic.data.file_record_stream import FileRecordStream
from nupic.frameworks.opf.metrics import MetricSpec

import model_params



_LOGGER = logging.getLogger(__name__)

_INPUT_FILE_PATH = resource_filename(
  "nupic.datafiles", "extra/hotgym/rec-center-hourly.csv"
)

_NUM_RECORDS = 1000



def createModel():
  data = {"modelParams": model_params.MODEL_PARAMS,
          "predictedFieldName": "consumption"}
  requests.post("http://localhost:8888/models/demo",
                json.dumps(data))



def runDemo():
  createModel()

  with FileRecordStream(_INPUT_FILE_PATH) as f:
    headers = f.getFieldNames()

    for i in range(_NUM_RECORDS):
      record = f.getNextRecord()
      modelInput = dict(zip(headers, record))
      modelInput["consumption"] = float(modelInput["consumption"])
      modelInput["timestamp"] = modelInput["timestamp"].strftime("%m/%d/%y %H:%M")

      res = requests.post("http://localhost:8888/models/demo/run",
                          json.dumps(modelInput))
      print "result = %s" % res.text

      isLast = i == _NUM_RECORDS
      if isLast:
        break



if __name__ == "__main__":
  runDemo()
