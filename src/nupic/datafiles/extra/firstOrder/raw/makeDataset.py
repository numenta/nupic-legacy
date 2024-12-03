# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""

Generate artificial datasets

"""

import numpy
from nupic.data.file import File


def createFirstOrderModel(numCategories=5, alpha=0.5):
  
  categoryList = ['cat%02d' % i for i in range(numCategories)]
  
  initProbability = numpy.ones(numCategories)/numCategories
  
  transitionTable = numpy.random.dirichlet(alpha=[alpha]*numCategories,
                                           size=numCategories)
  
  return categoryList, initProbability, transitionTable


def generateFirstOrderData(model, numIterations=10000, seqLength=5,
                           resets=True, suffix='train'):
  
  print "Creating %d iteration file with seqLength %d" % (numIterations, seqLength)
  print "Filename", 
  categoryList, initProbability, transitionTable = model
  initProbability = initProbability.cumsum()
  transitionTable = transitionTable.cumsum(axis=1)
  
  outputFile = 'fo_%d_%d_%s.csv' % (numIterations, seqLength, suffix)
  print "Filename", outputFile
  fields = [('reset', 'int', 'R'), ('name', 'string', '')]
  o = File(outputFile, fields)
  
  seqIdx = 0
  rand = numpy.random.rand()
  catIdx = numpy.searchsorted(initProbability, rand)
  for i in xrange(numIterations):
    rand = numpy.random.rand()
    if seqIdx == 0 and resets:
      catIdx = numpy.searchsorted(initProbability, rand)
      reset  = 1
    else:
      catIdx = numpy.searchsorted(transitionTable[catIdx], rand)
      reset  = 0
      
    o.write([reset,categoryList[catIdx]])    
    seqIdx = (seqIdx+1)%seqLength
  
  o.close()

if __name__=='__main__':
  
  numpy.random.seed(1956)
  
  model = createFirstOrderModel()
  
  categoryList = model[0]
  categoryFile = open("categories.txt", 'w')
  for category in categoryList:
    categoryFile.write(category+'\n')
  categoryFile.close()
  
  #import pylab
  #pylab.imshow(model[2], interpolation='nearest')
  #pylab.show()
  
  for resets in [True, False]:
    for seqLength in [2, 10]:        
      for numIterations in [1000, 10000, 100000]:
      
        generateFirstOrderData(model,
                               numIterations=numIterations,
                               seqLength=seqLength,
                               resets=resets,
                               suffix='train_%s' % ('resets' if resets else 'noresets',))
    
      generateFirstOrderData(model, numIterations=10000, seqLength=seqLength,
                           resets=resets,
                           suffix='test_%s' % ('resets' if resets else 'noresets',))  
