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
This script provides the runExperiment() API function that is used
by the command-line client run_opf_experiment.py of Online Prediction
Framework (OPF). It executes a single experiment.

This runner is generally run through `scripts/run_opf_experiment.py`.
"""

from collections import namedtuple
import itertools
import logging
import optparse
import os
import sys

import random
import numpy

from nupic.data import json_helpers
from nupic.frameworks.opf import opf_basic_environment, helpers
from nupic.frameworks.opf.exp_description_api import OpfEnvironment
from nupic.frameworks.opf.model_factory import ModelFactory
from nupic.frameworks.opf.opf_task_driver import OPFTaskDriver
from nupic.frameworks.opf.opf_utils import (InferenceElement, matchPatterns,
                                            validateOpfJsonValue)
from nupic.support import initLogging



g_defaultCheckpointExtension = ".nta"


# Schema of the Private Command-line Options dictionary returned by
# _parseCommandLineOptions(). This "Private" options dict is consumed internally
# by runExperiment (i.e. not passed to external modules).
g_parsedPrivateCommandLineOptionsSchema = {
  "description":"OPF RunExperiment control args",
  "type":"object",
  "additionalProperties":False,
  "properties":{
    "createCheckpointName":{
      "description":"Create a model and save it under the checkpoint name, " + \
                    "but don't run it. " + \
                    "TODO: 'blank' is a non-standard JSON schema setting; " + \
                    "validictory 8.0 supports a blank_by_default arg.",
      "required":True,
      "type":"string",
      "minLength":0,
      "blank":True
    },

    "listAvailableCheckpoints":{
      "description":"List all checkpoints and exit",
      "required":True,
      "type":"boolean"
    },

    "listTasks":{
      "description":"List all tasks and exit",
      "required":True,
      "type":"boolean"
    },

    "runCheckpointName":{
      "description":"Name of saved checkpoint to load and run" + \
                    "TODO: 'blank' is a non-standard JSON schema setting; " + \
                    "validictory 8.0 supports a blank_by_default arg.",
      "required":True,
      "type":"string",
      "minLength":0,
      "blank":True
    },

    "newSerialization":{
      "description":"Use new capnproto serialization.",
      "required":True,
      "type":"boolean"
    },

    #"reuseDatasets":{
    #  "description":"Keep existing generated/aggregated datasets",
    #  "required":True,
    #  "type":"boolean"
    #},

    "testMode":{
      "description":"True to override iteration counts with very small values",
      "required":True,
      "type":"boolean"
    },

    "taskLabels":{
      "required":False,
      "type":"array",
      "uniqueItems":False,
      "minItems":0,
      "items":{"type":"string", "minLength":1}
    },

    "checkpointModel":{
      "description":"True to checkpoint model after running each task",
      "required":True,
      "type":"boolean"
    },

  }
}



def runExperiment(args, model=None):
  """
  Run a single OPF experiment.

  .. note:: The caller is responsible for initializing python logging before
     calling this function (e.g., import :mod:`nupic.support`;
     :meth:`nupic.support.initLogging`)

  See also: :meth:`.initExperimentPrng`.

  :param args: (string) Experiment command-line args list. Too see all options,
      run with ``--help``:

      .. code-block:: text

        Options:
          -h, --help           show this help message and exit
          -c <CHECKPOINT>      Create a model and save it under the given <CHECKPOINT>
                               name, but don't run it
          --listCheckpoints    List all available checkpoints
          --listTasks          List all task labels in description.py
          --load=<CHECKPOINT>  Load a model from the given <CHECKPOINT> and run it.
                               Run with --listCheckpoints flag for more details.
          --newSerialization   Use new capnproto serialization
          --tasks              Run the tasks with the given TASK LABELS in the order
                               they are given.  Either end of arg-list, or a
                               standalone dot ('.') arg or the next short or long
                               option name (-a or --blah) terminates the list. NOTE:
                               FAILS TO RECOGNIZE task label names with one or more
                               leading dashes. [default: run all of the tasks in
                               description.py]
          --testMode           Reduce iteration count for testing
          --noCheckpoint       Don't checkpoint the model after running each task.

  :param model: (:class:`~nupic.frameworks.opf.model.Model`) For testing, may
      pass in an existing OPF Model to use instead of creating a new one.

  :returns: (:class:`~nupic.frameworks.opf.model.Model`)
    reference to OPF Model instance that was constructed (this
    is provided to aid with debugging) or None, if none was
    created.
  """
  # Parse command-line options
  opt = _parseCommandLineOptions(args)

  #print "runExperiment: Parsed Command Options: ", opt

  model = _runExperimentImpl(opt, model)

  return model



def initExperimentPrng():
  """Initialize PRNGs that may be used by other modules in the experiment stack.

  .. note:: User may call this function to initialize PRNGs that are used by the
     experiment stack before calling runExperiment(), unless user has its own
     own logic for initializing these PRNGs.
  """
  seed = 42
  random.seed(seed)
  numpy.random.seed(seed)



ParseCommandLineOptionsResult = namedtuple('ParseCommandLineOptionsResult',
                                           ('experimentDir', 'privateOptions'))
"""_parseCommandLineOptions() return value type

