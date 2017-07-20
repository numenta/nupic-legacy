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
"""
Provides two classes with the same signature for writing data out of NuPIC
models.
(This is a component of the One Hot Gym Prediction Tutorial.)
"""
import csv
from collections import deque
from abc import ABCMeta, abstractmethod
# Try to import matplotlib, but we don't have to.
try:
  import matplotlib
  matplotlib.use('TKAgg')
  import matplotlib.pyplot as plt
  import matplotlib.gridspec as gridspec
  from matplotlib.dates import date2num
except ImportError:
  pass

WINDOW = 100


class NuPICOutput(object):

  __metaclass__ = ABCMeta


  def __init__(self, names, showAnomalyScore=False):
    self.names = names
    self.showAnomalyScore = showAnomalyScore


  @abstractmethod
  def write(self, timestamps, actualValues, predictedValues,
            predictionStep=1):
    pass


  @abstractmethod
  def close(self):
    pass



class NuPICFileOutput(NuPICOutput):


  def __init__(self, *args, **kwargs):
    super(NuPICFileOutput, self).__init__(*args, **kwargs)
    self.outputFiles = []
    self.outputWriters = []
    self.lineCounts = []
    headerRow = ['timestamp', 'kw_energy_consumption', 'prediction']
    for name in self.names:
      self.lineCounts.append(0)
      outputFileName = "%s_out.csv" % name
      print "Preparing to output %s data to %s" % (name, outputFileName)
      outputFile = open(outputFileName, "w")
      self.outputFiles.append(outputFile)
      outputWriter = csv.writer(outputFile)
      self.outputWriters.append(outputWriter)
      outputWriter.writerow(headerRow)



  def write(self, timestamps, actualValues, predictedValues,
            predictionStep=1):

    assert len(timestamps) == len(actualValues) == len(predictedValues)

    for index in range(len(self.names)):
      timestamp = timestamps[index]
      actual = actualValues[index]
      prediction = predictedValues[index]
      writer = self.outputWriters[index]

      if timestamp is not None:
        outputRow = [timestamp, actual, prediction]
        writer.writerow(outputRow)
        self.lineCounts[index] += 1



  def close(self):
    for index, name in enumerate(self.names):
      self.outputFiles[index].close()
      print "Done. Wrote %i data lines to %s." % (self.lineCounts[index], name)



class NuPICPlotOutput(NuPICOutput):


  def __init__(self, *args, **kwargs):
    super(NuPICPlotOutput, self).__init__(*args, **kwargs)
    # Turn matplotlib interactive mode on.
    plt.ion()
    self.dates = []
    self.convertedDates = []
    self.actualValues = []
    self.predictedValues = []
    self.actualLines = []
    self.predictedLines = []
    self.linesInitialized = False
    self.graphs = []
    plotCount = len(self.names)
    plotHeight = max(plotCount * 3, 6)
    fig = plt.figure(figsize=(14, plotHeight))
    gs = gridspec.GridSpec(plotCount, 1)
    for index in range(len(self.names)):
      self.graphs.append(fig.add_subplot(gs[index, 0]))
      plt.title(self.names[index])
      plt.ylabel('KW Energy Consumption')
      plt.xlabel('Date')
    plt.tight_layout()



  def initializeLines(self, timestamps):
    for index in range(len(self.names)):
      print "initializing %s" % self.names[index]
      # graph = self.graphs[index]
      self.dates.append(deque([timestamps[index]] * WINDOW, maxlen=WINDOW))
      self.convertedDates.append(deque(
        [date2num(date) for date in self.dates[index]], maxlen=WINDOW
      ))
      self.actualValues.append(deque([0.0] * WINDOW, maxlen=WINDOW))
      self.predictedValues.append(deque([0.0] * WINDOW, maxlen=WINDOW))

      actualPlot, = self.graphs[index].plot(
        self.dates[index], self.actualValues[index]
      )
      self.actualLines.append(actualPlot)
      predictedPlot, = self.graphs[index].plot(
        self.dates[index], self.predictedValues[index]
      )
      self.predictedLines.append(predictedPlot)
    self.linesInitialized = True



  def write(self, timestamps, actualValues, predictedValues,
            predictionStep=1):

    assert len(timestamps) == len(actualValues) == len(predictedValues)

    # We need the first timestamp to initialize the lines at the right X value,
    # so do that check first.
    if not self.linesInitialized:
      self.initializeLines(timestamps)

    for index in range(len(self.names)):
      self.dates[index].append(timestamps[index])
      self.convertedDates[index].append(date2num(timestamps[index]))
      self.actualValues[index].append(actualValues[index])
      self.predictedValues[index].append(predictedValues[index])

      # Update data
      self.actualLines[index].set_xdata(self.convertedDates[index])
      self.actualLines[index].set_ydata(self.actualValues[index])
      self.predictedLines[index].set_xdata(self.convertedDates[index])
      self.predictedLines[index].set_ydata(self.predictedValues[index])

      self.graphs[index].relim()
      self.graphs[index].autoscale_view(True, True, True)

    plt.draw()
    plt.legend(('actual','predicted'), loc=3)


  def refreshGUI(self):
      """Give plot a pause, so data is drawn and GUI's event loop can run.
      """
      plt.pause(0.0001)


  def close(self):
    plt.ioff()
    plt.show()



NuPICOutput.register(NuPICFileOutput)
NuPICOutput.register(NuPICPlotOutput)
