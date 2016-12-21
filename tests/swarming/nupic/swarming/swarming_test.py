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

import sys
import os
import imp
import subprocess
import re
import json
import pprint
import shutil
import copy
import StringIO
import logging
import itertools
import numpy
import time
import math
import uuid
import tempfile
from pkg_resources import resource_filename

from optparse import OptionParser


from nupic.database.ClientJobsDAO import ClientJobsDAO
from nupic.support import configuration, initLogging
from nupic.support.unittesthelpers.testcasebase import (unittest,
    TestCaseBase as HelperTestCaseBase)
from nupic.swarming import HypersearchWorker
from nupic.swarming.api import getSwarmModelParams, createAndStartSwarm
from nupic.swarming.utils import generatePersistentJobGUID
from nupic.swarming.DummyModelRunner import OPFDummyModelRunner

DEFAULT_JOB_TIMEOUT_SEC = 60 * 2

# Filters _debugOut messages
g_debug = True

# Our setUpModule entry block sets this to an instance of MyTestEnvironment()
g_myEnv = None

# These are the args after using the optparse

# This value for the swarm maturity window gives more repeatable results for
#  unit tests that use multiple workers
g_repeatableSwarmMaturityWindow = 5



class MyTestEnvironment(object):

  # =======================================================================
  def __init__(self):

    # Save all command line options
    self.options = _ArgParser.parseArgs()

    # Create the path to our source experiments
    thisFile = __file__
    testDir = os.path.split(os.path.abspath(thisFile))[0]
    self.testSrcExpDir = os.path.join(testDir, 'experiments')
    self.testSrcDataDir = os.path.join(testDir, 'data')

    return



