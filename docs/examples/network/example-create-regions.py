import json

# Add a sensor region, set its encoder and data source.
network.addRegion("sensor", "py.RecordSensor", json.dumps({"verbosity": 0}))

# Make sure the SP input width matches the sensor region output width.
modelParams["spParams"]["inputWidth"] = sensorRegion.encoder.getWidth()

# Add the SP and TM regions.
network.addRegion("SP", "py.SPRegion", json.dumps(modelParams["spParams"]))
network.addRegion("TM", "py.TMRegion", json.dumps(modelParams["tmParams"]))

# Add the classifier region.
clName = "py.%s" % modelParams[]
network.addRegion("classifier", , json.dumps(modelParams["clParams"]))



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
sensorRegion.encoder = createEncoder(modelParams["sensorParams"]["encoders"])



# Make sure all objects are initialized.
network.initialize()



