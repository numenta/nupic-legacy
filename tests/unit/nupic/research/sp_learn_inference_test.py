#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
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

"""
This test intermixes learning and inference calls. It checks that inserting
random inference calls have no effect on learning.

TODO: implement an SP Diff routine.  That should be fun!
"""

import cPickle as pickle
import numpy as np
import random
import time

import unittest2 as unittest

from nupic.bindings.math import GetNTAReal
from nupic.research import FDRCSpatial2
from nupic.research.fdrutilities import spDiff

realDType = GetNTAReal()



class SPLearnInferenceTest(unittest.TestCase):
  """Test to check that inference calls do not affect learning."""


  def _runLearnInference(self,
                         n=30,
                         w=15,
                         coincidencesShape=2048,
                         numActivePerInhArea=40,
                         spSeed=1951,
                         spVerbosity=0,
                         numTrainingRecords=100,
                         seed=42):
    # Instantiate two identical spatial pooler. One will be used only for
    # learning. The other will be trained with identical records, but with
    # random inference calls thrown in
    spLearnOnly = FDRCSpatial2.FDRCSpatial2(
        coincidencesShape=(coincidencesShape, 1),
        inputShape=(1, n),
        inputBorder=n/2 - 1,
        coincInputRadius=n/2,
        numActivePerInhArea=numActivePerInhArea,
        spVerbosity=spVerbosity,
        seed=spSeed,
        synPermInactiveDec=0.01,
        synPermActiveInc=0.2,)

    spLearnInfer = FDRCSpatial2.FDRCSpatial2(
        coincidencesShape=(coincidencesShape, 1),
        inputShape=(1, n),
        inputBorder=n/2 - 1,
        coincInputRadius=n/2,
        numActivePerInhArea=numActivePerInhArea,
        spVerbosity=spVerbosity,
        seed=spSeed,
        synPermInactiveDec=0.01,
        synPermActiveInc=0.2,)

    random.seed(seed)
    np.random.seed(seed)

    # Build up training set with numTrainingRecords patterns
    inputs = []         # holds post-encoded input patterns
    for i in xrange(numTrainingRecords):
      inputVector = np.zeros(n, dtype=realDType)
      inputVector [random.sample(xrange(n), w)] = 1
      inputs.append(inputVector)

    # Train each SP with identical inputs
    startTime = time.time()

    random.seed(seed)
    np.random.seed(seed)
    for i in xrange(numTrainingRecords):
      if spVerbosity > 0:
        print "Input #%d" % i
      encodedInput = inputs[i]

      spLearnOnly.compute(encodedInput, learn=True, infer=False)

    random.seed(seed)
    np.random.seed(seed)
    for i in xrange(numTrainingRecords):
      if spVerbosity > 0:
        print "Input #%d" % i
      encodedInput = inputs[i]
      spLearnInfer.compute(encodedInput, learn=True, infer=False)

    print "\nElapsed time: %.2f seconds\n" % (time.time() - startTime)

    # Test that both SP"s are identical by checking learning stats
    # A more in depth test would check all the coincidences, duty cycles, etc.
    # ala tpDiff
    # Edit: spDiff has been written as an in depth tester of the spatial pooler
    learnOnlyStats = spLearnOnly.getLearningStats()
    learnInferStats = spLearnInfer.getLearningStats()

    success = True
    # Check that the two spatial poolers are equivalent after the same training.
    success = success and spDiff(spLearnInfer, spLearnOnly)
    self.assertTrue(success)
    # Make sure that the pickled and loaded SPs are equivalent.
    spPickle = pickle.dumps(spLearnOnly, protocol=0)
    spLearnOnlyLoaded = pickle.loads(spPickle)
    success = success and spDiff(spLearnOnly, spLearnOnlyLoaded)
    self.assertTrue(success)
    for k in learnOnlyStats.keys():
      if learnOnlyStats[k] != learnInferStats[k]:
        success = False
        print "Stat", k, "is different:", learnOnlyStats[k], learnInferStats[k]

    self.assertTrue(success)
    if success:
      print "Test succeeded"


  def testLearnInference(self):
    self._runLearnInference(n=50, w=15)



if __name__ == "__main__":
  unittest.main()
