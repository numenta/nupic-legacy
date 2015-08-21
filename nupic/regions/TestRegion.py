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

# This is a PyRegion-based python test regions for exploring/testing CLA Network
# mechanisms

from abc import ABCMeta, abstractmethod


from PyRegion import PyRegion

from nupic.data.dictutils import DictObj



class RegionIdentityPolicyBase(object):
  """ A base class that must be subclassed by users in order to define the
  TestRegion instance's specialization. See also setIdentityPolicyInstance().
  """
  __metaclass__ = ABCMeta

  @abstractmethod
  def initialize(self, testRegionObj):
    """ Called from the scope of the region's PyRegion.initialize() method.

    testRegionObj:  TestRegion instance with which this policy is
                    associated.
    """

  @abstractmethod
  def compute(self, inputs, outputs):
    """Perform the main computation

    This method is called in each iteration for each phase the node supports.

    Called from the scope of the region's PyRegion.compute() method.

    inputs: dict of numpy arrays (one per input)
    outputs: dict of numpy arrays (one per output)
    """

  @abstractmethod
  def getOutputElementCount(self, name):
    """Return the number of elements in the given output of the region

    Called from the scope of the region's PyRegion.getOutputElementCount() method.

    name: the name of the output
    """

  @abstractmethod
  def getName(self):
    """ Return the name of the region
    """



