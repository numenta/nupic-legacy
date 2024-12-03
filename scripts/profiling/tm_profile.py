# Copyright 2015 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

## run python -m cProfile --sort cumtime $NUPIC/scripts/profiling/tm_profile.py [nColumns nEpochs]

import numpy
import sys

from nupic.algorithms.backtracking_tm import BacktrackingTM as PyTM
from nupic.algorithms.backtracking_tm_cpp import BacktrackingTMCPP as CppTM


def profileTM(tmClass, tmDim, nRuns):
  """
  profiling performance of TemporalMemory (TM)
  using the python cProfile module and ordered by cumulative time,
  see how to run on command-line above.

  @param tmClass implementation of TM (cpp, py, ..)
  @param tmDim number of columns in TM
  @param nRuns number of calls of the profiled code (epochs)
  """

  # create TM instance to measure
  tm = tmClass(numberOfCols=tmDim)

  # generate input data
  data = numpy.random.randint(0, 2, [tmDim, nRuns]).astype('float32')

  for i in xrange(nRuns):
    # new data every time, this is the worst case performance
    # real performance would be better, as the input data would not be completely random
    d = data[:,i]

    # the actual function to profile!
    tm.compute(d, True)



if __name__ == "__main__":
  columns=2048
  epochs=10000
  # read command line params
  if len(sys.argv) == 3: # 2 args + name
    columns=int(sys.argv[1])
    epochs=int(sys.argv[2])

  profileTM(CppTM, columns, epochs)
