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

import numpy

from nupic.data.file_record_stream import FileRecordStream



def _generateModel0(numCategories):
  """ Generate the initial, first order, and second order transition
  probabilities for 'model0'. For this model, we generate the following
  set of sequences:
  
  1-2-3   (4X)
  1-2-4   (1X)
  5-2-3   (1X)
  5-2-4   (4X)
  
  
  Parameters:
  ----------------------------------------------------------------------
  numCategories:      Number of categories
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


  Here is an example of some return values:
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

  # ===============================================================
  # Let's model the following:
  #  a-b-c (4X)
  #  a-b-d (1X)
  #  e-b-c (1X)
  #  e-b-d (4X)


  # --------------------------------------------------------------------
  # Initial probabilities, 'a' and 'e' equally likely
  initProb = numpy.zeros(numCategories)
  initProb[0] = 0.5
  initProb[4] = 0.5
  

  # --------------------------------------------------------------------
  # 1st order transitions
  # both 'a' and 'e' should lead to 'b'
  firstOrder = dict()
  for catIdx in range(numCategories):
    key = str([catIdx])
    probs = numpy.ones(numCategories) / numCategories
    if catIdx == 0 or catIdx == 4:
      probs.fill(0)
      probs[1] = 1.0    # lead only to b
    firstOrder[key] = probs
   
  # --------------------------------------------------------------------
  # 2nd order transitions
  # a-b should lead to c 80% and d 20%
  # e-b should lead to c 20% and d 80%
  secondOrder = dict()
  for firstIdx in range(numCategories):
    for secondIdx in range(numCategories):
      key = str([firstIdx, secondIdx])
      probs = numpy.ones(numCategories) / numCategories
      if key == str([0,1]):
        probs.fill(0)
        probs[2] = 0.80   # 'ab' leads to 'c' 80% of the time
        probs[3] = 0.20   # 'ab' leads to 'd' 20% of the time
      elif key == str([4,1]):
        probs.fill(0)
        probs[2] = 0.20   # 'eb' leads to 'c' 20% of the time
        probs[3] = 0.80   # 'eb' leads to 'd' 80% of the time
    
      secondOrder[key] = probs
  
  return (initProb, firstOrder, secondOrder, 3)



def _generateModel1(numCategories):
  """ Generate the initial, first order, and second order transition
  probabilities for 'model1'. For this model, we generate the following
  set of sequences:
  
  0-10-15 (1X)
  0-11-16 (1X)
  0-12-17 (1X)
  0-13-18 (1X)
  0-14-19 (1X)

  1-10-20 (1X)
  1-11-21 (1X)
  1-12-22 (1X)
  1-13-23 (1X)
  1-14-24 (1X)
  
  
  Parameters:
  ----------------------------------------------------------------------
  numCategories:      Number of categories
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


  Here is an example of some return values:
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
  # Initial probabilities, 0 and 1 equally likely
  initProb = numpy.zeros(numCategories)
  initProb[0] = 0.5
  initProb[1] = 0.5
  

  # --------------------------------------------------------------------
  # 1st order transitions
  # both 0 and 1 should lead to 10,11,12,13,14 with equal probability
  firstOrder = dict()
  for catIdx in range(numCategories):
    key = str([catIdx])
    probs = numpy.ones(numCategories) / numCategories
    if catIdx == 0 or catIdx == 1:
      indices = numpy.array([10,11,12,13,14])
      probs.fill(0)
      probs[indices] = 1.0    # lead only to b
      probs /= probs.sum()
    firstOrder[key] = probs
   
  # --------------------------------------------------------------------
  # 2nd order transitions
  # 0-10 should lead to 15
  # 0-11 to 16
  # ...
  # 1-10 should lead to 20
  # 1-11 shold lean to 21
  # ...
  secondOrder = dict()
  for firstIdx in range(numCategories):
    for secondIdx in range(numCategories):
      key = str([firstIdx, secondIdx])
      probs = numpy.ones(numCategories) / numCategories
      if key == str([0,10]):
        probs.fill(0)
        probs[15] = 1
      elif key == str([0,11]):
        probs.fill(0)
        probs[16] = 1
      elif key == str([0,12]):
        probs.fill(0)
        probs[17] = 1
      elif key == str([0,13]):
        probs.fill(0)
        probs[18] = 1
      elif key == str([0,14]):
        probs.fill(0)
        probs[19] = 1
    
      elif key == str([1,10]):
        probs.fill(0)
        probs[20] = 1
      elif key == str([1,11]):
        probs.fill(0)
        probs[21] = 1
      elif key == str([1,12]):
        probs.fill(0)
        probs[22] = 1
      elif key == str([1,13]):
        probs.fill(0)
        probs[23] = 1
      elif key == str([1,14]):
        probs.fill(0)
        probs[24] = 1
    
      secondOrder[key] = probs
  
  return (initProb, firstOrder, secondOrder, 3)