class ExperimentTestBaseClass(HelperTestCaseBase):


  def setUp(self):
    """ Method called to prepare the test fixture. This is called by the
    unittest framework immediately before calling the test method; any exception
    raised by this method will be considered an error rather than a test
    failure. The default implementation does nothing.
    """
    pass


  def tearDown(self):
    """ Method called immediately after the test method has been called and the
    result recorded. This is called even if the test method raised an exception,
    so the implementation in subclasses may need to be particularly careful
    about checking internal state. Any exception raised by this method will be
    considered an error rather than a test failure. This method will only be
    called if the setUp() succeeds, regardless of the outcome of the test
    method. The default implementation does nothing.
    """
    # Reset our log items
    self.resetExtraLogItems()


  def shortDescription(self):
    """ Override to force unittest framework to use test method names instead
    of docstrings in the report.
    """
    return None


  def _printTestHeader(self):
    """ Print out what test we are running
    """

    print "###############################################################"
    print "Running test: %s.%s..." % (self.__class__, self._testMethodName)


  def _setDataPath(self, env):
    """ Put the path to our datasets int the NTA_DATA_PATH variable which
    will be used to set the environment for each of the workers
    
    Parameters:
    ---------------------------------------------------------------------
    env: The current environment dict
    """
    
    assert env is not None
    
    # If already have a path, concatenate to it
    if "NTA_DATA_PATH" in env:
      newPath = "%s%s%s" % (env["NTA_DATA_PATH"], os.pathsep, g_myEnv.testSrcDataDir)
    else:
      newPath = g_myEnv.testSrcDataDir
      
    env["NTA_DATA_PATH"] = newPath


  def _launchWorkers(self, cmdLine, numWorkers):
    """ Launch worker processes to execute the given command line
    
    Parameters:
    -----------------------------------------------
    cmdLine: The command line for each worker
    numWorkers: number of workers to launch
    retval: list of workers 
    
    """

    workers = []
    for i in range(numWorkers):
      stdout = tempfile.TemporaryFile()
      stderr = tempfile.TemporaryFile()
      p = subprocess.Popen(cmdLine, bufsize=1, env=os.environ, shell=True,
                           stdin=None, stdout=stdout, stderr=stderr)
      workers.append(p)
      
    return workers


  def _getJobInfo(self, cjDAO, workers, jobID):
    """ Return the job info for a job
    
    Parameters:
    -----------------------------------------------
    cjDAO:   client jobs database instance
    workers: list of workers for this job
    jobID:   which job ID
    
    retval: job info
    """

    # Get the job info
    jobInfo = cjDAO.jobInfo(jobID)

    # Since we're running outside of the Nupic engine, we launched the workers 
    #  ourself, so see how many are still running and jam the correct status 
    #  into the job info. When using the Nupic engine, it would do this
    #  for us. 
    runningCount = 0
    for worker in workers:
      retCode = worker.poll()
      if retCode is None:
        runningCount += 1
        
    if runningCount > 0:
      status = ClientJobsDAO.STATUS_RUNNING
    else:
      status = ClientJobsDAO.STATUS_COMPLETED

    jobInfo = jobInfo._replace(status=status)
    if status == ClientJobsDAO.STATUS_COMPLETED:
      jobInfo = jobInfo._replace(
                        completionReason=ClientJobsDAO.CMPL_REASON_SUCCESS)
    return jobInfo


  def _generateHSJobParams(self,
                           expDirectory=None,
                           hsImp='v2',
                           maxModels=2,
                           predictionCacheMaxRecords=None,
                           dataPath=None,
                           maxRecords=10):
    """
    This method generates a canned Hypersearch Job Params structure based
    on some high level options

    Parameters:
    ---------------------------------------------------------------------
    predictionCacheMaxRecords:
                   If specified, determine the maximum number of records in
                   the prediction cache.
    dataPath:      When expDirectory is not specified, this is the data file
                   to be used for the operation. If this value is not specified,
                   it will use the /extra/qa/hotgym/qa_hotgym.csv.
    """


    if expDirectory is not None:
      descriptionPyPath = os.path.join(expDirectory, "description.py")
      permutationsPyPath = os.path.join(expDirectory, "permutations.py")

      permutationsPyContents = open(permutationsPyPath, 'r').read()
      descriptionPyContents = open(descriptionPyPath, 'r').read()

      jobParams = {'persistentJobGUID' : generatePersistentJobGUID(),
                   'permutationsPyContents': permutationsPyContents,
                   'descriptionPyContents': descriptionPyContents,
                   'maxModels': maxModels,
                   'hsVersion': hsImp}

      if predictionCacheMaxRecords is not None:
        jobParams['predictionCacheMaxRecords'] = predictionCacheMaxRecords

    else:


      # Form the stream definition
      if dataPath is None:
        dataPath = resource_filename("nupic.data",
                                     os.path.join("extra", "qa", "hotgym",
                                                  "qa_hotgym.csv"))
        
      streamDef = dict(
        version = 1,
        info = "TestHypersearch",
        streams = [
          dict(source="file://%s" % (dataPath),
               info=dataPath,
               columns=["*"],
               first_record=0,
               last_record=maxRecords),
          ],
      )


      # Generate the experiment description
      expDesc = {
        "predictionField": "consumption",
        "streamDef": streamDef,
        "includedFields": [
          { "fieldName": "gym",
            "fieldType": "string"
          },
          { "fieldName": "consumption",
            "fieldType": "float",
            "minValue": 0,
            "maxValue": 200,
          },
        ],
        "iterationCount": maxRecords,
        "resetPeriod": {
          'weeks': 0,
          'days': 0,
          'hours': 8,
          'minutes': 0,
          'seconds': 0,
          'milliseconds': 0,
          'microseconds': 0,
        },
      }


      jobParams = {
        "persistentJobGUID": generatePersistentJobGUID(),
        "description":expDesc,
        "maxModels": maxModels,
        "hsVersion": hsImp,
      }

      if predictionCacheMaxRecords is not None:
        jobParams['predictionCacheMaxRecords'] = predictionCacheMaxRecords

    return jobParams


  def _runPermutationsLocal(self, jobParams, loggingLevel=logging.INFO,
                            env=None, waitForCompletion=True,
                            continueJobId=None, ignoreErrModels=False):
    """ This runs permutations on the given experiment using just 1 worker
    in the current process

    Parameters:
    -------------------------------------------------------------------
    jobParams:        filled in job params for a hypersearch
    loggingLevel:    logging level to use in the Hypersearch worker
    env:             if not None, this is a dict of environment variables
                        that should be sent to each worker process. These can
                        aid in re-using the same description/permutations file
                        for different tests.
    waitForCompletion: If True, wait for job to complete before returning
                       If False, then return resultsInfoForAllModels and
                       metricResults will be None
    continueJobId:    If not None, then this is the JobId of a job we want
                      to continue working on with another worker.
    ignoreErrModels:  If true, ignore erred models
    retval:          (jobId, jobInfo, resultsInfoForAllModels, metricResults)
    """


    print
    print "=================================================================="
    print "Running Hypersearch job using 1 worker in current process"
    print "=================================================================="

    # Plug in modified environment variables
    if env is not None:
      saveEnvState = copy.deepcopy(os.environ)
      os.environ.update(env)

    # Insert the job entry into the database in the pre-running state
    cjDAO = ClientJobsDAO.get()
    if continueJobId is None:
      jobID = cjDAO.jobInsert(client='test', cmdLine='<started manually>',
              params=json.dumps(jobParams),
              alreadyRunning=True, minimumWorkers=1, maximumWorkers=1,
              jobType = cjDAO.JOB_TYPE_HS)
    else:
      jobID = continueJobId

    # Command line args.
    args = ['ignoreThis', '--jobID=%d' % (jobID),
            '--logLevel=%d' % (loggingLevel)]
    if continueJobId is None:
      args.append('--clearModels')

    # Run it in the current process
    try:
      HypersearchWorker.main(args)

    # The dummy model runner will call sys.exit(0) when
    #  NTA_TEST_sysExitAfterNIterations is set
    except SystemExit:
      pass
    except:
      raise

    # Restore environment
    if env is not None:
      os.environ = saveEnvState

    # ----------------------------------------------------------------------
    # Make sure all models completed successfully
    models = cjDAO.modelsGetUpdateCounters(jobID)
    modelIDs = [model.modelId for model in models]
    if len(modelIDs) > 0:
      results = cjDAO.modelsGetResultAndStatus(modelIDs)
    else:
      results = []

    metricResults = []
    for result in results:
      if result.results is not None:
        metricResults.append(json.loads(result.results)[1].values()[0])
      else:
        metricResults.append(None)
      if not ignoreErrModels:
        self.assertNotEqual(result.completionReason, cjDAO.CMPL_REASON_ERROR,
            "Model did not complete successfully:\n%s" % (result.completionMsg))

    # Print worker completion message
    jobInfo = cjDAO.jobInfo(jobID)

    return (jobID, jobInfo, results, metricResults)


  def _runPermutationsCluster(self, jobParams, loggingLevel=logging.INFO,
                              maxNumWorkers=4, env=None,
                              waitForCompletion=True, ignoreErrModels=False,
                              timeoutSec=DEFAULT_JOB_TIMEOUT_SEC):
    """ Given a prepared, filled in jobParams for a hypersearch, this starts
    the job, waits for it to complete, and returns the results for all
    models.

    Parameters:
    -------------------------------------------------------------------
    jobParams:        filled in job params for a hypersearch
    loggingLevel:    logging level to use in the Hypersearch worker
    maxNumWorkers:    max # of worker processes to use
    env:             if not None, this is a dict of environment variables
                        that should be sent to each worker process. These can
                        aid in re-using the same description/permutations file
                        for different tests.
    waitForCompletion: If True, wait for job to complete before returning
                       If False, then return resultsInfoForAllModels and
                       metricResults will be None
    ignoreErrModels:  If true, ignore erred models
    retval:          (jobID, jobInfo, resultsInfoForAllModels, metricResults)
    """

    print
    print "=================================================================="
    print "Running Hypersearch job on cluster"
    print "=================================================================="

    # --------------------------------------------------------------------
    # Submit the job
    if env is not None and len(env) > 0:
      envItems = []
      for (key, value) in env.iteritems():
        if (sys.platform.startswith('win')):
          envItems.append("set \"%s=%s\"" % (key, value))
        else:
          envItems.append("export %s=%s" % (key, value))
      if (sys.platform.startswith('win')):
        envStr = "%s &" % (' & '.join(envItems))
      else:
        envStr = "%s;" % (';'.join(envItems))
    else:
      envStr = ''

    cmdLine = '%s python -m nupic.swarming.HypersearchWorker ' \
                          '--jobID={JOBID} --logLevel=%d' \
                          % (envStr, loggingLevel)

    cjDAO = ClientJobsDAO.get()
    jobID = cjDAO.jobInsert(client='test', cmdLine=cmdLine,
            params=json.dumps(jobParams),
            minimumWorkers=1, maximumWorkers=maxNumWorkers,
            jobType = cjDAO.JOB_TYPE_HS)

    # Launch the workers ourself if necessary (no nupic engine running). 
    workerCmdLine = '%s python -m nupic.swarming.HypersearchWorker ' \
                          '--jobID=%d --logLevel=%d' \
                          % (envStr, jobID, loggingLevel)
    workers = self._launchWorkers(cmdLine=workerCmdLine, numWorkers=maxNumWorkers)

    print "Successfully submitted new test job, jobID=%d" % (jobID)
    print "Each of %d workers executing the command line: " % (maxNumWorkers), \
            cmdLine

    if not waitForCompletion:
      return (jobID, None, None)

    if timeoutSec is None:
      timeout=DEFAULT_JOB_TIMEOUT_SEC
    else:
      timeout=timeoutSec

    # --------------------------------------------------------------------
    # Wait for it to complete
    startTime = time.time()
    lastUpdate = time.time()
    lastCompleted = 0
    lastCompletedWithError = 0
    lastCompletedAsOrphan = 0
    lastStarted = 0
    lastJobStatus = "NA"
    lastJobResults = None
    lastActiveSwarms = None
    lastEngStatus = None
    modelIDs = []
    print "\n%-15s    %-15s %-15s %-15s %-15s" % ("jobStatus", "modelsStarted",
                                "modelsCompleted", "modelErrs", "modelOrphans")
    print "-------------------------------------------------------------------"
    while (lastJobStatus != ClientJobsDAO.STATUS_COMPLETED) \
          and (time.time() - lastUpdate < timeout):

      printUpdate = False
      if g_myEnv.options.verbosity == 0:
        time.sleep(0.5)

      # --------------------------------------------------------------------
      # Get the job status
      jobInfo = self._getJobInfo(cjDAO, workers, jobID)
      if jobInfo.status != lastJobStatus:
        if jobInfo.status == ClientJobsDAO.STATUS_RUNNING \
            and lastJobStatus != ClientJobsDAO.STATUS_RUNNING:
          print "# Swarm job now running. jobID=%s" \
                % (jobInfo.jobId)

        lastJobStatus = jobInfo.status
        printUpdate = True

      if g_myEnv.options.verbosity >= 1:
        if jobInfo.engWorkerState is not None:
          activeSwarms = json.loads(jobInfo.engWorkerState)['activeSwarms']
          if activeSwarms != lastActiveSwarms:
            #print "-------------------------------------------------------"
            print ">> Active swarms:\n   ", '\n    '.join(activeSwarms)
            lastActiveSwarms = activeSwarms
            print

        if jobInfo.results != lastJobResults:
          #print "-------------------------------------------------------"
          print ">> New best:", jobInfo.results, "###"
          lastJobResults = jobInfo.results

        if jobInfo.engStatus != lastEngStatus:
          print '>> Status: "%s"' % jobInfo.engStatus
          print
          lastEngStatus = jobInfo.engStatus


      # --------------------------------------------------------------------
      # Get the list of models created for this job
      modelCounters = cjDAO.modelsGetUpdateCounters(jobID)
      if len(modelCounters) != lastStarted:
        modelIDs = [x.modelId for x in modelCounters]
        lastStarted = len(modelCounters)
        printUpdate = True

      # --------------------------------------------------------------------
      # See how many have finished
      if len(modelIDs) > 0:
        completed = 0
        completedWithError = 0
        completedAsOrphan = 0
        infos = cjDAO.modelsGetResultAndStatus(modelIDs)
        for info in infos:
          if info.status == ClientJobsDAO.STATUS_COMPLETED:
            completed += 1
            if info.completionReason == ClientJobsDAO.CMPL_REASON_ERROR:
              completedWithError += 1
            if info.completionReason == ClientJobsDAO.CMPL_REASON_ORPHAN:
              completedAsOrphan += 1


        if completed != lastCompleted \
              or completedWithError != lastCompletedWithError \
              or completedAsOrphan != lastCompletedAsOrphan:
          lastCompleted = completed
          lastCompletedWithError = completedWithError
          lastCompletedAsOrphan = completedAsOrphan
          printUpdate = True

      # --------------------------------------------------------------------
      # Print update?
      if printUpdate:
        lastUpdate = time.time()
        if g_myEnv.options.verbosity >= 1:
          print ">>",
        print "%-15s %-15d %-15d %-15d %-15d" % (lastJobStatus, lastStarted,
                lastCompleted,
                lastCompletedWithError,
                lastCompletedAsOrphan)


    # ========================================================================
    # Final total
    print "\n<< %-15s %-15d %-15d %-15d %-15d" % (lastJobStatus, lastStarted,
                lastCompleted,
                lastCompletedWithError,
                lastCompletedAsOrphan)

    # Success?
    jobInfo = self._getJobInfo(cjDAO, workers, jobID)

    if not ignoreErrModels:
      self.assertEqual (jobInfo.completionReason,
                      ClientJobsDAO.CMPL_REASON_SUCCESS)

    # Get final model results
    models = cjDAO.modelsGetUpdateCounters(jobID)
    modelIDs = [model.modelId for model in models]
    if len(modelIDs) > 0:
      results = cjDAO.modelsGetResultAndStatus(modelIDs)
    else:
      results = []

    metricResults = []
    for result in results:
      if result.results is not None:
        metricResults.append(json.loads(result.results)[1].values()[0])
      else:
        metricResults.append(None)
      if not ignoreErrModels:
        self.assertNotEqual(result.completionReason, cjDAO.CMPL_REASON_ERROR,
          "Model did not complete successfully:\n%s" % (result.completionMsg))


    return (jobID, jobInfo, results, metricResults)


  def runPermutations(self, expDirectory, hsImp='v2', maxModels=2,
                      maxNumWorkers=4, loggingLevel=logging.INFO,
                      onCluster=False, env=None, waitForCompletion=True,
                      continueJobId=None, dataPath=None, maxRecords=None,
                      timeoutSec=None, ignoreErrModels=False,
                      predictionCacheMaxRecords=None, **kwargs):
    """ This runs permutations on the given experiment using just 1 worker

    Parameters:
    -------------------------------------------------------------------
    expDirectory:    directory containing the description.py and permutations.py
    hsImp:           which implementation of Hypersearch to use
    maxModels:       max # of models to generate
    maxNumWorkers:   max # of workers to use, N/A if onCluster is False
    loggingLevel:    logging level to use in the Hypersearch worker
    onCluster:       if True, run on the Hadoop cluster
    env:             if not None, this is a dict of environment variables
                        that should be sent to each worker process. These can
                        aid in re-using the same description/permutations file
                        for different tests.
    waitForCompletion: If True, wait for job to complete before returning
                       If False, then return resultsInfoForAllModels and
                       metricResults will be None
    continueJobId:    If not None, then this is the JobId of a job we want
                      to continue working on with another worker.
    ignoreErrModels:  If true, ignore erred models
    maxRecords:       This value is passed to the function, _generateHSJobParams(),
                      to represent the maximum number of records to generate for
                      the operation.
    dataPath:         This value is passed to the function, _generateHSJobParams(),
                      which points to the data file for the operation.
    predictionCacheMaxRecords:
                      If specified, determine the maximum number of records in
                      the prediction cache.
                
    retval:          (jobID, jobInfo, resultsInfoForAllModels, metricResults,
                        minErrScore)
    """
    
    # Put in the path to our datasets
    if env is None:
      env = dict()
    self._setDataPath(env)
    
    # ----------------------------------------------------------------
    # Prepare the jobParams
    jobParams = self._generateHSJobParams(expDirectory=expDirectory,
                                          hsImp=hsImp, maxModels=maxModels,
                                          maxRecords=maxRecords,
                                          dataPath=dataPath,
                                          predictionCacheMaxRecords=predictionCacheMaxRecords)

    jobParams.update(kwargs)

    if onCluster:
      (jobID, jobInfo, resultInfos, metricResults) \
        =  self._runPermutationsCluster(jobParams=jobParams,
                                        loggingLevel=loggingLevel,
                                        maxNumWorkers=maxNumWorkers,
                                        env=env,
                                        waitForCompletion=waitForCompletion,
                                        ignoreErrModels=ignoreErrModels,
                                        timeoutSec=timeoutSec)

    else:
      (jobID, jobInfo, resultInfos, metricResults) \
        = self._runPermutationsLocal(jobParams=jobParams,
                                     loggingLevel=loggingLevel,
                                     env=env,
                                     waitForCompletion=waitForCompletion,
                                     continueJobId=continueJobId,
                                     ignoreErrModels=ignoreErrModels)

    if not waitForCompletion:
      return (jobID, jobInfo, resultInfos, metricResults, None)

    # Print job status
    print "\n------------------------------------------------------------------"
    print "Hadoop completion reason: %s" % (jobInfo.completionReason)
    print "Worker completion reason: %s" % (jobInfo.workerCompletionReason)
    print "Worker completion msg: %s" % (jobInfo.workerCompletionMsg)

    if jobInfo.engWorkerState is not None:
      print "\nEngine worker state:"
      print "---------------------------------------------------------------"
      pprint.pprint(json.loads(jobInfo.engWorkerState))


    # Print out best results
    minErrScore=None
    metricAmts = []
    for result in metricResults:
      if result is None:
        metricAmts.append(numpy.inf)
      else:
        metricAmts.append(result)

    metricAmts = numpy.array(metricAmts)
    if len(metricAmts) > 0:
      minErrScore = metricAmts.min()
      minModelID = resultInfos[metricAmts.argmin()].modelId

      # Get model info
      cjDAO = ClientJobsDAO.get()
      modelParams = cjDAO.modelsGetParams([minModelID])[0].params
      print "Model params for best model: \n%s" \
                              % (pprint.pformat(json.loads(modelParams)))
      print "Best model result: %f" % (minErrScore)

    else:
      print "No models finished"


    return (jobID, jobInfo, resultInfos, metricResults, minErrScore)



