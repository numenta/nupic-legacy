# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013-2016, Numenta, Inc.  Unless you have an agreement
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

import numpy
import os

try:
  import capnp
except ImportError:
  capnp = None

from nupic.bindings.regions.PyRegion import PyRegion

from nupic.algorithms import (anomaly, backtracking_tm, backtracking_tm_cpp,
                              backtracking_tm_shim)
if capnp:
  from nupic.regions.tm_region_capnp import TMRegionProto

from nupic.support import getArgumentDescriptions



gDefaultTemporalImp = 'py'



def _getTPClass(temporalImp):
  """ Return the class corresponding to the given temporalImp string
  """

  if temporalImp == 'py':
    return backtracking_tm.BacktrackingTM
  elif temporalImp == 'cpp':
    return backtracking_tm_cpp.BacktrackingTMCPP
  elif temporalImp == 'tm_py':
    return backtracking_tm_shim.TMShim
  elif temporalImp == 'tm_cpp':
    return backtracking_tm_shim.TMCPPShim
  elif temporalImp == 'monitored_tm_py':
    return backtracking_tm_shim.MonitoredTMShim
  else:
    raise RuntimeError("Invalid temporalImp '%s'. Legal values are: 'py', "
              "'cpp', 'tm_py', 'monitored_tm_py'" % (temporalImp))



def _buildArgs(f, self=None, kwargs={}):
  """
  Get the default arguments from the function and assign as instance vars.

  Return a list of 3-tuples with (name, description, defaultValue) for each
    argument to the function.

  Assigns all arguments to the function as instance variables of TMRegion.
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
  init = TMRegion.__init__
  ourArgNames = [t[0] for t in getArgumentDescriptions(init)]
  # Also remove a few other names that aren't in our constructor but are
  #  computed automatically (e.g. numberOfCols for the TM)
  ourArgNames += [
    'numberOfCols',    # TM
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


def _getAdditionalSpecs(temporalImp, kwargs={}):
  """Build the additional specs in three groups (for the inspector)

  Use the type of the default argument to set the Spec type, defaulting
  to 'Byte' for None and complex types

  Determines the spatial parameters based on the selected implementation.
  It defaults to TemporalMemory.
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

  # Build up parameters from temporal memory's constructor
  TemporalClass = _getTPClass(temporalImp)
  tArgTuples = _buildArgs(TemporalClass.__init__)
  temporalSpec = {}
  for argTuple in tArgTuples:
    d = dict(
      description=argTuple[1],
      accessMode='ReadWrite',
      dataType=getArgType(argTuple[2])[0],
      count=getArgType(argTuple[2])[1],
      constraints=getConstraints(argTuple[2]))
    temporalSpec[argTuple[0]] = d

  # Add temporal parameters that weren't handled automatically
  temporalSpec.update(dict(
    columnCount=dict(
      description='Total number of columns.',
      accessMode='Read',
      dataType='UInt32',
      count=1,
      constraints=''),

    cellsPerColumn=dict(
      description='Number of cells per column.',
      accessMode='Read',
      dataType='UInt32',
      count=1,
      constraints=''),

    inputWidth=dict(
      description='Number of inputs to the TM.',
      accessMode='Read',
      dataType='UInt32',
      count=1,
      constraints=''),

    predictedSegmentDecrement=dict(
      description='Predicted segment decrement',
      accessMode='Read',
      dataType='Real',
      count=1,
      constraints=''),

    orColumnOutputs=dict(
      description="""OR together the cell outputs from each column to produce
      the temporal memory output. When this mode is enabled, the number of
      cells per column must also be specified and the output size of the region
      should be set the same as columnCount""",
      accessMode='Read',
      dataType='Bool',
      count=1,
      constraints='bool'),

    cellsSavePath=dict(
      description="""Optional path to file in which large temporal memory cells
                     data structure is to be saved.""",
      accessMode='ReadWrite',
      dataType='Byte',
      count=0,
      constraints=''),

    temporalImp=dict(
      description="""Which temporal memory implementation to use. Set to either
       'py' or 'cpp'. The 'cpp' implementation is optimized for speed in C++.""",
      accessMode='ReadWrite',
      dataType='Byte',
      count=0,
      constraints='enum: py, cpp'),

  ))

  # The last group is for parameters that aren't strictly spatial or temporal
  otherSpec = dict(
    learningMode=dict(
      description='True if the node is learning (default True).',
      accessMode='ReadWrite',
      dataType='Bool',
      count=1,
      defaultValue=True,
      constraints='bool'),

    inferenceMode=dict(
      description='True if the node is inferring (default False).',
      accessMode='ReadWrite',
      dataType='Bool',
      count=1,
      defaultValue=False,
      constraints='bool'),

    computePredictedActiveCellIndices=dict(
      description='True if active and predicted active indices should be computed',
      accessMode='Create',
      dataType='Bool',
      count=1,
      defaultValue=False,
      constraints='bool'),

    anomalyMode=dict(
      description='True if an anomaly score is being computed',
      accessMode='Create',
      dataType='Bool',
      count=1,
      defaultValue=False,
      constraints='bool'),

    topDownMode=dict(
      description='True if the node should do top down compute on the next call '
                  'to compute into topDownOut (default False).',
      accessMode='ReadWrite',
      dataType='Bool',
      count=1,
      defaultValue=False,
      constraints='bool'),

    activeOutputCount=dict(
      description='Number of active elements in bottomUpOut output.',
      accessMode='Read',
      dataType='UInt32',
      count=1,
      constraints=''),

    storeDenseOutput=dict(
      description="""Whether to keep the dense column output (needed for
                     denseOutput parameter).""",
      accessMode='ReadWrite',
      dataType='UInt32',
      count=1,
      constraints='bool'),

    logPathOutput=dict(
      description='Optional name of output log file. If set, every output vector'
                  ' will be logged to this file as a sparse vector.',
      accessMode='ReadWrite',
      dataType='Byte',
      count=0,
      constraints=''),

  )

  return temporalSpec, otherSpec



