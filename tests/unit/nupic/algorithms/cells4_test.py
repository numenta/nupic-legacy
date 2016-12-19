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

"""Unit tests for Cells4."""

import cPickle as pickle
import os

import numpy
import unittest2 as unittest

from nupic.bindings.math import Random
from nupic.bindings.algorithms import Cells4

_RGEN = Random(43)



class Cells4Test(unittest.TestCase):


  @staticmethod
  def _cellsDiff(cell1, cell2):
    """Test that the two cell instances have the same segments and synapses."""
    result = True
  
    # Check that each cell has the same number of segments and synapses
    for c in xrange(cell1.nColumns()):
      if not result:
        break
      for i in xrange(cell1.nCellsPerCol()):
        if cell1.nSegmentsOnCell(c, i) != cell2.nSegmentsOnCell(c, i):
          print "Num segments different in cell:", c, i,
          print "numbers = ", cell1.nSegmentsOnCell(c, i), \
              cell2.nSegmentsOnCell(c, i)
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


  def _testPersistence(self, cells):
    """This will pickle the cells instance, unpickle it, and test to ensure
    the unpickled instance is identical to the pre-pickled version.
    """
    pickle.dump(cells, open("test.pkl", "wb"))
    cells.saveToFile("test2.bin")
    cells2 = pickle.load(open("test.pkl"))

    # Test all public attributes of Cells4 that should get pickled
    for f1, f2 in zip(dir(cells), dir(cells2)):
      if f1[0] != "_" and f1 not in ["initialize", "setStatePointers",
                                     "getStates", "rebuildOutSynapses"]:
        ff1, ff2 = getattr(cells, f1), getattr(cells, f2)
        try:
          r1, r2 = ff1(), ff2()
          resultsEqual = (r1 == r2)
        except (NotImplementedError, RuntimeError, TypeError, ValueError):
          continue
        self.assertTrue(resultsEqual, "Cells do not match.")

    # Ensure that the cells are identical
    self.assertTrue(self._cellsDiff(cells, cells2))

    os.unlink("test.pkl")

    # Now try the Cells4.saveToFile method.
    pickle.dump(cells, open("test.pkl", "wb"))
    cells.saveToFile("test2.bin")
    cells2 = Cells4()
    cells2.loadFromFile("test2.bin")

    self.assertTrue(self._cellsDiff(cells, cells2))

    # Test all public attributes of Cells4 that should get pickled
    for f1, f2 in zip(dir(cells), dir(cells2)):
      if f1[0] != "_" and f1 not in ["initialize", "setStatePointers",
                                     "getStates", "rebuildOutSynapses"]:
        ff1, ff2 = getattr(cells, f1), getattr(cells, f2)
        try:
          r1, r2 = ff1(), ff2()
          resultsEqual = (r1 == r2)
        except (NotImplementedError, RuntimeError, TypeError, ValueError):
          continue
        self.assertTrue(resultsEqual, "Cells do not match.")

    # Ensure that the cells are identical
    self.assertTrue(self._cellsDiff(cells, cells2))

    os.unlink("test2.bin")


  def testLearn(self):
    # Make sure we set non-default parameters so we can test persistence
    nCols = 8
    nCellsPerCol = 4
    activationThreshold = 1
    minThreshold = 1
    newSynapseCount = 2
    segUpdateValidDuration = 2
    permInitial = .5
    permConnected = .8
    permMax = 1.0
    permDec = .1
    permInc = .2
    globalDecay = .05
    doPooling = True
    pamLength = 2
    maxAge = 3

    activeStateT = numpy.zeros((nCols, nCellsPerCol), dtype="uint32")
    activeStateT1 = numpy.zeros((nCols, nCellsPerCol), dtype="uint32")
    predictedStateT = numpy.zeros((nCols, nCellsPerCol), dtype="uint32")
    predictedStateT1 = numpy.zeros((nCols, nCellsPerCol), dtype="uint32")
    colConfidenceT = numpy.zeros(nCols, dtype="float32")
    colConfidenceT1 = numpy.zeros(nCols, dtype="float32")
    confidenceT = numpy.zeros((nCols, nCellsPerCol), dtype="float32")
    confidenceT1 = numpy.zeros((nCols, nCellsPerCol), dtype="float32")

    cells = Cells4(nCols,
                   nCellsPerCol,
                   activationThreshold,
                   minThreshold,
                   newSynapseCount,
                   segUpdateValidDuration,
                   permInitial,
                   permConnected,
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
        print "Adding segment: ", i, j, [((i + 1) % nCols,
                                          (j + 1) % nCellsPerCol)]
        cells.addNewSegment(i, j, True if j % 2 == 0 else False,
                            [((i + 1) % nCols, (j + 1) % nCellsPerCol)])

    for i in xrange(10):
      x = numpy.zeros(nCols, dtype="uint32")
      _RGEN.initializeUInt32Array(x, 2)
      print "Input:", x
      cells.compute(x, True, True)

    cells.rebuildOutSynapses()

    self._testPersistence(cells)

    for i in xrange(100):
      x = numpy.zeros(nCols, dtype="uint32")
      _RGEN.initializeUInt32Array(x, 2)
      cells.compute(x, True, False)

    self._testPersistence(cells)



if __name__ == "__main__":
  unittest.main()
