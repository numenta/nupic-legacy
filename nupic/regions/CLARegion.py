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

import numpy
import sys
import os

from nupic.research.FDRCSpatial2 import FDRCSpatial2
from nupic.research.flat_spatial_pooler import (
    FlatSpatialPooler as PyFlatSpatialPooler)
from nupic.bindings.algorithms import FlatSpatialPooler as CPPFlatSpatialPooler
from nupic.research import TP, TPTrivial
from nupic.research import TP10X2

from nupic.support import getArgumentDescriptions

from PyRegion import PyRegion

from nupic.bindings.algorithms import FDRCSpatial as CPPSP
from nupic.bindings.math import GetNTAReal


##############################################################################

gDefaultTemporalImp = 'py'

def getDefaultSPImp():
  """
  Return the default spatial pooler implementation for this region.
  """
  return 'oldpy'

def getSPClass(spatialImp):
  """ Return the class corresponding to the given spatialImp string
  """

  if spatialImp == 'py':
    return PYSpatialPooler
  elif spatialImp == 'cpp':
    return CPPSpatialPooler
  elif spatialImp == 'oldpy':
    return FDRCSpatial2
  else:
    raise RuntimeError("Invalid spatialImp '%s'. Legal values are: 'py', "
          "'cpp', 'oldpy'" % (spatialImp))



##############################################################################
def _getTPClass(temporalImp):
  """ Return the class corresponding to the given temporalImp string
  """

  if temporalImp == 'py':
    return TP.TP
  elif temporalImp == 'cpp':
    return TP10X2.TP10X2
  elif temporalImp == 'trivial':
    return TPTrivial.TPTrivial
  else:
    raise RuntimeError("Invalid temporalImp '%s'. Legal values are: 'py', "
              "'cpp', and 'trivial'" % (temporalImp))


##############################################################################
def _buildArgs(f, self=None, kwargs={}):
  """
  Get the default arguments from the function and assign as instance vars.

  Return a list of 3-tuples with (name, description, defaultValue) for each
    argument to the function.

  Assigns all arguments to the function as instance variables of CLARegion.
  If the argument was not provided, uses the default value.

  Pops any values from kwargs that go to the function.
  """
  # Get the name, description, and default value for each argument
  argTuples = getArgumentDescriptions(f)
  argTuples = argTuples[1:]  # Remove 'self'

  # Get the names of the parameters to our own constructor and remove them
  # Check for _originial_init first, because if LockAttributesMixin is used,
  #  __init__'s signature will be just (self, *args, **kw), but
  #  _original_init is created with the original signature
  #init = getattr(self, '_original_init', self.__init__)
  init = CLARegion.__init__
  ourArgNames = [t[0] for t in getArgumentDescriptions(init)]
  # Also remove a few other names that aren't in our constructor but are
  #  computed automatically (e.g. numberOfCols for the TP)
  ourArgNames += [
    'numberOfCols',    # TP
    'cellsPerColumn',  # TP
    'nCells',          # FDRSTemporal
    'cloneMap',        # FDRSTemporal / FDRCSpatial
    'numCloneMasters', # FDRSTemporal / FDRCSpatial
    'whichCellsClass', # FDRSTemporal
  ]
  for argTuple in argTuples[:]:
    if argTuple[0] in ourArgNames:
      argTuples.remove(argTuple)

  # Build the dictionary of arguments
  if self:
    for argTuple in argTuples:
      argName = argTuple[0]
      if argName in kwargs:
        # Argument was provided
        argValue = kwargs.pop(argName)
      else:
        # Argument was not provided; use the default value if there is one, and
        #  raise an exception otherwise
        if len(argTuple) == 2:
          # No default value
          raise TypeError("Must provide '%s'" % argName)
        argValue = argTuple[2]
      # Set as an instance variable if 'self' was passed in
      setattr(self, argName, argValue)

  return argTuples


