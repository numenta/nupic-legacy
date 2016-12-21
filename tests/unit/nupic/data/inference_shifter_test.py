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

"""Unit tests for InferenceShifter."""

from nupic.data.inference_shifter import InferenceShifter
from nupic.frameworks.opf.opfutils import InferenceElement, ModelResult
from nupic.support.unittesthelpers.testcasebase import (TestCaseBase,
                                                        unittest)


class TestInferenceShifter(TestCaseBase):

  def _shiftAndCheck(self, inferences, expectedOutput):
    inferenceShifter = InferenceShifter()
    for inference, expected in zip(inferences, expectedOutput):
      inputResult = ModelResult(inferences=inference)
      outputResult = inferenceShifter.shift(inputResult)
      self.assertEqual(outputResult.inferences, expected)

  def testNoShift(self):
    for element in (InferenceElement.anomalyScore,
                    InferenceElement.classification,
                    InferenceElement.classConfidences):
      inferences = [
          {element: 1},
          {element: 2},
          {element: 3},
      ]
      expectedOutput = [
          {element: 1},
          {element: 2},
          {element: 3},
      ]
      self._shiftAndCheck(inferences, expectedOutput)

  def testNoShiftMultipleValues(self):
    for element in (InferenceElement.anomalyScore,
                    InferenceElement.classification,
                    InferenceElement.classConfidences):
      inferences = [
          {element: [1, 2, 3]},
          {element: [4, 5, 6]},
          {element: [5, 6, 7]},
      ]
      expectedOutput = [
          {element: [1, 2, 3]},
          {element: [4, 5, 6]},
          {element: [5, 6, 7]},
      ]
      self._shiftAndCheck(inferences, expectedOutput)

  def testSingleShift(self):
    for element in (InferenceElement.prediction,
                    InferenceElement.encodings):
      inferences = [
          {element: 1},
          {element: 2},
          {element: 3},
      ]
      expectedOutput = [
          {element: None},
          {element: 1},
          {element: 2},
      ]
      self._shiftAndCheck(inferences, expectedOutput)

  def testSingleShiftMultipleValues(self):
    for element in (InferenceElement.prediction,
                    InferenceElement.encodings):
      inferences = [
          {element: [1, 2, 3]},
          {element: [4, 5, 6]},
          {element: [5, 6, 7]},
      ]
      expectedOutput = [
          {element: [None, None, None]},
          {element: [1, 2, 3]},
          {element: [4, 5, 6]},
      ]
      self._shiftAndCheck(inferences, expectedOutput)

  def testMultiStepShift(self):
    for element in (InferenceElement.multiStepPredictions,
                    InferenceElement.multiStepBestPredictions):
      inferences = [
          {element: {2: 1}},
          {element: {2: 2}},
          {element: {2: 3}},
          {element: {2: 4}},
      ]
      expectedOutput = [
          {element: {2: None}},
          {element: {2: None}},
          {element: {2: 1}},
          {element: {2: 2}},
      ]
      self._shiftAndCheck(inferences, expectedOutput)

  def testMultiStepShiftMultipleValues(self):
    for element in (InferenceElement.multiStepPredictions,
                    InferenceElement.multiStepBestPredictions):
      inferences = [
          {element: {2: [1, 11]}},
          {element: {2: [2, 12]}},
          {element: {2: [3, 13]}},
          {element: {2: [4, 14]}},
      ]
      expectedOutput = [
          {element: {2: None}},
          {element: {2: None}},
          {element: {2: [1, 11]}},
          {element: {2: [2, 12]}},
      ]
      self._shiftAndCheck(inferences, expectedOutput)

  def testDifferentMultiStepsShift(self):
    for element in (InferenceElement.multiStepPredictions,
                    InferenceElement.multiStepBestPredictions):
      inferences = [
          {element: {2: 1, 3: 5}},
          {element: {2: 2, 3: 6}},
          {element: {2: 3, 3: 7}},
          {element: {2: 4, 3: 8}},
      ]
      expectedOutput = [
          {element: {2: None, 3: None}},
          {element: {2: None, 3: None}},
          {element: {2: 1, 3: None}},
          {element: {2: 2, 3: 5}},
      ]
      self._shiftAndCheck(inferences, expectedOutput)

  def testDifferentMultiStepsShiftMultipleValues(self):
    for element in (InferenceElement.multiStepPredictions,
                    InferenceElement.multiStepBestPredictions):
      inferences = [
          {element: {2: [1, 11], 3: [5, 15]}},
          {element: {2: [2, 12], 3: [6, 16]}},
          {element: {2: [3, 13], 3: [7, 17]}},
          {element: {2: [4, 14], 3: [8, 18]}},
      ]
      expectedOutput = [
          {element: {2: None, 3: None}},
          {element: {2: None, 3: None}},
          {element: {2: [1, 11], 3: None}},
          {element: {2: [2, 12], 3: [5, 15]}},
      ]
      self._shiftAndCheck(inferences, expectedOutput)


if __name__ == '__main__':
  unittest.main()
