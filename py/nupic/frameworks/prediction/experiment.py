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
import math
import json
import time
import shutil
import cPickle
import pprint
import types
import socket
from optparse import OptionParser
from collections import defaultdict

from nupic.engine import Network
import utils
from utils import Timer
from utils import addStepCallback
from utils import normalizeDescription
from utils import loadDescriptionFile
from nupic.data.datasethelpers import findDataset, uncompressAndCopyDataset


from nupic.data.file_record_stream import FileRecordStream

class Position(object):
  def __init__(self, phase=0, step=0, iter=0):
    assert isinstance(phase, int)
    assert isinstance(step, int)
    assert isinstance(iter, int)
    self._phase = phase
    self.step = step
    self.iter = iter

  def __repr__(self):
    return '%d, %d, %d' % (self.phase, self.step, self.iter)

  def __str__(self):
    return repr(self)

  @property
  def phase(self):
    return self._phase

  @phase.setter
  def phase(self, value):
    self._phase = value

class Experiment(object):

  """An experiment represents a sequence of steps to create, train,
  and test an HTM network. The details of these steps is described by
  entries in a dictionary called the "description". The experiment
  description is usually specified in a file called description.py.

  a random message...

  The description of an experiment and the results of an experiment
  (untrained network, trained network, results, etc.) are stored in an
  experiment directory.

  The lightweight prediction framework assumes a network structure like this

  classifier
      |
   CLARegion
      |
  RecordSensor

The classifier may be missing.

Network description:

  description['network'] = dict(
     sensorDataSource=<sensor data source> (datasource object),
     sensorEncoder=<encoder> (encoder object),
     sensorFilters=[list of pre-encoding sensor filters]
     sensorParams=<create params for sensor> (dict)
     CLAType=<region type for CLARegion> (string)
     CLAParams=<create params for the CLA Region> (dict)
     classifierType=<string> or None
     classifierParams=<create params for CLA Region> (dict) or None)

Experiment steps:
The phases of an experiment are:
1. create network
2. train the sp ("spTrain")
3. train the tp ("tpTrain")
4. train the classifier ("classifierTrain")
5. infer ("infer")

Each of phases 2,3,4,5 consists of zero or more "steps", aka training steps
or inference steps.
A "step" has three pieces ("substeps")
"setup", "iter", "finish", and an iteration count, and each
of these substeps is specified by a list of callback objects.
[The postprocess step only has a "finish" substep -- the setup
and iter substeps are not used]

  setup -- called before the step to set up the network/sensor
  iter -- called after each network iteration
  finish -- called when the step is finished


Additionally, if "iterationCount", if not None, is the number of iterations
to run.

The callbacks are just lists of callables:

step = dict(
    iterationCount = 100,
    setup = [callback1, callback2],
    iter = [callback3, callback4],
    finish = callback5
)

Each callback is a callable. For the above
step definition, the step would be executed roughly as:
   callback1.(experiment)
   callback2.(experiment)
   for i in xrange(iterationCount):
     experiment.run(1)
     callback3.(experiment, i)
     callback4.(experiment, i)
   callback5(experiment)

If there is only one callback, it may be given directly, rather
than inside a list, as with the finish callback above.

Also, there are standard callbacks that are added
to setup/finish for each iteration step.

Some optional functionality can be handled automatically by the
LPF. These are specified in the "options". Currently supported options
are:

  logOutputsDuringInference (boolean)
  runGUI


Running experiments

The run() method is the entry point for running experiments. It goes through
the workflow and runs through each step of each phase for the prescribed
number of iterations. The experiment tracks its position in the workflow:
phase, step, iteration. If during a callback the self.pause attribute is set
the experiment will return immediately. If you call run() again, it will
continue to run from the last position.
"""

  @staticmethod
  def parseOptions(args):
    """

    Parse command line options for RunExperiment.py
    args: command line arguments (not including sys.argv[0])

    Returns (experiments, experimentOptions, otherOptions) where
    experiments is a list of experiment names
    experimentOptions is a dictionary of options that are passed to the experiment
    """
    parser = OptionParser()
    parser.add_option("-c", help="Create network",
                      dest="createNetworkOnly", action="store_true", default=False)
    parser.add_option("-t", help="Train network. <PHASE> indicates where to start training. "
                      "If <PHASE> is specified, -c flag is disallowed. "
                      "Run with -l flag for more details. ",
                      dest="trainFromPhase", action="store", type="string", metavar="<PHASE>")
    parser.add_option("-l", help="List all available checkpoints",
                      dest="listAvailableCheckpoints", action="store_true", default=False)
    parser.add_option("-r", help="Run inference with the trained net",
                      dest="runInferenceOnly", action="store_true", default=False)
    parser.add_option("-p", help="Run postprocessing only with logged outputs",
                      dest="postProcessOnly", action="store_true", default=False)
    parser.add_option("-g", help="Run experiment with GUI",
                      dest="runGUI", action="store_true", default=False)
    parser.add_option("-v", "--verbosity", help="Verbosity level of the output",
                      dest="verbosity", action="store", type="int", default=1)

    parser.add_option("--postProcess", help="turn on output logging and "
                      "compute sp statistics after inference during postProcessing",
                      dest="postProcess", action="store_true", default=False)
    parser.add_option("--logOutputs", help="turn on output logging (needed for computing sp statistics)",
                      dest="logOutputsDuringInference", action="store_true", default=False)
    parser.add_option("--profilePython", help="turn on cProfile-based profiling",
                      dest="profilePython", action="store_true", default=False)
    parser.add_option("--profile", help="turn on LPF and NuPIC profiling",
                      dest="profile", action="store_true", default=False)
    parser.add_option("--keepData", help="Keep existing generated datasets",
                      dest="keepData", action="store_true", default=False)
    parser.add_option("--testMode", help="Reduce iteration count for testing",
                      dest="testMode", action="store_true", default=False)
    parser.add_option("--checkpoint", help="Checkpoint network before it is fully trained",
                      dest="checkpoint", action="store_true", default=False)


    (options, experiments) = parser.parse_args(args)


    mutuallyExclusiveOptionCount = sum([(options.trainFromPhase is not None),
                                        options.createNetworkOnly,
                                        options.runInferenceOnly,
                                        options.postProcessOnly])

    if mutuallyExclusiveOptionCount > 1:
      print "Options: -c, -t<PHASE>, -r, -p are mutually exclusive\n" \
          "Please select only one"
      sys.exit(1)

    experimentOptions = dict()

    experimentOptions['logOutputsDuringInference'] = options.logOutputsDuringInference or options.postProcess
    experimentOptions['postProcess'] = options.postProcess or options.postProcessOnly
    experimentOptions['createNetworkOnly']         = options.createNetworkOnly
    experimentOptions['trainFromPhase']            = options.trainFromPhase
    experimentOptions['runInferenceOnly']          = options.runInferenceOnly
    experimentOptions['postProcessOnly']           = options.postProcessOnly
    experimentOptions['runGUI']                    = options.runGUI
    experimentOptions['verbosity']                 = options.verbosity
    experimentOptions['cleanData']  = not options.keepData
    experimentOptions['testMode'] = options.testMode
    experimentOptions['checkpoint'] = options.checkpoint

    # Tells experiment to collect NuPIC profiling information and
    # to print NuPIC info.
    experimentOptions['profile']                   = options.profile

    otherOptions = dict()
    otherOptions['profilePython'] = options.profilePython
    otherOptions['listAvailableCheckpoints'] = options.listAvailableCheckpoints

    return (experiments, experimentOptions, otherOptions)



  ##############################################################################
  def __init__(self, path=None, module=None, description=None, runtimeOptions={},
        generatedDatasets=None):
    """Create an experiment from one of:
    1. a path to a directory which contains description.py (string)
    2. a module object (the result of loadDescriptionModule())
    3. a dictionary object (the result of module.getDescription())

    For the path/module variants, we generate any needed datasets.
    For the dictionary variant, we assume all needed datasets have already
    been generated.

    """

    count = (path is not None) + (module is not None) + (description is not None)
    if count != 1:
      raise Exception("Exactly one of 'path', 'module', or 'description' must be "
                      "specified to create an experiment")

    # Default of True is temporary
    debugDatasets = runtimeOptions.get('debugDatasets', True)

    self.directory = None
    if path is not None:
      assert isinstance(path, basestring)
      filename = os.path.join(path, "description.py")
      # Convert from path to module
      module = loadDescriptionFile(filename)

    if module is not None:
      assert isinstance(module, types.ModuleType)

      print "Loaded module from %s" % module.__file__
      self.directory = os.path.dirname(os.path.abspath(module.__file__))

      # --------------------------------------------------------------------
      # Get the paths to the required datasets, if they weren't passed in to us
      if generatedDatasets is None:
        #  Find base datasets
        baseDatasets = module.getBaseDatasets()
        if debugDatasets:
          print "Experiment '%s' requires these base datasets:" % module.__file__
          for key in baseDatasets:
            print "   %s: %s" % (key, baseDatasets[key])

        for key in baseDatasets:
          fullPath = findDataset(baseDatasets[key])
          # Uncompress if necessary
          # Since we don't specify destDir, this will uncompress in place
          fullPath = uncompressAndCopyDataset(fullPath)
          baseDatasets[key] = fullPath

        # Convert from module to dictionary; Generate any needed files.
        requiredDatasets = module.getDatasets(baseDatasets, generate=False)

        disableDataGeneration = runtimeOptions.get('disableDataGeneration', False)
        if not disableDataGeneration:
          if debugDatasets:
            print "Experiment '%s' will use these datasets:" % module.__file__
            for key in requiredDatasets:
              print "   %s: %s" % (key, requiredDatasets[key])

          if runtimeOptions.get('cleanData', False):
            filesToDelete = set(requiredDatasets.values()) - set(baseDatasets.values())
            for f in filesToDelete:
              if os.path.exists(f):
                print "Removing generated file %s" % f
                os.remove(f)
      else:
        requiredDatasets = generatedDatasets

      # --------------------------------------------------------------------
      # See if each of the required datasets is present, if any are not, call the
      #  experiment's getDatasets( _, generate=True) method to generate
      filesNotFound = set()
      for f in requiredDatasets.values():
        if not os.path.exists(f):
          filesNotFound.add(f)

      if len(filesNotFound) > 0:
        if not disableDataGeneration:
          if debugDatasets:
            print "One or more required datasets must be generated. Generating data..."
          datasets = module.getDatasets(baseDatasets, generate=True)
          assert set(requiredDatasets.values()) == set(datasets.values())
        else:
          raise RuntimeError("Some required datasets should have been generated, before running this experiment, but weren't: %s" % filesNotFound)

      description = module.getDescription(requiredDatasets)

    # at this point we always have a description
    normalizeDescription(description)

    if runtimeOptions.get('testMode', False):
      utils.convertDescriptionToTestMode(description)

    self.description = description

    if self.directory is None:
      if self.description["directory"] is not None:
        self.directory = self.description['directory']
      else:
        raise RuntimeError("The experiment description does not contain a directory")

    self.done = False

    # Erase previous results file, if it exists
    resultsFile = self.getResultsPath()
    if os.path.exists(resultsFile):
      os.remove(resultsFile)

    # Initialize timers to None
    self.spTimer = None
    self.tpTimer = None
    self.classifierTimer = None
    self.inferTimer = None
    self.overallTimer = None

    # Init other variables
    self._pause = True
    self.position = Position()
    self.network = None

    # Make sure all needed subdirectories exist
    networkDir = self.getNetworkDirectory()
    if not os.path.exists(networkDir):
      os.mkdir(networkDir)

    # process options and merge with runtimeOptions
    options = self.description['options']
    options.update(runtimeOptions)

    self.verbosity = options.get('verbosity', 1)
    self.doProfile =  options.get('profile', False)
    # Whether or not to checkpoint
    self.checkpoint = runtimeOptions.get('checkpoint', False)

    self.options = options
    self._registerCallbacks()

    # Print to report file
    reportfile = os.path.join(self.directory, 'report.txt')
    self.reporter = utils.Reporter(reportfile)
    self.reporter.writeTitle("Experiment %s" % (self.directory))
    self.reporter.write("Command line options: %s" % (str(runtimeOptions)),
                      stdout=False)

    # Timers print themselves to the report file
    # These are global settings for all timers
    Timer.setReporter(self.reporter)

    # Setup results dictionary
    self.results = dict()

    # Sets self.workflow and returns network to load.
    checkpointLabel = self._setup()

    # Create or load the experiment network
    self._getNetwork(checkpointLabel)


  ##############################################################################
  def _registerCallbacks(self):
    step = dict(name='FinishLearning',
                iterationCount=0,
                setup=[],
                iter=[],
                finish=[self.finishCLALearning])
    self.description['tpTrain'].append(step)

    # Add the standard inference callbacks
    utils.addStandardInferenceCallbacks(self.description)

    # Add the standard training callbacks
    utils.addStandardTrainingCallbacks(self.description)

    o = defaultdict(lambda: False, self.options)
    if o['logOutputsDuringInference']:
      # Automatically log outputs during each inference phase.
      # Remove any output from previous runs
      infDir = self.getInferenceDirectory()
      if os.path.exists(infDir):
        shutil.rmtree(infDir)
      os.mkdir(infDir)
      utils.addLogOutputsDuringInference(self.description, infDir)


  ##############################################################################
  def _createNetwork(self):
    self.reporter.write("Creating network...", stdout=self.verbosity>0)

    nd = self.description['network']

    n = Network()
    n.addRegion("sensor", "py.RecordSensor", json.dumps(nd['sensorParams']))
    sensor = n.regions['sensor'].getSelf()
    sensor.encoder = nd['sensorEncoder']
    sensor.dataSource = nd['sensorDataSource']
    sensor.preEncodingFilters = nd['sensorFilters']

    n.addRegion("level1", nd['CLAType'], json.dumps(nd['CLAParams']))

    n.link("sensor", "level1", "UniformLink", "")
    n.link("sensor", "level1", "UniformLink", "",
           srcOutput="resetOut", destInput="resetIn")

    if 'classifierType' in nd and nd['classifierType'] is not None:
      n.addRegion("classifier", nd['classifierType'],
                  json.dumps(nd['classifierParams']))
      n.link("level1", "classifier", "UniformLink", "")
      n.link("sensor", "classifier", "UniformLink", "",
             srcOutput="categoryOut", destInput="categoryIn")


    if self.checkpoint:
      filename = self.getNetworkPath(None)
      n.save(filename)
    self.network = n


  ##############################################################################
  # public method called by postprocess

  def loadNetwork(self, checkpointLabel):
    filename = self.getNetworkPath(checkpointLabel)
    self.network = Network(filename)
    # NuPIC doesn't initialize the network until you try to run it
    # but users may want to access components in a setup callback
    self.network.initialize()


  ##############################################################################
  def _getCallbackInfo(self, callback):
    if isinstance(callback, types.FunctionType):
      return 'function ' + callback.__name__ + '()'
    elif isinstance(callback, types.MethodType):
      return 'method ' + callback.im_class.__name__ + '.' + callback.__name__ + '()'
    elif isinstance(callback, types.InstanceType):
      return 'object ' + callback.__class__.__name__
    else:
      return str(type(callback)) + " of unknown type"

  ##############################################################################
  def call(self, callbacks):
    """
    Invoke each callback on the network.
    """
    assert hasattr(callbacks, '__iter__')
    for callback in callbacks:
      try:
        assert callable(callback)
        callback(self)
      except Exception, e:
        # Construct the error message intelligently based on the callback type
        message = 'Callback %s failed. ' % self._getCallbackInfo(callback)
        message += str(e.args[0]) if len(e.args) > 0 else ''
        e.args = (message,) + e.args[1:]
        #from dbgp.client import brk; brk(port=9011)
        raise

  ##############################################################################
  def callWithIteration(self, callbacks, iteration):
    """
    Invoke each callback on the network.
    """
    for callback in callbacks:
      try:
        assert callable(callback)
        callback(self, iteration)
      except Exception, e:
        # Construct the error message intelligently based on the callback type
        message = 'Callback %s failed at iteration %d ' % \
            (self._getCallbackInfo(callback), iteration)
        message += str(e.args[0]) if len(e.args) > 0 else ''
        e.args = (message,) + e.args[1:]
        raise

  ##############################################################################
  def runNetwork(self, iterationCount, callbacks):
    if iterationCount == 0:
      return True

    if iterationCount is None:
      printProgressEvery = 1000
      # Run until we get a StopIteration
      # upper bound is larger than any experiment we might run
      dataSource = self.network.regions['sensor'].getSelf().dataSource
      if isinstance(dataSource, FileRecordStream):
        if dataSource.rewindAtEOF:
          raise RuntimeError("iterationCount=None and rewindAtEOF are incompatible")
      maxIters =  2000000000
    else:
      printProgressEvery = int(math.ceil(iterationCount/20.0))
      printProgressEvery = min(1000, printProgressEvery)
      maxIters = iterationCount
    printNumItersEvery = 10000

    lastPct = None
    try:
      for i in xrange(0, maxIters):

        # Print progress
        if self.verbosity > 0 and i>0 and i % printProgressEvery == 0:
          if iterationCount is None:
            print ".",
          else:
            pct = (100 * i / iterationCount)
            if pct != lastPct:
              print "%d%%" % (100 * i / iterationCount),
            else:
              print ".",
            lastPct = pct
          sys.stdout.flush()

        if self.verbosity > 0 and iterationCount is None and i>0 \
              and i % printNumItersEvery == 0:
          print i,
          sys.stdout.flush()

        # Run the netowkr
        self.network.run(1)

        self.callWithIteration(callbacks, self.position.iter)
        self.position.iter += 1
        if self.pause:
          break

      if self.verbosity > 0:
        print
      done = i == maxIters - 1
      return done

    except StopIteration, e:
      if iterationCount is not None:
        raise Exception("File ran out of data at iteration %d of %d" % (i,iterationCount))
      self.reporter.write("\n%d iterations total" % i, stdout=self.verbosity>0)
      return True


  ##############################################################################
  def runStep(self, step, phaseName):
    if not 'timer' in step:
      step['timer'] = Timer("Phase %s step %s" % (phaseName, step['name']))
      self.reporter.write("Running phase %s step '%s'" % (phaseName, step['name']),
                        stdout=self.verbosity > 0)

    # Call callback only if beginning a step (not if continuing)
    if self.position.iter == 0:
      self.call(step['setup'])
      if self.pause:
        return False

    if step['iterationCount'] is None:
      iterationCount = None
    else:
      # Find out how many iterations until the end of the step
      iterationCount = step['iterationCount'] - self.position.iter

    # Doing special run loop that supports multi-step prediction?
    # This is a temporary "hack" initially put in to evaluate multi-step
    #  prediction on the monthly tourism dataset
    if 'runLoop' in step and len(step['runLoop']) > 0:
      done = step['runLoop'][0](self, iterationCount, step['iter'])
    else:
      done = self.runNetwork(iterationCount, step['iter'])
    if done:
      if step['iterationCount'] is not None:
        assert self.position.iter == step['iterationCount']

      step['timer'].stopAndPrint(stdout=self.verbosity > 0)
      del step['timer']
      # Move to next step
      self.position.step += 1
      # Reset iteration to 0
      self.position.iter = 0
      self.call(step['finish'])

    return done

  def runPhase(self, name):
    if self.doProfile:
      self.network.resetProfiling()
      self.network.enableProfiling()

    phase = self.description[name]
    startStep = self.position.step
    assert 0 <= startStep < len(phase)
    done = False
    steps = phase[startStep:]
    for i, step in enumerate(steps):
      done = self.runStep(step, name)
      if self.pause:
        break

    # Last step completed
    if i == (len(steps) - 1) and done:
      if self.doProfile:
        self.network.disableProfiling()
        self._printNuPICProfile(name)

      self.position.phase += 1
      self.position.step = 0
      return True
    else:
      return False

  def _printNuPICProfile(self, name):

    self.reporter.write("|---  %s %s-------------------------------------|" %
                        (name, ("-" * (10 - len(name)))))
    self.reporter.write("|    region |  avg compute | total compute |        n |")
    for r in self.network.regions:
      computeTimer = self.network.regions[r].getComputeTimer()
      # Not currently interested in execution time
      # executeTimer = r.getExecuteTimer()
      if computeTimer.getStartCount() > 0:
             self.reporter.write("|%10s |%13.6f | %13.6f | %8d |" %
                   (r,
                    computeTimer.getElapsed()/computeTimer.getStartCount(),
                    computeTimer.getElapsed(), computeTimer.getStartCount()))
    print "|---------------------------------------------------- |"

  ##############################################################################
  def trainSP(self):
    if len(self.description["spTrain"]) == 0:
      print "No SP training  specified"
      done = True
    else:
      if not self.spTimer:
        self.spTimer = Timer("Train SP")
        self.reporter.write("Training SP...", stdout=self.verbosity>0)

      level1 = self.network.regions['level1']
      level1.setParameter("trainingStep", "spatial")
      done = self.runPhase('spTrain')

      if done:
        self.spTimer.stopAndPrint(stdout=self.verbosity>0)
        if self.checkpoint:
          filename = self.getNetworkPath("level1SP")
          self.network.save(filename)

    return done

  ##############################################################################
  def trainTP(self):
    if len(self.description["tpTrain"]) == 0:
      print "No TP training specified"
      # just save the network as "level1" and bail out
      if self.checkpoint:
        filename = self.getNetworkPath("level1")
        self.network.save(filename)
      return True
    else:
      if not self.tpTimer:
        self.tpTimer = Timer("Train TP")
        self.reporter.write("Training TP...", stdout=self.verbosity>0)

      level1 = self.network.regions['level1']
      level1.setParameter("trainingStep", "temporal")

      done = self.runPhase('tpTrain')
      if done:
        self.tpTimer.stopAndPrint(stdout=self.verbosity>0)

      return done

  ##############################################################################
  def finishCLALearning(self, *args, **kwargs):
    # turn off learning mode
    t = Timer("Finish CLA Learning")
    if self.verbosity > 0:
        print "Finish Learning"
    level1 = self.network.regions['level1']
    level1.setParameter("learningMode", 0)
    level1.setParameter("inferenceMode", 1)
    t.stopAndPrint(stdout=self.verbosity>0)

    if self.checkpoint:
      filename = self.getNetworkPath("level1")
      self.network.save(filename)

  ##############################################################################
  def trainClassifier(self):
    if len(self.description["classifierTrain"]) == 0:
      print "No classifier specified"
      done = True
    else:
      if not self.classifierTimer:
        self.classifierTimer = Timer("Train Classifier")
        if self.verbosity > 0:
          print "Training Classifier"

      # These three lines are wrong.
      level1 = self.network.regions['level1']
      level1.setParameter("trainingStep", "temporal")
      done = self.runPhase('classifierTrain')

      if done:
        self.classifierTimer.stopAndPrint(stdout=self.verbosity>0)

    if done:
      # save the fully trained network unconditionally
      filename = self.getNetworkPath("all")
      self.network.save(filename)

    return done

  ##############################################################################
  def infer(self):
    if len(self.description["infer"]) == 0:
      print "No inference specified"
      return True

    if not self.inferTimer:
      self.inferTimer = Timer("Infer")
      self.reporter.write("Running inference...", stdout=self.verbosity>0)

    done = self.runPhase('infer')
    if done:
      self.inferTimer.stopAndPrint(stdout=self.verbosity>0)

    return done

  ##############################################################################
  def _setup(self):
    """
      This function prepares the workflow, and also selects
      which checkpoint network is to be loaded, based on the user options.
    """

    workflowSteps = [
      ('spTrain', self.trainSP),
      ('tpTrain',self.trainTP),
      ('classifierTrain', self.trainClassifier),
      ('infer', self.infer)]

    phases = [s[0] for s in workflowSteps]

    # These are the default starting and ending points for the workflow
    startingPoint   = phases.index('spTrain')
    endingPoint     = None  # all the way to the end
    checkpointLabel = None

    # The starting and ending points for the workflow and the network are
    # modified based on the user options
    options = self.description['options']

    # This block deals with the user option to train the network from an
    # available checkpointLabel
    # Option: -t <PHASE>
    trainFromPhase = options.get('trainFromPhase', None)
    if trainFromPhase is not None:
      if trainFromPhase=='level1SP':
        # XXX -t level1SP just starts from loading untrained.nta instead
        # of re-creating the network. Is this useful?
        startingPoint    = phases.index('spTrain')
        endingPoint      = phases.index('infer')
        checkpointLabel  = "untrained"

      elif trainFromPhase=='level1TP':
        startingPoint    = phases.index('tpTrain')
        endingPoint      = phases.index('infer')
        checkpointLabel  = "level1SP"

      elif trainFromPhase in ('classifier'):
        startingPoint    = phases.index('classifierTrain')
        endingPoint      = phases.index('infer')
        checkpointLabel  = "level1"
      else:
        assert 0, "Unsupported train phase: %s "   \
                  "\nChoose from level1SP, level1TP, classifier" % trainFromPhase

    # This block deals with the user option to create network only
    # Option: -c
    if options.get('createNetworkOnly', False):
      startingPoint    = phases.index('spTrain')
      endingPoint      = phases.index('spTrain') # start==end means no workflow
      checkpointLabel  = None

    # This block deals with the user option to run inference only
    # Option: -r
    if options.get('runInferenceOnly', False):
      startingPoint    = phases.index('infer')
      endingPoint      = None
      checkpointLabel  = 'all'

    self.workflow = workflowSteps[startingPoint:endingPoint]
    return checkpointLabel

  def _getNetwork(self, checkpointLabel):
    """Create or load the experiment network"""
    if checkpointLabel is not None:
      try:
        self.loadNetwork(checkpointLabel)
      except Exception, e:
        message = "Loading network has failed in prepareWorkFlow," \
                  " check available checkpoints with option -l\n %s" % e.args[0]
        #"\nNetwork %s does not exist" % self.getNetworkPath(trainFromPhase)
        e.args = (message,) +e.args[1:]
        raise
    else:
      self._createNetwork()



  ##############################################################################
  def run(self):
    print
    if self.done:
      return True

    self._pause = False
    self.done = True
    if not self.overallTimer:
      self.overallTimer = Timer("Overall")

    if self.workflow:
      startPhase = self.position.phase
      assert 0 <= startPhase < len(self.workflow)
      workflow = self.workflow[startPhase:]

      done = False
      for i,f in enumerate(workflow):
        #print i, 'Running phase:', f[0]
        done = f[1]()
        if self.pause:
          break

      # Last phase is done
      self.done = i == (len(workflow) - 1) and done
    else:
      # If there is no workflow you are done (e.g. when just creating a network)
      self.done = True

    if self.done:
      self.overallTimer.stopAndPrint(stdout=self.verbosity)
      self.results['overallTime'] = self.overallTimer.getElapsed()

      trainingTime = 0
      if self.spTimer:
        trainingTime += self.spTimer.getElapsed()
      if self.tpTimer:
        trainingTime += self.tpTimer.getElapsed()
      self.results['trainingTime'] = trainingTime

      if self.inferTimer:
        self.results['testingTime'] = self.inferTimer.getElapsed()
      else:
        self.results['testingTime'] = 0

      self.writeResults()
      if self.doProfile:
        Timer.printReport()

  ##############################################################################
  def getInferenceDirectory(self):
    return os.path.join(self.directory, "inference")

  ##############################################################################
  def getNetworkDirectory(self):
    return os.path.join(self.directory, "networks")

  ##############################################################################
  def getResultsPath(self):
    return os.path.join(self.directory, "results.pkl")

  ##############################################################################
  def getNetworkPath(self, checkpointLabel):
    if checkpointLabel is None or checkpointLabel == "untrained":
      return os.path.join(self.directory, "networks/untrained.nta")
    elif checkpointLabel == "level1SP":
      return os.path.join(self.directory, "networks/trained_level1SP.nta")
    elif checkpointLabel == "level1":
      return os.path.join(self.directory, "networks/trained_level1.nta")
    elif checkpointLabel == "classifier" or checkpointLabel == "all":
      return os.path.join(self.directory, "networks/trained.nta")
    else:
      raise RuntimeError("Unknown checkpoint label: '%s'" % checkpointLabel)


  ##############################################################################
  def writeResults(self):
    """Write the results file..
    If the file already exists, it overwrites the previous version
    """

    d = dict()
    d['results'] = self.results
    #d['description'] = self.description
    d['name'] = self.directory

    if self.verbosity >= 2:
      print "Results stored in pickled results file:"
      pprint.pprint(d)

    f = open(self.getResultsPath(), "wb")
    cPickle.dump(d, f)
    f.close()

  @property
  def pause(self):
    return self._pause

  @pause.setter
  def pause(self, value):
    self._pause = value

def test():
  pass

if __name__ == "__main__":
  #test()
  print "Use 'RunExperiment.py' in the examples/prediction directory"
  sys.exit(1)
