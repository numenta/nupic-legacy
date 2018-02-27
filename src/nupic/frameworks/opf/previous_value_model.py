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

from nupic.data import field_meta
from nupic.frameworks.opf import model
from nupic.frameworks.opf import opf_utils
from opf_utils import InferenceType

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.frameworks.opf.previous_value_model_capnp import (
    PreviousValueModelProto)



class PreviousValueModel(model.Model):
  """
  Previous value model.

  :param inferenceType: (:class:`nupic.frameworks.opf.opf_utils.InferenceType`)

  :param fieldNames: a list of field names

  :param fieldTypes: a list of the types for the fields mentioned in
         ``fieldNames``

  :param predictedField: the field from ``fieldNames`` which is to be predicted

  :param predictionSteps: a list of steps for which a prediction is made. This is
      only needed in the case of multi step predictions. For example, to get
      predictions 1, 5, and 10 steps ahead: ``[1,5,10]``.

  """

  def __init__(self, inferenceType=InferenceType.TemporalNextStep,
               fieldNames=[],
               fieldTypes=[],
               predictedField=None,
               predictionSteps=[]):
    super(PreviousValueModel, self).__init__(inferenceType)

    self._logger = opf_utils.initLogger(self)
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
    # set the results. note that there is no translation to sensorInput
    results = super(PreviousValueModel, self).run(inputRecord)
    results.sensorInput = opf_utils.SensorInput(dataRow= \
      [inputRecord[fn] for fn in self._fieldNames])

    # select the current value for the prediction with probablity of 1
    results.inferences = {opf_utils.InferenceElement.multiStepBestPredictions : \
                          dict((steps, inputRecord[self._predictedField]) \
                          for steps in self._predictionSteps),
                          opf_utils.InferenceElement.multiStepPredictions : \
                          dict((steps, {inputRecord[self._predictedField] : 1}) \
                          for steps in self._predictionSteps)
                          }

    # set the next step prediction if step of 1 is selected
    if 1 in self._predictionSteps:
      results.inferences[opf_utils.InferenceElement.prediction] = \
      inputRecord[self._predictedField]

    return results

  def finishLearning(self):
    """
    The PVM does not learn, so this function has no effect.
    """
    pass


  def setFieldStatistics(self,fieldStats):
    """
    Since the PVM has no use for this information, this is a no-op
    """
    pass

  def getFieldInfo(self):
    return tuple(field_meta.FieldMetaInfo(*args) for args in
                 itertools.izip(
                     self._fieldNames, self._fieldTypes,
                     itertools.repeat(field_meta.FieldMetaSpecial.none)))

  def getRuntimeStats(self):
    # TODO: Add debugging stats.
    # > what sort of stats are we supposed to return?
    return dict()

  def _getLogger(self):
    return self._logger

  def resetSequenceStates(self):
    self._reset = True


  @staticmethod
  def getSchema():
    return PreviousValueModelProto


  def write(self, proto):
    """ Serialize via capnp

    :param proto: capnp PreviousValueModelProto message builder
    """
    super(PreviousValueModel, self).writeBaseToProto(proto.modelBase)

    proto.fieldNames = self._fieldNames
    proto.fieldTypes = self._fieldTypes
    proto.predictedField = self._predictedField
    proto.predictionSteps = self._predictionSteps


  @classmethod
  def read(cls, proto):
    """Deserialize via capnp

    :param proto: capnp PreviousValueModelProto message reader

    :returns: new instance of PreviousValueModel deserialized from the given
              proto
    """
    instance = object.__new__(cls)
    super(PreviousValueModel, instance).__init__(proto=proto.modelBase)

    instance._logger = opf_utils.initLogger(instance)

    instance._predictedField = proto.predictedField
    instance._fieldNames = list(proto.fieldNames)
    instance._fieldTypes = list(proto.fieldTypes)
    instance._predictionSteps = list(proto.predictionSteps)

    return instance


  def __getstate__(self):
    # NOTE This deletion doesn't seem to make sense, as someone might want to
    # serialize and then continue to use the model instance.
    del self._logger
    return self.__dict__

  def __setstate__(self):
    self._logger = opf_utils.initLogger(self)
