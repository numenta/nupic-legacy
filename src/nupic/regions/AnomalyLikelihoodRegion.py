# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2016, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
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

"""Implementation of region for computing anomaly likelihoods."""

from nupic.algorithms.anomaly_likelihood import AnomalyLikelihood
from nupic.bindings.regions.PyRegion import PyRegion


class AnomalyLikelihoodRegion(PyRegion):
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
  def read(cls, proto):
    anomalyLikelihoodRegion = object.__new__(cls)
    anomalyLikelihoodRegion.anomalyLikelihood = AnomalyLikelihood.read(proto)

    return anomalyLikelihoodRegion


  def write(self, proto):
    self.anomalyLikelihood.write(proto)


  def initialize(self, inputs, outputs):
    pass


  def compute(self, inputs, outputs):
    anomalyScore = inputs["rawAnomalyScore"][0]
    value = inputs["metricValue"][0]
    anomalyProbability = self.anomalyLikelihood.anomalyProbability(
      value, anomalyScore)
    outputs["anomalyLikelihood"][0] = anomalyProbability
