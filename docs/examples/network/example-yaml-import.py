import yaml

_PARAMS_PATH = "/path/to/model.yaml"

with open(_PARAMS_PATH, "r") as f:
  modelParams = yaml.safe_load(f)["modelParams"]