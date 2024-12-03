# Copyright 2015 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

from nupic.bindings.regions.PyRegion import PyRegion



class IdentityRegion(PyRegion):
  """
  IdentityRegion is designed to implement a dummy region that returns the input
  as the output.
  """


  def __init__(self, dataWidth):
    if dataWidth <= 0:
      raise ValueError("Parameter dataWidth must be > 0")
    self._dataWidth = dataWidth


  def initialize(self):
    pass


  def compute(self, inputs, outputs):
    """
    Run one iteration of IdentityRegion's compute
    """
    outputs["out"][:] = inputs["in"]


  @classmethod
  def getSpec(cls):
    """Return the Spec for IdentityRegion.
    """
    spec = {
        "description":IdentityRegion.__doc__,
        "singleNodeOnly":True,
        "inputs":{
          "in":{
            "description":"The input vector.",
            "dataType":"Real32",
            "count":0,
            "required":True,
            "regionLevel":False,
            "isDefaultInput":True,
            "requireSplitterMap":False},
        },
        "outputs":{
          "out":{
            "description":"A copy of the input vector.",
            "dataType":"Real32",
            "count":0,
            "regionLevel":True,
            "isDefaultOutput":True},
        },

        "parameters":{
          "dataWidth":{
            "description":"Size of inputs",
            "accessMode":"Read",
            "dataType":"UInt32",
            "count":1,
            "constraints":""},
        },
    }

    return spec


  def getOutputElementCount(self, name):
    if name == "out":
      return self._dataWidth
    else:
      raise Exception("Unrecognized output: " + name)
