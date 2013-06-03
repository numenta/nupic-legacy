# copyright 2003-2012 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This file is part of Logilab-common.
#
# Logilab-common is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 2.1 of the License, or (at your
# option) any later version.
#
# Logilab-common is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with Logilab-common.  If not, see <http://www.gnu.org/licenses/>.
"""This module provides bases for predicates dispatching (the pattern in use
here is similar to what's refered as multi-dispatch or predicate-dispatch in the
literature, though a bit different since the idea is to select across different
implementation 'e.g. classes), not to dispatch a message to a function or
method. It contains the following classes:

* :class:`RegistryStore`, the top level object which loads implementation
  objects and stores them into registries. You'll usually use it to access
  registries and their contained objects;

* :class:`Registry`, the base class which contains objects semantically grouped
  (for instance, sharing a same API, hence the 'implementation' name). You'll
  use it to select the proper implementation according to a context. Notice you
  may use registries on their own without using the store.

.. Note::

  implementation objects are usually designed to be accessed through the
  registry and not by direct instantiation, besides to use it as base classe.

The selection procedure is delegated to a selector, which is responsible for
scoring the object according to some context. At the end of the selection, if an
implementation has been found, an instance of this class is returned. A selector
is built from one or more predicates combined together using AND, OR, NOT
operators (actually `&`, `|` and `~`). You'll thus find some base classes to
build predicates:

* :class:`Predicate`, the abstract base predicate class

* :class:`AndPredicate`, :class:`OrPredicate`, :class:`NotPredicate`, which you
  shouldn't have to use directly. You'll use `&`, `|` and '~' operators between
  predicates directly

* :func:`objectify_predicate`

You'll eventually find one concrete predicate: :class:`yes`

.. autoclass:: RegistryStore
.. autoclass:: Registry

Predicates
----------
.. autoclass:: Predicate
.. autofunc:: objectify_predicate
.. autoclass:: yes

Debugging
---------
.. autoclass:: traced_selection

Exceptions
----------
.. autoclass:: RegistryException
.. autoclass:: RegistryNotFound
.. autoclass:: ObjectNotFound
.. autoclass:: NoSelectableObject
"""

__docformat__ = "restructuredtext en"

import sys
import types
import weakref
import traceback as tb
from os import listdir, stat
from os.path import join, isdir, exists
from logging import getLogger
from warnings import warn

from logilab.common.modutils import modpath_from_file
from logilab.common.logging_ext import set_log_methods
from logilab.common.decorators import classproperty


class RegistryException(Exception):
    """Base class for registry exception."""

class RegistryNotFound(RegistryException):
    """Raised when an unknown registry is requested.

    This is usually a programming/typo error.
    """

class ObjectNotFound(RegistryException):
    """Raised when an unregistered object is requested.

    This may be a programming/typo or a misconfiguration error.
    """

class NoSelectableObject(RegistryException):
    """Raised when no object is selectable for a given context."""
    def __init__(self, args, kwargs, objects):
        self.args = args
        self.kwargs = kwargs
        self.objects = objects

    def __str__(self):
        return ('args: %s, kwargs: %s\ncandidates: %s'
                % (self.args, self.kwargs.keys(), self.objects))


def _modname_from_path(path, extrapath=None):
    modpath = modpath_from_file(path, extrapath)
    # omit '__init__' from package's name to avoid loading that module
    # once for each name when it is imported by some other object
    # module. This supposes import in modules are done as::
    #
    #   from package import something
    #
    # not::
    #
    #   from package.__init__ import something
    #
    # which seems quite correct.
    if modpath[-1] == '__init__':
        modpath.pop()
    return '.'.join(modpath)


def _toload_info(path, extrapath, _toload=None):
    """Return a dictionary of <modname>: <modpath> and an ordered list of
    (file, module name) to load
    """
    if _toload is None:
        assert isinstance(path, list)
        _toload = {}, []
    for fileordir in path:
        if isdir(fileordir) and exists(join(fileordir, '__init__.py')):
            subfiles = [join(fileordir, fname) for fname in listdir(fileordir)]
            _toload_info(subfiles, extrapath, _toload)
        elif fileordir[-3:] == '.py':
            modname = _modname_from_path(fileordir, extrapath)
            _toload[0][modname] = fileordir
            _toload[1].append((fileordir, modname))
    return _toload


