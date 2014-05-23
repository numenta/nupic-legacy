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

from nupic.algorithms.KNNClassifier import KNNClassifier


#############################################################################
class ClassificationStats(object):
  """ This class trains a classifier on every unique input it receives
  in compute. It also keeps track of which input samples are unique (by
  sample index) and assigns each category indices to the unique one.

  Every time it sees a new unique input, it also trains a separate classifier
  on the corresponding output, using the same category index assigned to
  the input.

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
            ('sensorBUOut' in logNames) and \
            ('spBUOut' in logNames)


  #########################################################################
  def __init__(self, netInfo, options, baseline, logNames):
    """ Instantiate data structures for training the input and output
    classifiers

    Parameters:
    ------------------------------------------------------------
    netInfo:      trained network info
    options:      object containing all "command-line" options for post-processsing
    baseline:     dictionary of information from the corresponding baseline test set
                    if any, or None
    logNames:     Names of the available log files
    """

    # Save arguments
    self.netInfo = netInfo
    self.options = options

    # Create KNNs
    self.inputCl = KNNClassifier(k=1, distanceNorm=1.0,
                          distThreshold=0.0, useSparseMemory = True)

    self.outputCl = KNNClassifier(k=1, distanceNorm=1.0,
                          distThreshold=0.0, useSparseMemory = True)


    # Init vars
    self.uniqueInput = []
    self.category = []
    self.numSamples = 0


  #########################################################################
  def compute(self, sampleIdx, data):
    """ Learn the next data sample, if it's a unique input

    Parameters:
    ------------------------------------------------------------
    sampleIdx:      The index assigned to this sample
    data:           dictionary of available outputs
    """

    self.numSamples += 1

    # Get the data we need
    resetOutput = data['reset']
    input = data['sensorBUOut'][1]
    output = data['spBUOut'][1]

    # ---------------------------------------------------------------------
    # Save unique samples into the input and SP output classifiers
    if sampleIdx == 0:
      isUniqueInput = True
    else:
      (winner, dist, topNCats) = self.inputCl.getClosest(input, 0)
      isUniqueInput = (dist.min() > 0)


    self.uniqueInput.append(isUniqueInput)

    if isUniqueInput:
      self.inputCl.learn(input, sampleIdx)    # sampleIdx is the category
      self.outputCl.learn(output, sampleIdx)
      self.category.append(sampleIdx)
    else:
      self.category.append(winner)


    # Verbose printing
    if self.options['verbosity'] >= 2:
      print "category: %d, unique: %s" % (self.category[-1], self.uniqueInput[-1])

  #############################################################################
  def _computeDistances(self, stats):
    """ Compute the distances between the SP's input and output representations

    We produce the following stats:

    * The distribution of the distances between SP input representations.
    * The distribution of the distances between SP output representations.
    * The average distance between 2 output representations, plotted vs. distance
       between the 2 input representations.
    * The number of output representations that differ by 1, 2, 3, ... bits.


    Parameters:
    ----------------------------------------------------------
    stats:            Dictionary to store results into

    """


    verbosity = 1 #self.options['verbosity']

    # How many samples in this test set?
    numSamples = len(self.category)

    # How big is the SP output?
    output = self.outputCl.getPattern(0)
    outputSize = len(output)

    # Get the list of categories. We are assuming the category numbers are
    #  all sequential starting at 0....
    categories = self.category[self.uniqueInput]
    numCategories = len(categories)

    print "\nComputing input and output distances using %d unique input patterns..." \
              % (numCategories)

    # ---------------------------------------------------------------------------
    # Let's capture the distribution of distances between the input representations
    #  and between the output representations

    # Accumulate input stats here
    inputDistanceStats = dict(min=numpy.inf, max=0, sum=0, samples=0)

    # Accumulate output stats here
    outputDistanceStats = dict(min=numpy.inf, max=0, sum=0, samples=0)

    # List of category pairs that have identical outputs
    outputCollisions = set()

    # list of output distances seen for each input distance. key: inputDistance,
    #  value: list of output distances seen
    outputVsInputDistance = dict()

    # Max overlap seen for each category, key: category, value: maxOverlap
    maxOverlaps = dict()

    for cat in categories:
      input1 = self.inputCl.getPattern(idx=None, cat=cat)
      output1 = self.outputCl.getPattern(idx=None, cat=cat)
      #netInfo['encoder'].pprint(input1, prefix="%6d:   " % (categories[cat1Idx]))

      # Get the input and output distances
      (inDistances, inCats) = self.inputCl.getDistances(input1)
      (outDistances, outCats) = self.outputCl.getDistances(output1)

      # Record collisions, two output representations which are the same for
      #  two different categories.
      indices = numpy.where(outDistances == 0)[0]
      for index in indices:
        otherCat = outCats[index]
        if otherCat != cat:
          cats = [cat, otherCat]
          cats.sort()
          outputCollisions.add(tuple(cats))

      # Update input distance stats
      assert len(inCats) == len(outCats)
      notUs = (inCats != cat)
      inDistances = inDistances[notUs]
      inputDistanceStats['min'] = min(inputDistanceStats['min'], inDistances.min())
      inputDistanceStats['max'] = max(inputDistanceStats['max'], inDistances.max())
      inputDistanceStats['sum'] += inDistances.sum()
      inputDistanceStats['samples'] += len(inDistances)

      # Update output distance stats
      outDistances = outDistances[notUs]
      outputDistanceStats['min'] = min(outputDistanceStats['min'], outDistances.min())
      outputDistanceStats['max'] = max(outputDistanceStats['max'], outDistances.max())
      outputDistanceStats['sum'] += outDistances.sum()
      outputDistanceStats['samples'] += len(outDistances)


      # Update list of output distance corresponding to each input distance seen
      # assume the input and output classifiers have the same category mappings
      for inDistance in range(int(inDistances.min()), int(inDistances.max())+1):
        indices = numpy.where(inDistances == inDistance)[0]
        if len(indices) == 0:
          continue
        distances = outDistances[indices]
        if inDistance in outputVsInputDistance:
          outputVsInputDistance[inDistance].extend(distances)
        else:
          outputVsInputDistance[inDistance] = list(distances)

      # Record the max overlap seen in the output representations for this category
      (outputOverlaps, cats) = self.outputCl.getOverlaps(output1)
      outputOverlaps = outputOverlaps[notUs]
      maxOverlaps[cat] = outputOverlaps.max()



    # =========================================================================
    # Compute and optionally print the stats on the input distances and output
    #  distances
    stats['inputDistancesMin'] = inputDistanceStats['min']
    stats['inputDistancesMax'] = inputDistanceStats['max']
    stats['inputDistancesAvg'] = float(inputDistanceStats['sum']) \
                                    / inputDistanceStats['samples']
    stats['outputDistancesMin'] = outputDistanceStats['min']
    stats['outputDistancesMax'] = outputDistanceStats['max']
    stats['outputDistancesAvg'] = float(outputDistanceStats['sum']) \
                                    / outputDistanceStats['samples']

    if verbosity >= 1:
      print
      print "input  distances min:", stats['inputDistancesMin'], "max:", \
                stats['inputDistancesMax'], "mean:", stats['inputDistancesAvg']
      print "output distances min:", stats['outputDistancesMin'], "max:", \
                stats['outputDistancesMax'], "mean:", stats['outputDistancesAvg']


    # ---------------------------------------------------------------------------
    # Compute and optionally print the average output distance for each input distance
    numPairingsAtEachDistance = dict()
    for (inputDistance, outputDistances) in outputVsInputDistance.items():
      outputVsInputDistance[inputDistance] = numpy.array(outputDistances).mean()
      numPairingsAtEachDistance[inputDistance] = len(outputDistances)
    if verbosity >= 1:
      totalPairings = numCategories * (numCategories-1)
      inputVsOutput = outputVsInputDistance.items()
      inputVsOutput.sort()
      print
      print "Average output distance vs. input distance:"
      print "numPairings  (%)    inputDist  outputDistAvg"
      print "--------------------------------------------"
      for (inputDistance, avgOutputDistance) in inputVsOutput:
        print "%9d    %4.2f %9d  %9.1f" % (numPairingsAtEachDistance[inputDistance],
                100.0*numPairingsAtEachDistance[inputDistance]/totalPairings,
                inputDistance, avgOutputDistance)
      print


    # ---------------------------------------------------------------------------
    # Compute and optionally print how many output representations overlap with
    #  a maximum of N, where N goes from 1 to maxOverlap seen
    overlaps = numpy.array(maxOverlaps.values())
    maxOverlap = int(overlaps.max())
    if verbosity >= 1:
      print "Overlap Distribution"
      print "overlap     numOutputPatterns  %%(of %d total)" % (numCategories)
      print "------------------------------------------------"
      sumTotal = 0
      for i in xrange(maxOverlap+1, 0, -1):
        whichCats = numpy.where(overlaps == i)[0]
        sumTotal += len(whichCats)
        print ">=%-4d      %-12d       %.1f" % (i, sumTotal,
                                      100.0 * sumTotal / numCategories)
      print

    # ---------------------------------------------------------------------------
    # Print output representations which collide
    if len(outputCollisions) > 0 and verbosity >= 1:
      print "These input pairs produce identical outputs:"
      print "-------------------------------------------"
      self.netInfo['encoder'].pprintHeader(prefix=" " * 7)
      for (cat1, cat2) in outputCollisions:
        input1 = self.inputCl.getPattern(idx=None, cat=cat1)
        input2 = self.inputCl.getPattern(idx=None, cat=cat2)
        output = self.outputCl.getPattern(idx=None, cat=cat1)

        self.netInfo['encoder'].pprint(input1, prefix="%06d:" % cat1)
        self.netInfo['encoder'].pprint(input2, prefix="%06d:" % cat2)
        print "input distance:", numpy.sum(numpy.abs(input1 - input2))
        print "active outputs for both:", output.nonzero()[0]
        print



  #########################################################################
  def getStats(self, stats):
    """ Insert the stats we computed into the passed in 'stats' dict.

    Parameters:
    ------------------------------------------------------------
    stats:      dict in which to place the stats we computed

    """

    # Convert category and uniqueInput to numpy arrays
    self.category = numpy.array(self.category, dtype='int')
    self.uniqueInput = numpy.array(self.uniqueInput, dtype='bool')

    if self.options['computeDistances']:
      self._computeDistances(stats)




#############################################################################
class ClassificationVsBaselineStats(object):
  """ Check classification against a previous baseline test set.
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

    return  baseline is not None and \
            ('sensorBUOut' in logNames) and \
            ('spBUOut' in logNames)


  #########################################################################
  def __init__(self, netInfo, options, baseline, logNames):
    """ Instantiate data structures for training the input and output
    classifiers

    Parameters:
    ------------------------------------------------------------
    netInfo:      trained network info
    options:      object containing all "command-line" options for post-processsing
    baseline:     dictionary of information from the corresponding baseline test set
                    if any, or None
    logNames:     Names of the available log files
    """

    # Save net info
    self.netInfo = netInfo
    self.options = options
    self.trainedClassificationStats = baseline['classificationStats']

    # Init member vars
    self.numSamples = 0
    self.classificationSamples = 0
    self.classificationErrs = 0

    # We use this classifier to detect which input samples are unique. This
    #  way we don't get classification accuracy skewed by multiple instances
    #  of the same input.
    self.inputCl = KNNClassifier(k=1, distanceNorm=1.0,
                          distThreshold=0.0, useSparseMemory = True)


    # This array is used to recored the Temporal Pooler fitness score for each
    #  sample.
    self.tpFitnessScores = []



  #############################################################################
  def _computeTPFitnessScore(self, sampleIdx, spOutput, correctCategory,
            tpActivationThresholds=[8]):
    """ Compute the TP fitness score for an SP output. This is a measure of
    how well a TP could recognize this SP output, in terms of being able to
    identify it as a specific element in one of it's learned sequences.

    We want to see which segments of the TP this SP output could turn on. In the
    ideal case, it would turn on only segments that represent this specific category
    (the category is passed in as an argument). For a TP segment to fire, it must
    have at least N active synapses, were N is the activationThreshold
    of the TP. This function assumes the knn stores all of the valid TP elements,
    labeled with category numbers. The basic idea is to see how many of the knn
    records overlap this spOutput with at least 'activationThreshold' outputs
    (we will say the segment "fires").

    If only 1 TP segment fires, and that segments belongs to the right category,
    then the returned score is 1.0. If no segments are firing, or if none of the
    firing segments are in the right category, then the returned score is 0.0. If
    the correct category segment is present in the list of firing segments, then
    the returned score is 1.0/numSegmentsThatOverlap.

    Parameters:
    ----------------------------------------------------------
    sampleIdx:              The sample index
    spOutput:               The SP output to evaluate
    correctCategory:        The correct category
    tpActivationThresholds: List of TP activation thresholds to evaluate the
                              TP fitness score for.

    retval:                 List of TP fitness scores, one for each activation
                              threshold passed in

    """

    # Get pertinent information
    knn = self.trainedClassificationStats.outputCl
    verbosity = self.options['verbosity']

    # Get all the overlaps
    (overlaps, categories) = knn.getOverlaps(spOutput)
    categories = numpy.array(categories)

    # See if we fired the correct category
    fitnessScores = []
    for threshold in tpActivationThresholds:

      firingSegments = numpy.where(overlaps >= threshold)[0]
      if len(firingSegments) == 0:
        fitnessScore = 0.0

      else:
        # Is the correct category present?
        firingCats = categories[firingSegments]

        if verbosity >= 3:
          print "TPFitnessScore: overlaps with the TP segments of category: ", \
                  firingCats

        if correctCategory in firingCats:
          fitnessScore = 1.0 / len(firingCats)
        else:
          fitnessScore = 0.0

      fitnessScores.append(fitnessScore)

    return fitnessScores

  #########################################################################
  def compute(self, sampleIdx, data):
    """ Test classification accuracy of the next sample

    Parameters:
    ------------------------------------------------------------
    sampleIdx:      The index assigned to this sample
    data:           dictionary of available outputs
    """

    self.numSamples += 1

    # Get the data we need
    input = data['sensorBUOut'][1]
    output = data['spBUOut'][1]

    # ---------------------------------------------------------------------
    # Is this a unique input?
    if sampleIdx == 0:
      isUniqueInput = True
    else:
      (winner, dist, topNCats) = self.inputCl.getClosest(input, 0)
      isUniqueInput = (dist.min() > 0)

    if isUniqueInput:
      self.inputCl.learn(input, sampleIdx)    # sampleIdx is the category


    # Test classification accuracy
    if isUniqueInput:
      correctCategory = self.trainedClassificationStats.category[sampleIdx]
      (inferCat, dist, _) = self.trainedClassificationStats.outputCl.getClosest(
                              output, topKCategories=0)
      self.classificationSamples += 1
      if self.trainedClassificationStats.category[sampleIdx] != inferCat:
        self.classificationErrs += 1

      # The TP fitness score is a measure for how well a TP could do with
      #  this SP output, in terms of being able to identify it as a specific
      #  element within one of it's learned sequences.
      self.tpFitnessScores.append(self._computeTPFitnessScore(sampleIdx, output,
          correctCategory,
          tpActivationThresholds = self.options['tpActivationThresholds']
          ))


      if self.options['verbosity'] >= 2:
        print "Training category: %d" % (correctCategory)
        print "Classifier inference category: %d" % (inferCat)
        print "TP fitness scores: %s" % (self.tpFitnessScores[-1])


  #########################################################################
  def getStats(self, stats):
    """ Insert the stats we computed into the passed in 'stats' dict.

    Parameters:
    ------------------------------------------------------------
    stats:      dict in which to place the stats we computed

    """

    stats['classificationSamples'] = self.classificationSamples
    stats['classificationAccPct'] = 100.0 * \
            (1.0 - float(self.classificationErrs) / self.classificationSamples)
    self.tpFitnessScores = numpy.array(self.tpFitnessScores).mean(axis=0)
    for (threshold, fitness) in zip(self.options['tpActivationThresholds'],
                                    self.tpFitnessScores):
      stats['tpFitnessScore%d' % threshold] = fitness
