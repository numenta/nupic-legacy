# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import functools
import logging
from  collections import namedtuple


PeriodicActivityRequest = namedtuple("PeriodicActivityRequest",
                                     ("repeating", "period", "cb"))



class ModelTerminator(object):
  """
  This is essentially an static class that handles the logic for
  terminating bad models.
  """


  _MILESTONES = [(10, 0.5),
                 (15, 0.25),
                 (20, 0.01)]


  def __init__(self, modelID, cjDAO, logLevel = None):

    self._modelID = modelID
    self._cjDB = cjDAO
    self.logger = self.logger = logging.getLogger(".".join( ['com.numenta',
                  self.__class__.__module__, self.__class__.__name__]))

    self._jobID = self._cjDB.modelsGetFields(modelID, ['jobId'])[0]

    if logLevel is not None:
      self.logger.setLevel(logLevel)

    self.logger.info("Created new ModelTerminator for model %d"%modelID)


  def getTerminationCallbacks(self, terminationFunc):
    """ Returns the periodic checks to see if the model should
    continue running.

    Parameters:
    -----------------------------------------------------------------------
    terminationFunc:  The function that will be called in the model main loop
                      as a wrapper around this function. Must have a parameter
                      called 'index'

    Returns:          A list of PeriodicActivityRequest objects.
    """
    activities = [None] * len(ModelTerminator._MILESTONES)
    for index, (iteration, _) in enumerate(ModelTerminator._MILESTONES):
      cb = functools.partial(terminationFunc, index=index)
      activities[index] = PeriodicActivityRequest(repeating =False,
                                                  period = iteration,
                                                  cb=cb)


  def checkIsTerminated(self, metric, milestoneIndex):
    bestMetric = self._cjDB.jobGetFields(self._jobID,['results'])[0]['bestMetric']
    tolerance = ModelTerminator._MILESTONES[self._index](1)

    # Right now we're assuming that we want to minize the metric
    if metric >= (1.0 + tolerance) * bestMetric:
      self.logger.info("Model %d underperforming (metric:%f, best:%f). Canceling..."
                       %(metric, bestMetric))

      self._cjDB.modelSetFields(self._modelID,
                                {'engCancel':True},
                                ignoreUnchanged = True)

      return True
    return False
