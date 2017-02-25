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
  def getSchema(cls):
    """
    Get Cap'n Proto schema

    Note: This is an abstract method.  Per abc protocol, attempts to subclass
    without overriding will fail.
    """
    pass


  @classmethod
  @abstractmethod
  def read(cls, proto):
    """
    Create a new object initialized from Cap'n Proto obj.

    Note: This is an abstract method.  Per abc protocol, attempts to subclass
    without overriding will fail.

    :param proto: Cap'n Proto obj
    :return: Obj initialized from proto
    """
    pass


  @abstractmethod
  def write(self, proto):
    """
    Write obj instance to Cap'n Proto object

    Note: This is an abstract method.  Per abc protocol, attempts to subclass
    without overriding will fail.

    :param proto: Cap'n Proto obj
    """
    pass


  @classmethod
  def readFromFile(cls, inp, packed=True):
    # Get capnproto schema from instance
    schema = cls.getSchema()

    # Read from file
    if packed:
      proto = schema.read_packed(inp)
    else:
      proto = schema.read(inp)

    # Return first-class instance initialized from proto obj
    return cls.read(proto)


  def writeToFile(self, outp, packed=True):
    # Get capnproto schema from instance
    schema = self.getSchema()

    # Construct new message, otherwise refered to as `proto`
    proto = schema.new_message()

    # Populate message w/ `write()` instance method
    self.write(proto)

    # Finally, write to file
    if packed:
      proto.write_packed(outp)
    else:
      proto.write(outp)
