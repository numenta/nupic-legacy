#!/usr/bin/env python
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

import tempfile
import unittest2 as unittest

import capnp
import numpy

from nupic.algorithms import KNNClassifier_capnp
from nupic.algorithms.KNNClassifier import KNNClassifier
from nupic.test.test_framework_helpers import assertInstancesAlmostEqual



class KNNClassifierTest(unittest.TestCase):
  """Tests for k Nearest Neighbor classifier"""
  

  def testWriteRead(self):
    numPatterns = numpy.random.randint(300, 600)
    numClasses = numpy.random.randint(50, 150)
    patterns = numpy.random.rand(numPatterns, 100)
    patternDict = dict()

    for i in xrange(numPatterns):
      randCategory = numpy.random.randint(0, numClasses-1)
      patternDict[i] = dict()
      patternDict[i]['pattern'] = patterns[i]
      patternDict[i]['category'] = randCategory

    numSVDSamples = int(.1 * numPatterns)
    knn1 = KNNClassifier(k=1, distanceNorm=1.0, useSparseMemory=True,
                         numSVDSamples=numSVDSamples, numSVDDims=1)
    for i in patternDict.keys():
      knn1.learn(patternDict[i]['pattern'], patternDict[i]['category'])

    proto1 = KNNClassifier_capnp.KNNClassifierProto.new_message()
    knn1.write(proto1)

    # Write the proto to a temp file and read it back into a new proto
    with tempfile.TemporaryFile() as f:
      proto1.write(f)
      f.seek(0)
      proto2 = KNNClassifier_capnp.KNNClassifierProto.read(f)

    # Load the deserialized proto
    knn2 = KNNClassifier.read(proto2)

    assertInstancesAlmostEqual(self, "", knn1, knn2,
                               classesToCompare=[KNNClassifier])

    for i in patternDict.keys():
      winner1, inferenceResult1, dist1, categoryDist1 \
        = knn1.infer(patternDict[i]['pattern'])
      winner2, inferenceResult2, dist2, categoryDist2 \
        = knn2.infer(patternDict[i]['pattern'])

      self.assertEqual(winner1, winner2)
      self.assertTrue(numpy.array_equal(inferenceResult1, inferenceResult2))
      for i in xrange(len(dist1)):
        self.assertAlmostEqual(dist1[i], dist2[i], 5)
      for i in xrange(len(categoryDist1)):
        self.assertAlmostEqual(categoryDist1[i], categoryDist2[i], 5)



if __name__ == "__main__":
  unittest.main()
