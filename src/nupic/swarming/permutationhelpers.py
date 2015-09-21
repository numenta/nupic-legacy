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

"""
This class provides utility classes and functions for use inside permutations
scripts.
"""

import random

import numpy
from nupic.support.configuration import Configuration


class PermuteVariable(object):
  """The base class of all PermuteXXX classes that can be used from within
  a permutation script."""

  def __init__(self):
    pass

  def getState(self):
    """Return the current state of this particle. This is used for
    communicating our state into a model record entry so that it can be
    instantiated on another worker."""
    raise NotImplementedError

  def setState(self, state):
    """Set the current state of this particle. This is counterpart to getState.
    """
    raise NotImplementedError

  def getPosition(self):
    """for int vars, returns position to nearest int

    Parameters:
    --------------------------------------------------------------
    retval:     current position
    """
    raise NotImplementedError

  def agitate(self):
    """This causes the variable to jiggle away from its current position.
    It does this by increasing its velocity by a multiplicative factor.
    Every time agitate() is called, the velocity will increase. In this way,
    you can call agitate over and over again until the variable reaches a
    new position."""
    raise NotImplementedError


  #=========================================================================
  def newPosition(self, globalBestPosition, rng):
    """Choose a new position based on results obtained so far from other
    particles and the passed in globalBestPosition.

    Parameters:
    --------------------------------------------------------------
    globalBestPosition:   global best position for this colony
    rng:                  instance of random.Random() used for generating
                              random numbers
    retval:       new position
    """
    raise NotImplementedError


  def pushAwayFrom(self, otherVars, rng):
    """Choose a new position that is as far away as possible from all
    'otherVars', where 'otherVars' is a list of PermuteVariable instances.

    Parameters:
    --------------------------------------------------------------
    otherVars:   list of other PermuteVariables to push away from
    rng:                  instance of random.Random() used for generating
                              random numbers
    """
    raise NotImplementedError

  def resetVelocity(self, rng):
    """Reset the velocity to be some fraction of the total distance. This
    is called usually when we start a new swarm and want to start at the
    previous best position found in the previous swarm but with a
    velocity which is a known fraction of the total distance between min
    and max.

    Parameters:
    --------------------------------------------------------------
    rng:                  instance of random.Random() used for generating
                              random numbers
    """
    raise NotImplementedError


