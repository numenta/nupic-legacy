# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""
This package contains modules related to mathematical, probabilistic and 
statistical data structures and simple algorithms.
"""

import sys
import math as coremath # The core Python module.

# bitstringToArray/CMultiArgMax are not part of NuPIC2
from nupic.bindings.math import (GetNTAReal,
                                 GetNumpyDataType,
                                 SparseMatrix,  SparseTensor,
                                 TensorIndex, Domain)
from nupic.bindings.math import lgamma, erf

def choose(n, c):
  return int(round(coremath.exp(logChoose(n, c))))

def logChoose(n, c):
  return lgamma(n+1) - lgamma(c+1) - lgamma(n-c+1)


# __all__ affects what symbols match "*"
# set __all__ so that "from math import *" doesn't clobber "sys"

__all__ = [
    "GetNTAReal", "GetNumpyDataType",
    "SparseMatrix", "SparseTensor", "TensorIndex", "Domain", "choose", "logChoose"]


__all__.extend(["CMultiArgMax", "bitstringToArray",
    "pickByDistribution", "ConditionalProbabilityTable2D", "MultiIndicator", "Indicator"])
