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
import time
import logging
import json
import hashlib
import itertools
import StringIO
import shutil
import tempfile
import copy
import pprint
from operator import itemgetter

from nupic.frameworks.opf import opfhelpers
from nupic.swarming.hypersearch.utils import sortedJSONDumpS, rApply, rCopy
from nupic.support.configuration import Configuration
from nupic.swarming.hypersearch.utils import clippedObj
from nupic.swarming.hypersearch.errorcodes import ErrorCodes
from nupic.swarming.hypersearch.experimentutils import InferenceType
from nupic.database.ClientJobsDAO import (
    ClientJobsDAO, InvalidConnectionException)
from nupic.swarming.hypersearch.utils import (runModelGivenBaseAndParams,
                                              runDummyModel)
from nupic.swarming.permutationhelpers import *
from nupic.swarming.exp_generator.ExpGenerator import expGenerator


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


class ResultsDB(object):
  """This class holds all the information we have accumulated on completed
  models, which particles were used, etc.

  When we get updated results sent to us (via recordModelProgress), we
  record it here for access later by various functions in this module.
  """

  def __init__(self, hsObj):
    """ Instantiate our results database

    Parameters:
    --------------------------------------------------------------------
    hsObj:        Reference to the HypersearchV2 instance
    """
    self._hsObj = hsObj

    # This list holds all the results we have so far on every model. In
    #  addition, we maintain mutliple other data structures which provide
    #  faster access into portions of this list
    self._allResults = []

    # Models that completed with errors and all completed.
    # These are used to determine when we should abort because of too many
    #   errors
    self._errModels = set()
    self._numErrModels = 0
    self._completedModels = set()
    self._numCompletedModels = 0

    # Map of the model ID to index of result in _allResults
    self._modelIDToIdx = dict()

    # The global best result on the optimize metric so far, and the model ID
    self._bestResult = numpy.inf
    self._bestModelID = None

    # This is a dict of dicts. The top level dict has the swarmId as the key.
    # Each entry is a dict of genIdx: (modelId, errScore) entries.
    self._swarmBestOverall = dict()

    # For each swarm, we keep track of how many particles we have per generation
    # The key is the swarmId, the value is a list of the number of particles
    # at each generation
    self._swarmNumParticlesPerGeneration = dict()

    # The following variables are used to support the
    # getMaturedSwarmGenerations() call.
    #
    # The _modifiedSwarmGens set contains the set of (swarmId, genIdx) tuples
    # that have had results reported to them since the last time
    # getMaturedSwarmGenerations() was called.
    #
    # The maturedSwarmGens contains (swarmId,genIdx) tuples, one for each
    # swarm generation index which we have already detected has matured. This
    # insures that if by chance we get a rogue report from a model in a swarm
    # generation index which we have already assumed was matured that we won't
    # report on it again.
    self._modifiedSwarmGens = set()
    self._maturedSwarmGens = set()

    # For each particle, we keep track of it's best score (across all
    # generations) and the position it was at when it got that score. The keys
    # in this dict are the particleId, the values are (bestResult, position),
    # where position is a dict with varName:position items in it.
    self._particleBest = dict()

    # For each particle, we keep track of it's latest generation index.
    self._particleLatestGenIdx = dict()

    # For each swarm, we keep track of which models are in it. The key
    # is the swarmId, the value is a list of indexes into self._allResults.
    self._swarmIdToIndexes = dict()

    # ParamsHash to index mapping
    self._paramsHashToIndexes = dict()
    

  def update(self, modelID, modelParams, modelParamsHash, metricResult,
             completed, completionReason, matured, numRecords):
    """ Insert a new entry or update an existing one. If this is an update
    of an existing entry, then modelParams will be None

    Parameters:
    --------------------------------------------------------------------
    modelID:       globally unique modelID of this model
    modelParams:    params dict for this model, or None if this is just an update
                    of a model that it already previously reported on.

                    See the comments for the createModels() method for
                    a description of this dict.

    modelParamsHash:  hash of the modelParams dict, generated by the worker
                    that put it into the model database.
    metricResult:   value on the optimizeMetric for this model.
                    May be None if we have no results yet.
    completed:      True if the model has completed evaluation, False if it
                      is still running (and these are online results)
    completionReason: One of the ClientJobsDAO.CMPL_REASON_XXX equates
    matured:        True if this model has matured
    numRecords:     Number of records that have been processed so far by this
                      model.

    retval: Canonicalized result on the optimize metric
    """
    # The modelParamsHash must always be provided - it can change after a
    #  model is inserted into the models table if it got detected as an
    #  orphan
    assert (modelParamsHash is not None)

    # We consider a model metricResult as "final" if it has completed or
    #  matured. By default, assume anything that has completed has matured
    if completed:
      matured = True

    # Get the canonicalized optimize metric results. For this metric, lower
    #  is always better
    if metricResult is not None and matured and \
                       completionReason in [ClientJobsDAO.CMPL_REASON_EOF,
                                            ClientJobsDAO.CMPL_REASON_STOPPED]:
      # Canonicalize the error score so that lower is better
      if self._hsObj._maximize:
        errScore = -1 * metricResult
      else:
        errScore = metricResult

      if errScore < self._bestResult:
        self._bestResult = errScore
        self._bestModelID = modelID
        self._hsObj.logger.info("New best model after %d evaluations: errScore "
              "%g on model %s" % (len(self._allResults), self._bestResult,
                                  self._bestModelID))

    else:
      errScore = numpy.inf

    # If this model completed with an unacceptable completion reason, set the
    #  errScore to infinite and essentially make this model invisible to
    #  further queries
    if completed and completionReason in [ClientJobsDAO.CMPL_REASON_ORPHAN]:
      errScore = numpy.inf
      hidden = True
    else:
      hidden = False

    # Update our set of erred models and completed models. These are used
    #  to determine if we should abort the search because of too many errors
    if completed:
      self._completedModels.add(modelID)
      self._numCompletedModels = len(self._completedModels)
      if completionReason == ClientJobsDAO.CMPL_REASON_ERROR:
        self._errModels.add(modelID)
        self._numErrModels = len(self._errModels)

    # Are we creating a new entry?
    wasHidden = False
    if modelID not in self._modelIDToIdx:
      assert (modelParams is not None)
      entry = dict(modelID=modelID, modelParams=modelParams,
                   modelParamsHash=modelParamsHash,
                   errScore=errScore, completed=completed,
                   matured=matured, numRecords=numRecords, hidden=hidden)
      self._allResults.append(entry)
      entryIdx = len(self._allResults) - 1
      self._modelIDToIdx[modelID] = entryIdx

      self._paramsHashToIndexes[modelParamsHash] = entryIdx

      swarmId = modelParams['particleState']['swarmId']
      if not hidden:
        # Update the list of particles in each swarm
        if swarmId in self._swarmIdToIndexes:
          self._swarmIdToIndexes[swarmId].append(entryIdx)
        else:
          self._swarmIdToIndexes[swarmId] = [entryIdx]

        # Update number of particles at each generation in this swarm
        genIdx = modelParams['particleState']['genIdx']
        numPsEntry = self._swarmNumParticlesPerGeneration.get(swarmId, [0])
        while genIdx >= len(numPsEntry):
          numPsEntry.append(0)
        numPsEntry[genIdx] += 1
        self._swarmNumParticlesPerGeneration[swarmId] = numPsEntry

    # Replacing an existing one
    else:
      entryIdx = self._modelIDToIdx.get(modelID, None)
      assert (entryIdx is not None)
      entry = self._allResults[entryIdx]
      wasHidden = entry['hidden']

      # If the paramsHash changed, note that. This can happen for orphaned
      #  models
      if entry['modelParamsHash'] != modelParamsHash:

        self._paramsHashToIndexes.pop(entry['modelParamsHash'])
        self._paramsHashToIndexes[modelParamsHash] = entryIdx
        entry['modelParamsHash'] = modelParamsHash

      # Get the model params, swarmId, and genIdx
      modelParams = entry['modelParams']
      swarmId = modelParams['particleState']['swarmId']
      genIdx = modelParams['particleState']['genIdx']

      # If this particle just became hidden, remove it from our swarm counts
      if hidden and not wasHidden:
        assert (entryIdx in self._swarmIdToIndexes[swarmId])
        self._swarmIdToIndexes[swarmId].remove(entryIdx)
        self._swarmNumParticlesPerGeneration[swarmId][genIdx] -= 1

      # Update the entry for the latest info
      entry['errScore']  = errScore
      entry['completed'] = completed
      entry['matured'] = matured
      entry['numRecords'] = numRecords
      entry['hidden'] = hidden

    # Update the particle best errScore
    particleId = modelParams['particleState']['id']
    genIdx = modelParams['particleState']['genIdx']
    if matured and not hidden:
      (oldResult, pos) = self._particleBest.get(particleId, (numpy.inf, None))
      if errScore < oldResult:
        pos = Particle.getPositionFromState(modelParams['particleState'])
        self._particleBest[particleId] = (errScore, pos)

    # Update the particle latest generation index
    prevGenIdx = self._particleLatestGenIdx.get(particleId, -1)
    if not hidden and genIdx > prevGenIdx:
      self._particleLatestGenIdx[particleId] = genIdx
    elif hidden and not wasHidden and genIdx == prevGenIdx:
      self._particleLatestGenIdx[particleId] = genIdx-1

    # Update the swarm best score
    if not hidden:
      swarmId = modelParams['particleState']['swarmId']
      if not swarmId in self._swarmBestOverall:
        self._swarmBestOverall[swarmId] = []

      bestScores = self._swarmBestOverall[swarmId]
      while genIdx >= len(bestScores):
        bestScores.append((None, numpy.inf))
      if errScore < bestScores[genIdx][1]:
        bestScores[genIdx] = (modelID, errScore)

    # Update the self._modifiedSwarmGens flags to support the
    #   getMaturedSwarmGenerations() call.
    if not hidden:
      key = (swarmId, genIdx)
      if not key in self._maturedSwarmGens:
        self._modifiedSwarmGens.add(key)

    return errScore

  def getNumErrModels(self):
    """Return number of models that completed with errors.

    Parameters:
    ---------------------------------------------------------------------
    retval:      # if models
    """
    return self._numErrModels

  def getErrModelIds(self):
    """Return list of models IDs that completed with errors.

    Parameters:
    ---------------------------------------------------------------------
    retval:      # if models
    """
    return list(self._errModels)

  def getNumCompletedModels(self):
    """Return total number of models that completed.

    Parameters:
    ---------------------------------------------------------------------
    retval:      # if models that completed
    """
    return self._numCompletedModels

  def getModelIDFromParamsHash(self, paramsHash):
    """ Return the modelID of the model with the given paramsHash, or
    None if not found.

    Parameters:
    ---------------------------------------------------------------------
    paramsHash:  paramsHash to look for
    retval:      modelId, or None if not found
    """
    entryIdx = self. _paramsHashToIndexes.get(paramsHash, None)
    if entryIdx is not None:
      return self._allResults[entryIdx]['modelID']
    else:
      return None

  def numModels(self, swarmId=None, includeHidden=False):
    """Return the total # of models we have in our database (if swarmId is
    None) or in a specific swarm.

    Parameters:
    ---------------------------------------------------------------------
    swarmId:        A string representation of the sorted list of encoders
                    in this swarm. For example '__address_encoder.__gym_encoder'
    includeHidden:  If False, this will only return the number of models
                    that are not hidden (i.e. orphanned, etc.)
    retval:  numModels
    """
    # Count all models
    if includeHidden:
      if swarmId is None:
        return len(self._allResults)

      else:
        return len(self._swarmIdToIndexes.get(swarmId, []))
    # Only count non-hidden models
    else:
      if swarmId is None:
        entries = self._allResults
      else:
        entries = [self._allResults[entryIdx]
                   for entryIdx in self._swarmIdToIndexes.get(swarmId,[])]

      return len([entry for entry in entries if not entry['hidden']])

  def bestModelIdAndErrScore(self, swarmId=None, genIdx=None):
    """Return the model ID of the model with the best result so far and
    it's score on the optimize metric. If swarm is None, then it returns
    the global best, otherwise it returns the best for the given swarm
    for all generatons up to and including genIdx.

    Parameters:
    ---------------------------------------------------------------------
    swarmId:  A string representation of the sorted list of encoders in this
                 swarm. For example '__address_encoder.__gym_encoder'
    genIdx:   consider the best in all generations up to and including this
                generation if not None.
    retval:  (modelID, result)
    """
    if swarmId is None:
      return (self._bestModelID, self._bestResult)

    else:
      if swarmId not in self._swarmBestOverall:
        return (None, numpy.inf)


      # Get the best score, considering the appropriate generations
      genScores = self._swarmBestOverall[swarmId]
      bestModelId = None
      bestScore = numpy.inf

      for (i, (modelId, errScore)) in enumerate(genScores):
        if genIdx is not None and i > genIdx:
          break
        if errScore < bestScore:
          bestScore = errScore
          bestModelId = modelId

      return (bestModelId, bestScore)

  def getParticleInfo(self, modelId):
    """Return particle info for a specific modelId.

    Parameters:
    ---------------------------------------------------------------------
    modelId:  which model Id

    retval:  (particleState, modelId, errScore, completed, matured)
    """
    entry = self._allResults[self._modelIDToIdx[modelId]]
    return (entry['modelParams']['particleState'], modelId, entry['errScore'],
            entry['completed'], entry['matured'])


  def getParticleInfos(self, swarmId=None, genIdx=None, completed=None,
                       matured=None, lastDescendent=False):
    """Return a list of particleStates for all particles we know about in
    the given swarm, their model Ids, and metric results.

    Parameters:
    ---------------------------------------------------------------------
    swarmId:  A string representation of the sorted list of encoders in this
                 swarm. For example '__address_encoder.__gym_encoder'

    genIdx:  If not None, only return particles at this specific generation
                  index.

    completed:   If not None, only return particles of the given state (either
                completed if 'completed' is True, or running if 'completed'
                is false

    matured:   If not None, only return particles of the given state (either
                matured if 'matured' is True, or not matured if 'matured'
                is false. Note that any model which has completed is also
                considered matured.

    lastDescendent: If True, only return particles that are the last descendent,
                that is, the highest generation index for a given particle Id

    retval:  (particleStates, modelIds, errScores, completed, matured)
              particleStates: list of particleStates
              modelIds: list of modelIds
              errScores: list of errScores, numpy.inf is plugged in
                              if we don't have a result yet
              completed: list of completed booleans
              matured: list of matured booleans
    """
    # The indexes of all the models in this swarm. This list excludes hidden
    #  (orphaned) models.
    if swarmId is not None:
      entryIdxs = self._swarmIdToIndexes.get(swarmId, [])
    else:
      entryIdxs = range(len(self._allResults))
    if len(entryIdxs) == 0:
      return ([], [], [], [], [])

    # Get the particles of interest
    particleStates = []
    modelIds = []
    errScores = []
    completedFlags = []
    maturedFlags = []
    for idx in entryIdxs:
      entry = self._allResults[idx]

      # If this entry is hidden (i.e. it was an orphaned model), it should
      #  not be in this list
      if swarmId is not None:
        assert (not entry['hidden'])

      # Get info on this model
      modelParams = entry['modelParams']
      isCompleted = entry['completed']
      isMatured = entry['matured']
      particleState = modelParams['particleState']
      particleGenIdx = particleState['genIdx']
      particleId = particleState['id']

      if genIdx is not None and particleGenIdx != genIdx:
        continue

      if completed is not None and (completed != isCompleted):
        continue

      if matured is not None and (matured != isMatured):
        continue

      if lastDescendent \
              and (self._particleLatestGenIdx[particleId] != particleGenIdx):
        continue

      # Incorporate into return values
      particleStates.append(particleState)
      modelIds.append(entry['modelID'])
      errScores.append(entry['errScore'])
      completedFlags.append(isCompleted)
      maturedFlags.append(isMatured)


    return (particleStates, modelIds, errScores, completedFlags, maturedFlags)



  def getOrphanParticleInfos(self, swarmId, genIdx):
    """Return a list of particleStates for all particles in the given
    swarm generation that have been orphaned. 

    Parameters:
    ---------------------------------------------------------------------
    swarmId:  A string representation of the sorted list of encoders in this
                 swarm. For example '__address_encoder.__gym_encoder'

    genIdx:  If not None, only return particles at this specific generation
                  index.

    retval:  (particleStates, modelIds, errScores, completed, matured)
              particleStates: list of particleStates
              modelIds: list of modelIds
              errScores: list of errScores, numpy.inf is plugged in
                              if we don't have a result yet
              completed: list of completed booleans
              matured: list of matured booleans
    """

    entryIdxs = range(len(self._allResults))
    if len(entryIdxs) == 0:
      return ([], [], [], [], [])

    # Get the particles of interest
    particleStates = []
    modelIds = []
    errScores = []
    completedFlags = []
    maturedFlags = []
    for idx in entryIdxs:
      
      # Get info on this model
      entry = self._allResults[idx]
      if not entry['hidden']:
        continue
      
      modelParams = entry['modelParams']
      if modelParams['particleState']['swarmId'] != swarmId:
        continue
      
      isCompleted = entry['completed']
      isMatured = entry['matured']
      particleState = modelParams['particleState']
      particleGenIdx = particleState['genIdx']
      particleId = particleState['id']

      if genIdx is not None and particleGenIdx != genIdx:
        continue

      # Incorporate into return values
      particleStates.append(particleState)
      modelIds.append(entry['modelID'])
      errScores.append(entry['errScore'])
      completedFlags.append(isCompleted)
      maturedFlags.append(isMatured)

    return (particleStates, modelIds, errScores, completedFlags, maturedFlags)


  def getMaturedSwarmGenerations(self):
    """Return a list of swarm generations that have completed and the
    best (minimal) errScore seen for each of them.

    Parameters:
    ---------------------------------------------------------------------
    retval:  list of tuples. Each tuple is of the form:
              (swarmId, genIdx, bestErrScore)
    """
    # Return results go in this list
    result = []


    # For each of the swarm generations which have had model result updates
    # since the last time we were called, see which have completed.
    modifiedSwarmGens = sorted(self._modifiedSwarmGens)

    # Walk through them in order from lowest to highest generation index
    for key in modifiedSwarmGens:
      (swarmId, genIdx) = key

      # Skip it if we've already reported on it. This should happen rarely, if
      #  ever. It means that some worker has started and completed a model in
      #  this generation after we've determined that the generation has ended.
      if key in self._maturedSwarmGens:
        self._modifiedSwarmGens.remove(key)
        continue

      # If the previous generation for this swarm is not complete yet, don't
      #  bother evaluating this one.
      if (genIdx >= 1) and not (swarmId, genIdx-1) in self._maturedSwarmGens:
        continue

      # We found a swarm generation that had some results reported since last
      # time, see if it's complete or not
      (_, _, errScores, completedFlags, maturedFlags) = \
                                self.getParticleInfos(swarmId, genIdx)
      maturedFlags = numpy.array(maturedFlags)
      numMatured = maturedFlags.sum()
      if numMatured >= self._hsObj._minParticlesPerSwarm \
            and numMatured == len(maturedFlags):
        errScores = numpy.array(errScores)
        bestScore = errScores.min()

        self._maturedSwarmGens.add(key)
        self._modifiedSwarmGens.remove(key)
        result.append((swarmId, genIdx, bestScore))

    # Return results
    return result

  def firstNonFullGeneration(self, swarmId, minNumParticles):
    """ Return the generation index of the first generation in the given
    swarm that does not have numParticles particles in it, either still in the
    running state or completed. This does not include orphaned particles.

    Parameters:
    ---------------------------------------------------------------------
    swarmId:  A string representation of the sorted list of encoders in this
                 swarm. For example '__address_encoder.__gym_encoder'
    minNumParticles: minium number of partices required for a full
                  generation.

    retval:  generation index, or None if no particles at all. 
    """
    
    if not swarmId in self._swarmNumParticlesPerGeneration:
      return None
    
    numPsPerGen = self._swarmNumParticlesPerGeneration[swarmId]

    numPsPerGen = numpy.array(numPsPerGen)
    firstNonFull = numpy.where(numPsPerGen < minNumParticles)[0]
    if len(firstNonFull) == 0:
      return len(numPsPerGen)
    else:
      return firstNonFull[0]

  def highestGeneration(self, swarmId):
    """ Return the generation index of the highest generation in the given
    swarm.

    Parameters:
    ---------------------------------------------------------------------
    swarmId:  A string representation of the sorted list of encoders in this
                 swarm. For example '__address_encoder.__gym_encoder'
    retval:  generation index
    """
    numPsPerGen = self._swarmNumParticlesPerGeneration[swarmId]
    return len(numPsPerGen)-1

  def getParticleBest(self, particleId):
    """ Return the best score and position for a given particle. The position
    is given as a dict, with varName:varPosition items in it.

    Parameters:
    ---------------------------------------------------------------------
    particleId:    which particle
    retval:        (bestResult, bestPosition)
    """
    return self._particleBest.get(particleId, (None, None))

  def getResultsPerChoice(self, swarmId, maxGenIdx, varName):
    """ Return a dict of the errors obtained on models that were run with
    each value from a PermuteChoice variable.

    For example, if a PermuteChoice variable has the following choices:
      ['a', 'b', 'c']

    The dict will have 3 elements. The keys are the stringified choiceVars, 
    and each value is tuple containing (choiceVar, errors) where choiceVar is 
    the original form of the choiceVar (before stringification) and errors is 
    the list of errors received from models that used the specific choice:
    retval:
      ['a':('a', [0.1, 0.2, 0.3]), 'b':('b', [0.5, 0.1, 0.6]), 'c':('c', [])]


    Parameters:
    ---------------------------------------------------------------------
    swarmId:  swarm Id of the swarm to retrieve info from
    maxGenIdx: max generation index to consider from other models, ignored
                if None
    varName:  which variable to retrieve

    retval:  list of the errors obtained from each choice.
    """
    results = dict()
    # Get all the completed particles in this swarm
    (allParticles, _, resultErrs, _, _) = self.getParticleInfos(swarmId,
                                              genIdx=None, matured=True)

    for particleState, resultErr in itertools.izip(allParticles, resultErrs):
      # Consider this generation?
      if maxGenIdx is not None:
        if particleState['genIdx'] > maxGenIdx:
          continue

      # Ignore unless this model completed successfully
      if resultErr == numpy.inf:
        continue

      position = Particle.getPositionFromState(particleState)
      varPosition = position[varName]
      varPositionStr = str(varPosition)
      if varPositionStr in results:
        results[varPositionStr][1].append(resultErr)
      else:
        results[varPositionStr] = (varPosition, [resultErr])

    return results


