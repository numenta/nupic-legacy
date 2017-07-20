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
