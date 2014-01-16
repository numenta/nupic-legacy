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

from nupic.data.record_stream import RecordStreamIface
from nupic.support.fshelpers import makeDirectoryFromAbsolutePath
import os
import pprint
import sys
try:
  import matplotlib
  matplotlib.use('agg', warn=False)
  import pylab
  pylabAvailable = True
except:
  pylabAvailable = False

"""A callback (aka "hook function") for the Prediction Framework is invoked by
the framework as:

setup and finish phases:
  c(experiment)

iteration phase:
  c(experiment, iteration)


In order to have reusable functions, we usually want to define
them in a configurable way, e.g. printSPCoincidences(updateEvery=20).

To remember state you may define the callback as a class with a __call__()
method. The class instance will have access to the state when the __call__()
is invoked as a callback. Many examples bellow.
"""

###############################################################
class sensorOpen(object):
  """This callback is used when the sensor has a FileSource datasource.
  It asks the sensor to open the named file"""
  def __init__(self, filename):
    self.filename = filename

  def __call__(self, experiment):
    sensor = experiment.network.regions['sensor']
    assert sensor.type == "py.RecordSensor"
    dataSource = sensor.getSelf().dataSource
    assert isinstance(dataSource, RecordStreamIface)

def sensorRewind(experiment):
  """This callback is used when the sensor has a FileSource dataSource.
  It asks the sensor to rewind to the beginning of its data"""
  sensor = experiment.network.regions['sensor']
  assert sensor.type == "py.RecordSensor"
  sensor.getSelf().rewind()


###############################################################################
class fileSourceAutoRewind(object):
  """This callback may be used only when the sensor's datasource is FileSource.
  It controls the FileSource's auto-rewind mode."""
  def __init__(self, autoRewindOnEOF):
    """
      autoRewindOnEOF: True or False; True will cause FileSource.getNext() to
      "rewind" the file if EOF has been reached.  (see FileSource.setAutoRewind)
    """
    self.autoRewindOnEOF = autoRewindOnEOF

  def __call__(self, experiment):
    sensor = experiment.network.regions['sensor']
    assert sensor.type == "py.RecordSensor"
    dataSource = sensor.getSelf().dataSource
    assert (isinstance(dataSource, RecordStreamIface))

    dataSource.setAutoRewind(self.autoRewindOnEOF)


###############################################################
from nupic.data.filters import AutoResetFilter

class setAutoResetInterval(object):
  """Set the interval for automatically-generated resets from
  a RecordSensor. Set to None to disable resets."""
  def __init__(self, interval):
    from datetime import timedelta
    assert isinstance(interval, timedelta)
    self.interval = interval

  def __call__(self, experiment):
    sensor = experiment.network.regions['sensor'].getSelf()
    # see if sensor already has an autoreset filter
    filter = None
    for f in sensor.preEncodingFilters:
      if isinstance(f, AutoResetFilter):
        filter = f
        break
    if filter is None:
      filter = AutoResetFilter()
      sensor.preEncodingFilters.append(filter)

    filter.setInterval(self.interval)


###############################################################
class setupInferenceRun(object):
  """ Callback that prepares the network for a new dataset. This
  will reset the sensor and tell the TP and SP to reset their
  captured statistics. Installed by LPF"""

  def __init__(self, name):
    self.name = name

  def __call__(self, experiment):
    # Reset the sensor
    sensorRewind(experiment)

    # Reset statistics captured by the TP and SP
    tp = experiment.network.regions['level1'].getSelf()._tfdr
    if tp is not None:
      tp.resetStats()

    sp = experiment.network.regions['level1'].getSelf()._sfdr
    if sp is not None:
      # NOTE: for now, sp.resetStats() only resets the SP periodic stats, but not
      #  the SP learning stats
      sp.resetStats()