class Particle(object):
  """Construct a particle. Each particle evaluates one or more models
  serially. Each model represents a position that the particle is evaluated
  at.

  Each position is a set of values chosen for each of the permutation variables.
  The particle's best position is the value of the permutation variables when it
  did best on the optimization metric.

  Some permutation variables are treated like traditional particle swarm
  variables - that is they have a position and velocity. Others are simply
  choice variables, for example a list of strings. We follow a different
  methodology for choosing each permutation variable value depending on its
  type.

  A particle belongs to 1 and only 1 swarm. A swarm is a collection of particles
  that all share the same global best position. A swarm is identified by its
  specific combination of fields. If we are evaluating multiple different field
  combinations, then there will be multiple swarms. A Hypersearch Worker (HSW)
  will only instantiate and run one particle at a time. When done running a
  particle, another worker can pick it up, pick a new position, for it and run
  it based on the particle state information which is stored in each model table
  entry.

  Each particle has a generationIdx. It starts out at generation #0. Every time
  a model evaluation completes and the particle is moved to a different position
  (to evaluate a different model), the generation index is incremented.

  Every particle that is created has a unique particleId. The particleId
  is a string formed as '<workerConnectionId>.<particleIdx>', where particleIdx
  starts at 0 for each worker and increments by 1 every time a new particle
  is created by that worker.
  """

  _nextParticleID = 0

  def __init__(self, hsObj, resultsDB, flattenedPermuteVars,
               swarmId=None, newFarFrom=None, evolveFromState=None,
               newFromClone=None, newParticleId=False):
    """ Create a particle.

    There are 3 fundamentally different methods of instantiating a particle:
    1.) You can instantiate a new one from scratch, at generation index #0. This
          particle gets a new particleId.
            required: swarmId
            optional: newFarFrom
            must be None: evolveFromState, newFromClone

    2.) You can instantiate one from savedState, in which case it's generation
          index is incremented (from the value stored in the saved state) and
          its particleId remains the same.
            required: evolveFromState
            optional:
            must be None: flattenedPermuteVars, swarmId, newFromClone

    3.) You can clone another particle, creating a new particle at the same
          generationIdx but a different particleId. This new particle will end
          up at exactly the same position as the one it was cloned from. If
          you want to move it to the next position, or just jiggle it a bit, call
          newPosition() or agitate() after instantiation.
            required: newFromClone
            optional:
            must be None: flattenedPermuteVars, swarmId, evolveFromState


    Parameters:
    --------------------------------------------------------------------
    hsObj:    The HypersearchV2 instance

    resultsDB: the ResultsDB instance that holds all the model results

    flattenedPermuteVars: dict() containing the (key, PermuteVariable) pairs
          of the  flattened permutation variables as read from the permutations
          file.

    swarmId: String that represents the encoder names of the encoders that are
          to be included in this particle's model. Of the form
          'encoder1.encoder2'.
          Required for creation method #1.

    newFarFrom: If not None, this is a list of other particleState dicts in the
          swarm that we want to be as far away from as possible. Optional
          argument for creation method #1.

    evolveFromState: If not None, evolve an existing particle. This is a
          dict containing the particle's state. Preserve the particleId, but
          increment the generation index. Required for creation method #2.

    newFromClone: If not None, clone this other particle's position and generation
          index, with small random perturbations. This is a dict containing the
          particle's state. Required for creation method #3.
          
    newParticleId: Only applicable when newFromClone is True. Give the clone
          a new particle ID. 
    
    """
    # Save constructor arguments
    self._hsObj = hsObj
    self.logger = hsObj.logger
    self._resultsDB = resultsDB

    # See the random number generator used for all the variables in this
    # particle. We will seed it differently based on the construction method,
    # below.
    self._rng = random.Random()
    self._rng.seed(42)

    # Setup our variable set by taking what's in flattenedPermuteVars and
    # stripping out vars that belong to encoders we are not using.
    def _setupVars(flattenedPermuteVars):
      allowedEncoderNames = self.swarmId.split('.')
      self.permuteVars = copy.deepcopy(flattenedPermuteVars)

      # Remove fields we don't want.
      varNames = self.permuteVars.keys()
      for varName in varNames:
        # Remove encoders we're not using
        if ':' in varName:    # if an encoder
          if varName.split(':')[0] not in allowedEncoderNames:
            self.permuteVars.pop(varName)
            continue

        # All PermuteChoice variables need to know all prior results obtained
        # with each choice.
        if isinstance(self.permuteVars[varName], PermuteChoices):
          if self._hsObj._speculativeParticles:
            maxGenIdx = None
          else:
            maxGenIdx = self.genIdx-1

          resultsPerChoice = self._resultsDB.getResultsPerChoice(
              swarmId=self.swarmId, maxGenIdx=maxGenIdx, varName=varName)
          self.permuteVars[varName].setResultsPerChoice(
              resultsPerChoice.values())

    # Method #1
    # Create from scratch, optionally pushing away from others that already
    #  exist.
    if swarmId is not None:
      assert (evolveFromState is None)
      assert (newFromClone is None)

      # Save construction param
      self.swarmId = swarmId

      # Assign a new unique ID to this particle
      self.particleId = "%s.%s" % (str(self._hsObj._workerID),
                                   str(Particle._nextParticleID))
      Particle._nextParticleID += 1

      # Init the generation index
      self.genIdx = 0

      # Setup the variables to initial locations.
      _setupVars(flattenedPermuteVars)

      # Push away from other particles?
      if newFarFrom is not None:
        for varName in self.permuteVars.iterkeys():
          otherPositions = []
          for particleState in newFarFrom:
            otherPositions.append(particleState['varStates'][varName]['position'])
          self.permuteVars[varName].pushAwayFrom(otherPositions, self._rng)

          # Give this particle a unique seed.
          self._rng.seed(str(otherPositions))

    # Method #2
    # Instantiate from saved state, preserving particleId but incrementing
    #  generation index.
    elif evolveFromState is not None:
      assert (swarmId is None)
      assert (newFarFrom is None)
      assert (newFromClone is None)

      # Setup other variables from saved state
      self.particleId = evolveFromState['id']
      self.genIdx = evolveFromState['genIdx'] + 1
      self.swarmId = evolveFromState['swarmId']

      # Setup the variables to initial locations.
      _setupVars(flattenedPermuteVars)

      # Override the position and velocity of each variable from
      #  saved state
      self.initStateFrom(self.particleId, evolveFromState, newBest=True)

      # Move it to the next position. We need the swarm best for this.
      self.newPosition()

    # Method #3
    # Clone another particle, producing a new particle at the same genIdx with
    #  the same particleID. This is used to re-run an orphaned model.
    elif newFromClone is not None:
      assert (swarmId is None)
      assert (newFarFrom is None)
      assert (evolveFromState is None)

      # Setup other variables from clone particle
      self.particleId = newFromClone['id']
      if newParticleId:
        self.particleId = "%s.%s" % (str(self._hsObj._workerID),
                                     str(Particle._nextParticleID))
        Particle._nextParticleID += 1
        
      self.genIdx = newFromClone['genIdx']
      self.swarmId = newFromClone['swarmId']

      # Setup the variables to initial locations.
      _setupVars(flattenedPermuteVars)

      # Override the position and velocity of each variable from
      #  the clone
      self.initStateFrom(self.particleId, newFromClone, newBest=False)

    else:
      assert False, "invalid creation parameters"

    # Log it
    self.logger.debug("Created particle: %s" % (str(self)))

  def __repr__(self):
    return "Particle(swarmId=%s) [particleId=%s, genIdx=%d, " \
        "permuteVars=\n%s]" % (self.swarmId, self.particleId,
        self.genIdx, pprint.pformat(self.permuteVars, indent=4))

  def getState(self):
    """Get the particle state as a dict. This is enough information to
    instantiate this particle on another worker."""
    varStates = dict()
    for varName, var in self.permuteVars.iteritems():
      varStates[varName] = var.getState()

    return dict(id = self.particleId,
                genIdx = self.genIdx,
                swarmId = self.swarmId,
                varStates = varStates)

  def initStateFrom(self, particleId, particleState, newBest):
    """Init all of our variable positions, velocities, and optionally the best
    result and best position from the given particle.

    If newBest is true, we get the best result and position for this new
    generation from the resultsDB, This is used when evoloving a particle
    because the bestResult and position as stored in was the best AT THE TIME
    THAT PARTICLE STARTED TO RUN and does not include the best since that
    particle completed.
    """
    # Get the update best position and result?
    if newBest:
      (bestResult, bestPosition) = self._resultsDB.getParticleBest(particleId)
    else:
      bestResult = bestPosition = None

    # Replace with the position and velocity of each variable from
    #  saved state
    varStates = particleState['varStates']
    for varName in varStates.keys():
      varState = copy.deepcopy(varStates[varName])
      if newBest:
        varState['bestResult'] = bestResult
      if bestPosition is not None:
        varState['bestPosition'] = bestPosition[varName]
      self.permuteVars[varName].setState(varState)

  def copyEncoderStatesFrom(self, particleState):
    """Copy all encoder variables from particleState into this particle.

    Parameters:
    --------------------------------------------------------------
    particleState:        dict produced by a particle's getState() method
    """
    # Set this to false if you don't want the variable to move anymore
    #  after we set the state
    allowedToMove = True

    for varName in particleState['varStates']:
      if ':' in varName:    # if an encoder

        # If this particle doesn't include this field, don't copy it
        if varName not in self.permuteVars:
          continue

        # Set the best position to the copied position
        state = copy.deepcopy(particleState['varStates'][varName])
        state['_position'] = state['position']
        state['bestPosition'] = state['position']

        if not allowedToMove:
          state['velocity'] = 0

        # Set the state now
        self.permuteVars[varName].setState(state)

        if allowedToMove:
          # Let the particle move in both directions from the best position
          #  it found previously and set it's initial velocity to a known
          #  fraction of the total distance.
          self.permuteVars[varName].resetVelocity(self._rng)

  def copyVarStatesFrom(self, particleState, varNames):
    """Copy specific variables from particleState into this particle.

    Parameters:
    --------------------------------------------------------------
    particleState:        dict produced by a particle's getState() method
    varNames:             which variables to copy
    """
    # Set this to false if you don't want the variable to move anymore
    #  after we set the state
    allowedToMove = True

    for varName in particleState['varStates']:
      if varName in varNames:    

        # If this particle doesn't include this field, don't copy it
        if varName not in self.permuteVars:
          continue

        # Set the best position to the copied position
        state = copy.deepcopy(particleState['varStates'][varName])
        state['_position'] = state['position']
        state['bestPosition'] = state['position']

        if not allowedToMove:
          state['velocity'] = 0

        # Set the state now
        self.permuteVars[varName].setState(state)

        if allowedToMove:
          # Let the particle move in both directions from the best position
          #  it found previously and set it's initial velocity to a known
          #  fraction of the total distance.
          self.permuteVars[varName].resetVelocity(self._rng)


  def getPosition(self):
    """Return the position of this particle. This returns a dict() of key
    value pairs where each key is the name of the flattened permutation
    variable and the value is its chosen value.

    Parameters:
    --------------------------------------------------------------
    retval:     dict() of flattened permutation choices
    """
    result = dict()
    for (varName, value) in self.permuteVars.iteritems():
      result[varName] = value.getPosition()

    return result

  @staticmethod
  def getPositionFromState(pState):
    """Return the position of a particle given its state dict.

    Parameters:
    --------------------------------------------------------------
    retval:     dict() of particle position, keys are the variable names,
                  values are their positions
    """
    result = dict()
    for (varName, value) in pState['varStates'].iteritems():
      result[varName] = value['position']

    return result

  def agitate(self):
    """Agitate this particle so that it is likely to go to a new position.
    Every time agitate is called, the particle is jiggled an even greater
    amount.

    Parameters:
    --------------------------------------------------------------
    retval:               None
    """
    for (varName, var) in self.permuteVars.iteritems():
      var.agitate()

    self.newPosition()

  def newPosition(self, whichVars=None):
    # TODO: incorporate data from choice variables....
    # TODO: make sure we're calling this when appropriate.
    """Choose a new position based on results obtained so far from all other
    particles.

    Parameters:
    --------------------------------------------------------------
    whichVars:       If not None, only move these variables
    retval:               new position
    """
    # Get the global best position for this swarm generation
    globalBestPosition = None
    # If speculative particles are enabled, use the global best considering
    #  even particles in the current generation. This gives better results
    #  but does not provide repeatable results because it depends on
    #  worker timing
    if self._hsObj._speculativeParticles:
      genIdx = self.genIdx
    else:
      genIdx = self.genIdx - 1

    if genIdx >= 0:
      (bestModelId, _) = self._resultsDB.bestModelIdAndErrScore(self.swarmId, genIdx)
      if bestModelId is not None:
        (particleState, _, _, _, _) = self._resultsDB.getParticleInfo(bestModelId)
        globalBestPosition = Particle.getPositionFromState(particleState)

    # Update each variable
    for (varName, var) in self.permuteVars.iteritems():
      if whichVars is not None and varName not in whichVars:
        continue
      if globalBestPosition is None:
        var.newPosition(None, self._rng)
      else:
        var.newPosition(globalBestPosition[varName], self._rng)

    # get the new position
    position = self.getPosition()

    # Log the new position
    if self.logger.getEffectiveLevel() <= logging.DEBUG:
      msg = StringIO.StringIO()
      print >> msg, "New particle position: \n%s" % (pprint.pformat(position,
                                                      indent=4))
      print >> msg, "Particle variables:"
      for (varName, var) in self.permuteVars.iteritems():
        print >> msg, "  %s: %s" % (varName, str(var))
      self.logger.debug(msg.getvalue())
      msg.close()

    return position


