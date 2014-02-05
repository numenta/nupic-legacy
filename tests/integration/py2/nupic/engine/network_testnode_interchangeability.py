"""This test verifies that the C++ test node and py.TestNode

It creates the same two node network with all four combinations
of TestNode and py.TestNode:

1. TestNode, TestNode
2. TestNode, py.TestNode
3. py.TestNode, TestNode
4. py.TestNode, py.TestNode

Then it performs the same tests as the twonode_network demo (except the error
messages tests for the three node network):

 - Can add regions to network and set dimensions
 - Linking induces dimensions correctly
 - Network computation happens in correct order
 - Direct (zero-copy) access to outputs
 - Linking correctly maps outputs to inputs
"""

from nupic.engine import Network, Dimensions, Array

# =====================================================
# Build and run the network
# =====================================================

def test(nodeType1, nodeType2):
  print 'test(level1: %s, level2: %s)' % (nodeType1, nodeType2)
  net = Network()
  level1 = net.addRegion("level1", nodeType1, "{int32Param: 15}")
  dims = Dimensions([6,4])
  level1.setDimensions(dims);

  level2 = net.addRegion("level2", nodeType2, "{real64Param: 128.23}")

  net.link("level1", "level2", "TestFanIn2", "")

  # Could call initialize here, but not necessary as net.run()
  # initializes implicitly.
  # net.initialize()

  net.run(1)
  print "Successfully created network and ran for one iteration"

  # =====================================================
  # Check everything
  # =====================================================
  dims = level1.getDimensions()
  assert(len(dims) == 2)
  assert(dims[0] == 6)
  assert(dims[1] == 4)

  dims = level2.getDimensions()
  assert(len(dims) == 2)
  assert(dims[0] == 3)
  assert(dims[1] == 2)

  # Check L1 output. "False" means don't copy, i.e.
  # get a pointer to the actual output
  # Actual output values are determined by the TestNode
  # compute() behavior.
  l1output = level1.getOutputData("bottomUpOut")
  assert(len(l1output) == 48) # 24 nodes; 2 values per node
  for i in xrange(24):
    assert(l1output[2*i] == 0)      # size of input to each node is 0
    assert(l1output[2*i+1] == i)    # node number

  # check L2 output.
  l2output = level2.getOutputData("bottomUpOut")
  assert(len(l2output) == 12) # 6 nodes; 2 values per node
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
    if l2output[2*i] != 8:
      print l2output[2*i]
      from dbgp.client import brk; brk(port=9019)

    assert(l2output[2*i] == 8)      # size of input for each node is 8
    assert(l2output[2*i+1] == outputVals[i])


  # =====================================================
  # Run for one more iteration
  # =====================================================
  print "Running for a second iteration"
  net.run(1)

  # =====================================================
  # Check everything again
  # =====================================================

  # Outputs are all the same except that the first output is
  # incremented by the iteration number
  for i in xrange(24):
    assert(l1output[2*i] == 1)
    assert(l1output[2*i+1] == i)

  for i in xrange(6):
    assert(l2output[2*i] == 9)
    assert(l2output[2*i+1] == outputVals[i] + 4)


  # =====================================================
  # Demonstrate a few other features
  # =====================================================

  #
  # Linking can induce dimensions downward
  #


  net = Network()
  level1 = net.addRegion("level1", nodeType1, "")
  level2 = net.addRegion("level2", nodeType2, "")
  dims = Dimensions([3,2])
  level2.setDimensions(dims);
  net.link("level1", "level2", "TestFanIn2", "")
  net.initialize()

  # Level1 should now have dimensions [6, 4]
  assert(level1.getDimensions()[0] == 6)
  assert(level1.getDimensions()[1] == 4)

if __name__=='__main__':
  test('py.TestNode', 'TestNode')
  test('TestNode', 'py.TestNode')
  test('TestNode', 'TestNode')
  test('py.TestNode', 'py.TestNode')

print "All tests passed"