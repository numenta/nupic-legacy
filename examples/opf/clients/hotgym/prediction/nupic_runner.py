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
import importlib
import os

from nupic.frameworks.opf.modelfactory import ModelFactory

from swarm_helper import swarm_for_input
from io_helper import run_io_through_nupic
import generate_data


DATA_DIR = "./local_data"
MODEL_PARAMS_DIR = "./model_params"



def _create_model(model_params):
  model = ModelFactory.create(model_params)
  model.enableInference({"predictedField": "kw_energy_consumption"})
  return model



def _get_model_params_from_name(gym_name):
  imported_model_params = importlib.import_module(
    "model_params.%s_model_params" % (
      gym_name.replace(" ", "_").replace("-", "_")
    )
  ).MODEL_PARAMS
  return imported_model_params



def run_model(gym_name, plot=False):
  print "Creating model from %s..." % gym_name
  model = _create_model(_get_model_params_from_name(gym_name))
  input_data = ["%s/%s.csv" % (DATA_DIR, gym_name.replace(" ", "_"))]
  run_io_through_nupic(input_data, [model], [gym_name], plot)



def run_all_models(plot=False):
  models = []
  names = []
  input_files = []
  for input_file in sorted(os.listdir(DATA_DIR)):
    name = os.path.splitext(input_file)[0]
    names.append(name)
    input_files.append(os.path.abspath(os.path.join(DATA_DIR, input_file)))
    models.append(_create_model(_get_model_params_from_name(name)))
  run_io_through_nupic(input_files, models, names, plot)



def run_it_all(plot=False):
  input_files = generate_data.run()
  print "Generated input data files:"
  print input_files
  names = input_files.keys()
  input_files = input_files.values()
  all_model_params = []

  for index, input_file_path in enumerate(input_files):
    model_params = swarm_for_input(input_file_path, names[index])
    all_model_params.append(model_params)

  print
  print "================================================="
  print "= Swarming complete!                            ="
  print "================================================="
  print

  models = []

  for index, model_params in enumerate(all_model_params):
    print "Creating %s model..." % names[index]
    models.append(_create_model(model_params[1]))

  print
  print "================================================="
  print "= Model creation complete!                      ="
  print "================================================="
  print

  run_io_through_nupic(input_files, models, names, plot)
