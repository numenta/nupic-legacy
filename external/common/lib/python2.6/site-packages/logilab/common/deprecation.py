# copyright 2003-2012 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This file is part of logilab-common.
#
# logilab-common is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option) any
# later version.
#
# logilab-common is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with logilab-common.  If not, see <http://www.gnu.org/licenses/>.
"""Deprecation utilities."""

__docformat__ = "restructuredtext en"

import sys
from warnings import warn

class class_deprecated(type):
    """metaclass to print a warning on instantiation of a deprecated class"""

    def __call__(cls, *args, **kwargs):
        msg = getattr(cls, "__deprecation_warning__",
                      "%(cls)s is deprecated") % {'cls': cls.__name__}
        warn(msg, DeprecationWarning, stacklevel=2)
        return type.__call__(cls, *args, **kwargs)


def class_renamed(old_name, new_class, message=None):
    """automatically creates a class which fires a DeprecationWarning
    when instantiated.

    >>> Set = class_renamed('Set', set, 'Set is now replaced by set')
    >>> s = Set()
    sample.py:57: DeprecationWarning: Set is now replaced by set
      s = Set()
    >>>
    """
    clsdict = {}
    if message is None:
        message = '%s is deprecated, use %s' % (old_name, new_class.__name__)
    clsdict['__deprecation_warning__'] = message
    try:
        # new-style class
        return class_deprecated(old_name, (new_class,), clsdict)
    except (NameError, TypeError):
        # old-style class
        class DeprecatedClass(new_class):
            """FIXME: There might be a better way to handle old/new-style class
            """
            def __init__(self, *args, **kwargs):
                warn(message, DeprecationWarning, stacklevel=2)
                new_class.__init__(self, *args, **kwargs)
        return DeprecatedClass


def class_moved(new_class, old_name=None, message=None):
    """nice wrapper around class_renamed when a class has been moved into
    another module
    """
    if old_name is None:
        old_name = new_class.__name__
    if message is None:
        message = 'class %s is now available as %s.%s' % (
            old_name, new_class.__module__, new_class.__name__)
    return class_renamed(old_name, new_class, message)

def deprecated(reason=None, stacklevel=2, name=None, doc=None):
    """Decorator that raises a DeprecationWarning to print a message
    when the decorated function is called.
    """
    def deprecated_decorator(func):
        message = reason or 'The function "%s" is deprecated'
        if '%s' in message:
            message = message % func.func_name
        def wrapped(*args, **kwargs):
            warn(message, DeprecationWarning, stacklevel=stacklevel)
            return func(*args, **kwargs)
        try:
            wrapped.__name__ = name or func.__name__
        except TypeError: # readonly attribute in 2.3
            pass
        wrapped.__doc__ = doc or func.__doc__
        return wrapped
    return deprecated_decorator

def moved(modpath, objname):
    """use to tell that a callable has been moved to a new module.

    It returns a callable wrapper, so that when its called a warning is printed
    telling where the object can be found, import is done (and not before) and
    the actual object is called.

    NOTE: the usage is somewhat limited on classes since it will fail if the
    wrapper is use in a class ancestors list, use the `class_moved` function
    instead (which has no lazy import feature though).
    """
    def callnew(*args, **kwargs):
        from logilab.common.modutils import load_module_from_name
        message = "object %s has been moved to module %s" % (objname, modpath)
        warn(message, DeprecationWarning, stacklevel=2)
        m = load_module_from_name(modpath)
        return getattr(m, objname)(*args, **kwargs)
    return callnew



class DeprecationWrapper(object):
    """proxy to print a warning on access to any attribute of the wrapped object
    """
    def __init__(self, proxied, msg=None):
        self._proxied = proxied
        self._msg = msg

    def __getattr__(self, attr):
        warn(self._msg, DeprecationWarning, stacklevel=2)
        return getattr(self._proxied, attr)

    def __setattr__(self, attr, value):
        if attr in ('_proxied', '_msg'):
            self.__dict__[attr] = value
        else:
            warn(self._msg, DeprecationWarning, stacklevel=2)
            setattr(self._proxied, attr, value)
