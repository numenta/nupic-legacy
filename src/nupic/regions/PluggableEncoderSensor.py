# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2016, Numenta, Inc.  Unless you have an agreement
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

from nupic.bindings.regions.PyRegion import PyRegion

class PluggableEncoderSensor(PyRegion):
  """
  A PluggableEncoderSensor holds a value and encodes it into network output.

  It requires you to reach in and insert an encoder.
  """

  @classmethod
  def getSpec(cls):
    return {
      'singleNodeOnly': True,
      'description': PluggableEncoderSensor.__doc__,
      'outputs': {
        'encoded': {
          'description': '',
          'dataType': 'Real32',
          'count': 0,
          'regionLevel': True,
          'isDefaultOutput': True,
        }},
      'parameters': {},
    }

  def __init__(self, **kwargs):
    # We don't know the sensed value's type, so it's not a spec parameter.
    self._sensedValue = None

  def initialize(self, dims, splitterMaps):
    pass

  def compute(self, inputs, outputs):
    if self.encoder is None:
      raise Exception('Please insert an encoder.')

    result = self.encoder.encode(self._sensedValue)
    self.encoder.encodeIntoArray(self._sensedValue, outputs['encoded'])

  def getOutputElementCount(self, name):
    if name == 'encoded':
      return self.encoder.getWidth()
    else:
      raise Exception('Unrecognized output %s' % name)

  def getSensedValue(self):
    return self._sensedValue

  def setSensedValue(self, value):
    """
    Sets the value that will be encoded when this region does a compute.
    """
    self._sensedValue = value

  def getParameter(self, parameterName, index=-1):
    if parameter == 'sensedValue':
      raise Exception('For the PluggableEncoderSensor, get the sensedValue via the getSensedValue method')
    else:
      raise Exception('Unrecognized parameter %s' % parameterName)

  def setParameter(self, parameterName, index, parameterValue):
    if parameter == 'sensedValue':
      raise Exception('For the PluggableEncoderSensor, set the sensedValue via the setSensedValue method')
    else:
      raise Exception('Unrecognized parameter %s' % parameterName)
