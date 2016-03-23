# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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
Implementation for a SDR classifier.

The SDR classifier takes the form of a single layer classification network
that takes SDRs as input and outputs a predicted distribution of classes.
"""

from collections import deque
import itertools

import numpy

g_debugPrefix = "SDRClassifier"


def _pFormatArray(array_, fmt="%.2f"):
  """Return a string with pretty-print of a numpy array using the given format
  for each element"""
  return "[ " + " ".join(fmt % x for x in array_) + " ]"


class SDRClassifier(object):
  """
  The SDR Classifier accepts a binary input pattern from the
  level below (the "activationPattern") and information from the sensor and
  encoders (the "classification") describing the true (target) input.

  The SDR classifier maps input patterns to class labels. There are as many
  output units as the number of class labels (buckets). The output is a
  probabilistic distribution over all class labels

  During inference, the output is calculated by first doing a weighted summation
  of all the inputs, and then perform a softmax nonlinear function to get
  the predicted distribution of class labels

  During learning, the connection weights between input units and output units
  are adjusted to maximize the likelihood of the model

  References:
    Alex Graves. Supervised Sequence Labeling with Recurrent Neural Networks
    PhD Thesis, 2008

    J. S. Bridle. Probabilistic interpretation of feedforward classification
    network outputs, with relationships to statistical pattern recognition.
    In F. Fogleman-Soulie and J.Herault, editors, Neurocomputing: Algorithms,
    Architectures and Applications, pp 227-236, Springer-Verlag, 1990
  """

  __VERSION__ = 1


  def __init__(self,
               steps=(1,),
               alpha=0.001,
               actValueAlpha=0.3,
               verbosity=0):
    """Constructor for the SDR classifier.

    Parameters:
    ---------------------------------------------------------------------
    @param numInputs (int) Length of the input activation pattern
    @param steps (list) Sequence of the different steps of multi-step
        predictions to learn
    @param alpha (float) The alpha used to adapt the weight matrix during
        learning. A lower alpha results in longer term memory.
    @param actValueAlpha (float) Used to track the actual value within each
        bucket. A lower actValueAlpha results in longer term memory
    @param verbosity (int) verbosity level, can be 0, 1, or 2
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

    # This contains the value of the highest input number we've ever seen
    # It is used to pre-allocate fixed size arrays that hold the weights
    self._maxInputIdx = 0

    # This contains the value of the highest bucket index we've ever seen
    # It is used to pre-allocate fixed size arrays that hold the weights of
    # each bucket index during inference
    self._maxBucketIdx = 0

    # The connection weight matrix
    self._weightMatrix = dict()
    for step in self.steps:
      self._weightMatrix[step] = numpy.zeros(shape=(self._maxInputIdx+1,
                                                    self._maxBucketIdx+1))

    # This keeps track of the actual value to use for each bucket index. We
    # start with 1 bucket, no actual value so that the first infer has something
    # to return
    self._actualValues = [None]

    # Set the version to the latest version.
    # This is used for serialization/deserialization
    self._version = SDRClassifier.__VERSION__


  def compute(self, recordNum, patternNZ, classification, learn, infer):
    """
    Process one input sample.
    This method is called by outer loop code outside the nupic-engine. We
    use this instead of the nupic engine compute() because our inputs and
    outputs aren't fixed size vectors of reals.

    Parameters:
    --------------------------------------------------------------------
    @param recordNum  Record number of this input pattern. Record numbers
                normally increase sequentially by 1 each time unless there
                are missing records in the dataset. Knowing this information
                insures that we don't get confused by missing records.
    @param patternNZ  List of the active indices from the output below.
                - When the input is from TemporalMemory, this list should be the
                  indices of the active cells.
    @param classification Dict of the classification information:
                    bucketIdx: index of the encoder bucket
                    actValue:  actual value going into the encoder
    @param learn (bool) if true, learn this sample
    @param infer (bool) if true, perform inference

    @return     Dict containing inference results, there is one entry for each
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

    # Update maxInputIdx and augment weight matrix with zero padding
    if max(patternNZ) > self._maxInputIdx:
      newMaxInputIdx = max(patternNZ)
      for nSteps in self.steps:
        self._weightMatrix[nSteps] = numpy.concatenate((
          self._weightMatrix[nSteps],
          numpy.zeros(shape=(newMaxInputIdx-self._maxInputIdx,
                             self._maxBucketIdx+1))), axis=0)
      self._maxInputIdx = newMaxInputIdx

    # ------------------------------------------------------------------------
    # Inference:
    # For each active bit in the activationPattern, get the classification
    # votes
    if infer:
      retval = self.infer(patternNZ, classification)


    if learn and classification["bucketIdx"] is not None:
      # Get classification info
      bucketIdx = classification["bucketIdx"]
      actValue = classification["actValue"]

      # Update maxBucketIndex and augment weight matrix with zero padding
      if bucketIdx > self._maxBucketIdx:
        for nSteps in self.steps:
          self._weightMatrix[nSteps] = numpy.concatenate((
            self._weightMatrix[nSteps],
            numpy.zeros(shape=(self._maxInputIdx+1,
                               bucketIdx-self._maxBucketIdx))), axis=1)

        self._maxBucketIdx = bucketIdx

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

      for (iteration, learnPatternNZ) in self._patternNZHistory:
        error = self.calculateError(classification)

        nSteps = self._learnIteration - iteration
        if nSteps in self.steps:
          for bit in learnPatternNZ:
            self._weightMatrix[nSteps][bit, :] += self.alpha * error[nSteps]

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
    @param patternNZ  list of the active indices from the output below
    @param classification dict of the classification information:
                    bucketIdx: index of the encoder bucket
                    actValue:  actual value going into the encoder

    @return     dict containing inference results, one entry for each step in
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

    for nSteps in self.steps:
      predictDist = self.inferSingleStep(patternNZ, self._weightMatrix[nSteps])

      retval[nSteps] = predictDist

    return retval


  def inferSingleStep(self, patternNZ, weightMatrix):
    outputActivation = numpy.zeros(self._maxBucketIdx + 1)
    for bit in patternNZ:
      outputActivation += weightMatrix[bit, :]

    # softmax normalization
    expOutputActivation = numpy.exp(outputActivation)
    predictDist = expOutputActivation / numpy.sum(expOutputActivation)
    return predictDist


  def calculateError(self, classification):
    """
    Calculate error signal
    :param classification:
    :return: dict containing error. The key is the number of steps
             The value is a numpy array of error at the output layer
    """
    error = dict()
    targetDist = numpy.zeros(self._maxBucketIdx + 1)
    targetDist[classification["bucketIdx"]] = 1.0

    for (iteration, learnPatternNZ) in self._patternNZHistory:
      nSteps = self._learnIteration - iteration
      if nSteps in self.steps:
        predictDist = self.inferSingleStep(learnPatternNZ,
                                           self._weightMatrix[nSteps])
        error[nSteps] = targetDist - predictDist

    return error