class RegistrableObject(object):
    """This is the base class for registrable objects which are selected
    according to a context.

    :attr:`__registry__`
      name of the registry for this object (string like 'views',
      'templates'...). You may want to define `__registries__` directly if your
      object should be registered in several registries.

    :attr:`__regid__`
      object's identifier in the registry (string like 'main',
      'primary', 'folder_box')

    :attr:`__select__`
      class'selector

    Moreover, the `__abstract__` attribute may be set to True to indicate that a
    class is abstract and should not be registered.

    You don't have to inherit from this class to put it in a registry (having
    `__regid__` and `__select__` is enough), though this is needed for classes
    that should be automatically registered.
    """

    __registry__ = None
    __regid__ = None
    __select__ = None
    __abstract__ = True # see doc snipppets below (in Registry class)

    @classproperty
    def __registries__(cls):
        if cls.__registry__ is None:
            return ()
        return (cls.__registry__,)


class RegistrableInstance(RegistrableObject):
    """Inherit this class if you want instances of the classes to be
    automatically registered.
    """

    def __new__(cls, *args, **kwargs):
        """Add a __module__ attribute telling the module where the instance was
        created, for automatic registration.
        """
        obj = super(RegistrableInstance, cls).__new__(cls)
        # XXX subclass must no override __new__
        filepath = tb.extract_stack(limit=2)[0][0]
        obj.__module__ = _modname_from_path(filepath)
        return obj


