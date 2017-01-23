# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
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

"""
## @file
This file tests VectorFileSensor exhaustively using the sessions interface.

Need to add tests for parameters:
  loading and appending CSV files
  test for recentFile

"""

import os

import pkg_resources
import unittest2 as unittest

from nupic.engine import Array, Dimensions, Network

g_filename = pkg_resources.resource_filename(__name__, "data/vectorfile.nta")
g_dataFile = pkg_resources.resource_filename(__name__,
                                             "data/vectortestdata.txt")
g_dataFile2 = pkg_resources.resource_filename(__name__,
                                              "data/vectortestdata2.txt")
g_dataFileCSV  = pkg_resources.resource_filename(__name__,
                                                 "data/vectortestdata.csv")
g_dataFileCSV2 = pkg_resources.resource_filename(__name__,
                                                 "data/vectortestdata2.csv")
g_dataFileCSV3 = pkg_resources.resource_filename(__name__,
                                                 "data/vectortestdata3.csv")
g_dataFileLF4 = pkg_resources.resource_filename(__name__,
                                                "data/vectortestdata.lf4")
g_dataFileBF4 = pkg_resources.resource_filename(__name__,
                                                "data/vectortestdata.bf4")
g_dataFileIDX = pkg_resources.resource_filename(__name__,
                                                "data/vectortestdata.idx")



