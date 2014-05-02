#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

"""
This test ensures that SPRegion and TPRegion are working as expected. It runs a
number of tests:

1: testCLAAndSP -- side by side comparison of network with CLARegion and network
with SPRegion.

2: testSaveAndReload -- tests that a saved and reloaded network behaves the same
as an unsaved network.

3: testCLAAndSPTP -- side by side comparison of network with CLARegion and
network with SPRegion and TPRegion

4: testCLAAndSPFlow -- side by side comparison of network with CLARegion and
network with SPRegion with both bottom-up and top-down flow.

5: testCLAAndSPTPFlow -- side by side comparison of network with CLARegion and
network with SPRegion and TPRegion with both bottom-up and top-down flow.

6: testMaxEnabledPhase -- tests that maxEnabledPhase can be set.

The following are unimplemented currently, but should be implemented:

Test N: test that top down compute is working

Test N: test that combined learning and inference is working

Test N: test that all the parameters of an SP region work properly

Test N: test that all the parameters of a TP region work properly

"""

import numpy
import os
import json
import random
import tempfile
import unittest2 as unittest

from nupic.data.datasethelpers import findDataset
from nupic.data.file_record_stream import FileRecordStream
from nupic.engine import Network
from nupic.research import fdrutilities as fdrutils
from nupic.encoders import MultiEncoder
from nupic.frameworks.prediction.experimentdeschelpers import _getCLAParams
from nupic.regions.RecordSensorFilters.ModifyFields import ModifyFields
from nupic.support.unittesthelpers.testcasebase import (TestCaseBase,
                                                        TestOptionParser)

_VERBOSITY = 0         # how chatty the unit tests should be
_SEED = 35             # the random seed used throughout

# Seed the random number generators
rgen = numpy.random.RandomState(_SEED)
random.seed(_SEED)

g_claConfig = None
g_spRegionConfig = None
g_tpRegionConfig = None


def _initConfigDicts():
  # ============================================================================
  # Config field to configure the old CLARegion
  
  global g_claConfig  # pylint: disable=W0603
  g_claConfig = dict(
    spVerbosity = _VERBOSITY,
    claRegionNColumns = 200,
    spEnable = True,
    spTrain = True,
    spSeed = _SEED,
    spPrintStatsPeriodIter = 0,
    spNumActivePerInhArea = 20,
    tpSeed = _SEED,
    tpVerbosity = 0,
    tpTrainPrintStatsPeriodIter = 0,
    tpEnable = True,
    tpImplementation = 'cpp',
    tpNCellsPerCol = 8,
    tpNewSynapseCount = 15,
    tpMaxSynapsesPerSegment = 32,
    tpMaxSegmentsPerCell = 128,
    tpInitialPerm = 0.21,
    tpPermanenceInc = 0.1,
    tpPermanenceDec = 0.1,
    tpMinSegmentMatchSynapseThreshold = 12,
    tpSegmentActivationThreshold = 12,
    )
  
  # ============================================================================
  # Config field for SPRegion, to match the old CLARegion
  global g_spRegionConfig  # pylint: disable=W0603
  g_spRegionConfig = dict(
    spVerbosity = _VERBOSITY,
    columnCount = 200,
    inputWidth   = 0,
    numActivePerInhArea = 20,
    spatialImp = 'oldpy',
    seed = _SEED,
    )
  
  # ============================================================================
  # Config field for TPRegion, to match the old CLARegion parameters
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


# ============================================================================
def _createLPFNetwork(addSP = True, addTP = False):
  """Create an 'old-style' network ala LPF and return it."""

  # ==========================================================================
  # Create the encoder and data source stuff we need to configure the sensor
  sensorParams = dict(verbosity = _VERBOSITY)
  encoder = _createEncoder()
  trainFile = findDataset("extra/gym/gym.csv")
  dataSource = FileRecordStream(streamID=trainFile)
  dataSource.setAutoRewind(True)

  # Create all the stuff we need to configure the CLARegion
  g_claConfig['spEnable'] = addSP
  g_claConfig['tpEnable'] = addTP
  claParams = _getCLAParams(encoder = encoder, config= g_claConfig)
  claParams['spSeed'] = g_claConfig['spSeed']
  claParams['tpSeed'] = g_claConfig['tpSeed']

  # ==========================================================================
  # Now create the network itself
  n = Network()

  n.addRegion("sensor", "py.RecordSensor", json.dumps(sensorParams))

  sensor = n.regions['sensor'].getSelf()
  sensor.encoder = encoder
  sensor.dataSource = dataSource

  n.addRegion("level1", "py.CLARegion", json.dumps(claParams))

  n.link("sensor", "level1", "UniformLink", "")
  n.link("sensor", "level1", "UniformLink", "",
         srcOutput="resetOut", destInput="resetIn")

  return n


