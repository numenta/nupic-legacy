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

from nupic.regions.CLAClassifierRegion import CLAClassifierRegion
from nupic.regions.CLAClassifierRegion_capnp import CLAClassifierRegionProto



class CLAClassifierRegionTest(unittest.TestCase):
  """Tests for CLA classifier region"""


  def testWriteRead(self):
    clRegion1 = CLAClassifierRegion(steps='1', alpha=0.1, clVerbosity=0,
                                    implementation='py')
    clRegion1.learningMode = True
    clRegion1.inferenceMode = True

    # Create a vector of input bit indices
    input = [1, 5, 9]
    result1 = clRegion1.customCompute(recordNum=0, patternNZ=input,
                                      classification={
                                          'bucketIdx': 4,
                                          'actValue': 34.7})

    proto1 = CLAClassifierRegionProto.new_message()
    clRegion1.write(proto1)

    # Write the proto to a temp file and read it back into a new proto
    with tempfile.TemporaryFile() as f:
      proto1.write(f)
      f.seek(0)
      proto2 = CLAClassifierRegionProto.read(f)

    # Load the deserialized proto
    clRegion2 = CLAClassifierRegion.read(proto2)

    self.assertEqual(clRegion1, clRegion1)

    result1 = clRegion1.customCompute(recordNum=1, patternNZ=input,
                                      classification={
                                          'bucketIdx': 4,
                                          'actValue': 34.7})
    result2 = clRegion2.customCompute(recordNum=1, patternNZ=input,
                                      classification={
                                          'bucketIdx': 4,
                                          'actValue': 34.7})

    self.assertEqual(result1.keys(), result2.keys())
    for key in result1.keys():
      for i in xrange(len(clRegion1._claClassifier._actualValues)):
        self.assertAlmostEqual(result1[key][i], result2[key][i], 5)



if __name__ == "__main__":
  unittest.main()
