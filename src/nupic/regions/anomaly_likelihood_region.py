# Copyright 2016 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""Implementation of region for computing anomaly likelihoods."""

from nupic.algorithms.anomaly_likelihood import AnomalyLikelihood
from nupic.bindings.regions.PyRegion import PyRegion

from nupic.serializable import Serializable


class AnomalyLikelihoodRegion(PyRegion, Serializable):
  """Region for computing the anomaly likelihoods."""


  @classmethod
  def getSpec(cls):
    return {
      "description": ("Region that computes anomaly likelihoods for \
                       temporal memory."),
      "singleNodeOnly": True,
      "inputs": {
        "rawAnomalyScore": {
          "description": "The anomaly score whose \
                          likelihood is to be computed",
          "dataType": "Real32",
          "count": 1,
          "required": True,
          "isDefaultInput": False
        },
        "metricValue": {
          "description": "The input metric value",
          "dataType": "Real32",
          "count": 1,
          "required": True,
          "isDefaultInput": False
        },
      },
      "outputs": {
        "anomalyLikelihood": {
          "description": "The resultant anomaly likelihood",
          "dataType": "Real32",
          "count": 1,
          "isDefaultOutput": True,
        },
      },
      "parameters": {
        "learningPeriod": {
          "description": "The number of iterations required for the\
                          algorithm to learn the basic patterns in the dataset\
                          and for the anomaly score to 'settle down'.",
          "dataType": "UInt32",
          "count": 1,
          "constraints": "",
          "defaultValue": 288,
          "accessMode": "ReadWrite"
        },
        "estimationSamples": {
          "description": "The number of reasonable anomaly scores\
                           required for the initial estimate of the\
                           Gaussian.",
          "dataType": "UInt32",
          "count": 1,
          "constraints": "",
          "defaultValue": 100,
          "accessMode": "ReadWrite"
        },
        "historicWindowSize": {
          "description": "Size of sliding window of historical data\
                          points to maintain for periodic reestimation\
                          of the Gaussian.",
          "dataType": "UInt32",
          "count": 1,
          "constraints": "",
          "defaultValue": 8640,
          "accessMode": "ReadWrite"
        },
        "reestimationPeriod": {
          "description": "How often we re-estimate the Gaussian\
                          distribution.",
          "dataType": "UInt32",
          "count": 1,
          "constraints": "",
          "defaultValue": 100,
          "accessMode": "ReadWrite"
        },
      },
      "commands": {
      },
    }


  def __init__(self,
               learningPeriod = 288,
               estimationSamples = 100,
               historicWindowSize = 8640,
               reestimationPeriod = 100):
    self.anomalyLikelihood = AnomalyLikelihood(
      learningPeriod = learningPeriod,
      estimationSamples = estimationSamples,
      historicWindowSize = historicWindowSize,
      reestimationPeriod = reestimationPeriod)

  def __eq__(self, other):
    return self.anomalyLikelihood == other.anomalyLikelihood


  def __ne__(self, other):
    return not self == other

  @classmethod
  def getSchema(cls):
    return AnomalyLikelihood.getSchema()

  @classmethod
  def read(cls, proto):
    anomalyLikelihoodRegion = object.__new__(cls)
    anomalyLikelihoodRegion.anomalyLikelihood = AnomalyLikelihood.read(proto)

    return anomalyLikelihoodRegion


  def write(self, proto):
    self.anomalyLikelihood.write(proto)


  def initialize(self):
    pass


  def compute(self, inputs, outputs):
    anomalyScore = inputs["rawAnomalyScore"][0]
    value = inputs["metricValue"][0]
    anomalyProbability = self.anomalyLikelihood.anomalyProbability(
      value, anomalyScore)
    outputs["anomalyLikelihood"][0] = anomalyProbability
