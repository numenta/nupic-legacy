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
Generate artificial datasets for the multi-step prediction experiments
"""

import os
import numpy
import random
from optparse import OptionParser

from nupic.data.file_record_stream import FileRecordStream



def _generateSimple(filename="simple.csv", numSequences=2, elementsPerSeq=1, 
                    numRepeats=10, resets=False):
  """ Generate a simple dataset. This contains a bunch of non-overlapping
  sequences. 
  
  Parameters:
  ----------------------------------------------------
  filename:       name of the file to produce, including extension. It will
                  be created in a 'datasets' sub-directory within the 
                  directory containing this script. 
  numSequences:   how many sequences to generate
  elementsPerSeq: length of each sequence
  numRepeats:     how many times to repeat each sequence in the output 
  resets:         if True, turn on reset at start of each sequence
  """
  
  # Create the output file
  scriptDir = os.path.dirname(__file__)
  pathname = os.path.join(scriptDir, 'datasets', filename)
  print "Creating %s..." % (pathname)
  fields = [('reset', 'int', 'R'), 
            ('field1', 'string', ''),  
            ('field2', 'float', '')]  
  outFile = FileRecordStream(pathname, write=True, fields=fields)
  
  # Create the sequences
  sequences = []
  for i in range(numSequences):
    seq = [x for x in range(i*elementsPerSeq, (i+1)*elementsPerSeq)]
    sequences.append(seq)
  
  # Write out the sequences in random order
  seqIdxs = []
  for i in range(numRepeats):
    seqIdxs += range(numSequences)
  random.shuffle(seqIdxs)
  
  for seqIdx in seqIdxs:
    reset = int(resets)
    seq = sequences[seqIdx]
    for x in seq:
      outFile.appendRecord([reset, str(x), x])
      reset = 0

  outFile.close()



def _generateOverlapping(filename="overlap.csv", numSequences=2, elementsPerSeq=3, 
                    numRepeats=10, hub=[0,1], hubOffset=1, resets=False):
  
  """ Generate a temporal dataset containing sequences that overlap one or more
  elements with other sequences. 
  
  Parameters:
  ----------------------------------------------------
  filename:       name of the file to produce, including extension. It will
                  be created in a 'datasets' sub-directory within the 
                  directory containing this script. 
  numSequences:   how many sequences to generate
  elementsPerSeq: length of each sequence
  numRepeats:     how many times to repeat each sequence in the output 
  hub:            sub-sequence to place within each other sequence 
  hubOffset:      where, within each sequence, to place the hub
  resets:         if True, turn on reset at start of each sequence
  """
  
  # Check for conflicts in arguments
  assert (hubOffset + len(hub) <= elementsPerSeq)
  
  # Create the output file
  scriptDir = os.path.dirname(__file__)
  pathname = os.path.join(scriptDir, 'datasets', filename)
  print "Creating %s..." % (pathname)
  fields = [('reset', 'int', 'R'), 
            ('field1', 'string', ''),  
            ('field2', 'float', '')]  
  outFile = FileRecordStream(pathname, write=True, fields=fields)
  

  # Create the sequences with the hub in the middle
  sequences = []
  nextElemIdx = max(hub)+1
  
  for _ in range(numSequences):
    seq = []
    for j in range(hubOffset):
      seq.append(nextElemIdx)
      nextElemIdx += 1
    for j in hub:
      seq.append(j)
    j = hubOffset + len(hub)
    while j < elementsPerSeq:
      seq.append(nextElemIdx)
      nextElemIdx += 1
      j += 1
    sequences.append(seq)
  
  # Write out the sequences in random order
  seqIdxs = []
  for _ in range(numRepeats):
    seqIdxs += range(numSequences)
  random.shuffle(seqIdxs)
  
  for seqIdx in seqIdxs:
    reset = int(resets)
    seq = sequences[seqIdx]
    for (x) in seq:
      outFile.appendRecord([reset, str(x), x])
      reset = 0

  outFile.close()
  


def _generateFirstOrder0():
  """ Generate the initial, first order, and second order transition
  probabilities for 'probability0'. For this model, we generate the following
  set of sequences:
  
    .1   .75
  0----1-----2
   \    \   
    \    \  .25
     \    \-----3
      \
       \ .9     .5 
        \--- 4--------- 2
              \
               \   .5
                \---------3   
          
  
  
  
  Parameters:
  ----------------------------------------------------------------------
  retval: (initProb, firstOrder, secondOrder, seqLen)
            initProb:     Initial probability for each category. This is a vector
                            of length len(categoryList).
            firstOrder:   A dictionary of the 1st order probabilities. The key
                            is the 1st element of the sequence, the value is
                            the probability of each 2nd element given the first. 
            secondOrder:  A dictionary of the 2nd order probabilities. The key
                            is the first 2 elements of the sequence, the value is
                            the probability of each possible 3rd element given the 
                            first two. 
            seqLen:       Desired length of each sequence. The 1st element will
                          be generated using the initProb, the 2nd element by the
                          firstOrder table, and the 3rd and all successive 
                          elements by the secondOrder table. 
            categoryList:  list of category names to use


  Here is an example of some return values when there are 3 categories
  initProb:         [0.7, 0.2, 0.1]
  
  firstOrder:       {'[0]': [0.3, 0.3, 0.4],
                     '[1]': [0.3, 0.3, 0.4],
                     '[2]': [0.3, 0.3, 0.4]}
                     
  secondOrder:      {'[0,0]': [0.3, 0.3, 0.4],
                     '[0,1]': [0.3, 0.3, 0.4],
                     '[0,2]': [0.3, 0.3, 0.4],
                     '[1,0]': [0.3, 0.3, 0.4],
                     '[1,1]': [0.3, 0.3, 0.4],
                     '[1,2]': [0.3, 0.3, 0.4],
                     '[2,0]': [0.3, 0.3, 0.4],
                     '[2,1]': [0.3, 0.3, 0.4],
                     '[2,2]': [0.3, 0.3, 0.4]}
  """


  # --------------------------------------------------------------------
  # Initial probabilities, 'a' and 'e' equally likely
  numCategories = 5
  initProb = numpy.zeros(numCategories)
  initProb[0] = 1.0
  

  # --------------------------------------------------------------------
  # 1st order transitions
  firstOrder = dict()
  firstOrder['0'] = numpy.array([0, 0.1, 0, 0, 0.9])
  firstOrder['1'] = numpy.array([0, 0, 0.75, 0.25, 0])
  firstOrder['2'] = numpy.array([1.0, 0, 0, 0, 0])
  firstOrder['3'] = numpy.array([1.0, 0, 0, 0, 0])
  firstOrder['4'] = numpy.array([0, 0, 0.5, 0.5, 0])
   
  # --------------------------------------------------------------------
  # 2nd order transitions don't apply
  secondOrder = None
  
  # Generate the category list
  categoryList = ['%d' % x for x in range(5)]
  return (initProb, firstOrder, secondOrder, 3, categoryList)



def _generateFileFromProb(filename, numRecords, categoryList, initProb, 
      firstOrderProb, secondOrderProb, seqLen, numNoise=0, resetsEvery=None):
  """ Generate a set of records reflecting a set of probabilities.
  
  Parameters:
  ----------------------------------------------------------------
  filename:         name of .csv file to generate
  numRecords:       number of records to generate
  categoryList:     list of category names
  initProb:         Initial probability for each category. This is a vector
                      of length len(categoryList).
  firstOrderProb:   A dictionary of the 1st order probabilities. The key
                      is the 1st element of the sequence, the value is
                      the probability of each 2nd element given the first. 
  secondOrderProb:  A dictionary of the 2nd order probabilities. The key
                      is the first 2 elements of the sequence, the value is
                      the probability of each possible 3rd element given the 
                      first two. If this is None, then the sequences will be
                      first order only. 
  seqLen:           Desired length of each sequence. The 1st element will
                      be generated using the initProb, the 2nd element by the
                      firstOrder table, and the 3rd and all successive 
                      elements by the secondOrder table. None means infinite
                      length. 
  numNoise:         Number of noise elements to place between each 
                      sequence. The noise elements are evenly distributed from 
                      all categories. 
  resetsEvery:      If not None, generate a reset every N records
                      
                      
  Here is an example of some parameters:
  
  categoryList:     ['cat1', 'cat2', 'cat3']
  
  initProb:         [0.7, 0.2, 0.1]
  
  firstOrderProb:   {'[0]': [0.3, 0.3, 0.4],
                     '[1]': [0.3, 0.3, 0.4],
                     '[2]': [0.3, 0.3, 0.4]}
                     
  secondOrderProb:  {'[0,0]': [0.3, 0.3, 0.4],
                     '[0,1]': [0.3, 0.3, 0.4],
                     '[0,2]': [0.3, 0.3, 0.4],
                     '[1,0]': [0.3, 0.3, 0.4],
                     '[1,1]': [0.3, 0.3, 0.4],
                     '[1,2]': [0.3, 0.3, 0.4],
                     '[2,0]': [0.3, 0.3, 0.4],
                     '[2,1]': [0.3, 0.3, 0.4],
                     '[2,2]': [0.3, 0.3, 0.4]}
                   
  """
  
  # Create the file
  print "Creating %s..." % (filename)
  fields = [('reset', 'int', 'R'), 
            ('field1', 'string', ''),
            ('field2', 'float', '')]

  scriptDir = os.path.dirname(__file__)
  pathname = os.path.join(scriptDir, 'datasets', filename)
  outFile = FileRecordStream(pathname, write=True, fields=fields)
  
  # --------------------------------------------------------------------
  # Convert the probabilitie tables into cumulative probabilities
  initCumProb = initProb.cumsum()
  
  firstOrderCumProb = dict()
  for (key,value) in firstOrderProb.iteritems():
    firstOrderCumProb[key] = value.cumsum()
    
  if secondOrderProb is not None:
    secondOrderCumProb = dict()
    for (key,value) in secondOrderProb.iteritems():
      secondOrderCumProb[key] = value.cumsum()
  else:
    secondOrderCumProb = None
    

  # --------------------------------------------------------------------
  # Write out the sequences
  elementsInSeq = []
  numElementsSinceReset = 0
  maxCatIdx = len(categoryList) - 1
  for _ in xrange(numRecords):

    # Generate a reset?
    if numElementsSinceReset == 0:
      reset = 1
    else:
      reset = 0
      
    # Pick the next element, based on how are we are into the 2nd order
    #   sequence. 
    rand = numpy.random.rand()
    
    # Generate 1st order sequences
    if secondOrderCumProb is None:
      if len(elementsInSeq) == 0:
        catIdx = numpy.searchsorted(initCumProb, rand)
      elif len(elementsInSeq) >= 1 and \
                    (seqLen is None or len(elementsInSeq) < seqLen-numNoise):
        catIdx = numpy.searchsorted(firstOrderCumProb[str(elementsInSeq[-1])], 
                                    rand)
      else:   # random "noise"
        catIdx = numpy.random.randint(len(categoryList))

    # Generate 2nd order sequences
    else:
      if len(elementsInSeq) == 0:
        catIdx = numpy.searchsorted(initCumProb, rand)
      elif len(elementsInSeq) == 1:
        catIdx = numpy.searchsorted(firstOrderCumProb[str(elementsInSeq)], rand)
      elif (len(elementsInSeq) >=2) and \
                    (seqLen is None or len(elementsInSeq) < seqLen-numNoise):
        catIdx = numpy.searchsorted(secondOrderCumProb[str(elementsInSeq[-2:])], rand)
      else:   # random "noise"
        catIdx = numpy.random.randint(len(categoryList))
      
    # -------------------------------------------------------------------
    # Write out the record
    catIdx = min(maxCatIdx, catIdx)
    outFile.appendRecord([reset, categoryList[catIdx], catIdx])    
    #print categoryList[catIdx]
    
    # ------------------------------------------------------------
    # Increment counters
    elementsInSeq.append(catIdx)
    numElementsSinceReset += 1
    
    # Generate another reset?
    if resetsEvery is not None and numElementsSinceReset == resetsEvery:
      numElementsSinceReset = 0
      elementsInSeq = []
    
    # Start another 2nd order sequence?
    if seqLen is not None and (len(elementsInSeq) == seqLen+numNoise):
      elementsInSeq = []
      
  
  outFile.close()



if __name__ == '__main__':

  helpString = \
  """%prog [options] 
  Generate artificial datasets for testing multi-step prediction """
  
  
  
  # ============================================================================
  # Process command line arguments
  parser = OptionParser(helpString)

  parser.add_option("--verbosity", default=0, type="int",
        help="Verbosity level, either 0, 1, 2, or 3 [default: %default].")
  

  (options, args) = parser.parse_args()
  if len(args) != 0:
    parser.error("No arguments accepted")

  # Set random seed
  random.seed(42)
  
  # Create the dataset directory if necessary
  datasetsDir = os.path.join(os.path.dirname(__file__), 'datasets')
  if not os.path.exists(datasetsDir):
    os.mkdir(datasetsDir)
    

  
  # Generate the sample datasets
  _generateSimple('simple_0.csv', numSequences=2, elementsPerSeq=5, 
                  numRepeats=30)
  
  _generateSimple('simple_1.csv', numSequences=10, elementsPerSeq=5, 
                  numRepeats=20)

  _generateOverlapping('simple_2.csv', numSequences=10, elementsPerSeq=5, 
                  numRepeats=20, hub=[0,1], hubOffset=1, resets=False)
  
  _generateSimple('simple_3.csv', numSequences=2, elementsPerSeq=10, 
                  numRepeats=30, resets=False)
  

  # The first order 0 dataset
  (initProb, firstOrderProb, secondOrderProb, seqLen, categoryList) = \
                                              _generateFirstOrder0()
  _generateFileFromProb(filename='first_order_0.csv', numRecords=1000,
                  categoryList=categoryList, initProb=initProb,
                  firstOrderProb=firstOrderProb, secondOrderProb=secondOrderProb,
                  seqLen=seqLen, numNoise=0, resetsEvery=None)
 
