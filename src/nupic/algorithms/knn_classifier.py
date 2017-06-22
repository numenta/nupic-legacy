# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013-15, Numenta, Inc.  Unless you have an agreement
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

"""This module implements a k nearest neighbor classifier."""

import numpy

from nupic.bindings.math import (NearestNeighbor, min_score_per_category)

from nupic.serializable import Serializable

try:
  import capnp
except ImportError:
  capnp = None
import numpy

if capnp:
  from nupic.algorithms.knn_classifier_capnp import KNNClassifierProto


g_debugPrefix = "KNN"
KNNCLASSIFIER_VERSION = 1



def _labeledInput(activeInputs, cellsPerCol=32):
  """Print the list of [column, cellIdx] indices for each of the active
  cells in activeInputs.
  """
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
      items.append("Col %d: [" % col)
      prevCol = col

    items.append("%d," % cellIdx)

  items.append("]")
  return " ".join(items)



class KNNClassifier(Serializable):
  """
  This class implements NuPIC's k Nearest Neighbor Classifier. KNN is very
  useful as a basic classifier for many situations. This implementation contains
  many enhancements that are useful for HTM experiments. These enhancements
  include an optimized C++ class for sparse vectors, support for continuous
  online learning, support for various distance methods (including Lp-norm and
  raw overlap), support for performing SVD on the input vectors (very useful for
  large vectors), support for a fixed-size KNN, and a mechanism to store custom
  ID's for each vector.

  :param k: (int) The number of nearest neighbors used in the classification
      of patterns. Must be odd.

  :param exact: (boolean) If true, patterns must match exactly when assigning
      class labels

  :param distanceNorm: (int) When distance method is "norm", this specifies
      the p value of the Lp-norm

  :param distanceMethod: (string) The method used to compute distance between
      input patterns and prototype patterns. The possible options are:

      - ``norm``: When distanceNorm is 2, this is the euclidean distance,
              When distanceNorm is 1, this is the manhattan distance
              In general: sum(abs(x-proto) ^ distanceNorm) ^ (1/distanceNorm)
              The distances are normalized such that farthest prototype from
              a given input is 1.0.
      - ``rawOverlap``: Only appropriate when inputs are binary. This computes:
              (width of the input) - (# bits of overlap between input
              and prototype).
      - ``pctOverlapOfInput``: Only appropriate for binary inputs. This computes
              1.0 - (# bits overlap between input and prototype) /
                      (# ON bits in input)
      - ``pctOverlapOfProto``: Only appropriate for binary inputs. This computes
              1.0 - (# bits overlap between input and prototype) /
                      (# ON bits in prototype)
      - ``pctOverlapOfLarger``: Only appropriate for binary inputs. This computes
              1.0 - (# bits overlap between input and prototype) /
                      max(# ON bits in input, # ON bits in prototype)

  :param distThreshold: (float) A threshold on the distance between learned
      patterns and a new pattern proposed to be learned. The distance must be
      greater than this threshold in order for the new pattern to be added to
      the classifier's memory.

  :param doBinarization: (boolean) If True, then scalar inputs will be
      binarized.

  :param binarizationThreshold: (float) If doBinarization is True, this
      specifies the threshold for the binarization of inputs

  :param useSparseMemory: (boolean) If True, classifier will use a sparse
      memory matrix

  :param sparseThreshold: (float) If useSparseMemory is True, input variables
      whose absolute values are less than this threshold will be stored as
      zero

  :param relativeThreshold: (boolean) Flag specifying whether to multiply
      sparseThreshold by max value in input

  :param numWinners: (int) Number of elements of the input that are stored. If
      0, all elements are stored

  :param numSVDSamples: (int) Number of samples the must occur before a SVD
      (Singular Value Decomposition) transformation will be performed. If 0,
      the transformation will never be performed

  :param numSVDDims: (string) Controls dimensions kept after SVD
      transformation. If "adaptive", the number is chosen automatically

  :param fractionOfMax: (float) If numSVDDims is "adaptive", this controls the
      smallest singular value that is retained as a fraction of the largest
      singular value

  :param verbosity: (int) Console verbosity level where 0 is no output and
      larger integers provide increasing levels of verbosity

  :param maxStoredPatterns: (int) Limits the maximum number of the training
      patterns stored. When KNN learns in a fixed capacity mode, the unused
      patterns are deleted once the number of stored patterns is greater than
      maxStoredPatterns. A value of -1 is no limit

  :param replaceDuplicates: (bool) A boolean flag that determines whether,
      during learning, the classifier replaces duplicates that match exactly,
      even if distThreshold is 0. Should be True for online learning

  :param cellsPerCol: (int) If >= 1, input is assumed to be organized into
      columns, in the same manner as the temporal memory AND whenever a new
      prototype is stored, only the start cell (first cell) is stored in any
      bursting column

  :param minSparsity: (float) If useSparseMemory is set, only vectors with
      sparsity >= minSparsity will be stored during learning. A value of 0.0
      implies all vectors will be stored. A value of 0.1 implies only vectors
      with at least 10% sparsity will be stored

  """

  def __init__(self, k=1,
                     exact=False,
                     distanceNorm=2.0,
                     distanceMethod="norm",
                     distThreshold=0,
                     doBinarization=False,
                     binarizationThreshold=0.5,
                     useSparseMemory=True,
                     sparseThreshold=0.1,
                     relativeThreshold=False,
                     numWinners=0,
                     numSVDSamples=None,
                     numSVDDims=None,
                     fractionOfMax=None,
                     verbosity=0,
                     maxStoredPatterns=-1,
                     replaceDuplicates=False,
                     cellsPerCol=0,
                     minSparsity=0.0):

    self.version = KNNCLASSIFIER_VERSION

    self.k = k
    self.exact = exact
    self.distanceNorm = distanceNorm
    assert (distanceMethod in ("norm", "rawOverlap", "pctOverlapOfLarger",
                               "pctOverlapOfProto", "pctOverlapOfInput"))
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
    if self.numSVDDims=="adaptive":
      self._adaptiveSVDDims = True
    else:
      self._adaptiveSVDDims = False
    self.verbosity = verbosity
    self.replaceDuplicates = replaceDuplicates
    self.cellsPerCol = cellsPerCol
    self.maxStoredPatterns = maxStoredPatterns
    self.minSparsity = minSparsity
    self.clear()


  def clear(self):
    """Clears the state of the KNNClassifier."""
    self._Memory = None
    self._numPatterns = 0
    self._M = None
    self._categoryList = []
    self._partitionIdList = []
    self._partitionIdMap = {}
    self._finishedLearning = False
    self._iterationIdx = -1

    # Fixed capacity KNN
    if self.maxStoredPatterns > 0:
      assert self.useSparseMemory, ("Fixed capacity KNN is implemented only "
                                    "in the sparse memory mode")
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


  def _doubleMemoryNumRows(self):

    m = 2 * self._Memory.shape[0]
    n = self._Memory.shape[1]
    self._Memory = numpy.resize(self._Memory,(m,n))
    self._M = self._Memory[:self._numPatterns]


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


  def prototypeSetCategory(self, idToCategorize, newCategory):
    """
    Allows ids to be assigned a category and subsequently enables users to use:

      - :meth:`~.KNNClassifier.KNNClassifier.removeCategory`
      - :meth:`~.KNNClassifier.KNNClassifier.closestTrainingPattern`
      - :meth:`~.KNNClassifier.KNNClassifier.closestOtherTrainingPattern`
    """
    if idToCategorize not in self._categoryRecencyList:
      return

    recordIndex = self._categoryRecencyList.index(idToCategorize)
    self._categoryList[recordIndex] = newCategory


  def removeIds(self, idsToRemove):
    """
    There are two caveats. First, this is a potentially slow operation. Second,
    pattern indices will shift if patterns before them are removed.

    :param idsToRemove: A list of row indices to remove.
    """
    # Form a list of all categories to remove
    rowsToRemove = [k for k, rowID in enumerate(self._categoryRecencyList) \
                    if rowID in idsToRemove]

    # Remove rows from the classifier
    self._removeRows(rowsToRemove)


  def removeCategory(self, categoryToRemove):
    """
    There are two caveats. First, this is a potentially slow operation. Second,
    pattern indices will shift if patterns before them are removed.

    :param categoryToRemove: Category label to remove
    """
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
    """
    A list of row indices to remove. There are two caveats. First, this is
    a potentially slow operation. Second, pattern indices will shift if
    patterns before them are removed.
    """
    # Form a numpy array of row indices to be removed
    removalArray = numpy.array(rowsToRemove)

    # Remove categories
    self._categoryList = numpy.delete(numpy.array(self._categoryList),
                                      removalArray).tolist()

    if self.fixedCapacity:
      self._categoryRecencyList = numpy.delete(
        numpy.array(self._categoryRecencyList), removalArray).tolist()

    # Remove the partition ID, if any for these rows and rebuild the id map.
    for row in reversed(rowsToRemove):  # Go backwards
      # Remove these patterns from partitionList
      self._partitionIdList.pop(row)
    self._rebuildPartitionIdMap(self._partitionIdList)


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

    self._numPatterns -= numRemoved
    return numRemoved


  def doIteration(self):
    """
    Utility method to increment the iteration index. Intended for models that
    don't learn each timestep.
    """
    self._iterationIdx += 1


  def learn(self, inputPattern, inputCategory, partitionId=None, isSparse=0,
            rowID=None):
    """
    Train the classifier to associate specified input pattern with a
    particular category.

    :param inputPattern: (list) The pattern to be assigned a category. If
        isSparse is 0, this should be a dense array (both ON and OFF bits
        present). Otherwise, if isSparse > 0, this should be a list of the
        indices of the non-zero bits in sorted order

    :param inputCategory: (int) The category to be associated to the training
        pattern

    :param partitionId: (int) partitionID allows you to associate an id with each
        input vector. It can be used to associate input patterns stored in the
        classifier with an external id. This can be useful for debugging or
        visualizing. Another use case is to ignore vectors with a specific id
        during inference (see description of infer() for details). There can be
        at most one partitionId per stored pattern (i.e. if two patterns are
        within distThreshold, only the first partitionId will be stored). This
        is an optional parameter.

    :param isSparse: (int) If 0, the input pattern is a dense representation. If
        isSparse > 0, the input pattern is a list of non-zero indices and
        isSparse is the length of the dense representation

    :param rowID: (int) UNKNOWN

    :returns: The number of patterns currently stored in the classifier
    """
    if self.verbosity >= 1:
      print "%s learn:" % g_debugPrefix
      print "  category:", int(inputCategory)
      print "  active inputs:", _labeledInput(inputPattern,
                                              cellsPerCol=self.cellsPerCol)

    if isSparse > 0:
      assert all(inputPattern[i] <= inputPattern[i+1]
                 for i in xrange(len(inputPattern)-1)), \
                     "Sparse inputPattern must be sorted."
      assert all(bit < isSparse for bit in inputPattern), \
        ("Sparse inputPattern must not index outside the dense "
         "representation's bounds.")

    if rowID is None:
      rowID = self._iterationIdx

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
            self._categoryList += [-1] * (vectorIndex -
                                          len(self._categoryList) + 1)
          self._categoryList[vectorIndex] = int(inputCategory)

        # Set _M to the "active" part of _Memory
        self._M = self._Memory[0:self._numPatterns]

        self._addPartitionId(self._numPatterns-1, partitionId)

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


      # If sparsity is too low, we do not want to add this vector
      if addRow and self.minSparsity > 0.0:
        if isSparse==0:
          sparsity = ( float(len(thresholdedInput.nonzero()[0])) /
                       len(thresholdedInput) )
        else:
          sparsity = float(len(inputPattern)) / isSparse
        if sparsity < self.minSparsity:
          addRow = False

      # Add the new sparse vector to our storage
      if addRow:
        self._protoSizes = None     # need to re-compute
        if isSparse == 0:
          self._Memory.addRow(thresholdedInput)
        else:
          self._Memory.addRowNZ(inputPattern, [1]*len(inputPattern))
        self._numPatterns += 1
        self._categoryList.append(int(inputCategory))
        self._addPartitionId(self._numPatterns-1, partitionId)
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


  def getOverlaps(self, inputPattern):
    """
    Return the degree of overlap between an input pattern and each category
    stored in the classifier. The overlap is computed by computing:

    .. code-block:: python

      logical_and(inputPattern != 0, trainingPattern != 0).sum()

    :param inputPattern: pattern to check overlap of

    :returns: (overlaps, categories) Two numpy arrays of the same length, where:
    
                * overlaps: an integer overlap amount for each category
                * categories: category index for each element of overlaps
    """
    assert self.useSparseMemory, "Not implemented yet for dense storage"

    overlaps = self._Memory.rightVecSumAtNZ(inputPattern)
    return (overlaps, self._categoryList)


  def getDistances(self, inputPattern):
    """Return the distances between the input pattern and all other
    stored patterns.

    :param inputPattern: pattern to check distance with

    :returns: (distances, categories) numpy arrays of the same length.
        - overlaps: an integer overlap amount for each category
        - categories: category index for each element of distances
    """
    dist = self._getDistances(inputPattern)
    return (dist, self._categoryList)


  def infer(self, inputPattern, computeScores=True, overCategories=True,
            partitionId=None):
    """Finds the category that best matches the input pattern. Returns the
    winning category index as well as a distribution over all categories.

    :param inputPattern: (list) A pattern to be classified

    :param computeScores: NO EFFECT

    :param overCategories: NO EFFECT

    :param partitionId: (int) If provided, all training vectors with partitionId
        equal to that of the input pattern are ignored.
        For example, this may be used to perform k-fold cross validation
        without repopulating the classifier. First partition all the data into
        k equal partitions numbered 0, 1, 2, ... and then call learn() for each
        vector passing in its partitionId. Then, during inference, by passing
        in the partition ID in the call to infer(), all other vectors with the
        same partitionId are ignored simulating the effect of repopulating the
        classifier while ommitting the training vectors in the same partition.

    :returns: 4-tuple with these keys:

      - ``winner``: The category with the greatest number of nearest neighbors
          within the kth nearest neighbors. If the inferenceResult contains no
          neighbors, the value of winner is None. This can happen, for example,
          in cases of exact matching, if there are no stored vectors, or if
          minSparsity is not met.
      - ``inferenceResult``: A list of length numCategories, each entry contains
          the number of neighbors within the top k neighbors that are in that
          category.
      - ``dist``: A list of length numPrototypes. Each entry is the distance
          from the unknown to that prototype. All distances are between 0.0 and
          1.0.
      - ``categoryDist``: A list of length numCategories. Each entry is the
                        distance from the unknown to the nearest prototype of
                        that category. All distances are between 0 and 1.0.
    """

    # Calculate sparsity. If sparsity is too low, we do not want to run
    # inference with this vector
    sparsity = 0.0
    if self.minSparsity > 0.0:
      sparsity = ( float(len(inputPattern.nonzero()[0])) /
                   len(inputPattern) )

    if len(self._categoryList) == 0 or sparsity < self.minSparsity:
      # No categories learned yet; i.e. first inference w/ online learning or
      # insufficient sparsity
      winner = None
      inferenceResult = numpy.zeros(1)
      dist = numpy.ones(1)
      categoryDist = numpy.ones(1)

    else:
      maxCategoryIdx = max(self._categoryList)
      inferenceResult = numpy.zeros(maxCategoryIdx+1)
      dist = self._getDistances(inputPattern, partitionId=partitionId)
      validVectorCount = len(self._categoryList) - self._categoryList.count(-1)

      # Loop through the indices of the nearest neighbors.
      if self.exact:
        # Is there an exact match in the distances?
        exactMatches = numpy.where(dist<0.00001)[0]
        if len(exactMatches) > 0:
          for i in exactMatches[:min(self.k, validVectorCount)]:
            inferenceResult[self._categoryList[i]] += 1.0
      else:
        sorted = dist.argsort()
        for j in sorted[:min(self.k, validVectorCount)]:
          inferenceResult[self._categoryList[j]] += 1.0

      # Prepare inference results.
      if inferenceResult.any():
        winner = inferenceResult.argmax()
        inferenceResult /= inferenceResult.sum()
      else:
        winner = None
      categoryDist = min_score_per_category(maxCategoryIdx,
                                            self._categoryList, dist)
      categoryDist.clip(0, 1.0, categoryDist)

    if self.verbosity >= 1:
      print "%s infer:" % (g_debugPrefix)
      print "  active inputs:",  _labeledInput(inputPattern,
                                               cellsPerCol=self.cellsPerCol)
      print "  winner category:", winner
      print "  pct neighbors of each category:", inferenceResult
      print "  dist of each prototype:", dist
      print "  dist of each category:", categoryDist

    result = (winner, inferenceResult, dist, categoryDist)
    return result


  def getClosest(self, inputPattern, topKCategories=3):
    """Returns the index of the pattern that is closest to inputPattern,
    the distances of all patterns to inputPattern, and the indices of the k
    closest categories.
    """
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


  def closestTrainingPattern(self, inputPattern, cat):
    """Returns the closest training pattern to inputPattern that belongs to
    category "cat".

    :param inputPattern: The pattern whose closest neighbor is sought

    :param cat: The required category of closest neighbor

    :returns: A dense version of the closest training pattern, or None if no
        such patterns exist
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


  def closestOtherTrainingPattern(self, inputPattern, cat):
    """Return the closest training pattern that is *not* of the given
    category "cat".

    :param inputPattern: The pattern whose closest neighbor is sought

    :param cat: Training patterns of this category will be ignored no matter
        their distance to inputPattern

    :returns: A dense version of the closest training pattern, or None if no
        such patterns exist
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


  def getPattern(self, idx, sparseBinaryForm=False, cat=None):
    """Gets a training pattern either by index or category number.

    :param idx: Index of the training pattern

    :param sparseBinaryForm: If true, returns a list of the indices of the
        non-zero bits in the training pattern

    :param cat: If not None, get the first pattern belonging to category cat. If
        this is specified, idx must be None.

    :returns: The training pattern with specified index
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


  def getPartitionId(self, i):
    """
    Gets the partition id given an index.

    :param i: index of partition
    :returns: the partition id associated with pattern i. Returns None if no id
        is associated with it.
    """
    if (i < 0) or (i >= self._numPatterns):
      raise RuntimeError("index out of bounds")
    partitionId = self._partitionIdList[i]
    if partitionId == numpy.inf:
      return None
    else:
      return partitionId


  def getPartitionIdList(self):
    """
    :returns: a list of complete partition id objects
    """
    return self._partitionIdList


  def getNumPartitionIds(self):
    """
    :returns: the number of unique partition Ids stored.
    """
    return len(self._partitionIdMap)


  def getPartitionIdKeys(self):
    """
    :returns: a list containing unique (non-None) partition Ids (just the keys)
    """
    return self._partitionIdMap.keys()


  def getPatternIndicesWithPartitionId(self, partitionId):
    """
    :returns: a list of pattern indices corresponding to this partitionId.
        Return an empty list if there are none.
    """
    return self._partitionIdMap.get(partitionId, [])


  def _addPartitionId(self, index, partitionId=None):
    """
    Adds partition id for pattern index
    """
    if partitionId is None:
      self._partitionIdList.append(numpy.inf)
    else:
      self._partitionIdList.append(partitionId)
      indices = self._partitionIdMap.get(partitionId, [])
      indices.append(index)
      self._partitionIdMap[partitionId] = indices


  def _rebuildPartitionIdMap(self, partitionIdList):
    """
    Rebuilds the partition Id map using the given partitionIdList
    """
    self._partitionIdMap = {}
    for row, partitionId in enumerate(partitionIdList):
      indices = self._partitionIdMap.get(partitionId, [])
      indices.append(row)
      self._partitionIdMap[partitionId] = indices


  def _calcDistance(self, inputPattern, distanceNorm=None):
    """Calculate the distances from inputPattern to all stored patterns. All
    distances are between 0.0 and 1.0

    :param inputPattern The pattern from which distances to all other patterns
        are calculated

    :param distanceNorm Degree of the distance norm
    """
    if distanceNorm is None:
      distanceNorm = self.distanceNorm

    # Sparse memory
    if self.useSparseMemory:
      if self._protoSizes is None:
        self._protoSizes = self._Memory.rowSums()
      overlapsWithProtos = self._Memory.rightVecSumAtNZ(inputPattern)
      inputPatternSum = inputPattern.sum()

      if self.distanceMethod == "rawOverlap":
        dist = inputPattern.sum() - overlapsWithProtos
      elif self.distanceMethod == "pctOverlapOfInput":
        dist = inputPatternSum - overlapsWithProtos
        if inputPatternSum > 0:
          dist /= inputPatternSum
      elif self.distanceMethod == "pctOverlapOfProto":
        overlapsWithProtos /= self._protoSizes
        dist = 1.0 - overlapsWithProtos
      elif self.distanceMethod == "pctOverlapOfLarger":
        maxVal = numpy.maximum(self._protoSizes, inputPatternSum)
        if maxVal.all() > 0:
          overlapsWithProtos /= maxVal
        dist = 1.0 - overlapsWithProtos
      elif self.distanceMethod == "norm":
        dist = self._Memory.vecLpDist(self.distanceNorm, inputPattern)
        distMax = dist.max()
        if distMax > 0:
          dist /= distMax
      else:
        raise RuntimeError("Unimplemented distance method %s" %
          self.distanceMethod)

    # Dense memory
    else:
      if self.distanceMethod == "norm":
        dist = numpy.power(numpy.abs(self._M - inputPattern), self.distanceNorm)
        dist = dist.sum(1)
        dist = numpy.power(dist, 1.0/self.distanceNorm)
        dist /= dist.max()
      else:
        raise RuntimeError ("Not implemented yet for dense storage....")

    return dist


  def _getDistances(self, inputPattern, partitionId=None):
    """Return the distances from inputPattern to all stored patterns.

    :param inputPattern The pattern from which distances to all other patterns
        are returned

    :param partitionId If provided, ignore all training vectors with this
        partitionId.
    """
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

    # Ignore vectors with this partition id by setting their distances to inf
    if partitionId is not None:
      dist[self._partitionIdMap.get(partitionId, [])] = numpy.inf

    return dist


  def finishLearning(self):
    """
    Used for batch scenarios.  This method needs to be called between learning
    and inference.
    """
    if self.numSVDDims is not None and self._vt is None:
      self.computeSVD()


  def computeSVD(self, numSVDSamples=None, finalize=True):
    """
    Compute the singular value decomposition (SVD). The SVD is a factorization
    of a real or complex matrix. It factors the matrix `a` as
    `u * np.diag(s) * v`, where `u` and `v` are unitary and `s` is a 1-d array
    of `a`'s singular values.

    **Reason for computing the SVD:**
    
    There are cases where you want to feed a lot of vectors to the
    KNNClassifier. However, this can be slow. You can speed up training by (1)
    computing the SVD of the input patterns which will give you the
    eigenvectors, (2) only keeping a fraction of the eigenvectors, and (3)
    projecting the input patterns onto the remaining eigenvectors.

    Note that all input patterns are projected onto the eigenvectors in the same
    fashion. Keeping only the highest eigenvectors increases training
    performance since it reduces the dimensionality of the input.

    :param numSVDSamples: (int) the number of samples to use for the SVD
                          computation.

    :param finalize: (bool) whether to apply SVD to the input patterns.

    :returns: (array) The singular values for every matrix, sorted in
               descending order.
    """
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
      self._finalizeSVD()

    return self._s


  def getAdaptiveSVDDims(self, singularValues, fractionOfMax=0.001):
    """
    Compute the number of eigenvectors (singularValues) to keep.

    :param singularValues:
    :param fractionOfMax:
    :return:
    """
    v = singularValues/singularValues[0]
    idx = numpy.where(v<fractionOfMax)[0]
    if len(idx):
      print "Number of PCA dimensions chosen: ", idx[0], "out of ", len(v)
      return idx[0]
    else:
      print "Number of PCA dimensions chosen: ", len(v)-1, "out of ", len(v)
      return len(v)-1


  def _finalizeSVD(self, numSVDDims=None):
    """
    Called by finalizeLearning(). This will project all the patterns onto the
    SVD eigenvectors.
    :param numSVDDims: (int) number of egeinvectors used for projection.
    :return:
    """
    if numSVDDims is not None:
      self.numSVDDims = numSVDDims


    if self.numSVDDims=="adaptive":
      if self.fractionOfMax is not None:
          self.numSVDDims = self.getAdaptiveSVDDims(self._s, self.fractionOfMax)
      else:
          self.numSVDDims = self.getAdaptiveSVDDims(self._s)


    if self._vt.shape[0] < self.numSVDDims:
      print "******************************************************************"
      print ("Warning: The requested number of PCA dimensions is more than "
             "the number of pattern dimensions.")
      print "Setting numSVDDims = ", self._vt.shape[0]
      print "******************************************************************"
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


  def remapCategories(self, mapping):
    """Change the category indices.

    Used by the Network Builder to keep the category indices in sync with the
    ImageSensor categoryInfo when the user renames or removes categories.

    :param mapping: List of new category indices. For example, mapping=[2,0,1]
        would change all vectors of category 0 to be category 2, category 1 to
        0, and category 2 to 1
    """
    categoryArray = numpy.array(self._categoryList)
    newCategoryArray = numpy.zeros(categoryArray.shape[0])
    newCategoryArray.fill(-1)
    for i in xrange(len(mapping)):
      newCategoryArray[categoryArray==i] = mapping[i]
    self._categoryList = list(newCategoryArray)


  def setCategoryOfVectors(self, vectorIndices, categoryIndices):
    """Change the category associated with this vector(s).

    Used by the Network Builder to move vectors between categories, to enable
    categories, and to invalidate vectors by setting the category to -1.

    :param vectorIndices: Single index or list of indices

    :param categoryIndices: Single index or list of indices. Can also be a
        single index when vectorIndices is a list, in which case the same
        category will be used for all vectors
    """
    if not hasattr(vectorIndices, "__iter__"):
      vectorIndices = [vectorIndices]
      categoryIndices = [categoryIndices]
    elif not hasattr(categoryIndices, "__iter__"):
      categoryIndices = [categoryIndices] * len(vectorIndices)

    for i in xrange(len(vectorIndices)):
      vectorIndex = vectorIndices[i]
      categoryIndex = categoryIndices[i]

      # Out-of-bounds is not an error, because the KNN may not have seen the
      # vector yet
      if vectorIndex < len(self._categoryList):
        self._categoryList[vectorIndex] = categoryIndex

  @staticmethod
  def getSchema():
    return KNNClassifierProto


  @classmethod
  def read(cls, proto):
    if proto.version != KNNCLASSIFIER_VERSION:
      raise RuntimeError("Invalid KNNClassifier Version")

    knn = object.__new__(cls)

    knn.version = proto.version
    knn.k = proto.k
    knn.exact = proto.exact
    knn.distanceNorm = proto.distanceNorm
    knn.distanceMethod = proto.distanceMethod
    knn.distThreshold = proto.distThreshold
    knn.doBinarization = proto.doBinarization
    knn.binarizationThreshold = proto.binarizationThreshold
    knn.useSparseMemory = proto.useSparseMemory
    knn.sparseThreshold = proto.sparseThreshold
    knn.relativeThreshold = proto.relativeThreshold
    knn.numWinners = proto.numWinners
    knn.numSVDSamples = proto.numSVDSamples
    knn.numSVDDims = proto.numSVDDims
    knn.fractionOfMax = proto.fractionOfMax
    knn.verbosity = proto.verbosity
    knn.maxStoredPatterns = proto.maxStoredPatterns
    knn.replaceDuplicates = proto.replaceDuplicates
    knn.cellsPerCol = proto.cellsPerCol
    knn.minSparsity = proto.minSparsity

    if knn.numSVDDims == "adaptive":
      knn._adaptiveSVDDims = True
    else:
      knn._adaptiveSVDDims = False

    # Read private state
    knn.clear()
    if proto.memory is not None:
      which = proto.memory.which()
      if which == "ndarray":
        knn._Memory = numpy.array(proto.memory.ndarray, dtype=numpy.float64)
      elif which == "nearestNeighbor":
        knn._Memory = NearestNeighbor()
        knn._Memory.read(proto.memory.nearestNeighbor)

    knn._numPatterns = proto.numPatterns

    if proto.m is not None:
      knn._M = numpy.array(proto.m, dtype=numpy.float64)

    if proto.categoryList is not None:
      knn._categoryList = list(proto.categoryList)

    if proto.partitionIdList is not None:
      knn._partitionIdList = list(proto.partitionIdList)
      knn._rebuildPartitionIdMap(knn._partitionIdList)

    knn._iterationIdx = proto.iterationIdx
    knn._finishedLearning = proto.finishedLearning

    if proto.s is not None:
      knn._s = numpy.array(proto.s, dtype=numpy.float32)

    if proto.vt is not None:
      knn._vt = numpy.array(proto.vt, dtype=numpy.float32)

    if proto.mean is not None:
      knn._mean = numpy.array(proto.mean, dtype=numpy.float32)

    return knn


  def write(self, proto):

    proto.version = self.version
    proto.k = self.k
    proto.exact = bool(self.exact)
    proto.distanceNorm = self.distanceNorm
    proto.distanceMethod = self.distanceMethod
    proto.distThreshold = self.distThreshold
    proto.doBinarization = bool(self.doBinarization)
    proto.binarizationThreshold = self.binarizationThreshold
    proto.useSparseMemory = bool(self.useSparseMemory)
    proto.sparseThreshold = self.sparseThreshold
    proto.relativeThreshold = bool(self.relativeThreshold)
    proto.numWinners = self.numWinners
    proto.verbosity = self.verbosity
    proto.maxStoredPatterns = self.maxStoredPatterns
    proto.replaceDuplicates = bool(self.replaceDuplicates)
    proto.cellsPerCol = self.cellsPerCol
    proto.minSparsity = self.minSparsity

    # Write private state
    if self._Memory is not None:
      if isinstance(self._Memory, numpy.ndarray):
        proto.memory.ndarray = self._Memory.tolist()
      else:
        proto.memory.init("nearestNeighbor")
        self._Memory.write(proto.memory.nearestNeighbor)

    proto.numPatterns = self._numPatterns

    if self._M is not None:
      proto.m = self._M.tolist()

    if self._categoryList is not None:
      proto.categoryList = self._categoryList

    if self._partitionIdList is not None:
      proto.partitionIdList = self._partitionIdList

    proto.finishedLearning = bool(self._finishedLearning)
    proto.iterationIdx = self._iterationIdx

    if self._s is not None:
      proto.s = self._s.tolist()

    if self._vt is not None:
      proto.vt = self._vt.tolist()

    if self._mean is not None:
      proto.mean = self._mean.tolist()


  def __getstate__(self):
    """Return serializable state.

    This function will return a version of the __dict__.
    """
    state = self.__dict__.copy()
    return state


  def __setstate__(self, state):
    """Set the state of this object from a serialized state."""
    if "version" not in state:
      pass
    elif state["version"] == 1:
      pass
    elif state["version"] == 2:
      raise RuntimeError("Invalid deserialization of invalid KNNClassifier"
          "Version")

    # Backward compatibility
    if "_partitionIdArray" in state:
      state.pop("_partitionIdArray")

    if "minSparsity" not in state:
      state["minSparsity"] = 0.0

    self.__dict__.update(state)

    # Backward compatibility
    if "_partitionIdMap" not in state:
      self._rebuildPartitionIdMap(self._partitionIdList)

    # Set to new version
    self.version = KNNCLASSIFIER_VERSION
