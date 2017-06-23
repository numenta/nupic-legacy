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
This file performs a variety of tests on the reference temporal memory code.

basic_test
==========

Tests creation and serialization of the TM class. Sets parameters and ensures
they are the same after a serialization and de-serialization step. Runs learning
and inference on a small number of random patterns and ensures it doesn't crash.

===============================================================================
                Basic First Order Sequences
===============================================================================

These tests ensure the most basic (first order) sequence learning mechanism is
working.

Parameters: Use a "fast learning mode": turn off global decay, temporal pooling
and hilo (make minThreshold really high). initPerm should be greater than
connectedPerm and permanenceDec should be zero. With these settings sequences
should be learned in one pass:

  minThreshold = newSynapseCount
  globalDecay = 0
  temporalPooling = False
  initialPerm = 0.8
  connectedPerm = 0.7
  permanenceDec = 0
  permanenceInc = 0.4

Other Parameters:
  numCols = 100
  cellsPerCol = 1
  newSynapseCount=11
  activationThreshold = 8
  permanenceMax = 1

Note: this is not a high order sequence, so one cell per column is fine.


Input Sequence: We train with M input sequences, each consisting of N random
patterns. Each pattern consists of a random number of bits on. The number of 1's
in each pattern should be between 21 and 25 columns. The sequences are
constructed so that consecutive patterns within a sequence don't share any
columns.

Training: The TM is trained with P passes of the M sequences. There
should be a reset between sequences. The total number of iterations during
training is P*N*M.

Testing: Run inference through the same set of sequences, with a reset before
each sequence. For each sequence the system should accurately predict the
pattern at the next time step up to and including the N-1'st pattern. A perfect
prediction consists of getting every column correct in the prediction, with no
extra columns. We report the number of columns that are incorrect and report a
failure if more than 2 columns are incorrectly predicted.

We can also calculate the number of segments and synapses that should be
learned. We raise an error if too many or too few were learned.

B1) Basic sequence learner.  M=1, N=100, P=1.

B2) Same as above, except P=2. Test that permanences go up and that no
additional synapses or segments are learned.

B3) N=300, M=1, P=1.  (See how high we can go with M)

B4) N=100, M=3, P=1   (See how high we can go with N*M)

B5) Like B1) but only have newSynapseCount columns ON in each pattern (instead
of between 21 and 25), and set activationThreshold to newSynapseCount.

B6) Like B1 but with cellsPerCol = 4. First order sequences should still work
just fine.

B7) Like B1 but with slower learning. Set the following parameters differently:

    activationThreshold = newSynapseCount
    minThreshold = activationThreshold
    initialPerm = 0.2
    connectedPerm = 0.7
    permanenceInc = 0.2

Now we train the TM with the B1 sequence 4 times (P=4). This will increment
the permanences to be above 0.8 and at that point the inference will be correct.
This test will ensure the basic match function and segment activation rules are
working correctly.

B8) Like B7 but with 4 cells per column. Should still work.

B9) Like B7 but present the sequence less than 4 times: the inference should be
incorrect.

B10) Like B2, except that cells per column = 4. Should still add zero additional
synapses.


===============================================================================
                High Order Sequences
===============================================================================

These tests ensure that high order sequences can be learned in a multiple cells
per column instantiation.

Parameters: Same as Basic First Order Tests above, but with varying cells per
column.

Input Sequence: We train with M input sequences, each consisting of N random
patterns. Each pattern consists of a random number of bits on. The number of 1's
in each pattern should be between 21 and 25 columns (except for H0). The
sequences are constructed so that consecutive patterns within a sequence don't
share any columns. The sequences are constructed to contain shared subsequences,
such as:

A B C D E F G H I J
K L M D E F N O P Q

The position and length of shared subsequences are parameters in the tests.

Training: Identical to basic first order tests above.

Testing: Identical to basic first order tests above unless noted.

We can also calculate the number of segments and synapses that should be
learned. We raise an error if too many or too few were learned.

H0) Two simple high order sequences, each of length 7, with a shared
subsequence in positions 2-4.  Each pattern has a consecutive set of 5 bits on.
No pattern shares any columns with the others. These sequences are easy to
visualize and is very useful for debugging.

H1) Learn two sequences with a short shared pattern. Parameters
should be the same as B1. This test will FAIL since cellsPerCol == 1. No
consecutive patterns share any column.

H2) As above but with cellsPerCol == 4. This test should PASS. No consecutive
patterns share any column.

H2a) Same as above, except P=2. Test that permanences go up and that no
additional synapses or segments are learned.

H3) Same parameters as H.2 except sequences are created such that they share a
single significant sub-sequence. Subsequences should be reasonably long and in
the middle of sequences. No consecutive patterns share any column.

H4) Like H.3, except the shared subsequence is in the beginning. (e.g.
"ABCDEF" and "ABCGHIJ". At the point where the shared subsequence ends, all
possible next patterns should be predicted. As soon as you see the first unique
pattern, the predictions should collapse to be a perfect prediction.

H5) Shared patterns. Similar to H3 except that patterns are shared between
sequences.  All sequences are different shufflings of the same set of N
patterns (there is no shared subsequence). Care should be taken such that the
same three patterns never follow one another in two sequences.

H6) Combination of H5) and H3). Shared patterns in different sequences, with a
shared subsequence.

H7) Stress test: every other pattern is shared. [Unimplemented]

H8) Start predicting in the middle of a sequence. [Unimplemented]

H9) Hub capacity. How many patterns can use that hub?
[Implemented, but does not run by default.]

H10) Sensitivity to small amounts of noise during inference. [Unimplemented]

H11) Higher order patterns with alternating elements.

Create the following 4 sequences:

     A B A B A C
     A B A B D E
     A B F G H I
     A J K L M N

After training we should verify that the expected transitions are in the
model. Prediction accuracy should be perfect. In addition, during inference,
after the first element is presented, the columns should not burst any more.
Need to verify, for the first sequence, that the high order representation
when presented with the second A and B is different from the representation
in the first presentation.


===============================================================================
                Temporal Pooling Tests [UNIMPLEMENTED]
===============================================================================

Parameters: Use a "fast learning mode": With these settings sequences should be
learned in one pass:

  minThreshold = newSynapseCount
  globalDecay = 0
  initialPerm = 0.8
  connectedPerm = 0.7
  permanenceDec = 0
  permanenceInc = 0.4

Other Parameters:
  cellsPerCol = 4
  newSynapseCount=11
  activationThreshold = 11
  permanenceMax = 1
  doPooling = True

Input Sequence: We train with M input sequences, each consisting of N random
patterns. Each pattern consists of a random number of bits on. The number of 1's
in each pattern should be between 17 and 21 columns. The sequences are
constructed so that consecutive patterns within a sequence don't share any
columns.

Note: for pooling tests the density of input patterns should be pretty low
since each pooling step increases the output density. At the same time, we need
enough bits on in the input for the temporal memory to find enough synapses. So,
for the tests, constraints should be something like:

(Input Density) * (Number of pooling steps) < 25 %.
          AND
sum(Input) > newSynapseCount*1.5

Training: The TM is trained with P passes of the M sequences. There
should be a reset between sequences. The total number of iterations during
training is P*N*M.

Testing: Run inference through the same set of sequences, with a reset before
each sequence. For each sequence the system should accurately predict the
pattern at the next P time steps, up to and including the N-P'th pattern. A
perfect prediction consists of getting every column correct in the prediction,
with no extra columns. We report the number of columns that are incorrect and
report a failure if more than 2 columns are incorrectly predicted.

P1) Train the TM two times (P=2) on a single long sequence consisting of random
patterns (N=20, M=1). There should be no overlapping columns between successive
patterns. During inference, the TM should be able reliably predict the pattern
two time steps in advance. numCols should be about 350 to meet the above
constraints and also to maintain consistency with test P2.

P2) Increase TM rate to 3 time steps in advance (P=3). At each step during
inference, the TM should be able to reliably predict the pattern coming up at
t+1, t+2, and t+3..

P3) Set segUpdateValidDuration to 2 and set P=3. This should behave almost
identically to P1. It should only predict the next time step correctly and not
two time steps in advance. (Check off by one error in this logic.)

P4) As above, but with multiple sequences.

P5) Same as P3 but with shared subsequences.



Continuous mode tests
=====================

Slow changing inputs.


Orphan Decay Tests
==================


HiLo Tests
==========

A high order sequence memory like the TM can memorize very long sequences. In
many applications though you don't want to memorize. You see a long sequence of
patterns but there are actually lower order repeating sequences embedded within
it.  A simplistic example is words in a sentence. Words such as You'd like the
TM to learn those sequences.

Tests should capture number of synapses learned and compare against
theoretically optimal numbers to pass/fail.

HL0a) For debugging, similar to H0. We want to learn a 3 pattern long sequence
presented with noise before and after, with no resets. Two steps of noise will
be presented.
The noise will be 20 patterns, presented in random order. Every pattern has a
consecutive set of 5 bits on, so the vector will be 115 bits long. No pattern
shares any columns with the others. These sequences are easy to visualize and is
very useful for debugging.

TM parameters should be the same as B7 except that permanenceDec should be 0.05:

    activationThreshold = newSynapseCount
    minThreshold = activationThreshold
    initialPerm = 0.2
    connectedPerm = 0.7
    permanenceInc = 0.2
    permanenceDec = 0.05

So, this means it should learn a sequence after 4 repetitions. It will take
4 orphan decay steps to get an incorrect synapse to go away completely.

