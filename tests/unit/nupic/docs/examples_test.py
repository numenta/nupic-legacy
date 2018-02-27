# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2017, Numenta, Inc.  Unless you have an agreement
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

"""Unit tests for all quick-start examples in the NuPIC docs."""

import os
import sys
import unittest2 as unittest
import numpy as np
from numpy.testing import assert_approx_equal

import random

MAX_PREDICTIONS = 100
SEED = 42
random.seed(SEED)
np.random.seed(SEED)


def _getPredictionsGenerator(examplesDir, exampleName):
  """
  Get predictions generator for one of the quick-start example. 

  .. note::

    The examples are not part of the nupic package so we need to manually 
    append the example module path to syspath.

  :param examplesDir: 
    (str) path to the example parent directory.
  :param exampleName: 
    (str) name of the example. E.g: "opf", "network", "algo".
  :return predictionsGenerator: 
    (function) predictions generator functions. 
  """

  sys.path.insert(0, os.path.join(examplesDir, exampleName))
  modName = "complete-%s-example" % exampleName
  mod = __import__(modName, fromlist=["runHotgym"])
  return getattr(mod, "runHotgym")



class ExamplesTest(unittest.TestCase):
  """Unit tests for all quick-start examples."""

  examples = ["opf", "network", "algo"]
  oneStepPredictions = {example: [] for example in examples}
  oneStepConfidences = {example: [] for example in examples}
  fiveStepPredictions = {example: [] for example in examples}
  fiveStepConfidences = {example: [] for example in examples}

  docsTestsPath = os.path.dirname(os.path.abspath(__file__))
  examplesDir = os.path.join(docsTestsPath, os.path.pardir,
                             os.path.pardir, os.path.pardir,
                             os.path.pardir, "docs", "examples")


  @classmethod
  def setUpClass(cls):
    """Get the predictions and prediction confidences for all examples."""
    for example in cls.examples:
      predictionGenerator = _getPredictionsGenerator(cls.examplesDir, example)
      for prediction in predictionGenerator(MAX_PREDICTIONS):
        cls.oneStepPredictions[example].append(prediction[0])
        cls.oneStepConfidences[example].append(prediction[1])
        cls.fiveStepPredictions[example].append(prediction[2])
        cls.fiveStepConfidences[example].append(prediction[3])


  def testExamplesDirExists(self):
    """Make sure the examples directory is in the correct location"""
    failMsg = "Path to examples does not exist: %s" % ExamplesTest.examplesDir
    self.assertTrue(os.path.exists(ExamplesTest.examplesDir), failMsg)


  def testNumberOfOneStepPredictions(self):
    """Make sure all examples output the same number of oneStepPredictions."""

    self.assertEquals(len(ExamplesTest.oneStepPredictions["opf"]),
                      len(ExamplesTest.oneStepPredictions["algo"]))
    self.assertEquals(len(ExamplesTest.oneStepPredictions["opf"]),
                      len(ExamplesTest.oneStepPredictions["network"]))

  @unittest.expectedFailure
  def testOneStepPredictionsOpfVsAlgo(self):
    """Make sure one-step predictions are the same for OPF and Algo API."""
    for resultPair in zip(self.oneStepPredictions["opf"],
                          self.oneStepPredictions["algo"]):
      assert_approx_equal(*resultPair,
                          err_msg="one-step 'opf' and 'algo' differ")

  @unittest.expectedFailure
  def testOneStepPredictionsOpfVsNetwork(self):
    """Make sure one-step predictions are the same for OPF and Network API."""
    for resultPair in zip(self.oneStepPredictions["opf"],
                          self.oneStepPredictions["network"]):
      assert_approx_equal(*resultPair,
                          err_msg="one-step 'opf' and 'network' differ")

  @unittest.expectedFailure
  def testOneStepPredictionsAlgoVsNetwork(self):
    """Make sure one-step predictions are the same for Algo and Network API."""
    for resultPair in zip(self.oneStepPredictions["algo"],
                          self.oneStepPredictions["network"]):
      assert_approx_equal(*resultPair,
                          err_msg="one-step 'algo' and 'network' differ")

  @unittest.expectedFailure
  def testFiveStepPredictionsOpfVsNetwork(self):
    """Make sure five-step predictions are the same for OPF and Network API."""
    for resultPair in zip(self.fiveStepPredictions["opf"],
                          self.fiveStepPredictions["network"]):
      assert_approx_equal(*resultPair,
                          err_msg="five-step 'opf' and 'network' differ")

  @unittest.expectedFailure
  def testOneStepConfidencesOpfVsAlgo(self):
    """Make sure one-step confidences are the same for OPF and Algo API."""
    for resultPair in zip(self.oneStepConfidences["opf"],
                          self.oneStepConfidences["algo"]):
      assert_approx_equal(*resultPair,
                          err_msg="one-step 'opf' and 'algo' differ")

  @unittest.expectedFailure
  def testOneStepConfidencesOpfVsNetwork(self):
    """Make sure one-step confidences are the same for OPF and Network API."""
    for resultPair in zip(self.oneStepConfidences["opf"],
                          self.oneStepConfidences["network"]):
      assert_approx_equal(*resultPair,
                          err_msg="one-step 'opf' and 'network' differ")

  @unittest.expectedFailure
  def testOneStepConfidencesAlgoVsNetwork(self):
    """Make sure one-step confidences are the same for Algo and Network API."""
    for resultPair in zip(self.oneStepConfidences["algo"],
                          self.oneStepConfidences["network"]):
      assert_approx_equal(*resultPair,
                          err_msg="one-step 'algo' and 'network' differ")

  @unittest.expectedFailure
  def testFiveStepConfidencesOpfVsNetwork(self):
    """Make sure five-step confidences are the same for OPF and Network API."""
    for resultPair in zip(self.fiveStepConfidences["opf"],
                          self.fiveStepConfidences["network"]):
      assert_approx_equal(*resultPair,
                          err_msg="five-step 'opf' and 'network' differ")



if __name__ == '__main__':
  unittest.main()
