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

import numpy
from numpy import *
import random
import copy
import itertools

random.seed(42)
numpy.random.seed(42)

from nupic.bindings.math import (SM32, SparseBinaryMatrix)



def setRandomSeed(seed):
  """ Set the random seeds. Helpful to make unit tests repeatable"""
  random.seed(seed)
  numpy.random.seed(seed)



def addNoise(input, noise=0.1, doForeground=True, doBackground=True):
  """
  Add noise to the given input.

  Parameters:
  -----------------------------------------------
  input:         the input to add noise to
  noise:         how much noise to add
  doForeground:  If true, turn off some of the 1 bits in the input
  doBackground:  If true, turn on some of the 0 bits in the input

  """
  if doForeground and doBackground:
    return numpy.abs(input -  (numpy.random.random(input.shape) < noise))
  else:
    if doForeground:
      return numpy.logical_and(input, numpy.random.random(input.shape) > noise)
    if doBackground:
      return numpy.logical_or(input, numpy.random.random(input.shape) < noise)
  return input



def generateCoincMatrix(nCoinc=10, length=500, activity=50):
  """
  Generate a coincidence matrix. This is used to generate random inputs to the
  temporal learner and to compare the predicted output against.

  It generates a matrix of nCoinc rows, each row has length 'length' and has
  a total of 'activity' bits on.

  Parameters:
  -----------------------------------------------
  nCoinc:        the number of rows to generate
  length:        the length of each row
  activity:      the number of ones to put into each row.

  """

  coincMatrix0 = SM32(int(nCoinc), int(length))
  theOnes = numpy.array([1.0] * activity, dtype=numpy.float32)
  for rowIdx in xrange(nCoinc):
    coinc = numpy.array(random.sample(xrange(length),
                activity), dtype=numpy.uint32)
    coinc.sort()
    coincMatrix0.setRowFromSparse(rowIdx, coinc, theOnes)

  # This is the right code to use, it's faster, but it derails the unit
  # testing of the pooling for now.
  coincMatrix = SM32(int(nCoinc), int(length))
  coincMatrix.initializeWithFixedNNZR(activity)

  return coincMatrix0



def generateVectors(numVectors=100, length=500, activity=50):
  """
  Generate a list of random sparse distributed vectors.  This is used to generate
  training vectors to the spatial or temporal learner and to compare the predicted
  output against.

  It generates a list of 'numVectors' elements, each element has length 'length'
  and has a total of 'activity' bits on.

  Parameters:
  -----------------------------------------------
  numVectors:    the number of vectors to generate
  length:        the length of each row
  activity:      the number of ones to put into each row.

  """

  vectors = []
  coinc = numpy.zeros(length, dtype='int32')
  indexList = range(length)

  for i in xrange(numVectors):
      coinc[:] = 0
      coinc[random.sample(indexList, activity)] = 1
      vectors.append(coinc.copy())

  return vectors



def generateSimpleSequences(nCoinc=10, seqLength=[5,6,7], nSeq=100):
  """
  Generate a set of simple sequences. The elements of the sequences will be
  integers from 0 to 'nCoinc'-1. The length of each sequence will be
  randomly chosen from the 'seqLength' list.

  Parameters:
  -----------------------------------------------
  nCoinc:      the number of elements available to use in the sequences
  seqLength:   a list of possible sequence lengths. The length of each
               sequence will be randomly chosen from here.
  nSeq:        The number of sequences to generate

  retval:      a list of sequences. Each sequence is itself a list
               containing the coincidence indices for that sequence.
  """

  coincList = range(nCoinc)
  seqList  = []

  for i in xrange(nSeq):
    if max(seqLength) <= nCoinc:
      seqList.append(random.sample(coincList, random.choice(seqLength)))
    else:
      len = random.choice(seqLength)
      seq = []
      for x in xrange(len):
        seq.append(random.choice(coincList))
      seqList.append(seq)

  return seqList



