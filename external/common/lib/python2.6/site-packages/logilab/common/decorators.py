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
""" A few useful function/method decorators. """
__docformat__ = "restructuredtext en"

import sys
import types
from time import clock, time

from logilab.common.compat import callable, method_type

# XXX rewrite so we can use the decorator syntax when keyarg has to be specified

def _is_generator_function(callableobj):
    return callableobj.func_code.co_flags & 0x20

class cached_decorator(object):
    def __init__(self, cacheattr=None, keyarg=None):
        self.cacheattr = cacheattr
        self.keyarg = keyarg
    def __call__(self, callableobj=None):
        assert not _is_generator_function(callableobj), \
               'cannot cache generator function: %s' % callableobj
        if callableobj.func_code.co_argcount == 1 or self.keyarg == 0:
            cache = _SingleValueCache(callableobj, self.cacheattr)
        elif self.keyarg:
            cache = _MultiValuesKeyArgCache(callableobj, self.keyarg, self.cacheattr)
        else:
            cache = _MultiValuesCache(callableobj, self.cacheattr)
        return cache.closure()

class _SingleValueCache(object):
    def __init__(self, callableobj, cacheattr=None):
        self.callable = callableobj
        if cacheattr is None:
            self.cacheattr = '_%s_cache_' % callableobj.__name__
        else:
            assert cacheattr != callableobj.__name__
            self.cacheattr = cacheattr

    def __call__(__me, self, *args):
        try:
            return self.__dict__[__me.cacheattr]
        except KeyError:
            value = __me.callable(self, *args)
            setattr(self, __me.cacheattr, value)
            return value

    def closure(self):
        def wrapped(*args, **kwargs):
            return self.__call__(*args, **kwargs)
        wrapped.cache_obj = self
        try:
            wrapped.__doc__ = self.callable.__doc__
            wrapped.__name__ = self.callable.__name__
            wrapped.func_name = self.callable.func_name
        except:
            pass
        return wrapped

    def clear(self, holder):
        holder.__dict__.pop(self.cacheattr, None)


class _MultiValuesCache(_SingleValueCache):
    def _get_cache(self, holder):
        try:
            _cache = holder.__dict__[self.cacheattr]
        except KeyError:
            _cache = {}
            setattr(holder, self.cacheattr, _cache)
        return _cache

    def __call__(__me, self, *args, **kwargs):
        _cache = __me._get_cache(self)
        try:
            return _cache[args]
        except KeyError:
            _cache[args] = __me.callable(self, *args)
            return _cache[args]

class _MultiValuesKeyArgCache(_MultiValuesCache):
    def __init__(self, callableobj, keyarg, cacheattr=None):
        super(_MultiValuesKeyArgCache, self).__init__(callableobj, cacheattr)
        self.keyarg = keyarg

    def __call__(__me, self, *args, **kwargs):
        _cache = __me._get_cache(self)
        key = args[__me.keyarg-1]
        try:
            return _cache[key]
        except KeyError:
            _cache[key] = __me.callable(self, *args, **kwargs)
            return _cache[key]


def cached(callableobj=None, keyarg=None, **kwargs):
    """Simple decorator to cache result of method call."""
    kwargs['keyarg'] = keyarg
    decorator = cached_decorator(**kwargs)
    if callableobj is None:
        return decorator
    else:
        return decorator(callableobj)


class cachedproperty(object):
    """ Provides a cached property equivalent to the stacking of
    @cached and @property, but more efficient.

    After first usage, the <property_name> becomes part of the object's
    __dict__. Doing:

      del obj.<property_name> empties the cache.

    Idea taken from the pyramid_ framework and the mercurial_ project.

    .. _pyramid: http://pypi.python.org/pypi/pyramid
    .. _mercurial: http://pypi.python.org/pypi/Mercurial
    """
    __slots__ = ('wrapped',)

    def __init__(self, wrapped):
        try:
            wrapped.__name__
        except AttributeError:
            raise TypeError('%s must have a __name__ attribute' %
                            wrapped)
        self.wrapped = wrapped

    @property
    def __doc__(self):
        doc = getattr(self.wrapped, '__doc__', None)
        return ('<wrapped by the cachedproperty decorator>%s'
                % ('\n%s' % doc if doc else ''))

    def __get__(self, inst, objtype=None):
        if inst is None:
            return self
        val = self.wrapped(inst)
        setattr(inst, self.wrapped.__name__, val)
        return val


