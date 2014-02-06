#!/usr/bin/env python

# ----------------------------------------------------------------------
#  Copyright (C) 2010 Numenta Inc. All rights reserved.
#
#  The information and source code contained herein is the
#  exclusive property of Numenta Inc. No part of this software
#  may be used, reproduced, stored or distributed in any form,
#  without explicit written authorization from Numenta Inc.
# ----------------------------------------------------------------------

from nupic.regions.Spec import *

def testInvalidInputSpec():
  """ """
  try:
    x = InputSpec()
    assert False
  except:
    pass

  try:
    x = InputSpec(dataType='int', count=-4)
    assert False
  except:
    pass

  try:
    x = InputSpec(description=555, dataType='int', count=4)
    assert False
  except:
    pass

def testValidInputSpec():
  """ """
  x = InputSpec(dataType='int', count=4)
  x.invariant()

  x = InputSpec(description='description',
                dataType='int',
                count=3,
                required=True,
                regionLevel=True,
                isDefaultInput=True,
                requireSplitterMap=True)
  x.invariant()

def testInvalidOutputSpec():
  """ """
  try:
    x = OutputSpec()
    assert False
  except:
    pass

  try:
    x = OutputSpec(dataType='int', count=4, isDefaultOutput='Sure')
    assert False
  except:
    pass

  try:
    x = OutputSpec(description=555, dataType='int', count=4)
    assert False
  except:
    pass
def testValidOutputSpec():
  """ """
  x = OutputSpec(dataType='int', count=4)
  x.invariant()

  x = OutputSpec(description='description',
                dataType='int',
                count=3,
                regionLevel=True,
                isDefaultOutput=True)
  x.invariant()


def testInvalidParameterSpec():
  """ """
  try:
    x = ParameterSpec()
    assert False
  except:
    pass

  try:
    x = ParameterSpec(dataType='int', count=4, defaultValue='not an int')
    assert False
  except:
    pass

  try:
    x = ParameterSpec(description=555, dataType='int')
    assert False
  except:
    pass

  try:
    x = ParameterSpec(dataType='int',
                      accessMode='no such mode')
    assert False
  except:
    pass

  try:
    x = ParameterSpec(dataType='int',
                      defaultValue=5,
                      accessMode='Read')
    assert False
  except:
    pass

def testValidParameterSpec():
  """ """
  x = ParameterSpec(dataType='int', accessMode='Read')
  x.invariant()

  x = ParameterSpec(description='description',
                dataType='int',
                count=3,
                defaultValue=-6,
                accessMode='Create')
  x.invariant()

def testInvalidCommandSpec():
  """ """
  try:
    x = CommandSpec()
    assert False
  except:
    pass

  try:
    x = CommandSpec(description=None)
    assert False
  except:
    pass

  try:
    x = CommandSpec(description=3)
    assert False
  except:
    pass

def testValidCommandSpec():
  """ """
  x = CommandSpec('')
  x.invariant()
  x = CommandSpec(description='')
  x.invariant()
  x = CommandSpec(description='this is a command')
  x.invariant()

def testInvalidSpec():
  """ """
  try:
    x = Spec()
    assert False
  except:
    pass

  try:
    x = Spec(description=3)
    assert False
  except:
    pass

  try:
    x = Spec(description='123', singleNodeOnly=3)
    assert False
  except:
    pass

def testValidSpec():
  """ """
  x = Spec(description='123', singleNodeOnly=True)
  x.invariant()

  x = Spec(description='123', singleNodeOnly=True)
  x.commands = dict(command1=CommandSpec('A command'),
                    command2=CommandSpec('Another command'))
  x.invariant()


def testSpec_toDict():
  """ """
  x = Spec(description='123', singleNodeOnly=True)
  d = x.toDict()
  assert d['description'] == '123'
  assert d['singleNodeOnly']
  assert d['inputs'] == d['outputs'] == d['parameters'] == d['commands'] == {}

  x.inputs = dict(i1=InputSpec(dataType='int'),
                  i2=InputSpec(dataType='str', isDefaultInput=True))
  x.outputs = dict(o=OutputSpec(dataType='float', count=8))
  x.parameters = dict(p=ParameterSpec(description='param',
                                      dataType='float',
                                      defaultValue=3.14,
                                      accessMode='Create'))

  d = x.toDict()
  print d
  inputs = d['inputs']
  assert len(inputs) == 2
  i1 = inputs['i1']
  assert i1['count'] == 1
  assert not i1['isDefaultInput']
  assert i1['description'] == ''
  assert i1['dataType'] == 'int'
  assert not i1['required']
  assert i1['requireSplitterMap']
  assert not i1['regionLevel']

  i2 = inputs['i2']
  assert i2['count'] == 1
  assert i2['isDefaultInput']
  assert i2['description'] == ''
  assert i2['dataType'] == 'str'
  assert not i2['required']
  assert i2['requireSplitterMap']
  assert not i2['regionLevel']

  outputs = d['outputs']
  assert len(outputs) == 1
  o = outputs['o']
  assert o['count'] == 8
  assert not o['isDefaultOutput']
  assert o['description'] == ''
  assert o['dataType'] == 'float'
  assert not o['regionLevel']

  parameters = d['parameters']
  assert len(parameters) == 1
  p = parameters['p']
  assert p['description'] == 'param'
  assert p['dataType'] == 'float'
  assert p['accessMode'] == 'Create'
  assert p['defaultValue'] == 3.14
  assert p['count'] == 1
  assert p['constraints'] == ''

  assert d['commands'] == {}


def test():
  """Test valid and invalid node spec objects and items"""
  testInvalidInputSpec()
  testValidInputSpec()
  testInvalidOutputSpec()
  testValidOutputSpec()
  testInvalidParameterSpec()
  testValidParameterSpec()
  testInvalidCommandSpec()
  testValidCommandSpec()
  testInvalidSpec()
  testValidSpec()
  testSpec_toDict()

if __name__=='__main__':
  test()
  print 'Done.'