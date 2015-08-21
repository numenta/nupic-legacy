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

"""TimeShifter class for shifting ModelResults."""

import collections
import copy

from nupic.frameworks.opf.opfutils import InferenceElement, ModelResult


class InferenceShifter(object):
  """Shifts time for ModelResult objects."""

  def __init__(self):
    self._inferenceBuffer = None

  def shift(self, modelResult):
    """Shift the model result and return the new instance.

    Queues up the T(i+1) prediction value and emits a T(i)
    input/prediction pair, if possible. E.g., if the previous T(i-1)
    iteration was learn-only, then we would not have a T(i) prediction in our
    FIFO and would not be able to emit a meaningful input/prediction pair.

    Args:
      modelResult: A ModelResult instance to shift.
    Returns:
      A ModelResult instance.
    """
    inferencesToWrite = {}

    if self._inferenceBuffer is None:
      maxDelay = InferenceElement.getMaxDelay(modelResult.inferences)
      self._inferenceBuffer = collections.deque(maxlen=maxDelay + 1)

    self._inferenceBuffer.appendleft(copy.deepcopy(modelResult.inferences))

    for inferenceElement, inference in modelResult.inferences.iteritems():
      if isinstance(inference, dict):
        inferencesToWrite[inferenceElement] = {}
        for key, _ in inference.iteritems():
          delay = InferenceElement.getTemporalDelay(inferenceElement, key)
          if len(self._inferenceBuffer) > delay:
            prevInference = self._inferenceBuffer[delay][inferenceElement][key]
            inferencesToWrite[inferenceElement][key] = prevInference
          else:
            inferencesToWrite[inferenceElement][key] = None
      else:
        delay = InferenceElement.getTemporalDelay(inferenceElement)
        if len(self._inferenceBuffer) > delay:
          inferencesToWrite[inferenceElement] = (
              self._inferenceBuffer[delay][inferenceElement])
        else:
          if type(inference) in (list, tuple):
            inferencesToWrite[inferenceElement] = [None] * len(inference)
          else:
            inferencesToWrite[inferenceElement] = None

    shiftedResult = ModelResult(rawInput=modelResult.rawInput,
                                sensorInput=modelResult.sensorInput,
                                inferences=inferencesToWrite,
                                metrics=modelResult.metrics,
                                predictedFieldIdx=modelResult.predictedFieldIdx,
                                predictedFieldName=modelResult.predictedFieldName)
    return shiftedResult
