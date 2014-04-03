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

import os
import datetime
import csv
import shutil

from nupic.swarming import permutations_runner
from nupic.frameworks.opf.modelfactory import ModelFactory
from nupic_output import NuPICFileOutput, NuPICPlotOutput
import generate_data
from base_swarm_description import BASE_SWARM_DESCRIPTION



def swarm_for_best_model_params(swarm_config):
  # print swarm_config
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
    # stop after one for debugging

  print
  print "================================================="
  print "= Swarming complete!                            ="
  print "================================================="
  print

  models = {}

  for name, model_params in all_model_params.iteritems():
    print "Creating %s model..." % name
    model = ModelFactory.create(model_params)
    model.enableInference({"predictedField": "kw_energy_consumption"})
    models[name] = model

  print
  print "================================================="
  print "= Model creation complete!                      ="
  print "================================================="
  print

  for name, model in models.iteritems():
    input_file = input_files[name]
    output = NuPICFileOutput(name, show_anomaly_score=False)
    with open(input_file, "rb") as gym_input:
      csv_reader = csv.reader(gym_input)
      # skip header rows
      csv_reader.next()
      csv_reader.next()
      csv_reader.next()
      # the real data
      for row in csv_reader:
        timestamp = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        consumption = float(row[1])
        result = model.run({
          "timestamp": timestamp,
          "kw_energy_consumption": consumption
        })
        output.write(timestamp, consumption, result, prediction_step=1)

    output.close()


  # shutil.copyfile("model_%s/model_params.py" % name, "model_params.py")
  # import model_params
  # output = NuPICFileOutput(name, show_anomaly_score=False)
  # model = ModelFactory.create(model_params.MODEL_PARAMS)
  # model.enableInference({"predictedField": "kw_energy_consumption"})
  # input_file = os.path.join("../local_data", "%s.csv" % name)
  # with open(input_file, "rb") as gym_input:
  #   csv_reader = csv.reader(gym_input)
  #
  #   # skip header rows
  #   csv_reader.next()
  #   csv_reader.next()
  #   csv_reader.next()
  #
  #   # the real data
  #   for row in csv_reader:
  #     timestamp = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
  #     consumption = float(row[1])
  #     result = model.run({
  #       "timestamp": timestamp,
  #       "kw_energy_consumption": consumption
  #     })
  #     output.write(timestamp, consumption, result, prediction_step=1)
  #
  # output.close()



if __name__ == "__main__":
  run_experiment()