class Registry(dict):
    """The registry store a set of implementations associated to identifier:

    * to each identifier are associated a list of implementations

    * to select an implementation of a given identifier, you should use one of the
      :meth:`select` or :meth:`select_or_none` method

    * to select a list of implementations for a context, you should use the
      :meth:`possible_objects` method

    * dictionary like access to an identifier will return the bare list of
      implementations for this identifier.

    To be usable in a registry, the only requirement is to have a `__select__`
    attribute.

    At the end of the registration process, the :meth:`__registered__`
    method is called on each registered object which have them, given the
    registry in which it's registered as argument.

    Registration methods:

    .. automethod: register
    .. automethod: unregister

    Selection methods:

    .. automethod: select
    .. automethod: select_or_none
    .. automethod: possible_objects
    .. automethod: object_by_id
    """
    def __init__(self, debugmode):
        super(Registry, self).__init__()
        self.debugmode = debugmode

    def __getitem__(self, name):
        """return the registry (list of implementation objects) associated to
        this name
        """
        try:
            return super(Registry, self).__getitem__(name)
        except KeyError:
            raise ObjectNotFound(name), None, sys.exc_info()[-1]

    @classmethod
    def objid(cls, obj):
        """returns a unique identifier for an object stored in the registry"""
        return '%s.%s' % (obj.__module__, cls.objname(obj))

    @classmethod
    def objname(cls, obj):
        """returns a readable name for an object stored in the registry"""
        return getattr(obj, '__name__', id(obj))

    def initialization_completed(self):
        """call method __registered__() on registered objects when the callback
        is defined"""
        for objects in self.itervalues():
            for objectcls in objects:
                registered = getattr(objectcls, '__registered__', None)
                if registered:
                    registered(self)
        if self.debugmode:
            wrap_predicates(_lltrace)

    def register(self, obj, oid=None, clear=False):
        """base method to add an object in the registry"""
        assert not '__abstract__' in obj.__dict__, obj
        assert obj.__select__, obj
        oid = oid or obj.__regid__
        assert oid, ('no explicit name supplied to register object %s, '
                     'which has no __regid__ set' % obj)
        if clear:
            objects = self[oid] =  []
        else:
            objects = self.setdefault(oid, [])
        assert not obj in objects, 'object %s is already registered' % obj
        objects.append(obj)

    def register_and_replace(self, obj, replaced):
        """remove <replaced> and register <obj>"""
        # XXXFIXME this is a duplication of unregister()
        # remove register_and_replace in favor of unregister + register
        # or simplify by calling unregister then register here
        if not isinstance(replaced, basestring):
            replaced = self.objid(replaced)
        # prevent from misspelling
        assert obj is not replaced, 'replacing an object by itself: %s' % obj
        registered_objs = self.get(obj.__regid__, ())
        for index, registered in enumerate(registered_objs):
            if self.objid(registered) == replaced:
                del registered_objs[index]
                break
        else:
            self.warning('trying to replace %s that is not registered with %s',
                         replaced, obj)
        self.register(obj)

    def unregister(self, obj):
        """remove object <obj> from this registry"""
        objid = self.objid(obj)
        oid = obj.__regid__
        for registered in self.get(oid, ()):
            # use self.objid() to compare objects because vreg will probably
            # have its own version of the object, loaded through execfile
            if self.objid(registered) == objid:
                self[oid].remove(registered)
                break
        else:
            self.warning('can\'t remove %s, no id %s in the registry',
                         objid, oid)

    def all_objects(self):
        """return a list containing all objects in this registry.
        """
        result = []
        for objs in self.values():
            result += objs
        return result

    # dynamic selection methods ################################################

    def object_by_id(self, oid, *args, **kwargs):
        """return object with the `oid` identifier. Only one object is expected
        to be found.

        raise :exc:`ObjectNotFound` if not object with id <oid> in <registry>

        raise :exc:`AssertionError` if there is more than one object there
        """
        objects = self[oid]
        assert len(objects) == 1, objects
        return objects[0](*args, **kwargs)

    def select(self, __oid, *args, **kwargs):
        """return the most specific object among those with the given oid
        according to the given context.

        raise :exc:`ObjectNotFound` if not object with id <oid> in <registry>

        raise :exc:`NoSelectableObject` if not object apply
        """
        obj =  self._select_best(self[__oid], *args, **kwargs)
        if obj is None:
            raise NoSelectableObject(args, kwargs, self[__oid] )
        return obj

    def select_or_none(self, __oid, *args, **kwargs):
        """return the most specific object among those with the given oid
        according to the given context, or None if no object applies.
        """
        try:
            return self.select(__oid, *args, **kwargs)
        except (NoSelectableObject, ObjectNotFound):
            return None

    def possible_objects(self, *args, **kwargs):
        """return an iterator on possible objects in this registry for the given
        context
        """
        for objects in self.itervalues():
            obj = self._select_best(objects,  *args, **kwargs)
            if obj is None:
                continue
            yield obj

    def _select_best(self, objects, *args, **kwargs):
        """return an instance of the most specific object according
        to parameters

        return None if not object apply (don't raise `NoSelectableObject` since
        it's costly when searching objects using `possible_objects`
        (e.g. searching for hooks).
        """
        score, winners = 0, None
        for obj in objects:
            objectscore = obj.__select__(obj, *args, **kwargs)
            if objectscore > score:
                score, winners = objectscore, [obj]
            elif objectscore > 0 and objectscore == score:
                winners.append(obj)
        if winners is None:
            return None
        if len(winners) > 1:
            # log in production environement / test, error while debugging
            msg = 'select ambiguity: %s\n(args: %s, kwargs: %s)'
            if self.debugmode:
                # raise bare exception in debug mode
                raise Exception(msg % (winners, args, kwargs.keys()))
            self.error(msg, winners, args, kwargs.keys())
        # return the result of calling the object
        return self.selected(winners[0], args, kwargs)

    def selected(self, winner, args, kwargs):
        """override here if for instance you don't want "instanciation"
        """
        return winner(*args, **kwargs)

    # these are overridden by set_log_methods below
    # only defining here to prevent pylint from complaining
    info = warning = error = critical = exception = debug = lambda msg, *a, **kw: None


def obj_registries(cls, registryname=None):
    """return a tuple of registry names (see __registries__)"""
    if registryname:
        return (registryname,)
    return cls.__registries__


