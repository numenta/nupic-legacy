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

import unittest2 as unittest

from nupic.regions.PyRegion import PyRegion



class PyRegionTest(unittest.TestCase):


  def testClass(self):
    class NoInit(PyRegion):
      pass

    try:
      ni = NoInit()
    except TypeError, e:
      assert str(e) == "Can't instantiate abstract class NoInit with abstract methods __init__, compute, initialize"

    class X(PyRegion):
      def __init__(self):
        self.x = 5

    # Test unimplemented getSpec (results in NotImplementedError)
    try:
      X.getSpec()
      assert False
    except NotImplementedError:
      pass

    # Test unimplemented abstract methods (x can't be instantiated)
    try:
      x = X()
    except TypeError, e:
      assert str(e) == "Can't instantiate abstract class X with abstract methods compute, initialize"

    # Test unimplemented @not_implemented methods
    class Y(PyRegion):
      def __init__(self):
        self.zzz = 5
        self._zzz = 3
      def initialize(self): pass
      def compute(self): pass
      def getOutputElementCount(self): pass

    # Can instantiate because all abstract methods are implemented
    y = Y()

    # Can call the default getParameter() from PyRegion
    assert y.getParameter('zzz', -1) == 5

    # Accessing an attribute whose name starts with '_' via getParameter()
    try:
      y.getParameter('_zzz', -1) == 5
      assert False
    except Exception, e:
      assert str(e) == 'Parameter name must not start with an underscore'

    # Calling not implemented method result in NotImplementedError
    try:
      y.setParameter('zzz', 4)
      assert False
    except NotImplementedError, e:
      assert str(e) == \
      'The unimplemented method setParameter() was called by PyRegionTest.testClass()'

    class Z(object):
      def __init__(self):
        y = Y()
        y.setParameter('zzz, 4')

    try:
      z = Z()
    except NotImplementedError, e:
      assert str(e) == \
      'The unimplemented method setParameter() was called by Z.__init__()'



if __name__ == '__main__':
  unittest.main()
