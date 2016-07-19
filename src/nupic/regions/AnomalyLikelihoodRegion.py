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

import numpy

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
            "value": {
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
        },
        "commands": {
        },
    }


  def __init__(self, *args, **kwargs):
    self.anomalyLikelihood = AnomalyLikelihood()


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
    value = inputs["value"][0]
    anomalyProbability = self.anomalyLikelihood.anomalyProbability(
      value, anomalyScore)
    outputs["anomalyLikelihood"][0] = anomalyProbability
