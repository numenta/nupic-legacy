# Copyright 2014 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""
 This test demonstrates building and running
 a two node network. Some features demonstrated include:

 - Can add regions to network and set dimensions
 - Linking induces dimensions correctly
 - Network computation happens in correct order
 - Direct (zero-copy) access to outputs
 - Linking correctly maps outputs to inputs
"""

import logging
import unittest2 as unittest

from nupic.engine import Network, Dimensions

LOGGER = logging.getLogger(__name__)



class NetworkTwoNodeTest(unittest.TestCase):


  def testTwoNode(self):
    # =====================================================
    # Build and run the network
    # =====================================================

    net = Network()
    level1 = net.addRegion("level1", "TestNode", "{int32Param: 15}")
    dims = Dimensions([6, 4])
    level1.setDimensions(dims)

    level2 = net.addRegion("level2", "TestNode", "{real64Param: 128.23}")

    net.link("level1", "level2", "TestFanIn2", "")

    # Could call initialize here, but not necessary as net.run()
    # initializes implicitly.
    # net.initialize()

    net.run(1)
    LOGGER.info("Successfully created network and ran for one iteration")

    # =====================================================
    # Check everything
    # =====================================================
    dims = level1.getDimensions()
    self.assertEquals(len(dims), 2)
    self.assertEquals(dims[0], 6)
    self.assertEquals(dims[1], 4)

    dims = level2.getDimensions()
    self.assertEquals(len(dims), 2)
    self.assertEquals(dims[0], 3)
    self.assertEquals(dims[1], 2)

    # Check L1 output. "False" means don't copy, i.e.
    # get a pointer to the actual output
    # Actual output values are determined by the TestNode
    # compute() behavior.
    l1output = level1.getOutputData("bottomUpOut")
    self.assertEquals(len(l1output), 48) # 24 nodes; 2 values per node
    for i in xrange(24):
      self.assertEquals(l1output[2*i], 0)      # size of input to each node is 0
      self.assertEquals(l1output[2*i+1], i)    # node number

    # check L2 output.
    l2output = level2.getOutputData("bottomUpOut", )
    self.assertEquals(len(l2output), 12) # 6 nodes; 2 values per node
    # Output val = node number + sum(inputs)
    # Can compute from knowing L1 layout
    #
    #  00 01 | 02 03 | 04 05
    #  06 07 | 08 09 | 10 11
    #  ---------------------
    #  12 13 | 14 15 | 16 17
    #  18 19 | 20 21 | 22 23
    outputVals = []
    outputVals.append(0 + (0 + 1 + 6 + 7))
    outputVals.append(1 + (2 + 3 + 8 + 9))
    outputVals.append(2 + (4 + 5 + 10 + 11))
    outputVals.append(3 + (12 + 13 + 18 + 19))
    outputVals.append(4 + (14 + 15 + 20 + 21))
    outputVals.append(5 + (16 + 17 + 22 + 23))
    for i in xrange(6):
      self.assertEquals(l2output[2*i], 8) # size of input for each node is 8
      self.assertEquals(l2output[2*i+1], outputVals[i])


    # =====================================================
    # Run for one more iteration
    # =====================================================
    LOGGER.info("Running for a second iteration")
    net.run(1)

    # =====================================================
    # Check everything again
    # =====================================================

    # Outputs are all the same except that the first output is
    # incremented by the iteration number
    for i in xrange(24):
      self.assertEquals(l1output[2*i], 1)
      self.assertEquals(l1output[2*i+1], i)

    for i in xrange(6):
      self.assertEquals(l2output[2*i], 9)
      self.assertEquals(l2output[2*i+1], outputVals[i] + 4)


  def testLinkingDownwardDimensions(self):
    #
    # Linking can induce dimensions downward
    #
    net = Network()
    level1 = net.addRegion("level1", "TestNode", "")
    level2 = net.addRegion("level2", "TestNode", "")
    dims = Dimensions([3, 2])
    level2.setDimensions(dims)
    net.link("level1", "level2", "TestFanIn2", "")
    net.initialize()

    # Level1 should now have dimensions [6, 4]
    self.assertEquals(level1.getDimensions()[0], 6)
    self.assertEquals(level1.getDimensions()[1], 4)

    #
    # We get nice error messages when network can't be initialized
    #
    LOGGER.info("=====")
    LOGGER.info("Creating a 3 level network in which levels 1 and 2 have")
    LOGGER.info("dimensions but network initialization will fail because")
    LOGGER.info("level3 does not have dimensions")
    LOGGER.info("Error message follows:")

    net = Network()
    level1 = net.addRegion("level1", "TestNode", "")
    level2 = net.addRegion("level2", "TestNode", "")
    _level3 = net.addRegion("level3", "TestNode", "")
    dims = Dimensions([6, 4])
    level1.setDimensions(dims)
    net.link("level1", "level2", "TestFanIn2", "")
    self.assertRaises(RuntimeError, net.initialize)
    LOGGER.info("=====")

    LOGGER.info("======")
    LOGGER.info("Creating a link with incompatible dimensions. \
      Error message follows")
    net.link("level2", "level3", "TestFanIn2", "")
    self.assertRaises(RuntimeError, net.initialize)



if __name__ == "__main__":
  unittest.main()
