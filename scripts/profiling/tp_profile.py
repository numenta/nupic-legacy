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

## run python -m cProfile --sort cumtime $NUPIC/scripts/profiling/tp_profile.py [nColumns nEpochs]

import sys
import numpy
# chose desired TP implementation to compare:
from nupic.research.TP10X2 import TP10X2 as CppTP 
from nupic.research.TP import TP as PyTP


def profileTP(tpClass, tpDim, nRuns):
  """
  profiling performance of TemporalPooler (TP)
  using the python cProfile module and ordered by cumulative time, 
  see how to run on command-line above.

  @param tpClass implementation of TP (cpp, py, ..)
  @param tpDim number of columns in TP
  @param nRuns number of calls of the profiled code (epochs)
  """

  # create TP instance to measure
  tp = tpClass(numberOfCols=tpDim)

  # generate input data
  data = numpy.random.randint(0, 2, [tpDim, nRuns]).astype('float32')

  for i in xrange(nRuns):
    # new data every time, this is the worst case performance
    # real performance would be better, as the input data would not be completely random
    d = data[:,i]

    # the actual function to profile!
    tp.compute(d, True)



if __name__ == "__main__":
  columns=2048
  epochs=10000
  # read command line params
  if len(sys.argv) == 3: # 2 args + name
    columns=int(sys.argv[1])
    epochs=int(sys.argv[2])

  profileTP(CppTP, columns, epochs)