class PermuteFloat(PermuteVariable):
  """Define a permutation variable which can take on floating point values."""

  def __init__(self, min, max, stepSize=None, inertia=None, cogRate=None,
               socRate=None):
    """Construct a variable that permutes over floating point values using
    the Particle Swarm Optimization (PSO) algorithm. See descriptions of
    PSO (i.e. http://en.wikipedia.org/wiki/Particle_swarm_optimization)
    for references to the inertia, cogRate, and socRate parameters.

    Parameters:
    -----------------------------------------------------------------------
    min:          min allowed value of position
    max:          max allowed value of position
    stepSize:     if not None, the position must be at min + N * stepSize,
                    where N is an integer
    inertia:      The inertia for the particle.
    cogRate:      This parameter controls how much the particle is affected
                    by its distance from it's local best position
    socRate:      This parameter controls how much the particle is affected
                    by its distance from the global best position

    """
    super(PermuteFloat, self).__init__()
    self.min = min
    self.max = max
    self.stepSize = stepSize

    # The particle's initial position and velocity.
    self._position = (self.max + self.min) / 2.0
    self._velocity = (self.max - self.min) / 5.0


    # The inertia, cognitive, and social components of the particle
    self._inertia = (float(Configuration.get("nupic.hypersearch.inertia"))
                     if inertia is None else inertia)
    self._cogRate = (float(Configuration.get("nupic.hypersearch.cogRate"))
                     if cogRate is None else cogRate)
    self._socRate = (float(Configuration.get("nupic.hypersearch.socRate"))
                     if socRate is None else socRate)

    # The particle's local best position and the best global position.
    self._bestPosition = self.getPosition()
    self._bestResult = None

  def __repr__(self):
    """See comments in base class."""
    return ("PermuteFloat(min=%f, max=%f, stepSize=%s) [position=%f(%f), "
            "velocity=%f, _bestPosition=%s, _bestResult=%s]" % (
                self.min, self.max, self.stepSize, self.getPosition(),
                self._position, self._velocity, self._bestPosition,
                self._bestResult))

  def getState(self):
    """See comments in base class."""
    return dict(_position = self._position,
                position = self.getPosition(),
                velocity = self._velocity,
                bestPosition = self._bestPosition,
                bestResult = self._bestResult)

  def setState(self, state):
    """See comments in base class."""
    self._position = state['_position']
    self._velocity = state['velocity']
    self._bestPosition = state['bestPosition']
    self._bestResult = state['bestResult']

  def getPosition(self):
    """See comments in base class."""
    if self.stepSize is None:
      return self._position

    # Find nearest step
    numSteps = (self._position - self.min)  / self.stepSize
    numSteps = int(round(numSteps))
    position = self.min + (numSteps * self.stepSize)
    position = max(self.min, position)
    position = min(self.max, position)
    return position

  def agitate(self):
    """See comments in base class."""
    # Increase velocity enough that it will be higher the next time
    # newPosition() is called. We know that newPosition multiplies by inertia,
    # so take that into account.
    self._velocity *= 1.5 / self._inertia

    # Clip velocity
    maxV = (self.max - self.min)/2
    if self._velocity > maxV:
      self._velocity = maxV
    elif self._velocity < -maxV:
      self._velocity = -maxV

    # if we at the max or min, reverse direction
    if self._position == self.max and self._velocity > 0:
      self._velocity *= -1
    if self._position == self.min and self._velocity < 0:
      self._velocity *= -1

  def newPosition(self, globalBestPosition, rng):
    """See comments in base class."""
    # First, update the velocity. The new velocity is given as:
    # v = (inertia * v)  + (cogRate * r1 * (localBest-pos))
    #                    + (socRate * r2 * (globalBest-pos))
    #
    # where r1 and r2 are random numbers between 0 and 1.0
    lb=float(Configuration.get("nupic.hypersearch.randomLowerBound"))
    ub=float(Configuration.get("nupic.hypersearch.randomUpperBound"))

    self._velocity = (self._velocity * self._inertia + rng.uniform(lb, ub) *
                      self._cogRate * (self._bestPosition - self.getPosition()))
    if globalBestPosition is not None:
      self._velocity += rng.uniform(lb, ub) * self._socRate * (
          globalBestPosition - self.getPosition())

    # update position based on velocity
    self._position += self._velocity

    # Clip it
    self._position = max(self.min, self._position)
    self._position = min(self.max, self._position)

    # Return it
    return self.getPosition()

  def pushAwayFrom(self, otherPositions, rng):
    """See comments in base class."""
    # If min and max are the same, nothing to do
    if self.max == self.min:
      return

    # How many potential other positions to evaluate?
    numPositions = len(otherPositions) * 4
    if numPositions == 0:
      return

    # Assign a weight to each potential position based on how close it is
    # to other particles.
    stepSize = float(self.max-self.min) / numPositions
    positions = numpy.arange(self.min, self.max + stepSize, stepSize)

    # Get rid of duplicates.
    numPositions = len(positions)
    weights = numpy.zeros(numPositions)

    # Assign a weight to each potential position, based on a gaussian falloff
    # from each existing variable. The weight of a variable to each potential
    # position is given as:
    #    e ^ -(dist^2/stepSize^2)
    maxDistanceSq = -1 * (stepSize ** 2)
    for pos in otherPositions:
      distances = pos - positions
      varWeights = numpy.exp(numpy.power(distances, 2) / maxDistanceSq)
      weights += varWeights


    # Put this particle at the position with smallest weight.
    positionIdx = weights.argmin()
    self._position = positions[positionIdx]

    # Set its best position to this.
    self._bestPosition = self.getPosition()

    # Give it a random direction.
    self._velocity *= rng.choice([1, -1])

  def resetVelocity(self, rng):
    """See comments in base class."""
    maxVelocity = (self.max - self.min) / 5.0
    self._velocity = maxVelocity #min(abs(self._velocity), maxVelocity)
    self._velocity *= rng.choice([1, -1])


class PermuteInt(PermuteFloat):
  """Define a permutation variable which can take on integer values."""

  def __init__(self, min, max, stepSize=1, inertia=None, cogRate=None,
               socRate=None):
    super(PermuteInt, self).__init__(min, max, stepSize, inertia=inertia,
                                     cogRate=cogRate, socRate=socRate)

  def __repr__(self):
    """See comments in base class."""
    return ("PermuteInt(min=%d, max=%d, stepSize=%d) [position=%d(%f), "
            "velocity=%f, _bestPosition=%s, _bestResult=%s]" % (
                self.min, self.max, self.stepSize, self.getPosition(),
                self._position, self._velocity, self._bestPosition,
                self._bestResult))

  def getPosition(self):
    """See comments in base class."""
    position = super(PermuteInt, self).getPosition()
    position =  int(round(position))
    return position