class RegistryStore(dict):
    """This class is responsible for loading objects and storing them
    in their registry which is created on the fly as needed.

    It handles dynamic registration of objects and provides a
    convenient api to access them. To be recognized as an object that
    should be stored into one of the store's registry
    (:class:`Registry`), an object must provide the following
    attributes, used control how they interact with the registry:

    :attr:`__registries__`
      list of registry names (string like 'views', 'templates'...) into which
      the object should be registered

    :attr:`__regid__`
      object identifier in the registry (string like 'main',
      'primary', 'folder_box')

    :attr:`__select__`
      the object predicate selectors

    Moreover, the :attr:`__abstract__` attribute may be set to `True`
    to indicate that an object is abstract and should not be registered
    (such inherited attributes not considered).

    .. Note::

      When using the store to load objects dynamically, you *always* have
      to use **super()** to get the methods and attributes of the
      superclasses, and not use the class identifier. If not, you'll get into
      trouble at reload time.

      For example, instead of writing::

          class Thing(Parent):
              __regid__ = 'athing'
              __select__ = yes()

              def f(self, arg1):
                  Parent.f(self, arg1)

      You must write::

          class Thing(Parent):
              __regid__ = 'athing'
              __select__ = yes()

              def f(self, arg1):
                  super(Thing, self).f(arg1)

    Controlling object registration
    -------------------------------

    Dynamic loading is triggered by calling the
    :meth:`register_objects` method, given a list of directories to
    inspect for python modules.

    .. automethod: register_objects

    For each module, by default, all compatible objects are registered
    automatically. However if some objects come as replacement of
    other objects, or have to be included only if some condition is
    met, you'll have to define a `registration_callback(vreg)`
    function in the module and explicitly register **all objects** in
    this module, using the api defined below.


    .. automethod:: RegistryStore.register_all
    .. automethod:: RegistryStore.register_and_replace
    .. automethod:: RegistryStore.register
    .. automethod:: RegistryStore.unregister

    .. Note::
        Once the function `registration_callback(vreg)` is implemented in a
        module, all the objects from this module have to be explicitly
        registered as it disables the automatic object registration.


    Examples:

    .. sourcecode:: python

       def registration_callback(store):
          # register everything in the module except BabarClass
          store.register_all(globals().values(), __name__, (BabarClass,))

          # conditionally register BabarClass
          if 'babar_relation' in store.schema:
              store.register(BabarClass)

    In this example, we register all application object classes defined in the module
    except `BabarClass`. This class is then registered only if the 'babar_relation'
    relation type is defined in the instance schema.

    .. sourcecode:: python

       def registration_callback(store):
          store.register(Elephant)
          # replace Babar by Celeste
          store.register_and_replace(Celeste, Babar)

    In this example, we explicitly register classes one by one:

    * the `Elephant` class
    * the `Celeste` to replace `Babar`

    If at some point we register a new appobject class in this module, it won't be
    registered at all without modification to the `registration_callback`
    implementation. The first example will register it though, thanks to the call
    to the `register_all` method.

    Controlling registry instantiation
    ----------------------------------

    The `REGISTRY_FACTORY` class dictionary allows to specify which class should
    be instantiated for a given registry name. The class associated to `None`
    key will be the class used when there is no specific class for a name.
    """

    def __init__(self, debugmode=False):
        super(RegistryStore, self).__init__()
        self.debugmode = debugmode

    def reset(self):
        """clear all registries managed by this store"""
        # don't use self.clear, we want to keep existing subdictionaries
        for subdict in self.itervalues():
            subdict.clear()
        self._lastmodifs = {}

    def __getitem__(self, name):
        """return the registry (dictionary of class objects) associated to
        this name
        """
        try:
            return super(RegistryStore, self).__getitem__(name)
        except KeyError:
            raise RegistryNotFound(name), None, sys.exc_info()[-1]

    # methods for explicit (un)registration ###################################

    # default class, when no specific class set
    REGISTRY_FACTORY = {None: Registry}

    def registry_class(self, regid):
        """return existing registry named regid or use factory to create one and
        return it"""
        try:
            return self.REGISTRY_FACTORY[regid]
        except KeyError:
            return self.REGISTRY_FACTORY[None]

    def setdefault(self, regid):
        try:
            return self[regid]
        except RegistryNotFound:
            self[regid] = self.registry_class(regid)(self.debugmode)
            return self[regid]

    def register_all(self, objects, modname, butclasses=()):
        """register registrable objects into `objects`.

        Registrable objects are properly configured subclasses of
        :class:`RegistrableObject`.  Objects which are not defined in the module
        `modname` or which are in `butclasses` won't be registered.

        Typical usage is:

        .. sourcecode:: python

            store.register_all(globals().values(), __name__, (ClassIWantToRegisterExplicitly,))

        So you get partially automatic registration, keeping manual registration
        for some object (to use
        :meth:`~logilab.common.registry.RegistryStore.register_and_replace` for
        instance).
        """
        assert isinstance(modname, basestring), \
            'modname expected to be a module name (ie string), got %r' % modname
        for obj in objects:
            if self.is_registrable(obj) and obj.__module__ == modname and not obj in butclasses:
                if isinstance(obj, type):
                    self._load_ancestors_then_object(modname, obj, butclasses)
                else:
                    self.register(obj)

    def register(self, obj, registryname=None, oid=None, clear=False):
        """register `obj` implementation into `registryname` or
        `obj.__registries__` if not specified, with identifier `oid` or
        `obj.__regid__` if not specified.

        If `clear` is true, all objects with the same identifier will be
        previously unregistered.
        """
        assert not obj.__dict__.get('__abstract__'), obj
        for registryname in obj_registries(obj, registryname):
            registry = self.setdefault(registryname)
            registry.register(obj, oid=oid, clear=clear)
            self.debug("register %s in %s['%s']",
                       registry.objname(obj), registryname, oid or obj.__regid__)
            self._loadedmods.setdefault(obj.__module__, {})[registry.objid(obj)] = obj

    def unregister(self, obj, registryname=None):
        """unregister `obj` object from the registry `registryname` or
        `obj.__registries__` if not specified.
        """
        for registryname in obj_registries(obj, registryname):
            registry = self[registryname]
            registry.unregister(obj)
            self.debug("unregister %s from %s['%s']",
                       registry.objname(obj), registryname, obj.__regid__)

    def register_and_replace(self, obj, replaced, registryname=None):
        """register `obj` object into `registryname` or
        `obj.__registries__` if not specified. If found, the `replaced` object
        will be unregistered first (else a warning will be issued as it is
        generally unexpected).
        """
        for registryname in obj_registries(obj, registryname):
            registry = self[registryname]
            registry.register_and_replace(obj, replaced)
            self.debug("register %s in %s['%s'] instead of %s",
                       registry.objname(obj), registryname, obj.__regid__,
                       registry.objname(replaced))

    # initialization methods ###################################################

    def init_registration(self, path, extrapath=None):
        """reset registry and walk down path to return list of (path, name)
        file modules to be loaded"""
        # XXX make this private by renaming it to _init_registration ?
        self.reset()
        # compute list of all modules that have to be loaded
        self._toloadmods, filemods = _toload_info(path, extrapath)
        # XXX is _loadedmods still necessary ? It seems like it's useful
        #     to avoid loading same module twice, especially with the
        #     _load_ancestors_then_object logic but this needs to be checked
        self._loadedmods = {}
        return filemods

    def register_objects(self, path, extrapath=None):
        """register all objects found walking down <path>"""
        # load views from each directory in the instance's path
        # XXX inline init_registration ?
        filemods = self.init_registration(path, extrapath)
        for filepath, modname in filemods:
            self.load_file(filepath, modname)
        self.initialization_completed()

    def initialization_completed(self):
        """call initialization_completed() on all known registries"""
        for reg in self.itervalues():
            reg.initialization_completed()

    def _mdate(self, filepath):
        """ return the modification date of a file path """
        try:
            return stat(filepath)[-2]
        except OSError:
            # this typically happens on emacs backup files (.#foo.py)
            self.warning('Unable to load %s. It is likely to be a backup file',
                         filepath)
            return None

    def is_reload_needed(self, path):
        """return True if something module changed and the registry should be
        reloaded
        """
        lastmodifs = self._lastmodifs
        for fileordir in path:
            if isdir(fileordir) and exists(join(fileordir, '__init__.py')):
                if self.is_reload_needed([join(fileordir, fname)
                                          for fname in listdir(fileordir)]):
                    return True
            elif fileordir[-3:] == '.py':
                mdate = self._mdate(fileordir)
                if mdate is None:
                    continue # backup file, see _mdate implementation
                elif "flymake" in fileordir:
                    # flymake + pylint in use, don't consider these they will corrupt the registry
                    continue
                if fileordir not in lastmodifs or lastmodifs[fileordir] < mdate:
                    self.info('File %s changed since last visit', fileordir)
                    return True
        return False

    def load_file(self, filepath, modname):
        """ load registrable objects (if any) from a python file """
        from logilab.common.modutils import load_module_from_name
        if modname in self._loadedmods:
            return
        self._loadedmods[modname] = {}
        mdate = self._mdate(filepath)
        if mdate is None:
            return # backup file, see _mdate implementation
        elif "flymake" in filepath:
            # flymake + pylint in use, don't consider these they will corrupt the registry
            return
        # set update time before module loading, else we get some reloading
        # weirdness in case of syntax error or other error while importing the
        # module
        self._lastmodifs[filepath] = mdate
        # load the module
        module = load_module_from_name(modname)
        self.load_module(module)

    def load_module(self, module):
        """Automatically handle module objects registration.

        Instances are registered as soon as they are hashable and have the
        following attributes:

        * __regid__ (a string)
        * __select__ (a callable)
        * __registries__ (a tuple/list of string)

        For classes this is a bit more complicated :

        - first ensure parent classes are already registered

        - class with __abstract__ == True in their local dictionary are skipped

        - object class needs to have registries and identifier properly set to a
          non empty string to be registered.
        """
        self.info('loading %s from %s', module.__name__, module.__file__)
        if hasattr(module, 'registration_callback'):
            module.registration_callback(self)
        else:
            self.register_all(vars(module).itervalues(), module.__name__)

    def _load_ancestors_then_object(self, modname, objectcls, butclasses=()):
        """handle class registration according to rules defined in
        :meth:`load_module`
        """
        # backward compat, we used to allow whatever else than classes
        if not isinstance(objectcls, type):
            if self.is_registrable(objectcls) and objectcls.__module__ == modname:
                self.register(objectcls)
            return
        # imported classes
        objmodname = objectcls.__module__
        if objmodname != modname:
            # The module of the object is not the same as the currently
            # worked on module, or this is actually an instance, which
            # has no module at all
            if objmodname in self._toloadmods:
                # if this is still scheduled for loading, let's proceed immediately,
                # but using the object module
                self.load_file(self._toloadmods[objmodname], objmodname)
            return
        # ensure object hasn't been already processed
        clsid = '%s.%s' % (modname, objectcls.__name__)
        if clsid in self._loadedmods[modname]:
            return
        self._loadedmods[modname][clsid] = objectcls
        # ensure ancestors are registered
        for parent in objectcls.__bases__:
            self._load_ancestors_then_object(modname, parent, butclasses)
        # ensure object is registrable
        if objectcls in butclasses or not self.is_registrable(objectcls):
            return
        # backward compat
        reg = self.setdefault(obj_registries(objectcls)[0])
        if reg.objname(objectcls)[0] == '_':
            warn("[lgc 0.59] object whose name start with '_' won't be "
                 "skipped anymore at some point, use __abstract__ = True "
                 "instead (%s)" % objectcls, DeprecationWarning)
            return
        # register, finally
        self.register(objectcls)

    @classmethod
    def is_registrable(cls, obj):
        """ensure `obj` should be registered

        as arbitrary stuff may be registered, do a lot of check and warn about
        weird cases (think to dumb proxy objects)
        """
        if isinstance(obj, type):
            if not issubclass(obj, RegistrableObject):
                # ducktyping backward compat
                if not (getattr(obj, '__registries__', None)
                        and getattr(obj, '__regid__', None)
                        and getattr(obj, '__select__', None)):
                    return False
            elif issubclass(obj, RegistrableInstance):
 		return False
        elif not isinstance(obj, RegistrableInstance):
            return False
        if not obj.__regid__:
            return False # no regid
        registries = obj.__registries__
        if not registries:
            return False # no registries
        selector = obj.__select__
        if not selector:
            return False # no selector
        if obj.__dict__.get('__abstract__', False):
            return False
        # then detect potential problems that should be warned
        if not isinstance(registries, (tuple, list)):
            cls.warning('%s has __registries__ which is not a list or tuple', obj)
            return False
        if not callable(selector):
            cls.warning('%s has not callable __select__', obj)
            return False
        return True

    # these are overridden by set_log_methods below
    # only defining here to prevent pylint from complaining
    info = warning = error = critical = exception = debug = lambda msg, *a, **kw: None