HL0b) Like HL0a, but after the 3-sequence is learned, try to learn a 4-sequence
that builds on the 3-sequence. For example, if learning A-B-C we train also on
D-A-B-C. It should learn that ABC is separate from DABC.  Note: currently this
test is disabled in the code. It is a bit tricky to test this. When you present
DAB, you should predict the same columns as when you present AB (i.e. in both
cases C should be predicted). However, the representation for C in DABC should
be different than the representation for C in ABC. Furthermore, when you present
AB, the representation for C should be an OR of the representation in DABC and
ABC since you could also be starting in the middle of the DABC sequence. All
this is actually happening in the code, but verified by visual inspection only.

HL1) Noise + sequence + noise + sequence repeatedly without resets until it has
learned that sequence. Train the TM repeatedly with N random sequences that all
share a single subsequence. Each random sequence can be 10 patterns long,
sharing a subsequence that is 5 patterns long. There should be no resets
between presentations.  Inference should then be on that 5 long shared
subsequence.

Example (3-long shared subsequence):

A B C D E F G H I J
K L M D E F N O P Q
R S T D E F U V W X
Y Z 1 D E F 2 3 4 5

TM parameters should be the same as HL0.

HL2) Like HL1, but after A B C has learned, try to learn D A B C . It should
learn ABC is separate from DABC.

HL3) Like HL2, but test with resets.

HL4) Like HL1 but with minThreshold high. This should FAIL and learn a ton
of synapses.

HiLo but with true high order sequences embedded in noise

Present 25 sequences in random order with no resets but noise between
sequences (1-20 samples). Learn all 25 sequences. Test global decay vs non-zero
permanenceDec .

Pooling + HiLo Tests [UNIMPLEMENTED]
====================

Needs to be defined.


Global Decay Tests [UNIMPLEMENTED]
==================

Simple tests to ensure global decay is actually working.


Sequence Likelihood Tests
=========================

These tests are in the file TMLikelihood.py


Segment Learning Tests [UNIMPLEMENTED]
======================

Multi-attribute sequence tests.

SL1) Train the TM repeatedly using a single (multiple) sequence plus noise. The
sequence can be relatively short, say 20 patterns. No two consecutive patterns
in the sequence should share columns. Add random noise each time a pattern is
presented. The noise should be different for each presentation and can be equal
to the number of on bits in the pattern. After N iterations of the noisy
sequences, the TM should should achieve perfect inference on the true sequence.
There should be resets between each presentation of the sequence.

Check predictions in the sequence only. And test with clean sequences.

Vary percentage of bits that are signal vs noise.

Noise can be a fixed alphabet instead of being randomly generated.

HL2) As above, but with no resets.

Shared Column Tests [UNIMPLEMENTED]
===================

Carefully test what happens when consecutive patterns in a sequence share
columns.

Sequence Noise Tests [UNIMPLEMENTED]
====================

Note: I don't think these will work with the current logic. Need to discuss
whether we want to accommodate sequence noise like this.

SN1) Learn sequence with pooling up to T timesteps. Run inference on a sequence
and occasionally drop elements of a sequence. Inference should still work.

SN2) As above, but occasionally add a random pattern into a sequence.

SN3) A combination of the above two.


Capacity Tests [UNIMPLEMENTED]
==============

These are stress tests that verify that the temporal memory can learn a large
number of sequences and can predict a large number of possible next steps. Some
research needs to be done first to understand the capacity of the system as it
relates to the number of columns, cells per column, etc.

Token Prediction Tests: Test how many predictions of individual tokens we can
superimpose and still recover.


Online Learning Tests [UNIMPLEMENTED]
=====================

These tests will verify that the temporal memory continues to work even if
sequence statistics (and the actual sequences) change slowly over time. The TM
should adapt to the changes and learn to recognize newer sequences (and forget
the older sequences?).



"""

import numpy
import pprint
import random
import sys
from numpy import *

from nupic.algorithms import fdrutilities as fdrutils
from nupic.algorithms.backtracking_tm import BacktrackingTM
from nupic.algorithms.backtracking_tm_cpp import BacktrackingTMCPP

#-------------------------------------------------------------------------------
TEST_CPP_TM = 1   # temporarily disabled until it can be updated
VERBOSITY = 0 # how chatty the unit tests should be
SEED = 33     # the random seed used throughout
TMClass = BacktrackingTM
checkSynapseConsistency = False

rgen = numpy.random.RandomState(SEED) # always call this rgen, NOT random

#-------------------------------------------------------------------------------
# Helper routines
#-------------------------------------------------------------------------------


def printOneTrainingVector(x):

    print ''.join('1' if k != 0 else '.' for k in x)


def printAllTrainingSequences(trainingSequences, upTo = 99999):

    for t in xrange(min(len(trainingSequences[0]), upTo)):
        print 't=',t,
        for i,trainingSequence in enumerate(trainingSequences):
            print "\tseq#",i,'\t',
            printOneTrainingVector(trainingSequences[i][t])


def generatePattern(numCols = 100,
                    minOnes =21,
                    maxOnes =25,
                    colSet = [],
                    prevPattern =numpy.array([])):

  """Generate a single test pattern with given parameters.

  Parameters:
  --------------------------------------------
  numCols:                Number of columns in each pattern.
  minOnes:                The minimum number of 1's in each pattern.
  maxOnes:                The maximum number of 1's in each pattern.
  colSet:                 The set of column indices for the pattern.
  prevPattern:            Pattern to avoid (null intersection).
  """

  assert minOnes < maxOnes
  assert maxOnes < numCols

  nOnes = rgen.randint(minOnes, maxOnes)
  candidates = list(colSet.difference(set(prevPattern.nonzero()[0])))
  rgen.shuffle(candidates)
  ind = candidates[:nOnes]
  x = numpy.zeros(numCols, dtype='float32')
  x[ind] = 1

  return x


def buildTrainingSet(numSequences = 2,
                     sequenceLength = 100,
                     pctShared = 0.2,
                     seqGenMode = 'shared sequence',
                     subsequenceStartPos = 10,
                     numCols = 100,
                     minOnes=21,
                     maxOnes = 25,
                     disjointConsecutive =True):

  """Build random high order test sequences.

  Parameters:
  --------------------------------------------
  numSequences:           The number of sequences created.
  sequenceLength:         The length of each sequence.
  pctShared:              The percentage of sequenceLength that is shared across
                          every sequence. If sequenceLength is 100 and pctShared
                          is 0.2, then a subsequence consisting of 20 patterns
                          will be in every sequence. Can also be the keyword
                          'one pattern', in which case a single time step is
                          shared.
  seqGenMode:             What kind of sequence to generate. If contains 'shared'
                          generates shared subsequence. If contains 'no shared',
                          does not generate any shared subsequence. If contains
                          'shuffle', will use common patterns shuffle among the
                          different sequences. If contains 'beginning', will
                          place shared subsequence at the beginning.
  subsequenceStartPos:    The position where the shared subsequence starts
  numCols:                Number of columns in each pattern.
  minOnes:                The minimum number of 1's in each pattern.
  maxOnes:                The maximum number of 1's in each pattern.
  disjointConsecutive:    Whether to generate disjoint consecutive patterns or not.
  """

  # Calculate the set of column indexes once to be used in each call to
  # generatePattern()
  colSet = set(range(numCols))

  if 'beginning' in seqGenMode:
      assert 'shared' in seqGenMode and 'no shared' not in seqGenMode

  if 'no shared' in seqGenMode or numSequences == 1:
      pctShared = 0.0

  #-----------------------------------------------------------------------------
  # Build shared subsequence
  if 'no shared' not in seqGenMode and 'one pattern' not in seqGenMode:
      sharedSequenceLength = int(pctShared*sequenceLength)
  elif 'one pattern' in seqGenMode:
      sharedSequenceLength = 1
  else:
      sharedSequenceLength = 0

  assert sharedSequenceLength + subsequenceStartPos < sequenceLength

  sharedSequence = []

  for i in xrange(sharedSequenceLength):
    if disjointConsecutive and i > 0:
      x = generatePattern(numCols, minOnes, maxOnes, colSet,
                          sharedSequence[i-1])
    else:
      x = generatePattern(numCols, minOnes, maxOnes, colSet)
    sharedSequence.append(x)

  #-----------------------------------------------------------------------------
  # Build random training set, splicing in the shared subsequence
  trainingSequences = []

  if 'beginning' not in seqGenMode:
      trailingLength = sequenceLength - sharedSequenceLength - subsequenceStartPos
  else:
      trailingLength = sequenceLength - sharedSequenceLength

  for k,s in enumerate(xrange(numSequences)):

    # TODO: implement no repetitions
    if len(trainingSequences) > 0 and 'shuffle' in seqGenMode:

      r = range(subsequenceStartPos) \
          + range(subsequenceStartPos + sharedSequenceLength, sequenceLength)

      rgen.shuffle(r)

      r = r[:subsequenceStartPos] \
          + range(subsequenceStartPos, subsequenceStartPos + sharedSequenceLength) \
          + r[subsequenceStartPos:]

      sequence = [trainingSequences[k-1][j] for j in r]

    else:
        sequence = []

        if 'beginning' not in seqGenMode:
          for i in xrange(subsequenceStartPos):
            if disjointConsecutive and i > 0:
              x = generatePattern(numCols, minOnes, maxOnes, colSet, sequence[i-1])
            else:
              x = generatePattern(numCols, minOnes, maxOnes, colSet)
            sequence.append(x)

        if 'shared' in seqGenMode and 'no shared' not in seqGenMode:
          sequence.extend(sharedSequence)

        for i in xrange(trailingLength):
          if disjointConsecutive and i > 0:
            x = generatePattern(numCols, minOnes, maxOnes, colSet, sequence[i-1])
          else:
            x = generatePattern(numCols, minOnes, maxOnes, colSet)
          sequence.append(x)

    assert len(sequence) == sequenceLength

    trainingSequences.append(sequence)

  assert len(trainingSequences) == numSequences

  if VERBOSITY >= 2:
    print "Training Sequences"
    pprint.pprint(trainingSequences)

  if sharedSequenceLength > 0:
      return (trainingSequences, subsequenceStartPos + sharedSequenceLength)
  else:
      return (trainingSequences, -1)


def getSimplePatterns(numOnes, numPatterns):
  """Very simple patterns. Each pattern has numOnes consecutive
  bits on. There are numPatterns*numOnes bits in the vector."""

  numCols = numOnes * numPatterns
  p = []
  for i in xrange(numPatterns):
    x = numpy.zeros(numCols, dtype='float32')
    x[i*numOnes:(i+1)*numOnes] = 1
    p.append(x)

  return p


def buildSimpleTrainingSet(numOnes=5):

  """Two very simple high order sequences for debugging. Each pattern in the
  sequence has a series of 1's in a specific set of columns."""

  numPatterns = 11
  p = getSimplePatterns(numOnes, numPatterns)
  s1 = [p[0], p[1], p[2], p[3], p[4], p[5], p[6] ]
  s2 = [p[7], p[8], p[2], p[3], p[4], p[9], p[10]]
  trainingSequences = [s1, s2]

  return (trainingSequences, 5)


