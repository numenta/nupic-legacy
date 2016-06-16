#!/usr/bin/env python

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

"""
## @file
This file defines the k Nearest Neighbor classifier region.
"""
import numpy
from nupic.bindings.regions.PyRegion import PyRegion
from nupic.algorithms import KNNClassifier
from nupic.bindings.math import Random


class KNNClassifierRegion(PyRegion):
  """
  KNNClassifierRegion implements the k Nearest Neighbor classification algorithm.
  By default it will implement vanilla 1-nearest neighbor using the L2 (Euclidean)
  distance norm.  There are options for using different norms as well as
  various ways of sparsifying the input.

  Note: categories are ints >= 0.
  """

  __VERSION__ = 1


  @classmethod
  def getSpec(cls):
    ns = dict(
        description=KNNClassifierRegion.__doc__,
        singleNodeOnly=True,
        inputs=dict(
          categoryIn=dict(
            description='Vector of zero or more category indices for this input'
                         'sample. -1 implies no category.',
            dataType='Real32',
            count=0,
            required=True,
            regionLevel=True,
            isDefaultInput=False,
            requireSplitterMap=False),

          bottomUpIn=dict(
            description='Belief values over children\'s groups',
            dataType='Real32',
            count=0,
            required=True,
            regionLevel=False,
            isDefaultInput=True,
            requireSplitterMap=False),

          partitionIn=dict(
            description='Partition ID of the input sample',
            dataType='Real32',
            count=0,
            required=True,
            regionLevel=True,
            isDefaultInput=False,
            requireSplitterMap=False),

          auxDataIn=dict(
            description='Auxiliary data from the sensor',
            dataType='Real32',
            count=0,
            required=False,
            regionLevel=True,
            isDefaultInput=False,
            requireSplitterMap=False)
        ),


        outputs=dict(
          categoriesOut=dict(
          description='A vector representing, for each category '
                      'index, the likelihood that the input to the node belongs '
                      'to that category based on the number of neighbors of '
                      'that category that are among the nearest K.',
          dataType='Real32',
          count=0,
          regionLevel=True,
          isDefaultOutput=True),

          bestPrototypeIndices=dict(
          description='A vector that lists, in descending order of '
                      'the match, the positions of the prototypes '
                      'that best match the input pattern.',
          dataType='Real32',
          count=0,
          regionLevel=True,
          isDefaultOutput=False),

          categoryProbabilitiesOut=dict(
          description='A vector representing, for each category '
                      'index, the probability that the input to the node belongs '
                      'to that category based on the distance to the nearest '
                      'neighbor of each category.',
          dataType='Real32',
          count=0,
          regionLevel=True,
          isDefaultOutput=True),

        ),

        parameters=dict(
          learningMode=dict(
            description='Boolean (0/1) indicating whether or not a region '
                        'is in learning mode.',
            dataType='UInt32',
            count=1,
            constraints='bool',
            defaultValue=1,
            accessMode='ReadWrite'),

          inferenceMode=dict(
            description='Boolean (0/1) indicating whether or not a region '
                        'is in inference mode.',
            dataType='UInt32',
            count=1,
            constraints='bool',
            defaultValue=0,
            accessMode='ReadWrite'),

          acceptanceProbability=dict(
            description='During learning, inputs are learned with '
                        'probability equal to this parameter. '
                        'If set to 1.0, the default, '
                        'all inputs will be considered '
                        '(subject to other tests).',
            dataType='Real32',
            count=1,
            constraints='',
            defaultValue=1.0,
            #accessMode='Create'),
            accessMode='ReadWrite'), # and Create too

          confusion=dict(
            description='Confusion matrix accumulated during inference. '
                        'Reset with reset(). This is available to Python '
                        'client code only.',
            dataType='Handle',
            count=2,
            constraints='',
            defaultValue=None,
            accessMode='Read'),

          activeOutputCount=dict(
            description='The number of active elements in the '
                        '"categoriesOut" output.',
            dataType='UInt32',
            count=1,
            constraints='',
            defaultValue=0,
            accessMode='Read'),

          categoryCount=dict(
            description='An integer indicating the number of '
                        'categories that have been learned',
            dataType='UInt32',
            count=1,
            constraints='',
            defaultValue=None,
            accessMode='Read'),

          patternCount=dict(
            description='Number of patterns learned by the classifier.',
            dataType='UInt32',
            count=1,
            constraints='',
            defaultValue=None,
            accessMode='Read'),

          patternMatrix=dict(
            description='The actual patterns learned by the classifier, '
                        'returned as a matrix.',
            dataType='Handle',
            count=1,
            constraints='',
            defaultValue=None,
            accessMode='Read'),

          k=dict(
            description='The number of nearest neighbors to use '
                        'during inference.',
            dataType='UInt32',
            count=1,
            constraints='',
            defaultValue=1,
            accessMode='Create'),

          maxCategoryCount=dict(
            description='The maximal number of categories the '
                        'classifier will distinguish between.',
            dataType='UInt32',
            count=1,
            constraints='',
            defaultValue=2,
            accessMode='Create'),

          distanceNorm=dict(
            description='The norm to use for a distance metric (i.e., '
                        'the "p" in Lp-norm)',
            dataType='Real32',
            count=1,
            constraints='',
            defaultValue=2.0,
            accessMode='ReadWrite'),
            #accessMode='Create'),

          distanceMethod=dict(
            description='Method used to compute distances between inputs and'
              'prototypes. Possible options are norm, rawOverlap, '
              'pctOverlapOfLarger, and pctOverlapOfProto',
            dataType="Byte",
            count=0,
            constraints='enum: norm, rawOverlap, pctOverlapOfLarger, '
              'pctOverlapOfProto, pctOverlapOfInput',
            defaultValue='norm',
            accessMode='ReadWrite'),

          outputProbabilitiesByDist=dict(
            description='If True, categoryProbabilitiesOut is the probability of '
              'each category based on the distance to the nearest neighbor of '
              'each category. If False, categoryProbabilitiesOut is the '
              'percentage of neighbors among the top K that are of each category.',
            dataType='UInt32',
            count=1,
            constraints='bool',
            defaultValue=0,
            accessMode='Create'),

          distThreshold=dict(
            description='Distance Threshold.  If a pattern that '
                        'is less than distThreshold apart from '
                        'the input pattern already exists in the '
                        'KNN memory, then the input pattern is '
                        'not added to KNN memory.',
            dataType='Real32',
            count=1,
            constraints='',
            defaultValue=0.0,
            accessMode='ReadWrite'),

          inputThresh=dict(
            description='Input binarization threshold, used if '
                        '"doBinarization" is True.',
            dataType='Real32',
            count=1,
            constraints='',
            defaultValue=0.5,
            accessMode='Create'),

          doBinarization=dict(
            description='Whether or not to binarize the input vectors.',
            dataType='UInt32',
            count=1,
            constraints='bool',
            defaultValue=0,
            accessMode='Create'),

          useSparseMemory=dict(
            description='A boolean flag that determines whether or '
                        'not the KNNClassifier will use sparse Memory',
            dataType='UInt32',
            count=1,
            constraints='',
            defaultValue=1,
            accessMode='Create'),

          minSparsity=dict(
            description="If useSparseMemory is set, only vectors with sparsity"
                        " >= minSparsity will be stored during learning. A value"
                        " of 0.0 implies all vectors will be stored. A value of"
                        " 0.1 implies only vectors with at least 10% sparsity"
                        " will be stored",
            dataType='Real32',
            count=1,
            constraints='',
            defaultValue=0.0,
            accessMode='ReadWrite'),

          sparseThreshold=dict(
            description='If sparse memory is used, input variables '
                        'whose absolute value is less than this '
                        'threshold  will be stored as zero',
            dataType='Real32',
            count=1,
            constraints='',
            defaultValue=0.0,
            accessMode='Create'),

          relativeThreshold=dict(
            description='Whether to multiply sparseThreshold by max value '
                        ' in input',
            dataType='UInt32',
            count=1,
            constraints='bool',
            defaultValue=0,
            accessMode='Create'),

          winnerCount=dict(
            description='Only this many elements of the input are '
                       'stored. All elements are stored if 0.',
            dataType='UInt32',
            count=1,
            constraints='',
            defaultValue=0,
            accessMode='Create'),

          doSphering=dict(
            description='A boolean indicating whether or not data should'
              'be "sphered" (i.e. each dimension should be normalized such'
              'that its mean and variance are zero and one, respectively.) This'
              ' sphering normalization would be performed after all training '
              'samples had been received but before inference was performed. '
              'The dimension-specific normalization constants would then '
              ' be applied to all future incoming vectors prior to performing '
              ' conventional NN inference.',
            dataType='UInt32',
            count=1,
            constraints='bool',
            defaultValue=0,
            accessMode='Create'),

          SVDSampleCount=dict(
            description='If not 0, carries out SVD transformation after '
                          'that many samples have been seen.',
            dataType='UInt32',
            count=1,
            constraints='',
            defaultValue=0,
            accessMode='Create'),

          SVDDimCount=dict(
            description='Number of dimensions to keep after SVD if greater '
                        'than 0. If set to -1 it is considered unspecified. '
                        'If set to 0 it is consider "adaptive" and the number '
                        'is chosen automatically.',
            dataType='Int32',
            count=1,
            constraints='',
            defaultValue=-1,
            accessMode='Create'),

          fractionOfMax=dict(
            description='The smallest singular value which is retained '
                        'as a fraction of the largest singular value. This is '
                        'used only if SVDDimCount==0 ("adaptive").',
            dataType='UInt32',
            count=1,
            constraints='',
            defaultValue=0,
            accessMode='Create'),

          useAuxiliary=dict(
            description='Whether or not the classifier should use auxiliary '
                        'input data.',
            dataType='UInt32',
            count=1,
            constraints='bool',
            defaultValue=0,
            accessMode='Create'),

          justUseAuxiliary=dict(
            description='Whether or not the classifier should ONLUY use the '
                        'auxiliary input data.',
            dataType='UInt32',
            count=1,
            constraints='bool',
            defaultValue=0,
            accessMode='Create'),

          verbosity=dict(
            description='An integer that controls the verbosity level, '
                        '0 means no verbose output, increasing integers '
                        'provide more verbosity.',
            dataType='UInt32',
            count=1,
            constraints='',
            defaultValue=0 ,
            accessMode='ReadWrite'),

          keepAllDistances=dict(
            description='Whether to store all the protoScores in an array, '
                        'rather than just the ones for the last inference. '
                        'When this parameter is changed from True to False, '
                        'all the scores are discarded except for the most '
                        'recent one.',
            dataType='UInt32',
            count=1,
            constraints='bool',
            defaultValue=None,
            accessMode='ReadWrite'),

          replaceDuplicates=dict(
            description='A boolean flag that determines whether or'
                        'not the KNNClassifier should replace duplicates'
                        'during learning. This should be on when online'
                        'learning.',
            dataType='UInt32',
            count=1,
            constraints='bool',
            defaultValue=None,
            accessMode='ReadWrite'),

          cellsPerCol=dict(
            description='If >= 1, we assume the input is organized into columns, '
                        'in the same manner as the temporal pooler AND '
                        'whenever we store a new prototype, we only store the '
                        'start cell (first cell) in any column which is bursting.'
              'colum ',
            dataType='UInt32',
            count=1,
            constraints='',
            defaultValue=0,
            accessMode='Create'),

          maxStoredPatterns=dict(
            description='Limits the maximum number of the training patterns '
                        'stored. When KNN learns in a fixed capacity mode, '
                        'the unused patterns are deleted once the number '
                        'of stored patterns is greater than maxStoredPatterns'
                        'columns. [-1 is no limit] ',
            dataType='Int32',
            count=1,
            constraints='',
            defaultValue=-1,
            accessMode='Create'),
      ),
      commands=dict()
    )

    return ns


  def __init__(self,
               maxCategoryCount=0,
               bestPrototypeIndexCount=0,
               outputProbabilitiesByDist=False,
               k=1,
               distanceNorm=2.0,
               distanceMethod='norm',
               distThreshold=0.0,
               doBinarization=False,
               inputThresh=0.500,
               useSparseMemory=True,
               sparseThreshold=0.0,
               relativeThreshold=False,
               winnerCount=0,
               acceptanceProbability=1.0,
               seed=42,
               doSphering=False,
               SVDSampleCount=0,
               SVDDimCount=0,
               fractionOfMax=0,
               useAuxiliary=0,
               justUseAuxiliary=0,
               verbosity=0,
               replaceDuplicates=False,
               cellsPerCol=0,
               maxStoredPatterns=-1,
               minSparsity=0.0
               ):

    self.version = KNNClassifierRegion.__VERSION__

    # Convert various arguments to match the expectation
    # of the KNNClassifier
    if SVDSampleCount == 0:
      SVDSampleCount = None

    if SVDDimCount == -1:
      SVDDimCount = None
    elif SVDDimCount == 0:
      SVDDimCount = 'adaptive'

    if fractionOfMax == 0:
      fractionOfMax = None

    if useAuxiliary == 0:
      useAuxiliary = False

    if justUseAuxiliary == 0:
      justUseAuxiliary = False

    # KNN Parameters
    self.knnParams = dict(
        k=k,
        distanceNorm=distanceNorm,
        distanceMethod=distanceMethod,
        distThreshold=distThreshold,
        doBinarization=doBinarization,
        binarizationThreshold=inputThresh,
        useSparseMemory=useSparseMemory,
        sparseThreshold=sparseThreshold,
        relativeThreshold=relativeThreshold,
        numWinners=winnerCount,
        numSVDSamples=SVDSampleCount,
        numSVDDims=SVDDimCount,
        fractionOfMax=fractionOfMax,
        verbosity=verbosity,
        replaceDuplicates=replaceDuplicates,
        cellsPerCol=cellsPerCol,
        maxStoredPatterns=maxStoredPatterns,
        minSparsity=minSparsity
    )

    # Initialize internal structures
    self.outputProbabilitiesByDist = outputProbabilitiesByDist
    self.learningMode = True
    self.inferenceMode = False
    self._epoch = 0
    self.acceptanceProbability = acceptanceProbability
    self._rgen = Random(seed)
    self.confusion = numpy.zeros((1, 1))
    self.keepAllDistances = False
    self._protoScoreCount = 0
    self._useAuxiliary = useAuxiliary
    self._justUseAuxiliary = justUseAuxiliary

    # Sphering normalization
    self._doSphering = doSphering
    self._normOffset = None
    self._normScale  = None
    self._samples = None
    self._labels  = None

    # Debugging
    self.verbosity = verbosity

    # Taps
    self._tapFileIn = None
    self._tapFileOut = None

    self._initEphemerals()

    self.maxStoredPatterns = maxStoredPatterns
    self.maxCategoryCount = maxCategoryCount
    self._bestPrototypeIndexCount = bestPrototypeIndexCount


  def _getEphemeralAttributes(self):
    """
    List of attributes to not save with serialized state.
    """
    return ['_firstComputeCall', '_accuracy', '_protoScores',
      '_categoryDistances']


  def _initEphemerals(self):
    """
    Initialize attributes that are not saved with the checkpoint.
    """
    self._firstComputeCall = True
    self._accuracy = None
    self._protoScores = None
    self._categoryDistances = None

    self._knn = KNNClassifier.KNNClassifier(**self.knnParams)

    for x in ('_partitions', '_useAuxiliary', '_doSphering',
              '_scanInfo', '_protoScores'):
      if not hasattr(self, x):
        setattr(self, x, None)


  def __setstate__(self, state):
    """Set state from serialized state."""

    if 'version' not in state:
      self.__dict__.update(state)
    elif state['version'] == 1:

      # Backward compatibility
      if "doSelfValidation" in state:
        state.pop("doSelfValidation")

      knnState = state['_knn_state']
      del state['_knn_state']

      self.__dict__.update(state)
      self._initEphemerals()
      self._knn.__setstate__(knnState)
    else:
      raise RuntimeError("Invalid KNNClassifierRegion version for __setstate__")

    # Set to current version
    self.version = KNNClassifierRegion.__VERSION__


  def __getstate__(self):
    """Get serializable state."""
    state = self.__dict__.copy()
    state['_knn_state'] = self._knn.__getstate__()
    del state['_knn']

    for field in self._getEphemeralAttributes():
      del state[field]
    return state


  def initialize(self, dims, splitterMaps):
    assert tuple(dims) == (1,) * len(dims)


  def _getActiveOutputCount(self):
    if self._knn._categoryList:
      return int(max(self._knn._categoryList)+1)
    else:
      return 0

  activeOutputCount = property(fget=_getActiveOutputCount)


  def _getSeenCategoryCount(self):
    return len(set(self._knn._categoryList))

  categoryCount = property(fget=_getSeenCategoryCount)


  def _getPatternMatrix(self):

    if self._knn._M is not None:
      return self._knn._M
    else:
      return self._knn._Memory


  def _getAccuracy(self):

    n = self.confusion.shape[0]
    assert n == self.confusion.shape[1], "Confusion matrix is non-square."
    return self.confusion[range(n), range(n)].sum(), self.confusion.sum()

  accuracy = property(fget=_getAccuracy)


  def clear(self):

    self._knn.clear()


  def getAlgorithmInstance(self):
    """Returns instance of the underlying KNNClassifier algorithm object."""
    return self._knn


  def getParameter(self, name, index=-1):
    """
    Get the value of the parameter.

    @param name -- the name of the parameter to retrieve, as defined
            by the Node Spec.
    """
    if name == "patternCount":
      return self._knn._numPatterns
    elif name == "patternMatrix":
      return self._getPatternMatrix()
    elif name == "k":
      return self._knn.k
    elif name == "distanceNorm":
      return self._knn.distanceNorm
    elif name == "distanceMethod":
      return self._knn.distanceMethod
    elif name == "distThreshold":
      return self._knn.distThreshold
    elif name == "inputThresh":
      return self._knn.binarizationThreshold
    elif name == "doBinarization":
      return self._knn.doBinarization
    elif name == "useSparseMemory":
      return self._knn.useSparseMemory
    elif name == "sparseThreshold":
      return self._knn.sparseThreshold
    elif name == "winnerCount":
      return self._knn.numWinners
    elif name == "relativeThreshold":
      return self._knn.relativeThreshold
    elif name == "SVDSampleCount":
      v = self._knn.numSVDSamples
      return v if v is not None else 0
    elif name == "SVDDimCount":
      v = self._knn.numSVDDims
      return v if v is not None else 0
    elif name == "fractionOfMax":
      v = self._knn.fractionOfMax
      return v if v is not None else 0
    elif name == "useAuxiliary":
      return self._useAuxiliary
    elif name == "justUseAuxiliary":
      return self._justUseAuxiliary
    elif name == "doSphering":
      return self._doSphering
    elif name == "cellsPerCol":
      return self._knn.cellsPerCol
    elif name == "maxStoredPatterns":
      return self.maxStoredPatterns
    elif name == 'categoryRecencyList':
      return self._knn._categoryRecencyList
    else:
      # If any spec parameter name is the same as an attribute, this call
      # will get it automatically, e.g. self.learningMode
      return PyRegion.getParameter(self, name, index)


  def setParameter(self, name, index, value):
    """
    Set the value of the parameter.

    @param name -- the name of the parameter to update, as defined
            by the Node Spec.
    @param value -- the value to which the parameter is to be set.
    """
    if name == "learningMode":
      self.learningMode = bool(int(value))
      self._epoch = 0
    elif name == "inferenceMode":
      self._epoch = 0
      if int(value) and not self.inferenceMode:
        self._finishLearning()
      self.inferenceMode = bool(int(value))
    elif name == "distanceNorm":
      self._knn.distanceNorm = value
    elif name == "distanceMethod":
      self._knn.distanceMethod = value
    elif name == "keepAllDistances":
      self.keepAllDistances = bool(value)
      if not self.keepAllDistances:
        # Discard all distances except the latest
        if self._protoScores is not None and self._protoScores.shape[0] > 1:
          self._protoScores = self._protoScores[-1,:]
        if self._protoScores is not None:
          self._protoScoreCount = 1
        else:
          self._protoScoreCount = 0
    elif name == "verbosity":
      self.verbosity = value
      self._knn.verbosity = value
    else:
      return PyRegion.setParameter(self, name, index, value)


  def reset(self):

    self.confusion = numpy.zeros((1, 1))


  def doInference(self, activeInput):
    """Explicitly run inference on a vector that is passed in and return the
    category id. Useful for debugging."""

    prediction, inference, allScores = self._knn.infer(activeInput)
    return inference


  def enableTap(self, tapPath):
    """
    Begin writing output tap files.

    @param tapPath -- base name of the output tap files to write.
    """

    self._tapFileIn = open(tapPath + '.in', 'w')
    self._tapFileOut = open(tapPath + '.out', 'w')


  def disableTap(self):
    """Disable writing of output tap files. """

    if self._tapFileIn is not None:
      self._tapFileIn.close()
      self._tapFileIn = None
    if self._tapFileOut is not None:
      self._tapFileOut.close()
      self._tapFileOut = None


  def handleLogInput(self, inputs):
    """Write inputs to output tap file."""

    if self._tapFileIn is not None:
      for input in inputs:
        for k in range(len(input)):
          print >> self._tapFileIn, input[k],
        print >> self._tapFileIn


  def handleLogOutput(self, output):
    """Write outputs to output tap file."""
    #raise Exception('MULTI-LINE DUMMY\nMULTI-LINE DUMMY')
    if self._tapFileOut is not None:
      for k in range(len(output)):
        print >> self._tapFileOut, output[k],
      print >> self._tapFileOut


  def _storeSample(self, inputVector, trueCatIndex, partition=0):
    """
    Store a training sample and associated category label
    """

    # If this is the first sample, then allocate a numpy array
    # of the appropriate size in which to store all samples.
    if self._samples is None:
      self._samples = numpy.zeros((0, len(inputVector)), dtype=RealNumpyDType)
      assert self._labels is None
      self._labels = []

    # Add the sample vector and category lable
    self._samples = numpy.concatenate((self._samples, numpy.atleast_2d(inputVector)), axis=0)
    self._labels += [trueCatIndex]

    # Add the partition ID
    if self._partitions is None:
      self._partitions = []
    if partition is None:
      partition = 0
    self._partitions += [partition]


  def compute(self, inputs, outputs):
    """
    Process one input sample. This method is called by the runtime engine.

    NOTE: the number of input categories may vary, but the array size is fixed
    to the max number of categories allowed (by a lower region), so "unused"
    indices of the input category array are filled with -1s.

    TODO: confusion matrix does not support multi-label classification
    """

    #raise Exception('MULTI-LINE DUMMY\nMULTI-LINE DUMMY')
    #For backward compatibility
    if self._useAuxiliary is None:
      self._useAuxiliary = False

    # If the first time being called, then print potential warning messsages
    if self._firstComputeCall:
      self._firstComputeCall = False
      if self._useAuxiliary:
        #print "\n  Auxiliary input stream from Image Sensor enabled."
        if self._justUseAuxiliary == True:
          print "  Warning: You have chosen to ignore the image data and instead just use the auxiliary data stream."


    # Format inputs
    #childInputs = [x.wvector(0) for x in inputs["bottomUpIn"]]
    #inputVector = numpy.concatenate([x.array() for x in childInputs])
    inputVector = inputs['bottomUpIn']

    # Look for auxiliary input
    if self._useAuxiliary==True:
      #auxVector = inputs['auxDataIn'][0].wvector(0).array()
      auxVector = inputs['auxDataIn']
      if auxVector.dtype != numpy.float32:
        raise RuntimeError, "KNNClassifierRegion expects numpy.float32 for the auxiliary data vector"
      if self._justUseAuxiliary == True:
        #inputVector = inputs['auxDataIn'][0].wvector(0).array()
        inputVector = inputs['auxDataIn']
      else:
        #inputVector = numpy.concatenate([inputVector, inputs['auxDataIn'][0].wvector(0).array()])
        inputVector = numpy.concatenate([inputVector, inputs['auxDataIn']])

    # Logging
    #self.handleLogInput(childInputs)
    self.handleLogInput([inputVector])

    # Read the category.
    assert "categoryIn" in inputs, "No linked category input."
    categories = inputs['categoryIn']

    # Read the partition ID.
    if "partitionIn" in inputs:
      assert len(inputs["partitionIn"]) == 1, "Must have exactly one link to partition input."
      partInput = inputs['partitionIn']
      assert len(partInput) == 1, "Partition input element count must be exactly 1."
      partition = int(partInput[0])
    else:
      partition = None


    # ---------------------------------------------------------------------
    # Inference (can be done simultaneously with learning)
    if self.inferenceMode:
      categoriesOut = outputs['categoriesOut']
      probabilitiesOut = outputs['categoryProbabilitiesOut']

      # If we are sphering, then apply normalization
      if self._doSphering:
        inputVector = (inputVector + self._normOffset) * self._normScale

      nPrototypes = 0
      if "bestPrototypeIndices" in outputs:
        #bestPrototypeIndicesOut = outputs["bestPrototypeIndices"].wvector()
        bestPrototypeIndicesOut = outputs["bestPrototypeIndices"]
        nPrototypes = len(bestPrototypeIndicesOut)

      winner, inference, protoScores, categoryDistances = \
                  self._knn.infer(inputVector, partitionId=partition)



      if not self.keepAllDistances:
        self._protoScores = protoScores
      else:
        # Keep all prototype scores in an array
        if self._protoScores is None:
          self._protoScores = numpy.zeros((1, protoScores.shape[0]),
                                          protoScores.dtype)
          self._protoScores[0,:] = protoScores#.reshape(1, protoScores.shape[0])
          self._protoScoreCount = 1
        else:
          if self._protoScoreCount == self._protoScores.shape[0]:
            # Double the size of the array
            newProtoScores = numpy.zeros((self._protoScores.shape[0] * 2,
                                          self._protoScores.shape[1]),
                                          self._protoScores.dtype)
            newProtoScores[:self._protoScores.shape[0],:] = self._protoScores
            self._protoScores = newProtoScores
          # Store the new prototype score
          self._protoScores[self._protoScoreCount,:] = protoScores
          self._protoScoreCount += 1
      self._categoryDistances = categoryDistances


      # --------------------------------------------------------------------
      # Compute the probability of each category
      if self.outputProbabilitiesByDist:
        scores = 1.0 - self._categoryDistances
      else:
        scores = inference

      # Probability is simply the scores/scores.sum()
      total = scores.sum()
      if total == 0:
        numScores = len(scores)
        probabilities = numpy.ones(numScores) / numScores
      else:
        probabilities = scores / total


      # -------------------------------------------------------------------
      # Fill the output vectors with our results
      nout = min(len(categoriesOut), len(inference))
      categoriesOut.fill(0)
      categoriesOut[0:nout] = inference[0:nout]

      probabilitiesOut.fill(0)
      probabilitiesOut[0:nout] = probabilities[0:nout]

      if self.verbosity >= 1:
        print "KNNRegion: categoriesOut: ", categoriesOut[0:nout]
        print "KNNRegion: probabilitiesOut: ", probabilitiesOut[0:nout]

      if self._scanInfo is not None:
        self._scanResults = [tuple(inference[:nout])]

      # Update the stored confusion matrix.
      for category in categories:
        if category >= 0:
          dims = max(category+1, len(inference))
          oldDims = len(self.confusion)
          if oldDims < dims:
            confusion = numpy.zeros((dims, dims))
            confusion[0:oldDims, 0:oldDims] = self.confusion
            self.confusion = confusion
          self.confusion[inference.argmax(), category] += 1

      # Calculate the best prototype indices
      if nPrototypes > 1:
        bestPrototypeIndicesOut.fill(0)
        if categoryDistances is not None:
          indices = categoryDistances.argsort()
          nout = min(len(indices), nPrototypes)
          bestPrototypeIndicesOut[0:nout] = indices[0:nout]
      elif nPrototypes == 1:
        if (categoryDistances is not None) and len(categoryDistances):
          bestPrototypeIndicesOut[0] = categoryDistances.argmin()
        else:
          bestPrototypeIndicesOut[0] = 0

      # Logging
      self.handleLogOutput(inference)

    # ---------------------------------------------------------------------
    # Learning mode
    if self.learningMode:
      if (self.acceptanceProbability < 1.0) and \
            (self._rgen.getReal64() > self.acceptanceProbability):
        pass

      else:
        # Accept the input
        for category in categories:
          if category >= 0:
            # category values of -1 are to be skipped (they are non-categories)
            if self._doSphering:
              # If we are sphering, then we can't provide the data to the KNN
              # library until we have computed per-dimension normalization
              # constants. So instead, we'll just store each training sample.
              self._storeSample(inputVector, category, partition)
            else:
              # Pass the raw training sample directly to the KNN library.
              self._knn.learn(inputVector, category, partition)

    self._epoch += 1


  def getCategoryList(self):
    """
    Public API for returning the category list
    This is a required API of the NearestNeighbor inspector.

    It returns an array which has one entry per stored prototype. The value
    of the entry is the category # of that stored prototype.
    """

    return self._knn._categoryList


  def removeCategory(self, categoryToRemove):
    return self._knn.removeCategory(categoryToRemove)


  def getLatestDistances(self):
    """
    Public API for returning the full scores
    (distance to each prototype) from the last
    compute() inference call.
    This is a required API of the NearestNeighbor inspector.

    It returns an array which has one entry per stored prototype. The value
    of the entry is distance of the most recenty inferred input from the
    stored prototype.
    """
    if self._protoScores is not None:
      if self.keepAllDistances:
        return self._protoScores[self._protoScoreCount - 1,:]
      else:
        return self._protoScores
    else:
      return None


  def getAllDistances(self):
    """
    Return all the prototype distances from all computes available.

    Like getLatestDistances, but returns all the scores if more than one set is
    available. getLatestDistances will always just return one set of scores.
    """

    if self._protoScores is None:
      return None
    return self._protoScores[:self._protoScoreCount, :]


  def calculateProbabilities(self):
    # Get the scores, from 0 to 1
    scores = 1.0 - self._categoryDistances

    # Probability is simply the score/scores.sum()
    total = scores.sum()
    if total == 0:
      numScores = len(scores)
      return numpy.ones(numScores) / numScores

    return scores / total


  def _finishLearning(self):
    """Does nothing. Kept here for API compatibility """
    if self._doSphering:
      self._finishSphering()

    self._knn.finishLearning()

    # Compute leave-one-out validation accuracy if
    # we actually received non-trivial partition info
    self._accuracy = None


  def _finishSphering(self):
    """
    Compute normalization constants for each feature dimension
    based on the collected training samples.  Then normalize our
    training samples using these constants (so that each input
    dimension has mean and variance of zero and one, respectively.)
    Then feed these "sphered" training samples into the underlying
    SVM model.
    """

    # If we are sphering our data, we need to compute the
    # per-dimension normalization constants
    # First normalize the means (to zero)
    self._normOffset = self._samples.mean(axis=0) * -1.0
    self._samples += self._normOffset
    # Now normalize the variances (to one).  However, we need to be
    # careful because the variance could conceivably be zero for one
    # or more dimensions.
    variance = self._samples.var(axis=0)
    variance[numpy.where(variance == 0.0)] = 1.0
    self._normScale  = 1.0 / numpy.sqrt(variance)
    self._samples *= self._normScale

    # Now feed each "sphered" sample into the SVM library
    for sampleIndex in range(len(self._labels)):
      self._knn.learn(self._samples[sampleIndex],
                      self._labels[sampleIndex],
                      self._partitions[sampleIndex])


  def _arraysToLists(self, samplesArray, labelsArray):

    labelsList = list(labelsArray)
    samplesList = [[float(y) for y in x] for x in [list(x) for x in samplesArray]]
    return samplesList, labelsList


  def getOutputElementCount(self, name):
    """This method will be called only when the node is used in nuPIC 2"""
    if name == 'categoriesOut':
      return self.maxCategoryCount
    elif name == 'categoryProbabilitiesOut':
      return self.maxCategoryCount
    elif name == 'bestPrototypeIndices':
      return self._bestPrototypeIndexCount if self._bestPrototypeIndexCount else 0
    else:
      raise Exception('Unknown output: ' + name)



if __name__=='__main__':
  from nupic.engine import Network
  n = Network()
  classifier = n.addRegion(
  'classifier',
  'py.KNNClassifierRegion',
  '{ maxCategoryCount: 48, SVDSampleCount: 400, ' +
  '  SVDDimCount: 20, distanceNorm: 0.6 }')
