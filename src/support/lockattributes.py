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
import os

# This is the environment variable that controls the lock attributes
# enforcement.
#
# The lock attributes machinery is engaged by default. To deactivate it
# define this environment variabe. The benefit is that there will be no runtime
# overhead (Except for a one-time check when classes that derive from
# LockAttributesMixin are defined or methods decorated with
# _canAddAttributes are defined).
deactivation_key = 'NTA_DONT_USE_LOCK_ATTRIBUTES'

def _allow_new_attributes(f):
  """A decorator that maintains the attribute lock state of an object

  It coperates with the LockAttributesMetaclass (see bellow) that replaces
  the __setattr__ method with a custom one that checks the _canAddAttributes
  counter and allows setting new attributes only if _canAddAttributes > 0.

  New attributes can be set only from methods decorated
  with this decorator (should be only __init__ and __setstate__ normally)

  The decorator is reentrant (e.g. if from inside a decorated function another
  decorated function is invoked). Before invoking the target function it
  increments the counter (or sets it to 1). After invoking the target function
  it decrements the counter and if it's 0 it removed the counter.
  """
  def decorated(self, *args, **kw):
    """The decorated function that replaces __init__() or __setstate__()

    """
    # Run the original function
    if not hasattr(self, '_canAddAttributes'):
      self.__dict__['_canAddAttributes'] = 1
    else:
      self._canAddAttributes += 1
    assert self._canAddAttributes >= 1

    # Save add attribute counter
    count = self._canAddAttributes
    f(self, *args, **kw)

    # Restore _CanAddAttributes if deleted from dict (can happen in __setstte__)
    if hasattr(self, '_canAddAttributes'):
      self._canAddAttributes -= 1
    else:
      self._canAddAttributes = count - 1

    assert self._canAddAttributes >= 0
    if self._canAddAttributes == 0:
      del self._canAddAttributes

  decorated.__doc__ = f.__doc__
  decorated.__name__ = f.__name__
  return decorated

def _simple_init(self, *args, **kw):
  """trivial init method that just calls base class's __init__()

  This method is attached to classes that don't define __init__(). It is needed
  because LockAttributesMetaclass must decorate the __init__() method of
  its target class.
  """
  type(self).__base__.__init__(self, *args, **kw)

class LockAttributesMetaclass(type):
  """This metaclass makes objects attribute-locked by decorating their
  __init__() and __setstate__() methods with the _allow_new_attributes
  decorator.

  It doesn't do anything unless the environment variable
  'NTA_USE_LOCK_ATTRIBUTES' is defined.
  That allows for verifying proper usage during testing and skipping
  it in production code (that was verified during testing) to avoid the cost
  of verifying every attribute setting.

  It also replaces the __setattr__ magic method with a custom one that verifies
  new attributes are set only in code that originates from a decorated method
  (normally __init__() or __setstate__()).

  If the target class has no __init__() method it adds a trivial __init__()
  method to provide a hook for the decorator (the _simple_init()
  function defined above)
  """
  def __init__(cls, name, bases, dict):
    """
    """
    def custom_setattr(self, name, value):
      """A custom replacement for __setattr__

      Allows setting only exisitng attributes. It is designed to work
      with the _allow_new_attributes decorator.

      It works is by checking if the requested attribute is already in the
      __dict__ or if the _canAddAttributes counter > 0. Otherwise it raises an
      exception.
      If all is well it calls the original __setattr__. This means it can work
      also with classes that already have custom __setattr__
      """
      if (name == '_canAddAttributes' or
         (hasattr(self, '_canAddAttributes') and self._canAddAttributes > 0) or
         hasattr(self, name)):
        return self._original_setattr(name, value)
      else:
        #from dbgp.client import brk; brk(port=9029)
        raise Exception('Attempting to set a new attribute: ' + name)


    # Bail out if not active. Zero overhead other than this one-time check
    # at class definition time
    if deactivation_key in os.environ:
      return

    # Initialize the super-class
    super(LockAttributesMetaclass, cls).__init__(name, bases, dict)

    # Store and replace the __setattr__ with the custom one (if needed)
    if not hasattr(cls, '_original_setattr'):
      cls._original_setattr = cls.__setattr__
      cls.__setattr__ = custom_setattr


    # Keep the original __init__ if exists. This was needed for NuPIC 1. Remove?
    if '__init__' in dict:
      setattr(cls, '_original_init', dict['__init__'])


    # Get the __init__ and __setstate__ form the target class's dict
    # If there is no __init__ use _simple_init (it's Ok if there is no
    #__setstate__)
    methods = [('__init__', dict.get('__init__', _simple_init)),
               ('__setstate__', dict.get('__setstate__', None))]

    # Wrap the methods with _allow_new_attributes decorator
    for name, method in methods:
      if method is not None:
        setattr(cls, name, _allow_new_attributes(method))

class LockAttributesMixin(object):
  """This class serves as a base (or mixin) for classes that want to enforce
  the locked attributes pattern (all attributes should be defined in __init__()
  or __setstate__().

  All the target class has to do add LockAttributesMixin as one of its bases
  (inherit from it).

  The metaclass will be activated when the application class is created
  and the lock attributes machinery will be injected (unless the
  deactivation_key is defined in the environment)
  """
  __metaclass__ = LockAttributesMetaclass
