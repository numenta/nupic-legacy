#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013-15, Numenta, Inc.  Unless you have an agreement
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
This file implements the CLA Classifier region. See the comments in the class
definition of CLAClassifierRegion for a description.
"""

from PyRegion import PyRegion
from nupic.algorithms.cla_classifier_factory import CLAClassifierFactory



class _NumCatgoriesNotSpecified(Exception):
  pass



class _UnknownOutput(Exception):
  pass



class CLAClassifierRegion(PyRegion):
  """
  CLAClassifierRegion implements a CLA specific classifier that accepts a binary
  input from the level below (the "activationPattern") and information from the
  sensor and encoders (the "classification") describing the input to the system
  at that time step.

  When learning, for every bit in activation pattern, it records a history of the
  classification each time that bit was active. The history is bounded by a
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

        # The inputs and outputs are not used in this region because they are
        #  either sparse vectors or dictionaries and hence don't fit the "vector
        #  of real" input/output pattern.
        # There is a custom compute() function provided that accepts the
        #  inputs and outputs.
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
        ),

        outputs=dict(
          classificationResults=dict(
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
          
          numCategories=dict(
            description='Number of categories from the sensor region',
            dataType='UInt32',
            required=True,
            count=1,
            constraints='bool',
            defaultValue=None,
            accessMode='ReadWrite'),

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
               'bucket duty cycles for each activation pattern bit. A lower '
               'alpha results in longer term memory',
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

           clVerbosity=dict(
            description='An integer that controls the verbosity level, '
                        '0 means no verbose output, increasing integers '
                        'provide more verbosity.',
            dataType='UInt32',
            count=1,
            constraints='',
            defaultValue=0 ,
            accessMode='ReadWrite'),

     ),
      commands=dict()
    )

    return ns


  def __init__(self,
               steps='1',
               alpha=0.001,
               clVerbosity=0,
               implementation=None,
               numCategories=None
               ):

    # Convert the steps designation to a list
    self.steps = steps
    self.stepsList = eval("[%s]" % (steps))
    self.alpha = alpha
    self.verbosity = clVerbosity

    # Initialize internal structures
    self._claClassifier = CLAClassifierFactory.create(
        steps=self.stepsList,
        alpha=self.alpha,
        verbosity=self.verbosity,
        implementation=implementation,
        )
    self.learningMode = True
    self.inferenceMode = False
    self.numCategories = numCategories
    self.recordNum = 0
    self._initEphemerals()


  def _initEphemerals(self):
    pass


  def initialize(self, dims, splitterMaps):
    pass


  def clear(self):
    self._claClassifier.clear()


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


  def reset(self):
    pass


  def compute(self, inputs, outputs):
    """
    Process one input sample.
    This method is called by the runtime engine.

    """

    # An input can potentially belong to multiple categories. 
    # If a category value is < 0, it means that the input does not belong to that category.
    categories = [category for category in inputs["categoryIn"] if category >= 0]
  
    activeCells = inputs["bottomUpIn"]
    patternNZ = activeCells.nonzero()[0]
    
    # Allow to train on multiple input categories. 
    # Do inference first, and then train on all input categories.
    #   1. Call classifier. Don't train. Just inference. Train after.
    clResults = self._claClassifier.compute(
      recordNum=self.recordNum, patternNZ=patternNZ, classification=None, learn=False, infer=self.inferenceMode)

    for category in categories:
      classificationIn = {"bucketIdx": int(category),
                          "actValue": int(category)}
  
      #   2. Train classifier, no inference
      self._claClassifier.compute(
          recordNum=self.recordNum, patternNZ=patternNZ, classification=classificationIn, learn=self.learningMode, infer=False)
  
    outputs['actualValues'] = clResults["actualValues"]
    for step in self.stepsList:
      stepIndex = self.stepsList.index(step)
      outputs['classificationResults'][stepIndex] = clResults["actualValues"][clResults[step].argmax()]
      
      # Flaten the rest of the output. For example:
      #   Original dict  {1 : [0.1, 0.3, 0.2, 0.7]
      #                   4 : [0.2, 0.4, 0.3, 0.5]}
      #   becomes: [0.1, 0.3, 0.2, 0.7, 0.2, 0.4, 0.3, 0.5] 
      stepProbabilities = clResults[step]
      for categoryIndex in xrange(self.numCategories):
        flatIndex = categoryIndex + stepIndex * self.numCategories
        if categoryIndex < len(stepProbabilities):        
          outputs['probabilities'][flatIndex] = stepProbabilities[categoryIndex]
        else:
          outputs['probabilities'][flatIndex] = 0.0
          
    
    self.recordNum += 1   


  def customCompute(self, recordNum, patternNZ, classification):
    """
    Process one input sample.

    Parameters:
    --------------------------------------------------------------------
    patternNZ:      list of the active indices from the output below
    classification: dict of the classification information:
                      bucketIdx: index of the encoder bucket
                      actValue:  actual value going into the encoder

    retval:     dict containing inference results, one entry for each step in
                self.steps. The key is the number of steps, the value is an
                array containing the relative likelihood for each bucketIdx
                starting from bucketIdx 0.

                for example:
                  {1 : [0.1, 0.3, 0.2, 0.7]
                   4 : [0.2, 0.4, 0.3, 0.5]}
    """

    return self._claClassifier.compute( recordNum=recordNum,
                                        patternNZ=patternNZ,
                                        classification=classification,
                                        learn = self.learningMode,
                                        infer = self.inferenceMode)


  def getOutputValues(self, outputName):
    """Return the dictionary of output values. Note that these are normal Python
    lists, rather than numpy arrays. This is to support lists with mixed scalars
    and strings, as in the case of records with categorical variables
    """
    return self._outputValues[outputName]


  def getOutputElementCount(self, name):
    """Returns the width of dataOut."""
   
    if name == "classificationResults":
      return len(self.stepsList)
    elif name == "probabilities":
      return len(self.stepsList) * self.numCategories
    elif name == "actualValues":
      return self.numCategories
    else:
      raise _UnknownOutput("Unknown output {}.".format(name))


if __name__=='__main__':
  from nupic.engine import Network
  n = Network()
  classifier = n.addRegion(
    'classifier',
    'py.CLAClassifierRegion',
    '{ steps: "1,2", maxAge: 1000}'
  )
