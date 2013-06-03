# copyright 2003-2011 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
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
"""Cache module, with a least recently used algorithm for the management of the
deletion of entries.




"""
__docformat__ = "restructuredtext en"

from threading import Lock

from logilab.common.decorators import locked

_marker = object()

class Cache(dict):
    """A dictionary like cache.

    inv:
        len(self._usage) <= self.size
        len(self.data) <= self.size
    """

    def __init__(self, size=100):
        """ Warning : Cache.__init__() != dict.__init__().
        Constructor does not take any arguments beside size.
        """
        assert size >= 0, 'cache size must be >= 0 (0 meaning no caching)'
        self.size = size
        self._usage = []
        self._lock = Lock()
        super(Cache, self).__init__()

    def _acquire(self):
        self._lock.acquire()

    def _release(self):
        self._lock.release()

    def _update_usage(self, key):
        if not self._usage:
            self._usage.append(key)
        elif self._usage[-1] != key:
            try:
                self._usage.remove(key)
            except ValueError:
                # we are inserting a new key
                # check the size of the dictionary
                # and remove the oldest item in the cache
                if self.size and len(self._usage) >= self.size:
                    super(Cache, self).__delitem__(self._usage[0])
                    del self._usage[0]
            self._usage.append(key)
        else:
            pass # key is already the most recently used key

    def __getitem__(self, key):
        value = super(Cache, self).__getitem__(key)
        self._update_usage(key)
        return value
    __getitem__ = locked(_acquire, _release)(__getitem__)

    def __setitem__(self, key, item):
        # Just make sure that size > 0 before inserting a new item in the cache
        if self.size > 0:
            super(Cache, self).__setitem__(key, item)
            self._update_usage(key)
    __setitem__ = locked(_acquire, _release)(__setitem__)

    def __delitem__(self, key):
        super(Cache, self).__delitem__(key)
        self._usage.remove(key)
    __delitem__ = locked(_acquire, _release)(__delitem__)

    def clear(self):
        super(Cache, self).clear()
        self._usage = []
    clear = locked(_acquire, _release)(clear)

    def pop(self, key, default=_marker):
        if key in self:
            self._usage.remove(key)
        #if default is _marker:
        #    return super(Cache, self).pop(key)
        return super(Cache, self).pop(key, default)
    pop = locked(_acquire, _release)(pop)

    def popitem(self):
        raise NotImplementedError()

    def setdefault(self, key, default=None):
        raise NotImplementedError()

    def update(self, other):
        raise NotImplementedError()


