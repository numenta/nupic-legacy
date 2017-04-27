from nupic.encoders import MultiEncoder

def createEncoder(encoderParams):
  encoder = MultiEncoder()
  encoder.addMultipleEncoders(encoderParams)
  return encoder

# Use the same modelParams extracted from the YAML file earlier.
encoderParams = modelParams["sensorParams"]["encoders"]

# Add encoder to the sensor region.
sensorRegion = network.regions["sensor"].getSelf()
sensorRegion.encoder = createEncoder(encoderParams)