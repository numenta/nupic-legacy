# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

"""Regression test that checks for differences in hotgym results.

If the prediction results differ then the test fails and must be
explicitly updated to match the new results.
"""

import collections
import csv
import os
import pkg_resources
import shutil
import unittest

from nupic.frameworks.opf import experiment_runner



class HotgymRegressionTest(unittest.TestCase):
  """Hotgym regression test to validate that predictions don't change."""


  @unittest.skip("This currently fails on Travis. The issue is being tracked "
                 "at: https://github.com/numenta/nupic/issues/2358")
  def testHotgymRegression(self):
    experimentDir = pkg_resources.resource_filename(
        "nupic",
        os.path.join(os.pardir, "examples", "opf", "experiments", "multistep",
                     "hotgym")
    )

    resultsDir = os.path.join(experimentDir, "inference")
    savedModelsDir = os.path.join(experimentDir, "savedmodels")
    try:
      _model = experiment_runner.runExperiment([experimentDir])

      resultsPath = os.path.join(
          resultsDir, "DefaultTask.TemporalMultiStep.predictionLog.csv")
      with open(resultsPath) as f:
        reader = csv.reader(f)
        headers = reader.next()
        self.assertEqual(headers[12],
                         "multiStepBestPredictions:multiStep:errorMetric='aae':"
                         "steps=1:window=1000:field=consumption")
        lastRow = collections.deque(reader, 1)[0]

      # Changes that affect prediction results will cause this test to fail.
      # If the change is understood and reviewers agree that there has not been a
      # regression then this value can be updated to reflect the new result.
      self.assertAlmostEqual(float(lastRow[12]), 6.0933712258)

    finally:
      shutil.rmtree(resultsDir, ignore_errors=True)
      shutil.rmtree(savedModelsDir, ignore_errors=True)



if __name__ == "__main__":
  unittest.main()
