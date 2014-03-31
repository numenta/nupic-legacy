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
import csv
from collections import deque
from abc import ABCMeta, abstractmethod
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from nupic.data.inference_shifter import InferenceShifter


WINDOW = 360


class NuPICOutput(object):

  __metaclass__ = ABCMeta


  def __init__(self, name, show_anomaly_score=False):
    self.name = name
    self.show_anomaly_score = show_anomaly_score


  @abstractmethod
  def write(self, index, value, prediction_result, prediction_step=1):
    pass


  @abstractmethod
  def close(self):
    pass



class NuPICFileOutput(NuPICOutput):


  def __init__(self, *args, **kwargs):
    super(NuPICFileOutput, self).__init__(*args, **kwargs)
    self.linecount = 0
    output_filename = "%s_out.csv" % self.name
    print "Preparing to output to %s" % output_filename
    self.file = open(output_filename, 'w')
    self.writer = csv.writer(self.file)
    header_row = ['timestamp', 'kw_energy_consumption', 'prediction']
    if self.show_anomaly_score:
      header_row.append('anomaly score')
    self.writer.writerow(header_row)


  def write(self, index, value, prediction_result, prediction_step=1):
    prediction = prediction_result.inferences\
      ['multiStepBestPredictions'][prediction_step]
    output_row = [index, value, prediction]
    if self.show_anomaly_score:
      output_row.append(prediction_result.inferences['anomalyScore'])
    self.writer.writerow(output_row)
    self.linecount = self.linecount + 1


  def close(self):
    self.file.close()
    print "Done. Wrote %i data lines to %s." % (self.linecount, self.file.name)



class NuPICPlotOutput(NuPICOutput):


  def __init__(self, *args, **kwargs):
    super(NuPICPlotOutput, self).__init__(*args, **kwargs)
    # turn matplotlib interactive mode on (ion)
    plt.ion()
    plt.figure(figsize=(24, 14))
    gs = gridspec.GridSpec(2, 1, height_ratios=[3,1])
    # plot title, legend, etc
    plt.title('Hot Gym prediction example')
    plt.ylabel('KW Energy Consumption')
    # The shifter will align prediction and actual values.
    self.shifter = InferenceShifter()
    # Keep the last WINDOW predicted and actual values for plotting.
    self.actual_history = deque([0.0] * WINDOW, maxlen=360)
    self.predicted_history = deque([0.0] * WINDOW, maxlen=360)
    if self.show_anomaly_score:
      self.anomaly_score = deque([0.0] * WINDOW, maxlen=360)
    # Initialize the plot lines that we will update with each new record.
    if self.show_anomaly_score:
      plt.subplot(gs[0])
    self.actual_line, = plt.plot(range(WINDOW), self.actual_history)
    self.predicted_line, = plt.plot(range(WINDOW), self.predicted_history)
    plt.legend(tuple(['actual','predicted']), loc=3)
    if self.show_anomaly_score:
      plt.subplot(gs[1])
      self.anomaly_score_line, = plt.plot(range(WINDOW), self.anomaly_score, 'r-')
      plt.legend(tuple(['anomaly score']), loc=3)

    # Set the y-axis range.
    self.actual_line.axes.set_ylim(-1, 1)
    self.predicted_line.axes.set_ylim(-1, 1)
    if self.show_anomaly_score:
      self.anomaly_score_line.axes.set_ylim(-1, 1)
    # legend_fields = ['actual','predicted']
    # if self.show_anomaly_score:
    #   legend_fields.append('anomaly score')
    # plt.legend(tuple(legend_fields), loc=3)



  def write(self, index, value, prediction_result, prediction_step=1):
    shifted_result = self.shifter.shift(prediction_result)
    # shifted_result = prediction_result
    # Update the trailing predicted and actual value deques.
    inference = shifted_result.inferences\
      ['multiStepBestPredictions'][prediction_step]
    if inference is not None:
      self.actual_history.append(shifted_result.rawInput['kw_energy_consumption'])
      self.predicted_history.append(inference)
      if self.show_anomaly_score:
        anomaly_score = prediction_result.inferences['anomalyScore']
        self.anomaly_score.append(anomaly_score)

    # Redraw the chart with the new data.
    self.actual_line.set_ydata(self.actual_history)  # update the data
    self.predicted_line.set_ydata(self.predicted_history)  # update the data
    if self.show_anomaly_score:
      self.anomaly_score_line.set_ydata(self.anomaly_score)  # update the data
    plt.draw()
    plt.tight_layout()



  def close(self):
    plt.ioff()
    plt.show()



NuPICOutput.register(NuPICFileOutput)
NuPICOutput.register(NuPICPlotOutput)