#!/usr/bin/python

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

import datetime
import csv
import sys

from nupic.frameworks.opf.modelfactory import ModelFactory
from nupic.data.inference_shifter import InferenceShifter
from nupic.swarming import permutations_runner

from nupic_output import NuPICFileOutput, NuPICPlotOutput
import generate_data
from base_swarm_description import BASE_SWARM_DESCRIPTION



def swarm_for_best_model_params(swarm_config):
  return permutations_runner.runWithConfig(swarm_config, {
    'maxWorkers': 4, 'overwrite': True
  })



def get_swarm_description_for(input_data_file_path):
  print "Constructing swarm desc for %s" % input_data_file_path
  desc_copy = dict(BASE_SWARM_DESCRIPTION)
  stream = desc_copy["streamDef"]["streams"][0]
  stream["info"] = input_data_file_path
  stream["source"] = "file://%s" % input_data_file_path
  return desc_copy


def run_io_through_nupic(input_data, models, names, plot):
  readers = []
  input_files = []
  if plot:
    output = NuPICPlotOutput(names)
    shifter = InferenceShifter()
  else:
    output = NuPICFileOutput(names)
  # Populate input files and csv readers for each model.
  for index, model in enumerate(models):
    input_file = open(input_data[index], 'rb')
    input_files.append(input_file)
    csv_reader = csv.reader(input_file)
    # Skip header rows.
    csv_reader.next()
    csv_reader.next()
    csv_reader.next()
    # Reader is now at the top of the real data.
    readers.append(csv_reader)

  read_count = 0

  while True:
    next_lines = [next(reader, None) for reader in readers]
    # If all lines are None, we're done.
    if all(value is None for value in next_lines):
      print "Done after reading %i lines" % read_count
      break

    read_count += 1

    if (read_count % 100 == 0):
      print "Read %i lines..." % read_count

    times = []
    consumptions = []
    predictions = []

    # Gather one more input from each input file and send into each model.
    for index, line in enumerate(next_lines):
      model = models[index]
      # Ignore models that are out of input data.
      if line is None:
        timestamp = None
        consumption = None
        prediction = None
      else:
        timestamp = datetime.datetime.strptime(line[0], "%Y-%m-%d %H:%M:%S")
        consumption = float(line[1])
        result = model.run({
          "timestamp": timestamp,
          "kw_energy_consumption": consumption
        })

        if plot:
          # The shifter will align prediction and actual values for plotting.
          result = shifter.shift(result)

        prediction = result.inferences \
          ['multiStepBestPredictions'][1]



      times.append(timestamp)
      consumptions.append(consumption)
      predictions.append(prediction)

    output.write(times, consumptions, predictions)

  # close all I/O
  for file in input_files:
    file.close()
  output.close()



def run_experiment(plot=False):
  input_files = generate_data.run()
  print "Generated input data files:"
  print input_files
  names = input_files.keys()
  input_files = input_files.values()
  all_model_params = []

  for index, input_file_path in enumerate(input_files):
    swarm_description = get_swarm_description_for(input_file_path)
    print "================================================="
    print "= Swarming on %s data..." % names[index]
    print "================================================="
    model_params = swarm_for_best_model_params(swarm_description)
    all_model_params.append(model_params)

  print
  print "================================================="
  print "= Swarming complete!                            ="
  print "================================================="
  print

  models = []

  for index, model_params in enumerate(all_model_params):
    print "Creating %s model..." % names[index]
    model = ModelFactory.create(model_params)
    model.enableInference({"predictedField": "kw_energy_consumption"})
    models.append(model)

  print
  print "================================================="
  print "= Model creation complete!                      ="
  print "================================================="
  print

  run_io_through_nupic(input_files, models, names, plot)



if __name__ == "__main__":
  plot = len(sys.argv) > 1 and sys.argv[1] == 'plot'
  run_experiment(plot=plot)
  # run_plot_test()
