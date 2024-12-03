# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""A simple client to create a CLA model for hotgym."""

import csv
import datetime
import logging

from pkg_resources import resource_filename

from nupic.frameworks.opf.metrics import MetricSpec
from nupic.frameworks.opf.model_factory import ModelFactory
from nupic.frameworks.opf.prediction_metrics_manager import MetricsManager

import model_params

_LOGGER = logging.getLogger(__name__)

_INPUT_FILE_PATH = resource_filename(
  "nupic.datafiles", "extra/hotgym/rec-center-hourly.csv"
)

_METRIC_SPECS = (
    MetricSpec(field='consumption', metric='multiStep',
               inferenceElement='multiStepBestPredictions',
               params={'errorMetric': 'aae', 'window': 1000, 'steps': 1}),
    MetricSpec(field='consumption', metric='trivial',
               inferenceElement='prediction',
               params={'errorMetric': 'aae', 'window': 1000, 'steps': 1}),
    MetricSpec(field='consumption', metric='multiStep',
               inferenceElement='multiStepBestPredictions',
               params={'errorMetric': 'altMAPE', 'window': 1000, 'steps': 1}),
    MetricSpec(field='consumption', metric='trivial',
               inferenceElement='prediction',
               params={'errorMetric': 'altMAPE', 'window': 1000, 'steps': 1}),
)

_NUM_RECORDS = 4000



def createModel():
  return ModelFactory.create(model_params.MODEL_PARAMS)



def runHotgym():
  model = createModel()
  model.enableInference({'predictedField': 'consumption'})
  metricsManager = MetricsManager(_METRIC_SPECS, model.getFieldInfo(),
                                  model.getInferenceType())
  with open (_INPUT_FILE_PATH) as fin:
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
      result.metrics = metricsManager.update(result)
      isLast = i == _NUM_RECORDS
      if i % 100 == 0 or isLast:
        _LOGGER.info("After %i records, 1-step altMAPE=%f", i,
                    result.metrics["multiStepBestPredictions:multiStep:"
                                   "errorMetric='altMAPE':steps=1:window=1000:"
                                   "field=consumption"])
      if isLast:
        break



if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  runHotgym()
