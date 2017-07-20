# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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
A shim for the TemporalMemory class that transparently implements TM,
for use with tests.
"""

import numpy

from nupic.algorithms.backtracking_tm import BacktrackingTM
from nupic.algorithms.backtracking_tm_cpp import BacktrackingTMCPP
from nupic.algorithms.connections import Connections
from nupic.math import GetNTAReal



TMClass = BacktrackingTMCPP
dtype = GetNTAReal()



class TemporalMemoryShim(TMClass):
  """
  Temporal Memory => TM shim class.
  """
  def __init__(self,
               columnDimensions=(2048,),
               cellsPerColumn=32,
               activationThreshold=13,
               initialPermanence=0.21,
               connectedPermanence=0.50,
               minThreshold=10,
               maxNewSynapseCount=20,
               permanenceIncrement=0.10,
               permanenceDecrement=0.10,
               seed=42):
    """
    Translate parameters and initialize member variables
    specific to TemporalMemory
    """
    numberOfCols = 1
    for n in columnDimensions:
      numberOfCols *= n

    super(TemporalMemoryShim, self).__init__(
      numberOfCols=numberOfCols,
      cellsPerColumn=cellsPerColumn,
      initialPerm=initialPermanence,
      connectedPerm=connectedPermanence,
      minThreshold=minThreshold,
      newSynapseCount=maxNewSynapseCount,
      permanenceInc=permanenceIncrement,
      permanenceDec=permanenceDecrement,
      permanenceMax=1.0,
      globalDecay=0,
      activationThreshold=activationThreshold,
      seed=seed)

    self.connections = Connections(numberOfCols * cellsPerColumn)
    self.predictiveCells = set()


  def compute(self, activeColumns, learn=True):
    """
    Feeds input record through TM, performing inference and learning.
    Updates member variables with new state.

    @param activeColumns (set) Indices of active columns in `t`
    """
    bottomUpInput = numpy.zeros(self.numberOfCols, dtype=dtype)
    bottomUpInput[list(activeColumns)] = 1
    super(TemporalMemoryShim, self).compute(bottomUpInput,
                                            enableLearn=learn,
                                            enableInference=True)

    predictedState = self.getPredictedState()
    self.predictiveCells = set(numpy.flatnonzero(predictedState))
