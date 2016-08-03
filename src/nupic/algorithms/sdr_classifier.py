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

"""
Implementation of a SDR classifier.

The SDR classifier takes the form of a single layer classification network
that takes SDRs as input and outputs a predicted distribution of classes.
"""

from collections import deque

import numpy



class SDRClassifier(object):
  """
  The SDR Classifier accepts a binary input pattern from the
  level below (the "activationPattern") and information from the sensor and
  encoders (the "classification") describing the true (target) input.

  The SDR classifier maps input patterns to class labels. There are as many
  output units as the number of class labels or buckets (in the case of scalar
  encoders). The output is a probabilistic distribution over all class labels.

  During inference, the output is calculated by first doing a weighted summation
  of all the inputs, and then perform a softmax nonlinear function to get
  the predicted distribution of class labels

  During learning, the connection weights between input units and output units
  are adjusted to maximize the likelihood of the model

  The SDR Classifier is a variation of the previous CLAClassifier which was
  not based on the references below.

  Example Usage:

  c = SDRClassifier(steps=[1], alpha=0.1, actValueAlpha=0.1, verbosity=0)

  # learning
  c.compute(recordNum=0, patternNZ=[1, 5, 9],
            classification={"bucketIdx": 4, "actValue": 34.7},
            learn=True, infer=False)

  # inference
  result = c.compute(recordNum=1, patternNZ=[1, 5, 9],
                     classification={"bucketIdx": 4, "actValue": 34.7},
                     learn=False, infer=True)

  # Print the top three predictions for 1 steps out.
  topPredictions = sorted(zip(result[1],
                          result["actualValues"]), reverse=True)[:3]
  for probability, value in topPredictions:
    print "Prediction of {} has probability of {}.".format(value,
                                                           probability*100.0)

  References:
    Alex Graves. Supervised Sequence Labeling with Recurrent Neural Networks
    PhD Thesis, 2008

    J. S. Bridle. Probabilistic interpretation of feedforward classification
    network outputs, with relationships to statistical pattern recognition.
    In F. Fogleman-Soulie and J.Herault, editors, Neurocomputing: Algorithms,
    Architectures and Applications, pp 227-236, Springer-Verlag, 1990
  """

  VERSION = 1


  def __init__(self,
               steps=(1,),
               alpha=0.001,
               actValueAlpha=0.3,
               verbosity=0):
    """Constructor for the SDR classifier.

    Parameters:
    ---------------------------------------------------------------------
    @param steps (list) Sequence of the different steps of multi-step
        predictions to learn
    @param alpha (float) The alpha used to adapt the weight matrix during
        learning. A larger alpha results in faster adaptation to the data.
    @param actValueAlpha (float) Used to track the actual value within each
        bucket. A lower actValueAlpha results in longer term memory
    @param verbosity (int) verbosity level, can be 0, 1, or 2
    """
    if len(steps) == 0:
      raise TypeError("steps cannot be empty")
    if not all(isinstance(item, int) for item in steps):
      raise TypeError("steps must be a list of ints")
    if any(item < 0 for item in steps):
      raise ValueError("steps must be a list of non-negative ints")

    if alpha < 0:
      raise ValueError("alpha (learning rate) must be a positive number")
    if actValueAlpha < 0 or actValueAlpha >= 1:
      raise ValueError("actValueAlpha be a number between 0 and 1")

    # Save constructor args
    self.steps = steps
    self.alpha = alpha
    self.actValueAlpha = actValueAlpha
    self.verbosity = verbosity

    # Max # of steps of prediction we need to support
    self._maxSteps = max(self.steps) + 1

    # History of the last _maxSteps activation patterns. We need to keep
    # these so that we can associate the current iteration's classification
    # with the activationPattern from N steps ago
    self._patternNZHistory = deque(maxlen=self._maxSteps)

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
    self._version = SDRClassifier.VERSION


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
                    classification could be None for inference mode
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
    if self.verbosity >= 1:
      print "  recordNum:", recordNum
      print "  patternNZ (%d):" % len(patternNZ), patternNZ
      print "  classificationIn:", classification

    # Store pattern in our history
    self._patternNZHistory.append((recordNum, patternNZ))

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
      self._maxInputIdx = int(newMaxInputIdx)

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

        self._maxBucketIdx = int(bucketIdx)

      # Update rolling average of actual values if it's a scalar. If it's
      # not, it must be a category, in which case each bucket only ever
      # sees one category so we don't need a running average.
      while self._maxBucketIdx > len(self._actualValues) - 1:
        self._actualValues.append(None)
      if self._actualValues[bucketIdx] is None:
        self._actualValues[bucketIdx] = actValue
      else:
        if (isinstance(actValue, int) or
              isinstance(actValue, float) or
              isinstance(actValue, long)):
          self._actualValues[bucketIdx] = ((1.0 - self.actValueAlpha)
                                           * self._actualValues[bucketIdx]
                                           + self.actValueAlpha * actValue)
        else:
          self._actualValues[bucketIdx] = actValue

      for (learnRecordNum, learnPatternNZ) in self._patternNZHistory:
        error = self._calculateError(recordNum, classification)

        nSteps = recordNum - learnRecordNum
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
    learning happens in compute().

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
    if self.steps[0] == 0 or classification is None:
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
    """
    Perform inference for a single step. Given an SDR input and a weight
    matrix, return a predicted distribution.

    @param patternNZ  list of the active indices from the output below
    @param weightMatrix numpy array of the weight matrix
    @return numpy array of the predicted class label distribution
    """
    outputActivation = weightMatrix[patternNZ].sum(axis=0)

    # softmax normalization
    expOutputActivation = numpy.exp(outputActivation)
    predictDist = expOutputActivation / numpy.sum(expOutputActivation)
    return predictDist


  @classmethod
  def read(cls, proto):
    classifier = object.__new__(cls)

    classifier.steps = [step for step in proto.steps]

    classifier.alpha = proto.alpha
    classifier.actValueAlpha = proto.actValueAlpha

    classifier._patternNZHistory = deque(maxlen=max(classifier.steps) + 1)

    patternNZHistoryProto = proto.patternNZHistory
    recordNumHistoryProto = proto.recordNumHistory
    for i in xrange(len(patternNZHistoryProto)):
      classifier._patternNZHistory.append((recordNumHistoryProto[i],
                                           list(patternNZHistoryProto[i])))

    classifier._maxSteps = proto.maxSteps

    classifier._maxBucketIdx = proto.maxBucketIdx
    classifier._maxInputIdx = proto.maxInputIdx

    classifier._weightMatrix = {}
    weightMatrixProto = proto.weightMatrix
    for i in xrange(len(weightMatrixProto)):
      classifier._weightMatrix[weightMatrixProto[i].steps] = numpy.reshape(
        weightMatrixProto[i].weight, newshape=(classifier._maxInputIdx+1,
                                               classifier._maxBucketIdx+1))

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

    proto.maxSteps = self._maxSteps

    patternProto = proto.init("patternNZHistory", self._maxSteps)
    recordNumHistoryProto = proto.init("recordNumHistory", self._maxSteps)
    for  i in xrange(self._maxSteps):
      subPatternProto = patternProto.init(i, len(self._patternNZHistory[i][1]))
      for j in xrange(len(self._patternNZHistory[i][1])):
        subPatternProto[j] = int(self._patternNZHistory[i][1][j])
      recordNumHistoryProto[i] = int(self._patternNZHistory[i][0])

    weightMatrices = proto.init("weightMatrix", len(self._weightMatrix))

    i = 0
    for step in self.steps:
      stepWeightMatrixProto = weightMatrices[i]
      stepWeightMatrixProto.steps = step
      stepWeightMatrixProto.weight = list(
        self._weightMatrix[step].flatten().astype(type('float', (float,), {})))
      i += 1

    proto.maxBucketIdx = self._maxBucketIdx
    proto.maxInputIdx = self._maxInputIdx

    actualValuesProto = proto.init("actualValues", len(self._actualValues))
    for i in xrange(len(self._actualValues)):
      if self._actualValues[i] is not None:
        actualValuesProto[i] = self._actualValues[i]
      else:
        actualValuesProto[i] = 0

    proto.version = self._version
    proto.verbosity = self.verbosity


  def _calculateError(self, recordNum, classification):
    """
    Calculate error signal
    @param classification dict of the classification information:
                    bucketIdx: index of the encoder bucket
                    actValue:  actual value going into the encoder
    @return: dict containing error. The key is the number of steps
             The value is a numpy array of error at the output layer
    """
    error = dict()
    targetDist = numpy.zeros(self._maxBucketIdx + 1)
    targetDist[classification["bucketIdx"]] = 1.0

    for (learnRecordNum, learnPatternNZ) in self._patternNZHistory:
      nSteps = recordNum - learnRecordNum
      if nSteps in self.steps:
        predictDist = self.inferSingleStep(learnPatternNZ,
                                           self._weightMatrix[nSteps])
        error[nSteps] = targetDist - predictDist

    return error


def _pFormatArray(array_, fmt="%.2f"):
  """Return a string with pretty-print of a numpy array using the given format
  for each element"""
  return "[ " + " ".join(fmt % x for x in array_) + " ]"

