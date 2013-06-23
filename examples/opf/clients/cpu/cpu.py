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

"""A simple client to read CPU usage and predict it in real time."""

from collections import deque
import time

import psutil
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.pylab import *

from nupic.data.inference_shifter import InferenceShifter
from nupic.frameworks.opf.metrics import MetricSpec
from nupic.frameworks.opf.modelfactory import ModelFactory
from nupic.frameworks.opf.predictionmetricsmanager import MetricsManager

import model_params

METRIC_SPECS = (
    MetricSpec(field='cpu', metric='multiStep',
               inferenceElement='multiStepBestPredictions',
               params={'errorMetric': 'aae', 'window': 60, 'steps': 5}),
)



def createModel():
  return ModelFactory.create(model_params.MODEL_PARAMS)



def runCPU():
  ion()
  model = createModel()
  model.enableInference({'predictedField': 'cpu'})
  metricsManager = MetricsManager(METRIC_SPECS, model.getFieldInfo(),
                                  model.getInferenceType())
  shifter = InferenceShifter()
  actHistory = deque([0.0] * 60, maxlen=60)
  predHistory = deque([0.0] * 60, maxlen=60)

  actline, = plot(range(60), actHistory)
  predline, = plot(range(60), predHistory)
  actline.axes.set_ylim(0, 100)
  predline.axes.set_ylim(0, 100)

  while True:
    s = time.time()
    cpu = psutil.cpu_percent()
    modelInput = {'cpu': cpu}
    result = shifter.shift(model.run(modelInput))
    result.metrics = metricsManager.update(result)
    inference = result.inferences['multiStepBestPredictions'][5]
    if inference is not None:
      actHistory.append(result.rawInput['cpu'])
      predHistory.append(inference)

    actline.set_ydata(actHistory)  # update the data
    predline.set_ydata(predHistory)  # update the data
    draw()

    time.sleep(2.0 - (time.time() - s))



if __name__ == "__main__":
  runCPU()
