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

"""This file implements the CLAClassifier."""

import array
from collections import deque
import itertools

import numpy


# This determines how large one of the duty cycles must get before each of the
# duty cycles are updated to the current iteration.
# This must be less than float32 size since storage is float32 size
DUTY_CYCLE_UPDATE_INTERVAL = numpy.finfo(numpy.float32).max / (2 ** 20)

g_debugPrefix = "CLAClassifier"


def _pFormatArray(array_, fmt="%.2f"):
  """Return a string with pretty-print of a numpy array using the given format
  for each element"""
  return "[ " + " ".join(fmt % x for x in array_) + " ]"


class BitHistory(object):
  """Class to store an activationPattern  bit history."""

  __slots__ = ("_classifier", "_id", "_stats", "_lastTotalUpdate",
               "_learnIteration", "_version")

  __VERSION__ = 2


  def __init__(self, classifier, bitNum, nSteps):
    """Constructor for bit history.

    Parameters:
    ---------------------------------------------------------------------
    classifier:    instance of the CLAClassifier that owns us
    bitNum:        activation pattern bit number this history is for,
                        used only for debug messages
    nSteps:        number of steps of prediction this history is for, used
                        only for debug messages
    """
    # Store reference to the classifier
    self._classifier = classifier

    # Form our "id"
    self._id = "%d[%d]" % (bitNum, nSteps)

    # Dictionary of bucket entries. The key is the bucket index, the
    # value is the dutyCycle, which is the rolling average of the duty cycle
    self._stats = array.array("f")

    # lastUpdate is the iteration number of the last time it was updated.
    self._lastTotalUpdate = None

    # The bit's learning iteration. This is updated each time store() gets
    # called on this bit.
    self._learnIteration = 0

    # Set the version to the latest version.
    # This is used for serialization/deserialization
    self._version = BitHistory.__VERSION__


  def store(self, iteration, bucketIdx):
    """Store a new item in our history.

    This gets called for a bit whenever it is active and learning is enabled

    Parameters:
    --------------------------------------------------------------------
    iteration:  the learning iteration number, which is only incremented
                  when learning is enabled
    bucketIdx:  the bucket index to store

    Save duty cycle by normalizing it to the same iteration as
    the rest of the duty cycles which is lastTotalUpdate.

    This is done to speed up computation in inference since all of the duty
    cycles can now be scaled by a single number.

    The duty cycle is brought up to the current iteration only at inference and
    only when one of the duty cycles gets too large (to avoid overflow to
    larger data type) since the ratios between the duty cycles are what is
    important. As long as all of the duty cycles are at the same iteration
    their ratio is the same as it would be for any other iteration, because the
    update is simply a multiplication by a scalar that depends on the number of
    steps between the last update of the duty cycle and the current iteration.
    """

    # If lastTotalUpdate has not been set, set it to the current iteration.
    if self._lastTotalUpdate is None:
      self._lastTotalUpdate = iteration
    # Get the duty cycle stored for this bucket.
    statsLen = len(self._stats) - 1
    if bucketIdx > statsLen:
      self._stats.extend(itertools.repeat(0.0, bucketIdx - statsLen))

    # Update it now.
    # duty cycle n steps ago is dc{-n}
    # duty cycle for current iteration is (1-alpha)*dc{-n}*(1-alpha)**(n)+alpha
    dc = self._stats[bucketIdx]

    # To get the duty cycle from n iterations ago that when updated to the
    # current iteration would equal the dc of the current iteration we simply
    # divide the duty cycle by (1-alpha)**(n). This results in the formula
    # dc'{-n} = dc{-n} + alpha/(1-alpha)**n where the apostrophe symbol is used
    # to denote that this is the new duty cycle at that iteration. This is
    # equivalent to the duty cycle dc{-n}
    denom = ((1.0 - self._classifier.alpha) **
             (iteration - self._lastTotalUpdate))
    if denom > 0:
      dcNew = dc + (self._classifier.alpha / denom)

    # This is to prevent errors associated with inf rescale if too large
    if denom == 0 or dcNew > DUTY_CYCLE_UPDATE_INTERVAL:
      exp = ((1.0 - self._classifier.alpha) **
             (iteration - self._lastTotalUpdate))
      for (bucketIdxT, dcT) in enumerate(self._stats):
        dcT *= exp
        self._stats[bucketIdxT] = dcT

      # Reset time since last update
      self._lastTotalUpdate = iteration

      # Add alpha since now exponent is 0
      dc = self._stats[bucketIdx] + self._classifier.alpha
    else:
      dc = dcNew

    self._stats[bucketIdx] = dc
    if self._classifier.verbosity >= 2:
      print "updated DC for %s, bucket %d to %f" % (self._id, bucketIdx, dc)


  def infer(self, votes):
    """Look up and return the votes for each bucketIdx for this bit.

    Parameters:
    --------------------------------------------------------------------
    votes:      a numpy array, initialized to all 0's, that should be filled
                in with the votes for each bucket. The vote for bucket index N
                should go into votes[N].
    """
    # Place the duty cycle into the votes and update the running total for
    # normalization
    total = 0
    for (bucketIdx, dc) in enumerate(self._stats):
      # Not updating to current iteration since we are normalizing anyway
      if dc > 0.0:
        votes[bucketIdx] = dc
        total += dc

    # Experiment... try normalizing the votes from each bit
    if total > 0:
      votes /= total
    if self._classifier.verbosity >= 2:
      print "bucket votes for %s:" % (self._id), _pFormatArray(votes)


  def __getstate__(self):
    return dict((elem, getattr(self, elem)) for elem in self.__slots__)


  def __setstate__(self, state):
    version = 0
    if "_version" in state:
      version = state["_version"]

    # Migrate from version 0 to version 1
    if version == 0:
      stats = state.pop("_stats")
      assert isinstance(stats, dict)
      maxBucket = max(stats.iterkeys())
      self._stats = array.array("f", itertools.repeat(0.0, maxBucket + 1))
      for (index, value) in stats.iteritems():
        self._stats[index] = value
    elif version == 1:
      state.pop("_updateDutyCycles", None)
    elif version == 2:
      pass
    else:
      raise Exception("Error while deserializing %s: Invalid version %s"
                      % (self.__class__, version))

    for (attr, value) in state.iteritems():
      setattr(self, attr, value)

    self._version = BitHistory.__VERSION__


  def write(self, proto):
    proto.id = self._id

    statsProto = proto.init("stats", len(self._stats))
    for (bucketIdx, dutyCycle) in enumerate(self._stats):
      statsProto[bucketIdx].index = bucketIdx
      statsProto[bucketIdx].dutyCycle = dutyCycle

    proto.lastTotalUpdate = self._lastTotalUpdate
    proto.learnIteration = self._learnIteration


  @classmethod
  def read(cls, proto):
    bitHistory = object.__new__(cls)

    bitHistory._id = proto.id

    for statProto in proto.stats:
      statsLen = len(bitHistory._stats) - 1
      if statProto.index > statsLen:
        bitHistory._stats.extend(
          itertools.repeat(0.0, statProto.index - statsLen))
      bitHistory._stats[statProto.index] = statProto.dutyCycle

    bitHistory._lastTotalUpdate = proto.lastTotalUpdate
    bitHistory._learnIteration = proto.learnIteration

    return bitHistory



