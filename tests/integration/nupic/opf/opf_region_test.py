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
This test ensures that SPRegion and TMRegion are working as expected. It runs a
number of tests:

1: testSaveAndReload -- tests that a saved and reloaded network behaves the same
as an unsaved network.

2: testMaxEnabledPhase -- tests that maxEnabledPhase can be set.

The following are unimplemented currently, but should be implemented:

Test N: test that top down compute is working

Test N: test that combined learning and inference is working

Test N: test that all the parameters of an SP region work properly

Test N: test that all the parameters of a TM region work properly

"""

import json
import numpy
import os
import random
import tempfile
import unittest2 as unittest
from nupic.bindings.algorithms import SpatialPooler
from pkg_resources import resource_filename

from nupic.algorithms.backtracking_tm_cpp import BacktrackingTMCPP
from nupic.data.file_record_stream import FileRecordStream
from nupic.encoders import MultiEncoder
from nupic.engine import Network
from nupic.regions.sp_region import SPRegion
from nupic.regions.tm_region import TMRegion
from nupic.support.unittesthelpers.testcasebase import TestCaseBase

_VERBOSITY = 0         # how chatty the unit tests should be
_SEED = 35             # the random seed used throughout

# Seed the random number generators
rgen = numpy.random.RandomState(_SEED)
random.seed(_SEED)

g_spRegionConfig = None
g_tpRegionConfig = None


def _initConfigDicts():

  # ============================================================================
  # Config field for SPRegion
  global g_spRegionConfig  # pylint: disable=W0603
  g_spRegionConfig = dict(
    spVerbosity = _VERBOSITY,
    columnCount = 200,
    inputWidth   = 0,
    numActiveColumnsPerInhArea = 20,
    spatialImp = 'cpp',
    seed = _SEED,
    )

  # ============================================================================
  # Config field for TMRegion
  global g_tpRegionConfig  # pylint: disable=W0603
  g_tpRegionConfig = dict(
    verbosity = _VERBOSITY,
    columnCount = 200,
    cellsPerColumn = 8,
    inputWidth   = 0,
    seed = _SEED,
    temporalImp = 'cpp',
    newSynapseCount = 15,
    maxSynapsesPerSegment = 32,
    maxSegmentsPerCell = 128,
    initialPerm = 0.21,
    permanenceInc = 0.1,
    permanenceDec = 0.1,
    globalDecay = 0.0,
    maxAge = 0,
    minThreshold = 12,
    activationThreshold = 12,
    )


# ==============================================================================
# Utility routines
def _setupTempDirectory(filename):
  """Create a temp directory, and return path to filename in that directory"""

  tmpDir = tempfile.mkdtemp()
  tmpFileName = os.path.join(tmpDir, os.path.basename(filename))

  return tmpDir, tmpFileName


def _createEncoder():
  """Create the encoder instance for our test and return it."""
  encoder = MultiEncoder()
  encoder.addMultipleEncoders({
      'timestamp': dict(fieldname='timestamp', type='DateEncoder',
                        timeOfDay=(5,5), forced=True),
      'attendeeCount': dict(fieldname='attendeeCount', type='ScalarEncoder',
                            name='attendeeCount', minval=0, maxval=270,
                            clipInput=True, w=5, resolution=10, forced=True),
      'consumption': dict(fieldname='consumption',type='ScalarEncoder',
                          name='consumption', minval=0,maxval=115,
                          clipInput=True, w=5, resolution=5, forced=True),
  })

  return encoder


# ==========================================================================
def _createOPFNetwork(addSP = True, addTP = False):
  """Create a 'new-style' network ala OPF and return it.
  If addSP is true, an SPRegion will be added named 'level1SP'.
  If addTP is true, a TMRegion will be added named 'level1TP'
  """

  # ==========================================================================
  # Create the encoder and data source stuff we need to configure the sensor
  sensorParams = dict(verbosity = _VERBOSITY)
  encoder = _createEncoder()
  trainFile = resource_filename("nupic.datafiles", "extra/gym/gym.csv")
  dataSource = FileRecordStream(streamID=trainFile)
  dataSource.setAutoRewind(True)

  # ==========================================================================
  # Now create the network itself
  n = Network()
  n.addRegion("sensor", "py.RecordSensor", json.dumps(sensorParams))

  sensor = n.regions['sensor'].getSelf()
  sensor.encoder = encoder
  sensor.dataSource = dataSource

  # ==========================================================================
  # Add the SP if requested
  if addSP:
    print "Adding SPRegion"
    g_spRegionConfig['inputWidth'] = encoder.getWidth()
    n.addRegion("level1SP", "py.SPRegion", json.dumps(g_spRegionConfig))

    n.link("sensor", "level1SP", "UniformLink", "")
    n.link("sensor", "level1SP", "UniformLink", "",
           srcOutput="resetOut", destInput="resetIn")
    n.link("level1SP", "sensor", "UniformLink", "",
           srcOutput="spatialTopDownOut", destInput="spatialTopDownIn")
    n.link("level1SP", "sensor", "UniformLink", "",
           srcOutput="temporalTopDownOut", destInput="temporalTopDownIn")

  # ==========================================================================
  if addTP and addSP:
    # Add the TM on top of SP if requested
    # The input width of the TM is set to the column count of the SP
    print "Adding TMRegion on top of SP"
    g_tpRegionConfig['inputWidth'] = g_spRegionConfig['columnCount']
    n.addRegion("level1TP", "py.TMRegion", json.dumps(g_tpRegionConfig))
    n.link("level1SP", "level1TP", "UniformLink", "")
    n.link("level1TP", "level1SP", "UniformLink", "",
           srcOutput="topDownOut", destInput="topDownIn")
    n.link("sensor", "level1TP", "UniformLink", "",
           srcOutput="resetOut", destInput="resetIn")

  elif addTP:
    # Add a lone TMRegion if requested
    # The input width of the TM is set to the encoder width
    print "Adding TMRegion"
    g_tpRegionConfig['inputWidth'] = encoder.getWidth()
    n.addRegion("level1TP", "py.TMRegion", json.dumps(g_tpRegionConfig))

    n.link("sensor", "level1TP", "UniformLink", "")
    n.link("sensor", "level1TP", "UniformLink", "",
           srcOutput="resetOut", destInput="resetIn")

  return n


class OPFRegionTest(TestCaseBase):
  """Unit tests for the OPF Region Test."""


  def setUp(self):
    _initConfigDicts()

  # ============================================================================
  def testSaveAndReload(self):
    """
    This function tests saving and loading. It will train a network for 500
    iterations, then save it and reload it as a second network instance. It will
    then run both networks for 100 iterations and ensure they return identical
    results.
    """

    print "Creating network..."

    netOPF = _createOPFNetwork()
    level1OPF = netOPF.regions['level1SP']

    # ==========================================================================
    print "Training network for 500 iterations"
    level1OPF.setParameter('learningMode', 1)
    level1OPF.setParameter('inferenceMode', 0)
    netOPF.run(500)
    level1OPF.setParameter('learningMode', 0)
    level1OPF.setParameter('inferenceMode', 1)

    # ==========================================================================
    # Save network and reload as a second instance. We need to reset the data
    # source for the unsaved network so that both instances start at the same
    # place
    print "Saving and reload network"
    _, tmpNetworkFilename = _setupTempDirectory("trained.nta")
    netOPF.save(tmpNetworkFilename)
    netOPF2 = Network(tmpNetworkFilename)
    level1OPF2 = netOPF2.regions['level1SP']

    sensor = netOPF.regions['sensor'].getSelf()
    trainFile = resource_filename("nupic.datafiles", "extra/gym/gym.csv")
    sensor.dataSource = FileRecordStream(streamID=trainFile)
    sensor.dataSource.setAutoRewind(True)

    # ==========================================================================
    print "Running inference on the two networks for 100 iterations"
    for _ in xrange(100):
      netOPF2.run(1)
      netOPF.run(1)
      l1outputOPF2 = level1OPF2.getOutputData("bottomUpOut")
      l1outputOPF  = level1OPF.getOutputData("bottomUpOut")
      opfHash2 = l1outputOPF2.nonzero()[0].sum()
      opfHash  = l1outputOPF.nonzero()[0].sum()

      self.assertEqual(opfHash2, opfHash)

  # ============================================================================
  def testMaxEnabledPhase(self):
    """ Test maxEnabledPhase"""

    print "Creating network..."

    netOPF = _createOPFNetwork(addSP = True, addTP = True)
    netOPF.initialize()
    level1SP = netOPF.regions['level1SP']
    level1SP.setParameter('learningMode', 1)
    level1SP.setParameter('inferenceMode', 0)

    tm = netOPF.regions['level1TP']
    tm.setParameter('learningMode', 0)
    tm.setParameter('inferenceMode', 0)

    print "maxPhase,maxEnabledPhase = ", netOPF.maxPhase, \
                                      netOPF.getMaxEnabledPhase()
    self.assertEqual(netOPF.maxPhase, 2)
    self.assertEqual(netOPF.getMaxEnabledPhase(), 2)

    print "Setting setMaxEnabledPhase to 1"
    netOPF.setMaxEnabledPhase(1)
    print "maxPhase,maxEnabledPhase = ", netOPF.maxPhase, \
                                      netOPF.getMaxEnabledPhase()
    self.assertEqual(netOPF.maxPhase, 2)
    self.assertEqual(netOPF.getMaxEnabledPhase(), 1)

    netOPF.run(1)

    print "RUN SUCCEEDED"

    # TODO: The following does not run and is probably flawed.
    """
    print "\nSetting setMaxEnabledPhase to 2"
    netOPF.setMaxEnabledPhase(2)
    print "maxPhase,maxEnabledPhase = ", netOPF.maxPhase, \
                                      netOPF.getMaxEnabledPhase()
    netOPF.run(1)

    print "RUN SUCCEEDED"

    print "\nSetting setMaxEnabledPhase to 1"
    netOPF.setMaxEnabledPhase(1)
    print "maxPhase,maxEnabledPhase = ", netOPF.maxPhase, \
                                      netOPF.getMaxEnabledPhase()
    netOPF.run(1)
    print "RUN SUCCEEDED"
    """


  def testGetInputOutputNamesOnRegions(self):
    network = _createOPFNetwork(addSP = True, addTP = True)
    network.run(1)

    spRegion = network.getRegionsByType(SPRegion)[0]
    self.assertEqual(set(spRegion.getInputNames()),
                     set(['sequenceIdIn', 'bottomUpIn', 'resetIn',
                     'topDownIn']))
    self.assertEqual(set(spRegion.getOutputNames()),
                     set(['topDownOut', 'spatialTopDownOut',
                     'temporalTopDownOut', 'bottomUpOut', 'anomalyScore']))



  def testGetAlgorithmOnRegions(self):
    network = _createOPFNetwork(addSP = True, addTP = True)
    network.run(1)

    spRegions = network.getRegionsByType(SPRegion)
    tpRegions = network.getRegionsByType(TMRegion)

    self.assertEqual(len(spRegions), 1)
    self.assertEqual(len(tpRegions), 1)

    spRegion = spRegions[0]
    tpRegion = tpRegions[0]

    sp = spRegion.getSelf().getAlgorithmInstance()
    tm = tpRegion.getSelf().getAlgorithmInstance()

    self.assertEqual(type(sp), SpatialPooler)
    self.assertEqual(type(tm), BacktrackingTMCPP)



if __name__ == "__main__":
  unittest.main()
