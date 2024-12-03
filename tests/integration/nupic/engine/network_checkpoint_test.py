# Copyright 2016 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import unittest
import numpy

from nupic.regions.record_sensor import RecordSensor
from nupic.regions.sp_region import SPRegion
from nupic.regions.tm_region import TMRegion

from network_creation_common import createAndRunNetwork

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.proto import NetworkProto_capnp



class NetworkCheckpointTest(unittest.TestCase):

  @unittest.skipUnless(
      capnp, "pycapnp is not installed, skipping serialization test.")
  def testSensorRegion(self):
    results1 = createAndRunNetwork(RecordSensor, "dataOut")

    results2 = createAndRunNetwork(RecordSensor, "dataOut",
                                   checkpointMidway=True)

    self.compareArrayResults(results1, results2)


  @unittest.skipUnless(
      capnp, "pycapnp is not installed, skipping serialization test.")
  def testSPRegion(self):
    results1 = createAndRunNetwork(SPRegion, "bottomUpOut")

    results2 = createAndRunNetwork(SPRegion, "bottomUpOut",
                                   checkpointMidway=True)

    self.assertEqual(len(results1), len(results2))

    for i in xrange(len(results1)):
      result1 = list(results1[i].nonzero()[0])
      result2 = list(results2[i].nonzero()[0])
      self.assertEqual(result1, result2,
        "Row {0} not equal: {1} vs. {2}".format(i, result1, result2))


  @unittest.skipUnless(
    capnp, "pycapnp is not installed, skipping serialization test.")
  def testTMRegion(self):
    results1 = createAndRunNetwork(TMRegion, "bottomUpOut",
                                   checkpointMidway=False,
                                   temporalImp="tm_py")

    results2 = createAndRunNetwork(TMRegion, "bottomUpOut",
                                   checkpointMidway=True,
                                   temporalImp="tm_py")

    self.assertEqual(len(results1), len(results2))

    for i in xrange(len(results1)):
      result1 = list(results1[i].nonzero()[0])
      result2 = list(results2[i].nonzero()[0])
      self.assertEqual(result1, result2,
                       "Row {0} not equal: {1} vs. {2}".format(i, result1, result2))


  def compareArrayResults(self, results1, results2):
    self.assertEqual(len(results1), len(results2))

    for i in xrange(len(results1)):
      result1 = list(results1[i].nonzero()[0])
      result2 = list(results2[i].nonzero()[0])

      self.assertEqual(result1, result2,
        "Row {0} not equal: {1} vs. {2}".format(i, result1, result2))



if __name__ == "__main__":
  unittest.main()