###############################################################
class finishInferenceRun(object):
  """ Callback that gets called at the end of each inference run. This
  will, among other things, retrieve and print out the accumulated
  statistcs from the TP and/or SP. Installed by LPF """

  def __init__(self, name):
    self.name = name

  def __call__(self, experiment):
    # Get statistics captured by the TP and copy them into the
    #  results dict
    tp = experiment.network.regions['level1'].getSelf()._tfdr
    if tp is not None:
      stats = tp.getStats()
      tp.reset()
      if stats is not None:
        if experiment.verbosity >= 1:
          print "Accumulated TP Stats for test set %s:" % self.name
          pprint.pprint(stats)

        # Add these status to the experiment results
        results = {'infer_%s_tpStats' % (self.name): stats}
        experiment.results.update(results)

    # Get statistics captured by the SP and copy them into the
    #   results dict
    sp = experiment.network.regions['level1'].getSelf()._sfdr
    if sp is not None:
      stats = sp.getLearningStats()
      if experiment.verbosity >= 1:
        print "Accumulated SP Stats for test set %s:" % self.name
        pprint.pprint(stats)

      # Add these status to the experiment results
      results = {'infer_%s_spStats' % (self.name): stats}
      experiment.results.update(results)



###############################################################
class finishSPTrainingStep(object):
  """ Callback that gets called at the end of each SP training step. This
  will reset SP stats. Installed by LPF """

  def __init__(self):
    pass

  def __call__(self, experiment):
    # Reset SP stats
    # TODO Is there something useful that we should print here (see
    #  finishTPTrainingStep)?
    sp = experiment.network.regions['level1'].getSelf()._sfdr
    if sp is not None:
      # NOTE: for now, sp.resetStats() only resets the SP periodic stats, but not
      #  the SP learning stats
      sp.resetStats()



###############################################################
class finishTPTrainingStep(object):
  """ Callback that gets called at the end of each TP training step. This
  will print some statistics from the TP that help determine when
  enough training has been performed and resets TP stats. Installed by LPF """

  def __init__(self):
    pass

  def __call__(self, experiment):
    # Get statistics captured by the TP and copy them into the
    #  results dict
    tp = experiment.network.regions['level1'].getSelf()._tfdr
    if tp is not None:
      stats = tp.getStats()
      if stats is not None:
        print "TP total missing:", stats['totalMissing']
        print "TP total extra:", stats['totalExtra']
      tp.resetStats()



###############################################################
# Debugging
###############################################################

class pdbBreak(object):
  """Stop execution and enter debugger if condition
  evaluates to True or condition is None"""
  def __init__(self, condition = None, maxtimes=2000000):
    self.condition = condition
    self.maxtimes = maxtimes
    self.ntimes = 0
  def __call__(self, experiment, iteration=0):
    if self.ntimes < self.maxtimes and (self.condition is None or eval(self.condition)):
      self.ntimes += 1
      import pdb; pdb.set_trace()

class pause(object):
  """Pause experiment execution if condition evaluates to True
  or condition is None."""
  def __init__(self, condition = None, maxtimes=2000000):
    self.condition = condition
    self.maxtimes = maxtimes
    self.ntimes = 0
  def __call__(self, experiment, iteration=0):
    if self.ntimes < self.maxtimes and (self.condition is None or eval(self.condition)):
      self.ntimes += 1
      experiment.pause = True
      print "\n***Pausing experiment. To continue, call experiment.run()***"




##########################################################
# Callbacks for displaying Sensor output
##########################################################

class printSensorOutput(object):
  """Print sensor output every N iterations"""

  def __init__(self, updateEvery=1):
    self.updateEvery = updateEvery
    self.encoder = None
    self.dataOut = None
    self.resetOut = None
    self.sequenceIdOut = None

  def __call__(self, experiment, iteration=0):
    if not self.updateEvery:
      return

    if self.encoder is None:
      sensor = experiment.network.regions['sensor']
      self.encoder = sensor.getSelf().encoder
      self.dataOut = sensor.getOutputData('dataOut')
      self.resetOut = sensor.getOutputData('resetOut')
      self.sequenceIdOut = sensor.getOutputData('sequenceIdOut')

    if iteration % self.updateEvery == 0:
      if self.resetOut[0]:
        prefix = "%6d R " % iteration
      else:
        prefix = "%6d   " % iteration
      self.encoder.pprint(self.dataOut, prefix=prefix)