def _getAdditionalSpecs(spatialImp, temporalImp, kwargs={}):
  """Build the additional specs in three groups (for the inspector)

  Use the type of the default argument to set the Spec type, defaulting
  to 'Byte' for None and complex types

  Determines the spatial parameters based on the selected implementation.
  It defaults to FDRCSpatial.
  Determines the temporal parameters based on the temporalImp
  """
  typeNames = {int: 'UInt32', float: 'Real32', str: 'Byte', bool: 'bool', tuple: 'tuple'}

  def getArgType(arg):
    t = typeNames.get(type(arg), 'Byte')
    count = 0 if t == 'Byte' else 1
    if t == 'tuple':
      t = typeNames.get(type(arg[0]), 'Byte')
      count = len(arg)
    if t == 'bool':
      t = 'UInt32'
    return (t, count)

  def getConstraints(arg):
    t = typeNames.get(type(arg), 'Byte')
    if t == 'Byte':
      return 'multiple'
    elif t == 'bool':
      return 'bool'
    else:
      return ''

  FDRSpatialClass = getSPClass(spatialImp)
  FDRTemporalClass = _getTPClass(temporalImp)

  spatialSpec = {}
  sArgTuples = _buildArgs(FDRSpatialClass.__init__)
  tArgTuples = _buildArgs(FDRTemporalClass.__init__)

  for argTuple in sArgTuples:
    d = dict(
      description=argTuple[1],
      accessMode='ReadWrite',
      dataType=getArgType(argTuple[2])[0],
      count=getArgType(argTuple[2])[1],
      constraints=getConstraints(argTuple[2]))

    spatialSpec[argTuple[0]] = d

  temporalSpec = {}
  for argTuple in tArgTuples:
    d = dict(
      description=argTuple[1],
      accessMode='ReadWrite',
      dataType=getArgType(argTuple[2])[0],
      count=getArgType(argTuple[2])[1],
      constraints=getConstraints(argTuple[2]))
    temporalSpec[argTuple[0]] = d

  # Add special parameters that weren't handled automatically
  # Spatial parameters only!
  spatialSpec.update(dict(
    disableSpatial=dict(
      description='Disable the spatial FDR (become a temporal nregion)',
      accessMode='ReadWrite',
      dataType='UInt32',
      count=1,
      constraints='bool'),

    coincidenceCount=dict(
      description='Total number of coincidences.',
      accessMode='Read',
      dataType='UInt32',
      count=1,
      constraints=''),

    spInputNonZeros=dict(
      description='The indices of the non-zero inputs to the spatial pooler',
      accessMode='Read',
      dataType='UInt32',
      count=0,
      constraints=''),

    spOutputNonZeros=dict(
      description='The indices of the non-zero outputs from the spatial pooler',
      accessMode='Read',
      dataType='UInt32',
      count=0,
      constraints=''),

    spOverlapDistribution=dict(
      description="""The overlaps between the active output coincidences
      and the input. The overlap amounts for each coincidence are sorted
      from highest to lowest. """,
      accessMode='Read',
      dataType='Real32',
      count=0,
      constraints=''),

    sparseCoincidenceMatrix=dict(
      description='The coincidences, as a SparseMatrix',
      accessMode='Read',
      dataType='Byte',
      count=0,
      constraints=''),

    spatialPoolerInput=dict(
      description='Input to the spatial pooler.',
      accessMode='Read',
      dataType='Real32',
      count=0,
      constraints=''),

    spatialPoolerOutput=dict(
      description='Output of the spatial pooler.',
      accessMode='Read',
      dataType='Real32',
      count=0,
      constraints=''),

    spNumActiveOutputs=dict(
      description='Number of active spatial pooler outputs',
      accessMode='Read',
      dataType='UInt32',
      count=1,
      constraints=''),

    denseOutput=dict(
      description='Score for each coincidence.',
      accessMode='Read',
      dataType='Real32',
      count=0,
      constraints=''),

    outputCloningWidth=dict(
      description="""The number of columns you'd have to move horizontally
                     (or vertically) before you get back to the same the same
                     clone that you started with.""",
      accessMode='Read',
      dataType='UInt32',
      count=1,
      constraints=''),

    outputCloningHeight=dict(
      description="""If non-negative, can be used to make rectangular
                     (instead of square) cloning fields.""",
      accessMode='Read',
      dataType='UInt32',
      count=1,
      constraints=''),

    saveMasterCoincImages=dict(
      description="""If non-zero, saves an image of the master coincidences
                     every N iterations.""",
      accessMode='Read',
      dataType='UInt32',
      count=1,
      constraints='',
      defaultValue=0),

    spLearningStatsStr=dict(
      description="""String representation of dictionary containing a number
                     of statistics related to learning.""",
      accessMode='Read',
      dataType='Byte',
      count=0,
      constraints='handle'),
  ))


  # Add temporal parameters that weren't handled automatically
  temporalSpec.update(dict(
    disableTemporal=dict(
      description='Disable the temporal FDR (become a spatial region)',
      accessMode='Read',
      dataType='UInt32',
      count=1,
      constraints='bool'),

    orColumnOutputs=dict(
      description="""OR together the cell outputs from each column to produce
      the temporal pooler output. When this mode is enabled, the number of
      cells per column must also be specified (via the 'nCellsPerCol'
      creation parameter) and the output size of the node should be set the
      same as the number of spatial pooler coincidences
      ('coincidenceCount')""",
      accessMode='Read',
      dataType='UInt32',
      count=1,
      constraints='bool'),

    nCellsPerCol=dict(
      description="""The number of cells, or states, allocated per column
      (the number of columns is the same as the number of coincidences).""",
      accessMode='Read',
      dataType='UInt32',
      count=1,
      constraints=''),

    maxSegmentsPerCell=dict(
      description='Max allowed number of segments per cellf.',
      accessMode='ReadWrite',
      dataType='Int32',
      count=1,
      constraints=''),

    maxSynapsesPerSegment=dict(
      description='Max allowed number of segments per cellf.',
      accessMode='ReadWrite',
      dataType='Int32',
      count=1,
      constraints=''),

    tpOutputNonZeros=dict(
      description='The indices of the non-zero outputs from the temporal pooler',
      accessMode='Read',
      dataType='UInt32',
      count=0,
      constraints=''),

    tpNumSynapses=dict(
      description='Total number of synapses learned in the temporal pooler.',
      accessMode='Read',
      dataType='UInt32',
      count=1,
      constraints=''),

    tpNumSynapsesPerSegmentMax=dict(
      description='Max number of synapses found in any one dendritic segment of the temporal pooler.',
      accessMode='Read',
      dataType='UInt32',
      count=1,
      constraints=''),

    tpNumSynapsesPerSegmentAvg=dict(
      description='Average number of synapses learned per dendritic segment.',
      accessMode='Read',
      dataType='Real32',
      count=1,
      constraints=''),

    tpNumSegments=dict(
      description='Total number of dendritic segments present in the temporal pooler.',
      accessMode='Read',
      dataType='UInt32',
      count=1,
      constraints=''),

    tpNumCells=dict(
      description='Total number of cells present in the temporal pooler.',
      accessMode='Read',
      dataType='UInt32',
      count=1,
      constraints=''),

    tpNumActiveCells=dict(
      description='Total number of active cells in the temporal pooler output.',
      accessMode='Read',
      dataType='UInt32',
      count=1,
      constraints=''),

    tpNumActiveColumns=dict(
      description='Total number of active columns in the temporal pooler output.',
      accessMode='Read',
      dataType='UInt32',
      count=1,
      constraints=''),

    tpNumBurstingColumns=dict(
      description='Total number of bursting columns in the temporal pooler output.',
      accessMode='Read',
      dataType='UInt32',
      count=1,
      constraints=''),

  ))

  # The last group is for parameters that aren't strictly spatial or temporal
  otherSpec = dict(
    learningMode=dict(
      description='1 if the node is learning (default 1).',
      accessMode='ReadWrite',
      dataType='UInt32',
      count=1,
      constraints='bool'),

    trainingStep=dict(
      description="""Controls which pooler is trained when learningMode is true.
                  Set to 'spatial' to train spatial pooler, 'temporal'
                  to train temporal pooler, or 'both' to train both
                  simultaneously.""",
      accessMode='ReadWrite',
      dataType='Byte',
      count=0,
      constraints='enum: spatial,temporal,both'),

    inferenceMode=dict(
      description='1 if the node is inferring (default 0).',
      accessMode='ReadWrite',
      dataType='UInt32',
      count=1,
      constraints='bool'),

    activeOutputCount=dict(
      description='Number of active elements in bottomUpOut output.',
      accessMode='Read',
      dataType='UInt32',
      count=1,
      constraints=''),

    spSeed=dict(
      description='Random seed for the spatial pooler.',
      accessMode='Read',
      dataType='UInt32',
      count=1,
      constraints=''),

    tpSeed=dict(
      description='Random seed for the temporal pooler.',
      accessMode='Read',
      dataType='UInt32',
      count=1,
      constraints=''),

    logPathSPInput=dict(
      description='Optional name of spatial pooler input log file.',
      accessMode='ReadWrite',
      dataType='Byte',
      count=0,
      constraints=''),

    logPathSP=dict(
      description='Optional name of spatial pooler output log file.',
      accessMode='ReadWrite',
      dataType='Byte',
      count=0,
      constraints=''),

    logPathSPDense=dict(
      description='Optional name of spatial pooler dense output log file.',
      accessMode='ReadWrite',
      dataType='Byte',
      count=0,
      constraints=''),

    logPathTP=dict(
      description='Optional name of temporal pooler output log file.',
      accessMode='ReadWrite',
      dataType='Byte',
      count=0,
      constraints=''),

    cellsSavePath=dict(
      description="""Optional path to file in which large temporal pooler cells
                     data structure is to be saved.""",
      accessMode='ReadWrite',
      dataType='Byte',
      count=0,
      constraints=''),

    statelessMode=dict(
      description='Ignores temporal state when in inference mode.',
      accessMode='ReadWrite',
      dataType='UInt32',
      count=1,
      constraints='bool'),

    temporalImp=dict(
      description="""Which temporal pooler implementation to use. Set to either
       'simple', 'py' or 'cpp'. The 'simple' implementation supports only 1 cell
       per column and is typically only used for vision spatial invariance
       applications. The 'cpp' implementation is optimized for speed in C++.
       The 'trivial' implementation makes random or zeroth order predictions.""",
      accessMode='ReadWrite',
      dataType='Byte',
      count=0,
      constraints='enum: simple, full, cpp, trivial'),

    computeTopDown=dict(
      description='1 to compute and output the topDownOut output',
      accessMode='ReadWrite',
      dataType='UInt32',
      count=1,
      constraints='bool'),

    nMultiStepPrediction=dict(
      description="""The number of time steps to be predicted in future.""",
      accessMode='ReadWrite',
      dataType='UInt32',
      count=1,
      constraints=''),

  )

  return spatialSpec, temporalSpec, otherSpec