class TMRegion(PyRegion):

  """
  TMRegion is designed to implement the temporal memory compute for a given
  HTM level.

  Uses a form of Temporal Memory to do most of the work. The specific TM 
  implementation is specified using the ``temporalImp`` parameter.
  """

  def __init__(self,

               columnCount,   # Number of columns in the SP, a required parameter
               inputWidth,    # Size of inputs to the SP, a required parameter
               cellsPerColumn, # Number of cells per column, required

               # Constructor arguments are picked up automatically. There is no
               # need to add them anywhere in TMRegion, unless you need to do
               # something special with them. See docstring above.

               orColumnOutputs=False,
               cellsSavePath='',
               temporalImp=gDefaultTemporalImp,
               anomalyMode=False,
               computePredictedActiveCellIndices=False,

               **kwargs):
    # Which Temporal implementation?
    TemporalClass = _getTPClass(temporalImp)

    # Make a list of automatic temporal arg names for later use
    # Pull out the temporal arguments automatically
    # These calls whittle down kwargs and create instance variables of TMRegion
    tArgTuples = _buildArgs(TemporalClass.__init__, self, kwargs)

    self._temporalArgNames = [t[0] for t in tArgTuples]

    self.learningMode   = True      # Start out with learning enabled
    self.inferenceMode  = False
    self.anomalyMode    = anomalyMode
    self.computePredictedActiveCellIndices = computePredictedActiveCellIndices
    self.topDownMode    = False
    self.columnCount    = columnCount
    self.inputWidth     = inputWidth
    self.outputWidth    = columnCount * cellsPerColumn
    self.cellsPerColumn = cellsPerColumn

    PyRegion.__init__(self, **kwargs)

    # Initialize all non-persistent base members, as well as give
    # derived class an opportunity to do the same.
    self._loaded = False
    self._initialize()

    # Debugging support, used in _conditionalBreak
    self.breakPdb = False
    self.breakKomodo = False

    # TMRegion only, or special handling
    self.orColumnOutputs = orColumnOutputs
    self.temporalImp = temporalImp

    # Various file names
    self.storeDenseOutput = False
    self.logPathOutput = ''
    self.cellsSavePath = cellsSavePath
    self._fpLogTPOutput = None

    # Variables set up in initInNetwork()
    self._tfdr = None  # FDRTemporal instance


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


  def initialize(self):
    """
    Overrides :meth:`~nupic.bindings.regions.PyRegion.initialize`.
    """
    # Allocate appropriate temporal memory object
    # Retrieve the necessary extra arguments that were handled automatically
    autoArgs = dict((name, getattr(self, name))
                    for name in self._temporalArgNames)

    if self._tfdr is None:
      tpClass = _getTPClass(self.temporalImp)

      if self.temporalImp in ['py', 'cpp', 'r',
                              'tm_py', 'tm_cpp',
                              'monitored_tm_py',]:
        self._tfdr = tpClass(
             numberOfCols=self.columnCount,
             cellsPerColumn=self.cellsPerColumn,
             **autoArgs)
      else:
        raise RuntimeError("Invalid temporalImp")


  #############################################################################
  #
  # Core compute methods: learning, inference, and prediction
  #
  #############################################################################


  #############################################################################
  def compute(self, inputs, outputs):
    """
    Run one iteration of :class:`~nupic.regions.tm_region.TMRegion` compute, 
    profiling it if requested.

    :param inputs: (dict) mapping region input names to numpy.array values
    :param outputs: (dict) mapping region output names to numpy.arrays that 
           should be populated with output values by this method
     """

    # Uncomment this to find out who is generating divide by 0, or other numpy warnings
    # numpy.seterr(divide='raise', invalid='raise', over='raise')

    # Modify this line to turn on profiling for a given node. The results file
    #  ('hotshot.stats') will be sensed and printed out by the vision framework's
    #  RunInference.py script at the end of inference.
    # Also uncomment the hotshot import at the top of this file.
    if False and self.learningMode \
        and self._iterations > 0 and self._iterations <= 10:

      import hotshot
      if self._iterations == 10:
        print "\n  Collecting and sorting internal node profiling stats generated by hotshot..."
        stats = hotshot.stats.load("hotshot.stats")
        stats.strip_dirs()
        stats.sort_stats('time', 'calls')
        stats.print_stats()

      # The guts of the compute are contained in the _compute() call so that
      # we can profile it if requested.
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
    Run one iteration of TMRegion's compute
    """

    #if self.topDownMode and (not 'topDownIn' in inputs):
    # raise RuntimeError("The input topDownIn must be linked in if "
    #                    "topDownMode is True")

    if self._tfdr is None:
      raise RuntimeError("TM has not been initialized")

    # Conditional compute break
    self._conditionalBreak()

    self._iterations += 1

    # Get our inputs as numpy array
    buInputVector = inputs['bottomUpIn']

    # Handle reset signal
    resetSignal = False
    if 'resetIn' in inputs:
      assert len(inputs['resetIn']) == 1
      if inputs['resetIn'][0] != 0:
        self._tfdr.reset()
        self._sequencePos = 0  # Position within the current sequence

    if self.computePredictedActiveCellIndices:
      prevPredictedState = self._tfdr.getPredictedState().reshape(-1).astype('float32')

    if self.anomalyMode:
      prevPredictedColumns = self._tfdr.topDownCompute().copy().nonzero()[0]

    # Perform inference and/or learning
    tpOutput = self._tfdr.compute(buInputVector, self.learningMode, self.inferenceMode)
    self._sequencePos += 1

    # OR'ing together the cells in each column?
    if self.orColumnOutputs:
      tpOutput= tpOutput.reshape(self.columnCount,
                                     self.cellsPerColumn).max(axis=1)

    # Direct logging of non-zero TM outputs
    if self._fpLogTPOutput:
      output = tpOutput.reshape(-1)
      outputNZ = tpOutput.nonzero()[0]
      outStr = " ".join(["%d" % int(token) for token in outputNZ])
      print >>self._fpLogTPOutput, output.size, outStr

    # Write the bottom up out to our node outputs
    outputs['bottomUpOut'][:] = tpOutput.flat

    if self.topDownMode:
      # Top-down compute
      outputs['topDownOut'][:] = self._tfdr.topDownCompute().copy()

    # Set output for use with anomaly classification region if in anomalyMode
    if self.anomalyMode:
      activeLearnCells = self._tfdr.getLearnActiveStateT()
      size = activeLearnCells.shape[0] * activeLearnCells.shape[1]
      outputs['lrnActiveStateT'][:] = activeLearnCells.reshape(size)

      activeColumns = buInputVector.nonzero()[0]
      outputs['anomalyScore'][:] = anomaly.computeRawAnomalyScore(
        activeColumns, prevPredictedColumns)

    if self.computePredictedActiveCellIndices:
      # Reshape so we are dealing with 1D arrays
      activeState = self._tfdr._getActiveState().reshape(-1).astype('float32')
      activeIndices = numpy.where(activeState != 0)[0]
      predictedIndices= numpy.where(prevPredictedState != 0)[0]
      predictedActiveIndices = numpy.intersect1d(activeIndices, predictedIndices)
      outputs["activeCells"].fill(0)
      outputs["activeCells"][activeIndices] = 1
      outputs["predictedActiveCells"].fill(0)
      outputs["predictedActiveCells"][predictedActiveIndices] = 1


  #############################################################################
  #
  # Region API support methods: getSpec, getParameter, and setParameter
  #
  #############################################################################

  #############################################################################
  @classmethod
  def getBaseSpec(cls):
    """
    Doesn't include the spatial, temporal and other parameters

    :returns: (dict) the base Spec for TMRegion.
    """
    spec = dict(
      description=TMRegion.__doc__,
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
        bottomUpOut=dict(
          description="""The output signal generated from the bottom-up inputs
                          from lower levels.""",
          dataType='Real32',
          count=0,
          regionLevel=True,
          isDefaultOutput=True),

        topDownOut=dict(
          description="""The top-down inputsignal, generated from
                        feedback from upper levels""",
          dataType='Real32',
          count=0,
          regionLevel=True,
          isDefaultOutput=False),

        activeCells=dict(
          description="The cells that are active",
          dataType='Real32',
          count=0,
          regionLevel=True,
          isDefaultOutput=False),

        predictedActiveCells=dict(
          description="The cells that are active and predicted",
          dataType='Real32',
          count=0,
          regionLevel=True,
          isDefaultOutput=False),

        anomalyScore = dict(
          description="""The score for how 'anomalous' (i.e. rare) the current
                        sequence is. Higher values are increasingly rare""",
          dataType='Real32',
          count=1,
          regionLevel=True,
          isDefaultOutput=False),

        lrnActiveStateT = dict(
          description="""Active cells during learn phase at time t.  This is
                        used for anomaly classification.""",
          dataType='Real32',
          count=0,
          regionLevel=True,
          isDefaultOutput=False),

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
    """
    Overrides :meth:`~nupic.bindings.regions.PyRegion.PyRegion.getSpec`.

    The parameters collection is constructed based on the parameters specified
    by the various components (spatialSpec, temporalSpec and otherSpec)
    """
    spec = cls.getBaseSpec()
    t, o = _getAdditionalSpecs(temporalImp=gDefaultTemporalImp)
    spec['parameters'].update(t)
    spec['parameters'].update(o)

    return spec


  def getAlgorithmInstance(self):
    """
    :returns: instance of the underlying 
              :class:`~nupic.algorithms.temporal_memory.TemporalMemory` 
              algorithm object.
    """
    return self._tfdr


  def getParameter(self, parameterName, index=-1):
    """
    Overrides :meth:`~nupic.bindings.regions.PyRegion.PyRegion.getParameter`.

    Get the value of a parameter. Most parameters are handled automatically by
    :class:`~nupic.bindings.regions.PyRegion.PyRegion`'s parameter get mechanism. The 
    ones that need special treatment are explicitly handled here.
    """
    if parameterName in self._temporalArgNames:
      return getattr(self._tfdr, parameterName)
    else:
      return PyRegion.getParameter(self, parameterName, index)


  def setParameter(self, parameterName, index, parameterValue):
    """
    Overrides :meth:`~nupic.bindings.regions.PyRegion.PyRegion.setParameter`.
    """
    if parameterName in self._temporalArgNames:
      setattr(self._tfdr, parameterName, parameterValue)

    elif parameterName == "logPathOutput":
      self.logPathOutput = parameterValue
      # Close any existing log file
      if self._fpLogTPOutput is not None:
        self._fpLogTPOutput.close()
        self._fpLogTPOutput = None

      # Open a new log file if requested
      if parameterValue:
        self._fpLogTPOutput = open(self.logPathOutput, 'w')

    elif hasattr(self, parameterName):
      setattr(self, parameterName, parameterValue)

    else:
      raise Exception('Unknown parameter: ' + parameterName)


  #############################################################################
  #
  # Commands
  #
  #############################################################################

  def resetSequenceStates(self):
    """ 
    Resets the region's sequence states.
    """
    self._tfdr.reset()
    self._sequencePos = 0  # Position within the current sequence
    return

  def finishLearning(self):
    """
    Perform an internal optimization step that speeds up inference if we know
    learning will not be performed anymore. This call may, for example, remove
    all potential inputs to each column.
    """
    if self._tfdr is None:
      raise RuntimeError("Temporal memory has not been initialized")

    if hasattr(self._tfdr, 'finishLearning'):
      self.resetSequenceStates()
      self._tfdr.finishLearning()

  #############################################################################
  #
  # Methods to support serialization
  #
  #############################################################################


  @staticmethod
  def getSchema():
    """
    Overrides :meth:`~nupic.bindings.regions.PyRegion.PyRegion.getSchema`.
    """
    return TMRegionProto


  def writeToProto(self, proto):
    """
    Overrides :meth:`~nupic.bindings.regions.PyRegion.PyRegion.writeToProto`.

    Write state to proto object.

    :param proto: TMRegionProto capnproto object
    """
    proto.temporalImp = self.temporalImp
    proto.columnCount = self.columnCount
    proto.inputWidth = self.inputWidth
    proto.cellsPerColumn = self.cellsPerColumn
    proto.learningMode = self.learningMode
    proto.inferenceMode = self.inferenceMode
    proto.anomalyMode = self.anomalyMode
    proto.topDownMode = self.topDownMode
    proto.computePredictedActiveCellIndices = (
      self.computePredictedActiveCellIndices)
    proto.orColumnOutputs = self.orColumnOutputs

    if self.temporalImp == "py":
      tmProto = proto.init("backtrackingTM")
    elif self.temporalImp == "cpp":
      tmProto = proto.init("backtrackingTMCpp")
    elif self.temporalImp == "tm_py":
      tmProto = proto.init("temporalMemory")
    elif self.temporalImp == "tm_cpp":
      tmProto = proto.init("temporalMemory")
    else:
      raise TypeError(
          "Unsupported temporalImp for capnp serialization: {}".format(
              self.temporalImp))

    self._tfdr.write(tmProto)


  @classmethod
  def readFromProto(cls, proto):
    """
    Overrides :meth:`~nupic.bindings.regions.PyRegion.PyRegion.readFromProto`.

    Read state from proto object.

    :param proto: TMRegionProto capnproto object
    """
    instance = cls(proto.columnCount, proto.inputWidth, proto.cellsPerColumn)

    instance.temporalImp = proto.temporalImp
    instance.learningMode = proto.learningMode
    instance.inferenceMode = proto.inferenceMode
    instance.anomalyMode = proto.anomalyMode
    instance.topDownMode = proto.topDownMode
    instance.computePredictedActiveCellIndices = (
      proto.computePredictedActiveCellIndices)
    instance.orColumnOutputs = proto.orColumnOutputs

    if instance.temporalImp == "py":
      tmProto = proto.backtrackingTM
    elif instance.temporalImp == "cpp":
      tmProto = proto.backtrackingTMCpp
    elif instance.temporalImp == "tm_py":
      tmProto = proto.temporalMemory
    elif instance.temporalImp == "tm_cpp":
      tmProto = proto.temporalMemory
    else:
      raise TypeError(
          "Unsupported temporalImp for capnp serialization: {}".format(
              instance.temporalImp))

    instance._tfdr = _getTPClass(proto.temporalImp).read(tmProto)

    return instance


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
    """
    Overrides :meth:`~nupic.bindings.regions.PyRegion.PyRegion.serializeExtraData`.
    """
    if self._tfdr is not None:
      self._tfdr.saveToFile(filePath)

  def deSerializeExtraData(self, filePath):
    """
    Overrides :meth:`~nupic.bindings.regions.PyRegion.PyRegion.deSerializeExtraData`.

    This method is called during network deserialization with an external
    filename that can be used to bypass pickle for loading large binary states.

    :param filePath: (string) absolute file path
    """
    if self._tfdr is not None:
      self._tfdr.loadFromFile(filePath)


  def __setstate__(self, state):
    """
    Set the state of ourself from a serialized state.
    """

    if not hasattr(self, 'storeDenseOutput'):
      self.storeDenseOutput = False

    if not hasattr(self, 'computePredictedActiveCellIndices'):
      self.computePredictedActiveCellIndices = False

    self.__dict__.update(state)
    self._loaded = True
    # Initialize all non-persistent base members, as well as give
    # derived class an opportunity to do the same.
    self._initialize()


  def _initEphemerals(self):
    """
    Initialize all ephemerals used by derived classes.
    """

    self._sequencePos = 0
    self._fpLogTPOutput = None
    self.logPathOutput = None


  def _getEphemeralMembers(self):
    """
    Callback that returns a list of all "ephemeral" members (i.e., data members
    that should not and/or cannot be pickled.)
    """

    return ['_sequencePos', '_fpLogTPOutput', 'logPathOutput',]


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
    """
    Overrides :meth:`~nupic.bindings.regions.PyRegion.PyRegion.getOutputElementCount`.
    """
    if name == 'bottomUpOut':
      return self.outputWidth
    elif name == 'topDownOut':
      return self.columnCount
    elif name == 'lrnActiveStateT':
      return self.outputWidth
    elif name == "activeCells":
      return self.outputWidth
    elif name == "predictedActiveCells":
      return self.outputWidth
    else:
      raise Exception("Invalid output name specified")


  # TODO: as a temporary hack, getParameterArrayCount checks to see if there's a variable, private or
  # not, with that name. If so, it attempts to return the length of that variable.
  def getParameterArrayCount(self, name, index):
    """
    Overrides :meth:`~nupic.bindings.regions.PyRegion.PyRegion.getParameterArrayCount`.
    """
    p = self.getParameter(name)
    if (not hasattr(p, '__len__')):
      raise Exception("Attempt to access parameter '%s' as an array but it is not an array" % name)
    return len(p)


  # TODO: as a temporary hack, getParameterArray checks to see if there's a variable, private or not,
  # with that name. If so, it returns the value of the variable.
  def getParameterArray(self, name, index, a):
    """
    Overrides :meth:`~nupic.bindings.regions.PyRegion.PyRegion.getParameterArray`.
    """
    p = self.getParameter(name)
    if (not hasattr(p, '__len__')):
      raise Exception("Attempt to access parameter '%s' as an array but it is not an array" % name)

    if len(p) >  0:
      a[:] = p[:]