# init logging
set_log_methods(RegistryStore, getLogger('registry.store'))
set_log_methods(Registry, getLogger('registry'))


# helpers for debugging selectors
TRACED_OIDS = None

def _trace_selector(cls, selector, args, ret):
    vobj = args[0]
    if TRACED_OIDS == 'all' or vobj.__regid__ in TRACED_OIDS:
        print '%s -> %s for %s(%s)' % (cls, ret, vobj, vobj.__regid__)

def _lltrace(selector):
    """use this decorator on your predicates so they become traceable with
    :class:`traced_selection`
    """
    def traced(cls, *args, **kwargs):
        ret = selector(cls, *args, **kwargs)
        if TRACED_OIDS is not None:
            _trace_selector(cls, selector, args, ret)
        return ret
    traced.__name__ = selector.__name__
    traced.__doc__ = selector.__doc__
    return traced

class traced_selection(object): # pylint: disable=C0103
    """
    Typical usage is :

    .. sourcecode:: python

        >>> from logilab.common.registry import traced_selection
        >>> with traced_selection():
        ...     # some code in which you want to debug selectors
        ...     # for all objects

    Don't forget the 'from __future__ import with_statement' at the module top-level
    if you're using python prior to 2.6.

    This will yield lines like this in the logs::

        selector one_line_rset returned 0 for <class 'elephant.Babar'>

    You can also give to :class:`traced_selection` the identifiers of objects on
    which you want to debug selection ('oid1' and 'oid2' in the example above).

    .. sourcecode:: python

        >>> with traced_selection( ('regid1', 'regid2') ):
        ...     # some code in which you want to debug selectors
        ...     # for objects with __regid__ 'regid1' and 'regid2'

    A potentially useful point to set up such a tracing function is
    the `logilab.common.registry.Registry.select` method body.
    """

    def __init__(self, traced='all'):
        self.traced = traced

    def __enter__(self):
        global TRACED_OIDS
        TRACED_OIDS = self.traced

    def __exit__(self, exctype, exc, traceback):
        global TRACED_OIDS
        TRACED_OIDS = None
        return traceback is None

