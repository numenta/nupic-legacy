# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have purchased from
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

"""Region for computing the anomaly score."""

import numpy

from nupic.algorithms import anomaly
from nupic.bindings.regions.PyRegion import PyRegion

from nupic.serializable import Serializable


class AnomalyRegion(PyRegion, Serializable):
  """Region for computing the anomaly score."""


  @classmethod
  def getSpec(cls):
    return {
        "description": ("Region that computes anomaly scores from temporal "
                        "memory."),
        "singleNodeOnly": True,
        "inputs": {
            "activeColumns": {
                "description": "The currently active columns.",
                "regionLevel": True,
                "dataType": "Real32",
                "count": 0,
                "required": True,
                "isDefaultInput": False,
                "requireSplitterMap": False,
            },
            "predictedColumns": {
                "description": "The currently predicted columns.",
                "regionLevel": True,
                "dataType": "Real32",
                "count": 0,
                "required": True,
                "isDefaultInput": False,
                "requireSplitterMap": False,
            },
        },
        "outputs": {
            "rawAnomalyScore": {
                "description": "The raw anomaly score.",
                "dataType": "Real32",
                "count": 1,
                "regionLevel": True,
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
    anomalyRegion = object.__new__(cls)
    anomalyRegion.prevPredictedColumns = numpy.array(proto.prevPredictedColumns)
    return anomalyRegion


  def write(self, proto):
    proto.prevPredictedColumns = self.prevPredictedColumns.tolist()


  def initialize(self):
    pass


  def compute(self, inputs, outputs):
    activeColumns = inputs["activeColumns"].nonzero()[0]

    rawAnomalyScore = anomaly.computeRawAnomalyScore(
        activeColumns, self.prevPredictedColumns)

    self.prevPredictedColumns = inputs["predictedColumns"].nonzero()[0]

    outputs["rawAnomalyScore"][0] = rawAnomalyScore
