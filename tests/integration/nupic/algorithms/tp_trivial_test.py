#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

"""
This file test that we can instantiate and call the TP10X class.
"""

import sys
import time
import numpy
from numpy import *
import pickle
import cPickle

import random
random.seed(42)
numpy.random.seed(42)

from nupic.bindings.math import Random
from nupic.research.TPTrivial import TPTrivial
from nupic.research import fdrutilities as fdrutils

#---------------------------------------------------------------------------------
VERBOSITY = 0 # how chatty the unit tests should be
SEED = 12     # the random seed used throughout
LEARNING_ITERATIONS = 500
INFER_ITERATIONS = 100

rgen = Random(SEED) # always call this rgen, NOT random

def getPattern(numberOfCols, activity):
  x = numpy.zeros(numberOfCols, dtype='uint32')
  coinc = numpy.array(random.sample(xrange(numberOfCols),
                activity), dtype=numpy.uint32)
  x[coinc] = 1
  return x

#---------------------------------------------------------------------------------
# Basic test (creation, pickling, basic run of learning and inference)
#---------------------------------------------------------------------------------
def basicTest():

  print "Testing TPTrivial"

  #--------------------------------------------------------------------------------
  # Create TP object
  tp = TPTrivial(numberOfCols=50,
          seed=SEED, verbosity = VERBOSITY)

  print "TPTrivial creation ok"

  #--------------------------------------------------------------------------------
  # Save and reload
  pickle.dump(tp, open("test_tptrivial.pkl", "wb"))
  tp2 = pickle.load(open("test_tptrivial.pkl"))

  assert tp2.numberOfCols == 50

  print "Save/load ok"

  #--------------------------------------------------------------------------------
  # Learn
  t = time.time()
  density = 0.2
  trainingSet = []
  for i in xrange(LEARNING_ITERATIONS):
    x = getPattern(tp.numberOfCols, int(density*tp.numberOfCols))
    y = tp.learn(x)
    trainingSet.append(x)

  # Ensure it estimated a reasonable density
  assert abs(tp.averageDensity - density) < 0.01

  print "Learning completed. t = %.1f seconds" % (time.time() - t)

  #--------------------------------------------------------------------------------
  # Save and reload after learning
  print "Pickling and unpickling"
  tp.reset()
  pickle.dump(tp, open("test_tptrivial.pkl", "wb"))
  tp2 = pickle.load(open("test_tptrivial.pkl"))

  assert tp.averageDensity == tp2.averageDensity

  ##--------------------------------------------------------------------------------
  ## Infer
  print "Running inference with 'random' prediction"

  tp.reset()
  tp.predictionMethod = "random"
  tp.collectStats = True
  for i in xrange(INFER_ITERATIONS):
    x = getPattern(tp.numberOfCols, int(density*tp.numberOfCols))
    y = tp.infer(x)

  # Ensure we predicted something
  print tp.getStats()
  print "AVERAGE2 random: " + str(tp.getStats()['predictionScoreAvg2'])
  assert tp.getStats()['predictionScoreAvg2'] < 0
  assert tp.getStats()['nPredictions'] == INFER_ITERATIONS - tp.burnIn

  ##--------------------------------------------------------------------------------
  ## Infer
  print "Running inference with 'zeroth' prediction"

  tp.reset()
  tp.resetStats()
  tp.predictionMethod = "zeroth"
  tp.collectStats = True
  for i in xrange(INFER_ITERATIONS):
    x = getPattern(tp.numberOfCols, int(density*tp.numberOfCols))
    y = tp.infer(x)

  # Ensure we predicted something
  print "AVERAGE2 zeroth: " + str(tp.getStats()['predictionScoreAvg2'])
  assert tp.getStats()['predictionScoreAvg2'] < 0
  assert tp.getStats()['nPredictions'] == INFER_ITERATIONS - tp.burnIn

  ##--------------------------------------------------------------------------------
  ## Infer
  print "Running inference with 'all' prediction"

  tp.reset()
  tp.resetStats()
  tp.predictionMethod = "all"
  tp.collectStats = True
  for i in xrange(INFER_ITERATIONS):
    x = getPattern(tp.numberOfCols, int(density*tp.numberOfCols))
    y = tp.infer(x)

  # Ensure we predicted something
  print "AVERAGE2 all: " + str(tp.getStats()['predictionScoreAvg2'])
  assert tp.getStats()['predictionScoreAvg2'] < 0
  assert tp.getStats()['nPredictions'] == INFER_ITERATIONS - tp.burnIn

  ##--------------------------------------------------------------------------------
  ## Infer
  print "Running inference with 'last' prediction"

  tp.reset()
  tp.resetStats()
  tp.predictionMethod = "last"
  tp.collectStats = True
  for i in xrange(INFER_ITERATIONS):
    x = getPattern(tp.numberOfCols, int(density*tp.numberOfCols))
    # Feed the same input twice in a row. This way "last" will have a high
    # prediction score - it will be correct 50% of the time
    y = tp.infer(x)
    y = tp.infer(x)

  # Ensure we predicted something
  print "AVERAGE2: " + str(tp.getStats()['predictionScoreAvg2'])
  assert tp.getStats()['predictionScoreAvg2'] > 0.2
  assert tp.getStats()['nPredictions'] == INFER_ITERATIONS*2 - tp.burnIn


  print "TPTrivial basicTest ok"



#---------------------------------------------------------------------------------
if __name__=="__main__":
  basicTest()
  pass