def buildAlternatingTrainingSet(numOnes=5):

  """High order sequences that alternate elements. Pattern i has one's in
  i*numOnes to (i+1)*numOnes.

  The sequences are:
     A B A B A C
     A B A B D E
     A B F G H I
     A J K L M N

  """

  numPatterns = 14
  p = getSimplePatterns(numOnes, numPatterns)
  s1 = [p[0], p[1], p[0], p[1], p[0], p[2]]
  s2 = [p[0], p[1], p[0], p[1], p[3], p[4]]
  s3 = [p[0], p[1], p[5], p[6], p[7], p[8]]
  s4 = [p[0], p[9], p[10], p[11], p[12], p[13]]
  trainingSequences = [s1, s2, s3, s4]

  return (trainingSequences, 5)


def buildHL0aTrainingSet(numOnes=5):
  """Simple sequences for HL0. Each pattern in the sequence has a series of 1's
  in a specific set of columns.
    There are 23 patterns, p0 to p22.
    The sequence we want to learn is p0->p1->p2
    We create a very long sequence consisting of N N p0 p1 p2 N N p0 p1 p2
    N is randomly chosen from p3 to p22
  """

  numPatterns = 23
  p = getSimplePatterns(numOnes, numPatterns)

  s = []
  s.append(p[rgen.randint(3,23)])
  for _ in xrange(20):
    s.append(p[rgen.randint(3,23)])
    s.append(p[0])
    s.append(p[1])
    s.append(p[2])
    s.append(p[rgen.randint(3,23)])

  return ([s], [[p[0], p[1], p[2]]])


def buildHL0bTrainingSet(numOnes=5):
  """Simple sequences for HL0b. Each pattern in the sequence has a series of 1's
  in a specific set of columns.
    There are 23 patterns, p0 to p22.
    The sequences we want to learn are p1->p2->p3 and p0->p1->p2->p4.
    We create a very long sequence consisting of these two sub-sequences
    intermixed with noise, such as:
          N N p0 p1 p2 p4 N N p1 p2 p3 N N p1 p2 p3
    N is randomly chosen from p5 to p22
  """

  numPatterns = 23
  p = getSimplePatterns(numOnes, numPatterns)

  s = []
  s.append(p[rgen.randint(5,numPatterns)])
  for _ in xrange(50):
    r = rgen.randint(5,numPatterns)
    print r,
    s.append(p[r])
    if rgen.binomial(1, 0.5) > 0:
      print "S1",
      s.append(p[0])
      s.append(p[1])
      s.append(p[2])
      s.append(p[4])
    else:
      print "S2",
      s.append(p[1])
      s.append(p[2])
      s.append(p[3])
    r = rgen.randint(5,numPatterns)
    s.append(p[r])
    print r,
  print

  return ([s], [ [p[0], p[1], p[2], p[4]],  [p[1], p[2], p[3]] ])



# Basic test (creation, pickling, basic run of learning and inference)
def basicTest():

  global TMClass, SEED, VERBOSITY, checkSynapseConsistency
  #--------------------------------------------------------------------------------
  # Create TM object
  numberOfCols =10
  cellsPerColumn =3
  initialPerm =.2
  connectedPerm =.8
  minThreshold =2
  newSynapseCount =5
  permanenceInc =.1
  permanenceDec =.05
  permanenceMax =1
  globalDecay =.05
  activationThreshold =4 # low for those basic tests on purpose
  doPooling =True
  segUpdateValidDuration =5
  seed =SEED
  verbosity =VERBOSITY

  tm = TMClass(numberOfCols, cellsPerColumn,
               initialPerm, connectedPerm,
               minThreshold, newSynapseCount,
               permanenceInc, permanenceDec, permanenceMax,
               globalDecay, activationThreshold,
               doPooling, segUpdateValidDuration,
               seed=seed, verbosity=verbosity,
               pamLength = 1000,
               checkSynapseConsistency=checkSynapseConsistency)

  print "Creation ok"

  #--------------------------------------------------------------------------------
  # Save and reload
  schema = TMClass.getSchema()

  with open("test_tm.bin", "w+b") as f:
    # Save
    proto = schema.new_message()
    tm.write(proto)
    proto.write(f)

    # Load
    f.seek(0)
    proto2 = schema.read(f)
    tm2 = TMClass.read(proto2)

  assert tm2.numberOfCols == numberOfCols
  assert tm2.cellsPerColumn == cellsPerColumn
  print tm2.initialPerm
  assert tm2.initialPerm == numpy.float32(.2)
  assert tm2.connectedPerm == numpy.float32(.8)
  assert tm2.minThreshold == minThreshold
  assert tm2.newSynapseCount == newSynapseCount
  assert tm2.permanenceInc == numpy.float32(.1)
  assert tm2.permanenceDec == numpy.float32(.05)
  assert tm2.permanenceMax == 1
  assert tm2.globalDecay == numpy.float32(.05)
  assert tm2.activationThreshold == activationThreshold
  assert tm2.doPooling == doPooling
  assert tm2.segUpdateValidDuration == segUpdateValidDuration
  assert tm2.seed == SEED
  assert tm2.verbosity == verbosity

  print "Save/load ok"

  #--------------------------------------------------------------------------------
  # Learn
  for i in xrange(5):
    xi = rgen.randint(0,2,(numberOfCols))
    x = numpy.array(xi, dtype="uint32")
    y = tm.learn(x)

  #--------------------------------------------------------------------------------
  # Infer
  patterns = rgen.randint(0,2,(4,numberOfCols))
  for i in xrange(10):
    xi = rgen.randint(0,2,(numberOfCols))
    x = numpy.array(xi, dtype="uint32")
    y = tm.infer(x)
    if i > 0:
        p = tm._checkPrediction([pattern.nonzero()[0] for pattern in patterns])

  print "basicTest ok"

#---------------------------------------------------------------------------------
# Figure out acceptable patterns if none were passed to us.
def findAcceptablePatterns(tm, t, whichSequence, trainingSequences, nAcceptable = 1):

    """
    Tries to infer the set of acceptable patterns for prediction at the given
    time step and for the give sequence. Acceptable patterns are: the current one,
    plus a certain number of patterns after timeStep, in the sequence that the TM
    is currently tracking. Any other pattern is not acceptable.

    TODO:
    ====
    - Doesn't work for noise cases.
    - Might run in trouble if shared subsequence at the beginning.

    Parameters:
    ==========
    tm                       the whole TM, so that we can look at its parameters
    t                        the current time step
    whichSequence            the sequence we are currently tracking
    trainingSequences        all the training sequences
    nAcceptable              the number of steps forward from the current timeStep
                             we are willing to consider acceptable. In the case of
                             pooling, it is less than or equal to the min of the
                             number of training reps and the segUpdateValidDuration
                             parameter of the TM, depending on the test case.
                             The default value is 1, because by default, the pattern
                             after the current one should always be predictable.

    Return value:
    ============
    acceptablePatterns       A list of acceptable patterns for prediction.

    """

    # Determine how many steps forward we want to see in the prediction
    upTo = t + 2 # always predict current and next

    # If the TM is pooling, more steps can be predicted
    if tm.doPooling:
        upTo += min(tm.segUpdateValidDuration, nAcceptable)

    assert upTo <= len(trainingSequences[whichSequence])

    acceptablePatterns = []

    # Check whether we were in a shared subsequence at the beginning.
    # If so, at the point of exiting the shared subsequence (t), we should
    # be predicting multiple patterns for 1 time step, then collapse back
    # to a single sequence.
    if len(trainingSequences) == 2 and \
       (trainingSequences[0][0] == trainingSequences[1][0]).all():
      if (trainingSequences[0][t] == trainingSequences[1][t]).all() \
        and (trainingSequences[0][t+1] != trainingSequences[1][t+1]).any():
          acceptablePatterns.append(trainingSequences[0][t+1])
          acceptablePatterns.append(trainingSequences[1][t+1])

    # Add patterns going forward
    acceptablePatterns += [trainingSequences[whichSequence][t] \
                           for t in xrange(t,upTo)]

    return acceptablePatterns



