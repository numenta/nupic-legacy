# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2016, Numenta, Inc.  Unless you have an agreement
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
This file implements the SDR Classifier region. See the comments in the class
definition of SDRClassifierRegion for a description.
"""

import warnings

from nupic.bindings.regions.PyRegion import PyRegion
from nupic.algorithms.sdr_classifier_factory import SDRClassifierFactory
from nupic.support.configuration import Configuration

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.regions.SDRClassifierRegion_capnp import SDRClassifierRegionProto



class SDRClassifierRegion(PyRegion):
  """
  SDRClassifierRegion implements a SDR classifier that accepts a binary
  input from the level below (the "activationPattern") and information from the
  sensor and encoders (the "classification") describing the input to the system
  at that time step.

  The SDR classifier maps input patterns to class labels. There are as many
  output units as the number of class labels or buckets (in the case of scalar
  encoders). The output is a probabilistic distribution over all class labels.

  During inference, the output is calculated by first doing a weighted summation
  of all the inputs, and then perform a softmax nonlinear function to get
  the predicted distribution of class labels

  During learning, the connection weights between input units and output units
  are adjusted to maximize the likelihood of the model

  The caller can choose to tell the region that the classifications for
  iteration N+K should be aligned with the activationPattern for iteration N.
  This results in the classifier producing predictions for K steps in advance.
  Any number of different K's can be specified, allowing the classifier to learn
  and infer multi-step predictions for a number of steps in advance.
  
  :param steps: (int) default=1
  :param alpha: (float) default=0.001
  :param verbosity: (int) How verbose to log, default=0
  :param implementation: (string) default=None
  :param maxCategoryCount: (int) default=None

  """


  @classmethod
  def getSpec(cls):
    """
    Overrides :meth:`nupic.bindings.regions.PyRegion.PyRegion.getSpec`.
    """
    ns = dict(
      description=SDRClassifierRegion.__doc__,
      singleNodeOnly=True,

      inputs=dict(
        actValueIn=dict(
          description="Actual value of the field to predict. Only taken "
                      "into account if the input has no category field.",
          dataType="Real32",
          count=0,
          required=False,
          regionLevel=False,
          isDefaultInput=False,
          requireSplitterMap=False),

        bucketIdxIn=dict(
          description="Active index of the encoder bucket for the "
                      "actual value of the field to predict. Only taken "
                      "into account if the input has no category field.",
          dataType="UInt64",
          count=0,
          required=False,
          regionLevel=False,
          isDefaultInput=False,
          requireSplitterMap=False),

        categoryIn=dict(
          description='Vector of categories of the input sample',
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

        predictedActiveCells=dict(
          description="The cells that are active and predicted",
          dataType='Real32',
          count=0,
          required=True,
          regionLevel=True,
          isDefaultInput=False,
          requireSplitterMap=False),

        sequenceIdIn=dict(
          description="Sequence ID",
          dataType='UInt64',
          count=1,
          required=False,
          regionLevel=True,
          isDefaultInput=False,
          requireSplitterMap=False),
      ),

      outputs=dict(
        categoriesOut=dict(
          description='Classification results',
          dataType='Real32',
          count=0,
          regionLevel=True,
          isDefaultOutput=False,
          requireSplitterMap=False),

        actualValues=dict(
          description='Classification results',
          dataType='Real32',
          count=0,
          regionLevel=True,
          isDefaultOutput=False,
          requireSplitterMap=False),

        probabilities=dict(
          description='Classification results',
          dataType='Real32',
          count=0,
          regionLevel=True,
          isDefaultOutput=False,
          requireSplitterMap=False),
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

        maxCategoryCount=dict(
          description='The maximal number of categories the '
                      'classifier will distinguish between.',
          dataType='UInt32',
          required=True,
          count=1,
          constraints='',
          # arbitrarily large value
          defaultValue=2000,
          accessMode='Create'),

        steps=dict(
          description='Comma separated list of the desired steps of '
                      'prediction that the classifier should learn',
          dataType="Byte",
          count=0,
          constraints='',
          defaultValue='0',
          accessMode='Create'),

        alpha=dict(
          description='The alpha is the learning rate of the classifier.'
                      'lower alpha results in longer term memory and slower '
                      'learning',
          dataType="Real32",
          count=1,
          constraints='',
          defaultValue=0.001,
          accessMode='Create'),

        implementation=dict(
          description='The classifier implementation to use.',
          accessMode='ReadWrite',
          dataType='Byte',
          count=0,
          constraints='enum: py, cpp'),

        verbosity=dict(
          description='An integer that controls the verbosity level, '
                      '0 means no verbose output, increasing integers '
                      'provide more verbosity.',
          dataType='UInt32',
          count=1,
          constraints='',
          defaultValue=0,
          accessMode='ReadWrite'),
      ),
      commands=dict()
    )

    return ns


  def __init__(self,
               steps='1',
               alpha=0.001,
               verbosity=0,
               implementation=None,
               maxCategoryCount=None
               ):

    # Set default implementation
    if implementation is None:
      implementation = Configuration.get(
        'nupic.opf.sdrClassifier.implementation')

    self.implementation = implementation
    # Convert the steps designation to a list
    self.steps = steps
    self.stepsList = [int(i) for i in steps.split(",")]
    self.alpha = alpha
    self.verbosity = verbosity

    # Initialize internal structures
    self._sdrClassifier = None
    self.learningMode = True
    self.inferenceMode = False
    self.maxCategoryCount = maxCategoryCount
    self.recordNum = 0

    # Flag to know if the compute() function is ever called. This is to
    # prevent backward compatibilities issues with the customCompute() method
    # being called at the same time as the compute() method. Only compute()
    # should be called via network.run(). This flag will be removed once we
    # get to cleaning up the htm_prediction_model.py file.
    self._computeFlag = False


  def initialize(self):
    """
    Overrides :meth:`nupic.bindings.regions.PyRegion.PyRegion.initialize`.

    Is called once by NuPIC before the first call to compute().
    Initializes self._sdrClassifier if it is not already initialized.
    """
    if self._sdrClassifier is None:
      self._sdrClassifier = SDRClassifierFactory.create(
        steps=self.stepsList,
        alpha=self.alpha,
        verbosity=self.verbosity,
        implementation=self.implementation,
      )


  def getAlgorithmInstance(self):
    """
    :returns: (:class:`nupic.regions.sdr_classifier_region.SDRClassifierRegion`)
    """
    return self._sdrClassifier


  def getParameter(self, name, index=-1):
    """
    Overrides :meth:`nupic.bindings.regions.PyRegion.PyRegion.getParameter`.
    """
    # If any spec parameter name is the same as an attribute, this call
    # will get it automatically, e.g. self.learningMode
    return PyRegion.getParameter(self, name, index)


  def setParameter(self, name, index, value):
    """
    Overrides :meth:`nupic.bindings.regions.PyRegion.PyRegion.setParameter`.
    """
    if name == "learningMode":
      self.learningMode = bool(int(value))
    elif name == "inferenceMode":
      self.inferenceMode = bool(int(value))
    else:
      return PyRegion.setParameter(self, name, index, value)


  @staticmethod
  def getSchema():
    """
    :returns: the pycapnp proto type that the class uses for serialization.
    """
    return SDRClassifierRegionProto


  def writeToProto(self, proto):
    """
    Write state to proto object.

    :param proto: SDRClassifierRegionProto capnproto object
    """
    proto.implementation = self.implementation
    proto.steps = self.steps
    proto.alpha = self.alpha
    proto.verbosity = self.verbosity
    proto.maxCategoryCount = self.maxCategoryCount
    proto.learningMode = self.learningMode
    proto.inferenceMode = self.inferenceMode
    proto.recordNum = self.recordNum

    self._sdrClassifier.write(proto.sdrClassifier)


  @classmethod
  def readFromProto(cls, proto):
    """
    Read state from proto object.

    :param proto: SDRClassifierRegionProto capnproto object
    """
    instance = cls()

    instance.implementation = proto.implementation
    instance.steps = proto.steps
    instance.stepsList = [int(i) for i in proto.steps.split(",")]
    instance.alpha = proto.alpha
    instance.verbosity = proto.verbosity
    instance.maxCategoryCount = proto.maxCategoryCount

    instance._sdrClassifier = SDRClassifierFactory.read(proto)

    instance.learningMode = proto.learningMode
    instance.inferenceMode = proto.inferenceMode
    instance.recordNum = proto.recordNum

    return instance



  def compute(self, inputs, outputs):
    """
    Process one input sample.
    This method is called by the runtime engine.

    :param inputs: (dict) mapping region input names to numpy.array values
    :param outputs: (dict) mapping region output names to numpy.arrays that 
           should be populated with output values by this method
    """

    # This flag helps to prevent double-computation, in case the deprecated
    # customCompute() method is being called in addition to compute() called
    # when network.run() is called
    self._computeFlag = True

    patternNZ = inputs["bottomUpIn"].nonzero()[0]

    if self.learningMode:
      # An input can potentially belong to multiple categories.
      # If a category value is < 0, it means that the input does not belong to
      # that category.
      categories = [category for category in inputs["categoryIn"]
                    if category >= 0]

      if len(categories) > 0:
        # Allow to train on multiple input categories.
        bucketIdxList = []
        actValueList = []
        for category in categories:
          bucketIdxList.append(int(category))
          if "actValueIn" not in inputs:
            actValueList.append(int(category))
          else:
            actValueList.append(float(inputs["actValueIn"]))

        classificationIn = {"bucketIdx": bucketIdxList,
                            "actValue": actValueList}
      else:
        # If the input does not belong to a category, i.e. len(categories) == 0,
        # then look for bucketIdx and actValueIn.
        if "bucketIdxIn" not in inputs:
          raise KeyError("Network link missing: bucketIdxOut -> bucketIdxIn")
        if "actValueIn" not in inputs:
          raise KeyError("Network link missing: actValueOut -> actValueIn")

        classificationIn = {"bucketIdx": int(inputs["bucketIdxIn"]),
                            "actValue": float(inputs["actValueIn"])}
    else:
      # Use Dummy classification input, because this param is required even for
      # inference mode. Because learning is off, the classifier is not learning
      # this dummy input. Inference only here.
      classificationIn = {"actValue": 0, "bucketIdx": 0}

    # Perform inference if self.inferenceMode is True
    # Train classifier if self.learningMode is True
    clResults = self._sdrClassifier.compute(recordNum=self.recordNum,
                                            patternNZ=patternNZ,
                                            classification=classificationIn,
                                            learn=self.learningMode,
                                            infer=self.inferenceMode)

    # fill outputs with clResults
    if clResults is not None and len(clResults) > 0:
      outputs['actualValues'][:len(clResults["actualValues"])] = \
        clResults["actualValues"]

      for step in self.stepsList:
        stepIndex = self.stepsList.index(step)
        categoryOut = clResults["actualValues"][clResults[step].argmax()]
        outputs['categoriesOut'][stepIndex] = categoryOut

        # Flatten the rest of the output. For example:
        #   Original dict  {1 : [0.1, 0.3, 0.2, 0.7]
        #                   4 : [0.2, 0.4, 0.3, 0.5]}
        #   becomes: [0.1, 0.3, 0.2, 0.7, 0.2, 0.4, 0.3, 0.5]
        stepProbabilities = clResults[step]
        for categoryIndex in xrange(self.maxCategoryCount):
          flatIndex = categoryIndex + stepIndex * self.maxCategoryCount
          if categoryIndex < len(stepProbabilities):
            outputs['probabilities'][flatIndex] = \
              stepProbabilities[categoryIndex]
          else:
            outputs['probabilities'][flatIndex] = 0.0

    self.recordNum += 1


  def customCompute(self, recordNum, patternNZ, classification):
    """
    Just return the inference value from one input sample. The actual
    learning happens in compute() -- if, and only if learning is enabled --
    which is called when you run the network.

    .. warning:: This method is deprecated and exists only to maintain backward 
       compatibility. This method is deprecated, and will be removed. Use 
       :meth:`nupic.engine.Network.run` instead, which will call 
       :meth:`~nupic.regions.sdr_classifier_region.compute`.

    :param recordNum: (int) Record number of the input sample.
    :param patternNZ: (list) of the active indices from the output below
    :param classification: (dict) of the classification information:
    
           * ``bucketIdx``: index of the encoder bucket
           * ``actValue``:  actual value going into the encoder

    :returns: (dict) containing inference results, one entry for each step in
              ``self.steps``. The key is the number of steps, the value is an
              array containing the relative likelihood for each ``bucketIdx``
              starting from 0.

              For example:
              
              :: 
              
                {'actualValues': [0.0, 1.0, 2.0, 3.0]
                  1 : [0.1, 0.3, 0.2, 0.7]
                  4 : [0.2, 0.4, 0.3, 0.5]}
    """

    # If the compute flag has not been initialized (for example if we
    # restored a model from an old checkpoint) initialize it to False.
    if not hasattr(self, "_computeFlag"):
      self._computeFlag = False

    if self._computeFlag:
      # Will raise an exception if the deprecated method customCompute() is
      # being used at the same time as the compute function.
      warnings.simplefilter('error', DeprecationWarning)
      warnings.warn("The customCompute() method should not be "
                    "called at the same time as the compute() "
                    "method. The compute() method is called "
                    "whenever network.run() is called.",
                    DeprecationWarning)

    return self._sdrClassifier.compute(recordNum,
                                       patternNZ,
                                       classification,
                                       self.learningMode,
                                       self.inferenceMode)



  def getOutputElementCount(self, outputName):
    """
    Overrides :meth:`nupic.bindings.regions.PyRegion.PyRegion.getOutputElementCount`.
    """
    if outputName == "categoriesOut":
      return len(self.stepsList)
    elif outputName == "probabilities":
      return len(self.stepsList) * self.maxCategoryCount
    elif outputName == "actualValues":
      return self.maxCategoryCount
    else:
      raise ValueError("Unknown output {}.".format(outputName))
