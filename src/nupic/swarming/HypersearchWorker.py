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
import pprint
from optparse import OptionParser
import random
import logging
import json
import hashlib
import itertools
import StringIO
import traceback

from nupic.support import initLogging
from nupic.support.configuration import Configuration
from nupic.swarming.hypersearch.ExtendedLogger import ExtendedLogger
from nupic.swarming.hypersearch.errorcodes import ErrorCodes
from nupic.swarming.utils import clippedObj, validate
from nupic.database.ClientJobsDAO import ClientJobsDAO
from HypersearchV2 import HypersearchV2



class HypersearchWorker(object):
  """ The HypersearchWorker is responsible for evaluating one or more models
  within a specific Hypersearch job.

  One or more instances of this object are launched by the engine, each in a
  separate process. When running within Hadoop, each instance is run within a
  separate Hadoop Map Task. Each instance gets passed the parameters of the
  hypersearch via a reference to a search job request record in a "jobs" table
  within a database.

  From there, each instance will try different models, based on the search
  parameters and share it's results via a "models" table within the same
  database.

  The general flow for each worker is this:
  while more models to evaluate:
    pick a model based on information about the job and the other models that
      have already been evaluated.
    mark the model as "in progress" in the "models" table.
    evaluate the model, storing metrics on performance periodically back to
      the model's entry in the "models" table.
    mark the model as "completed" in the "models" table

  """


  def __init__(self, options, cmdLineArgs):
    """ Instantiate the Hypersearch worker

    Parameters:
    ---------------------------------------------------------------------
    options:      The command line options. See the main() method for a
                    description of these options
    cmdLineArgs:  Copy of the command line arguments, so we can place them
                    in the log
    """

    # Save options
    self._options = options

    # Instantiate our logger
    self.logger = logging.getLogger(".".join(
        ['com.numenta.nupic.swarming', self.__class__.__name__]))


    # Override log level?
    if options.logLevel is not None:
      self.logger.setLevel(options.logLevel)


    self.logger.info("Launched with command line arguments: %s" %
                      str(cmdLineArgs))

    self.logger.debug("Env variables: %s" % (pprint.pformat(os.environ)))
    #self.logger.debug("Value of nupic.hypersearch.modelOrphanIntervalSecs: %s" \
    #          % Configuration.get('nupic.hypersearch.modelOrphanIntervalSecs'))

    # Init random seed
    random.seed(42)

    # This will hold an instance of a Hypersearch class which handles
    #  the logic of which models to create/evaluate.
    self._hs = None


    # -------------------------------------------------------------------------
    # These elements form a cache of the update counters we last received for
    # the all models in the database. It is used to determine which models we
    # have to notify the Hypersearch object that the results have changed.

    # This is a dict of modelID -> updateCounter
    self._modelIDCtrDict = dict()

    # This is the above is a list of tuples: (modelID, updateCounter)
    self._modelIDCtrList = []

    # This is just the set of modelIDs (keys)
    self._modelIDSet = set()

    # This will be filled in by run()
    self._workerID = None


  def _processUpdatedModels(self, cjDAO):
    """ For all models that modified their results since last time this method
    was called, send their latest results to the Hypersearch implementation.
    """


    # Get the latest update counters. This returns a list of tuples:
    #  (modelID, updateCounter)
    curModelIDCtrList = cjDAO.modelsGetUpdateCounters(self._options.jobID)
    if len(curModelIDCtrList) == 0:
      return

    self.logger.debug("current modelID/updateCounters: %s" \
                      % (str(curModelIDCtrList)))
    self.logger.debug("last modelID/updateCounters: %s" \
                      % (str(self._modelIDCtrList)))

    # --------------------------------------------------------------------
    # Find out which ones have changed update counters. Since these are models
    # that the Hypersearch implementation already knows about, we don't need to
    # send params or paramsHash
    curModelIDCtrList = sorted(curModelIDCtrList)
    numItems = len(curModelIDCtrList)

    # Each item in the list we are filtering contains:
    #  (idxIntoModelIDCtrList, (modelID, curCtr), (modelID, oldCtr))
    # We only want to keep the ones where the oldCtr != curCtr
    changedEntries = filter(lambda x:x[1][1] != x[2][1],
                      itertools.izip(xrange(numItems), curModelIDCtrList,
                                     self._modelIDCtrList))

    if len(changedEntries) > 0:
      # Update values in our cache
      self.logger.debug("changedEntries: %s", str(changedEntries))
      for entry in changedEntries:
        (idx, (modelID, curCtr), (_, oldCtr)) = entry
        self._modelIDCtrDict[modelID] = curCtr
        assert (self._modelIDCtrList[idx][0] == modelID)
        assert (curCtr != oldCtr)
        self._modelIDCtrList[idx][1] = curCtr


      # Tell Hypersearch implementation of the updated results for each model
      changedModelIDs = [x[1][0] for x in changedEntries]
      modelResults = cjDAO.modelsGetResultAndStatus(changedModelIDs)
      for mResult in modelResults:
        results = mResult.results
        if results is not None:
          results = json.loads(results)
        self._hs.recordModelProgress(modelID=mResult.modelId,
                     modelParams = None,
                     modelParamsHash = mResult.engParamsHash,
                     results = results,
                     completed = (mResult.status == cjDAO.STATUS_COMPLETED),
                     completionReason = mResult.completionReason,
                     matured = mResult.engMatured,
                     numRecords = mResult.numRecords)

    # --------------------------------------------------------------------
    # Figure out which ones are newly arrived and add them to our
    #   cache
    curModelIDSet = set([x[0] for x in curModelIDCtrList])
    newModelIDs = curModelIDSet.difference(self._modelIDSet)
    if len(newModelIDs) > 0:

      # Add new modelID and counters to our cache
      self._modelIDSet.update(newModelIDs)
      curModelIDCtrDict = dict(curModelIDCtrList)

      # Get the results for each of these models and send them to the
      #  Hypersearch implementation.
      modelInfos = cjDAO.modelsGetResultAndStatus(newModelIDs)
      modelInfos.sort()
      modelParamsAndHashs = cjDAO.modelsGetParams(newModelIDs)
      modelParamsAndHashs.sort()

      for (mResult, mParamsAndHash) in itertools.izip(modelInfos,
                                                  modelParamsAndHashs):

        modelID = mResult.modelId
        assert (modelID == mParamsAndHash.modelId)

        # Update our cache of IDs and update counters
        self._modelIDCtrDict[modelID] = curModelIDCtrDict[modelID]
        self._modelIDCtrList.append([modelID, curModelIDCtrDict[modelID]])

        # Tell the Hypersearch implementation of the new model
        results = mResult.results
        if results is not None:
          results = json.loads(mResult.results)

        self._hs.recordModelProgress(modelID = modelID,
            modelParams = json.loads(mParamsAndHash.params),
            modelParamsHash = mParamsAndHash.engParamsHash,
            results = results,
            completed = (mResult.status == cjDAO.STATUS_COMPLETED),
            completionReason = (mResult.completionReason),
            matured = mResult.engMatured,
            numRecords = mResult.numRecords)




      # Keep our list sorted
      self._modelIDCtrList.sort()


  def run(self):
    """ Run this worker.

    Parameters:
    ----------------------------------------------------------------------
    retval:     jobID of the job we ran. This is used by unit test code
                  when calling this working using the --params command
                  line option (which tells this worker to insert the job
                  itself).
    """
    # Easier access to options
    options = self._options

    # ---------------------------------------------------------------------
    # Connect to the jobs database
    self.logger.info("Connecting to the jobs database")
    cjDAO = ClientJobsDAO.get()

    # Get our worker ID
    self._workerID = cjDAO.getConnectionID()

    if options.clearModels:
      cjDAO.modelsClearAll()

    # -------------------------------------------------------------------------
    # if params were specified on the command line, insert a new job using
    #  them.
    if options.params is not None:
      options.jobID = cjDAO.jobInsert(client='hwTest', cmdLine="echo 'test mode'",
                  params=options.params, alreadyRunning=True,
                  minimumWorkers=1, maximumWorkers=1,
                  jobType = cjDAO.JOB_TYPE_HS)
    if options.workerID is not None:
      wID = options.workerID
    else:
      wID = self._workerID
    
    buildID = Configuration.get('nupic.software.buildNumber', 'N/A')
    logPrefix = '<BUILDID=%s, WORKER=HW, WRKID=%s, JOBID=%s> ' % \
                (buildID, wID, options.jobID)
    ExtendedLogger.setLogPrefix(logPrefix)

    # ---------------------------------------------------------------------
    # Get the search parameters
    # If asked to reset the job status, do that now
    if options.resetJobStatus:
      cjDAO.jobSetFields(options.jobID,
           fields={'workerCompletionReason': ClientJobsDAO.CMPL_REASON_SUCCESS,
                   'cancel': False,
                   #'engWorkerState': None
                   },
           useConnectionID=False,
           ignoreUnchanged=True)
    jobInfo = cjDAO.jobInfo(options.jobID)
    self.logger.info("Job info retrieved: %s" % (str(clippedObj(jobInfo))))


    # ---------------------------------------------------------------------
    # Instantiate the Hypersearch object, which will handle the logic of
    #  which models to create when we need more to evaluate.
    jobParams = json.loads(jobInfo.params)

    # Validate job params
    jsonSchemaPath = os.path.join(os.path.dirname(__file__),
                                  "jsonschema",
                                  "jobParamsSchema.json")
    validate(jobParams, schemaPath=jsonSchemaPath)


    hsVersion = jobParams.get('hsVersion', None)
    if hsVersion == 'v2':
      self._hs = HypersearchV2(searchParams=jobParams, workerID=self._workerID,
              cjDAO=cjDAO, jobID=options.jobID, logLevel=options.logLevel)
    else:
      raise RuntimeError("Invalid Hypersearch implementation (%s) specified" \
                          % (hsVersion))


    # =====================================================================
    # The main loop.
    try:
      exit = False
      numModelsTotal = 0
      print >>sys.stderr, "reporter:status:Evaluating first model..."
      while not exit:

        # ------------------------------------------------------------------
        # Choose a model to evaluate
        batchSize = 10              # How many to try at a time.
        modelIDToRun = None
        while modelIDToRun is None:

          if options.modelID is None:
            # -----------------------------------------------------------------
            # Get the latest results on all running models and send them to
            #  the Hypersearch implementation
            # This calls cjDAO.modelsGetUpdateCounters(), compares the
            # updateCounters with what we have cached, fetches the results for the
            # changed and new models, and sends those to the Hypersearch
            # implementation's self._hs.recordModelProgress() method.
            self._processUpdatedModels(cjDAO)
  
            # --------------------------------------------------------------------
            # Create a new batch of models
            (exit, newModels) = self._hs.createModels(numModels = batchSize)
            if exit:
              break

            # No more models left to create, just loop. The _hs is waiting for
            #   all remaining running models to complete, and may pick up on an
            #  orphan if it detects one.
            if len(newModels) == 0:
              continue
  
            # Try and insert one that we will run
            for (modelParams, modelParamsHash, particleHash) in newModels:
              jsonModelParams = json.dumps(modelParams)
              (modelID, ours) = cjDAO.modelInsertAndStart(options.jobID,
                                  jsonModelParams, modelParamsHash, particleHash)
  
              # Some other worker is already running it, tell the Hypersearch object
              #  so that it doesn't try and insert it again
              if not ours:
                mParamsAndHash = cjDAO.modelsGetParams([modelID])[0]
                mResult = cjDAO.modelsGetResultAndStatus([modelID])[0]
                results = mResult.results
                if results is not None:
                  results = json.loads(results)
  
                modelParams = json.loads(mParamsAndHash.params)
                particleHash = cjDAO.modelsGetFields(modelID, 
                                  ['engParticleHash'])[0]
                particleInst = "%s.%s" % (
                          modelParams['particleState']['id'],
                          modelParams['particleState']['genIdx'])
                self.logger.info("Adding model %d to our internal DB " \
                      "because modelInsertAndStart() failed to insert it: " \
                      "paramsHash=%s, particleHash=%s, particleId='%s'", modelID, 
                      mParamsAndHash.engParamsHash.encode('hex'),
                      particleHash.encode('hex'), particleInst)
                self._hs.recordModelProgress(modelID = modelID,
                      modelParams = modelParams,
                      modelParamsHash = mParamsAndHash.engParamsHash,
                      results = results,
                      completed = (mResult.status == cjDAO.STATUS_COMPLETED),
                      completionReason = mResult.completionReason,
                      matured = mResult.engMatured,
                      numRecords = mResult.numRecords)
              else:
                modelIDToRun = modelID
                break
  
          else:
            # A specific modelID was passed on the command line
            modelIDToRun = int(options.modelID)
            mParamsAndHash = cjDAO.modelsGetParams([modelIDToRun])[0]
            modelParams = json.loads(mParamsAndHash.params)
            modelParamsHash = mParamsAndHash.engParamsHash
            
            # Make us the worker
            cjDAO.modelSetFields(modelIDToRun,
                                     dict(engWorkerConnId=self._workerID))
            if False:
              # Change the hash and params of the old entry so that we can
              #  create a new model with the same params
              for attempt in range(1000):
                paramsHash = hashlib.md5("OrphanParams.%d.%d" % (modelIDToRun,
                                                                 attempt)).digest()
                particleHash = hashlib.md5("OrphanParticle.%d.%d" % (modelIDToRun,
                                                                  attempt)).digest()
                try:
                  cjDAO.modelSetFields(modelIDToRun,
                                           dict(engParamsHash=paramsHash,
                                                engParticleHash=particleHash))
                  success = True
                except:
                  success = False
                if success:
                  break
              if not success:
                raise RuntimeError("Unexpected failure to change paramsHash and "
                                   "particleHash of orphaned model")
              
              (modelIDToRun, ours) = cjDAO.modelInsertAndStart(options.jobID,
                                  mParamsAndHash.params, modelParamsHash)

            
            
            # ^^^ end while modelIDToRun ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

        # ---------------------------------------------------------------
        # We have a model, evaluate it now
        # All done?
        if exit:
          break

        # Run the model now
        self.logger.info("RUNNING MODEL GID=%d, paramsHash=%s, params=%s",
              modelIDToRun, modelParamsHash.encode('hex'), modelParams)

        # ---------------------------------------------------------------------
        # Construct model checkpoint GUID for this model:
        # jobParams['persistentJobGUID'] contains the client's (e.g., API Server)
        # persistent, globally-unique model identifier, which is what we need;
        persistentJobGUID = jobParams['persistentJobGUID']
        assert persistentJobGUID, "persistentJobGUID: %r" % (persistentJobGUID,)

        modelCheckpointGUID = jobInfo.client + "_" + persistentJobGUID + (
          '_' + str(modelIDToRun))


        self._hs.runModel(modelID=modelIDToRun, jobID = options.jobID,
                          modelParams=modelParams, modelParamsHash=modelParamsHash,
                          jobsDAO=cjDAO, modelCheckpointGUID=modelCheckpointGUID)

        # TODO: don't increment for orphaned models
        numModelsTotal += 1

        self.logger.info("COMPLETED MODEL GID=%d; EVALUATED %d MODELs",
          modelIDToRun, numModelsTotal)
        print >>sys.stderr, "reporter:status:Evaluated %d models..." % \
                                    (numModelsTotal)
        print >>sys.stderr, "reporter:counter:HypersearchWorker,numModels,1"

        if options.modelID is not None:
          exit = True
        # ^^^ end while not exit

    finally:
      # Provide Hypersearch instance an opportunity to clean up temporary files
      self._hs.close()

    self.logger.info("FINISHED. Evaluated %d models." % (numModelsTotal))
    print >>sys.stderr, "reporter:status:Finished, evaluated %d models" % (numModelsTotal)
    return options.jobID



