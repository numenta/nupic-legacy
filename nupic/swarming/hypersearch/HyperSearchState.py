#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have an agreement
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



class HyperSearchState(object):
  """
    Defines the class storing necessary state for hyperSearch runs.
  """

  def __init__(self, permuteVars, particles, numParticles, options):
    """
      @oaram  permuteVars   (list)    Collection of client-specified permutation
                                      variables necessary for a given run.
      @param  particles     (list)    Collection of particles instantiated by
                                      client, in HyperSearchRunner.
      @param  numParticles  (int)     Client provided number of particles in
                                      swarm. TODO: May want to just provide a
                                      generic param with swarm-specific options?
      @param  options       (dict)    Dict of client-specified params for
                                      evaluating models/running jobs.
    """
    # Number of particles in current running instance of swarm
    self.numParticles = numParticles
    # Store collection of user-specified permutation variables
    self.permuteVars = permuteVars
    self.swarmIDs = []
    # Store collection of particles for given swarm, where key is
    # the swarmID and value is the list of particles for the swarm
    self.particles = dict()
    # Dict of params used to generate particular model
    self.options= options
    # Dict of (swarmID, globalBest) pairs
    self.bestScore = dict()
    # (swarmID, swarmState) pairs
    self.swarmInfo = dict()

    # Debugging info
    self.jobIDs = []
    self.modelIDs = []

    # TODO: Define custom JobInfo module with info about all running jobs?
    # This instance variable would then be a dict of (jobID, JobInfo) instances
    self.jobStates = dict()

    # TODO: Ditto
    self.modelStates = dict()

  def getParticleStates(self):
    """
      Return a list of all the particle states in the current swarm.
    """
    return [particle.getState() for particle in self.particles]


  def updateState(self, swarmID, score):
    """
      Update score for given swarm.

      @param  swarmID   (int)     ID of swarm to be updated
      @param  score     (int)     Score to update for swarm
    """
    self.bestScore[swarmID] = score


  def addJobID(self, jobID):
    self.jobIDs.append(jobID)


  def addModelID(self, modelID):
    self.modelIDs.append(modelID)


  def addModel(self, modelID, modelInfo):
    self.modelStates[modelID] = modelInfo


  def addJob(self, jobID, jobInfo):
    self.jobStates[jobID] = jobInfo


  def getJobInfo(self, jobID):
    return self.jobStates[jobID]


  def getModelInfo(self, modelID):
    return self.modelIDs[modelID]


  def __repr__(self):
    raise NotImplementedError
