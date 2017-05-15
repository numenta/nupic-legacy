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