class PermuteChoices(PermuteVariable):
  """Define a permutation variable which can take on discrete choices."""

  def __init__(self, choices, fixEarly=False):
    super(PermuteChoices, self).__init__()

    self.choices = choices
    self._positionIdx = 0

    # Keep track of the results obtained for each choice
    self._resultsPerChoice = [[]] * len(self.choices)

    # The particle's local best position and the best global position
    self._bestPositionIdx = self._positionIdx
    self._bestResult = None

    # If this is true then we only return the best position for this encoder
    # after all choices have been seen.
    self._fixEarly = fixEarly

    # Factor that affects how quickly we assymptote to simply choosing the
    # choice with the best error value
    self._fixEarlyFactor = .7

  def __repr__(self):
    """See comments in base class."""
    return "PermuteChoices(choices=%s) [position=%s]" % (self.choices,
                                      self.choices[self._positionIdx])

  def getState(self):
    """See comments in base class."""
    return dict(_position = self.getPosition(),
                position = self.getPosition(),
                velocity = None,
                bestPosition = self.choices[self._bestPositionIdx],
                bestResult = self._bestResult)

  def setState(self, state):
    """See comments in base class."""
    self._positionIdx = self.choices.index(state['_position'])
    self._bestPositionIdx = self.choices.index(state['bestPosition'])
    self._bestResult = state['bestResult']

  def setResultsPerChoice(self, resultsPerChoice):
    """Setup our resultsPerChoice history based on the passed in
    resultsPerChoice.

    For example, if this variable has the following choices:
      ['a', 'b', 'c']

    resultsPerChoice will have up to 3 elements, each element is a tuple
    containing (choiceValue, errors) where errors is the list of errors
    received from models that used the specific choice:
    retval:
      [('a', [0.1, 0.2, 0.3]), ('b', [0.5, 0.1, 0.6]), ('c', [0.2])]
    """
    # Keep track of the results obtained for each choice.
    self._resultsPerChoice = [[]] * len(self.choices)
    for (choiceValue, values) in resultsPerChoice:
      choiceIndex = self.choices.index(choiceValue)
      self._resultsPerChoice[choiceIndex] = list(values)

  def getPosition(self):
    """See comments in base class."""
    return self.choices[self._positionIdx]

  def agitate(self):
    """See comments in base class."""
    # Not sure what to do for choice variables....
    # TODO: figure this out
    pass

  def newPosition(self, globalBestPosition, rng):
    """See comments in base class."""
    # Compute the mean score per choice.
    numChoices = len(self.choices)
    meanScorePerChoice = []
    overallSum = 0
    numResults = 0

    for i in range(numChoices):
      if len(self._resultsPerChoice[i]) > 0:
        data = numpy.array(self._resultsPerChoice[i])
        meanScorePerChoice.append(data.mean())
        overallSum += data.sum()
        numResults += data.size
      else:
        meanScorePerChoice.append(None)

    if numResults == 0:
      overallSum = 1.0
      numResults = 1

    # For any choices we don't have a result for yet, set to the overall mean.
    for i in range(numChoices):
      if meanScorePerChoice[i] is None:
        meanScorePerChoice[i] = overallSum / numResults

    # Now, pick a new choice based on the above probabilities. Note that the
    #  best result is the lowest result. We want to make it more likely to
    #  pick the choice that produced the lowest results. So, we need to invert
    #  the scores (someLargeNumber - score).
    meanScorePerChoice = numpy.array(meanScorePerChoice)

    # Invert meaning.
    meanScorePerChoice = (1.1 * meanScorePerChoice.max()) - meanScorePerChoice

    # If you want the scores to quickly converge to the best choice, raise the
    # results to a power. This will cause lower scores to become lower
    # probability as you see more results, until it eventually should
    # assymptote to only choosing the best choice.
    if self._fixEarly:
      meanScorePerChoice **= (numResults * self._fixEarlyFactor / numChoices)
    # Normalize.
    total = meanScorePerChoice.sum()
    if total == 0:
      total = 1.0
    meanScorePerChoice /= total

    # Get distribution and choose one based on those probabilities.
    distribution = meanScorePerChoice.cumsum()
    r = rng.random() * distribution[-1]
    choiceIdx = numpy.where(r <= distribution)[0][0]

    self._positionIdx = choiceIdx
    return self.getPosition()

  def pushAwayFrom(self, otherPositions, rng):
    """See comments in base class."""
    # Get the count of how many in each position
    positions = [self.choices.index(x) for x in otherPositions]

    positionCounts = [0] * len(self.choices)
    for pos in positions:
      positionCounts[pos] += 1

    self._positionIdx = numpy.array(positionCounts).argmin()
    self._bestPositionIdx = self._positionIdx

  def resetVelocity(self, rng):
    """See comments in base class."""
    pass


