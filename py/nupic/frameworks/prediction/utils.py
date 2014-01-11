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

import os
import sys
import time
import imp
import nupic.frameworks.prediction.callbacks as callbacks
from nupic.data.datasethelpers import findDataset, uncompressAndCopyDataset
from functools import partial
from collections import defaultdict

# This file contains utility functions that are used
# internally by the prediction framework. It should not be
# imported by description files. (see helpers.py)


##############################################################################
# Common values used by components of the prediction framework.
defaultSaveExtension = '.nta'
trainedNetworkName = 'trained'
untrainedNetworkName = 'untrained'

supportedOptions = ["logOutputsDuringInference", "verbosity"]



##############################################################################
def fixExperimentPath(path):
  """Verify and if needed fix an experiment path

  If the path is a relative path and doesn't start with a '.' but it doesn't
  point to a valid directory try to fix it by prefixing it with 'experiments'.
  That is very convenient in the common use case when running or cleaning
  experiments using RunExperiment.py, Cleanup.py or RunPermutations.py.

  After the path was fixed (if needed) the function checks if it's a valid
  directory andif not raises an exception using the original path.
  """
  fixedPath = path # Need original path for error message
  if not(path[0] == '.' and os.path.abspath(path)):
    if not os.path.isdir(path):
      fixedPath = 'experiments/' + path

  if not os.path.isdir(fixedPath):
    raise Exception('The is no such experiment: ' + path)

  return fixedPath


def findExperiment(path):
  return fixExperimentPath(path)



##############################################################################
descriptionImportCount = 0

def loadDescriptionFile(filename):
  """Reads a description file and returns is as a module.
  """
  global descriptionImportCount
  if not os.path.isfile(filename):
    raise RuntimeError("Experiment description file %s does not exist or is not a file" %
                       filename)

  mod = imp.load_source("pf_description%d" % descriptionImportCount,
                        filename)
  descriptionImportCount += 1

  for name in ["getDescription", "getBaseDatasets", "getDatasets"]:
    if not hasattr(mod, name):
      raise RuntimeError("Experiment description file %s does not define %s" %
                         (filename, name))

    if not callable(getattr(mod, name)):
      raise RuntimeError("Experiment description file %s defines %s but it "
                         "is not callable" % (filename, name))


  return mod

##############################################################################
def findAllDatasets(datasets):
  """Find all datasets in a dataset dictionary"""
  d = dict()
  for key in datasets:
    d[key] = findDataset(datasets[key])
  return d


##############################################################################
def uncompressAndCopyAllDatasets(datasets, destDir, overwrite):
  """If destDir is not None, we uncompress all datasets into that
  directory. Otherwise we uncompress them in place.
  If data is not compressed, then we just copy the file (if destDir is not None"""
  d = dict()
  for key in datasets:
    d[key] = uncompressAndCopyDataset(datasets[key], destDir, overwrite)
  return d


##############################################################################
def convertDescriptionToTestMode(description):
  """Takes a normalized description and sets iterationCount to a maximum
  of 10 for all steps."""
  print "Converting experiment to test mode..."
  runPhases = ["spTrain", "tpTrain", "classifierTrain", "infer", "postProcess"]
  for phase in runPhases:
    nsteps = len(description[phase])
    # no more than 10 steps -- cut out all the middle steps
    if nsteps > 10:
      print "Reducing phase '%s' from %d steps to 10 steps" % (phase, nsteps)
      lastSteps = description[phase][-5:]
      description[phase] = description[phase][0:5]
      description[phase].extend(lastSteps)
      nsteps = 10
    # no more than 10 iterations per step
    for i in xrange(nsteps):
      count = description[phase][i]['iterationCount']
      if count is None or count > 10:
        print "Reducing iteration count on step %d of phase %s from %s to 10" % \
            (i, phase, count)
        description[phase][i]['iterationCount'] = 10


