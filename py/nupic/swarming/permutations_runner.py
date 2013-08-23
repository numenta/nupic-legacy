# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
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

"""This script is the command-line interface for running swarms.
"""

import collections
import csv
from datetime import datetime, timedelta
import json
import optparse
import os
import cPickle as pickle
import pprint
import shutil
import signal
import sys
import time
import subprocess
import tempfile
import uuid

from nupic.support import object_json as json
import nupic.database.ClientJobsDAO as cjdao
from nupic.swarming import HypersearchWorker
from nupic.swarming.HypersearchV2 import HypersearchV2


gCurrentSearch = None

def termHandler(signal, frame):
  global gCurrentSearch
  try:
    jobrunner = gCurrentSearch
    jobID = jobrunner._HyperSearchRunner__searchJob.getJobID()
  except Exception as exc:
    print exc
  else:
    print "Canceling jobs due to receiving SIGTERM"
    cjdao.ClientJobsDAO.get().jobCancel(jobID)


class Verbosity(object):
  WARNING = 0
  INFO = 1
  DEBUG = 2


g_currentVerbosityLevel = 0


def _verbosityEnabled(verbosityLevel):
  return (verbosityLevel <= g_currentVerbosityLevel)


def _emit(verbosityLevel, info):
  if _verbosityEnabled(verbosityLevel):
    print info


def _escape(s):
  """Escape commas, tabs, newlines and dashes in a string

  Commas are encoded as tabs
  """
  assert isinstance(s, str), \
        "expected %s but got %s; value=%s" % (type(str), type(s), s)
  s = s.replace('\\', '\\\\')
  s = s.replace('\n', '\\n')
  s = s.replace('\t', '\\t')
  s = s.replace(',', '\t')
  return s


def _engineServicesRunning():
  """ Return true if the engine services are running 
  """
  process = subprocess.Popen(["ps", "aux"], stdout=subprocess.PIPE)
  
  stdout = process.communicate()[0]
  result = process.returncode
  if result != 0:
    raise RuntimeError("Unable to check for running client job manager")
  
  # See if the CJM is running
  running = False
  for line in stdout.split("\n"):
    if "python" in line and "clientjobmanager.client_job_manager" in line:
      running = True
      break

  return running

  

def main():
  """Runs hypersearch with command-line args in sys.argv (see
  runPermutations() for arg definitions)

  Parameters:
  ----------------------------------------------------------------------
  retval:         for the actions 'run', 'pickup', and 'dryRun', returns the
                  Hypersearch job ID (in ClinetJobs table); otherwise returns
                  None
  """
  return runPermutations(sys.argv[1:])



def runPermutations(args):
  """
  The main function of the RunPermutations utility.
  This utility will automatically generate and run multiple prediction framework
  experiments that are permutations of a base experiment via the Grok engine.
  For example, if you have an experiment that you want to test with 3 possible
  values of variable A and 2 possible values of variable B, this utility will
  automatically generate the experiment directories and description files for
  each of the 6 different experiments.

  Here is an example permutations file which is read by this script below. The
  permutations file must be in the same directory as the description.py for the
  base experiment that you want to permute. It contains a permutations dict, an
  optional list of the result items to report on for each experiment, and an
  optional result item to optimize for.

  When an 'optimize' entry is provided, this tool will attempt to prioritize the
  order in which the various permutations are run in order to improve the odds
  of running the best permutations sooner. It does this by watching the results
  for various parameter values and putting parameter values that give generally
  better results at the head of the queue.

  In addition, when the optimize key is provided, we periodically update the UI
  with the best results obtained so far on that metric.

  ---------------------------------------------------------------------------
  permutations = dict(
                  iterationCount = [1000, 5000],
                  coincCount = [50, 100],
                  trainTP = [False],
                  )

  report = ['.*reconstructErrAvg',
            '.*inputPredScore.*',
            ]

  optimize = 'postProc_gym1_baseline:inputPredScore'

  Parameters:
  ----------------------------------------------------------------------
  args:           Command-line args; the equivalent of sys.argv[1:]
  retval:         for the actions 'run', 'pickup', and 'dryRun', returns the
                  Hypersearch job ID (in ClinetJobs table); otherwise returns
                  None
  """
  global g_currentVerbosityLevel
  
  # First, see if the engine services are running because this impacts what
  #  our default options are
  engineRunning = _engineServicesRunning()

  helpString = (
      "\n\n%prog [options] permutationsScript\n"
      "%prog [options] expDescription.json\n\n"
      "This script runs permutations of an experiment via Grok engine, as "
      "defined in a\npermutations.py script or an expGenerator experiment "
      "description json file.\nIn the expDescription.json form, the json file "
      "MUST have the file extension\n'.json' and MUST conform to "
      "expGenerator/experimentDescriptionSchema.json.")

  parser = optparse.OptionParser(usage=helpString)

  parser.add_option(
    "--searchMethod", dest="searchMethod", default="v2",
    #choices=['ronomatic', 'pso', 'blended'],
    choices=['v2'],
    help="Which hypersearch optimization method to use. Possible choices are: "
         "'v2' (ronomatic was deprecated). "
         "'v2' builds up field combinations gradually, using PSO to optimize "
         "variables within each field combination. "
         "[default: %default].")

  #parser.add_option(
  #  "--stopOnErr", dest="stopOnErr", action="store_true", default=False,
  #  help="If any sub-experiment encounters a failure, immediately stop and "
  #       "cancel all remaining permutations [default: %default].")

  parser.add_option(
    "--replaceReport", dest="replaceReport", action="store_true", default=False,
    help="Replace existing csv report file if it exists. Default is to "
         "append to the existing file. [default: %default].")

  #parser.add_option(
  #  "--noreorder", dest="noreorder", action="store_true", default=False,
  #  help="Turn off the automatic experiment re-ordering which tries to run "
  #       "experiments with the potentially best results on the optimize "
  #       "metric first [default: %default].")

  parser.add_option(
    "--action", dest="action", default="run",
    choices=['run', 'pickup', 'report', 'dryRun'],
    help="Which action to perform. Possible actions are run, pickup, choices, "
         "report, list. "
         "run: run a new HyperSearch via Grok. "
         "pickup: pick up the latest run of a HyperSearch job. "
         "dryRun: run a single HypersearchWorker inline within the application "
         "process without the Grok infrastructure to flush out bugs in "
         "description and permutations scripts; defaults to "
         "maxPermutations=1: use --maxPermutations to change this; defaults to "
         "useStreams=yes: use --useStreams=no to override. "
         "report: just print results from the last or current run. "
         "[default: %default].")

  #parser.add_option(
  #  "-R", dest="runOptions", action="append", default=[],
  #  metavar="<RUNOPTION>",
  #  help="A <RUNOPTION> to pass on to the command that runs each experiment. "
  #       "Multiple <RUNOPTION>s may be specified. Example: -R--testMode "
  #       "-R-r [default: %default].")

  #parser.add_option(
  #  "--override", dest="override", action="append", default=[],
  #  help="Override the given variable in all experiments. This option "
  #  "will override any values found in either the base description file "
  #  "or the permutations script. "
  #  "If desired, multiple --override options can be specified.\n"
  #  " [default: %default].")

  parser.add_option(
    "--maxPermutations", dest="maxPermutations", default=None, type="int",
    help="Maximum number of models to search. Applies only to the 'run' and "
    "'dryRun' actions. [default: %default].")

  parser.add_option(
    "--exports", dest="exports", default=None, type="string",
    help="json dump of environment variable settings that should be applied"
    "for the job before running. [default: %default].")

  parser.add_option(
    "--useTerminators", dest="useTerminators", action='store_true',
    default=False, help="Use early model terminators in HyperSearch"
         "[default: %default].")

  parser.add_option(
      "--clusterDefault", dest="clusterDefault", action='store_true',
      default=False, help="Use default search values. Overwrites all search "
      "options [default: %default].")

  parser.add_option(
      "--maxWorkers", dest="maxWorkers", default=2, type="int",
      help="Maximum number of concurrent workers to launch. Applies only to "
      "the 'run' action. [default: %default].")

  parser.add_option(
    "-v", dest="verbosityCount", action="count", default=0,
    help="Increase verbosity of the output.  Specify multiple times for "
         "increased verbosity. e.g., -vv is more verbose than -v.")

  parser.add_option(
    "--timeout", dest="timeout", default=None,type="int",
     help="Time out for this search in minutes"
         "[default: %default].")

  parser.add_option(
    "--useEngine", dest="useEngine", default="yes" if engineRunning else "no",
    choices=["yes", "no"], help="If set to 'yes', the grok engine will be used "
    "and the swarm can run across multiple machines. If set to 'no', then "
    "the engine is not required and swarming will run multiple processes on the "
    "local machine only. [default: %default].")

  parser.add_option(
    "--useStreams", dest="useStreams", default="yes" if engineRunning else "no",
    help="If 'yes', use Hbase streams for input/output. If 'no', use files. "
         "[default: %default].")

  parser.add_option(
    "--genTopNDescriptions", dest="genTopNDescriptions", default=1, type="int",
    help="Generate description files for the top N models. Each one will be"
         " placed into it's own subdirectory under the base description file."
         "[default: %default].")

  (options, positionalArgs) = parser.parse_args(args)

  # Process the options

  g_currentVerbosityLevel = options.verbosityCount

  # Get the permutations script's filepath
  if len(positionalArgs) != 1:
    parser.error("You must supply the name of exactly one permutations script "
                 "or JSON description file.")

  expDescJsonPath = None
  permutationsScriptPath = None

  fileArgPath = os.path.expanduser(positionalArgs[0])
  fileArgPath = os.path.expandvars(fileArgPath)
  fileArgPath = os.path.abspath(fileArgPath)

  permWorkDir = os.path.dirname(fileArgPath)

  outputLabel = os.path.splitext(os.path.basename(fileArgPath))[0]

  basename = os.path.basename(fileArgPath)
  fileExtension = os.path.splitext(basename)[1]

  # Setup interrupt handling
  signal.signal(signal.SIGTERM, termHandler)
  signal.signal(signal.SIGINT, termHandler)

  if fileExtension == '.json':
    expDescJsonPath = fileArgPath
  else:
    # Assume it's a permutations python script
    permutationsScriptPath = fileArgPath

  # Set up cluster default values if required
  if(options.clusterDefault):
    options.useTerminators = None
    options.searchMethod = "v2"

  grokOptions = dict(
    action = options.action,

    # NOTE: exactly one of expDescJsonPath or permutationsScriptPath
    #       MUST be specfied; the other MUST be None.
    expDescJsonPath = expDescJsonPath,
    permutationsScriptPath = permutationsScriptPath,

    # Path for storing hypersearch output (based on given file path arg)
    permWorkDir = permWorkDir,

    # Label derived from the given file path arg that may be incorporated into
    # generated output file names
    outputLabel = outputLabel,

    searchMethod = options.searchMethod,
    #stopOnError = options.stopOnErr,
    #autoExperimentReorder = not options.noreorder,
    #experimentRunOptions = options.runOptions,
    #variableOverrides = options.override,
    timeout=options.timeout,
    exports = options.exports,
    useTerminators = options.useTerminators,
    maxNumWorkers = options.maxWorkers,
    maxPermutations = options.maxPermutations,
    useStreams = options.useStreams == "yes",
    genTopNDescriptions = options.genTopNDescriptions,
    useEngine = options.useEngine == "yes",
  )

  # Print Grok HyperSearch results from the current or last run
  if options.action == 'report':
    _HyperSearchRunner.generateReport(
      options=grokOptions,
      replaceReport=options.replaceReport,
      hyperSearchJob=None,
      metricsKeys=None)

    return None

  # Run HyperSearch via Grok
  elif options.action in ('run', 'dryRun', 'pickup'):
    # Run HyperSearch
    startTime = time.time()

    search = _HyperSearchRunner(grokOptions)
    
    # Save in global for the signal handler. 
    global gCurrentSearch
    gCurrentSearch = search

    if options.action in ('run', 'dryRun'):
      search.runNewSearch()
    else:
      search.pickupSearch()

    # Generate reports

    # Print results and generate report csv file
    _HyperSearchRunner.generateReport(
      options=grokOptions,
      replaceReport=options.replaceReport,
      hyperSearchJob=search.peekSearchJob(),
      metricsKeys=search.getDiscoveredMetricsKeys())

    secs = time.time() - startTime
    hours = int(secs) / (60*60)
    secs -= hours * (60*60)
    minutes = int(secs) / 60
    secs -= minutes * 60
    print "Elapsed time (h:mm:ss): %d:%02d:%02d" % (hours, minutes, int(secs))

    jobID = search.peekSearchJob().getJobID()

    print "Hypersearch ClientJobs job ID: ", jobID

    #if _grokHyperSearchHasErrors(search.peekSearchJob()):
    #  # TODO: if job or some models failed, emit error messages
    #  sys.exit(1)
    #else:
    #  sys.exit(0)

  else:
    raise Exception("Unhandled action: %s" % options.action)

  return jobID