##########################################################
# Callbacks for displaying SP information
##########################################################


class printSPCoincidences(object):
  """Finish callback normally called after SP learning.
  Prints SP learned coincidences to the screen."""

  def __init__(self, updateEvery=50):
    self.updateEvery = updateEvery
    self.encoder = None
    self.sfdr = None

  def __call__(self, experiment, iteration=0):
    if not self.updateEvery:
      return

    if self.encoder is None:
      self.encoder = experiment.network.regions['sensor'].getSelf().encoder
      self.sfdr = experiment.network.regions['level1'].getSelf()._sfdr

    for i in xrange(self.sfdr.numCloneMasters):
      syns = self.sfdr._masterPermanenceM[i].toDense()
      syns = (syns >= self.sfdr.synPermConnected).astype('uint8')
      self.encoder.pprint(syns.flat, prefix="%3d"%i)


class displaySPCoincidences(object):
  """Ask the SP to display its coincidences"""
  def __init__(self, updateEvery=50):
    self.updateEvery = updateEvery
    self.encoder = None
    self.sfdr = None

    if  'NTA_AUTOBUILD_NO_DISPLAY' in os.environ:
      self.gui = False
      self.printer = printSPCoincidences(updateEvery)
    else:
      self.gui = True
      self.printer = None

  def __call__(self, experiment, iteration=0):
    if self.gui:
      if not self.updateEvery:
        return

      if iteration % self.updateEvery == 0:
        if self.encoder is None:
          _initPylab()
          self.encoder = experiment.network.regions['sensor'].getSelf().encoder
          self.sfdr = experiment.network.regions['level1'].getSelf()._sfdr

        self.sfdr._showCoincsImage(self.encoder)
    else:
      self.printer(experiment,iteration)


################################################################################
class PickleSPInitArgs(object):
  """ Saves FDRCSpatial2 initialization args
  """
  def __init__(self, filePath):
    """
    filePath: path of file where SP __init__ args are to be saved
    """

    self.__filePath = filePath

    return


  def __call__(self, experiment):

    import pickle

    sfdr = experiment.network.regions['level1'].getSelf()._sfdr

    initArgsDict = sfdr._initArgsDict


    # Write it out to a file as json
    absFilePath = os.path.abspath(self.__filePath)

    absDir = os.path.dirname(absFilePath)
    makeDirectoryFromAbsolutePath(absDir)

    with open(absFilePath, 'wb') as pickleFile:
      pickle.dump(initArgsDict, pickleFile)

    return


################################################################################
# Helper method called when creating a matplotlib plot
_pylabInitialized = False
def _initPylab():
  """
  Initialize pylab for plotting
  """
  global _pylabInitialized

  if pylabAvailable and not _pylabInitialized:
    pylab.ion()
    pylab.figure(2)
    pylab.figure(1)

    _pylabInitialized = True



##########################################################
# Callbacks for displaying TP information
##########################################################

