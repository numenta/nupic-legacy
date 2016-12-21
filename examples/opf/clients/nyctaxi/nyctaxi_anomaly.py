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

"""
A simple client to create a HTM anomaly detection model for nyctaxi dataset.
The script prints out all records that have an abnormally high anomaly
score.
"""

import csv
import datetime
import logging

from pkg_resources import resource_filename

from nupic.frameworks.opf.modelfactory import ModelFactory

import model_params

_LOGGER = logging.getLogger(__name__)

_INPUT_DATA_FILE = resource_filename(
  "nupic.datafiles", "extra/nyctaxi/nyc_taxi.csv"
)
_OUTPUT_PATH = "anomaly_scores.csv"

_ANOMALY_THRESHOLD = 0.9

# minimum metric value of nyc_taxi.csv
_INPUT_MIN = 8

# maximum metric value of nyc_taxi.csv
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
