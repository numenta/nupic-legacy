# Copyright 2016 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""
A simple client to create a HTM anomaly detection model for nyctaxi dataset.
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
  "nupic.datafiles", "extra/nycTaxi/nycTaxi.csv"
)
_OUTPUT_PATH = "anomaly_scores.csv"

_ANOMALY_THRESHOLD = 0.9

# minimum metric value of nycTaxi.csv
_INPUT_MIN = 8

# maximum metric value of nycTaxi.csv
_INPUT_MAX = 39197


def _setRandomEncoderResolution(minResolution=0.001):
  """
  Given model params, figure out the correct resolution for the
  RandomDistributed encoder. Modifies params in place.
  """
  encoder = (
    model_params.MODEL_PARAMS["modelParams"]["sensorParams"]["encoders"]["value"]
  )

  if encoder["type"] == "RandomDistributedScalarEncoder":
    rangePadding = abs(_INPUT_MAX - _INPUT_MIN) * 0.2
    minValue = _INPUT_MIN - rangePadding
    maxValue = _INPUT_MAX + rangePadding
    resolution = max(minResolution,
                     (maxValue - minValue) / encoder.pop("numBuckets")
                    )
    encoder["resolution"] = resolution


def createModel():
  _setRandomEncoderResolution()
  return ModelFactory.create(model_params.MODEL_PARAMS)


def runNYCTaxiAnomaly():
  model = createModel()
  model.enableInference({'predictedField': 'value'})
  with open (_INPUT_DATA_FILE) as fin:
    reader = csv.reader(fin)
    csvWriter = csv.writer(open(_OUTPUT_PATH,"wb"))
    csvWriter.writerow(["timestamp", "value", "anomaly_score"])
    headers = reader.next()
    for i, record in enumerate(reader, start=1):
      modelInput = dict(zip(headers, record))
      modelInput["value"] = float(modelInput["value"])
      modelInput["timestamp"] = datetime.datetime.strptime(
          modelInput["timestamp"], "%Y-%m-%d %H:%M:%S")
      result = model.run(modelInput)
      anomalyScore = result.inferences['anomalyScore']
      csvWriter.writerow([modelInput["timestamp"], modelInput["value"],
                          "%.3f" % anomalyScore])
      if anomalyScore > _ANOMALY_THRESHOLD:
        _LOGGER.info("Anomaly detected at [%s]. Anomaly score: %f.",
                      result.rawInput["timestamp"], anomalyScore)

  print "Anomaly scores have been written to",_OUTPUT_PATH

if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  runNYCTaxiAnomaly()
