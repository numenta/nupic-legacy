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
from nupic.research.TP import TP
from nupic.research.TP10X2 import TP10X2
from nupic.research import fdrutilities as fdrutils

#---------------------------------------------------------------------------------
VERBOSITY = 0 # how chatty the unit tests should be
SEED = 12     # the random seed used throughout
LEARNING_ITERATIONS = 500
INFER_ITERATIONS=100

rgen = Random(SEED) # always call this rgen, NOT random

allMethods = "random zeroth last all lots"
allMethodsList = ["random", "zeroth", "last", "all", "lots"]

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

  print "Testing Trivial Predictors"


  for baseclass in TP, TP10X2:
    print "Testing trivial predictors in class %s" % baseclass

    #--------------------------------------------------------------------------------
    # Create TP object with no trivial predictors
    tp = baseclass(numberOfCols=50,
            seed=SEED, verbosity = VERBOSITY,
            trivialPredictionMethods="")

    assert tp.trivialPredictor is None

    #--------------------------------------------------------------------------------
    # Create TP object with all predictors
    tp = baseclass(numberOfCols=50,
            seed=SEED, verbosity = VERBOSITY,
            trivialPredictionMethods=allMethods)

    assert tp.trivialPredictor is not None
    assert set(tp.trivialPredictor.methods) == set(allMethodsList)


    print "TrivialPredictor creation ok"

    #--------------------------------------------------------------------------------
    # Save and reload
    pickle.dump(tp, open("test_tptrivial.pkl", "wb"))
    tp2 = pickle.load(open("test_tptrivial.pkl"))

    assert tp2.trivialPredictor.__dict__.keys() == tp.trivialPredictor.__dict__.keys()
    # Deep comparison is hard; punt for now

    assert tp2.numberOfCols == 50
    assert tp2.trivialPredictor.numberOfCols == 50

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
    assert abs(tp.trivialPredictor.averageDensity - density) < 0.01

    print "Learning completed. t = %.1f seconds" % (time.time() - t)

    #--------------------------------------------------------------------------------
    # Save and reload after learning
    print "Pickling and unpickling"
    tp.reset()
    pickle.dump(tp, open("test_tptrivial.pkl", "wb"))
    tp2 = pickle.load(open("test_tptrivial.pkl"))

    assert tp.trivialPredictor.averageDensity == tp2.trivialPredictor.averageDensity
    assert (tp.trivialPredictor.columnCount == tp2.trivialPredictor.columnCount).all()
    totalColumns = tp.trivialPredictor.columnCount.sum()
    print "Number of columns seen during learning: %d" % totalColumns
    assert totalColumns == LEARNING_ITERATIONS * int(density*tp.numberOfCols)

    ##--------------------------------------------------------------------------------
    ## Infer

    # Infer with single presentation
    tp.collectStats = True
    tp.reset()
    tp.resetStats()
    for i in xrange(INFER_ITERATIONS):
      x = getPattern(tp.numberOfCols, int(density*tp.numberOfCols))
      y = tp.infer(x)

    # Make sure we get all stats
    print "Results for single presentation:"
    stats = tp.getStats()
    assert tp.getStats()['nPredictions'] == INFER_ITERATIONS - tp.burnIn

    for m in allMethodsList:
      key = "tr_%s" % m
      assert key in stats
      print "Prediction score for method %s: %f" % (m, stats["tr_%s" % m])
    print
    #for key in ["tr_random", "tr_zeroth", "tr_last", "tr_lots"]:
    #  assert (stats[key] != 0) and (abs(stats[key]) < 0.05)
    assert stats["tr_all"] < 0.1

    # Infer with two presentations
    tp.reset()
    tp.resetStats()
    tp.collectStats = True
    for i in xrange(INFER_ITERATIONS):
      x = getPattern(tp.numberOfCols, int(density*tp.numberOfCols))
      y = tp.infer(x)
      y = tp.infer(x)

    # Check predictions
    print "Results for double presentation:"
    stats = tp.getStats()
    assert tp.getStats()['nPredictions'] == INFER_ITERATIONS*2 - tp.burnIn
    for m in allMethodsList:
      print "Prediction score for method %s: %f" % (m, stats["tr_%s" % m])

    #for key in ["tr_random", "tr_zeroth", "tr_lots"]:
    #  assert (stats[key] != 0) and (abs(stats[key]) < 0.05)
    assert stats["tr_all"] < 0.1
    assert stats["tr_last"] > 0.4

    print "Done with testing for %s" % tp
    print

  print "TrivialPredictor  basicTest ok"



#---------------------------------------------------------------------------------
if __name__=="__main__":
  basicTest()
  pass