def generateHubSequences(nCoinc=10, hubs = [2,6], seqLength=[5,6,7], nSeq=100):
  """
  Generate a set of hub sequences. These are sequences which contain a hub
  element in the middle. The elements of the sequences will be integers
  from 0 to 'nCoinc'-1. The hub elements will only appear in the middle of
  each sequence. The length of each sequence will be randomly chosen from the
  'seqLength' list.

  Parameters:
  -----------------------------------------------
  nCoinc:        the number of elements available to use in the sequences
  hubs:          which of the elements will be used as hubs.
  seqLength:     a list of possible sequence lengths. The length of each
                        sequence will be randomly chosen from here.
  nSeq:          The number of sequences to generate

  retval:        a list of sequences. Each sequence is itself a list
                containing the coincidence indices for that sequence.
  """


  coincList = range(nCoinc)
  for hub in hubs:
    coincList.remove(hub)

  seqList = []
  for i in xrange(nSeq):
    length = random.choice(seqLength)-1
    seq = random.sample(coincList,length)
    seq.insert(length//2, random.choice(hubs))
    seqList.append(seq)

  return seqList


def genTestSeqsForLookback(nPatterns=10, patternLen=500, patternActivity=50,
                           seqLength=[5,6,7], nSequences=50):
  """
  Generate two sets of sequences. The first set of sequences is used to train
  the sequence learner till it fills up capacity. The second set is then used
  to further train the system to test its generalization capability using the
  one step look back idea. The second set of sequences are generated by modifying
  the first set

  Parameters:
  -----------------------------------------------
  nPatterns:        the number of patterns to use in the sequences.
  patternLen:       The number of elements in each pattern
  patternActivity:  The number of elements that should be active in
                        each pattern
  seqLength:        a list of possible sequence lengths. The length of each
                        sequence will be randomly chosen from here.
  nSequences: The number of simple sequences in the first set

  retval:           (seqList1, seqList2, patterns)
                    seqList1, seqList2: a list of sequences. Each sequence is itself a list
                                  containing the input pattern indices for that sequence.
                    patterns: the input patterns used in the seqList.
  """
  # Create the input patterns
  patterns = generateCoincMatrix(nCoinc=nPatterns, length=patternLen,
             activity=patternActivity)
  #patterns = generateSimpleCoincMatrix(nCoinc=nPatterns, length=patternLen,
  #           activity=patternActivity)

  similarity = []
  for i in xrange(nPatterns):
     similarity.append(patterns.rightVecProd(patterns.getRow(i)))
  similarity = numpy.array(similarity, dtype='int32')

  print similarity


  # Create the raw sequences
  seqList1 =  generateSimpleSequences(nCoinc=nPatterns, seqLength=seqLength,
                                    nSeq=nSequences)

  #The second set of sequences are obtained by replacing just the first
  #element in each sequence.
  seqList2 = copy.deepcopy(seqList1)
  for i in range(0,len(seqList2)):
    seqList2[i][0] = random.randint(0,nPatterns-1)

  #return ([range(6),[5,4,1,3,4]],[[7,1,2,3,4,5]],patterns)
  return (seqList1, seqList2, patterns)



def generateSimpleCoincMatrix(nCoinc=10, length=500, activity=50):
  """
  Generate a non overlapping coincidence matrix. This is used to generate random
  inputs to the temporal learner and to compare the predicted output against.

  It generates a matrix of nCoinc rows, each row has length 'length' and has
  a total of 'activity' bits on.

  Parameters:
  -----------------------------------------------
  nCoinc:        the number of rows to generate
  length:        the length of each row
  activity:      the number of ones to put into each row.

  """
  assert nCoinc*activity<=length, "can't generate non-overlapping coincidences"
  coincMatrix = SM32(0, length)
  coinc = numpy.zeros(length, dtype='int32')

  for i in xrange(nCoinc):
      coinc[:] = 0
      coinc[i*activity:(i+1)*activity] = 1
      coincMatrix.addRow(coinc)

  return coincMatrix



def generateSequences(nPatterns=10, patternLen=500, patternActivity=50,
                    hubs=[2,6],  seqLength=[5,6,7],
                    nSimpleSequences=50,  nHubSequences=50):
  """
  Generate a set of simple and hub sequences. A simple sequence contains
  a randomly chosen set of elements from 0 to 'nCoinc-1'. A hub sequence
  always contains a hub element in the middle of it.

  Parameters:
  -----------------------------------------------
  nPatterns:        the number of patterns to use in the sequences.
  patternLen:       The number of elements in each pattern
  patternActivity:  The number of elements that should be active in
                        each pattern
  hubs:             which of the elements will be used as hubs.
  seqLength:        a list of possible sequence lengths. The length of each
                        sequence will be randomly chosen from here.
  nSimpleSequences: The number of simple sequences to generate
  nHubSequences:    The number of hub sequences to generate

  retval:           (seqList, patterns)
                    seqList: a list of sequences. Each sequence is itself a list
                                  containing the input pattern indices for that sequence.
                    patterns: the input patterns used in the seqList.
  """

  # Create the input patterns
  patterns = generateCoincMatrix(nCoinc=nPatterns, length=patternLen,
              activity=patternActivity)

  # Create the raw sequences
  seqList =  generateSimpleSequences(nCoinc=nPatterns, seqLength=seqLength,
                                    nSeq=nSimpleSequences) + \
             generateHubSequences(nCoinc=nPatterns, hubs=hubs, seqLength=seqLength,
                                  nSeq=nHubSequences)

  # Return results
  return (seqList, patterns)



def generateL2Sequences(nL1Patterns=10, l1Hubs=[2,6], l1SeqLength=[5,6,7],
                  nL1SimpleSequences=50,  nL1HubSequences=50,
                  l1Pooling=4, perfectStability=False, spHysteresisFactor=1.0,
                  patternLen=500, patternActivity=50):
  """
  Generate the simulated output from a spatial pooler that's sitting
  on top of another spatial pooler / temporal pooler pair.  The average on-time
  of the outputs from the simulated TP is given by the l1Pooling argument.

  In this routine, L1 refers to the first spatial and temporal pooler and L2
  refers to the spatial pooler above that.

  Parameters:
  -----------------------------------------------
  nL1Patterns:          the number of patterns to use in the L1 sequences.
  l1Hubs:               which of the elements will be used as hubs.
  l1SeqLength:          a list of possible sequence lengths. The length of each
                        sequence will be randomly chosen from here.
  nL1SimpleSequences:   The number of simple sequences to generate for L1
  nL1HubSequences:      The number of hub sequences to generate for L1
  l1Pooling:            The number of time steps to pool over in the L1 temporal
                          pooler
  perfectStability:     If true, then the input patterns represented by the
                        sequences generated will have perfect stability over
                        l1Pooling time steps. This is the best case ideal input
                        to a TP. In actual situations, with an actual SP
                        providing input, the stability will always be less than
                        this.
  spHystereisFactor:    The hysteresisFactor to use in the L2 spatial pooler.
                        Only used when perfectStability is  False
  patternLen:           The number of elements in each pattern output by L2
  patternActivity:      The number of elements that should be active in
                        each pattern

  @retval:              (seqList, patterns)
                        seqList: a list of sequences output from L2. Each sequence is
                            itself a list containing the input pattern indices for that
                            sequence.
                        patterns: the input patterns used in the L2 seqList.
  """

  # First, generate the L1 sequences
  l1SeqList = generateSimpleSequences(nCoinc=nL1Patterns, seqLength=l1SeqLength,
                                    nSeq=nL1SimpleSequences) + \
             generateHubSequences(nCoinc=nL1Patterns, hubs=l1Hubs,
                                    seqLength=l1SeqLength, nSeq=nL1HubSequences)

  # Generate the L2 SP output from those
  spOutput = generateSlowSPOutput(seqListBelow = l1SeqList,
                poolingTimeBelow=l1Pooling, outputWidth=patternLen,
                activity=patternActivity, perfectStability=perfectStability,
                spHysteresisFactor=spHysteresisFactor)

  # Map the spOutput patterns into indices into a pattern matrix which we
  #  generate now.
  outSeq = None
  outSeqList = []
  outPatterns = SM32(0, patternLen)
  for pattern in spOutput:
    # If we have a reset vector start a new sequence
    if pattern.sum() == 0:
      if outSeq is not None:
        outSeqList.append(outSeq)
      outSeq = []
      continue

    # See if this vector matches a pattern we've already seen before
    patternIdx = None
    if outPatterns.nRows() > 0:
      # Find most matching 1's.
      matches = outPatterns.rightVecSumAtNZ(pattern)
      outCoinc = matches.argmax().astype('uint32')
      # See if its number of 1's is the same in the pattern and in the
      #  coincidence row. If so, it is an exact match
      numOnes = pattern.sum()
      if matches[outCoinc] == numOnes \
          and outPatterns.getRow(int(outCoinc)).sum() == numOnes:
        patternIdx = outCoinc

    # If no match, add this pattern to our matrix
    if patternIdx is None:
      outPatterns.addRow(pattern)
      patternIdx = outPatterns.nRows() - 1

    # Store the pattern index into the sequence
    outSeq.append(patternIdx)

  # Put in last finished sequence
  if outSeq is not None:
    outSeqList.append(outSeq)

  # Return with the seqList and patterns matrix
  return (outSeqList, outPatterns)



def vectorsFromSeqList(seqList, patternMatrix):
  """
  Convert a list of sequences of pattern indices, and a pattern lookup table
      into a an array of patterns

  Parameters:
  -----------------------------------------------
  seq:            the sequence, given as indices into the patternMatrix
  patternMatrix:  a SparseMatrix contaning the possible patterns used in
                          the sequence.
  """

  totalLen = 0
  for seq in seqList:
    totalLen += len(seq)

  vectors = numpy.zeros((totalLen, patternMatrix.shape[1]), dtype='bool')
  vecOffset = 0
  for seq in seqList:
    seq = numpy.array(seq, dtype='uint32')
    for idx,coinc in enumerate(seq):
      vectors[vecOffset] = patternMatrix.getRow(int(coinc))
      vecOffset += 1

  return vectors

###############################################################################
# The following three functions are used in tests to compare two different
# TP instances.

def sameTPParams(tp1, tp2):
  """Given two TP instances, see if any parameters are different."""
  result = True
  for param in ["numberOfCols", "cellsPerColumn", "initialPerm", "connectedPerm",
                "minThreshold", "newSynapseCount", "permanenceInc", "permanenceDec",
                "permanenceMax", "globalDecay", "activationThreshold",
                "doPooling", "segUpdateValidDuration", "seed",
                "burnIn", "pamLength", "maxAge"]:
    if getattr(tp1, param) != getattr(tp2,param):
      print param,"is different"
      print getattr(tp1, param), "vs", getattr(tp2,param)
      result = False
  return result

def sameSynapse(syn, synapses):
  """Given a synapse and a list of synapses, check whether this synapse
  exist in the list.  A synapse is represented as [col, cell, permanence].
  A synapse matches if col and cell are identical and the permanence value is
  within 0.001."""
  for s in synapses:
    if (s[0]==syn[0]) and (s[1]==syn[1]) and (abs(s[2]-syn[2]) <= 0.001):
      return True
  return False

def sameSegment(seg1, seg2):
  """Return True if seg1 and seg2 are identical, ignoring order of synapses"""
  result = True

  # check sequence segment, total activations etc. In case any are floats,
  # check that they are within 0.001.
  for field in [1, 2, 3, 4, 5, 6]:
    if abs(seg1[0][field] - seg2[0][field]) > 0.001:
      result = False

  # Compare number of synapses
  if len(seg1[1:]) != len(seg2[1:]):
    result = False

  # Now compare synapses, ignoring order of synapses
  for syn in seg2[1:]:
    if syn[2] <= 0:
      print "A synapse with zero permanence encountered"
      result = False
  if result == True:
    for syn in seg1[1:]:
      if syn[2] <= 0:
        print "A synapse with zero permanence encountered"
        result = False
      res = sameSynapse(syn, seg2[1:])
      if res == False:
        result = False

  return result

def tpDiff(tp1, tp2, verbosity = 0, relaxSegmentTests =True):
  """
  Given two TP instances, list the difference between them and returns False
  if there is a difference. This function checks the major parameters. If this
  passes (and checkLearn is true) it checks the number of segments on
  each cell. If this passes, checks each synapse on each segment.
  When comparing C++ and Py, the segments are usually in different orders in the
  cells. tpDiff ignores segment order when comparing TP's.

  """

  # First check basic parameters. If we fail here, don't continue
  if sameTPParams(tp1, tp2) == False:
    print "Two TP's have different parameters"
    return False

  result = True

  # Compare states at t first, they usually diverge before the structure of the
  # cells starts diverging

  if (tp1.activeState['t'] != tp2.activeState['t']).any():
    print 'Active states diverge', numpy.where(tp1.activeState['t'] != tp2.activeState['t'])
    result = False

  if (tp1.predictedState['t'] - tp2.predictedState['t']).any():
    print 'Predicted states diverge', numpy.where(tp1.predictedState['t'] != tp2.predictedState['t'])
    result = False

  # TODO: check confidence at T (confT)

  # Now check some high level learned parameters.
  if tp1.getNumSegments() != tp2.getNumSegments():
    print "Number of segments are different", tp1.getNumSegments(), tp2.getNumSegments()
    result = False

  if tp1.getNumSynapses() != tp2.getNumSynapses():
    print "Number of synapses are different", tp1.getNumSynapses(), tp2.getNumSynapses()
    tp1.printCells()
    tp2.printCells()
    result = False

  # Check that each cell has the same number of segments and synapses
  for c in xrange(tp1.numberOfCols):
    for i in xrange(tp2.cellsPerColumn):
      if tp1.getNumSegmentsInCell(c, i) != tp2.getNumSegmentsInCell(c, i):
        print "Num segments different in cell:",c,i,
        print tp1.getNumSegmentsInCell(c, i), tp2.getNumSegmentsInCell(c, i)
        result = False

  # If the above tests pass, then check each segment and report differences
  # Note that segments in tp1 can be in a different order than tp2. Here we
  # make sure that, for each segment in tp1, there is an identical segment
  # in tp2.
  if result == True and not relaxSegmentTests:
    for c in xrange(tp1.numberOfCols):
      for i in xrange(tp2.cellsPerColumn):
        nSegs = tp1.getNumSegmentsInCell(c, i)
        for segIdx in xrange(nSegs):
          tp1seg = tp1.getSegmentOnCell(c, i, segIdx)

          # Loop through all segments in tp2seg and see if any of them match tp1seg
          res = False
          for tp2segIdx in xrange(nSegs):
            tp2seg = tp2.getSegmentOnCell(c, i, tp2segIdx)
            if sameSegment(tp1seg, tp2seg) == True:
              res = True
              break
          if res == False:
            print "\nSegments are different for cell:",c,i
            if verbosity >= 1:
              print "C++"
              tp1.printCell(c,i)
              print "Py"
              tp2.printCell(c,i)
            result = False

  if result == True and (verbosity > 1):
    print "TP's match"

  return result

def tpDiff2(tp1, tp2, verbosity = 0, relaxSegmentTests =True,
            checkLearn = True, checkStates = True):
  """
  Given two TP instances, list the difference between them and returns False
  if there is a difference. This function checks the major parameters. If this
  passes (and checkLearn is true) it checks the number of segments on each cell.
  If this passes, checks each synapse on each segment.
  When comparing C++ and Py, the segments are usually in different orders in the
  cells. tpDiff ignores segment order when comparing TP's.

  If checkLearn is True, will check learn states as well as all the segments

  If checkStates is True, will check the various state arrays

  """

  # First check basic parameters. If we fail here, don't continue
  if sameTPParams(tp1, tp2) == False:
    print "Two TP's have different parameters"
    return False

  tp1Label = "<tp_1 (%s)>" % tp1.__class__.__name__
  tp2Label = "<tp_2 (%s)>" % tp2.__class__.__name__

  result = True

  if checkStates:
    # Compare states at t first, they usually diverge before the structure of the
    # cells starts diverging

    if (tp1.infActiveState['t'] != tp2.infActiveState['t']).any():
      print 'Active states diverged', numpy.where(tp1.infActiveState['t'] != tp2.infActiveState['t'])
      result = False

    if (tp1.infPredictedState['t'] - tp2.infPredictedState['t']).any():
      print 'Predicted states diverged', numpy.where(tp1.infPredictedState['t'] != tp2.infPredictedState['t'])
      result = False

    if checkLearn and (tp1.lrnActiveState['t'] - tp2.lrnActiveState['t']).any():
      print 'lrnActiveState[t] diverged', numpy.where(tp1.lrnActiveState['t'] != tp2.lrnActiveState['t'])
      result = False

    if checkLearn and (tp1.lrnPredictedState['t'] - tp2.lrnPredictedState['t']).any():
      print 'lrnPredictedState[t] diverged', numpy.where(tp1.lrnPredictedState['t'] != tp2.lrnPredictedState['t'])
      result = False

    if checkLearn and abs(tp1.getAvgLearnedSeqLength() - tp2.getAvgLearnedSeqLength()) > 0.01:
      print "Average learned sequence lengths differ: ",
      print tp1.getAvgLearnedSeqLength()," vs ", tp2.getAvgLearnedSeqLength()
      result = False

  # TODO: check confidence at T (confT)

  # Now check some high level learned parameters.
  if tp1.getNumSegments() != tp2.getNumSegments():
    print "Number of segments are different", tp1.getNumSegments(), tp2.getNumSegments()
    result = False

  if tp1.getNumSynapses() != tp2.getNumSynapses():
    print "Number of synapses are different", tp1.getNumSynapses(), tp2.getNumSynapses()
    if verbosity >= 3:
      print "%s: " % tp1Label,
      tp1.printCells()
      print "\n%s  : " % tp2Label,
      tp2.printCells()
    #result = False

  # Check that each cell has the same number of segments and synapses
  for c in xrange(tp1.numberOfCols):
    for i in xrange(tp2.cellsPerColumn):
      if tp1.getNumSegmentsInCell(c, i) != tp2.getNumSegmentsInCell(c, i):
        print "Num segments different in cell:",c,i,
        print tp1.getNumSegmentsInCell(c, i), tp2.getNumSegmentsInCell(c, i)
        result = False

  # If the above tests pass, then check each segment and report differences
  # Note that segments in tp1 can be in a different order than tp2. Here we
  # make sure that, for each segment in tp1, there is an identical segment
  # in tp2.
  if result == True and not relaxSegmentTests and checkLearn:
    for c in xrange(tp1.numberOfCols):
      for i in xrange(tp2.cellsPerColumn):
        nSegs = tp1.getNumSegmentsInCell(c, i)
        for segIdx in xrange(nSegs):
          tp1seg = tp1.getSegmentOnCell(c, i, segIdx)

          # Loop through all segments in tp2seg and see if any of them match tp1seg
          res = False
          for tp2segIdx in xrange(nSegs):
            tp2seg = tp2.getSegmentOnCell(c, i, tp2segIdx)
            if sameSegment(tp1seg, tp2seg) == True:
              res = True
              break
          if res == False:
            print "\nSegments are different for cell:",c,i
            result = False
            if verbosity >= 0:
              print "%s : " % tp1Label,
              tp1.printCell(c,i)
              print "\n%s  : " % tp2Label,
              tp2.printCell(c,i)

  if result == True and (verbosity > 1):
    print "TP's match"

  return result



def spDiff(SP1,SP2):
    """
    Function that compares two spatial pooler instances. Compares the
    static variables between the two poolers to make sure that they are equivalent.

    Parameters
    -----------------------------------------
    SP1 first spatial pooler to be compared

    SP2 second spatial pooler to be compared

    To establish equality, this function does the following:

    1.Compares the connected synapse matrices for each coincidence

    2.Compare the potential synapse matrices for each coincidence

    3.Compare the permanence matrices for each coincidence

    4.Compare the firing boosts between the two poolers.

    5.Compare the duty cycles before and after inhibition for both poolers

    """
    if(len(SP1._masterConnectedM)!=len(SP2._masterConnectedM)):
        print "Connected synapse matrices are different sizes"
        return False

    if(len(SP1._masterPotentialM)!=len(SP2._masterPotentialM)):
        print "Potential synapse matrices are different sizes"
        return False

    if(len(SP1._masterPermanenceM)!=len(SP2._masterPermanenceM)):
        print "Permanence matrices are different sizes"
        return False


    #iterate over cells
    for i in range(0,len(SP1._masterConnectedM)):
        #grab the Coincidence Matrices and compare them
        connected1 = SP1._masterConnectedM[i]
        connected2 = SP2._masterConnectedM[i]
        if(connected1!=connected2):
            print "Connected Matrices for cell %d different"  % (i)
            return False
        #grab permanence Matrices and compare them
        permanences1 = SP1._masterPermanenceM[i];
        permanences2 = SP2._masterPermanenceM[i];
        if(permanences1!=permanences2):
            print "Permanence Matrices for cell %d different" % (i)
            return False
        #grab the potential connection Matrices and compare them
        potential1 = SP1._masterPotentialM[i];
        potential2 = SP2._masterPotentialM[i];
        if(potential1!=potential2):
            print "Potential Matrices for cell %d different" % (i)
            return False

    #Check firing boosts
    if(not numpy.array_equal(SP1._firingBoostFactors,SP2._firingBoostFactors)):
        print "Firing boost factors are different between spatial poolers"
        return False

    #Check duty cycles after inhibiton
    if(not numpy.array_equal(SP1._dutyCycleAfterInh,SP2._dutyCycleAfterInh)):
        print "Duty cycles after inhibition are different between spatial poolers"
        return False


    #Check duty cycles before inhibition
    if(not numpy.array_equal(SP1._dutyCycleBeforeInh,SP2._dutyCycleBeforeInh)):
        print "Duty cycles before inhibition are different between spatial poolers"
        return False


    print("Spatial Poolers are equivalent")

    return True



def removeSeqStarts(vectors, resets, numSteps=1):
  """
  Convert a list of sequences of pattern indices, and a pattern lookup table
      into a an array of patterns

  Parameters:
  -----------------------------------------------
  vectors:          the data vectors. Row 0 contains the outputs from time
                    step 0, row 1 from time step 1, etc.
  resets:           the reset signal. This is a vector of booleans
                    the same length as the number of rows in 'vectors'. It
                    has a 1 where a sequence started and a 0 otherwise. The
                    first 'numSteps' rows of 'vectors' of each sequence will
                    not be included in the return result.
  numSteps          Number of samples to remove from the start of each sequence

  retval:           copy of vectors, with the first 'numSteps' samples at the
                    start of each sequence removed.
  """

  # Do nothing if numSteps is 0
  if numSteps == 0:
    return vectors

  resetIndices = resets.nonzero()[0]
  removeRows = resetIndices
  for i in range(numSteps-1):
    removeRows = numpy.hstack((removeRows, resetIndices+i+1))

  return numpy.delete(vectors, removeRows, axis=0)



def _accumulateFrequencyCounts(values, freqCounts=None):
  """
  Accumulate a list of values 'values' into the frequency counts 'freqCounts',
  and return the updated frequency counts

  For example, if values contained the following: [1,1,3,5,1,3,5], and the initial
  freqCounts was None, then the return value would be:
  [0,3,0,2,0,2]
  which corresponds to how many of each value we saw in the input, i.e. there
  were 0 0's, 3 1's, 0 2's, 2 3's, 0 4's, and 2 5's.

  If freqCounts is not None, the values will be added to the existing counts and
  the length of the frequency Counts will be automatically extended as necessary

  Parameters:
  -----------------------------------------------
  values:         The values to accumulate into the frequency counts
  freqCounts:     Accumulated frequency counts so far, or none
  """

  # How big does our freqCounts vector need to be?
  values = numpy.array(values)
  numEntries = values.max() + 1
  if freqCounts is not None:
    numEntries = max(numEntries, freqCounts.size)

  # Where do we accumulate the results?
  if freqCounts is not None:
    if freqCounts.size != numEntries:
      newCounts = numpy.zeros(numEntries, dtype='int32')
      newCounts[0:freqCounts.size] = freqCounts
    else:
      newCounts = freqCounts
  else:
    newCounts = numpy.zeros(numEntries, dtype='int32')

  # Accumulate the new values
  for v in values:
    newCounts[v] += 1

  return newCounts



def _listOfOnTimesInVec(vector):
  """
  Returns 3 things for a vector:
    * the total on time
    * the number of runs
    * a list of the durations of each run.

  Parameters:
  -----------------------------------------------
  input stream: 11100000001100000000011111100000
  return value: (11, 3, [3, 2, 6])
  """

  # init counters
  durations = []
  numOnTimes   = 0
  totalOnTime = 0

  # Find where the nonzeros are
  nonzeros = numpy.array(vector).nonzero()[0]

  # Nothing to do if vector is empty
  if len(nonzeros) == 0:
    return (0, 0, [])

  # Special case of only 1 on bit
  if len(nonzeros) == 1:
    return (1, 1, [1])

  # Count the consecutive non-zeros
  prev = nonzeros[0]
  onTime = 1
  endIdx = nonzeros[-1]
  for idx in nonzeros[1:]:
    if idx != prev+1:
      totalOnTime += onTime
      numOnTimes  += 1
      durations.append(onTime)
      onTime       = 1
    else:
      onTime += 1
    prev = idx

  # Add in the last one
  totalOnTime += onTime
  numOnTimes  += 1
  durations.append(onTime)

  return (totalOnTime, numOnTimes, durations)



def _fillInOnTimes(vector, durations):
  """
  Helper function used by averageOnTimePerTimestep. 'durations' is a vector
  which must be the same len as vector. For each "on" in vector, it fills in
  the corresponding element of duration with the duration of that "on" signal
  up until that time

  Parameters:
  -----------------------------------------------
  vector:     vector of output values over time
  durations:  vector same length as 'vector', initialized to 0's.
              This is filled in with the durations of each 'on" signal.

  Example:
  vector:     11100000001100000000011111100000
  durations:  12300000001200000000012345600000
  """

  # Find where the nonzeros are
  nonzeros = numpy.array(vector).nonzero()[0]

  # Nothing to do if vector is empty
  if len(nonzeros) == 0:
    return

  # Special case of only 1 on bit
  if len(nonzeros) == 1:
    durations[nonzeros[0]] = 1
    return

  # Count the consecutive non-zeros
  prev = nonzeros[0]
  onTime = 1
  onStartIdx = prev
  endIdx = nonzeros[-1]
  for idx in nonzeros[1:]:
    if idx != prev+1:
      # Fill in the durations
      durations[onStartIdx:onStartIdx+onTime] = range(1,onTime+1)
      onTime       = 1
      onStartIdx = idx
    else:
      onTime += 1
    prev = idx

  # Fill in the last one
  durations[onStartIdx:onStartIdx+onTime] = range(1,onTime+1)



def averageOnTimePerTimestep(vectors, numSamples=None):
  """
  Computes the average on-time of the outputs that are on at each time step, and
  then averages this over all time steps.

  This metric is resiliant to the number of outputs that are on at each time
  step. That is, if time step 0 has many more outputs on than time step 100, it
  won't skew the results. This is particularly useful when measuring the
  average on-time of things like the temporal pooler output where you might
  have many columns bursting at the start of a sequence - you don't want those
  start of sequence bursts to over-influence the calculated average on-time.

  Parameters:
  -----------------------------------------------
  vectors:          the vectors for which the onTime is calculated. Row 0
                    contains the outputs from time step 0, row 1 from time step
                    1, etc.
  numSamples:       the number of elements for which on-time is calculated.
                    If not specified, then all elements are looked at.

  Returns  (scalar average on-time over all time steps,
            list containing frequency counts of each encountered on-time)

  """


  # Special case given a 1 dimensional vector: it represents a single column
  if vectors.ndim == 1:
    vectors.shape = (-1,1)
  numTimeSteps = len(vectors)
  numElements  = len(vectors[0])

  # How many samples will we look at?
  if numSamples is not None:
    import pdb; pdb.set_trace()   # Test this....
    countOn    = numpy.random.randint(0, numElements, numSamples)
    vectors = vectors[:, countOn]

  # Fill in each non-zero of vectors with the on-time that that output was
  #  on for.
  durations = numpy.zeros(vectors.shape, dtype='int32')
  for col in xrange(vectors.shape[1]):
    _fillInOnTimes(vectors[:,col], durations[:,col])

  # Compute the average on time for each time step
  sums = vectors.sum(axis=1)
  sums.clip(min=1, max=numpy.inf, out=sums)
  avgDurations = durations.sum(axis=1, dtype='float64') / sums
  avgOnTime = avgDurations.sum() / (avgDurations > 0).sum()

  # Generate the frequency counts for each duration
  freqCounts = _accumulateFrequencyCounts(avgDurations)
  return (avgOnTime, freqCounts)



def averageOnTime(vectors, numSamples=None):
  """
  Returns the average on-time, averaged over all on-time runs.

  Parameters:
  -----------------------------------------------
  vectors:          the vectors for which the onTime is calculated. Row 0
                    contains the outputs from time step 0, row 1 from time step
                    1, etc.
  numSamples:       the number of elements for which on-time is calculated.
                    If not specified, then all elements are looked at.

  Returns:    (scalar average on-time of all outputs,
               list containing frequency counts of each encountered on-time)


  """

  # Special case given a 1 dimensional vector: it represents a single column
  if vectors.ndim == 1:
    vectors.shape = (-1,1)
  numTimeSteps = len(vectors)
  numElements  = len(vectors[0])

  # How many samples will we look at?
  if numSamples is None:
    numSamples = numElements
    countOn    = range(numElements)
  else:
    countOn    = numpy.random.randint(0, numElements, numSamples)

  # Compute the on-times and accumulate the frequency counts of each on-time
  #  encountered
  sumOfLengths = 0.0
  onTimeFreqCounts = None
  n = 0
  for i in countOn:
    (onTime, segments, durations) = _listOfOnTimesInVec(vectors[:,i])
    if onTime != 0.0:
      sumOfLengths += onTime
      n += segments
      onTimeFreqCounts = _accumulateFrequencyCounts(durations, onTimeFreqCounts)

  # Return the average on time of each element that was on.
  if n > 0:
    return (sumOfLengths/n, onTimeFreqCounts)
  else:
    return (0.0, onTimeFreqCounts)



def plotOutputsOverTime(vectors, buVectors=None, title='On-times'):
  """
  Generate a figure that shows each output over time. Time goes left to right,
  and each output is plotted on a different line, allowing you to see the overlap
  in the outputs, when they turn on/off, etc.

  Parameters:
  ------------------------------------------------------------
  vectors:            the vectors to plot
  buVectors:          These are normally specified when plotting the pooling
                      outputs of the temporal pooler over time. The 'buVectors'
                      are the sequence outputs and the 'vectors' are the
                      pooling outputs. The buVector (sequence) outputs will be drawn
                      in a darker color than the vector (pooling) outputs to
                      distinguish where the cell is outputting due to pooling vs.
                      sequence memory.
  title:              title for the plot
  avgOnTime:          The average on-time measurement. If not supplied,
                      then it will be calculated from the passed in vectors.

  """

  # Produce the plot
  import pylab
  pylab.ion()
  pylab.figure()
  imData = vectors.transpose()
  if buVectors is not None:
    assert(buVectors.shape == vectors.shape)
    imData = imData.copy()
    imData[buVectors.transpose().astype('bool')] = 2
  pylab.imshow(imData, aspect='auto', cmap=pylab.cm.gray_r,
                interpolation='nearest')

  pylab.title(title)



def plotHistogram(freqCounts, title='On-Times Histogram', xLabel='On-Time'):
  """
  This is usually used to display a histogram of the on-times encountered
  in a particular output.

  The freqCounts is a vector containg the frequency counts of each on-time
  (starting at an on-time of 0 and going to an on-time = len(freqCounts)-1)

  The freqCounts are typically generated from the averageOnTimePerTimestep
  or averageOnTime methods of this module.

  Parameters:
  -----------------------------------------------
  freqCounts:       The frequency counts to plot
  title:            Title of the plot


  """

  import pylab
  pylab.ion()
  pylab.figure()
  pylab.bar(numpy.arange(len(freqCounts)) - 0.5, freqCounts)
  pylab.title(title)
  pylab.xlabel(xLabel)



def populationStability(vectors, numSamples=None):
  """
  Returns the stability for the population averaged over multiple time steps

  Parameters:
  -----------------------------------------------
  vectors:          the vectors for which the stability is calculated
  numSamples        the number of time steps where stability is counted

  At each time step, count the fraction of the active elements which are stable
  from the previous step
  Average all the fraction

  """

  # ----------------------------------------------------------------------
  # Calculate the stability
  numVectors = len(vectors)

  if numSamples is None:
    numSamples = numVectors-1
    countOn = range(numVectors-1)
  else:
    countOn = numpy.random.randint(0, numVectors-1, numSamples)


  sigmap = 0.0
  for i in countOn:
    match = checkMatch(vectors[i], vectors[i+1], sparse=False)
    # Ignore reset vectors (all 0's)
    if match[1] != 0:
      sigmap += float(match[0])/match[1]

  return sigmap / numSamples



def percentOutputsStableOverNTimeSteps(vectors, numSamples=None):
  """
  Returns the percent of the outputs that remain completely stable over
  N time steps.

  Parameters:
  -----------------------------------------------
  vectors:        the vectors for which the stability is calculated
  numSamples:     the number of time steps where stability is counted

  For each window of numSamples, count how many outputs are active during
  the entire window.

  """

  # ----------------------------------------------------------------------
  # Calculate the stability
  totalSamples = len(vectors)
  windowSize = numSamples

  # Process each window
  numWindows = 0
  pctStable = 0

  for wStart in range(0, totalSamples-windowSize+1):
    # Count how many elements are active for the entire time
    data = vectors[wStart:wStart+windowSize]
    outputSums = data.sum(axis=0)
    stableOutputs = (outputSums == windowSize).sum()

    # Accumulated
    samplePctStable = float(stableOutputs) / data[0].sum()
    print samplePctStable
    pctStable += samplePctStable
    numWindows += 1

  # Return percent average over all possible windows
  return float(pctStable) / numWindows



def computeSaturationLevels(outputs, outputsShape, sparseForm=False):
  """
  Compute the saturation for a continuous level. This breaks the level into
  multiple regions and computes the saturation level for each region.

  Parameters:
  --------------------------------------------
  outputs:      output of the level. If sparseForm is True, this is a list of
                  the non-zeros. If sparseForm is False, it is the dense
                  representation
  outputsShape: The shape of the outputs of the level (height, width)
  retval:       (sat, innerSat):
                  sat: list of the saturation levels of each non-empty
                    region of the level (each 0 -> 1.0)
                  innerSat: list of the saturation level of each non-empty region
                       that is not near an edge (each 0 -> 1.0)

  """

  # Get the outputs into a SparseBinaryMatrix
  if not sparseForm:
    outputs = outputs.reshape(outputsShape)
    spOut = SM32(outputs)
  else:
    if len(outputs) > 0:
      assert (outputs.max() < outputsShape[0] * outputsShape[1])
    spOut = SM32(1, outputsShape[0] * outputsShape[1])
    spOut.setRowFromSparse(0, outputs, [1]*len(outputs))
    spOut.reshape(outputsShape[0], outputsShape[1])

  # Get the activity in each local region using the nNonZerosPerBox method
  # This method takes a list of the end row indices and a list of the end
  #  column indices.
  # We will use regions that are 15x15, which give us about a 1/225 (.4%) resolution
  #  on saturation.
  regionSize = 15
  rows = xrange(regionSize+1, outputsShape[0]+1, regionSize)
  cols = xrange(regionSize+1, outputsShape[1]+1, regionSize)
  regionSums = spOut.nNonZerosPerBox(rows, cols)

  # Get all the nonzeros out - those are our saturation sums
  (locations, values) = regionSums.tolist()
  values /= float(regionSize * regionSize)
  sat = list(values)

  # Now, to compute which are the inner regions, we will only take the ones that
  #  are surrounded by activity above, below, left and right
  innerSat = []
  locationSet = set(locations)
  for (location, value) in itertools.izip(locations, values):
    (row, col) = location
    if (row-1,col) in locationSet and (row, col-1) in locationSet \
      and (row+1, col) in locationSet and (row, col+1) in locationSet:
      innerSat.append(value)


  return (sat, innerSat)



def checkMatch(input, prediction, sparse=True, verbosity=0):
  """
  Compares the actual input with the predicted input and returns results

  Parameters:
  -----------------------------------------------
  input:          The actual input
  prediction:     the predicted input
  verbosity:        If > 0, print debugging messages
  sparse:         If true, they are in sparse form (list of
                     active indices)

  retval         (foundInInput, totalActiveInInput, missingFromInput,
                            totalActiveInPrediction)
    foundInInput:       The number of predicted active elements that were
                        found in the actual input
    totalActiveInInput: The total number of active elements in the input.
    missingFromInput:   The number of predicted active elements that were not
                        found in the actual input
    totalActiveInPrediction:  The total number of active elements in the prediction

  """

  if sparse:
    activeElementsInInput = set(input)
    activeElementsInPrediction = set(prediction)

  else:
    activeElementsInInput = set(input.nonzero()[0])
    activeElementsInPrediction = set(prediction.nonzero()[0])

  totalActiveInPrediction = len(activeElementsInPrediction)
  totalActiveInInput     = len(activeElementsInInput)

  foundInInput = len(activeElementsInPrediction.intersection(activeElementsInInput))
  missingFromInput = len(activeElementsInPrediction.difference(activeElementsInInput))
  missingFromPrediction = len(activeElementsInInput.difference(activeElementsInPrediction))

  if verbosity >= 1:
    print "preds. found in input:", foundInInput, "out of", totalActiveInPrediction,
    print "; preds. missing from input:", missingFromInput, "out of", \
              totalActiveInPrediction,
    print "; unexpected active in input:", missingFromPrediction, "out of", \
              totalActiveInInput

  return (foundInInput, totalActiveInInput, missingFromInput,
          totalActiveInPrediction)



def predictionExtent(inputs, resets, outputs, minOverlapPct=100.0):
  """
  Computes the predictive ability of a temporal pooler (TP). This routine returns
  a value which is the average number of time steps of prediction provided
  by the TP. It accepts as input the inputs, outputs, and resets provided to
  the TP as well as a 'minOverlapPct' used to evalulate whether or not a
  prediction is a good enough match to the actual input.

  The 'outputs' are the pooling outputs of the TP. This routine treats each output
  as a "manifold" that includes the active columns that should be present in the
  next N inputs. It then looks at each successive input and sees if it's active
  columns are within the manifold. For each output sample, it computes how
  many time steps it can go forward on the input before the input overlap with
  the manifold is less then 'minOverlapPct'. It returns the average number of
  time steps calculated for each output.

  Parameters:
  -----------------------------------------------
  inputs:          The inputs to the TP. Row 0 contains the inputs from time
                   step 0, row 1 from time step 1, etc.
  resets:          The reset input to the TP. Element 0 contains the reset from
                   time step 0, element 1 from time step 1, etc.
  outputs:         The pooling outputs from the TP. Row 0 contains the outputs
                   from time step 0, row 1 from time step 1, etc.
  minOverlapPct:   How much each input's columns must overlap with the pooling
                   output's columns to be considered a valid prediction.

  retval:          (Average number of time steps of prediction over all output
                     samples,
                    Average number of time steps of prediction when we aren't
                     cut short by the end of the sequence,
                    List containing frequency counts of each encountered
                     prediction time)

  """

  # List of how many times we encountered each prediction amount. Element 0
  #  is how many times we successfully predicted 0 steps in advance, element 1
  #  is how many times we predicted 1 step in advance, etc.
  predCounts = None

  # Total steps of prediction over all samples
  predTotal = 0

  # Total number of samples
  nSamples = len(outputs)

  # Total steps of prediction for samples at the start of the sequence, or
  #  for samples whose prediction runs aren't cut short by the end of the
  #  sequence.
  predTotalNotLimited = 0
  nSamplesNotLimited = 0

  # Compute how many cells/column we have
  nCols = len(inputs[0])
  nCellsPerCol = len(outputs[0]) // nCols

  # Evalulate prediction for each output sample
  for idx in xrange(nSamples):

    # What are the active columns for this output?
    activeCols = outputs[idx].reshape(nCols, nCellsPerCol).max(axis=1)

    # How many steps of prediction do we have?
    steps = 0
    while (idx+steps+1 < nSamples) and (resets[idx+steps+1] == 0):
      overlap = numpy.logical_and(inputs[idx+steps+1], activeCols)
      overlapPct = 100.0 * float(overlap.sum()) / inputs[idx+steps+1].sum()
      if overlapPct >= minOverlapPct:
        steps += 1
      else:
        break

    # print "idx:", idx, "steps:", steps
    # Accumulate into our total
    predCounts = _accumulateFrequencyCounts([steps], predCounts)
    predTotal += steps

    # If this sample was not cut short by the end of the sequence, include
    #  it into the "NotLimited" runs
    if resets[idx] or \
        ((idx+steps+1 < nSamples) and (not resets[idx+steps+1])):
      predTotalNotLimited += steps
      nSamplesNotLimited += 1

  # Return results
  return (float(predTotal) / nSamples,
          float(predTotalNotLimited) / nSamplesNotLimited,
          predCounts)



def getCentreAndSpreadOffsets(spaceShape,
                              spreadShape,
                              stepSize=1):
  """
  Generates centre offsets and spread offsets for block-mode based training
  regimes - star, cross, block.

    Parameters:
    -----------------------------------------------
    spaceShape:   The (height, width) of the 2-D space to explore. This
                  sets the number of center-points.
    spreadShape:  The shape (height, width) of the area around each center-point
                  to explore.
    stepSize:     The step size. How big each step is, in pixels. This controls
                  *both* the spacing of the center-points within the block and the
                  points we explore around each center-point
    retval:       (centreOffsets, spreadOffsets)
  """


  from nupic.math.cross import cross
  # =====================================================================
  # Init data structures
  # What is the range on the X and Y offsets of the center points?
  shape = spaceShape
  # If the shape is (1,1), special case of just 1 center point
  if shape[0] == 1 and shape[1] == 1:
    centerOffsets = [(0,0)]
  else:
    xMin = -1 * (shape[1] // 2)
    xMax = xMin + shape[1] - 1
    xPositions = range(stepSize * xMin, stepSize * xMax + 1, stepSize)

    yMin = -1 * (shape[0] // 2)
    yMax = yMin + shape[0] - 1
    yPositions = range(stepSize * yMin, stepSize * yMax + 1, stepSize)

    centerOffsets = list(cross(yPositions, xPositions))

  numCenterOffsets = len(centerOffsets)
  print "centerOffsets:", centerOffsets

  # What is the range on the X and Y offsets of the spread points?
  shape = spreadShape
  # If the shape is (1,1), special case of no spreading around each center
  #  point
  if shape[0] == 1 and shape[1] == 1:
    spreadOffsets = [(0,0)]
  else:
    xMin = -1 * (shape[1] // 2)
    xMax = xMin + shape[1] - 1
    xPositions = range(stepSize * xMin, stepSize * xMax + 1, stepSize)

    yMin = -1 * (shape[0] // 2)
    yMax = yMin + shape[0] - 1
    yPositions = range(stepSize * yMin, stepSize * yMax + 1, stepSize)

    spreadOffsets = list(cross(yPositions, xPositions))

    # Put the (0,0) entry first
    spreadOffsets.remove((0,0))
    spreadOffsets.insert(0, (0,0))

  numSpreadOffsets = len(spreadOffsets)
  print "spreadOffsets:", spreadOffsets

  return centerOffsets, spreadOffsets



def makeCloneMap(columnsShape, outputCloningWidth, outputCloningHeight=-1):
  """Make a two-dimensional clone map mapping columns to clone master.

  This makes a map that is (numColumnsHigh, numColumnsWide) big that can
  be used to figure out which clone master to use for each column.  Here are
  a few sample calls

  >>> makeCloneMap(columnsShape=(10, 6), outputCloningWidth=4)
  (array([[ 0,  1,  2,  3,  0,  1],
         [ 4,  5,  6,  7,  4,  5],
         [ 8,  9, 10, 11,  8,  9],
         [12, 13, 14, 15, 12, 13],
         [ 0,  1,  2,  3,  0,  1],
         [ 4,  5,  6,  7,  4,  5],
         [ 8,  9, 10, 11,  8,  9],
         [12, 13, 14, 15, 12, 13],
         [ 0,  1,  2,  3,  0,  1],
         [ 4,  5,  6,  7,  4,  5]], dtype=uint32), 16)

  >>> makeCloneMap(columnsShape=(7, 8), outputCloningWidth=3)
  (array([[0, 1, 2, 0, 1, 2, 0, 1],
         [3, 4, 5, 3, 4, 5, 3, 4],
         [6, 7, 8, 6, 7, 8, 6, 7],
         [0, 1, 2, 0, 1, 2, 0, 1],
         [3, 4, 5, 3, 4, 5, 3, 4],
         [6, 7, 8, 6, 7, 8, 6, 7],
         [0, 1, 2, 0, 1, 2, 0, 1]], dtype=uint32), 9)

  >>> makeCloneMap(columnsShape=(7, 11), outputCloningWidth=5)
  (array([[ 0,  1,  2,  3,  4,  0,  1,  2,  3,  4,  0],
         [ 5,  6,  7,  8,  9,  5,  6,  7,  8,  9,  5],
         [10, 11, 12, 13, 14, 10, 11, 12, 13, 14, 10],
         [15, 16, 17, 18, 19, 15, 16, 17, 18, 19, 15],
         [20, 21, 22, 23, 24, 20, 21, 22, 23, 24, 20],
         [ 0,  1,  2,  3,  4,  0,  1,  2,  3,  4,  0],
         [ 5,  6,  7,  8,  9,  5,  6,  7,  8,  9,  5]], dtype=uint32), 25)

  >>> makeCloneMap(columnsShape=(7, 8), outputCloningWidth=3, outputCloningHeight=4)
  (array([[ 0,  1,  2,  0,  1,  2,  0,  1],
         [ 3,  4,  5,  3,  4,  5,  3,  4],
         [ 6,  7,  8,  6,  7,  8,  6,  7],
         [ 9, 10, 11,  9, 10, 11,  9, 10],
         [ 0,  1,  2,  0,  1,  2,  0,  1],
         [ 3,  4,  5,  3,  4,  5,  3,  4],
         [ 6,  7,  8,  6,  7,  8,  6,  7]], dtype=uint32), 12)

  The basic idea with this map is that, if you imagine things stretching off
  to infinity, every instance of a given clone master is seeing the exact
  same thing in all directions.  That includes:
  - All neighbors must be the same
  - The "meaning" of the input to each of the instances of the same clone
    master must be the same.  If input is pixels and we have translation
    invariance--this is easy.  At higher levels where input is the output
    of lower levels, this can be much harder.
  - The "meaning" of the inputs to neighbors of a clone master must be the
    same for each instance of the same clone master.


  The best way to think of this might be in terms of 'inputCloningWidth' and
  'outputCloningWidth'.
  - The 'outputCloningWidth' is the number of columns you'd have to move
    horizontally (or vertically) before you get back to the same the same
    clone that you started with.  MUST BE INTEGRAL!
  - The 'inputCloningWidth' is the 'outputCloningWidth' of the node below us.
    If we're getting input from an sensor where every element just represents
    a shift of every other element, this is 1.
    At a conceptual level, it means that if two different inputs are shown
    to the node and the only difference between them is that one is shifted
    horizontally (or vertically) by this many pixels, it means we are looking
    at the exact same real world input, but shifted by some number of pixels
    (doesn't have to be 1).  MUST BE INTEGRAL!

  At level 1, I think you could have this:
  * inputCloningWidth = 1
  * sqrt(coincToInputRatio^2) = 2.5
  * outputCloningWidth = 5
  ...in this case, you'd end up with 25 masters.


  Let's think about this case:
    input:    - - -  0     1     2     3     4     5     -     -   - - -
    columns:        0 1  2 3 4  0 1  2 3 4  0 1  2 3 4  0 1  2 3 4

  ...in other words, input 0 is fed to both column 0 and column 1.  Input 1
  is fed to columns 2, 3, and 4, etc.  Hopefully, you can see that you'll
  get the exact same output (except shifted) with:
    input:    - - -  -     -     0     1     2     3     4     5   - - -
    columns:        0 1  2 3 4  0 1  2 3 4  0 1  2 3 4  0 1  2 3 4

  ...in other words, we've shifted the input 2 spaces and the output shifted
  5 spaces.


  *** The outputCloningWidth MUST ALWAYS be an integral multiple of the ***
  *** inputCloningWidth in order for all of our rules to apply.         ***
  *** NOTE: inputCloningWidth isn't passed here, so it's the caller's   ***
  ***       responsibility to ensure that this is true.                ***

  *** The outputCloningWidth MUST ALWAYS be an integral multiple of     ***
  *** sqrt(coincToInputRatio^2), too.                                  ***

  @param  columnsShape         The shape (height, width) of the columns.
  @param  outputCloningWidth   See docstring above.
  @param  outputCloningHeight  If non-negative, can be used to make
                               rectangular (instead of square) cloning fields.
  @return cloneMap             An array (numColumnsHigh, numColumnsWide) that
                               contains the clone index to use for each
                               column.
  @return numDistinctClones    The number of distinct clones in the map.  This
                               is just outputCloningWidth*outputCloningHeight.
  """
  if outputCloningHeight < 0:
    outputCloningHeight = outputCloningWidth

  columnsHeight, columnsWidth = columnsShape

  numDistinctMasters = outputCloningWidth * outputCloningHeight

  a = numpy.empty((columnsHeight, columnsWidth), 'uint32')
  for row in xrange(columnsHeight):
    for col in xrange(columnsWidth):
      a[row, col] = (col % outputCloningWidth) + \
                    (row % outputCloningHeight) * outputCloningWidth

  return a, numDistinctMasters



def numpyStr(array, format='%f', includeIndices=False, includeZeros=True):
  """ Pretty print a numpy matrix using the given format string for each
  value. Return the string representation

  Parameters:
  ------------------------------------------------------------
  array:    The numpy array to print. This can be either a 1D vector or 2D matrix
  format:   The format string to use for each value
  includeIndices: If true, include [row,col] label for each value
  includeZeros:   Can only be set to False if includeIndices is on.
                  If True, include 0 values in the print-out
                  If False, exclude 0 values from the print-out.


  """

  shape = array.shape
  assert (len(shape) <= 2)
  items = ['[']
  if len(shape) == 1:
    if includeIndices:
      format = '%d:' + format
      if includeZeros:
        rowItems = [format % (c,x) for (c,x) in enumerate(array)]
      else:
        rowItems = [format % (c,x) for (c,x) in enumerate(array) if x != 0]
    else:
      rowItems = [format % (x) for x in array]
    items.extend(rowItems)

  else:
    (rows, cols) = shape
    if includeIndices:
      format = '%d,%d:' + format

    for r in xrange(rows):
      if includeIndices:
        rowItems = [format % (r,c,x) for c,x in enumerate(array[r])]
      else:
        rowItems = [format % (x) for x in array[r]]
      if r > 0:
        items.append('')

      items.append('[')
      items.extend(rowItems)
      if r < rows-1:
        items.append(']\n')
      else:
        items.append(']')


  items.append(']')
  return ' '.join(items)



if __name__=='__main__':

  testStability(numOrigVectors=10, length=500, activity=50,morphTime=3)

  from IPython.Shell import IPShellEmbed; IPShellEmbed()()
