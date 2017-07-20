# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2016, Numenta, Inc.  Unless you have an agreement
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
