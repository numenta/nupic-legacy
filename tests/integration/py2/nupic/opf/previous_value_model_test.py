#! /usr/bin/env python
# ----------------------------------------------------------------------
#  Copyright (C) 2006,2007,2010 Numenta Inc. All rights reserved.
#
#  The information and source code contained herein is the
#  exclusive property of Numenta Inc. No part of this software
#  may be used, reproduced, stored or distributed in any form,
#  without explicit written authorization from Numenta Inc.
# ----------------------------------------------------------------------

"""
## @file
This file tests the operation of the Previous Value Model.
"""

import unittest2 as unittest

from nupic.data import dictutils
from nupic.frameworks.opf import opfutils, previousvaluemodel
from nupic.support.unittesthelpers.testcasebase import (TestCaseBase,
                                                        TestOptionParser)

SEQUENCE_LENGTH = 100


################################################################################
# Functions that generate the datasets

def _generateIncreasing():
  return [i for i in range(SEQUENCE_LENGTH)]

def _generateDecreasing():
  return [SEQUENCE_LENGTH - i for i in range(SEQUENCE_LENGTH)]

def _generateSaw():
  return [i % 3 for i in range(SEQUENCE_LENGTH)]


class PreviousValueModelTest(TestCaseBase):
  """Unit test for the Previous Value Model."""

  #-----------------------------------------------------------------------------
  # Methods that run the model for either next step or multistep

  def _runNextStep(self, data):
    model = previousvaluemodel.PreviousValueModel(
      opfutils.InferenceType.TemporalNextStep, predictedField = 'a')

    inputRecords = (dictutils.DictObj({'a' : d}) for d in data)

    for i, (inputRecord, expectedInference) in enumerate(zip(inputRecords,
                                                             data)):
      results = model.run(inputRecord)
      self.assertEqual(results.predictionNumber, i)
      self.assertEqual(results.inferences[
        opfutils.InferenceElement.prediction], expectedInference)
      self.assertEqual(results.inferences[
        opfutils.InferenceElement.multiStepBestPredictions][1],
        expectedInference)

  def _runMultiStep(self, data):
    model = previousvaluemodel.PreviousValueModel(
      opfutils.InferenceType.TemporalMultiStep, predictedField = 'a',
      predictionSteps = [1, 3, 5])

    inputRecords = (dictutils.DictObj({'a' : d}) for d in data)

    for i, (inputRecord, expectedInference) in enumerate(zip(inputRecords,
                                                             data)):
      results = model.run(inputRecord)
      self.assertEqual(results.predictionNumber, i)
      self.assertEqual(results.inferences[
        opfutils.InferenceElement.prediction], expectedInference)
      self.assertEqual(results.inferences[
        opfutils.InferenceElement.multiStepBestPredictions][1],
        expectedInference)
      self.assertEqual(results.inferences[
        opfutils.InferenceElement.multiStepBestPredictions][3],
        expectedInference)
      self.assertEqual(results.inferences[
        opfutils.InferenceElement.multiStepBestPredictions][5],
        expectedInference)

  #-----------------------------------------------------------------------------
  # Methods that are called by the unittest framework

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

##############################################################################
if __name__ == '__main__':
  
  parser = TestOptionParser()
  parser.parse_args()
  unittest.main()