def setUpExports(exports):
  ret = ""
  if  exports is None:
    return ret
  exportDict = json.loads(exports)
  for key in exportDict.keys():
    ret+= "export %s=%s;" % (str(key), str(exportDict[key]))
  return ret



def _clientJobsDB():
  """
  Returns: The shared cjdao.ClientJobsDAO instance
  """
  return cjdao.ClientJobsDAO.get()



def _grokHyperSearchHasErrors(hyperSearchJob):
  """Check whether any experiments failed in our latest hypersearch

  Parameters:
    hyperSearchJob: _HyperSearchJob instance; if None, will get it from saved
                    jobID, if any

  Returns: False if all models succeeded, True if one or more had errors
  """
  # TODO flesh me out

  # Get search ID for our latest hypersearch

  # Query Grok for experiment failures in the given search

  return False



class _HyperSearchRunner(object):
  """Manages one instance of HyperSearch"""


  def __init__(self, options):
    """
    Parameters:
    ----------------------------------------------------------------------
    options:        GrokRunPermutations options dict
    retval:         nothing
    """

    self.__cjDAO = _clientJobsDB()

    self._options = options

    # _HyperSearchJob instance set up by runNewSearch() and pickupSearch()
    self.__searchJob = None

    self.__foundMetrcsKeySet = set()
    
    # If we are instead relying on the engine to launch workers for us, this 
    # will stay as None, otherwise it becomes an array of subprocess Popen 
    # instances. 
    self._workers = None

    return


  def runNewSearch(self):
    """Start a new hypersearch job and monitor it to completion
    Parameters:
    ----------------------------------------------------------------------
    retval:         nothing
    """
    self.__searchJob = self.__startSearch()

    self.monitorSearchJob()


  def pickupSearch(self):
    """Pick up the latest search from a saved jobID and monitor it to completion
    Parameters:
    ----------------------------------------------------------------------
    retval:         nothing
    """
    self.__searchJob = self.loadSavedHyperSearchJob(
      permWorkDir=self._options['permWorkDir'],
      outputLabel=self._options['outputLabel'])


    self.monitorSearchJob()


  def monitorSearchJob(self):
    """
    Parameters:
    ----------------------------------------------------------------------
    retval:         nothing
    """
    assert self.__searchJob is not None

    jobID = self.__searchJob.getJobID()

    startTime = time.time()
    lastUpdateTime = datetime.now()

    # Monitor HyperSearch and report progress

    # NOTE: may be -1 if it can't be determined
    expectedNumModels = self.__searchJob.getExpectedNumModels(
                                searchMethod = self._options['searchMethod'])

    lastNumFinished = 0
    finishedModelIDs = set()

    finishedModelStats = _ModelStats()

    # Keep track of the worker state, results, and milestones from the job
    # record
    lastWorkerState = None
    lastJobResults = None
    lastModelMilestones = None
    lastEngStatus = None

    hyperSearchFinished = False
    while not hyperSearchFinished:
      jobInfo = self.__searchJob.getJobStatus(self._workers)

      # Check for job completion BEFORE processing models; NOTE: this permits us
      # to process any models that we may not have accounted for in the
      # previous iteration.
      hyperSearchFinished = jobInfo.isFinished()

      # Look for newly completed models, and process them
      modelIDs = self.__searchJob.queryModelIDs()
      _emit(Verbosity.DEBUG,
            "Current number of models is %d (%d of them completed)" % (
              len(modelIDs), len(finishedModelIDs)))

      if len(modelIDs) > 0:
        # Build a list of modelIDs to check for completion
        checkModelIDs = []
        for modelID in modelIDs:
          if modelID not in finishedModelIDs:
            checkModelIDs.append(modelID)

        del modelIDs

        # Process newly completed models
        if checkModelIDs:
          _emit(Verbosity.DEBUG,
                "Checking %d models..." % (len(checkModelIDs)))
          errorCompletionMsg = None
          for (i, modelInfo) in enumerate(_iterModels(checkModelIDs)):
            _emit(Verbosity.DEBUG,
                  "[%s] Checking completion: %s" % (i, modelInfo))
            if modelInfo.isFinished():
              finishedModelIDs.add(modelInfo.getModelID())

              finishedModelStats.update(modelInfo)

              if (modelInfo.getCompletionReason().isError() and
                  not errorCompletionMsg):
                errorCompletionMsg = modelInfo.getCompletionMsg()

              # Update the set of all encountered metrics keys (we will use
              # these to print column names in reports.csv)
              metrics = modelInfo.getReportMetrics()
              self.__foundMetrcsKeySet.update(metrics.keys())

        numFinished = len(finishedModelIDs)

        # Print current completion stats
        if numFinished != lastNumFinished:
          lastNumFinished = numFinished

          if expectedNumModels is None:
            expModelsStr = ""
          else:
            expModelsStr = "of %s" % (expectedNumModels)

          stats = finishedModelStats
          print ("<jobID: %s> %s %s models finished [success: %s; %s: %s; %s: "
                 "%s; %s: %s; %s: %s; %s: %s; %s: %s]" % (
                     jobID,
                     numFinished,
                     expModelsStr,
                     #stats.numCompletedSuccess,
                     (stats.numCompletedEOF+stats.numCompletedStopped),
                     "EOF" if stats.numCompletedEOF else "eof",
                     stats.numCompletedEOF,
                     "STOPPED" if stats.numCompletedStopped else "stopped",
                     stats.numCompletedStopped,
                     "KILLED" if stats.numCompletedKilled else "killed",
                     stats.numCompletedKilled,
                     "ERROR" if stats.numCompletedError else "error",
                     stats.numCompletedError,
                     "ORPHANED" if stats.numCompletedError else "orphaned",
                     stats.numCompletedOrphaned,
                     "UNKNOWN" if stats.numCompletedOther else "unknown",
                     stats.numCompletedOther))

          # Print the first error message from the latest batch of completed
          # models
          if errorCompletionMsg:
            print "ERROR MESSAGE: %s" % errorCompletionMsg

        # Print the new worker state, if it changed
        workerState = jobInfo.getWorkerState()
        if workerState != lastWorkerState:
          print "##>> UPDATED WORKER STATE: \n%s" % (pprint.pformat(workerState,
                                                           indent=4))
          lastWorkerState = workerState

        # Print the new job results, if it changed
        jobResults = jobInfo.getResults()
        if jobResults != lastJobResults:
          print "####>> UPDATED JOB RESULTS: \n%s (elapsed time: %g secs)" \
              % (pprint.pformat(jobResults, indent=4), time.time()-startTime)
          lastJobResults = jobResults

        # Print the new model milestones if they changed
        modelMilestones = jobInfo.getModelMilestones()
        if modelMilestones != lastModelMilestones:
          print "##>> UPDATED MODEL MILESTONES: \n%s" % (
              pprint.pformat(modelMilestones, indent=4))
          lastModelMilestones = modelMilestones

        # Print the new engine status if it changed
        engStatus = jobInfo.getEngStatus()
        if engStatus != lastEngStatus:
          print "##>> UPDATED STATUS: \n%s" % (engStatus)
          lastEngStatus = engStatus

      # Sleep before next check
      if not hyperSearchFinished:
        if self._options['timeout'] != None:
          if ((datetime.now() - lastUpdateTime) >
              timedelta(minutes=self._options['timeout'])):
            print "Timeout reached, exiting"
            self.__cjDAO.jobCancel(jobID)
            sys.exit(1)
        time.sleep(1)

    # Tabulate results
    modelIDs = self.__searchJob.queryModelIDs()
    print "Evaluated %s models" % len(modelIDs)
    print "HyperSearch finished!"

    jobInfo = self.__searchJob.getJobStatus(self._workers)
    print "Worker completion message: %s" % (jobInfo.getWorkerCompletionMsg())


  def _launchWorkers(self, cmdLine, numWorkers):
    """ Launch worker processes to execute the given command line
    
    Parameters:
    -----------------------------------------------
    cmdLine: The command line for each worker
    numWorkers: number of workers to launch
    """

    self._workers = []    
    for i in range(numWorkers):
      args = ["bash", "-c", cmdLine]
      stdout = tempfile.TemporaryFile()
      stderr = tempfile.TemporaryFile()
      p = subprocess.Popen(args, bufsize=1, env=os.environ, shell=False,
                           stdin=None, stdout=stdout, stderr=stderr)
      self._workers.append(p)
      

  def __startSearch(self):
    """Starts HyperSearch in Grok or runs it inline for the 'dryRun' action

    Parameters:
    ----------------------------------------------------------------------
    retval:         the new _HyperSearchJob instance representing the
                    HyperSearch job
    """
    # This search uses a pre-existing permutations script
    params = _ClientJobUtils.makeSearchJobParamsDict(options=self._options,
                                                     forRunning=True)

    if self._options['action'] == 'dryRun':
      args = [sys.argv[0], '--params=%s' % (json.dumps(params))]

      print
      print "=================================================================="
      print "RUNNING PERMUTATIONS INLINE as 'DRY RUN'..."
      print "=================================================================="
      jobID = HypersearchWorker.main(args)

    else:
      cmdLine = setUpExports(self._options['exports'])
      # Begin the new search. The {JOBID} string is replaced by the actual
      # jobID returned from jobInsert.
      cmdLine += "$HYPERSEARCH"
      maxWorkers = self._options['maxNumWorkers']

      jobID = self.__cjDAO.jobInsert(
        client='GRP',
        cmdLine=cmdLine,
        params=json.dumps(params),
        minimumWorkers=1,
        maximumWorkers=maxWorkers,
        jobType=self.__cjDAO.JOB_TYPE_HS)

      # If running without the engine, startup the workers ourselves
      if not self._options["useEngine"]:
        cmdLine = "python -m nupic.swarming.HypersearchWorker" \
                   " --jobID=%d" % (jobID)
        self._launchWorkers(cmdLine, maxWorkers)
          
    searchJob = _HyperSearchJob(jobID)

    # Save search ID to file (this is used for report generation)
    self.__saveHyperSearchJobID(
      permWorkDir=self._options['permWorkDir'],
      outputLabel=self._options['outputLabel'],
      hyperSearchJob=searchJob)

    if self._options['action'] == 'dryRun':
      print "Successfully executed 'dry-run' hypersearch, jobID=%d" % (jobID)
    else:
      print "Successfully submitted new HyperSearch job, jobID=%d" % (jobID)
      _emit(Verbosity.DEBUG,
            "Each worker executing the command line: %s" % (cmdLine,))

    return searchJob


  def peekSearchJob(self):
    """Retrieves the runner's _HyperSearchJob instance; NOTE: only available
    after run().

    Parameters:
    ----------------------------------------------------------------------
    retval:         _HyperSearchJob instance or None
    """
    assert self.__searchJob is not None
    return self.__searchJob


  def getDiscoveredMetricsKeys(self):
    """Returns a tuple of all metrics keys discovered while running HyperSearch.

    NOTE: This is an optimization so that our client may
        use this info for generating the report csv file without having
        to pre-scan all modelInfos

    Parameters:
    ----------------------------------------------------------------------
    retval:         Tuple of metrics keys discovered while running
                    HyperSearch;
    """
    return tuple(self.__foundMetrcsKeySet)


  @classmethod
  def printModels(cls, options):
    """Prints a listing of experiments that would take place without
    actually executing them.

    Parameters:
    ----------------------------------------------------------------------
    options:        GrokRunPermutations options dict
    retval:         nothing
    """
    print "Generating experiment requests..."

    searchParams = _ClientJobUtils.makeSearchJobParamsDict(options=options)


  @classmethod
  def generateReport(cls,
                     options,
                     replaceReport,
                     hyperSearchJob,
                     metricsKeys):
    """Prints all available results in the given HyperSearch job and emits
    model information to the permutations report csv.

    The job may be completed or still in progress.

    Parameters:
    ----------------------------------------------------------------------
    options:        GrokRunPermutations options dict
    replaceReport:  True to replace existing report csv, if any; False to
                    append to existing report csv, if any
    hyperSearchJob: _HyperSearchJob instance; if None, will get it from saved
                    jobID, if any
    metricsKeys:    sequence of report metrics key names to include in report;
                    if None, will pre-scan all modelInfos to generate a complete
                    list of metrics key names.
    retval:         nothing
    """
    # Load _HyperSearchJob instance from storage, if not provided
    if hyperSearchJob is None:
      hyperSearchJob = cls.loadSavedHyperSearchJob(
          permWorkDir=options['permWorkDir'],
          outputLabel=options['outputLabel'])

    modelIDs = hyperSearchJob.queryModelIDs()
    bestModel = None

    # If metricsKeys was not provided, pre-scan modelInfos to create the list;
    # this is needed by _ReportCSVWriter
    # Also scan the parameters to generate a list of encoders and search
    # parameters
    metricstmp = set()
    searchVar = set()
    for modelInfo in _iterModels(modelIDs):
      if modelInfo.isFinished():
        vars = modelInfo.getParamLabels().keys()
        searchVar.update(vars)
        metrics = modelInfo.getReportMetrics()
        metricstmp.update(metrics.keys())
    if metricsKeys is None:
      metricsKeys = metricstmp
    # Create a csv report writer
    reportWriter = _ReportCSVWriter(hyperSearchJob=hyperSearchJob,
                                    metricsKeys=metricsKeys,
                                    searchVar=searchVar,
                                    outputDirAbsPath=options['permWorkDir'],
                                    outputLabel=options['outputLabel'],
                                    replaceReport=replaceReport)

    # Tallies of experiment dispositions
    modelStats = _ModelStats()
    #numCompletedOther = long(0)

    print "\nResults from all experiments:"
    print "----------------------------------------------------------------"

    # Get common optimization metric info from permutations script
    searchParams = hyperSearchJob.getParams()

    (optimizationMetricKey, maximizeMetric) = (
      _PermutationUtils.getOptimizationMetricInfo(searchParams))

    # Print metrics, while looking for the best model
    formatStr = None
    # NOTE: we may find additional metrics if HyperSearch is still running
    foundMetricsKeySet = set(metricsKeys)
    sortedMetricsKeys = []
   
    # pull out best Model from jobs table
    jobInfo = _clientJobsDB().jobInfo(hyperSearchJob.getJobID())
    try:
      results = json.loads(jobInfo.results)
    except Exception, e:
      print "json.loads(jobInfo.results) raised an exception.  " \
            "Here is some info to help with debugging:"
      print "jobInfo: ", jobInfo
      print "jobInfo.results: ", jobInfo.results
      print "EXCEPTION: ", e
      raise

    bestModelNum = results['bestModel']
    bestModelIterIndex = None

    # performance metrics for the entire job
    totalWallTime = 0
    totalRecords = 0

    # At the end, we will sort the models by their score on the optimization
    # metric
    scoreModelIDDescList = []
    for (i, modelInfo) in enumerate(_iterModels(modelIDs)):

      # Output model info to report csv
      reportWriter.emit(modelInfo)

      # Update job metrics
      totalRecords+=modelInfo.getNumRecords()
      format = "%Y-%m-%d %H:%M:%S"
      startTime = modelInfo.getStartTime()
      if modelInfo.isFinished():
        endTime = modelInfo.getEndTime()
        st = datetime.strptime(startTime, format)
        et = datetime.strptime(endTime, format)
        totalWallTime+=(et-st).seconds

      # Tabulate experiment dispositions
      modelStats.update(modelInfo)

      # For convenience
      expDesc = modelInfo.getModelDescription()
      reportMetrics = modelInfo.getReportMetrics()
      optimizationMetrics = modelInfo.getOptimizationMetrics()
      if modelInfo.getModelID() == bestModelNum:
        bestModel = modelInfo
        bestModelIterIndex=i
        bestMetric = optimizationMetrics.values()[0]

      # Keep track of the best-performing model
      if optimizationMetrics:
        assert len(optimizationMetrics) == 1, (
            "expected 1 opt key, but got %d (%s) in %s" % (
                len(optimizationMetrics), optimizationMetrics, modelInfo))

      # Append to our list of modelIDs and scores
      if modelInfo.getCompletionReason().isEOF():
        scoreModelIDDescList.append((optimizationMetrics.values()[0],
                                    modelInfo.getModelID(),
                                    modelInfo.getGeneratedDescriptionFile(),
                                    modelInfo.getParamLabels()))

      print "[%d] Experiment %s\n(%s):" % (i, modelInfo, expDesc)
      if (modelInfo.isFinished() and
          not (modelInfo.getCompletionReason().isStopped or
               modelInfo.getCompletionReason().isEOF())):
        print ">> COMPLETION MESSAGE: %s" % modelInfo.getCompletionMsg()

      if reportMetrics:
        # Update our metrics key set and format string
        foundMetricsKeySet.update(reportMetrics.iterkeys())
        if len(sortedMetricsKeys) != len(foundMetricsKeySet):
          sortedMetricsKeys = sorted(foundMetricsKeySet)

          maxKeyLen = max([len(k) for k in sortedMetricsKeys])
          formatStr = "  %%-%ds" % (maxKeyLen+2)

        # Print metrics
        for key in sortedMetricsKeys:
          if key in reportMetrics:
            if key == optimizationMetricKey:
              m = "%r (*)" % reportMetrics[key]
            else:
              m = "%r" % reportMetrics[key]
            print formatStr % (key+':'), m
        print

    # Summarize results
    print "--------------------------------------------------------------"
    if len(modelIDs) > 0:
      print "%d experiments total (%s).\n" % (
          len(modelIDs),
          ("all completed successfully"
           if (modelStats.numCompletedKilled + modelStats.numCompletedEOF) ==
               len(modelIDs)
           else "WARNING: %d models have not completed or there were errors" % (
               len(modelIDs) - (
                   modelStats.numCompletedKilled + modelStats.numCompletedEOF +
                   modelStats.numCompletedStopped))))

      if modelStats.numStatusOther > 0:
        print "ERROR: models with unexpected status: %d" % (
            modelStats.numStatusOther)

      print "WaitingToStart: %d" % modelStats.numStatusWaitingToStart
      print "Running: %d" % modelStats.numStatusRunning
      print "Completed: %d" % modelStats.numStatusCompleted
      if modelStats.numCompletedOther > 0:
        print "    ERROR: models with unexpected completion reason: %d" % (
            modelStats.numCompletedOther)
      print "    ran to EOF: %d" % modelStats.numCompletedEOF
      print "    ran to stop signal: %d" % modelStats.numCompletedStopped
      print "    were orphaned: %d" % modelStats.numCompletedOrphaned
      print "    killed off: %d" % modelStats.numCompletedKilled
      print "    failed: %d" % modelStats.numCompletedError

      assert modelStats.numStatusOther == 0, "numStatusOther=%s" % (
          modelStats.numStatusOther)
      assert modelStats.numCompletedOther == 0, "numCompletedOther=%s" % (
          modelStats.numCompletedOther)

    else:
      print "0 experiments total."

    # Print out the field contributions
    print
    global gCurrentSearch
    jobStatus = hyperSearchJob.getJobStatus(gCurrentSearch._workers)
    jobResults = jobStatus.getResults()
    if 'fieldContributions' in jobResults:
      print "Field Contributions:"
      pprint.pprint(jobResults['fieldContributions'], indent=4)
    else:
      print "Field contributions info not available"

    # Did we have an optimize key?
    if bestModel is not None:
      maxKeyLen = max([len(k) for k in sortedMetricsKeys])
      maxKeyLen = max(maxKeyLen, len(optimizationMetricKey))
      formatStr = "  %%-%ds" % (maxKeyLen+2)
      bestMetricValue = bestModel.getOptimizationMetrics().values()[0]
      optimizationMetricName = bestModel.getOptimizationMetrics().keys()[0]
      print
      print "Best results on the optimization metric %s (maximize=%s):" % (
          optimizationMetricName, maximizeMetric)
      print "[%d] Experiment %s (%s):" % (
          bestModelIterIndex, bestModel, bestModel.getModelDescription())
      print formatStr % (optimizationMetricName+':'), bestMetricValue
      print
      print "Total number of Records processed: %d"  % totalRecords
      print
      print "Total wall time for all models: %d" % totalWallTime

      hsJobParams = hyperSearchJob.getParams()

    # Were we asked to write out the top N model description files?
    if options['genTopNDescriptions'] > 0:
      print "\nGenerating description files for top %d models..." % (
              options['genTopNDescriptions'])
      scoreModelIDDescList.sort()
      scoreModelIDDescList = scoreModelIDDescList[
          0:options['genTopNDescriptions']]

      i = -1
      for (score, modelID, description, paramLabels) in scoreModelIDDescList:
        i += 1
        outDir = os.path.join(options['permWorkDir'], 'model_%d' % (i))
        print "Generating description file for model %s at %s" % \
          (modelID, outDir)
        if not os.path.exists(outDir):
          os.makedirs(outDir)

        # Fix up the location to the base description file
        description = description.replace(
              "importBaseDescription('base.py', config)",
              "importBaseDescription('../description.py', config)")
        fd = open(os.path.join(outDir, 'description.py'), 'wb')
        fd.write(description)
        fd.close()

        # Generate a csv file with the parameter settings in it
        fd = open(os.path.join(outDir, 'params.csv'), 'wb')
        writer = csv.writer(fd)
        colNames = paramLabels.keys()
        colNames.sort()
        writer.writerow(colNames)
        row = [paramLabels[x] for x in colNames]
        writer.writerow(row)
        fd.close()

      print

    reportWriter.finalize()



  @classmethod
  def loadSavedHyperSearchJob(cls, permWorkDir, outputLabel):
    """Instantiates a _HyperSearchJob instance from info saved in file

    Parameters:
    ----------------------------------------------------------------------
    permWorkDir: Directory path for saved jobID file
    outputLabel: Label string for incorporating into file name for saved jobID
    retval:      _HyperSearchJob instance; raises exception if not found
    """
    jobID = cls.__loadHyperSearchJobID(permWorkDir=permWorkDir,
                                       outputLabel=outputLabel)

    searchJob = _HyperSearchJob(grokJobID=jobID)
    return searchJob


  @classmethod
  def __saveHyperSearchJobID(cls, permWorkDir, outputLabel, hyperSearchJob):
    """Saves the given _HyperSearchJob instance's jobID to file

    Parameters:
    ----------------------------------------------------------------------
    permWorkDir:   Directory path for saved jobID file
    outputLabel:   Label string for incorporating into file name for saved jobID
    hyperSearchJob: _HyperSearchJob instance
    retval:        nothing
    """
    jobID = hyperSearchJob.getJobID()
    filePath = cls.__getHyperSearchJobIDFilePath(permWorkDir=permWorkDir,
                                                 outputLabel=outputLabel)

    if os.path.exists(filePath):
      _backupFile(filePath)

    d = dict(hyperSearchJobID = jobID)

    with open(filePath, 'wb') as jobIdPickleFile:
      pickle.dump(d, jobIdPickleFile)


  @classmethod
  def __loadHyperSearchJobID(cls, permWorkDir, outputLabel):
    """Loads a saved jobID from file

    Parameters:
    ----------------------------------------------------------------------
    permWorkDir:  Directory path for saved jobID file
    outputLabel:  Label string for incorporating into file name for saved jobID
    retval:       HyperSearch jobID; raises exception if not found.
    """
    filePath = cls.__getHyperSearchJobIDFilePath(permWorkDir=permWorkDir,
                                                 outputLabel=outputLabel)

    jobID = None
    with open(filePath, 'rb') as jobIdPickleFile:
      jobInfo = pickle.load(jobIdPickleFile)
      jobID = jobInfo['hyperSearchJobID']

    return jobID


  @classmethod
  def __getHyperSearchJobIDFilePath(cls, permWorkDir, outputLabel):
    """Returns filepath where to store HyperSearch JobID

    Parameters:
    ----------------------------------------------------------------------
    permWorkDir: Directory path for saved jobID file
    outputLabel: Label string for incorporating into file name for saved jobID
    retval:      Filepath where to store HyperSearch JobID
    """
    # Get the base path and figure out the path of the report file.
    basePath = permWorkDir

    # Form the name of the output csv file that will contain all the results
    filename = "%s_HyperSearchJobID.pkl" % (outputLabel,)
    filepath = os.path.join(basePath, filename)

    return filepath



