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

"""TMRegion unit tests."""

import tempfile
import unittest

try:
  import capnp
except ImportError:
  capnp = None
import numpy as np

from nupic.regions.tm_region import TMRegion
if capnp:
  from nupic.regions.tm_region_capnp import TMRegionProto



class TMRegionTest(unittest.TestCase):


  def checkTMRegionImpl(self, impl):
    output1 = {
      "bottomUpOut": np.zeros((40,)),
      "topDownOut": np.zeros((10,)),
      "activeCells": np.zeros((40,)),
      "predictedActiveCells": np.zeros((40,)),
      "anomalyScore": np.zeros((1,)),
      "lrnActiveStateT": np.zeros((40,)),
    }
    output2 = {
      "bottomUpOut": np.zeros((40,)),
      "topDownOut": np.zeros((10,)),
      "activeCells": np.zeros((40,)),
      "predictedActiveCells": np.zeros((40,)),
      "anomalyScore": np.zeros((1,)),
      "lrnActiveStateT": np.zeros((40,)),
    }

    a = np.zeros(10, dtype="int32")
    a[[1, 3, 7]] = 1
    b = np.zeros(10, dtype="int32")
    b[[2, 4, 8]] = 1

    inputA = {
      "bottomUpIn": a,
      "resetIn": np.zeros(1),
      "sequenceIdIn": np.zeros(1),
    }
    inputB = {
      "bottomUpIn": b,
      "resetIn": np.zeros(1),
      "sequenceIdIn": np.zeros(1),
    }

    region1 = TMRegion(10, 10, 4, temporalImp=impl)
    region1.initialize()
    region1.compute(inputA, output1)

    proto1 = TMRegionProto.new_message()
    region1.writeToProto(proto1)
    with tempfile.TemporaryFile() as f:
      proto1.write(f)
      f.seek(0)
      proto2 = TMRegionProto.read(f)
    region2 = TMRegion.readFromProto(proto2)

    region1.compute(inputB, output1)
    region2.compute(inputB, output2)

    self.assertTrue(np.array_equal(output1["bottomUpOut"],
                                   output2["bottomUpOut"]))
    self.assertTrue(np.array_equal(output1["topDownOut"],
                                   output2["topDownOut"]))
    self.assertTrue(np.array_equal(output1["activeCells"],
                                   output2["activeCells"]))
    self.assertTrue(np.array_equal(output1["predictedActiveCells"],
                                   output2["predictedActiveCells"]))
    self.assertTrue(np.array_equal(output1["anomalyScore"],
                                   output2["anomalyScore"]))
    self.assertTrue(np.array_equal(output1["lrnActiveStateT"],
                                   output2["lrnActiveStateT"]))


  @unittest.skipUnless(
    capnp, "pycapnp is not installed, skipping serialization test.")
  def testWriteReadPy(self):
    self.checkTMRegionImpl("py")


  @unittest.skipUnless(
    capnp, "pycapnp is not installed, skipping serialization test.")
  def testWriteReadCpp(self):
    self.checkTMRegionImpl("cpp")


  @unittest.skipUnless(
    capnp, "pycapnp is not installed, skipping serialization test.")
  def testWriteReadTMPy(self):
    self.checkTMRegionImpl("tm_py")


  @unittest.skipUnless(
    capnp, "pycapnp is not installed, skipping serialization test.")
  def testWriteReadTMCpp(self):
    self.checkTMRegionImpl("tm_cpp")



if __name__ == "__main__":
  unittest.main()
