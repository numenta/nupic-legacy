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

import json
import time
import logging
import os
import sys
import shutil
import StringIO
import threading
import traceback
from collections import deque

from nupic.swarming.hypersearch import regression
from nupic.swarming.hypersearch.error_codes import ErrorCodes

from nupic.database.client_jobs_dao import ClientJobsDAO
from nupic.frameworks.opf import helpers
from nupic.frameworks.opf.model_factory import ModelFactory
from nupic.frameworks.opf.opf_basic_environment import BasicPredictionLogger
from nupic.frameworks.opf.opf_utils import matchPatterns
from nupic.frameworks.opf.periodic import (PeriodicActivityMgr,
                                           PeriodicActivityRequest)
from nupic.frameworks.opf.prediction_metrics_manager import MetricsManager
from nupic.support.configuration import Configuration
from nupic.swarming.experiment_utils import InferenceElement
from nupic.swarming import utils



class OPFModelRunner(object):
  """This class runs an a given Model"""

  # The minimum number of records that need to have been read for this model
  # to be a candidate for 'best model'
  _MIN_RECORDS_TO_BE_BEST = None

  # The number of points we look at when trying to figure out whether or not a
  # model has matured
  _MATURITY_NUM_POINTS = None

  # The maximum rate of change in the model's metric for it to be considered 'mature'
  _MATURITY_MAX_CHANGE = None


  def __init__(self,
               modelID,
               jobID,
               predictedField,
               experimentDir,
               reportKeyPatterns,
               optimizeKeyPattern,
               jobsDAO,
               modelCheckpointGUID,
               logLevel=None,
               predictionCacheMaxRecords=None):
    """
    Parameters:
    -------------------------------------------------------------------------
    modelID:            ID for this model in the models table

    jobID:              ID for this hypersearch job in the jobs table
    predictedField:     Name of the input field for which this model is being
                        optimized
    experimentDir:      Directory path containing the experiment's
                        description.py script
    reportKeyPatterns:  list of items from the results dict to include in
                        the report. These can be regular expressions.
    optimizeKeyPattern: Which report item, if any, we will be optimizing for.
                        This can also be a regular expression, but is an error
                        if it matches more than one key from the experiment's
                        results.
    jobsDAO:            Jobs data access object - the interface to the
                        jobs database which has the model's table.
    modelCheckpointGUID:
                        A persistent, globally-unique identifier for
                        constructing the model checkpoint key. If None, then
                        don't bother creating a model checkpoint.
    logLevel:           override logging level to this value, if not None
    predictionCacheMaxRecords:
                        Maximum number of records for the prediction output cache.
                        Pass None for default value.
    """

    # -----------------------------------------------------------------------
    # Initialize class constants
    # -----------------------------------------------------------------------
    self._MIN_RECORDS_TO_BE_BEST = int(Configuration.get('nupic.hypersearch.bestModelMinRecords'))
    self._MATURITY_MAX_CHANGE = float(Configuration.get('nupic.hypersearch.maturityPctChange'))
    self._MATURITY_NUM_POINTS = int(Configuration.get('nupic.hypersearch.maturityNumPoints'))

    # -----------------------------------------------------------------------
    # Initialize instance variables
    # -----------------------------------------------------------------------
    self._modelID = modelID
    self._jobID = jobID
    self._predictedField = predictedField
    self._experimentDir = experimentDir
    self._reportKeyPatterns = reportKeyPatterns
    self._optimizeKeyPattern = optimizeKeyPattern
    self._jobsDAO = jobsDAO
    self._modelCheckpointGUID = modelCheckpointGUID
    self._predictionCacheMaxRecords = predictionCacheMaxRecords

    self._isMaturityEnabled = bool(int(Configuration.get('nupic.hypersearch.enableModelMaturity')))

    self._logger = logging.getLogger(".".join( ['com.numenta',
                       self.__class__.__module__, self.__class__.__name__]))

    self._optimizedMetricLabel = None
    self._reportMetricLabels = []


    # Our default completion reason
    self._cmpReason = ClientJobsDAO.CMPL_REASON_EOF

    if logLevel is not None:
      self._logger.setLevel(logLevel)

    # The manager object to compute the metrics for this model
    self.__metricMgr = None

    # Will be set to a new instance of OPFTaskDriver by __runTask()
    #self.__taskDriver = None

    # Current task control parameters. Will be set by __runTask()
    self.__task = None

    # Will be set to a new instance of PeriodicActivityManager by __runTask()
    self._periodic = None

    # Will be set to streamDef string by _runTask()
    self._streamDef = None

    # Will be set to new OpfExperiment instance by run()
    self._model = None

    # Will be set to new InputSource by __runTask()
    self._inputSource = None

    # 0-based index of the record being processed;
    # Initialized and updated by __runTask()
    self._currentRecordIndex = None

    # Interface to write predictions to a persistent storage
    self._predictionLogger = None

    # In-memory cache for predictions. Predictions are written here for speed
    # when they don't need to be written to a persistent store
    self.__predictionCache = deque()

    # Flag to see if this is the best model in the job (as determined by the
    # model chooser logic). This is essentially a cache of the value in the
    # ClientJobsDB
    self._isBestModel = False

    # Flag to see if there is a best model (not necessarily this one)
    # stored in the DB
    self._isBestModelStored = False


    # -----------------------------------------------------------------------
    # Flags for model cancelation/checkpointing
    # -----------------------------------------------------------------------

    # Flag to see if the job that this model is part of
    self._isCanceled = False

    # Flag to see if model was killed, either by the model terminator or by the
    # hypsersearch implementation (ex. the a swarm is killed/matured)
    self._isKilled = False

    # Flag to see if the model is matured. In most cases, this means that we
    # should stop running the model. The only execption is if this model is the
    # best model for the job, in which case it should continue running.
    self._isMature = False

    # Event to see if interrupt signal has been sent
    self._isInterrupted = threading.Event()

    # -----------------------------------------------------------------------
    # Facilities for measuring model maturity
    # -----------------------------------------------------------------------
    # List of tuples, (iteration, metric), used to see if the model has 'matured'
    self._metricRegression = regression.AveragePctChange(windowSize=self._MATURITY_NUM_POINTS)

    self.__loggedMetricPatterns = []


  def run(self):
    """ Runs the OPF Model

    Parameters:
    -------------------------------------------------------------------------
    retval:  (completionReason, completionMsg)
              where completionReason is one of the ClientJobsDAO.CMPL_REASON_XXX
                equates.
    """
    # -----------------------------------------------------------------------
    # Load the experiment's description.py module
    descriptionPyModule = helpers.loadExperimentDescriptionScriptFromDir(
      self._experimentDir)
    expIface = helpers.getExperimentDescriptionInterfaceFromModule(
      descriptionPyModule)
    expIface.normalizeStreamSources()

    modelDescription = expIface.getModelDescription()
    self._modelControl = expIface.getModelControl()

    # -----------------------------------------------------------------------
    # Create the input data stream for this task
    streamDef = self._modelControl['dataset']

    from nupic.data.stream_reader import StreamReader
    readTimeout = 0

    self._inputSource = StreamReader(streamDef, isBlocking=False,
                                     maxTimeout=readTimeout)


    # -----------------------------------------------------------------------
    #Get field statistics from the input source
    fieldStats = self._getFieldStats()
    # -----------------------------------------------------------------------
    # Construct the model instance
    self._model = ModelFactory.create(modelDescription)
    self._model.setFieldStatistics(fieldStats)
    self._model.enableLearning()
    self._model.enableInference(self._modelControl.get("inferenceArgs", None))

    # -----------------------------------------------------------------------
    # Instantiate the metrics
    self.__metricMgr = MetricsManager(self._modelControl.get('metrics',None),
                                      self._model.getFieldInfo(),
                                      self._model.getInferenceType())

    self.__loggedMetricPatterns = self._modelControl.get("loggedMetrics", [])

    self._optimizedMetricLabel = self.__getOptimizedMetricLabel()
    self._reportMetricLabels = matchPatterns(self._reportKeyPatterns,
                                              self._getMetricLabels())


    # -----------------------------------------------------------------------
    # Initialize periodic activities (e.g., for model result updates)
    self._periodic = self._initPeriodicActivities()

    # -----------------------------------------------------------------------
    # Create our top-level loop-control iterator
    numIters = self._modelControl.get('iterationCount', -1)

    # Are we asked to turn off learning for a certain # of iterations near the
    #  end?
    learningOffAt = None
    iterationCountInferOnly = self._modelControl.get('iterationCountInferOnly', 0)
    if iterationCountInferOnly == -1:
      self._model.disableLearning()
    elif iterationCountInferOnly > 0:
      assert numIters > iterationCountInferOnly, "when iterationCountInferOnly " \
        "is specified, iterationCount must be greater than " \
        "iterationCountInferOnly."
      learningOffAt = numIters - iterationCountInferOnly

    self.__runTaskMainLoop(numIters, learningOffAt=learningOffAt)

    # -----------------------------------------------------------------------
    # Perform final operations for model
    self._finalize()

    return (self._cmpReason, None)


  def __runTaskMainLoop(self, numIters, learningOffAt=None):
    """ Main loop of the OPF Model Runner.

    Parameters:
    -----------------------------------------------------------------------

    recordIterator:    Iterator for counting number of records (see _runTask)
    learningOffAt:     If not None, learning is turned off when we reach this
                        iteration number

    """

    ## Reset sequence states in the model, so it starts looking for a new
    ## sequence
    self._model.resetSequenceStates()

    self._currentRecordIndex = -1
    while True:

      # If killed by a terminator, stop running
      if self._isKilled:
        break

      # If job stops or hypersearch ends, stop running
      if self._isCanceled:
        break

      # If the process is about to be killed, set as orphaned
      if self._isInterrupted.isSet():
        self.__setAsOrphaned()
        break

      # If model is mature, stop running ONLY IF  we are not the best model
      # for the job. Otherwise, keep running so we can keep returning
      # predictions to the user
      if self._isMature:
        if not self._isBestModel:
          self._cmpReason = self._jobsDAO.CMPL_REASON_STOPPED
          break
        else:
          self._cmpReason = self._jobsDAO.CMPL_REASON_EOF

      # Turn off learning?
        if learningOffAt is not None \
                  and self._currentRecordIndex == learningOffAt:
          self._model.disableLearning()

      # Read input record. Note that any failure here is a critical JOB failure
      #  and results in the job being immediately canceled and marked as
      #  failed. The runModelXXX code in hypesearch.utils, if it sees an
      #  exception of type utils.JobFailException, will cancel the job and
      #  copy the error message into the job record.
      try:
        inputRecord = self._inputSource.getNextRecordDict()
        if self._currentRecordIndex < 0:
          self._inputSource.setTimeout(10)
      except Exception, e:
        raise utils.JobFailException(ErrorCodes.streamReading, str(e.args),
                                     traceback.format_exc())

      if inputRecord is None:
        # EOF
        self._cmpReason = self._jobsDAO.CMPL_REASON_EOF
        break

      if inputRecord:
        # Process input record
        self._currentRecordIndex += 1

        result = self._model.run(inputRecord=inputRecord)

        # Compute metrics.
        result.metrics = self.__metricMgr.update(result)
        # If there are None, use defaults. see MetricsManager.getMetrics()
        # TODO remove this when JAVA API server is gone
        if not result.metrics:
          result.metrics = self.__metricMgr.getMetrics()


        # Write the result to the output cache. Don't write encodings, if they
        # were computed
        if InferenceElement.encodings in result.inferences:
          result.inferences.pop(InferenceElement.encodings)
        result.sensorInput.dataEncodings = None
        self._writePrediction(result)

        # Run periodic activities
        self._periodic.tick()

        if numIters >= 0 and self._currentRecordIndex >= numIters-1:
          break

      else:
        # Input source returned an empty record.
        #
        # NOTE: This is okay with Stream-based Source (when it times out
        # waiting for next record), but not okay with FileSource, which should
        # always return either with a valid record or None for EOF.
        raise ValueError("Got an empty record from FileSource: %r" %
                         inputRecord)


  def _finalize(self):
    """Run final activities after a model has run. These include recording and
    logging the final score"""

    self._logger.info(
      "Finished: modelID=%r; %r records processed. Performing final activities",
      self._modelID, self._currentRecordIndex + 1)

    # =========================================================================
    # Dump the experiment metrics at the end of the task
    # =========================================================================
    self._updateModelDBResults()

    # =========================================================================
    # Check if the current model is the best. Create a milestone if necessary
    # If the model has been killed, it is not a candidate for "best model",
    # and its output cache should be destroyed
    # =========================================================================
    if not self._isKilled:
      self.__updateJobResults()
    else:
      self.__deleteOutputCache(self._modelID)

    # =========================================================================
    # Close output stream, if necessary
    # =========================================================================
    if self._predictionLogger:
      self._predictionLogger.close()


  def __createModelCheckpoint(self):
    """ Create a checkpoint from the current model, and store it in a dir named
    after checkpoint GUID, and finally store the GUID in the Models DB """

    if self._model is None or self._modelCheckpointGUID is None:
      return

    # Create an output store, if one doesn't exist already
    if self._predictionLogger is None:
      self._createPredictionLogger()

    predictions = StringIO.StringIO()
    self._predictionLogger.checkpoint(
      checkpointSink=predictions,
      maxRows=int(Configuration.get('nupic.model.checkpoint.maxPredictionRows')))

    self._model.save(os.path.join(self._experimentDir, str(self._modelCheckpointGUID)))
    self._jobsDAO.modelSetFields(modelID,
                                 {'modelCheckpointId':str(self._modelCheckpointGUID)},
                                 ignoreUnchanged=True)

    self._logger.info("Checkpointed Hypersearch Model: modelID: %r, "
                      "checkpointID: %r", self._modelID, checkpointID)
    return


  def __deleteModelCheckpoint(self, modelID):
    """
    Delete the stored checkpoint for the specified modelID. This function is
    called if the current model is now the best model, making the old model's
    checkpoint obsolete

    Parameters:
    -----------------------------------------------------------------------
    modelID:      The modelID for the checkpoint to delete. This is NOT the
                  unique checkpointID
    """

    checkpointID = \
        self._jobsDAO.modelsGetFields(modelID, ['modelCheckpointId'])[0]

    if checkpointID is None:
      return

    try:
      shutil.rmtree(os.path.join(self._experimentDir, str(self._modelCheckpointGUID)))
    except:
      self._logger.warn("Failed to delete model checkpoint %s. "\
                        "Assuming that another worker has already deleted it",
                        checkpointID)
      return

    self._jobsDAO.modelSetFields(modelID,
                                 {'modelCheckpointId':None},
                                 ignoreUnchanged=True)
    return


  def _createPredictionLogger(self):
    """
    Creates the model's PredictionLogger object, which is an interface to write
    model results to a permanent storage location
    """
    # Write results to a file
    self._predictionLogger = BasicPredictionLogger(
      fields=self._model.getFieldInfo(),
      experimentDir=self._experimentDir,
      label = "hypersearch-worker",
      inferenceType=self._model.getInferenceType())

    if self.__loggedMetricPatterns:
      metricLabels = self.__metricMgr.getMetricLabels()
      loggedMetrics = matchPatterns(self.__loggedMetricPatterns, metricLabels)
      self._predictionLogger.setLoggedMetrics(loggedMetrics)


  def __getOptimizedMetricLabel(self):
    """ Get the label for the metric being optimized. This function also caches
    the label in the instance variable self._optimizedMetricLabel

    Parameters:
    -----------------------------------------------------------------------
    metricLabels:   A sequence of all the labels being computed for this model

    Returns:        The label for the metric being optmized over
    """
    matchingKeys = matchPatterns([self._optimizeKeyPattern],
                                  self._getMetricLabels())

    if len(matchingKeys) == 0:
      raise Exception("None of the generated metrics match the specified "
                      "optimization pattern: %s. Available metrics are %s" % \
                       (self._optimizeKeyPattern, self._getMetricLabels()))
    elif len(matchingKeys) > 1:
      raise Exception("The specified optimization pattern '%s' matches more "
              "than one metric: %s" % (self._optimizeKeyPattern, matchingKeys))

    return matchingKeys[0]


  def _getMetricLabels(self):
    """
    Returns:  A list of labels that correspond to metrics being computed
    """
    return self.__metricMgr.getMetricLabels()


  def _getFieldStats(self):
    """
    Method which returns a dictionary of field statistics received from the
    input source.

    Returns:

      fieldStats: dict of dicts where the first level is the field name and
        the second level is the statistic. ie. fieldStats['pounds']['min']

    """

    fieldStats = dict()
    fieldNames = self._inputSource.getFieldNames()
    for field in fieldNames:
      curStats = dict()
      curStats['min'] = self._inputSource.getFieldMin(field)
      curStats['max'] = self._inputSource.getFieldMax(field)
      fieldStats[field] = curStats
    return fieldStats


  def _getMetrics(self):
    """ Protected function that can be overriden by subclasses. Its main purpose
    is to allow the the OPFDummyModelRunner to override this with deterministic
    values

    Returns: All the metrics being computed for this model
    """
    return self.__metricMgr.getMetrics()


  def _updateModelDBResults(self):
    """ Retrieves the current results and updates the model's record in
    the Model database.
    """

    # -----------------------------------------------------------------------
    # Get metrics
    metrics = self._getMetrics()

    # -----------------------------------------------------------------------
    # Extract report metrics that match the requested report REs
    reportDict = dict([(k,metrics[k]) for k in self._reportMetricLabels])

    # -----------------------------------------------------------------------
    # Extract the report item that matches the optimize key RE
    # TODO cache optimizedMetricLabel sooner
    metrics = self._getMetrics()
    optimizeDict = dict()
    if self._optimizeKeyPattern is not None:
      optimizeDict[self._optimizedMetricLabel] = \
                                      metrics[self._optimizedMetricLabel]

    # -----------------------------------------------------------------------
    # Update model results
    results = json.dumps((metrics , optimizeDict))
    self._jobsDAO.modelUpdateResults(self._modelID,  results=results,
                              metricValue=optimizeDict.values()[0],
                              numRecords=(self._currentRecordIndex + 1))

    self._logger.debug(
      "Model Results: modelID=%s; numRecords=%s; results=%s" % \
        (self._modelID, self._currentRecordIndex + 1, results))

    return


  def __updateJobResultsPeriodic(self):
    """
    Periodic check to see if this is the best model. This should only have an
    effect if this is the *first* model to report its progress
    """
    if self._isBestModelStored and not self._isBestModel:
      return

    while True:
      jobResultsStr = self._jobsDAO.jobGetFields(self._jobID, ['results'])[0]
      if jobResultsStr is None:
          jobResults = {}
      else:
        self._isBestModelStored = True
        if not self._isBestModel:
          return

        jobResults = json.loads(jobResultsStr)

      bestModel = jobResults.get('bestModel', None)
      bestMetric = jobResults.get('bestValue', None)
      isSaved = jobResults.get('saved', False)

      # If there is a best model, and it is not the same as the current model
      # we should wait till we have processed all of our records to see if
      # we are the the best
      if (bestModel is not None) and (self._modelID != bestModel):
        self._isBestModel = False
        return

      # Make sure prediction output stream is ready before we present our model
      # as "bestModel"; sometimes this takes a long time, so update the model's
      # timestamp to help avoid getting orphaned
      self.__flushPredictionCache()
      self._jobsDAO.modelUpdateTimestamp(self._modelID)

      metrics = self._getMetrics()

      jobResults['bestModel'] = self._modelID
      jobResults['bestValue'] = metrics[self._optimizedMetricLabel]
      jobResults['metrics'] = metrics
      jobResults['saved'] = False

      newResults = json.dumps(jobResults)

      isUpdated = self._jobsDAO.jobSetFieldIfEqual(self._jobID,
                                                    fieldName='results',
                                                    curValue=jobResultsStr,
                                                    newValue=newResults)
      if isUpdated or (not isUpdated and newResults==jobResultsStr):
        self._isBestModel = True
        break


  def __checkIfBestCompletedModel(self):
    """
    Reads the current "best model" for the job and returns whether or not the
    current model is better than the "best model" stored for the job

    Returns: (isBetter, storedBest, origResultsStr)

    isBetter:
      True if the current model is better than the stored "best model"
    storedResults:
      A dict of the currently stored results in the jobs table record
    origResultsStr:
      The json-encoded string that currently resides in the "results" field
      of the jobs record (used to create atomicity)
    """

    jobResultsStr = self._jobsDAO.jobGetFields(self._jobID, ['results'])[0]

    if jobResultsStr is None:
        jobResults = {}
    else:
      jobResults = json.loads(jobResultsStr)

    isSaved = jobResults.get('saved', False)
    bestMetric = jobResults.get('bestValue', None)

    currentMetric = self._getMetrics()[self._optimizedMetricLabel]
    self._isBestModel = (not isSaved) \
                        or (currentMetric < bestMetric)



    return self._isBestModel, jobResults, jobResultsStr


  def __updateJobResults(self):
    """"
    Check if this is the best model
    If so:
      1) Write it's checkpoint
      2) Record this model as the best
      3) Delete the previous best's output cache
    Otherwise:
      1) Delete our output cache
     """
    isSaved = False
    while True:
      self._isBestModel, jobResults, jobResultsStr = \
                                              self.__checkIfBestCompletedModel()

      # -----------------------------------------------------------------------
      # If the current model is the best:
      #   1) Save the model's predictions
      #   2) Checkpoint the model state
      #   3) Update the results for the job
      if self._isBestModel:

        # Save the current model and its results
        if not isSaved:
          self.__flushPredictionCache()
          self._jobsDAO.modelUpdateTimestamp(self._modelID)
          self.__createModelCheckpoint()
          self._jobsDAO.modelUpdateTimestamp(self._modelID)
          isSaved = True

        # Now record the model as the best for the job
        prevBest = jobResults.get('bestModel', None)
        prevWasSaved = jobResults.get('saved', False)

        # If the current model is the best, it shouldn't already be checkpointed
        if prevBest == self._modelID:
          assert not prevWasSaved

        metrics = self._getMetrics()

        jobResults['bestModel'] = self._modelID
        jobResults['bestValue'] = metrics[self._optimizedMetricLabel]
        jobResults['metrics'] = metrics
        jobResults['saved'] = True

        isUpdated = self._jobsDAO.jobSetFieldIfEqual(self._jobID,
                                                    fieldName='results',
                                                    curValue=jobResultsStr,
                                                    newValue=json.dumps(jobResults))
        if isUpdated:
          if prevWasSaved:
            self.__deleteOutputCache(prevBest)
            self._jobsDAO.modelUpdateTimestamp(self._modelID)
            self.__deleteModelCheckpoint(prevBest)
            self._jobsDAO.modelUpdateTimestamp(self._modelID)

          self._logger.info("Model %d chosen as best model", self._modelID)
          break

      # -----------------------------------------------------------------------
      # If the current model is not the best, delete its outputs
      else:
        # NOTE: we update model timestamp around these occasionally-lengthy
        #  operations to help prevent the model from becoming orphaned
        self.__deleteOutputCache(self._modelID)
        self._jobsDAO.modelUpdateTimestamp(self._modelID)
        self.__deleteModelCheckpoint(self._modelID)
        self._jobsDAO.modelUpdateTimestamp(self._modelID)
        break


  def _writePrediction(self, result):
    """
    Writes the results of one iteration of a model. The results are written to
    this ModelRunner's in-memory cache unless this model is the "best model" for
    the job. If this model is the "best model", the predictions are written out
    to a permanent store via a prediction output stream instance


    Parameters:
    -----------------------------------------------------------------------
    result:      A opf_utils.ModelResult object, which contains the input and
                  output for this iteration
    """
    self.__predictionCache.append(result)

    if self._isBestModel:
     self.__flushPredictionCache()


  def __writeRecordsCallback(self):
    """ This callback is called by self.__predictionLogger.writeRecords()
    between each batch of records it writes. It gives us a chance to say that
    the model is 'still alive' during long write operations.
    """

    # This updates the engLastUpdateTime of the model record so that other
    #  worker's don't think that this model is orphaned.
    self._jobsDAO.modelUpdateResults(self._modelID)


  def __flushPredictionCache(self):
    """
    Writes the contents of this model's in-memory prediction cache to a permanent
    store via the prediction output stream instance
    """

    if not self.__predictionCache:
      return

    # Create an output store, if one doesn't exist already
    if self._predictionLogger is None:
      self._createPredictionLogger()

    startTime = time.time()
    self._predictionLogger.writeRecords(self.__predictionCache,
                                        progressCB=self.__writeRecordsCallback)
    self._logger.info("Flushed prediction cache; numrows=%s; elapsed=%s sec.",
                      len(self.__predictionCache), time.time() - startTime)
    self.__predictionCache.clear()


  def __deleteOutputCache(self, modelID):
    """
    Delete's the output cache associated with the given modelID. This actually
    clears up the resources associated with the cache, rather than deleting al
    the records in the cache

    Parameters:
    -----------------------------------------------------------------------
    modelID:      The id of the model whose output cache is being deleted

    """

    # If this is our output, we should close the connection
    if modelID == self._modelID and self._predictionLogger is not None:
      self._predictionLogger.close()
      del self.__predictionCache
      self._predictionLogger = None
      self.__predictionCache = None


  def _initPeriodicActivities(self):
    """ Creates and returns a PeriodicActivityMgr instance initialized with
    our periodic activities

    Parameters:
    -------------------------------------------------------------------------
    retval:             a PeriodicActivityMgr instance
    """

    # Activity to update the metrics for this model
    # in the models table
    updateModelDBResults = PeriodicActivityRequest(repeating=True,
                                                 period=100,
                                                 cb=self._updateModelDBResults)

    updateJobResults = PeriodicActivityRequest(repeating=True,
                                               period=100,
                                               cb=self.__updateJobResultsPeriodic)

    checkCancelation = PeriodicActivityRequest(repeating=True,
                                               period=50,
                                               cb=self.__checkCancelation)

    checkMaturity = PeriodicActivityRequest(repeating=True,
                                            period=10,
                                            cb=self.__checkMaturity)


    # Do an initial update of the job record after 2 iterations to make
    # sure that it is populated with something without having to wait too long
    updateJobResultsFirst = PeriodicActivityRequest(repeating=False,
                                               period=2,
                                               cb=self.__updateJobResultsPeriodic)


    periodicActivities = [updateModelDBResults,
                          updateJobResultsFirst,
                          updateJobResults,
                          checkCancelation]

    if self._isMaturityEnabled:
      periodicActivities.append(checkMaturity)

    return PeriodicActivityMgr(requestedActivities=periodicActivities)


  def __checkCancelation(self):
    """ Check if the cancelation flag has been set for this model
    in the Model DB"""

    # Update a hadoop job counter at least once every 600 seconds so it doesn't
    #  think our map task is dead
    print >>sys.stderr, "reporter:counter:HypersearchWorker,numRecords,50"

    # See if the job got cancelled
    jobCancel = self._jobsDAO.jobGetFields(self._jobID, ['cancel'])[0]
    if jobCancel:
      self._cmpReason = ClientJobsDAO.CMPL_REASON_KILLED
      self._isCanceled = True
      self._logger.info("Model %s canceled because Job %s was stopped.",
                        self._modelID, self._jobID)
    else:
      stopReason = self._jobsDAO.modelsGetFields(self._modelID, ['engStop'])[0]

      if stopReason is None:
        pass

      elif stopReason == ClientJobsDAO.STOP_REASON_KILLED:
        self._cmpReason = ClientJobsDAO.CMPL_REASON_KILLED
        self._isKilled = True
        self._logger.info("Model %s canceled because it was killed by hypersearch",
                          self._modelID)

      elif stopReason == ClientJobsDAO.STOP_REASON_STOPPED:
        self._cmpReason = ClientJobsDAO.CMPL_REASON_STOPPED
        self._isCanceled = True
        self._logger.info("Model %s stopped because hypersearch ended", self._modelID)
      else:
        raise RuntimeError ("Unexpected stop reason encountered: %s" % (stopReason))


  def __checkMaturity(self):
    """ Save the current metric value and see if the model's performance has
    'leveled off.' We do this by looking at some number of previous number of
    recordings """

    if self._currentRecordIndex+1 < self._MIN_RECORDS_TO_BE_BEST:
      return

    # If we are already mature, don't need to check anything
    if self._isMature:
      return

    metric = self._getMetrics()[self._optimizedMetricLabel]
    self._metricRegression.addPoint(x=self._currentRecordIndex, y=metric)

   # Perform a linear regression to see if the error is leveled off
    #pctChange = self._metricRegression.getPctChange()
    #if pctChange  is not None and abs(pctChange ) <= self._MATURITY_MAX_CHANGE:
    pctChange, absPctChange = self._metricRegression.getPctChanges()
    if pctChange  is not None and absPctChange <= self._MATURITY_MAX_CHANGE:
      self._jobsDAO.modelSetFields(self._modelID,
                                   {'engMatured':True})

      # TODO: Don't stop if we are currently the best model. Also, if we
      # are still running after maturity, we have to periodically check to
      # see if we are still the best model. As soon we lose to some other
      # model, then we should stop at that point.
      self._cmpReason = ClientJobsDAO.CMPL_REASON_STOPPED
      self._isMature = True

      self._logger.info("Model %d has matured (pctChange=%s, n=%d). \n"\
                        "Scores = %s\n"\
                         "Stopping execution",self._modelID, pctChange,
                                              self._MATURITY_NUM_POINTS,
                                              self._metricRegression._window)


  def handleWarningSignal(self, signum, frame):
    """
    Handles a "warning signal" from the scheduler. This is received when the
    scheduler is about to kill the the current process so that the worker can be
    allocated to another job.

    Right now, this function just sets the current model to the "Orphaned" state
    in the models table so that another worker can eventually re-run this model

    Parameters:
    -----------------------------------------------------------------------
    """
    self._isInterrupted.set()


  def __setAsOrphaned(self):
    """
    Sets the current model as orphaned. This is called when the scheduler is
    about to kill the process to reallocate the worker to a different process.
    """
    cmplReason = ClientJobsDAO.CMPL_REASON_ORPHAN
    cmplMessage = "Killed by Scheduler"
    self._jobsDAO.modelSetCompleted(self._modelID, cmplReason, cmplMessage)
