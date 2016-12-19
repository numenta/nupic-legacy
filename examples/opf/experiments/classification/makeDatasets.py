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

Generate artificial datasets

"""

import os
import random
from optparse import OptionParser

from nupic.data.file_record_stream import FileRecordStream



def _generateCategory(filename="simple.csv", numSequences=2, elementsPerSeq=1, 
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
  fields = [('reset', 'int', 'R'), ('category', 'int', 'C'),
            ('field1', 'string', '')]  
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
      outFile.appendRecord([reset, str(seqIdx), str(x)])
      reset = 0

  outFile.close()



def _generateScalar(filename="simple.csv", numSequences=2, elementsPerSeq=1, 
                    numRepeats=10, stepSize=0.1, resets=False):
  """ Generate a simple dataset. This contains a bunch of non-overlapping
  sequences of scalar values. 
  
  Parameters:
  ----------------------------------------------------
  filename:       name of the file to produce, including extension. It will
                  be created in a 'datasets' sub-directory within the 
                  directory containing this script. 
  numSequences:   how many sequences to generate
  elementsPerSeq: length of each sequence
  numRepeats:     how many times to repeat each sequence in the output
  stepSize:       how far apart each scalar is 
  resets:         if True, turn on reset at start of each sequence
  """
  
  # Create the output file
  scriptDir = os.path.dirname(__file__)
  pathname = os.path.join(scriptDir, 'datasets', filename)
  print "Creating %s..." % (pathname)
  fields = [('reset', 'int', 'R'), ('category', 'int', 'C'),
            ('field1', 'float', '')]  
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
      outFile.appendRecord([reset, str(seqIdx), x*stepSize])
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
  fields = [('reset', 'int', 'R'), ('category', 'int', 'C'),
            ('field1', 'string', '')]  
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
      outFile.appendRecord([reset, str(seqIdx), str(x)])
      reset = 0

  outFile.close()



if __name__ == '__main__':

  helpString = \
  """%prog [options] <datasetName>
  Generate artifical datasets for testing classification """
  
  
  
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
    

  
  # Generate the category field datasets
  _generateCategory('category_SP_0.csv', numSequences=2, elementsPerSeq=1, 
                  numRepeats=20)
  
  _generateCategory('category_SP_1.csv', numSequences=50, elementsPerSeq=1, 
                  numRepeats=20)
  
  _generateCategory('category_TP_0.csv', numSequences=2, elementsPerSeq=5, 
                  numRepeats=30)
  
  _generateCategory('category_TP_1.csv', numSequences=10, elementsPerSeq=5, 
                  numRepeats=20)

  _generateOverlapping('category_hub_TP_0.csv', numSequences=10, elementsPerSeq=5, 
                  numRepeats=20, hub=[0,1], hubOffset=1, resets=False)
  
  
  
  # Generate the scalar field datasets
  _generateScalar('scalar_SP_0.csv', numSequences=2, elementsPerSeq=1, 
                  numRepeats=20, stepSize=0.1, resets=False)
  
  _generateScalar('scalar_TP_0.csv', numSequences=2, elementsPerSeq=5, 
                  numRepeats=20, stepSize=0.1, resets=False)
  
  _generateScalar('scalar_TP_1.csv', numSequences=10, elementsPerSeq=5, 
                  numRepeats=20, stepSize=0.1, resets=False)
  
  
  
  

