# Copyright 2014 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""
## @file
This file generates data for the PCA/KNN classifier tests
"""

import logging
import numpy

LOGGER = logging.getLogger(__name__)



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
    for _j in range(numPatternsPerClass):
      data0[c] = pt+5*numpy.random.random((numDims))
      class0[c] = i
      c += 1

  if 0: # Change this to visualize the output
    import pylab
    pylab.ion()
    pylab.figure()
    _u, _s, vt = pylab.svd(data0[:numPatterns])
    tmp = numpy.zeros((numPatterns, 2))
    for i in range(numPatterns):
      tmp[i] = numpy.dot(vt, data0[i])[:2]
    pylab.scatter(tmp[:, 0], tmp[:, 1])

  ind = numpy.random.permutation(numPatterns + numTests)
  train_data = data0[ind[:numPatterns]]
  train_class = class0[ind[:numPatterns]]
  test_data = data0[ind[numPatterns:]]
  test_class = class0[ind[numPatterns:]]
  
  return train_data, train_class, test_data, test_class