def testSequence(trainingSequences,
                 nTrainingReps = 1,
                 numberOfCols = 40,
                 cellsPerColumn =5,
                 initialPerm =.8,
                 connectedPerm =.7,
                 minThreshold = 11,
                 newSynapseCount =5,
                 permanenceInc =.4,
                 permanenceDec =0.0,
                 permanenceMax =1,
                 globalDecay =0.0,
                 pamLength = 1000,
                 activationThreshold =5,
                 acceptablePatterns = [], # if empty, try to infer what they are
                 doPooling = False,
                 nAcceptable = -1, # if doPooling, number of acceptable steps
                 noiseModel = None,
                 noiseLevel = 0,
                 doResets = True,
                 shouldFail = False,
                 testSequences = None,
                 predJustAfterHubOnly = None,
                 compareToPy = False,
                 nMultiStepPrediction = 0,
                 highOrder = False):

  """Test a single set of sequences once and return the number of
  prediction failures, the number of errors, and the number of perfect
  predictions"""

  global BacktrackingTM, SEED, checkSynapseConsistency, VERBOSITY

  numPerfect = 0        # When every column is correct in the prediction
  numStrictErrors = 0   # When at least one column is incorrect
  numFailures = 0       # When > 2 columns are incorrect

  sequenceLength = len(trainingSequences[0])
  segUpdateValidDuration =5
  verbosity = VERBOSITY

  # override default maxSeqLEngth value for high-order sequences
  if highOrder:
    tm = TMClass(numberOfCols, cellsPerColumn,
                 initialPerm, connectedPerm,
                 minThreshold, newSynapseCount,
                 permanenceInc, permanenceDec, permanenceMax,
                 globalDecay, activationThreshold,
                 doPooling, segUpdateValidDuration,
                 seed=SEED, verbosity=verbosity,
                 checkSynapseConsistency=checkSynapseConsistency,
                 pamLength=pamLength,
                 maxSeqLength=0
                 )
  else:
    tm = TMClass(numberOfCols, cellsPerColumn,
                 initialPerm, connectedPerm,
                 minThreshold, newSynapseCount,
                 permanenceInc, permanenceDec, permanenceMax,
                 globalDecay, activationThreshold,
                 doPooling, segUpdateValidDuration,
                 seed=SEED, verbosity=verbosity,
                 checkSynapseConsistency=checkSynapseConsistency,
                 pamLength=pamLength
                 )

  if compareToPy:
    # override default maxSeqLEngth value for high-order sequences
    if highOrder:
      py_tm = BacktrackingTM(numberOfCols, cellsPerColumn,
                             initialPerm, connectedPerm,
                             minThreshold, newSynapseCount,
                             permanenceInc, permanenceDec, permanenceMax,
                             globalDecay, activationThreshold,
                             doPooling, segUpdateValidDuration,
                             seed=SEED, verbosity=verbosity,
                             pamLength=pamLength,
                             maxSeqLength=0
                             )
    else:
      py_tm = BacktrackingTM(numberOfCols, cellsPerColumn,
                             initialPerm, connectedPerm,
                             minThreshold, newSynapseCount,
                             permanenceInc, permanenceDec, permanenceMax,
                             globalDecay, activationThreshold,
                             doPooling, segUpdateValidDuration,
                             seed=SEED, verbosity=verbosity,
                             pamLength=pamLength,
                             )

  trainingSequences = trainingSequences[0]
  if testSequences == None: testSequences = trainingSequences
  inferAcceptablePatterns = acceptablePatterns == []

  #--------------------------------------------------------------------------------
  # Learn
  for r in xrange(nTrainingReps):
    if VERBOSITY > 1:
      print "============= Learning round",r,"================="
    for sequenceNum, trainingSequence in enumerate(trainingSequences):
      if VERBOSITY > 1:
        print "============= New sequence ================="
      if doResets:
          tm.reset()
          if compareToPy:
              py_tm.reset()
      for t,x in enumerate(trainingSequence):
        if noiseModel is not None and \
               'xor' in noiseModel and 'binomial' in noiseModel \
               and 'training' in noiseModel:
            noise_vector = rgen.binomial(len(x), noiseLevel, (len(x)))
            x = logical_xor(x, noise_vector)
        if VERBOSITY > 2:
          print "Time step",t, "learning round",r, "sequence number", sequenceNum
          print "Input: ",tm.printInput(x)
          print "NNZ:", x.nonzero()
        x = numpy.array(x).astype('float32')
        y = tm.learn(x)
        if compareToPy:
            py_y = py_tm.learn(x)
            if t % 25 == 0: # To track bugs, do that every iteration, but very slow
                assert fdrutils.tmDiff(tm, py_tm, VERBOSITY) == True

        if VERBOSITY > 3:
          tm.printStates(printPrevious = (VERBOSITY > 4))
          print
      if VERBOSITY > 3:
        print "Sequence finished. Complete state after sequence"
        tm.printCells()
        print

  numPerfectAtHub = 0

  if compareToPy:
      print "End of training"
      assert fdrutils.tmDiff(tm, py_tm, VERBOSITY) == True

  #--------------------------------------------------------------------------------
  # Infer
  if VERBOSITY > 1: print "============= Inference ================="

  for s,testSequence in enumerate(testSequences):

    if VERBOSITY > 1: print "============= New sequence ================="

    if doResets:
        tm.reset()
        if compareToPy:
            py_tm.reset()

    slen = len(testSequence)

    for t,x in enumerate(testSequence):

      # Generate noise (optional)
      if noiseModel is not None and \
             'xor' in noiseModel and 'binomial' in noiseModel \
             and 'inference' in noiseModel:
        noise_vector = rgen.binomial(len(x), noiseLevel, (len(x)))
        x = logical_xor(x, noise_vector)

      if VERBOSITY > 2: print "Time step",t, '\nInput:', tm.printInput(x)

      x = numpy.array(x).astype('float32')
      y = tm.infer(x)

      if compareToPy:
          py_y = py_tm.infer(x)
          assert fdrutils.tmDiff(tm, py_tm, VERBOSITY) == True

      # if t == predJustAfterHubOnly:
      #     z = sum(y, axis = 1)
      #     print '\t\t',
      #     print ''.join('.' if z[i] == 0 else '1' for i in xrange(len(z)))

      if VERBOSITY > 3: tm.printStates(printPrevious = (VERBOSITY > 4),
                                       printLearnState = False); print


      if nMultiStepPrediction > 0:

        y_ms = tm.predict(nSteps=nMultiStepPrediction)

        if VERBOSITY > 3:
          print "Multi step prediction at Time step", t
          for i in range(nMultiStepPrediction):
            print "Prediction at t+", i+1
            tm.printColConfidence(y_ms[i])

        # Error Checking
        for i in range(nMultiStepPrediction):
          predictedTimeStep = t+i+1
          if predictedTimeStep < slen:
            input = testSequence[predictedTimeStep].nonzero()[0]
            prediction = y_ms[i].nonzero()[0]
            foundInInput, totalActiveInInput, \
            missingFromInput, totalActiveInPrediction  = \
                          fdrutils.checkMatch(input, prediction, sparse=True)
            falseNegatives = totalActiveInInput - foundInInput
            falsePositives = missingFromInput

            if VERBOSITY > 2:
              print "Predition from %d to %d" % (t, t+i+1)
              print "\t\tFalse Negatives:", falseNegatives
              print "\t\tFalse Positivies:", falsePositives

            if falseNegatives > 0 or falsePositives > 0:
              numStrictErrors += 1

              if falseNegatives > 0 and VERBOSITY > 1:
                print "Multi step prediction from t=", t, "to t=", t+i+1,\
                      "false negative with error=",falseNegatives,
                print "out of", totalActiveInInput,"ones"

              if falsePositives > 0 and VERBOSITY > 1:
                print "Multi step prediction from t=", t, "to t=", t+i+1,\
                    "false positive with error=",falsePositives,
                print "out of",totalActiveInInput,"ones"

              if falsePositives > 3 or falseNegatives > 3:
                numFailures += 1

                # Analyze the failure if we care about it
                if VERBOSITY > 1 and not shouldFail:
                  print 'Input at t=', t
                  print '\t\t',; printOneTrainingVector(testSequence[t])
                  print 'Prediction for t=', t+i+1
                  print '\t\t',; printOneTrainingVector(y_ms[i])
                  print 'Actual input at t=', t+i+1
                  print '\t\t',; printOneTrainingVector(testSequence[t+i+1])


      if t < slen-1:

        # If no acceptable patterns were passed to us, we need to infer them
        # for the current sequence and time step by looking at the testSequences.
        # nAcceptable is used to reduce the number of automatically determined
        # acceptable patterns.
        if inferAcceptablePatterns:
            acceptablePatterns = findAcceptablePatterns(tm, t, s, testSequences,
                                                        nAcceptable)

        scores = tm._checkPrediction([pattern.nonzero()[0] \
                                      for pattern in acceptablePatterns])

        falsePositives, falseNegatives = scores[0], scores[1]

        # We report an error if FN or FP is > 0.
        # We report a failure if number of FN or number of FP is > 2 for any
        # pattern.  We also count the number of perfect predictions.
        if falseNegatives > 0 or falsePositives > 0:

          numStrictErrors += 1

          if falseNegatives > 0 and VERBOSITY > 1:
            print "Pattern",s,"time",t,\
                  "prediction false negative with error=",falseNegatives,
            print "out of",int(testSequence[t+1].sum()),"ones"

          if falsePositives > 0 and VERBOSITY > 1:
            print "Pattern",s,"time",t,\
                  "prediction false positive with error=",falsePositives,
            print "out of",int(testSequence[t+1].sum()),"ones"

          if falseNegatives > 3 or falsePositives > 3:

            numFailures += 1

            # Analyze the failure if we care about it
            if VERBOSITY > 1 and not shouldFail:
              print 'Test sequences'
              if len(testSequences) > 1:
                  printAllTrainingSequences(testSequences, t+1)
              else:
                  print '\t\t',; printOneTrainingVector(testSequence[t])
                  print '\t\t',; printOneTrainingVector(testSequence[t+1])
              print 'Acceptable'
              for p in acceptablePatterns:
                  print '\t\t',; printOneTrainingVector(p)
              print 'Output'
              diagnostic = ''
              output = sum(tm.currentOutput,axis=1)
              print '\t\t',; printOneTrainingVector(output)

        else:
            numPerfect += 1

            if predJustAfterHubOnly is not None and predJustAfterHubOnly == t:
                numPerfectAtHub += 1

  if predJustAfterHubOnly is None:
      return numFailures, numStrictErrors, numPerfect, tm
  else:
      return numFailures, numStrictErrors, numPerfect, numPerfectAtHub, tm



