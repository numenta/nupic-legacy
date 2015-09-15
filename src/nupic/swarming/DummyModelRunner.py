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

import copy
import itertools
import json
import math
import os
import random
import sys
import time

from nupic.frameworks.opf.modelfactory import ModelFactory
from nupic.frameworks.opf import opfhelpers
from nupic.frameworks.opf.opfutils import ModelResult
from nupic.swarming.hypersearch import utils
from nupic.swarming.ModelRunner import OPFModelRunner


class OPFDummyModelRunner(OPFModelRunner):
  """ This class runs a 'dummy' OPF Experiment. It will periodically update the
  models db with a deterministic metric value. It can also simulate different
  amounts of computation time
  """

  modelIndex = 0
  metrics = [lambda x: float(x+1),
             lambda x: 100.0 - x-1,
             lambda x: 20.0 * math.sin(x),
             lambda x: (x/9.0)**2]

  _DEFAULT_PARAMS = dict(delay= None,
                        finalDelay=None,
                        waitTime=None,
                        randomizeWait=None,
                        iterations=1,
                        metricFunctions=None,
                        metricValue=None,
                        finalize=True,
                        permutationParams={},
                        experimentDirectory=None,
                        makeCheckpoint=False,
                        sysExitModelRange=None,
                        delayModelRange=None,
                        exitAfter=None,
                        errModelRange=None,
                        sleepModelRange=None,
                        jobFailErr=False,
                        )

  # Dummy streamDef.
  _DUMMY_STREAMDEF = dict(
    version = 1,
    info = "test_NoProviders",
    streams = [
      dict(source="file://%s" % (os.path.join("extra", "hotgym",
                                              "joined_mosman_2011.csv")),
           info="hotGym.csv",
           columns=["*"],
           #last_record=-1,
           ),
      ],
    aggregation = {
      'hours': 1,
      'fields': [
         ('consumption', 'sum'),
         ('timestamp', 'first'),
         ('TEMP', 'mean'),
         ('DEWP', 'mean'),
         #('SLP',  'mean'),
         #('STP',  'mean'),
         ('MAX',  'mean'),
         ('MIN',  'mean'),
         ('PRCP', 'sum'),
         ],
       },
    )

  def __init__(self,
               modelID,
               jobID,
               params,
               predictedField,
               reportKeyPatterns,
               optimizeKeyPattern,
               jobsDAO,
               modelCheckpointGUID,
               logLevel=None,
               predictionCacheMaxRecords=None):
    """
    Parameters:
    -------------------------------------------------------------------------
    modelID:    ID of this model in the models table

    jobID:

    params:     a dictionary of parameters for this dummy model. The
                possible keys are:

                  delay:          OPTIONAL-This specifies the amount of time
                                  (in seconds) that the experiment should wait
                                  before STARTING to process records. This is
                                  useful for simulating workers that start/end
                                  at different times

                  finalDelay:     OPTIONAL-This specifies the amount of time
                                  (in seconds) that the experiment should wait
                                  before it conducts its finalization operations.
                                  These operations include checking if the model
                                  is the best model, and writing out checkpoints.

                  waitTime:       OPTIONAL-The amount of time (in seconds)
                                  to wait in a busy loop to simulate
                                  computation time on EACH ITERATION

                  randomizeWait:  OPTIONAL-([0.0-1.0] ). Default:None
                                  If set to a value, the above specified
                                  wait time will be randomly be dithered by
                                  +/- <randomizeWait>% of the specfied value.
                                  For example, if randomizeWait=0.2, the wait
                                  time will be dithered by +/- 20% of its value.

                  iterations:     OPTIONAL-How many iterations to run the model
                                  for. -1 means run forever (default=1)

                  metricFunctions: OPTIONAL-A list of single argument functions
                                   serialized as strings, which return the metric
                                   value given the record number.

                                   Mutually exclusive with metricValue

                  metricValue:    OPTIONAL-A single value to use for the metric
                                  value (used to debug hypersearch).

                                  Mutually exclusive with metricFunctions

                  finalize:       OPTIONAL-(True/False). Default:True
                                  When False, this will prevent the model from
                                  recording it's metrics and performing other
                                  functions that it usually performs after the
                                  model has finished running

                  permutationParams: A dict containing the instances of all the
                                      variables being permuted over

                  experimentDirectory: REQUIRED-An absolute path to a directory
                                       with a valid description.py file.

                                       NOTE: This does not actually affect the
                                       running of the model or the metrics
                                       produced. It is required to create certain
                                       objects (such as the output stream)

                  makeCheckpoint:     True to actually write a checkpoint out to
                                      disk (default: False)

                  sysExitModelRange: A string containing two integers 'firstIdx,
                                  endIdx'. When present, if we are running the
                                  firstIdx'th model up to but not including the
                                  endIdx'th model, then do a sys.exit() while
                                  running the model. This causes the worker to
                                  exit, simulating an orphaned model.

                  delayModelRange: A string containing two integers 'firstIdx,
                                  endIdx'. When present, if we are running the
                                  firstIdx'th model up to but not including the
                                  endIdx'th model, then do a delay of 10 sec.
                                  while running the model. This causes the 
                                  worker to run slower and for some other worker
                                  to think the model should be orphaned.

                  exitAfter:      The number of iterations after which the model
                                  should perform a sys exit. This is an
                                  alternative way of creating an orphaned model
                                  that use's the dummmy model's modelIndex
                                  instead of the modelID

                  errModelRange: A string containing two integers 'firstIdx,
                                  endIdx'. When present, if we are running the
                                  firstIdx'th model up to but not including the
                                  endIdx'th model, then raise an exception while
                                  running the model. This causes the model to
                                  fail with a CMPL_REASON_ERROR reason

                  sleepModelRange: A string containing 3 integers 'firstIdx,
                                  endIdx: delay'. When present, if we are running
                                  the firstIdx'th model up to but not including
                                  the endIdx'th model, then sleep for delay
                                  seconds at the beginning of the run.

                  jobFailErr: If true, model will raise a JobFailException
                              which should cause the job to be marked as
                              failed and immediately cancel all other workers.

    predictedField:     Name of the input field for which this model is being
                        optimized

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
                        constructing the model checkpoint key

    logLevel:           override logging level to this value, if not None
    predictionCacheMaxRecords:
                        Maximum number of records for the prediction output cache.
                        Pass None for the default value.
    """

    super(OPFDummyModelRunner, self).__init__(modelID=modelID,
                                              jobID=jobID,
                                              predictedField=predictedField,
                                              experimentDir=None,
                                              reportKeyPatterns=reportKeyPatterns,
                                              optimizeKeyPattern=optimizeKeyPattern,
                                              jobsDAO=jobsDAO,
                                              modelCheckpointGUID=modelCheckpointGUID,
                                              logLevel=logLevel,
                                              predictionCacheMaxRecords=None)

    self._predictionCacheMaxRecords = predictionCacheMaxRecords
    self._streamDef = copy.deepcopy(self._DUMMY_STREAMDEF)
    self._params = copy.deepcopy(self._DEFAULT_PARAMS)

    # -----------------------------------------------------------------------
    # Read the index of the current model in the test
    if 'permutationParams' in params \
          and '__model_num' in params['permutationParams']:
      self.modelIndex=params['permutationParams']['__model_num']
    else:
      self.modelIndex = OPFDummyModelRunner.modelIndex
      OPFDummyModelRunner.modelIndex += 1

    # -----------------------------------------------------------------------
    self._loadDummyModelParameters(params)

    # =========================================================================
    # Load parameters into instance variables
    # =========================================================================
    self._logger.debug("Using Dummy model params: %s", self._params)

    self._busyWaitTime = self._params['waitTime']
    self._iterations = self._params['iterations']
    self._doFinalize = self._params['finalize']
    self._delay = self._params['delay']
    self._sleepModelRange = self._params['sleepModelRange']
    self._makeCheckpoint = self._params['makeCheckpoint']
    self._finalDelay = self._params['finalDelay']
    self._exitAfter = self._params['exitAfter']

    # =========================================================================
    # Randomize Wait time, if necessary
    # =========================================================================
    self.randomizeWait = self._params['randomizeWait']
    if self._busyWaitTime is not None:
      self.__computeWaitTime()

    # =========================================================================
    # Load the appropriate metric value or metric function
    # =========================================================================
    if self._params['metricFunctions'] is not None \
        and self._params['metricValue'] is not None:
      raise RuntimeError("Error, only 1 of 'metricFunctions' or 'metricValue'"\
                         " can be passed to OPFDummyModelRunner params ")
    self.metrics = None
    self.metricValue = None

    if self._params['metricFunctions'] is not None:
      self.metrics = eval(self._params['metricFunctions'])
    elif self._params['metricValue'] is not None:
      self.metricValue = float(self._params['metricValue'])
    else:
      self.metrics = OPFDummyModelRunner.metrics[0]


    # =========================================================================
    # Create an OpfExperiment instance, if a directory is specified
    # =========================================================================
    if self._params['experimentDirectory'] is not None:
      self._model = self.__createModel(self._params['experimentDirectory'])
      self.__fieldInfo = self._model.getFieldInfo()


    # =========================================================================
    # Get the sysExit model range
    # =========================================================================
    self._sysExitModelRange = self._params['sysExitModelRange']
    if self._sysExitModelRange is not None:
      self._sysExitModelRange = [int(x) for x in self._sysExitModelRange.split(',')]

    # =========================================================================
    # Get the delay model range
    # =========================================================================
    self._delayModelRange = self._params['delayModelRange']
    if self._delayModelRange is not None:
      self._delayModelRange = [int(x) for x in self._delayModelRange.split(',')]

    # =========================================================================
    # Get the errModel range
    # =========================================================================
    self._errModelRange = self._params['errModelRange']
    if self._errModelRange is not None:
      self._errModelRange = [int(x) for x in self._errModelRange.split(',')]

    self._computModelDelay()

    # Get the jobFailErr boolean
    self._jobFailErr = self._params['jobFailErr']

    self._logger.debug("Dummy Model %d params %r", self._modelID, self._params)


  def _loadDummyModelParameters(self, params):
    """ Loads all the parameters for this dummy model. For any paramters
    specified as lists, read the appropriate value for this model using the model
    index """

    for key, value in params.iteritems():
      if type(value) == list:
        index = self.modelIndex % len(params[key])
        self._params[key] = params[key][index]
      else:
        self._params[key] = params[key]


  def _computModelDelay(self):
    """ Computes the amount of time (if any) to delay the run of this model.
    This can be determined by two mutually exclusive parameters:
    delay and sleepModelRange.

    'delay' specifies the number of seconds a model should be delayed. If a list
    is specified, the appropriate amount of delay is determined by using the
    model's modelIndex property.

    However, this doesn't work when testing orphaned models, because the
    modelIndex will be the same for every recovery attempt. Therefore, every
    recovery attempt will also be delayed and potentially orphaned.

    'sleepModelRange' doesn't use the modelIndex property for a model, but rather
    sees which order the model is in the database, and uses that to determine
    whether or not a model should be delayed.
    """

    # 'delay' and 'sleepModelRange' are mutually exclusive
    if self._params['delay'] is not None \
        and self._params['sleepModelRange'] is not None:
          raise RuntimeError("Only one of 'delay' or "
                             "'sleepModelRange' may be specified")

    # Get the sleepModel range
    if self._sleepModelRange is not None:
      range, delay = self._sleepModelRange.split(':')
      delay = float(delay)
      range = map(int, range.split(','))
      modelIDs = self._jobsDAO.jobGetModelIDs(self._jobID)
      modelIDs.sort()

      range[1] = min(range[1], len(modelIDs))

      # If the model is in range, add the delay
      if self._modelID in modelIDs[range[0]:range[1]]:
        self._delay = delay
    else:
      self._delay = self._params['delay']


  def _getMetrics(self):
    """ Protected function that can be overridden by subclasses. Its main purpose
    is to allow the the OPFDummyModelRunner to override this with deterministic
    values

    Returns: All the metrics being computed for this model
    """
    metric = None
    if self.metrics is not None:
      metric = self.metrics(self._currentRecordIndex+1)
    elif self.metricValue is not None:
      metric = self.metricValue
    else:
      raise RuntimeError('No metrics or metric value specified for dummy model')

    return {self._optimizeKeyPattern:metric}


  def run(self):
    """ Runs the given OPF task against the given Model instance """

    self._logger.debug("Starting Dummy Model: modelID=%s;" % (self._modelID))

    # =========================================================================
    # Initialize periodic activities (e.g., for model result updates)
    # =========================================================================
    periodic = self._initPeriodicActivities()

    self._optimizedMetricLabel = self._optimizeKeyPattern
    self._reportMetricLabels = [self._optimizeKeyPattern]

    # =========================================================================
    # Create our top-level loop-control iterator
    # =========================================================================
    if self._iterations >= 0:
      iterTracker = iter(xrange(self._iterations))
    else:
      iterTracker = iter(itertools.count())

    # =========================================================================
    # This gets set in the unit tests. It tells the worker to sys exit
    #  the first N models. This is how we generate orphaned models
    doSysExit = False
    if self._sysExitModelRange is not None:
      modelAndCounters = self._jobsDAO.modelsGetUpdateCounters(self._jobID)
      modelIDs = [x[0] for x in modelAndCounters]
      modelIDs.sort()
      (beg,end) = self._sysExitModelRange
      if self._modelID in modelIDs[int(beg):int(end)]:
        doSysExit = True

    if self._delayModelRange is not None:
      modelAndCounters = self._jobsDAO.modelsGetUpdateCounters(self._jobID)
      modelIDs = [x[0] for x in modelAndCounters]
      modelIDs.sort()
      (beg,end) = self._delayModelRange
      if self._modelID in modelIDs[int(beg):int(end)]:
        time.sleep(10)
        
      # DEBUG!!!! infinite wait if we have 50 models
      #if len(modelIDs) >= 50:
      #  jobCancel = self._jobsDAO.jobGetFields(self._jobID, ['cancel'])[0]
      #  while not jobCancel:
      #    time.sleep(1)
      #    jobCancel = self._jobsDAO.jobGetFields(self._jobID, ['cancel'])[0]

    if self._errModelRange is not None:
      modelAndCounters = self._jobsDAO.modelsGetUpdateCounters(self._jobID)
      modelIDs = [x[0] for x in modelAndCounters]
      modelIDs.sort()
      (beg,end) = self._errModelRange
      if self._modelID in modelIDs[int(beg):int(end)]:
        raise RuntimeError("Exiting with error due to errModelRange parameter")

    # =========================================================================
    # Delay, if necessary
    if self._delay is not None:
      time.sleep(self._delay)

    # =========================================================================
    # Run it!
    # =========================================================================
    self._currentRecordIndex = 0
    while True:

      # =========================================================================
      # Check if the model should be stopped
      # =========================================================================

      # If killed by a terminator, stop running
      if self._isKilled:
        break

      # If job stops or hypersearch ends, stop running
      if self._isCanceled:
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

      # =========================================================================
      # Get the the next record, and "write it"
      # =========================================================================
      try:
        self._currentRecordIndex = next(iterTracker)
      except StopIteration:
        break

      # "Write" a dummy output value. This is used to test that the batched
      # writing works properly

      self._writePrediction(ModelResult(None, None, None, None))

      periodic.tick()

      # =========================================================================
      # Compute wait times. See if model should exit
      # =========================================================================

      if self.__shouldSysExit(self._currentRecordIndex):
        sys.exit(1)

      # Simulate computation time
      if self._busyWaitTime is not None:
        time.sleep(self._busyWaitTime)
        self.__computeWaitTime()

      # Asked to abort after so many iterations?
      if doSysExit:
        sys.exit(1)

      # Asked to raise a jobFailException?
      if self._jobFailErr:
        raise utils.JobFailException("E10000",
                                      "dummyModel's jobFailErr was True.")

    # =========================================================================
    # Handle final operations
    # =========================================================================
    if self._doFinalize:
      if not self._makeCheckpoint:
        self._model = None

      # Delay finalization operation
      if self._finalDelay is not None:
        time.sleep(self._finalDelay)

      self._finalize()

    self._logger.info("Finished: modelID=%r "% (self._modelID))

    return (self._cmpReason, None)


  def __computeWaitTime(self):
    if self.randomizeWait is not None:
      self._busyWaitTime = random.uniform((1.0-self.randomizeWait) * self._busyWaitTime,
                                          (1.0+self.randomizeWait) * self._busyWaitTime)


  def __createModel(self, expDir):
    # -----------------------------------------------------------------------
    # Load the experiment's description.py module
    descriptionPyModule = opfhelpers.loadExperimentDescriptionScriptFromDir(
      expDir)
    expIface = opfhelpers.getExperimentDescriptionInterfaceFromModule(
      descriptionPyModule)


    # -----------------------------------------------------------------------
    # Construct the model instance
    modelDescription = expIface.getModelDescription()
    return ModelFactory.create(modelDescription)


  def _createPredictionLogger(self):
    """
    Creates the model's PredictionLogger object, which is an interface to write
    model results to a permanent storage location
    """

    class DummyLogger:
      def writeRecord(self, record): pass
      def writeRecords(self, records, progressCB): pass
      def close(self): pass

    self._predictionLogger = DummyLogger()


  def __shouldSysExit(self, iteration):
    """
    Checks to see if the model should exit based on the exitAfter dummy
    parameter
    """

    if self._exitAfter is None \
       or iteration < self._exitAfter:
      return False

    results = self._jobsDAO.modelsGetFieldsForJob(self._jobID, ['params'])

    modelIDs = [e[0] for e in results]
    modelNums = [json.loads(e[1][0])['structuredParams']['__model_num'] for e in results]

    sameModelNumbers = filter(lambda x: x[1] == self.modelIndex,
                              zip(modelIDs, modelNums))

    firstModelID = min(zip(*sameModelNumbers)[0])

    return firstModelID == self._modelID
