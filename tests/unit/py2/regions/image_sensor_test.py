import sys
import os


from nupic.engine import Network
from nupic.regions.ImageSensor import ImageSensor

# Create network
net = Network()

# Add sensor
sensor = net.addRegion("sensor", "py.ImageSensor", "{width: 100, height: 50}")
pysensor = sensor.getSelf()

# Verify set parameters
assert(type(pysensor) == ImageSensor)
assert(pysensor.height == 50)
assert(pysensor.width == 100)

assert (pysensor.width == sensor.getParameter('width'))
assert (pysensor.height == sensor.getParameter('height'))

sensor.setParameter('width', 444)
sensor.setParameter('height', 444)
assert pysensor.width == 444
assert pysensor.height == 444


# Verify py object is not a copy
sensor.getSelf().height = 100
sensor.getSelf().width = 200
assert(pysensor.height == 100)
assert(pysensor.width == 200)

pysensor.height = 50
pysensor.width = 100
assert(sensor.getSelf().height == 50)
assert(sensor.getSelf().width == 100)

print "Test passed"