# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2017, Numenta, Inc.  Unless you have an agreement
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

import os
import unittest

try:
  import capnp
  import serializable_test_capnp
except ImportError:
  # Ignore for platforms in which capnp is not available, e.g. windows
  capnp = None

from nupic.serializable import  Serializable



@unittest.skipUnless(capnp, "Capnp not available.")
class SerializableTest(unittest.TestCase):

  def testABCProtocolEnforced(self):

    class Foo(Serializable):
      pass # read(), write(), getCapnpSchema() not implemented here

    with self.assertRaises(TypeError):
      Foo()


  def testReadFromAndWriteToFile(self):
    """ Test generic usage of serializable mixin class """

    class Bar(object):
      pass


    class Foo(Bar, Serializable):


      def __init__(self, bar):
        self.bar = bar


      @classmethod
      def getSchema(cls):
        return serializable_test_capnp.Foo


      @classmethod
      def read(cls, proto):
        foo = object.__new__(cls)
        foo.bar = proto.bar
        return foo


      def write(self, proto):
        proto.bar = self.bar

    def _remove(fname):
      if os.path.isfile(fname):
        os.remove(fname)

    self.addCleanup(_remove, "foo.data")

    with open("foo.data", "wb") as outp:
      Foo("bar").writeToFile(outp)

    with open("foo.data", "rb") as inp:
      self.assertEqual(Foo.readFromFile(inp).bar, "bar")
