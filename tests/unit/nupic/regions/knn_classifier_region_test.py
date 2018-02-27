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
"""Unit tests for the KNNClassifier region."""

import tempfile
import unittest

import numpy as np
from nupic.regions.knn_classifier_region import KNNClassifierRegion

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.regions.knn_classifier_region_capnp import KNNClassifierRegionProto



class KNNClassifierRegionTest(unittest.TestCase):
  """KNNClassifierRegion unit tests."""


  @unittest.skipUnless(
    capnp, "pycapnp is not installed, skipping serialization test.")
  def testWriteRead(self):
    knn = KNNClassifierRegion(distanceMethod="norm", SVDDimCount=2,
                              SVDSampleCount=2, useSparseMemory=True,
                              minSparsity=0.1, distThreshold=0.1)

    a = np.zeros(40)
    a[[1, 3, 7, 11, 13, 17, 19, 23, 29]] = 1
    b = np.zeros(40)
    b[[2, 4, 8, 12, 14, 18, 20, 28, 30]] = 1
    c = np.zeros(40)
    c[[1, 2, 3, 14, 16, 19, 22, 24, 33]] = 1
    d = np.zeros(40)
    d[[2, 4, 8, 12, 14, 19, 22, 24, 33]] = 1

    knn.setParameter('learningMode', None, True)

    outputs = {
      "categoriesOut": np.zeros((1,)),
      "bestPrototypeIndices": np.zeros((1,)),
      "categoryProbabilitiesOut": np.zeros((1,))
    }

    input_a = {
      'categoryIn': [0],
      'bottomUpIn': a
    }
    knn.compute(input_a, outputs)

    input_b = {
      'categoryIn': [1],
      'bottomUpIn': b
    }
    knn.compute(input_b, outputs)

    input_c = {
      'categoryIn': [2],
      'bottomUpIn': c,
      'partitionIn': [211]
    }
    knn.compute(input_c, outputs)

    input_d = {
      'categoryIn': [1],
      'bottomUpIn': d,
      'partitionIn': [405]
    }
    knn.compute(input_d, outputs)

    knn.setParameter('learningMode', None, False)
    knn.setParameter('inferenceMode', None, True)

    proto = KNNClassifierRegionProto.new_message()
    knn.writeToProto(proto)

    with tempfile.TemporaryFile() as f:
      proto.write(f)
      f.seek(0)
      protoDeserialized = KNNClassifierRegionProto.read(f)

    knnDeserialized = KNNClassifierRegion.readFromProto(protoDeserialized)
    expected = {
      "categoriesOut": np.zeros((1,)),
      "bestPrototypeIndices": np.zeros((1,)),
      "categoryProbabilitiesOut": np.zeros((1,))
    }

    actual = {
      "categoriesOut": np.zeros((1,)),
      "bestPrototypeIndices": np.zeros((1,)),
      "categoryProbabilitiesOut": np.zeros((1,))
    }

    knn.compute(input_a, expected)
    knnDeserialized.compute(input_a, actual)
    self.assertItemsEqual(actual, expected)

    knn.compute(input_d, expected)
    knnDeserialized.compute(input_a, actual)
    self.assertItemsEqual(actual, expected)



if __name__ == "__main__":
  unittest.main()
