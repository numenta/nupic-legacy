
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

"""
## @file
SVMClassifierNode implements Support Vector Machines (SVMs)
"""

import math
import random
import logging

import numpy
from nupic.pynodes.PyNode import (PyNode,
                                  NodeSpec,
                                  NodeSpecItem,
                                  RealTypeName,
                                  RealNumpyDType)
from nupic.pynodes import PyNode as PyNodeModule
from nupic.algorithms import svm_01, svm_dense
from nupic.analysis.memoryAwareness import MemoryAwareness


_kKernelTypes = ["rbf", "linear"]



class SVMClassifierNode(PyNode, MemoryAwareness):
  """
  SVMClassifierNode implements Support Vector Machines (SVMs), which can be used to
  perform supervised learning by mapping a set of top-level groups beliefs onto
  a set of category labels. The node is a wrapper around a modified version
  of the libsvm library.
  """

  def __init__(self,
      categoriesOut=2,
      # SVM parameter ranges
      minC=0.0,
      maxC=0.0,
      minGamma=0.0,
      maxGamma=0.0,
      kernelType='rbf',
      # Latin Hypercube sampling (LHS)
      numSamplesPerRecursion=1,
      numRecursions=0,
      contractionFactor=0.3,
      numCrossValidations=5,
      # Implementation
      convEpsilon=0.01,
      useSparseSvm=False,
      inputThresh=0.500,
      useProbabilisticSvm=True,
      doSphering=False,
      deterministic=False,
      nta_cpp_svm_seed=-1,
      # PCA
      numSVDSamples=None,
      numSVDDims=None,
      fractionOfMax=None,
      useAuxiliary=False,
      justUseAuxiliary=False,
      discardProblem=True,  # Set to False to keep data for PCA visualizer
      # KNN-type stuff
      keepSamples=False,  # Keep the original inputs around
      calculateDistances=False,  # Calculate and store distances to orig. inputs
      nta_monitorMemory=False,
    ):
    """
    @param categoriesOut -- The maximum number of distinct category
          labels that can be learned.
    """
    MemoryAwareness.__init__(self)
    self.clear()
    self._firstComputeCall = True
    self._inputVector = None
    self._scanInfo = None
    self._scanResults = None

    # SVM parameters
    self.C = minC
    self.minC = minC
    self.maxC = maxC
    self.gamma = minGamma
    self.minGamma = minGamma
    self.maxGamma = maxGamma
    self._kernelType = kernelType

    # Latin Hypercube Sampling
    self.numSamplesPerRecursion = numSamplesPerRecursion
    self.numRecursions = numRecursions
    self.contractionFactor = contractionFactor
    self.numCrossValidations = numCrossValidations

    # Bindings parameters
    self.convEpsilon = convEpsilon
    self.useSparseSvm = useSparseSvm
    self.inputThresh = inputThresh
    self.useProbabilisticSvm = useProbabilisticSvm
    self.doSphering = doSphering
    self.deterministic = deterministic
    self.cpp_svm_seed = nta_cpp_svm_seed

    # PCA
    self._numSVDSamples = numSVDSamples
    self._numSVDDims = numSVDDims
    self._fractionOfMax = fractionOfMax
    self._useAuxiliary = useAuxiliary
    self._justUseAuxiliary = justUseAuxiliary
    self._auxInputLen = None
    if numSVDDims=='adaptive':
      self._adaptiveSVDDims = True
    else:
      self._adaptiveSVDDims = False
    self.discardProblem = discardProblem

    # KNN-type stuff
    self.keepSamples = keepSamples
    self.calculateDistances = calculateDistances

    # Memory monitoring
    self._enableMonitoring(nta_monitorMemory)
    self._initRandom()
    self.clear()

  def clear(self):
    """Clear all persistent internal state."""

    self._learningMode = True
    self._inferenceMode = False
    self._autoTuningData = False
    self._inputWidth = None
    self._catIdMap = None
    self._svm = None
    self._svmParams = None
    self._samples = None
    self._labels  = None
    self._partitionIds = None
    self._upcomingPartitionIds = None
    # Support for using non-training samples for
    # (C, Gamma) optimization
    self._autoTuneSamples      = None
    self._autoTuneLabels       = None
    self._autoTunePartitionIds = None

    # We operate in two modes:
    #   'classification' - the SVM is used for top-level classification
    #   'feedback' - the SVM is a "temporary" classified whose real purpose
    #                is simply to identify the most useful features
    #                so that this information can be fed back to the
    #                feature selection stage for pruning purposes.
    # The only difference is the choice of kernel; for 'classification'
    # mode, then kernel is selected based on the value of the parameter
    # 'kernelType'.  But in 'feedback' mode, the kernel is always
    # of type 'linear' regardless of the value of 'kernelType'.
    self._mode = 'classification'

    # Sphering normalization
    self._normOffset = None
    self._normScale  = None

    # PCA
    self._numPatterns = 0
    self._s = None
    self._vt = None
    self._mean = None

    # KNN-type stuff
    self.distances = None
    self._distanceCount = 0


  def _initRandom(self):
    """
    Create and seed random number generator.
    """
    # Create PRNG
    self._rng = random.Random()
    # Seed
    if self.deterministic:
      self._rng.seed(42)
    else:
      self._rng.seed()

  def _setInferenceMode(self, parameterValue):
    # If inference mode is being turned on, build the SVM model and turn off learning mode
    # This node only supports a one-time switch from learning mode to inference mode
    value = bool(int(parameterValue))
    if self._learningMode and value:
      self._finishLearning()
    assert self._inferenceMode == value

  inferenceMode = property(
      fget=lambda self: self._inferenceMode,
      fset=_setInferenceMode,
      doc="""Boolean indicating whether or not a node
          is in inference mode"""
    )

  def _setLearningMode(self, parameterValue):
    # If learning mode is being turned off, build the SVM model and turn on inference mode
    # This node only supports a one-time switch from learning mode to inference mode
    value = bool(int(parameterValue))
    if self._learningMode and not value:
      self._finishLearning()
    assert self._learningMode == value

  learningMode = property(
      fget=lambda self: self._learningMode,
      fset=_setLearningMode,
      doc="""Boolean indicating whether or not a node
          is in learning mode"""
    )

  def _setMode(self, parameterValue):
    # We can only change this before we have received our first compute()
    # call.  Otherwise it is a runtime error.
    if self._svm is not None:
      raise RuntimeError, "SVMClassifierNode 'mode' parameter cannot be changed" \
                          "after first compute() call"
    self._mode = parameterValue

  mode = property(
      fget=lambda self: self._mode,
      fset=_setMode,
      doc="""We operate in two modes: 'classification' - the SVM is
          used for top-level classification; 'feedback' - the SVM is a "temporary"
          classified whose real purpose is simply to identify the most useful
          features so that this information can be fed back to the feature
          selection stage for pruning purposes.  The only difference is the
          choice of kernel; for 'classification' mode, then kernel is selected
          based on the value of the parameter 'kernelType'.  But in 'feedback'
          mode, the kernel is always of type 'linear' regardless of the value
          of 'kernelType'."""
    )

  def _setKernelType(self, parameterValue):
    # Convert in case they passed an integer, since technically we are an
    # enum...
    try:    parameterValue = _kKernelTypes[parameterValue]
    except: pass
    self._kernelType = parameterValue

  kernelType = property(
      fget=lambda self: self._kernelType,
      fset=_setKernelType,
      # Doc provided with constraints in NodeSpec.
    )

  def _set_nta_cpp_svm_seed(self, parameterValue):
    self.cpp_svm_seed = parameterValue
  nta_cpp_svm_seed = property(fget=lambda self: self.cpp_svm_seed,
                              fset=_set_nta_cpp_svm_seed)


  def compute(self, nodeInfo, inputs, outputs):
    """
    Process one input sample.
    This method is called by the runtime engine.
    """

    # If the first time being called, then print potential warning messsages
    if self._firstComputeCall:
      self._firstComputeCall = False
      if self._useAuxiliary:
