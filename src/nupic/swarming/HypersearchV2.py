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

from nupic.swarming.hypersearch.permutation_helpers import *
from nupic.swarming.hypersearch.Particle import Particle
from nupic.swarming.hypersearch.errorcodes import ErrorCodes
from nupic.swarming.hypersearch.SwarmTerminator import SwarmTerminator
from nupic.swarming.hypersearch.HsState import HsState, HsSearchType

from nupic.frameworks.opf import opfhelpers
from nupic.swarming.experimentutils import InferenceType
from nupic.swarming.utils import sortedJSONDumpS, rApply, rCopy
from nupic.swarming.utils import clippedObj
from nupic.swarming.utils import (runModelGivenBaseAndParams, runDummyModel)
from nupic.database.ClientJobsDAO import (
    ClientJobsDAO, InvalidConnectionException)
from nupic.swarming.exp_generator.ExpGenerator import expGenerator


def _flattenKeys(keys):
  return '|'.join(keys)



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