class printTPTiming(object):
  """ Ask the TP to print out it's timing and segment information
  """
  def __init__(self, updateEvery = 0):
    """ Pass 0 to use as a finish callback
    """
    self.updateEvery = updateEvery

  def __call__(self, experiment, iteration=0):
    if self.updateEvery > 0 and ((iteration+1) % self.updateEvery) != 0:
      return

    tp = experiment.network.regions['level1'].getSelf()._tfdr
    if tp is not None:
      if self.updateEvery > 0:
        print "\n========= TP TIMING RESULTS, ITERATION: %d ============" \
              % (iteration)
      else:
        print "\n========= TP TIMING RESULTS ============" \

      if hasattr(tp, "cells4"):
        tp.cells4.dumpTiming()
        tp.cells4.resetTimers()
      print "\n========= TP SEGMENT INFORMATION ======="
      segInfo = tp.getSegmentInfo()
      print "Total number of segments =",segInfo[0]
      print "Total number of synapses =",segInfo[1]
      #print "d[n] = number of cells with n segments:"
      #pprint.pprint(segInfo[5])
      print "d[n] = number of segments with n synapses:"
      pprint.pprint(segInfo[4])
      print "d[n] = number cells with n segments:"
      pprint.pprint(segInfo[5])
      print "d[p] = number of synapses with perm = p/10:"
      pprint.pprint(segInfo[6])
      print "d[n] = number of segments last active n steps ago:"
      pprint.pprint(segInfo[7])
      print "total number of connected synapes = ",
      totalConnected = 0
      for (key, value) in segInfo[6].iteritems():
        if key/10.0 >= tp.connectedPerm:
          totalConnected += value
      print totalConnected
      print "average learned seq. length = ", tp.avgLearnedSeqLength
      print "=======================================\n"




################################################################################
def printTPCells(experiment):
    tp = experiment.network.regions['level1'].getSelf()._tfdr
    tp.printCells()



################################################################################
class PickleTPInitArgs(object):
  """ Saves TP10X2 initialization args
  """
  def __init__(self, filePath):
    """
    filePath: path of file where TP __init__ args are to be saved
    """

    self.__filePath = filePath

    return

  def __call__(self, experiment):
    import pickle

    tfdr = experiment.network.regions['level1'].getSelf()._tfdr

    initArgsDict = tfdr._initArgsDict


    # Write it out to a file as json
    absFilePath = os.path.abspath(self.__filePath)

    absDir = os.path.dirname(absFilePath)
    makeDirectoryFromAbsolutePath(absDir)

    with open(absFilePath, 'wb') as pickleFile:
      pickle.dump(initArgsDict, pickleFile)

    return




######################################################################
# Set a PyRegion attribute at the beginning of any phase
######################################################################

class setAttribute(object):
  def __init__(self, regionName, attributeName, value):
    self.regionName = regionName
    self.attributeName = attributeName
    self.value = value;

  def __call__(self, experiment, iteration=0):
    r = experiment.network.regions[self.regionName].getSelf()
    setattr(r, self.attributeName, self.value)


class setTPAttribute(object):
  """Sets 'attributeName' on the TP instance in 'regionName' to 'value'."""
  def __init__(self, attributeName, value, regionName = "level1"):
    self.regionName = regionName
    self.attributeName = attributeName
    self.value = value;

  def __call__(self, experiment, iteration=0):
    r = experiment.network.regions[self.regionName].getSelf()
    tp = r._tfdr
    if tp is not None:
      setattr(tp, self.attributeName, self.value)




#######################################################
# Log data to files
# Used automatically by the PF with --logOutputsToFile
#######################################################

def _logNonZeros(a, f):
  nz = a.nonzero()[0]
  outstr = " ".join(["%d" % int(token) for token in nz])
  print >> f, a.size, outstr

def _logSparse(a, f):
  nonzeros = a.nonzero()[0]
  outstr = " ".join(["%d %g" % (nz, a[nz]) for nz in nonzeros])
  print >> f, a.size, outstr

def _logDense(a, f):
  outstr = " ".join(["%f" % (token) for token in a])
  print >> f, outstr

def _logInt(a, f):
  print >> f, int(a)

def _logMultiDense(a, f):
  shape = a.shape
  _logInt(shape[0], f)
  for i in range(shape[0]):
    _logDense(a[i], f)

def getLogOutputsToFileCallbacks(baseFileName):
  openFiles = dict()
  arrays = dict()
  setupCallback = logOutputsToFileSetup(baseFileName, openFiles, arrays)
  iterCallback = logOutputsToFileIter(baseFileName, openFiles, arrays)
  finishCallback = logOutputsToFileFinish(baseFileName, openFiles, arrays)
  return (setupCallback, iterCallback, finishCallback)