class TestRegion(PyRegion):

  """
  TestRegion is designed for testing and exploration of CLA Network
  mechanisms.  Each TestRegion instance takes on a specific role via
  the associated TestRegionRole policy (TBD).
  """

  def __init__(self,
               **kwargs):

    super(PyRegion, self).__init__(**kwargs)


    # Learning, inference, and other parameters.
    # By default we start out in stage learn with inference disabled

    # The specialization policy is what gives this region instance its identity.
    # Users set this via setIdentityPolicyInstance() before running the network
    self.identityPolicy = None

    # Debugging support, used in _conditionalBreak
    self.breakPdb = False
    self.breakKomodo = False

    # Construct ephemeral variables (those that aren't serialized)
    self.__constructEphemeralInstanceVars()

    # Variables set up in initialize()
    #self._sfdr                = None  # FDRCSpatial instance

    return


  def __constructEphemeralInstanceVars(self):
    """ Initialize ephemeral instance variables (those that aren't serialized)
    """
    assert not hasattr(self, 'ephemeral')

    self.ephemeral = DictObj()

    self.ephemeral.logPathInput = ''
    self.ephemeral.logPathOutput = ''
    self.ephemeral.logPathOutputDense = ''
    self.ephemeral._fpLogInput = None
    self.ephemeral._fpLogOutput = None
    self.ephemeral._fpLogOutputDense = None

    return



  #############################################################################
  #
  # Initialization code
  #
  #############################################################################


  def initialize(self, dims, splitterMaps):
    """ Called by network after all links have been set up

    dims, splitterMaps:   Unused legacy args
    """
    self.identityPolicy.initialize(self)

    _debugOut(self.identityPolicy.getName())
    return


  #############################################################################
  #
  # Core compute methods: learning, inference, and prediction
  #
  #############################################################################


  def compute(self, inputs, outputs):
    """
    Run one iteration of the region's compute.

    The guts of the compute are contained in the _compute() call so that
    we can profile it if requested.
    """

    # Uncomment this to find out who is generating divide by 0, or other numpy warnings
    # numpy.seterr(divide='raise', invalid='raise', over='raise')

    self.identityPolicy.compute(inputs, outputs)

    _debugOut(("%s: inputs=%s; outputs=%s") % \
                (self.identityPolicy.getName(),inputs, outputs))

    return


  #############################################################################
  #
  # NuPIC 2 Support
  #    These methods are required by NuPIC 2
  #
  #############################################################################


  def getOutputElementCount(self, name):
    nOutputElements = self.identityPolicy.getOutputElementCount(name)
    return nOutputElements


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

    return



  #############################################################################
  #
  # Region API support methods: getSpec, getParameter, and setParameter
  #
  #############################################################################


  @classmethod
  def getSpec(cls):
    """Return the base Spec for TestRegion.
    """
    spec = dict(
      description="TestRegion",
      singleNodeOnly=True,
      inputs=dict(
          bottomUpIn=dict(
            description="""The input vector.""",
            dataType='Real32',
            count=0,
            required=False,
            regionLevel=True,
            isDefaultInput=True,
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
      ),

      parameters=dict(

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
      commands=dict(
        setIdentityPolicyInstance=dict(description=
                "Set identity policy instance BERORE running the network. " + \
                "The instance MUST be derived from TestRegion's " + \
                "RegionIdentityPolicyBase class."),

        getIdentityPolicyInstance=dict(description=
                "Returns identity policy instance that was associated with " + \
                "the TestRegion instance via the setIdentityPolicyInstance " + \
                "command."),
      )
    )

    return spec


  def getParameter(self, parameterName, index=-1):
    """
      Get the value of a NodeSpec parameter. Most parameters are handled
      automatically by PyRegion's parameter get mechanism. The ones that need
      special treatment are explicitly handled here.
    """

    assert not (parameterName in self.__dict__ and parameterName in self.ephemeral)

    if parameterName in self.ephemeral:
      assert parameterName not in self.__dict__
      return self.ephemeral[parameterName]

    else:
      return super(PyRegion, self).getParameter(parameterName, index)


  def setParameter(self, parameterName, index, parameterValue):
    """
      Set the value of a Spec parameter. Most parameters are handled
      automatically by PyRegion's parameter set mechanism. The ones that need
      special treatment are explicitly handled here.
    """
    assert not (parameterName in self.__dict__ and parameterName in self.ephemeral)

    if parameterName in self.ephemeral:
      if parameterName == "logPathInput":
        self.ephemeral.logPathInput = parameterValue
        # Close any existing log file
        if self.ephemeral._fpLogInput:
          self.ephemeral._fpLogInput.close()
          self.ephemeral._fpLogInput = None
        # Open a new log file
        if parameterValue:
          self.ephemeral._fpLogInput = open(self.ephemeral.logPathInput, 'w')

      elif parameterName == "logPathOutput":
        self.ephemeral.logPathOutput = parameterValue
        # Close any existing log file
        if self.ephemeral._fpLogOutput:
          self.ephemeral._fpLogOutput.close()
          self.ephemeral._fpLogOutput = None
        # Open a new log file
        if parameterValue:
          self.ephemeral._fpLogOutput = open(self.ephemeral.logPathOutput, 'w')

      elif parameterName == "logPathOutputDense":
        self.ephemeral.logPathOutputDense = parameterValue
        # Close any existing log file
        if self.ephemeral._fpLogOutputDense:
          self.ephemeral._fpLogOutputDense.close()
          self.ephemeral._fpLogOutputDense = None
        # Open a new log file
        if parameterValue:
          self.ephemeral._fpLogOutputDense = open(self.ephemeral.logPathOutputDense, 'w')

    else:
      raise Exception('Unknown parameter: ' + parameterName)

    return


  #############################################################################
  #
  # Commands
  #
  #############################################################################


  def setIdentityPolicyInstance(self, identityPolicyObj):
    """TestRegion command that sets identity policy instance.  The instance
    MUST be derived from TestRegion's RegionIdentityPolicyBase class.

    Users MUST set the identity instance BEFORE running the network

    Exception: AssertionError if identity policy instance has already been set
               or if the passed-in instance is not derived from
               RegionIdentityPolicyBase.
    """
    assert not self.identityPolicy
    assert isinstance(identityPolicyObj, RegionIdentityPolicyBase)

    self.identityPolicy = identityPolicyObj

    return


  def getIdentityPolicyInstance(self):
    """TestRegion command that returns the identity policy instance that was
    associated with this TestRegion instance via setIdentityPolicyInstance().

    Returns: a RegionIdentityPolicyBase-based instance that was associated with
             this TestRegion intstance.

    Exception: AssertionError if no identity policy instance has been set.
    """
    assert self.identityPolicy

    return self.identityPolicy


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

    # Don't serialize ephemeral data
    state.pop('ephemeral')

    return state


  def __setstate__(self, state):
    """
    Set the state of ourself from a serialized state.
    """

    assert 'ephemeral' not in state

    self.__dict__.update(state)

    # Initialize our ephemeral member variables
    self.__constructEphemeralInstanceVars()

    return


  #############################################################################
  #
  # Debugging support code
  #
  #############################################################################


  def _conditionalBreak(self):
    if self.breakKomodo:
      import dbgp.client; dbgp.client.brk()
    if self.breakPdb:
      import pdb; pdb.set_trace()

    return



g_debug = True
def _debugOut(msg):
  import sys
  global g_debug
  if g_debug:
    callerTraceback = whois_callers_caller()
    print "TEST_REGION (f=%s;line=%s): %s" % \
                          (callerTraceback.function, callerTraceback.lineno, msg,)
    sys.stdout.flush()

  return



def whois_callers_caller():
  """
  Returns: Traceback namedtuple for our caller's caller
  """
  import inspect

  frameObj = inspect.stack()[2][0]

  return inspect.getframeinfo(frameObj)
