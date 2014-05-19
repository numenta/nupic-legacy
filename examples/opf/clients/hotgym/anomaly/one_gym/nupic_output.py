# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
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
"""
Provides two classes with the same signature for writing data out of NuPIC
models.
(This is a component of the One Hot Gym Prediction Tutorial.)
"""
import csv
from collections import deque
from abc import ABCMeta, abstractmethod
import anomaly_likelihood
# Try to import matplotlib, but we don't have to.
try:
  import matplotlib
  matplotlib.use('TKAgg')
  import matplotlib.pyplot as plt
  import matplotlib.gridspec as gridspec
  from matplotlib.dates import date2num, DateFormatter
except ImportError:
  pass

WINDOW = 100


class NuPICOutput(object):

  __metaclass__ = ABCMeta


  def __init__(self, name):
    self.name = name
    self.anomalyLikelihoodHelper = anomaly_likelihood.AnomalyLikelihood()


  @abstractmethod
  def write(self, timestamp, value, predicted, anomalyScore):
    pass


  @abstractmethod
  def close(self):
    pass




class NuPICFileOutput(NuPICOutput):


  def __init__(self, *args, **kwargs):
    super(NuPICFileOutput, self).__init__(*args, **kwargs)
    self.outputFiles = []
    self.outputWriters = []
    self.lineCount = 0
    headerRow = [
      'timestamp', 'kw_energy_consumption', 'prediction',
      'anomaly_score', 'anomaly_likelihood'
    ]
    outputFileName = "%s_out.csv" % self.name
    print "Preparing to output %s data to %s" % (self.name, outputFileName)
    self.outputFile = open(outputFileName, "w")
    self.outputWriter = csv.writer(self.outputFile)
    self.outputWriter.writerow(headerRow)




  def write(self, timestamp, value, predicted, anomalyScore):
    if timestamp is not None:
      anomalyLikelihood = self.anomalyLikelihoodHelper.anomalyProbability(
        value, anomalyScore, timestamp
      )
      outputRow = [timestamp, value, predicted, anomalyScore, anomalyLikelihood]
      self.outputWriter.writerow(outputRow)
      self.lineCount += 1



  def close(self):
    self.outputFile.close()
    print "Done. Wrote %i data lines to %s." % (self.lineCount, self.name)



class NuPICPlotOutput(NuPICOutput):


  def __init__(self, *args, **kwargs):
    super(NuPICPlotOutput, self).__init__(*args, **kwargs)
    # Turn matplotlib interactive mode on.
    plt.ion()
    self.dates = []
    self.convertedDates = []
    self.value = []
    self.predicted = []
    self.anomalyScore = []
    self.anomalyLikelihood = []
    self.actualLine = None
    self.predictedLine = None
    self.anomalyScoreLine = None
    self.anomalyLikelihoodLine = None
    self.linesInitialized = False
    fig = plt.figure(figsize=(14, 10))
    gs = gridspec.GridSpec(2, 1, height_ratios=[3,1])

    self._mainGraph = fig.add_subplot(gs[0, 0])
    plt.title(self.name)
    plt.ylabel('KW Energy Consumption')
    plt.xlabel('Date')

    self._anomalyGraph = fig.add_subplot(gs[1])

    plt.ylabel('Percentage')
    plt.xlabel('Date')

    plt.tight_layout()



  def initializeLines(self, timestamp):
    print "initializing %s" % self.name
    anomalyRange = (0.0, 1.0)
    self.dates = deque([timestamp] * WINDOW, maxlen=WINDOW)
    self.convertedDates = deque(
      [date2num(date) for date in self.dates], maxlen=WINDOW
    )
    self.value = deque([0.0] * WINDOW, maxlen=WINDOW)
    self.predicted = deque([0.0] * WINDOW, maxlen=WINDOW)
    self.anomalyScore = deque([0.0] * WINDOW, maxlen=WINDOW)
    self.anomalyLikelihood = deque([0.0] * WINDOW, maxlen=WINDOW)

    actualPlot, = self._mainGraph.plot(self.dates, self.value)
    self.actualLine = actualPlot
    predictedPlot, = self._mainGraph.plot(self.dates, self.predicted)
    self.predictedLine = predictedPlot
    self._mainGraph.legend(tuple(['actual', 'predicted']), loc=3)

    anomalyScorePlot, = self._anomalyGraph.plot(
      self.dates, self.anomalyScore, 'm'
    )
    anomalyScorePlot.axes.set_ylim(anomalyRange)

    self.anomalyScoreLine = anomalyScorePlot
    anomalyLikelihoodPlot, = self._anomalyGraph.plot(
      self.dates, self.anomalyScore, 'r'
    )
    anomalyLikelihoodPlot.axes.set_ylim(anomalyRange)
    self.anomalyLikelihoodLine = anomalyLikelihoodPlot
    self._anomalyGraph.legend(tuple(['anomaly score', 'anomaly likelihood']), loc=3)

    dateFormatter = DateFormatter('%m/%d %H:%M')
    self._mainGraph.xaxis.set_major_formatter(dateFormatter)
    self._anomalyGraph.xaxis.set_major_formatter(dateFormatter)


    self.linesInitialized = True



  def write(self, timestamp, value, predicted, anomalyScore):

    # We need the first timestamp to initialize the lines at the right X value,
    # so do that check first.
    if not self.linesInitialized:
      self.initializeLines(timestamp)

    anomalyLikelihood = self.anomalyLikelihoodHelper.anomalyProbability(
      value, anomalyScore, timestamp
    )

    self.dates.append(timestamp)
    self.convertedDates.append(date2num(timestamp))
    self.value.append(value)
    self.predicted.append(predicted)
    self.anomalyScore.append(anomalyScore)
    self.anomalyLikelihood.append(anomalyLikelihood)

    # Update main chart data
    self.actualLine.set_xdata(self.convertedDates)
    self.actualLine.set_ydata(self.value)
    self.predictedLine.set_xdata(self.convertedDates)
    self.predictedLine.set_ydata(self.predicted)
    # Update anomaly chart data
    self.anomalyScoreLine.set_xdata(self.convertedDates)
    self.anomalyScoreLine.set_ydata(self.anomalyScore)
    self.anomalyLikelihoodLine.set_xdata(self.convertedDates)
    self.anomalyLikelihoodLine.set_ydata(self.anomalyLikelihood)

    self._mainGraph.relim()
    self._mainGraph.autoscale_view(True, True, True)
    self._anomalyGraph.relim()
    self._anomalyGraph.autoscale_view(True, True, True)

    plt.draw()



  def close(self):
    plt.ioff()
    plt.show()



NuPICOutput.register(NuPICFileOutput)
NuPICOutput.register(NuPICPlotOutput)