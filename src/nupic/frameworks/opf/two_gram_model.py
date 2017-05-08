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

"""Module containing the two gram OPF model implementation. """

import collections
import itertools

from nupic import encoders
from nupic.data import field_meta
from nupic.frameworks.opf import model
from nupic.frameworks.opf import opf_utils
from opf_utils import InferenceType


class TwoGramModel(model.Model):
  """
  Two-gram benchmark model.

  :param inferenceType: (:class:`nupic.frameworks.opf.opf_utils.InferenceType`)
  :param encoders: a dict of dicts, eventually sent to
         :meth:`~nupic.encoders.multi.MultiEncoder.addMultipleEncoders` (see
         there for details).
  """

  def __init__(self, inferenceType=InferenceType.TemporalNextStep,
               encoderParams=()):
    super(TwoGramModel, self).__init__(inferenceType)

    self._logger = opf_utils.initLogger(self)
    self._reset = False
    self._hashToValueDict = dict()
    self._learningEnabled = True
    self._encoder = encoders.MultiEncoder(encoderParams)
    self._fieldNames = self._encoder.getScalarNames()
    self._prevValues = [None] * len(self._fieldNames)
    self._twoGramDicts = [dict() for _ in xrange(len(self._fieldNames))]

  def run(self, inputRecord):
    results = super(TwoGramModel, self).run(inputRecord)

    # Set up the lists of values, defaults, and encoded values.
    values = [inputRecord[k] for k in self._fieldNames]
    defaults = ['' if type(v) == str else 0 for v in values]
    inputFieldEncodings = self._encoder.encodeEachField(inputRecord)
    inputBuckets = self._encoder.getBucketIndices(inputRecord)

    results.sensorInput = opf_utils.SensorInput(
        dataRow=values, dataEncodings=inputFieldEncodings,
        sequenceReset=int(self._reset))

    # Keep track of the last value associated with each encoded value for that
    # predictions can be returned in the original value format.
    for value, bucket in itertools.izip(values, inputBuckets):
      self._hashToValueDict[bucket] = value

    # Update the two-gram dict if learning is enabled.
    for bucket, prevValue, twoGramDict in itertools.izip(
        inputBuckets, self._prevValues, self._twoGramDicts):
      if self._learningEnabled and not self._reset:
        if prevValue not in twoGramDict:
          twoGramDict[prevValue] = collections.defaultdict(int)
        twoGramDict[prevValue][bucket] += 1

    # Populate the results.inferences dict with the predictions and encoded
    # predictions.
    predictions = []
    encodedPredictions = []
    for bucket, twoGramDict, default, fieldName in (
        itertools.izip(inputBuckets, self._twoGramDicts, defaults,
                       self._fieldNames)):
      if bucket in twoGramDict:
        probabilities = twoGramDict[bucket].items()
        prediction = self._hashToValueDict[
            max(probabilities, key=lambda x: x[1])[0]]
        predictions.append(prediction)
        encodedPredictions.append(self._encoder.encodeField(fieldName,
                                                            prediction))
      else:
        predictions.append(default)
        encodedPredictions.append(self._encoder.encodeField(fieldName,
                                                            default))
    results.inferences = dict()
    results.inferences[opf_utils.InferenceElement.prediction] = predictions
    results.inferences[opf_utils.InferenceElement.encodings] = encodedPredictions

    self._prevValues = inputBuckets
    self._reset = False
    return results

  def finishLearning(self):
    self._learningEnabled = False

  def setFieldStatistics(self,fieldStats):
    """
    Since the two-gram has no use for this information, this is a no-op
    """
    pass

  def getFieldInfo(self):
    fieldTypes = self._encoder.getDecoderOutputFieldTypes()
    assert len(self._fieldNames) == len(fieldTypes)

    return tuple(field_meta.FieldMetaInfo(*args) for args in
                 itertools.izip(
                     self._fieldNames, fieldTypes,
                     itertools.repeat(field_meta.FieldMetaSpecial.none)))

  def getRuntimeStats(self):
    # TODO: Add debugging stats.
    return dict()

  def _getLogger(self):
    return self._logger

  def resetSequenceStates(self):
    self._reset = True

  def __getstate__(self):
    del self._logger
    return self.__dict__

  def __setstate__(self):
    self._logger = opf_utils.initLogger(self)
