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
import random

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
      predictionsGenerator = _getPredictionsGenerator(cls.examplesDir, example)
      for (oneStepPrediction, oneStepConfidence,
           fiveStepPrediction, fiveStepConfidence) in predictionsGenerator():
        cls.oneStepPredictions[example].append(oneStepPrediction)
        cls.oneStepConfidences[example].append(oneStepConfidence)
        cls.fiveStepPredictions[example].append(fiveStepPrediction)
        cls.fiveStepConfidences[example].append(fiveStepConfidence)


  def testExamplesDirExists(self):
    """Make sure the examples directory is in the correct location"""
    failMsg = "Path to examples does not exist: %s" % ExamplesTest.examplesDir
    self.assertTrue(os.path.exists(ExamplesTest.examplesDir), failMsg)


  @unittest.skip("Skip test until we figure out why we get different "
                 "results with OPF, Network and Algorithm APIs.")
  def testNumberOfOneStepPredictions(self):
    """Make sure all examples output the same number of oneStepPredictions."""

    self.assertEquals(len(ExamplesTest.oneStepPredictions["opf"]),
                      len(ExamplesTest.oneStepPredictions["algo"]))
    self.assertEquals(len(ExamplesTest.oneStepPredictions["opf"]),
                      len(ExamplesTest.oneStepPredictions["network"]))


  @unittest.skip("Skip test until we figure out why we get different "
                 "results with OPF, Network and Algorithm APIs.")
  def testOneStepPredictionsOpfVsAlgo(self):
    """Make sure one-step predictions are the same for OPF and Algo API."""
    for i in range(len(ExamplesTest.oneStepPredictions["opf"])):
      self.assertEquals(ExamplesTest.oneStepPredictions["opf"][i],
                        ExamplesTest.oneStepPredictions["algo"][i])


  @unittest.skip("Skip test until we figure out why we get different "
                 "results with OPF, Network and Algorithm APIs.")
  def testOneStepPredictionsOpfVsNetwork(self):
    """Make sure one-step predictions are the same for OPF and Network API."""
    for i in range(len(ExamplesTest.oneStepPredictions["opf"])):
      self.assertEquals(ExamplesTest.oneStepPredictions["opf"][i],
                        ExamplesTest.oneStepPredictions["network"][i])


  @unittest.skip("Skip test until we figure out why we get different "
                 "results with OPF, Network and Algorithm APIs.")
  def testOneStepPredictionsAlgoVsNetwork(self):
    """Make sure one-step predictions are the same for Algo and Network API."""
    for i in range(len(ExamplesTest.oneStepPredictions["algo"])):
      self.assertEquals(ExamplesTest.oneStepPredictions["algo"][i],
                        ExamplesTest.oneStepPredictions["network"][i])


  @unittest.skip("Skip test until we figure out why we get different "
                 "results with OPF, Network and Algorithm APIs.")
  def testFiveStepPredictionsOpfVsNetwork(self):
    """Make sure five-step predictions are the same for OPF and Network API."""
    for i in range(len(ExamplesTest.fiveStepPredictions["opf"])):
      self.assertEquals(ExamplesTest.fiveStepPredictions["opf"][i],
                        ExamplesTest.fiveStepPredictions["network"][i])


  @unittest.skip("Skip test until we figure out why we get different "
                 "results with OPF, Network and Algorithm APIs.")
  def testOneStepConfidencesOpfVsAlgo(self):
    """Make sure one-step confidences are the same for OPF and Algo API."""
    for i in range(len(ExamplesTest.oneStepConfidences["opf"])):
      self.assertEquals(ExamplesTest.oneStepConfidences["opf"][i],
                        ExamplesTest.oneStepConfidences["algo"][i])


  @unittest.skip("Skip test until we figure out why we get different "
                 "results with OPF, Network and Algorithm APIs.")
  def testOneStepConfidencesOpfVsNetwork(self):
    """Make sure one-step confidences are the same for OPF and Network API."""
    for i in range(len(ExamplesTest.oneStepConfidences["opf"])):
      self.assertEquals(ExamplesTest.oneStepConfidences["opf"][i],
                        ExamplesTest.oneStepConfidences["network"][i])


  @unittest.skip("Skip test until we figure out why we get different "
                 "results with OPF, Network and Algorithm APIs.")
  def testOneStepConfidencesAlgoVsNetwork(self):
    """Make sure one-step confidences are the same for Algo and Network API."""
    for i in range(len(ExamplesTest.oneStepConfidences["algo"])):
      self.assertEquals(ExamplesTest.oneStepConfidences["algo"][i],
                        ExamplesTest.oneStepConfidences["network"][i])


  @unittest.skip("Skip test until we figure out why we get different "
                 "results with OPF, Network and Algorithm APIs.")
  def testFiveStepConfidencesOpfVsNetwork(self):
    """Make sure five-step confidences are the same for OPF and Network API."""
    for i in range(len(ExamplesTest.fiveStepConfidences["opf"])):
      self.assertEquals(ExamplesTest.fiveStepConfidences["opf"][i],
                        ExamplesTest.fiveStepConfidences["network"][i])



if __name__ == '__main__':
  unittest.main()
