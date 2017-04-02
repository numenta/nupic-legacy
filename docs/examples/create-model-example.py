from nupic.frameworks.opf.modelfactory import ModelFactory

import model_params

model = ModelFactory.create(model_params.MODEL_PARAMS)

# This tells the model the field to predict.
model.enableInference({'predictedField': 'consumption'})
