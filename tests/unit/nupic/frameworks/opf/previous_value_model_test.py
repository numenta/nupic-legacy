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
This file tests the operation of the Previous Value Model.
"""

import unittest2 as unittest

from nupic.data import dict_utils
from nupic.frameworks.opf import opf_utils, previous_value_model

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.frameworks.opf.previous_value_model_capnp import (
    PreviousValueModelProto)



SEQUENCE_LENGTH = 100



def _generateIncreasing():
  return [i for i in range(SEQUENCE_LENGTH)]



def _generateDecreasing():
  return [SEQUENCE_LENGTH - i for i in range(SEQUENCE_LENGTH)]



def _generateSaw():
  return [i % 3 for i in range(SEQUENCE_LENGTH)]



class PreviousValueModelTest(unittest.TestCase):
  """Unit test for the Previous Value Model."""


  def _runNextStep(self, data):
    model = previous_value_model.PreviousValueModel(
      opf_utils.InferenceType.TemporalNextStep, predictedField ='a')

    inputRecords = (dict_utils.DictObj({'a' : d}) for d in data)

    for i, (inputRecord, expectedInference) in enumerate(zip(inputRecords,
                                                             data)):
      results = model.run(inputRecord)
      self.assertEqual(results.predictionNumber, i)
      self.assertEqual(results.inferences[
        opf_utils.InferenceElement.prediction], expectedInference)
      self.assertEqual(results.inferences[
        opf_utils.InferenceElement.multiStepBestPredictions][1],
                       expectedInference)


  def _runMultiStep(self, data):
    model = previous_value_model.PreviousValueModel(
      opf_utils.InferenceType.TemporalMultiStep, predictedField ='a',
      predictionSteps = [1, 3, 5])

    inputRecords = (dict_utils.DictObj({'a' : d}) for d in data)

    for i, (inputRecord, expectedInference) in enumerate(zip(inputRecords,
                                                             data)):
      results = model.run(inputRecord)
      self.assertEqual(results.predictionNumber, i)
      self.assertEqual(results.inferences[
        opf_utils.InferenceElement.prediction], expectedInference)
      self.assertEqual(results.inferences[
        opf_utils.InferenceElement.multiStepBestPredictions][1],
                       expectedInference)
      self.assertEqual(results.inferences[
        opf_utils.InferenceElement.multiStepBestPredictions][3],
                       expectedInference)
      self.assertEqual(results.inferences[
        opf_utils.InferenceElement.multiStepBestPredictions][5],
                       expectedInference)


  def testNextStepIncreasing(self):
    self._runNextStep(_generateIncreasing())


  def testNextStepDecreasing(self):
    self._runNextStep(_generateDecreasing())


  def testNextStepSaw(self):
    self._runNextStep(_generateSaw())


  def testMultiStepIncreasing(self):
    self._runMultiStep(_generateIncreasing())


  def testMultiStepDecreasing(self):
    self._runMultiStep(_generateDecreasing())


  def testMultiStepSaw(self):
    self._runMultiStep(_generateSaw())


  @unittest.skipUnless(
    capnp, "pycapnp is not installed, skipping serialization test.")
  def testCapnpWriteRead(self):
    m1 = previous_value_model.PreviousValueModel(
      opf_utils.InferenceType.TemporalMultiStep, predictedField ='a',
      predictionSteps = [1, 3, 5])

    m1.run(dict_utils.DictObj({'a' : 0}))

    # Serialize
    builderProto = PreviousValueModelProto.new_message()
    m1.write(builderProto)

    # Construct reader from populated builder
    readerProto = PreviousValueModelProto.from_bytes(builderProto.to_bytes())

    # Deserialize
    m2 = previous_value_model.PreviousValueModel.read(readerProto)

    self.assertIs(m1.getSchema(), PreviousValueModelProto)
    self.assertIs(m2.getSchema(), PreviousValueModelProto)

    self.assertEqual(m2._numPredictions, m1._numPredictions)
    self.assertEqual(m2.getInferenceType(), m1.getInferenceType())
    self.assertEqual(m2.isLearningEnabled(), m1.isLearningEnabled())
    self.assertEqual(m2.isInferenceEnabled(), m1.isInferenceEnabled())
    self.assertEqual(m2.getInferenceArgs(), m1.getInferenceArgs())
    self.assertEqual(m2._predictedField, m1._predictedField)
    self.assertEqual(m2._fieldNames, m1._fieldNames)
    self.assertEqual(m2._fieldTypes, m1._fieldTypes)
    self.assertEqual(m2._predictionSteps, m1._predictionSteps)

    # Run computes on m1 & m2 and compare results
    r1 = m1.run(dict_utils.DictObj({'a' : 1}))
    r2 = m2.run(dict_utils.DictObj({'a' : 1}))

    self.assertEqual(r2.predictionNumber, r1.predictionNumber)
    self.assertEqual(r2.rawInput, r1.rawInput)

    self.assertEqual(r2.predictionNumber, r1.predictionNumber)
    self.assertEqual(r2.inferences[opf_utils.InferenceElement.prediction],
                     r1.inferences[opf_utils.InferenceElement.prediction])
    self.assertEqual(
      r2.inferences[opf_utils.InferenceElement.multiStepBestPredictions][1],
      r1.inferences[opf_utils.InferenceElement.multiStepBestPredictions][1])
    self.assertEqual(
      r2.inferences[opf_utils.InferenceElement.multiStepBestPredictions][3],
      r1.inferences[opf_utils.InferenceElement.multiStepBestPredictions][3])
    self.assertEqual(
      r2.inferences[opf_utils.InferenceElement.multiStepBestPredictions][5],
      r1.inferences[opf_utils.InferenceElement.multiStepBestPredictions][5])



if __name__ == '__main__':
  unittest.main()
