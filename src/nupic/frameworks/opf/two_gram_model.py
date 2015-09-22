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
from nupic.data import fieldmeta
from nupic.frameworks.opf import model
from nupic.frameworks.opf import opfutils
from opfutils import InferenceType


class TwoGramModel(model.Model):
  """Two-gram benchmark model."""

  def __init__(self, inferenceType=InferenceType.TemporalNextStep,
               encoderParams=()):
    """ Two-gram model constructor.

    inferenceType: An opfutils.InferenceType value that specifies what type of
        inference (i.e. TemporalNextStep, Classification, etc.)
    encoders: Sequence of encoder params dictionaries.
    """
    super(TwoGramModel, self).__init__(inferenceType)

    self._logger = opfutils.initLogger(self)
    self._reset = False
    self._hashToValueDict = dict()
    self._learningEnabled = True
    self._encoder = encoders.MultiEncoder(encoderParams)
    self._fieldNames = self._encoder.getScalarNames()
    self._prevValues = [None] * len(self._fieldNames)
    self._twoGramDicts = [dict() for _ in xrange(len(self._fieldNames))]

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
    results = super(TwoGramModel, self).run(inputRecord)

    # Set up the lists of values, defaults, and encoded values.
    values = [inputRecord[k] for k in self._fieldNames]
    defaults = ['' if type(v) == str else 0 for v in values]
    inputFieldEncodings = self._encoder.encodeEachField(inputRecord)
    inputBuckets = self._encoder.getBucketIndices(inputRecord)

    results.sensorInput = opfutils.SensorInput(
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
    results.inferences[opfutils.InferenceElement.prediction] = predictions
    results.inferences[opfutils.InferenceElement.encodings] = encodedPredictions

    self._prevValues = inputBuckets
    self._reset = False
    return results

  def finishLearning(self):
    """Places the model in a permanent "finished learning" mode.

    Once called, the model will not be able to learn from subsequent input
    records. Learning may not be resumed on a given instance of the model once
    this is called as the implementation may optimize itself by pruning data
    structures that are necessary for learning.
    """
    self._learningEnabled = False

  def setFieldStatistics(self,fieldStats):
    """
    This method is used for the data source to communicate to the 
    model any statistics that it knows about the fields 
    Since the two-gram has no use for this information, this is a no-op
    """
    pass

  def getFieldInfo(self):
    """Returns the metadata specifying the format of the model's output.

    The result may be different than the list of
    nupic.data.fieldmeta.FieldMetaInfo objects supplied at initialization due
    to the transcoding of some input fields into meta- fields, such as
    datetime -> dayOfWeek, timeOfDay, etc.
    """
    fieldTypes = self._encoder.getDecoderOutputFieldTypes()
    assert len(self._fieldNames) == len(fieldTypes)

    return tuple(fieldmeta.FieldMetaInfo(*args) for args in
                 itertools.izip(
                     self._fieldNames, fieldTypes,
                     itertools.repeat(fieldmeta.FieldMetaSpecial.none)))

  def getRuntimeStats(self):
    """Get the runtime statistics specific to the model.

    I.E. activeCellOverlapAvg

    Returns:
      A dict mapping statistic names to values.
    """
    # TODO: Add debugging stats.
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