# selector base classes and operations ########################################

def objectify_predicate(selector_func):
    """Most of the time, a simple score function is enough to build a selector.
    The :func:`objectify_predicate` decorator turn it into a proper selector
    class::

        @objectify_predicate
        def one(cls, req, rset=None, **kwargs):
            return 1

        class MyView(View):
            __select__ = View.__select__ & one()

    """
    return type(selector_func.__name__, (Predicate,),
                {'__doc__': selector_func.__doc__,
                 '__call__': lambda self, *a, **kw: selector_func(*a, **kw)})


_PREDICATES = {}

def wrap_predicates(decorator):
    for predicate in _PREDICATES.itervalues():
        if not '_decorators' in predicate.__dict__:
            predicate._decorators = set()
        if decorator in predicate._decorators:
            continue
        predicate._decorators.add(decorator)
        predicate.__call__ = decorator(predicate.__call__)

class PredicateMetaClass(type):
    def __new__(cls, *args, **kwargs):
        # use __new__ so subclasses doesn't have to call Predicate.__init__
        inst = type.__new__(cls, *args, **kwargs)
        proxy = weakref.proxy(inst, lambda p: _PREDICATES.pop(id(p)))
        _PREDICATES[id(proxy)] = proxy
        return inst

class Predicate(object):
    """base class for selector classes providing implementation
    for operators ``&``, ``|`` and  ``~``

    This class is only here to give access to binary operators, the selector
    logic itself should be implemented in the :meth:`__call__` method. Notice it
    should usually accept any arbitrary arguments (the context), though that may
    vary depending on your usage of the registry.

    a selector is called to help choosing the correct object for a
    particular context by returning a score (`int`) telling how well
    the implementation given as first argument fit to the given context.

    0 score means that the class doesn't apply.
    """
    __metaclass__ = PredicateMetaClass

    @property
    def func_name(self):
        # backward compatibility
        return self.__class__.__name__

    def search_selector(self, selector):
        """search for the given selector, selector instance or tuple of
        selectors in the selectors tree. Return None if not found.
        """
        if self is selector:
            return self
        if (isinstance(selector, type) or isinstance(selector, tuple)) and \
               isinstance(self, selector):
            return self
        return None

    def __str__(self):
        return self.__class__.__name__

    def __and__(self, other):
        return AndPredicate(self, other)
    def __rand__(self, other):
        return AndPredicate(other, self)
    def __iand__(self, other):
        return AndPredicate(self, other)
    def __or__(self, other):
        return OrPredicate(self, other)
    def __ror__(self, other):
        return OrPredicate(other, self)
    def __ior__(self, other):
        return OrPredicate(self, other)

    def __invert__(self):
        return NotPredicate(self)

    # XXX (function | function) or (function & function) not managed yet

    def __call__(self, cls, *args, **kwargs):
        return NotImplementedError("selector %s must implement its logic "
                                   "in its __call__ method" % self.__class__)

    def __repr__(self):
        return u'<Predicate %s at %x>' % (self.__class__.__name__, id(self))


