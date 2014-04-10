import os
import json

from nupic.swarming import permutations_runner



def model_params_to_string(model_params):
  return json.dumps(
    model_params, 
    sort_keys=True,
    indent=4, 
    separators=(',', ': ')
  )



def write_model_params_file(model_params, name):
  clean_name = name.replace(" ", "_").replace("-", "_")
  params_name = "%s_model_params.py" % clean_name
  out_dir = os.path.join(os.getcwd(), 'model_params')
  if not os.path.isdir(out_dir):
    os.mkdir(out_dir)
  out_path = os.path.join(os.getcwd(), 'model_params', params_name)
  with open(out_path, "wb") as out_file:
    out_file.write("MODEL_PARAMS = %s" % model_params_to_string(model_params))



def swarm_for_best_model_params(swarm_config, name=None):
  model_params = permutations_runner.runWithConfig(swarm_config, {
    "maxWorkers": 4, "overwrite": True
  })
  if name is not None:
    write_model_params_file(model_params, name)
  return model_params