def TestB1(numUniquePatterns, nTests, cellsPerColumn = 1, name = "B1"):

  numCols = 100
  sequenceLength = numUniquePatterns
  nFailed = 0

  for numSequences in [1]:

    print "Test "+name+" (sequence memory - 1 repetition - 1 sequence)"

    for k in range(nTests): # Test that configuration several times

      trainingSet = buildTrainingSet(numSequences =numSequences,
                                     sequenceLength = sequenceLength,
                                     pctShared = 0.0,
                                     subsequenceStartPos = 0,
                                     numCols = numCols,
                                     minOnes = 15, maxOnes = 20)

      numFailures, numStrictErrors, numPerfect, tm = \
                   testSequence(trainingSet,
                                nTrainingReps = 1,
                                numberOfCols = numCols,
                                cellsPerColumn = cellsPerColumn,
                                initialPerm = .8,
                                connectedPerm = .7,
                                minThreshold = 8,
                                newSynapseCount = 11,
                                permanenceInc = .4,
                                permanenceDec = 0,
                                permanenceMax = 1,
                                globalDecay = .0,
                                activationThreshold = 8,
                                doPooling = False)
      if numFailures == 0:
        print "Test "+name+" ok"
      else:
        print "Test "+name+" failed"
        nFailed = nFailed + 1
        print "numFailures=", numFailures
        print "numStrictErrors=", numStrictErrors
        print "numPerfect=", numPerfect

  return nFailed

def TestB7(numUniquePatterns, nTests, cellsPerColumn = 1, name = "B7"):

  numCols = 100
  sequenceLength = numUniquePatterns
  nFailed = 0

  for numSequences in [1]:

    print "Test "+name+" (sequence memory - 4 repetition - 1 sequence - slow learning)"

    for _ in range(nTests): # Test that configuration several times

      trainingSet = buildTrainingSet(numSequences =numSequences,
                                     sequenceLength = sequenceLength,
                                     pctShared = 0.0,
                                     subsequenceStartPos = 0,
                                     numCols = numCols,
                                     minOnes = 15, maxOnes = 20)

      numFailures, numStrictErrors, numPerfect, tm = \
                   testSequence(trainingSet,
                                nTrainingReps = 4,
                                numberOfCols = numCols,
                                cellsPerColumn = cellsPerColumn,
                                minThreshold = 11,
                                newSynapseCount = 11,
                                activationThreshold = 11,
                                initialPerm = .2,
                                connectedPerm = .6,
                                permanenceInc = .2,
                                permanenceDec = 0,
                                permanenceMax = 1,
                                globalDecay = .0,
                                doPooling = False)

      if numFailures == 0:
        print "Test "+name+" ok"
      else:
        print "Test "+name+" failed"
        nFailed = nFailed + 1
        print "numFailures=", numFailures,
        print "numStrictErrors=", numStrictErrors,
        print "numPerfect=", numPerfect

  return nFailed



def TestB2(numUniquePatterns, nTests, cellsPerColumn = 1, name = "B2"):

  numCols = 100
  sequenceLength = numUniquePatterns
  nFailed = 0

  for numSequences in [1]: # TestC has multiple sequences

    print "Test",name,"(sequence memory - second repetition of the same sequence" +\
          " should not add synapses)"
    print "Num patterns in sequence =", numUniquePatterns,
    print "cellsPerColumn=",cellsPerColumn

    for _ in range(nTests): # Test that configuration several times

      trainingSet = buildTrainingSet(numSequences =numSequences,
                                     sequenceLength = sequenceLength,
                                     pctShared = 0.0,
                                     subsequenceStartPos = 0,
                                     numCols = numCols,
                                     minOnes = 15, maxOnes = 20)

      # Do one pass through the training set
      numFailures1, numStrictErrors1, numPerfect1, tm1 = \
                   testSequence(trainingSet,
                                nTrainingReps = 1,
                                numberOfCols = numCols,
                                cellsPerColumn = cellsPerColumn,
                                initialPerm = .8,
                                connectedPerm = .7,
                                minThreshold = 8,
                                newSynapseCount = 11,
                                permanenceInc = .4,
                                permanenceDec = 0,
                                permanenceMax = 1,
                                globalDecay = .0,
                                activationThreshold = 8)

      # Do two passes through the training set
      numFailures, numStrictErrors, numPerfect, tm2 = \
                   testSequence(trainingSet,
                                nTrainingReps = 2,
                                numberOfCols = numCols,
                                cellsPerColumn = cellsPerColumn,
                                initialPerm = .8,
                                connectedPerm = .7,
                                minThreshold = 8,
                                newSynapseCount = 11,
                                permanenceInc = .4,
                                permanenceDec = 0,
                                permanenceMax = 1,
                                globalDecay = .0,
                                activationThreshold = 8)

      # Check that training with a second pass did not result in more synapses
      segmentInfo1 = tm1.getSegmentInfo()
      segmentInfo2 = tm2.getSegmentInfo()
      if (segmentInfo1[0] != segmentInfo2[0]) or \
         (segmentInfo1[1] != segmentInfo2[1]) :
          print "Training twice incorrectly resulted in more segments or synapses"
          print "Number of segments: ", segmentInfo1[0], segmentInfo2[0]
          numFailures += 1

      if numFailures == 0:
        print "Test",name,"ok"
      else:
        print "Test",name,"failed"
        nFailed = nFailed + 1
        print "numFailures=", numFailures
        print "numStrictErrors=", numStrictErrors
        print "numPerfect=", numPerfect

  return nFailed



def TestB3(numUniquePatterns, nTests):

  numCols = 100
  sequenceLength = numUniquePatterns
  nFailed = 0

  for numSequences in [2,5]:

    print "Test B3 (sequence memory - 2 repetitions -", numSequences, "sequences)"

    for _ in range(nTests): # Test that configuration several times

      trainingSet = buildTrainingSet(numSequences =numSequences,
                                     sequenceLength = sequenceLength,
                                     pctShared = 0.0,
                                     subsequenceStartPos = 0,
                                     numCols = numCols,
                                     minOnes = 15, maxOnes = 20)

      numFailures, numStrictErrors, numPerfect, tm = \
                   testSequence(trainingSet,
                                nTrainingReps = 2,
                                numberOfCols = numCols,
                                cellsPerColumn = 4,
                                initialPerm = .8,
                                connectedPerm = .7,
                                minThreshold = 11,
                                permanenceInc = .4,
                                permanenceDec = 0,
                                permanenceMax = 1,
                                globalDecay = .0,
                                newSynapseCount = 11,
                                activationThreshold = 8,
                                doPooling = False)
      if numFailures == 0:
        print "Test B3 ok"
      else:
        print "Test B3 failed"
        nFailed = nFailed + 1
        print "numFailures=", numFailures
        print "numStrictErrors=", numStrictErrors
        print "numPerfect=", numPerfect

  return nFailed



def TestH0(numOnes = 5,nMultiStepPrediction=0):

  cellsPerColumn = 4

  print "Higher order test 0 with cellsPerColumn=",cellsPerColumn

  trainingSet = buildSimpleTrainingSet(numOnes)

  numFailures, numStrictErrors, numPerfect, tm = \
               testSequence(trainingSet,
                            nTrainingReps = 20,
                            numberOfCols = trainingSet[0][0][0].size,
                            cellsPerColumn = cellsPerColumn,
                            initialPerm = .8,
                            connectedPerm = .7,
                            minThreshold = 6,
                            permanenceInc = .4,
                            permanenceDec = .2,
                            permanenceMax = 1,
                            globalDecay = .0,
                            newSynapseCount = 5,
                            activationThreshold = 4,
                            doPooling = False,
                            nMultiStepPrediction=nMultiStepPrediction)

  if numFailures == 0 and \
     numStrictErrors == 0 and \
     numPerfect == len(trainingSet[0])*(len(trainingSet[0][0]) - 1):
    print "Test PASS"
    return 0
  else:
    print "Test FAILED"
    print "numFailures=", numFailures
    print "numStrictErrors=", numStrictErrors
    print "numPerfect=", numPerfect
    return 1



