# Copyright 2017 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

from abc import ABCMeta, abstractmethod



class Serializable(object):
  """
  Serializable base class establishing
  :meth:`~nupic.serializable.Serializable.read` and
  :meth:`~nupic.serializable.Serializable.write` abstract methods,
  :meth:`.readFromFile` and :meth:`.writeToFile` concrete methods to support
  serialization with Cap'n Proto.
  """

  __metaclass__ = ABCMeta


  @classmethod
  @abstractmethod
  def getSchema(cls):
    """
    Get Cap'n Proto schema.

    ..warning: This is an abstract method.  Per abc protocol, attempts to subclass
               without overriding will fail.

    @returns Cap'n Proto schema
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

    .. warning: This is an abstract method.  Per abc protocol, attempts to
                subclass without overriding will fail.

    :param proto: Cap'n Proto obj
    """
    pass


  @classmethod
  def readFromFile(cls, f, packed=True):
    """
    Read serialized object from file.

    :param f: input file
    :param packed: If true, will assume content is packed
    :return: first-class instance initialized from proto obj
    """
    # Get capnproto schema from instance
    schema = cls.getSchema()

    # Read from file
    if packed:
      proto = schema.read_packed(f)
    else:
      proto = schema.read(f)

    # Return first-class instance initialized from proto obj
    return cls.read(proto)


  def writeToFile(self, f, packed=True):
    """
    Write serialized object to file.

    :param f: output file
    :param packed: If true, will pack contents.
    """
    # Get capnproto schema from instance
    schema = self.getSchema()

    # Construct new message, otherwise refered to as `proto`
    proto = schema.new_message()

    # Populate message w/ `write()` instance method
    self.write(proto)

    # Finally, write to file
    if packed:
      proto.write_packed(f)
    else:
      proto.write(f)