class _ModelStats(object):


  def __init__(self):
    # Tallies of experiment dispositions
    self.numStatusWaitingToStart = long(0)
    self.numStatusRunning = long(0)
    self.numStatusCompleted = long(0)
    self.numStatusOther = long(0)
    #self.numCompletedSuccess = long(0)
    self.numCompletedKilled = long(0)
    self.numCompletedError = long(0)
    self.numCompletedStopped = long(0)
    self.numCompletedEOF = long(0)
    self.numCompletedOther = long(0)
    self.numCompletedOrphaned = long(0)


  def update(self, modelInfo):
    # Tabulate experiment dispositions
    if modelInfo.isWaitingToStart():
      self.numStatusWaitingToStart += 1
    elif modelInfo.isRunning():
      self.numStatusRunning += 1
    elif modelInfo.isFinished():
      self.numStatusCompleted += 1

      reason = modelInfo.getCompletionReason()
#      if reason.isSuccess():
#        self.numCompletedSuccess += 1
      if reason.isEOF():
        self.numCompletedEOF += 1
      elif reason.isKilled():
        self.numCompletedKilled += 1
      elif reason.isStopped():
        self.numCompletedStopped += 1
      elif reason.isError():
        self.numCompletedError += 1
      elif reason.isOrphaned():
        self.numCompletedOrphaned += 1
      else:
        self.numCompletedOther += 1
    else:
      self.numStatusOther += 1