class PermuteEncoder(PermuteVariable):
  """ A permutation variable that defines a field encoder. This serves as
  a container for the encoder constructor arguments.
  """

  def __init__(self, fieldName, encoderClass, name=None,  **kwArgs):
    super(PermuteEncoder, self).__init__()
    self.fieldName = fieldName
    if name is None:
      name = fieldName
    self.name = name
    self.encoderClass = encoderClass

    # Possible values in kwArgs include: w, n, minval, maxval, etc.
    self.kwArgs = dict(kwArgs)

  def __repr__(self):
    """See comments in base class."""
    suffix = ""
    for key, value in self.kwArgs.items():
      suffix += "%s=%s, " % (key, value)

    return "PermuteEncoder(fieldName=%s, encoderClass=%s, name=%s, %s)" % (
        (self.fieldName, self.encoderClass, self.name, suffix))

  def getDict(self, encoderName, flattenedChosenValues):
    """ Return a dict that can be used to construct this encoder. This dict
    can be passed directly to the addMultipleEncoders() method of the
    multi encoder.

    Parameters:
    ----------------------------------------------------------------------
    encoderName:            name of the encoder
    flattenedChosenValues:  dict of the flattened permutation variables. Any
                              variables within this dict whose key starts
                              with encoderName will be substituted for
                              encoder constructor args which are being
                              permuted over.
    """
    encoder = dict(fieldname=self.fieldName,
                   name=self.name)

    # Get the position of each encoder argument
    for encoderArg, value in self.kwArgs.iteritems():
      # If a permuted variable, get its chosen value.
      if isinstance(value, PermuteVariable):
        value = flattenedChosenValues["%s:%s" % (encoderName, encoderArg)]

      encoder[encoderArg] = value

    # Special treatment for DateEncoder timeOfDay and dayOfWeek stuff. In the
    #  permutations file, the class can be one of:
    #    DateEncoder.timeOfDay
    #    DateEncoder.dayOfWeek
    #    DateEncoder.season
    # If one of these, we need to intelligently set the constructor args.
    if '.' in self.encoderClass:
      (encoder['type'], argName) = self.encoderClass.split('.')
      argValue = (encoder['w'], encoder['radius'])
      encoder[argName] = argValue
      encoder.pop('w')
      encoder.pop('radius')
    else:
      encoder['type'] = self.encoderClass

    return encoder


