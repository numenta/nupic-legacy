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
"""Unit tests for the SDRClassifier region."""

import os
import unittest2 as unittest

from nupic.engine import Network
from nupic.encoders import MultiEncoder
from nupic.data.file_record_stream import FileRecordStream



def _createNetwork():
  """Create a network with a RecordSensor region and a SDRClassifier region"""

  network = Network()
  network.addRegion('sensor', 'py.RecordSensor', '{}')
  network.addRegion('classifier', 'py.SDRClassifierRegion', '{}')
  _createSensorToClassifierLinks(network, 'sensor', 'classifier')

  # Add encoder to sensor region.
  sensorRegion = network.regions['sensor'].getSelf()
  encoderParams = {'consumption': {'fieldname': 'consumption',
                                   'resolution': 0.88,
                                   'seed': 1,
                                   'name': 'consumption',
                                   'type': 'RandomDistributedScalarEncoder'}}

  encoder = MultiEncoder()
  encoder.addMultipleEncoders(encoderParams)
  sensorRegion.encoder = encoder

  # Add data source.
  testDir = os.path.dirname(os.path.abspath(__file__))
  inputFile = os.path.join(testDir, 'fixtures', 'gymdata-test.csv')
  dataSource = FileRecordStream(streamID=inputFile)
  sensorRegion.dataSource = dataSource

  # Get and set what field index we want to predict.
  network.regions['sensor'].setParameter('predictedField', 'consumption')

  return network



def _createSensorToClassifierLinks(network, sensorRegionName,
                                   classifierRegionName):
  """Create links from sensor region to classifier region."""
  network.link(sensorRegionName, classifierRegionName, 'UniformLink', '',
               srcOutput='bucketIdxOut', destInput='bucketIdxIn')
  network.link(sensorRegionName, classifierRegionName, 'UniformLink', '',
               srcOutput='actValueOut', destInput='actValueIn')
  network.link(sensorRegionName, classifierRegionName, 'UniformLink', '',
               srcOutput='categoryOut', destInput='categoryIn')
  network.link(sensorRegionName, classifierRegionName, 'UniformLink', '',
               srcOutput='dataOut', destInput='bottomUpIn')



class SDRClassifierRegionTest(unittest.TestCase):
  """ SDRClassifier region unit tests."""


  def setUp(self):
    self.network = _createNetwork()
    self.classifierRegion = self.network.regions['classifier']


  def testActValueIn(self):
    self.network.run(1)  # Process 1 row of data
    actValueIn = self.classifierRegion.getInputData('actValueIn')[0]
    self.assertEquals(round(actValueIn, 1), 21.2)  # only 1 precision digit


  def testBucketIdxIn(self):
    self.network.run(1)  # Process 1 row of data
    bucketIdxIn = self.classifierRegion.getInputData('bucketIdxIn')[0]
    self.assertEquals(bucketIdxIn, 500)



if __name__ == "__main__":
  unittest.main()