def TestH(sequenceLength, nTests, cellsPerColumn, numCols =100, nSequences =[2],
          pctShared = 0.1, seqGenMode = 'shared sequence', nTrainingReps = 2,
          shouldFail = False, compareToPy = False, highOrder = False):

  nFailed = 0
  subsequenceStartPos = 10
  assert subsequenceStartPos < sequenceLength

  for numSequences in nSequences:

    print "Higher order test with sequenceLength=",sequenceLength,
    print "cellsPerColumn=",cellsPerColumn,"nTests=",nTests,
    print "numSequences=",numSequences, "pctShared=", pctShared

    for _ in range(nTests): # Test that configuration several times

      trainingSet = buildTrainingSet(numSequences = numSequences,
                                     sequenceLength = sequenceLength,
                                     pctShared = pctShared, seqGenMode = seqGenMode,
                                     subsequenceStartPos = subsequenceStartPos,
                                     numCols = numCols,
                                     minOnes = 21, maxOnes = 25)

      numFailures, numStrictErrors, numPerfect, tm = \
                   testSequence(trainingSet,
                                nTrainingReps = nTrainingReps,
                                numberOfCols = numCols,
                                cellsPerColumn = cellsPerColumn,
                                initialPerm = .8,
                                connectedPerm = .7,
                                minThreshold = 12,
                                permanenceInc = .4,
                                permanenceDec = .1,
                                permanenceMax = 1,
                                globalDecay = .0,
                                newSynapseCount = 11,
                                activationThreshold = 8,
                                doPooling = False,
                                shouldFail = shouldFail,
                                compareToPy = compareToPy,
                                highOrder = highOrder)

      if numFailures == 0 and not shouldFail \
             or numFailures > 0 and shouldFail:
          print "Test PASS",
          if shouldFail:
              print '(should fail, and failed)'
          else:
              print
      else:
        print "Test FAILED"
        nFailed = nFailed + 1
        print "numFailures=", numFailures
        print "numStrictErrors=", numStrictErrors
        print "numPerfect=", numPerfect

  return nFailed



def TestH11(numOnes = 3):

  cellsPerColumn = 4

  print "Higher order test 11 with cellsPerColumn=",cellsPerColumn

  trainingSet = buildAlternatingTrainingSet(numOnes= 3)

  numFailures, numStrictErrors, numPerfect, tm = \
               testSequence(trainingSet,
                            nTrainingReps = 1,
                            numberOfCols = trainingSet[0][0][0].size,
                            cellsPerColumn = cellsPerColumn,
                            initialPerm = .8,
                            connectedPerm = .7,
                            minThreshold = 6,
                            permanenceInc = .4,
                            permanenceDec = 0,
                            permanenceMax = 1,
                            globalDecay = .0,
                            newSynapseCount = 1,
                            activationThreshold = 1,
                            doPooling = False)

  if numFailures == 0 and \
     numStrictErrors == 0 and \
     numPerfect == len(trainingSet[0])*(len(trainingSet[0][0]) - 1):
    print "Test PASS"
    return 0
  else:
    print "Test FAILED"
    print "numFailures=", numFailures
    print "numStrictErrors=", numStrictErrors
    print "numPerfect=", numPerfect
    return 1



def TestH2a(sequenceLength, nTests, cellsPerColumn, numCols =100, nSequences =[2],
          pctShared = 0.02, seqGenMode = 'shared sequence',
          shouldFail = False):
  """
  Still need to test:
      Two overlapping sequences. OK to get new segments but check that we can
      get correct high order prediction after multiple reps.
  """

  print "Test H2a - second repetition of the same sequence should not add synapses"

  nFailed = 0
  subsequenceStartPos = 10
  assert subsequenceStartPos < sequenceLength

  for numSequences in nSequences:

    print "Higher order test with sequenceLength=",sequenceLength,
    print "cellsPerColumn=",cellsPerColumn,"nTests=",nTests,"numCols=", numCols
    print "numSequences=",numSequences, "pctShared=", pctShared,
    print "sharing mode=", seqGenMode

    for _ in range(nTests): # Test that configuration several times

      trainingSet = buildTrainingSet(numSequences = numSequences,
                                     sequenceLength = sequenceLength,
                                     pctShared = pctShared, seqGenMode = seqGenMode,
                                     subsequenceStartPos = subsequenceStartPos,
                                     numCols = numCols,
                                     minOnes = 21, maxOnes = 25)

      print "============== 10 ======================"

      numFailures3, numStrictErrors3, numPerfect3, tm3 = \
                   testSequence(trainingSet,
                                nTrainingReps = 10,
                                numberOfCols = numCols,
                                cellsPerColumn = cellsPerColumn,
                                initialPerm = .4,
                                connectedPerm = .7,
                                minThreshold = 12,
                                permanenceInc = .1,
                                permanenceDec = 0.1,
                                permanenceMax = 1,
                                globalDecay = .0,
                                newSynapseCount = 15,
                                activationThreshold = 12,
                                doPooling = False,
                                shouldFail = shouldFail)

      print "============== 2 ======================"

      numFailures, numStrictErrors, numPerfect, tm2 = \
                   testSequence(trainingSet,
                                nTrainingReps = 2,
                                numberOfCols = numCols,
                                cellsPerColumn = cellsPerColumn,
                                initialPerm = .8,
                                connectedPerm = .7,
                                minThreshold = 12,
                                permanenceInc = .1,
                                permanenceDec = 0,
                                permanenceMax = 1,
                                globalDecay = .0,
                                newSynapseCount = 15,
                                activationThreshold = 12,
                                doPooling = False,
                                shouldFail = shouldFail)

      print "============== 1 ======================"

      numFailures1, numStrictErrors1, numPerfect1, tm1 = \
                   testSequence(trainingSet,
                                nTrainingReps = 1,
                                numberOfCols = numCols,
                                cellsPerColumn = cellsPerColumn,
                                initialPerm = .8,
                                connectedPerm = .7,
                                minThreshold = 12,
                                permanenceInc = .1,
                                permanenceDec = 0,
                                permanenceMax = 1,
                                globalDecay = .0,
                                newSynapseCount = 15,
                                activationThreshold = 12,
                                doPooling = False,
                                shouldFail = shouldFail)

      # Check that training with a second pass did not result in more synapses
      segmentInfo1 = tm1.getSegmentInfo()
      segmentInfo2 = tm2.getSegmentInfo()
      if (abs(segmentInfo1[0] - segmentInfo2[0]) > 3) or \
         (abs(segmentInfo1[1] - segmentInfo2[1]) > 3*15) :
          print "Training twice incorrectly resulted in too many segments or synapses"
          print segmentInfo1
          print segmentInfo2
          print tm3.getSegmentInfo()
          tm3.trimSegments()
          print tm3.getSegmentInfo()

          print "Failures for 1, 2, and N reps"
          print numFailures1, numStrictErrors1, numPerfect1
          print numFailures, numStrictErrors, numPerfect
          print numFailures3, numStrictErrors3, numPerfect3
          numFailures += 1

      if numFailures == 0 and not shouldFail \
             or numFailures > 0 and shouldFail:
          print "Test PASS",
          if shouldFail:
              print '(should fail, and failed)'
          else:
              print
      else:
        print "Test FAILED"
        nFailed = nFailed + 1
        print "numFailures=", numFailures
        print "numStrictErrors=", numStrictErrors
        print "numPerfect=", numPerfect

  return nFailed



def TestP(sequenceLength, nTests, cellsPerColumn, numCols =300, nSequences =[2],
          pctShared = 0.1, seqGenMode = 'shared subsequence', nTrainingReps = 2):

  nFailed = 0

  newSynapseCount = 7
  activationThreshold = newSynapseCount - 2
  minOnes = 1.5 * newSynapseCount
  maxOnes = .3 * numCols / nTrainingReps

  for numSequences in nSequences:

    print "Pooling test with sequenceLength=",sequenceLength,
    print 'numCols=', numCols,
    print "cellsPerColumn=",cellsPerColumn,"nTests=",nTests,
    print "numSequences=",numSequences, "pctShared=", pctShared,
    print "nTrainingReps=", nTrainingReps, "minOnes=", minOnes,
    print "maxOnes=", maxOnes

    for _ in range(nTests): # Test that configuration several times

      minOnes = 1.5 * newSynapseCount

      trainingSet = buildTrainingSet(numSequences =numSequences,
                                     sequenceLength = sequenceLength,
                                     pctShared = pctShared, seqGenMode = seqGenMode,
                                     subsequenceStartPos = 10,
                                     numCols = numCols,
                                     minOnes = minOnes, maxOnes = maxOnes)

      numFailures, numStrictErrors, numPerfect, tm = \
                   testSequence(trainingSet,
                                nTrainingReps = nTrainingReps,
                                numberOfCols = numCols,
                                cellsPerColumn = cellsPerColumn,
                                initialPerm = .8,
                                connectedPerm = .7,
                                minThreshold = 11,
                                permanenceInc = .4,
                                permanenceDec = 0,
                                permanenceMax = 1,
                                globalDecay = .0,
                                newSynapseCount = newSynapseCount,
                                activationThreshold = activationThreshold,
                                doPooling = True)

      if numFailures == 0 and \
         numStrictErrors == 0 and \
         numPerfect == numSequences*(sequenceLength - 1):
        print "Test PASS"
      else:
        print "Test FAILED"
        print "numFailures=", numFailures
        print "numStrictErrors=", numStrictErrors
        print "numPerfect=", numPerfect
        nFailed = nFailed + 1

  return nFailed



