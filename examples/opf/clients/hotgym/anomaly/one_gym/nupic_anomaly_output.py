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
(This is a component of the One Hot Gym Anomaly Tutorial.)
"""
import csv
from collections import deque
from abc import ABCMeta, abstractmethod
from nupic.algorithms import anomaly_likelihood
# Try to import matplotlib, but we don't have to.
try:
  import matplotlib
  matplotlib.use('TKAgg')
  import matplotlib.pyplot as plt
  import matplotlib.gridspec as gridspec
  from matplotlib.dates import date2num, DateFormatter
except ImportError:
  pass

WINDOW = 300
HIGHLIGHT_ALPHA = 0.3
ANOMALY_HIGHLIGHT_COLOR = 'red'
WEEKEND_HIGHLIGHT_COLOR = 'yellow'
ANOMALY_THRESHOLD = 0.9


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



def extractWeekendHighlights(dates):
  weekendsOut = []
  weekendSearch = [5, 6]
  weekendStart = None
  for i, date in enumerate(dates):
    if date.weekday() in weekendSearch:
      if weekendStart is None:
        # Mark start of weekend
        weekendStart = i
    else:
      if weekendStart is not None:
        # Mark end of weekend
        weekendsOut.append((
          weekendStart, i, WEEKEND_HIGHLIGHT_COLOR, HIGHLIGHT_ALPHA
        ))
        weekendStart = None

  # Cap it off if we're still in the middle of a weekend
  if weekendStart is not None:
    weekendsOut.append((
      weekendStart, len(dates)-1, WEEKEND_HIGHLIGHT_COLOR, HIGHLIGHT_ALPHA
    ))

  return weekendsOut



def extractAnomalyIndices(anomalyLikelihood):
  anomaliesOut = []
  anomalyStart = None
  for i, likelihood in enumerate(anomalyLikelihood):
    if likelihood >= ANOMALY_THRESHOLD:
      if anomalyStart is None:
        # Mark start of anomaly
        anomalyStart = i
    else:
      if anomalyStart is not None:
        # Mark end of anomaly
        anomaliesOut.append((
          anomalyStart, i, ANOMALY_HIGHLIGHT_COLOR, HIGHLIGHT_ALPHA
        ))
        anomalyStart = None

  # Cap it off if we're still in the middle of an anomaly
  if anomalyStart is not None:
    anomaliesOut.append((
      anomalyStart, len(anomalyLikelihood)-1,
      ANOMALY_HIGHLIGHT_COLOR, HIGHLIGHT_ALPHA
    ))

  return anomaliesOut



class NuPICPlotOutput(NuPICOutput):


  def __init__(self, *args, **kwargs):
    super(NuPICPlotOutput, self).__init__(*args, **kwargs)
    # Turn matplotlib interactive mode on.
    plt.ion()
    self.dates = []
    self.convertedDates = []
    self.value = []
    self.allValues = []
    self.predicted = []
    self.anomalyScore = []
    self.anomalyLikelihood = []
    self.actualLine = None
    self.predictedLine = None
    self.anomalyScoreLine = None
    self.anomalyLikelihoodLine = None
    self.linesInitialized = False
    self._chartHighlights = []
    fig = plt.figure(figsize=(16, 10))
    gs = gridspec.GridSpec(2, 1, height_ratios=[3,  1])

    self._mainGraph = fig.add_subplot(gs[0, 0])
    plt.title(self.name)
    plt.ylabel('KW Energy Consumption')
    plt.xlabel('Date')

    self._anomalyGraph = fig.add_subplot(gs[1])

    plt.ylabel('Percentage')
    plt.xlabel('Date')

    # Maximizes window
    mng = plt.get_current_fig_manager()
    mng.resize(*mng.window.maxsize())

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
    self._anomalyGraph.legend(
      tuple(['anomaly score', 'anomaly likelihood']), loc=3
    )

    dateFormatter = DateFormatter('%m/%d %H:%M')
    self._mainGraph.xaxis.set_major_formatter(dateFormatter)
    self._anomalyGraph.xaxis.set_major_formatter(dateFormatter)

    self._mainGraph.relim()
    self._mainGraph.autoscale_view(True, True, True)

    self.linesInitialized = True



  def highlightChart(self, highlights, chart):
    for highlight in highlights:
      # Each highlight contains [start-index, stop-index, color, alpha]
      self._chartHighlights.append(chart.axvspan(
        self.convertedDates[highlight[0]], self.convertedDates[highlight[1]],
        color=highlight[2], alpha=highlight[3]
      ))



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
    self.allValues.append(value)
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

    # Remove previous highlighted regions
    for poly in self._chartHighlights:
      poly.remove()
    self._chartHighlights = []

    weekends = extractWeekendHighlights(self.dates)
    anomalies = extractAnomalyIndices(self.anomalyLikelihood)

    # Highlight weekends in main chart
    self.highlightChart(weekends, self._mainGraph)

    # Highlight anomalies in anomaly chart
    self.highlightChart(anomalies, self._anomalyGraph)

    maxValue = max(self.allValues)
    self._mainGraph.relim()
    self._mainGraph.axes.set_ylim(0, maxValue + (maxValue * 0.02))

    self._mainGraph.relim()
    self._mainGraph.autoscale_view(True, scaley=False)
    self._anomalyGraph.relim()
    self._anomalyGraph.autoscale_view(True, True, True)

    plt.draw()



  def close(self):
    plt.ioff()
    plt.show()



NuPICOutput.register(NuPICFileOutput)
NuPICOutput.register(NuPICPlotOutput)
