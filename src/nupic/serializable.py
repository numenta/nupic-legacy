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

from abc import ABCMeta, abstractmethod



class Serializable(object):
  """ Serializable base class establishing `read()` and `write()` abstract
      methods, `readFromFile()` and `writeToFile()` concrete methods to support
      serialization with Cap'n Proto.
  """


  __metaclass__ = ABCMeta


  @classmethod
  @abstractmethod
  def getCapnpSchema(cls):
    pass  # Not implemented here.  Per abc protocol, attempts to subclass without
    # overriding will fail.


  @classmethod
  @abstractmethod
  def read(cls, proto):
    pass # Not implemented here.  Per abc protocol, attempts to subclass without
         # overriding will fail.


  @abstractmethod
  def write(self, proto):
    pass # Not implemented here.  Per abc protocol, attempts to subclass without
         # overriding will fail.


  @classmethod
  def readFromFile(cls, inp, packed=True):
    # Get capnproto schema from instance
    schema = cls.getCapnpSchema()

    # Read from file
    proto = getattr(schema, "read_packed" if packed else "read")(inp)

    # Return first-class instance initialized from proto obj
    return cls.read(proto)


  def writeToFile(self, outp, packed=True):
    # Get capnproto schema from instance
    schema = self.getCapnpSchema()

    # Construct new message, otherwise refered to as `proto`
    proto = schema.new_message()

    # Populate message w/ `write()` instance method
    self.write(proto)

    # Finally, write to file
    getattr(proto, "write_packed" if packed else "write")(outp)
