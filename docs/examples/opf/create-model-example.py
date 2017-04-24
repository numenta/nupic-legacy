import yaml
from nupic.frameworks.opf.model_factory import ModelFactory

_PARAMS_PATH = "/path/to/model.yaml"

with open(_PARAMS_PATH, "r") as f:
  modelParams = yaml.safe_load(f)

model = ModelFactory.create(modelParams.MODEL_PARAMS)

# This tells the model the field to predict.
model.enableInference({'predictedField': 'consumption'})
