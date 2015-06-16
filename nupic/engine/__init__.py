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

import os
import sys
import nupic.bindings.engine_internal as engine
from nupic.support.lockattributes import LockAttributesMixin
import functools

basicTypes = ['Byte', 'Int16', 'UInt16', 'Int32', 'UInt32', 'Int64', 'UInt64', 'Real32', 'Real64', 'Handle']


# Import all the array types from engine (there is no HandleArray)
arrayTypes = [t + 'Array' for t in basicTypes[:-1]]
for a in arrayTypes:
  exec('from %s import %s as %s' % (engine.__name__, a, a))

# Intercept the default exception handling for the purposes of stripping
# parts of the stack trace that can confuse users. If you want the original
# stack trace define this environment variable
if not 'NTA_STANDARD_PYTHON_UNHANDLED_EXCEPTIONS' in os.environ:
  import traceback
  import cStringIO
  
  def customExceptionHandler(type, value, tb):
    """Catch unhandled Python exception
    
    The handler prints the original exception info including into a buffer.
    It then extracts the original error message (when the exception is raised
    inside a Py node additional stacktrace info will be appended in the end)
    and saves the original exception to a file called error.txt. It prints
    just the error message to the screen and tells the user about the error.txt
    file.
    """
    # Print the exception info to a string IO buffer for manipulation
    buff = cStringIO.StringIO()
    traceback.print_exception(type, value, tb, file=buff)

    text = buff.getvalue()
      
    # get the lines skip the first one: "Traceback (most recent call last)"
    lines = text.split('\n')[1:]
    #
    # Extract the error message
    begin = 0
    end = len(lines)
    for i, line in enumerate(lines):
      if line.startswith('RuntimeError:'):
        begin = i
    #  
    #  elif line.startswith('Traceback (most recent call last):'):
    #    end = i
    #    break
    #
    message = '\n'.join(lines[begin:end])
    message = message[len('Runtime Error:'):]
    #stacktrace = lines[end:]
    
    # Get the stack trace if available (default to empty string)
    stacktrace = getattr(value, 'stackTrace', '')    

        

    # Remove engine from stack trace
    lines = [x for x in lines if 'engine' not in x]
    
    failMessage = 'The program failed with the following error message:'
    dashes = '-' * len(failMessage)
    print
    print dashes
    print 'Traceback (most recent call last):'
    print '\n'.join(lines[:begin-2])
    if stacktrace:
      print stacktrace
    print dashes
    print 'The program failed with the following error message:'
    print dashes
    print message
    print

  #sys.excepthook = customExceptionHandler

# ------------------------------
#
#   T I M E R
#
# ------------------------------

# Expose the timer class directly
# Do it this way instead of bringing engine.Timer 
# into the namespace to avoid engine
# in the class name
class Timer(engine.Timer):
  pass

# ------------------------------
#
#   O S
#
# ------------------------------

# Expose the os class directly
# The only wrapped method is getProcessMemoryUsage()
class OS(engine.OS):
  pass

# ------------------------------
#
#   D I M E N S I O N S
#
# ------------------------------
class Dimensions(engine.Dimensions):
  """Represent the topology of an N-dimensional region
  
  Basically, it is a list of integers such as: [4, 8, 6]
  In this example the topology is a 3 dimensional region with
  4 x 8 x 6 nodes.
  
  You can initialize it with a list of dimensions or with no arguments
  and then append dimensions.
  
  """
  def __init__(self, *args):
    """Construct a Dimensions object
    
    The constructor can be called with no arguments or with a list
    of integers
    """
    # Init the base class
    engine.Dimensions.__init__(self, *args)
    
  def __str__(self):
    return self.toString()

# ------------------------------
#
#   A R R A Y
#
# ------------------------------
def Array(dtype, size=None, ref=False):
  """Factory function that creates typed Array or ArrayRef objects
  
  dtype - the data type of the array (as string).
    Supported types are: Byte, Int16, UInt16, Int32, UInt32, Int64, UInt64, Real32, Real64
  
  size - the size of the array. Must be positive integer.
  """
  
  def getArrayType(self):
    """A little function to replace the getType() method of arrays
    
    It returns a string representation of the array element type instead of the
    integer value (NTA_BasicType enum) returned by the origianl array
    """
    return self._dtype
      
    
  # ArrayRef can't be allocated
  if ref:
    assert size is None
    
  index = basicTypes.index(dtype)
  if index == -1:
    raise Exception('Invalid data type: ' + dtype)
  if size and size <= 0:
    raise Exception('Array size must be positive')
  suffix = 'ArrayRef' if ref else 'Array'
  arrayFactory = getattr(engine, dtype + suffix)
  arrayFactory.getType = getArrayType
  
  if size:
    a = arrayFactory(size)
  else:
    a = arrayFactory()
    
  a._dtype = basicTypes[index]
  return a

