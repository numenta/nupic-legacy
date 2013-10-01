#!/usr/bin/env python

# ----------------------------------------------------------------------
#  Copyright (C) 2009, Numenta Inc. All rights reserved.
#
#  The information and source code contained herein is the
#  exclusive property of Numenta Inc. No part of this software
#  may be used, reproduced, stored or distributed in any form,
#  without explicit written authorization from Numenta Inc.
# ----------------------------------------------------------------------

from __future__ import division

import sys
import os
import time
import copy
import cPickle
import hotshot

import itertools as iter

import numpy
import numpy as np
from numpy import *

from nupic.bindings.math import Random
from nupic.bindings.algorithms import *

#---------------------------------------------------------------------------------

rgen = Random(43)

def cellsDiff(cell1, cell2):
  """Test that the two cell instances have the same segments and synapses."""
  result = True

  # Check that each cell has the same number of segments and synapses
  for c in xrange(cell1.nColumns()):
    if not result:
      break
    for i in xrange(cell1.nCellsPerCol()):
      if cell1.nSegmentsOnCell(c, i) != cell2.nSegmentsOnCell(c, i):
        print "Num segments different in cell:",c,i,
        print "numbers = ", cell1.nSegmentsOnCell(c, i), cell2.nSegmentsOnCell(c, i)
        result = False
        break
      else:
        c1 = cell1.getCell(c, i)
        c2 = cell2.getCell(c, i)
        for j in xrange(cell1.nSegmentsOnCell(c, i)):
          seg1 = c1.getSegment(j)
          seg2 = c2.getSegment(j)
          if seg1.size() != seg2.size():
            result = False
            break
          for k in xrange(seg1.size()):
            sourceCellIdx1 = seg1.getSrcCellIdx(k)
            sourceCellIdx2 = seg1.getSrcCellIdx(k)
            if sourceCellIdx1 != sourceCellIdx2:
              result = False
              break
            perm1 = seg1.getPermanence(k)
            perm2 = seg2.getPermanence(k)
            if perm1 != perm2:
              result = False
              break

  if result == True:
    print "TP's match"

  return result

#---------------------------------------------------------------------------------
def test_persistence(cells):
    """This test will pickle the cells instance, unpickle it, and test
    to ensure the unpickled instance is identical to the pre-pickled version."""

    print 'Testing pickling'
    cPickle.dump(cells, open('test.pkl', 'wb'))
    cells.saveToFile('test2.bin')
    cells2 = cPickle.load(open('test.pkl'))

    # Test all public attributes of Cells4 that should get pickled
    for f1,f2 in zip(dir(cells), dir(cells2)):
        if f1[0] != '_' and f1 not in ['initialize', 'setStatePointers',
                                       'getStates', 'rebuildOutSynapses']:
            ff1,ff2 = getattr(cells, f1), getattr(cells, f2)
            try:
                r1,r2 = ff1(),ff2()
                print 'Calling', f1, ':', r1, r2
                if r1 != r2:
                    print 'Error'
                    sys.exit(-1)
            except:
                #print f, 'failed'
                pass

    # Ensure that the cells are identical
    assert cellsDiff(cells, cells2) == True

    print 'pickling ok'
    os.unlink('test.pkl')

    # Now try the Cells4.saveToFile method.
    cPickle.dump(cells, open('test.pkl', 'wb'))
    cells.saveToFile('test2.bin')
    cells2 = Cells4()
    cells2.loadFromFile('test2.bin')

    assert cellsDiff(cells, cells2) == True

    # Test all public attributes of Cells4 that should get pickled
    for f1,f2 in zip(dir(cells), dir(cells2)):
        if f1[0] != '_' and f1 not in ['initialize', 'setStatePointers',
                                       'getStates', 'rebuildOutSynapses']:
            ff1,ff2 = getattr(cells, f1), getattr(cells, f2)
            try:
                r1,r2 = ff1(),ff2()
                print 'Calling', f1, ':', r1, r2
                if r1 != r2:
                    print 'Error'
                    sys.exit(-1)
            except:
                #print f, 'failed'
                pass

    # Ensure that the cells are identical
    assert cellsDiff(cells, cells2) == True

    print 'pickling ok'
    os.unlink('test2.bin')

