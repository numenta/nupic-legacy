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

"""Module containing the trivial predictor OPF model implementation. """

import itertools

from nupic.data import fieldmeta
from nupic.frameworks.opf import model
from nupic.frameworks.opf import opfutils
from opfutils import InferenceType


class PreviousValueModel(model.Model):
  """Previous value model."""

  def __init__(self, inferenceType=InferenceType.TemporalNextStep,
               fieldNames=[],
               fieldTypes=[],
               predictedField=None,
               predictionSteps=[]):
    """ PVM constructor.

    inferenceType: An opfutils.InferenceType value that specifies what type of
        inference (i.e. TemporalNextStep, TemporalMultiStep, etc.)
    fieldNames: a list of field names
    fieldTypes: a list of the types for the fields mentioned in fieldNames
    predictedField: the field from fieldNames which is to be predicted
    predictionSteps: a list of steps for which a prediction is made. This is
        only needed in the case of multi step predictions
    """
    super(PreviousValueModel, self).__init__(inferenceType)

    self._logger = opfutils.initLogger(self)
    self._predictedField = predictedField
    self._fieldNames = fieldNames
    self._fieldTypes = fieldTypes

    # only implement multistep and temporalnextstep
    if inferenceType == InferenceType.TemporalNextStep:
      self._predictionSteps = [1]
    elif inferenceType == InferenceType.TemporalMultiStep:
      self._predictionSteps = predictionSteps
    else:
      assert False, "Previous Value Model only works for next step or multi-step."

  def run(self, inputRecord):
    """Run one iteration of this model.

    Args:
      inputRecord: A record object formatted according to
          nupic.data.FileSource.getNext() result format.

    Returns:
      A ModelResult named tuple (see opfutils.py). The contents of
      ModelResult.inferences depends on the specific inference type of this
      model, which can be queried by getInferenceType().
      TODO: Implement getInferenceType()?
    """
    # set the results. note that there is no translation to sensorInput
    results = super(PreviousValueModel, self).run(inputRecord)
    results.sensorInput = opfutils.SensorInput(dataRow= \
      [inputRecord[fn] for fn in self._fieldNames])
    
    # select the current value for the prediction with probablity of 1
    results.inferences = { opfutils.InferenceElement.multiStepBestPredictions : \
                          dict((steps, inputRecord[self._predictedField]) \
                          for steps in self._predictionSteps),
                          opfutils.InferenceElement.multiStepPredictions : \
                          dict((steps, {inputRecord[self._predictedField] : 1}) \
                          for steps in self._predictionSteps)
    }

    # set the next step prediction if step of 1 is selected
    if 1 in self._predictionSteps:
      results.inferences[opfutils.InferenceElement.prediction] = \
      inputRecord[self._predictedField]
    
    return results

  def finishLearning(self):
    """Places the model in a permanent "finished learning" mode.

    The PVM does not learn, so this function has no effect.
    """
    pass


  def setFieldStatistics(self,fieldStats):
    """
    This method is used for the data source to communicate to the 
    model any statistics that it knows about the fields 
    Since the PVM has no use for this information, this is a no-op
    """
    pass

  def getFieldInfo(self):
    """Returns the metadata specifying the format of the model's output.

    The result may be different than the list of
    nupic.data.fieldmeta.FieldMetaInfo objects supplied at initialization due
    to the transcoding of some input fields into meta- fields, such as
    datetime -> dayOfWeek, timeOfDay, etc.
    """
    return tuple(fieldmeta.FieldMetaInfo(*args) for args in
                 itertools.izip(
                     self._fieldNames, self._fieldTypes,
                     itertools.repeat(fieldmeta.FieldMetaSpecial.none)))

  def getRuntimeStats(self):
    """Get the runtime statistics specific to the model.

    I.E. activeCellOverlapAvg

    Returns:
      A dict mapping statistic names to values.
    """
    # TODO: Add debugging stats.
    # > what sort of stats are we supposed to return?
    return dict()

  def _getLogger(self):
    """Get the logger created by this subclass.

    Returns:
      A logging.Logger object. Should not be None.
    """
    return self._logger

  def resetSequenceStates(self):
    """Called to indicate the start of a new sequence.

    The next call to run should not perform learning.
    """
    self._reset = True

  def __getstate__(self):
    del self._logger
    return self.__dict__

  def __setstate__(self):
    self._logger = opfutils.initLogger(self)