def ArrayRef(dtype):
  return Array(dtype, None, True)

# -------------------------------------
#
#   C O L L E C T I O N   W R A P P E R
#
# -------------------------------------
class CollectionIterator(object):
  def __init__(self, collection):
    self.collection = collection
    self.index = 0
    
  def next(self):
    index = self.index
    if index == self.collection.getCount():
      raise StopIteration
    self.index += 1
    return self.collection.getByIndex(index)[0]

class CollectionWrapper(object):
  """Wrap an nupic::Collection with a dict-like interface
  
  The optional valueWrapper is used to wrap values for adaptation purposes.
  Maintains the original documentation
  
  collection - the original collection
  valueWrapper - an optional callable object used to wrap values.
  """
  def IdentityWrapper(o):
    return o
  
  
  def __init__(self, collection, valueWrapper=IdentityWrapper):
    self.collection = collection
    self.valueWrapper = valueWrapper
    self.__class__.__doc__ == collection.__class__.__doc__    

  def __iter__(self):
    return CollectionIterator(self.collection)
  
  def __str__(self):
    return str(self.collection)

  def __repr__(self):
    return repr(self.collection)
  
  def __len__(self):
    return self.collection.getCount()
    
  def __getitem__(self, key):
    if not self.collection.contains(key):
      raise KeyError('Key ' + key + ' not found')

    value =  self.collection.getByName(key)
    value = self.valueWrapper(key, value)
    
    return value
  
  def get(self, key, default=None):
    try:
      return self.__getitem__(key)
    except KeyError:
      return default
        
  def __contains__(self, key):
    return self.collection.contains(key)
    
  def keys(self):
    keys = set()
    for i in range(self.collection.getCount()):
      keys.add(self.collection.getByIndex(i)[0])
    return keys
  
  def values(self):
    values = set()
    
    for i in range(self.collection.getCount()):
      p = self.collection.getByIndex(i)
      values.add(self.valueWrapper(p[0], p[1]))
    return values
  
  def items(self):
    items = set()
    for i in range(self.collection.getCount()):
      p = self.collection.getByIndex(i)
      items.add((p[0], self.valueWrapper(p[0], p[1])))
    return items
  
  def __cmp__(self, other):
    return self.collection == other.collection
  
  def __hash__(self):
    return hash(self.collection)

# -----------------------------
#
#   S P E C   I T E M
#
# -----------------------------
class SpecItem(object):
  """Wrapper that translates the data type and access code to a string
  
  The original values are an enumerated type in C++ that become
  just integers in Python. This class wraps the original ParameterSpec
  and translates the integer values to meaningful strings: that correspond to the C++ enum labels.
  
  It is used to wrap ParameterSpec, InputSpec and OutputSpec
  """
  accessModes = ['Create', 'ReadOnly', 'ReadWrite']

  def __init__(self, name, item):
    self.name = name
    self.item = item
    self.__class__.__doc__ == item.__class__.__doc__
    # Translate data type to string representation
    self.dataType = basicTypes[item.dataType]
    # Translate access mode to string representation
    if hasattr(item, 'accessMode'): # ParameterSpec only
      self.accessMode = SpecItem.accessModes[item.accessMode]
            
  def __getattr__(self, name):
    return getattr(self.item, name)
    
  def __str__(self):
    d = dict(name=self.name,
             description=self.description,
             dataType=self.dataType,
             count=self.count)
    if hasattr(self.item, 'accessMode'): # ParameterSpec only
      self.accessMode = SpecItem.accessModes[self.item.accessMode]
    if hasattr(self.item, 'accessMode'): # ParameterSpec only
      d['accessMode'] = self.accessMode
    if hasattr(self.item, 'constraints'): # ParameterSpec only
      d['constraints'] = self.constraints
    if hasattr(self.item, 'defaultValue'): # ParameterSpec only
      d['defaultValue'] = self.defaultValue
    
    return str(d)

