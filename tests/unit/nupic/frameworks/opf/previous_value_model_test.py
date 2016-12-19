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

from nupic.data import dictutils
from nupic.frameworks.opf import opfutils, previousvaluemodel

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



if __name__ == '__main__':
  unittest.main()
