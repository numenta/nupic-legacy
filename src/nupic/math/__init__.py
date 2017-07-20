# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
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
