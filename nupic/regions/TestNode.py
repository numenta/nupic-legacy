from pprint import pprint as pp

import numpy
from PyRegion import PyRegion


class TestNode(PyRegion):
  @classmethod
  def getSpec(cls):
    if hasattr(TestNode, '_failIngetSpec'):
      assert False, 'Failing in TestNode.getSpec() as requested'
    result = dict(
      description='The node spec of the NuPIC 2 Python TestNode',
      singleNodeOnly=False,
      inputs=dict(
        bottomUpIn=dict(
          description='Primary input for the node',
          dataType='Real64',
          count=0,
          required=True,
          regionLevel=False,
          isDefaultInput=True,
          requireSplitterMap=True
          )
        ),
      outputs=dict(
        bottomUpOut=dict(
          description='Primary output for the node',
          dataType='Real64',
          count=0,
          regionLevel=False,
          isDefaultOutput=True
          )
        ),
      parameters=dict(
        int32Param=dict(
          description='Int32 scalar parameter',
          dataType='Int32',
          count=1,
          constraints='',
          defaultValue='32',
          accessMode='ReadWrite'
        ),
        uint32Param=dict(
          description='UInt32 scalar parameter',
          dataType='UInt32',
          count=1,
          constraints='',
          defaultValue='33',
          accessMode='ReadWrite'
        ),
        int64Param=dict(
          description='Int64 scalar parameter',
          dataType='Int64',
          count=1,
          constraints='',
          defaultValue='64',
          accessMode='ReadWrite'
        ),
        uint64Param=dict(
          description='UInt64 scalar parameter',
          dataType='UInt64',
          count=1,
          constraints='',
          defaultValue='65',
          accessMode='ReadWrite'
        ),
        real32Param=dict(
          description='Real32 scalar parameter',
          dataType='Real32',
          count=1,
          constraints='',
          defaultValue='32.1',
          accessMode='ReadWrite'
        ),
        real64Param=dict(
          description='Real64 scalar parameter',
          dataType='Real64',
          count=1,
          constraints='',
          defaultValue='64.1',
          accessMode='ReadWrite'
        ),
        real32arrayParam=dict(
          description='Real32 array parameter',
          dataType='Real32',
          count=0, # array
          constraints='',
          defaultValue='',
          accessMode='ReadWrite'
        ),
        int64arrayParam=dict(
          description='Int64 array parameter',
          dataType='Int64',
          count=0, # array
          constraints='',
          defaultValue='',
          accessMode='ReadWrite'
        ),
        stringParam=dict(
          description='String parameter',
          dataType='Byte',
          count=0, # string is conventionally Byte/0
          constraints='',
          defaultValue='nodespec value',
          accessMode='ReadWrite'
        ),
        failInInit=dict(
          description='For testing failure in __init__()',
          dataType='Int32',
          count=1,
          constraints='',
          defaultValue='0',
          accessMode='ReadWrite'
        ),
        failInCompute=dict(
          description='For testing failure in compute()',
          dataType='Int32',
          count=1,
          constraints='',
          defaultValue='0',
          accessMode='ReadWrite'
        ),
      ),
      commands=dict()
    )

    print result
    return result

  def __init__(self, *args, **kwargs):
    """ """
    # Facilitate failing in __init__ to test error handling
    if 'failInInit' in kwargs:
      assert False, 'TestNode.__init__() Failing on purpose as requested'

    # Check if should fail in compute to test error handling
    self._failInCompute = kwargs.pop('failInCompute', False)

    # set these to a bunch of incorrect values, just to make
    # sure they are set correctly by the nodespec.
    self.parameters = dict(
      int32Param=32,
      uint32Param=33,
      int64Param=64,
      uint64Param=65,
      real32Param=32.1,
      real64Param=64.1,
      real32ArrayParam=numpy.arange(10).astype('float32'),
      real64ArrayParam=numpy.arange(10).astype('float64'),
      # Construct int64 array in the same way as in C++
      int64ArrayParam=numpy.arange(4).astype('int64'),
      stringParam="nodespec value")


    for key in kwargs:
      if not key in self.parameters:
        raise Exception("TestNode found keyword %s but there is no parameter with that name" % key)
      self.parameters[key] = kwargs[key]

    self.outputElementCount = 2 # used for computation
    self._delta = 1
    self._iter = 0
    for i in xrange(0,4):
      self.parameters["int64ArrayParam"][i] = i*64

  def getParameter(self, name, index):
    assert name in self.parameters
    return self.parameters[name]

  def setParameter(self, name, index, value):
    assert name in self.parameters
    self.parameters[name] = value

  def initialize(self, dims, splitterMaps):
    print 'TestNode.initialize() here.'
    assert len(dims) == 2
    self.dims = dims
    self.nodeCount = dims[0] * dims[1]
    self.splitterMap = splitterMaps['bottomUpIn']
    print 'self.nodeCount:', self.nodeCount
    print 'self.splitterMap:', self.splitterMap
    print

  def _getInputForNode(self, input, index):
    #from dbgp.client import brk; brk(port=9019)
    #indices = self.splitterMap[index * 8: index * 8 + 8]
    indices = self.splitterMap[index]
    v = []
    for i in indices:
      v.append(input[i])

    return v

  def compute(self, inputs, outputs):
    if self._failInCompute:
      assert False, 'TestNode.compute() Failing on purpose as requested'

    print 'TestNode.compute() here.'
    print 'splitter map:',
    pp(self.splitterMap)
    print

    print 'inputs:',
    pp(inputs)
    print

    if not 'bottomUpIn' in inputs:
      bottomUpIn = [0] * 8
    else:
      bottomUpIn = inputs['bottomUpIn']
    bottomUpOut = outputs['bottomUpOut']
    assert len(bottomUpOut) == self.nodeCount * self.outputElementCount

    for node in range(self.nodeCount):
      input = self._getInputForNode(bottomUpIn, node)
      if len(input) > 0:
        try:
          input = numpy.concatenate(input)
        except ValueError: # 0-d dimensioned inputs don't need concatenation
          #from dbgp.client import brk; brk(port=9019)
          pass

      base = node * self.outputElementCount
      bottomUpOut[base] = len(input) + self._iter
      x = sum(input)
      for i in range(1, self.outputElementCount):
        value = node + x + (i - 1) * self._delta
        bottomUpOut[base+i] = value
        print 'index, value:', base+i, value
        print bottomUpOut[:base+i+1]
        print '-----'

    self._iter += 1

    print 'outputs:',
    pp(outputs)
    print

  def getOutputElementCount(self, name):
    assert name == 'bottomUpOut'
    return self.outputElementCount

  def getParameterArrayCount(self, name, index):
    assert name.endswith('ArrayParam')
    print 'len(self.parameters[%s]) = %d' % (name, len(self.parameters[name]))
    return len(self.parameters[name])

  def getParameterArray(self, name, index, array):
    assert name.endswith('ArrayParam')
    assert name in self.parameters
    v = self.parameters[name]
    assert len(array) == len(v)
    assert array.dtype == v.dtype
    array[:] = v

  def setParameterArray(self, name, index, array):
    assert name.endswith('ArrayParam')
    assert name in self.parameters
    assert array.dtype == self.parameters[name].dtype
    self.parameters[name] = numpy.array(array)

def test():
  from pprint import pprint as pp
  ns = TestNode.getSpec()
  pp(ns)

if __name__=='__main__':
  test()