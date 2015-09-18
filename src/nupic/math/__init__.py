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
## @file

nupic.math is a package containing modules related to mathematical, probabilistic
and statistical data structures and simple algorithms.

The primary sub-modules include (use help on these modules for additional
online documentation):

nupic.bindings.math
A module containing many low-level mathematical data structures and algorithms.
This module is a set of Python bindings for the Numenta C++ math libraries.
Because of this, some calling conventions may more closely reflect the underlying
C++ architecture than a typical Python module.
All classes, functions and constants of nupic.bindings.math are pre-imported
into nupic.math, and thus are accessible from nupic.math.
The module contains the following important and frequently used classes:
  SparseMatrix
  SparseTensor
  TensorIndex
  Domain

nupic.math.stats
Module of statistical data structures and functions used in learning algorithms
and for analysis of HTM network inputs and outputs.
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