def TestHL0a(numOnes = 5):

  cellsPerColumn = 4
  newSynapseCount = 5
  activationThreshold = newSynapseCount

  print "HiLo test 0a with cellsPerColumn=",cellsPerColumn

  trainingSet, testSet = buildHL0aTrainingSet()
  numCols = trainingSet[0][0].size

  numFailures, numStrictErrors, numPerfect, tm = \
               testSequence([trainingSet],
                            nTrainingReps = 1,
                            numberOfCols = numCols,
                            cellsPerColumn = cellsPerColumn,
                            initialPerm = .2,
                            connectedPerm = .7,
                            permanenceInc = .2,
                            permanenceDec = 0.05,
                            permanenceMax = 1,
                            globalDecay = .0,
                            minThreshold = activationThreshold,
                            newSynapseCount = newSynapseCount,
                            activationThreshold = activationThreshold,
                            pamLength = 2,
                            doPooling = False,
                            testSequences = testSet)

  tm.trimSegments()
  retAfter = tm.getSegmentInfo()
  print retAfter[0], retAfter[1]
  if retAfter[0] > 20:
    print "Too many segments"
    numFailures += 1
  if retAfter[1] > 100:
    print "Too many synapses"
    numFailures += 1

  if numFailures == 0:
    print "Test HL0a ok"
    return 0
  else:
    print "Test HL0a failed"
    print "numFailures=", numFailures
    print "numStrictErrors=", numStrictErrors
    print "numPerfect=", numPerfect
    return 1



def TestHL0b(numOnes = 5):

  cellsPerColumn = 4
  newSynapseCount = 5
  activationThreshold = newSynapseCount

  print "HiLo test 0b with cellsPerColumn=",cellsPerColumn

  trainingSet, testSet = buildHL0bTrainingSet()
  numCols = trainingSet[0][0].size
  print "numCols=", numCols

  numFailures, numStrictErrors, numPerfect, tm = \
               testSequence([trainingSet],
                            nTrainingReps = 1,
                            numberOfCols = numCols,
                            cellsPerColumn = cellsPerColumn,
                            initialPerm = .2,
                            connectedPerm = .7,
                            permanenceInc = .2,
                            permanenceDec = 0.05,
                            permanenceMax = 1,
                            globalDecay = .0,
                            minThreshold = activationThreshold,
                            newSynapseCount = newSynapseCount,
                            activationThreshold = activationThreshold,
                            doPooling = False,
                            testSequences = testSet)

  tm.trimSegments()
  retAfter = tm.getSegmentInfo()
  tm.printCells()

  if numFailures == 0:
    print "Test HL0 ok"
    return 0
  else:
    print "Test HL0 failed"
    print "numFailures=", numFailures
    print "numStrictErrors=", numStrictErrors
    print "numPerfect=", numPerfect
    return 1



def TestHL(sequenceLength, nTests, cellsPerColumn, numCols =200, nSequences =[2],
           pctShared = 0.1, seqGenMode = 'shared subsequence', nTrainingReps = 3,
           noiseModel = 'xor binomial in learning only', noiseLevel = 0.1,
           hiloOn = True):

  nFailed = 0

  newSynapseCount = 8
  activationThreshold = newSynapseCount
  minOnes = 1.5 * newSynapseCount
  maxOnes = 0.3 * numCols / nTrainingReps

  if hiloOn == False:
      minThreshold = 0.9

  for numSequences in nSequences:

    print "Hilo test with sequenceLength=", sequenceLength,
    print "cellsPerColumn=", cellsPerColumn, "nTests=", nTests,
    print "numSequences=", numSequences, "pctShared=", pctShared,
    print "nTrainingReps=", nTrainingReps, "minOnes=", minOnes,
    print "maxOnes=", maxOnes,
    print 'noiseModel=', noiseModel, 'noiseLevel=', noiseLevel

    for _ in range(nTests): # Test that configuration several times

      minOnes = 1.5 * newSynapseCount

      trainingSet = buildTrainingSet(numSequences =numSequences,
                                     sequenceLength = sequenceLength,
                                     pctShared = pctShared, seqGenMode = seqGenMode,
                                     subsequenceStartPos = 10,
                                     numCols = numCols,
                                     minOnes = minOnes, maxOnes = maxOnes)

      numFailures, numStrictErrors, numPerfect, tm = \
                   testSequence(trainingSet,
                                nTrainingReps = nTrainingReps,
                                numberOfCols = numCols,
                                cellsPerColumn = cellsPerColumn,
                                initialPerm = .2,
                                connectedPerm = .7,
                                minThreshold = activationThreshold,
                                newSynapseCount = newSynapseCount,
                                activationThreshold = activationThreshold,
                                permanenceInc = .2,
                                permanenceDec = 0.05,
                                permanenceMax = 1,
                                globalDecay = .0,
                                doPooling = False,
                                noiseModel = noiseModel,
                                noiseLevel = noiseLevel)

      if numFailures == 0 and \
         numStrictErrors == 0 and \
         numPerfect == numSequences*(sequenceLength - 1):
        print "Test PASS"
      else:
        print "Test FAILED"
        print "numFailures=", numFailures
        print "numStrictErrors=", numStrictErrors
        print "numPerfect=", numPerfect
        nFailed = nFailed + 1

  return nFailed



def worker(x):
  """Worker function to use in parallel hub capacity test below."""

  cellsPerColumn, numSequences = x[0], x[1]
  nTrainingReps = 1
  sequenceLength = 10
  numCols = 200

  print 'Started', cellsPerColumn, numSequences

  seqGenMode = 'shared subsequence, one pattern'
  subsequenceStartPos = 5
  trainingSet = buildTrainingSet(numSequences = numSequences,
                                 sequenceLength = sequenceLength,
                                 pctShared = .1, seqGenMode = seqGenMode,
                                 subsequenceStartPos = subsequenceStartPos,
                                 numCols = numCols,
                                 minOnes = 21, maxOnes = 25)

  numFailures1, numStrictErrors1, numPerfect1, atHub, tm = \
               testSequence(trainingSet,
                            nTrainingReps = nTrainingReps,
                            numberOfCols = numCols,
                            cellsPerColumn = cellsPerColumn,
                            initialPerm = .8,
                            connectedPerm = .7,
                            minThreshold = 11,
                            permanenceInc = .4,
                            permanenceDec = 0,
                            permanenceMax = 1,
                            globalDecay = .0,
                            newSynapseCount = 8,
                            activationThreshold = 8,
                            doPooling = False,
                            shouldFail = False,
                            predJustAfterHubOnly = 5)

  seqGenMode = 'no shared subsequence'
  trainingSet = buildTrainingSet(numSequences = numSequences,
                                 sequenceLength = sequenceLength,
                                 pctShared = 0, seqGenMode = seqGenMode,
                                 subsequenceStartPos = 0,
                                 numCols = numCols,
                                 minOnes = 21, maxOnes = 25)

  numFailures2, numStrictErrors2, numPerfect2, tm = \
               testSequence(trainingSet,
                            nTrainingReps = nTrainingReps,
                            numberOfCols = numCols,
                            cellsPerColumn = cellsPerColumn,
                            initialPerm = .8,
                            connectedPerm = .7,
                            minThreshold = 11,
                            permanenceInc = .4,
                            permanenceDec = 0,
                            permanenceMax = 1,
                            globalDecay = .0,
                            newSynapseCount = 8,
                            activationThreshold = 8,
                            doPooling = False,
                            shouldFail = False)

  print 'Completed',
  print cellsPerColumn, numSequences, numFailures1, numStrictErrors1, numPerfect1, atHub, \
         numFailures2, numStrictErrors2, numPerfect2

  return cellsPerColumn, numSequences, numFailures1, numStrictErrors1, numPerfect1, atHub, \
         numFailures2, numStrictErrors2, numPerfect2



def hubCapacity():

  """
  Study hub capacity. Figure out how many sequences can share a pattern
  for a given number of cells per column till we the system fails.
  DON'T RUN IN BUILD SYSTEM!!! (takes too long)
  """

  from multiprocessing import Pool
  import itertools

  print "Hub capacity test"
  # scalar value on predictions by looking at max perm over column

  p = Pool(2)

  results = p.map(worker, itertools.product([1,2,3,4,5,6,7,8], xrange(1,2000,200)))

  f = open('results-numPerfect.11.22.10.txt', 'w')
  for i,r in enumerate(results):
      print >>f, '{%d,%d,%d,%d,%d,%d,%d,%d,%d},' % r
  f.close()



