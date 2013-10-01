#!/usr/bin/env python
# ----------------------------------------------------------------------
#  Copyright (C) 2012 Numenta Inc. All rights reserved.
#
#  The information and source code contained herein is the
#  exclusive property of Numenta Inc. No part of this software
#  may be used, reproduced, stored or distributed in any form,
#  without explicit written authorization from Numenta Inc.
# ----------------------------------------------------------------------
import unittest2 as unittest

from nupic.data import dictutils
from nupic.frameworks.opf import opfutils, two_gram_model
from nupic.support.unittesthelpers import testcasebase

"""Unit tests for TwoGramModel.py."""


class TwoGramModelTest(testcasebase.TestCaseBase):
  """Unit tests for TwoGramModel."""

  def testBasicPredictions(self):
    encoders = {'a': {'fieldname': 'a',
                      'maxval': 9,
                      'minval': 0,
                      'n': 10,
                      'w': 1,
                      'clipInput': True,
                      'type': 'ScalarEncoder'}}
    inferenceType = opfutils.InferenceType.TemporalNextStep
    twoGramModel = two_gram_model.TwoGramModel(inferenceType, encoders)
    inputRecords = (dictutils.DictObj(d) for d in ({'a': 5},
                                                   {'a': 6},
                                                   {'a': 5},
                                                   {'a': 6}))
    inferences = ((0,), (0,), (6,), (5,))
    for i, (inputRecord, expectedInference) in enumerate(zip(inputRecords,
                                                             inferences)):
      results = twoGramModel.run(inputRecord)
      self.assertEqual(results.predictionNumber, i)
      self.assertSequenceEqual(
          results.inferences[opfutils.InferenceElement.prediction],
          expectedInference)

  def testSequenceReset(self):
    encoders = {'a': {'fieldname': u'a',
                      'maxval': 9,
                      'minval': 0,
                      'n': 10,
                      'w': 1,
                      'clipInput': True,
                      'type': 'ScalarEncoder'}}
    inferenceType = opfutils.InferenceType.TemporalNextStep
    twoGramModel = two_gram_model.TwoGramModel(inferenceType, encoders)
    inputRecords = (dictutils.DictObj(d) for d in ({'a': 5},
                                                   {'a': 6},
                                                   {'a': 5},
                                                   {'a': 6}))
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
    encoders = {'a': {'fieldname': u'a',
                      'maxval': 9,
                      'minval': 0,
                      'n': 10,
                      'w': 1,
                      'clipInput': True,
                      'type': 'ScalarEncoder'},
                'b': {'fieldname': u'b',
                      'maxval': 9,
                      'minval': 0,
                      'n': 10,
                      'w': 1,
                      'clipInput': True,
                      'type': 'ScalarEncoder'}}
    inferenceType = opfutils.InferenceType.TemporalNextStep
    twoGramModel = two_gram_model.TwoGramModel(inferenceType, encoders)
    inputRecords = (dictutils.DictObj(d) for d in ({'a': 5, 'b': 1},
                                                   {'a': 6, 'b': 2},
                                                   {'a': 5, 'b': 3},
                                                   {'a': 6, 'b': 2}))
    inferences = ((0, 0), (0, 0), (6, 0), (5, 3))
    for i, (inputRecord, expectedInference) in enumerate(zip(inputRecords,
                                                             inferences)):
      results = twoGramModel.run(inputRecord)
      self.assertEqual(results.predictionNumber, i)
      self.assertSequenceEqual(
          results.inferences[opfutils.InferenceElement.prediction],
          expectedInference)

  def testCategoryPredictions(self):
    encoders = {'a': {'fieldname': u'a',
                      'n': 10,
                      'w': 3,
                      'type': 'SDRCategoryEncoder'}}
    inferenceType = opfutils.InferenceType.TemporalNextStep
    twoGramModel = two_gram_model.TwoGramModel(inferenceType, encoders)
    inputRecords = (dictutils.DictObj(d) for d in ({'a': 'A'},
                                                   {'a': 'B'},
                                                   {'a': 'A'},
                                                   {'a': 'B'}))
    inferences = (('',), ('',), ('B',), ('A',))
    for i, (inputRecord, expectedInference) in enumerate(zip(inputRecords,
                                                             inferences)):
      results = twoGramModel.run(inputRecord)
      self.assertEqual(results.predictionNumber, i)
      self.assertSequenceEqual(
          results.inferences[opfutils.InferenceElement.prediction],
          expectedInference)

  def testBucketedScalars(self):
    encoders = {'a': {'fieldname': u'a',
                      'maxval': 9,
                      'minval': 0,
                      'n': 2,
                      'w': 1,
                      'clipInput': True,
                      'type': 'ScalarEncoder'}}
    inferenceType = opfutils.InferenceType.TemporalNextStep
    twoGramModel = two_gram_model.TwoGramModel(inferenceType, encoders)
    inputRecords = (dictutils.DictObj(d) for d in ({'a': 5},
                                                   {'a': 6},
                                                   {'a': 5},
                                                   {'a': 4},
                                                   {'a': 6},
                                                   {'a': 7},
                                                   {'a': 3}))
    inferences = ((0,), (6,), (5,), (0,), (6,), (7,), (7,))
    for i, (inputRecord, expectedInference) in enumerate(zip(inputRecords,
                                                             inferences)):
      results = twoGramModel.run(inputRecord)
      self.assertEqual(results.predictionNumber, i)
      self.assertSequenceEqual(
          results.inferences[opfutils.InferenceElement.prediction],
          expectedInference)


if __name__ == '__main__':
  parser = testcasebase.TestOptionParser()
  parser.parse_args()
  unittest.main()
