# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""A simple client to read CPU usage and predict it in real time."""

from collections import deque
import time

import psutil
import matplotlib.pyplot as plt

from nupic.data.inference_shifter import InferenceShifter
from nupic.frameworks.opf.model_factory import ModelFactory

import model_params

SECONDS_PER_STEP = 2
WINDOW = 60

# turn matplotlib interactive mode on (ion)
plt.ion()
fig = plt.figure()
# plot title, legend, etc
plt.title('CPU prediction example')
plt.xlabel('time [s]')
plt.ylabel('CPU usage [%]')

def runCPU():
  """Poll CPU usage, make predictions, and plot the results. Runs forever."""
  # Create the model for predicting CPU usage.
  model = ModelFactory.create(model_params.MODEL_PARAMS)
  model.enableInference({'predictedField': 'cpu'})
  # The shifter will align prediction and actual values.
  shifter = InferenceShifter()
  # Keep the last WINDOW predicted and actual values for plotting.
  actHistory = deque([0.0] * WINDOW, maxlen=60)
  predHistory = deque([0.0] * WINDOW, maxlen=60)

  # Initialize the plot lines that we will update with each new record.
  actline, = plt.plot(range(WINDOW), actHistory)
  predline, = plt.plot(range(WINDOW), predHistory)
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

    # Update the trailing predicted and actual value deques.
    inference = result.inferences['multiStepBestPredictions'][5]
    if inference is not None:
      actHistory.append(result.rawInput['cpu'])
      predHistory.append(inference)

    # Redraw the chart with the new data.
    actline.set_ydata(actHistory)  # update the data
    predline.set_ydata(predHistory)  # update the data
    plt.draw()
    plt.legend( ('actual','predicted') )

    # Make sure we wait a total of 2 seconds per iteration.
    try:
      plt.pause(SECONDS_PER_STEP)
    except:
      pass

if __name__ == "__main__":
  runCPU()
