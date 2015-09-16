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

import functools

from nupic.swarming.hypersearch.utils import PeriodicActivityRequest



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