class _ReportCSVWriter(object):


  __totalModelTime = timedelta()


  def __init__(self,
               hyperSearchJob,
               metricsKeys,
               searchVar,
               outputDirAbsPath,
               outputLabel,
               replaceReport):
    """
    Parameters:
    ----------------------------------------------------------------------
    hyperSearchJob: _HyperSearchJob instance
    metricsKeys:    sequence of report metrics key names to include in report
    outputDirAbsPath:
                    Directory for creating report CSV file (absolute path)
    outputLabel:    A string label to incorporate into report CSV file name
    replaceReport:  True to replace existing report csv, if any; False to
                    append to existing report csv, if any
    retval:         nothing
    """
    self.__searchJob = hyperSearchJob
    self.__searchJobID = hyperSearchJob.getJobID()
    self.__sortedMetricsKeys = sorted(metricsKeys)
    self.__outputDirAbsPath = os.path.abspath(outputDirAbsPath)
    self.__outputLabel = outputLabel
    self.__replaceReport = replaceReport
    self.__sortedVariableNames=searchVar
    # These are set up by __openAndInitCSVFile
    self.__csvFileObj = None
    self.__reportCSVPath = None
    self.__backupCSVPath = None


  def emit(self, modelInfo):
    """Emit model info to csv file

    Parameters:
    ----------------------------------------------------------------------
    modelInfo:      _GrokModelInfo instance
    retval:         nothing
    """
    # Open/init csv file, if needed
    if self.__csvFileObj is None:
      # sets up self.__sortedVariableNames and self.__csvFileObj
      self.__openAndInitCSVFile(modelInfo)

    csv = self.__csvFileObj

    # Emit model info row to report.csv
    print >> csv, '%s, ' % (self.__searchJobID),
    print >> csv, '%s, ' % (modelInfo.getModelID()),
    print >> csv, '%s, ' % (modelInfo.statusAsString()),
    if modelInfo.isFinished():
      print >> csv, '%s, ' % (modelInfo.getCompletionReason()),
    else:
      print >> csv, 'NA, ',
    if not modelInfo.isWaitingToStart():
      print >> csv, '%s, ' % (modelInfo.getStartTime()),
    else:
      print >> csv, 'NA, ',
    if modelInfo.isFinished():
      format = "%Y-%m-%d %H:%M:%S"
      startTime = modelInfo.getStartTime()
      endTime = modelInfo.getEndTime()
      print >> csv, '%s, ' % endTime,
      st = datetime.strptime(startTime, format)
      et = datetime.strptime(endTime, format)
      print >> csv, '%s, ' % (str((et - st).seconds)),
    else:
      print >> csv, 'NA, ',
      print >> csv, 'NA, ',
    print >> csv, '%s, ' % str(modelInfo.getModelDescription()),
    print >> csv, '%s, ' % str(modelInfo.getNumRecords()),
    paramLabelsDict = modelInfo.getParamLabels()
    for key in self.__sortedVariableNames:
      # Some values are complex structures,.. which need to be represented as
      # strings
      if key in paramLabelsDict:
        print >> csv, '%s, ' % (paramLabelsDict[key]),
      else:
        print >> csv, 'None, ',
    metrics = modelInfo.getReportMetrics()
    for key in self.__sortedMetricsKeys:
      value = metrics.get(key, "NA")
      value = str(value)
      value = value.replace('\n', ' ')
      print >> csv, '%s, ' % (value),

    print >> csv


  def finalize(self):
    """Close file and print report/backup csv file paths

    Parameters:
    ----------------------------------------------------------------------
    retval:         nothing
    """
    if self.__csvFileObj is not None:
      # Done with file
      self.__csvFileObj.close()
      self.__csvFileObj = None

      print "Report csv saved in %s" % (self.__reportCSVPath,)

      if self.__backupCSVPath:
        print "Previous report csv file was backed up to %s" % \
                (self.__backupCSVPath,)
    else:
      print "Nothing was written to report csv file."


  def __openAndInitCSVFile(self, modelInfo):
    """
    - Backs up old report csv file;
    - opens the report csv file in append or overwrite mode (per
      self.__replaceReport);
    - emits column fields;
    - sets up self.__sortedVariableNames, self.__csvFileObj,
      self.__backupCSVPath, and self.__reportCSVPath

    Parameters:
    ----------------------------------------------------------------------
    modelInfo:      First _GrokModelInfo instance passed to emit()
    retval:         nothing
    """
    # Get the base path and figure out the path of the report file.
    basePath = self.__outputDirAbsPath

    # Form the name of the output csv file that will contain all the results
    reportCSVName = "%s_Report.csv" % (self.__outputLabel,)
    reportCSVPath = self.__reportCSVPath = os.path.join(basePath, reportCSVName)

    # If a report CSV file already exists, back it up
    backupCSVPath = None
    if os.path.exists(reportCSVPath):
      backupCSVPath = self.__backupCSVPath = _backupFile(reportCSVPath)


    # Open report file
    if self.__replaceReport:
      mode = 'w'
    else:
      mode = 'a'
    csv = self.__csvFileObj = open(reportCSVPath, mode)

    # If we are appending, add some blank line separators
    if not self.__replaceReport and backupCSVPath:
      print >> csv
      print >> csv

    # Print the column names
    print >> csv, 'jobID, ',
    print >> csv, 'modelID, ',
    print >> csv, 'status, ' ,
    print >> csv, 'completionReason, ',
    print >> csv, 'startTime, ',
    print >> csv, 'endTime, ',
    print >> csv, 'runtime(s), ' ,
    print >> csv, 'expDesc, ',
    print >> csv, 'numRecords, ',

    for key in self.__sortedVariableNames:
      print >> csv, '%s, ' % key,
    for key in self.__sortedMetricsKeys:
      print >> csv, '%s, ' % key,
    print >> csv