class CLARegion(PyRegion):

  """
  Fixed Distributed Representation Continuous node (both spatial and temporal).
  This node is designed to implement an entire HTM level as a continuous sheet
  of coincidence detectors and temporal poolers.

  Uses the FDRCSpatial and FDRTemporal classes to do most of the work. This node
  has just one FDRCSpatial and FDRTemporal instance for the entire level and
  does *not* support the concept of "baby nodes" within it.

  The output from the FDRCSpatial instances is saved in spatialPoolerOutput.

  The disableSpatial and disableTemporal parameters can be used to turn the
  node into a temporal-only or spatial-only node.

  Parameter names, default values, and descriptions are retrieved automatically
  from FDRCSpatial and FDRTemporal. Thus, there are only a few hardcoded
  arguments in __init__, and the rest are passed to the appropriate underlying
  class. The NodeSpec is mostly built automatically from these parameters, too.

  If you add a parameter to FDRCSpatial or FDRTemporal, it will be exposed
  through CLARegion automatically as if it were in CLARegion.__init__, with the
  right default value. Add an entry in the __init__ docstring for it too, and
  that will be brought into the NodeSpec.
  CLARegion will maintain the parameter as its own instance variable and also
  pass it to the FDRCSpatial or FDRTemporal. If the parameter is changed,
  CLARegion will propagate the change.

  If you want to do something different with the parameter, add it as an
  argument into CLARegion.__init__, which will override all the default handling.
  """

  def __init__(self,

               # Constructor arguments for FDRSpatial and FDRTemporal are
               # picked up automatically. There is no need to add them anywhere
               # in CLARegion, unless you need to do something special with them.
               # See docstring above.

               # These args are used by CLARegion only or need special handling
               disableSpatial=False,
               disableTemporal=False,
               orColumnOutputs=False,
               nCellsPerCol=1,
               trainingStep = 'temporal',
               cellsSavePath='',
               statelessMode=False,
               storeDenseOutput=False, #DEPRECATED
               outputCloningWidth=0,
               outputCloningHeight=0,
               saveMasterCoincImages = 0,
               temporalImp='py', #'py', 'simple' or 'cpp'
               spatialImp=getDefaultSPImp(),   #'py', 'cpp', or 'oldpy'
               computeTopDown = 0,
               nMultiStepPrediction = 0,

               # We have separate seeds for spatial and temporal
               spSeed=-1,
               tpSeed=-1,

               # Needed for vision framework
               bottomUpOut=None,
               **kwargs):

    #if disableSpatial and disableTemporal:
    #  raise RuntimeError("Disable both the spatial and temporal components? "
    #                     "That would make it too easy.")

    # Make sure our tuple arguments are integers
    for name in ['coincidencesShape', 'inputShape']:
      if name in kwargs:
        (height, width) = kwargs[name]
        kwargs[name] = (int(height), int(width))

    # Which FDR Temporal implementation?
    FDRCSpatialClass = getSPClass(spatialImp)
    FDRTemporalClass = _getTPClass(temporalImp)

    # Pull out the spatial and temporal arguments automatically
    # These calls whittle down kwargs and create instance variables of CLARegion
    sArgTuples = _buildArgs(FDRCSpatialClass.__init__, self, kwargs)
    tArgTuples = _buildArgs(FDRTemporalClass.__init__, self, kwargs)

    # Make a list of automatic spatial and temporal arg names for later use
    self._spatialArgNames = [t[0] for t in sArgTuples]
    self._temporalArgNames = [t[0] for t in tArgTuples]

    # Start out in stage learn
    self.learningMode = True
    self.inferenceMode = False

    PyRegion.__init__(self, **kwargs)

    # Initialize all non-persistent base members, as well as give
    # derived class an opportunity to do the same.
    self._loaded = False
    self._initialize()

    # Debugging support, used in _conditionalBreak
    self.breakPdb = False
    self.breakKomodo = False

    # CLARegion only, or special handling
    self.disableSpatial = disableSpatial
    self.saveMasterCoincImages = saveMasterCoincImages
    self.disableTemporal = disableTemporal
    self.orColumnOutputs = orColumnOutputs
    self.nCellsPerCol = nCellsPerCol  # Modified in initInNetwork
    self.coincidenceCount = self.coincidencesShape[0] * self.coincidencesShape[1]
    self.temporalImp = temporalImp
    self.spatialImp = spatialImp
    self.computeTopDown = computeTopDown
    self.nMultiStepPrediction = nMultiStepPrediction

    # Handle -1 for cloning sizes, which essentially just means no cloning...
    # ...also handle 0, since that's the new default...
    if outputCloningWidth in (0, -1):
      outputCloningWidth = self.coincidencesShape[1]
    if outputCloningHeight in (0, -1):
      outputCloningHeight = self.coincidencesShape[0]

    self.outputCloningWidth = outputCloningWidth
    self.outputCloningHeight = outputCloningHeight

    # Make the clone map, which is used by both spatial and temporal components.
    self._cloneMap, self._numCloneMasters = self.makeCloneMap(
      self.coincidencesShape, outputCloningWidth, outputCloningHeight
    )

    # Both FDRCSpatial and FDRTemporal
    self.tpSeed = tpSeed
    self.spSeed = spSeed
    self.trainingStep = trainingStep
    self.logPathSPInput = ''
    self.logPathSP = ''
    self.logPathSPDense = ''
    self.logPathTP = ''
    # Used to save TP cells data structure to auxiliary file
    self.cellsSavePath = cellsSavePath
    # Instructs node to ignore past temporal state when operating in
    # inference mode; i.e., tells node to ignore the actual resetSignal
    # input and treat it as if the resetSignal was *always* set (in
    # inference mode only)
    self.statelessMode = statelessMode
    self._hasRunInference = False

    # Variables set up in initInNetwork()
    self._sfdr                = None  # FDRCSpatial instance
    self._tfdr                = None  # FDRTemporal instance
    self._numOutputs          = None  # Number of outputs allocated per node
    self._spatialPoolerOutput = None  # Hang on to this output for debugging
    self._tpSeqOutput         = None  # Hang on to this for supporting the
                                      #  tpSeqOutputNonZeros parameter
    self._spatialPoolerInput  = None  # Hang on to this for supporting the
                                      #  spInputNonZeros parameter
    self._rfOutput            = None  # Hang on to this for supporting the
                                      #  tpOutputNonZeros parameter

    # Read-only node parameters
    self.activeOutputCount        = None
    self.cppOutput                = None
    self.file = None

    # For inspector usage
    #from dbgp.client import brk; brk(port=9019)
    self._spatialSpec, self._temporalSpec, self._otherSpec = \
                    _getAdditionalSpecs(spatialImp=self.spatialImp, temporalImp=self.temporalImp)

  #############################################################################
  #
  # Initialization code
  #
  #############################################################################
  def _initialize(self):
    """
    Initialize all ephemeral data members, and give the derived
    class the opportunity to do the same by invoking the
    virtual member _initEphemerals(), which is intended to be
    overridden.
    """

    for attrName in self._getEphemeralMembersBase():
      if attrName != "_loaded":
        if hasattr(self, attrName):
          if self._loaded:
            # print self.__class__.__name__, "contains base class member '%s' " \
            #     "after loading." % attrName
            # TODO: Re-enable warning or turn into error in a future release.
            pass
          else:
            print self.__class__.__name__, "contains base class member '%s'" % \
                attrName
    if not self._loaded:
      for attrName in self._getEphemeralMembersBase():
        if attrName != "_loaded":
          # if hasattr(self, attrName):
          #   import pdb; pdb.set_trace()
          assert not hasattr(self, attrName)
        else:
          assert hasattr(self, attrName)

    # Profiling information
    self._profileObj = None
    self._iterations = 0

    # Let derived class initialize ephemerals
    self._initEphemerals()
    self._checkEphemeralMembers()

  #############################################################################
  def initialize(self, dims, splitterMaps):
    # Calculate the total number of coincidences
    nSPInputs = int(self.inputShape[0] * self.inputShape[1])

    if self.disableSpatial:
      nNodeInputs = self.coincidenceCount
    else:
      nNodeInputs = nSPInputs
    if self.disableTemporal:
      self.nCellsPerCol = 1
    self._numOutputs = self.getOutputElementCount('bottomUpOut')
    if self.nCellsPerCol == -1:
      raise Exception("When running with temporal enabled, you must specify nCellsPerCol when creating the network")

    # Make sure the number of input elements defined by 'inputShape' matches
    #  the total number of inputs sent from the node below us
    if self.disableSpatial:
      if self.coincidenceCount  != nNodeInputs:
         raise Exception("The number of columns for this temporal-only node, "
                         "which is set by coincidenceCount (%s), "
                         % str(self.coincidenceCount) +
                         "does not match the number of elements in this node's "
                         "input (%d)" % nNodeInputs)

    # If this node is being used in temporal-only mode (no spatial FDR), then
    #  the number of input elements is the number of columns
    else:
      if nSPInputs != nNodeInputs:
        raise Exception("The number of inputs for this node, "
                         "which is set by inputShape (%s), "
                         % str(self.inputShape) +
                         "does not match the number of elements in this node's "
                         "input (%d)" % nNodeInputs)

    # Zero out the spatial output in case it is requested
    self._spatialPoolerOutput = numpy.zeros(self.coincidenceCount,
                                            dtype=GetNTAReal())


    # Zero out the rfInput in case it is requested
    self._spatialPoolerInput = numpy.zeros((1,nNodeInputs), dtype=GetNTAReal())

    # Zero out the rfOutput in case it is requested
    self._rfOutput = numpy.zeros((1, self._numOutputs), dtype=GetNTAReal())


    if self.disableTemporal:
      # Spatial-only mode; verify that coincidence count matches output count
      if self._numOutputs != self.coincidenceCount:
        errorStr = "When disableTemporal is True, coincidenceCount " + \
                           "should be same size as outputElementCount."
        errorStr += "   coincidenceCount = " + str(self.coincidenceCount)
        errorStr += "   outputElementCount = " + str(self._numOutputs)
        raise RuntimeError(errorStr)
      self.nCellsPerCol = 1

    else:
      # TP is being used
      # How many states can we allocate per coincidence?
      if self.nCellsPerCol == -1:
        self.nCellsPerCol = self._numOutputs // self.coincidenceCount

      # If the number of cells per column was specified as a creation parameter,
      #  then most likely we are using 'orColumnOutputs' together mode.
      else:
        if self.orColumnOutputs:
          if self.coincidenceCount != self._numOutputs:
            raise RuntimeError ("When using 'orColumnOutputs' mode, "
                "the node output size should be set to be the same as the "
                "number of spatial pooler coincidences (%d in this case). " \
                % (self.coincidenceCount))
        else:
          if self.nCellsPerCol != self._numOutputs // self.coincidenceCount:
            raise RuntimeError ("When not using 'orColumnOutputs' mode, "
                "the 'nCellsPerCol' should be left unspecified - the node "
                "will calculate this given the output size and number of "
                "spatial pooler coincidences.")
      if self.nCellsPerCol == 0:
        raise RuntimeError("Calculated nCellsPerCol=0. This may occur because "
                           "bottomUpOut is smaller than coincidenceCount -- "
                           "or if disableSpatial is True, because bottomUpOut "
                           "is smaller than the number of elements coming "
                           "into the node (each of which becomes a column)")

      # Allocate a temporal FDR object for each baby node
      # Retrieve the necessary extra arguments that were handled automatically
      autoArgs = dict((name, getattr(self, name))
                       for name in self._temporalArgNames)
      autoArgs.pop('seed')

      if self._tfdr is None:
        tpClass = _getTPClass(self.temporalImp)

        if self.temporalImp == 'simple':
          assert (self.nCellsPerCol == 1)
          self._tfdr = tpClass(
               nCells=self.coincidencesShape,
               seed=self.tpSeed,
               cloneMap=self._cloneMap,
               numCloneMasters=self._numCloneMasters,
               **autoArgs)

        elif self.temporalImp in ['py', 'py_v1', 'cpp', 'cpp_v1']:
          self._tfdr = tpClass(
               numberOfCols=self.coincidencesShape[0] * self.coincidencesShape[1],
               cellsPerColumn=self.nCellsPerCol,
               seed=self.tpSeed,
               **autoArgs)

        elif self.temporalImp == 'trivial':
          self._tfdr = TPTrivial.TPTrivial(
               numberOfCols=self.coincidencesShape[0] * self.coincidencesShape[1],
               seed=self.tpSeed,
               **autoArgs)
        else:
          raise RuntimeError("Invalid temporalImp")

    # Allocate space for the tpSeqOutput
    self._tpSeqOutput = numpy.zeros(self.nCellsPerCol * self.coincidenceCount,
                          dtype=GetNTAReal())

    # Compute the active output count
    if self.activeOutputCount is None:
      if self.disableTemporal or self.orColumnOutputs:
        self.activeOutputCount = self.coincidenceCount
      else:
        self.activeOutputCount = self.nCellsPerCol * self.coincidenceCount

    # Allocate the spatial pooler
    self._allocateSpatialFDR(None)

    # Allocate multi step prediction variables
    self._allocateMultiStepPredictionVariables()

  #############################################################################
  def _allocateMultiStepPredictionVariables(self,):
    """Preallocate space for the multistep prediction variables to save time."""

    if self.nMultiStepPrediction > 0:
      if not self.disableTemporal:
        # This variable holds the predictions in the column space
        self._multiStepColumnPrediction = numpy.zeros((self.nMultiStepPrediction,
                                                     self.coincidenceCount),
                                                    dtype=GetNTAReal())

      # This variable holds the predictions in the input space
      if self.disableSpatial:
        nNodeInputs = self.coincidenceCount
      else:
        nNodeInputs = int(self.inputShape[0] * self.inputShape[1])
      self._multiStepInputPrediction  = numpy.zeros((self.nMultiStepPrediction,
                                                     nNodeInputs),
                                                    dtype=GetNTAReal())



  #############################################################################
  def _allocateSpatialFDR(self, rfInput):
    """Allocate the spatial FDR instance, which requires the input length."""
    if self._sfdr or self.disableSpatial:
      return

    # Retrieve the necessary extra arguments that were handled automatically
    autoArgs = dict((name, getattr(self, name))
                     for name in self._spatialArgNames)
    autoArgs.pop('seed')


    FDRCSpatialClass = getSPClass(self.spatialImp)
    self._sfdr =  FDRCSpatialClass(
      cloneMap=self._cloneMap,
      numCloneMasters=self._numCloneMasters,
      seed=self.spSeed,
      **autoArgs)


  #############################################################################


  #############################################################################
  @staticmethod
  def makeCloneMap(columnsShape, outputCloningWidth, outputCloningHeight=-1):
    """Make a two-dimensional clone map mapping columns to clone master.

    This makes a map that is (numColumnsHigh, numColumnsWide) big that can
    be used to figure out which clone master to use for each column.  Here are
    a few sample calls

    >>> CLARegion.makeCloneMap(columnsShape=(10, 6), outputCloningWidth=4)
    (array([[ 0,  1,  2,  3,  0,  1],
           [ 4,  5,  6,  7,  4,  5],
           [ 8,  9, 10, 11,  8,  9],
           [12, 13, 14, 15, 12, 13],
           [ 0,  1,  2,  3,  0,  1],
           [ 4,  5,  6,  7,  4,  5],
           [ 8,  9, 10, 11,  8,  9],
           [12, 13, 14, 15, 12, 13],
           [ 0,  1,  2,  3,  0,  1],
           [ 4,  5,  6,  7,  4,  5]], dtype=uint32), 16)

    >>> CLARegion.makeCloneMap(columnsShape=(7, 8), outputCloningWidth=3)
    (array([[0, 1, 2, 0, 1, 2, 0, 1],
           [3, 4, 5, 3, 4, 5, 3, 4],
           [6, 7, 8, 6, 7, 8, 6, 7],
           [0, 1, 2, 0, 1, 2, 0, 1],
           [3, 4, 5, 3, 4, 5, 3, 4],
           [6, 7, 8, 6, 7, 8, 6, 7],
           [0, 1, 2, 0, 1, 2, 0, 1]], dtype=uint32), 9)

    >>> CLARegion.makeCloneMap(columnsShape=(7, 11), outputCloningWidth=5)
    (array([[ 0,  1,  2,  3,  4,  0,  1,  2,  3,  4,  0],
           [ 5,  6,  7,  8,  9,  5,  6,  7,  8,  9,  5],
           [10, 11, 12, 13, 14, 10, 11, 12, 13, 14, 10],
           [15, 16, 17, 18, 19, 15, 16, 17, 18, 19, 15],
           [20, 21, 22, 23, 24, 20, 21, 22, 23, 24, 20],
           [ 0,  1,  2,  3,  4,  0,  1,  2,  3,  4,  0],
           [ 5,  6,  7,  8,  9,  5,  6,  7,  8,  9,  5]], dtype=uint32), 25)

    >>> CLARegion.makeCloneMap(columnsShape=(7, 8), outputCloningWidth=3, outputCloningHeight=4)
    (array([[ 0,  1,  2,  0,  1,  2,  0,  1],
           [ 3,  4,  5,  3,  4,  5,  3,  4],
           [ 6,  7,  8,  6,  7,  8,  6,  7],
           [ 9, 10, 11,  9, 10, 11,  9, 10],
           [ 0,  1,  2,  0,  1,  2,  0,  1],
           [ 3,  4,  5,  3,  4,  5,  3,  4],
           [ 6,  7,  8,  6,  7,  8,  6,  7]], dtype=uint32), 12)

    The basic idea with this map is that, if you imagine things stretching off
    to infinity, every instance of a given clone master is seeing the exact
    same thing in all directions.  That includes:
    - All neighbors must be the same
    - The "meaning" of the input to each of the instances of the same clone
      master must be the same.  If input is pixels and we have translation
      invariance--this is easy.  At higher levels where input is the output
      of lower levels, this can be much harder.
    - The "meaning" of the inputs to neighbors of a clone master must be the
      same for each instance of the same clone master.


    The best way to think of this might be in terms of 'inputCloningWidth' and
    'outputCloningWidth'.
    - The 'outputCloningWidth' is the number of columns you'd have to move
      horizontally (or vertically) before you get back to the same the same
      clone that you started with.  MUST BE INTEGRAL!
    - The 'inputCloningWidth' is the 'outputCloningWidth' of the node below us.
      If we're getting input from an sensor where every element just represents
      a shift of every other element, this is 1.
      At a conceptual level, it means that if two different inputs are shown
      to the node and the only difference between them is that one is shifted
      horizontally (or vertically) by this many pixels, it means we are looking
      at the exact same real world input, but shifted by some number of pixels
      (doesn't have to be 1).  MUST BE INTEGRAL!

    At level 1, I think you could have this:
    * inputCloningWidth = 1
    * sqrt(coincToInputRatio^2) = 2.5
    * outputCloningWidth = 5
    ...in this case, you'd end up with 25 masters.


    Let's think about this case:
      input:    - - -  0     1     2     3     4     5     -     -   - - -
      columns:        0 1  2 3 4  0 1  2 3 4  0 1  2 3 4  0 1  2 3 4

    ...in other words, input 0 is fed to both column 0 and column 1.  Input 1
    is fed to columns 2, 3, and 4, etc.  Hopefully, you can see that you'll
    get the exact same output (except shifted) with:
      input:    - - -  -     -     0     1     2     3     4     5   - - -
      columns:        0 1  2 3 4  0 1  2 3 4  0 1  2 3 4  0 1  2 3 4

    ...in other words, we've shifted the input 2 spaces and the output shifted
    5 spaces.


    *** The outputCloningWidth MUST ALWAYS be an integral multiple of the ***
    *** inputCloningWidth in order for all of our rules to apply.         ***
    *** NOTE: inputCloningWidth isn't passed here, so it's the caller's   ***
    ***       responsibility to ensure that this is true.                ***

    *** The outputCloningWidth MUST ALWAYS be an integral multiple of     ***
    *** sqrt(coincToInputRatio^2), too.                                  ***

    @param  columnsShape         The shape (height, width) of the columns.
    @param  outputCloningWidth   See docstring above.
    @param  outputCloningHeight  If non-negative, can be used to make
                                 rectangular (instead of square) cloning fields.
    @return cloneMap             An array (numColumnsHigh, numColumnsWide) that
                                 contains the clone index to use for each
                                 column.
    @return numDistinctClones    The number of distinct clones in the map.  This
                                 is just outputCloningWidth*outputCloningHeight.
    """
    if outputCloningHeight < 0:
      outputCloningHeight = outputCloningWidth

    columnsHeight, columnsWidth = columnsShape

    numDistinctMasters = outputCloningWidth * outputCloningHeight

    a = numpy.empty((columnsHeight, columnsWidth), 'uint32')
    for row in xrange(columnsHeight):
      for col in xrange(columnsWidth):
        a[row, col] = (col % outputCloningWidth) + \
                      (row % outputCloningHeight) * outputCloningWidth

    return a, numDistinctMasters


  #############################################################################
  #
  # Core compute methods: learning, inference, and prediction
  #
  #############################################################################


  #############################################################################
  def compute(self, inputs, outputs):
    """
    Run one iteration of CLARegion's compute, profiling it if requested.

    The guts of the compute are contained in the _compute() call so that
    we can profile it if requested.
    """

    # Uncomment this to find out who is generating divide by 0, or other numpy warnings
    # numpy.seterr(divide='raise', invalid='raise', over='raise')

    # Modify this line to turn on profiling for a given node. The results file
    #  ('hotshot.stats') will be sensed and printed out by the vision framework's
    #  RunInference.py script at the end of inference.
    # Also uncomment the hotshot import at the top of this file.
    if False and self.learningMode \
        and self._iterations > 100 and self._iterations <= 500:

      import hotshot.stats
      if self._iterations == 500:
        print "\n  Collecting and sorting internal node profiling stats generated by hotshot..."
        stats = hotshot.stats.load("hotshot.stats")
        stats.strip_dirs()
        stats.sort_stats('time', 'calls')
        stats.print_stats()

      if self._profileObj is None:
        print "\n  Preparing to capture profile using hotshot..."
        if os.path.exists('hotshot.stats'):
          # There is an old hotshot stats profile left over, remove it.
          os.remove('hotshot.stats')
        self._profileObj = hotshot.Profile("hotshot.stats", 1, 1)
                                          # filename, lineevents, linetimings
      self._profileObj.runcall(self._compute, *[inputs, outputs])
    else:
      self._compute(inputs, outputs)

  def _compute(self, inputs, outputs):
    """
    Run one iteration of CLARegion's compute
    """

    self._iterations += 1

    # Get our inputs into numpy arrays
    buInputVector = inputs['bottomUpIn']

    resetSignal = False
    if 'resetIn' in inputs:
      assert len(inputs['resetIn']) == 1
      resetSignal = inputs['resetIn'][0] != 0

    if self.learningMode:
      # print "INPUT: %s" %  [ i for i in xrange(len(buInputVector)) if buInputVector[i] != 0]
      rfOutput = self._doLearn(
        rfInput = buInputVector.reshape((1,buInputVector.size)),
        resetSignal = resetSignal,
        outputs = outputs
        )

    if self.inferenceMode:
      rfOutput = self._doInfer(
        rfInput = buInputVector.reshape((1,buInputVector.size)),
        resetSignal = resetSignal,
        outputs = outputs
        )

      if self.nMultiStepPrediction > 0:
        self._doPredict()

      # Write the bottom up out to our node outputs only if we are doing
      # inference
      outputs['bottomUpOut'][:] = rfOutput.flat


  #############################################################################
  def _doLearn(self, rfInput, resetSignal, outputs):
    """ Learn the current input

    Parameters:
    --------------------------------------------
    rfInput:      Input vector. Shape is: (1, inputVectorLen).
                  NOTE: As a special case, this can be None when 'resetSignal'
                  is True to indicate that we should "wrap up" the current
                  sequence learning before switching into inference mode. This
                  is necessary when doing batch-like learning which is used
                  for serial cloning and cross-training mode in FDRTemporal.
    resetSignal:  True if reset is asserted
    outputs:      The node outputs

    """

    # Conditional compute break
    self._conditionalBreak()

    # Stores in self._spatialPoolerOutput
    # If disableSpatial is True, just copies rfInput to _spatialPoolerOutput
    if rfInput is not None:
      # This is the normal case
      self._doSpatialInfer(rfInput, resetSignal, outputs)

    # We want to train the temporal pooler if it is not disabled and trainingStep
    # is set appropriately
    if not self.disableTemporal and (self.trainingStep != 'spatial'):
      # Update the counts (add 1 for each active coincidence)
      # This is done here, rather than in _doSpatialInfer, because we only want
      #  to count during learning
      #if rfInput is not None:
      #  self.coincidenceVectorCounts += self._spatialPoolerOutput.astype('bool')

      # First, we feed in the evidence into each baby node so that they
      #  can update their seqOutputs based on the bottom up and their
      #  current lateral activations (which were computed at the end of the
      #  last compute).
      if resetSignal:
        self._tfdr.reset()
      if rfInput is not None:
        self._tfdr.learn(self._spatialPoolerOutput)

      # No rfInput with reset indicates finishLearning
      if rfInput is None and resetSignal:
        self._tfdr.finishLearning()


  #############################################################################
  def _doInfer(self, rfInput, resetSignal, outputs):
    """
    Do one iteration of inference.

    Parameters:
    --------------------------------------------
    rfInput:      Input vector. Shape is: (1, inputVectorLen).
    resetSignal:  True if reset is asserted

    """

    # If we're in stateless mode, then act as if we always receive
    # a reset even if we don't really receive one.
    resetSignal |= bool(self.statelessMode)

    # Conditional compute break
    self._conditionalBreak()

    # Zero the output
    self._rfOutput.fill(0)

    # Stores in self._spatialPoolerOutput
    # If disableSpatial is True, just copies rfInput to _spatialPoolerOutput
    self._doSpatialInfer(rfInput, resetSignal, outputs)

    if not self.disableTemporal:
      if resetSignal:
        self._sequencePos = 0  # Position within the current sequence

      # --------------------------------------------------------------
      # Temporal inference
      # First, feed in the bottom up evidence so that each node can update it's
      #  seqOutput based on it's lateral activation (which was computed at the
      #  end of the last compute) and the current input. The seqOutput includes
      #  only the cells that had lateral activation into their first time slot
      #  AND now receive bottom up input.
      self._predictedColumns = []
      if resetSignal:
        self._tfdr.reset()

      # Run Inference
      tpOut = self._tfdr.infer(self._spatialPoolerOutput)

      # Different TP implementations are currently returning different results
      # todo: fix this in the TP
      if hasattr(tpOut, '__len__') and len(tpOut) == 2:
        (temporalOut, seqOut) = tpOut
      else:
        temporalOut = tpOut
        seqOut = self._tfdr.getActiveState()

      # OR'ing together the cells in each column?
      if self.orColumnOutputs:
        temporalOut = temporalOut.reshape(self.coincidenceCount,
                                          self.nCellsPerCol).max(axis=1)

      self._rfOutput[0, :len(temporalOut)] = temporalOut
      self._tpSeqOutput = seqOut

      self._sequencePos += 1

      outputTP = self._rfOutput

    else:
      # Copy the spatial output to the node output
      self._rfOutput = self._spatialPoolerOutput.copy()
      outputTP = None

    # Direct logging of TP outputs (faster than node watch)
    if self._fpLogTP and outputTP is not None:
      output = outputTP.reshape(-1)
      outputNZ = output.nonzero()[0]
      outStr = " ".join(["%d" % int(token) for token in outputNZ])
      print >>self._fpLogTP, output.size, outStr

    # Direct logging of SP outputs (faster than node watch)
    if self._fpLogSP:
      output = self._spatialPoolerOutput.reshape(-1)
      outputNZ = output.nonzero()[0]
      outStr = " ".join(["%d" % int(token) for token in outputNZ])
      print >>self._fpLogSP, output.size, outStr

    # Direct logging of SP inputs (faster than node watch)
    if self._fpLogSPInput:
      output = rfInput.reshape(-1)
      outputNZ = output.nonzero()[0]
      outStr = " ".join(["%d" % int(token) for token in outputNZ])
      print >>self._fpLogSPInput, output.size, outStr

    return self._rfOutput

  #############################################################################
  def _doPredict(self,):
    """
    Do one iteration of multi-step prediction.

    Parameters:
    --------------------------------------------

    """

    # 1) Multi step predictions at the column level
    # If there is no temporal pooler, we just copy over the spatial pooler output
    # to all future timesteps. We can skip updating the column prediction in this
    # trivial case to save computation time.
    if not self.disableTemporal:
      self._multiStepColumnPrediction[:] = \
                            self._tfdr.predict(nSteps=self.nMultiStepPrediction)

    # 2) Multi step predictions at the input level
    for i in range(self.nMultiStepPrediction):
      if not self.disableTemporal:
        spTopDownIn = self._multiStepColumnPrediction[i]
      else:
        spTopDownIn = self._spatialPoolerOutput

      # Input reconstruction
      self._multiStepInputPrediction[i,:] = spTopDownIn


  #############################################################################
  def _doSpatialInfer(self, rfInput, resetSignal, outputs):
    """
    Do inference through the spatial pooler.
    No return value. Stores the output in self._spatialPoolerOutput.
    Sets up the spatial FDR(s) first if necessary.
    """

    # Save the rfInput for the spInputNonZeros parameter
    self._spatialPoolerInput = rfInput.reshape(-1)
    assert(rfInput.shape[0] == 1)

    if self.disableSpatial:
      self._spatialPoolerOutput = rfInput.flatten()
      self._hasRunInference = True
      return

    #if not self._sfdr:
    #  self._allocateSpatialFDR(rfInput)

    # Is the spatial pooler in learning mode?
    learnFlag = (self.learningMode and (self.trainingStep in ('spatial', 'both')))
    inferFlag = not learnFlag


    # Run inference using the spatial pooler. We learn on the coincidences only
    # if we are in learning mode and trainingStep is set appropriately.

    # Save master coincidences if requested
    if learnFlag and (self.saveMasterCoincImages>0) and \
        (self._iterations%self.saveMasterCoincImages == 0):
      self.saveMasterCoincidenceImage()


    if (self._sfdr.__class__ == FDRCSpatial2):
      # Backwards compatibility
      output = self._sfdr.compute(rfInput[0], learnFlag, inferFlag)
      self._spatialPoolerOutput[:] = output[:]

    else:  
      inputVector = numpy.array(rfInput[0]).astype('uint32')
      outputVector = numpy.zeros(self._sfdr.getNumColumns()).astype('uint32')
      self._sfdr.compute(inputVector, learnFlag, outputVector)
      self._spatialPoolerOutput[:] = outputVector[:]



    # This is queried by the node inspectors to indicate that it is safe
    #  to ask for the variables they need.
    self._hasRunInference = True


  #############################################################################
  def predict(self, nSteps=1, mode='coincidences'):
    """Predict forward and return active columns (coincidences) or cells."""

    if nSteps != 1:
      raise ValueError("Only one-step prediction is currently supported.")

    if mode != "coincidences":
      raise ValueError("Only coincidence prediction is currently supported.")

    if self.disableTemporal:
      raise RuntimeError("This is just a spatial node (disableTemporal was "
                         "True) so it cannot do prediction")

    # No prediction during learning (?).  ...at least not at the moment...
    if self.learningMode:
      return None

    return self._tfdr.predict(1)[0]

  #############################################################################
  #
  # Region API support methods: getSpec, getParameter, and setParameter
  #
  #############################################################################

  #############################################################################
  @classmethod
  def getBaseSpec(cls):
    """Return the base Spec for CLARegion.

    Doesn't include the spatial, temporal and other parameters
    """
    spec = dict(
      description=CLARegion.__doc__,
      singleNodeOnly=True,
      inputs=dict(
          bottomUpIn=dict(
          description="""The input signal, conceptually organized as an
                         image pyramid data structure, but internally
                         organized as a flattened vector.""",
          dataType='Real32',
          count=0,
          required=True,
          regionLevel=False,
          isDefaultInput=True,
          requireSplitterMap=False),

          resetIn=dict(
          description="""Effectively a boolean flag that indicates whether
                         or not the input vector received in this compute cycle
                         represents the first training presentation in a
                         new temporal sequence.""",
          dataType='Real32',
          count=1,
          required=False,
          regionLevel=True,
          isDefaultInput=False,
          requireSplitterMap=False),
      ),

      outputs=dict(
        bottomUpOut=dict(
          description="""The output signal generated from the bottom-up inputs
                          from lower levels.""",
          dataType='Real32',
          count=0,
          regionLevel=True,
          isDefaultOutput=True),

        topDownOut=dict(
          description="""The top-down output signal, generated from
                        feedback from upper levels""",
          dataType='Real32',
          count=0,
          regionLevel=True,
          isDefaultOutput=True),

        spReconstructedIn = dict(
          description="""The top-down output, if generated only from the current
                         SP output. This can be used to evaluate how well the
                         SP is representing the inputs independent of the TP.""",
          dataType='Real32',
          count=0,
          regionLevel=True,
          isDefaultOutput=True),
      ),

      parameters=dict(
        breakPdb=dict(
          description='Set to 1 to stop in the pdb debugger on the next compute',
          dataType='UInt32',
          count=1,
          constraints='bool',
          defaultValue=0,
          accessMode='ReadWrite'),

        breakKomodo=dict(
          description='Set to 1 to stop in the Komodo debugger on the next compute',
          dataType='UInt32',
          count=1,
          constraints='bool',
          defaultValue=0,
          accessMode='ReadWrite'),

      ),
      commands = {}
    )

    return spec

  @classmethod
  def getSpec(cls):
    """Return the Spec for CLARegion.

    The parameters collection is constructed based on the parameters specified
    by the variosu components (spatialSpec, temporalSpec and otherSpec)
    """
    spec = cls.getBaseSpec()
    s, t, o = _getAdditionalSpecs(spatialImp=getDefaultSPImp(),
                                  temporalImp=gDefaultTemporalImp)
    spec['parameters'].update(s)
    spec['parameters'].update(t)
    spec['parameters'].update(o)

    #from dbgp.client import brk; brk(port=9011)
    return spec


  #############################################################################
  def getParameter(self, parameterName, index=-1):
    """
      Get the value of a NodeSpec parameter. Most parameters are handled
      automatically by PyRegion's parameter get mechanism. The ones that need
      special treatment are explicitly handled here.
    """

    # Ignore nodeSet since we have only a single node
    # assert len(nodeSet) == 1
    # babyIdx = nodeSet[0][0]
    # assert(babyIdx == 0)

    if parameterName == 'spatialPoolerInput':
      return list(self._spatialPoolerInput.reshape(-1))
    elif parameterName == 'spatialPoolerOutput':
      return list(self._spatialPoolerOutput)
    elif parameterName == 'spNumActiveOutputs':
      return len(self._spatialPoolerOutput.nonzero()[0])

    elif parameterName == 'spOutputNonZeros':
      return [len(self._spatialPoolerOutput)] + \
              list(self._spatialPoolerOutput.nonzero()[0])
    elif parameterName == 'spInputNonZeros':
      import pdb; pdb.set_trace()
      return [len(self._spatialPoolerInput)] + \
              list(self._spatialPoolerInput.nonzero()[0])
    elif parameterName == 'spLearningStatsStr':
      try:
        return str(self._sfdr.getLearningStats())
      except:
        return str(dict())
    elif parameterName == 'tpOutputNonZeros':
      return [len(self._rfOutput)] + \
              list(self._rfOutput.nonzero()[0])
    elif parameterName == 'tpSeqOutputNonZeros':
      return [len(self._tpSeqOutput)] + \
              list(self._tpSeqOutput.nonzero()[0])
    elif parameterName == 'tpNumSynapses':
      return self._tfdr.getNumSynapses() \
                if not self.disableTemporal else 0
    elif parameterName == 'tpNumStrongSynapses':
      return self._tfdr.getNumStrongSynapses() \
                if not self.disableTemporal else 0
    elif parameterName == 'tpNumStrongSynapsesPerTimeSlot':
      return self._tfdr.getNumStrongSynapsesPerTimeSlot() \
                if not self.disableTemporal else 0
    elif parameterName == 'tpNumSynapsesPerSegmentMax':
      return int(self._tfdr.getNumSynapsesPerSegmentMax()) \
                if not self.disableTemporal else 0
    elif parameterName == 'tpNumSynapsesPerSegmentAvg':
      return self._tfdr.getNumSynapsesPerSegmentAvg() \
                if not self.disableTemporal else 0
    elif parameterName == 'tpNumSegments':
      return self._tfdr.getNumSegments() if not self.disableTemporal else 0
    elif parameterName == 'tpNumCells':
      return self._tfdr.getNumCells() if not self.disableTemporal else 0
    elif parameterName == 'tpNumActiveCells':
      return int((self._rfOutput).sum()) if not self.disableTemporal else 0
    elif parameterName == 'tpNumActiveColumns':
      return int((self._tfdr.activeColumns(self._rfOutput) > 0).sum()) \
                if not self.disableTemporal else 0
    elif parameterName == 'tpNumBurstingColumns':
      return int((self._tfdr.burstingColumns(self._tpSeqOutput) > 0).sum()) \
                if not self.disableTemporal else 0
    #elif parameterName == 'coincidenceVectorCounts':
    #  if self.disableTemporal:
    #    return []
    #  else:
    #    return list(self.coincidenceVectorCounts)
    else:
      return PyRegion.getParameter(self, parameterName, index)


  #############################################################################
  def setParameter(self, parameterName, index, parameterValue):
    """
      Set the value of a Spec parameter. Most parameters are handled
      automatically by PyRegion's parameter set mechanism. The ones that need
      special treatment are explicitly handled here.
    """
    if parameterName in self._spatialArgNames:
      setattr(self._sfdr, parameterName, parameterValue)

    if parameterName in self._temporalArgNames:
      setattr(self._tfdr, parameterName, parameterValue)

    elif parameterName == 'inferenceMode':
      # If switching into inference mode, send one last reset into all our child
      # nodes to finish up learning
      if not self.inferenceMode and parameterValue:
        self._doLearn(rfInput=None, resetSignal=True, outputs=None)
      self.inferenceMode = parameterValue

    elif parameterName == "logPathSPInput":
      self.logPathSPInput = parameterValue
      # Close any existing log file
      if self._fpLogSPInput:
        self._fpLogSPInput.close()
        self._fpLogSPInput = None
      # Open a new log file
      if parameterValue:
        if self.disableSpatial:
          raise RuntimeError ("Spatial pooler is disabled for this level, "
            "can not turn on logging of SP inputs.")
        self._fpLogSPInput = open(self.logPathSPInput, 'w')

    elif parameterName == "logPathSP":
      self.logPathSP = parameterValue
      # Close any existing log file
      if self._fpLogSP:
        self._fpLogSP.close()
        self._fpLogSP = None
      # Open a new log file
      if parameterValue:
        if self.disableSpatial:
          raise RuntimeError ("Spatial pooler is disabled for this level, "
            "can not turn on logging of SP outputs.")
        self._fpLogSP = open(self.logPathSP, 'w')

    elif parameterName == "logPathTP":
      self.logPathTP = parameterValue
      # Close any existing log file
      if self._fpLogTP:
        self._fpLogTP.close()
        self._fpLogTP = None
      # Open a new log file
      if parameterValue and not self.disableTemporal:
        self._fpLogTP = open(self.logPathTP, 'w')

    elif parameterName == "logPathSPDense":
      self.logPathSPDense = parameterValue
      # Close any existing log file
      if self._fpLogSPDense:
        self._fpLogSPDense.close()
        self._fpLogSPDense = None
      # Open a new log file
      if parameterValue:
        self._fpLogSPDense = open(self.logPathSPDense, 'w')

    elif parameterName == 'learningMode':
      self.learningMode = parameterValue

    elif parameterName == 'trainingStep':
      # If done training the SP, give it a chance to finishLearning
      if self.trainingStep == 'spatial' and parameterValue != 'spatial':
        self._doLearn(rfInput=None, resetSignal=True, outputs=None)
      self.trainingStep = parameterValue
    elif parameterName == 'nMultiStepPrediction':
      self.nMultiStepPrediction = parameterValue
      self._allocateMultiStepPredictionVariables()
    else:
      raise Exception('Unknown parameter: ' + parameterName)


  #############################################################################
  def getTfdrActiveSynapses(self, cellNums, input):
    """Given a specific input to the temporal pooler 'input', return the list of
    synapses for each 'cellNum' in 'cellNums' that caused cell 'cellNum' to
    fire.

    We'll return a dict keyed by cellNum whoses values are synapses.  The
    synapses are returned as a list of tuples (srcCell, strength), where
    srcCell is the source cell driving the synapses and strength is the
    permanence value of the synapse

    @param  cellNums  An iterable of cell numbers to get activity for.
    @param  input     Nonzero inputs.
    @return allSyns   Dict, keyed by cellNum.  Values are:
                        list of (srcCell, strength) tuples
    """
    # Put the input in a format that it's quicker to use...
    nzInput = input.nonzero()[0]
    if nzInput.dtype not in (numpy.dtype('uint32'), numpy.dtype('int32')):
      nzInput = nzInput.astype('int32')
    nzInputSet = frozenset(nzInput)

    # Figure out which segments were active above threshold...
    # ...we don't care about 'best', so just pass a really big number...
    _, activeDsegs = self._tfdr.cells.dsegActivations(
      nzInput, 0x7FFFFFFF, self._tfdr.dsegThresholdInference
    )

    # For every cell that we care about, figure out the synapses in the
    # active segments that contributed...
    # ...note: this is a bit inefficient, but means that we don't need
    # to modify dsegActivations to also include the synapses that fired...
    allSyns = {}
    for cellIdx in cellNums:
      thisCellSyns = []
      if cellIdx in activeDsegs:
        for segmentIdx, _ in activeDsegs[cellIdx]:
          thisCellSyns.extend(
            (srcCellIdx, permanence)
            for (srcCellIdx, permanence)
            in self._tfdr.cells.synapsesInDseg((cellIdx, segmentIdx))
            if srcCellIdx in nzInputSet
          )

      allSyns[cellIdx] = thisCellSyns
    return allSyns


  #############################################################################
  def hasRunInference(self):
    """Simple accessor to tell if we've run inference yet.

    Used by CoincsTab.

    @return hasRunInference  True if we've run inference so far.
    """

    return self._hasRunInference


  #############################################################################
  #
  # Methods to support serialization
  #
  #############################################################################


  #############################################################################
  def __getstate__(self):
    """
    Return serializable state.  This function will return a version of the
    __dict__ with all "ephemeral" members stripped out.  "Ephemeral" members
    are defined as those that do not need to be (nor should be) stored
    in any kind of persistent file (e.g., NuPIC network XML file.)
    """
    state = self.__dict__.copy()
    # We only want to serialize a single spatial/temporal FDR if they're cloned
    for ephemeralMemberName in self._getEphemeralMembersAll():
      state.pop(ephemeralMemberName, None)
    return state

  def serializeExtraData(self, filePath):
    """This method is called during network serialization with an external
    filename that can be used to bypass pickle for saving large binary states.

    filePath: full filepath and name
    """
    if self._tfdr is not None:
      self._tfdr.saveToFile(filePath)

  def deSerializeExtraData(self, filePath):
    """This method is called during network deserialization with an external
    filename that can be used to bypass pickle for loading large binary states.

    filePath: full filepath and name
    """
    if self._tfdr is not None:
      self._tfdr.loadFromFile(filePath)


  #############################################################################
  def __setstate__(self, state):
    """
    Set the state of ourself from a serialized state.
    """
    # Support for legacy networks
    if 'statelessMode' not in state:
      state['statelessMode'] = False

    self.__dict__.update(state)
    self._loaded = True
    # Initialize all non-persistent base members, as well as give
    # derived class an opportunity to do the same.
    self._initialize()
    self._allocateSpatialFDR(None)

  #############################################################################
  def _initEphemerals(self):
    """
    Initialize all ephemerals used by derived classes.
    """

    self._sequencePos = 0
    self._temporalState = None
    self._predictedColumns = []
    if hasattr(self, '_sfdr') and self._sfdr:
      self._spatialPoolerOutput = numpy.zeros(self.coincidenceCount,
                                               dtype=GetNTAReal())
    else:
      self._spatialPoolerOutput = None  # Will be filled in initInNetwork

    # Direct logging support (faster than node watch)
    self._fpLogSPInput = None
    self._fpLogSP = None
    self._fpLogTP = None
    self._fpLogSPDense = None
    self.logPathSPInput = None
    self.logPathSP = None
    self.logPathTP = None
    self.logPathSPDense = None

  #############################################################################
  def _getEphemeralMembers(self):
    """
    Callback (to be overridden) allowing the class to publish a list of
    all "ephemeral" members (i.e., data members that should not and/or
    cannot be pickled.)
    """

    return ['_sequencePos', '_temporalState', '_spatialPoolerOutput',
            '_predictedColumns', '_fpLogSP', '_fpLogSPDense', '_fpLogTP', 'logPathSP',
            'logPathTP', 'logPathSPDense'
        ]

  #############################################################################

  def _getEphemeralMembersBase(self):
    """
    Returns list of all ephemeral members.
    """
    return [
        '_loaded',
        '_profileObj',
        '_iterations',
      ]

  def _getEphemeralMembersAll(self):
    """
    Returns a concatenated list of both the standard base class
    ephemeral members, as well as any additional ephemeral members
    (e.g., file handles, etc.).
    """
    return self._getEphemeralMembersBase() + self._getEphemeralMembers()

  #############################################################################

  def _checkEphemeralMembers(self):
    for attrName in self._getEphemeralMembersBase():
      if not hasattr(self, attrName):
        print "Missing base class member:", attrName
    for attrName in self._getEphemeralMembers():
      if not hasattr(self, attrName):
        print "Missing derived class member:", attrName

    for attrName in self._getEphemeralMembersBase():
      assert hasattr(self, attrName)
    for attrName in self._getEphemeralMembers():
      assert hasattr(self, attrName), "Node missing attr '%s'." % attrName

  #############################################################################
  #
  # Misc. code
  #
  #############################################################################

  #########################################################################################
  def _conditionalBreak(self):
    if self.breakKomodo:
      import dbgp.client; dbgp.client.brk()
    if self.breakPdb:
      import pdb; pdb.set_trace()

  #############################################################################
  #
  # NuPIC 2 Support
  #
  #############################################################################
  def getOutputElementCount(self, name):
    if self.nCellsPerCol <= 0:
      raise Exception("In NuPIC 2, nCellsPerCol must be specified at node creation time")
    if name == 'bottomUpOut':
      if self.disableTemporal:
        return self.coincidenceCount
      else:
        return self.nCellsPerCol * self.coincidenceCount
    elif name == 'topDownOut' or name == 'spReconstructedIn':
      if not self.computeTopDown:
        return 0
      else:
        if self.disableSpatial:
          return int(self.coincidencesShape[0] * self.coincidencesShape[1])
        else:
          return int(self.inputShape[0] * self.inputShape[1])
    else:
      raise Exception("Invalid output name specified")

  # TODO: as a temporary hack, getParameterArrayCount checks to see if there's a variable, private or
  # not, with that name. If so, it attempts to return the length of that variable.
  def getParameterArrayCount(self, name, index):
    p = self.getParameter(name)
    if (not hasattr(p, '__len__')):
      raise Exception("Attempt to access parameter '%s' as an array but it is not an array" % name)
    return len(p)

    #
    #if not hasattr(self, name):
    #  name = '_' + name
    #  if not hasattr(self, name):
    #    from dbgp.client import brk; brk(port=9011)
    #    raise Exception("Attempt to access parameter '%s' as an array but it is not an array" % name)
    #attr = getattr(self, name)
    #if (hasattr(attr, "__len__")):
    #  return len(attr)
    #else:
    #  raise Exception("Attempt to access parameter '%s' as an array but it is not an array" % name)

  # TODO: as a temporary hack, getParameterArray checks to see if there's a variable, private or not,
  # with that name. If so, it returns the value of the variable.
  def getParameterArray(self, name, index, a):
    #if not hasattr(self, name):
    #  name = '_' + name
    #  if not hasattr(self, name):
    #    raise Exception("Attempt to access array parameter '%s' - no such parameter exists" % name)
    #
    #attr = getattr(self, name)
    #
    #if not hasattr(attr, "__len__"):
    #  raise Exception("Attempt to access parameter '%s' as an array but it is not an array" % name)
    #
    #if len(attr) == 0:
    #  return

    p = self.getParameter(name)
    if (not hasattr(p, '__len__')):
      raise Exception("Attempt to access parameter '%s' as an array but it is not an array" % name)

    if len(p) >  0:
      a[:] = p[:]

###############################################################################
# Command line unit testing

###############################################################################
def _helptest():
  """Run a test of creating the node and calling nodeHelp()."""
  import os
  from nupic.network import CreateNode

  name = os.path.splitext(os.path.basename(__file__))[0]
  n = CreateNode('py.%s' % name)
  n.nodeHelp()

###############################################################################
def _doctest():
  """Run doctests."""
  import doctest
  doctest.testmod(verbose=True)


###############################################################################
def main(cmd='all', *args, **kwargs):
  """Main function.

  @param  cmd  The first argument passed on the command line.
  """
  didCmd = False

  if cmd in ('doctest', 'all'):
    print "========================= doctest ========================="
    _doctest(*args, **kwargs)
    didCmd = True

  if cmd in ('helptest', 'all'):
    print "========================= helptest ========================="
    _helptest(*args, **kwargs)
    didCmd = True

  if not didCmd:
    print "Unknown command: %s" % cmd

if __name__ == '__main__':
  main(*sys.argv[1:])