class Tests(object):

  def _testValidPositions(self, varClass, minValue, maxValue, stepSize,
                          iterations=100):
    """Run a bunch of iterations on a PermuteVar and collect which positions
    were visited. Verify that they were all valid.
    """

    positions = set()
    cogRate = 2.0
    socRate = 2.0
    inertia = None
    gBestPosition = maxValue
    lBestPosition = minValue
    foundBestPosition = None
    foundBestResult = None
    rng = random.Random()
    rng.seed(42)
    var = varClass(min=minValue, max=maxValue, stepSize=stepSize,
                       inertia=inertia, cogRate=cogRate, socRate=socRate)
    for _ in xrange(iterations):
      pos = var.getPosition()
      if self.verbosity >= 1:
        print "pos: %f" % (pos),
      if self.verbosity >= 2:
        print var
      positions.add(pos)

      # Set the result so that the local best is at lBestPosition.
      result = 1.0 - abs(pos - lBestPosition)

      if foundBestResult is None or result > foundBestResult:
        foundBestResult = result
        foundBestPosition = pos
        state = var.getState()
        state['bestPosition'] = foundBestPosition
        state['bestResult'] = foundBestResult
        var.setState(state)

      var.newPosition(gBestPosition, rng)

    positions = sorted(positions)
    print "Positions visited (%d):" % (len(positions)), positions

    # Validate positions.
    assert (max(positions) <= maxValue)
    assert (min(positions) <= minValue)
    assert (len(positions)) <= int(round((maxValue - minValue)/stepSize)) + 1

  def _testConvergence(self, varClass, minValue, maxValue, targetValue,
                       iterations=100):
    """Test that we can converge on the right answer."""

    gBestPosition = targetValue
    lBestPosition = targetValue
    foundBestPosition = None
    foundBestResult = None
    rng = random.Random()
    rng.seed(42)

    var = varClass(min=minValue, max=maxValue)
    for _ in xrange(iterations):
      pos = var.getPosition()
      if self.verbosity >= 1:
        print "pos: %f" % (pos),
      if self.verbosity >= 2:
        print var

      # Set the result so that the local best is at lBestPosition.
      result = 1.0 - abs(pos - lBestPosition)

      if foundBestResult is None or result > foundBestResult:
        foundBestResult = result
        foundBestPosition = pos
        state = var.getState()
        state['bestPosition'] = foundBestPosition
        state['bestResult'] = foundBestResult
        var.setState(state)

      var.newPosition(gBestPosition, rng)

    # Test that we reached the target.
    print "Target: %f, Converged on: %f" % (targetValue, pos)
    assert abs(pos-targetValue) < 0.001

  def _testChoices(self):
    pc = PermuteChoices(['0', '1', '2', '3'])
    counts = [0] * 4
    rng = random.Random()
    rng.seed(42)
    # Check the without results the choices are chosen uniformly.
    for _ in range(1000):
      pos = int(pc.newPosition(None, rng))
      counts[pos] += 1
    for count in counts:
      assert count < 270 and count > 230
    print "No results permuteChoice test passed"

    # Check that with some results the choices are chosen with the lower
    # errors being chosen more often.
    choices = ['1', '11', '21', '31']
    pc = PermuteChoices(choices)
    resultsPerChoice = []
    counts = dict()
    for choice in choices:
      resultsPerChoice.append((choice, [float(choice)]))
      counts[choice] = 0
    pc.setResultsPerChoice(resultsPerChoice)
    rng = random.Random()
    rng.seed(42)
    # Check the without results the choices are chosen uniformly.
    for _ in range(1000):
      choice = pc.newPosition(None, rng)
      counts[choice] += 1
    # Make sure that as the error goes up, the number of times the choice is
    # seen goes down.
    prevCount = 1001
    for choice in choices:
      assert prevCount > counts[choice]
      prevCount = counts[choice]
    print "Results permuteChoice test passed"

    # Check that with fixEarly as you see more data points you begin heavily
    # biasing the probabilities to the one with the lowest error.
    choices = ['1', '11', '21', '31']
    pc = PermuteChoices(choices, fixEarly=True)
    resultsPerChoiceDict = dict()
    counts = dict()

    for choice in choices:
      resultsPerChoiceDict[choice] = (choice, [])
      counts[choice] = 0
    # The count of the highest probability entry, this should go up as more
    # results are seen.
    prevLowestErrorCount = 0
    for _ in range(10):
      for choice in choices:
        resultsPerChoiceDict[choice][1].append(float(choice))
        counts[choice] = 0
      pc.setResultsPerChoice(resultsPerChoiceDict.values())
      rng = random.Random()
      rng.seed(42)
      # Check the without results the choices are chosen uniformly.
      for _ in range(1000):
        choice = pc.newPosition(None, rng)
        counts[choice] += 1
      # Make sure that as the error goes up, the number of times the choice is
      # seen goes down.
      assert prevLowestErrorCount < counts['1']
      prevLowestErrorCount = counts['1']
    print "Fix early permuteChoice test passed"

  def run(self):
    """Run unit tests on this module."""

    # Set the verbosity level.
    self.verbosity = 0

    # ------------------------------------------------------------------------
    # Test that step size is handled correctly for floats
    self._testValidPositions(varClass=PermuteFloat, minValue=2.1,
                             maxValue=5.1, stepSize=0.5)

    # ------------------------------------------------------------------------
    # Test that step size is handled correctly for ints
    self._testValidPositions(varClass=PermuteInt, minValue=2,
                             maxValue=11, stepSize=3)

    # ------------------------------------------------------------------------
    # Test that step size is handled correctly for ints
    self._testValidPositions(varClass=PermuteInt, minValue=2,
                             maxValue=11, stepSize=1)


    # ------------------------------------------------------------------------
    # Test that we can converge on a target value
    # Using Float
    self._testConvergence(varClass=PermuteFloat, minValue=2.1,
                             maxValue=5.1, targetValue=5.0)
    self._testConvergence(varClass=PermuteFloat, minValue=2.1,
                             maxValue=5.1, targetValue=2.2)
    self._testConvergence(varClass=PermuteFloat, minValue=2.1,
                             maxValue=5.1, targetValue=3.5)

    # Using int
    self._testConvergence(varClass=PermuteInt, minValue=1,
                             maxValue=20, targetValue=19)
    self._testConvergence(varClass=PermuteInt, minValue=1,
                             maxValue=20, targetValue=1)


    #test permute choices
    self._testChoices()



if __name__ == '__main__':

  # Run all tests
  tests = Tests()
  tests.run()
