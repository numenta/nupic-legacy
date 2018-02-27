# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014-2017, Numenta, Inc.  Unless you have an agreement
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

import sys
from mock import patch
import unittest2 as unittest

from nupic import engine
from nupic.bindings.regions.TestNode import TestNode
from nupic.regions.sp_region import SPRegion



class NetworkTest(unittest.TestCase):


  @unittest.skipIf(sys.platform.lower().startswith("win"),
                   "Not supported on Windows, yet!")
  def testErrorHandling(self):
    n = engine.Network()

    # Test trying to add non-existent node
    with self.assertRaises(Exception) as cm:
      n.addRegion('r', 'py.NonExistingNode', '')

    self.assertEqual(cm.exception.message, "Matching Python module for NonExistingNode not found.")

    orig_import = __import__
    def import_mock(name, *args):
      if name == "nupic.regions.unimportable_node":
        raise SyntaxError("invalid syntax (unimportable_node.py, line 5)")

      return orig_import(name, *args)

    with patch('__builtin__.__import__', side_effect=import_mock):
      # Test failure during import
      with self.assertRaises(Exception) as cm:
        n.addRegion('r', 'py.UnimportableNode', '')

      self.assertEqual(cm.exception.message, "invalid syntax (unimportable_node.py, line 5)")

    # Test failure in the __init__() method
    with self.assertRaises(Exception) as cm:
      n.addRegion('r', 'py.TestNode', '{ failInInit: 1 }')

    self.assertEqual(cm.exception.message, "TestNode.__init__() Failing on purpose as requested")

    # Test failure inside the compute() method
    with self.assertRaises(Exception) as cm:
      r = n.addRegion('r', 'py.TestNode', '{ failInCompute: 1 }')
      r.dimensions = engine.Dimensions([4, 4])
      n.initialize()
      n.run(1)

    self.assertEqual(str(cm.exception),
      'TestNode.compute() Failing on purpose as requested')

    # Test failure in the static getSpec
    from nupic.bindings.regions.TestNode import TestNode
    TestNode._failIngetSpec = True

    with self.assertRaises(Exception) as cm:
      TestNode.getSpec()

    self.assertEqual(str(cm.exception),
      'Failing in TestNode.getSpec() as requested')

    del TestNode._failIngetSpec


  def testGetSpecFromType(self):
    ns = engine.Region.getSpecFromType('py.SPRegion')
    p = ns.parameters['breakPdb']
    self.assertEqual(p.accessMode, 'ReadWrite')


  def testOneRegionNetwork(self):
    n = engine.Network()

    print "Number of regions in new network: %d" % len(n.regions)
    self.assertEqual(len(n.regions), 0)

    print "Adding level1SP"
    level1SP = n.addRegion("level1SP", "TestNode", "")
    print "Current dimensions are: %s" % level1SP.dimensions
    print "Number of regions in network: %d" % len(n.regions)

    self.assertEqual(len(n.regions), 1)
    self.assertEqual(len(n.regions), len(n.regions))

    print 'Node type: ', level1SP.type

    print("Attempting to initialize net when "
           "one region has unspecified dimensions")
    print "Current dimensions are: %s" % level1SP.dimensions

    with self.assertRaises(Exception):
      n.initialize()

    # Test Dimensions
    level1SP.dimensions = engine.Dimensions([4, 4])
    print "Set dimensions of level1SP to %s" % str(level1SP.dimensions)

    n.initialize()

    # Test Array
    a = engine.Array('Int32', 10)
    self.assertEqual(a.getType(), 'Int32')
    self.assertEqual(len(a), 10)
    import nupic
    self.assertEqual(type(a), nupic.bindings.engine_internal.Int32Array)

    for i in range(len(a)):
      a[i] = i

    for i in range(len(a)):
      self.assertEqual(type(a[i]), int)
      self.assertEqual(a[i], i)
      print i,
    print

    # --- Test Numpy Array
    print 'Testing Numpy Array'
    a = engine.Array('Byte', 15)
    print len(a)
    for i in range(len(a)):
      a[i] = ord('A') + i

    for i in range(len(a)):
      print a[i], ord('A') + i
      self.assertEqual(ord(a[i]), ord('A') + i)
    print

    print 'before asNumpyarray()'
    na = a.asNumpyArray()
    print 'after asNumpyarray()'

    self.assertEqual(na.shape, (15,))
    print 'na.shape:', na.shape
    na = na.reshape(5, 3)
    self.assertEqual(na.shape, (5, 3))
    print 'na.shape:', na.shape
    for i in range(5):
      for j in range(3):
        print chr(na[i, j]), ' ',
      print
    print


    # --- Test get/setParameter for Int64 and Real64
    print '---'
    print 'Testing get/setParameter for Int64/Real64'
    val = level1SP.getParameterInt64('int64Param')
    rval = level1SP.getParameterReal64('real64Param')
    print 'level1SP.int64Param = ', val
    print 'level1SP.real64Param = ', rval

    val = 20
    level1SP.setParameterInt64('int64Param', val)
    val = 0
    val = level1SP.getParameterInt64('int64Param')
    print 'level1SP.int64Param = ', val, ' after setting to 20'

    rval = 30.1
    level1SP.setParameterReal64('real64Param', rval)
    rval = 0.0
    rval = level1SP.getParameterReal64('real64Param')
    print 'level1SP.real64Param = ', rval, ' after setting to 30.1'

    # --- Test array parameter
    # Array a will be allocated inside getParameter
    print '---'
    print 'Testing get/setParameterArray'
    a = engine.Array('Int64', 4)
    level1SP.getParameterArray("int64ArrayParam", a)
    print 'level1SP.int64ArrayParam size = ', len(a)
    print 'level1SP.int64ArrayParam = [ ',
    for i in range(len(a)):
      print a[i],

    print ']'
    #
    # --- test setParameter of an Int64 Array ---
    print 'Setting level1SP.int64ArrayParam to [ 1 2 3 4 ]'
    a2 = engine.Array('Int64', 4)
    for i in range(4):
      a2[i] = i + 1

    level1SP.setParameterArray('int64ArrayParam', a2)

    # get the value of int64ArrayParam after the setParameter call.
    # The array a owns its buffer, so we can call releaseBuffer if we
    # want, but the buffer should be reused if we just pass it again.
    #// a.releaseBuffer();
    level1SP.getParameterArray('int64ArrayParam', a)
    print 'level1SP.int64ArrayParam size = ', len(a)
    print 'level1SP.int64ArrayParam = [ ',
    for i in range(len(a)):
      print a[i],
    print ']'

    level1SP.compute()

    print "Running for 2 iteraitons"
    n.run(2)


    # --- Test input/output access
    #
    # Getting access via zero-copy
    with self.assertRaises(Exception):
      level1SP.getOutputData('doesnotexist')

    output = level1SP.getOutputData('bottomUpOut')
    print 'Element count in bottomUpOut is ', len(output)
    # set the actual output
    output[11] = 7777
    output[12] = 54321


    # Create a reshaped view of the numpy array
    # original output is 32x1 -- 16 nodes, 2 elements per node
    # Reshape to 8 rows, 4 columns
    numpy_output2 = output.reshape(8, 4)

    # Make sure the original output, the numpy array and the reshaped numpy view
    # are all in sync and access the same underlying memory.
    numpy_output2[1, 0] = 5555
    self.assertEqual(output[4], 5555)

    output[5] = 3333
    self.assertEqual(numpy_output2[1, 1], 3333)
    numpy_output2[1, 2] = 4444

    # --- Test doc strings
    # TODO: commented out because I'm not sure what to do with these
    # now that regions have been converted to the Collection class.
    # print
    # print "Here are some docstrings for properties and methods:"
    # for name in ('regionCount', 'getRegionCount', 'getRegionByName'):
    #   x = getattr(engine.Network, name)
    #   if isinstance(x, property):
    #     print 'property Network.{0}: "{1}"'.format(name, x.__doc__)
    #   else:
    #     print 'method Network.{0}(): "{1}"'.format(name, x.__doc__)

    # Typed methods should return correct type
    print "real64Param: %.2f" % level1SP.getParameterReal64("real64Param")

    # Uncomment to get performance for getParameter

    if 0:
      import time
      t1 = time.time()
      t1 = time.time()
      for i in xrange(0, 1000000):
        # x = level1SP.getParameterInt64("int64Param")   # buffered
        x = level1SP.getParameterReal64("real64Param")   # unbuffered
      t2 = time.time()

      print "Time for 1M getParameter calls: %.2f seconds" % (t2 - t1)


  def testTwoRegionNetwork(self):
    n = engine.Network()

    region1 = n.addRegion("region1", "TestNode", "")
    region2 = n.addRegion("region2", "TestNode", "")

    names = [region[0] for region in n.regions]
    self.assertEqual(names, ['region1', 'region2'])
    print n.getPhases('region1')
    self.assertEqual(n.getPhases('region1'), (0,))
    self.assertEqual(n.getPhases('region2'), (1,))

    n.link("region1", "region2", "TestFanIn2", "")

    print "Initialize should fail..."
    with self.assertRaises(Exception):
      n.initialize()

    print "Setting region1 dims"
    r1dims = engine.Dimensions([6, 4])
    region1.setDimensions(r1dims)

    print "Initialize should now succeed"
    n.initialize()

    r2dims = region2.dimensions
    self.assertEqual(len(r2dims), 2)
    self.assertEqual(r2dims[0], 3)
    self.assertEqual(r2dims[1], 2)

    # Negative test
    with self.assertRaises(Exception):
      region2.setDimensions(r1dims)


  def testDelayedLink(self):
    n = engine.Network()

    region1 = n.addRegion("region1", "TestNode", "")
    region2 = n.addRegion("region2", "TestNode", "")

    names = []

    propagationDelay = 2
    n.link("region1", "region2", "TestFanIn2", "",
           propagationDelay=propagationDelay)

    r1dims = engine.Dimensions([6, 4])
    region1.setDimensions(r1dims)

    n.initialize()

    outputArrays = []
    inputArrays = []

    iterations = propagationDelay + 2
    for i in xrange(iterations):
      n.run(1)

      if i < iterations - propagationDelay:
        outputArrays.append(list(region1.getOutputData("bottomUpOut")))

      if i < propagationDelay:
        # Pre-initialized delay elements should be arrays of all 0's
        outputArrays.insert(i, [0.0] * len(outputArrays[0]))

      inputArrays.append(list(region2.getInputData("bottomUpIn")))

    self.assertListEqual(inputArrays, outputArrays)


  def testInputsAndOutputs(self):
    n = engine.Network()

    region1 = n.addRegion("region1", "TestNode", "")
    region2 = n.addRegion("region2", "TestNode", "")
    region1.setDimensions(engine.Dimensions([6, 4]))
    n.link("region1", "region2", "TestFanIn2", "")
    n.initialize()

    r1_output = region1.getOutputData("bottomUpOut")

    region1.compute()
    print "Region 1 output after first iteration:"
    print "r1_output:", r1_output

    region2.prepareInputs()
    r2_input = region2.getInputData("bottomUpIn")
    print "Region 2 input after first iteration:"
    print 'r2_input:', r2_input


  def testNodeSpec(self):
    n = engine.Network()
    r = n.addRegion("region", "TestNode", "")

    print r.getSpec()


  @unittest.skipIf(sys.platform.lower().startswith("win"),
                   "Not supported on Windows, yet!")
  def testPyNodeGetSetParameter(self):
    n = engine.Network()

    r = n.addRegion("region", "py.TestNode", "")

    print "Setting region1 dims"
    r.dimensions = engine.Dimensions([6, 4])

    print "Initialize should now succeed"
    n.initialize()

    result = r.getParameterReal64('real64Param')
    self.assertEqual(result, 64.1)

    r.setParameterReal64('real64Param', 77.7)

    result = r.getParameterReal64('real64Param')
    self.assertEqual(result, 77.7)


  @unittest.skipIf(sys.platform.lower().startswith("win"),
                   "Not supported on Windows, yet!")
  def testPyNodeGetNodeSpec(self):
    n = engine.Network()

    r = n.addRegion("region", "py.TestNode", "")

    print "Setting region1 dims"
    r.setDimensions(engine.Dimensions([6, 4]))

    print "Initialize should now succeed"
    n.initialize()

    ns = r.spec

    self.assertEqual(len(ns.inputs), 1)
    i = ns.inputs['bottomUpIn']
    self.assertEqual(i.description, 'Primary input for the node')

    self.assertEqual(len(ns.outputs), 1)
    i = ns.outputs['bottomUpOut']
    self.assertEqual(i.description, 'Primary output for the node')


  @unittest.skipIf(sys.platform.lower().startswith("win"),
                   "Not supported on Windows, yet!")
  def testTwoRegionPyNodeNetwork(self):
    n = engine.Network()

    region1 = n.addRegion("region1", "py.TestNode", "")
    region2 = n.addRegion("region2", "py.TestNode", "")

    n.link("region1", "region2", "TestFanIn2", "")

    print "Initialize should fail..."
    with self.assertRaises(Exception):
      n.initialize()

    print "Setting region1 dims"
    r1dims = engine.Dimensions([6, 4])
    region1.setDimensions(r1dims)

    print "Initialize should now succeed"
    n.initialize()

    r2dims = region2.dimensions
    self.assertEqual(len(r2dims), 2)
    self.assertEqual(r2dims[0], 3)
    self.assertEqual(r2dims[1], 2)


  def testGetRegion(self):
    n = engine.Network()
    n.addRegion("region1", "py.TestNode", "")

    region = n.getRegionsByType(TestNode)[0]
    self.assertEqual(type(region.getSelf()), TestNode)

    self.assertEqual(n.getRegionsByType(SPRegion), [])