# -------------------
#
#   S P E C
#
# -------------------
class Spec(object):
  def __init__(self, spec):
    self.spec = spec
    self.__class__.__doc__ == spec.__class__.__doc__
    self.description = spec.description
    self.singleNodeOnly = spec.singleNodeOnly
    self.inputs = CollectionWrapper(spec.inputs, SpecItem)
    self.outputs = CollectionWrapper(spec.outputs, SpecItem)
    self.parameters = CollectionWrapper(spec.parameters, SpecItem)
    self.commands = CollectionWrapper(spec.commands)
          
  def __str__(self):
    return self.spec.toString()

  def __repr__(self):
    return self.spec.toString()
  
class _ArrayParameterHelper:
  """This class is used by Region._getParameterMethods"""
  def __init__(self, region, datatype):
    self._region = region
    self.datatype = basicTypes[datatype]

  def getParameterArray(self, paramName):
    # return a PyArray instead of a plain array. 
    # PyArray constructor/class for type X is called XArray()
    #factoryName = self.datatype + 'Array'
    #if factoryName not in globals():
    #  import exceptions
    #  raise exceptions.Exception("Internal error -- did not find %s constructor in engine" % factoryName)
    #
    #arrayFactory = globals()[factoryName]
    #a = arrayFactory();
    a = Array(self.datatype)
    self._region.getParameterArray(paramName, a)
    return a

# -------------------------------------
#
#   R E G I O N
#
# -------------------------------------
class Region(LockAttributesMixin):
  """
  @doc:place_holder(Region.description)
  """

  #Wrapper for a network region
  #- Maintains original documentation
  #- Implement syntactic sugar properties:  
      #name = property(getName)
      #type = property(getType)
      #spec = property(getSpec)
      #dimensions = property(getDimensions, setDimensions)
      #network = property(getNetwork)
  #- Makes sure that returned objects are high-level wrapper objects
  #- Forwards everything else to internal region
  
  def __init__(self, region, network):
    """Store the wraped region and hosting network
    
    The network is the high-level Network and not the internal
    Network. This is important in case the user requests the network
    from the region (never leak a engine object, remember)
    """
    self._network = network
    self._region = region
    self.__class__.__doc__ == region.__class__.__doc__
    
    # A cache for typed get/setPArameter() calls
    self._paramTypeCache = {}
    
  def __getattr__(self, name):
    if not '_region' in self.__dict__:
      raise AttributeError
    return getattr(self._region, name)

  def __setattr__(self, name, value):
    if name in ('_region', '__class__', '_network'):
      self.__dict__[name] = value
    elif name == 'dimensions':
      self.setDimensions(value)
    else:
      setattr(self._region, name, value)
        
  @staticmethod
  def getSpecFromType(nodeType):
    """
    @doc:place_holder(Region.getSpecFromType)
    """
    return Spec(engine.Region.getSpecFromType(nodeType))
    
  def compute(self):
    """
    @doc:place_holder(Region.compute)
    
    ** This line comes from the original docstring (not generated by Documentor) 
    
    """
    return self._region.compute()
    
  def getInputData(self, inputName):
    """
    @doc:place_holder(Region.getInputData)
    """
    return self._region.getInputArray(inputName)

  def getOutputData(self, outputName):
    """
    @doc:place_holder(Region.getOutputData)
    """
    return self._region.getOutputArray(outputName)
    
  
  def executeCommand(self, args):
    """
    @doc:place_holder(Region.executeCommand)
    """    
    return self._region.executeCommand(args)
    
    
  def _getSpec(self):
    """Spec of the region"""
    return Spec(self._region.getSpec())

  def _getDimensions(self):
    """Dimensions of the region"""
    return Dimensions(tuple(self._region.getDimensions()))
      
  def _getNetwork(self):
    """Network for the region"""
    return self._network
            
  def __hash__(self):
    """Hash a region"""
    return self._region.__hash__()
    
  def __cmp__(self, other):
    """Compare regions"""
    return self._region == other._region
 

  def _getParameterMethods(self, paramName):
    """Returns functions to set/get the parameter. These are 
    the strongly typed functions get/setParameterUInt32, etc.
    The return value is a pair:
        setfunc, getfunc
    If the parameter is not available on this region, setfunc/getfunc
    are None. """
    if paramName in self._paramTypeCache:
      return self._paramTypeCache[paramName]
    try:
      # Catch the error here. We will re-throw in getParameter or 
      # setParameter with a better error message than we could generate here
      paramSpec = self.getSpec().parameters.getByName(paramName)
    except:
      return (None, None)
    dataType = paramSpec.dataType
    dataTypeName = basicTypes[dataType]
    count = paramSpec.count
    if count == 1:
      # Dynamically generate the proper typed get/setParameter<dataType>
      x = 'etParameter' + dataTypeName
      try:
        g = getattr(self, 'g' + x) # get the typed getParameter method
        s = getattr(self, 's' + x) # get the typed setParameter method
      except AttributeError:
        raise Exception("Internal error: unknown parameter type %s" % dataTypeName)
      info = (s, g)      
    else:
      if dataTypeName == "Byte":
        info = (self.setParameterString, self.getParameterString)
      else:
        helper = _ArrayParameterHelper(self, dataType)
        info = (self.setParameterArray, helper.getParameterArray)

    self._paramTypeCache[paramName] = info
    return info

  def getParameter(self, paramName):
    """Get parameter value"""
    (setter, getter) = self._getParameterMethods(paramName)
    if getter is None:
      import exceptions
      raise exceptions.Exception("getParameter -- parameter name '%s' does not exist in region %s of type %s" %
                       (paramName, self.name, self.type))
    return getter(paramName)

  def setParameter(self, paramName, value):
    """Set parameter value"""
    (setter, getter) = self._getParameterMethods(paramName)
    if setter is None:
      import exceptions
      raise exceptions.Exception("setParameter -- parameter name '%s' does not exist in region %s of type %s" %
                       (paramName, self.name, self.type))
    setter(paramName, value)


  def _get(self, method):
    """Auto forwarding of properties to get methods of internal region"""
    return getattr(self._region, method)()

  network = property(_getNetwork,
                     doc='@property:place_holder(Region.getNetwork)')

  name = property(functools.partial(_get, method='getName'),
                  doc="@property:place_holder(Region.getName)")

  type = property(functools.partial(_get, method='getType'),
                      doc='@property:place_holder(Region.getType)')

  spec = property(_getSpec,
                      doc='@property:place_holder(Region.getSpec)')
      
  dimensions = property(_getDimensions,
                        engine.Region.setDimensions,
                        doc='@property:place_holder(Region.getDimensions)')
  
  computeTimer = property(functools.partial(_get, method='getComputeTimer'),
                          doc='@property:place_holder(Region.getComputeTimer)')

  executeTimer = property(functools.partial(_get, method='getExecuteTimer'),
                          doc='@property:place_holder(Region.getExecuteTimer)')

