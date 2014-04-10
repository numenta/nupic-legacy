#!/usr/bin/python

import sys
import os
import pprint

from nupic.swarming import permutations_runner
from base_swarm_description import BASE_SWARM_DESCRIPTION



def get_swarm_description_for(input_data_file_path):
  print "Constructing swarm desc for %s" % input_data_file_path
  desc_copy = dict(BASE_SWARM_DESCRIPTION)
  stream = desc_copy["streamDef"]["streams"][0]
  stream["info"] = input_data_file_path
  stream["source"] = "file://%s" % input_data_file_path
  return desc_copy



def model_params_to_string(model_params):
  pp = pprint.PrettyPrinter(indent=2)
  return pp.pformat(model_params)



def write_model_params_file(model_params, name):
  clean_name = name.replace(" ", "_").replace("-", "_")
  params_name = "%s_model_params.py" % clean_name
  out_dir = os.path.join(os.getcwd(), 'model_params')
  if not os.path.isdir(out_dir):
    os.mkdir(out_dir)
  out_path = os.path.join(os.getcwd(), 'model_params', params_name)
  with open(out_path, "wb") as out_file:
    out_file.write("MODEL_PARAMS = \\\n%s" % model_params_to_string(model_params))



def swarm_for_best_model_params(swarm_config, name=None):
  model_params = permutations_runner.runWithConfig(swarm_config, {
    "maxWorkers": 4, "overwrite": True
  })
  if name is not None:
    write_model_params_file(model_params, name)
  return model_params


def swarm_for_input(input_file_path, name):
  swarm_description = get_swarm_description_for(input_file_path)
  print "================================================="
  print "= Swarming on %s data..." % name
  print "================================================="
  return swarm_for_best_model_params(swarm_description, name)



if __name__ == "__main__":
  if len(sys.argv) < 3:
    print "Usage: swarm_helper.py <name> <csv-data-file>"
    exit()
  name = sys.argv[1]
  input_file = sys.argv[2]
  swarm_for_input(input_file, name)