def get_cache_impl(obj, funcname):
    cls = obj.__class__
    member = getattr(cls, funcname)
    if isinstance(member, property):
        member = member.fget
    return member.cache_obj

def clear_cache(obj, funcname):
    """Clear a cache handled by the :func:`cached` decorator. If 'x' class has
    @cached on its method `foo`, type

    >>> clear_cache(x, 'foo')

    to purge this method's cache on the instance.
    """
    get_cache_impl(obj, funcname).clear(obj)

def copy_cache(obj, funcname, cacheobj):
    """Copy cache for <funcname> from cacheobj to obj."""
    cacheattr = get_cache_impl(obj, funcname).cacheattr
    try:
        setattr(obj, cacheattr, cacheobj.__dict__[cacheattr])
    except KeyError:
        pass


class wproperty(object):
    """Simple descriptor expecting to take a modifier function as first argument
    and looking for a _<function name> to retrieve the attribute.
    """
    def __init__(self, setfunc):
        self.setfunc = setfunc
        self.attrname = '_%s' % setfunc.__name__

    def __set__(self, obj, value):
        self.setfunc(obj, value)

    def __get__(self, obj, cls):
        assert obj is not None
        return getattr(obj, self.attrname)


class classproperty(object):
    """this is a simple property-like class but for class attributes.
    """
    def __init__(self, get):
        self.get = get
    def __get__(self, inst, cls):
        return self.get(cls)


class iclassmethod(object):
    '''Descriptor for method which should be available as class method if called
    on the class or instance method if called on an instance.
    '''
    def __init__(self, func):
        self.func = func
    def __get__(self, instance, objtype):
        if instance is None:
            return method_type(self.func, objtype, objtype.__class__)
        return method_type(self.func, instance, objtype)
    def __set__(self, instance, value):
        raise AttributeError("can't set attribute")


def timed(f):
    def wrap(*args, **kwargs):
        t = time()
        c = clock()
        res = f(*args, **kwargs)
        print '%s clock: %.9f / time: %.9f' % (f.__name__,
                                               clock() - c, time() - t)
        return res
    return wrap


def locked(acquire, release):
    """Decorator taking two methods to acquire/release a lock as argument,
    returning a decorator function which will call the inner method after
    having called acquire(self) et will call release(self) afterwards.
    """
    def decorator(f):
        def wrapper(self, *args, **kwargs):
            acquire(self)
            try:
                return f(self, *args, **kwargs)
            finally:
                release(self)
        return wrapper
    return decorator


def monkeypatch(klass, methodname=None):
    """Decorator extending class with the decorated callable
    >>> class A:
    ...     pass
    >>> @monkeypatch(A)
    ... def meth(self):
    ...     return 12
    ...
    >>> a = A()
    >>> a.meth()
    12
    >>> @monkeypatch(A, 'foo')
    ... def meth(self):
    ...     return 12
    ...
    >>> a.foo()
    12
    """
    def decorator(func):
        try:
            name = methodname or func.__name__
        except AttributeError:
            raise AttributeError('%s has no __name__ attribute: '
                                 'you should provide an explicit `methodname`'
                                 % func)
        if callable(func):
            if sys.version_info < (3, 0):
                setattr(klass, name, method_type(func, None, klass))
            #elif  isinstance(func, types.FunctionType):
            else:
                setattr(klass, name, func)
            #else:
            #    setattr(klass, name, UnboundMethod(func))
        else:
            # likely a property
            # this is quite borderline but usage already in the wild ...
            setattr(klass, name, func)
        return func
    return decorator

if sys.version_info >= (3, 0):
    class UnboundMethod(object):
        """unbound method wrapper necessary for python3 where we can't turn
        arbitrary object (eg class implementing __call__) into a method, as
        there is no more unbound method and only function are turned
        automatically to method when accessed through an instance.
        """
        __slots__ = ('_callable',)

        def __init__(self, callable):
            self._callable = callable

        def __get__(self, instance, objtype):
            if instance is None:
                return self._callable
            return types.MethodType(self._callable, instance)
