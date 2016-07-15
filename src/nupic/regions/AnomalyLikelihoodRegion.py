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
                "description": "The anomaly likelihood",
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
    self.prevPredictedColumns = numpy.zeros([], dtype="float32")
    self.anomalyLikelihood = AnomalyLikelihood()


  def __eq__(self, other):
    for k, v1 in self.__dict__.iteritems():
      if not k in other.__dict__:
        return False
      v2 = getattr(other, k)
      if isinstance(v1, numpy.ndarray):
        if v1.dtype != v2.dtype:
          return False
        if not numpy.isclose(v1, v2).all():
          return False
      else:
        if type(v1) != type(v2):
          return False
        if v1 != v2:
          return False
    return True


  def __ne__(self, other):
    return not self == other


  @classmethod
  def read(cls, proto):
    anomalyLikelihoodRegion = object.__new__(cls)
    anomalyLikelihoodRegion.prevPredictedColumns = numpy.array(
      proto.prevPredictedColumns)
    return anomalyLikelihoodRegion


  def write(self, proto):
    proto.prevPredictedColumns = self.prevPredictedColumns.tolist()
    proto.state = "hello"

  def initialize(self, inputs, outputs):
    pass


  def compute(self, inputs, outputs):
    anomalyScore = inputs["rawAnomalyScore"]
    value = inputs["value"]
    anomalyProbability = self.anomalyLikelihood.anomalyProbability(
      value, anomalyScore)

    outputs["anomalyLikelihood"][0] = anomalyProbability

