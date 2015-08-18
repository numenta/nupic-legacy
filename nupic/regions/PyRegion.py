# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013-2014, Numenta, Inc.  Unless you have an agreement
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
This file defines the base class for NuPIC 2 Python regions.
"""
import numpy

RealNumpyDType = numpy.float32
from abc import ABCMeta, abstractmethod
from nupic.support import getCallerInfo

def not_implemented(f):
  """A decorator that raises NotImplementedError exception when called

  Keeps the docstring of the original function.
  """
  def decorated(*args, **kw):
    gci = getCallerInfo()
    caller = gci[0] + '()'
    if gci[2]:
      caller = gci[2] + '.' + caller

    message = 'The unimplemented method '
    message += '%s() was called by %s' % (f.func_name, caller)
    raise NotImplementedError(message)
  decorated.__doc__ == f.__doc__
  return decorated



class PyRegion(object):
  """
  PyRegion provides services to its sub-classes (the actual regions):

  - Define and document the interface of a Python region
  - Enforce implementation of required methods
  - Default implementation for some methods

  PyRegion is an abstract base class (http://docs.python.org/library/abc.html).
  If a subclass doesn't implement all its abstract methods it can't be
  instantiated. Note, that the signature of implemented abstract method in the
  subclass doesn't need to match the signature of the abstract method in the
  base class. This is very important for __init__() in this case.

  The abstract methods (decorated with @abstract method) are:

  * __init__
  * initialize
  * compute

  In addition, PyRegion decorates some other methods with the
  @not_implemented decorator. A sub-class may opt not to implement these
  methods, but if such a methods is called then a NotImplementedError will be
  raised. This is useful for methods like setParameterArray if a particular
  subclass has no array parameters.

  The not implemented methods (decorated with @not_implemented) are:

  * getSpec (class method)
  * setParameter
  * setParameterArray
  * getOutputElementCount

  The getSpec is a class method, which is actually required but since it's
  not an instance method the @abstractmethod decorator doesn't apply.

  Finally, PyRegion provides reasonable default implementation to some methods.
  Sub-classes may opt to override these methods or use the default
  implementation (often recommended).

  The implemented methods are:

  * getParameter
  * getParameterArray
  * getParameterArrayCount
  * executeMethod

  """
  __metaclass__ = ABCMeta


  @classmethod
  @not_implemented
  def getSpec(cls):
    """Returns the region spec for this region. The Region Spec is a dictionary
    with the following keys:
    description -- a string

    singleNodeOnly -- a boolean (True if this Region supports only a single node)

    inputs -- a dictionary in which the keys are the names of the inputs and
    the values are dictionaries with these keys:
         description - string
         regionLevel -- True if this is a "region-level" input.
         dataType - a string describing the data type, usually 'Real32'
         count - the number of items in the input. 0 means unspecified.
         required -- boolean - whether the input is must be connected
         isDefaultInput -- must be True for exactly one input
         requireSplitterMap -- [just set this to False.]

    outputs -- a dictionary with similar structure to inputs. The keys
    are:
         description
         dataType
         count
         regionLevel
         isDefaultOutput

    parameters -- a dictionary of dictionaries with the following keys:
         description
         dataType
         count
         constraints (optional)
         accessMode (one of "ReadWrite", "Read", "Create")

    This class method is called by NuPIC before creating a Region.
    """

  @abstractmethod
  def __init__(self, *args, **kwars):
    """Initialize the node with creation parameters from the node spec

    Should be implemented by subclasses (unless there are no creation params)
    """

  @abstractmethod
  def initialize(self, inputs, outputs):
    """Initialize the node after the network is fully linked

    It is called once by NuPIC before the first call to compute(). It is
    a good place to perform one time initialization that depend on the inputs
    and/or outputs. The region may also remember its inputs and outputs here
    because they will not change.

    inputs: dict of numpy arrays (one per input)
    outputs: dict of numpy arrays (one per output)
    """

  @abstractmethod
  def compute(self, inputs, outputs):
    """Perform the main computation

    This method is called in each iteration for each phase the node supports.

    inputs: dict of numpy arrays (one per input)
    outputs: dict of numpy arrays (one per output)
    """

  @not_implemented
  def getOutputElementCount(self, name):
    """Return the number of elements in the output of a single node

    If the region has multiple nodes (all must have the same output
    size) then just the number of output elements of a single node
    should be returned.

    name: the name of the output
    """

  def getParameter(self, name, index):
    """Default implementation that return an attribute with the requested name

    This method provides a default implementation of getParameter() that simply
    returns an attribute with the parameter name. If the Region conceptually
    contains multiple nodes with separate state the 'index' argument is used
    to request a parameter of a specific node inside the region. In case of
    a region-level parameter the index should be -1

    The implementation prevents accessing parameters names that start with '_'.
    It may be better to enforce this convention at the node spec level.

    name: name of requested parameter
    index: index of node inside the region (if relevant)

    """
    if name.startswith('_'):
      raise Exception('Parameter name must not start with an underscore')

    value = getattr(self, name)
    return value

  def getParameterArrayCount(self, name, index):
    """Default implementation that return the length of the attribute

    This default implementation goes hand in hand with getParameterArray().
    If you override one of them in your subclass, you should probably override
    both of them.

    The implementation prevents accessing parameters names that start with '_'.
    It may be better to enforce this convention at the node spec level.

    name: name of requested parameter
    index: index of node inside the region (if relevant)
    """
    if name.startswith('_'):
      raise Exception('Parameter name must not start with an underscore')


    v = getattr(self, name)
    return len(self.parameters[name])

  def getParameterArray(self, name, index, array):
    """Default implementation that return an attribute with the requested name

    This method provides a default implementation of getParameterArray() that
    returns an attribute with the parameter name. If the Region conceptually
    contains multiple nodes with separate state the 'index' argument is used
    to request a parameter of a specific node inside the region. The attribute
    value is written into the output array. No type or sanity checks are
    performed for performance reasons. If something goes awry it will result
    in a low-level exception. If you are unhappy about it you can implement
    your own getParameterArray() method in the subclass.

    The implementation prevents accessing parameters names that start with '_'.
    It may be better to enforce this convention at the node spec level.

    name: name of requested parameter
    index: index of node inside the region (if relevant)
    array: output numpy array that the value is written to
    """
    if name.startswith('_'):
      raise Exception('Parameter name must not start with an underscore')

    v = getattr(self, name)
    # Not performing sanity checks for performance reasons.
    #assert array.dtype == v.dtype
    #assert len(array) == len(v)
    array[:] = v

  @not_implemented
  def setParameter(self, name, index, value):
    """Set the value of a parameter

    If the Region conceptually contains multiple nodes with separate state
    the 'index' argument is used set a parameter of a specific node inside
    the region.

    name: name of requested parameter
    index: index of node inside the region (if relevant)
    value: the value to assign to the requested parameter
    """

  @not_implemented
  def setParameterArray(self, name, index, array):
    """Set the value of an array parameter

    If the Region conceptually contains multiple nodes with separate state
    the 'index' argument is used set a parameter of a specific node inside
    the region.

    name: name of requested parameter
    index: index of node inside the region (if relevant)
    array: the value to assign to the requested parameter (a numpy array)
    """

  def serializeExtraData(self, filePath):
    """This method is called during network serialization with an external
    filename that can be used to bypass pickle for saving large binary states.

    filePath: full filepath and name
    """
    pass


  def deSerializeExtraData(self, filePath):
    """This method is called during network deserialization with an external
    filename that can be used to bypass pickle for loading large binary states.

    filePath: full filepath and name
    """
    pass


  def executeMethod(self, methodName, args):
    """Executes a method named 'methodName' with the specified arguments.

    This method is called when the user executes a command as defined in
    the node spec. It provides a perfectly reasonble implementation
    of the command mechanism. As a sub-class developer you just need to
    implement a method for each command in the node spec. Note that due to
    the command mechanism only unnamed argument are supported.

    methodName: the name of the method that correspond to a command in the spec
    args: list of arguments that will be passed to the method
    """
    if not hasattr(self, methodName):
      raise Exception('Missing command method: ' + methodName)

    m = getattr(self, methodName)
    if not hasattr(m, '__call__'):
      raise Exception('Command: ' + methodName + ' must be callable')

    return m(*args)