Args:
  experimentDir: path of experiment directory that contains description.py
  privateOptions: dictionary of options of consumption only by this script;
      the schema is described by g_parsedPrivateCommandLineOptionsSchema
"""



def _parseCommandLineOptions(args):
  """Parse command line options

  Args:
    args: command line arguments (not including sys.argv[0])
  Returns:
    namedtuple ParseCommandLineOptionsResult
  """
  usageStr = (
    "%prog [options] descriptionPyDirectory\n"
    "This script runs a single OPF Model described by description.py "
    "located in the given directory."
    )

  parser = optparse.OptionParser(usage=usageStr)

  parser.add_option("-c",
                    help="Create a model and save it under the given "
                         "<CHECKPOINT> name, but don't run it",
                    dest="createCheckpointName",
                    action="store", type="string", default="",
                    metavar="<CHECKPOINT>")

  parser.add_option("--listCheckpoints",
                    help="List all available checkpoints",
                    dest="listAvailableCheckpoints",
                    action="store_true", default=False)

  parser.add_option("--listTasks",
                    help="List all task labels in description.py",
                    dest="listTasks",
                    action="store_true", default=False)

  parser.add_option("--load",
                    help="Load a model from the given <CHECKPOINT> and run it. "
                         "Run with --listCheckpoints flag for more details. ",
                    dest="runCheckpointName",
                    action="store", type="string", default="",
                    metavar="<CHECKPOINT>")

  parser.add_option("--newSerialization",
                    help="Use new capnproto serialization",
                    dest="newSerialization",
                    action="store_true", default=False)

  #parser.add_option("--reuseDatasets",
  #                  help="Keep existing generated/aggregated datasets",
  #                  dest="reuseDatasets", action="store_true",
  #                  default=False)

  parser.add_option("--tasks",
                    help="Run the tasks with the given TASK LABELS "
                         "in the order they are given.  Either end of "
                         "arg-list, or a standalone dot ('.') arg or "
                         "the next short or long option name (-a or "
                         "--blah) terminates the list. NOTE: FAILS "
                         "TO RECOGNIZE task label names with one or more "
                         "leading dashes. [default: run all of the tasks in "
                         "description.py]",
                    dest="taskLabels", default=[],
                    action="callback", callback=reapVarArgsCallback,
                    metavar="TASK_LABELS")

  parser.add_option("--testMode",
                    help="Reduce iteration count for testing",
                    dest="testMode", action="store_true",
                    default=False)

  parser.add_option("--noCheckpoint",
                    help="Don't checkpoint the model after running each task.",
                    dest="checkpointModel", action="store_false",
                    default=True)

  options, experiments = parser.parse_args(args)

  # Validate args
  mutuallyExclusiveOptionCount = sum([bool(options.createCheckpointName),
                                      options.listAvailableCheckpoints,
                                      options.listTasks,
                                      bool(options.runCheckpointName)])
  if mutuallyExclusiveOptionCount > 1:
    _reportCommandLineUsageErrorAndExit(
        parser,
        "Options: -c, --listCheckpoints, --listTasks, and --load are "
        "mutually exclusive. Please select only one")

  mutuallyExclusiveOptionCount = sum([bool(not options.checkpointModel),
                                      bool(options.createCheckpointName)])
  if mutuallyExclusiveOptionCount > 1:
    _reportCommandLineUsageErrorAndExit(
        parser,
        "Options: -c and --noCheckpoint are "
        "mutually exclusive. Please select only one")

  if len(experiments) != 1:
    _reportCommandLineUsageErrorAndExit(
        parser,
        "Exactly ONE experiment must be specified, but got %s (%s)" % (
            len(experiments), experiments))

  # Done with parser
  parser.destroy()

  # Prepare results

  # Directory path of the experiment (that contain description.py)
  experimentDir = os.path.abspath(experiments[0])

  # RunExperiment.py's private options (g_parsedPrivateCommandLineOptionsSchema)
  privateOptions = dict()
  privateOptions['createCheckpointName'] = options.createCheckpointName
  privateOptions['listAvailableCheckpoints'] = options.listAvailableCheckpoints
  privateOptions['listTasks'] = options.listTasks
  privateOptions['runCheckpointName'] = options.runCheckpointName
  privateOptions['newSerialization'] = options.newSerialization
  privateOptions['testMode'] = options.testMode
  #privateOptions['reuseDatasets']  = options.reuseDatasets
  privateOptions['taskLabels'] = options.taskLabels
  privateOptions['checkpointModel'] = options.checkpointModel

  result = ParseCommandLineOptionsResult(experimentDir=experimentDir,
                                         privateOptions=privateOptions)
  return result



def reapVarArgsCallback(option, optStr, value, parser):
  """Used as optparse callback for reaping a variable number of option args.
  The option may be specified multiple times, and all the args associated with
  that option name will be accumulated in the order that they are encountered
  """
  newValues = []

  # Reap the args, taking care to stop before the next option or '.'
  gotDot = False
  for arg in parser.rargs:
    # Stop on --longname options
    if arg.startswith("--") and len(arg) > 2:
      break

    # Stop on -b options
    if arg.startswith("-") and len(arg) > 1:
      break

    if arg == ".":
      gotDot = True
      break

    newValues.append(arg)

  if not newValues:
    raise optparse.OptionValueError(
      ("Empty arg list for option %r expecting one or more args "
       "(remaining tokens: %r)") % (optStr, parser.rargs))

  del parser.rargs[:len(newValues) + int(gotDot)]

  # Retrieve the existing arg accumulator, if any
  value = getattr(parser.values, option.dest, [])
  #print "Previous value: %r" % value
  if value is None:
    value = []

  # Append the new args to the existing ones and save to the parser
  value.extend(newValues)
  setattr(parser.values, option.dest, value)



def _reportCommandLineUsageErrorAndExit(parser, message):
  """Report usage error and exit program with error indication."""
  print parser.get_usage()
  print message
  sys.exit(1)



def _runExperimentImpl(options, model=None):
  """Creates and runs the experiment

  Args:
    options: namedtuple ParseCommandLineOptionsResult
    model: For testing: may pass in an existing OPF Model instance
        to use instead of creating a new one.

  Returns: reference to OPFExperiment instance that was constructed (this
      is provided to aid with debugging) or None, if none was
      created.
  """
  json_helpers.validate(options.privateOptions,
                        schemaDict=g_parsedPrivateCommandLineOptionsSchema)

  # Load the experiment's description.py module
  experimentDir = options.experimentDir
  descriptionPyModule = helpers.loadExperimentDescriptionScriptFromDir(
      experimentDir)
  expIface = helpers.getExperimentDescriptionInterfaceFromModule(
      descriptionPyModule)

  # Handle "list checkpoints" request
  if options.privateOptions['listAvailableCheckpoints']:
    _printAvailableCheckpoints(experimentDir)
    return None

  # Load experiment tasks
  experimentTasks = expIface.getModelControl().get('tasks', [])

  # If the tasks list is empty, and this is a nupic environment description
  # file being run from the OPF, convert it to a simple OPF description file.
  if (len(experimentTasks) == 0 and
      expIface.getModelControl()['environment'] == OpfEnvironment.Nupic):
    expIface.convertNupicEnvToOPF()
    experimentTasks = expIface.getModelControl().get('tasks', [])

  # Ensures all the source locations are either absolute paths or relative to
  # the nupic.datafiles package_data location.
  expIface.normalizeStreamSources()

  # Extract option
  newSerialization = options.privateOptions['newSerialization']

  # Handle listTasks
  if options.privateOptions['listTasks']:
    print "Available tasks:"

    for label in [t['taskLabel'] for t in experimentTasks]:
      print "\t", label

    return None

  # Construct the experiment instance
  if options.privateOptions['runCheckpointName']:

    assert model is None

    checkpointName = options.privateOptions['runCheckpointName']

    model = ModelFactory.loadFromCheckpoint(
          savedModelDir=_getModelCheckpointDir(experimentDir, checkpointName),
          newSerialization=newSerialization)

  elif model is not None:
    print "Skipping creation of OPFExperiment instance: caller provided his own"
  else:
    modelDescription = expIface.getModelDescription()
    model = ModelFactory.create(modelDescription)

  # Handle "create model" request
  if options.privateOptions['createCheckpointName']:
    checkpointName = options.privateOptions['createCheckpointName']
    _saveModel(model=model,
               experimentDir=experimentDir,
               checkpointLabel=checkpointName,
               newSerialization=newSerialization)

    return model

  # Build the task list

  # Default task execution index list is in the natural list order of the tasks
  taskIndexList = range(len(experimentTasks))

  customTaskExecutionLabelsList = options.privateOptions['taskLabels']
  if customTaskExecutionLabelsList:
    taskLabelsList = [t['taskLabel'] for t in experimentTasks]
    taskLabelsSet = set(taskLabelsList)

    customTaskExecutionLabelsSet = set(customTaskExecutionLabelsList)

    assert customTaskExecutionLabelsSet.issubset(taskLabelsSet), \
           ("Some custom-provided task execution labels don't correspond "
            "to actual task labels: mismatched labels: %r; actual task "
            "labels: %r.") % (customTaskExecutionLabelsSet - taskLabelsSet,
                              customTaskExecutionLabelsList)

    taskIndexList = [taskLabelsList.index(label) for label in
                     customTaskExecutionLabelsList]

    print "#### Executing custom task list: %r" % [taskLabelsList[i] for
                                                   i in taskIndexList]

  # Run all experiment tasks
  for taskIndex in taskIndexList:

    task = experimentTasks[taskIndex]

    # Create a task runner and run it!
    taskRunner = _TaskRunner(model=model,
                             task=task,
                             cmdOptions=options)
    taskRunner.run()
    del taskRunner

    if options.privateOptions['checkpointModel']:
      _saveModel(model=model,
                 experimentDir=experimentDir,
                 checkpointLabel=task['taskLabel'],
                 newSerialization=newSerialization)

  return model



def _saveModel(model, experimentDir, checkpointLabel, newSerialization=False):
  """Save model"""
  checkpointDir = _getModelCheckpointDir(experimentDir, checkpointLabel)
  if newSerialization:
    model.writeToCheckpoint(checkpointDir)
  else:
    model.save(saveModelDir=checkpointDir)



def _getModelCheckpointDir(experimentDir, checkpointLabel):
  """Creates directory for serialization of the model

  checkpointLabel:
      Checkpoint label (string)

  Returns:
    absolute path to the serialization directory
  """
  checkpointDir = os.path.join(getCheckpointParentDir(experimentDir),
                               checkpointLabel + g_defaultCheckpointExtension)
  checkpointDir = os.path.abspath(checkpointDir)

  return checkpointDir



def getCheckpointParentDir(experimentDir):
  """Get checkpoint parent dir.

  Returns: absolute path to the base serialization directory within which
      model checkpoints for this experiment are created
  """
  baseDir = os.path.join(experimentDir, "savedmodels")
  baseDir = os.path.abspath(baseDir)

  return baseDir



def _checkpointLabelFromCheckpointDir(checkpointDir):
  """Returns a checkpoint label string for the given model checkpoint directory

  checkpointDir: relative or absolute model checkpoint directory path
  """
  assert checkpointDir.endswith(g_defaultCheckpointExtension)

  lastSegment = os.path.split(checkpointDir)[1]

  checkpointLabel = lastSegment[0:-len(g_defaultCheckpointExtension)]

  return checkpointLabel



def _isCheckpointDir(checkpointDir):
  """Return true iff checkpointDir appears to be a checkpoint directory."""
  lastSegment = os.path.split(checkpointDir)[1]
  if lastSegment[0] == '.':
    return False

  if not checkpointDir.endswith(g_defaultCheckpointExtension):
    return False

  if not os.path.isdir(checkpointDir):
    return False

  return True



def _printAvailableCheckpoints(experimentDir):
  """List available checkpoints for the specified experiment."""
  checkpointParentDir = getCheckpointParentDir(experimentDir)

  if not os.path.exists(checkpointParentDir):
    print "No available checkpoints."
    return

  checkpointDirs = [x for x in os.listdir(checkpointParentDir)
                    if _isCheckpointDir(os.path.join(checkpointParentDir, x))]
  if not checkpointDirs:
    print "No available checkpoints."
    return

  print "Available checkpoints:"
  checkpointList = [_checkpointLabelFromCheckpointDir(x)
                    for x in checkpointDirs]

  for checkpoint in sorted(checkpointList):
    print "\t", checkpoint

  print
  print "To start from a checkpoint:"
  print "  python run_opf_experiment.py experiment --load <CHECKPOINT>"
  print "For example, to start from the checkpoint \"MyCheckpoint\":"
  print "  python run_opf_experiment.py experiment --load MyCheckpoint"



class _TaskRunner(object):
  """This class is responsible for running a single experiment task on the
  given Model instance
  """


  __FILE_SCHEME = "file://"


  def __init__(self, model, task, cmdOptions):
    """ Constructor

    Args:
      model: The OPF Model instance against which to run the task
      task: A dictionary conforming to opfTaskSchema.json
      cmdOptions: ParseCommandLineOptionsResult namedtuple
    """
    validateOpfJsonValue(task, "opfTaskSchema.json")

    # Set up our logger
    self.__logger = logging.getLogger(".".join(
      ['com.numenta', self.__class__.__module__, self.__class__.__name__]))
    #self.__logger.setLevel(logging.DEBUG)

    self.__logger.debug(("Instantiated %s(" + \
                      "model=%r, " + \
                      "task=%r, " + \
                      "cmdOptions=%r)") % \
                        (self.__class__.__name__,
                         model,
                         task,
                         cmdOptions))

    # Generate a new dataset from streamDef and create the dataset reader
    streamDef = task['dataset']
    datasetReader = opf_basic_environment.BasicDatasetReader(streamDef)

    self.__model = model
    self.__datasetReader = datasetReader
    self.__task = task
    self.__cmdOptions = cmdOptions


    self.__predictionLogger = opf_basic_environment.BasicPredictionLogger(
      fields=model.getFieldInfo(),
      experimentDir=cmdOptions.experimentDir,
      label=task['taskLabel'],
      inferenceType=self.__model.getInferenceType())

    taskControl = task['taskControl']

    # Create Task Driver
    self.__taskDriver = OPFTaskDriver(
      taskControl=taskControl,
      model=model)

    loggedMetricPatterns = taskControl.get('loggedMetrics', None)
    loggedMetricLabels = matchPatterns(loggedMetricPatterns,
                                       self.__taskDriver.getMetricLabels())

    self.__predictionLogger.setLoggedMetrics(loggedMetricLabels)

    # Create a prediction metrics logger
    self.__metricsLogger = opf_basic_environment.BasicPredictionMetricsLogger(
      experimentDir=cmdOptions.experimentDir,
      label=task['taskLabel'])


  def __del__(self):
    """Destructor"""
    #print "IN %s.%r destructor" % (type(self), self)


  def run(self):
    """Runs a single experiment task"""
    self.__logger.debug("run(): Starting task <%s>", self.__task['taskLabel'])

    # Set up the task

    # Create our main loop-control iterator
    if self.__cmdOptions.privateOptions['testMode']:
      numIters = 10
    else:
      numIters = self.__task['iterationCount']

    if numIters >= 0:
      iterTracker = iter(xrange(numIters))
    else:
      iterTracker = iter(itertools.count())

    # Initialize periodic activities
    periodic = PeriodicActivityMgr(
      requestedActivities=self._createPeriodicActivities())

    # Reset sequence states in the model, so it starts looking for a new
    # sequence
    # TODO: should this be done in OPFTaskDriver.setup(), instead?  Is it always
    #       desired in Nupic?
    self.__model.resetSequenceStates()

    # Have Task Driver perform its initial setup activities, including setup
    # callbacks
    self.__taskDriver.setup()

    # Run it!
    while True:
      # Check controlling iterator first
      try:
        next(iterTracker)
      except StopIteration:
        break

      # Read next input record
      try:
        inputRecord = self.__datasetReader.next()
      except StopIteration:
        break

      # Process input record
      result = self.__taskDriver.handleInputRecord(inputRecord=inputRecord)

      if InferenceElement.encodings in result.inferences:
        result.inferences.pop(InferenceElement.encodings)
      self.__predictionLogger.writeRecord(result)

      # Run periodic activities
      periodic.tick()

    # Dump the experiment metrics at the end of the task
    self._getAndEmitExperimentMetrics(final=True)

    # Have Task Driver perform its final activities
    self.__taskDriver.finalize()

    # Reset sequence states in the model, so it starts looking for a new
    # sequence
    # TODO: should this be done in OPFTaskDriver.setup(), instead?  Is it always
    #       desired in Nupic?
    self.__model.resetSequenceStates()


  def _createPeriodicActivities(self):
    """Creates and returns a list of activites for this TaskRunner instance

    Returns: a list of PeriodicActivityRequest elements
    """
    # Initialize periodic activities
    periodicActivities = []

    # Metrics reporting
    class MetricsReportCb(object):
      def __init__(self, taskRunner):
        self.__taskRunner = taskRunner
        return

      def __call__(self):
        self.__taskRunner._getAndEmitExperimentMetrics()

    reportMetrics = PeriodicActivityRequest(
      repeating=True,
      period=1000,
      cb=MetricsReportCb(self))

    periodicActivities.append(reportMetrics)

    # Iteration progress
    class IterationProgressCb(object):
      PROGRESS_UPDATE_PERIOD_TICKS = 1000

      def __init__(self, taskLabel, requestedIterationCount, logger):
        self.__taskLabel = taskLabel
        self.__requestedIterationCount = requestedIterationCount
        self.__logger = logger

        self.__numIterationsSoFar = 0

      def __call__(self):
        self.__numIterationsSoFar += self.PROGRESS_UPDATE_PERIOD_TICKS
        self.__logger.debug("%s: ITERATION PROGRESS: %s of %s" % (
                              self.__taskLabel,
                              self.__numIterationsSoFar,
                              self.__requestedIterationCount))

    iterationProgressCb = IterationProgressCb(
      taskLabel=self.__task['taskLabel'],
      requestedIterationCount=self.__task['iterationCount'],
      logger=self.__logger)
    iterationProgressReporter = PeriodicActivityRequest(
      repeating=True,
      period=IterationProgressCb.PROGRESS_UPDATE_PERIOD_TICKS,
      cb=iterationProgressCb)

    periodicActivities.append(iterationProgressReporter)

    return periodicActivities


  def _getAndEmitExperimentMetrics(self, final=False):
    # Get metrics
    metrics = self.__taskDriver.getMetrics()

    # Emit metrics
    if metrics is not None:
      if final:
        self.__metricsLogger.emitFinalMetrics(metrics)
      else:
        self.__metricsLogger.emitPeriodicMetrics(metrics)



PeriodicActivityRequest = namedtuple("PeriodicActivityRequest",
                                     ("repeating", "period", "cb"))
"""Passed as parameter to PeriodicActivityMgr

