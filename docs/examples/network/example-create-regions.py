import json

# Add a sensor region, set its encoder and data source.
network.addRegion("sensor", "py.RecordSensor", json.dumps({"verbosity": 0}))

# Make sure the SP input width matches the sensor region output width.
model_params["spParams"]["inputWidth"] = sensorRegion.encoder.getWidth()

# Add the SP and TM regions.
network.addRegion("SP", "py.SPRegion", json.dumps(model_params["spParams"]))
network.addRegion("TM", "py.TPRegion", json.dumps(model_params["tmParams"]))

# Add the classifier region.
clName = "py.%s" % model_params[]
network.addRegion("classifier", , json.dumps(model_params["clParams"]))



# Add all links
createSensorToClassifierLinks(network, "sensor", "classifier")

# Link the sensor region to the SP region so that it can pass it data.
createDataOutLink(network, "sensor", "SP")

# Create feed-forward links between regions.
createFeedForwardLink(network, "SP", "TM")
createFeedForwardLink(network, "TM", "classifier")

# Propagate reset signals to SP and TM regions.
# Optional if you know that your sensor regions does not send resets.
createResetLink(network, "sensor", "SP")
createResetLink(network, "sensor", "TM")



# Set the data source to the sensor region
sensorRegion = network.regions["sensor"].getSelf()
sensorRegion.dataSource = dataSource

# Set the encoder to the sensor region
sensorRegion.encoder = createEncoder(model_params["sensorParams"]["encoders"])



# Make sure all objects are initialized.
network.initialize()



