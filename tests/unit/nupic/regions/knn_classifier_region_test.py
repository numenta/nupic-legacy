#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have purchased from
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

from nupic.regions.KNNClassifierRegion import KNNClassifierRegion
from nupic.regions.KNNClassifierRegion_capnp import KNNClassifierRegionProto



class KNNClassifierRegionTest(unittest.TestCase):
  """Tests for KNN classifier region"""


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
    knnRegion1 = KNNClassifierRegion(k=1, distanceNorm=1.0, useSparseMemory=True,
                                     SVDSampleCount=numSVDSamples, SVDDimCount=1)
    knnRegion1.learningMode = True
    knnRegion1.inferenceMode = False

    for i in patternDict.keys():
      inputs = dict()
      inputs['bottomUpIn'] = patternDict[i]['pattern']
      inputs['categoryIn'] = [patternDict[i]['category']]
      knnRegion1.compute(inputs, outputs=None)

    proto1 = KNNClassifierRegionProto.new_message()
    knnRegion1.write(proto1)

    # Write the proto to a temp file and read it back into a new proto
    with tempfile.TemporaryFile() as f:
      proto1.write(f)
      f.seek(0)
      proto2 = KNNClassifierRegionProto.read(f)

    # Load the deserialized proto
    knnRegion2 = KNNClassifierRegion.read(proto2)

    self.assertEqual(knnRegion1, knnRegion2)

    knnRegion1.learningMode = False
    knnRegion2.learningMode = False
    knnRegion1.inferenceMode = True
    knnRegion2.inferenceMode = True
    outputs1 = dict()
    outputs2 = dict()
    for i in patternDict.keys():
      inputs = dict()
      inputs['bottomUpIn'] = patternDict[i]['pattern']
      inputs['categoryIn'] = [patternDict[i]['category']]
      outputs2['categoriesOut'] = outputs1['categoriesOut'] = numpy.zeros(numClasses)
      outputs2['categoryProbabilitiesOut'] = outputs1['categoryProbabilitiesOut'] = numpy.zeros(numClasses)
      knnRegion1.compute(inputs, outputs1)
      knnRegion2.compute(inputs, outputs2)
      self.assertEqual(outputs1, outputs2)


if __name__ == "__main__":
  unittest.main()