class _GrokJob(object):
  """Our Grok Job abstraction"""


  def __init__(self, grokJobID):
    """_GrokJob constructor

    Parameters:
    ----------------------------------------------------------------------
    retval:         Grok Client JobID of the job
    """
    self.__grokJobID = grokJobID

    jobInfo = _clientJobsDB().jobInfo(grokJobID)
    assert jobInfo is not None, "jobID=%s not found" % grokJobID
    assert jobInfo.jobId == grokJobID, "%s != %s" % (jobInfo.jobId, grokJobID)
    _emit(Verbosity.DEBUG, "_GrokJob: \n%s" % pprint.pformat(jobInfo, indent=4))

    if jobInfo.params is not None:
      self.__params = json.loads(jobInfo.params)
    else:
      self.__params = None


  def __repr__(self):
    """
    Parameters:
    ----------------------------------------------------------------------
    retval:         representation of this _GrokJob instance
    """
    return "%s(jobID=%s)" % (self.__class__.__name__, self.__grokJobID)


  def getJobStatus(self, workers):
    """
    Parameters:
    ----------------------------------------------------------------------
    workers:  If this job was launched outside of the Grok engine, then this
               is an array of subprocess Popen instances, one for each worker
    retval:         _GrokJob.JobStatus instance
    
    """
    jobInfo = self.JobStatus(self.__grokJobID, workers)
    return jobInfo


  def getJobID(self):
    """Semi-private method for retrieving the jobId

    Parameters:
    ----------------------------------------------------------------------
    retval:         Grok Client JobID of this _GrokJob instance
    """
    return self.__grokJobID


  def getParams(self):
    """Semi-private method for retrieving the job-specific params

    Parameters:
    ----------------------------------------------------------------------
    retval:         Job params dict corresponding to the JSON params value
                    returned by ClientJobsDAO.jobInfo()
    """
    return self.__params


  class JobStatus(object):
    """Our Grok Job Info abstraction class"""

    # Job Status values (per ClientJobsDAO.py):
    __grokJobStatus_NotStarted  = cjdao.ClientJobsDAO.STATUS_NOTSTARTED
    __grokJobStatus_Starting    = cjdao.ClientJobsDAO.STATUS_STARTING
    __grokJobStatus_running     = cjdao.ClientJobsDAO.STATUS_RUNNING
    __grokJobStatus_completed   = cjdao.ClientJobsDAO.STATUS_COMPLETED

    def __init__(self, grokJobID, workers):
      """_GrokJob.JobStatus Constructor

      Parameters:
      ----------------------------------------------------------------------
      grokJobID:    Grok ClientJob ID
      workers:  If this job was launched outside of the Grok engine, then this
               is an array of subprocess Popen instances, one for each worker
      retval:       nothing
      """

      jobInfo = _clientJobsDB().jobInfo(grokJobID)
      assert jobInfo.jobId == grokJobID, "%s != %s" % (jobInfo.jobId, grokJobID)
      
      # If we launched the workers ourself, set the job status based on the
      #  workers that are still running
      if workers is not None:
        runningCount = 0
        for worker in workers:
          retCode = worker.poll()
          if retCode is None:
            runningCount += 1
        if runningCount > 0:
          status = cjdao.ClientJobsDAO.STATUS_RUNNING
        else:
          status = cjdao.ClientJobsDAO.STATUS_COMPLETED

        jobInfo = jobInfo._replace(status=status)
          
      _emit(Verbosity.DEBUG, "JobStatus: \n%s" % pprint.pformat(jobInfo,
                                                                indent=4))

      self.__jobInfo = jobInfo


    def __repr__(self):
      return "%s(jobId=%s, status=%s, completionReason=%s, " \
             "startTime=%s, endTime=%s)" % (
                self.__class__.__name__, self.__jobInfo.jobId,
                self.statusAsString(), self.__jobInfo.completionReason,
                self.__jobInfo.startTime, self.__jobInfo.endTime)


    def statusAsString(self):
      """
      Parameters:
      ----------------------------------------------------------------------
      retval:       Job status as a human-readable string
      """
      return self.__jobInfo.status


    def isWaitingToStart(self):
      """
      Parameters:
      ----------------------------------------------------------------------
      retval:       True if the job has not been started yet
      """
      waiting = (self.__jobInfo.status == self.__grokJobStatus_NotStarted)
      return waiting

    def isStarting(self):
      """
      Parameters:
      ----------------------------------------------------------------------
      retval:         True if the job is starting
      """
      starting = (self.__jobInfo.status == self.__grokJobStatus_Starting)
      return starting

    def isRunning(self):
      """
      Parameters:
      ----------------------------------------------------------------------
      retval:         True if the job is running
      """
      running = (self.__jobInfo.status == self.__grokJobStatus_running)
      return running

    def isFinished(self):
      """
      Parameters:
      ----------------------------------------------------------------------
      retval:         True if the job has finished (either with success or
                      failure)
      """
      done = (self.__jobInfo.status == self.__grokJobStatus_completed)
      return done


    def getCompletionReason(self):
      """Returns JobCompletionReason.
      NOTE: it's an error to call this method if isFinished() would return
      False.

      Parameters:
      ----------------------------------------------------------------------
      retval:         JobCompletionReason instance
      """
      assert self.isFinished(), "Too early to tell: %s" % self
      return JobCompletionReason(self.__jobInfo.completionReason)


    def getCompletionMsg(self):
      """Returns job completion message.

      NOTE: it's an error to call this method if isFinished() would return
      False.

      Parameters:
      ----------------------------------------------------------------------
      retval:         completion message
      """
      assert self.isFinished(), "Too early to tell: %s" % self
      return "%s" % self.__jobInfo.completionMsg


    def getWorkerCompletionMsg(self):
      """Returns the worker generated completion message.

      NOTE: it's an error to call this method if isFinished() would return
      False.

      Parameters:
      ----------------------------------------------------------------------
      retval:         completion message
      """
      assert self.isFinished(), "Too early to tell: %s" % self
      return "%s" % self.__jobInfo.workerCompletionMsg


    def getStartTime(self):
      """Returns job start time.

      NOTE: it's an error to call this method if isWaitingToStart() would
      return True.

      Parameters:
      ----------------------------------------------------------------------
      retval:         job processing start time
      """
      assert not self.isWaitingToStart(), "Too early to tell: %s" % self
      return "%s" % self.__jobInfo.startTime


    def getEndTime(self):
      """Returns job end time.

      NOTE: it's an error to call this method if isFinished() would return
      False.

      Parameters:
      ----------------------------------------------------------------------
      retval:         job processing end time
      """
      assert self.isFinished(), "Too early to tell: %s" % self
      return "%s" % self.__jobInfo.endTime



    def getWorkerState(self):
      """Returns the worker state field.

      Parameters:
      ----------------------------------------------------------------------
      retval:         worker state field as a dict
      """
      if self.__jobInfo.engWorkerState is not None:
        return json.loads(self.__jobInfo.engWorkerState)
      else:
        return None


    def getResults(self):
      """Returns the results field.

      Parameters:
      ----------------------------------------------------------------------
      retval:         job results field as a dict
      """
      if self.__jobInfo.results is not None:
        return json.loads(self.__jobInfo.results)
      else:
        return None

    def getModelMilestones(self):
      """Returns the model milestones field.

      Parameters:
      ----------------------------------------------------------------------
      retval:        model milestones as a dict
      """
      if self.__jobInfo.engModelMilestones is not None:
        return json.loads(self.__jobInfo.engModelMilestones)
      else:
        return None

    def getEngStatus(self):
      """Returns the engine status field - used for progress messages

      Parameters:
      ----------------------------------------------------------------------
      retval:        engine status field as string
      """
      return self.__jobInfo.engStatus



