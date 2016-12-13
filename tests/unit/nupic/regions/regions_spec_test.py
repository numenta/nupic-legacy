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

import unittest2 as unittest

from nupic.regions.Spec import (Spec,
                                InputSpec,
                                OutputSpec,
                                ParameterSpec,
                                CommandSpec)



class KNNAnomalyClassifierRegionTest(unittest.TestCase):


  def testInvalidInputSpec(self):
    with self.assertRaises(Exception):
      _x = InputSpec()

    with self.assertRaises(Exception):
      _x = InputSpec(dataType="int", count=-4)

    with self.assertRaises(Exception):
      _x = InputSpec(description=555, dataType="int", count=4)


  def testValidInputSpec(self):
    try:
      x = InputSpec(dataType="int", count=4)
      x.invariant()

      x = InputSpec(description="description",
                    dataType="int",
                    count=3,
                    required=True,
                    regionLevel=True,
                    isDefaultInput=True,
                    requireSplitterMap=True)
      x.invariant()
    except:
      self.fail("Got unexpected exception")


  def testInvalidOutputSpec(self):
    with self.assertRaises(Exception):
      _x = OutputSpec()

    with self.assertRaises(Exception):
      _x = OutputSpec(dataType="int", count=4, isDefaultOutput="Sure")

    with self.assertRaises(Exception):
      _x = OutputSpec(description=555, dataType="int", count=4)


  def testValidOutputSpec(self):
    try:
      x = OutputSpec(dataType="int", count=4)
      x.invariant()

      x = OutputSpec(description="description",
                    dataType="int",
                    count=3,
                    regionLevel=True,
                    isDefaultOutput=True)
      x.invariant()
    except:
      self.fail("Got unexpected exception")


  def testInvalidParameterSpec(self):
    with self.assertRaises(Exception):
      _x = ParameterSpec()

    with self.assertRaises(Exception):
      _x = ParameterSpec(dataType="int", count=4, defaultValue="not an int")

    with self.assertRaises(Exception):
      _x = ParameterSpec(description=555, dataType="int")

    with self.assertRaises(Exception):
      _x = ParameterSpec(dataType="int",
                        accessMode="no such mode")

    with self.assertRaises(Exception):
      _x = ParameterSpec(dataType="int",
                        defaultValue=5,
                        accessMode="Read")


  def testValidParameterSpec(self):
    try:
      x = ParameterSpec(dataType="int", accessMode="Read")
      x.invariant()

      x = ParameterSpec(description="description",
                    dataType="int",
                    count=3,
                    defaultValue=-6,
                    accessMode="Create")
      x.invariant()
    except:
      self.fail("Got unexpected exception")


  @unittest.skip("(#616) Disabled for now,"
    "to add error checking in commandSpec later.")
  def testInvalidCommandSpec(self):
    with self.assertRaises(Exception):
      _x = CommandSpec()

    with self.assertRaises(Exception):
      _x = CommandSpec(description=None)

    with self.assertRaises(Exception):
      _x = CommandSpec(description=3)


  def testValidCommandSpec(self):
    try:
      x = CommandSpec("")
      x.invariant()
      x = CommandSpec(description="")
      x.invariant()
      x = CommandSpec(description="this is a command")
      x.invariant()
    except:
      self.fail("Got unexpected exception")


  @unittest.skip("(#617) Disabled for now,"
    "to add error checking in Spec initializer later.")
  def testInvalidSpec(self):
    with self.assertRaises(Exception):
      _x = Spec()

    with self.assertRaises(Exception):
      _x = Spec(description=3)

    with self.assertRaises(Exception):
      _x = Spec(description="123", singleNodeOnly=3)


  def testValidSpec(self):
    try:
      x = Spec(description="123", singleNodeOnly=True)
      x.invariant()

      x = Spec(description="123", singleNodeOnly=True)
      x.commands = dict(command1=CommandSpec("A command"),
                        command2=CommandSpec("Another command"))
      x.invariant()
    except:
      self.fail("Got unexpected exception")


  def testSpec_toDict(self):
    x = Spec(description="123", singleNodeOnly=True)
    d = x.toDict()
    self.assertEqual(d["description"], "123")
    self.assertTrue(d["singleNodeOnly"])
    self.assertTrue(d["inputs"] == d["outputs"]
                    == d["parameters"] == d["commands"] == {})

    x.inputs = dict(i1=InputSpec(dataType="int"),
                    i2=InputSpec(dataType="str", isDefaultInput=True))
    x.outputs = dict(o=OutputSpec(dataType="float", count=8))
    x.parameters = dict(p=ParameterSpec(description="param",
                                        dataType="float",
                                        defaultValue=3.14,
                                        accessMode="Create"))

    d = x.toDict()
    inputs = d["inputs"]
    self.assertEqual(len(inputs), 2)
    i1 = inputs["i1"]
    self.assertEqual(i1["count"], 1)
    self.assertFalse(i1["isDefaultInput"])
    self.assertEqual(i1["description"], "")
    self.assertEqual(i1["dataType"], "int")
    self.assertFalse(i1["required"])
    self.assertTrue(i1["requireSplitterMap"])
    self.assertFalse(i1["regionLevel"])

    i2 = inputs["i2"]
    self.assertEqual(i2["count"], 1)
    self.assertTrue(i2["isDefaultInput"])
    self.assertEqual(i2["description"], "")
    self.assertEqual(i2["dataType"], "str")
    self.assertFalse(i2["required"])
    self.assertTrue(i2["requireSplitterMap"])
    self.assertFalse(i2["regionLevel"])

    outputs = d["outputs"]
    self.assertEqual(len(outputs), 1)
    o = outputs["o"]
    self.assertEqual(o["count"], 8)
    self.assertFalse(o["isDefaultOutput"])
    self.assertEqual(o["description"], "")
    self.assertEqual(o["dataType"], "float")
    self.assertFalse(o["regionLevel"])

    parameters = d["parameters"]
    self.assertEqual(len(parameters), 1)
    p = parameters["p"]
    self.assertEqual(p["description"], "param")
    self.assertEqual(p["dataType"], "float")
    self.assertEqual(p["accessMode"], "Create")
    self.assertEqual(p["defaultValue"], 3.14)
    self.assertEqual(p["count"], 1)
    self.assertEqual(p["constraints"], "")

    self.assertEqual(d["commands"], {})



if __name__ == "__main__":
  unittest.main()
