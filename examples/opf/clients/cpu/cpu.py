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
from matplotlib.pylab import draw, plot

from nupic.data.inference_shifter import InferenceShifter
from nupic.frameworks.opf.metrics import MetricSpec
from nupic.frameworks.opf.modelfactory import ModelFactory
from nupic.frameworks.opf.predictionmetricsmanager import MetricsManager

import model_params

SECONDS_PER_STEP = 2
WINDOW = 60

METRIC_SPECS = (
    # This metric computes average absolute error for 5-step predictions over
    # the last 60 steps
    MetricSpec(field='cpu', metric='multiStep',
               inferenceElement='multiStepBestPredictions',
               params={'errorMetric': 'aae', 'window': 60, 'steps': 5}),
)



def runCPU():
  """Poll CPU usage, make predictions, and plot the results. Runs forever."""
  # Create the model for predicting CPU usage.
  model = ModelFactory.create(model_params.MODEL_PARAMS)
  model.enableInference({'predictedField': 'cpu'})
  # Create a metrics manager for computing an error metric.
  metricsManager = MetricsManager(METRIC_SPECS, model.getFieldInfo(),
                                  model.getInferenceType())
  # The shifter will align prediction and actual values.
  shifter = InferenceShifter()
  # Keep the last WINDOW predicted and actual values for plotting.
  actHistory = deque([0.0] * WINDOW, maxlen=60)
  predHistory = deque([0.0] * WINDOW, maxlen=60)

  # Initialize the plot lines that we will update with each new record.
  actline, = plot(range(WINDOW), actHistory)
  predline, = plot(range(WINDOW), predHistory)
  # Set the y-axis range.
  actline.axes.set_ylim(0, 100)
  predline.axes.set_ylim(0, 100)

  while True:
    s = time.time()

    # Get the CPU usage.
    cpu = psutil.cpu_percent()

    # Run the input through the model and shift the resulting prediction.
    modelInput = {'cpu': cpu}
    result = shifter.shift(model.run(modelInput))

    # Compute an error metric (not currently used).
    result.metrics = metricsManager.update(result)

    # Update the trailing predicted and actual value deques.
    inference = result.inferences['multiStepBestPredictions'][5]
    if inference is not None:
      actHistory.append(result.rawInput['cpu'])
      predHistory.append(inference)

    # Redraw the chart with the new data.
    actline.set_ydata(actHistory)  # update the data
    predline.set_ydata(predHistory)  # update the data
    draw()

    # Make sure we wait a total of 2 seconds per iteration.
    time.sleep(SECONDS_PER_STEP - (time.time() - s))



if __name__ == "__main__":
  runCPU()
