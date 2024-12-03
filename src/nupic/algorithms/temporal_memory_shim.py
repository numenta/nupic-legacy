# Copyright 2014 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""
A shim for the TemporalMemory class that transparently implements TM,
for use with tests.
"""

import numpy

from nupic.algorithms.backtracking_tm import BacktrackingTM
from nupic.algorithms.backtracking_tm_cpp import BacktrackingTMCPP
from nupic.algorithms.connections import Connections
from nupic.math import GetNTAReal
try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.algorithms.temporal_memory_shim_capnp import (
    TemporalMemoryShimProto)



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


  @classmethod
  def getSchema(cls):
    return TemporalMemoryShimProto


  @classmethod
  def read(cls, proto):
    """Deserialize from proto instance.

    :param proto: (TemporalMemoryShimProto) the proto instance to read from
    """
    tm = super(TemporalMemoryShim, cls).read(proto.baseTM)
    tm.predictiveCells = set(proto.predictedState)
    tm.connections = Connections.read(proto.conncetions)


  def write(self, proto):
    """Populate serialization proto instance.

    :param proto: (TemporalMemoryShimProto) the proto instance to populate
    """
    super(TemporalMemoryShim, self).write(proto.baseTM)
    proto.connections.write(self.connections)
    proto.predictiveCells = self.predictiveCells