class logOutputsToFileSetup(object):
  def __init__(self, baseFileName, openFiles, arrays):
    self.baseFileName = baseFileName
    self.openFiles = openFiles
    self.arrays = arrays

  def __call__(self, experiment):
    regions = experiment.network.regions
    if "sensor" in regions:
      # sensor bottom-up out
      self.openFiles['sensor'] = \
          open(self.baseFileName + "_sensorBUOut.txt", "w")
      self.arrays['sensor'] = \
          regions['sensor'].getOutputData("dataOut")

      # data source bottom-up out
      self.openFiles['source'] = \
          open(self.baseFileName + "_sourceScalars.txt", "w")
      self.arrays['source'] = \
          regions['sensor'].getOutputData("sourceOut")

      # sensor reset out
      self.openFiles['reset'] = \
          open(self.baseFileName + "_reset.txt", "w")
      self.arrays['reset'] = \
          regions['sensor'].getOutputData("resetOut")

    if "level1" in regions:
      if not regions['level1'].getParameter("disableSpatial"):
        # SP bottom-up out
        self.openFiles['sp'] = \
            open(self.baseFileName + "_spBUOut.txt", "w")
        self.arrays['sp'] = \
            regions['level1'].getSelf()._spatialPoolerOutput

        # SP reconstructed input
        if "spReconstructedIn" in regions['level1'].spec.outputs:
          spReconstructedIn = regions['level1'].getOutputData("spReconstructedIn")
          if spReconstructedIn.size > 0:
            self.openFiles['spRI'] = open(self.baseFileName \
                                      + "_spReconstructedIn.txt", "w")
            self.arrays['spRI'] = spReconstructedIn

      if "topDownOut" in regions['level1'].spec.outputs:
        topDownOutput = regions['level1'].getOutputData("topDownOut")

        # SP top-down out
        if topDownOutput.size > 0:
          self.openFiles['spTD'] = open(self.baseFileName + "_spTDOut.txt", "w")
          self.arrays['spTD'] = topDownOutput

      # TP bottom-up out - not currently needed and very large, so don't
      #  generate.
      #if not regions['level1'].getParameter("disableTemporal"):
      #  self.openFiles['tp'] = \
      #      open(self.baseFileName + "_tpBUOut.txt", "w")
      #  self.arrays['tp'] = \
      #      regions['level1'].getOutputData("bottomUpOut")

      # TP multi-step prediction data
      if regions['level1'].getParameter("nMultiStepPrediction") > 0:
        self.openFiles['prediction'] = open(self.baseFileName \
                                      + "_multiStepPrediction.txt", "w")
        self.arrays['prediction'] = \
            regions['level1'].getSelf()._multiStepInputPrediction

class logOutputsToFileIter(object):
  def __init__(self, baseFileName, openFiles, arrays):
    self.baseFileName = baseFileName
    self.openFiles = openFiles
    self.arrays = arrays

  def __call__(self, experiment, iteration=0):
    for t in ["sensor", "sp", "tp"]:
      if t in self.arrays:
        _logNonZeros(self.arrays[t], self.openFiles[t])

    for t in ["source", "spRI"]:
      if t in self.arrays:
        _logDense(self.arrays[t], self.openFiles[t])

    for t in ["spTD"]:
      if t in self.arrays:
        _logSparse(self.arrays[t], self.openFiles[t])

    if "reset" in self.arrays:
      _logInt(self.arrays["reset"], self.openFiles["reset"])

    if "prediction" in self.arrays:
      _logMultiDense(self.arrays["prediction"], self.openFiles["prediction"])

class logOutputsToFileFinish(object):
  def __init__(self, baseFileName, openFiles, arrays):
    self.baseFileName = baseFileName
    self.openFiles = openFiles
    self.arrays = arrays

  def __call__(self, experiment):
    for f in self.openFiles.values():
      f.close()
