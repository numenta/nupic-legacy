#! /usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
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

## run python -m cProfile --sort cumtime tp_large.py 

import numpy
# chose desired TP implementation to compare:
from nupic.research.TP10X2 import TP10X2 as CppTP 
from nupic.research.TP import TP as PyTP


def profileTP(tpClass, tpDim, nRuns):
  """Checks that feeding in the same input vector leads to polarized
  permanence values: either zeros or ones, but no fractions"""

  tp = tpClass(numberOfCols=tpDim)

  data = numpy.random.randint(0, 2, tpDim).astype('float32')

  for _ in xrange(nRuns):
    tp.compute(data, True)



if __name__ == "__main__":
  profileTP(CppTP, 2048, 10000)