class HsState(object):
  """This class encapsulates the Hypersearch state which we share with all
  other workers. This state gets serialized into a JSON dict and written to
  the engWorkerState field of the job record.

  Whenever a worker changes this state, it does an atomic setFieldIfEqual to
  insure it has the latest state as updated by any other worker as a base.

  Here is an example snapshot of this state information:
  swarms = {'a': {'status': 'completed',        # 'active','completing','completed',
                                               # or 'killed'
                   'bestModelId': <modelID>,   # Only set for 'completed' swarms
                   'bestErrScore': <errScore>, # Only set for 'completed' swarms
                   'sprintIdx': 0,
                   },
           'a.b': {'status': 'active',
                   'bestModelId': None,
                   'bestErrScore': None,
                   'sprintIdx': 1,
                  }
           }

  sprints = [{'status': 'completed',      # 'active','completing','completed'
              'bestModelId': <modelID>,   # Only set for 'completed' sprints
              'bestErrScore': <errScore>, # Only set for 'completed' sprints
             },
             {'status': 'completing',
              'bestModelId': <None>,
              'bestErrScore': <None>
             }
             {'status': 'active',
              'bestModelId': None
              'bestErrScore': None
             }
             ]
  """

  def __init__(self, hsObj):
    """ Create our state object.

    Parameters:
    ---------------------------------------------------------------------
    hsObj:     Reference to the HypersesarchV2 instance
    cjDAO:     ClientJobsDAO instance
    logger:    logger to use
    jobID:     our JobID
    """
    # Save constructor parameters
    self._hsObj = hsObj

    # Convenient access to the logger
    self.logger = self._hsObj.logger

    # This contains our current state, and local working changes
    self._state = None

    # This contains the state we last read from the database
    self._priorStateJSON = None

    # Set when we make a change to our state locally
    self._dirty = False

    # Read in the initial state
    self.readStateFromDB()

  def isDirty(self):
    """Return true if our local copy of the state has changed since the
    last time we read from the DB.
    """
    return self._dirty

  def isSearchOver(self):
    """Return true if the search should be considered over."""
    return self._state['searchOver']

  def readStateFromDB(self):
    """Set our state to that obtained from the engWorkerState field of the
    job record.


    Parameters:
    ---------------------------------------------------------------------
    stateJSON:    JSON encoded state from job record

    """
    self._priorStateJSON = self._hsObj._cjDAO.jobGetFields(self._hsObj._jobID,
                                                    ['engWorkerState'])[0]

    # Init if no prior state yet
    if self._priorStateJSON is None:
      swarms = dict()

      # Fast Swarm, first and only sprint has one swarm for each field
      # in fixedFields 
      if self._hsObj._fixedFields is not None:
        print self._hsObj._fixedFields
        encoderSet = []
        for field in self._hsObj._fixedFields:
            if field =='_classifierInput':
              continue
            encoderName = self.getEncoderKeyFromName(field)
            assert encoderName in self._hsObj._encoderNames, "The field '%s' " \
              " specified in the fixedFields list is not present in this " \
              " model." % (field)
            encoderSet.append(encoderName)
        encoderSet.sort()
        swarms['.'.join(encoderSet)] = {
                                'status': 'active',
                                'bestModelId': None,
                                'bestErrScore': None,
                                'sprintIdx': 0,
                                }
      # Temporal prediction search, first sprint has N swarms of 1 field each,
      #  the predicted field may or may not be that one field. 
      elif self._hsObj._searchType == HsSearchType.temporal:
        for encoderName in self._hsObj._encoderNames:
          swarms[encoderName] = {
                                  'status': 'active',
                                  'bestModelId': None,
                                  'bestErrScore': None,
                                  'sprintIdx': 0,
                                  }


      # Classification prediction search, first sprint has N swarms of 1 field
      #  each where this field can NOT be the predicted field. 
      elif self._hsObj._searchType == HsSearchType.classification:
        for encoderName in self._hsObj._encoderNames:
          if encoderName == self._hsObj._predictedFieldEncoder:
            continue
          swarms[encoderName] = {
                                  'status': 'active',
                                  'bestModelId': None,
                                  'bestErrScore': None,
                                  'sprintIdx': 0,
                                  }
          
      # Legacy temporal. This is either a model that uses reconstruction or
      #  an older multi-step model that doesn't have a separate 
      #  'classifierOnly' encoder for the predicted field. Here, the predicted 
      #  field must ALWAYS be present and the first sprint tries the predicted 
      #  field only
      elif self._hsObj._searchType == HsSearchType.legacyTemporal:
        swarms[self._hsObj._predictedFieldEncoder] = {
                       'status': 'active',
                       'bestModelId': None,
                       'bestErrScore': None,
                       'sprintIdx': 0,
                       }

      else:
        raise RuntimeError("Unsupported search type: %s" % \
                            (self._hsObj._searchType))

      # Initialize the state.
      self._state = dict(
        # The last time the state was updated by a worker.
        lastUpdateTime = time.time(),

        # Set from within setSwarmState() if we detect that the sprint we just
        #  completed did worse than a prior sprint. This stores the index of
        #  the last good sprint.
        lastGoodSprint = None,

        # Set from within setSwarmState() if lastGoodSprint is True and all
        #  sprints have completed.
        searchOver = False,

        # This is a summary of the active swarms - this information can also
        #  be obtained from the swarms entry that follows, but is summarized here
        #  for easier reference when viewing the state as presented by
        #  log messages and prints of the hsState data structure (by
        #  permutations_runner).
        activeSwarms = swarms.keys(),

        # All the swarms that have been created so far.
        swarms = swarms,

        # All the sprints that have completed or are in progress.
        sprints = [{'status': 'active',
                    'bestModelId': None,
                    'bestErrScore': None}],

        # The list of encoders we have "blacklisted" because they
        #  performed so poorly.
        blackListedEncoders = [],
        )

      # This will do nothing if the value of engWorkerState is not still None.
      self._hsObj._cjDAO.jobSetFieldIfEqual(
          self._hsObj._jobID, 'engWorkerState', json.dumps(self._state), None)

      self._priorStateJSON = self._hsObj._cjDAO.jobGetFields(
          self._hsObj._jobID, ['engWorkerState'])[0]
      assert (self._priorStateJSON is not None)

    # Read state from the database
    self._state = json.loads(self._priorStateJSON)
    self._dirty = False

  def writeStateToDB(self):
    """Update the state in the job record with our local changes (if any).
    If we don't have the latest state in our priorStateJSON, then re-load
    in the latest state and return False. If we were successful writing out
    our changes, return True

    Parameters:
    ---------------------------------------------------------------------
    retval:    True if we were successful writing out our changes
               False if our priorState is not the latest that was in the DB.
               In this case, we will re-load our state from the DB
    """
    # If no changes, do nothing
    if not self._dirty:
      return True

    # Set the update time
    self._state['lastUpdateTime'] = time.time()
    newStateJSON = json.dumps(self._state)
    success = self._hsObj._cjDAO.jobSetFieldIfEqual(self._hsObj._jobID,
                'engWorkerState', str(newStateJSON), str(self._priorStateJSON))

    if success:
      self.logger.debug("Success changing hsState to: \n%s " % \
                       (pprint.pformat(self._state, indent=4)))
      self._priorStateJSON = newStateJSON

    # If no success, read in the current state from the DB
    else:
      self.logger.debug("Failed to change hsState to: \n%s " % \
                       (pprint.pformat(self._state, indent=4)))

      self._priorStateJSON = self._hsObj._cjDAO.jobGetFields(self._hsObj._jobID,
                                                      ['engWorkerState'])[0]
      self._state =  json.loads(self._priorStateJSON)

      self.logger.info("New hsState has been set by some other worker to: "
                       " \n%s" % (pprint.pformat(self._state, indent=4)))

    return success


  def getEncoderNameFromKey(self, key):
    """ Given an encoder dictionary key, get the encoder name. 
    
    Encoders are a sub-dict within model params, and in HSv2, their key
    is structured like this for example:
       'modelParams|sensorParams|encoders|home_winloss'
       
    The encoderName is the last word in the | separated key name
    """
    return key.split('|')[-1]
    

  def getEncoderKeyFromName(self, name):
    """ Given an encoder name, get the key. 
    
    Encoders are a sub-dict within model params, and in HSv2, their key
    is structured like this for example:
       'modelParams|sensorParams|encoders|home_winloss'
       
    The encoderName is the last word in the | separated key name
    """
    return 'modelParams|sensorParams|encoders|%s' % (name)


  def getFieldContributions(self):
    """Return the field contributions statistics.

    Parameters:
    ---------------------------------------------------------------------
    retval:   Dictionary where the keys are the field names and the values
                are how much each field contributed to the best score.
    """

    #in the fast swarm, there is only 1 sprint and field contributions are 
    #not defined
    if self._hsObj._fixedFields is not None:
      return dict(), dict()
    # Get the predicted field encoder name    
    predictedEncoderName = self._hsObj._predictedFieldEncoder
    
    # -----------------------------------------------------------------------
    # Collect all the single field scores
    fieldScores = []
    for swarmId, info in self._state['swarms'].iteritems():
      encodersUsed = swarmId.split('.')
      if len(encodersUsed) != 1:
        continue
      field = self.getEncoderNameFromKey(encodersUsed[0])
      bestScore = info['bestErrScore']
      
      # If the bestScore is None, this swarm hasn't completed yet (this could
      #  happen if we're exiting because of maxModels), so look up the best
      #  score so far
      if bestScore is None:
        (_modelId, bestScore) = \
            self._hsObj._resultsDB.bestModelIdAndErrScore(swarmId)

      fieldScores.append((bestScore, field))
      
      
    # -----------------------------------------------------------------------
    # If we only have 1 field that was tried in the first sprint, then use that 
    #  as the base and get the contributions from the fields in the next sprint. 
    if self._hsObj._searchType == HsSearchType.legacyTemporal:
      assert(len(fieldScores)==1)
      (baseErrScore, baseField) = fieldScores[0]
      
      for swarmId, info in self._state['swarms'].iteritems():
        encodersUsed = swarmId.split('.')
        if len(encodersUsed) != 2:
          continue

        fields = [self.getEncoderNameFromKey(name) for name in encodersUsed]
        fields.remove(baseField)
        
        fieldScores.append((info['bestErrScore'], fields[0]))
        
    # The first sprint tried a bunch of fields, pick the worst performing one
    #  (within the top self._hsObj._maxBranching ones) as the base 
    else:
      fieldScores.sort(reverse=True)
      
      # If maxBranching was specified, pick the worst performing field within
      #  the top maxBranching+1 fields as our base, which will give that field 
      #  a contribution of 0. 
      if self._hsObj._maxBranching > 0 \
              and len(fieldScores) > self._hsObj._maxBranching: 
        baseErrScore = fieldScores[-self._hsObj._maxBranching-1][0]
      else:
        baseErrScore = fieldScores[0][0]
      
      
    # -----------------------------------------------------------------------
    # Prepare and return the fieldContributions dict
    pctFieldContributionsDict = dict()
    absFieldContributionsDict = dict()
    
    # If we have no base score, can't compute field contributions. This can
    #  happen when we exit early due to maxModels or being cancelled
    if baseErrScore is not None:      
    
      # If the base error score is 0, we can't compute a percent difference
      #  off of it, so move it to a very small float
      if abs(baseErrScore) < 0.00001:
        baseErrScore = 0.00001
      for (errScore, field) in fieldScores:
        if errScore is not None:
          pctBetter = (baseErrScore - errScore) * 100.0 / baseErrScore
        else:
          pctBetter = 0.0
          errScore = baseErrScore   # for absFieldContribution 
        
        pctFieldContributionsDict[field] = pctBetter
        absFieldContributionsDict[field] = baseErrScore - errScore
      
    self.logger.debug("FieldContributions: %s" % (pctFieldContributionsDict))
    return pctFieldContributionsDict, absFieldContributionsDict
     
    
  def getAllSwarms(self, sprintIdx):
    """Return the list of all swarms in the given sprint.

    Parameters:
    ---------------------------------------------------------------------
    retval:   list of active swarm Ids in the given sprint
    """
    swarmIds = []
    for swarmId, info in self._state['swarms'].iteritems():
      if info['sprintIdx'] == sprintIdx:
        swarmIds.append(swarmId)

    return swarmIds

  def getActiveSwarms(self, sprintIdx=None):
    """Return the list of active swarms in the given sprint. These are swarms
    which still need new particles created in them.

    Parameters:
    ---------------------------------------------------------------------
    sprintIdx:    which sprint to query. If None, get active swarms from all
                      sprints
    retval:   list of active swarm Ids in the given sprint
    """
    swarmIds = []
    for swarmId, info in self._state['swarms'].iteritems():
      if sprintIdx is not None and info['sprintIdx'] != sprintIdx:
        continue
      if info['status'] == 'active':
        swarmIds.append(swarmId)

    return swarmIds

  def getNonKilledSwarms(self, sprintIdx):
    """Return the list of swarms in the given sprint that were not killed.
    This is called when we are trying to figure out which encoders to carry
    forward to the next sprint. We don't want to carry forward encoder
    combintations which were obviously bad (in killed swarms).

    Parameters:
    ---------------------------------------------------------------------
    retval:   list of active swarm Ids in the given sprint
    """
    swarmIds = []
    for swarmId, info in self._state['swarms'].iteritems():
      if info['sprintIdx'] == sprintIdx and info['status'] != 'killed':
        swarmIds.append(swarmId)

    return swarmIds

  def getCompletedSwarms(self):
    """Return the list of all completed swarms.

    Parameters:
    ---------------------------------------------------------------------
    retval:   list of active swarm Ids
    """
    swarmIds = []
    for swarmId, info in self._state['swarms'].iteritems():
      if info['status'] == 'completed':
        swarmIds.append(swarmId)

    return swarmIds

  def getCompletingSwarms(self):
    """Return the list of all completing swarms.

    Parameters:
    ---------------------------------------------------------------------
    retval:   list of active swarm Ids
    """
    swarmIds = []
    for swarmId, info in self._state['swarms'].iteritems():
      if info['status'] == 'completing':
        swarmIds.append(swarmId)

    return swarmIds

  def bestModelInCompletedSwarm(self, swarmId):
    """Return the best model ID and it's errScore from the given swarm.
    If the swarm has not completed yet, the bestModelID will be None.

    Parameters:
    ---------------------------------------------------------------------
    retval:   (modelId, errScore)
    """
    swarmInfo = self._state['swarms'][swarmId]
    return (swarmInfo['bestModelId'],
            swarmInfo['bestErrScore'])

  def bestModelInCompletedSprint(self, sprintIdx):
    """Return the best model ID and it's errScore from the given sprint.
    If the sprint has not completed yet, the bestModelID will be None.

    Parameters:
    ---------------------------------------------------------------------
    retval:   (modelId, errScore)
    """
    sprintInfo = self._state['sprints'][sprintIdx]
    return (sprintInfo['bestModelId'],
            sprintInfo['bestErrScore'])

  def bestModelInSprint(self, sprintIdx):
    """Return the best model ID and it's errScore from the given sprint,
    which may still be in progress. This returns the best score from all models
    in the sprint which have matured so far.

    Parameters:
    ---------------------------------------------------------------------
    retval:   (modelId, errScore)
    """
    # Get all the swarms in this sprint
    swarms = self.getAllSwarms(sprintIdx)

    # Get the best model and score from each swarm
    bestModelId = None
    bestErrScore = numpy.inf
    for swarmId in swarms:
      (modelId, errScore) = self._hsObj._resultsDB.bestModelIdAndErrScore(swarmId)
      if errScore < bestErrScore:
        bestModelId = modelId
        bestErrScore = errScore

    return (bestModelId, bestErrScore)

  def setSwarmState(self, swarmId, newStatus):
    """Change the given swarm's state to 'newState'. If 'newState' is
    'completed', then bestModelId and bestErrScore must be provided.

    Parameters:
    ---------------------------------------------------------------------
    swarmId:      swarm Id
    newStatus:    new status, either 'active', 'completing', 'completed', or
                    'killed'
    """
    assert (newStatus in ['active', 'completing', 'completed', 'killed'])

    # Set the swarm status
    swarmInfo = self._state['swarms'][swarmId]
    if swarmInfo['status'] == newStatus:
      return

    # If some other worker noticed it as completed, setting it to completing
    #  is obviously old information....
    if swarmInfo['status'] == 'completed' and newStatus == 'completing':
      return

    self._dirty = True
    swarmInfo['status'] = newStatus
    if newStatus == 'completed':
      (modelId, errScore) = self._hsObj._resultsDB.bestModelIdAndErrScore(swarmId)
      swarmInfo['bestModelId'] = modelId
      swarmInfo['bestErrScore'] = errScore

    # If no longer active, remove it from the activeSwarms entry
    if newStatus != 'active' and swarmId in self._state['activeSwarms']:
      self._state['activeSwarms'].remove(swarmId)

    # If new status is 'killed', kill off any running particles in that swarm
    if newStatus=='killed':
      self._hsObj.killSwarmParticles(swarmId)

    # In case speculative particles are enabled, make sure we generate a new
    #  swarm at this time if all of the swarms in the current sprint have
    #  completed. This will insure that we don't mark the sprint as completed
    #  before we've created all the possible swarms.
    sprintIdx = swarmInfo['sprintIdx']
    self.isSprintActive(sprintIdx)

    # Update the sprint status. Check all the swarms that belong to this sprint.
    #  If they are all completed, the sprint is completed.
    sprintInfo = self._state['sprints'][sprintIdx]

    statusCounts = dict(active=0, completing=0, completed=0, killed=0)
    bestModelIds = []
    bestErrScores = []
    for info in self._state['swarms'].itervalues():
      if info['sprintIdx'] != sprintIdx:
        continue
      statusCounts[info['status']] += 1
      if info['status'] == 'completed':
        bestModelIds.append(info['bestModelId'])
        bestErrScores.append(info['bestErrScore'])

    if statusCounts['active'] > 0:
      sprintStatus = 'active'
    elif statusCounts['completing'] > 0:
      sprintStatus = 'completing'
    else:
      sprintStatus = 'completed'
    sprintInfo['status'] = sprintStatus

    # If the sprint is complete, get the best model from all of its swarms and
    #  store that as the sprint best
    if sprintStatus == 'completed':
      if len(bestErrScores) > 0:
        whichIdx = numpy.array(bestErrScores).argmin()
        sprintInfo['bestModelId'] = bestModelIds[whichIdx]
        sprintInfo['bestErrScore'] = bestErrScores[whichIdx]
      else:
        # This sprint was empty, most likely because all particles were
        #  killed. Give it a huge error score
        sprintInfo['bestModelId'] = 0
        sprintInfo['bestErrScore'] = numpy.inf
        

      # See if our best err score got NO BETTER as compared to a previous
      #  sprint. If so, stop exploring subsequent sprints (lastGoodSprint
      #  is no longer None).
      bestPrior = numpy.inf
      for idx in range(sprintIdx):
        if self._state['sprints'][idx]['status'] == 'completed':
          (_, errScore) = self.bestModelInCompletedSprint(idx)
          if errScore is None:
            errScore = numpy.inf
        else:
          errScore = numpy.inf
        if errScore < bestPrior:
          bestPrior = errScore

      if sprintInfo['bestErrScore'] >= bestPrior:
        self._state['lastGoodSprint'] = sprintIdx-1

      # If ALL sprints up to the last good one are done, the search is now over
      if self._state['lastGoodSprint'] is not None \
            and not self.anyGoodSprintsActive():
        self._state['searchOver'] = True

  def anyGoodSprintsActive(self):
    """Return True if there are any more good sprints still being explored.
    A 'good' sprint is one that is earlier than where we detected an increase
    in error from sprint to subsequent sprint.
    """
    if self._state['lastGoodSprint'] is not None:
      goodSprints = self._state['sprints'][0:self._state['lastGoodSprint']+1]
    else:
      goodSprints = self._state['sprints']

    for sprint in goodSprints:
      if sprint['status'] == 'active':
        anyActiveSprints = True
        break
    else:
      anyActiveSprints = False

    return anyActiveSprints

  def isSprintCompleted(self, sprintIdx):
    """Return True if the given sprint has completed."""
    numExistingSprints = len(self._state['sprints'])
    if sprintIdx >= numExistingSprints:
      return False

    return (self._state['sprints'][sprintIdx]['status'] == 'completed')

  def killUselessSwarms(self):
    """See if we can kill off some speculative swarms. If an earlier sprint
    has finally completed, we can now tell which fields should *really* be present
    in the sprints we've already started due to speculation, and kill off the
    swarms that should not have been included.
    """
    # Get number of existing sprints
    numExistingSprints = len(self._state['sprints'])

    # Should we bother killing useless swarms?
    if self._hsObj._searchType == HsSearchType.legacyTemporal:
      if numExistingSprints <= 2:
        return
    else:
      if numExistingSprints <= 1:
        return

    # Form completedSwarms as a list of tuples, each tuple contains:
    #  (swarmName, swarmState, swarmBestErrScore)
    # ex. completedSwarms:
    #    [('a', {...}, 1.4),
    #     ('b', {...}, 2.0),
    #     ('c', {...}, 3.0)]
    completedSwarms = self.getCompletedSwarms()
    completedSwarms = [(swarm, self._state["swarms"][swarm],
                        self._state["swarms"][swarm]["bestErrScore"]) \
                                                for swarm in completedSwarms]

    # Form the completedMatrix. Each row corresponds to a sprint. Each row
    #  contains the list of swarm tuples that belong to that sprint, sorted
    #  by best score. Each swarm tuple contains (swarmName, swarmState,
    #  swarmBestErrScore).
    # ex. completedMatrix:
    #    [(('a', {...}, 1.4), ('b', {...}, 2.0), ('c', {...}, 3.0)),
    #     (('a.b', {...}, 3.0), ('b.c', {...}, 4.0))] 
    completedMatrix = [[] for i in range(numExistingSprints)]
    for swarm in completedSwarms:
      completedMatrix[swarm[1]["sprintIdx"]].append(swarm)
    for sprint in completedMatrix:
      sprint.sort(key=itemgetter(2))

    # Form activeSwarms as a list of tuples, each tuple contains:
    #  (swarmName, swarmState, swarmBestErrScore)
    # Include all activeSwarms and completingSwarms
    # ex. activeSwarms:
    #    [('d', {...}, 1.4),
    #     ('e', {...}, 2.0),
    #     ('f', {...}, 3.0)]
    activeSwarms = self.getActiveSwarms()
    # Append the completing swarms
    activeSwarms.extend(self.getCompletingSwarms())
    activeSwarms = [(swarm, self._state["swarms"][swarm],
                     self._state["swarms"][swarm]["bestErrScore"]) \
                                                for swarm in activeSwarms]

    # Form the activeMatrix. Each row corresponds to a sprint. Each row
    #  contains the list of swarm tuples that belong to that sprint, sorted
    #  by best score. Each swarm tuple contains (swarmName, swarmState,
    #  swarmBestErrScore)
    # ex. activeMatrix:
    #    [(('d', {...}, 1.4), ('e', {...}, 2.0), ('f', {...}, 3.0)),
    #     (('d.e', {...}, 3.0), ('e.f', {...}, 4.0))] 
    activeMatrix = [[] for i in range(numExistingSprints)]
    for swarm in activeSwarms:
      activeMatrix[swarm[1]["sprintIdx"]].append(swarm)
    for sprint in activeMatrix:
      sprint.sort(key=itemgetter(2))

    
    # Figure out which active swarms to kill
    toKill = []
    for i in range(1, numExistingSprints):
      for swarm in activeMatrix[i]:
        curSwarmEncoders = swarm[0].split(".")

        # If previous sprint is complete, get the best swarm and kill all active
        #  sprints that are not supersets
        if(len(activeMatrix[i-1])==0):
          # If we are trying all possible 3 field combinations, don't kill any
          #  off in sprint 2 
          if i==2 and (self._hsObj._tryAll3FieldCombinations or \
                self._hsObj._tryAll3FieldCombinationsWTimestamps):
            pass
          else: 
            bestInPrevious = completedMatrix[i-1][0]
            bestEncoders = bestInPrevious[0].split('.')
            for encoder in bestEncoders:
              if not encoder in curSwarmEncoders:
                toKill.append(swarm)

        # if there are more than two completed encoders sets that are complete and
        # are worse than at least one active swarm in the previous sprint. Remove
        # any combinations that have any pair of them since they cannot have the best encoder.
        #elif(len(completedMatrix[i-1])>1):
        #  for completedSwarm in completedMatrix[i-1]:
        #    activeMatrix[i-1][0][2]<completed

    # Mark the bad swarms as killed
    if len(toKill) > 0:
      print "ParseMe: Killing encoders:" + str(toKill)
      
    for swarm in toKill:
      self.setSwarmState(swarm[0], "killed")

    return

  def isSprintActive(self, sprintIdx):
    """If the given sprint exists and is active, return active=True.

    If the sprint does not exist yet, this call will create it (and return
    active=True). If it already exists, but is completing or complete, return
    active=False.

    If sprintIdx is past the end of the possible sprints, return
      active=False, noMoreSprints=True

    IMPORTANT: When speculative particles are enabled, this call has some
    special processing to handle speculative sprints:

      * When creating a new speculative sprint (creating sprint N before
      sprint N-1 has completed), it initially only puts in only ONE swarm into
      the sprint.

      * Every time it is asked if sprint N is active, it also checks to see if
      it is time to add another swarm to the sprint, and adds a new swarm if
      appropriate before returning active=True

      * We decide it is time to add a new swarm to a speculative sprint when ALL
      of the currently active swarms in the sprint have all the workers they
      need (number of running (not mature) particles is _minParticlesPerSwarm).
      This means that we have capacity to run additional particles in a new
      swarm.

    It is expected that the sprints will be checked IN ORDER from 0 on up. (It
    is an error not to) The caller should always try to allocate from the first
    active sprint it finds. If it can't, then it can call this again to
    find/create the next active sprint.

    Parameters:
    ---------------------------------------------------------------------
    retval:   (active, noMoreSprints)
                active: True if the given sprint is active
                noMoreSprints: True if there are no more sprints possible
    """

    while True:
      numExistingSprints = len(self._state['sprints'])

      # If this sprint already exists, see if it is active
      if sprintIdx <= numExistingSprints-1:

        # With speculation off, it's simple, just return whether or not the
        #  asked for sprint has active status
        if not self._hsObj._speculativeParticles:
          active = (self._state['sprints'][sprintIdx]['status'] == 'active')
          return (active, False)

        # With speculation on, if the sprint is still marked active, we also
        #  need to see if it's time to add a new swarm to it.
        else:
          active = (self._state['sprints'][sprintIdx]['status'] == 'active')
          if not active:
            return (active, False)

          # See if all of the existing swarms are at capacity (have all the
          # workers they need):
          activeSwarmIds = self.getActiveSwarms(sprintIdx)
          swarmSizes = [self._hsObj._resultsDB.getParticleInfos(swarmId,
                              matured=False)[0] for swarmId in activeSwarmIds]
          notFullSwarms = [len(swarm) for swarm in swarmSizes \
                           if len(swarm) < self._hsObj._minParticlesPerSwarm]

          # If some swarms have room return that the swarm is active.
          if len(notFullSwarms) > 0:
            return (True, False)

          # If the existing swarms are at capacity, we will fall through to the
          #  logic below which tries to add a new swarm to the sprint.

      # Stop creating new sprints?
      if self._state['lastGoodSprint'] is not None:
        return (False, True)

      # if fixedFields is set, we are running a fast swarm and only run sprint0
      if self._hsObj._fixedFields is not None:
        return (False, True)

      # ----------------------------------------------------------------------
      # Get the best model (if there is one) from the prior sprint. That gives
      # us the base encoder set for the next sprint. For sprint zero make sure
      # it does not take the last sprintidx because of wrapping.
      if sprintIdx > 0  \
            and self._state['sprints'][sprintIdx-1]['status'] == 'completed':
        (bestModelId, _) = self.bestModelInCompletedSprint(sprintIdx-1)
        (particleState, _, _, _, _) = self._hsObj._resultsDB.getParticleInfo(
                                                                  bestModelId)
        bestSwarmId = particleState['swarmId']
        baseEncoderSets = [bestSwarmId.split('.')]

      # If there is no best model yet, then use all encoder sets from the prior
      #  sprint that were not killed
      else:
        bestSwarmId = None
        particleState = None
        # Build up more combinations, using ALL of the sets in the current
        #  sprint.
        baseEncoderSets = []
        for swarmId in self.getNonKilledSwarms(sprintIdx-1):
          baseEncoderSets.append(swarmId.split('.'))

      # ----------------------------------------------------------------------
      # Which encoders should we add to the current base set?
      encoderAddSet = []

      # If we have constraints on how many fields we carry forward into
      # subsequent sprints (either nupic.hypersearch.max.field.branching or
      # nupic.hypersearch.min.field.contribution was set), then be more
      # picky about which fields we add in.
      limitFields = False
      if self._hsObj._maxBranching > 0 \
            or self._hsObj._minFieldContribution >= 0:
        if self._hsObj._searchType == HsSearchType.temporal or \
            self._hsObj._searchType == HsSearchType.classification:
          if sprintIdx >= 1:
            limitFields = True
            baseSprintIdx = 0
        elif self._hsObj._searchType == HsSearchType.legacyTemporal: 
          if sprintIdx >= 2:
            limitFields = True
            baseSprintIdx = 1
        else:
          raise RuntimeError("Unimplemented search type %s" % \
                                  (self._hsObj._searchType))


      # Only add top _maxBranching encoders to the swarms?
      if limitFields:

        # Get field contributions to filter added fields
        pctFieldContributions, absFieldContributions = \
                                                self.getFieldContributions()
        toRemove = []
        self.logger.debug("FieldContributions min: %s" % \
                          (self._hsObj._minFieldContribution))
        for fieldname in pctFieldContributions:
          if pctFieldContributions[fieldname] < self._hsObj._minFieldContribution:
            self.logger.debug("FieldContributions removing: %s" % (fieldname))
            toRemove.append(self.getEncoderKeyFromName(fieldname))
          else:
            self.logger.debug("FieldContributions keeping: %s" % (fieldname))

        
        # Grab the top maxBranching base sprint swarms.
        swarms = self._state["swarms"]
        sprintSwarms = [(swarm, swarms[swarm]["bestErrScore"]) \
            for swarm in swarms if swarms[swarm]["sprintIdx"] == baseSprintIdx]
        sprintSwarms = sorted(sprintSwarms, key=itemgetter(1))
        if self._hsObj._maxBranching > 0:
          sprintSwarms = sprintSwarms[0:self._hsObj._maxBranching]

        # Create encoder set to generate further swarms.
        for swarm in sprintSwarms:
          swarmEncoders = swarm[0].split(".")
          for encoder in swarmEncoders:
            if not encoder in encoderAddSet:
              encoderAddSet.append(encoder)
        encoderAddSet = [encoder for encoder in encoderAddSet \
                         if not str(encoder) in toRemove]

      # If no limit on the branching or min contribution, simply use all of the
      # encoders.
      else:
        encoderAddSet = self._hsObj._encoderNames


      # -----------------------------------------------------------------------
      # Build up the new encoder combinations for the next sprint. 
      newSwarmIds = set()
      
      # See if the caller wants to try more extensive field combinations with
      #  3 fields. 
      if (self._hsObj._searchType == HsSearchType.temporal \
           or self._hsObj._searchType == HsSearchType.legacyTemporal) \
          and sprintIdx == 2 \
          and (self._hsObj._tryAll3FieldCombinations or \
               self._hsObj._tryAll3FieldCombinationsWTimestamps):
        
        if self._hsObj._tryAll3FieldCombinations:
          newEncoders = set(self._hsObj._encoderNames)
          if self._hsObj._predictedFieldEncoder in newEncoders:
            newEncoders.remove(self._hsObj._predictedFieldEncoder)
        else:
          # Just make sure the timestamp encoders are part of the mix
          newEncoders = set(encoderAddSet)
          if self._hsObj._predictedFieldEncoder in newEncoders:
            newEncoders.remove(self._hsObj._predictedFieldEncoder)
          for encoder in self._hsObj._encoderNames:
            if encoder.endswith('_timeOfDay') or encoder.endswith('_weekend') \
                or encoder.endswith('_dayOfWeek'):
              newEncoders.add(encoder)
          
        allCombos = list(itertools.combinations(newEncoders, 2))
        for combo in allCombos:
          newSet = list(combo)
          newSet.append(self._hsObj._predictedFieldEncoder)
          newSet.sort()
          newSwarmId = '.'.join(newSet)
          if newSwarmId not in self._state['swarms']:
            newSwarmIds.add(newSwarmId)

            # If a speculative sprint, only add the first encoder, if not add
            #   all of them.
            if (len(self.getActiveSwarms(sprintIdx-1)) > 0):
              break
            
      # Else, we only build up by adding 1 new encoder to the best combination(s)
      #  we've seen from the prior sprint
      else:
        for baseEncoderSet in baseEncoderSets:
          for encoder in encoderAddSet:
            if encoder not in self._state['blackListedEncoders'] \
                and encoder not in baseEncoderSet:
              newSet = list(baseEncoderSet)
              newSet.append(encoder)
              newSet.sort()
              newSwarmId = '.'.join(newSet)
              if newSwarmId not in self._state['swarms']:
                newSwarmIds.add(newSwarmId)
  
                # If a speculative sprint, only add the first encoder, if not add
                #   all of them.
                if (len(self.getActiveSwarms(sprintIdx-1)) > 0):
                  break      
        
        
      # ----------------------------------------------------------------------
      # Sort the new swarm Ids
      newSwarmIds = sorted(newSwarmIds)

      # If no more swarms can be found for this sprint...
      if len(newSwarmIds) == 0:
        # if sprint is not an empty sprint return that it is active but do not
        #  add anything to it.
        if len(self.getAllSwarms(sprintIdx)) > 0:
          return (True, False)

        # If this is an empty sprint and we couldn't find any new swarms to
        #   add (only bad fields are remaining), the search is over
        else:
          return (False, True)

      # Add this sprint and the swarms that are in it to our state
      self._dirty = True

      # Add in the new sprint if necessary
      if len(self._state["sprints"]) == sprintIdx:
        self._state['sprints'].append({'status': 'active',
                                       'bestModelId': None,
                                       'bestErrScore': None})

      # Add in the new swarm(s) to the sprint
      for swarmId in newSwarmIds:
        self._state['swarms'][swarmId] = {'status': 'active',
                                            'bestModelId': None,
                                            'bestErrScore': None,
                                            'sprintIdx': sprintIdx}

      # Update the list of active swarms
      self._state['activeSwarms'] = self.getActiveSwarms()

      # Try to set new state
      success = self.writeStateToDB()

      # Return result if successful
      if success:
        return (True, False)

      # No success, loop back with the updated state and try again


