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
from logilab.common.testlib import TestCase, unittest_main

from logilab.common.tasksqueue import *

class TaskTC(TestCase):

    def test_eq(self):
        self.assertFalse(Task('t1') == Task('t2'))
        self.assertTrue(Task('t1') == Task('t1'))

    def test_cmp(self):
        self.assertTrue(Task('t1', LOW) < Task('t2', MEDIUM))
        self.assertFalse(Task('t1', LOW) > Task('t2', MEDIUM))
        self.assertTrue(Task('t1', HIGH) > Task('t2', MEDIUM))
        self.assertFalse(Task('t1', HIGH) < Task('t2', MEDIUM))


class PrioritizedTasksQueueTC(TestCase):

    def test_priority(self):
        queue = PrioritizedTasksQueue()
        queue.put(Task('t1'))
        queue.put(Task('t2', MEDIUM))
        queue.put(Task('t3', HIGH))
        queue.put(Task('t4', LOW))
        self.assertEqual(queue.get().id, 't3')
        self.assertEqual(queue.get().id, 't2')
        self.assertEqual(queue.get().id, 't1')
        self.assertEqual(queue.get().id, 't4')

    def test_remove_equivalent(self):
        queue = PrioritizedTasksQueue()
        queue.put(Task('t1'))
        queue.put(Task('t2', MEDIUM))
        queue.put(Task('t1', HIGH))
        queue.put(Task('t3', MEDIUM))
        queue.put(Task('t2', MEDIUM))
        self.assertEqual(queue.qsize(), 3)
        self.assertEqual(queue.get().id, 't1')
        self.assertEqual(queue.get().id, 't2')
        self.assertEqual(queue.get().id, 't3')
        self.assertEqual(queue.qsize(), 0)

    def test_remove(self):
        queue = PrioritizedTasksQueue()
        queue.put(Task('t1'))
        queue.put(Task('t2'))
        queue.put(Task('t3'))
        queue.remove('t2')
        self.assertEqual([t.id for t in queue], ['t3', 't1'])
        self.assertRaises(ValueError, queue.remove, 't4')

if __name__ == '__main__':
    unittest_main()
