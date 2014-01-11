# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

import sys
import os
import numpy
import pprint

from inputpredictionstats import IpsDetails

gTrainedNGramState = None
#############################################################################
class NGramStats(object):
  """ This class calculates prediction capability using n-grams
  """

  #########################################################################
  @staticmethod
  def isSupported(netInfo, options, baseline, logNames):
    """ Return true if we support collecting stats in the passed in
    configuration.

    Parameters:
    ------------------------------------------------------------
    netInfo:      trained network info
    options:      object containing all "command-line" options for post-processsing
    baseline:     dictionary of information from the corresponding baseline test set
                    if any, or None
    logNames:     Names of the available log files
    """

    return  ('reset' in logNames) and \
            ('sourceScalars' in logNames) and \
            (options['nGrams'] == 'test' or options['nGrams'] == 'train')



  #########################################################################
  def __init__(self, netInfo, options, baseline, logNames):
    """ Instantiate data structures for calculating the SP stats on a given
    data set.

    Parameters:
    ------------------------------------------------------------
    netInfo:      trained network info
    options:      object containing all "command-line" options for post-processsing
    baseline:     dictionary of information from the corresponding baseline test set
                    if any, or None
    logNames:     Names of the available log files
    """


    # -----------------------------------------------------------------------
    # Get info about the network
    self.netInfo = netInfo
    self.options = options
    self.verbosity = self.options['verbosity']
    #self.verbosity = 3    # Uncomment for verbosity only in this module

    # If testing, make sure we have a trained nGram state
    if self.options['nGrams'] == 'test':
      self.training = False
      global gTrainedNGramState
      if gTrainedNGramState is None:
        print "\nWARNING: You are using the option 'nGrams=test', but haven't " \
              " trained the nGrams using 'nGrams=train' yet. " \
              " No n-gram evaluation will be performed."
      self.trainedStates = gTrainedNGramState
    else:
      self.training = True
      self.trainedStates = dict()


    # -----------------------------------------------------------------------
    # Init variables
    self.sourceFieldNames = self.netInfo['encoder'].getScalarNames()
    self.numFields = len(self.sourceFieldNames)

    # The max value of N we will train and test with
    self.maxN = 4

    # n-grams must show up at lest this number of times or they will be
    #  pruned out of the trained state.
    self.minFreqThreshold = 1

    # Create the queue of the last N elements for each field
    self.elementQueue = dict()
    for fieldName in self.sourceFieldNames:
      self.elementQueue[fieldName] = []



    # ----------------------------------------------------------------------
    # Training specific
    # Create the initial trained state for each field
    if self.training:
      for fieldName in self.sourceFieldNames:
        trainedState = dict()
        for n in range(1, self.maxN+1):
          trainedState['n=%d' % (n)] = dict(keyFreq=dict(), keyPredictions=dict())
        self.trainedStates[fieldName] = trainedState


    # ----------------------------------------------------------------------
    # Testing specific
    else:
      # Asked for IPS details?
      detailsAt = options['ipsDetailsFor']
      if detailsAt is not None:
        (fieldName, detailsAtOffset, maxPathLen) = detailsAt.split(',')
        assert fieldName in self.sourceFieldNames
        self.ipsDetailsAt = dict()
        detailsAtOffset = eval(detailsAtOffset)
        maxPathLen = eval(maxPathLen)

        for n in range(1, self.maxN+1):
          self.ipsDetailsAt['n=%d' % (n)] = IpsDetails(netInfo,
                                fieldName, detailsAtOffset, maxPathLen,
                                clientName="N-gram (n=%d)" % (n))

      else:
        self.ipsDetailsAt = None



    # ----------------------------------------------------------------------
    # Accumulated prediction stats
    # Predicted state on last time step, one for each value of n, starting at
    #  n==0
    self.predictedSourcePrev = numpy.zeros((self.maxN+1, self.numFields))
    self.idxWithinSequence = 0

    # Accumuated closeness scores for each burn-in and for each value of n,
    #  starting at n==0
    self.numSamples = dict()
    self.sourceClosenessSums = dict()
    for burnIn in options['burnIns']:
      self.numSamples[burnIn] = 0
      self.sourceClosenessSums[burnIn] = numpy.zeros((self.maxN+1, self.numFields))


    # Accumuated closeness scores for each 'at' offset and for each value of n,
    #  starting at n==0
    self.numSamplesAt = dict()
    self.sourceClosenessSumsAt = dict()
    for offset in options['ipsAt']:
      self.numSamplesAt[offset] = 0
      self.sourceClosenessSumsAt[offset] = numpy.zeros((self.maxN+1, self.numFields))



  #########################################################################
  def _updateQueue(self, queue, resetOutput, newElement):
    """ Update our queue of the last N elements for each field

    Parameters:
    ----------------------------------------------------------------------
    queue:            Queue (as a list) of the last N elements for this field
    resetOutput:      The reset signal
    newElement:       The input to this field
    """

    if resetOutput:
      while(len(queue) > 0):
        queue.pop(0)
    elif len(queue) > self.maxN:
      queue.pop(0)
    queue.append(newElement)


  #########################################################################
  def _train(self, trainedState, elements, sampleIdx):
    """ Feed in the next data sample and train the n-gram state for
    a field.

    Parameters:
    ------------------------------------------------------------
    trainedState:     The dictionary containing the trained state for this field
    elements:         The last N elements seen for this field
    sampleIdx:        index of this sample. This is used to store the
                        last updated time on each prediction, used for tie-breaking
    """

    # Update the state for each value of N we are processing
    for n in range(1, self.maxN+1):
      state = trainedState['n=%d' % (n)]
      keyFreq = state['keyFreq']
      keyPredictions = state['keyPredictions']

      numPrevElements = len(elements) - 1

      # No update if we don't have n elements preceding this one
      if numPrevElements < n:
        continue

      # Form the key
      prevElements = elements[-n-1:-1]
      key = '_'.join([str(v) for v in prevElements])
      newElement = elements[-1]

      # Add/update the prediction for this key
      if not key in keyFreq:
        keyFreq[key] = 1
        keyPredictions[key] = {newElement:[1,sampleIdx]}
      else:
        keyFreq[key] += 1
        predictions = keyPredictions[key]
        if newElement in predictions:
          predictions[newElement][0] += 1
          predictions[newElement][1] = sampleIdx
        else:
          predictions[newElement] = [1, sampleIdx]


    # All done
    #pprint.pprint(trainedState)
    #import pdb; pdb.set_trace()

  #########################################################################
  def _finishTraining(self, trainedState):
    """ Finish training on this field

    Parameters:
    ------------------------------------------------------------
    trainedState:     The dictionary containing the trained state for this field

    """
    # Finish up the state for each value of N
    for n in range(1, self.maxN+1):
      state = trainedState['n=%d' % (n)]
      keyFreq = state['keyFreq']
      keyPredictions = state['keyPredictions']

      # -------------------------------------------------------------------
      # Remove any ngrams that fall below the frequency threshold
      keys = keyFreq.keys()
      mostFreqKey = None
      mostFreqKeyCount = 0
      for k in keys:
        if keyFreq[k] > mostFreqKeyCount:
          mostFreqKey = k
          mostFreqKeyCount = keyFreq[k]
        if keyFreq[k] < self.minFreqThreshold:
          keyFreq.pop(k)
          keyPredictions.pop(k)
      state['mostFreq'] = mostFreqKey

      # ------------------------------------------------------------------
      # For each ngram, create a list of predictions sorted by frequency
      sortedKeyPredictions = dict()
      for (key, predictions) in keyPredictions.iteritems():
        predFreqPairs = predictions.items()

        # Convert the frequency to a composite of freq+updateIdx/lastUpdateIdx
        #  so that when we have ties, predictions that occurred most recently
        #  will win
        for i in xrange(len(predFreqPairs)):
          subkey = predFreqPairs[i][0]
          (freq, sampleIdx) = predFreqPairs[i][1]
          predFreqPairs[i] = [subkey, freq \
                            + float(sampleIdx)/(self.lastTrainSampleIdx+1)]

        predFreqPairs.sort(key=lambda x: x[1], reverse=True)

        # Convert back to ints
        for i in xrange(len(predFreqPairs)):
          predFreqPairs[i][1] = int(predFreqPairs[i][1])

        sortedKeyPredictions[key] = predFreqPairs

      state['keyPredictions'] = sortedKeyPredictions


    # Verbose print?
    if self.verbosity >= 3:
      print "Trained n-grams:"
      pprint.pprint(trainedState)


  #########################################################################
  def _predict(self, trainedState, elements, maxN):
    """ Return a prediction for the next element for one field

    Parameters:
    ------------------------------------------------------------
    trainedState:     The dictionary containing the trained state for this field
    elements:         The last N elements seen for this field
    maxN:             Only used trained N grams of order <= maxN

    """

    # Special case maxN=0, just return the most common key from the
    #  n=1 trained state.
    if maxN == 0:
      return eval(trainedState['n=1']['mostFreq'])

    # Look for a match against the largest Ns first, working smaller
    numPrevElements = len(elements)
    prediction = None
    for n in range(maxN, 0, -1):
      # Can't use if we don't have n elements preceding this one
      if numPrevElements < n:
        continue

      state = trainedState['n=%d' % (n)]
      keyPredictions = state['keyPredictions']

      # Form the key
      prevElements = elements[-n:]
      key = '_'.join([str(v) for v in prevElements])

      # Found this key?
      if key in keyPredictions:
        prediction = keyPredictions[key][0][0]
        break

    # Verbose printing
    if self.verbosity >= 3:
      if prediction is not None:
        print "Found n-gram match of length %d within %s" % (n,
                  str(elements[-n:]))
        print "Predicted value:", prediction
      else:
        print "No matching n-grams"

    # Return results. If no prediction, just return -1
    if prediction is None:
      prediction = -1
    return prediction


  #########################################################################
  def compute(self, sampleIdx, data):
    """ Feed in the next data sample and accumulate stats on it.

    Parameters:
    ------------------------------------------------------------
    sampleIdx:      The index assigned to this sample
    data:           Logged data for this sample

    """

    # Return quietly if no training available
    if self.trainedStates is None:
      return

    # Get the data we need
    resetOutput = data['reset']
    sensorBUInput = data['sourceScalars']

    # =====================================================================
    # Training
    if self.training:
      # update last training sample idx
      self.lastTrainSampleIdx = sampleIdx
      for fieldName, newElement in zip(self.sourceFieldNames, sensorBUInput):
        self._updateQueue(self.elementQueue[fieldName], resetOutput, newElement)
        #print sampleIdx, self.elementQueue[fieldName]
        self._train(self.trainedStates[fieldName], self.elementQueue[fieldName],
                    sampleIdx)


    # =====================================================================
    # Testing
    else:
      # Update what index we are in within a sequence
      if resetOutput:
        self.idxWithinSequence = 0
      else:
        self.idxWithinSequence += 1

      # ---------------------------------------------------------------------
      # Evaluate prediction accuracy for each n-gram model and each field
      # In here, we will compute sourceCloseness, which is a 2D array:
      #
      #         field0    field1   ....
      #   n=0     X         X
      #   n=1     X         X
      #   ...
      #
      # Compute the closeness scores for each n and each field. Keep in
      #  mind that self.predictedSourcePrev is shaped the same as
      #  sourceCloseness and has the predicted value from each N-gram
      #  model and each field.
      sourceCloseness = numpy.zeros((self.maxN+1, self.numFields))
      for maxN in range(self.maxN+1):
        # Verbose printing
        if self.verbosity >= 2:
          print "ngramPrevPred%d:" % (maxN), \
              self.netInfo['encoder'].scalarsToStr(self.predictedSourcePrev[maxN],
                                                   self.sourceFieldNames)

        # Compute the closeness between the predicted value last iteration and the
        #  actual value this iteration.
        closeness = self.netInfo['encoder'].closenessScores(sensorBUInput,
                                    self.predictedSourcePrev[maxN])
        sourceCloseness[maxN][:] = closeness


        # Compute the IPS details if requested
        if maxN > 0 and self.ipsDetailsAt is not None:
          self.ipsDetailsAt['n=%d' % (maxN)].compute(sampleIdx,
              resetOutput=resetOutput,
              sourceScalars = sensorBUInput,
              predictedSourceScalars = self.predictedSourcePrev[maxN])


      # ---------------------------------------------------------------------
      # Update the sourecCloseness sums for each applicable burn-in, which
      #  depends on how farare we are into the sequence.
      for burnIn in self.options['burnIns']:
        if self.idxWithinSequence < burnIn:
          continue
        self.numSamples[burnIn] += 1
        self.sourceClosenessSums[burnIn] += sourceCloseness


      # ---------------------------------------------------------------------
      # Update the sourecCloseness sums for each 'ipsAt', which
      #  depends on how far are we are into the sequence.
      if self.idxWithinSequence in self.options['ipsAt']:
        self.numSamplesAt[self.idxWithinSequence] += 1
        self.sourceClosenessSumsAt[self.idxWithinSequence] += sourceCloseness


      # ---------------------------------------------------------------------
      # Get the prediction for the next time step for each n-gram model and
      #  field.

      # Update the last N elements for each field
      for fieldName, newElement in zip(self.sourceFieldNames, sensorBUInput):
        self._updateQueue(self.elementQueue[fieldName], resetOutput, newElement)

      # For each n-gram model, calculate the next predicted value for each field
      for maxN in range(self.maxN+1):
        for fieldIdx,fieldName in enumerate(self.sourceFieldNames):
          predValue = self._predict(trainedState=self.trainedStates[fieldName],
                              elements=self.elementQueue[fieldName],
                              maxN=maxN)
          self.predictedSourcePrev[maxN, fieldIdx] = predValue




  #########################################################################
  def getStats(self, stats):
    """ Insert the stats we computed into the passed in 'stats' dict.

    Parameters:
    ------------------------------------------------------------
    stats:      dict in which to place the stats we computed

    """

    # Return quietly if no training state available
    if self.trainedStates is None:
      return

    # ====================================================================
    # Finish up the trained state
    if self.training:
      for fieldName in self.sourceFieldNames:
        self._finishTraining(self.trainedStates[fieldName])

      global gTrainedNGramState
      gTrainedNGramState = self.trainedStates


    # ====================================================================
    # Compute overall prediction score and store stats
    else:
      subStats = dict()

      # ------------------------------------------------------------------
      # For various burn-ins
      for burnIn in self.options['burnIns']:
        numSamples = self.numSamples[burnIn]
        sourceClosenessSums = self.sourceClosenessSums[burnIn]
        burnInLabel = 'burnIn%d' % (burnIn)

        for maxN in range(self.maxN+1):
          fieldScores = sourceClosenessSums[maxN] / max(1.0, numSamples)
          if self.numFields > 1:
            for fieldName, score in zip(self.sourceFieldNames, fieldScores):
              subStats['inputPredScore_%s_n%d_%s' \
                                    % (fieldName, maxN, burnInLabel)] = score
          subStats['inputPredScore_n%d_%s' % (maxN, burnInLabel)] \
                                  = fieldScores.mean()

      # ------------------------------------------------------------------
      # for specific offsets
      for offset in self.options['ipsAt']:
        numSamples = self.numSamplesAt[offset]
        sourceClosenessSums = self.sourceClosenessSumsAt[offset]
        atLabel = 'at%d' % (offset)

        for maxN in range(self.maxN+1):
          fieldScores = sourceClosenessSums[maxN] / max(1.0, numSamples)
          if self.numFields > 1:
            for fieldName, score in zip(self.sourceFieldNames, fieldScores):
              subStats['inputPredScore_%s_n%d_%s' \
                                    % (fieldName, maxN, atLabel)] = score
          subStats['inputPredScore_n%d_%s' % (maxN, atLabel)] \
                                  = fieldScores.mean()


      # -------------------------------------------------------------------
      # Print out IPS details if requested
      if self.ipsDetailsAt is not None:
        for maxN in range(1, self.maxN+1):
          self.ipsDetailsAt['n=%d' % (maxN)].printStats()


      stats['ngram'] = subStats

      #print "numSamples", self.numSamples
      #pprint.pprint(subStats)
      #import pdb; pdb.set_trace()
