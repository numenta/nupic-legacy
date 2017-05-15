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

import logging
import StringIO
import copy
import pprint
import random

from nupic.swarming.hypersearch.permutation_helpers import PermuteChoices

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
        if ':' in varName:  # if an encoder
          if varName.split(':')[0] not in allowedEncoderNames:
            self.permuteVars.pop(varName)
            continue

        # All PermuteChoice variables need to know all prior results obtained
        # with each choice.
        if isinstance(self.permuteVars[varName], PermuteChoices):
          if self._hsObj._speculativeParticles:
            maxGenIdx = None
          else:
            maxGenIdx = self.genIdx - 1

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
            otherPositions.append(
              particleState['varStates'][varName]['position'])
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
                                  self.genIdx,
                                  pprint.pformat(self.permuteVars, indent=4))

  def getState(self):
    """Get the particle state as a dict. This is enough information to
    instantiate this particle on another worker."""
    varStates = dict()
    for varName, var in self.permuteVars.iteritems():
      varStates[varName] = var.getState()

    return dict(id=self.particleId,
                genIdx=self.genIdx,
                swarmId=self.swarmId,
                varStates=varStates)

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
      if ':' in varName:  # if an encoder

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
      (bestModelId, _) = self._resultsDB.bestModelIdAndErrScore(self.swarmId,
                                                                genIdx)
      if bestModelId is not None:
        (particleState, _, _, _, _) = self._resultsDB.getParticleInfo(
          bestModelId)
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
