# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

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