class MultiPredicate(Predicate):
    """base class for compound selector classes"""

    def __init__(self, *selectors):
        self.selectors = self.merge_selectors(selectors)

    def __str__(self):
        return '%s(%s)' % (self.__class__.__name__,
                           ','.join(str(s) for s in self.selectors))

    @classmethod
    def merge_selectors(cls, selectors):
        """deal with selector instanciation when necessary and merge
        multi-selectors if possible:

        AndPredicate(AndPredicate(sel1, sel2), AndPredicate(sel3, sel4))
        ==> AndPredicate(sel1, sel2, sel3, sel4)
        """
        merged_selectors = []
        for selector in selectors:
            # XXX do we really want magic-transformations below?
            # if so, wanna warn about them?
            if isinstance(selector, types.FunctionType):
                selector = objectify_predicate(selector)()
            if isinstance(selector, type) and issubclass(selector, Predicate):
                selector = selector()
            assert isinstance(selector, Predicate), selector
            if isinstance(selector, cls):
                merged_selectors += selector.selectors
            else:
                merged_selectors.append(selector)
        return merged_selectors

    def search_selector(self, selector):
        """search for the given selector or selector instance (or tuple of
        selectors) in the selectors tree. Return None if not found
        """
        for childselector in self.selectors:
            if childselector is selector:
                return childselector
            found = childselector.search_selector(selector)
            if found is not None:
                return found
        # if not found in children, maybe we are looking for self?
        return super(MultiPredicate, self).search_selector(selector)