helpString = \
"""%prog [options]
This script runs as a Hypersearch worker process. It loops, looking for and
evaluating prospective models from a Hypersearch database.
"""



def main(argv):
  """
  The main function of the HypersearchWorker script. This parses the command
  line arguments, instantiates a HypersearchWorker instance, and then
  runs it.

  Parameters:
  ----------------------------------------------------------------------
  retval:     jobID of the job we ran. This is used by unit test code
                when calling this working using the --params command
                line option (which tells this worker to insert the job
                itself).
  """

  parser = OptionParser(helpString)

  parser.add_option("--jobID", action="store", type="int", default=None,
        help="jobID of the job within the dbTable [default: %default].")

  parser.add_option("--modelID", action="store", type="str", default=None,
        help=("Tell worker to re-run this model ID. When specified, jobID "
         "must also be specified [default: %default]."))

  parser.add_option("--workerID", action="store", type="str", default=None,
        help=("workerID of the scheduler's SlotAgent (GenericWorker) that "
          "hosts this SpecializedWorker [default: %default]."))

  parser.add_option("--params", action="store", default=None,
        help="Create and execute a new hypersearch request using this JSON " \
        "format params string. This is helpful for unit tests and debugging. " \
        "When specified jobID must NOT be specified. [default: %default].")

  parser.add_option("--clearModels", action="store_true", default=False,
        help="clear out the models table before starting [default: %default].")

  parser.add_option("--resetJobStatus", action="store_true", default=False,
        help="Reset the job status before starting  [default: %default].")

  parser.add_option("--logLevel", action="store", type="int", default=None,
        help="override default log level. Pass in an integer value that "
        "represents the desired logging level (10=logging.DEBUG, "
        "20=logging.INFO, etc.) [default: %default].")

  # Evaluate command line arguments
  (options, args) = parser.parse_args(argv[1:])
  if len(args) != 0:
    raise RuntimeError("Expected no command line arguments, but got: %s" % \
                        (args))

  if (options.jobID and options.params):
    raise RuntimeError("--jobID and --params can not be used at the same time")

  if (options.jobID is None and options.params is None):
    raise RuntimeError("Either --jobID or --params must be specified.")

  initLogging(verbose=True)

  # Instantiate the HypersearchWorker and run it
  hst = HypersearchWorker(options, argv[1:])

  # Normal use. This is one of among a number of workers. If we encounter
  #  an exception at the outer loop here, we fail the entire job.
  if options.params is None:
    try:
      jobID = hst.run()

    except Exception, e:
      jobID = options.jobID
      msg = StringIO.StringIO()
      print >>msg, "%s: Exception occurred in Hypersearch Worker: %r" % \
         (ErrorCodes.hypersearchLogicErr, e)
      traceback.print_exc(None, msg)

      completionReason = ClientJobsDAO.CMPL_REASON_ERROR
      completionMsg = msg.getvalue()
      hst.logger.error(completionMsg)

      # If no other worker already marked the job as failed, do so now.
      jobsDAO = ClientJobsDAO.get()
      workerCmpReason = jobsDAO.jobGetFields(options.jobID,
          ['workerCompletionReason'])[0]
      if workerCmpReason == ClientJobsDAO.CMPL_REASON_SUCCESS:
        jobsDAO.jobSetFields(options.jobID, fields=dict(
            cancel=True,
            workerCompletionReason = ClientJobsDAO.CMPL_REASON_ERROR,
            workerCompletionMsg = completionMsg),
            useConnectionID=False,
            ignoreUnchanged=True)


  # Run just 1 worker for the entire job. Used for unit tests that run in
  # 1 process
  else:
    jobID = None
    completionReason = ClientJobsDAO.CMPL_REASON_SUCCESS
    completionMsg = "Success"

    try:
      jobID = hst.run()
    except Exception, e:
      jobID = hst._options.jobID
      completionReason = ClientJobsDAO.CMPL_REASON_ERROR
      completionMsg = "ERROR: %s" % (e,)
      raise
    finally:
      if jobID is not None:
        cjDAO = ClientJobsDAO.get()
        cjDAO.jobSetCompleted(jobID=jobID,
                              completionReason=completionReason,
                              completionMsg=completionMsg)

  return jobID



if __name__ == "__main__":
  logging.setLoggerClass(ExtendedLogger)
  buildID = Configuration.get('nupic.software.buildNumber', 'N/A')
  logPrefix = '<BUILDID=%s, WORKER=HS, WRKID=N/A, JOBID=N/A> ' % buildID
  ExtendedLogger.setLogPrefix(logPrefix)
  
  try:
    main(sys.argv)
  except:
    logging.exception("HypersearchWorker is exiting with unhandled exception; "
                      "argv=%r", sys.argv)
    raise
