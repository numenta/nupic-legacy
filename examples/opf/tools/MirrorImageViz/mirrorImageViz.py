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
# Author: Surabhi Gupta

import sys
import numpy as np
import matplotlib.pylab as pyl

def analyzeOverlaps(activeCoincsFile, encodingsFile, dataset):
  '''Mirror Image Visualization: Shows the encoding space juxtaposed against the
  coincidence space. The encoding space is the bottom-up sensory encoding and
  the coincidence space depicts the corresponding activation of coincidences in
  the SP. Hence, the mirror image visualization is a visual depiction of the
  mapping of SP cells to the input representations.
  
  Note:
  * The files spBUOut and sensorBUOut are assumed to be in the output format
  used for LPF experiment outputs.
  * BU outputs for some sample datasets are provided. Specify the name of the
  dataset as an option while running this script. 
  '''
  
  lines = activeCoincsFile.readlines()
  inputs = encodingsFile.readlines()
  w = len(inputs[0].split(' '))-1

  patterns = set([])
  encodings = set([])
  coincs = []    #The set of all coincidences that have won at least once
  reUsedCoincs = []
  
  firstLine = inputs[0].split(' ')
  size = int(firstLine.pop(0))
  spOutput = np.zeros((len(lines),40))
  inputBits = np.zeros((len(lines),w))
  print 'Total n:', size
  print 'Total number of records in the file:', len(lines), '\n'
  print 'w:', w
  
  count = 0
  for x in xrange(len(lines)):
    inputSpace = []     #Encoded representation for each input 
    
    spBUout = [int(z) for z in lines[x].split(' ')]  
    spBUout.pop(0)         #The first element of each row of spBUOut is the size of the SP 
    temp = set(spBUout)
    spOutput[x]=spBUout
    
    input = [int(z) for z in inputs[x].split(' ')]    
    input.pop(0)   #The first element of each row of sensorBUout is the size of the encoding space
    tempInput = set(input)
    inputBits[x]=input
    
    #Creating the encoding space 
    for m in xrange(size):
      if m in tempInput:
        inputSpace.append(m)
      else:
        inputSpace.append('|')  #A non-active bit
    
    repeatedBits = tempInput.intersection(encodings)    #Storing the bits that have been previously active
    reUsed = temp.intersection(patterns)  #Checking if any of the active cells have been previously active  
    
    #Dividing the coincidences into two difference categories. 
    if len(reUsed)==0:
      coincs.append((count,temp,repeatedBits,inputSpace, tempInput))  #Pattern no, active cells, repeated bits, encoding (full), encoding (summary)
    else:
      reUsedCoincs.append((count,temp,repeatedBits,inputSpace, tempInput))
    patterns=patterns.union(temp)   #Adding the active cells to the set of coincs that have been active at least once
    
    encodings = encodings.union(tempInput)
    count +=1
    
  overlap = {}
  overlapVal = 0

  seen = []
  seen = (printOverlaps(coincs, coincs, seen))
  print len(seen), 'sets of 40 cells'
  seen = printOverlaps(reUsedCoincs, coincs, seen)
  
  Summ=[]
  for z in coincs:
    c=0
    for y in reUsedCoincs:
      c += len(z[1].intersection(y[1]))
    Summ.append(c)
  print 'Sum: ', Summ
  
  for m in xrange(3):
    displayLimit = min(51, len(spOutput[m*200:]))
    if displayLimit>0:
      drawFile(dataset, np.zeros([len(inputBits[:(m+1)*displayLimit]),len(inputBits[:(m+1)*displayLimit])]), inputBits[:(m+1)*displayLimit], spOutput[:(m+1)*displayLimit], w, m+1)
    else: 
      print 'No more records to display'
  pyl.show()
  
def drawFile(dataset, matrix, patterns, cells, w, fnum):
  '''The similarity of two patterns in the bit-encoding space is displayed alongside
  their similarity in the sp-coinc space.'''
  score=0
  count = 0
  assert len(patterns)==len(cells)
  for p in xrange(len(patterns)-1):
    matrix[p+1:,p] = [len(set(patterns[p]).intersection(set(q)))*100/w for q in patterns[p+1:]]
    matrix[p,p+1:] = [len(set(cells[p]).intersection(set(r)))*5/2 for r in cells[p+1:]]
    
    score += sum(abs(np.array(matrix[p+1:,p])-np.array(matrix[p,p+1:])))
    count += len(matrix[p+1:,p])
  
  print 'Score', score/count
  
  fig = pyl.figure(figsize = (10,10), num = fnum)
  pyl.matshow(matrix, fignum = fnum)
  pyl.colorbar()
  pyl.title('Coincidence Space', verticalalignment='top', fontsize=12)
  pyl.xlabel('The Mirror Image Visualization for '+dataset, fontsize=17)
  pyl.ylabel('Encoding space', fontsize=12)
  
def printOverlaps(comparedTo, coincs, seen):
  """ Compare the results and return True if success, False if failure
    
  Parameters:
  --------------------------------------------------------------------
  coincs:               Which cells are we comparing?
  comparedTo:           The set of 40 cells we being compared to (they have no overlap with seen)
  seen:                 Which of the cells we are comparing to have already been encountered.
                        This helps glue together the unique and reused coincs
  """
  inputOverlap = 0
  cellOverlap = 0
  for y in comparedTo:
    closestInputs = []
    closestCells = []
    if len(seen)>0:
      inputOverlap = max([len(seen[m][1].intersection(y[4])) for m in xrange(len(seen))])
      cellOverlap = max([len(seen[m][0].intersection(y[1])) for m in xrange(len(seen))])
      for m in xrange( len(seen) ):
        if len(seen[m][1].intersection(y[4]))==inputOverlap:
          closestInputs.append(seen[m][2])
        if len(seen[m][0].intersection(y[1]))==cellOverlap:
          closestCells.append(seen[m][2])
    seen.append((y[1], y[4], y[0]))
        
    print 'Pattern',y[0]+1,':',' '.join(str(len(z[1].intersection(y[1]))).rjust(2) for z in coincs),'input overlap:', inputOverlap, ';', len(closestInputs), 'closest encodings:',','.join(str(m+1) for m in closestInputs).ljust(15), \
    'cell overlap:', cellOverlap, ';', len(closestCells), 'closest set(s):',','.join(str(m+1) for m in closestCells)
  
  return seen



if __name__=='__main__': 
  if len(sys.argv)<2:   #Use basil if no dataset specified
    print ('Input files required. Read documentation for details.')
  else:
    dataset = sys.argv[1]
    activeCoincsPath = dataset+'/'+dataset+'_spBUOut.txt' 
    encodingsPath = dataset+'/'+dataset+'_sensorBUOut.txt'
    activeCoincsFile=open(activeCoincsPath, 'r')
    encodingsFile=open(encodingsPath, 'r')
  analyzeOverlaps(activeCoincsFile, encodingsFile, dataset)