repeating: True if the activity is a repeating activite, False if one-shot
period: period of activity's execution (number of "ticks")
cb: a callable to call upon expiration of period; will be called
    as cb()
"""



class PeriodicActivityMgr(object):


  Activity = namedtuple("Activity",
                        ("repeating", "period", "cb", "iteratorHolder"))
  """Activity

  iteratorHolder: a list holding one iterator; we use a list so that we can
      replace the iterator for repeating activities (a tuple would not
      allow it if the field was an imutable value)
  """


  def __init__(self, requestedActivities):
    """
    requestedActivities: a sequence of PeriodicActivityRequest elements
    """
    self.__activities = []
    for req in requestedActivities:
      act =   self.Activity(repeating=req.repeating,
                            period=req.period,
                            cb=req.cb,
                            iteratorHolder=[iter(xrange(req.period-1))])
      self.__activities.append(act)


  def tick(self):
    """Activity tick handler; services all activities

    Returns:
      True if controlling iterator says it's okay to keep going;
      False to stop
    """
    # Run activities whose time has come
    for act in self.__activities:
      if not act.iteratorHolder[0]:
        continue

      try:
        next(act.iteratorHolder[0])
      except StopIteration:
        act.cb()
        if act.repeating:
          act.iteratorHolder[0] = iter(xrange(act.period-1))
        else:
          act.iteratorHolder[0] = None

    return True



def main():
  """ Module-level entry point.  Run according to options in sys.argv

  Usage: python -m python -m nupic.frameworks.opf.experiment_runner

  """
  initLogging(verbose=True)

  # Initialize pseudo-random number generators (PRNGs)
  #
  # This will fix the seed that is used by numpy when generating 'random'
  # numbers. This allows for repeatability across experiments.
  initExperimentPrng()

  # Run it!
  runExperiment(sys.argv[1:])



if __name__ == "__main__":
  main()

