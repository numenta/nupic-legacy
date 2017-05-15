# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2016, Numenta, Inc.  Unless you have an agreement
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

import logging
import copy

from nupic.swarming.hypersearch.support import Configuration


def _flattenKeys(keys):
  return '|'.join(keys)



class SwarmTerminator(object):
  """Class that records the performane of swarms in a sprint and makes
  decisions about which swarms should stop running. This is a usful optimization
  that identifies field combinations that no longer need to be run.
  """
  MATURITY_WINDOW = None
  MAX_GENERATIONS = None
  _DEFAULT_MILESTONES = [1.0 / (x + 1) for x in xrange(12)]

  def __init__(self, milestones=None, logLevel=None):
    # Set class constants.
    self.MATURITY_WINDOW  = int(Configuration.get(
                                      "nupic.hypersearch.swarmMaturityWindow"))
    self.MAX_GENERATIONS = int(Configuration.get(
                                      "nupic.hypersearch.swarmMaxGenerations"))
    if self.MAX_GENERATIONS < 0:
      self.MAX_GENERATIONS = None

    # Set up instsance variables.

    self._isTerminationEnabled = bool(int(Configuration.get(
        'nupic.hypersearch.enableSwarmTermination')))

    self.swarmBests = dict()
    self.swarmScores = dict()
    self.terminatedSwarms = set([])

    self._logger = logging.getLogger(".".join(
        ['com.numenta', self.__class__.__module__, self.__class__.__name__]))

    if milestones is not None:
      self.milestones = milestones
    else:
      self.milestones = copy.deepcopy(self._DEFAULT_MILESTONES)

  def recordDataPoint(self, swarmId, generation, errScore):
    """Record the best score for a swarm's generation index (x)
    Returns list of swarmIds to terminate.
    """
    terminatedSwarms = []

    # Append score to existing swarm.
    if swarmId in self.swarmScores:
      entry = self.swarmScores[swarmId]
      assert(len(entry) == generation)
      entry.append(errScore)

      entry = self.swarmBests[swarmId]
      entry.append(min(errScore, entry[-1]))

      assert(len(self.swarmBests[swarmId]) == len(self.swarmScores[swarmId]))
    else:
      # Create list of scores for a new swarm
      assert (generation == 0)
      self.swarmScores[swarmId] = [errScore]
      self.swarmBests[swarmId] = [errScore]

    # If the current swarm hasn't completed at least MIN_GENERATIONS, it should
    # not be candidate for maturation or termination. This prevents the initial
    # allocation of particles in PSO from killing off a field combination too
    # early.
    if generation + 1 < self.MATURITY_WINDOW:
      return terminatedSwarms

    # If the swarm has completed more than MAX_GENERATIONS, it should be marked
    # as mature, regardless of how its value is changing.
    if self.MAX_GENERATIONS is not None and generation > self.MAX_GENERATIONS:
      self._logger.info(
          'Swarm %s has matured (more than %d generations). Stopping' %
          (swarmId, self.MAX_GENERATIONS))
      terminatedSwarms.append(swarmId)

    if self._isTerminationEnabled:
      terminatedSwarms.extend(self._getTerminatedSwarms(generation))

    # Return which swarms to kill when we've reached maturity
    # If there is no change in the swarm's best for some time,
    # Mark it dead
    cumulativeBestScores = self.swarmBests[swarmId]
    if cumulativeBestScores[-1] == cumulativeBestScores[-self.MATURITY_WINDOW]:
      self._logger.info('Swarm %s has matured (no change in %d generations).'
                        'Stopping...'% (swarmId, self.MATURITY_WINDOW))
      terminatedSwarms.append(swarmId)

    self.terminatedSwarms = self.terminatedSwarms.union(terminatedSwarms)
    return terminatedSwarms

  def numDataPoints(self, swarmId):
    if swarmId in self.swarmScores:
      return len(self.swarmScores[swarmId])
    else:
      return 0

  def _getTerminatedSwarms(self, generation):
    terminatedSwarms = []
    generationScores = dict()
    for swarm, scores in self.swarmScores.iteritems():
      if len(scores) > generation and swarm not in self.terminatedSwarms:
        generationScores[swarm] = scores[generation]

    if len(generationScores) == 0:
      return

    bestScore = min(generationScores.values())
    tolerance = self.milestones[generation]

    for swarm, score in generationScores.iteritems():
      if score > (1 + tolerance) * bestScore:
        self._logger.info('Swarm %s is doing poorly at generation %d.\n'
                          'Current Score:%s \n'
                          'Best Score:%s \n'
                          'Tolerance:%s. Stopping...',
                          swarm, generation, score, bestScore, tolerance)
        terminatedSwarms.append(swarm)
    return terminatedSwarms
