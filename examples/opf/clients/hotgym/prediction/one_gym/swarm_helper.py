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
import pprint

from nupic.swarming import permutations_runner


PERMUTATIONS_PATH = "swarm/permutations.py"



def _model_params_to_string(model_params):
  pp = pprint.PrettyPrinter(indent=2)
  return pp.pformat(model_params)



def _write_model_params_file(model_params, name):
  clean_name = name.replace(" ", "_").replace("-", "_")
  params_name = "%s_model_params.py" % clean_name
  out_dir = os.path.join(os.getcwd(), 'model_params')
  if not os.path.isdir(out_dir):
    os.mkdir(out_dir)
  out_path = os.path.join(os.getcwd(), 'model_params', params_name)
  with open(out_path, "wb") as out_file:
    model_params_string = _model_params_to_string(model_params)
    out_file.write("MODEL_PARAMS = \\\n%s" % model_params_string)
  return out_path



def _swarm_for_best_model_params(name, max_workers=4):
  output_label = name
  perm_work_dir = os.path.abspath('swarm')
  options = {
    "maxWorkers": max_workers, "overwrite": True
  }
  model_params = permutations_runner.runWithPermutationsScript(
    PERMUTATIONS_PATH, options, output_label, perm_work_dir
  )
  model_params_file = _write_model_params_file(model_params, name)
  return model_params_file, model_params



def swarm_for_input(name):
  print "================================================="
  print "= Swarming on %s data..." % name
  print "================================================="
  return _swarm_for_best_model_params(name)



def _run_swarm(file_path):
  name = os.path.splitext(os.path.basename(file_path))[0]
  return swarm_for_input(name)



def swarm(input_file):
  output = _run_swarm(input_file)
  print "\nWrote the following model param files:"
  print "\t%s" % output[0]
  return output