class JobCompletionReason(object):
  """Represents completion reason for Client Jobs and Models"""


  def __init__(self, reason):
    """
    Parameters:
    ----------------------------------------------------------------------
    reason:   completion reason value from ClientJobsDAO.jobInfo()
    """
    self.__reason = reason


  def __str__(self):
    return "%s" % self.__reason


  def __repr__(self):
    return "%s(reason=%s)" % (self.__class__.__name__, self.__reason)


  def isEOF(self):
    return self.__reason == cjdao.ClientJobsDAO.CMPL_REASON_EOF


  def isSuccess(self):
    return self.__reason == cjdao.ClientJobsDAO.CMPL_REASON_SUCCESS


  def isStopped(self):
    return self.__reason == cjdao.ClientJobsDAO.CMPL_REASON_STOPPED


  def isKilled(self):
    return self.__reason == cjdao.ClientJobsDAO.CMPL_REASON_KILLED


  def isOrphaned(self):
    return self.__reason == cjdao.ClientJobsDAO.CMPL_REASON_ORPHAN


  def isError(self):
    return self.__reason == cjdao.ClientJobsDAO.CMPL_REASON_ERROR



class _HyperSearchJob(_GrokJob):
  """This class represents a single running Grok HyperSearch job"""


  def __init__(self, grokJobID):
    """
    Parameters:
    ----------------------------------------------------------------------
    grokJobID:      Grok Client JobID of a HyperSearch job
    retval:         nothing
    """
    super(_HyperSearchJob, self).__init__(grokJobID)

    # Cache of the total count of expected models or -1 if it can't be
    # deteremined.
    #
    # Set by getExpectedNumModels()
    #
    # TODO: update code to handle non-ronomatic search algorithms
    self.__expectedNumModels = None


  def queryModelIDs(self):
    """Queuries Grok for model IDs of all currently instantiated models
    associated with this HyperSearch job.

    See also: _iterModels()

    Parameters:
    ----------------------------------------------------------------------
    retval:         A sequence of Grok modelIDs
    """
    jobID = self.getJobID()
    modelCounterPairs = _clientJobsDB().modelsGetUpdateCounters(jobID)
    modelIDs = tuple(x[0] for x in modelCounterPairs)

    return modelIDs


  def getExpectedNumModels(self, searchMethod):
    """Returns:  the total number of expected models if known, -1 if it can't
    be determined.

    NOTE: this can take a LONG time to complete for HyperSearches with a huge
          number of possible permutations.

    Parameters:
    ----------------------------------------------------------------------
    searchMethod:   'v2' is the only method currently supported
    retval:         The total number of expected models, if known; -1 if unknown
    """
    return self.__expectedNumModels