class OneNodeTests(ExperimentTestBaseClass):
  """
  """
  # AWS tests attribute required for tagging via automatic test discovery via
  # nosetests
  engineAWSClusterTest=True


  def setUp(self):
    super(OneNodeTests, self).setUp()
    if not g_myEnv.options.runInProc:
      self.skipTest("Skipping One Node test since runInProc is not specified")


  def testSimpleV2(self, onCluster=False, env=None, **kwargs):
    """ 
    Try running simple permutations
    """
    self._printTestHeader()
    expDir = os.path.join(g_myEnv.testSrcExpDir, 'simpleV2')

    # Test it out
    if env is None:
      env = dict()
    env["NTA_TEST_numIterations"] = '99'
    env["NTA_CONF_PROP_nupic_hypersearch_swarmMaturityWindow"] = \
                         '%d' % (g_repeatableSwarmMaturityWindow)

    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
           = self.runPermutations(expDir,
                                  hsImp='v2',
                                  loggingLevel=g_myEnv.options.logLevel,
                                  onCluster=onCluster,
                                  env=env,
                                  maxModels=None,
                                  **kwargs)


    self.assertEqual(minErrScore, 20)
    self.assertLess(len(resultInfos), 350)

    return


  def testDeltaV2(self, onCluster=False, env=None, **kwargs):
    """ Try running a simple permutations with delta encoder
    Test which tests the delta encoder. Runs a swarm of the sawtooth dataset
    With a functioning delta encoder this should give a perfect result
    DEBUG: disabled temporarily because this test takes too long!!!
    """

    self._printTestHeader()
    expDir = os.path.join(g_myEnv.testSrcExpDir, 'delta')

    # Test it out
    if env is None:
      env = dict()
    env["NTA_CONF_PROP_nupic_hypersearch_swarmMaturityWindow"] = \
                         '%d' % (g_repeatableSwarmMaturityWindow)
    env["NTA_TEST_exitAfterNModels"] = str(20)

    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
           = self.runPermutations(expDir,
                                  hsImp='v2',
                                  loggingLevel=g_myEnv.options.logLevel,
                                  onCluster=onCluster,
                                  env=env,
                                  maxModels=None,
                                  **kwargs)


    self.assertLess(minErrScore, 0.002)

    return


  def testSimpleV2NoSpeculation(self, onCluster=False, env=None, **kwargs):
    """ Try running a simple permutations
    """

    self._printTestHeader()
    expDir = os.path.join(g_myEnv.testSrcExpDir, 'simpleV2')

    # Test it out
    if env is None:
      env = dict()
    env["NTA_TEST_numIterations"] = '99'
    env["NTA_CONF_PROP_nupic_hypersearch_swarmMaturityWindow"] = \
                         '%d' % (g_repeatableSwarmMaturityWindow)

    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
           = self.runPermutations(expDir,
                                  hsImp='v2',
                                  loggingLevel=g_myEnv.options.logLevel,
                                  onCluster=onCluster,
                                  env=env,
                                  maxModels=None,
                                  speculativeParticles=False,
                                  **kwargs)


    self.assertEqual(minErrScore, 20)
    self.assertGreater(len(resultInfos), 1)
    self.assertLess(len(resultInfos), 350)
    return


  def testCLAModelV2(self, onCluster=False, env=None, maxModels=2,
                      **kwargs):
    """ Try running a simple permutations using an actual CLA model, not
    a dummy
    """

    self._printTestHeader()
    expDir = os.path.join(g_myEnv.testSrcExpDir, 'dummyV2')

    # Test it out
    if env is None:
      env = dict()

    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
           = self.runPermutations(expDir,
                                  hsImp='v2',
                                  loggingLevel=g_myEnv.options.logLevel,
                                  onCluster=onCluster,
                                  env=env,
                                  maxModels=maxModels,
                                  **kwargs)


    self.assertEqual(len(resultInfos), maxModels)
    return


  def testCLAMultistepModel(self, onCluster=False, env=None, maxModels=2,
                      **kwargs):
    """ Try running a simple permutations using an actual CLA model, not
    a dummy
    """

    self._printTestHeader()
    expDir = os.path.join(g_myEnv.testSrcExpDir, 'simple_cla_multistep')

    # Test it out
    if env is None:
      env = dict()

    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
           = self.runPermutations(expDir,
                                  hsImp='v2',
                                  loggingLevel=g_myEnv.options.logLevel,
                                  onCluster=onCluster,
                                  env=env,
                                  maxModels=maxModels,
                                  **kwargs)


    self.assertEqual(len(resultInfos), maxModels)
    return


  def testLegacyCLAMultistepModel(self, onCluster=False, env=None, maxModels=2,
                      **kwargs):
    """ Try running a simple permutations using an actual CLA model, not
    a dummy. This is a legacy CLA multi-step model that doesn't declare a
    separate 'classifierOnly' encoder for the predicted field. 
    """

    self._printTestHeader()
    expDir = os.path.join(g_myEnv.testSrcExpDir, 'legacy_cla_multistep')

    # Test it out
    if env is None:
      env = dict()

    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
           = self.runPermutations(expDir,
                                  hsImp='v2',
                                  loggingLevel=g_myEnv.options.logLevel,
                                  onCluster=onCluster,
                                  env=env,
                                  maxModels=maxModels,
                                  **kwargs)


    self.assertEqual(len(resultInfos), maxModels)
    return


  def testFilterV2(self, onCluster=False):
    """ Try running a simple permutations
    """

    self._printTestHeader()
    expDir = os.path.join(g_myEnv.testSrcExpDir, 'simpleV2')



    # Don't allow the consumption encoder maxval to get to it's optimum
    #   value (which is 250). This increases our errScore by +25.
    env = dict()
    env["NTA_TEST_maxvalFilter"] = '225'
    env["NTA_CONF_PROP_nupic_hypersearch_swarmMaturityWindow"] = '6'
    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
           = self.runPermutations(expDir,
                                  hsImp='v2',
                                  loggingLevel=g_myEnv.options.logLevel,
                                  onCluster=onCluster,
                                  env=env,
                                  maxModels=None)


    self.assertEqual(minErrScore, 45)
    self.assertLess(len(resultInfos), 400)
    return


  def testLateWorker(self, onCluster=False):
    """ Try running a simple permutations where a worker comes in late,
    after the some models have already been evaluated
    """

    self._printTestHeader()
    expDir = os.path.join(g_myEnv.testSrcExpDir, 'simpleV2')

    env = dict()
    env["NTA_CONF_PROP_nupic_hypersearch_swarmMaturityWindow"] = \
               '%d' % (g_repeatableSwarmMaturityWindow)
    env["NTA_TEST_exitAfterNModels"] =  '100'

    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
         = self.runPermutations(expDir,
                                hsImp='v2',
                                loggingLevel=g_myEnv.options.logLevel,
                                maxModels=None,
                                onCluster=onCluster,
                                env=env,
                                waitForCompletion=True,
                                )
    self.assertEqual(len(resultInfos), 100)

    # Run another worker the rest of the way
    env.pop("NTA_TEST_exitAfterNModels")
    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
         = self.runPermutations(expDir,
                                hsImp='v2',
                                loggingLevel=g_myEnv.options.logLevel,
                                maxModels=None,
                                onCluster=onCluster,
                                env=env,
                                waitForCompletion=True,
                                continueJobId = jobID,
                                )

    self.assertEqual(minErrScore, 20)
    self.assertLess(len(resultInfos), 350)
    return


  def testOrphanedModel(self, onCluster=False, modelRange=(0,1)):
    """ Run a worker on a model for a while, then have it exit before the
    model finishes. Then, run another worker, which should detect the orphaned
    model.
    """

    self._printTestHeader()
    expDir = os.path.join(g_myEnv.testSrcExpDir, 'simpleV2')

    # NTA_TEST_numIterations is watched by the dummyModelParams() method of
    #  the permutations file.
    # NTA_TEST_sysExitModelRange  is watched by the dummyModelParams() method of
    #  the permutations file. It tells it to do a sys.exit() after so many
    #  iterations.
    # We increase the swarm maturity window to make our unit tests more
    #   repeatable. There is an element of randomness as to which model
    #   parameter combinations get evaluated first when running with
    #   multiple workers, so this insures that we can find the "best" model
    #   that we expect to see in our unit tests.
    env = dict()
    env["NTA_TEST_numIterations"] = '2'
    env["NTA_TEST_sysExitModelRange"] = '%d,%d' % (modelRange[0], modelRange[1])
    env["NTA_CONF_PROP_nupic_hypersearch_swarmMaturityWindow"] \
            =  '%d' % (g_repeatableSwarmMaturityWindow)

    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
         = self.runPermutations(expDir,
                                hsImp='v2',
                                loggingLevel=g_myEnv.options.logLevel,
                                maxModels=300,
                                onCluster=onCluster,
                                env=env,
                                waitForCompletion=False,
                                )
    # At this point, we should have 1 model, still running
    (beg, end) = modelRange
    self.assertEqual(len(resultInfos), end)
    numRunning = 0
    for res in resultInfos:
      if res.status == ClientJobsDAO.STATUS_RUNNING:
        numRunning += 1
    self.assertEqual(numRunning, 1)


    # Run another worker the rest of the way, after delaying enough time to
    #  generate an orphaned model
    env["NTA_CONF_PROP_nupic_hypersearch_modelOrphanIntervalSecs"] = '1'
    time.sleep(2)

    # Here we launch another worker to finish up the job. We set the maxModels
    #  to 300 (200 something should be enough) in case the orphan detection is
    #  not working, it will make sure we don't loop for excessively long.
    # With orphan detection working, we should detect that the first model
    #  would never complete, orphan it, and create a new one in the 1st sprint.
    # Without orphan detection working, we will wait forever for the 1st sprint
    #  to finish, and will create a bunch of gen 1, then gen2, then gen 3, etc.
    #  and gen 0 will never finish, so the swarm will never mature.
    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
         = self.runPermutations(expDir,
                                hsImp='v2',
                                loggingLevel=g_myEnv.options.logLevel,
                                maxModels=300,
                                onCluster=onCluster,
                                env=env,
                                waitForCompletion=True,
                                continueJobId = jobID,
                                )

    self.assertEqual(minErrScore, 20)
    self.assertLess(len(resultInfos), 350)
    return


  def testOrphanedModelGen1(self):
    """ Run a worker on a model for a while, then have it exit before a
    model finishes in gen index 2. Then, run another worker, which should detect
    the orphaned model.
    """

    self._printTestHeader()
    inst = OneNodeTests(self._testMethodName)
    return inst.testOrphanedModel(modelRange=(10,11))


  def testErredModel(self, onCluster=False, modelRange=(6,7)):
    """ Run with 1 or more models generating errors
    """

    self._printTestHeader()
    expDir = os.path.join(g_myEnv.testSrcExpDir, 'simpleV2')

    # We increase the swarm maturity window to make our unit tests more
    #   repeatable. There is an element of randomness as to which model
    #   parameter combinations get evaluated first when running with
    #   multiple workers, so this insures that we can find the "best" model
    #   that we expect to see in our unit tests.
    env = dict()
    env["NTA_TEST_errModelRange"] = '%d,%d' % (modelRange[0], modelRange[1])
    env["NTA_CONF_PROP_nupic_hypersearch_swarmMaturityWindow"] \
            =  '%d' % (g_repeatableSwarmMaturityWindow)

    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
         = self.runPermutations(expDir,
                                hsImp='v2',
                                loggingLevel=g_myEnv.options.logLevel,
                                onCluster=onCluster,
                                env=env,
                                maxModels=None,
                                ignoreErrModels=True
                                )

    self.assertEqual(minErrScore, 20)
    self.assertLess(len(resultInfos), 350)
    return


  def testJobFailModel(self, onCluster=False, modelRange=(6,7)):
    """ Run with 1 or more models generating jobFail exception
    """

    self._printTestHeader()
    expDir = os.path.join(g_myEnv.testSrcExpDir, 'simpleV2')

    # We increase the swarm maturity window to make our unit tests more
    #   repeatable. There is an element of randomness as to which model
    #   parameter combinations get evaluated first when running with
    #   multiple workers, so this insures that we can find the "best" model
    #   that we expect to see in our unit tests.
    env = dict()
    env["NTA_TEST_jobFailErr"] = 'True'

    maxNumWorkers = 4
    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
         = self.runPermutations(expDir,
                                hsImp='v2',
                                loggingLevel=g_myEnv.options.logLevel,
                                onCluster=onCluster,
                                env=env,
                                maxModels=None,
                                maxNumWorkers=maxNumWorkers,
                                ignoreErrModels=True
                                )

    # Make sure workerCompletionReason was error
    self.assertEqual (jobInfo.workerCompletionReason,
                      ClientJobsDAO.CMPL_REASON_ERROR)
    self.assertLess (len(resultInfos), maxNumWorkers+1)
    return


  def testTooManyErredModels(self, onCluster=False, modelRange=(5,10)):
    """ Run with too many models generating errors
    """

    self._printTestHeader()
    expDir = os.path.join(g_myEnv.testSrcExpDir,  'simpleV2')

    # We increase the swarm maturity window to make our unit tests more
    #   repeatable. There is an element of randomness as to which model
    #   parameter combinations get evaluated first when running with
    #   multiple workers, so this insures that we can find the "best" model
    #   that we expect to see in our unit tests.
    env = dict()
    env["NTA_TEST_errModelRange"] = '%d,%d' % (modelRange[0], modelRange[1])
    env["NTA_CONF_PROP_nupic_hypersearch_swarmMaturityWindow"] \
            =  '%d' % (g_repeatableSwarmMaturityWindow)

    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
         = self.runPermutations(expDir,
                                hsImp='v2',
                                loggingLevel=g_myEnv.options.logLevel,
                                onCluster=onCluster,
                                env=env,
                                maxModels=None,
                                ignoreErrModels=True
                                )

    self.assertEqual (jobInfo.workerCompletionReason,
                      ClientJobsDAO.CMPL_REASON_ERROR)
    return


  def testFieldThreshold(self, onCluster=False, env=None, **kwargs):
    """ Test minimum field contribution threshold for a field to be included in further sprints
    """


    self._printTestHeader()
    expDir = os.path.join(g_myEnv.testSrcExpDir, 'field_threshold_temporal')

    # Test it out
    if env is None:
      env = dict()
    env["NTA_TEST_numIterations"] = '99'
    env["NTA_CONF_PROP_nupic_hypersearch_swarmMaturityWindow"] = \
                         '%d' % (g_repeatableSwarmMaturityWindow)

    env["NTA_CONF_PROP_nupic_hypersearch_max_field_branching"] = \
                         '%d' % (0)
    env["NTA_CONF_PROP_nupic_hypersearch_minParticlesPerSwarm"] = \
                         '%d' % (2)
    env["NTA_CONF_PROP_nupic_hypersearch_min_field_contribution"] = \
                         '%f' % (100)


    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
           = self.runPermutations(expDir,
                                  hsImp='v2',
                                  loggingLevel=g_myEnv.options.logLevel,
                                  onCluster=onCluster,
                                  env=env,
                                  maxModels=None,
                                  dummyModel={'iterations':200},
                                  **kwargs)

    # Get the field contributions from the hypersearch results dict
    cjDAO = ClientJobsDAO.get()
    jobResultsStr = cjDAO.jobGetFields(jobID, ['results'])[0]
    jobResults = json.loads(jobResultsStr)
    bestModel = cjDAO.modelsInfo([jobResults["bestModel"]])[0]
    params = json.loads(bestModel.params)
    
    prefix = 'modelParams|sensorParams|encoders|'
    expectedSwarmId = prefix + ('.' + prefix).join([
            'attendance', 
            'visitor_winloss'])

    self.assertEqual(params["particleState"]["swarmId"], 
                     expectedSwarmId,
                     "Actual swarm id = %s\nExpcted swarm id = %s" \
                     % (params["particleState"]["swarmId"], 
                        expectedSwarmId))
    self.assertEqual( bestModel.optimizedMetric, 75)


    #==========================================================================
    env["NTA_CONF_PROP_nupic_hypersearch_min_field_contribution"] = \
                         '%f' % (20)

    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
           = self.runPermutations(expDir,
                                  hsImp='v2',
                                  loggingLevel=g_myEnv.options.logLevel,
                                  onCluster=onCluster,
                                  env=env,
                                  maxModels=None,
                                  dummyModel={'iterations':200},
                                  **kwargs)

    # Get the field contributions from the hypersearch results dict
    cjDAO = ClientJobsDAO.get()
    jobResultsStr = cjDAO.jobGetFields(jobID, ['results'])[0]
    jobResults = json.loads(jobResultsStr)
    bestModel = cjDAO.modelsInfo([jobResults["bestModel"]])[0]
    params = json.loads(bestModel.params)

    prefix = 'modelParams|sensorParams|encoders|'
    expectedSwarmId = prefix + ('.' + prefix).join([
            'attendance', 
            'home_winloss', 
            'visitor_winloss'])
    self.assertEqual(params["particleState"]["swarmId"], 
                     expectedSwarmId,
                     "Actual swarm id = %s\nExpcted swarm id = %s" \
                     % (params["particleState"]["swarmId"], 
                        expectedSwarmId))
    assert bestModel.optimizedMetric == 55, bestModel.optimizedMetric



    #==========================================================================
    # Find best combo possible
    env["NTA_CONF_PROP_nupic_hypersearch_min_field_contribution"] = \
                         '%f' % (0.0)

    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
           = self.runPermutations(expDir,
                                  hsImp='v2',
                                  loggingLevel=g_myEnv.options.logLevel,
                                  onCluster=onCluster,
                                  env=env,
                                  maxModels=None,
                                  dummyModel={'iterations':200},
                                  **kwargs)

    # Get the field contributions from the hypersearch results dict
    cjDAO = ClientJobsDAO.get()
    jobResultsStr = cjDAO.jobGetFields(jobID, ['results'])[0]
    jobResults = json.loads(jobResultsStr)
    bestModel = cjDAO.modelsInfo([jobResults["bestModel"]])[0]
    params = json.loads(bestModel.params)

    prefix = 'modelParams|sensorParams|encoders|'
    expectedSwarmId = prefix + ('.' + prefix).join([
            'attendance', 
            'home_winloss', 
            'precip', 
            'timestamp_dayOfWeek',
            'timestamp_timeOfDay', 
            'visitor_winloss'])
    self.assertEqual(params["particleState"]["swarmId"], 
                     expectedSwarmId,
                     "Actual swarm id = %s\nExpcted swarm id = %s" \
                     % (params["particleState"]["swarmId"], 
                        expectedSwarmId))

    assert bestModel.optimizedMetric == 25, bestModel.optimizedMetric


  def testSpatialClassification(self, onCluster=False, env=None, **kwargs):
    """ 
    Try running a spatial classification swarm
    """
    self._printTestHeader()
    expDir = os.path.join(g_myEnv.testSrcExpDir, 'spatial_classification')

    # Test it out
    if env is None:
      env = dict()
    env["NTA_TEST_numIterations"] = '99'
    env["NTA_CONF_PROP_nupic_hypersearch_swarmMaturityWindow"] = \
                         '%d' % (g_repeatableSwarmMaturityWindow)

    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
           = self.runPermutations(expDir,
                                  hsImp='v2',
                                  loggingLevel=g_myEnv.options.logLevel,
                                  onCluster=onCluster,
                                  env=env,
                                  maxModels=None,
                                  **kwargs)


    self.assertEqual(minErrScore, 20)
    self.assertLess(len(resultInfos), 350)

    # Check the expected field contributions
    cjDAO = ClientJobsDAO.get()
    jobResultsStr = cjDAO.jobGetFields(jobID, ['results'])[0]
    jobResults = json.loads(jobResultsStr)
    bestModel = cjDAO.modelsInfo([jobResults["bestModel"]])[0]
    params = json.loads(bestModel.params)

    actualFieldContributions = jobResults['fieldContributions']
    print "Actual field contributions:", \
                              pprint.pformat(actualFieldContributions)
    expectedFieldContributions = {
                      'address': 100 * (90.0-30)/90.0,
                      'gym': 100 * (90.0-40)/90.0,  
                      'timestamp_dayOfWeek': 100 * (90.0-80.0)/90.0,
                      'timestamp_timeOfDay': 100 * (90.0-90.0)/90.0,
                      }

    for key, value in expectedFieldContributions.items():
      self.assertEqual(actualFieldContributions[key], value, 
                       "actual field contribution from field '%s' does not "
                       "match the expected value of %f" % (key, value))

      
    # Check the expected best encoder combination
    prefix = 'modelParams|sensorParams|encoders|'
    expectedSwarmId = prefix + ('.' + prefix).join([
            'address', 
            'gym'])

    self.assertEqual(params["particleState"]["swarmId"], 
                     expectedSwarmId,
                     "Actual swarm id = %s\nExpcted swarm id = %s" \
                     % (params["particleState"]["swarmId"], 
                        expectedSwarmId))


    return


  def testAlwaysInputPredictedField(self, onCluster=False, env=None, 
                                      **kwargs):
    """ 
    Run a swarm where 'inputPredictedField' is set in the permutations
    file. The dummy model for this swarm is designed to give the lowest
    error when the predicted field is INCLUDED, so make sure we don't get
    this low error
    """
    self._printTestHeader()
    expDir = os.path.join(g_myEnv.testSrcExpDir, 'input_predicted_field')

    # Test it out not requiring the predicted field. This should yield a
    #  low error score
    if env is None:
      env = dict()
    env["NTA_TEST_inputPredictedField"] = "auto"
    env["NTA_TEST_numIterations"] = '99'
    env["NTA_CONF_PROP_nupic_hypersearch_minParticlesPerSwarm"] = \
                         '%d' % (2)
    env["NTA_CONF_PROP_nupic_hypersearch_swarmMaturityWindow"] = \
                         '%d' % (g_repeatableSwarmMaturityWindow)

    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
           = self.runPermutations(expDir,
                                  hsImp='v2',
                                  loggingLevel=g_myEnv.options.logLevel,
                                  onCluster=onCluster,
                                  env=env,
                                  maxModels=None,
                                  **kwargs)


    self.assertEqual(minErrScore, -50)
    self.assertLess(len(resultInfos), 350)


    # Now, require the predicted field. This should yield a high error score
    if env is None:
      env = dict()
    env["NTA_TEST_inputPredictedField"] = "yes"
    env["NTA_TEST_numIterations"] = '99'
    env["NTA_CONF_PROP_nupic_hypersearch_minParticlesPerSwarm"] = \
                         '%d' % (2)
    env["NTA_CONF_PROP_nupic_hypersearch_swarmMaturityWindow"] = \
                         '%d' % (g_repeatableSwarmMaturityWindow)

    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
           = self.runPermutations(expDir,
                                  hsImp='v2',
                                  loggingLevel=g_myEnv.options.logLevel,
                                  onCluster=onCluster,
                                  env=env,
                                  maxModels=None,
                                  **kwargs)


    self.assertEqual(minErrScore, -40)
    self.assertLess(len(resultInfos), 350)

    return


  def testFieldThresholdNoPredField(self, onCluster=False, env=None, **kwargs):
    """ Test minimum field contribution threshold for a field to be included 
    in further sprints when doing a temporal search that does not require
    the predicted field. 
    """


    self._printTestHeader()
    expDir = os.path.join(g_myEnv.testSrcExpDir, 'input_predicted_field')

    # Test it out without any max field branching in effect
    if env is None:
      env = dict()
    env["NTA_TEST_numIterations"] = '99'
    env["NTA_TEST_inputPredictedField"] = "auto"
    env["NTA_CONF_PROP_nupic_hypersearch_swarmMaturityWindow"] = \
                         '%d' % (g_repeatableSwarmMaturityWindow)

    env["NTA_CONF_PROP_nupic_hypersearch_max_field_branching"] = \
                         '%d' % (0)
    env["NTA_CONF_PROP_nupic_hypersearch_minParticlesPerSwarm"] = \
                         '%d' % (2)
    env["NTA_CONF_PROP_nupic_hypersearch_min_field_contribution"] = \
                         '%f' % (0)


    if True:
      (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
             = self.runPermutations(expDir,
                                    hsImp='v2',
                                    loggingLevel=g_myEnv.options.logLevel,
                                    onCluster=onCluster,
                                    env=env,
                                    maxModels=None,
                                    dummyModel={'iterations':200},
                                    **kwargs)
  
      # Verify the best model and check the field contributions. 
      cjDAO = ClientJobsDAO.get()
      jobResultsStr = cjDAO.jobGetFields(jobID, ['results'])[0]
      jobResults = json.loads(jobResultsStr)
      bestModel = cjDAO.modelsInfo([jobResults["bestModel"]])[0]
      params = json.loads(bestModel.params)
      
      prefix = 'modelParams|sensorParams|encoders|'
      expectedSwarmId = prefix + ('.' + prefix).join([
              'address', 
              'gym',
              'timestamp_dayOfWeek', 
              'timestamp_timeOfDay'])
  
      self.assertEqual(params["particleState"]["swarmId"], 
                       expectedSwarmId,
                       "Actual swarm id = %s\nExpcted swarm id = %s" \
                       % (params["particleState"]["swarmId"], 
                          expectedSwarmId))
      self.assertEqual( bestModel.optimizedMetric, -50)
  
  
      # Check the field contributions
      actualFieldContributions = jobResults['fieldContributions']
      print "Actual field contributions:", \
                                pprint.pformat(actualFieldContributions)
      
      expectedFieldContributions = {
                        'consumption': 0.0, 
                        'address': 100 * (60.0-40.0)/60.0,
                        'timestamp_timeOfDay': 100 * (60.0-20.0)/60.0,
                        'timestamp_dayOfWeek': 100 * (60.0-10.0)/60.0,
                        'gym': 100 * (60.0-30.0)/60.0}
      
      
      for key, value in expectedFieldContributions.items():
        self.assertEqual(actualFieldContributions[key], value, 
                         "actual field contribution from field '%s' does not "
                         "match the expected value of %f" % (key, value))
      
  
    if True:
      #==========================================================================
      # Now test ignoring all fields that contribute less than 55% to the 
      #   error score. This means we can only use the timestamp_timeOfDay and
      #   timestamp_dayOfWeek fields. 
      # This should bring our best error score up to 50-30-40 = -20  
      env["NTA_CONF_PROP_nupic_hypersearch_min_field_contribution"] = \
                           '%f' % (55)
      env["NTA_CONF_PROP_nupic_hypersearch_max_field_branching"] = \
                         '%d' % (5)
  
      (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
             = self.runPermutations(expDir,
                                    hsImp='v2',
                                    loggingLevel=g_myEnv.options.logLevel,
                                    onCluster=onCluster,
                                    env=env,
                                    maxModels=None,
                                    dummyModel={'iterations':200},
                                    **kwargs)
  
      # Get the best model
      cjDAO = ClientJobsDAO.get()
      jobResultsStr = cjDAO.jobGetFields(jobID, ['results'])[0]
      jobResults = json.loads(jobResultsStr)
      bestModel = cjDAO.modelsInfo([jobResults["bestModel"]])[0]
      params = json.loads(bestModel.params)
  
      prefix = 'modelParams|sensorParams|encoders|'
      expectedSwarmId = prefix + ('.' + prefix).join([
              'timestamp_dayOfWeek', 
              'timestamp_timeOfDay'])
      self.assertEqual(params["particleState"]["swarmId"], 
                       expectedSwarmId,
                       "Actual swarm id = %s\nExpcted swarm id = %s" \
                       % (params["particleState"]["swarmId"], 
                          expectedSwarmId))
      self.assertEqual( bestModel.optimizedMetric, -20)

      # Check field contributions returned  
      actualFieldContributions = jobResults['fieldContributions']
      print "Actual field contributions:", \
                                pprint.pformat(actualFieldContributions)

      expectedFieldContributions = {
                        'consumption': 0.0, 
                        'address': 100 * (60.0-40.0)/60.0,
                        'timestamp_timeOfDay': 100 * (60.0-20.0)/60.0,
                        'timestamp_dayOfWeek': 100 * (60.0-10.0)/60.0,
                        'gym': 100 * (60.0-30.0)/60.0}
      
      for key, value in expectedFieldContributions.items():
        self.assertEqual(actualFieldContributions[key], value, 
                         "actual field contribution from field '%s' does not "
                         "match the expected value of %f" % (key, value))

    if True:  
      #==========================================================================
      # Now, test using maxFieldBranching to limit the max number of fields to
      #  3. This means we can only use the timestamp_timeOfDay, timestamp_dayOfWeek,
      # gym fields. 
      # This should bring our error score to 50-30-40-20 = -40
      env["NTA_CONF_PROP_nupic_hypersearch_min_field_contribution"] = \
                           '%f' % (0)
      env["NTA_CONF_PROP_nupic_hypersearch_max_field_branching"] = \
                           '%d' % (3)
  
      (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
             = self.runPermutations(expDir,
                                    hsImp='v2',
                                    loggingLevel=g_myEnv.options.logLevel,
                                    onCluster=onCluster,
                                    env=env,
                                    maxModels=None,
                                    dummyModel={'iterations':200},
                                    **kwargs)
  
      # Get the best model
      cjDAO = ClientJobsDAO.get()
      jobResultsStr = cjDAO.jobGetFields(jobID, ['results'])[0]
      jobResults = json.loads(jobResultsStr)
      bestModel = cjDAO.modelsInfo([jobResults["bestModel"]])[0]
      params = json.loads(bestModel.params)
  
      prefix = 'modelParams|sensorParams|encoders|'
      expectedSwarmId = prefix + ('.' + prefix).join([
              'gym',
              'timestamp_dayOfWeek', 
              'timestamp_timeOfDay'])
      self.assertEqual(params["particleState"]["swarmId"], 
                       expectedSwarmId,
                       "Actual swarm id = %s\nExpcted swarm id = %s" \
                       % (params["particleState"]["swarmId"], 
                          expectedSwarmId))
      self.assertEqual( bestModel.optimizedMetric, -40)


    if True:
      #==========================================================================
      # Now, test setting max models so that no swarm can finish completely.
      # Make sure we get the expected field contributions
      env["NTA_CONF_PROP_nupic_hypersearch_swarmMaturityWindow"] = \
                           '%d' % (g_repeatableSwarmMaturityWindow)
  
      env["NTA_CONF_PROP_nupic_hypersearch_max_field_branching"] = \
                           '%d' % (0)
      env["NTA_CONF_PROP_nupic_hypersearch_minParticlesPerSwarm"] = \
                           '%d' % (5)
      env["NTA_CONF_PROP_nupic_hypersearch_min_field_contribution"] = \
                           '%f' % (0)
  
      (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
             = self.runPermutations(expDir,
                                    hsImp='v2',
                                    loggingLevel=g_myEnv.options.logLevel,
                                    onCluster=onCluster,
                                    env=env,
                                    maxModels=10,
                                    dummyModel={'iterations':200},
                                    **kwargs)
  
      # Get the best model
      cjDAO = ClientJobsDAO.get()
      jobResultsStr = cjDAO.jobGetFields(jobID, ['results'])[0]
      jobResults = json.loads(jobResultsStr)
      bestModel = cjDAO.modelsInfo([jobResults["bestModel"]])[0]
      params = json.loads(bestModel.params)
  
      prefix = 'modelParams|sensorParams|encoders|'
      expectedSwarmId = prefix + ('.' + prefix).join([
              'timestamp_dayOfWeek'])
      self.assertEqual(params["particleState"]["swarmId"], 
                       expectedSwarmId,
                       "Actual swarm id = %s\nExpcted swarm id = %s" \
                       % (params["particleState"]["swarmId"], 
                          expectedSwarmId))
      self.assertEqual( bestModel.optimizedMetric, 10)

      # Check field contributions returned  
      actualFieldContributions = jobResults['fieldContributions']
      print "Actual field contributions:", \
                                pprint.pformat(actualFieldContributions)

      expectedFieldContributions = {
                        'consumption': 0.0, 
                        'address': 100 * (60.0-40.0)/60.0,
                        'timestamp_timeOfDay': 100 * (60.0-20.0)/60.0,
                        'timestamp_dayOfWeek': 100 * (60.0-10.0)/60.0,
                        'gym': 100 * (60.0-30.0)/60.0}



class MultiNodeTests(ExperimentTestBaseClass):
  """
  Test hypersearch on multiple nodes
  """
  # AWS tests attribute required for tagging via automatic test discovery via
  # nosetests
  engineAWSClusterTest=True


  def testSimpleV2(self):
    """ Try running a simple permutations
    """

    self._printTestHeader()
    inst = OneNodeTests(self._testMethodName)
    return inst.testSimpleV2(onCluster=True) #, maxNumWorkers=7)


  def testDeltaV2(self):
    """ Try running a simple permutations
    """

    self._printTestHeader()
    inst = OneNodeTests(self._testMethodName)
    return inst.testDeltaV2(onCluster=True) #, maxNumWorkers=7)


  def testSmartSpeculation(self, onCluster=True, env=None, **kwargs):
    """ Try running a simple permutations
    """

    self._printTestHeader()
    expDir = os.path.join(g_myEnv.testSrcExpDir, 'smart_speculation_temporal')

    # Test it out
    if env is None:
      env = dict()
    env["NTA_TEST_numIterations"] = '99'
    env["NTA_CONF_PROP_nupic_hypersearch_swarmMaturityWindow"] = \
                         '%d' % (g_repeatableSwarmMaturityWindow)

    env["NTA_CONF_PROP_nupic_hypersearch_minParticlesPerSwarm"] = \
                         '%d' % (1)


    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
           = self.runPermutations(expDir,
                                  hsImp='v2',
                                  loggingLevel=g_myEnv.options.logLevel,
                                  onCluster=onCluster,
                                  env=env,
                                  maxModels=None,
                                  dummyModel={'iterations':200},
                                  **kwargs)

    # Get the field contributions from the hypersearch results dict
    cjDAO = ClientJobsDAO.get()
    jobInfoStr = cjDAO.jobGetFields(jobID, ['results','engWorkerState'])
    jobResultsStr = jobInfoStr[0]
    engState = jobInfoStr[1]
    engState = json.loads(engState)
    swarms = engState["swarms"]
    jobResults = json.loads(jobResultsStr)
    bestModel = cjDAO.modelsInfo([jobResults["bestModel"]])[0]
    params = json.loads(bestModel.params)
    
    # Make sure that the only nonkilled models are the ones that would have been
    # run without speculation
    prefix = 'modelParams|sensorParams|encoders|'
    correctOrder = ["A","B","C","D","E","F","G","Pred"]
    correctOrder = [prefix + x for x in correctOrder]
    for swarm in swarms:
      if swarms[swarm]["status"] == 'killed':
        swarmId = swarm.split(".")
        if(len(swarmId)>1):
          # Make sure that something before the last two encoders is in the 
          # wrong sprint progression, hence why it was killed
          # The last encoder is the predicted field and the second to last is 
          # the current new addition
          wrong=0
          for i in range(len(swarmId)-2):
            if correctOrder[i] != swarmId[i]:
              wrong=1
          assert wrong==1, "Some of the killed swarms should not have been " \
                            + "killed as they are a legal combination."
                            
      if swarms[swarm]["status"] == 'completed':
          swarmId = swarm.split(".")
          if(len(swarmId)>3):
            # Make sure that the completed swarms are all swarms that should 
            # have been run.
            # The last encoder is the predicted field and the second to last is 
            # the current new addition
            for i in range(len(swarmId)-3):
              if correctOrder[i] != swarmId[i]:
                assert False ,  "Some of the completed swarms should not have " \
                          "finished as they are illegal combinations"
      if swarms[swarm]["status"] == 'active':
        assert False ,  "Some swarms are still active at the end of hypersearch"

    pass


  def testSmartSpeculationSpatialClassification(self, onCluster=True, 
                                                env=None, **kwargs):
    """ Test that smart speculation does the right thing with spatial
    classification models. This also applies to temporal models where the
    predicted field is optional (or excluded) since Hypersearch treats them
    the same. 
    """

    self._printTestHeader()
    expDir = os.path.join(g_myEnv.testSrcExpDir, 
                          'smart_speculation_spatial_classification')

    # Test it out
    if env is None:
      env = dict()
    env["NTA_TEST_numIterations"] = '99'
    env["NTA_CONF_PROP_nupic_hypersearch_swarmMaturityWindow"] = \
                         '%d' % (g_repeatableSwarmMaturityWindow)

    env["NTA_CONF_PROP_nupic_hypersearch_minParticlesPerSwarm"] = \
                         '%d' % (1)


    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
           = self.runPermutations(expDir,
                                  hsImp='v2',
                                  loggingLevel=g_myEnv.options.logLevel,
                                  onCluster=onCluster,
                                  env=env,
                                  maxModels=None,
                                  maxNumWorkers=5,
                                  dummyModel={'iterations':200},
                                  **kwargs)

    # Get the worker state
    cjDAO = ClientJobsDAO.get()
    jobInfoStr = cjDAO.jobGetFields(jobID, ['results','engWorkerState'])
    jobResultsStr = jobInfoStr[0]
    engState = jobInfoStr[1]
    engState = json.loads(engState)
    swarms = engState["swarms"]
    jobResults = json.loads(jobResultsStr)
    bestModel = cjDAO.modelsInfo([jobResults["bestModel"]])[0]
    params = json.loads(bestModel.params)
    
    
    # Make sure that the only non-killed models are the ones that would have been
    # run without speculation
    prefix = 'modelParams|sensorParams|encoders|'
    correctOrder = ["A","B","C"]
    correctOrder = [prefix + x for x in correctOrder]
    for swarm in swarms:
      if swarms[swarm]["status"] == 'killed':
        swarmId = swarm.split(".")
        if(len(swarmId) > 1):
          # Make sure that the best encoder is not in this swarm
          if correctOrder[0] in swarmId:
            raise RuntimeError("Some of the killed swarms should not have been "
                            "killed as they are a legal combination.")
                            
      elif swarms[swarm]["status"] == 'completed':
        swarmId = swarm.split(".")
        if(len(swarmId) >= 2):
          # Make sure that the completed swarms are all swarms that should 
          # have been run.
          for i in range(len(swarmId)-1):
            if correctOrder[i] != swarmId[i]:
              raise RuntimeError("Some of the completed swarms should not have "
                        "finished as they are illegal combinations")
      
      elif swarms[swarm]["status"] == 'active':
        raise RuntimeError("Some swarms are still active at the end of "
                           "hypersearch")


  def testFieldBranching(self, onCluster=True, env=None, **kwargs):
    """ Try running a simple permutations
    """

    self._printTestHeader()
    expDir = os.path.join(g_myEnv.testSrcExpDir, 'max_branching_temporal')

    # Test it out
    if env is None:
      env = dict()
    env["NTA_TEST_numIterations"] = '99'
    env["NTA_CONF_PROP_nupic_hypersearch_swarmMaturityWindow"] = \
                         '%d' % (g_repeatableSwarmMaturityWindow)

    env["NTA_CONF_PROP_nupic_hypersearch_max_field_branching"] = \
                         '%d' % (4)
    env["NTA_CONF_PROP_nupic_hypersearch_min_field_contribution"] = \
                         '%f' % (-20.0)
    env["NTA_CONF_PROP_nupic_hypersearch_minParticlesPerSwarm"] = \
                         '%d' % (2)


    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
           = self.runPermutations(expDir,
                                  hsImp='v2',
                                  loggingLevel=g_myEnv.options.logLevel,
                                  onCluster=onCluster,
                                  env=env,
                                  maxModels=None,
                                  dummyModel={'iterations':200},
                                  **kwargs)

    # Get the field contributions from the hypersearch results dict
    cjDAO = ClientJobsDAO.get()
    jobResultsStr = cjDAO.jobGetFields(jobID, ['results'])[0]
    jobResults = json.loads(jobResultsStr)
    bestModel = cjDAO.modelsInfo([jobResults["bestModel"]])[0]
    params = json.loads(bestModel.params)
    
    prefix = 'modelParams|sensorParams|encoders|'
    expectedSwarmId = prefix + ('.' + prefix).join([
            'attendance', 'home_winloss', 'timestamp_dayOfWeek',
            'timestamp_timeOfDay', 'visitor_winloss'])
    assert params["particleState"]["swarmId"] == expectedSwarmId, \
                  params["particleState"]["swarmId"]
    assert bestModel.optimizedMetric == 432, bestModel.optimizedMetric

    env["NTA_CONF_PROP_nupic_hypersearch_max_field_branching"] = \
                         '%d' % (3)

    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
           = self.runPermutations(expDir,
                                  hsImp='v2',
                                  loggingLevel=g_myEnv.options.logLevel,
                                  onCluster=onCluster,
                                  env=env,
                                  maxModels=None,
                                  dummyModel={'iterations':200},
                                  **kwargs)

    # Get the field contributions from the hypersearch results dict
    cjDAO = ClientJobsDAO.get()
    jobResultsStr = cjDAO.jobGetFields(jobID, ['results'])[0]
    jobResults = json.loads(jobResultsStr)
    bestModel = cjDAO.modelsInfo([jobResults["bestModel"]])[0]
    params = json.loads(bestModel.params)

    prefix = 'modelParams|sensorParams|encoders|'
    expectedSwarmId = prefix + ('.' + prefix).join([
            'attendance', 'home_winloss', 'timestamp_timeOfDay', 
            'visitor_winloss'])
    assert params["particleState"]["swarmId"] == expectedSwarmId, \
                  params["particleState"]["swarmId"]

    assert bestModel.optimizedMetric == 465, bestModel.optimizedMetric

    env["NTA_CONF_PROP_nupic_hypersearch_max_field_branching"] = \
                         '%d' % (5)

    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
           = self.runPermutations(expDir,
                                  hsImp='v2',
                                  loggingLevel=g_myEnv.options.logLevel,
                                  onCluster=onCluster,
                                  env=env,
                                  maxModels=None,
                                  dummyModel={'iterations':200},
                                  **kwargs)

    # Get the field contributions from the hypersearch results dict
    cjDAO = ClientJobsDAO.get()
    jobResultsStr = cjDAO.jobGetFields(jobID, ['results'])[0]
    jobResults = json.loads(jobResultsStr)
    bestModel = cjDAO.modelsInfo([jobResults["bestModel"]])[0]
    params = json.loads(bestModel.params)

    prefix = 'modelParams|sensorParams|encoders|'
    expectedSwarmId = prefix + ('.' + prefix).join([
            'attendance', 'home_winloss', 'precip', 'timestamp_dayOfWeek',
            'timestamp_timeOfDay', 'visitor_winloss'])
    assert params["particleState"]["swarmId"] == expectedSwarmId, \
                  params["particleState"]["swarmId"]

    assert bestModel.optimizedMetric == 390, bestModel.optimizedMetric

    #Find best combo with 3 fields
    env["NTA_CONF_PROP_nupic_hypersearch_max_field_branching"] = \
                         '%d' % (0)

    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
           = self.runPermutations(expDir,
                                  hsImp='v2',
                                  loggingLevel=g_myEnv.options.logLevel,
                                  onCluster=onCluster,
                                  env=env,
                                  maxModels=100,
                                  dummyModel={'iterations':200},
                                  **kwargs)

    # Get the field contributions from the hypersearch results dict
    cjDAO = ClientJobsDAO.get()
    jobResultsStr = cjDAO.jobGetFields(jobID, ['results'])[0]
    jobResults = json.loads(jobResultsStr)
    bestModel = cjDAO.modelsInfo([jobResults["bestModel"]])[0]
    params = json.loads(bestModel.params)

    prefix = 'modelParams|sensorParams|encoders|'
    expectedSwarmId = prefix + ('.' + prefix).join([
            'attendance', 'daynight', 'visitor_winloss'])
    assert params["particleState"]["swarmId"] == expectedSwarmId, \
                  params["particleState"]["swarmId"]

    assert bestModel.optimizedMetric == 406, bestModel.optimizedMetric



    return


  def testFieldThreshold(self, onCluster=True, env=None, **kwargs):
    """ Test minimum field contribution threshold for a field to be included in further sprints
    """

    self._printTestHeader()
    inst = OneNodeTests(self._testMethodName)
    return inst.testFieldThreshold(onCluster=True) 


  def testFieldContributions(self, onCluster=True, env=None, **kwargs):
    """ Try running a simple permutations
    """

    self._printTestHeader()
    expDir = os.path.join(g_myEnv.testSrcExpDir, 'field_contrib_temporal')

    # Test it out
    if env is None:
      env = dict()
    env["NTA_TEST_numIterations"] = '99'
    env["NTA_CONF_PROP_nupic_hypersearch_swarmMaturityWindow"] = \
                         '%d' % (g_repeatableSwarmMaturityWindow)

    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
           = self.runPermutations(expDir,
                                  hsImp='v2',
                                  loggingLevel=g_myEnv.options.logLevel,
                                  onCluster=onCluster,
                                  env=env,
                                  maxModels=None,
                                  **kwargs)

    # Get the field contributions from the hypersearch results dict
    cjDAO = ClientJobsDAO.get()
    jobResultsStr = cjDAO.jobGetFields(jobID, ['results'])[0]
    jobResults = json.loads(jobResultsStr)

    actualFieldContributions = jobResults['fieldContributions']
    print "Actual field contributions:", actualFieldContributions
    
    expectedFieldContributions = {'consumption': 0.0, 
                                  'address': 0.0,
                                  'timestamp_timeOfDay': 20.0,
                                  'timestamp_dayOfWeek': 50.0,
                                  'gym': 10.0}
    
    
    for key, value in expectedFieldContributions.items():
      self.assertEqual(actualFieldContributions[key], value, 
                       "actual field contribution from field '%s' does not "
                       "match the expected value of %f" % (key, value))
    return


  def testCLAModelV2(self):
    """ Try running a simple permutations through a real CLA model
    """

    self._printTestHeader()
    inst = OneNodeTests(self._testMethodName)
    return inst.testCLAModelV2(onCluster=True, maxModels=4)


  def testCLAMultistepModel(self):
    """ Try running a simple permutations through a real CLA model that
    uses multistep
    """

    self._printTestHeader()
    inst = OneNodeTests(self._testMethodName)
    return inst.testCLAMultistepModel(onCluster=True, maxModels=4)


  def testLegacyCLAMultistepModel(self):
    """ Try running a simple permutations through a real CLA model that
    uses multistep
    """

    self._printTestHeader()
    inst = OneNodeTests(self._testMethodName)
    return inst.testLegacyCLAMultistepModel(onCluster=True, maxModels=4)


  def testSimpleV2VariableWaits(self):
    """ Try running a simple permutations where certain field combinations
    take longer to complete, this lets us test that we successfully kill
    models in bad swarms that are still running.
    """

    self._printTestHeader()

    # NTA_TEST_variableWaits and NTA_TEST_numIterations are watched by the
    #  dummyModelParams() method of the permutations.py file
    # NTA_TEST_numIterations
    env = dict()
    env["NTA_TEST_variableWaits"] ='True'
    env["NTA_TEST_numIterations"] = '100'

    inst = OneNodeTests('testSimpleV2')
    return inst.testSimpleV2(onCluster=True, env=env)


  def testOrphanedModel(self, modelRange=(0,2)):
    """ Run a worker on a model for a while, then have it exit before the
    model finishes. Then, run another worker, which should detect the orphaned
    model.
    """
    self._printTestHeader()
    expDir = os.path.join(g_myEnv.testSrcExpDir, 'simpleV2')

    # NTA_TEST_numIterations is watched by the dummyModelParams() method of
    #  the permutations file.
    # NTA_TEST_sysExitModelRange  is watched by the dummyModelParams() method of
    #  the permutations file. It tells it to do a sys.exit() after so many
    #  iterations.
    env = dict()
    env["NTA_TEST_numIterations"] = '99'
    env["NTA_TEST_sysExitModelRange"] = '%d,%d' % (modelRange[0], modelRange[1])
    env["NTA_CONF_PROP_nupic_hypersearch_modelOrphanIntervalSecs"] = '1'
    env["NTA_CONF_PROP_nupic_hypersearch_swarmMaturityWindow"] \
            =  '%d' % (g_repeatableSwarmMaturityWindow)

    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
         = self.runPermutations(expDir,
                                hsImp='v2',
                                loggingLevel=g_myEnv.options.logLevel,
                                maxModels=500,
                                onCluster=True,
                                env=env,
                                waitForCompletion=True,
                                maxNumWorkers=4,
                                )

    self.assertEqual(minErrScore, 20)
    self.assertLess(len(resultInfos), 500)
    return


  def testTwoOrphanedModels(self, modelRange=(0,2)):
    """ Test behavior when a worker marks 2 models orphaned at the same time. 
    """

    self._printTestHeader()
    expDir = os.path.join(g_myEnv.testSrcExpDir, 'oneField')

    # NTA_TEST_numIterations is watched by the dummyModelParams() method of
    #  the permutations file.
    # NTA_TEST_sysExitModelRange  is watched by the dummyModelParams() method of
    #  the permutations file. It tells it to do a sys.exit() after so many
    #  iterations.
    env = dict()
    env["NTA_TEST_numIterations"] = '99'
    env["NTA_TEST_delayModelRange"] = '%d,%d' % (modelRange[0], modelRange[1])
    env["NTA_CONF_PROP_nupic_hypersearch_modelOrphanIntervalSecs"] = '1'
    env["NTA_CONF_PROP_nupic_hypersearch_swarmMaturityWindow"] \
            =  '%d' % (g_repeatableSwarmMaturityWindow)

    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
         = self.runPermutations(expDir,
                                hsImp='v2',
                                loggingLevel=g_myEnv.options.logLevel,
                                maxModels=100,
                                onCluster=True,
                                env=env,
                                waitForCompletion=True,
                                maxNumWorkers=4,
                                )

    self.assertEqual(minErrScore, 50)
    self.assertLess(len(resultInfos), 100)
    return


  def testOrphanedModelGen1(self):
    """ Run a worker on a model for a while, then have it exit before the
    model finishes. Then, run another worker, which should detect the orphaned
    model.
    """

    self._printTestHeader()
    inst = MultiNodeTests(self._testMethodName)
    return inst.testOrphanedModel(modelRange=(10,11))


  def testOrphanedModelMaxModels(self):
    """ Test to make sure that the maxModels parameter doesn't include
    orphaned models. Run a test with maxModels set to 2, where one becomes
    orphaned. At the end, there should be 3 models in the models table, one
    of which will be the new model that adopted the orphaned model
    """
    self._printTestHeader()
    expDir = os.path.join(g_myEnv.testSrcExpDir, 'dummyV2')

    numModels = 5

    env = dict()
    env["NTA_CONF_PROP_nupic_hypersearch_modelOrphanIntervalSecs"] = '3'
    env['NTA_TEST_max_num_models']=str(numModels)

    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
    = self.runPermutations(expDir,
                          hsImp='v2',
                          loggingLevel=g_myEnv.options.logLevel,
                          maxModels=numModels,
                          env=env,
                          onCluster=True,
                          waitForCompletion=True,
                          dummyModel={'metricValue':  ['25','50'],
                                      'sysExitModelRange': '0, 1',
                                      'iterations': 20,
                                      }
                          )

    cjDB = ClientJobsDAO.get()

    self.assertGreaterEqual(len(resultInfos), numModels+1)
    completionReasons = [x.completionReason for x in resultInfos]
    self.assertGreaterEqual(completionReasons.count(cjDB.CMPL_REASON_EOF), numModels)
    self.assertGreaterEqual(completionReasons.count(cjDB.CMPL_REASON_ORPHAN), 1)


  def testOrphanedModelConnection(self):
    """Test for the correct behavior when a model uses a different connection id
    than what is stored in the db. The correct behavior is for the worker to log
    this as a warning and move on to a new model"""

    self._printTestHeader()

    # -----------------------------------------------------------------------
    # Trigger "Using connection from another worker" exception inside
    # ModelRunner
    # -----------------------------------------------------------------------
    expDir = os.path.join(g_myEnv.testSrcExpDir, 'dummy_multi_v2')

    numModels = 2

    env = dict()
    env["NTA_CONF_PROP_nupic_hypersearch_modelOrphanIntervalSecs"] = '1'

    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
    = self.runPermutations(expDir,
                          hsImp='v2',
                          loggingLevel=g_myEnv.options.logLevel,
                          maxModels=numModels,
                          env=env,
                          onCluster=True,
                          waitForCompletion=True,
                          dummyModel={'metricValue':  ['25','50'],
                                      'sleepModelRange': '0, 1:5',
                                      'iterations': 20,
                                      }
                          )

    cjDB = ClientJobsDAO.get()

    self.assertGreaterEqual(len(resultInfos), numModels,
                     "%d were run. Expecting %s"%(len(resultInfos), numModels+1))
    completionReasons = [x.completionReason for x in resultInfos]
    self.assertGreaterEqual(completionReasons.count(cjDB.CMPL_REASON_EOF), numModels)
    self.assertGreaterEqual(completionReasons.count(cjDB.CMPL_REASON_ORPHAN), 1)


  def testErredModel(self, modelRange=(6,7)):
    """ Run a worker on a model for a while, then have it exit before the
    model finishes. Then, run another worker, which should detect the orphaned
    model.
    """

    self._printTestHeader()
    inst = OneNodeTests(self._testMethodName)
    return inst.testErredModel(onCluster=True)


  def testJobFailModel(self):
    """ Run a worker on a model for a while, then have it exit before the
    model finishes. Then, run another worker, which should detect the orphaned
    model.
    """

    self._printTestHeader()
    inst = OneNodeTests(self._testMethodName)
    return inst.testJobFailModel(onCluster=True)


  def testTooManyErredModels(self, modelRange=(5,10)):
    """ Run a worker on a model for a while, then have it exit before the
    model finishes. Then, run another worker, which should detect the orphaned
    model.
    """

    self._printTestHeader()
    inst = OneNodeTests(self._testMethodName)
    return inst.testTooManyErredModels(onCluster=True)


  def testSpatialClassification(self):
    """ Try running a simple permutations
    """

    self._printTestHeader()
    inst = OneNodeTests(self._testMethodName)
    return inst.testSpatialClassification(onCluster=True) #, maxNumWorkers=7)


  def testAlwaysInputPredictedField(self):

    self._printTestHeader()
    inst = OneNodeTests(self._testMethodName)
    return inst.testAlwaysInputPredictedField(onCluster=True) 


  def testFieldThresholdNoPredField(self):

    self._printTestHeader()
    inst = OneNodeTests(self._testMethodName)
    return inst.testFieldThresholdNoPredField(onCluster=True) 



class ModelMaturityTests(ExperimentTestBaseClass):
  """
  """
  # AWS tests attribute required for tagging via automatic test discovery via
  # nosetests
  engineAWSClusterTest=True


  def setUp(self):
    # Ignore the global hypersearch version setting. Always test hypersearch v2
    hsVersion = 2
    self.expDir = os.path.join(g_myEnv.testSrcExpDir, 'dummyV%d' %hsVersion)
    self.hsImp = "v%d" % hsVersion

    self.env = {'NTA_CONF_PROP_nupic_hypersearch_enableModelTermination':'0',
                'NTA_CONF_PROP_nupic_hypersearch_enableModelMaturity':'1',
                'NTA_CONF_PROP_nupic_hypersearch_maturityMaxSlope':'0.1',
                'NTA_CONF_PROP_nupic_hypersearch_enableSwarmTermination':'0',
                'NTA_CONF_PROP_nupic_hypersearch_bestModelMinRecords':'0'}


  def testMatureInterleaved(self):
    """ Test to make sure that the best model continues running even when it has
    matured. The 2nd model (constant) will be marked as mature first and will
    continue to run till the end. The 2nd model reaches maturity and should
    stop before all the records are consumed, and should be the best model
    because it has a lower error
    """
    self._printTestHeader()
    self.expDir =  os.path.join(g_myEnv.testSrcExpDir,
                               'dummy_multi_v%d' % 2)
    self.env['NTA_TEST_max_num_models'] = '2'
    jobID,_,_,_,_ = self.runPermutations(self.expDir, hsImp=self.hsImp, maxModels=2,
                                loggingLevel = g_myEnv.options.logLevel,
                                env = self.env,
                                onCluster = True,
                                dummyModel={'metricFunctions':
                                              ['lambda x: -10*math.log10(x+1) +100',
                                               'lambda x: 100.0'],

                                            'delay': [2.0,
                                                      0.0 ],
                                            'waitTime':[0.05,
                                                        0.01],
                                            'iterations':500,
                                            'experimentDirectory':self.expDir,
                                })

    cjDB = ClientJobsDAO.get()

    modelIDs, records, completionReasons, matured = \
                    zip(*self.getModelFields( jobID, ['numRecords',
                                                           'completionReason',
                                                            'engMatured']))

    results = cjDB.jobGetFields(jobID, ['results'])[0]
    results = json.loads(results)

    self.assertEqual(results['bestModel'], modelIDs[0])

    self.assertEqual(records[1], 500)
    self.assertTrue(records[0] > 100 and records[0] < 500,
                    "Model 2 num records: 100 < %d < 500 " % records[1])

    self.assertEqual(completionReasons[1], cjDB.CMPL_REASON_EOF)
    self.assertEqual(completionReasons[0], cjDB.CMPL_REASON_STOPPED)

    self.assertTrue(matured[0], True)


  def testConstant(self):
    """ Sanity check to make sure that when only 1 model is running, it continues
    to run even when it has reached maturity """
    self._printTestHeader()
    jobID,_,_,_,_ = self.runPermutations(self.expDir, hsImp=self.hsImp, maxModels=1,
                                loggingLevel = g_myEnv.options.logLevel,
                                env = self.env,
                                dummyModel={'metricFunctions':
                                              ['lambda x: 100'],
                                            'iterations':350,
                                            'experimentDirectory':self.expDir,
                                })


    cjDB = ClientJobsDAO.get()

    modelIDs = cjDB.jobGetModelIDs(jobID)

    dbResults = cjDB.modelsGetFields(modelIDs, ['numRecords', 'completionReason',
                                                'engMatured'])
    modelIDs = [x[0] for x in dbResults]
    records = [x[1][0] for x in dbResults]
    completionReasons = [x[1][1] for x in dbResults]
    matured = [x[1][2] for x in dbResults]

    results = cjDB.jobGetFields(jobID, ['results'])[0]
    results = json.loads(results)

    self.assertEqual(results['bestModel'], min(modelIDs))
    self.assertEqual(records[0], 350)
    self.assertEqual(completionReasons[0], cjDB.CMPL_REASON_EOF)
    self.assertEqual(matured[0], True)


  def getModelFields(self, jobID, fields):
    cjDB = ClientJobsDAO.get()
    modelIDs = cjDB.jobGetModelIDs(jobID)
    modelParams = cjDB.modelsGetFields(modelIDs, ['params']+fields)
    modelIDs = [e[0] for e in modelParams]

    modelOrders = [json.loads(e[1][0])['structuredParams']['__model_num'] for e in modelParams]
    modelFields = []

    for f in xrange(len(fields)):
      modelFields.append([e[1][f+1] for e in modelParams])

    modelInfo = zip(modelOrders, modelIDs, *tuple(modelFields))
    modelInfo.sort(key=lambda info:info[0])

    return [e[1:] for e in sorted(modelInfo, key=lambda info:info[0])]



class SwarmTerminatorTests(ExperimentTestBaseClass):
  """
  """
  # AWS tests attribute required for tagging via automatic test discovery via
  # nosetests
  engineAWSClusterTest=True


  def setUp(self):
    self.env = {'NTA_CONF_PROP_nupic_hypersearch_enableModelMaturity':'0',
                'NTA_CONF_PROP_nupic_hypersearch_enableModelTermination':'0',
                'NTA_CONF_PROP_nupic_hypersearch_enableSwarmTermination':'1',
                'NTA_TEST_recordSwarmTerminations':'1'}


  def testSimple(self, useCluster=False):
    """Run with one really bad swarm to see if terminator picks it up correctly"""

    if not g_myEnv.options.runInProc:
      self.skipTest("Skipping One Node test since runInProc is not specified")
    self._printTestHeader()
    expDir = os.path.join(g_myEnv.testSrcExpDir, 'swarm_v2')

    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
         = self.runPermutations(expDir,
                                hsImp='v2',
                                loggingLevel=g_myEnv.options.logLevel,
                                maxModels=None,
                                onCluster=useCluster,
                                env=self.env,
                                dummyModel={'iterations':200})

    cjDB = ClientJobsDAO.get()
    jobResultsStr = cjDB.jobGetFields(jobID, ['results'])[0]
    jobResults = json.loads(jobResultsStr)
    terminatedSwarms = jobResults['terminatedSwarms']

    swarmMaturityWindow = int(configuration.Configuration.get(
        'nupic.hypersearch.swarmMaturityWindow'))

    prefix = 'modelParams|sensorParams|encoders|'
    for swarm, (generation, scores) in terminatedSwarms.iteritems():
      if prefix + 'gym' in swarm.split('.'):
        self.assertEqual(generation, swarmMaturityWindow-1)
      else:
        self.assertEqual(generation, swarmMaturityWindow-1+4)


  def testMaturity(self, useCluster=False):
    if not g_myEnv.options.runInProc:
      self.skipTest("Skipping One Node test since runInProc is not specified")
    self._printTestHeader()
    self.env['NTA_CONF_PROP_enableSwarmTermination'] = '0'
    expDir = os.path.join(g_myEnv.testSrcExpDir, 'swarm_maturity_v2')

    (jobID, jobInfo, resultInfos, metricResults, minErrScore) \
         = self.runPermutations(expDir,
                                hsImp='v2',
                                loggingLevel=g_myEnv.options.logLevel,
                                maxModels=None,
                                onCluster=useCluster,
                                env=self.env,
                                dummyModel={'iterations':200})

    cjDB = ClientJobsDAO.get()
    jobResultsStr = cjDB.jobGetFields(jobID, ['results'])[0]
    jobResults = json.loads(jobResultsStr)
    terminatedSwarms = jobResults['terminatedSwarms']

    swarmMaturityWindow = int(configuration.Configuration.get(
        'nupic.hypersearch.swarmMaturityWindow'))

    prefix = 'modelParams|sensorParams|encoders|'
    for swarm, (generation, scores) in terminatedSwarms.iteritems():
      encoders = swarm.split('.')
      if prefix + 'gym' in encoders:
        self.assertEqual(generation, swarmMaturityWindow-1 + 3)

      elif prefix + 'address' in encoders:
        self.assertEqual(generation, swarmMaturityWindow-1)

      else:
        self.assertEqual(generation, swarmMaturityWindow-1 + 7)


  def testSimpleMN(self):
    self.testSimple(useCluster=True)


  def testMaturityMN(self):
    self.testMaturity(useCluster=True)



def getHypersearchWinningModelID(jobID):
  """
  Parameters:
  -------------------------------------------------------------------
  jobID:            jobID of successfully-completed Hypersearch job
  
  retval:           modelID of the winning model
  """
  
  cjDAO = ClientJobsDAO.get()
  jobResults = cjDAO.jobGetFields(jobID, ['results'])[0]
  print "Hypersearch job results: %r" % (jobResults,)
  jobResults = json.loads(jobResults)
  return jobResults['bestModel']



def _executeExternalCmdAndReapStdout(args):
  """
  args:     Args list as defined for the args parameter in subprocess.Popen()

  Returns:  result dicionary:
              {
                'exitStatus':<exit-status-of-external-command>,
                'stdoutData':"string",
                'stderrData':"string"
              }
  """

  _debugOut(("_executeExternalCmdAndReapStdout: Starting...\n<%s>") % \
                (args,))

  p = subprocess.Popen(args,
                       env=os.environ,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
  _debugOut(("Process started for <%s>") % (args,))

  (stdoutData, stderrData) = p.communicate()
  _debugOut(("Process completed for <%s>: exit status=%s, stdoutDataType=%s, " + \
             "stdoutData=<%s>, stderrData=<%s>") % \
                (args, p.returncode, type(stdoutData), stdoutData, stderrData))

  result = dict(
    exitStatus = p.returncode,
    stdoutData = stdoutData,
    stderrData = stderrData,
  )

  _debugOut(("_executeExternalCmdAndReapStdout for <%s>: result=\n%s") % \
                (args, pprint.pformat(result, indent=4)))

  return result



def _debugOut(text):
  global g_debug
  if g_debug:
    print text
    sys.stdout.flush()

  return



def _getTestList():
  """ Get the list of tests that can be run from this module"""

  suiteNames = [
                'OneNodeTests', 
                'MultiNodeTests',
                'ModelMaturityTests',
                'SwarmTerminatorTests',
               ]
		
  testNames = []
  for suite in suiteNames:
    for f in dir(eval(suite)):
      if f.startswith('test'):
        testNames.append('%s.%s' % (suite, f))

  return testNames

class _ArgParser(object):
  """Class which handles command line arguments and arguments passed to the test
  """
  args = []
  
  @classmethod
  def _processArgs(cls):
    """ 
    Parse our command-line args/options and strip them from sys.argv
    Returns the tuple (parsedOptions, remainingArgs)
    """
    helpString = \
    """%prog [options...] [-- unittestoptions...] [suitename.testname | suitename]
    Run the Hypersearch unit tests. To see unit test framework options, enter:
    python %prog -- --help

    Example usages:
      python %prog MultiNodeTests
      python %prog MultiNodeTests.testOrphanedModel
      python %prog -- MultiNodeTests.testOrphanedModel
      python %prog -- --failfast
      python %prog -- --failfast OneNodeTests.testOrphanedModel

    Available suitename.testnames: """

    # Update help string
    allTests = _getTestList()
    for test in allTests:
      helpString += "\n    %s" % (test)

    # ============================================================================
    # Process command line arguments
    parser = OptionParser(helpString,conflict_handler="resolve")


    parser.add_option("--verbosity", default=0, type="int",
          help="Verbosity level, either 0, 1, 2, or 3 [default: %default].")

    parser.add_option("--runInProc", action="store_true", default=False,
        help="Run inProc tests, currently inProc are not being run by default "
             " running. [default: %default].")

    parser.add_option("--logLevel", action="store", type="int",
          default=logging.INFO,
          help="override default log level. Pass in an integer value that "
          "represents the desired logging level (10=logging.DEBUG, "
          "20=logging.INFO, etc.) [default: %default].")

    parser.add_option("--hs", dest="hsVersion", default=2, type='int',
                      help=("Hypersearch version (only 2 supported; 1 was "
                            "deprecated) [default: %default]."))
    return parser.parse_args(args=cls.args)

  @classmethod
  def parseArgs(cls):
    """ Returns the test arguments after parsing 
    """
    return cls._processArgs()[0]
  
  @classmethod
  def consumeArgs(cls):
    """ Consumes the test arguments and returns the remaining arguments meant
    for unittest.man
    """
    return cls._processArgs()[1]



def setUpModule():
  print "\nCURRENT DIRECTORY:", os.getcwd()

  initLogging(verbose=True)
  
  global g_myEnv
  # Setup our environment
  g_myEnv = MyTestEnvironment()

if __name__ == '__main__':
  # Form the command line for the unit test framework
  # Consume test specific arguments and pass remaining to unittest.main
  _ArgParser.args = sys.argv[1:] 
  args = [sys.argv[0]] + _ArgParser.consumeArgs()

  # Run the tests if called using python
  unittest.main(argv=args)
