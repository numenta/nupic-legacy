# Copyright 2016 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

from nupic.bindings.regions.PyRegion import PyRegion

class PluggableEncoderSensor(PyRegion):
  """
  Holds a value and encodes it into network output.

  It requires you to reach in and insert an encoder:
  
  .. code-block:: python
  
    timestampSensor = network.addRegion("timestampSensor",
                                      'py.PluggableEncoderSensor', "")
    timestampSensor.getSelf().encoder = DateEncoder(timeOfDay=(21, 9.5),
                                                  name="timestamp_timeOfDay")

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

  def initialize(self):
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
    """
    :return: sensed value 
    """
    return self._sensedValue

  def setSensedValue(self, value):
    """
    :param value: will be encoded when this region does a compute.
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