class _ClientJobUtils(object):
  """Our Grok Client Job utilities"""


  @classmethod
  def makeSearchJobParamsDict(cls, options, forRunning=False):
    """Constructs a dictionary of HyperSearch parameters suitable for converting
    to json and passing as the params argument to ClientJobsDAO.jobInsert()
    Parameters:
    ----------------------------------------------------------------------
    options:        GrokRunPermutations options dict
    forRunning:     True if the params are for running a Hypersearch job; False
                    if params are for introspection only.

    retval:         A dictionary of HyperSearch parameters for
                    ClientJobsDAO.jobInsert()
    """
    if options['searchMethod'] == 'v2':
      hsVersion = 'v2'
    else:
      raise Exception("Unsupported search method: %r" % options['searchMethod'])

    maxModels = options['maxPermutations']
    if options['action'] == 'dryRun' and maxModels is None:
      maxModels = 1

    useTerminators = options['useTerminators']
    if useTerminators is None:
      params = {
              'hsVersion':          hsVersion,
              'maxModels':          maxModels,
              'useStreams':         options['useStreams']
             }
    else:
      params = {
              'hsVersion':          hsVersion,
              'useTerminators':     useTerminators,
              'maxModels':          maxModels,
              'useStreams':         options['useStreams']
             }

    if forRunning:
      params['persistentJobGUID'] = str(uuid.uuid1())

    if options['permutationsScriptPath']:

      params['permutationsPyFilename'] = options['permutationsScriptPath']
    else:
      with open(name=options['expDescJsonPath'], mode="r") as fp:
        params['description'] = json.load(fp)

    return params



class _PermutationUtils(object):
  """Utilities for running permutations"""


  @classmethod
  def getOptimizationMetricInfo(cls, searchJobParams):
    """Retrives the optimization key name and optimization function.

    Parameters:
    ---------------------------------------------------------
    searchJobParams:
                    Parameter for passing as the searchParams arg to
                    Hypersearch constructor.
    retval:       (optimizationMetricKey, maximize)
                  optimizationMetricKey: which report key to optimize for
                  maximize: True if we should try and maximize the optimizeKey
                    metric. False if we should minimize it.
    """
    if searchJobParams['hsVersion'] == 'v2':
      search = HypersearchV2(searchParams=searchJobParams)
    else:
      raise RuntimeError("Unsupported hypersearch version '%s'" % \
                         (searchJobParams['hsVersion']))

    info = search.getOptimizationMetricInfo()
    return info



def _backupFile(filePath):
  """Back up a file

  Parameters:
  ----------------------------------------------------------------------
  retval:         Filepath of the back-up
  """
  assert os.path.exists(filePath)

  stampNum = 0
  (prefix, suffix) = os.path.splitext(filePath)
  while True:
    backupPath = "%s.%d%s" % (prefix, stampNum, suffix)
    stampNum += 1
    if not os.path.exists(backupPath):
      break
  shutil.copyfile(filePath, backupPath)

  return backupPath



def _getOneModelInfo(grokModelID):
  """A convenience function that retrieves inforamtion about a single model

  See also: _iterModels()

  Parameters:
  ----------------------------------------------------------------------
  grokModelID:      Grok modelID
  retval:           _GrokModelInfo instance for the given grokModelID.
  """
  return _iterModels([grokModelID]).next()



def _iterModels(modelIDs):
  """Creates an iterator that returns ModelInfo elements for the given modelIDs

  WARNING:      The order of ModelInfo elements returned by the iterator
                may not match the order of the given modelIDs

  Parameters:
  ----------------------------------------------------------------------
  modelIDs:       A sequence of model identifiers (e.g., as returned by
                  _HyperSearchJob.queryModelIDs()).
  retval:         Iterator that returns ModelInfo elements for the given
                  modelIDs (NOTE:possibly in a different order)
  """

  class ModelInfoIterator(object):
    """ModelInfo iterator implementation class
    """

    # Maximum number of ModelInfo elements to load into cache whenever
    # cache empties
    __CACHE_LIMIT = 1000

    debug=False

    def __init__(self, modelIDs):
      """
      Parameters:
      ----------------------------------------------------------------------
      modelIDs:     a sequence of Grok model identifiers for which this
                    iterator will return _GrokModelInfo instances.
                    NOTE: The returned instances are NOT guaranteed to be in
                    the same order as the IDs in modelIDs sequence.
      retval:       nothing
      """
      # Make our own copy in case caller changes model id list during iteration
      self.__modelIDs = tuple(modelIDs)

      if self.debug:
        _emit(Verbosity.DEBUG,
              "MODELITERATOR: __init__; numModelIDs=%s" % len(self.__modelIDs))

      self.__nextIndex = 0
      self.__modelCache = collections.deque()
      return

    def __iter__(self):
      """Iterator Protocol function

      Parameters:
      ----------------------------------------------------------------------
      retval:         self
      """
      return self


    def next(self):
      """Iterator Protocol function

      Parameters:
      ----------------------------------------------------------------------
      retval:       A _GrokModelInfo instance or raises StopIteration to
                    signal end of iteration.
      """
      return self.__getNext()


    def __getNext(self):
      """Implementation of the next() Iterator Protocol function.

      When the modelInfo cache becomes empty, queries Grok and fills the cache
      with the next set of GrokModelInfo instances.

      Parameters:
      ----------------------------------------------------------------------
      retval:       A _GrokModelInfo instance or raises StopIteration to
                    signal end of iteration.
      """

      if self.debug:
        _emit(Verbosity.DEBUG,
              "MODELITERATOR: __getNext(); modelCacheLen=%s" % (
                  len(self.__modelCache)))

      if not self.__modelCache:
        self.__fillCache()

      if not self.__modelCache:
        raise StopIteration()

      return self.__modelCache.popleft()

    def __fillCache(self):
      """Queries Grok and fills an empty modelInfo cache with the next set of
      _GrokModelInfo instances

      Parameters:
      ----------------------------------------------------------------------
      retval:       nothing
      """
      assert (not self.__modelCache)

      # Assemble a list of model IDs to look up
      numModelIDs = len(self.__modelIDs) if self.__modelIDs else 0

      if self.__nextIndex >= numModelIDs:
        return

      idRange = self.__nextIndex + self.__CACHE_LIMIT
      if idRange > numModelIDs:
        idRange = numModelIDs

      lookupIDs = self.__modelIDs[self.__nextIndex:idRange]

      self.__nextIndex += (idRange - self.__nextIndex)

      # Query Grok for model info of all models in the look-up list
      # NOTE: the order of results may not be the same as lookupIDs
      infoList = _clientJobsDB().modelsInfo(lookupIDs)
      assert len(infoList) == len(lookupIDs), \
            "modelsInfo returned %s elements; expected %s." % \
            (len(infoList), len(lookupIDs))

      # Create _GrokModelInfo instances and add them to cache
      for rawInfo in infoList:
        modelInfo = _GrokModelInfo(rawInfo=rawInfo)
        self.__modelCache.append(modelInfo)

      assert len(self.__modelCache) == len(lookupIDs), \
             "Added %s elements to modelCache; expected %s." % \
             (len(self.__modelCache), len(lookupIDs))

      if self.debug:
        _emit(Verbosity.DEBUG,
              "MODELITERATOR: Leaving __fillCache(); modelCacheLen=%s" % \
                (len(self.__modelCache),))

  return ModelInfoIterator(modelIDs)



