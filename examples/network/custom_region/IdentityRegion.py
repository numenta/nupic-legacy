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
from nupic.regions.PyRegion import PyRegion


class IdentityRegion(PyRegion):
  """
  IdentityRegion is designed to implement a dummy region that returns the input
  as the output.
  """

  def __init__(self, dataWidth, **kwargs):
    if dataWidth <=0:
      raise TypeError("Parameter dataWidth must be > 0")
    
    self.dataWidth = dataWidth
    PyRegion.__init__(self, **kwargs)


  #############################################################################
  #
  # Initialization code
  #
  #############################################################################
  def initialize(self, inputs, outputs):
    """"""
    pass

  #############################################################################
  #
  # Core compute methods: compute
  #
  #############################################################################
  def compute(self, inputs, outputs):
    """
    Run one iteration of IdentityRegion's compute
    """
    for k in inputs:
      if k in outputs:
          outputs[k][:] = inputs[k]
      else:
          outputs[k] = inputs[k].copy()

  #############################################################################
  #
  # Region API support methods: getSpec
  #
  #############################################################################

  #############################################################################
  @classmethod
  def getSpec(cls):
    """Return the base Spec for MySPRegion.

    Doesn't include the spatial, temporal and other parameters
    """
    spec = dict(
      description=IdentityRegion.__doc__,
      singleNodeOnly=True,
      inputs=dict(
          data=dict(
          description="""The input vector.""",
          dataType='Real32',
          count=0,
          required=True,
          regionLevel=False,
          isDefaultInput=True,
          requireSplitterMap=False),
      ),
      outputs=dict(
        data=dict(
          description="""A copy of the input vector.""",
          dataType='Real32',
          count=0,
          regionLevel=True,
          isDefaultOutput=True),
      ),

      parameters=dict(
        dataWidth=dict(
          description='Size of inputs',
          accessMode='Read',
          dataType='UInt32',
          count=1,
          constraints=''),
        ),
    )

    return spec

  def getOutputElementCount(self, name):
      return self.dataWidth
