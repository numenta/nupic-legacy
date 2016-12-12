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

"""Unit tests for TwoGramModel.py."""

import unittest2 as unittest

from nupic.data import dictutils
from nupic.frameworks.opf import opfutils, two_gram_model



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
    inferenceType = opfutils.InferenceType.TemporalNextStep
    twoGramModel = two_gram_model.TwoGramModel(inferenceType, encoders)
    inputRecords = (dictutils.DictObj(d) for d in ({"a": 5},
                                                   {"a": 6},
                                                   {"a": 5},
                                                   {"a": 6}))
    inferences = ((0,), (0,), (6,), (5,))
    for i, (inputRecord, expectedInference) in enumerate(zip(inputRecords,
                                                             inferences)):
      results = twoGramModel.run(inputRecord)
      self.assertEqual(results.predictionNumber, i)
      self.assertSequenceEqual(
          results.inferences[opfutils.InferenceElement.prediction],
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
    inferenceType = opfutils.InferenceType.TemporalNextStep
    twoGramModel = two_gram_model.TwoGramModel(inferenceType, encoders)
    inputRecords = (dictutils.DictObj(d) for d in ({"a": 5},
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
          results.inferences[opfutils.InferenceElement.prediction],
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
    inferenceType = opfutils.InferenceType.TemporalNextStep
    twoGramModel = two_gram_model.TwoGramModel(inferenceType, encoders)
    inputRecords = (dictutils.DictObj(d) for d in ({"a": 5, "b": 1},
                                                   {"a": 6, "b": 2},
                                                   {"a": 5, "b": 3},
                                                   {"a": 6, "b": 2}))
    inferences = ((0, 0), (0, 0), (6, 0), (5, 3))
    for i, (inputRecord, expectedInference) in enumerate(zip(inputRecords,
                                                             inferences)):
      results = twoGramModel.run(inputRecord)
      self.assertEqual(results.predictionNumber, i)
      self.assertSequenceEqual(
          results.inferences[opfutils.InferenceElement.prediction],
          expectedInference)


  def testCategoryPredictions(self):
    encoders = {"a": {"fieldname": u"a",
                      "n": 10,
                      "w": 3,
		      "forced": True,
                      "type": "SDRCategoryEncoder"}}
    inferenceType = opfutils.InferenceType.TemporalNextStep
    twoGramModel = two_gram_model.TwoGramModel(inferenceType, encoders)
    inputRecords = (dictutils.DictObj(d) for d in ({"a": "A"},
                                                   {"a": "B"},
                                                   {"a": "A"},
                                                   {"a": "B"}))
    inferences = (("",), ("",), ("B",), ("A",))
    for i, (inputRecord, expectedInference) in enumerate(zip(inputRecords,
                                                             inferences)):
      results = twoGramModel.run(inputRecord)
      self.assertEqual(results.predictionNumber, i)
      self.assertSequenceEqual(
          results.inferences[opfutils.InferenceElement.prediction],
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
    inferenceType = opfutils.InferenceType.TemporalNextStep
    twoGramModel = two_gram_model.TwoGramModel(inferenceType, encoders)
    inputRecords = (dictutils.DictObj(d) for d in ({"a": 5},
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
          results.inferences[opfutils.InferenceElement.prediction],
          expectedInference)



if __name__ == "__main__":
  unittest.main()
