#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

## run python -m cProfile --sort cumtime tp_large.py [nColumns nEpochs]

import sys
import numpy
# chose desired TP implementation to compare:
from nupic.research.TP10X2 import TP10X2 as CppTP 
from nupic.research.TP import TP as PyTP


def profileTP(tpClass, tpDim, nRuns):
  """Checks that feeding in the same input vector leads to polarized
  permanence values: either zeros or ones, but no fractions"""

  # create TP instance to measure
  tp = tpClass(numberOfCols=tpDim)

  # generate input data; if used only this - it's the easiest scenario (const data)
  data = numpy.random.randint(0, 2, tpDim).astype('float32')

  for _ in xrange(nRuns):
    # new data every time, this is the worst case performance
    # real performance would be better, as the input data would not be completely random
    data = numpy.random.randint(0, 2, tpDim).astype('float32') # time spent for this can be ignored

    # the actual function to profile!
    tp.compute(data, True)



if __name__ == "__main__":
  columns=2048
  epochs=10000
  if len(sys.argv) == 3: # 2 args + name
    columns=int(sys.argv[1])
    epochs=int(sys.argv[2])

  profileTP(CppTP, columns, epochs)
