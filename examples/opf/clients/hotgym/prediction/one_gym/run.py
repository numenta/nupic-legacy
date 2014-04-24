#! /usr/bin/python
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
Groups together code used for creating a NuPIC model and dealing with IO.
(This is a component of the One Hot Gym Prediction Tutorial.)
"""
import importlib
import os
import sys

from nupic.frameworks.opf.modelfactory import ModelFactory

from io_helper import run_io_through_nupic


GYM_NAME = "rec-center-hourly"
DATA_DIR = "."
MODEL_PARAMS_DIR = "./model_params"
DESCRIPTION = (
  "Starts a NuPIC model from the model params returned by the swarm\n"
  "and pushes each line of input from the gym into the model. Results\n"
  "are written to an output file (default) or plotted dynamically if\n"
  "the --plot option is specified.\n"
  "NOTE: You must run ./swarm.py before this, because model parameters\n"
  "are required to run NuPIC.\n"
)


def _create_model(model_params):
  model = ModelFactory.create(model_params)
  model.enableInference({"predictedField": "kw_energy_consumption"})
  return model



def _get_model_params_from_name(gym_name):
  import_name = "model_params.%s_model_params" % (
    gym_name.replace(" ", "_").replace("-", "_")
  )
  print "Importing model params from %s" % import_name
  try:
    imported_model_params = importlib.import_module(import_name).MODEL_PARAMS
  except ImportError:
    raise Exception("No model params exist for '%s'. Run swarm first!"
                    % gym_name)
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



if __name__ == "__main__":
  print DESCRIPTION
  plot = False
  args = sys.argv[1:]
  if "--plot" in args:
    plot = True
  run_model(GYM_NAME, plot=plot)