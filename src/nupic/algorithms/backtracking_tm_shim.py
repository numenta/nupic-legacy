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
A shim for the TM class that transparently implements TemporalMemory,
for use with OPF.
"""

import numpy
from nupic.bindings.algorithms import TemporalMemory as TemporalMemoryCPP

from nupic.algorithms.monitor_mixin.temporal_memory_monitor_mixin import (
  TemporalMemoryMonitorMixin)
from nupic.algorithms.temporal_memory import TemporalMemory


class MonitoredTemporalMemory(TemporalMemoryMonitorMixin,
                              TemporalMemory): pass



class TMShimMixin(object):
  """
  TM => Temporal Memory shim class.
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
               activationThreshold=12,
               predictedSegmentDecrement=0.0,
               maxSegmentsPerCell=255,
               maxSynapsesPerSegment=255,
               globalDecay=0.10,
               maxAge=100000,
               pamLength=1,
               verbosity=0,
               outputType="normal",
               seed=42):
    """
    Translate parameters and initialize member variables specific to `backtracking_tm.py`.
    """
    super(TMShimMixin, self).__init__(
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
      maxSegmentsPerCell=maxSegmentsPerCell,
      maxSynapsesPerSegment=maxSynapsesPerSegment,
      seed=seed)

    self.infActiveState = {"t": None}


  @classmethod
  def read(cls, proto):
    """
    Intercepts TemporalMemory deserialization request in order to initialize
    `self.infActiveState`

    @param proto (DynamicStructBuilder) Proto object

    @return (TemporalMemory) TemporalMemory shim instance
    """
    tm = super(TMShimMixin, cls).read(proto)
    tm.infActiveState = {"t": None}
    return tm


  def compute(self, bottomUpInput, enableLearn, computeInfOutput=None):
    """
    (From `backtracking_tm.py`)
    Handle one compute, possibly learning.

    @param bottomUpInput     The bottom-up input, typically from a spatial pooler
    @param enableLearn       If true, perform learning
    @param computeInfOutput  If None, default behavior is to disable the inference
                             output when enableLearn is on.
                             If true, compute the inference output
                             If false, do not compute the inference output
    """
    super(TMShimMixin, self).compute(set(bottomUpInput.nonzero()[0]),
                                     learn=enableLearn)
    numberOfCells = self.numberOfCells()

    activeState = numpy.zeros(numberOfCells)
    activeState[self.getActiveCells()] = 1
    self.infActiveState["t"] = activeState

    output = numpy.zeros(numberOfCells)

    output[self.getPredictiveCells()] = 1
    output[self.getActiveCells()] = 1
    return output


  def topDownCompute(self, topDownIn=None):
    """
    (From `backtracking_tm.py`)
    Top-down compute - generate expected input given output of the TM

    @param topDownIn top down input from the level above us

    @returns best estimate of the TM input that would have generated bottomUpOut.
    """
    output = numpy.zeros(self.numberOfColumns())
    columns = [self.columnForCell(idx) for idx in self.getPredictiveCells()]
    output[columns] = 1
    return output


  def getActiveState(self):
    activeState = numpy.zeros(self.numberOfCells())
    activeState[self.getActiveCells()] = 1
    return activeState


  def getPredictedState(self):
    predictedState = numpy.zeros(self.numberOfCells())
    predictedState[self.getPredictiveCells()] = 1
    return predictedState


  def getLearnActiveStateT(self):
    state = numpy.zeros([self.numberOfColumns(), self.getCellsPerColumn()])
    return state



class TMShim(TMShimMixin, TemporalMemory):
  pass



class TMCPPShim(TMShimMixin, TemporalMemoryCPP):
  pass



class MonitoredTMShim(MonitoredTemporalMemory):
  """
  TM => Monitored Temporal Memory shim class.

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
               activationThreshold=12,
               predictedSegmentDecrement=0.0,
               maxSegmentsPerCell=255,
               maxSynapsesPerSegment=255,
               globalDecay=0.10,
               maxAge=100000,
               pamLength=1,
               verbosity=0,
               outputType="normal",
               seed=42):
    """
    Translate parameters and initialize member variables specific to `backtracking_tm.py`.
    """
    super(MonitoredTMShim, self).__init__(
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
      maxSegmentsPerCell=maxSegmentsPerCell,
      maxSynapsesPerSegment=maxSynapsesPerSegment,
      seed=seed)

    self.infActiveState = {"t": None}


  def compute(self, bottomUpInput, enableLearn, computeInfOutput=None):
    """
    (From `backtracking_tm.py`)
    Handle one compute, possibly learning.

    @param bottomUpInput     The bottom-up input, typically from a spatial pooler
    @param enableLearn       If true, perform learning
    @param computeInfOutput  If None, default behavior is to disable the inference
                             output when enableLearn is on.
                             If true, compute the inference output
                             If false, do not compute the inference output
    """
    super(MonitoredTMShim, self).compute(set(bottomUpInput.nonzero()[0]),
                                         learn=enableLearn)
    numberOfCells = self.numberOfCells()

    activeState = numpy.zeros(numberOfCells)
    activeState[self.getActiveCells()] = 1
    self.infActiveState["t"] = activeState

    output = numpy.zeros(numberOfCells)
    output[self.getPredictiveCells() + self.getActiveCells()] = 1
    return output


  def topDownCompute(self, topDownIn=None):
    """
    (From `backtracking_tm.py`)
    Top-down compute - generate expected input given output of the TM

    @param topDownIn top down input from the level above us

    @returns best estimate of the TM input that would have generated bottomUpOut.
    """
    output = numpy.zeros(self.numberOfColumns())
    columns = [self.columnForCell(idx) for idx in self.getPredictiveCells()]
    output[columns] = 1
    return output


  def getActiveState(self):
    activeState = numpy.zeros(self.numberOfCells())
    activeState[self.getActiveCells()] = 1
    return activeState


  def getPredictedState(self):
    predictedState = numpy.zeros(self.numberOfCells())
    predictedState[self.getPredictiveCells()] = 1
    return predictedState


  def getLearnActiveStateT(self):
    state = numpy.zeros([self.numberOfColumns(), self.cellsPerColumn])
    return state



