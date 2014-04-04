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

from nupic.swarming import permutations_runner
from nupic.frameworks.opf.modelfactory import ModelFactory
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


def run_io_through_nupic(input_files, models):
  # Set up model I/O
  for model_index, model_container in enumerate(models):
    name = model_container['name']
    input_file = input_files[name]
    output = NuPICPlotOutput(name, show_anomaly_score=False)
    model_container['output'] = output
    model_container['input'] = open(input_file, 'rb')
    csv_reader = csv.reader(model_container['input'])
    # skip header rows
    csv_reader.next()
    csv_reader.next()
    csv_reader.next()
    # the real data
    model_container['reader'] = csv_reader

  # Read input for as long as a model as more data
  while True:
    next_lines = [next(model_container['reader'], None) for model_container in
                  models]
    print
    print next_lines
    # If all lines are None, we're done
    if all(value is None for value in next_lines):
      break
    for model_index, line in enumerate(next_lines):
      print "%s: %s" % (models[model_index]['name'], ', '.join(line))
      # ignore models that are out of input data
      if line is None: continue
      model_container = models[model_index]
      model = model_container['model']
      output = model_container['output']
      timestamp = datetime.datetime.strptime(line[0], "%Y-%m-%d %H:%M:%S")
      consumption = float(line[1])
      result = model.run({
        "timestamp": timestamp,
        "kw_energy_consumption": consumption
      })
      print "Output %s: %s, %s" % (
      output.name, str(timestamp), str(consumption))
      output.write(timestamp, consumption, result, prediction_step=1)

  # close all I/O
  for model_container in models:
    model_container['input'].close()
    model_container['output'].close()


def run_experiment():
  input_files = generate_data.run()
  print "Generated input data files:"
  print input_files
  all_model_params = {}

  for input_name, input_file_path in input_files.iteritems():
    swarm_description = get_swarm_description_for(input_file_path)
    print "================================================="
    print "= Swarming on %s data..." % input_name
    print "================================================="
    all_model_params[input_name] \
      = swarm_for_best_model_params(swarm_description)

  print
  print "================================================="
  print "= Swarming complete!                            ="
  print "================================================="
  print

  models = []

  for name, model_params in all_model_params.iteritems():
    print "Creating %s model..." % name
    model = ModelFactory.create(model_params)
    model.enableInference({"predictedField": "kw_energy_consumption"})
    models.append({'name': name, 'model': model})

  print
  print "================================================="
  print "= Model creation complete!                      ="
  print "================================================="
  print

  run_io_through_nupic(input_files, models)



if __name__ == "__main__":
  run_experiment()
  # run_plot_test()
