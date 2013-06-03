# unit tests for the cache module
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

from logilab.common.testlib import TestCase, unittest_main, TestSuite
from logilab.common.cache import Cache

class CacheTestCase(TestCase):

    def setUp(self):
        self.cache = Cache(5)
        self.testdict = {}

    def test_setitem1(self):
        """Checks that the setitem method works"""
        self.cache[1] = 'foo'
        self.assertEqual(self.cache[1], 'foo', "1:foo is not in cache")
        self.assertEqual(len(self.cache._usage), 1)
        self.assertEqual(self.cache._usage[-1], 1,
                         '1 is not the most recently used key')
        self.assertItemsEqual(self.cache._usage,
                              self.cache.keys(),
                              "usage list and data keys are different")

    def test_setitem2(self):
        """Checks that the setitem method works for multiple items"""
        self.cache[1] = 'foo'
        self.cache[2] = 'bar'
        self.assertEqual(self.cache[2], 'bar',
                         "2 : 'bar' is not in cache.data")
        self.assertEqual(len(self.cache._usage), 2,
                         "lenght of usage list is not 2")
        self.assertEqual(self.cache._usage[-1], 2,
                     '1 is not the most recently used key')
        self.assertItemsEqual(self.cache._usage,
                              self.cache.keys())# usage list and data keys are different

    def test_setitem3(self):
        """Checks that the setitem method works when replacing an element in the cache"""
        self.cache[1] = 'foo'
        self.cache[1] = 'bar'
        self.assertEqual(self.cache[1], 'bar', "1 : 'bar' is not in cache.data")
        self.assertEqual(len(self.cache._usage), 1, "lenght of usage list is not 1")
        self.assertEqual(self.cache._usage[-1], 1, '1 is not the most recently used key')
        self.assertItemsEqual(self.cache._usage,
                              self.cache.keys())# usage list and data keys are different

    def test_recycling1(self):
        """Checks the removal of old elements"""
        self.cache[1] = 'foo'
        self.cache[2] = 'bar'
        self.cache[3] = 'baz'
        self.cache[4] = 'foz'
        self.cache[5] = 'fuz'
        self.cache[6] = 'spam'
        self.assertTrue(1 not in self.cache,
                     'key 1 has not been suppressed from the cache dictionnary')
        self.assertTrue(1 not in self.cache._usage,
                     'key 1 has not been suppressed from the cache LRU list')
        self.assertEqual(len(self.cache._usage), 5, "lenght of usage list is not 5")
        self.assertEqual(self.cache._usage[-1], 6, '6 is not the most recently used key')
        self.assertItemsEqual(self.cache._usage,
                              self.cache.keys())# usage list and data keys are different

    def test_recycling2(self):
        """Checks that accessed elements get in the front of the list"""
        self.cache[1] = 'foo'
        self.cache[2] = 'bar'
        self.cache[3] = 'baz'
        self.cache[4] = 'foz'
        a = self.cache[1]
        self.assertEqual(a, 'foo')
        self.assertEqual(self.cache._usage[-1], 1, '1 is not the most recently used key')
        self.assertItemsEqual(self.cache._usage,
                              self.cache.keys())# usage list and data keys are different

    def test_delitem(self):
        """Checks that elements are removed from both element dict and element
        list.
        """
        self.cache['foo'] = 'bar'
        del self.cache['foo']
        self.assertTrue('foo' not in self.cache.keys(), "Element 'foo' was not removed cache dictionnary")
        self.assertTrue('foo' not in self.cache._usage, "Element 'foo' was not removed usage list")
        self.assertItemsEqual(self.cache._usage,
                              self.cache.keys())# usage list and data keys are different


    def test_nullsize(self):
        """Checks that a 'NULL' size cache doesn't store anything
        """
        null_cache = Cache(0)
        null_cache['foo'] = 'bar'
        self.assertEqual(null_cache.size, 0, 'Cache size should be O, not %d' % \
                     null_cache.size)
        self.assertEqual(len(null_cache), 0, 'Cache should be empty !')
        # Assert null_cache['foo'] raises a KeyError
        self.assertRaises(KeyError, null_cache.__getitem__, 'foo')
        # Deleting element raises a KeyError
        self.assertRaises(KeyError, null_cache.__delitem__, 'foo')

    def test_getitem(self):
        """ Checks that getitem doest not modify the _usage attribute
        """
        try:
            self.cache['toto']
        except KeyError:
            self.assertTrue('toto' not in self.cache._usage)
        else:
            self.fail('excepted KeyError')


if __name__ == "__main__":
    unittest_main()
