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
This file implements the CLA Classifier region. See the comments in the class
definition of CLAClassifierRegion for a description.
"""

import warnings

from nupic.bindings.regions.PyRegion import PyRegion
from nupic.bindings.algorithms import FastCLAClassifier
from nupic.algorithms.cla_classifier_factory import CLAClassifierFactory
from nupic.support.configuration import Configuration

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.regions.CLAClassifierRegion_capnp import CLAClassifierRegionProto



class CLAClassifierRegion(PyRegion):
  """
  CLAClassifierRegion implements a CLA specific classifier that accepts a binary
  input from the level below (the "activationPattern") and information from the
  sensor and encoders (the "classification") describing the input to the system
  at that time step.

  When learning, for every bit in activation pattern, it records a history of 
  the classification each time that bit was active. The history is bounded by a
  maximum allowed age so that old entries are thrown away.

  For inference, it takes an ensemble approach. For every active bit in the
  activationPattern, it looks up the most likely classification(s) from the
  history stored for that bit and then votes across these to get the resulting
  classification(s).

  The caller can choose to tell the region that the classifications for
  iteration N+K should be aligned with the activationPattern for iteration N.
  This results in the classifier producing predictions for K steps in advance.
  Any number of different K's can be specified, allowing the classifier to learn
  and infer multi-step predictions for a number of steps in advance.
  """


  @classmethod
  def getSpec(cls):
    ns = dict(
      description=CLAClassifierRegion.__doc__,
      singleNodeOnly=True,

      inputs=dict(
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
          # arbitrarily large value for backward compatibility 
          defaultValue=1000,
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
          description='The alpha used to compute running averages of the '
                      'bucket duty cycles for each activation pattern bit. A '
                      'lower alpha results in longer term memory',
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
      implementation = Configuration.get('nupic.opf.claClassifier.implementation')

    # Convert the steps designation to a list
    self.classifierImp = implementation
    self.steps = steps
    self.stepsList = eval("[%s]" % (steps))
    self.alpha = alpha
    self.verbosity = verbosity

    # Initialize internal structures
    self._claClassifier = CLAClassifierFactory.create(
      steps=self.stepsList,
      alpha=self.alpha,
      verbosity=self.verbosity,
      implementation=implementation,
    )
    self.learningMode = True
    self.inferenceMode = False
    self.maxCategoryCount = maxCategoryCount
    self.recordNum = 0
    self._initEphemerals()

    # Flag to know if the compute() function is ever called. This is to 
    # prevent backward compatibilities issues with the customCompute() method
    # being called at the same time as the compute() method. Only compute() 
    # should be called via network.run(). This flag will be removed once we 
    # get to cleaning up the clamodel.py file.
    self._computeFlag = False


  def _initEphemerals(self):
    pass


  def initialize(self, dims, splitterMaps):
    pass


  def clear(self):
    self._claClassifier.clear()


  def getAlgorithmInstance(self):
    """Returns instance of the underlying CLAClassifier algorithm object."""
    return self._claClassifier


  def getParameter(self, name, index=-1):
    """
    Get the value of the parameter.

    @param name -- the name of the parameter to retrieve, as defined
            by the Node Spec.
    """
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
    elif name == "inferenceMode":
      self.inferenceMode = bool(int(value))
    else:
      return PyRegion.setParameter(self, name, index, value)


  @staticmethod
  def getProtoType():
    """Return the pycapnp proto type that the class uses for serialization."""
    return CLAClassifierRegionProto


  def writeToProto(self, proto):
    """Write state to proto object.

    proto: CLAClassifierRegionProto capnproto object
    """
    proto.classifierImp = self.classifierImp
    proto.steps = self.steps
    proto.alpha = self.alpha
    proto.verbosity = self.verbosity
    proto.maxCategoryCount = self.maxCategoryCount

    self._claClassifier.write(proto.claClassifier)


  @classmethod
  def readFromProto(cls, proto):
    """Read state from proto object.

    proto: CLAClassifierRegionProto capnproto object
    """
    instance = cls()

    instance.classifierImp = proto.classifierImp
    instance.steps = proto.steps
    instance.alpha = proto.alpha
    instance.verbosity = proto.verbosity
    instance.maxCategoryCount = proto.maxCategoryCount

    instance._claClassifier = CLAClassifierFactory.read(proto)

    return instance


  def reset(self):
    pass


  def compute(self, inputs, outputs):
    """
    Process one input sample.
    This method is called by the runtime engine.
    @param inputs -- inputs of the classifier region
    @param outputs -- outputs of the classifier region

    """

    # This flag helps to prevent double-computation, in case the deprecated 
    # customCompute() method is being called in addition to compute() called 
    # when network.run() is called
    self._computeFlag = True

    # An input can potentially belong to multiple categories. 
    # If a category value is < 0, it means that the input does not belong to 
    # that category.
    categories = [category for category in inputs["categoryIn"]
                  if category >= 0]

    activeCells = inputs["bottomUpIn"]
    patternNZ = activeCells.nonzero()[0]

    # ==========================================================================
    # Allow to train on multiple input categories. 
    # Do inference first, and then train on all input categories.

    # --------------------------------------------------------------------------
    #   1. Call classifier. Don't train. Just inference. Train after.

    # Dummy classification input, because this param is required. Learning is 
    # off, so the classifier is not learning this input. Inference only here.
    classificationIn = {"actValue": 0, "bucketIdx": 0}
    clResults = self._claClassifier.compute(recordNum=self.recordNum,
                                            patternNZ=patternNZ,
                                            classification=classificationIn,
                                            learn=False,
                                            infer=self.inferenceMode)

    for category in categories:
      classificationIn = {"bucketIdx": int(category), "actValue": int(category)}

      # ------------------------------------------------------------------------
      #   2. Train classifier, no inference
      self._claClassifier.compute(recordNum=self.recordNum,
                                  patternNZ=patternNZ,
                                  classification=classificationIn,
                                  learn=self.learningMode,
                                  infer=False)

    actualValues = clResults["actualValues"]
    outputs['actualValues'][:len(actualValues)] = actualValues
    for step in self.stepsList:
      stepIndex = self.stepsList.index(step)
      categoryOut = actualValues[clResults[step].argmax()]
      outputs['categoriesOut'][stepIndex] = categoryOut

      # Flatten the rest of the output. For example:
      #   Original dict  {1 : [0.1, 0.3, 0.2, 0.7]
      #                   4 : [0.2, 0.4, 0.3, 0.5]}
      #   becomes: [0.1, 0.3, 0.2, 0.7, 0.2, 0.4, 0.3, 0.5] 
      stepProbabilities = clResults[step]
      for categoryIndex in xrange(self.maxCategoryCount):
        flatIndex = categoryIndex + stepIndex * self.maxCategoryCount
        if categoryIndex < len(stepProbabilities):
          outputs['probabilities'][flatIndex] = stepProbabilities[categoryIndex]
        else:
          outputs['probabilities'][flatIndex] = 0.0

    self.recordNum += 1


  def customCompute(self, recordNum, patternNZ, classification):
    """
    Just return the inference value from one input sample. The actual 
    learning happens in compute() -- if, and only if learning is enabled -- 
    which is called when you run the network.
    
    WARNING: The method customCompute() is here to maintain backward 
    compatibility. This method is deprecated, and will be removed.
    Use network.run() instead, which will call the compute() method.

    Parameters:
    --------------------------------------------------------------------
    recordNum:      Record number of the input sample.
    patternNZ:      List of the active indices from the output below
    classification: Dict of the classification information:
                      bucketIdx: index of the encoder bucket
                      actValue:  actual value going into the encoder

    retval:     dict containing inference results, one entry for each step in
                self.steps. The key is the number of steps, the value is an
                array containing the relative likelihood for each bucketIdx
                starting from bucketIdx 0.

                for example:
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

    return self._claClassifier.compute(recordNum,
                                       patternNZ,
                                       classification,
                                       self.learningMode,
                                       self.inferenceMode)


  def getOutputValues(self, outputName):
    """
    Return the dictionary of output values. Note that these are normal Python
    lists, rather than numpy arrays. This is to support lists with mixed scalars
    and strings, as in the case of records with categorical variables
    """
    return self._outputValues[outputName]


  def getOutputElementCount(self, outputName):
    """Returns the width of dataOut."""

    # Check if classifier has a 'maxCategoryCount' attribute
    if not hasattr(self, "maxCategoryCount"):
      # Large default value for backward compatibility 
      self.maxCategoryCount = 1000

    if outputName == "categoriesOut":
      return len(self.stepsList)
    elif outputName == "probabilities":
      return len(self.stepsList) * self.maxCategoryCount
    elif outputName == "actualValues":
      return self.maxCategoryCount
    else:
      raise ValueError("Unknown output {}.".format(outputName))



if __name__ == "__main__":
  from nupic.engine import Network

  n = Network()
  classifier = n.addRegion(
    'classifier',
    'py.CLAClassifierRegion',
    '{ steps: "1,2", maxAge: 1000}'
  )
