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

import sys

from nupic.frameworks.opf.modelfactory import ModelFactory

from swarm_helper import swarm_for_input
from io_helper import run_io_through_nupic
import generate_data



def run_experiment(plot=False):
  input_files = generate_data.run()
  print "Generated input data files:"
  print input_files
  names = input_files.keys()
  input_files = input_files.values()
  all_model_params = []

  # Debugging, limit to only one gym.
  # input_files = [input_files[0]]
  # names = [names[0]]

  for index, input_file_path in enumerate(input_files):
    model_params = swarm_for_input(input_file_path, names[index])
    all_model_params.append(model_params)

  print
  print "================================================="
  print "= Swarming complete!                            ="
  print "================================================="
  print

  # Debugging
  # exit()

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
