# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
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
A simple client to create a HTM anomaly detection model for hotgym.
The script prints out all records that have an abnormally high anomaly
score.
"""

import csv
import datetime
import logging

from pkg_resources import resource_filename

from nupic.frameworks.opf.model_factory import ModelFactory

import model_params

_LOGGER = logging.getLogger(__name__)

_INPUT_DATA_FILE = resource_filename(
  "nupic.datafiles", "extra/hotgym/rec-center-hourly.csv"
)
_OUTPUT_PATH = "anomaly_scores.csv"

_ANOMALY_THRESHOLD = 0.9


def createModel():
  return ModelFactory.create(model_params.MODEL_PARAMS)


def runHotgymAnomaly():
  model = createModel()
  model.enableInference({'predictedField': 'consumption'})
  with open (_INPUT_DATA_FILE) as fin:
    reader = csv.reader(fin)
    csvWriter = csv.writer(open(_OUTPUT_PATH,"wb"))
    csvWriter.writerow(["timestamp", "consumption", "anomaly_score"])
    headers = reader.next()
    reader.next()
    reader.next()
    for i, record in enumerate(reader, start=1):
      modelInput = dict(zip(headers, record))
      modelInput["consumption"] = float(modelInput["consumption"])
      modelInput["timestamp"] = datetime.datetime.strptime(
          modelInput["timestamp"], "%m/%d/%y %H:%M")
      result = model.run(modelInput)
      anomalyScore = result.inferences['anomalyScore']
      csvWriter.writerow([modelInput["timestamp"], modelInput["consumption"],
                          anomalyScore])
      if anomalyScore > _ANOMALY_THRESHOLD:
        _LOGGER.info("Anomaly detected at [%s]. Anomaly score: %f.",
                      result.rawInput["timestamp"], anomalyScore)

  print "Anomaly scores have been written to",_OUTPUT_PATH

if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  runHotgymAnomaly()