#        print "\n  Auxiliary input stream from Image Sensor enabled."
        if self._justUseAuxiliary == True:
          print "  Warning: You have chosen to ignore the image data and instead just use the auxiliary data stream."

    if self._scanInfo is not None:
      # The input is much larger than what we've been trained on
      # Sweep across it, assembling the outputs in a data structure
      self._scan(inputs)
      return

    # Assemble inputs
    childInputs = [x.wvector(0) for x in inputs['bottomUpIn']]
    inputVector = numpy.concatenate([x.array() for x in childInputs])

#    # Look for auxiliary input
#    if self._useAuxiliary==True:
#      auxVector = inputs['auxDataIn'][0].wvector(0).array()
#      if auxVector.dtype != numpy.float32:
#        raise RuntimeError, "SVMClassifierNode expects numpy.float32 for the auxiliary data vector"
#      if self._justUseAuxiliary == True:
#        inputVector = inputs['auxDataIn'][0].wvector(0).array()
#      else:
#        inputVector = numpy.concatenate([inputVector, inputs['auxDataIn'][0].wvector(0).array()])

    # Look for auxiliary input
    if self._useAuxiliary:
      auxVector = inputs['auxDataIn'][0].wvector(0).array()
      if auxVector.dtype != numpy.float32:
        raise RuntimeError, "SVMClassifierNode expects numpy.float32 for the auxiliary data vector"
      if self._justUseAuxiliary == True:
        inputVector = auxVector
      else:
        inputVector = numpy.concatenate([inputVector, auxVector])
    else:
      auxVector = numpy.array([])

    if self._auxInputLen == None:
      self._auxInputLen = len(auxVector)

    # Initialize data structures the first time
    if self._inputWidth is None:
      self._initDataStructures(len(inputVector))

    # Learn
    if self._learningMode:
      # Extract category label
      catInput = int(inputs["categoryIn"][0].wvector(0)[0])

      # Project the vector onto the PCA basis if present
      if self._vt is not None:
        inputVector = numpy.dot(self._vt, inputVector - self._mean)
        if self._useAuxiliary and not self._justUseAuxiliary:
          inputVector = numpy.concatenate([inputVector, auxVector])

      if self._upcomingPartitionIds:
        partitionId = self._upcomingPartitionIds.pop(0)
      else:
        partitionId = None

      # Perform learning
      self._learn(inputVector, catInput, partitionId)

      # Perform PCA if it is time to do so
      if self._vt is None and self._numSVDDims is not None \
          and self._numSVDSamples is not None \
          and self._samples.shape[0] == self._numSVDSamples:
        self.computeSVD()

    # Inference
    elif self._inferenceMode:
      # Project the vector onto the PCA basis if present
      if self._vt is not None:
        if self._useAuxiliary and not self._justUseAuxiliary:
          auxVector = inputVector[len(inputVector)-self._auxInputLen:]
          inputVector = inputVector[:len(inputVector)-self._auxInputLen]
          inputVector = numpy.dot(self._vt, inputVector - self._mean)
          inputVector = numpy.concatenate([inputVector, auxVector])
        else:
          inputVector = numpy.dot(self._vt, inputVector - self._mean)

      # Save the input vector, in case the distances are requested later
      self._inputVector = inputVector

      allOutputs = outputs['categoriesOut'].wvector()
      inferenceResult = self._infer(inputVector)
      allOutputs.fill(0)

      # Convert from internal indices back to ImageSensor's IDs
      # This is necessary to calculate accuracy by comparing our outputs to
      # the true category from the sensor
      remap = [self.catIndexToId(i) for i in xrange(len(self._catIdMap))]
      out = numpy.zeros(max(remap)+1)
      out[remap] = inferenceResult[0:len(self._catIdMap)]
      nout = min(len(allOutputs), len(out))
      allOutputs[0:nout] = out[0:nout]


  def _scan(self, inputs):
    """
    Run scanning inference and store the results.

    The input is from many nodes, but we were trained with just a single child.
    Perform inference on each node separately and store in a list.
    """

    childInputs = [x.wvector(0).array() for x in inputs['bottomUpIn']]
    self._scanResults = []

    for inputVector in childInputs:

      # Project the vector onto the PCA basis if present
      if self._vt is not None:
        inputVector = numpy.dot(self._vt, inputVector - self._mean)

      # Run inference
      inferenceResult = self._infer(inputVector)

      # Convert from internal indices back to ImageSensor's IDs
      # This is necessary to calculate accuracy by comparing our outputs to
      # the true category from the sensor
      remap = [self.catIndexToId(i) for i in xrange(len(self._catIdMap))]
      out = numpy.zeros(max(remap)+1)
      out[remap] = inferenceResult[0:len(self._catIdMap)]

      # Store
      self._scanResults.append(tuple(out))


  # @todo -- Modernize nodeSpec
  def getNodeSpec(self):
    """
    Return the NodeSpec for this PyNode.
    """

    parent = PyNode.getNodeSpec(self)
    out = NodeSpec(
        description=SVMClassifierNode.__doc__,
        inputs=[
          NodeSpecItem(name="categoryIn", type=RealTypeName,
                       description="""Category of the input sample"""),
          NodeSpecItem(name="bottomUpIn", type=RealTypeName,
                       description="""Belief values over children's groups"""),
           NodeSpecItem(name="auxDataIn", type=RealTypeName,
                        description="""Auxiliary data from the sensor""")
          ],
        outputs=[
          NodeSpecItem(name="categoriesOut", type=RealTypeName,
                      description="A vector representing, for each category" \
                                   " index, the likelihood that the input to" \
                                   " the node belongs to that category.")
          ],
        parameters=[
          NodeSpecItem(name="learningMode", type="bool", constraints="bool", access="gs", value = True,
                       description="Boolean indicating whether or not a node " \
                                   "is in learning mode"),
          NodeSpecItem(name="inferenceMode", type="bool", constraints="bool", access="gs", value = False,
                       description="Boolean indicating whether or not a node " \
                                   "is in inference mode"),
          NodeSpecItem(name="activeOutputCount", type="uint", access="g",
                       description="The number of active elements in the "    \
                                   "'categoriesOut' output."),
          NodeSpecItem(name="categoryCount", type="uint", access="g",
                       description="An integer indicating the number of "    \
                                   "categories that have been learned"),
          NodeSpecItem(name="C", type="float", access="g", value = 0.0,
                       description="""The current value of C, an SVM parameter that
                          influences the error rate. If numRecursions==0, this value is
                          used to build the SVM; otherwise, minC and maxC are used,
                          and this parameter is changed to the best value afterwards."""),
          NodeSpecItem(name="minC", type="float", access="cg", value = 0.0,
                       description="""The minimum value of C, an SVM parameter that
                          influences the error rate. SVMClassifierNode will
                          perform an optimization process in order to find the
                          value of C that minimizes error
                          rate on the set of training samples."""),
          NodeSpecItem(name="maxC", type="float", access="cg", value = 0.0,
                       description="""The maximum value of C, an SVM parameter that
                          influences the error rate."""),
          NodeSpecItem(name="gamma", type="float", access="g", value = 0.0,
                       description="""The current value of gamma, an SVM parameter that
                          influences the error rate. If numRecursions==0, this value is
                          used to build the SVM; otherwise, minGamma and maxGamma are used,
                          and this parameter is changed to the best value afterwards."""),
          NodeSpecItem(name="minGamma", type="float", access="cg", value = 0.0,
                       description="""The minimum value of Gamma, an SVM parameter that
                          influences the error rate.  SVMClassifierNode will perform an
                          optimization process in order to find the value of Gamma that
                          minimizes error rate on the set of training samples."""),
          NodeSpecItem(name="maxGamma", type="float", access="cg", value = 0.0,
                       description="""The maximum value of Gamma, an SVM parameter that
                          influences the error rate."""),
          NodeSpecItem(name="kernelType", type="string", access="cgs", value= "rbf",
                       description="""Specifies the type of kernel to use.  Valid choices
                          are: 'rbf' (for radial basis function kernel), or 'linear' (for
                          linear kernel.)  Default is 'rbf'.""",
                          constraints="enum: %s,%s" % (
                                        ",".join(_kKernelTypes),
                                        ",".join(map(str, xrange(len(_kKernelTypes))))
                                      )),
          NodeSpecItem(name="numRecursions", type="uint", access="cgs", value = 0,
                       description="""The number of rounds of recursive Latin Hypercube Sampling
                          to perform.  If set to 0 (the default), then no parameter search is
                          performed, and instead the values 'minC' and 'minGamma' are used."""),
          NodeSpecItem(name="numSamplesPerRecursion", type="uint", access="gs", value = 1,
                       description="""The number of samples we will test in each round of
                          recursive Latin Hypercube Sampling."""),
          NodeSpecItem(name="contractionFactor", type="float", access="cgs", value = 0.3,
                       description="""The fraction of the C and Gamma sampling space that we will
                          sample with each successive round of Latin Hypercube sampling."""),
          NodeSpecItem(name="numCrossValidations", type="uint", access="cg", value = 5,
                       description="""The number of cross validation steps
                          steps that are used to estimate the error rate for a given
                          set of C and Gamma values.  Increasing this number will yield
                          better error rate estimates, and hence more optimal values
                          for C and Gamma, but will take longer to complete the
                          learning process."""),
          NodeSpecItem(name="autoTuningData", type="bool", constraints="bool", access="gs",
                       description="""Data presented to the classifier while autoTuningData is set to True
                          will be used as a test set for the auto-tuning phase and is NOT
                          learned by the node. The auto-tuning phase is performed at the
                          end of learning (when inferenceMode is first set to True)."""),
          NodeSpecItem(name="convEpsilon", type="float", access="cg", value = 0.01,
                       description="""A parameter that controls the convergence
                          criterion used to halt the search for optimal SVM hyperplanes."""),
          NodeSpecItem(name="useSparseSvm", type="bool", constraints="bool", access="gc", value = False,
                       description="""A boolean that controls whether input vectors
                          should be binarized during learning and inference."""),
          NodeSpecItem(name="inputThresh", type="float", access="cg", value = 0.5,
                       description="""A floating point value that establishes the threshold
                          used for binarizing input vectors during learning and inference.
                          If 'useSparseSvm' is False, then this parameter has no effect."""),
          NodeSpecItem(name="useProbabilisticSvm", type="bool", constraints="bool", access="cg", value = True,
                       description="""A boolean that controls whether or not to
                          build an underlying SVM model that is capable of estimating
                          probabilistic beliefs during inference, as opposed to simply
                          determining a single winner-take-all category."""),
          NodeSpecItem(name="doSphering", type="bool", constraints="bool", access="cg", value = False,
                       description="""A boolean indicating whether or not data should
                          be "sphered" (i.e., each dimension should be normalized such that
                          its mean and variance are zero and one, respectively.)  This
                          sphering normalization would be performed after all training
                          samples had been received but before the actual SVM model was
                          built.  The dimension-specific normalization constants would then
                          be applied to all future incoming vectors prior to submitting them
                          to the SVM library for inference."""),
          NodeSpecItem(name="mode", type="string", access="gs",
                       description="""We operate in two modes: 'classification' - the SVM is
                          used for top-level classification; 'feedback' - the SVM is a "temporary"
                          classified whose real purpose is simply to identify the most useful
                          features so that this information can be fed back to the feature
                          selection stage for pruning purposes.  The only difference is the
                          choice of kernel; for 'classification' mode, then kernel is selected
                          based on the value of the parameter 'kernelType'.  But in 'feedback'
                          mode, the kernel is always of type 'linear' regardless of the value
                          of 'kernelType'."""),
          NodeSpecItem(name="deterministic", type="bool", constraints="bool", access="cgs", value = False,
                      description="""Set true to seed random number generator so that the SVM
                          picks the same hyperplanes each time during learning. Only has an
                          effect when finishLearning is called."""),
          NodeSpecItem(name='numSVDSamples', type='PyObject', access='gcs', value=None,
                       description="""If not None, carries out SVD transformation after
                          that many samples have been seen. Otherwise, performs SVD when
                          switching to inference."""),
          NodeSpecItem(name='numSVDDims', type='PyObject', access='gc', value=None,
                       description="""Number of dimensions to keep after SVD.
                          If set to 'adaptive' the number is chosen automatically."""),
          NodeSpecItem(name='fractionOfMax', type='PyObject', access='gc', value=None,
                       description="""The smallest singular value which is retained
                          as a fraction of the largest singular value. This is used
                          only if numSVDDims=='adaptive'."""),
          NodeSpecItem(name='useAuxiliary', type='PyObject', access='gc', value=None,
                       description="""Whether or not the classifier should use auxiliary
                          input data."""),
          NodeSpecItem(name='justUseAuxiliary', type='PyObject', access='gc', value=None,
                       description="""Whether or not the classifier should ONLY use the auxiliary
                          input data."""),
          NodeSpecItem(name='discardProblem', type='bool', access='cgs',
                       description="""Whether to discard extra SVM data to save space. Set to False
                          to preserve the data for the PCA visualizer."""),
          NodeSpecItem(name='nta_cpp_svm_seed', type='int', access='cgs', value=-1,
                       description="""Seed for the C++ RNG"""),
          NodeSpecItem(name='keepSamples', type='bool', access='cgs', value=False),
          NodeSpecItem(name='calculateDistances', type='bool', access='cgs', value=False),
          NodeSpecItem(name='nta_monitorMemory', type='bool', access='cgs',
                       description="""Whether to spawn an internal thread that monitors the
                          amount of memory being consumed during processing and reports
                          statistics""", value=False),
          NodeSpecItem(name="numTrainingSamples", type="int", access="g", value = 0,
                       description="""Returns the current number of training samples."""),
          ]
      )
    return out + parent


  def catIndexToId(self, catIndex):
    """
    Map category indices (internal) to category IDs (external).
    """
    return self._catIdMap[catIndex]


  def _getHyperplanes(self):
    """
    Return a numpy array containing the complete set of hyperplanes used
    by the (trained) SVM classifier.  In general, there will be N(N-1)/2
    hyperplanes, where N is the number of categories.  Each hyperplane
    will be returned as a row within the numpy array; each row will be
    of dimensionality equal to the number of "features" presented to the
    SVM during training and inference.
    """
    hyperplanes = self._svm.get_model().get_hyperplanes()
    return hyperplanes


  def simulateTrainingSample(self, inputWidth=None, category=None, partitionId=None):
    """
    Debugging/profiling utility method to allow tools to
    simulate the presentation of training sample.
    """

    if inputWidth is None:
      inputWidth = self._inputWidth
    if category is None:
      category = 0

    if self._samples is None:
      self._samples = numpy.zeros((0, inputWidth), dtype=RealNumpyDType)
      assert self._labels is None
      self._labels = []
      assert self._partitionIds is None
      self._partitionIds = []

    # Add the sample vector and category lable
    sample = numpy.random.random((1, inputWidth))
    self._samples = numpy.concatenate((self._samples, sample), axis=0)
    self._labels += [category]
    if partitionId is not None:
      self._partitionIds.append(partitionId)


  def getParameter(self, parameterName, nodeSet=""):
    """
    Get the value of a parameter.

    Note: this method may be overridden by derived classes, but if so, then
    the derived class should invoke this base method if 'parameterName'
    is unknown to the derived class.

    @param parameterName -- the name of the parameter to retrieve, as defined
            by the Node Spec.
    """
    if parameterName == "hyperplanes":
      return self._getHyperplanes()
    elif parameterName in ("numCategoriesSeen", "categoryCount"):
      if self._inferenceMode:
        # Use the catIdMap, which is created during finishLearning
        return len(self._catIdMap)
      elif self._labels:
        # Use the labels, which are not thrown away until finishLearning
        # Don't count -1, if it appears
        return len(set(self._labels)) - int(-1 in self._labels)
      else:
        return 0
    elif parameterName == "numSVDSamples":
      return self._numSVDSamples
    elif parameterName == "numSVDDims":
      return self._numSVDDims
    elif parameterName == "fractionOfMax":
      return self._fractionOfMax
    elif parameterName == 'useAuxiliary':
      return self._useAuxiliary
    elif parameterName == "numTrainingSamples":
      return self.getNumTrainingSamples()
    else:
      return PyNode.getParameter(self, parameterName, nodeSet)

  def setParameter(self, parameterName, parameterValue, nodeSet=""):
    """Set the value of a parameter."""

    if parameterName == "numSVDSamples":
      self._numSVDSamples = parameterValue

    else:
      PyNode.setParameter(self, parameterName, parameterValue, nodeSet)


  def getNumTrainingSamples(self):
    if self._samples is None:
      numSamples = 0
    else:
      numSamples = self._samples.shape[0]
    return numSamples


  def _getActiveOutputCount(self):
    if self._catIdMap is not None:
      # Use the catIdMap, which is created during finishLearning
      return max(self._catIdMap)+1
    elif self._labels is not None:
      # Use the labels, which are not thrown away until finishLearning
      return max(self._labels)+1
    else:
      return 0

  activeOutputCount = property(fget=_getActiveOutputCount)

  # Support for using non-training data for (C, Gamma)
  # parameter optimization search.
  def _setAutoTuningData(self, value):
    self._autoTuningData = value
    if value and self._numSVDDims is not None and self._vt is None:
      # Run SVD now, so we can save space by projecting the autotuning samples
      self.computeSVD()
  def _getAutoTuningData(self):
    return self._autoTuningData
  autoTuningData = property(_getAutoTuningData, _setAutoTuningData)


  def __setstate__(self, state):
    """
    Set the state of ourself from a serialized state.
    """

    # Register a global variable for scanning or other tomfoolery
    PyNodeModule.nodes = getattr(PyNodeModule, 'nodes', []) + [self]

    self.__dict__.update(state)
    self._firstComputeCall = True

    # Backward compatibility to be able to load
    # saved networks in which these attributes were
    # not defined.
    missing = dict(_vt=None,
                   deterministic=False,
                   discardProblem=True,
                   cpp_svm_seed=-1,
                   keepSamples=False,
                   calculateDistances=False,
                   _partitionIds=[],
                   C=self.minC,
                   gamma=self.minGamma,
                   _autoTuningData=False,
                   _autoTuneSamples=None,
                   _autoTuneLabels=None,
                   _autoTunePartitionIds=None,
                   distances=None,
                   _upcomingPartitionIds=None,
                   _monitorMemory=False,
                   _distanceCount=0,
                   _adaptiveSVDDims=False,
                   _fractionOfMax=None,
                   _useAuxiliary=False,
                   _inputVector=None,
                   _auxInputLen=None,
                   _scanInfo=None,
                   _scanResults=None)

    d = self.__dict__
    for k in missing:
      d[k] = d.get(k, missing[k])

    self._initRandom()


  def __getstate__(self):
    """
    Return serializable state.  This function will return a version of the
    __dict__ with all "ephemeral" members stripped out.  "Ephemeral" members
    are defined as those that do not need to be (nor should be) stored
    in any kind of persistent file (e.g., NuPIC network XML file.)
    """
    state = self.__dict__.copy()
    for ephemeralMemberName in [x for x in self._getEphemeralMembers() if x in state]:
      del state[ephemeralMemberName]
    return state


  def _getEphemeralMembers(self):
    """
    Returns list of all ephemeral class members.
    """
    return [
        '_rng',
        '_autoTuneSamples',
        '_autoTuneLabels',
        '_autoTunePartitionIds',
        ]


  def _initDataStructures(self, inputWidth):
    """
    Initialize internal data structures.
    """
    self._inputWidth = inputWidth

    self._catIdMap = None

    self._initSvm()

  def _initSvm(self, n_dims=None):
    """Initialize SVM Engine: Use the SWIG bindings to initialize
    an instance of an SVM Classifier engine."""

    # Select kernel type. If we are in 'classification' mode,
    # then this choice is simply the user-specified parameter
    # 'kernelType'.  If we are in 'feedback' mode however, we
    # must use a 'linear' kernel.
    #   0 = linear
    #   1 = rbf
    if self._mode == 'feedback' or self._kernelType == 'linear':
      kernelType = 0
    elif self._kernelType == 'rbf':
      kernelType = 1

    if n_dims is None:
      n_dims = self._inputWidth

    if self.useSparseSvm:
      self._svm = svm_01(kernelType,
                         n_dims=n_dims,
                         threshold=self.inputThresh,
                         probability=self.useProbabilisticSvm,
                         seed=self.cpp_svm_seed)
    else:
      self._svm = svm_dense(kernelType,
                            n_dims=n_dims,
                            probability=self.useProbabilisticSvm,
                            seed=self.cpp_svm_seed)


  def _learn(self, inputVector, trueCatIndex, partitionId=None):
    """
    Store current input vector and associated category index.
    """
    assert self._svm is not None
    # If we are sphering, then we can't provide the data to the SVM
    # library until we have computed per-dimension normalization constants.
    # So instead, we'll just store each training sample.
    # Note: now we always do this, because the labels are used to build the
    # category mapping later
    self._storeSample(trueCatIndex, inputVector, partitionId)


  def _storeSample(self, trueCatIndex, inputVector, partitionId):
    """
    Store a training sample and associated category label
    """

    # If the incoming samples are not training data, but instead
    # are testing data to be used only for parameter optimization,
    # then store them separately.
    if self._autoTuningData:
      # If this is the first sample, then allocate a numpy array
      # of the appropriate size in which to store all samples.
      if self._autoTuneSamples is None:
        self._autoTuneSamples = numpy.zeros((0, inputVector.shape[0]),
                                            dtype=RealNumpyDType)
        assert self._autoTuneLabels is None
        self._autoTuneLabels = []
        assert self._autoTunePartitionIds is None
        self._autoTunePartitionIds = []

      # Add the sample vector and category lable
      self._autoTuneSamples = numpy.concatenate((self._autoTuneSamples,
                                                 numpy.atleast_2d(inputVector)), axis=0)
      self._autoTuneLabels += [trueCatIndex]
      if partitionId is not None:
        self._autoTunePartitionIds.append(partitionId)

    # Normal mode (incoming samples are training data)
    else:
      # If this is the first sample, then allocate a numpy array
      # of the appropriate size in which to store all samples.
      if self._samples is None:
        self._samples = numpy.zeros((0, self._inputWidth), dtype=RealNumpyDType)
        assert self._labels is None
        self._labels = []
        assert self._partitionIds is None
        self._partitionIds = []

      # Add the sample vector and category lable
      self._samples = numpy.concatenate((self._samples, numpy.atleast_2d(inputVector)), axis=0)
      self._labels += [trueCatIndex]
      if partitionId is not None:
        self._partitionIds.append(partitionId)


  def _infer(self, sample):
    """
    Consult SVM to classify input vector.
    """
    if self.calculateDistances:
      # Calculate distances in the original input space (pre-sphering, post-PCA)
      # if specified, effectively being a KNN
      self._calculateAndStoreDistance(sample)

    # If we are sphering, then apply normalization
    if self.doSphering:
      sample = (sample + self._normOffset) * self._normScale

    numCats = self._svm.get_model().n_class()

    if self.useProbabilisticSvm:
      belief = numpy.zeros(numCats, dtype=RealNumpyDType)
      prediction = int(self._svm.predict_probability(sample, belief))
    else:
      prediction = int(self._svm.predict(sample))
      belief = numpy.zeros(numCats, dtype=RealNumpyDType)
      belief[prediction] = 1.0
    return belief


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
    # Don't modify _samples in-place; it may be saved and used later
    samples = self._samples + self._normOffset
    # Now normalize the variances (to one).  However, we need to be
    # careful because the variance could conceivably be zero for one
    # or more dimensions.
    variance = samples.var(axis=0)
    variance[numpy.where(variance == 0.0)] = 1.0
    self._normScale  = 1.0 / numpy.sqrt(variance)
    samples *= self._normScale

    return samples


  def _finishLearning(self):
    """
    Use the C++ implementation to build an SVM Model.
    """
    self._beginMemoryMonitoring("_finishLearning")

    print 'Finish learning'

    # Set progress to 0
    PyNodeModule.finishLearningProgress = 0.0

    if self._upcomingPartitionIds:
      raise Exception("Switching to inference, but upcomingPartitionIds is "
                      "not empty: %s" % self._upcomingPartitionIds)

    # Compute the mapping of ImageSensor IDs to internal indices
    # Only insert ImageSensor IDs if they were seen during training
    # self._catIdMap = sorted(list(set(self._labels)))
    # the above causes bugs!!!
    self._catIdMap = []
    for label in self._labels:
      if label not in self._catIdMap and label != -1:
        self._catIdMap.append(label)
    if self._autoTuneLabels:
      # Use the autotune labels too; there could be categories never seen
      # during training that showed up during autotuning
      for label in self._autoTuneLabels:
        if label not in self._catIdMap and label != -1:
          self._catIdMap.append(label)

    # Do sphering if specified
    if self.doSphering:
      samples = self._finishSphering()

    # Run SVD if necessary
    if self._numSVDDims is not None and self._vt is None:
      self._beginMemoryMonitoring("computeSVD")
      self.computeSVD()
      self._endMemoryMonitoring("computeSVD")

    if not self.doSphering:
      samples = self._samples

    # Feed each sample into the SVM library
    for sampleIndex, label in enumerate(self._labels):
      # Ignore samples whose label is -1, which can occur if
      #  changeCategoriesOfPartitionIds was called
      # Use the catIdMap to give the SVM a continuous range of indices
      if label != -1:
        self._svm.add_sample(self._catIdMap.index(label), samples[sampleIndex])

    # Initialize the random number generator for LHS
    #self._initRandom()

    if self.numRecursions > 0 and (self.minC < self.maxC or self.minGamma < self.maxGamma):
      # Do recursive Latin Hypercube sampling to obtain best C, gamma
      paramRange = (self.minC, self.maxC, self.minGamma, self.maxGamma)
      self._beginMemoryMonitoring("_doRecursion")
      (svmParams, svmAccuracy, svmModel) = self._doRecursion(None, None, paramRange)
      self._endMemoryMonitoring("_doRecursion")
      if svmParams is None:
        # User canceled
        self._learningMode = False  # To avoid exception
        self._inferenceMode = True
        return
      print 'optimal params', svmParams
      # Set self.C and self.gamma to the optimal values
      self.C, self.gamma = svmParams
    else:
      # Use the specified values of C and gamma
      svmParams = (self.C, self.gamma)

    # Build final model
    self._beginMemoryMonitoring("_buildSVM")
    self._buildSVM(svmParams[0], svmParams[1])
    self._endMemoryMonitoring("_buildSVM")
    # Save parameters used to build the model
    self._svmParams = svmParams

    if self.discardProblem:
      # Discard the samples and labels
      self._svm.discard_problem()

    # Uncomment this to print out the chosen C and Gamma values
    #print "SVM node (C,Gamma) = ", self._svmParams

    # We can now throw away all our stored training samples; this way they
    # won't get pickled into the final 'inference stage' node.
    if not self.keepSamples:
      self._samples = None
      self._labels  = None

    # Set learning mode off and turn on inference mode
    self._learningMode = False
    self._inferenceMode = True

    # Clear data structures that should begin fresh for testing
    self.distances = None
    self._distanceCount = None

    # Update progress
    PyNodeModule.finishLearningProgress = 1.0

    self._endMemoryMonitoring("_finishLearning")


  def _doRecursion(self, samples, validationSets, paramRange, recursionIndex=0, bestResults=None):
    """
    Perform recursive Latin Hypercube sampling
    """
    # Construct set of sample points
    minC, maxC, minGamma, maxGamma = paramRange
    rangeC = maxC - minC
    rangeGamma = maxGamma - minGamma

    if self.numSamplesPerRecursion == 1:
      intervalC = 0.0
      intervalGamma = 0.0
    else:
      intervalC = rangeC / float(self.numSamplesPerRecursion - 1)
      intervalGamma = rangeGamma / float(self.numSamplesPerRecursion - 1)

    gammaIndices = range(self.numSamplesPerRecursion)
    self._rng.shuffle(gammaIndices)

    sampleIndices = [(float(x), float(gammaIndices[x])) for x in range(self.numSamplesPerRecursion)]

    samplePoints = [(minC + intervalC * x[0], minGamma + intervalGamma * x[1]) for x in sampleIndices]

    bestAccuracy = -1.0
    bestSamplePoint = None
    for i, samplePoint in enumerate(samplePoints):

      # For progress updates
      progressStart = PyNodeModule.finishLearningProgress
      progressEnd = progressStart \
                  + 1 / float(self.numSamplesPerRecursion * self.numRecursions)
      # Make sure progress does not reach 1.0 before the end of finishLearning
      progressEnd = min(0.99, progressEnd)

      logging.debug("SVM recursion %d, sample %d: C is %.2f, gamma is %.2f"
                    % (recursionIndex, i, samplePoint[0], samplePoint[1]))
      accuracy, svmModel = self._validateSvm(samplePoint[0], samplePoint[1],
                                             progressStart, progressEnd)
      if accuracy is None:
        # User canceled
        return (None, None, None)

      logging.debug("Accuracy: %.2f" % (accuracy * 100))
      if accuracy > bestAccuracy:
        bestAccuracy = accuracy
        bestSamplePoint = samplePoint
        bestModel = svmModel

    # Check if the previous recursion actually produced better results (by chance)
    if bestResults is not None and bestResults[1] > bestAccuracy:
      bestSamplePoint, bestAccuracy, bestModel = bestResults

    # Have we completed our LHS recursions?
    recursionIndex += 1
    if recursionIndex == self.numRecursions:
      return (bestSamplePoint, bestAccuracy, bestModel)

    # Perform another round of LHS
    else:
      # Contract down the sampling range
      halfRangeC = 0.5 * self.contractionFactor * rangeC
      halfRangeGamma = 0.5 * self.contractionFactor * rangeGamma

      newParamRange = (bestSamplePoint[0] - halfRangeC,
                       bestSamplePoint[0] + halfRangeC,
                       bestSamplePoint[1] - halfRangeGamma,
                       bestSamplePoint[1] + halfRangeGamma)

      return self._doRecursion(samples, validationSets, newParamRange, recursionIndex,
                              (bestSamplePoint, bestAccuracy, svmModel))


  def _autoTuneTest(self, svm):
    if self.useProbabilisticSvm:
      numCats = svm.get_model().n_class()
      belief = numpy.zeros(numCats, dtype=RealNumpyDType)
    numErrors = 0
    numTestingSamples = self._autoTuneSamples.shape[0]
    for k in xrange(numTestingSamples):
      sample = self._autoTuneSamples[k]
      # Note: we currently do not support sphering and PCA at
      # the same time.
      assert not self.doSphering or not self._vt
      # If we are sphering, then apply normalization
      if self.doSphering:
        sample = (sample + self._normOffset) * self._normScale
      # Vector is already projected onto PCA basis (if present)
      # Present the sample
      if self.useProbabilisticSvm:
        prediction = int(svm.predict_probability(sample, belief))
      else:
        prediction = int(svm.predict(sample))
      if prediction != self._catIdMap.index(self._autoTuneLabels[k]):
        numErrors += 1
    return float(numTestingSamples - numErrors) / float(numTestingSamples)


  def _validateSvm(self, C, gamma, progressStart, progressEnd):
    """
    Perform cross-validation to measure the recognition accuracy of an SVM.
    """
    # @todo Problem - the cross_validate() API doesn't accept C, gamma parameters!
    #accuracy = self._svm.cross_validate(C, gamma, nFold=self.numCrossValidations)
    #accuracy = self._svm.cross_validate(nFold=self.numCrossValidations)

    valueC = math.pow(10.0, C)
    valueGamma = math.pow(10.0, gamma)

    # Validate against test samples
    if self._autoTuneSamples is not None:
      assert self._autoTuneLabels is not None
      assert self._autoTunePartitionIds is not None

      if False:
          # Choose number of dimensions
          if self._numSVDDims:
            numDims = self._numSVDDims
          else:
            numDims = self._inputWidth
          # Choosing kernel type
          if self._mode == 'feedback' or self._kernelType == 'linear':
            kernelType = 0
          elif self._kernelType == 'rbf':
            kernelType = 1
          # Create a new svm
          if self.useSparseSvm:
            svm = svm_01(kernelType,
                            n_dims=numDims,
                            threshold=self.inputThresh,
                            probability=self.useProbabilisticSvm,
                            seed=self.cpp_svm_seed)
          else:
            svm = svm_dense(kernelType,
                            n_dims=numDims,
                            probability=self.useProbabilisticSvm,
                            seed=self.cpp_svm_seed)
          # Feed each sample into the SVM library
          for k, label in enumerate(self._labels):
            # Ignore samples whose label is -1, which can occur if
            #  changeCategoriesOfPartitionIds was called
            # Use the catIdMap to give the SVM a continuous range of indices
            sample = self._samples[k]
            if label != -1:
              svm.add_sample(self._catIdMap.index(label), sample)
      else:
        svm = self._svm

      # Train using all the training samples with this
      # (C, Gamma) sample point
      svm.trainReleaseGIL(gamma=valueGamma, C=valueC, eps=self.convEpsilon)

      # Check and update progress
      if PyNodeModule.finishLearningProgress == -1:
        return (None, None)
      PyNodeModule.finishLearningProgress += (progressStart - progressEnd)/2

      # Test against all testing samples
      accuracy = self._autoTuneTest(svm)

      # Check and update progress
      if PyNodeModule.finishLearningProgress == -1:
        return (None, None)
      PyNodeModule.finishLearningProgress = progressEnd

      #print "(%.3f, %.3f) ==> %.2f%%" % (C, gamma, 100.0 * accuracy)

    # Use cross-validation to validate against training samples
    else:
      accuracy = self._svm.cross_validate(n_fold=self.numCrossValidations,
                                                gamma=valueGamma,
                                                C=valueC,
                                                eps=self.convEpsilon)
    return (accuracy, None)


  def _buildSVM(self, C, gamma):
    """
    Train an SVM model.

    @param C -- the value of parameter C to use.
    @param gamma -- the value of parameter Gamma to use.
    @param trainLabels -- the category labels associated with the
            training data.
    @param trainSamples -- the input sample vectors associated with
            the training data.
    """
    valueC = math.pow(10.0, C)
    valueGamma = math.pow(10.0, gamma)
    self._svm.trainReleaseGIL(gamma=valueGamma, C=valueC, eps=self.convEpsilon)


  def computeSVD(self, numSVDSamples=None, finalize=True):
    print 'Computing SVD'

    # Samples are in self._samples, not in the SVM yet
    if numSVDSamples is None:
      numSVDSamples = self._samples.shape[0]

    if self._useAuxiliary and not self._justUseAuxiliary:
      self._mean = numpy.mean(self._samples[:,:self._samples.shape[1]-self._auxInputLen], axis=0)
      self._samples[:,:self._samples.shape[1]-self._auxInputLen] -= self._mean
      # Remove the auxiliary data prior to computing the SVD
      u, self._s, self._vt = numpy.linalg.svd(self._samples[:numSVDSamples,:self._samples.shape[1]-self._auxInputLen])
    else:
      self._mean = numpy.mean(self._samples, axis=0)
      self._samples -= self._mean
      u, self._s, self._vt = numpy.linalg.svd(self._samples[:numSVDSamples,:])


    if finalize:
      self.finalizeSVD()
    return self._s


  def getAdaptiveSVDDims(self, singularValues, fractionOfMax=0.001):
    v = singularValues/singularValues[0]
    idx = numpy.where(v<fractionOfMax)[0]
    if len(idx):
      print "Number of PCA dimensions chosen: ", idx[0], "out of ", len(v)
      return idx[0]
    else:
      print "Number of PCA dimensions chosen: ", len(v)-1, "out of ", len(v)
      return len(v)-1


  def finalizeSVD(self, numSVDDims=None):
    print 'Finalizing SVD'


    if numSVDDims is not None:
      self._numSVDDims = numSVDDims

    if self._numSVDDims=='adaptive':
      if self._fractionOfMax is not None:
        self._numSVDDims = self.getAdaptiveSVDDims(self._s, self._fractionOfMax)
      else:
        self._numSVDDims = self.getAdaptiveSVDDims(self._s)

    if self._vt.shape[0] < self._numSVDDims:
      print "******************************************************************************"
      print "Warning: The requested number of PCA dimensions is more than the number of pattern dimensions."
      print "Setting numSVDDims = ", self._vt.shape[0]
      print "******************************************************************************"
      self._numSVDDims = self._vt.shape[0]

    self._vt = self._vt[:self._numSVDDims]
    if self._useAuxiliary and not self._justUseAuxiliary:
      self._initSvm(n_dims=self._numSVDDims + self._auxInputLen)
      # Project all the vectors (mean has already been subtracted from each one)
      auxSamples = self._samples[:, self._samples.shape[1]+1:]
      self._samples = self._samples[:, :self._samples.shape[1]-self._auxInputLen]
      self._samples = numpy.dot(self._samples, self._vt.T)
      self._samples = numpy.concatenate([numpy.atleast_2d(self._samples), numpy.atleast_2d(auxSamples)], axis=1)
    else:
      self._initSvm(n_dims=self._numSVDDims)
      self._samples = numpy.dot(self._samples, self._vt.T)


  def getAllDistances(self):
    """Return all the prototype distances from all computes available."""

    if self.distances is None:
      return None
    return self.distances[:self._distanceCount, :]


  def getLatestDistances(self):
    """Get the distances to all training samples (pre-SVM, post-PCA)."""

    if self._inputVector is None:
      return
    if self._samples is None:
      raise Exception("No samples stored")

    return self._calculateDistances(self._inputVector)


  def getCategoryList(self):
    """
    Public API for returning the category list
    """

    return self._labels


  def _calculateDistances(self, inputVector):
    """Calculate distances in the original input space (pre-SVM, post-PCA)."""

    # Calculate the distances from this input to all prototypes
    # TODO do this after sphering instead?
    # TODO custom distance norm?
    dist = numpy.power(numpy.abs(self._samples - inputVector), 2)
    dist = dist.sum(1)
    dist = numpy.power(dist, 0.5)
    # Ignore samples with a category of -1
    dist[numpy.array(self._labels) == -1] = numpy.inf

    return dist


  def _calculateAndStoreDistances(self, inputVector):
    """Calculate distances in the original input space (pre-SVM, post-PCA)."""

    dist = self._calculateDistances(inputVector)

    # Keep all distances in an array
    if self.distances is None:
      self.distances = numpy.zeros((1, dist.shape[0]), dist.dtype)
      self.distances[0,:] = dist
      self._distanceCount = 1
    else:
      if self._distanceCount == self.distances.shape[0]:
        # Double the size of the array
        newDistances = numpy.zeros((self.distances.shape[0] * 2,
                                    self.distances.shape[1]),
                                   self.distances.dtype)
        newDistances[:self.distances.shape[0],:] = self.distances
        self.distances = newDistances
      # Store the new distances
      self.distances[self._distanceCount,:] = dist
      self._distanceCount += 1


  def setUpcomingPartitionIds(self, partitionIds):
    """
    Set the queue of upcoming partition ids. This can be used instead of the
    partitionId input. Checks that no partition ids currently exist (which
    could indicate a bug).
    """

    if self._upcomingPartitionIds:
      raise Exception("PartitionIds already exist: %s"
                      % str(self._upcomingPartitionIds))

    if not partitionIds:
      return

    if not hasattr(partitionIds, '__iter__'):
      partitionIds = [partitionIds]
    else:
      partitionIds = list(partitionIds)
    self._upcomingPartitionIds = partitionIds


  def remapCategories(self, mapping):
    """
    Change the existing category labels.

    mapping -- List of new category indices. For example, mapping=[2,0,1]
      would change all vectors of category 0 to be category 2, category 1 to 0,
      and category 2 to 1.
    """

    if not self._labels:
      return

    if not hasattr(mapping, '__len__'):
      mapping = [mapping]  # Cannot send singleton lists through session

    labels = numpy.array(self._labels, dtype=numpy.int)
    newLabels = numpy.zeros(labels.shape[0], dtype=numpy.int)
    newLabels.fill(-1)
    for i in xrange(len(mapping)):
      newLabels[labels==i] = mapping[i]
    self._labels = list(newLabels)


  def changePartitionId(self, oldPartitionId, newPartitionId):
    """
    Change all instances of oldPartitionId to newPartitionId.
    """

    if not self._partitionIds:
      # No learning has occurred yet
      return

    self._partitionIds = numpy.array(self._partitionIds)
    self._partitionIds[self._partitionIds == oldPartitionId] = newPartitionId
    self._partitionIds = list(self._partitionIds)


  def changeCategoriesOfPartitionIds(self, partitionIds, categoryIndices):
    """
    Change the category associated with all vectors with this partitionId(s).

    partitionIds -- Single id or list of ids.
    categoryIndices -- Single index or list of indices. Can also be a single
      index when partitionIds is a list, in which case the same category will
      be used for all vectors with the specified id.
    """

    if not hasattr(partitionIds, '__iter__'):
      partitionIds = [partitionIds]
      categoryIndices = [categoryIndices]
    elif not hasattr(categoryIndices, '__iter__'):
      categoryIndices = [categoryIndices] * len(partitionIds)

    if not self._partitionIds:
      # No learning has occurred yet
      return

    # Convert partitionIds and labels to arrays
    self._partitionIds = numpy.array(self._partitionIds)
    self._labels = numpy.array(self._labels)

    for i in xrange(len(partitionIds)):
      partitionId = partitionIds[i]
      categoryIndex = categoryIndices[i]
      self._labels[self._partitionIds == partitionId] = categoryIndex

    # Convert partitionIds and labels back to lists
    self._partitionIds = list(self._partitionIds)
    self._labels = list(self._labels)


  def switchToLearning(self):
    """Force a switch back to learning mode (not normally supported)."""

    self._learningMode = True
    self._inferenceMode = False

    # Clear data structures that were creating in finishLearning or first
    # used there
    self._catIdMap = None
    self._svm = None
    self._svmParams = None
    self._initSvm()
    self.distances = None
    self._distanceCount = None



if __name__=='__main__':
  import os
  from nupic.network import CreateNode

  name = os.path.splitext(os.path.basename(__file__))[0]
  n = CreateNode('nupic.pynodes.extra.%(m)s.%(m)s' % {'m':name})
  n.nodeHelp()
