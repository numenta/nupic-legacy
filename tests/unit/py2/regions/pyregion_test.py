#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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

import unittest2 as unittest

from nupic.regions.PyRegion import PyRegion



# Classes used for testing

class X(PyRegion):
  def __init__(self):
    self.x = 5



class Y(PyRegion):
  def __init__(self):
    self.zzz = 5
    self._zzz = 3
  def initialize(self): pass
  def compute(self): pass
  def getOutputElementCount(self): pass



class Z(object):
  def __init__(self):
    y = Y()
    y.setParameter('zzz, 4')



class PyRegionTest(unittest.TestCase):


  def testNoInit(self):
    """Test unimplemented init method"""
    class NoInit(PyRegion):
      pass

    with self.assertRaises(TypeError) as cw:
      _ni = NoInit()

    self.assertEqual(str(cw.exception), "Can't instantiate abstract class " +
      "NoInit with abstract methods __init__, compute, initialize")


  def testUnimplementedAbstractMethods(self):
    """Test unimplemented abstract methods"""
    # Test unimplemented getSpec (results in NotImplementedError)
    with self.assertRaises(NotImplementedError):
      X.getSpec()

    # Test unimplemented abstract methods (x can't be instantiated)
    with self.assertRaises(TypeError) as cw:
      _x = X()

    self.assertEqual(str(cw.exception), "Can't instantiate abstract class " +
      "X with abstract methods compute, initialize")

  def testUnimplementedNotImplementedMethods(self):
    """Test unimplemented @not_implemented methods"""
    # Can instantiate because all abstract methods are implemented
    y = Y()

    # Can call the default getParameter() from PyRegion
    self.assertEqual(y.getParameter('zzz', -1), 5)

    # Accessing an attribute whose name starts with '_' via getParameter()
    with self.assertRaises(Exception) as cw:
      _ = y.getParameter('_zzz', -1) == 5

    self.assertEqual(str(cw.exception), "Parameter name must not " +
      "start with an underscore")

    # Calling not implemented method result in NotImplementedError
    with self.assertRaises(NotImplementedError) as cw:
      y.setParameter('zzz', 4, 5)

    self.assertEqual(str(cw.exception), "The unimplemented method " +
      "setParameter() was called by " +
      "PyRegionTest.testUnimplementedNotImplementedMethods()")

  def testCallUnimplementedMethod(self):
    """Test calling an unimplemented method"""
    with self.assertRaises(NotImplementedError) as cw:
      _z = Z()

    self.assertEqual(str(cw.exception), "The unimplemented method " +
      "setParameter() was called by Z.__init__()")



if __name__ == "__main__":
  unittest.main()