class AndPredicate(MultiPredicate):
    """and-chained selectors"""
    def __call__(self, cls, *args, **kwargs):
        score = 0
        for selector in self.selectors:
            partscore = selector(cls, *args, **kwargs)
            if not partscore:
                return 0
            score += partscore
        return score


class OrPredicate(MultiPredicate):
    """or-chained selectors"""
    def __call__(self, cls, *args, **kwargs):
        for selector in self.selectors:
            partscore = selector(cls, *args, **kwargs)
            if partscore:
                return partscore
        return 0

class NotPredicate(Predicate):
    """negation selector"""
    def __init__(self, selector):
        self.selector = selector

    def __call__(self, cls, *args, **kwargs):
        score = self.selector(cls, *args, **kwargs)
        return int(not score)

    def __str__(self):
        return 'NOT(%s)' % self.selector


class yes(Predicate): # pylint: disable=C0103
    """Return the score given as parameter, with a default score of 0.5 so any
    other selector take precedence.

    Usually used for objects which can be selected whatever the context, or
    also sometimes to add arbitrary points to a score.

    Take care, `yes(0)` could be named 'no'...
    """
    def __init__(self, score=0.5):
        self.score = score

    def __call__(self, *args, **kwargs):
        return self.score


# deprecated stuff #############################################################

from logilab.common.deprecation import deprecated

@deprecated('[lgc 0.59] use Registry.objid class method instead')
def classid(cls):
    return '%s.%s' % (cls.__module__, cls.__name__)

@deprecated('[lgc 0.59] use obj_registries function instead')
def class_registries(cls, registryname):
    return obj_registries(cls, registryname)