class CLAClassifier(object):
  """
  A CLA classifier accepts a binary input from the level below (the
  "activationPattern") and information from the sensor and encoders (the
  "classification") describing the input to the system at that time step.

  When learning, for every bit in activation pattern, it records a history of 
  the classification each time that bit was active. The history is weighted so 
  that more recent activity has a bigger impact than older activity. The alpha
  parameter controls this weighting.

  For inference, it takes an ensemble approach. For every active bit in the
  activationPattern, it looks up the most likely classification(s) from the
  history stored for that bit and then votes across these to get the resulting
  classification(s).

  This classifier can learn and infer a number of simultaneous classifications
  at once, each representing a shift of a different number of time steps. For
  example, say you are doing multi-step prediction and want the predictions for
  1 and 3 time steps in advance. The CLAClassifier would learn the associations
  between the activation pattern for time step T and the classifications for
  time step T+1, as well as the associations between activation pattern T and
  the classifications for T+3. The 'steps' constructor argument specifies the
  list of time-steps you want.

  """

  __VERSION__ = 2


  def __init__(self, steps=(1,), alpha=0.001, actValueAlpha=0.3, verbosity=0):
    """Constructor for the CLA classifier.

    Parameters:
    ---------------------------------------------------------------------
    steps:    Sequence of the different steps of multi-step predictions to learn
    alpha:    The alpha used to compute running averages of the bucket duty
               cycles for each activation pattern bit. A lower alpha results
               in longer term memory.
    verbosity: verbosity level, can be 0, 1, or 2
    """
    # Save constructor args
    self.steps = steps
    self.alpha = alpha
    self.actValueAlpha = actValueAlpha
    self.verbosity = verbosity

    # Init learn iteration index
    self._learnIteration = 0

    # This contains the offset between the recordNum (provided by caller) and
    #  learnIteration (internal only, always starts at 0).
    self._recordNumMinusLearnIteration = None

    # Max # of steps of prediction we need to support
    maxSteps = max(self.steps) + 1

    # History of the last _maxSteps activation patterns. We need to keep
    # these so that we can associate the current iteration's classification
    # with the activationPattern from N steps ago
    self._patternNZHistory = deque(maxlen=maxSteps)

    # These are the bit histories. Each one is a BitHistory instance, stored in
    # this dict, where the key is (bit, nSteps). The 'bit' is the index of the
    # bit in the activation pattern and nSteps is the number of steps of
    # prediction desired for that bit.
    self._activeBitHistory = dict()

    # This contains the value of the highest bucket index we've ever seen
    # It is used to pre-allocate fixed size arrays that hold the weights of
    # each bucket index during inference
    self._maxBucketIdx = 0

    # This keeps track of the actual value to use for each bucket index. We
    # start with 1 bucket, no actual value so that the first infer has something
    # to return
    self._actualValues = [None]

    # Set the version to the latest version.
    # This is used for serialization/deserialization
    self._version = CLAClassifier.__VERSION__


  def compute(self, recordNum, patternNZ, classification, learn, infer):
    """
    Process one input sample.
    This method is called by outer loop code outside the nupic-engine. We
    use this instead of the nupic engine compute() because our inputs and
    outputs aren't fixed size vectors of reals.

    Parameters:
    --------------------------------------------------------------------
    recordNum:  Record number of this input pattern. Record numbers should
                normally increase sequentially by 1 each time unless there
                are missing records in the dataset. Knowing this information
                insures that we don't get confused by missing records.
    patternNZ:  list of the active indices from the output below
    classification: dict of the classification information:
                    bucketIdx: index of the encoder bucket
                    actValue:  actual value going into the encoder
    learn:      if true, learn this sample
    infer:      if true, perform inference

    retval:     dict containing inference results, there is one entry for each
                step in self.steps, where the key is the number of steps, and
                the value is an array containing the relative likelihood for
                each bucketIdx starting from bucketIdx 0.

                There is also an entry containing the average actual value to
                use for each bucket. The key is 'actualValues'.

                for example:
                  {1 :             [0.1, 0.3, 0.2, 0.7],
                   4 :             [0.2, 0.4, 0.3, 0.5],
                   'actualValues': [1.5, 3,5, 5,5, 7.6],
                  }
    """

    # Save the offset between recordNum and learnIteration if this is the first
    #  compute
    if self._recordNumMinusLearnIteration is None:
      self._recordNumMinusLearnIteration = recordNum - self._learnIteration

    # Update the learn iteration
    self._learnIteration = recordNum - self._recordNumMinusLearnIteration

    if self.verbosity >= 1:
      print "\n%s: compute" % g_debugPrefix
      print "  recordNum:", recordNum
      print "  learnIteration:", self._learnIteration
      print "  patternNZ (%d):" % len(patternNZ), patternNZ
      print "  classificationIn:", classification

    # Store pattern in our history
    self._patternNZHistory.append((self._learnIteration, patternNZ))

    # To allow multi-class classification, we need to be able to run learning
    # without inference being on. So initialize retval outside 
    # of the inference block.
    retval = None

    # ------------------------------------------------------------------------
    # Inference:
    # For each active bit in the activationPattern, get the classification
    # votes
    if infer:
      retval = self.infer(patternNZ, classification)
      
    # ------------------------------------------------------------------------
    # Learning:
    # For each active bit in the activationPattern, store the classification
    # info. If the bucketIdx is None, we can't learn. This can happen when the
    # field is missing in a specific record.
    if learn and classification["bucketIdx"] is not None:

      # Get classification info
      bucketIdx = classification["bucketIdx"]
      actValue = classification["actValue"]

      # Update maxBucketIndex
      self._maxBucketIdx = max(self._maxBucketIdx, bucketIdx)

      # Update rolling average of actual values if it's a scalar. If it's
      # not, it must be a category, in which case each bucket only ever
      # sees one category so we don't need a running average.
      while self._maxBucketIdx > len(self._actualValues) - 1:
        self._actualValues.append(None)
      if self._actualValues[bucketIdx] is None:
        self._actualValues[bucketIdx] = actValue
      else:
        if isinstance(actValue, int) or isinstance(actValue, float):
          self._actualValues[bucketIdx] = ((1.0 - self.actValueAlpha)
                                           * self._actualValues[bucketIdx]
                                           + self.actValueAlpha * actValue)
        else:
          self._actualValues[bucketIdx] = actValue

      # Train each pattern that we have in our history that aligns with the
      # steps we have in self.steps
      for nSteps in self.steps:

        # Do we have the pattern that should be assigned to this classification
        # in our pattern history? If not, skip it
        found = False
        for (iteration, learnPatternNZ) in self._patternNZHistory:
          if iteration == self._learnIteration - nSteps:
            found = True;
            break
        if not found:
          continue

        # Store classification info for each active bit from the pattern
        # that we got nSteps time steps ago.
        for bit in learnPatternNZ:

          # Get the history structure for this bit and step #
          key = (bit, nSteps)
          history = self._activeBitHistory.get(key, None)
          if history is None:
            history = self._activeBitHistory[key] = BitHistory(self,
                                                               bitNum=bit,
                                                               nSteps=nSteps)

          # Store new sample
          history.store(iteration=self._learnIteration,
                        bucketIdx=bucketIdx)

    # ------------------------------------------------------------------------
    # Verbose print
    if infer and self.verbosity >= 1:
      print "  inference: combined bucket likelihoods:"
      print "    actual bucket values:", retval["actualValues"]
      for (nSteps, votes) in retval.items():
        if nSteps == "actualValues":
          continue
        print "    %d steps: " % (nSteps), _pFormatArray(votes)
        bestBucketIdx = votes.argmax()
        print ("      most likely bucket idx: "
               "%d, value: %s" % (bestBucketIdx,
                                  retval["actualValues"][bestBucketIdx]))
      print

    return retval
  
  
  def infer(self, patternNZ, classification):
    """
    Return the inference value from one input sample. The actual 
    learning happens in compute(). The method customCompute() is here to 
    maintain backward compatibility. 

    Parameters:
    --------------------------------------------------------------------
    patternNZ:      list of the active indices from the output below
    classification: dict of the classification information:
                    bucketIdx: index of the encoder bucket
                    actValue:  actual value going into the encoder

    retval:     dict containing inference results, one entry for each step in
                self.steps. The key is the number of steps, the value is an
                array containing the relative likelihood for each bucketIdx
                starting from bucketIdx 0.

                for example:
                  {'actualValues': [0.0, 1.0, 2.0, 3.0]
                    1 : [0.1, 0.3, 0.2, 0.7]
                    4 : [0.2, 0.4, 0.3, 0.5]}
    """
    
    # Return value dict. For buckets which we don't have an actual value
    # for yet, just plug in any valid actual value. It doesn't matter what
    # we use because that bucket won't have non-zero likelihood anyways.

    # NOTE: If doing 0-step prediction, we shouldn't use any knowledge
    #  of the classification input during inference.
    if self.steps[0] == 0:
      defaultValue = 0
    else:
      defaultValue = classification["actValue"]
    actValues = [x if x is not None else defaultValue
                 for x in self._actualValues]
    retval = {"actualValues": actValues}

    # For each n-step prediction...
    for nSteps in self.steps:

      # Accumulate bucket index votes and actValues into these arrays
      sumVotes = numpy.zeros(self._maxBucketIdx + 1)
      bitVotes = numpy.zeros(self._maxBucketIdx + 1)

      # For each active bit, get the votes
      for bit in patternNZ:
        key = (bit, nSteps)
        history = self._activeBitHistory.get(key, None)
        if history is None:
          continue

        bitVotes.fill(0)
        history.infer(votes=bitVotes)

        sumVotes += bitVotes

      # Return the votes for each bucket, normalized
      total = sumVotes.sum()
      if total > 0:
        sumVotes /= total
      else:
        # If all buckets have zero probability then simply make all of the
        # buckets equally likely. There is no actual prediction for this
        # timestep so any of the possible predictions are just as good.
        if sumVotes.size > 0:
          sumVotes = numpy.ones(sumVotes.shape)
          sumVotes /= sumVotes.size

      retval[nSteps] = sumVotes
    
    return retval
    

  def __getstate__(self):
    return self.__dict__


  def __setstate__(self, state):
    if "_profileMemory" in state:
      state.pop("_profileMemory")

    # Set our state
    self.__dict__.update(state)

    # Handle version 0 case (i.e. before versioning code)
    if "_version" not in state or state["_version"] < 2:
      self._recordNumMinusLearnIteration = None

      # Plug in the iteration number in the old patternNZHistory to make it
      #  compatible with the new format
      historyLen = len(self._patternNZHistory)
      for (i, pattern) in enumerate(self._patternNZHistory):
        self._patternNZHistory[i] = (self._learnIteration - (historyLen - i),
                                     pattern)


    elif state["_version"] == 2:
      # Version 2 introduced _recordNumMinusLearnIteration
      pass

    else:
      pass

    self._version = CLAClassifier.__VERSION__


  @classmethod
  def read(cls, proto):
    classifier = object.__new__(cls)

    classifier.steps = []
    for step in proto.steps:
      classifier.steps.append(step)

    classifier.alpha = proto.alpha
    classifier.actValueAlpha = proto.actValueAlpha
    classifier._learnIteration = proto.learnIteration
    classifier._recordNumMinusLearnIteration = (
      proto.recordNumMinusLearnIteration)

    classifier._patternNZHistory = deque(maxlen=max(classifier.steps) + 1)
    patternNZHistoryProto = proto.patternNZHistory
    learnIteration = classifier._learnIteration - len(patternNZHistoryProto) + 1
    for i in xrange(len(patternNZHistoryProto)):
      classifier._patternNZHistory.append((learnIteration,
                                           list(patternNZHistoryProto[i])))
      learnIteration += 1

    classifier._activeBitHistory = dict()
    activeBitHistoryProto = proto.activeBitHistory
    for i in xrange(len(activeBitHistoryProto)):
      stepBitHistories = activeBitHistoryProto[i]
      nSteps = stepBitHistories.steps
      for indexBitHistoryProto in stepBitHistories.bitHistories:
        bit = indexBitHistoryProto.index
        bitHistory = BitHistory.read(indexBitHistoryProto.history)
        classifier._activeBitHistory[(bit, nSteps)] = bitHistory

    classifier._maxBucketIdx = proto.maxBucketIdx

    classifier._actualValues = []
    for actValue in proto.actualValues:
      if actValue == 0:
        classifier._actualValues.append(None)
      else:
        classifier._actualValues.append(actValue)

    classifier._version = proto.version
    classifier.verbosity = proto.verbosity

    return classifier


  def write(self, proto):
    stepsProto = proto.init("steps", len(self.steps))
    for i in xrange(len(self.steps)):
      stepsProto[i] = self.steps[i]

    proto.alpha = self.alpha
    proto.actValueAlpha = self.actValueAlpha
    proto.learnIteration = self._learnIteration
    proto.recordNumMinusLearnIteration = self._recordNumMinusLearnIteration

    patternNZHistory = []
    for (iteration, learnPatternNZ) in self._patternNZHistory:
      patternNZHistory.append(learnPatternNZ)
    proto.patternNZHistory = patternNZHistory

    i = 0
    activeBitHistoryProtos = proto.init("activeBitHistory",
                                        len(self._activeBitHistory))
    if len(self._activeBitHistory) > 0:
      for nSteps in self.steps:
        stepBitHistory = {bit: self._activeBitHistory[(bit, step)]
                          for (bit, step) in self._activeBitHistory.keys()
                          if step == nSteps}
        stepBitHistoryProto = activeBitHistoryProtos[i]
        stepBitHistoryProto.steps = nSteps
        indexBitHistoryListProto = stepBitHistoryProto.init("bitHistories",
                                                            len(stepBitHistory))
        j = 0
        for indexBitHistory in stepBitHistory:
          indexBitHistoryProto = indexBitHistoryListProto[j]
          indexBitHistoryProto.index = indexBitHistory
          bitHistoryProto = indexBitHistoryProto.history
          stepBitHistory[indexBitHistory].write(bitHistoryProto)
          j += 1
        i += 1

    proto.maxBucketIdx = self._maxBucketIdx

    actualValuesProto = proto.init("actualValues", len(self._actualValues))
    for i in xrange(len(self._actualValues)):
      if self._actualValues[i] is not None:
        actualValuesProto[i] = self._actualValues[i]
      else:
        actualValuesProto[i] = 0

    proto.version = self._version
    proto.verbosity = self.verbosity