class HsSearchType(object):
  """This class enumerates the types of search we can perform."""
  temporal = 'temporal'
  legacyTemporal = 'legacyTemporal'
  classification = 'classification'


class HypersearchV2(object):
  """The v2 Hypersearch implementation. This is one example of a Hypersearch
  implementation that can be used by the HypersearchWorker. Other implementations
  just have to implement the following methods:

    createModels()
    recordModelProgress()
    getPermutationVariables()
    getComplexVariableLabelLookupDict()

  This implementation uses a hybrid of Particle Swarm Optimization (PSO) and
  the old "ronamatic" logic from Hypersearch V1. Variables which are lists of
  choices (i.e. string values, integer values that represent different
  categories) are searched using the ronamatic logic whereas floats and
  integers that represent a range of values are searched using PSO.

  For prediction experiments, this implementation starts out evaluating only 
  single encoder models that encode the predicted field. This is the first 
  "sprint". Once it finds the optimum set of variables for that, it starts to 
  build up by adding in combinations of 2 fields (the second "sprint"), where 
  one of them is the predicted field. Once the top 2-field combination(s) are 
  discovered, it starts to build up on those by adding in a 3rd field, etc. 
  Each new set of field combinations is called a sprint.
  
  For classification experiments, this implementation starts out evaluating two
  encoder models, where one of the encoders is the classified field. This is the
  first "sprint". Once it finds the optimum set of variables for that, it starts 
  to  build up by evauating combinations of 3 fields (the second "sprint"), where 
  two of them are the best 2 fields found in the first sprint (one of those of
  course being the classified field). Once the top 3-field combination(s) are 
  discovered, it starts to build up on those by adding in a 4th field, etc.
  In classification models, the classified field, although it has an encoder, is
  not sent "into" the network. Rather, the encoded value just goes directly to 
  the classifier as the classifier input.  

  At any one time, there are 1 or more swarms being evaluated at the same time -
  each swarm representing a certain field combination within the sprint. We try
  to load balance the swarms and have the same number of models evaluated for
  each swarm at any one time. Each swarm contains N particles, and we also try
  to keep N >= some mininum number. Each position of a particle corresponds to a
  model.

  When a worker is ready to evaluate a new model, it first picks the swarm with
  the least number of models so far (least number of evaluated particle
  positions). If that swarm does not have the min number of particles in it yet,
  or does not yet have a particle created by this worker, the worker will create
  a new particle, else it will choose another particle from that swarm that it
  had created in the past which has the least number of evaluated positions so
  far.
  """

  def __init__(self, searchParams, workerID=None, cjDAO=None, jobID=None,
               logLevel=None):
    """Instantiate the HyperseachV2 instance.

    Parameters:
    ----------------------------------------------------------------------
    searchParams:   a dict of the job's search parameters. The format is:

      persistentJobGUID:  REQUIRED.
                          Persistent, globally-unique identifier for this job
                          for use in constructing persistent model checkpoint
                          keys. MUST be compatible with S3 key-naming rules, but
                          MUST NOT contain forward slashes. This GUID is
                          expected to retain its global uniqueness across
                          clusters and cluster software updates (unlike the
                          record IDs in the Engine's jobs table, which recycle
                          upon table schema change and software update). In the
                          future, this may also be instrumental for checkpoint
                          garbage collection.

      permutationsPyFilename:
                          OPTIONAL - path to permutations.py file
      permutationsPyContents:
                          OPTIONAL - JSON encoded string with
                                      contents of permutations.py file
      descriptionPyContents:
                          OPTIONAL - JSON encoded string with
                                      contents of base description.py file
      description:        OPTIONAL - JSON description of the search
      createCheckpoints:  OPTIONAL - Whether to create checkpoints
      useTerminators      OPTIONAL - True of False (default config.xml). When set
                                     to False, the model and swarm terminators
                                     are disabled
      maxModels:          OPTIONAL - max # of models to generate
                                    NOTE: This is a deprecated location for this
                                    setting. Now, it should be specified through
                                    the maxModels variable within the permutations 
                                    file, or maxModels in the JSON description 
      dummyModel:         OPTIONAL - Either (True/False) or a dict of parameters
                                     for a dummy model. If this key is absent,
                                     a real model is trained.
                                     See utils.py/OPFDummyModel runner for the
                                     schema of the dummy parameters
      speculativeParticles OPTIONAL - True or False (default obtained from
                                     nupic.hypersearch.speculative.particles.default
                                     configuration property). See note below.

      NOTE: The caller must provide just ONE of the following to describe the
      hypersearch:
            1.) permutationsPyFilename
        OR  2.) permutationsPyContents & permutationsPyContents
        OR  3.) description

      The schema for the description element can be found at:
       "py/nupic/frameworks/opf/expGenerator/experimentDescriptionSchema.json"

      NOTE about speculativeParticles: If true (not 0), hypersearch workers will
      go ahead and create and run particles in subsequent sprints and
      generations before the current generation or sprint has been completed. If
      false, a worker will wait in a sleep loop until the current generation or
      sprint has finished before choosing the next particle position or going
      into the next sprint. When true, the best model can be found faster, but
      results are less repeatable due to the randomness of when each worker
      completes each particle. This property can be overridden via the
      speculativeParticles element of the Hypersearch job params.


    workerID:   our unique Hypersearch worker ID

    cjDAO:      ClientJobsDB Data Access Object
    jobID:      job ID for this hypersearch job
    logLevel:   override logging level to this value, if not None
    """
    
    # Instantiate our logger
    self.logger = logging.getLogger(".".join( ['com.numenta',
                        self.__class__.__module__, self.__class__.__name__]))

    # Override log level?
    if logLevel is not None:
      self.logger.setLevel(logLevel)

    # This is how to check the logging level
    #if self.logger.getEffectiveLevel() <= logging.DEBUG:
    #  print "at debug level"

    # Init random seed
    random.seed(42)

    # Save the search info
    self._searchParams = searchParams
    self._workerID = workerID
    self._cjDAO = cjDAO
    self._jobID = jobID

    # Log search params
    self.logger.info("searchParams: \n%s" % (pprint.pformat(
        clippedObj(searchParams))))

    self._createCheckpoints = self._searchParams.get('createCheckpoints',
                                                     False)
    self._maxModels = self._searchParams.get('maxModels', None)
    if self._maxModels == -1:
      self._maxModels = None
    self._predictionCacheMaxRecords = self._searchParams.get('predictionCacheMaxRecords', None)

    # Speculative particles?
    self._speculativeParticles = self._searchParams.get('speculativeParticles',
        bool(int(Configuration.get(
                        'nupic.hypersearch.speculative.particles.default'))))
    self._speculativeWaitSecondsMax = float(Configuration.get(
                    'nupic.hypersearch.speculative.particles.sleepSecondsMax'))

    # Maximum Field Branching
    self._maxBranching= int(Configuration.get(
                             'nupic.hypersearch.max.field.branching'))

    # Minimum Field Contribution
    self._minFieldContribution= float(Configuration.get(
                             'nupic.hypersearch.min.field.contribution'))

    # This gets set if we detect that the job got cancelled
    self._jobCancelled = False

    # Use terminators (typically set by permutations_runner.py)
    if 'useTerminators' in self._searchParams:
      useTerminators = self._searchParams['useTerminators']
      useTerminators = str(int(useTerminators))

      Configuration.set('nupic.hypersearch.enableModelTermination', useTerminators)
      Configuration.set('nupic.hypersearch.enableModelMaturity', useTerminators)
      Configuration.set('nupic.hypersearch.enableSwarmTermination', useTerminators)

    # Special test mode?
    if 'NTA_TEST_exitAfterNModels' in os.environ:
      self._maxModels = int(os.environ['NTA_TEST_exitAfterNModels'])

    self._dummyModel = self._searchParams.get('dummyModel', None)

    # Holder for temporary directory, if any, that needs to be cleaned up
    # in our close() method.
    self._tempDir = None
    try:
      # Get the permutations info. This can be either:
      #  1.) JSON encoded search description (this will be used to generate a
      #       permutations.py and description.py files using ExpGenerator)
      #  2.) path to a pre-generated permutations.py file. The description.py is
      #       assumed to be in the same directory
      #  3.) contents of the permutations.py and descrption.py files.
      if 'description' in self._searchParams:
        if ('permutationsPyFilename' in self._searchParams or
            'permutationsPyContents' in self._searchParams or
            'descriptionPyContents' in self._searchParams):
          raise RuntimeError(
              "Either 'description', 'permutationsPyFilename' or"
              "'permutationsPyContents' & 'permutationsPyContents' should be "
              "specified, but not two or more of these at once.")
        
        # Calculate training period for anomaly models
        searchParamObj = self._searchParams
        anomalyParams = searchParamObj['description'].get('anomalyParams',
          dict())

        # This is used in case searchParamObj['description']['anomalyParams']
        # is set to None.
        if anomalyParams is None:
          anomalyParams = dict()

        if (('autoDetectWaitRecords' not in anomalyParams) or
            (anomalyParams['autoDetectWaitRecords'] is None)):
          streamDef = self._getStreamDef(searchParamObj['description'])
          
          from nupic.data.stream_reader import StreamReader
            
          try:
            streamReader = StreamReader(streamDef, isBlocking=False, 
                                           maxTimeout=0, eofOnTimeout=True)
            anomalyParams['autoDetectWaitRecords'] = \
              streamReader.getDataRowCount()
          except Exception:
            anomalyParams['autoDetectWaitRecords'] = None
          self._searchParams['description']['anomalyParams'] = anomalyParams
        

        # Call the experiment generator to generate the permutations and base
        # description file.
        outDir = self._tempDir = tempfile.mkdtemp()
        expGenerator([
            '--description=%s' % (
                json.dumps(self._searchParams['description'])),
            '--version=v2',
            '--outDir=%s' % (outDir)])

        # Get the name of the permutations script.
        permutationsScript = os.path.join(outDir, 'permutations.py')

      elif 'permutationsPyFilename' in self._searchParams:
        if ('description' in self._searchParams or
            'permutationsPyContents' in self._searchParams or
            'descriptionPyContents' in self._searchParams):
          raise RuntimeError(
              "Either 'description', 'permutationsPyFilename' or "
              "'permutationsPyContents' & 'permutationsPyContents' should be "
              "specified, but not two or more of these at once.")
        permutationsScript = self._searchParams['permutationsPyFilename']

      elif 'permutationsPyContents' in self._searchParams:
        if ('description' in self._searchParams or
            'permutationsPyFilename' in self._searchParams):
          raise RuntimeError(
              "Either 'description', 'permutationsPyFilename' or"
              "'permutationsPyContents' & 'permutationsPyContents' should be "
              "specified, but not two or more of these at once.")

        assert ('descriptionPyContents' in self._searchParams)
        # Generate the permutations.py and description.py files
        outDir = self._tempDir = tempfile.mkdtemp()
        permutationsScript = os.path.join(outDir, 'permutations.py')
        fd = open(permutationsScript, 'w')
        fd.write(self._searchParams['permutationsPyContents'])
        fd.close()
        fd = open(os.path.join(outDir, 'description.py'), 'w')
        fd.write(self._searchParams['descriptionPyContents'])
        fd.close()

      else:
        raise RuntimeError ("Either 'description' or 'permutationsScript' must be"
                            "specified")

      # Get the base path of the experiment and read in the base description
      self._basePath = os.path.dirname(permutationsScript)
      self._baseDescription = open(os.path.join(self._basePath,
                                               'description.py')).read()
      self._baseDescriptionHash = hashlib.md5(self._baseDescription).digest()

      # Read the model config to figure out the inference type
      modelDescription, _ = opfhelpers.loadExperiment(self._basePath)

      # Read info from permutations file. This sets up the following member
      # variables:
      #   _predictedField
      #   _permutations
      #   _flattenedPermutations
      #   _encoderNames
      #   _reportKeys
      #   _filterFunc
      #   _optimizeKey
      #   _maximize
      #   _dummyModelParamsFunc
      self._readPermutationsFile(permutationsScript, modelDescription)

      # Fill in and save the base description and permutations file contents
      #  if they haven't already been filled in by another worker
      if self._cjDAO is not None:
        updated = self._cjDAO.jobSetFieldIfEqual(jobID=self._jobID,
                                                 fieldName='genBaseDescription',
                                                 curValue=None,
                                                 newValue = self._baseDescription)
        if updated:
          permContents = open(permutationsScript).read()
          self._cjDAO.jobSetFieldIfEqual(jobID=self._jobID,
                                         fieldName='genPermutations',
                                         curValue=None,
                                         newValue = permContents)

      # if user provided an artificialMetric, force use of the dummy model
      if self._dummyModelParamsFunc is not None:
        if self._dummyModel is None:
          self._dummyModel = dict()

      # If at DEBUG log level, print out permutations info to the log
      if self.logger.getEffectiveLevel() <= logging.DEBUG:
        msg = StringIO.StringIO()
        print >> msg, "Permutations file specifications: "
        info = dict()
        for key in ['_predictedField', '_permutations',
                    '_flattenedPermutations', '_encoderNames',
                    '_reportKeys', '_optimizeKey', '_maximize']:
          info[key] = getattr(self, key)
        print >> msg, pprint.pformat(info)
        self.logger.debug(msg.getvalue())
        msg.close()

      # Instantiate our database to hold the results we received so far
      self._resultsDB = ResultsDB(self)

      # Instantiate the Swarm Terminator
      self._swarmTerminator = SwarmTerminator()

      # Initial hypersearch state
      self._hsState = None

      # The Max # of attempts we will make to create a unique model before
      #  giving up.
      self._maxUniqueModelAttempts = int(Configuration.get(
                                      'nupic.hypersearch.maxUniqueModelAttempts'))

      # The max amount of time allowed before a model is considered orphaned.
      self._modelOrphanIntervalSecs = float(Configuration.get(
                                      'nupic.hypersearch.modelOrphanIntervalSecs'))

      # The max percent of models that can complete with errors
      self._maxPctErrModels = float(Configuration.get(
                                      'nupic.hypersearch.maxPctErrModels'))

    except:
      # Clean up our temporary directory, if any
      if self._tempDir is not None:
        shutil.rmtree(self._tempDir)
        self._tempDir = None

      raise

    return


  def _getStreamDef(self, modelDescription):
    """
    Generate stream definition based on 
    """
    #--------------------------------------------------------------------------
    # Generate the string containing the aggregation settings.
    aggregationPeriod = {
        'days': 0,
        'hours': 0,
        'microseconds': 0,
        'milliseconds': 0,
        'minutes': 0,
        'months': 0,
        'seconds': 0,
        'weeks': 0,
        'years': 0,
    }

    # Honor any overrides provided in the stream definition
    aggFunctionsDict = {}
    if 'aggregation' in modelDescription['streamDef']:
      for key in aggregationPeriod.keys():
        if key in modelDescription['streamDef']['aggregation']:
          aggregationPeriod[key] = modelDescription['streamDef']['aggregation'][key]
      if 'fields' in modelDescription['streamDef']['aggregation']:
        for (fieldName, func) in modelDescription['streamDef']['aggregation']['fields']:
          aggFunctionsDict[fieldName] = str(func)

    # Do we have any aggregation at all?
    hasAggregation = False
    for v in aggregationPeriod.values():
      if v != 0:
        hasAggregation = True
        break

    # Convert the aggFunctionsDict to a list
    aggFunctionList = aggFunctionsDict.items()
    aggregationInfo = dict(aggregationPeriod)
    aggregationInfo['fields'] = aggFunctionList

    streamDef = copy.deepcopy(modelDescription['streamDef'])
    streamDef['aggregation'] = copy.deepcopy(aggregationInfo)
    return streamDef


  def __del__(self):
    """Destructor; NOTE: this is not guaranteed to be called (bugs like
    circular references could prevent it from being called).
    """
    self.close()
    return

  def close(self):
    """Deletes temporary system objects/files. """
    if self._tempDir is not None and os.path.isdir(self._tempDir):
      self.logger.debug("Removing temporary directory %r", self._tempDir)
      shutil.rmtree(self._tempDir)
      self._tempDir = None

    return

  def _readPermutationsFile(self, filename, modelDescription):
    """
    Read the permutations file and initialize the following member variables:
        _predictedField: field name of the field we are trying to
          predict
        _permutations: Dict containing the full permutations dictionary.
        _flattenedPermutations: Dict containing the flattened version of
          _permutations. The keys leading to the value in the dict are joined
          with a period to create the new key and permute variables within
          encoders are pulled out of the encoder.
        _encoderNames: keys from self._permutations of only the encoder
          variables.
        _reportKeys:   The 'report' list from the permutations file.
          This is a list of the items from each experiment's pickled
          results file that should be included in the final report. The
          format of each item is a string of key names separated by colons,
          each key being one level deeper into the experiment results
          dict. For example, 'key1:key2'.
        _filterFunc: a user-supplied function that can be used to
          filter out specific permutation combinations.
        _optimizeKey: which report key to optimize for
        _maximize: True if we should try and maximize the optimizeKey
          metric. False if we should minimize it.
        _dummyModelParamsFunc: a user-supplied function that can be used to
          artificially generate CLA model results. When supplied,
          the model is not actually run through the OPF, but instead is run
          through a "Dummy Model" (nupic.swarming.ModelRunner.
          OPFDummyModelRunner). This function returns the params dict used
          to control various options in the dummy model (the returned metric,
          the execution time, etc.). This is used for hypersearch algorithm
          development.

    Parameters:
    ---------------------------------------------------------
    filename:     Name of permutations file
    retval:       None
    """
    # Open and execute the permutations file
    vars = {}
    
    permFile = execfile(filename, globals(), vars)
    

    # Read in misc info.
    self._reportKeys = vars.get('report', [])
    self._filterFunc = vars.get('permutationFilter', None)
    self._dummyModelParamsFunc = vars.get('dummyModelParams', None)
    self._predictedField = None   # default
    self._predictedFieldEncoder = None   # default
    self._fixedFields = None # default
    
    # The fastSwarm variable, if present, contains the params from a best
    #  model from a previous swarm. If present, use info from that to seed
    #  a fast swarm
    self._fastSwarmModelParams = vars.get('fastSwarmModelParams', None)
    if self._fastSwarmModelParams is not None:
      encoders = self._fastSwarmModelParams['structuredParams']['modelParams']\
                  ['sensorParams']['encoders']
      self._fixedFields = []
      for fieldName in encoders:
        if encoders[fieldName] is not None:
          self._fixedFields.append(fieldName)
          
    if 'fixedFields' in vars:
      self._fixedFields = vars['fixedFields']
    
    # Get min number of particles per swarm from either permutations file or
    # config.
    self._minParticlesPerSwarm = vars.get('minParticlesPerSwarm')
    if self._minParticlesPerSwarm  == None:
      self._minParticlesPerSwarm = Configuration.get(
                                      'nupic.hypersearch.minParticlesPerSwarm')
    self._minParticlesPerSwarm = int(self._minParticlesPerSwarm)
    
    # Enable logic to kill off speculative swarms when an earlier sprint
    #  has found that it contains poorly performing field combination?
    self._killUselessSwarms = vars.get('killUselessSwarms', True)
    
    # The caller can request that the predicted field ALWAYS be included ("yes")
    #  or optionally include ("auto"). The setting of "no" is N/A and ignored
    #  because in that case the encoder for the predicted field will not even
    #  be present in the permutations file. 
    # When set to "yes", this will force the first sprint to try the predicted 
    #  field only (the legacy mode of swarming).
    # When set to "auto", the first sprint tries all possible fields (one at a 
    #  time) in the first sprint.  
    self._inputPredictedField = vars.get("inputPredictedField", "yes")
    
    # Try all possible 3-field combinations? Normally, we start with the best
    #  2-field combination as a base. When this flag is set though, we try
    #  all possible 3-field combinations which takes longer but can find a 
    #  better model. 
    self._tryAll3FieldCombinations = vars.get('tryAll3FieldCombinations', False)
    
    # Always include timestamp fields in the 3-field swarms? 
    # This is a less compute intensive version of tryAll3FieldCombinations. 
    # Instead of trying ALL possible 3 field combinations, it just insures
    # that the timestamp fields (dayOfWeek, timeOfDay, weekend) are never left
    # out when generating the 3-field swarms.   
    self._tryAll3FieldCombinationsWTimestamps = vars.get(
                                'tryAll3FieldCombinationsWTimestamps', False)
    
    # Allow the permutations file to override minFieldContribution. This would
    #  be set to a negative number for large swarms so that you don't disqualify
    #  a field in an early sprint just because it did poorly there. Sometimes,
    #  a field that did poorly in an early sprint could help accuracy when 
    #  added in a later sprint
    minFieldContribution = vars.get('minFieldContribution', None)
    if minFieldContribution is not None:
      self._minFieldContribution = minFieldContribution
      
    # Allow the permutations file to override maxBranching. 
    maxBranching = vars.get('maxFieldBranching', None)
    if maxBranching is not None:
      self._maxBranching = maxBranching

    # Read in the optimization info.
    if 'maximize' in vars:
      self._optimizeKey = vars['maximize']
      self._maximize = True
    elif 'minimize' in vars:
      self._optimizeKey = vars['minimize']
      self._maximize = False
    else:
      raise RuntimeError("Permutations file '%s' does not include a maximize"
                         " or minimize metric.")
      
    # The permutations file is the new location for maxModels. The old location,
    #  in the jobParams is deprecated. 
    maxModels = vars.get('maxModels')
    if maxModels is not None:
      if self._maxModels is None:
        self._maxModels = maxModels
      else:
        raise RuntimeError('It is an error to specify maxModels both in the job'
                ' params AND in the permutations file.')


    # Figure out if what kind of search this is:
    #
    #  If it's a temporal prediction search:
    #    the first sprint has 1 swarm, with just the predicted field
    #  elif it's a spatial prediction search:
    #    the first sprint has N swarms, each with predicted field + one
    #    other field.
    #  elif it's a classification search:
    #    the first sprint has N swarms, each with 1 field
    inferenceType = modelDescription['modelParams']['inferenceType']
    if not InferenceType.validate(inferenceType):
      raise ValueError("Invalid inference type %s" %inferenceType)

    if inferenceType in [InferenceType.TemporalMultiStep,
                         InferenceType.NontemporalMultiStep]:
      # If it does not have a separate encoder for the predicted field that 
      #  goes to the classifier, it is a legacy multi-step network
      classifierOnlyEncoder = None 
      for encoder in modelDescription["modelParams"]["sensorParams"]\
                    ["encoders"].values():
        if encoder.get("classifierOnly", False) \
             and encoder["fieldname"] == vars.get('predictedField', None): 
          classifierOnlyEncoder = encoder
          break
        
      if classifierOnlyEncoder is None or self._inputPredictedField=="yes":
        # If we don't have a separate encoder for the classifier (legacy
        #  MultiStep) or the caller explicitly wants to include the predicted
        #  field, then use the legacy temporal search methodology. 
        self._searchType = HsSearchType.legacyTemporal
      else:
        self._searchType = HsSearchType.temporal


    elif inferenceType in [InferenceType.TemporalNextStep,
                         InferenceType.TemporalAnomaly]:
      self._searchType = HsSearchType.legacyTemporal

    elif inferenceType in (InferenceType.TemporalClassification,
                            InferenceType.NontemporalClassification):
      self._searchType = HsSearchType.classification

    else:
      raise RuntimeError("Unsupported inference type: %s" % inferenceType)

    # Get the predicted field. Note that even classification experiments
    #  have a "predicted" field - which is the field that contains the
    #  classification value. 
    self._predictedField = vars.get('predictedField', None)
    if self._predictedField is None:
      raise RuntimeError("Permutations file '%s' does not have the required"
                         " 'predictedField' variable" % filename)

    # Read in and validate the permutations dict
    if 'permutations' not in vars:
      raise RuntimeError("Permutations file '%s' does not define permutations" % filename)

    if not isinstance(vars['permutations'], dict):
      raise RuntimeError("Permutations file '%s' defines a permutations variable "
                         "but it is not a dict")

    self._encoderNames = []
    self._permutations = vars['permutations']
    self._flattenedPermutations = dict()
    def _flattenPermutations(value, keys):
      if ':' in keys[-1]:
        raise RuntimeError("The permutation variable '%s' contains a ':' "
                           "character, which is not allowed.")
      flatKey = _flattenKeys(keys)
      if isinstance(value, PermuteEncoder):
        self._encoderNames.append(flatKey)

        # If this is the encoder for the predicted field, save its name.
        if value.fieldName == self._predictedField:
          self._predictedFieldEncoder = flatKey

        # Store the flattened representations of the variables within the
        # encoder.
        for encKey, encValue in value.kwArgs.iteritems():
          if isinstance(encValue, PermuteVariable):
            self._flattenedPermutations['%s:%s' % (flatKey, encKey)] = encValue
      elif isinstance(value, PermuteVariable):
        self._flattenedPermutations[flatKey] = value


      else:
        if isinstance(value, PermuteVariable):
          self._flattenedPermutations[key] = value
    rApply(self._permutations, _flattenPermutations)

  def getExpectedNumModels(self):
    """Computes the number of models that are expected to complete as part of
    this instances's HyperSearch.

    NOTE: This is compute-intensive for HyperSearches with a huge number of
    combinations.

    NOTE/TODO:  THIS ONLY WORKS FOR RONOMATIC: This method is exposed for the
                benefit of perutations_runner.py for use in progress
                reporting.

    Parameters:
    ---------------------------------------------------------
    retval:       The total number of expected models, if known; -1 if unknown
    """
    return -1

  def getModelNames(self):
    """Generates a list of model names that are expected to complete as part of
    this instances's HyperSearch.

    NOTE: This is compute-intensive for HyperSearches with a huge number of
    combinations.

    NOTE/TODO:  THIS ONLY WORKS FOR RONOMATIC: This method is exposed for the
                benefit of perutations_runner.py.

    Parameters:
    ---------------------------------------------------------
    retval:       List of model names for this HypersearchV2 instance, or
                  None of not applicable
    """
    return None

  def getPermutationVariables(self):
    """Returns a dictionary of permutation variables.

    Parameters:
    ---------------------------------------------------------
    retval:       A dictionary of permutation variables; keys are
                  flat permutation variable names and each value is
                  a sub-class of PermuteVariable.
    """
    return self._flattenedPermutations

  def getComplexVariableLabelLookupDict(self):
    """Generates a lookup dictionary of permutation variables whose values
    are too complex for labels, so that artificial labels have to be generated
    for them.

    Parameters:
    ---------------------------------------------------------
    retval:       A look-up dictionary of permutation
                  variables whose values are too complex for labels, so
                  artificial labels were generated instead (e.g., "Choice0",
                  "Choice1", etc.); the key is the name of the complex variable
                  and the value is:
                    dict(labels=<list_of_labels>, values=<list_of_values>).
    """
    raise NotImplementedError

  def getOptimizationMetricInfo(self):
    """Retrives the optimization key name and optimization function.

    Parameters:
    ---------------------------------------------------------
    retval:       (optimizationMetricKey, maximize)
                  optimizationMetricKey: which report key to optimize for
                  maximize: True if we should try and maximize the optimizeKey
                    metric. False if we should minimize it.
    """
    return (self._optimizeKey, self._maximize)

  def _checkForOrphanedModels (self):
    """If there are any models that haven't been updated in a while, consider
    them dead, and mark them as hidden in our resultsDB. We also change the
    paramsHash and particleHash of orphaned models so that we can
    re-generate that particle and/or model again if we desire.

    Parameters:
    ----------------------------------------------------------------------
    retval:   

    """
    
    self.logger.debug("Checking for orphaned models older than %s" % \
                     (self._modelOrphanIntervalSecs))
    
    while True:
      orphanedModelId = self._cjDAO.modelAdoptNextOrphan(self._jobID,
                                                self._modelOrphanIntervalSecs)
      if orphanedModelId is None:
        return 

      self.logger.info("Removing orphaned model: %d" % (orphanedModelId))

      # Change the model hash and params hash as stored in the models table so
      #  that we can insert a new model with the same paramsHash
      for attempt in range(100):
        paramsHash = hashlib.md5("OrphanParams.%d.%d" % (orphanedModelId,
                                                         attempt)).digest()
        particleHash = hashlib.md5("OrphanParticle.%d.%d" % (orphanedModelId,
                                                          attempt)).digest()
        try:
          self._cjDAO.modelSetFields(orphanedModelId,
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

      # Mark this model as complete, with reason "orphaned"
      self._cjDAO.modelSetCompleted(modelID=orphanedModelId,
                    completionReason=ClientJobsDAO.CMPL_REASON_ORPHAN,
                    completionMsg="Orphaned")

      # Update our results DB immediately, rather than wait for the worker
      #  to inform us. This insures that the getParticleInfos() calls we make
      #  below don't include this particle. Setting the metricResult to None
      #  sets it to worst case
      self._resultsDB.update(modelID=orphanedModelId,
                             modelParams=None,
                             modelParamsHash=paramsHash,
                             metricResult=None,
                             completed = True,
                             completionReason = ClientJobsDAO.CMPL_REASON_ORPHAN,
                             matured = True,
                             numRecords = 0)


  def _hsStatePeriodicUpdate(self, exhaustedSwarmId=None):
    """
    Periodically, check to see if we should remove a certain field combination
    from evaluation (because it is doing so poorly) or move on to the next
    sprint (add in more fields).

    This method is called from _getCandidateParticleAndSwarm(), which is called
    right before we try and create a new model to run.

    Parameters:
    -----------------------------------------------------------------------
    removeSwarmId:     If not None, force a change to the current set of active
                      swarms by removing this swarm. This is used in situations
                      where we can't find any new unique models to create in
                      this swarm. In these situations, we update the hypersearch
                      state regardless of the timestamp of the last time another
                      worker updated it.

    """
    if self._hsState is None:
      self._hsState =  HsState(self)

    # Read in current state from the DB
    self._hsState.readStateFromDB()

    # This will hold the list of completed swarms that we find
    completedSwarms = set()

    # Mark the exhausted swarm as completing/completed, if any
    if exhaustedSwarmId is not None:
      self.logger.info("Removing swarm %s from the active set "
                       "because we can't find any new unique particle "
                       "positions" % (exhaustedSwarmId))
      # Is it completing or completed?
      (particles, _, _, _, _) = self._resultsDB.getParticleInfos(
                                      swarmId=exhaustedSwarmId, matured=False)
      if len(particles) > 0:
        exhaustedSwarmStatus = 'completing'
      else:
        exhaustedSwarmStatus = 'completed'

    # Kill all swarms that don't need to be explored based on the most recent
    # information.
    if self._killUselessSwarms:
      self._hsState.killUselessSwarms()

    # For all swarms that were in the 'completing' state, see if they have
    # completed yet.
    #
    # Note that we are not quite sure why this doesn't automatically get handled
    # when we receive notification that a model finally completed in a swarm.
    # But, we ARE running into a situation, when speculativeParticles is off,
    # where we have one or more swarms in the 'completing' state even though all
    # models have since finished. This logic will serve as a failsafe against
    # this situation.
    completingSwarms = self._hsState.getCompletingSwarms()
    for swarmId in completingSwarms:
      # Is it completed?
      (particles, _, _, _, _) = self._resultsDB.getParticleInfos(
                                      swarmId=swarmId, matured=False)
      if len(particles) == 0:
        completedSwarms.add(swarmId)

    # Are there any swarms we can remove (because they have matured)?
    completedSwarmGens = self._resultsDB.getMaturedSwarmGenerations()
    priorCompletedSwarms = self._hsState.getCompletedSwarms()
    for (swarmId, genIdx, errScore) in completedSwarmGens:

      # Don't need to report it if the swarm already completed
      if swarmId in priorCompletedSwarms:
        continue

      completedList = self._swarmTerminator.recordDataPoint(
          swarmId=swarmId, generation=genIdx, errScore=errScore)

      # Update status message
      statusMsg = "Completed generation #%d of swarm '%s' with a best" \
                  " errScore of %g" % (genIdx, swarmId, errScore)
      if len(completedList) > 0:
        statusMsg = "%s. Matured swarm(s): %s" % (statusMsg, completedList)
      self.logger.info(statusMsg)
      self._cjDAO.jobSetFields (jobID=self._jobID,
                                fields=dict(engStatus=statusMsg),
                                useConnectionID=False,
                                ignoreUnchanged=True)

      # Special test mode to check which swarms have terminated
      if 'NTA_TEST_recordSwarmTerminations' in os.environ:
        while True:
          resultsStr = self._cjDAO.jobGetFields(self._jobID, ['results'])[0]
          if resultsStr is None:
            results = {}
          else:
            results = json.loads(resultsStr)
          if not 'terminatedSwarms' in results:
            results['terminatedSwarms'] = {}

          for swarm in completedList:
            if swarm not in results['terminatedSwarms']:
              results['terminatedSwarms'][swarm] = (genIdx,
                                    self._swarmTerminator.swarmScores[swarm])

          newResultsStr = json.dumps(results)
          if newResultsStr == resultsStr:
            break
          updated = self._cjDAO.jobSetFieldIfEqual(jobID=self._jobID,
                                                   fieldName='results',
                                                   curValue=resultsStr,
                                                   newValue = json.dumps(results))
          if updated:
            break

      if len(completedList) > 0:
        for name in completedList:
          self.logger.info("Swarm matured: %s. Score at generation %d: "
                           "%s" % (name, genIdx, errScore))
        completedSwarms = completedSwarms.union(completedList)

    if len(completedSwarms)==0 and (exhaustedSwarmId is None):
      return

    # We need to mark one or more swarms as completed, keep trying until
    #  successful, or until some other worker does it for us.
    while True:

      if exhaustedSwarmId is not None:
        self._hsState.setSwarmState(exhaustedSwarmId, exhaustedSwarmStatus)

      # Mark the completed swarms as completed
      for swarmId in completedSwarms:
        self._hsState.setSwarmState(swarmId, 'completed')

      # If nothing changed, we're done
      if not self._hsState.isDirty():
        return

      # Update the shared Hypersearch state now
      # This will do nothing and return False if some other worker beat us to it
      success = self._hsState.writeStateToDB()

      if success:
        # Go through and cancel all models that are still running, except for
        # the best model. Once the best model changes, the one that used to be
        # best (and has  matured) will notice that and stop itself at that point.
        jobResultsStr = self._cjDAO.jobGetFields(self._jobID, ['results'])[0]
        if jobResultsStr is not None:
          jobResults = json.loads(jobResultsStr)
          bestModelId = jobResults.get('bestModel', None)
        else:
          bestModelId = None

        for swarmId in list(completedSwarms):
          (_, modelIds, _, _, _) = self._resultsDB.getParticleInfos(
                                          swarmId=swarmId, completed=False)
          if bestModelId in modelIds:
            modelIds.remove(bestModelId)
          if len(modelIds) == 0:
            continue
          self.logger.info("Killing the following models in swarm '%s' because"
                           "the swarm is being terminated: %s" % (swarmId,
                           str(modelIds)))

          for modelId in modelIds:
            self._cjDAO.modelSetFields(modelId,
                    dict(engStop=ClientJobsDAO.STOP_REASON_KILLED),
                    ignoreUnchanged = True)
        return

      # We were not able to change the state because some other worker beat us
      # to it.
      # Get the new state, and try again to apply our changes.
      self._hsState.readStateFromDB()
      self.logger.debug("New hsState has been set by some other worker to: "
                       " \n%s" % (pprint.pformat(self._hsState._state, indent=4)))

  def _getCandidateParticleAndSwarm (self, exhaustedSwarmId=None):
    """Find or create a candidate particle to produce a new model.

    At any one time, there is an active set of swarms in the current sprint, where
    each swarm in the sprint represents a particular combination of fields.
    Ideally, we should try to balance the number of models we have evaluated for
    each swarm at any time.

    This method will see how many models have been evaluated for each active
    swarm in the current active sprint(s) and then try and choose a particle
    from the least represented swarm in the first possible active sprint, with
    the following constraints/rules:

    for each active sprint:
      for each active swarm (preference to those with least# of models so far):
        1.) The particle will be created from new (generation #0) if there are not
        already self._minParticlesPerSwarm particles in the swarm.

        2.) Find the first gen that has a completed particle and evolve that
        particle to the next generation.

        3.) If we got to here, we know that we have satisfied the min# of
        particles for the swarm, and they are all currently running (probably at
        various generation indexes). Go onto the next swarm

      If we couldn't find a swarm to allocate a particle in, go onto the next
      sprint and start allocating particles there....


    Parameters:
    ----------------------------------------------------------------
    exhaustedSwarmId:   If not None, force a change to the current set of active
                        swarms by marking this swarm as either 'completing' or
                        'completed'. If there are still models being evaluaed in
                        it, mark it as 'completing', else 'completed. This is
                        used in situations where we can't find any new unique
                        models to create in this swarm. In these situations, we
                        force an update to the hypersearch state so no other
                        worker wastes time try to use this swarm.

    retval: (exit, particle, swarm)
              exit: If true, this worker is ready to exit (particle and
                      swarm will be None)
              particle: Which particle to run
              swarm: which swarm the particle is in

              NOTE: When particle and swarm are None and exit is False, it
              means that we need to wait for one or more other worker(s) to
              finish their respective models before we can pick a particle
              to run. This will generally only happen when speculativeParticles
              is set to False.
    """
    # Cancel search?
    jobCancel = self._cjDAO.jobGetFields(self._jobID, ['cancel'])[0]
    if jobCancel:
      self._jobCancelled = True
      # Did a worker cancel the job because of an error?
      (workerCmpReason, workerCmpMsg) = self._cjDAO.jobGetFields(self._jobID,
          ['workerCompletionReason', 'workerCompletionMsg'])
      if workerCmpReason == ClientJobsDAO.CMPL_REASON_SUCCESS:
        self.logger.info("Exiting due to job being cancelled")
        self._cjDAO.jobSetFields(self._jobID,
              dict(workerCompletionMsg="Job was cancelled"),
              useConnectionID=False, ignoreUnchanged=True)
      else:
        self.logger.error("Exiting because some worker set the "
              "workerCompletionReason to %s. WorkerCompletionMsg: %s" %
              (workerCmpReason, workerCmpMsg))
      return (True, None, None)

    # Perform periodic updates on the Hypersearch state.
    if self._hsState is not None:
      priorActiveSwarms = self._hsState.getActiveSwarms()
    else:
      priorActiveSwarms = None

    # Update the HypersearchState, checking for matured swarms, and marking
    #  the passed in swarm as exhausted, if any
    self._hsStatePeriodicUpdate(exhaustedSwarmId=exhaustedSwarmId)

    # The above call may have modified self._hsState['activeSwarmIds']
    # Log the current set of active swarms
    activeSwarms = self._hsState.getActiveSwarms()
    if activeSwarms != priorActiveSwarms:
      self.logger.info("Active swarms changed to %s (from %s)" % (activeSwarms,
                                                        priorActiveSwarms))
    self.logger.debug("Active swarms: %s" % (activeSwarms))

    # If too many model errors were detected, exit
    totalCmpModels = self._resultsDB.getNumCompletedModels()
    if totalCmpModels > 5:
      numErrs = self._resultsDB.getNumErrModels()
      if (float(numErrs) / totalCmpModels) > self._maxPctErrModels:
        # Get one of the errors
        errModelIds = self._resultsDB.getErrModelIds()
        resInfo = self._cjDAO.modelsGetResultAndStatus([errModelIds[0]])[0]
        modelErrMsg = resInfo.completionMsg
        cmpMsg = "%s: Exiting due to receiving too many models failing" \
                 " from exceptions (%d out of %d). \nModel Exception: %s" % \
                  (ErrorCodes.tooManyModelErrs, numErrs, totalCmpModels,
                   modelErrMsg)
        self.logger.error(cmpMsg)

        # Cancel the entire job now, if it has not already been cancelled
        workerCmpReason = self._cjDAO.jobGetFields(self._jobID,
            ['workerCompletionReason'])[0]
        if workerCmpReason == ClientJobsDAO.CMPL_REASON_SUCCESS:
          self._cjDAO.jobSetFields(
              self._jobID,
              fields=dict(
                      cancel=True,
                      workerCompletionReason = ClientJobsDAO.CMPL_REASON_ERROR,
                      workerCompletionMsg = cmpMsg),
              useConnectionID=False,
              ignoreUnchanged=True)
        return (True, None, None)

    # If HsState thinks the search is over, exit. It is seeing if the results
    #  on the sprint we just completed are worse than a prior sprint.
    if self._hsState.isSearchOver():
      cmpMsg = "Exiting because results did not improve in most recently" \
                        " completed sprint."
      self.logger.info(cmpMsg)
      self._cjDAO.jobSetFields(self._jobID,
            dict(workerCompletionMsg=cmpMsg),
            useConnectionID=False, ignoreUnchanged=True)
      return (True, None, None)

    # Search successive active sprints, until we can find a candidate particle
    #   to work with
    sprintIdx = -1
    while True:
      # Is this sprint active?
      sprintIdx += 1
      (active, eos) = self._hsState.isSprintActive(sprintIdx)

      # If no more sprints to explore:
      if eos:
        # If any prior ones are still being explored, finish up exploring them
        if self._hsState.anyGoodSprintsActive():
          self.logger.info("No more sprints to explore, waiting for prior"
                         " sprints to complete")
          return (False, None, None)

        # Else, we're done
        else:
          cmpMsg = "Exiting because we've evaluated all possible field " \
                           "combinations"
          self._cjDAO.jobSetFields(self._jobID,
                                   dict(workerCompletionMsg=cmpMsg),
                                   useConnectionID=False, ignoreUnchanged=True)
          self.logger.info(cmpMsg)
          return (True, None, None)

      if not active:
        if not self._speculativeParticles:
          if not self._hsState.isSprintCompleted(sprintIdx):
            self.logger.info("Waiting for all particles in sprint %d to complete"
                          "before evolving any more particles" % (sprintIdx))
            return (False, None, None)
        continue


      # ====================================================================
      # Look for swarms that have particle "holes" in their generations. That is,
      #  an earlier generation with less than minParticlesPerSwarm. This can
      #  happen if a model that was started eariler got orphaned. If we detect
      #  this, start a new particle in that generation.
      swarmIds = self._hsState.getActiveSwarms(sprintIdx)
      for swarmId in swarmIds:
        firstNonFullGenIdx = self._resultsDB.firstNonFullGeneration(
                                swarmId=swarmId, 
                                minNumParticles=self._minParticlesPerSwarm)
        if firstNonFullGenIdx is None:
          continue
        
        if firstNonFullGenIdx < self._resultsDB.highestGeneration(swarmId):
          self.logger.info("Cloning an earlier model in generation %d of swarm "
              "%s (sprintIdx=%s) to replace an orphaned model" % (
                firstNonFullGenIdx, swarmId, sprintIdx))
          
          # Clone a random orphaned particle from the incomplete generation 
          (allParticles, allModelIds, errScores, completed, matured) = \
            self._resultsDB.getOrphanParticleInfos(swarmId, firstNonFullGenIdx)
          
          if len(allModelIds) > 0:
            # We have seen instances where we get stuck in a loop incessantly
            #  trying to clone earlier models (NUP-1511). My best guess is that
            #  we've already successfully cloned each of the orphaned models at 
            #  least once, but still need at least one more. If we don't create 
            #  a new particleID, we will never be able to instantiate another 
            #  model (since particleID hash is a unique key in the models table). 
            #  So, on 1/8/2013 this logic was changed to create a new particleID          
            #  whenever we clone an orphan. 
            newParticleId = True
            self.logger.info("Cloning an orphaned model")
            
          # If there is no orphan, clone one of the other particles. We can
          #  have no orphan if this was a speculative generation that only
          #  continued particles completed in the prior generation. 
          else:
            newParticleId = True
            self.logger.info("No orphans found, so cloning a non-orphan")
            (allParticles, allModelIds, errScores, completed, matured) = \
            self._resultsDB.getParticleInfos(swarmId=swarmId, 
                                             genIdx=firstNonFullGenIdx)
            
          # Clone that model
          modelId = random.choice(allModelIds)
          self.logger.info("Cloning model %r" % (modelId))
          (particleState, _, _, _, _) = self._resultsDB.getParticleInfo(modelId)
          particle = Particle(hsObj = self,
                              resultsDB = self._resultsDB,
                              flattenedPermuteVars=self._flattenedPermutations,
                              newFromClone=particleState,
                              newParticleId=newParticleId)
          return (False, particle, swarmId)
            
          
      # ====================================================================
      # Sort the swarms in priority order, trying the ones with the least
      #  number of models first
      swarmSizes = numpy.array([self._resultsDB.numModels(x) for x in swarmIds])
      swarmSizeAndIdList = zip(swarmSizes, swarmIds)
      swarmSizeAndIdList.sort()
      for (_, swarmId) in swarmSizeAndIdList:
        
        # -------------------------------------------------------------------
        # 1.) The particle will be created from new (at generation #0) if there
        #   are not already self._minParticlesPerSwarm particles in the swarm.
        (allParticles, allModelIds, errScores, completed, matured) = (
            self._resultsDB.getParticleInfos(swarmId))
        if len(allParticles) < self._minParticlesPerSwarm:
          particle = Particle(hsObj=self,
                              resultsDB=self._resultsDB,
                              flattenedPermuteVars=self._flattenedPermutations,
                              swarmId=swarmId,
                              newFarFrom=allParticles)

          # Jam in the best encoder state found from the first sprint
          bestPriorModel = None
          if sprintIdx >= 1:
            (bestPriorModel, errScore) = self._hsState.bestModelInSprint(0)

          if bestPriorModel is not None:
            self.logger.info("Best model and errScore from previous sprint(%d):"
                              " %s, %g" % (0, str(bestPriorModel), errScore))
            (baseState, modelId, errScore, completed, matured) \
                 = self._resultsDB.getParticleInfo(bestPriorModel)
            particle.copyEncoderStatesFrom(baseState)
            
            # Copy the best inference type from the earlier sprint
            particle.copyVarStatesFrom(baseState, ['modelParams|inferenceType'])
            
            # It's best to jiggle the best settings from the prior sprint, so
            #  compute a new position starting from that previous best
            # Only jiggle the vars we copied from the prior model
            whichVars = []
            for varName in baseState['varStates']:
              if ':' in varName:
                whichVars.append(varName)
            particle.newPosition(whichVars)
            
            self.logger.debug("Particle after incorporating encoder vars from best "
                             "model in previous sprint: \n%s" % (str(particle)))

          return (False, particle, swarmId)

        # -------------------------------------------------------------------
        # 2.) Look for a completed particle to evolve
        # Note that we use lastDescendent. We only want to evolve particles that
        # are at their most recent generation index.
        (readyParticles, readyModelIds, readyErrScores, _, _) = (
            self._resultsDB.getParticleInfos(swarmId, genIdx=None,
                                             matured=True, lastDescendent=True))

        # If we have at least 1 ready particle to evolve...
        if len(readyParticles) > 0:
          readyGenIdxs = [x['genIdx'] for x in readyParticles]
          sortedGenIdxs = sorted(set(readyGenIdxs))
          genIdx = sortedGenIdxs[0]

          # Now, genIdx has the generation of the particle we want to run,
          # Get a particle from that generation and evolve it.
          useParticle = None
          for particle in readyParticles:
            if particle['genIdx'] == genIdx:
              useParticle = particle
              break

          # If speculativeParticles is off, we don't want to evolve a particle
          # into the next generation until all particles in the current
          # generation have completed.
          if not self._speculativeParticles:
            (particles, _, _, _, _) = self._resultsDB.getParticleInfos(
                swarmId, genIdx=genIdx, matured=False)
            if len(particles) > 0:
              continue

          particle = Particle(hsObj=self,
                              resultsDB=self._resultsDB,
                              flattenedPermuteVars=self._flattenedPermutations,
                              evolveFromState=useParticle)
          return (False, particle, swarmId)

        # END: for (swarmSize, swarmId) in swarmSizeAndIdList:
        # No success in this swarm, onto next swarm

      # ====================================================================
      # We couldn't find a particle in this sprint ready to evolve. If
      #  speculative particles is OFF, we have to wait for one or more other
      #  workers to finish up their particles before we can do anything.
      if not self._speculativeParticles:
        self.logger.info("Waiting for one or more of the %s swarms "
            "to complete a generation before evolving any more particles" \
            % (str(swarmIds)))
        return (False, None, None)

      # END: while True:
      # No success in this sprint, into next sprint

  def _okToExit(self):
    """Test if it's OK to exit this worker. This is only called when we run
    out of prospective new models to evaluate. This method sees if all models
    have matured yet. If not, it will sleep for a bit and return False. This
    will indicate to the hypersearch worker that we should keep running, and
    check again later. This gives this worker a chance to pick up and adopt any
    model which may become orphaned by another worker before it matures.

    If all models have matured, this method will send a STOP message to all
    matured, running models (presummably, there will be just one - the model
    which thinks it's the best) before returning True.
    """
    # Send an update status periodically to the JobTracker so that it doesn't
    # think this worker is dead.
    print >> sys.stderr, "reporter:status:In hypersearchV2: _okToExit"

    # Any immature models still running?
    if not self._jobCancelled:
      (_, modelIds, _, _, _) = self._resultsDB.getParticleInfos(matured=False)
      if len(modelIds) > 0:
        self.logger.info("Ready to end hyperseach, but not all models have " \
                         "matured yet. Sleeping a bit to wait for all models " \
                         "to mature.")
        # Sleep for a bit, no need to check for orphaned models very often
        time.sleep(5.0 * random.random())
        return False

    # All particles have matured, send a STOP signal to any that are still
    # running.
    (_, modelIds, _, _, _) = self._resultsDB.getParticleInfos(completed=False)
    for modelId in modelIds:
      self.logger.info("Stopping model %d because the search has ended" \
                          % (modelId))
      self._cjDAO.modelSetFields(modelId,
                      dict(engStop=ClientJobsDAO.STOP_REASON_STOPPED),
                      ignoreUnchanged = True)

    # Update the HsState to get the accurate field contributions.
    self._hsStatePeriodicUpdate()
    pctFieldContributions, absFieldContributions = \
                                          self._hsState.getFieldContributions()


    # Update the results field with the new field contributions.
    jobResultsStr = self._cjDAO.jobGetFields(self._jobID, ['results'])[0]
    if jobResultsStr is not None:
      jobResults = json.loads(jobResultsStr)
    else:
      jobResults = {}

    # Update the fieldContributions field.
    if pctFieldContributions != jobResults.get('fieldContributions', None):
      jobResults['fieldContributions'] = pctFieldContributions
      jobResults['absoluteFieldContributions'] = absFieldContributions

      isUpdated = self._cjDAO.jobSetFieldIfEqual(self._jobID,
                                                   fieldName='results',
                                                   curValue=jobResultsStr,
                                                   newValue=json.dumps(jobResults))
      if isUpdated:
        self.logger.info('Successfully updated the field contributions:%s',
                                                              pctFieldContributions)
      else:
        self.logger.info('Failed updating the field contributions, ' \
                         'another hypersearch worker must have updated it')

    return True

  def killSwarmParticles(self, swarmID):
    (_, modelIds, _, _, _) = self._resultsDB.getParticleInfos(
        swarmId=swarmID, completed=False)
    for modelId in modelIds:
      self.logger.info("Killing the following models in swarm '%s' because"
                       "the swarm is being terminated: %s" % (swarmID,
                                                              str(modelIds)))
      self._cjDAO.modelSetFields(
          modelId, dict(engStop=ClientJobsDAO.STOP_REASON_KILLED),
          ignoreUnchanged=True)

  def createModels(self, numModels=1):
    """Create one or more new models for evaluation. These should NOT be models
    that we already know are in progress (i.e. those that have been sent to us
    via recordModelProgress). We return a list of models to the caller
    (HypersearchWorker) and if one can be successfully inserted into
    the models table (i.e. it is not a duplicate) then HypersearchWorker will
    turn around and call our runModel() method, passing in this model. If it
    is a duplicate, HypersearchWorker will call this method again. A model
    is a duplicate if either the  modelParamsHash or particleHash is
    identical to another entry in the model table.

    The numModels is provided by HypersearchWorker as a suggestion as to how
    many models to generate. This particular implementation only ever returns 1
    model.

    Before choosing some new models, we first do a sweep for any models that 
    may have been abandonded by failed workers. If/when we detect an abandoned 
    model, we mark it as complete and orphaned and hide it from any subsequent 
    queries to our ResultsDB. This effectively considers it as if it never 
    existed. We also change the paramsHash and particleHash in the model record 
    of the models table so that we can create another model with the same 
    params and particle status and run it (which we then do immediately).

    The modelParamsHash returned for each model should be a hash (max allowed
    size of ClientJobsDAO.hashMaxSize) that uniquely identifies this model by
    it's params and the optional particleHash should be a hash of the particleId
    and generation index. Every model that gets placed into the models database,
    either by this worker or another worker, will have these hashes computed for
    it. The recordModelProgress gets called for every model in the database and
    the hash is used to tell which, if any, are the same as the ones this worker
    generated.

    NOTE: We check first ourselves for possible duplicates using the paramsHash
    before we return a model. If HypersearchWorker failed to insert it (because
    some other worker beat us to it), it will turn around and call our
    recordModelProgress with that other model so that we now know about it. It
    will then call createModels() again.

    This methods returns an exit boolean and the model to evaluate. If there is
    no model to evalulate, we may return False for exit because we want to stay
    alive for a while, waiting for all other models to finish. This gives us
    a chance to detect and pick up any possibly orphaned model by another
    worker.

    Parameters:
    ----------------------------------------------------------------------
    numModels:   number of models to generate
    retval:      (exit, models)
                    exit: true if this worker should exit.
                    models: list of tuples, one for each model. Each tuple contains:
                      (modelParams, modelParamsHash, particleHash)

                 modelParams is a dictionary containing the following elements:

                   structuredParams: dictionary containing all variables for
                     this model, with encoders represented as a dict within
                     this dict (or None if they are not included.

                   particleState: dictionary containing the state of this
                     particle. This includes the position and velocity of
                     each of it's variables, the particleId, and the particle
                     generation index. It contains the following keys:

                     id: The particle Id of the particle we are using to
                           generate/track this model. This is a string of the
                           form <hypesearchWorkerId>.<particleIdx>
                     genIdx: the particle's generation index. This starts at 0
                           and increments every time we move the particle to a
                           new position.
                     swarmId: The swarmId, which is a string of the form
                       <encoder>.<encoder>... that describes this swarm
                     varStates: dict of the variable states. The key is the
                         variable name, the value is a dict of the variable's
                         position, velocity, bestPosition, bestResult, etc.
    """
    
    # Check for and mark orphaned models
    self._checkForOrphanedModels()
    
    modelResults = []
    for _ in xrange(numModels):
      candidateParticle = None

      # If we've reached the max # of model to evaluate, we're done.
      if (self._maxModels is not None and
          (self._resultsDB.numModels() - self._resultsDB.getNumErrModels()) >=
          self._maxModels):

        return (self._okToExit(), [])

      # If we don't already have a particle to work on, get a candidate swarm and
      # particle to work with. If None is returned for the particle it means
      # either that the search is over (if exitNow is also True) or that we need
      # to wait for other workers to finish up their models before we can pick
      # another particle to run (if exitNow is False).
      if candidateParticle is None:
        (exitNow, candidateParticle, candidateSwarm) = (
            self._getCandidateParticleAndSwarm())
      if candidateParticle is None:
        if exitNow:
          return (self._okToExit(), [])
        else:
          # Send an update status periodically to the JobTracker so that it doesn't
          # think this worker is dead.
          print >> sys.stderr, "reporter:status:In hypersearchV2: speculativeWait"
          time.sleep(self._speculativeWaitSecondsMax * random.random())
          return (False, [])
      useEncoders = candidateSwarm.split('.')
      numAttempts = 0

      # Loop until we can create a unique model that we haven't seen yet.
      while True:

        # If this is the Nth attempt with the same candidate, agitate it a bit
        # to find a new unique position for it.
        if numAttempts >= 1:
          self.logger.debug("Agitating particle to get unique position after %d "
                  "failed attempts in a row" % (numAttempts))
          candidateParticle.agitate()

        # Create the hierarchical params expected by the base description. Note
        # that this is where we incorporate encoders that have no permuted
        # values in them.
        position = candidateParticle.getPosition()
        structuredParams = dict()
        def _buildStructuredParams(value, keys):
          flatKey = _flattenKeys(keys)
          # If it's an encoder, either put in None if it's not used, or replace
          # all permuted constructor params with the actual position.
          if flatKey in self._encoderNames:
            if flatKey in useEncoders:
              # Form encoder dict, substituting in chosen permutation values.
              return value.getDict(flatKey, position)
            # Encoder not used.
            else:
              return None
          # Regular top-level variable.
          elif flatKey in position:
            return position[flatKey]
          # Fixed override of a parameter in the base description.
          else:
            return value

        structuredParams = rCopy(self._permutations,
                                           _buildStructuredParams,
                                           discardNoneKeys=False)

        # Create the modelParams.
        modelParams = dict(
                   structuredParams=structuredParams,
                   particleState = candidateParticle.getState()
                   )

        # And the hashes.
        m = hashlib.md5()
        m.update(sortedJSONDumpS(structuredParams))
        m.update(self._baseDescriptionHash)
        paramsHash = m.digest()

        particleInst = "%s.%s" % (modelParams['particleState']['id'],
                                  modelParams['particleState']['genIdx'])
        particleHash = hashlib.md5(particleInst).digest()

        # Increase attempt counter
        numAttempts += 1

        # If this is a new one, and passes the filter test, exit with it.
        # TODO: There is currently a problem with this filters implementation as
        # it relates to self._maxUniqueModelAttempts. When there is a filter in
        # effect, we should try a lot more times before we decide we have
        # exhausted the parameter space for this swarm. The question is, how many
        # more times?
        if self._filterFunc and not self._filterFunc(structuredParams):
          valid = False
        else:
          valid = True
        if valid and self._resultsDB.getModelIDFromParamsHash(paramsHash) is None:
          break

        # If we've exceeded the max allowed number of attempts, mark this swarm
        #  as completing or completed, so we don't try and allocate any more new
        #  particles to it, and pick another.
        if numAttempts >= self._maxUniqueModelAttempts:
          (exitNow, candidateParticle, candidateSwarm) \
                = self._getCandidateParticleAndSwarm(
                                              exhaustedSwarmId=candidateSwarm)
          if candidateParticle is None:
            if exitNow:
              return (self._okToExit(), [])
            else:
              time.sleep(self._speculativeWaitSecondsMax * random.random())
              return (False, [])
          numAttempts = 0
          useEncoders = candidateSwarm.split('.')

      # Log message
      if self.logger.getEffectiveLevel() <= logging.DEBUG:
        self.logger.debug("Submitting new potential model to HypersearchWorker: \n%s"
                       % (pprint.pformat(modelParams, indent=4)))
      modelResults.append((modelParams, paramsHash, particleHash))
    return (False, modelResults)

  def recordModelProgress(self, modelID, modelParams, modelParamsHash, results,
                         completed, completionReason, matured, numRecords):
    """Record or update the results for a model. This is called by the
    HSW whenever it gets results info for another model, or updated results
    on a model that is still running.

    The first time this is called for a given modelID, the modelParams will
    contain the params dict for that model and the modelParamsHash will contain
    the hash of the params. Subsequent updates of the same modelID will
    have params and paramsHash values of None (in order to save overhead).

    The Hypersearch object should save these results into it's own working
    memory into some table, which it then uses to determine what kind of
    new models to create next time createModels() is called.

    Parameters:
    ----------------------------------------------------------------------
    modelID:        ID of this model in models table
    modelParams:    params dict for this model, or None if this is just an update
                    of a model that it already previously reported on.

                    See the comments for the createModels() method for a
                    description of this dict.

    modelParamsHash:  hash of the modelParams dict, generated by the worker
                    that put it into the model database.
    results:        tuple containing (allMetrics, optimizeMetric). Each is a
                    dict containing metricName:result pairs. .
                    May be none if we have no results yet.
    completed:      True if the model has completed evaluation, False if it
                      is still running (and these are online results)
    completionReason: One of the ClientJobsDAO.CMPL_REASON_XXX equates
    matured:        True if this model has matured. In most cases, once a
                    model matures, it will complete as well. The only time a
                    model matures and does not complete is if it's currently
                    the best model and we choose to keep it running to generate
                    predictions.
    numRecords:     Number of records that have been processed so far by this
                      model.
    """
    if results is None:
      metricResult = None
    else:
      metricResult = results[1].values()[0]

    # Update our database.
    errScore = self._resultsDB.update(modelID=modelID,
                modelParams=modelParams,modelParamsHash=modelParamsHash,
                metricResult=metricResult, completed=completed,
                completionReason=completionReason, matured=matured,
                numRecords=numRecords)

    # Log message.
    self.logger.debug('Received progress on model %d: completed: %s, '
                      'cmpReason: %s, numRecords: %d, errScore: %s' ,
                      modelID, completed, completionReason, numRecords, errScore)

    # Log best so far.
    (bestModelID, bestResult) = self._resultsDB.bestModelIdAndErrScore()
    self.logger.debug('Best err score seen so far: %s on model %s' % \
                     (bestResult, bestModelID))

  def runModel(self, modelID, jobID, modelParams, modelParamsHash,
               jobsDAO, modelCheckpointGUID):
    """Run the given model.

    This runs the model described by 'modelParams'. Periodically, it updates
    the results seen on the model to the model database using the databaseAO
    (database Access Object) methods.

    Parameters:
    -------------------------------------------------------------------------
    modelID:             ID of this model in models table

    jobID:               ID for this hypersearch job in the jobs table

    modelParams:         parameters of this specific model
                         modelParams is a dictionary containing the name/value
                         pairs of each variable we are permuting over. Note that
                         variables within an encoder spec have their name
                         structure as:
                           <encoderName>.<encodrVarName>

    modelParamsHash:     hash of modelParamValues

    jobsDAO              jobs data access object - the interface to the jobs
                          database where model information is stored

    modelCheckpointGUID: A persistent, globally-unique identifier for
                          constructing the model checkpoint key
    """
    
    # We're going to make an assumption that if we're not using streams, that
    #  we also don't need checkpoints saved. For now, this assumption is OK
    #  (if there are no streams, we're typically running on a single machine
    #  and just save models to files) but we may want to break this out as
    #  a separate controllable parameter in the future
    if not self._createCheckpoints:
      modelCheckpointGUID = None
    
    # Register this model in our database
    self._resultsDB.update(modelID=modelID,
                           modelParams=modelParams,
                           modelParamsHash=modelParamsHash,
                           metricResult = None,
                           completed = False,
                           completionReason = None,
                           matured = False,
                           numRecords = 0)

    # Get the structured params, which we pass to the base description
    structuredParams = modelParams['structuredParams']

    if self.logger.getEffectiveLevel() <= logging.DEBUG:
      self.logger.debug("Running Model. \nmodelParams: %s, \nmodelID=%s, " % \
                        (pprint.pformat(modelParams, indent=4), modelID))

    # Record time.clock() so that we can report on cpu time
    cpuTimeStart = time.clock()

    # Run the experiment. This will report the results back to the models
    #  database for us as well.
    logLevel = self.logger.getEffectiveLevel()
    try:
      if self._dummyModel is None or self._dummyModel is False:
        (cmpReason, cmpMsg) = runModelGivenBaseAndParams(
                    modelID=modelID,
                    jobID=jobID,
                    baseDescription=self._baseDescription,
                    params=structuredParams,
                    predictedField=self._predictedField,
                    reportKeys=self._reportKeys,
                    optimizeKey=self._optimizeKey,
                    jobsDAO=jobsDAO,
                    modelCheckpointGUID=modelCheckpointGUID,
                    logLevel=logLevel,
                    predictionCacheMaxRecords=self._predictionCacheMaxRecords)
      else:
        dummyParams = dict(self._dummyModel)
        dummyParams['permutationParams'] = structuredParams
        if self._dummyModelParamsFunc is not None:
          permInfo = dict(structuredParams)
          permInfo ['generation'] = modelParams['particleState']['genIdx']
          dummyParams.update(self._dummyModelParamsFunc(permInfo))

        (cmpReason, cmpMsg) = runDummyModel(
                      modelID=modelID,
                      jobID=jobID,
                      params=dummyParams,
                      predictedField=self._predictedField,
                      reportKeys=self._reportKeys,
                      optimizeKey=self._optimizeKey,
                      jobsDAO=jobsDAO,
                      modelCheckpointGUID=modelCheckpointGUID,
                      logLevel=logLevel,
                      predictionCacheMaxRecords=self._predictionCacheMaxRecords)

      # Write out the completion reason and message
      jobsDAO.modelSetCompleted(modelID,
                            completionReason = cmpReason,
                            completionMsg = cmpMsg,
                            cpuTime = time.clock() - cpuTimeStart)


    except InvalidConnectionException, e:
      self.logger.warn("%s", e)