def runTests(testLength = "short"):

  # Data structure to collect results of tests
  # TODO: put numFailures, numStrictErrors and numPerfect in here for reporting
  tests = {}

  # always run this one: if that one fails, we can't do anything
  basicTest()
  print

  #---------------------------------------------------------------------------------
  if testLength == "long":
    tests['B1'] = TestB1(numUniquePatterns, nTests)
    tests['B2'] = TestB2(numUniquePatterns, nTests)
    tests['B8'] = TestB7(4, nTests, cellsPerColumn = 4, name="B8")
    tests['B10'] = TestB2(numUniquePatterns, nTests, cellsPerColumn = 4,
                          name = "B10")

  # Run these always
  tests['B3'] = TestB3(numUniquePatterns, nTests)
  tests['B6'] = TestB1(numUniquePatterns, nTests,
                                   cellsPerColumn = 4, name="B6")
  tests['B7'] = TestB7(numUniquePatterns, nTests)

  print

  #---------------------------------------------------------------------------------

  #print "Test H11"
  #tests['H11'] = TestH11()

  if True:

      print "Test H0"
      tests['H0'] = TestH0(numOnes = 5)

      print "Test H2"
      #tests['H2'] = TestH(numUniquePatterns, nTests, cellsPerColumn = 4,
      #                    nTrainingReps = numUniquePatterns, compareToPy = False)

      print "Test H3"
      tests['H3'] = TestH(numUniquePatterns, nTests,
                          numCols = 200,
                          cellsPerColumn = 20,
                          pctShared = 0.3, nTrainingReps=numUniquePatterns,
                          compareToPy = False,
                          highOrder = True)

      print "Test H4" # Produces 3 false positives, but otherwise fine.
      # TODO: investigate initial false positives?
      tests['H4'] = TestH(numUniquePatterns, nTests,
                        cellsPerColumn = 20,
                        pctShared = 0.1,
                        seqGenMode='shared subsequence at beginning')

  if True:
      print "Test H0 with multistep prediction"

      tests['H0_MS'] = TestH0(numOnes = 5, nMultiStepPrediction=2)


  if True:

      print "Test H1" # - Should Fail
      tests['H1'] = TestH(numUniquePatterns, nTests,
                                      cellsPerColumn = 1, nTrainingReps = 1,
                                      shouldFail = True)

      # Also fails in --long mode. See H2 above
      #print "Test H2a"
      #tests['H2a'] = TestH2a(numUniquePatterns,
      #                  nTests, pctShared = 0.02, numCols = 300, cellsPerColumn = 4)



  if False:
      print "Test H5" # make sure seqs are good even with shuffling, fast learning
      tests['H5'] = TestH(numUniquePatterns, nTests,
                            cellsPerColumn = 10,
                            pctShared = 0.0,
                            seqGenMode='shuffle, no shared subsequence')

      print "Test H6" # should work
      tests['H6'] = TestH(numUniquePatterns, nTests,
                            cellsPerColumn = 10,
                            pctShared = 0.4,
                            seqGenMode='shuffle, shared subsequence')

      # Try with 2 sequences, then 3 sequences interleaved so that there is
      # always a shared pattern, but it belongs to 2 different sequences each
      # time!
      #print "Test H7"
      #tests['H7'] = TestH(numUniquePatterns, nTests,
      #                                  cellsPerColumn = 10,
      #                                  pctShared = 0.4,
      #                                  seqGenMode='shuffle, shared subsequence')

      # tricky: if start predicting in middle of subsequence, several predictions
      # are possible
      #print "Test H8"
      #tests['H8'] = TestH(numUniquePatterns, nTests,
      #                                  cellsPerColumn = 10,
      #                                  pctShared = 0.4,
      #                                  seqGenMode='shuffle, shared subsequence')

      print "Test H9" # plot hub capacity
      tests['H9'] = TestH(numUniquePatterns, nTests,
                                        cellsPerColumn = 10,
                                        pctShared = 0.4,
                                        seqGenMode='shuffle, shared subsequence')

      #print "Test H10" # plot
      #tests['H10'] = TestH(numUniquePatterns, nTests,
      #                                    cellsPerColumn = 10,
      #                                    pctShared = 0.4,
      #                                    seqGenMode='shuffle, shared subsequence')

      print

  #---------------------------------------------------------------------------------
  if False:
      print "Test P1"
      tests['P1'] = TestP(numUniquePatterns, nTests,
                                        cellsPerColumn = 4,
                                        pctShared = 0.0,
                                        seqGenMode = 'no shared subsequence',
                                        nTrainingReps = 3)

  if False:

      print "Test P2"
      tests['P2'] = TestP(numUniquePatterns, nTests,
                                        cellsPerColumn = 4,
                                        pctShared = 0.0,
                                        seqGenMode = 'no shared subsequence',
                                        nTrainingReps = 5)

      print "Test P3"
      tests['P3'] = TestP(numUniquePatterns, nTests,
                                        cellsPerColumn = 4,
                                        pctShared = 0.0,
                                        seqGenMode = 'no shared subsequence',
                                        nSequences = [2] if testLength == 'short' else [2,5],
                                        nTrainingReps = 5)

      print "Test P4"
      tests['P4'] = TestP(numUniquePatterns, nTests,
                                        cellsPerColumn = 4,
                                        pctShared = 0.0,
                                        seqGenMode = 'shared subsequence',
                                        nSequences = [2] if testLength == 'short' else [2,5],
                                        nTrainingReps = 5)

      print

  #---------------------------------------------------------------------------------
  if True:
      print "Test HL0a"
      tests['HL0a'] = TestHL0a(numOnes = 5)

  if False:

      print "Test HL0b"
      tests['HL0b'] = TestHL0b(numOnes = 5)

      print "Test HL1"
      tests['HL1'] = TestHL(sequenceLength = 20,
                                           nTests = nTests,
                                           numCols = 100,
                                           nSequences = [1],
                                           nTrainingReps = 3,
                                           cellsPerColumn = 1,
                                           seqGenMode = 'no shared subsequence',
                                           noiseModel = 'xor binomial in learning only',
                                           noiseLevel = 0.1,
                                           doResets = False)

      print "Test HL2"
      tests['HL2'] = TestHL(numUniquePatterns = 20,
                                           nTests = nTests,
                                           numCols = 200,
                                           nSequences = [1],
                                           nTrainingReps = 3,
                                           cellsPerColumn = 1,
                                           seqGenMode = 'no shared subsequence',
                                           noiseModel = 'xor binomial in learning only',
                                           noiseLevel = 0.1,
                                           doResets = False)

      print "Test HL3"
      tests['HL3'] = TestHL(numUniquePatterns = 30,
                                           nTests = nTests,
                                           numCols = 200,
                                           nSequences = [2],
                                           pctShared = 0.66,
                                           nTrainingReps = 3,
                                           cellsPerColumn = 1,
                                           seqGenMode = 'shared subsequence',
                                           noiseModel = None,
                                           noiseLevel = 0.0,
                                           doResets = True)

      print "Test HL4"
      tests['HL4'] = TestHL(numUniquePatterns = 30,
                                           nTests = nTests,
                                           numCols = 200,
                                           nSequences = [2],
                                           pctShared = 0.66,
                                           nTrainingReps = 3,
                                           cellsPerColumn = 1,
                                           seqGenMode = 'shared subsequence',
                                           noiseModel = None,
                                           noiseLevel = 0.0,
                                           doResets = False)

      print "Test HL5"
      tests['HL5'] = TestHL(numUniquePatterns = 30,
                                           nTests = nTests,
                                           numCols = 200,
                                           nSequences = [2],
                                           pctShared = 0.66,
                                           nTrainingReps = 3,
                                           cellsPerColumn = 1,
                                           seqGenMode = 'shared subsequence',
                                           noiseModel = 'xor binomial in learning only',
                                           noiseLevel = 0.1,
                                           doResets = False)

      print "Test HL6"
      tests['HL6'] = nTests - TestHL(numUniquePatterns = 20,
                                     nTests = nTests,
                                     numCols = 200,
                                     nSequences = [1],
                                     nTrainingReps = 3,
                                     cellsPerColumn = 1,
                                     seqGenMode = 'no shared subsequence',
                                     noiseModel = 'xor binomial in learning only',
                                     noiseLevel = 0.1,
                                     doResets = True,
                                     hiloOn = False)

      print

  #---------------------------------------------------------------------------------
  nFailures = 0
  for k,v in tests.iteritems():
    nFailures = nFailures + v

  if nFailures > 0: # 1 to account for H1
    print "There are failed tests"
    print "Test\tn failures"
    for k,v in tests.iteritems():
      print k, "\t", v
    assert 0
  else:
    print "All tests pass"

  #---------------------------------------------------------------------------------
  # Keep
  if False:
    import hotshot
    import hotshot.stats
    prof = hotshot.Profile("profile.prof")
    prof.runcall(TestB2, numUniquePatterns=100, nTests=2)
    prof.close()
    stats = hotshot.stats.load("profile.prof")
    stats.strip_dirs()
    stats.sort_stats('time', 'calls')
    stats.print_stats(50)



if __name__=="__main__":

  if not TEST_CPP_TM:
    print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    print "!!  WARNING: C++ TM testing is DISABLED until it can be updated."
    print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"

  # Three different test lengths are passed in through the command line.
  # Developer tests use --short. Autobuild does not pass in anything.
  # Acceptance tests pass in --long. testLength reflects these possibilities
  # as "autobuild", "short", and "long"
  testLength = "autobuild"

  # Scan command line arguments to see what to do for the seed
  # TODO: make default be a random seed, once we're sure it will pass reliably!
  for i,arg in enumerate(sys.argv):
      if 'seed' in arg:
          try:
              # used specified seed
              SEED = int(sys.argv[i+1])
          except ValueError as e:
              # random seed
              SEED = numpy.random.randint(100)
      if 'verbosity' in arg:
          VERBOSITY = int(sys.argv[i+1])
      if 'help' in arg:
          print "TMTest.py --short|long --seed number|'rand' --verbosity number"
          sys.exit()
      if "short" in arg:
        testLength = "short"
      if "long" in arg:
        testLength = "long"

  rgen = numpy.random.RandomState(SEED) # always call this rgen, NOT random

  # Setup the severity and length of the tests
  if testLength == "short":
    numUniquePatterns = 50
    nTests = 1
  elif testLength == "autobuild":
    print "Running autobuild tests"
    numUniquePatterns = 50
    nTests = 1
  elif testLength == "long":
    numUniquePatterns = 100
    nTests = 3

  print "TM tests", testLength, "numUniquePatterns=", numUniquePatterns, "nTests=", nTests,
  print "seed=", SEED
  print

  if testLength == "long":
    print 'Testing BacktrackingTM'
    TMClass = BacktrackingTM
    runTests(testLength)

  if testLength != 'long':
    checkSynapseConsistency = False
  else:
    # Setting this to True causes test to take way too long
    # Temporarily turned off so we can investigate
    checkSynapseConsistency = False

  if TEST_CPP_TM:
    print 'Testing C++ TM'
    TMClass = BacktrackingTMCPP
    runTests(testLength)
