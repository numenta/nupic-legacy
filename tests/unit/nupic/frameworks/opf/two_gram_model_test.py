# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""Unit tests for TwoGramModel.py."""

import tempfile
import unittest2 as unittest

from nupic.data import dict_utils
from nupic.frameworks.opf import opf_utils, two_gram_model

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.frameworks.opf.two_gram_model_capnp import TwoGramModelProto



class TwoGramModelTest(unittest.TestCase):
  """Unit tests for TwoGramModel."""


  def testBasicPredictions(self):
    encoders = {"a": {"fieldname": "a",
                      "maxval": 9,
                      "minval": 0,
                      "n": 10,
                      "w": 1,
                      "clipInput": True,
                      "forced": True,
                      "type": "ScalarEncoder"}}
    inferenceType = opf_utils.InferenceType.TemporalNextStep
    twoGramModel = two_gram_model.TwoGramModel(inferenceType, encoders)
    inputRecords = (dict_utils.DictObj(d) for d in ({"a": 5},
                                                    {"a": 6},
                                                    {"a": 5},
                                                    {"a": 6}))
    inferences = ((0,), (0,), (6,), (5,))
    for i, (inputRecord, expectedInference) in enumerate(zip(inputRecords,
                                                             inferences)):
      results = twoGramModel.run(inputRecord)
      self.assertEqual(results.predictionNumber, i)
      self.assertSequenceEqual(
          results.inferences[opf_utils.InferenceElement.prediction],
          expectedInference)


  def testSequenceReset(self):
    encoders = {"a": {"fieldname": u"a",
                      "maxval": 9,
                      "minval": 0,
                      "n": 10,
                      "w": 1,
                      "clipInput": True,
                      "forced": True,
                      "type": "ScalarEncoder"}}
    inferenceType = opf_utils.InferenceType.TemporalNextStep
    twoGramModel = two_gram_model.TwoGramModel(inferenceType, encoders)
    inputRecords = (dict_utils.DictObj(d) for d in ({"a": 5},
                                                    {"a": 6},
                                                    {"a": 5},
                                                    {"a": 6}))
    inferences = ((0,), (0,), (6,), (0,))
    resets = (False, False, True, False)
    for i, (inputRecord, expectedInference, reset) in enumerate(
        zip(inputRecords, inferences, resets)):
      if reset:
        twoGramModel.resetSequenceStates()
      results = twoGramModel.run(inputRecord)
      self.assertEqual(results.predictionNumber, i)
      self.assertSequenceEqual(
          results.inferences[opf_utils.InferenceElement.prediction],
          expectedInference)


  def testMultipleFields(self):
    encoders = {"a": {"fieldname": u"a",
                      "maxval": 9,
                      "minval": 0,
                      "n": 10,
                      "w": 1,
                      "clipInput": True,
                      "forced": True,
                      "type": "ScalarEncoder"},
                "b": {"fieldname": u"b",
                      "maxval": 9,
                      "minval": 0,
                      "n": 10,
                      "w": 1,
                      "clipInput": True,
                      "forced": True,
                      "type": "ScalarEncoder"}}
    inferenceType = opf_utils.InferenceType.TemporalNextStep
    twoGramModel = two_gram_model.TwoGramModel(inferenceType, encoders)
    inputRecords = (dict_utils.DictObj(d) for d in ({"a": 5, "b": 1},
                                                    {"a": 6, "b": 2},
                                                    {"a": 5, "b": 3},
                                                    {"a": 6, "b": 2}))
    inferences = ((0, 0), (0, 0), (6, 0), (5, 3))
    for i, (inputRecord, expectedInference) in enumerate(zip(inputRecords,
                                                             inferences)):
      results = twoGramModel.run(inputRecord)
      self.assertEqual(results.predictionNumber, i)
      self.assertSequenceEqual(
          results.inferences[opf_utils.InferenceElement.prediction],
          expectedInference)


  def testCategoryPredictions(self):
    encoders = {"a": {"fieldname": u"a",
                      "n": 10,
                      "w": 3,
                      "forced": True,
                      "type": "SDRCategoryEncoder"}}
    inferenceType = opf_utils.InferenceType.TemporalNextStep
    twoGramModel = two_gram_model.TwoGramModel(inferenceType, encoders)
    inputRecords = (dict_utils.DictObj(d) for d in ({"a": "A"},
                                                    {"a": "B"},
                                                    {"a": "A"},
                                                    {"a": "B"}))
    inferences = (("",), ("",), ("B",), ("A",))
    for i, (inputRecord, expectedInference) in enumerate(zip(inputRecords,
                                                             inferences)):
      results = twoGramModel.run(inputRecord)
      self.assertEqual(results.predictionNumber, i)
      self.assertSequenceEqual(
          results.inferences[opf_utils.InferenceElement.prediction],
          expectedInference)


  def testBucketedScalars(self):
    encoders = {"a": {"fieldname": u"a",
                      "maxval": 9,
                      "minval": 0,
                      "n": 2,
                      "w": 1,
                      "clipInput": True,
                      "forced": True,
                      "type": "ScalarEncoder"}}
    inferenceType = opf_utils.InferenceType.TemporalNextStep
    twoGramModel = two_gram_model.TwoGramModel(inferenceType, encoders)
    inputRecords = (dict_utils.DictObj(d) for d in ({"a": 5},
                                                    {"a": 6},
                                                    {"a": 5},
                                                    {"a": 4},
                                                    {"a": 6},
                                                    {"a": 7},
                                                    {"a": 3}))
    inferences = ((0,), (6,), (5,), (0,), (6,), (7,), (7,))
    for i, (inputRecord, expectedInference) in enumerate(zip(inputRecords,
                                                             inferences)):
      results = twoGramModel.run(inputRecord)
      self.assertEqual(results.predictionNumber, i)
      self.assertSequenceEqual(
          results.inferences[opf_utils.InferenceElement.prediction],
          expectedInference)


  @unittest.skipUnless(
    capnp, "pycapnp is not installed, skipping serialization test.")
  def testWriteRead(self):
    encoders = {"a": {"fieldname": u"a",
                      "maxval": 9,
                      "minval": 0,
                      "n": 10,
                      "w": 1,
                      "clipInput": True,
                      "forced": True,
                      "type": "ScalarEncoder"},
                "b": {"fieldname": u"b",
                      "maxval": 9,
                      "minval": 0,
                      "n": 10,
                      "w": 1,
                      "clipInput": True,
                      "forced": True,
                      "type": "ScalarEncoder"}}
    inferenceType = opf_utils.InferenceType.TemporalNextStep
    model = two_gram_model.TwoGramModel(inferenceType, encoders)
    inputRecords = (dict_utils.DictObj(d) for d in ({"a": 5, "b": 1},
                                                    {"a": 6, "b": 3},
                                                    {"a": 5, "b": 2},
                                                    {"a": 6, "b": 1}))
    inferences = ((0, 0), (0, 0), (6, 0), (5, 3))
    for i, (inputRecord, expectedInference) in enumerate(zip(inputRecords,
                                                             inferences)):
      results = model.run(inputRecord)
      self.assertEqual(results.predictionNumber, i)
      self.assertSequenceEqual(
        results.inferences[opf_utils.InferenceElement.prediction],
        expectedInference)

    proto = TwoGramModelProto.new_message()
    model.write(proto)
    with tempfile.TemporaryFile() as f:
      proto.write(f)
      f.seek(0)
      protoDeserialized = TwoGramModelProto.read(f)

    modelDeserialized = two_gram_model.TwoGramModel.read(protoDeserialized)

    self.assertEqual(model.getInferenceType(), inferenceType)
    self.assertEqual(modelDeserialized.getInferenceType(),
                     model.getInferenceType())

    self.assertSequenceEqual(modelDeserialized._prevValues,
                             model._prevValues)
    self.assertSequenceEqual(modelDeserialized._hashToValueDict,
                             model._hashToValueDict)
    self.assertSequenceEqual(modelDeserialized._fieldNames,
                             model._fieldNames)
    self.assertSequenceEqual(modelDeserialized._twoGramDicts,
                             model._twoGramDicts)

    for i, (inputRecord, expectedInference) in enumerate(zip(inputRecords,
                                                             inferences)):
      expected = model.run(inputRecord)
      actual = modelDeserialized.run(inputRecord)
      self.assertEqual(expected.predictionNumber, actual.predictionNumber)
      self.assertSequenceEqual(
        expected.inferences[opf_utils.InferenceElement.prediction],
        actual.inferences[opf_utils.InferenceElement.prediction])

if __name__ == "__main__":
  unittest.main()
