#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
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
A simple client to create a CLA anomaly detection model for hotgym.
The script prints out all records that have an abnoramlly high anomaly
score.
"""

import csv
import datetime
import logging

from nupic.data.datasethelpers import findDataset
from nupic.frameworks.opf.modelfactory import ModelFactory
from nupic.frameworks.opf.predictionmetricsmanager import MetricsManager

import model_params

_LOGGER = logging.getLogger(__name__)

_DATA_PATH = "extra/hotgym/rec-center-hourly.csv"

_ANOMALY_THRESHOLD = 0.8


def createModel():
  return ModelFactory.create(model_params.MODEL_PARAMS)


def runHotgymAnomaly():
  model = createModel()
  model.enableInference({'predictedField': 'consumption'})
  with open (findDataset(_DATA_PATH)) as fin:
    reader = csv.reader(fin)
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
      if anomalyScore > _ANOMALY_THRESHOLD:
        _LOGGER.info("Anomaly detected at [%s]. Anomaly score: %f.",
                      result.rawInput["timestamp"], anomalyScore)



if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  runHotgymAnomaly()