# ==========================================================================
def _createOPFNetwork(addSP = True, addTP = False):
  """Create a 'new-style' network ala OPF and return it.
  If addSP is true, an SPRegion will be added named 'level1SP'.
  If addTP is true, a TPRegion will be added named 'level1TP'
  """

  # ==========================================================================
  # Create the encoder and data source stuff we need to configure the sensor
  sensorParams = dict(verbosity = _VERBOSITY)
  encoder = _createEncoder()
  trainFile = findDataset("extra/gym/gym.csv")
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
    # Add the TP on top of SP if requested
    # The input width of the TP is set to the column count of the SP
    print "Adding TPRegion on top of SP"
    g_tpRegionConfig['inputWidth'] = g_spRegionConfig['columnCount']
    n.addRegion("level1TP", "py.TPRegion", json.dumps(g_tpRegionConfig))
    n.link("level1SP", "level1TP", "UniformLink", "")
    n.link("level1TP", "level1SP", "UniformLink", "",
           srcOutput="topDownOut", destInput="topDownIn")
    n.link("sensor", "level1TP", "UniformLink", "",
           srcOutput="resetOut", destInput="resetIn")

  elif addTP:
    # Add a lone TPRegion if requested
    # The input width of the TP is set to the encoder width
    print "Adding TPRegion"
    g_tpRegionConfig['inputWidth'] = encoder.getWidth()
    n.addRegion("level1TP", "py.TPRegion", json.dumps(g_tpRegionConfig))

    n.link("sensor", "level1TP", "UniformLink", "")
    n.link("sensor", "level1TP", "UniformLink", "",
           srcOutput="resetOut", destInput="resetIn")

  return n


