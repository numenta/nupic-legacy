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
import random
import datetime
from optparse import OptionParser

from nupic.data.file_record_stream import FileRecordStream



def _generateSimple(filename="simple.csv", numSequences=1, elementsPerSeq=3, 
                    numRepeats=10):
  """ Generate a simple dataset. This contains a bunch of non-overlapping
  sequences. 
  
  At the end of the dataset, we introduce missing records so that test
  code can insure that the model didn't get confused by them. 
  
  Parameters:
  ----------------------------------------------------
  filename:       name of the file to produce, including extension. It will
                  be created in a 'datasets' sub-directory within the 
                  directory containing this script. 
  numSequences:   how many sequences to generate
  elementsPerSeq: length of each sequence
  numRepeats:     how many times to repeat each sequence in the output 
  """
  
  # Create the output file
  scriptDir = os.path.dirname(__file__)
  pathname = os.path.join(scriptDir, 'datasets', filename)
  print "Creating %s..." % (pathname)
  fields = [('timestamp', 'datetime', 'T'), 
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
  
  # Put 1 hour between each record
  timestamp = datetime.datetime(year=2012, month=1, day=1, hour=0, minute=0,
                                second=0)
  timeDelta = datetime.timedelta(hours=1)
  
  # Write out the sequences without missing records
  for seqIdx in seqIdxs:
    seq = sequences[seqIdx]
    for x in seq:
      outFile.appendRecord([timestamp, str(x), x])
      timestamp += timeDelta
      
  # Now, write some out with missing records
  for seqIdx in seqIdxs:
    seq = sequences[seqIdx]
    for i,x in enumerate(seq):
      if i != 1:
        outFile.appendRecord([timestamp, str(x), x])
      timestamp += timeDelta
  for seqIdx in seqIdxs:
    seq = sequences[seqIdx]
    for i,x in enumerate(seq):
      if i != 1:
        outFile.appendRecord([timestamp, str(x), x])
      timestamp += timeDelta

  # Write out some more of the sequences *without* missing records
  for seqIdx in seqIdxs:
    seq = sequences[seqIdx]
    for x in seq:
      outFile.appendRecord([timestamp, str(x), x])
      timestamp += timeDelta
      
  

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
  _generateSimple('simple_0.csv', numSequences=1, elementsPerSeq=3, 
                  numRepeats=10)
  