#---------------------------------------------------------------------------------
def test_1():

    nCols = 8
    nCellsPerCol = 4
    activationThreshold = 2
    minThreshold = 1
    newSynapseCount = 2
    segUpdateValidDuration = 2
    permInitial = .5
    permConnected = .8
    permHysteresis = .1
    permMax = 1.0
    permDec = .1
    permInc = .15
    globalDecay = .2
    doPooling = True

    activeStateT = numpy.zeros((nCols, nCellsPerCol), dtype='int8')
    activeStateT1 = numpy.zeros((nCols, nCellsPerCol), dtype='int8')
    predictedStateT = numpy.zeros((nCols, nCellsPerCol), dtype='int8')
    predictedStateT1 = numpy.zeros((nCols, nCellsPerCol), dtype='int8')
    colConfidenceT = numpy.zeros(nCols, dtype='float32')
    colConfidenceT1 = numpy.zeros(nCols, dtype='float32')
    confidenceT = numpy.zeros((nCols, nCellsPerCol), dtype='float32')
    confidenceT1 = numpy.zeros((nCols, nCellsPerCol), dtype='float32')

    cells = Cells4(nCols,
                   nCellsPerCol,
                   activationThreshold,
                   minThreshold,
                   newSynapseCount,
                   segUpdateValidDuration,
                   permInitial,
                   permConnected,
                   permHysteresis,
                   permMax,
                   permDec,
                   permInc,
                   globalDecay,
                   doPooling)

    cells.setStatePointers(activeStateT, activeStateT1,
                           predictedStateT, predictedStateT1,
                           colConfidenceT, colConfidenceT1,
                           confidenceT, confidenceT1)

    #---------------------------------------------------------------------------------
    print 'Testing accessors'
    for f in dir(cells):
        if f[0] != '_' and f not in ['initialize', 'setStatePointers', 'getStates']:
            ff = getattr(cells, f)
            try:
                r = ff()
                print 'Calling', f, ':', r
            except:
                #print f, 'failed'
                pass


    #---------------------------------------------------------------------------------
    test_persistence(cells)

#---------------------------------------------------------------------------------
def test_learn():

    # Make sure we set non-default parameters so we can test persistence

    nCols = 8
    nCellsPerCol = 4
    activationThreshold = 1
    minThreshold = 1
    newSynapseCount = 2
    segUpdateValidDuration = 2
    permInitial = .5
    permConnected = .8
    permHysteresis = .1
    permMax = 1.0
    permDec = .1
    permInc = .2
    globalDecay = .05
    doPooling = True
    pamLength = 2
    maxAge = 3

    activeStateT = numpy.zeros((nCols, nCellsPerCol), dtype='uint32')
    activeStateT1 = numpy.zeros((nCols, nCellsPerCol), dtype='uint32')
    predictedStateT = numpy.zeros((nCols, nCellsPerCol), dtype='uint32')
    predictedStateT1 = numpy.zeros((nCols, nCellsPerCol), dtype='uint32')
    colConfidenceT = numpy.zeros(nCols, dtype='float32')
    colConfidenceT1 = numpy.zeros(nCols, dtype='float32')
    confidenceT = numpy.zeros((nCols, nCellsPerCol), dtype='float32')
    confidenceT1 = numpy.zeros((nCols, nCellsPerCol), dtype='float32')

    cells = Cells4(nCols,
                   nCellsPerCol,
                   activationThreshold,
                   minThreshold,
                   newSynapseCount,
                   segUpdateValidDuration,
                   permInitial,
                   permConnected,
                   permHysteresis,
                   permMax,
                   permDec,
                   permInc,
                   globalDecay,
                   doPooling,
                   42)

    cells.setStatePointers(activeStateT, activeStateT1,
                           predictedStateT, predictedStateT1,
                           colConfidenceT, colConfidenceT1,
                           confidenceT, confidenceT1)
    cells.setPamLength(pamLength)
    cells.setMaxAge(maxAge)
    cells.setMaxInfBacktrack(4)
    cells.setVerbosity(4)

    for i in xrange(nCols):
        for j in xrange(nCellsPerCol):
            print "Adding segment: ",i,j,[((i+1)%nCols, (j+1)%nCellsPerCol)]
            cells.addNewSegment(i,j,True if j % 2 == 0 else False,
                                [((i+1)%nCols, (j+1)%nCellsPerCol)])

    for i in xrange(10):
        x = numpy.zeros(nCols, dtype='uint32')
        rgen.initializeUInt32Array(x, 2)
        print "Input:",x
        y = cells.compute(x, True, True)

    cells.rebuildOutSynapses()

    test_persistence(cells)

    for i in xrange(100):

      x = numpy.zeros(nCols, dtype='uint32')
      rgen.initializeUInt32Array(x, 2)
      y = cells.compute(x, True, False)

    test_persistence(cells)

#---------------------------------------------------------------------------------
if __name__=='__main__':

  #test_1()
    test_learn()
