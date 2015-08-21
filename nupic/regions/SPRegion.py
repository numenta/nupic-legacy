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

import os

import numpy
from nupic.bindings.math import GetNTAReal
from nupic.bindings.algorithms import SpatialPooler as CPPSpatialPooler
from nupic.research.spatial_pooler import SpatialPooler as PYSpatialPooler
import nupic.research.fdrutilities as fdru
from nupic.support import getArgumentDescriptions
from PyRegion import PyRegion



def getDefaultSPImp():
  """
  Return the default spatial pooler implementation for this region.
  """
  return 'cpp'



def getSPClass(spatialImp):
  """ Return the class corresponding to the given spatialImp string
  """

  if spatialImp == 'py':
    return PYSpatialPooler
  elif spatialImp == 'cpp':
    return CPPSpatialPooler
  else:
    raise RuntimeError("Invalid spatialImp '%s'. Legal values are: 'py', "
          "'cpp'" % (spatialImp))



def _buildArgs(f, self=None, kwargs={}):
  """
  Get the default arguments from the function and assign as instance vars.

  Return a list of 3-tuples with (name, description, defaultValue) for each
    argument to the function.

  Assigns all arguments to the function as instance variables of SPRegion.
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
  init = SPRegion.__init__
  ourArgNames = [t[0] for t in getArgumentDescriptions(init)]
  # Also remove a few other names that aren't in our constructor but are
  #  computed automatically (e.g. numberOfCols for the TP)
  # TODO: where does numberOfCols come into SPRegion?
  ourArgNames += [
    'numberOfCols',
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
          raise TypeError("Must provide value for '%s'" % argName)
        argValue = argTuple[2]
      # Set as an instance variable if 'self' was passed in
      setattr(self, argName, argValue)

  return argTuples


def _getAdditionalSpecs(spatialImp, kwargs={}):
  """Build the additional specs in three groups (for the inspector)

  Use the type of the default argument to set the Spec type, defaulting
  to 'Byte' for None and complex types

  Determines the spatial parameters based on the selected implementation.
  It defaults to SpatialPooler.
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

  # Get arguments from spatial pooler constructors, figure out types of
  # variables and populate spatialSpec.
  SpatialClass = getSPClass(spatialImp)
  sArgTuples = _buildArgs(SpatialClass.__init__)
  spatialSpec = {}
  for argTuple in sArgTuples:
    d = dict(
      description=argTuple[1],
      accessMode='ReadWrite',
      dataType=getArgType(argTuple[2])[0],
      count=getArgType(argTuple[2])[1],
      constraints=getConstraints(argTuple[2]))
    spatialSpec[argTuple[0]] = d

  # Add special parameters that weren't handled automatically
  # Spatial parameters only!
  spatialSpec.update(dict(

    columnCount=dict(
      description='Total number of columns (coincidences).',
      accessMode='Read',
      dataType='UInt32',
      count=1,
      constraints=''),

    inputWidth=dict(
      description='Size of inputs to the SP.',
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

    denseOutput=dict(
      description='Score for each coincidence.',
      accessMode='Read',
      dataType='Real32',
      count=0,
      constraints=''),

    spLearningStatsStr=dict(
      description="""String representation of dictionary containing a number
                     of statistics related to learning.""",
      accessMode='Read',
      dataType='Byte',
      count=0,
      constraints='handle'),

    spatialImp=dict(
        description="""Which spatial pooler implementation to use. Set to either
                      'py', or 'cpp'. The 'cpp' implementation is optimized for 
                      speed in C++.""",
        accessMode='ReadWrite',
        dataType='Byte',
        count=0,
        constraints='enum: py, cpp'),
  ))


  # The last group is for parameters that aren't specific to spatial pooler
  otherSpec = dict(
    learningMode=dict(
      description='1 if the node is learning (default 1).',
      accessMode='ReadWrite',
      dataType='UInt32',
      count=1,
      constraints='bool'),

    inferenceMode=dict(
      description='1 if the node is inferring (default 0).',
      accessMode='ReadWrite',
      dataType='UInt32',
      count=1,
      constraints='bool'),

    anomalyMode=dict(
      description='1 if an anomaly score is being computed',
      accessMode='ReadWrite',
      dataType='UInt32',
      count=1,
      constraints='bool'),

    topDownMode=dict(
      description='1 if the node should do top down compute on the next call '
                  'to compute into topDownOut (default 0).',
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

    logPathInput=dict(
      description='Optional name of input log file. If set, every input vector'
                  ' will be logged to this file.',
      accessMode='ReadWrite',
      dataType='Byte',
      count=0,
      constraints=''),

    logPathOutput=dict(
      description='Optional name of output log file. If set, every output vector'
                  ' will be logged to this file.',
      accessMode='ReadWrite',
      dataType='Byte',
      count=0,
      constraints=''),

    logPathOutputDense=dict(
      description='Optional name of output log file. If set, every output vector'
                  ' will be logged to this file as a dense vector.',
      accessMode='ReadWrite',
      dataType='Byte',
      count=0,
      constraints=''),

  )

  return spatialSpec, otherSpec



class SPRegion(PyRegion):

  """
  SPRegion is designed to implement the spatial pooler compute for a given
  HTM level.

  Uses the SpatialPooler class to do most of the work. This node has just one
  SpatialPooler instance for the enitire level and does *not* support the concept
  of "baby nodes" within it.

  Automatic parameter handling:

  Parameter names, default values, and descriptions are retrieved automatically
  from SpatialPooler. Thus, there are only a few hardcoded arguments in __init__,
  and the rest are passed to the appropriate underlying class. The NodeSpec is
  mostly built automatically from these parameters, too.

  If you add a parameter to SpatialPooler, it will be exposed through SPRegion
  automatically as if it were in SPRegion.__init__, with the right default
  value. Add an entry in the __init__ docstring for it too, and that will be
  brought into the NodeSpec. SPRegion will maintain the parameter as its own
  instance variable and also pass it to SpatialPooler. If the parameter is
  changed, SPRegion will propagate the change.

  If you want to do something different with the parameter, add it as an
  argument into SPRegion.__init__, which will override all the default handling.
  """

  def __init__(self,
               columnCount,   # Number of columns in the SP, a required parameter
               inputWidth,    # Size of inputs to the SP, a required parameter
               spatialImp=getDefaultSPImp(),   #'py', 'cpp'
               **kwargs):

    if columnCount <= 0 or inputWidth <=0:
      raise TypeError("Parameters columnCount and inputWidth must be > 0")

    # Pull out the spatial arguments automatically
    # These calls whittle down kwargs and create instance variables of SPRegion
    self.SpatialClass = getSPClass(spatialImp)
    sArgTuples = _buildArgs(self.SpatialClass.__init__, self, kwargs)

    # Make a list of automatic spatial arg names for later use
    self._spatialArgNames = [t[0] for t in sArgTuples]

    # Learning and SP parameters.
    # By default we start out in stage learn with inference disabled
    self.learningMode   = True
    self.inferenceMode  = False
    self.anomalyMode    = False
    self.topDownMode    = False
    self.columnCount    = columnCount
    self.inputWidth     = inputWidth

    PyRegion.__init__(self, **kwargs)

    # Initialize all non-persistent base members, as well as give
    # derived class an opportunity to do the same.
    self._loaded = False
    self._initializeEphemeralMembers()

    # Debugging support, used in _conditionalBreak
    self.breakPdb = False
    self.breakKomodo = False

    # Defaults for all other parameters
    self.logPathInput = ''
    self.logPathOutput = ''
    self.logPathOutputDense = ''
    self._fpLogSPInput = None
    self._fpLogSP = None
    self._fpLogSPDense = None


    #
    # Variables set up in initInNetwork()
    #

    # Spatial instance
    self._sfdr                = None

    # Spatial pooler's bottom-up output value: hang on to this  output for
    # top-down inference and for debugging
    self._spatialPoolerOutput = None

    # Spatial pooler's bottom-up input: hang on to this for supporting the
    # spInputNonZeros parameter
    self._spatialPoolerInput  = None


  #############################################################################
  #
  # Initialization code
  #
  #############################################################################

  def _initializeEphemeralMembers(self):
    """
    Initialize all ephemeral data members, and give the derived class the
    opportunity to do the same by invoking the virtual member _initEphemerals(),
    which is intended to be overridden.

    NOTE: this is used by both __init__ and __setstate__ code paths.
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


  def initialize(self, dims, splitterMaps):
    """"""

    # Zero out the spatial output in case it is requested
    self._spatialPoolerOutput = numpy.zeros(self.columnCount,
                                            dtype=GetNTAReal())


    # Zero out the rfInput in case it is requested
    self._spatialPoolerInput = numpy.zeros((1,self.inputWidth), dtype=GetNTAReal())

    # Allocate the spatial pooler
    self._allocateSpatialFDR(None)


  def _allocateSpatialFDR(self, rfInput):
    """Allocate the spatial pooler instance."""
    if self._sfdr:
      return

    # Retrieve the necessary extra arguments that were handled automatically
    autoArgs = dict((name, getattr(self, name))
                     for name in self._spatialArgNames)
    
    # Instantiate the spatial pooler class.
    if ( (self.SpatialClass == CPPSpatialPooler) or
         (self.SpatialClass == PYSpatialPooler) ):
      
      autoArgs['columnDimensions'] = [self.columnCount]
      autoArgs['inputDimensions'] = [self.inputWidth]
      autoArgs['potentialRadius'] = self.inputWidth
    
      self._sfdr = self.SpatialClass(
        **autoArgs
      )
  

  #############################################################################
  #
  # Core compute methods: learning, inference, and prediction
  #
  #############################################################################


  def compute(self, inputs, outputs):
    """
    Run one iteration of SPRegion's compute, profiling it if requested.

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
        and self._iterations > 0 and self._iterations <= 10:

      import hotshot
      if self._iterations == 10:
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
    Run one iteration of SPRegion's compute
    """

    #if self.topDownMode and (not 'topDownIn' in inputs):
    #  raise RuntimeError("The input topDownIn must be linked in if "
    #                     "topDownMode is True")

    if self._sfdr is None:
      raise RuntimeError("Spatial pooler has not been initialized")


    if not self.topDownMode:
      #
      # BOTTOM-UP compute
      #

      self._iterations += 1

      # Get our inputs into numpy arrays
      buInputVector = inputs['bottomUpIn']

      resetSignal = False
      if 'resetIn' in inputs:
        assert len(inputs['resetIn']) == 1
        resetSignal = inputs['resetIn'][0] != 0

      # Perform inference and/or learning
      rfOutput = self._doBottomUpCompute(
        rfInput = buInputVector.reshape((1,buInputVector.size)),
        resetSignal = resetSignal
        )

      outputs['bottomUpOut'][:] = rfOutput.flat

    else:
      #
      # TOP-DOWN inference
      #

      topDownIn = inputs.get('topDownIn',None)
      spatialTopDownOut, temporalTopDownOut = self._doTopDownInfer(topDownIn)
      outputs['spatialTopDownOut'][:] = spatialTopDownOut
      if temporalTopDownOut is not None:
        outputs['temporalTopDownOut'][:] = temporalTopDownOut


    # OBSOLETE
    outputs['anomalyScore'][:] = 0

      # Write the bottom up out to our node outputs only if we are doing inference
      #print "SPRegion input: ", buInputVector.nonzero()[0]
      #print "SPRegion output: ", rfOutput.nonzero()[0]


  def _doBottomUpCompute(self, rfInput, resetSignal):
    """
    Do one iteration of inference and/or learning and return the result

    Parameters:
    --------------------------------------------
    rfInput:      Input vector. Shape is: (1, inputVectorLen).
    resetSignal:  True if reset is asserted

    """

    # Conditional compute break
    self._conditionalBreak()

    # Save the rfInput for the spInputNonZeros parameter
    self._spatialPoolerInput = rfInput.reshape(-1)
    assert(rfInput.shape[0] == 1)

    # Run inference using the spatial pooler. We learn on the coincidences only
    # if we are in learning mode and trainingStep is set appropriately.

    # Run SFDR bottom-up compute and cache output in self._spatialPoolerOutput
    
    inputVector = numpy.array(rfInput[0]).astype('uint32')
    outputVector = numpy.zeros(self._sfdr.getNumColumns()).astype('uint32')

    self._sfdr.compute(inputVector, self.learningMode, outputVector)

    self._spatialPoolerOutput[:] = outputVector[:]

    # Direct logging of SP outputs if requested
    if self._fpLogSP:
      output = self._spatialPoolerOutput.reshape(-1)
      outputNZ = output.nonzero()[0]
      outStr = " ".join(["%d" % int(token) for token in outputNZ])
      print >>self._fpLogSP, output.size, outStr

    # Direct logging of SP inputs
    if self._fpLogSPInput:
      output = rfInput.reshape(-1)
      outputNZ = output.nonzero()[0]
      outStr = " ".join(["%d" % int(token) for token in outputNZ])
      print >>self._fpLogSPInput, output.size, outStr

    return self._spatialPoolerOutput


  def _doTopDownInfer(self, topDownInput = None):
    """
    Do one iteration of top-down inference.

    Parameters:
    --------------------------------------------
    tdInput:      Top-down input

    retval:     (spatialTopDownOut, temporalTopDownOut)
                  spatialTopDownOut is the top down output computed only from the SP,
                    using it's current bottom-up output.
                  temporalTopDownOut is the top down output computed from the topDown in
                   of the level above us.

    """

    return None, None

  #############################################################################
  #
  # Region API support methods: getSpec, getParameter, and setParameter
  #
  #############################################################################

  @classmethod
  def getBaseSpec(cls):
    """Return the base Spec for SPRegion.

    Doesn't include the spatial, temporal and other parameters
    """
    spec = dict(
      description=SPRegion.__doc__,
      singleNodeOnly=True,
      inputs=dict(
          bottomUpIn=dict(
          description="""The input vector.""",
          dataType='Real32',
          count=0,
          required=True,
          regionLevel=False,
          isDefaultInput=True,
          requireSplitterMap=False),

          resetIn=dict(
          description="""A boolean flag that indicates whether
                         or not the input vector received in this compute cycle
                         represents the start of a new temporal sequence.""",
          dataType='Real32',
          count=1,
          required=False,
          regionLevel=True,
          isDefaultInput=False,
          requireSplitterMap=False),

          topDownIn=dict(
          description="""The top-down input signal, generated from
                        feedback from upper levels""",
          dataType='Real32',
          count=0,
          required = False,
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
          isDefaultOutput=False),

        spatialTopDownOut = dict(
          description="""The top-down output, generated only from the current
                         SP output. This can be used to evaluate how well the
                         SP is representing the inputs independent of the TP.""",
          dataType='Real32',
          count=0,
          regionLevel=True,
          isDefaultOutput=False),

        temporalTopDownOut = dict(
          description="""The top-down output, generated only from the current
                         TP output feedback down through the SP.""",
          dataType='Real32',
          count=0,
          regionLevel=True,
          isDefaultOutput=False),

        anomalyScore = dict(
          description="""The score for how 'anomalous' (i.e. rare) this spatial
                        input pattern is. Higher values are increasingly rare""",
          dataType='Real32',
          count=1,
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
    )

    return spec

  @classmethod
  def getSpec(cls):
    """Return the Spec for SPRegion.

    The parameters collection is constructed based on the parameters specified
    by the variosu components (spatialSpec, temporalSpec and otherSpec)
    """
    spec = cls.getBaseSpec()
    s, o = _getAdditionalSpecs(spatialImp=getDefaultSPImp())
    spec['parameters'].update(s)
    spec['parameters'].update(o)

    return spec


  def getParameter(self, parameterName, index=-1):
    """
      Get the value of a NodeSpec parameter. Most parameters are handled
      automatically by PyRegion's parameter get mechanism. The ones that need
      special treatment are explicitly handled here.
    """

    if parameterName == 'activeOutputCount':
      return self.columnCount
    elif parameterName == 'spatialPoolerInput':
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
    else:
      return PyRegion.getParameter(self, parameterName, index)


  def setParameter(self, parameterName, index, parameterValue):
    """
      Set the value of a Spec parameter. Most parameters are handled
      automatically by PyRegion's parameter set mechanism. The ones that need
      special treatment are explicitly handled here.
    """
    if parameterName in self._spatialArgNames:
      setattr(self._sfdr, parameterName, parameterValue)

    elif parameterName == "logPathInput":
      self.logPathInput = parameterValue
      # Close any existing log file
      if self._fpLogSPInput:
        self._fpLogSPInput.close()
        self._fpLogSPInput = None
      # Open a new log file
      if parameterValue:
        self._fpLogSPInput = open(self.logPathInput, 'w')

    elif parameterName == "logPathOutput":
      self.logPathOutput = parameterValue
      # Close any existing log file
      if self._fpLogSP:
        self._fpLogSP.close()
        self._fpLogSP = None
      # Open a new log file
      if parameterValue:
        self._fpLogSP = open(self.logPathOutput, 'w')

    elif parameterName == "logPathOutputDense":
      self.logPathOutputDense = parameterValue
      # Close any existing log file
      if self._fpLogSPDense:
        self._fpLogSPDense.close()
        self._fpLogSPDense = None
      # Open a new log file
      if parameterValue:
        self._fpLogSPDense = open(self.logPathOutputDense, 'w')

    elif hasattr(self, parameterName):
      setattr(self, parameterName, parameterValue)

    else:
      raise Exception('Unknown parameter: ' + parameterName)

  #############################################################################
  #
  # Methods to support serialization
  #
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


  def __setstate__(self, state):
    """
    Set the state of ourself from a serialized state.
    """

    self.__dict__.update(state)
    self._loaded = True
    # Backwards compatibility
    if not hasattr(self, "SpatialClass"):
      self.SpatialClass = self._sfdr.__class__
    # Initialize all non-persistent base members, as well as give
    # derived class an opportunity to do the same.
    self._initializeEphemeralMembers()
    self._allocateSpatialFDR(None)


  def _initEphemerals(self):
    """
    Initialize all ephemerals used by derived classes.
    """

    if hasattr(self, '_sfdr') and self._sfdr:
      self._spatialPoolerOutput = numpy.zeros(self.columnCount,
                                               dtype=GetNTAReal())
    else:
      self._spatialPoolerOutput = None  # Will be filled in initInNetwork

    # Direct logging support (faster than node watch)
    self._fpLogSPInput = None
    self._fpLogSP = None
    self._fpLogSPDense = None
    self.logPathInput = ""
    self.logPathOutput = ""
    self.logPathOutputDense = ""


  def _getEphemeralMembers(self):
    """
    Callback that returns a list of all "ephemeral" members (i.e., data members
    that should not and/or cannot be pickled.)
    """

    return ['_spatialPoolerOutput', '_fpLogSP', '_fpLogSPDense',
            'logPathInput', 'logPathOutput', 'logPathOutputDense'
        ]


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
  #    These methods are required by NuPIC 2
  #
  #############################################################################

  def getOutputElementCount(self, name):
    if name == 'bottomUpOut':
      return self.columnCount
    elif name == 'spatialTopDownOut' or name == 'temporalTopDownOut' or \
               name == 'topDownOut':
      return self.inputWidth
    else:
      raise Exception("Invalid output name specified")

  # TODO: as a temporary hack, getParameterArrayCount checks to see if there's a
  # variable, private or not, with that name. If so, it attempts to return the
  # length of that variable.
  def getParameterArrayCount(self, name, index):
    p = self.getParameter(name)
    if (not hasattr(p, '__len__')):
      raise Exception("Attempt to access parameter '%s' as an array but it is not an array" % name)
    return len(p)


  # TODO: as a temporary hack, getParameterArray checks to see if there's a
  # variable, private or not, with that name. If so, it returns the value of the
  # variable.
  def getParameterArray(self, name, index, a):

    p = self.getParameter(name)
    if (not hasattr(p, '__len__')):
      raise Exception("Attempt to access parameter '%s' as an array but it is not an array" % name)

    if len(p) >  0:
      a[:] = p[:]
