import os
import pprint

from nupic.swarming import permutations_runner


INPUT_FILE = "Balgowlah_Platinum.csv"
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
    print "Wrote model params file to %s" % out_path
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
  # swarm_description = _get_swarm_description_for(input_file_path)
  print "================================================="
  print "= Swarming on %s data..." % name
  print "================================================="
  # return _swarm_for_best_model_params(swarm_description, name)
  _swarm_for_best_model_params(name)



def _run_swarm(file_path):
  name = os.path.splitext(os.path.basename(file_path))[0]
  return swarm_for_input(name)



def _report(output):
  print "\nWrote the following model param files:"
  def model_report(one_output):
    print "\t%s" % one_output[0]
  if isinstance(output, list):
    for i in output:
      model_report(i)
  else:
    model_report(output)



def swarm():
  output = _run_swarm(INPUT_FILE)
  # _report(output)
  return output
