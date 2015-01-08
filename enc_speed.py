from nupic.encoders.scalar import ScalarEncoder
from nupic.encoders.random_distributed_scalar import RandomDistributedScalarEncoder as RDSE

import numpy as np

total=10000
minV=0
maxV=total

data=np.random.randint(minV, maxV+1, total)

encScalar = ScalarEncoder(w=21, minval=minV, maxval=maxV, resolution=1)
encRDSE = RDSE(resolution=1)

for d in data:
  encScalar.encode(d)
  encRDSE.encode(d)

print "Scalar n=",encScalar.n," RDSE n=",encRDSE.n