class OPFRegionTest(TestCaseBase):
  """Unit tests for the OPF Region Test."""


  def setUp(self):
    _initConfigDicts()


  def testCLAAndSP(self):
    """
    The test creates two networks, trains them, and ensures they return identical
    results. The two networks are:
  
    a) an LPF-style network using the LPF regions RecordSensor and CLARegion.
  
    b) an OPF-style network using RecordSensor and SPRegion.
  
    The test trains each network for 500 iterations (on the gym.csv file) and
    runs inference for 100 iterations. During inference the outputs of both
    networks are tested to ensure they are identical.
    """
  
    print "Creating network..."
  
    netLPF = _createLPFNetwork()
    netOPF = _createOPFNetwork()
  
    level1LPF = netLPF.regions['level1']
    level1OPF = netOPF.regions['level1SP']
  
    # ==========================================================================
    # Run learning for 500 iterations
    print "Training the LPF network for 500 iterations"
    level1LPF.setParameter('learningMode', 1)
    level1LPF.setParameter('inferenceMode', 0)
    level1LPF.setParameter('trainingStep','spatial')
    netLPF.run(500)
    level1LPF.setParameter('learningMode', 0)
    level1LPF.setParameter('inferenceMode', 1)
  
    print "Training the OPF network for 500 iterations"
    level1OPF.setParameter('learningMode', 1)
    level1OPF.setParameter('inferenceMode', 0)
    netOPF.run(500)
    level1OPF.setParameter('learningMode', 0)
    level1OPF.setParameter('inferenceMode', 1)
  
    # ==========================================================================
    print "Running inference on the two networks for 100 iterations"
    for _ in xrange(100):
      netLPF.run(1)
      netOPF.run(1)
      l1outputLPF = level1LPF.getOutputData("bottomUpOut")
      l1outputOPF = level1OPF.getOutputData("bottomUpOut")
      lpfHash = l1outputLPF.nonzero()[0].sum()
      opfHash = l1outputOPF.nonzero()[0].sum()
  
      self.assertEqual(lpfHash, opfHash)
  
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
    trainFile = findDataset("extra/gym/gym.csv")
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
  def testCLAAndSPTP(self):
    """
    The test creates two networks, trains their spatial and temporal poolers, and
    ensures they return identical results. The two networks are:
  
    a) an LPF-style network using the LPF regions RecordSensor and CLARegion.
  
    b) an OPF-style network using RecordSensor, SPRegion and TPRegion.
  
    The test trains each network for 500 iterations (on the gym.csv file) and
    runs inference for 100 iterations. During inference the outputs of both
    networks are tested to ensure they are identical.  The test also ensures
    the TP instances of CLARegion and TPRegion are identical after training.
    """
  
    print "Creating network..."
  
    netLPF = _createLPFNetwork(addSP = True, addTP = True)
    netOPF = _createOPFNetwork(addSP = True, addTP = True)
  
    # ==========================================================================
    # Train the LPF network for 500 iterations
    print "Training the LPF network for 500 iterations"
    level1LPF = netLPF.regions['level1']
    level1LPF.setParameter('learningMode', 1)
    level1LPF.setParameter('inferenceMode', 0)
    level1LPF.setParameter('trainingStep','spatial')
    netLPF.run(500)
    level1LPF.setParameter('trainingStep','temporal')
    netLPF.run(500)
    level1LPF.setParameter('learningMode', 0)
    level1LPF.setParameter('inferenceMode', 1)
  
    # ==========================================================================
    # Train the OPF network for 500 iterations
    print "Training the OPF network for 500 iterations"
  
    # Train SP for 1000 iterations. Here we set the maxEnabledPhase to exclude
    # the TPRegion.
    netOPF.initialize()
    level1SP = netOPF.regions['level1SP']
    level1SP.setParameter('learningMode', 1)
    level1SP.setParameter('inferenceMode', 0)
    netOPF.setMaxEnabledPhase(1)
    netOPF.run(500)
    level1SP.setParameter('learningMode', 0)
    level1SP.setParameter('inferenceMode', 1)
  
    # Train TP for 500 iterations. Here we set the maxEnabledPhase to include
    # all regions
    print "Training TP"
    level1TP = netOPF.regions['level1TP']
    level1TP.setParameter('learningMode', 1)
    level1TP.setParameter('inferenceMode', 0)
    netOPF.setMaxEnabledPhase(netOPF.maxPhase)
    netOPF.run(500)
    level1TP.setParameter('learningMode', 0)
    level1TP.setParameter('inferenceMode', 1)
  
    # To match CLARegion we need to explicitly call finishLearning
    level1TP.executeCommand(['finishLearning'])
  
    # ==========================================================================
    # Get the TP instances from the two networks and compare them using tpDiff
    claSelf = netLPF.regions['level1'].getSelf()
    tp1 = claSelf._tfdr  # pylint: disable=W0212
    level1TPSelf = netOPF.regions['level1TP'].getSelf()
    tp2 = level1TPSelf._tfdr  # pylint: disable=W0212
    if not fdrutils.tpDiff2(tp1, tp2, _VERBOSITY, False):
      print "Trained temporal poolers are different!"
      self.assertTrue(False, "Trained temporal poolers are different!")
    else:
      print "Trained temporal poolers are identical\n"
  
    # ==========================================================================
    print "Running inference on the two networks for 100 iterations"
    
    for i in xrange(100):
      netLPF.run(1)
      netOPF.run(1)
      outputLPF = level1LPF.getOutputData("bottomUpOut")
      outputOPF = level1TP.getOutputData("bottomUpOut")
  
      lpfHash = outputLPF.nonzero()[0].sum()
      opfHash = outputOPF.nonzero()[0].sum()
  
      self.assertEqual(lpfHash, opfHash,"Outputs for iteration %d unequal!" \
                       % (i))
      
  # ============================================================================
  def testCLAAndSPFlow(self, trainIterations=500, testIterations=100):
    """
    The test creates two networks, trains them, and ensures they return identical
    results for bottom-up and top-down flows. The difference between this test and
    the
  
    The two networks are:
  
    a) an LPF-style network using the LPF regions RecordSensor and CLARegion.
  
    b) an OPF-style network using RecordSensor and SPRegion.
  
    The test trains each network for 500 iterations (on the gym.csv file) and
    runs inference for 100 iterations. During inference the outputs at the end of
    the bottom-up flow and the end of top-down flow of both networks are tested to
    ensure they are identical.
    """
  
    print "Creating network..."
  
    netLPF = _createLPFNetwork()
    netOPF = _createOPFNetwork()
  
    sensorOPF = netOPF.regions['sensor']
    pySensorOPF = netOPF.regions['sensor'].getSelf()
  
    sensorLPF = netLPF.regions['sensor']
    pySensorLPF = netLPF.regions['sensor'].getSelf()
    encoderLPF = pySensorLPF.encoder
    level1LPF = netLPF.regions['level1']
  
    sensorOPF = netOPF.regions['sensor']
    pySensorOPF = netOPF.regions['sensor'].getSelf()
    level1OPF = netOPF.regions['level1SP']
  
    # ==========================================================================
    # Run learning for 500 iterations
    print "Training the LPF network for %d iterations" % (trainIterations,)
    level1LPF.setParameter('learningMode', 1)
    level1LPF.setParameter('inferenceMode', 0)
    level1LPF.setParameter('trainingStep','spatial')
    netLPF.run(trainIterations)
    level1LPF.setParameter('learningMode', 0)
    level1LPF.setParameter('inferenceMode', 1)
    pySensorLPF.postEncodingFilters = \
                    [ModifyFields(fields=['consumption'], \
                                  operation='setToZero')]
  
  
    print "Training the OPF network for %d iterations" % (trainIterations,)
    level1OPF.setParameter('learningMode', 1)
    level1OPF.setParameter('inferenceMode', 0)
    netOPF.run(trainIterations)
    level1OPF.setParameter('learningMode', 0)
    level1OPF.setParameter('inferenceMode', 1)
    pySensorOPF.postEncodingFilters = \
                    [ModifyFields(fields=['consumption'], \
                                  operation='setToZero')]
  
  
    # ==========================================================================
    print "Running inference on the two networks for %d iterations" \
                                                      % (testIterations,)
    for _ in xrange(testIterations):
  
      # This is a single LPF iteration
      netLPF.run(1)
  
      # Output at the end of bottom-up flow
      l1outputLPF = level1LPF.getOutputData("bottomUpOut")
  
      # This is the current of top-down reconstruction in LPF
      # 1) A callback function at the end of each iteration
      #  - logOutputsToFileIter
      # accesses the "spReconstructedIn" in CLA Region and logs it to a file on
      # disk
      spatialTDOutputLPF = level1LPF.getOutputData("spReconstructedIn")
      # 2) Encoder Top-down compute on spReconstructedIn is run in
      # postprocess/spstats.py The encoder is accessed directly
      sensorTDOutputLPF = encoderLPF.topDownCompute(spatialTDOutputLPF)
      sensorTDOutputLPF = [x.scalar for x in sensorTDOutputLPF]
      # 3) The bottom-up input is extracted from sensor
      sensorBUInputLPF = sensorLPF.getOutputData("sourceOut")
  
  
      # This is a single OPF iteration
      # Reconstruction is now done as part of the top-down flow
  
      #Bottom-up flow
      sensorOPF.setParameter('topDownMode', False)
      sensorOPF.prepareInputs()
      sensorOPF.compute()
      level1OPF.setParameter('topDownMode', False)
      level1OPF.prepareInputs()
      level1OPF.compute()
  
      #Top-down flow
      level1OPF.setParameter('topDownMode', True)
      level1OPF.prepareInputs()
      level1OPF.compute()
      sensorOPF.setParameter('topDownMode', True)
      sensorOPF.prepareInputs()
      sensorOPF.compute()
  
  
      l1outputOPF = level1OPF.getOutputData("bottomUpOut")
  
      spatialTDOutputOPF = level1OPF.getOutputData("spatialTopDownOut")
      sensorBUInputOPF = sensorOPF.getOutputData("sourceOut")
      sensorTDOutputOPF = sensorOPF.getOutputData("spatialTopDownOut")
  
      self.assertTrue(numpy.allclose(sensorTDOutputLPF, sensorTDOutputOPF) or
              numpy.allclose(sensorBUInputLPF, sensorBUInputOPF) or
              numpy.allclose(spatialTDOutputLPF, spatialTDOutputOPF) or
              numpy.allclose(l1outputLPF, l1outputOPF))
  
      lpfHash = l1outputLPF.nonzero()[0].sum()
      opfHash = l1outputOPF.nonzero()[0].sum()
  
      self.assertEqual(lpfHash, opfHash)
  
  # ============================================================================
  def testCLAAndSPTPFlow(self, trainIterations=500, testIterations=100):
    """
    The test creates two networks, trains their spatial and temporal poolers, and
    ensures they return identical results for bottom-up and top-down flows.
  
    The two networks are:
  
    a) an LPF-style network using the LPF regions RecordSensor and CLARegion.
  
    b) an OPF-style network using RecordSensor, SPRegion and TPRegion.
  
    The test trains each network for 500 iterations (on the gym.csv file) and
    runs inference for 100 iterations. During inference the outputs of both
    networks are tested to ensure they are identical.  The test also ensures
    the TP instances of CLARegion and TPRegion are identical after training.
    """
  
    print "Creating network..."

    netLPF = _createLPFNetwork(addSP = True, addTP = True)
    sensorLPF = netLPF.regions['sensor']
    pySensorLPF = netLPF.regions['sensor'].getSelf()
    encoderLPF = pySensorLPF.encoder
    level1LPF = netLPF.regions['level1']
  
    netOPF = _createOPFNetwork(addSP = True, addTP = True)
    sensorOPF = netOPF.regions['sensor']
    level1SP = netOPF.regions['level1SP']
    level1TP = netOPF.regions['level1TP']
  
    # ==========================================================================
    # Train the LPF network for 500 iterations
    print "Training the LPF network for %d iterations" % (trainIterations,)
    level1LPF.setParameter('learningMode', 1)
    level1LPF.setParameter('inferenceMode', 0)
    level1LPF.setParameter('trainingStep','spatial')
    netLPF.run(trainIterations)
    level1LPF.setParameter('trainingStep','temporal')
    netLPF.run(trainIterations)
    level1LPF.setParameter('learningMode', 0)
    level1LPF.setParameter('inferenceMode', 1)
  
    # ==========================================================================
    # Train the OPF network for 500 iterations
    print "Training the OPF network for %d iterations" % (trainIterations,)
    # Train SP for 1000 iterations. Here we call compute on regions
    # explicitly. Note that prepareInputs must be called on a region before
    # its compute is called.
    netOPF.initialize()
    level1SP.setParameter('learningMode', 1)
    level1SP.setParameter('inferenceMode', 0)
    for i in range(trainIterations):
      netOPF.regions['sensor'].compute()
      level1SP.prepareInputs()
      level1SP.compute()
    level1SP.setParameter('learningMode', 0)
    level1SP.setParameter('inferenceMode', 1)
  
    # Train TP for 500 iterations
    print "Training TP"
    level1TP.setParameter('learningMode', 1)
    level1TP.setParameter('inferenceMode', 0)
    netOPF.run(trainIterations)
    level1TP.setParameter('learningMode', 0)
    level1TP.setParameter('inferenceMode', 1)
  
    # To match CLARegion we need to explicitly call finishLearning
    level1TP.executeCommand(['finishLearning'])
  
    # ==========================================================================
    # Get the TP instances from the two networks and compare them using tpDiff
    claSelf = netLPF.regions['level1'].getSelf()
    tp1 = claSelf._tfdr  # pylint: disable=W0212
    level1TPSelf = netOPF.regions['level1TP'].getSelf()
    tp2 = level1TPSelf._tfdr  # pylint: disable=W0212
    if not fdrutils.tpDiff2(tp1, tp2, _VERBOSITY, False):
      print "Trained temporal poolers are different!"
      self.assertTrue(False, "Trained temporal poolers are different!")
    print "Trained temporal poolers are identical\n"
  
    # ==========================================================================
    print "Running inference on the two networks for %d iterations" \
                                                        % (testIterations,)
  
    prevSensorTDOutputLPF = None
    prevSensorTDOutputOPF = None
    for i in xrange(testIterations):
      netLPF.run(1)
      outputLPF = level1LPF.getOutputData("bottomUpOut")
  
      # This is the current of top-down reconstruction in LPF
      # 1) A callback function at the end of each iteration
      #   - logOutputsToFileIter
      # accesses the "topDownOut" in CLA Region and logs it to a file on disk
      temporalTDOutputLPF = level1LPF.getOutputData("topDownOut")
      # 2) Encoder top-down compute on spReconstructedIn is run in
      # postprocess/inputpredictionstats.py. The encoder is accessed directly
      sensorTDOutputLPF = encoderLPF.topDownCompute(temporalTDOutputLPF)
      # 3) The bottom-up input is extracted from sensor
      if prevSensorTDOutputLPF is None:
        prevSensorTDOutputLPF = sensorTDOutputLPF
  
      sensorBUInputLPF = sensorLPF.getOutputData("sourceOut")
      #print sensorBUInputLPF, prevSensorTDOutputLPF, sensorTDOutputLPF
  
      # This is a single OPF iteration
      # netOPF.run(1)
      # Reconstruction is now done as part of the top-down flow
  
      #Bottom-up flow
      sensorOPF.setParameter('topDownMode', False)
      sensorOPF.prepareInputs()
      sensorOPF.compute()
      level1SP.setParameter('topDownMode', False)
      level1SP.prepareInputs()
      level1SP.compute()
      level1TP.setParameter('topDownMode', False)
      level1TP.prepareInputs()
      level1TP.compute()
  
      #Top-down flow
      level1TP.setParameter('topDownMode', True)
      level1TP.prepareInputs()
      level1TP.compute()
      level1SP.setParameter('topDownMode', True)
      level1SP.prepareInputs()
      level1SP.compute()
      sensorOPF.setParameter('topDownMode', True)
      sensorOPF.prepareInputs()
      sensorOPF.compute()
  
      outputOPF = level1TP.getOutputData("bottomUpOut")
  
      temporalTDOutputOPF = level1SP.getOutputData("temporalTopDownOut")
      sensorBUInputOPF = sensorOPF.getOutputData("sourceOut")
      sensorTDOutputOPF = sensorOPF.getOutputData("temporalTopDownOut")
      if prevSensorTDOutputOPF is None:
        prevSensorTDOutputOPF = sensorTDOutputOPF
  
      #print sensorBUInputLPF, prevSensorTDOutputLPF, sensorTDOutputLPF
  
      self.assertTrue(numpy.allclose(temporalTDOutputLPF, temporalTDOutputOPF) \
              or numpy.allclose(sensorBUInputLPF, sensorBUInputOPF) or \
              numpy.allclose(sensorTDOutputLPF, sensorTDOutputOPF) or \
              numpy.allclose(outputLPF, outputOPF))
  
      lpfHash = outputLPF.nonzero()[0].sum()
      opfHash = outputOPF.nonzero()[0].sum()
  
      self.assertEqual(lpfHash, opfHash, "Outputs for iteration %d unequal!" \
                       % (i))
  
      prevSensorTDOutputLPF = sensorTDOutputLPF
      prevSensorTDOutputOPF = sensorTDOutputOPF
  
  def testMaxEnabledPhase(self):
    """ Test maxEnabledPhase"""
  
    print "Creating network..."
  
    netOPF = _createOPFNetwork(addSP = True, addTP = True)
    netOPF.initialize()
    level1SP = netOPF.regions['level1SP']
    level1SP.setParameter('learningMode', 1)
    level1SP.setParameter('inferenceMode', 0)
  
    tp = netOPF.regions['level1TP']
    tp.setParameter('learningMode', 0)
    tp.setParameter('inferenceMode', 0)
  
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



if __name__ == "__main__":
  unittest.main()
