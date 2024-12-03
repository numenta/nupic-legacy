# Copyright 2015 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

## run python -m cProfile --sort cumtime $NUPIC/scripts/profiling/enc_profile.py [nMaxValue nEpochs]

import sys
import numpy
# chose desired Encoder implementations to compare:
from nupic.encoders.scalar import ScalarEncoder
from nupic.encoders.random_distributed_scalar import RandomDistributedScalarEncoder as RDSE


def profileEnc(maxValue, nRuns):
  minV=0
  maxV=nRuns
  # generate input data
  data=numpy.random.randint(minV, maxV+1, nRuns)
  # instantiate measured encoders
  encScalar = ScalarEncoder(w=21, minval=minV, maxval=maxV, resolution=1)
  encRDSE = RDSE(resolution=1)
  
  # profile!  
  for d in data:
    encScalar.encode(d)
    encRDSE.encode(d)

  print "Scalar n=",encScalar.n," RDSE n=",encRDSE.n



if __name__ == "__main__":
  maxV=500
  epochs=10000
  if len(sys.argv) == 3: # 2 args + name
    columns=int(sys.argv[1])
    epochs=int(sys.argv[2])

  profileEnc(maxV, epochs)
