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
A shim for the TP class that transparently implements TemporalMemory,
for use with OPF.
"""

import numpy

from nupic.research.temporal_memory import TemporalMemory
from nupic.research.monitor_mixin.temporal_memory_monitor_mixin import (
  TemporalMemoryMonitorMixin)
class MonitoredTemporalMemory(TemporalMemoryMonitorMixin, TemporalMemory): pass



class TPShim(TemporalMemory):
  """
  TP => Temporal Memory shim class.
  """
  def __init__(self,
               numberOfCols=500,
               cellsPerColumn=10,
               initialPerm=0.11,
               connectedPerm=0.50,
               minThreshold=8,
               newSynapseCount=15,
               permanenceInc=0.10,
               permanenceDec=0.10,
               permanenceMax=1.0,
               globalDecay=0.10,
               activationThreshold=12,
               predictedSegmentDecrement=0,
               seed=42):
    """
    Translate parameters and initialize member variables specific to `TP.py`.
    """
    super(TPShim, self).__init__(
      columnDimensions=(numberOfCols,),
      cellsPerColumn=cellsPerColumn,
      activationThreshold=activationThreshold,
      initialPermanence=initialPerm,
      connectedPermanence=connectedPerm,
      minThreshold=minThreshold,
      maxNewSynapseCount=newSynapseCount,
      permanenceIncrement=permanenceInc,
      permanenceDecrement=permanenceDec,
      predictedSegmentDecrement=predictedSegmentDecrement,
      seed=seed)

    self.infActiveState = {"t": None}


  def compute(self, bottomUpInput, enableLearn, computeInfOutput=None):
    """
    (From `TP.py`)
    Handle one compute, possibly learning.

    @param bottomUpInput     The bottom-up input, typically from a spatial pooler
    @param enableLearn       If true, perform learning
    @param computeInfOutput  If None, default behavior is to disable the inference
                             output when enableLearn is on.
                             If true, compute the inference output
                             If false, do not compute the inference output
    """
    super(TPShim, self).compute(set(bottomUpInput.nonzero()[0]),
                                            learn=enableLearn)
    numberOfCells = self.numberOfCells()

    activeState = numpy.zeros(numberOfCells)
    activeState[self.getCellIndices(self.activeCells)] = 1
    self.infActiveState["t"] = activeState

    output = numpy.zeros(numberOfCells)
    output[self.getCellIndices(self.predictiveCells | self.activeCells)] = 1
    return output
  
  
  def getActiveState(self):
    activeState = numpy.zeros(self.numberOfCells())
    activeState[self.getCellIndices(self.activeCells)] = 1
    return activeState
  
  
  def getPredictedState(self):
    predictedState = numpy.zeros(self.numberOfCells())
    predictedState[self.getCellIndices(self.predictiveCells)] = 1
    return predictedState



class MonitoredTPShim(MonitoredTemporalMemory):
  """
  TP => Monitored Temporal Memory shim class.

  TODO: This class is not very DRY. This whole file needs to be replaced by a
  pure TemporalMemory region
  (WIP at https://github.com/numenta/nupic.research/pull/247).
  """
  def __init__(self,
               numberOfCols=500,
               cellsPerColumn=10,
               initialPerm=0.11,
               connectedPerm=0.50,
               minThreshold=8,
               newSynapseCount=15,
               permanenceInc=0.10,
               permanenceDec=0.10,
               permanenceMax=1.0,
               globalDecay=0.10,
               activationThreshold=12,
               predictedSegmentDecrement=0,
               seed=42):
    """
    Translate parameters and initialize member variables specific to `TP.py`.
    """
    super(MonitoredTPShim, self).__init__(
      columnDimensions=(numberOfCols,),
      cellsPerColumn=cellsPerColumn,
      activationThreshold=activationThreshold,
      initialPermanence=initialPerm,
      connectedPermanence=connectedPerm,
      minThreshold=minThreshold,
      maxNewSynapseCount=newSynapseCount,
      permanenceIncrement=permanenceInc,
      permanenceDecrement=permanenceDec,
      predictedSegmentDecrement=predictedSegmentDecrement,
      seed=seed)

    self.infActiveState = {"t": None}


  def compute(self, bottomUpInput, enableLearn, computeInfOutput=None):
    """
    (From `TP.py`)
    Handle one compute, possibly learning.

    @param bottomUpInput     The bottom-up input, typically from a spatial pooler
    @param enableLearn       If true, perform learning
    @param computeInfOutput  If None, default behavior is to disable the inference
                             output when enableLearn is on.
                             If true, compute the inference output
                             If false, do not compute the inference output
    """
    super(MonitoredTPShim, self).compute(set(bottomUpInput.nonzero()[0]),
                                             learn=enableLearn)
    numberOfCells = self.numberOfCells()

    activeState = numpy.zeros(numberOfCells)
    activeState[self.getCellIndices(self.activeCells)] = 1
    self.infActiveState["t"] = activeState

    output = numpy.zeros(numberOfCells)
    output[self.getCellIndices(self.predictiveCells | self.activeCells)] = 1
    return output


  def getActiveState(self):
    activeState = numpy.zeros(self.numberOfCells())
    activeState[self.getCellIndices(self.activeCells)] = 1
    return activeState


  def getPredictedState(self):
    predictedState = numpy.zeros(self.numberOfCells())
    predictedState[self.getCellIndices(self.predictiveCells)] = 1
    return predictedState