class _GrokModelInfo(object):
  """This class represents information obtained from ClientJobManager about a
  model
  """


  __grokModelStatus_notStarted  = cjdao.ClientJobsDAO.STATUS_NOTSTARTED
  __grokModelStatus_running     = cjdao.ClientJobsDAO.STATUS_RUNNING
  __grokModelStatus_completed   = cjdao.ClientJobsDAO.STATUS_COMPLETED
  __rawInfo = None


  def __init__(self, rawInfo):
    """
    Parameters:
    ----------------------------------------------------------------------
    rawInfo:        A single model information element as returned by
                    ClientJobsDAO.modelsInfo()
    retval:         nothing.
    """
    # Namedtuple returned by ClientJobsDAO.modelsInfo()
    self.__rawInfo = rawInfo

    # Cached model metrics (see __unwrapResults())
    self.__cachedResults = None

    assert self.__rawInfo.params is not None
    # Cached model params (see __unwrapParams())
    self.__cachedParams = None


  def __repr__(self):
    """
    Parameters:
    ----------------------------------------------------------------------
    retval:         Representation of this _GrokModelInfo instance.
    """
    return ("%s(jobID=%s, modelID=%s, status=%s, completionReason=%s, "
            "updateCounter=%s, numRecords=%s)" % (
                "_GrokModelInfo",
                self.__rawInfo.jobId,
                self.__rawInfo.modelId,
                self.__rawInfo.status,
                self.__rawInfo.completionReason,
                self.__rawInfo.updateCounter,
                self.__rawInfo.numRecords))


  def getModelID(self):
    """
    Parameters:
    ----------------------------------------------------------------------
    retval:         Grok modelID associated with this model info.
    """
    return self.__rawInfo.modelId


  def statusAsString(self):
    """
    Parameters:
    ----------------------------------------------------------------------
    retval:    Human-readable string representation of the model's status.
    """
    return "%s" % self.__rawInfo.status


  def getModelDescription(self):
    """
    Parameters:
    ----------------------------------------------------------------------
    retval:         Printable description of the model.
    """
    params = self.__unwrapParams()

    if 'experimentName' in params:
      return params['experimentName']

    else:
      paramSettings = self.getParamLabels()
      # Form a csv friendly string representation of this model
      items = []
      for key, value in paramSettings.items():
        items.append('%s_%s' % (key, value))
      return '.'.join(items)


  def getGeneratedDescriptionFile(self):
    """
    Parameters:
    ----------------------------------------------------------------------
    retval:         Contents of the sub-experiment description file for
                        this model
    """
    return self.__rawInfo.genDescription


  def getNumRecords(self):
    """
    Paramets:
    ----------------------------------------------------------------------
    retval:         The number of records processed by the model.
    """
    return self.__rawInfo.numRecords

  def getParamLabels(self):
    """
    Parameters:
    ----------------------------------------------------------------------
    retval:         a dictionary of model parameter labels. For each entry
                    the key is the name of the parameter and the value
                    is the value chosen for it.
    """
    params = self.__unwrapParams()

    # Hypersearch v2 stores the flattened parameter settings in 'particleState'
    if 'particleState' in params:
      retval = dict()
      queue = [(pair, retval) for pair in
               params['particleState']['varStates'].iteritems()]
      while len(queue) > 0:
        pair, output = queue.pop()
        k, v = pair
        if ('position' in v and 'bestPosition' in v and
            'velocity' in v):
          output[k] = v['position']
        else:
          if k not in output:
            output[k] = dict()
          queue.extend((pair, output[k]) for pair in v.iteritems())
      return retval


  def __unwrapParams(self):
    """Unwraps self.__rawInfo.params into the equivalent python dictionary
    and caches it in self.__cachedParams. Returns the unwrapped params

    Parameters:
    ----------------------------------------------------------------------
    retval:         Model params dictionary as correpsonding to the json
                    as returned in ClientJobsDAO.modelsInfo()[x].params
    """
    if self.__cachedParams is None:
      self.__cachedParams = json.loads(self.__rawInfo.params)
      assert self.__cachedParams is not None, \
             "%s resulted in None" % self.__rawInfo.params

    return self.__cachedParams


  def getReportMetrics(self):
    """Retrives a dictionary of metrics designated for report
    Parameters:
    ----------------------------------------------------------------------
    retval: a dictionary of metrics that were collected for the model or
            an empty dictionary if there aren't any.
    """
    return self.__unwrapResults().reportMetrics


  def getOptimizationMetrics(self):
    """Retrives a dictionary of metrics designagted for optimization
    Parameters:
    ----------------------------------------------------------------------
    retval:         a dictionary of optimization metrics that were collected
                    for the model or an empty dictionary if there aren't any.
    """
    return self.__unwrapResults().optimizationMetrics


  def getAllMetrics(self):
    """Retrives a dictionary of metrics that combines all report and
    optimization metrics

    Parameters:
    ----------------------------------------------------------------------
    retval:         a dictionary of optimization metrics that were collected
                    for the model; an empty dictionary if there aren't any.
    """
    result = self.getReportMetrics()
    result.update(self.getOptimizationMetrics())
    return result


  ModelResults = collections.namedtuple('ModelResultsTuple',
                                        ['reportMetrics',
                                         'optimizationMetrics'])
  """Each element is a dictionary: property name is the metric name and
  property value is the metric value as generated by the model
  """


  def __unwrapResults(self):
    """Unwraps self.__rawInfo.results and caches it in self.__cachedResults;
    Returns the unwrapped params

    Parameters:
    ----------------------------------------------------------------------
    retval:         ModelResults namedtuple instance
    """
    if self.__cachedResults is None:
      if self.__rawInfo.results is not None:
        resultList = json.loads(self.__rawInfo.results)
        assert len(resultList) == 2, \
               "Expected 2 elements, but got %s (%s)." % (
                len(resultList), resultList)
        self.__cachedResults = self.ModelResults(
          reportMetrics=resultList[0],
          optimizationMetrics=resultList[1])
      else:
        self.__cachedResults = self.ModelResults(
          reportMetrics={},
          optimizationMetrics={})


    return self.__cachedResults


  def isWaitingToStart(self):
    """
    Parameters:
    ----------------------------------------------------------------------
    retval:       True if the job has not been started yet
    """
    waiting = (self.__rawInfo.status == self.__grokModelStatus_notStarted)
    return waiting


  def isRunning(self):
    """
    Parameters:
    ----------------------------------------------------------------------
    retval:       True if the job has not been started yet
    """
    running = (self.__rawInfo.status == self.__grokModelStatus_running)
    return running


  def isFinished(self):
    """
    Parameters:
    ----------------------------------------------------------------------
    retval:         True if the model's processing has completed (either with
                    success or failure).
    """
    finished = (self.__rawInfo.status == self.__grokModelStatus_completed)
    return finished


  def getCompletionReason(self):
    """Returns ModelCompletionReason.

    NOTE: it's an error to call this method if isFinished() would return False.

    Parameters:
    ----------------------------------------------------------------------
    retval:         ModelCompletionReason instance
    """
    assert self.isFinished(), "Too early to tell: %s" % self
    return ModelCompletionReason(self.__rawInfo.completionReason)


  def getCompletionMsg(self):
    """Returns model completion message.

    NOTE: it's an error to call this method if isFinished() would return False.

    Parameters:
    ----------------------------------------------------------------------
    retval:         completion message
    """
    assert self.isFinished(), "Too early to tell: %s" % self
    return self.__rawInfo.completionMsg


  def getStartTime(self):
    """Returns model evaluation start time.

    NOTE: it's an error to call this method if isWaitingToStart() would
    return True.

    Parameters:
    ----------------------------------------------------------------------
    retval:         model evaluation start time
    """
    assert not self.isWaitingToStart(), "Too early to tell: %s" % self
    return "%s" % self.__rawInfo.startTime


  def getEndTime(self):
    """Returns mode evaluation end time.

    NOTE: it's an error to call this method if isFinished() would return False.

    Parameters:
    ----------------------------------------------------------------------
    retval:         model evaluation end time
    """
    assert self.isFinished(), "Too early to tell: %s" % self
    return "%s" % self.__rawInfo.endTime



class ModelCompletionReason(JobCompletionReason):
  pass
