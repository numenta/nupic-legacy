#!/usr/bin/env python

# ----------------------------------------------------------------------
#  Copyright (C) 2007 Numenta Inc. All rights reserved.
#
#  The information and source code contained herein is the
#  exclusive property of Numenta Inc. No part of this software
#  may be used, reproduced, stored or distributed in any form,
#  without explicit written authorization from Numenta Inc.
# ----------------------------------------------------------------------

"""
## @file
This file defines the k Nearest Neighbor classifier node.
"""

import numpy
import logging

LOGGER = logging.getLogger(__name__)

#---------------------------------------------------------------------------------
def generate(numDims, numClasses, k, numPatternsPerClass,
             numPatterns, numTests, numSVDSamples, keep):

  LOGGER.info('N dims=%s', numDims)
  LOGGER.info('N classes=%s', numClasses)
  LOGGER.info('k=%s', k)
  LOGGER.info('N vectors per class=%s', numPatternsPerClass)
  LOGGER.info('N training vectors=%s', numPatterns)
  LOGGER.info('N test vectors=%s', numTests)
  LOGGER.info('N SVD samples=%s', numSVDSamples)
  LOGGER.info('N reduced dims=%s', int(keep*numDims))


  LOGGER.info('Generating data')

  numpy.random.seed(42)
  data0 = numpy.zeros((numPatterns + numTests, numDims))
  class0 = numpy.zeros((numPatterns + numTests), dtype='int')
  c = 0

  for i in range(numClasses):
    pt = 5*i*numpy.ones((numDims))
    for j in range(numPatternsPerClass):
      data0[c] = pt+5*numpy.random.random((numDims))
      class0[c] = i; c += 1

  if 0:
    import pylab
    pylab.ion()
    pylab.figure()
    u,s,vt = pylab.svd(data0[:numPatterns])
    tmp = numpy.zeros((numPatterns, 2))
    for i in range(numPatterns):
      tmp[i] = numpy.dot(vt, data0[i])[:2]
    pylab.scatter(tmp[:,0], tmp[:,1])

  ind = numpy.random.permutation(numPatterns + numTests)
  train_data = data0[ind[:numPatterns]]
  train_class = class0[ind[:numPatterns]]
  test_data = data0[ind[numPatterns:]]
  test_class = class0[ind[numPatterns:]]

  return train_data, train_class, test_data, test_class


#---------------------------------------------------------------------------------