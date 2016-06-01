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

import json
import numpy as np
import os
from pkg_resources import resource_stream



def getScalarMetricWithTimeOfDayAnomalyParams(metricData,
                                              minVal=None,
                                              maxVal=None,
                                              minResolution=None,
                                              tmImplementation = "cpp"):
  """
    Return a dict that can be used to create an anomaly model via OPF's
    ModelFactory.

    :param metricData: numpy array of metric data. Used to calculate minVal
      and maxVal if either is unspecified

    :param minVal: minimum value of metric. Used to set up encoders. If None
      will be derived from metricData.

    :param maxVal: maximum value of metric. Used to set up input encoders. If
      None will be derived from metricData

    :param minResolution: minimum resolution of metric. Used to set up
      encoders.  If None, will use default value of 0.001.

    :param tmImplementation: string specifying type of temporal memory implementation.
      Valid strings : {"cpp", "tm_cpp"}

    :returns: a dict containing "modelConfig" and "inferenceArgs" top-level
      properties. The value of the "modelConfig" property is for passing to
      the OPF `ModelFactory.create()` method as the `modelConfig` parameter. The
      "inferenceArgs" property is for passing to the resulting model's
      `enableInference()` method as the inferenceArgs parameter. NOTE: the
      timestamp field corresponds to input "c0"; the predicted field corresponds
      to input "c1".
    :rtype: dict

    Example:
      from nupic.frameworks.opf.modelfactory import ModelFactory
      from nupic.frameworks.opf.common_models.cluster_params import (
        getScalarMetricWithTimeOfDayAnomalyParams)

      params = getScalarMetricWithTimeOfDayAnomalyParams(
        metricData=[0],
        tmImplementation="cpp",
        minVal=0.0,
        maxVal=100.0)

      model = ModelFactory.create(modelConfig=params["modelConfig"])
      model.enableLearning()
      model.enableInference(params["inferenceArgs"])
  """
  # Default values
  if minResolution is None:
    minResolution = 0.001

  # Compute min and/or max from the data if not specified
  if minVal is None or maxVal is None:
    compMinVal, compMaxVal = _rangeGen(metricData)
    if minVal is None:
      minVal = compMinVal
    if maxVal is None:
      maxVal = compMaxVal

  # Handle the corner case where the incoming min and max are the same
  if minVal == maxVal:
    maxVal = minVal + 1

  # Load model parameters and update encoder params
  if (tmImplementation is "cpp"):
    paramFileRelativePath = os.path.join(
      "anomaly_params_random_encoder",
      "best_single_metric_anomaly_params_cpp.json")
  elif (tmImplementation is "tm_cpp"):
    paramFileRelativePath = os.path.join(
      "anomaly_params_random_encoder",
      "best_single_metric_anomaly_params_tm_cpp.json")
  else:
    raise ValueError("Invalid string for tmImplementation. Try cpp or tm_cpp")

  with resource_stream(__name__, paramFileRelativePath) as infile:
    paramSet = json.load(infile)

  _fixupRandomEncoderParams(paramSet, minVal, maxVal, minResolution)

  return paramSet


def _rangeGen(data, std=1):
  """
  Return reasonable min/max values to use given the data.
  """
  dataStd = np.std(data)
  if dataStd == 0:
    dataStd = 1
  minval = np.min(data) -  std * dataStd
  maxval = np.max(data) +  std * dataStd
  return minval, maxval



def _fixupRandomEncoderParams(params, minVal, maxVal, minResolution):
  """
  Given model params, figure out the correct parameters for the
  RandomDistributed encoder. Modifies params in place.
  """
  encodersDict = (
    params["modelConfig"]["modelParams"]["sensorParams"]["encoders"]
  )

  for encoder in encodersDict.itervalues():
    if encoder is not None:
      if encoder["type"] == "RandomDistributedScalarEncoder":
        resolution = max(minResolution,
                         (maxVal - minVal) / encoder.pop("numBuckets")
                        )
        encodersDict["c1"]["resolution"] = resolution
