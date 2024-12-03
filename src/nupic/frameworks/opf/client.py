# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""Simple OPF client."""

from nupic.frameworks.opf.model_factory import ModelFactory
from nupic.frameworks.opf.opf_basic_environment import BasicDatasetReader
from nupic.frameworks.opf.prediction_metrics_manager import MetricsManager


class Client(object):
  """
  Simple OPF client.

  :param modelConfig: (dict) The model config.
  :param metricSpecs: A sequence of
         :class:`~nupic.frameworks.opf.metrics.MetricSpec` instances.
  :param sourceSpec: (string) Path to the source CSV file.
  :param sinkSpec: (string) Path to the sink CSV file.
"""

  def __init__(self, modelConfig, inferenceArgs, metricSpecs, sourceSpec,
               sinkSpec=None):
    self.model = ModelFactory.create(modelConfig)
    self.model.enableInference(inferenceArgs)
    self.metricsManager = MetricsManager(metricSpecs, self.model.getFieldInfo(),
                                         self.model.getInferenceType())
    self.sink = None
    if sinkSpec is not None:
      # TODO: make this work - sinkSpec not yet supported.
      raise NotImplementedError('The sinkSpec is not yet implemented.')
      #self.sink = BasicPredictionLogger(
      #    self.model.getFieldInfo(), sinkSpec, 'myOutput',
      #    self.model.getInferenceType())
      #self.sink.setLoggedMetrics(
      #    self.metricsManager.getMetricLabels())
    self.datasetReader = BasicDatasetReader(sourceSpec)

  def __iter__(self):
    return self

  def _processRecord(self, inputRecord):

    modelResult = self.model.run(inputRecord)
    modelResult.metrics = self.metricsManager.update(modelResult)
    if self.sink:
      self.sink.writeRecord(modelResult)
    return modelResult

  def next(self):
    record = self.datasetReader.next()
    return self._processRecord(record)

  def skipNRecords(self, n):
    for i in range(n):
      self.datasetReader.next()
  def nextTruthPrediction(self, field):
    record = self.datasetReader.next()
    prediction=self._processRecord(record).inferences['prediction'][0]
    truth=record[field]
    return truth, prediction


  def run(self):
    result = None
    while True:
      try:
        result = self.next()
        #print result
      except StopIteration:
        break
    return result