##############################################################################
def normalizeDescription(description):

  runPhases = ["spTrain", "tpTrain", "classifierTrain", "infer", "postProcess"]
  allKeys = runPhases + ["network", "options", "directory"]
  substeps = ["setup", "iter", "runLoop", "finish"]

  for key in description:
    if key not in allKeys:
      raise RuntimeError("Description key '%s' is unknown. Allowed keys are %s"
                         % (key, str(allKeys)))

  #######################################################
  # Network
  #######################################################

  if 'network' not in description:
    raise RuntimeError("Description does not contain network definition")

  if 'directory' in description:
    description['directory'] = os.path.normpath(os.path.abspath(description['directory']))
  else:
    description['directory'] = None

  if not isinstance(description['network'], dict):
    raise RuntimeError("Network definition must be a dictionary")

  net = description['network']

  requiredNetworkEntries = ["sensorDataSource", "sensorEncoder"]
  for required in requiredNetworkEntries:
    if required not in net:
      raise RuntimeError("Required network description entry '%s' not found" %
                         required)

  # Defaults
  net.setdefault("sensorParams", dict())
  net.setdefault("sensorFilters", list())
  net.setdefault("CLAType", "py.CLARegion")
  net.setdefault("CLAParams", dict())
  net.setdefault("classifierType", None)
  net.setdefault("classifierParams", None)


  #######################################################
  # Run Phases -- spTrain, tpTrain, etc.
  #######################################################
  for phase in runPhases:
    # Each run phase is a list of steps where
    # each step is composed of substeps
    # setup/iteration/finish/postprocess

    if phase not in description or description[phase] is None:
      description[phase] = list()
      continue

    # make it a list of steps if not already
    # (this is normal if there is only one step)
    if isinstance(description[phase], dict):
      description[phase] = [description[phase]]

    # we need to be able to append to the phase,
    # to make sure it is a list, not a tuple
    if isinstance(description[phase], tuple):
      description[phase] = list(description[phase])

    #######################################################
    # Steps within a phase (each phase is a list of steps)
    #######################################################
    for i in xrange(len(description[phase])):
      step = description[phase][i]
      if not isinstance(step, dict):
        raise RuntimeError("Step %d of phase %s is not a dict" % (i, phase))
      if 'name' not in step:
        step['name'] = "step_%d" % i

      #######################################################
      # Substeps -- setup/iter/finish
      #######################################################

      # Make sure only recognized substeps are specified. Anything else
      # is probably a typo.
      for key in step:
        if key  not in substeps + ['name', 'iterationCount', 'ppOptions',
                                    'runLoop']:
          raise RuntimeError("Unknown key '%s' specified for step %s in phase %s" %
                             (key, step['name'], phase))


      for substep in substeps:
        if substep not in step or step[substep] is None:
          step[substep] = []
          continue

        # Generic form of a callback spec is:
        # [func1, func2, ... funcn]
        # The enclosing list can be imitted
        if not hasattr(step[substep], "__len__"):
          step[substep] = [step[substep]]

        for i in xrange(len(step[substep])):
          # Sanity check -- make sure callback is callable
          if not callable(step[substep][i]):
            raise RuntimeError("Element %d in substep %s in step %s in phase %s "
                               "is not a callback function" %
                               (i, substep, step, phase))
      # All steps should have an iteration count
      if "iterationCount" not in step:
        step['iterationCount'] = None

  if 'options' not in description:
    description['options'] = dict()

  if not isinstance(description['options'], dict):
    raise RuntimeError("'options' must be a dictionary")

  for key in description['options']:
    if key not in supportedOptions:
      raise RuntimeError("Option '%s' is not supported" % key)



##############################################################################
def addLogOutputsDuringInference(description, inferenceDir):

  for step in description['infer']:
    # step is a directionary
    baseName = os.path.join(inferenceDir, step['name'])
    (setupcallback, itercallback, finishcallback) = \
            callbacks.getLogOutputsToFileCallbacks(baseName)
    if "setup" not in step:
      step["setup"] = [setupcallback]
    else:
      step["setup"].append(setupcallback)

    if "iter" not in step:
      step["iter"] = [itercallback]
    else:
      step["iter"].append(itercallback)

    if "finish" not in step:
      step["finish"] = [finishcallback]
    else:
      step["finish"].append(finishcallback)


def addStepCallback(step, name, callback):
  callbacks = step.get(name, [])
  callbacks.append(callback)
  step[name] = callbacks


##############################################################################
def addStandardInferenceCallbacks(description):
  """
  Installs callbacks for the beginning and end of each inference run
  """
  for step in description['infer']:
    # step is a directionary
    testSetName = step['name']
    setupCallback = callbacks.setupInferenceRun(testSetName)
    finishCallback = callbacks.finishInferenceRun(testSetName)

    addStepCallback(step, 'setup', setupCallback)
    addStepCallback(step, 'finish', finishCallback)

##############################################################################
def addStandardTrainingCallbacks(description):
  """
  Installs callbacks for the beginning and end of each training run
  """
  for step in description['spTrain']:
    # step is a dictionary
    finishCallback = callbacks.finishSPTrainingStep()
    addStepCallback(step, 'finish', finishCallback)

  for step in description['tpTrain']:
    # step is a dictionary
    finishCallback = callbacks.finishTPTrainingStep()
    addStepCallback(step, 'finish', finishCallback)

##############################################################################
def printAvailableCheckpoints(directory):
  """
  List available checkpoints for the specified experiment.
  """
  directory = os.path.abspath(directory)
  if not os.path.exists(os.path.join(directory, 'networks')):
    print "No available checkpoints."
    return
  networkFiles = [x for x in os.listdir(os.path.join(directory, 'networks'))
    if x[0] != '.']
  if not networkFiles:
    print "No available checkpoints."
    return

  print "Available checkpoints:"
  if (untrainedNetworkName + defaultSaveExtension) in networkFiles:
    print "Untrained"
  checkpoints = []
  for networkFile in sorted(networkFiles):
    if '_' in networkFile:
      parts = networkFile.split('_')
      tier = parts[1].split('.')[0]
      checkpoints.append(tier)
  for checkpoint in sorted(checkpoints):
    print "%s start" % checkpoint
  if (trainedNetworkName + defaultSaveExtension) in networkFiles:
    print "Trained"

  print
  print "To start from a checkpoint:"
  print "  python RunExperiment.py experiment -t <PHASE>"
  print "For example, to start from the checkpoint saved before level1SP:"
  print "  python RunExperiment.py experiment -t level1SP"



