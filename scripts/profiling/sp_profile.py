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

## run python -m cProfile --sort cumtime $NUPIC/scripts/profiling/sp_profile.py [nColumns nEpochs]
# example results (not averaged, on local machine):
# input size N=10000, columns=2048, epochs=150 
# PySP | 1D (colDim=(2048,))   | 0.441 s/call (compute)
# PySP | 2D (colDim=(2048,1))  | 0.295 s/call (compute)
# CppSP| 1D		       | 0.108 s/call (algorithms.py/compute)
# CppSP| 2D		       | 0.040 s/call --- 2.5x FASTER! should be same(or worse) as 1D, FIXME

import sys
import numpy
import itertools
# chose desired SP implementation to compare:
from nupic.research.spatial_pooler import SpatialPooler as PySP
from nupic.bindings.algorithms import SpatialPooler as CppSP


def profileSP(spClass, spDim, nRuns):
  """
  profiling performance of SpatialPooler (SP)
  using the python cProfile module and ordered by cumulative time, 
  see how to run on command-line above.

  @param spClass implementation of SP (cpp, py, ..)
  @param spDim number of columns in SP (in 1D, for 2D see colDim in code)
  @param nRuns number of calls of the profiled code (epochs)
  """
  # you can change dimensionality here, eg to 2D
  inDim = (10000,1) # a rather large input
  colDim = (spDim,1) # 1D vs 2D just toggle here (spDim,) vs (spDim,1), and do the same change in inDim ^^^


  # create SP instance to measure
  # changing the params here affects the performance
  sp = spClass(
        inputDimensions=inDim,
        columnDimensions=colDim,
        potentialRadius=3,
        potentialPct=0.5,
        globalInhibition=False,
        localAreaDensity=-1.0,
        numActiveColumnsPerInhArea=3,
        stimulusThreshold=1,
        synPermInactiveDec=0.01,
        synPermActiveInc=0.1,
        synPermConnected=0.10,
        minPctOverlapDutyCycle=0.1,
        dutyCyclePeriod=10,
        boostStrength=10.0,
        seed=42,
        spVerbosity=0)


  # helper vars
  dataSize = list(inDim)[0]
  activeArray = numpy.zeros(colDim)

  for i in xrange(nRuns):
    # new data every time, this is the worst case performance
    # real performance would be better, as the input data would not be completely random
    data = numpy.random.randint(0, 2, dataSize).astype('uint32')

    # the actual function to profile!
    sp.compute(data, True, activeArray)



if __name__ == "__main__":
  columns=2048
  epochs=150
  # read params from command line
  if len(sys.argv) == 3: # 2 args + name
    columns=int(sys.argv[1])
    epochs=int(sys.argv[2])

  profileSP(CppSP, columns, epochs)
