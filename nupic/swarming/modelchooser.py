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

from nupic.support import initLogging


class ModelChooser(object):
  """Utility Class to help with the selection of the 'best' model
  during hypersearch for a particular job.

  The main interface method is updateResultsForJob(), which is to
  be called periodically from the hypersearch worker.

  When called, the model chooser first tries to update the
  _eng_last_selection_sweep_time field in the jobs table. If it
  is successful, it then tries to find the model with the maximum
  metric.

  Note : Altough that there are many model choosers for a
  given job, only 1 will update the results because only one
  chooser will be  able to update the _eng_last_selection_sweep_time
  within a given interval
  """

  _MIN_UPDATE_THRESHOLD = 100
  _MIN_UPDATE_INTERVAL = 5


  def __init__(self,  jobID, jobsDAO, logLevel = None):
    """TODO: Documentation """

    self._jobID = jobID
    self._cjDB = jobsDAO
    self._lastUpdateAttemptTime = 0
    initLogging(verbose = True)
    self.logger = logging.getLogger(".".join( ['com.numenta',
                       self.__class__.__module__, self.__class__.__name__]))
    if logLevel is not None:
      self.logger.setLevel(logLevel)

    self.logger.info("Created new ModelChooser for job %s" % str(jobID))


  def updateResultsForJob(self, forceUpdate=True):
    """ Chooses the best model for a given job.

    Parameters
    -----------------------------------------------------------------------
    forceUpdate:  (True/False). If True, the update will ignore all the
                  restrictions on the minimum time to update and the minimum
                  number of records to update. This should typically only be
                  set to true if the model has completed running
    """
    updateInterval = time.time() - self._lastUpdateAttemptTime
    if updateInterval < self._MIN_UPDATE_INTERVAL and not forceUpdate:
      return

    self.logger.info("Attempting model selection for jobID=%d: time=%f"\
                     "  lastUpdate=%f"%(self._jobID,
                                        time.time(),
                                        self._lastUpdateAttemptTime))

    timestampUpdated = self._cjDB.jobUpdateSelectionSweep(self._jobID,
                                                          self._MIN_UPDATE_INTERVAL)
    if not timestampUpdated:
      self.logger.info("Unable to update selection sweep timestamp: jobID=%d" \
                       " updateTime=%f"%(self._jobID, self._lastUpdateAttemptTime))
      if not forceUpdate:
        return

    self._lastUpdateAttemptTime = time.time()
    self.logger.info("Succesfully updated selection sweep timestamp jobid=%d updateTime=%f"\
                     %(self._jobID, self._lastUpdateAttemptTime))

    minUpdateRecords = self._MIN_UPDATE_THRESHOLD

    jobResults = self._getJobResults()
    if forceUpdate or jobResults is None:
      minUpdateRecords = 0

    candidateIDs, bestMetric = self._cjDB.modelsGetCandidates(self._jobID, minUpdateRecords)

    self.logger.info("Candidate models=%s, metric=%s, jobID=%s"\
                     %(candidateIDs, bestMetric, self._jobID))

    if len(candidateIDs) == 0:
      return

    self._jobUpdateCandidate(candidateIDs[0], bestMetric, results=jobResults)


  def _jobUpdateCandidate(self, candidateID, metricValue, results):

    nullResults = results is None
    if nullResults:
      results = {'bestModel':None, 'bestValue':None}
    else:
      results = json.loads(results)
      self.logger.debug("Updating old results %s"%(results))

    oldCandidateID = results['bestModel']
    oldMetricValue = results['bestValue']

    results['bestModel'] = candidateID
    results['bestValue'] = metricValue
    isUpdated = candidateID == oldCandidateID

    if isUpdated:
      self.logger.info("Choosing new model. Old candidate: (id=%s, value=%s)"\
                   " New candidate: (id=%s, value=%f)"%\
                   (oldCandidateID, oldMetricValue, candidateID, metricValue))

    else:
      self.logger.info("Same model as before. id=%s, "\
                       "metric=%f"%(candidateID, metricValue))


    self.logger.debug("New Results %s"%(results))
    self._cjDB.jobUpdateResults(self._jobID, json.dumps(results))


  def _getJobResults(self):
    queryResults = self._cjDB.jobGetFields(self._jobID, ['results'])
    if  len(queryResults) == 0:
      raise RuntimeError("Trying to update results for non-existent job")

    results = queryResults[0]
    return results