class Timer(object):
  # list of nested timers
  allTimers = []
  activeTimers = []
  reporter = None

  @classmethod
  def setReporter(cls, reporter):
    cls.reporter = reporter

  @classmethod
  def printReport(cls, stdout=True):
    if cls.reporter is not None:
      reporter = cls.reporter
    else:
      # print to stdout
      reporter = Reporter()

    reporter.write("\n======= Timing Report ======", stdout=stdout)
    for t in cls.allTimers:
      reporter.write("%s %s" % ("--" * t.getLevel(), t.getMessage(hms=False)),
                     stdout=stdout)
    reporter.write("======= End Timing Report ======", stdout=stdout)

    reporter.write("\n======= Bottleneck Report ======", stdout=stdout)
    sortedTimers = sorted(cls.allTimers, key=lambda x:x.getElapsed(),
                          reverse=True)
    if len(sortedTimers) > 20:
      sortedTimers = sortedTimers[:20]
    for t in sortedTimers:
      reporter.write(t.getMessage(hms=False), stdout=stdout)
    reporter.write("======= End Bottleneck Report ======", stdout=stdout)


  @staticmethod
  def secsToHMS(secs):
    hours = int(secs/3600)
    secs = secs - hours*3600
    mins = int(secs/60)
    secs = secs - mins*60
    return (hours, mins, secs)

  def __init__(self, name):
    self.Level = len(Timer.activeTimers)
    self.name = name
    self.tic = time.time()
    self.running = True
    self.elapsed = None
    Timer.activeTimers.append(self.name)
    Timer.allTimers.append(self)

  def stop(self):
    if self.running:
      self.elapsed = time.time() - self.tic
      self.running = False
      if Timer.activeTimers is not None:
        if len(Timer.activeTimers) == 0 or Timer.activeTimers[-1] != self.name:
          print("WARNING: timers not properly nested. Stopped timer '%s' "
                "before sub-timers completed" % self.name)
          print "Current timer list:"
          for t in Timer.activeTimers:
            print "  %s" % t
          # timers are now all messed up -- don't print any more messages
          Timer.activeTimers = None
        else:
          Timer.activeTimers.pop()

  def getLevel(self):
    return self.Level

  def getElapsed(self, hms=False):
    if self.running:
      print "WARNING: called getElapsed() for timer '%s' before stopping timer" % self.name
      self.stop()
    if hms:
      hours, mins, secs = Timer.secsToHMS(self.elapsed)
      return '%3d h %2d m %5.2f s' % (hours, mins, secs)
    else:
      return self.elapsed

  def getName(self):
    return self.name

  def getMessage(self, hms=True):
    self.stop()
    if hms:
      t = self.getElapsed(hms)
    else:
      t = "%.2f" % self.getElapsed()
    message = "%s: %s" % (t, self.name)
    return message

  def __str__(self):
    return self.getMessage()

  def stopAndPrint(self, indent="", stdout=True):
    """Stop the timer and print the result"""
    self.stop()
    if type(indent) == str:
      strIndent = indent
    else:
      strIndent = " " * indent
    message = "%sElapsed:%s" % (strIndent, self.getMessage())
    if Timer.reporter is not None:
      Timer.reporter.write(message, stdout=stdout)
    elif stdout:
      print message
      sys.stdout.flush()


class Reporter(object):
  """A reporter writes information to a report file and
  optionally to the terminal."""

  def __init__(self, filename):
    if filename is not None:
      self.isStdout = False
      if not os.path.exists(filename):
        self.f = open(filename, "w")
      else:
        self.f = open(filename, "a")
        self.f.write(os.linesep)
    else:
      sys.isStdout = True
      self.f = sys.stdout


  ##############################################################################
  def writeTitle(self, title):
    """
    Print the title and the current time into the report file
    """

    timeStr = time.strftime('%c %Z')
    titleLen = len(title)
    timeLen = len(timeStr)
    maxLen = max(titleLen, timeLen)
    self.write(''.join(['-']*(maxLen+4)), stdout=False)
    self.write('| %s%s |' % (title, ''.join([' ']*(maxLen-titleLen))),
               stdout=False)
    self.write('| %s%s |' % (timeStr, ''.join([' ']*(maxLen-timeLen))),
               stdout=False)
    self.write(''.join(['-']*(maxLen+4)), stdout=False)



  ##############################################################################
  def write(self, text, stdout=True):
    """
    Write the text to the report and flush the file.

    report -- an open file handle
    printConsole -- if True, also prints the text to the console

    """
    if stdout and not self.isStdout:
      print text
      sys.stdout.flush()

    self.f.write(text + os.linesep)
    self.f.flush()
