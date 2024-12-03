# Copyright 2015 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""Regression test that checks for differences in hotgym results.

If the prediction results differ then the test fails and must be
explicitly updated to match the new results.
"""

import collections
import csv
import os
import shutil
import unittest

from nupic.frameworks.opf import experiment_runner



class HotgymRegressionTest(unittest.TestCase):
  """Hotgym regression test to validate that predictions don't change."""


  def testHotgymRegression(self):
    experimentDir = os.path.join(
      os.path.dirname(__file__).partition(
        os.path.normpath("tests/integration/nupic/opf"))[0],
        "examples", "opf", "experiments", "multistep", "hotgym")

    resultsDir = os.path.join(experimentDir, "inference")
    savedModelsDir = os.path.join(experimentDir, "savedmodels")
    try:
      _model = experiment_runner.runExperiment([experimentDir])

      resultsPath = os.path.join(
          resultsDir, "DefaultTask.TemporalMultiStep.predictionLog.csv")
      with open(resultsPath) as f:
        reader = csv.reader(f)
        headers = reader.next()
        self.assertEqual(headers[14],
                         "multiStepBestPredictions:multiStep:errorMetric='aae':"
                         "steps=1:window=1000:field=consumption")
        lastRow = collections.deque(reader, 1)[0]

      # Changes that affect prediction results will cause this test to fail. If
      # the change is understood and reviewers agree that there has not been a
      # regression then this value can be updated to reflect the new result.
      self.assertAlmostEqual(float(lastRow[14]), 5.85504058885)

    finally:
      shutil.rmtree(resultsDir, ignore_errors=True)
      shutil.rmtree(savedModelsDir, ignore_errors=True)



if __name__ == "__main__":
  unittest.main()
