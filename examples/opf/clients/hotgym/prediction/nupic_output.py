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
import matplotlib
matplotlib.use('TKAgg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.dates import date2num

from nupic.data.inference_shifter import InferenceShifter


WINDOW = 360


class NuPICOutput(object):

  __metaclass__ = ABCMeta


  def __init__(self, names, show_anomaly_score=False):
    self.names = names
    self.show_anomaly_score = show_anomaly_score


  @abstractmethod
  def write(self, timestamp, actual, model_results, prediction_step=1):
    pass


  @abstractmethod
  def close(self):
    pass



class NuPICFileOutput(NuPICOutput):


  def __init__(self, *args, **kwargs):
    super(NuPICFileOutput, self).__init__(*args, **kwargs)
    self.output_files = []
    self.output_writers = []
    self.line_counts = []
    header_row = ['timestamp', 'kw_energy_consumption', 'prediction']
    for name in self.names:
      self.line_counts.append(0)
      output_file_name = "%s_out.csv" % name
      print "Preparing to output %s data to %s" % (name, output_file_name)
      output_file = open(output_file_name, "w")
      self.output_files.append(output_file)
      output_writer = csv.writer(output_file)
      self.output_writers.append(output_writer)
      output_writer.writerow(header_row)



  def write(self, timestamps, actual_values, model_results, prediction_step=1):
    assert len(timestamps) == len(actual_values) == len(model_results)

    for index in range(len(self.names)):
      timestamp = timestamps[index]
      actual = actual_values[index]
      model_result = model_results[index]
      writer = self.output_writers[index]

      if timestamp is not None:
        prediction = model_result.inferences\
          ['multiStepBestPredictions'][prediction_step]
        output_row = [timestamp, actual, prediction]
        writer.writerow(output_row)
        self.line_counts[index] += 1



  def close(self):
    for index, name in enumerate(self.names):
      self.output_files[index].close()
      print "Done. Wrote %i data lines to %s." % (self.line_counts[index], name)


#
# class NuPICPlotOutput(NuPICOutput):
#
#
#   def __init__(self, *args, **kwargs):
#     super(NuPICPlotOutput, self).__init__(*args, **kwargs)
#     # turn matplotlib interactive mode on (ion)
#     plt.ion()
#     fig = plt.figure(figsize=(10, 6))
#     self.graph = fig.add_subplot(111)
#     gs = gridspec.GridSpec(2, 1, height_ratios=[3,1])
#     # plot title, legend, etc
#     plt.title('Hot Gym prediction example')
#     plt.ylabel('KW Energy Consumption')
#     plt.xlabel('Date')
#     plt.legend(tuple(['actual','predicted']), loc=3)
#     plt.tight_layout()
#     # The shifter will align prediction and actual values.
#     self.shifter = InferenceShifter()
#     self.lines_initialized = False
#
#
#
#   def initialize_lines(self, timestamp):
#     self.dates = deque([timestamp] * WINDOW, maxlen=WINDOW)
#     self.converted_dates = deque([date2num(date) for date in self.dates], maxlen=WINDOW)
#
#     self.actual_history = deque([0.0] * WINDOW, maxlen=WINDOW)
#     self.predicted_history = deque([0.0] * WINDOW, maxlen=WINDOW)
#
#     self.actual_line, = self.graph.plot(self.dates, self.actual_history)
#     self.predicted_line, = self.graph.plot(self.dates, self.predicted_history)
#
#     self.lines_initialized = True
#
#
#
#   def die(self):
#     matplotlib.pyplot.close("all")
#
#
#
#   def write(self, timestamp, value, prediction_result, prediction_step=1):
#     # We need the first timestamp to initialize the lines at the right X value,
#     # so do that check first.
#     if not self.lines_initialized:
#       self.initialize_lines(timestamp)
#
#     # Update the trailing predicted and actual value deques.
#     shifted_result = self.shifter.shift(prediction_result)
#     inference = shifted_result.inferences\
#       ['multiStepBestPredictions'][prediction_step]
#
#     if inference is not None:
#       self.dates.append(timestamp)
#       self.converted_dates.append(date2num(timestamp))
#       self.actual_history.append(shifted_result.rawInput['kw_energy_consumption'])
#       self.predicted_history.append(inference)
#
#       # Update data
#       self.actual_line.set_xdata(self.converted_dates)
#       self.actual_line.set_ydata(self.actual_history)
#       self.predicted_line.set_xdata(self.converted_dates)
#       self.predicted_line.set_ydata(self.predicted_history)
#
#       self.graph.relim()
#       self.graph.autoscale_view(True, True, True)
#       plt.draw()
#
#
#
#   def close(self):
#     plt.ioff()
#     plt.show()



NuPICOutput.register(NuPICFileOutput)
# NuPICOutput.register(NuPICPlotOutput)