class VectorFileSensorTest(unittest.TestCase):
  """Class for testing the VectorFileSensor plugin by loading a known network
  with a single VectorFileSensor node and a known data file."""


  def setUp(self):
    self.filename = g_filename
    self.nodeName = "TestSensor"
    self.sensorName = "VectorFileSensor"
    self.dataFile = g_dataFile
    self.dataFile2 = g_dataFile2
    self.dataFile3a = g_dataFileCSV
    self.dataFile3b = g_dataFileCSV2
    self.dataFile3c = g_dataFileCSV3
    self.dataFile4 = g_dataFileLF4
    self.dataFile5 = g_dataFileBF4
    self.dataFile6 = g_dataFileIDX

    self.numTests = 333
    self.testsPassed = 0
    self.testFailures = []

    self.sensor = None


  def testAll(self):
    """Run all the tests in our suite, catching any exceptions that might be
    thrown.
    """
    print 'VectorFileSensorTest parameters:'
    print 'PYTHONPATH: %s' % os.environ.get('PYTHONPATH', 'NOT SET')
    print 'filename: %s' % self.filename

    self._testRunWithoutFile()
    self._testNetLoad()

    self._testFakeLoadFile()
    self._testRepeatCount()
    self._testUnknownCommand()

    # Test maxOutput and activeOutputCount
    self._testOutputCounts(0)
    self._testLoadFile(self.dataFile, '0', '0')
    self._testOutputCounts(5)

    # Test a sequence of loads, runs, appends, etc.
    self._testLoadFile(self.dataFile, '0', '0')
    self._testRun()
    self._testLoadFile(self.dataFile2, '', '0')
    self._testRun()
    self._testLoadFile(self.dataFile2, '2', '0')
    self._testRun()
    self._testLoadFile(self.dataFile3a, '3', '0')
    self._testRun()
    self._testLoadFile(self.dataFile4, '4', '0')
    self._testRun()
    self._testLoadFile(self.dataFile5, '5', '0')
    self._testRun()
    self._testLoadFile(self.dataFile6, '6', '0')
    self._testRun()
    self._testPosition()
    self._testAppendFile(self.dataFile2, '2', '1', 10)
    self._testAppendFile(self.dataFile, '0', '1', 15)
    self._testRun()
    self._testScaling(self.dataFile3b, '3')

    # Test optional categoryOut and resetOut
    self.sensor.setParameter('hasCategoryOut', 1)
    self.sensor.setParameter('hasResetOut', 1)
    self._testLoadFile(self.dataFile3c, '3', '0')
    self._testOptionalOutputs()
    self.sensor.setParameter('hasCategoryOut', 0)
    self.sensor.setParameter('hasResetOut', 0)


  def _testNetLoad(self):
    """Test loading a network with this sensor in it."""
    n = Network()
    r = n.addRegion(self.nodeName, self.sensorName, '{ activeOutputCount: 11}')
    r.dimensions = Dimensions([1])
    n.save(self.filename)

    n = Network(self.filename)
    n.initialize()
    self.testsPassed += 1

    # Check that vectorCount parameter is zero
    r = n.regions[self.nodeName]

    res = r.getParameter('vectorCount')
    self.assertEqual(
        res, 0, "getting vectorCount:\n Expected '0',  got back  '%d'\n" % res)

    self.sensor = r


  def _testFakeLoadFile(self):
    """Test reading in a fake file."""
    # Loading a fake file should throw an exception
    with self.assertRaises(RuntimeError):
      self.sensor.executeCommand(['loadFile', 'ExistenceIsAnIllusion.txt', '0'])


  def _testRunWithoutFile(self):
    """Test running the network without a file loaded. This should be run
    before any file has been loaded in!"""
    with self.assertRaises(AttributeError):
      self.sensor.compute()


  def _testRepeatCount(self):
    """Test setting and getting repeat count using parameters."""
    # Check default repeat count
    n = Network(self.filename)
    sensor = n.regions[self.nodeName]
    res = sensor.executeCommand(['dump'])
    expected = self.sensorName + \
      ' isLabeled = 0 repeatCount = 1 vectorCount = 0 iterations = 0\n'
    self.assertEqual(
        res, expected,
        "repeat count test:\n   expected '%s'\n   got      '%s'\n" %
        (expected, res))

    # Set to 42, check it and return it back to 1
    sensor.setParameter('repeatCount', 42)

    res = sensor.getParameter('repeatCount')
    self.assertEqual(
        res, 42, "set repeatCount to 42:\n   got back     '%d'\n" % res)

    res = sensor.executeCommand(['dump'])
    expected = (self.sensorName +
                ' isLabeled = 0 repeatCount = 42 vectorCount = 0 '
                'iterations = 0\n')
    self.assertEqual(
        res, expected,
        "set to 42 test:\n   expected '%s'\n   got      '%s'\n" %
        (expected, res))
    sensor.setParameter('repeatCount', 1)


  def _testLoadFile(self, dataFile, fileFormat= '', iterations=''):
    """Test reading our sample vector file. The sample file
    has 5 vectors of the correct length, plus one with incorrect length.
    The sensor should ignore the last line."""

    # Now load a real file
    if fileFormat != '':
      res = self.sensor.executeCommand(['loadFile', dataFile, fileFormat])
    else:
      res = self.sensor.executeCommand(['loadFile', dataFile])

    self.assertTrue(res == '' or
                    res.startswith('VectorFileSensor read in file'),
                    'loading a real file: %s' % str(res))

    # Check recent file
    res = self.sensor.getParameter('recentFile')
    self.assertEqual(res, dataFile, 'recent file, got: %s' % (res))

    # Check summary of file contents
    res = self.sensor.executeCommand(['dump'])
    expected = (self.sensorName +
                ' isLabeled = 0 repeatCount = 1 vectorCount = 5 iterations = ' +
                iterations + '\n')
    self.assertEqual(res, expected,
                     'file summary:\n   expected "%s"\n   got      "%s"\n' %
                     (expected, res))


  def _testAppendFile(self, dataFile, fileFormat= '', iterations='',
                      numVecs=''):
    """Test appending our sample vector file. The sample file
    has 5 vectors of the correct length, plus one with incorrect length.
    The sensor should ignore the last line."""

    # Now load a real file
    if fileFormat != '':
      res = self.sensor.executeCommand(['appendFile', dataFile, fileFormat])
    else:
      res = self.sensor.executeCommand(['appendFile', dataFile])

    self.assertTrue(res == '' or
                    res.startswith('VectorFileSensor read in file'),
                    'loading a real file: %s' % str(res))

    # Check recent file
    res = self.sensor.getParameter('recentFile')
    self.assertEqual(res, dataFile, 'recent file, got: %s' % res)

    # Check summary of file contents
    res = self.sensor.executeCommand(['dump'])
    expected = self.sensorName + ' isLabeled = 0 repeatCount = 1' + \
        ' vectorCount = '+str(numVecs)+' iterations = ' + iterations + '\n'
    self.assertEqual(res, expected,
                     'file summary:\n   expected "%s"\n   got      "%s"\n' %
                     (expected, res))

    # Check vectorCount parameter
    res = self.sensor.getParameter('vectorCount')
    self.assertEqual(res, numVecs,
                     'getting position:\n Expected ' + str(numVecs) +
                     ',  got back  "%s"\n' % res)


  def _testRun(self):
    """This is the basic workhorse test routine. It runs the net several times
    to ensure the sensor is outputting the correct values. The routine tests
    looping, tests each vector, and tests repeat count. """

    # Set repeat count to 3
    self.sensor.setParameter('repeatCount', 3)
    self.sensor.setParameter('position', 0)

    # Run the sensor several times to ensure it is outputting the correct
    # values.
    for _epoch in [1, 2]:  # test looping
      for vec in [0, 1, 2, 3, 4]:  # test each vector
        for _rc in [1, 2, 3]:  # test repeatCount
          # Run and get outputs
          self.sensor.compute()
          outputs = self.sensor.getOutputData('dataOut')

          # Check outputs
          #sum = reduce(lambda x,y:int(x)+int(y),outputs)
          self.assertEqual(outputs[vec], vec+1, 'output = %s' % str(outputs))
          self.assertEqual(sum(outputs), vec+1, 'output = %s' % str(outputs))

    # Set repeat count back to 1
    self.sensor.setParameter('repeatCount', 1)


  def _testOutputCounts(self, vectorCount):
    """Test maxOutputVectorCount with different repeat counts."""

    # Test maxOutput with different repeat counts.
    res = self.sensor.getParameter('maxOutputVectorCount')
    self.assertEqual(res, vectorCount,
                     "getting maxOutputVectorCount:\n Expected '" +
                     str(vectorCount) + "',  got back  '%d'\n" % (res))

    self.sensor.setParameter('repeatCount', 3)

    res = self.sensor.getParameter('maxOutputVectorCount')
    self.assertEqual(res, 3 * vectorCount,
                     'getting maxOutputVectorCount:\n Expected ' +
                     str(3*vectorCount)+',  got back  "%d"\n' % res)
    self.sensor.setParameter('repeatCount', 1)

    # Test activeOutputCount
    res = self.sensor.getParameter('activeOutputCount')
    self.assertEqual(
        res, 11,
        'getting activeOutputCount :\n Expected 11,  got back  "%d"\n' % res)


  def _testPosition(self):
    """Test setting and getting position parameter. Run compute once to verify
    it went to the right position."""
    self.sensor.setParameter('position', 2)
    self.sensor.compute()
    outputs = self.sensor.getOutputData('dataOut')

    self.assertEqual(outputs[2], 3, 'output = %s' % str(outputs))
    self.assertEqual(sum(outputs), 3, 'output = %s' % str(outputs))

    # Now it should have incremented the position
    res = self.sensor.getParameter('position')
    self.assertEqual(res, 3,
                     'getting position:\n Expected "3",  got back  "%d"\n' %
                     res)


  def _testScaling(self, dataFile, fileFormat= ''):
    """Specific tests for setScaleVector, setOffsetVector, and scalingMode"""

    # Retrieve scalingMode after a netLoad. Should be 'none'
    res = self.sensor.getParameter('scalingMode')
    self.assertEqual(res, 'none',
                     'Getting scalingMode:\n Expected "none", got back "%s"\n' %
                     res)

    # Retrieve scaling and offset after netLoad - should be 1 and zero
    # respectively.
    a = Array('Real32', 11)
    self.sensor.getParameterArray('scaleVector', a)
    self.assertEqual(str(a), '[ 1 1 1 1 1 1 1 1 1 1 1 ]',
                     'Error getting ones scaleVector:\n Got back "%s"\n' %
                     str(res))

    self.sensor.getParameterArray('offsetVector', a)
    self.assertEqual(str(a), '[ 0 0 0 0 0 0 0 0 0 0 0 ]',
                     'Error getting zero offsetVector:\n Got back "%s"\n' %
                     str(res))

    # load data file, set scaling and offset to standardForm and check
    self.sensor.executeCommand(['loadFile', dataFile, fileFormat])
    self.sensor.setParameter('scalingMode', 'standardForm')
    self.sensor.getParameterArray('scaleVector', a)
    s = ('[ 2.23607 1.11803 0.745356 0.559017 0.447214 2.23607 1.11803 '
         '0.745356 0.559017 0.447214 2.23607 ]')
    self.assertEqual(
        str(a), s,
        'Error getting standardForm scaleVector:\n Got back "%s"\n' % res)

    o = '[ -0.2 -0.4 -0.6 -0.8 -1 -0.2 -0.4 -0.6 -0.8 -1 -0.2 ]'
    self.sensor.getParameterArray('offsetVector', a)
    self.assertEqual(
        str(a), o,
        'Error getting standardForm offsetVector:\n Got back "%s"\n' % res)

    # set to custom value and check

    scaleVector = Array('Real32', 11)
    for i, x in enumerate((1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 1)):
      scaleVector[i] = x
    self.sensor.setParameterArray('scaleVector', scaleVector)
    self.sensor.getParameterArray('scaleVector', a)
    self.assertEqual(str(a), str(scaleVector),
                     'Error getting modified scaleVector:\n Got back "%s"\n' %
                     str(res))

    offsetVector = Array('Real32', 11)
    for i, x in enumerate((1, 2, 3, 4, 1, 1, 1, 1, 1, 2, 1)):
      offsetVector[i] = x

    self.sensor.setParameterArray('offsetVector', offsetVector)
    self.sensor.getParameterArray('offsetVector', a)
    self.assertEqual(str(a), str(offsetVector),
                     'Error getting modified offsetVector:\n Got back "%s"\n' %
                     str(res))

    # scalingMode should now be custom
    mode = self.sensor.getParameter('scalingMode')
    self.assertEqual(
        mode, 'custom',
        'Getting scalingMode:\n Expected "custom", got back "%s"\n' % res)

    # At this point we test loading a data file using loadFile. The scaling
    # params should still be active and applied to the new vectors.
    res = self.sensor.executeCommand(['loadFile', dataFile, fileFormat])
    self.sensor.getParameterArray('offsetVector', a)
    self.assertEqual(
        str(a), str(offsetVector),
        'Error getting modified offsetVector after loadFile:\n Got back '
        '"%s"\n' % res)

    self.sensor.getParameterArray('scaleVector', a)
    self.assertEqual(str(a), str(scaleVector),
                     'Error getting modified scaleVector after loadFile:\n '
                     'Got back "%s"\n' % res)

    # Set scaling mode back to none and retrieve scaling and offset - should
    # be 1 and zero respectively.
    self.sensor.setParameter('scalingMode', 'none')
    self.sensor.getParameterArray('scaleVector', a)
    noScaling = Array('Real32', 11)
    for i in range(11):
      noScaling[i] = 1
    self.assertEqual(str(a), str(noScaling),
                     'Error getting ones scaleVector:\n Got back "%s"\n' % res)

    noOffset = Array('Real32', 11)
    for i in range(11):
      noOffset[i] = 0
    self.sensor.getParameterArray('offsetVector', a)
    self.assertEqual(str(a), str(noOffset),
                     'Error getting zero offsetVector:\n Got back "%s"\n' % res)


  def _testUnknownCommand(self):
    """Test that exception is thrown when unknown execute command sent."""
    with self.assertRaises(RuntimeError):
      self.sensor.executeCommand(['nonExistentCommand'])


  def _testOptionalOutputs(self):
    """This is the basic workhorse test routine. It runs the net several times
    to ensure the sensor is outputting the correct values. The routine tests
    looping, tests each vector, and tests repeat count. """

    # Set repeat count to 3
    self.sensor.setParameter('repeatCount', 3)
    self.sensor.setParameter('position', 0)

    # Run the sensor several times to ensure it is outputting the correct
    # values.
    categories = []
    resetOuts = []
    for _epoch in [1, 2]:               # test looping
      for vec in [0, 1, 2, 3, 4]:         # test each vector
        for _rc in [1, 2, 3]:            # test repeatCount
          # Run and get outputs
          self.sensor.compute()
          outputs = self.sensor.getOutputData('dataOut')

          a = self.sensor.getOutputData('categoryOut')
          categories.append(a[0])

          a = self.sensor.getOutputData('resetOut')
          resetOuts.append(a[0])

          # Check outputs
          self.assertEqual(outputs[vec], vec+1, 'output = %s' % str(outputs))
          self.assertEqual(sum(outputs), vec+1, 'output = %s' % str(outputs))

    self.assertEqual(categories, 2 * ([6] * 12 + [8] * 3))
    self.assertEqual(resetOuts,
                     2 * [1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1])

    # Set repeat count back to 1
    self.sensor.setParameter('repeatCount', 1)



if __name__=='__main__':
  unittest.main()
