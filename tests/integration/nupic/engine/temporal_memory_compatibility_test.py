# Copyright 2016 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import json
import unittest
import numpy

from nupic.regions.tm_region import TMRegion

from network_creation_common import createAndRunNetwork



class TemporalMemoryCompatibilityTest(unittest.TestCase):

  def testTMPyCpp(self):
    """
    Test compatibility between C++ and Python TM implementation.
    """
    results1 = createAndRunNetwork(TMRegion,
                                   "bottomUpOut",
                                   checkpointMidway=False,
                                   temporalImp="tm_cpp")

    results2 = createAndRunNetwork(TMRegion,
                                   "bottomUpOut",
                                   checkpointMidway=False,
                                   temporalImp="tm_py")

    self.compareArrayResults(results1, results2)


  def compareArrayResults(self, results1, results2):
    self.assertEqual(len(results1), len(results2))

    for i in xrange(len(results1)):
      result1 = list(results1[i].nonzero()[0])
      result2 = list(results2[i].nonzero()[0])

      self.assertEqual(result1, result2,
        "Row {0} not equal: {1} vs. {2}".format(i, result1, result2))



if __name__ == "__main__":
  unittest.main()
