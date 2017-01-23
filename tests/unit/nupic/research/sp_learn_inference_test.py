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
from nupic.research.spatial_pooler import SpatialPooler
from nupic.research.fdrutilities import spDiff

realDType = GetNTAReal()



class SPLearnInferenceTest(unittest.TestCase):
  """Test to check that inference calls do not affect learning."""


  def _runLearnInference(self,
                         n=30,
                         w=15,
                         columnDimensions=2048,
                         numActiveColumnsPerInhArea=40,
                         spSeed=1951,
                         spVerbosity=0,
                         numTrainingRecords=100,
                         seed=42):
    # Instantiate two identical spatial pooler. One will be used only for
    # learning. The other will be trained with identical records, but with
    # random inference calls thrown in
    spLearnOnly = SpatialPooler(
        columnDimensions=(columnDimensions, 1),
        inputDimensions=(1, n),
        potentialRadius=n/2,
        numActiveColumnsPerInhArea=numActiveColumnsPerInhArea,
        spVerbosity=spVerbosity,
        seed=spSeed,
        synPermInactiveDec=0.01,
        synPermActiveInc=0.2,
        synPermConnected=0.11,)

    spLearnInfer = SpatialPooler(
        columnDimensions=(columnDimensions, 1),
        inputDimensions=(1, n),
        potentialRadius=n/2,
        numActiveColumnsPerInhArea=numActiveColumnsPerInhArea,
        spVerbosity=spVerbosity,
        seed=spSeed,
        synPermInactiveDec=0.01,
        synPermActiveInc=0.2,
        synPermConnected=0.11,)

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
      # TODO: See https://github.com/numenta/nupic/issues/2072
      encodedInput = inputs[i]
      decodedOutput = np.zeros(columnDimensions)
      spLearnOnly.compute(encodedInput, learn=True, activeArray=decodedOutput)

    random.seed(seed)
    np.random.seed(seed)
    for i in xrange(numTrainingRecords):
      if spVerbosity > 0:
        print "Input #%d" % i
      # TODO: See https://github.com/numenta/nupic/issues/2072
      encodedInput = inputs[i]
      decodedOutput = np.zeros(columnDimensions)
      spLearnInfer.compute(encodedInput, learn=True, activeArray=decodedOutput)

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


  @unittest.skip("Currently fails due to switch from FDRCSpatial2 to SpatialPooler."
                 "The new SP doesn't have explicit methods to get inference.")
  # TODO: See https://github.com/numenta/nupic/issues/2072
  def testLearnInference(self):
    self._runLearnInference(n=50, w=15)



if __name__ == "__main__":
  unittest.main()
