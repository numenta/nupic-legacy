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
"""A generic visitor abstract implementation.




"""
__docformat__ = "restructuredtext en"

def no_filter(_):
    return 1

# Iterators ###################################################################
class FilteredIterator(object):

    def __init__(self, node, list_func, filter_func=None):
        self._next = [(node, 0)]
        if filter_func is None:
            filter_func = no_filter
        self._list = list_func(node, filter_func)

    def next(self):
        try:
            return self._list.pop(0)
        except :
            return None

# Base Visitor ################################################################
class Visitor(object):

    def __init__(self, iterator_class, filter_func=None):
        self._iter_class = iterator_class
        self.filter = filter_func

    def visit(self, node, *args, **kargs):
        """
        launch the visit on a given node

        call 'open_visit' before the beginning of the visit, with extra args
        given
        when all nodes have been visited, call the 'close_visit' method
        """
        self.open_visit(node, *args, **kargs)
        return self.close_visit(self._visit(node))

    def _visit(self, node):
        iterator = self._get_iterator(node)
        n = iterator.next()
        while n:
            result = n.accept(self)
            n = iterator.next()
        return result

    def _get_iterator(self, node):
        return self._iter_class(node, self.filter)

    def open_visit(self, *args, **kargs):
        """
        method called at the beginning of the visit
        """
        pass

    def close_visit(self, result):
        """
        method called at the end of the visit
        """
        return result

# standard visited mixin ######################################################
class VisitedMixIn(object):
    """
    Visited interface allow node visitors to use the node
    """
    def get_visit_name(self):
        """
        return the visit name for the mixed class. When calling 'accept', the
        method <'visit_' + name returned by this method> will be called on the
        visitor
        """
        try:
            return self.TYPE.replace('-', '_')
        except:
            return self.__class__.__name__.lower()

    def accept(self, visitor, *args, **kwargs):
        func = getattr(visitor, 'visit_%s' % self.get_visit_name())
        return func(self, *args, **kwargs)

    def leave(self, visitor, *args, **kwargs):
        func = getattr(visitor, 'leave_%s' % self.get_visit_name())
        return func(self, *args, **kwargs)