# ------------------------------
#
#   N E T W O R K
#
# ------------------------------
class Network(engine.Network):
  """
  @doc:place_holder(Network.description)
  """

  def __init__(self, *args):
    """Constructor
    
    - Initialize the internal engine.Network class generated by Swig
    - Attach docstrings to selected methods
    """
    # Init engine.Network class
    engine.Network.__init__(self, *args)
    
    # Prepare documentation table.
    # Each item is pair of method/property, docstring
    # The docstring is attached later to the method or property.
    # The key for method items is the method object of the engine.Network class.
    # The key for properties is the property name

    docTable = (
        (engine.Network.getRegions, 'Get the collection of regions in a network'),
    )
    
    # Attach documentation to methods and properties
    for obj, docString in docTable:
      if isinstance(obj, str):
        prop = getattr(Network, obj)
        assert isinstance(prop, property)
        setattr(Network, obj, property(prop.fget, prop.fset, prop.fdel, docString))
      else:
        obj.im_func.__doc__ = docString
    
  def _getRegions(self):
    """Get the collection of regions in a network
    
    This is a tricky one. The collection of regions returned from
    from the internal network is a collection of internal regions.
    The desired collection is a collelcion of net.Region objects
    that also points to this network (net.network) and not to
    the internal network. To achieve that a CollectionWrapper
    class is used with a custom makeRegion() function (see bellow)
    as a value wrapper. The CollectionWrapper class wraps each value in the
    original collection with the result of the valueWrapper.
    """

    def makeRegion(name, r):
      """Wrap a engine region with a nupic.engine.Region
      
      Also passes the containing nupic.engine.Network network in _network. This
      function is passed a value wrapper to the CollectionWrapper      
      """
      r = Region(r, self)
      #r._network = self
      return r
    
    regions = CollectionWrapper(engine.Network.getRegions(self), makeRegion)    
    return regions
    
  def addRegion(self, name, nodeType, nodeParams):    
    """
    @doc:place_holder(Network.addRegion)
    """
    engine.Network.addRegion(self, name, nodeType, nodeParams)
    return self._getRegions()[name]
    

  def addRegionFromBundle(self, name, nodeType, dimensions, bundlePath, label):
    """
    @doc:place_holder(Network.addRegionFromBundle)
    """

    engine.Network.addRegionFromBundle(self,
                                   name,
                                   nodeType,
                                   dimensions,
                                   bundlePath,
                                   label)
    return self._getRegions()[name]

  def setPhases(self, name, phases):
    """
    @doc:place_holder(Network.setPhases)
    """
    phases = engine.UInt32Set(phases)
    engine.Network.setPhases(self, name, phases)

  def run(self, n):
    """
    @doc:place_holder(Network.run)
    """

    #Just forward to the internal network
    #This is needed for inspectors to work properly because they wrap some key
    #methods such as 'run'.

    engine.Network.run(self, n)

  def disableProfiling(self, *args, **kwargs):
    """
    @doc:place_holder(Network.disableProfiling)
    """
    engine.Network.disableProfiling(self, *args, **kwargs)

  def enableProfiling(self, *args, **kwargs):
    """
    @doc:place_holder(Network.enableProfiling)
    """
    engine.Network.enableProfiling(self, *args, **kwargs)

  def getCallbacks(self, *args, **kwargs):
    """
    @doc:place_holder(Network.getCallbacks)
    """
    engine.Network.getCallbacks(self, *args, **kwargs)


  def initialize(self, *args, **kwargs):
    """
    @doc:place_holder(Network.initialize)
    """
    engine.Network.initialize(self, *args, **kwargs)

  def link(self, *args, **kwargs):
    """
    @doc:place_holder(Network.link)
    """
    engine.Network.link(self, *args, **kwargs)

  def removeLink(self, *args, **kwargs):
    """
    @doc:place_holder(Network.removeLink)
    """
    engine.Network.removeLink(self, *args, **kwargs)

  def removeRegion(self, *args, **kwargs):
    """
    @doc:place_holder(Network.removeRegion)
    """
    engine.Network.removeRegion(self, *args, **kwargs)

  def resetProfiling(self, *args, **kwargs):
    """
    @doc:place_holder(Network.resetProfiling)
    """
    engine.Network.resetProfiling(self, *args, **kwargs)

  def save(self, *args, **kwargs):
    """
    @doc:place_holder(Network.save)
    """
    engine.Network.save(self, *args, **kwargs)


  def inspect(self):
    """Launch a GUI inpector to inspect the network"""
    from nupic.analysis import inspect    
    inspect(self)

  @staticmethod
  def registerRegionPackage(package):
    """
    Adds the package to the list of packages the network can access for regions
    package: name of Python package, that is reachable through the PYTHONPATH
    """
    engine.Network.registerPyRegionPackage(package)

  # Syntactic sugar properties
  regions = property(_getRegions, doc='@property:place_holder(Network.getRegions)')
  minPhase = property(engine.Network.getMinPhase, doc='@property:place_holder(Network.getMinPhase)')
  maxPhase = property(engine.Network.getMaxPhase, doc='@property:place_holder(Network.getMaxPhase)')
  minEnabledPhase = property(engine.Network.getMinEnabledPhase, engine.Network.setMinEnabledPhase, doc='@property:place_holder(Network.getMinEnabledPhase)')
  maxEnabledPhase = property(engine.Network.getMaxEnabledPhase, engine.Network.setMaxEnabledPhase, doc='@property:place_holder(Network.getMaxEnabledPhase)')
    
if __name__=='__main__':
  n = Network()
  print n.regions
  print len(n.regions)
  print Network.regions.__doc__
  
  d = Dimensions([3, 4, 5])
  print len(d)
  print d
  
  a = Array('Byte', 5)
  print len(a)
  for i in range(len(a)):
    a[i] = ord('A') + i
    
  for i in range(len(a)):
    print a[i]
    
  r = n.addRegion('r', 'TestNode', '')
  print 'name:', r.name
  print 'node type:', r.type
  print 'node spec:', r.spec

