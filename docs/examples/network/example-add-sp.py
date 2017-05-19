spParams = modelParams["spParams"]

# Make sure the SP input width matches the sensor output width.
spParams["inputWidth"] = sensorRegion.encoder.getWidth()

# Add SP region.
network.addRegion("SP", "py.SPRegion", json.dumps(spParams))