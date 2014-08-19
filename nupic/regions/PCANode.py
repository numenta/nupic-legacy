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
PCANode implements PCA
"""

import numpy

from PyRegion import PyRegion

############################################################################

class PCANode(PyRegion):
  """
  PCANode implements PCA.
  """

  def __init__(self,
               SVDSampleCount=-1,
               SVDDimCount=-1,
               fractionOfMax=0.0,
               keepSamples=False,  # Keep the original inputs around
               logPath='',
               bottomUpCount=None):

    self._testInputs = None

    if bottomUpCount:
      bottomUpOut=bottomUpCount

    self._SVDSampleCount = SVDSampleCount
    self._SVDDimCount = SVDDimCount
    self._adaptiveSVDDims = SVDDimCount == -1
    self._fractionOfMax = fractionOfMax
    self._logPath = logPath

    self.keepSamples = 1 if keepSamples else 0

    self.clear()

  def clear(self):
    """Clear all persistent internal state."""

    self._learningMode = True
    self._inferenceMode = False
    self._inputWidth = None
    self._samples = None
    self._labels  = None
    self._partitionIds = None
    self._upcomingPartitionIds = None

    # Logging
    self._logFileCreated = False

    # PCA
    self._numPatterns = 0
    self._s = None
    self._vt = None
    self._mean = None

  def _setInferenceMode(self, value):
    value = bool(int(value))
    self._inferenceMode == value
    if value and self._vt is None:
      self.computeSVD()

  inferenceMode = property(
      fget=lambda self: self._inferenceMode,
      fset=_setInferenceMode,
      doc="""Boolean indicating whether or not a node
          is in inference mode"""
    )

  def _setLearningMode(self, value):
    value = bool(int(value))
    self._learningMode = value

  learningMode = property(
      fget=lambda self: self._learningMode,
      fset=_setLearningMode,
      doc="""Boolean indicating whether or not a node
          is in learning mode"""
    )

  def _setMode(self, value):
    self._mode = value

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

  #+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+
  # Region API methods
  #+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+

  #---------------------------------------------------------------------------------
  def initialize(self, dims, splitterMaps):
    pass

  #---------------------------------------------------------------------------------
  def compute(self, inputs, outputs):
    """
    Process one input sample.
    This method is called by the runtime engine.
    """

    # Assemble inputs
    if self._testInputs:
      inputVector = self._testInputs
    else:
      inputVector = inputs

    # Initialize data structures the first time
    if self._inputWidth is None:
      self._initDataStructures(len(inputVector))

    # Perform PCA if it is time to do so
    if self._vt is None and self._SVDDimCount != -1 \
        and self._SVDSampleCount != -1 \
        and self._samples.shape[0] == self._SVDSampleCount:
      self.computeSVD()

    # Project the vector onto the PCA basis if present
    if self._vt is not None:
      inputVector = numpy.dot(self._vt, inputVector - self._mean)

    self._samples = numpy.concatenate((self._samples, numpy.atleast_2d(inputVector)),axis=0)

    if self._vt is not None:
      allOutputs = outputs
      allOutputs.fill(0)
      allOutputs[:len(inputVector)] = inputVector

      # Do logging
      self._doLogging(inputVector)

    self._testInputs = None

  #---------------------------------------------------------------------------------
  def _doLogging(self, pcaCoeffs):
    """
    Log output coefficients to a .CSV file
    """
    if self._logPath:
      if not hasattr(self, '_logFileCreated') or not self._logFileCreated:
        logDir = os.path.split(self._logPath)[0]
        if not os.path.exists(logDir):
          print "Creating logging directory: %s" % logDir
          os.makedirs(logDir)
        fpOut = open(self._logPath, 'w')
        # Write initial line containing correct length
        # of coefficient vector
        print >>fpOut, '%d' % len(pcaCoeffs)
        fpOut.close()
        self._logFileCreated = True
      output = ",".join([str(x) for x in pcaCoeffs.tolist()])
      fpOut = open(self._logPath, 'a')
      print >>fpOut, output
      fpOut.close()

  #---------------------------------------------------------------------------------

  @classmethod
  def getSpec(cls):
    ns = dict(
      description=PCANode.__doc__,
      singleNodeOnly=True,
      inputs=dict(
        bottomUpIn=dict(
          description="Belief values over children's groups",
          dataType='Real32',
          count=0,
          required=True,
          regionLevel=True,
          isDefaultInput=False,
          requireSplitterMap=False)),

      outputs=dict(
        bottomUpOut=dict(
        description='PCA of input vector',
        dataType='Real32',
        count=0,
        regionLevel=True,
        isDefaultOutput=True)),

      parameters=dict(
        bottomUpCount=dict(
          description='The number of elements of the bottom up output',
          dataType='UInt32',
          count=1,
          constraints='',
          accessMode='Read'),

        learningMode=dict(
          description='Boolean (0/1) indicating whether or not a node '
                      'is in learning mode.',
          dataType='UInt32',
          count=1,
          constraints='bool',
          defaultValue=1,
          accessMode='ReadWrite'),

        inferenceMode=dict(
          description='Boolean (0/1) indicating whether or not a node '
                      'is in inference mode.',
          dataType='UInt32',
          count=1,
          constraints='bool',
          defaultValue=0,
          accessMode='ReadWrite'),

        SVDSampleCount=dict(
          description="""If not -1, carries out SVD transformation after
                        that many samples have been seen. Otherwise, performs
                        SVD when switching to inference.""",
          dataType='Int32',
          count=1,
          constraints='',
          defaultValue=-1,
          accessMode='ReadWrite'),

        SVDDimCount=dict(
          description="""Number of dimensions to keep after SVD.
                        If set to -1 (adaptive) the number is chosen automatically.""",
          dataType='Int32',
          count=1,
          constraints='',
          defaultValue=-1,
          accessMode='ReadWrite'),

        fractionOfMax=dict(
          description="""The smallest singular value which is retained
                        as a fraction of the largest singular value. This is used
                        only if SVDDimCount==-1 (adaptive DIMS)'.""",
          dataType='Real32',
          count=1,
          constraints='',
          defaultValue=0.0,
          accessMode='Read'),

        keepSamples=dict(
          description="""Keep the SVD samples around.""",
          dataType='UInt32',
          count=1,
          constraints='bool',
          defaultValue=0,
          accessMode='ReadWrite'),

        trainingSampleCount=dict(
          description="""the current number of training samples.""",
          dataType='UInt32',
          count=1,
          constraints='',
          accessMode='Read'),

        logPath=dict(
          description="""If not empty, causes the PCA outputs to be logged to a CSV
                      file as specified by the parameter value.""",
          dataType='Byte',
          count=0,
          constraints='string',
          accessMode='ReadWrite'),
      )
    )
    return ns

  #---------------------------------------------------------------------------------
  def getParameter(self, name, index=-1):
    """
    Get the value of a parameter.

    Note: this method may be overridden by derived classes, but if so, then
    the derived class should invoke this base method if 'name'
    is unknown to the derived class.

    @param name -- the name of the parameter to retrieve, as defined
            by the Node Spec.
    """
    if name == "SVDSampleCount":
      return self._SVDSampleCount
    elif name == "SVDDimCount":
      return self._SVDDimCount
    elif name == "fractionOfMax":
      return self._fractionOfMax
    elif name == "trainingSampleCount":
      return self.gettrainingSampleCount()
    else:
      # If any spec parameter name is the same as an attribute, this call
      # will get it automatically, e.g. self.learningMode
      return PyRegion.getParameter(self, name, index)

  #---------------------------------------------------------------------------------
  def setParameter(self, name, index, value):
    """Set the value of a parameter."""

    if name == "SVDSampleCount":
      self._SVDSampleCount = value
    elif name == "logPath":
      self._logPath = value
    else:
      PyRegion.setParameter(self, name, index, value)

  #---------------------------------------------------------------------------------
  def gettrainingSampleCount(self):
    if self._samples is None:
      numSamples = 0
    else:
      numSamples = self._samples.shape[0]
    return numSamples

  #+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+
  # Internal methods
  #+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+

  def __setstate__(self, state):
    """
    Set the state of ourself from a serialized state.
    """
    self.__dict__.update(state)
    # Backward compatibility to be able to load
    # saved networks in which these attributes were
    # not defined.
    self._testInputs = None
    if not hasattr(self, "_vt"):
      self._vt = None
    if not hasattr(self, 'keepSamples'):
      self.keepSamples = False
    if not hasattr(self, "_monitorMemory"):
      self._monitorMemory = False
    if not hasattr(self, "_adaptiveSVDDims"):
      self._adaptiveSVDDims = False
    if not hasattr(self, "_fractionOfMax"):
      self._fractionOfMax = 0.0

  #---------------------------------------------------------------------------------
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

  #---------------------------------------------------------------------------------
  def _getEphemeralMembers(self):
    """
    Returns list of all ephemeral class members.
    """
    return []

  #---------------------------------------------------------------------------------
  def _initDataStructures(self, inputWidth):
    """
    Initialize internal data structures.
    """
    self._inputWidth = inputWidth
    self._samples = numpy.zeros((0, self._inputWidth), dtype=RealNumpyDType)

  #---------------------------------------------------------------------------------
  def computeSVD(self, SVDSampleCount=None, finalize=True):

    # Samples are in self._samples, not in the SVM yet
    if SVDSampleCount is None:
      SVDSampleCount = self._samples.shape[0]

    self._mean = numpy.mean(self._samples, axis=0)
    self._samples -= self._mean
    u, self._s, self._vt = numpy.linalg.svd(self._samples[:SVDSampleCount,:])
    if finalize:
      self.finalizeSVD()
    return self._s

  #---------------------------------------------------------------------------------
  def getAdaptiveSVDDims(self, singularValues, fractionOfMax=0.001):

    v = singularValues/singularValues[0]
    idx = numpy.where(v<fractionOfMax)[0]

    if len(idx):
      print "Number of PCA dimensions chosen: ", idx[0], "out of ", len(v)
      return idx[0]
    else:
      print "Number of PCA dimensions chosen: ", len(v)-1, "out of ", len(v)
      return len(v)-1

  #---------------------------------------------------------------------------------
  def finalizeSVD(self, SVDDimCount=None):

    if SVDDimCount is not None:
      self._SVDDimCount = SVDDimCount

    if self._adaptiveSVDDims:
      if self._fractionOfMax != 0.0:
        self._SVDDimCount = self.getAdaptiveSVDDims(self._s, self._fractionOfMax)
      else:
        self._SVDDimCount = self.getAdaptiveSVDDims(self._s)
    self._vt = self._vt[:self._SVDDimCount]

    # Project all the vectors (mean has already been subtracted from each one)
    self._samples = numpy.dot(self._samples, self._vt.T)

  #---------------------------------------------------------------------------------
  def getOutputElementCount(self, name):
    """This method will be called only when the node is used in nuPIC 2"""
    if name == 'bottomUpOut':
      return self._bottomUpCount
    else:
      raise Exception('Unknown output: ' + name)



#+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+
# Command line unit testing
#+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+
if __name__=='__main__':

  from nupic.engine import *

  rgen = numpy.random.RandomState(37)

  inputSize = 8

  net = Network()
  sensor = net.addRegion('sensor', 'py.ImageSensor' ,
          '{ width: %d, height: %d }' % (inputSize, inputSize))

  params = """{bottomUpCount: %d,
              SVDSampleCount: 5,
              SVDDimCount: 2}""" % inputSize

  pca = net.addRegion('pca', 'py.PCANode', params)

  #nodeAbove = CreateNode("py.ImageSensor", phase=0, categoryOut=1, dataOut=3,
  #                       width=3, height=1)
  #net.addElement('nodeAbove', nodeAbove)

  linkParams = '{ mapping: in, rfSize: [%d, %d] }' % (inputSize, inputSize)
  net.link('sensor', 'pca', 'UniformLink', linkParams, 'dataOut', 'bottomUpIn')

  net.initialize()

  for i in range(10):
    pca.getSelf()._testInputs = numpy.random.random([inputSize])
    net.run(1)
    #print s.sendRequest('nodeOPrint pca_node')
