from nupic.encoders.date import DateEncoder
from nupic.encoders.random_distributed_scalar import \
    RandomDistributedScalarEncoder

timeOfDayEncoder = DateEncoder(timeOfDay=(21,1))
weekendEncoder = DateEncoder(weekend=21)
scalarEncoder = RandomDistributedScalarEncoder(0.88)
