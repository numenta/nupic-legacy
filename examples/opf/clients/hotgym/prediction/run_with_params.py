#!/usr/bin/python
import sys
import importlib

from nupic.frameworks.opf.modelfactory import ModelFactory
from io_helper import run_io_through_nupic


def run_experiment(gym_name):
  print "Creating model from %s..." % gym_name
  model_params_name = importlib.import_module(
    "model_params.%s_model_params" % (
      gym_name.replace(" ", "_").replace("-", "_")
    )
  )
  model = ModelFactory.create(model_params_name.MODEL_PARAMS)
  model.enableInference({"predictedField": "kw_energy_consumption"})
  input_data = ["./local_data/%s.csv" % gym_name.replace(" ", "_")]
  models = [model]
  names = [gym_name]
  plot = True
  run_io_through_nupic(input_data, models, names, plot)



if __name__ == "__main__":
  if len(sys.argv) == 1:
    print "Please provide gym name."
    exit()
  gym_name = sys.argv[1]
  print "Running %s" % gym_name
  run_experiment(gym_name)