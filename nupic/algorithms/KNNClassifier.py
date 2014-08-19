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
## @file
This file contains k Nearest Neighbor classifier.
"""

import numpy

from nupic.bindings.math import (NearestNeighbor, min_score_per_category)

g_debugPrefix = "KNN"

##########################################################################
def _labeledInput(activeInputs, cellsPerCol=32):
  """Print the list of [column, cellIdx] indices for each of the active
  cells in activeInputs. """


  if cellsPerCol == 0:
    cellsPerCol = 1
  cols = activeInputs.size / cellsPerCol
  activeInputs = activeInputs.reshape(cols, cellsPerCol)
  (cols, cellIdxs) = activeInputs.nonzero()

  if len(cols) == 0:
    return "NONE"

  items = ["(%d): " % (len(cols))]
  prevCol = -1
  for (col,cellIdx) in zip(cols, cellIdxs):
    if col != prevCol:
      if prevCol != -1:
        items.append("] ")
      items.append("Col %d: [" % (col))
      prevCol = col

    items.append("%d," % (cellIdx))

  items.append("]")
  return ' '.join(items)

KNNCLASSIFIER_VERSION = 1


##########################################################################
class KNNClassifier(object):
  """k nearest neighbor classifier"""

  def __init__(self,
      k=1,                       # The K in KNN
      distanceNorm=2.0,          # By default, we use L2 norm as distance metric
      distanceMethod='norm',     # The method used to compute distance. See
                                 # below for options
      distThreshold=0,           # Distance threshold for entering patterns
      doBinarization=False,      # Inputs are binarized.
      binarizationThreshold=0.5, # Threshold for binarization of inputs.
      useSparseMemory=True,      # Use sparse memory matrix
      sparseThreshold=0.1,       # Anything below this threshold is considered zero.
      relativeThreshold=False,   # Multiply the threshold by the max input value
      numWinners=0,              # Only numWinners elements of input are stored
      numSVDSamples=None,        # Number of samples to do SVD after
      numSVDDims=None,           # % of the dims to keep after SVD
      fractionOfMax=None,        # The cut-off fraction in relation to the largest singular value when adaptive dimension selection is used
      verbosity=0,               # verbosity level (0: none, increasing integers
                                 #  providing increasing levels of verbosity
      maxStoredPatterns=-1,      # Limits the maximum number of the training
                                 # patterns stored. When KNN learns in a fixed
                                 # capacity mode, the unused patterns are
                                 # deleted once the number of stored patterns
                                 # is greater than maxStoredPatterns
      replaceDuplicates=False,   # if true, during learning, replace existing
                                 # entries that match exactly, even if
                                 # distThreshold is 0.
      cellsPerCol=0,             # if >=1, then only store the start cell in
                                 # any columns which are bursting.

    ):
    """ Constructor for the kNN classifier.

    distanceMethod -- method used to compute distance. Possible options are:
      'norm': When distanceNorm is 2, this is the euclidean distance,
              When distanceNorm is 1, this is the manhattan distance
              In general: sum(abs(x-proto) ^ distanceNorm) ^ (1/distanceNorm)
      'rawOverlap': Only appropriate when inputs are binary. This computes:
              (width of the input) - (# bits of overlap between input
              and prototype).
      'pctOverlapOfLarger': Only appropriate for binary inputs. This computes
              1.0 - (# bits overlap between input and prototype) /
                      max(# bits in input, # bits in prototype)
      'pctOverlapOfProto': Only appropriate for binary inputs. This computes
              1.0 - (# bits overlap between input and prototype) /
                      (# bits in prototype)

    distThreshold -- Distance Threshold. If a pattern that is less than
      distThreshold apart from the input pattern already exists in the kNN's
      memory, then the input pattern is not added to kNN's memory.
    """
    self.version = KNNCLASSIFIER_VERSION

    self.k = k
    self.distanceNorm = distanceNorm
    assert (distanceMethod in ('norm', 'rawOverlap', 'pctOverlapOfLarger',
                               'pctOverlapOfProto'))
    self.distanceMethod = distanceMethod
    self.distThreshold = distThreshold
    self.doBinarization = doBinarization
    self.binarizationThreshold = binarizationThreshold
    self.useSparseMemory = useSparseMemory
    self.sparseThreshold = sparseThreshold
    self.relativeThreshold = relativeThreshold
    self.numWinners = numWinners
    self.numSVDSamples = numSVDSamples
    self.numSVDDims = numSVDDims
    self.fractionOfMax = fractionOfMax
    if self.numSVDDims=='adaptive':
      self._adaptiveSVDDims = True
    else:
      self._adaptiveSVDDims = False
    self.verbosity = verbosity
    self.replaceDuplicates = replaceDuplicates
    self.cellsPerCol = cellsPerCol
    self.maxStoredPatterns = maxStoredPatterns
    self.clear()

  ##########################################################################
  def clear(self):

    self._Memory = None
    self._numPatterns = 0
    self._M = None
    self._categoryList = []
    self._partitionIdList = []
    self._partitionIdArray = None
    self._finishedLearning = False
    self._iterationIdx = -1

    # Fixed capacity KNN
    if self.maxStoredPatterns > 0:
      assert self.useSparseMemory, "Fixed capacity KNN is implemented only in" \
                                   " the sparse memory mode"
      self.fixedCapacity = True
      self._categoryRecencyList = []
    else:
      self.fixedCapacity = False

    # Cached value of the store prototype sizes
    self._protoSizes = None

    # Used by PCA
    self._s = None
    self._vt = None
    self._nc = None
    self._mean = None

    # Used by Network Builder
    self._specificIndexTraining = False
    self._nextTrainingIndices = None

  ##########################################################################
  def _doubleMemoryNumRows(self):

    m = 2*self._Memory.shape[0]
    n = self._Memory.shape[1]
    self._Memory = numpy.resize(self._Memory,(m,n))
    self._M = self._Memory[:self._numPatterns]


  ##########################################################################
  def _sparsifyVector(self, inputPattern, doWinners=False):

    # Do sparsification, using a relative or absolute threshold
    if not self.relativeThreshold:
      inputPattern = inputPattern*(abs(inputPattern) > self.sparseThreshold)
    elif self.sparseThreshold > 0:
      inputPattern = inputPattern * \
        (abs(inputPattern) > (self.sparseThreshold * abs(inputPattern).max()))

    # Do winner-take-all
    if doWinners:
      if (self.numWinners>0) and (self.numWinners < (inputPattern > 0).sum()):
        sparseInput = numpy.zeros(inputPattern.shape)
        # Don't consider strongly negative numbers as winners.
        sorted = inputPattern.argsort()[0:self.numWinners]
        sparseInput[sorted] += inputPattern[sorted]
        inputPattern = sparseInput

    # Do binarization
    if self.doBinarization:
      # Don't binarize negative numbers to positive 1.
      inputPattern = (inputPattern > self.binarizationThreshold).astype(float)

    return inputPattern


  def prototypeSetCategory(self, idToRelabel, newCategory):
    if idToRelabel not in self._categoryRecencyList:
      return

    recordIndex = self._categoryRecencyList.index(idToRelabel)
    self._categoryList[recordIndex] = newCategory


  def removeIds(self, idsToRemove):
    # Form a list of all categories to remove
    rowsToRemove = [k for k, rowID in enumerate(self._categoryRecencyList) \
                    if rowID in idsToRemove]

    # Remove rows from the classifier
    self._removeRows(rowsToRemove)


  ##########################################################################
  def removeCategory(self, categoryToRemove):

    removedRows = 0
    if self._Memory is None:
      return removedRows

    # The internal category indices are stored in float
    # format, so we should compare with a float
    catToRemove = float(categoryToRemove)

    # Form a list of all categories to remove
    rowsToRemove = [k for k, catID in enumerate(self._categoryList) \
                    if catID == catToRemove]

    # Remove rows from the classifier
    self._removeRows(rowsToRemove)

    assert catToRemove not in self._categoryList


  def _removeRows(self, rowsToRemove):
    # Form a numpy array of row indices to be removed
    removalArray = numpy.array(rowsToRemove)

    # Remove categories
    self._categoryList = numpy.delete(numpy.array(self._categoryList),
                                      removalArray).tolist()

    self._categoryRecencyList = numpy.delete(numpy.array(self._categoryRecencyList),
                                  removalArray).tolist()

    # Remove the partition ID, if any
    if self._partitionIdArray is not None:
      self._partitionIdArray = numpy.delete(self._partitionIdArray, removalArray)

    # Remove actual patterns
    if self.useSparseMemory:
      # Delete backwards
      for rowIndex in rowsToRemove[::-1]:
        self._Memory.deleteRow(rowIndex)
    else:
      self._M = numpy.delete(self._M, removalArray, 0)

    numRemoved = len(rowsToRemove)

    # Sanity checks
    numRowsExpected = self._numPatterns - numRemoved
    if self.useSparseMemory:
      if self._Memory is not None:
        assert self._Memory.nRows() == numRowsExpected
    else:
      assert self._M.shape[0] == numRowsExpected
    assert len(self._categoryList) == numRowsExpected
    assert self._partitionIdArray is None or \
           self._partitionIdArray.shape[0] == numRowsExpected

    self._numPatterns -= numRemoved
    return numRemoved


  # Used to increment iteration for models that don't learn each timestep
  def doIteration(self):
    self._iterationIdx += 1


  ##########################################################################
  def learn(self, inputPattern, inputCategory, partitionId=None, isSparse=0,
              rowID=None):
    """
    Learn a new training presentation

    Parameters:
    ------------------------------------------------------------------------
    inputPattern: training pattern to learn. This should be a dense array if
                  isSparse==0 or a list of non-zero indices if
                  isSparse>0
    inputCategory: category index of the training pattern.
    partitionID:  ??
    isSparse:     If >0, the input pattern is a list of non-zero indices and
                  isSparse is the length of the dense representation.

    """
    if self.verbosity >= 1:
      print "%s learn:" % (g_debugPrefix)
      print "  category:", int(inputCategory)
      print "  active inputs:", _labeledInput(inputPattern,
                                              cellsPerCol=self.cellsPerCol)

    if rowID is None:
      rowID = self._iterationIdx

    assert partitionId is None, \
      "No documentation is available for partitionId, not sure how it works."

    #---------------------------------------------------------------------------------
    # Dense vectors
    if not self.useSparseMemory:

      # Not supported
      assert self.cellsPerCol == 0, "not implemented for dense vectors"

      # If the input was given in sparse form, convert it to dense
      if isSparse > 0:
        denseInput = numpy.zeros(isSparse)
        denseInput[inputPattern] = 1.0
        inputPattern = denseInput

      if self._specificIndexTraining and not self._nextTrainingIndices:
        # Specific index mode without any index provided - skip training
        return self._numPatterns

      if self._Memory is None:
        # Initialize memory with 100 rows and numPatterns = 0
        inputWidth = len(inputPattern)
        self._Memory = numpy.zeros((100,inputWidth))
        self._numPatterns = 0
        self._M = self._Memory[:self._numPatterns]

      addRow = True

      if self._vt is not None:
        # Compute projection
        inputPattern = numpy.dot(self._vt, inputPattern - self._mean)

      if self.distThreshold > 0:
        # Check if input is too close to an existing input to be accepted
        dist = self._calcDistance(inputPattern)
        minDist = dist.min()
        addRow = (minDist >= self.distThreshold)

      if addRow:
        self._protoSizes = None     # need to re-compute
        if self._numPatterns == self._Memory.shape[0]:
          # Double the size of the memory
          self._doubleMemoryNumRows()

        if not self._specificIndexTraining:
          # Normal learning - append the new input vector
          self._Memory[self._numPatterns] = inputPattern
          self._numPatterns += 1
          self._categoryList.append(int(inputCategory))
        else:
          # Specific index training mode - insert vector in specified slot
          vectorIndex = self._nextTrainingIndices.pop(0)
          while vectorIndex >= self._Memory.shape[0]:
            self._doubleMemoryNumRows()
          self._Memory[vectorIndex] = inputPattern
          self._numPatterns = max(self._numPatterns, vectorIndex + 1)
          if vectorIndex >= len(self._categoryList):
            self._categoryList += [-1] * (vectorIndex - len(self._categoryList) + 1)
          self._categoryList[vectorIndex] = int(inputCategory)

        # Set _M to the "active" part of _Memory
        self._M = self._Memory[0:self._numPatterns]

        if partitionId is not None:
          self._partitionIdList.append(partitionId)

    #---------------------------------------------------------------------------------
    # Sparse vectors
    else:

      # If the input was given in sparse form, convert it to dense if necessary
      if isSparse > 0 and (self._vt is not None or self.distThreshold > 0 \
              or self.numSVDDims is not None or self.numSVDSamples is not None \
              or self.numWinners > 0):
          denseInput = numpy.zeros(isSparse)
          denseInput[inputPattern] = 1.0
          inputPattern = denseInput
          isSparse = 0

      # Get the input width
      if isSparse > 0:
        inputWidth = isSparse
      else:
        inputWidth = len(inputPattern)

      # Allocate storage if this is the first training vector
      if self._Memory is None:
        self._Memory = NearestNeighbor(0, inputWidth)

      # Support SVD if it is on
      if self._vt is not None:
        inputPattern = numpy.dot(self._vt, inputPattern - self._mean)

      # Threshold the input, zeroing out entries that are too close to 0.
      #  This is only done if we are given a dense input.
      if isSparse == 0:
        thresholdedInput = self._sparsifyVector(inputPattern, True)
      addRow = True

      # If given the layout of the cells, then turn on the logic that stores
      # only the start cell for bursting columns.
      if self.cellsPerCol >= 1:
        numCols = thresholdedInput.size / self.cellsPerCol
        burstingCols = thresholdedInput.reshape(-1,
                                  self.cellsPerCol).min(axis=1).nonzero()[0]
        for col in burstingCols:
          thresholdedInput[(col * self.cellsPerCol) + 1 :
                           (col * self.cellsPerCol) + self.cellsPerCol] = 0


      # Don't learn entries that are too close to existing entries.
      if self._Memory.nRows() > 0:
        dist = None
        # if this vector is a perfect match for one we already learned, then
        #  replace the category - it may have changed with online learning on.
        if self.replaceDuplicates:
          dist = self._calcDistance(thresholdedInput, distanceNorm=1)
          if dist.min() == 0:
            rowIdx = dist.argmin()
            self._categoryList[rowIdx] = int(inputCategory)
            if self.fixedCapacity:
              self._categoryRecencyList[rowIdx] = rowID
            addRow = False

        # Don't add this vector if it matches closely with another we already
        #  added
        if self.distThreshold > 0:
          if dist is None or self.distanceNorm != 1:
            dist = self._calcDistance(thresholdedInput)
          minDist = dist.min()
          addRow = (minDist >= self.distThreshold)
          if not addRow:
            if self.fixedCapacity:
              rowIdx = dist.argmin()
              self._categoryRecencyList[rowIdx] = rowID


      # Add the new vector to our storage
      if addRow:
        self._protoSizes = None     # need to re-compute
        if isSparse == 0:
          self._Memory.addRow(thresholdedInput)
        else:
          self._Memory.addRowNZ(inputPattern, [1]*len(inputPattern))
        self._numPatterns += 1
        self._categoryList.append(int(inputCategory))
        if partitionId is not None:
          self._partitionIdList.append(partitionId)
        if self.fixedCapacity:
          self._categoryRecencyList.append(rowID)
          if self._numPatterns > self.maxStoredPatterns and \
            self.maxStoredPatterns > 0:
            leastRecentlyUsedPattern = numpy.argmin(self._categoryRecencyList)
            self._Memory.deleteRow(leastRecentlyUsedPattern)
            self._categoryList.pop(leastRecentlyUsedPattern)
            self._categoryRecencyList.pop(leastRecentlyUsedPattern)
            self._numPatterns -= 1



    if self.numSVDDims is not None and self.numSVDSamples is not None \
          and self._numPatterns == self.numSVDSamples:
        self.computeSVD()

    return self._numPatterns

  ##########################################################################
  def getOverlaps(self, inputPattern):
    """Return the overlap amount of the input pattern with each category.

    This returns 2 numpy arrays of the same length, the overlaps and the
    category numbers. The overlap is computed by compuing:
      logical_and(inputPattern != 0, trainingPattern != 0).sum()

    Parameters:
    -------------------------------------------------------------------
    inputPattern:   pattern to check overlap of
    retval:         (overlaps, categories)
                    overlaps: an integer overlap amount for each category
                    categories: category index for each element of overlaps
    """

    assert self.useSparseMemory, "Not implemented yet for dense storage"

    overlaps = self._Memory.rightVecSumAtNZ(inputPattern)
    return (overlaps, self._categoryList)


  ##########################################################################
  def getDistances(self, inputPattern):
    """Return the distance between the input pattern and all other
    stored patterns.

    This returns 2 numpy arrays of the same length, the distances and the
    category numbers.

    Parameters:
    -------------------------------------------------------------------
    inputPattern:   pattern to check distance with
    retval:         (distances, categories)
                    overlaps: an integer overlap amount for each category
                    categories: category index for each element of distances
    """

    dist = self._getDistances(inputPattern)
    return (dist, self._categoryList)


  ##########################################################################
  def infer(self, inputPattern, computeScores=True,
                  overCategories=True, partitionId=None):
    """Find the category that best matches the input pattern. Returns the
    winning category index plus a distribution over all categories.

    This method returns a 4 item tuple:
    (winner, inferenceResult, dist, categoryDist)
      winner: The category with the greatest number of nearest neighbors within
                the kth nearest neighbors
      inferenceResult: A list of length numCategories, each entry contains the
                number of neighbors within the top K neighbors that are in that
                category
      dist: A list of length numPrototypes. Each entry is the distance from
                the unknown to that prototype. All distances are between 0 and
                1.0
      categoryDist: A list of length numCategories. Each entry is the distance
                from the unknown to the nearest prototype of that category. All
                distances are between 0 and 1.0.

    """


    # If no categories learned yet (applies for first inference with
    #  online learning)
    if len(self._categoryList) == 0:
      winner = 0
      inferenceResult = numpy.zeros(1)
      dist = numpy.ones(1)
      categoryDist = numpy.ones(1)

    else:
      maxCategoryIdx = max(self._categoryList)
      inferenceResult = numpy.zeros(maxCategoryIdx+1)
      dist = self._getDistances(inputPattern, partitionId = partitionId)

      sorted = dist.argsort()

      validVectorCount = len(self._categoryList) - self._categoryList.count(-1)
      for j in sorted[:min(self.k, validVectorCount)]:
        inferenceResult[self._categoryList[j]] += 1.0

      winner = inferenceResult.argmax()
      inferenceResult /= inferenceResult.sum()

      categoryDist = min_score_per_category(maxCategoryIdx,
                                            self._categoryList, dist)
      categoryDist.clip(0, 1.0, categoryDist)


    if self.verbosity >= 1:
      print "%s infer:" % (g_debugPrefix)
      print "  active inputs:",  _labeledInput(inputPattern,
                                               cellsPerCol=self.cellsPerCol)
      print "  winner category:", int(winner)
      print "  pct neighbors of each category:", inferenceResult
      print "  dist of each prototype:", dist
      print "  dist of each category:", categoryDist

    result = (winner, inferenceResult, dist, categoryDist)
    return result

  ##########################################################################
  def getClosest(self, inputPattern, topKCategories = 3):
    """Return index to the pattern that is closest to inputPattern as well
    as indices to the topKCategories closest categories."""

    inferenceResult = numpy.zeros(max(self._categoryList)+1)
    dist = self._getDistances(inputPattern)

    sorted = dist.argsort()

    validVectorCount = len(self._categoryList) - self._categoryList.count(-1)
    for j in sorted[:min(self.k, validVectorCount)]:
      inferenceResult[self._categoryList[j]] += 1.0

    winner = inferenceResult.argmax()

    topNCats = []
    for i in range(topKCategories):
      topNCats.append((self._categoryList[sorted[i]], dist[sorted[i]] ))

    return winner, dist, topNCats

  ##########################################################################
  def closestTrainingPattern(self, inputPattern, cat):
    """
    Return the training pattern belonging to the given category 'cat', that
    matches inputPattern the closest.

    inputPattern: the pattern to compare with
    cat:       the category to consider
    retval:    dense version of training pattern, None if no patterns found
    """

    dist = self._getDistances(inputPattern)
    sorted = dist.argsort()

    for patIdx in sorted:
      patternCat = self._categoryList[patIdx]

      # If closest pattern belongs to desired category, return it
      if patternCat == cat:
        if self.useSparseMemory:
          closestPattern = self._Memory.getRow(int(patIdx))
        else:
          closestPattern = self._M[patIdx]

        return closestPattern

    # No patterns were found!
    return None

  ##########################################################################
  def closestOtherTrainingPattern(self, inputPattern, cat):
    """
    Return the closest training pattern that is *not* in the given
    category 'cat'.

    inputPattern: the pattern to compare with
    cat:       the category to avoid
    retval:    dense version of training pattern, None if no patterns found
    """
    dist = self._getDistances(inputPattern)
    sorted = dist.argsort()
    for patIdx in sorted:
      patternCat = self._categoryList[patIdx]

      # If closest pattern does not belong to specified category, return it
      if patternCat != cat:
        if self.useSparseMemory:
          closestPattern = self._Memory.getRow(int(patIdx))
        else:
          closestPattern = self._M[patIdx]

        return closestPattern

    # No patterns were found!
    return None

  ##########################################################################
  def getPattern(self, idx, sparseBinaryForm=False, cat=None):
    """Return a training pattern either by index or category number

    Parameters:
    ------------------------------------------------------------------------
    idx:                Index of the training pattern
    sparseBinaryForm:   If true, return only a list of the non-zeros in the
                          training pattern
    cat:                If not None, get the first pattern belonging to category
                          cat. If this is specified, idx must be None

    """

    if cat is not None:
      assert idx is None
      idx = self._categoryList.index(cat)

    if not self.useSparseMemory:
      pattern = self._Memory[idx]
      if sparseBinaryForm:
        pattern = pattern.nonzero()[0]

    else:
      (nz, values) = self._Memory.rowNonZeros(idx)
      if not sparseBinaryForm:
        pattern = numpy.zeros(self._Memory.nCols())
        numpy.put(pattern, nz, 1)
      else:
        pattern = nz

      return pattern


  ##########################################################################
  def _calcDistance(self, inputPattern, distanceNorm=None):
    """Calculate the distances from inputPattern to all stored patterns. The
    distances are all between 0 and 1.0"""

    if distanceNorm is None:
      distanceNorm = self.distanceNorm

    # Sparse memory
    if self.useSparseMemory:
      if self.distanceMethod == 'pctOvlerapOfLarger':
        if self._protoSizes is None:
          self._protoSizes = self._Memory.rowSums()
        dist =  self._Memory.rightVecSumAtNZ(inputPattern)
        maxVal = numpy.maximum(self._protoSizes, inputPattern.sum())
        if maxVal > 0:
          dist /= maxVal
        dist = 1.0 - dist
      elif self.distanceMethod == 'rawOverlap':
        if self._protoSizes is None:
          self._protoSizes = self._Memory.rowSums()
        inputPatternSum = inputPattern.sum()
        dist = (inputPatternSum - self._Memory.rightVecSumAtNZ(inputPattern))
        if inputPatternSum > 0:
          dist /= inputPatternSum
      elif self.distanceMethod == 'pctOverlapOfProto':
        if self._protoSizes is None:
          self._protoSizes = self._Memory.rowSums()
        dist =  self._Memory.rightVecSumAtNZ(inputPattern)
        dist /= self._protoSizes
        dist = 1.0 - dist
      elif self.distanceMethod == 'norm':
        dist = self._Memory.vecLpDist(self.distanceNorm, inputPattern)
        distMax = dist.max()
        if distMax > 0:
          dist /= distMax
      else:
        raise RuntimeError("Unimplemented distance method %s" % \
                           (self.distanceMethod))

    # Dense memory
    else:
      if self.distanceMethod == 'norm':
        dist = numpy.power(numpy.abs(self._M - inputPattern), self.distanceNorm)
        dist = dist.sum(1)
        dist = numpy.power(dist, 1.0/self.distanceNorm)
        dist /= dist.max()
      else:
        raise RuntimeError ("Not implemented yet for dense storage....")

    return dist


  ##########################################################################
  def _getDistances(self, inputPattern, partitionId = None):
    """Return distances from inputPattern to all stored patterns."""

    if not self._finishedLearning:
      self.finishLearning()
      self._finishedLearning = True

    if self._vt is not None and len(self._vt) > 0:
      inputPattern = numpy.dot(self._vt, inputPattern - self._mean)

    sparseInput = self._sparsifyVector(inputPattern)

    # Compute distances
    dist = self._calcDistance(sparseInput)
    # Invalidate results where category is -1
    if self._specificIndexTraining:
      dist[numpy.array(self._categoryList) == -1] = numpy.inf

    # Ignore vectors with same partition id
    if self._partitionIdArray is not None:
      dist[self._partitionIdArray == partitionId] = numpy.inf

    return dist


  ##########################################################################
  def finishLearning(self):

    if self.numSVDDims is not None and self._vt is None:
      self.computeSVD()

    # Check if our partition ID list is non-trivial
    # (i.e., whether it contains at least two different
    # partition IDs)
    if self._partitionIdList:
      partitions = set(self._partitionIdList)
      if len(partitions) > 1:
        # Compile into a numpy array
        self._partitionIdArray = numpy.array(self._partitionIdList)
      else:
        # Trivial partitions; ignore
        self._partitionIdArray = None
      # Either way, we don't need the original list
      self._partitionIdList = []

  ##########################################################################
  def restartLearning(self):
    """
    This is only invoked if we have already called finishLearning()
    but now want to go back and provide more samples.
    """
    # We need to convert the partition ID array back into a list
    if hasattr(self, '_partitionIdArray'):
      # In the case of trivial partitions, we need to regenerate
      # the 'null' partition ID
      if self._partitionIdArray is None:
        self._partitionIdList = [0] * self._numPatterns
      else:
        self._partitionIdList = self._partitionIdArray.tolist()

  ##########################################################################
  def computeSVD(self, numSVDSamples=None, finalize=True):

    if numSVDSamples is None:
      numSVDSamples = self._numPatterns

    if not self.useSparseMemory:
      self._a = self._Memory[:self._numPatterns]
    else:
      self._a = self._Memory.toDense()[:self._numPatterns]

    self._mean = numpy.mean(self._a, axis=0)
    self._a -= self._mean
    u,self._s,self._vt = numpy.linalg.svd(self._a[:numSVDSamples])

    if finalize:
      self.finalizeSVD()

    return self._s


  ##########################################################################
  def getAdaptiveSVDDims(self, singularValues, fractionOfMax=0.001):
    v = singularValues/singularValues[0]
    idx = numpy.where(v<fractionOfMax)[0]
    if len(idx):
      print "Number of PCA dimensions chosen: ", idx[0], "out of ", len(v)
      return idx[0]
    else:
      print "Number of PCA dimensions chosen: ", len(v)-1, "out of ", len(v)
      return len(v)-1

  ##########################################################################
  def finalizeSVD(self, numSVDDims=None):

    if numSVDDims is not None:
      self.numSVDDims = numSVDDims


    if self.numSVDDims=='adaptive':
      if self.fractionOfMax is not None:
          self.numSVDDims = self.getAdaptiveSVDDims(self._s, self.fractionOfMax)
      else:
          self.numSVDDims = self.getAdaptiveSVDDims(self._s)


    if self._vt.shape[0] < self.numSVDDims:
      print "******************************************************************************"
      print "Warning: The requested number of PCA dimensions is more than the number of pattern dimensions."
      print "Setting numSVDDims = ", self._vt.shape[0]
      print "******************************************************************************"
      self.numSVDDims = self._vt.shape[0]

    self._vt = self._vt[:self.numSVDDims]

    # Added when svd is not able to decompose vectors - uses raw spare vectors  
    if len(self._vt) == 0:
      return

    self._Memory = numpy.zeros((self._numPatterns,self.numSVDDims))
    self._M = self._Memory
    self.useSparseMemory = False

    for i in range(self._numPatterns):
      self._Memory[i] = numpy.dot(self._vt, self._a[i])

    self._a = None

  ##########################################################################
  def leaveOneOutTest(self):
    """
    Run leave-one-out testing.

    Returns the total number of samples and the number correctly classified.

    Ignores invalid vectors (those with a category of -1).

    Uses partitionIdList, if non-empty, to avoid matching a vector against
    other vectors that came from the same training sequence.
    """

    if self.useSparseMemory:
      raise Exception("leaveOneOutTest only works with dense memory right now")

    # The basic test is simple, but we need to prepare some data structures to
    # handle _specificIndexTraining and _partitionIdList
    categoryListArray = numpy.array(self._categoryList[:self._M.shape[0]])
    if self._specificIndexTraining:
      # Find valid and invalid vectors using the category list
      validIndices = (categoryListArray != -1)
      invalidIndices = (categoryListArray == -1)

    # Convert list of partitions to numpy array if we haven't
    # already done so.
    partitionIdArray = None
    if hasattr(self, '_partitionIdArray') and \
        self._partitionIdArray is not None:
      partitionIdArray = self._partitionIdArray
    elif self._partitionIdList:
      # Use the partition id list
      partitionIdArray = numpy.array(self._partitionIdList)

    # Find the winning vector for each cache vector, excluding itself,
    # excluding invalid vectors, and excluding other vectors with the
    # same partition id
    winners = numpy.zeros(self._M.shape[0], numpy.int32)
    for i in xrange(self._M.shape[0]):
      if self._specificIndexTraining \
          and categoryListArray[i] == -1:  # This is an invalid vector
        continue

      # Calculate distance between this vector and all others
      distances = numpy.power(numpy.abs(self._M - self._M[i,:]), self.distanceNorm)
      distances = distances.sum(1)

      # Invalidate certain vectors by setting their distance to infinity
      if self._specificIndexTraining:
        distances[invalidIndices] = numpy.inf  # Ignore invalid vectors
      if partitionIdArray is not None:  # Ignore vectors with same partition id
        distances[partitionIdArray == partitionIdArray[i]] = numpy.inf
      else:
        distances[i] = numpy.inf  # Don't match vector with itself

      if self.k == 1:
        # Take the closest vector as the winner (k=1)
        winners[i] = distances.argmin()
      else:
        # Have the top k winners vote on the category
        categoryScores = numpy.zeros(categoryListArray.max() + 1)
        for j in xrange(self.k):
          winner = distances.argmin()
          distances[winner] = numpy.inf
          categoryScores[categoryListArray[winner]] += 1
        winners[i] = categoryScores.argmax()

    if self.k == 1:
      # Convert the winners (vector IDs) to their category indices
      # For k > 1, the winners are already category indices
      winners = categoryListArray[winners]

    if self._specificIndexTraining:
      # Count the number of correct categories, ignoring invalid vectors
      matches = (winners[validIndices] == categoryListArray[validIndices])
    else:
      # Count the number of correct categories
      matches = (winners == categoryListArray)

    # number of samples, number correct
    return float(matches.shape[0]), matches.sum()

  ##########################################################################
  def remapCategories(self, mapping):
    """
    Change the category indices.

    mapping -- List of new category indices. For example, mapping=[2,0,1]
      would change all vectors of category 0 to be category 2, category 1 to 0,
      and category 2 to 1.

    Used by the Network Builder to keep the category indices in sync with the
    ImageSensor categoryInfo when the user renames or removes categories.
    """

    categoryArray = numpy.array(self._categoryList)
    newCategoryArray = numpy.zeros(categoryArray.shape[0])
    newCategoryArray.fill(-1)
    for i in xrange(len(mapping)):
      newCategoryArray[categoryArray==i] = mapping[i]
    self._categoryList = list(newCategoryArray)

  ##########################################################################
  def setCategoryOfVectors(self, vectorIndices, categoryIndices):
    """
    Change the category associated with this vector(s).

    vectorIndices -- Single index or list of indices.
    categoryIndices -- Single index or list of indices. Can also be a single
      index when vectorIndices is a list, in which case the same category will
      be used for all vectors.

    Used by the Network Builder to move vectors between categories, to enable
    categories, and to invalidate vectors by setting the category to -1.
    """

    if not hasattr(vectorIndices, '__iter__'):
      vectorIndices = [vectorIndices]
      categoryIndices = [categoryIndices]
    elif not hasattr(categoryIndices, '__iter__'):
      categoryIndices = [categoryIndices] * len(vectorIndices)

    for i in xrange(len(vectorIndices)):
      vectorIndex = vectorIndices[i]
      categoryIndex = categoryIndices[i]
      # Out-of-bounds is not an error, because the KNN may not have seen the
      # vector yet
      if vectorIndex < len(self._categoryList):
        self._categoryList[vectorIndex] = categoryIndex


  def __getstate__(self):
    """
    Return serializable state.  This function will return a version of the
    __dict__.
    """
    state = self.__dict__.copy()
    return state


  def __setstate__(self, state):
    """
    Set the state of ourself from a serialized state.
    """
    if 'version' not in state:
      pass
    elif state['version'] == 1:
      pass
    elif state['version'] == 2:
      raise RuntimeError("Invalid deserialization of invalid KNNClassifier"
          "Verison")

    self.__dict__.update(state)

    # Set to new version
    self.version = KNNCLASSIFIER_VERSION
