
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

"""
## @file
This file defines node spec item classes like InputSpec, OutputSpec,
ParameterSpec and CommandSpec as well as the Spec class itself.
These classes correspond very closely to the NuPIC 2 C++ Spec.

The data type of inputs outputs and parameters must be basic Python types. This
is different from nuPIC 1 that allowed for arbitrary Python values as objects.

The Spec class provides a toDict() method that converts itself a dict of
dicts. All the keys must be regular strings for simplicity (no Unicode strings).

Each item class provides a constructor (__init__() method) with some defaults
and an invariant() method that verifies the validity of initialized object.
"""

dataTypes = ('int', 'uint', 'bool', 'str', 'float', 'Handle')
dataTypesToPyTypes = {
                      'int': int,
                      'uint': int,
                      'bool': bool,
                      'str': str,
                      'float': float,
                      'Handle': object,
                     }

class InputSpec(object):
  def __init__(self,
               description='',
               dataType=None,
               count=1,
               required=False,
               regionLevel=False,
               isDefaultInput=False,
               requireSplitterMap=True):
    self.description=description
    self.dataType=dataType
    self.count=count
    self.required=required
    self.regionLevel=regionLevel
    self.isDefaultInput=isDefaultInput
    self.requireSplitterMap=requireSplitterMap
    self.invariant()

  def invariant(self):
    assert isinstance(self.description, str)
    assert isinstance(self.dataType, str)
    assert self.dataType in dataTypes
    assert isinstance(self.count, int)
    assert self.count >= 0
    assert isinstance(self.required, bool)
    assert isinstance(self.regionLevel, bool)
    assert isinstance(self.isDefaultInput, bool)
    assert isinstance(self.requireSplitterMap, bool)

class OutputSpec(object):
  def __init__(self,
               description='',
               dataType=None,
               count=1,
               regionLevel=False,
               isDefaultOutput=False):
    self.description=description
    self.dataType=dataType
    self.count=count
    self.regionLevel=regionLevel
    self.isDefaultOutput=isDefaultOutput
    self.invariant()

  def invariant(self):
    assert isinstance(self.description, str)
    assert isinstance(self.dataType, str)
    assert self.dataType in dataTypes
    assert isinstance(self.count, int)
    assert self.count >= 0
    assert isinstance(self.regionLevel, bool)
    assert isinstance(self.isDefaultOutput, bool)

class ParameterSpec(object):
  accessModes = ('Create', 'Read', 'ReadWrite')
  def __init__(self,
               description='',
               dataType=None,
               count=1,
               constraints='',
               defaultValue=None,
               accessMode=None):
    self.description=description
    self.dataType=dataType
    # String object can't have fixed length in the parameter spec
    if dataType == 'str':
      count = 0
    self.count=count
    self.constraints=constraints
    self.defaultValue=defaultValue
    self.accessMode=accessMode
    self.invariant()

  def invariant(self):
    assert isinstance(self.description, str)
    assert isinstance(self.dataType, str)
    assert self.dataType in dataTypes
    assert isinstance(self.count, int)
    assert self.count >= 0
    assert isinstance(self.constraints, str)
    # Verify that default value is specified only for 'Create' parameters
    if self.defaultValue is not None:
      assert self.accessMode == 'Create'
      assert isinstance(self.defaultValue, dataTypesToPyTypes[self.dataType])
    else:
      assert self.accessMode in ParameterSpec.accessModes, \
             'Bad access node: ' + self.accessMode

class CommandSpec(object):
  def __init__(self, description):
    self.description = description

  def invariant(self):
    assert isinstance(self.description, str)

class Spec(object):
  def __init__(self, description, singleNodeOnly):
    self.description = description
    self.singleNodeOnly = singleNodeOnly
    self.inputs = {}
    self.outputs = {}
    self.parameters = {}
    self.commands = {}

  def invariant(self):
    """Verify the validity of the node spec object

    The type of each sub-object is verified and then
    the validity of each node spec item is verified by calling
    it invariant() method. It also makes sure that there is at most
    one default input and one default output.
    """
    # Verify the description and singleNodeOnly attributes
    assert isinstance(self.description, str)
    assert isinstance(self.singleNodeOnly, bool)

    # Make sure that all items dicts are really dicts
    assert isinstance(self.inputs, dict)
    assert isinstance(self.outputs, dict)
    assert isinstance(self.parameters, dict)
    assert isinstance(self.commands, dict)

    # Verify all item dicts
    hasDefaultInput = False
    for k, v in self.inputs.items():
      assert isinstance(k, str)
      assert isinstance(v, InputSpec)
      v.invariant()
      if v.isDefaultInput:
        assert not hasDefaultInput
        hasDefaultInput = True


    hasDefaultOutput = False
    for k, v in self.outputs.items():
      assert isinstance(k, str)
      assert isinstance(v, OutputSpec)
      v.invariant()
      if v.isDefaultOutput:
        assert not hasDefaultOutput
        hasDefaultOutput = True

    for k, v in self.parameters.items():
      assert isinstance(k, str)
      assert isinstance(v, ParameterSpec)
      v.invariant()

    for k, v in self.commands.items():
      assert isinstance(k, str)
      assert isinstance(v, CommandSpec)
      v.invariant()

  def toDict(self):
    """Convert the information of the node spec to a plain dict of basic types

    The description and singleNodeOnly attributes are placed directly in
    the result dicts. The inputs, outputs, parameters and commands dicts
    contain Spec item objects (InputSpec, OutputSpec, etc). Each such object
    is converted also to a plain dict using the internal items2dict() function
    (see bellow).
    """

    def items2dict(items):
      """Convert a dict of node spec items to a plain dict

      Each node spec item object will be converted to a dict of its
      attributes. The entire items dict will become a dict of dicts (same keys).
      """
      d = {}
      for k, v in items.items():
        d[k] = v.__dict__

      return d

    self.invariant()
    return dict(description=self.description,
                singleNodeOnly=self.singleNodeOnly,
                inputs=items2dict(self.inputs),
                outputs=items2dict(self.outputs),
                parameters=items2dict(self.parameters),
                commands=items2dict(self.commands))