def _generateModel2(numCategories, alpha=0.25):
  """ Generate the initial, first order, and second order transition
  probabilities for 'model2'. For this model, we generate peaked random 
  transitions using dirichlet distributions. 
  
  Parameters:
  ----------------------------------------------------------------------
  numCategories:      Number of categories
  alpha:              Determines the peakedness of the transitions. Low alpha 
                      values (alpha=0.01) place the entire weight on a single 
                      transition. Large alpha values (alpha=10) distribute the 
                      evenly among all transitions. Intermediate values (alpha=0.5)
                      give a moderately peaked transitions. 
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
                          elements by the secondOrder table. None means infinite
                          length. 


  Here is an example of some return values for an intermediate alpha value:
  initProb:         [0.33, 0.33, 0.33]
  
  firstOrder:       {'[0]': [0.2, 0.7, 0.1],
                     '[1]': [0.1, 0.1, 0.8],
                     '[2]': [0.1, 0.0, 0.9]}
                     
  secondOrder:      {'[0,0]': [0.1, 0.0, 0.9],
                     '[0,1]': [0.0, 0.2, 0.8],
                     '[0,2]': [0.1, 0.8, 0.1],
                     ...
                     '[2,2]': [0.8, 0.2, 0.0]}
  """


  # --------------------------------------------------------------------
  # All initial probabilities, are equally likely
  initProb = numpy.ones(numCategories)/numCategories

  def generatePeakedProbabilities(lastIdx,
				  numCategories=numCategories, 
				  alpha=alpha):
    probs = numpy.random.dirichlet(alpha=[alpha]*numCategories)
    probs[lastIdx] = 0.0
    probs /= probs.sum()
    return probs 

  # --------------------------------------------------------------------
  # 1st order transitions
  firstOrder = dict()
  for catIdx in range(numCategories):
    key = str([catIdx])
    probs = generatePeakedProbabilities(catIdx) 
    firstOrder[key] = probs

  # --------------------------------------------------------------------
  # 2nd order transitions
  secondOrder = dict()
  for firstIdx in range(numCategories):
    for secondIdx in range(numCategories):
      key = str([firstIdx, secondIdx])
      probs = generatePeakedProbabilities(secondIdx) 
      secondOrder[key] = probs

  return (initProb, firstOrder, secondOrder, None)



def _generateFile(filename, numRecords, categoryList, initProb, 
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
                      first two. 
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
  fields = [('reset', 'int', 'R'), ('name', 'string', '')]
  outFile = FileRecordStream(filename, write=True, fields=fields)
  
  # --------------------------------------------------------------------
  # Convert the probabilitie tables into cumulative probabilities
  initCumProb = initProb.cumsum()
  
  firstOrderCumProb = dict()
  for (key,value) in firstOrderProb.iteritems():
    firstOrderCumProb[key] = value.cumsum()
    
  secondOrderCumProb = dict()
  for (key,value) in secondOrderProb.iteritems():
    secondOrderCumProb[key] = value.cumsum()
    

  # --------------------------------------------------------------------
  # Write out the sequences
  elementsInSeq = []
  numElementsSinceReset = 0
  maxCatIdx = len(categoryList) - 1
  for i in xrange(numRecords):

    # Generate a reset?
    if numElementsSinceReset == 0:
      reset = 1
    else:
      reset = 0
      
    # Pick the next element, based on how are we are into the 2nd order
    #   sequence. 
    rand = numpy.random.rand()
    if len(elementsInSeq) == 0:
      catIdx = numpy.searchsorted(initCumProb, rand)
    elif len(elementsInSeq) == 1:
      catIdx = numpy.searchsorted(firstOrderCumProb[str(elementsInSeq)], rand)
    elif (len(elementsInSeq) >=2) and \
                  (seqLen is None or len(elementsInSeq) < seqLen-numNoise):
      catIdx = numpy.searchsorted(secondOrderCumProb[str(elementsInSeq[-2:])], rand)
    else:   # random "noise"
      catIdx = numpy.random.randint(len(categoryList))
      
    # Write out the record
    catIdx = min(maxCatIdx, catIdx)
    outFile.appendRecord([reset,categoryList[catIdx]])    
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



def generate(model, filenameTrain, filenameTest, filenameCategory,
              numCategories=178, numTrainingRecords=1000,
              numTestingRecords=100, numNoise=5, resetsEvery=None):
  

  numpy.random.seed(41) 
  
  
  # =====================================================================
  # Create our categories and category file. 
  print "Creating %s..." % (filenameCategory)
  categoryList = ['cat%d' % i for i in range(1, numCategories+1)]
  categoryFile = open(filenameCategory, 'w')
  for category in categoryList:
    categoryFile.write(category+'\n')
  categoryFile.close()
  
  
  # ====================================================================
  # Generate the model
  if model == 'model0':
    (initProb, firstOrderProb, secondOrderProb, seqLen) = \
                                              _generateModel0(numCategories)
  elif model == 'model1':
    (initProb, firstOrderProb, secondOrderProb, seqLen) = \
                                              _generateModel1(numCategories)
  elif model == 'model2':
    (initProb, firstOrderProb, secondOrderProb, seqLen) = \
                                              _generateModel2(numCategories)
  else:
    raise RuntimeError("Unsupported model")
  
  
  # ====================================================================
  # Generate the training and testing files
  _generateFile(filename=filenameTrain, numRecords=numTrainingRecords,
                  categoryList=categoryList, initProb=initProb,
                  firstOrderProb=firstOrderProb, secondOrderProb=secondOrderProb,
                  seqLen=seqLen, numNoise=numNoise, resetsEvery=resetsEvery)
                  
  _generateFile(filename=filenameTest, numRecords=numTestingRecords,
                  categoryList=categoryList, initProb=initProb,
                  firstOrderProb=firstOrderProb, secondOrderProb=secondOrderProb,
                  seqLen=seqLen, numNoise=numNoise, resetsEvery=resetsEvery)
                  
                  
  
