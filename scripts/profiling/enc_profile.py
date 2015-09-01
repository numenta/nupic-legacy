#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

## run python -m cProfile --sort cumtime $NUPIC/scripts/profiling/enc_profile.py [nMaxValue nEpochs]

import sys
import numpy
# chose desired Encoder implementations to compare:
from nupic.encoders.scalar import ScalarEncoder
from nupic.encoders.random_distributed_scalar import RandomDistributedScalarEncoder as RDSE
from nupic.encoders.coordinate import CoordinateEncoder


def profileEnc(maxValue, nRuns):
  minV=0
  maxV=maxValue
  # generate input data
  data=numpy.random.randint(minV, maxV+1, nRuns)
  # instantiate measured encoders
  encScalar = ScalarEncoder(w=21, minval=minV, maxval=maxV, resolution=1)
  encRDSE = RDSE(resolution=1)
  encCoord = CoordinateEncoder(cacheSize = 1)
  
  # profile!  
  for d in data:
    encScalar.encode(d)
    encRDSE.encode(d)
    encCoord.encode((d, d), 2)

  print "Scalar n=",encScalar.n," RDSE n=",encRDSE.n," Coord n=",encCoord.n
  print encCoord.dump()



if __name__ == "__main__":
  maxV=500
  iters=10000
  epochs = 10
  if len(sys.argv) == 3: # 2 args + name
    columns=int(sys.argv[1])
    epochs=int(sys.argv[2])

  for _ in xrange(epochs):
    profileEnc(maxV, iters)
