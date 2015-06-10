#! /usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

"""
Abstraction around some test framework features to make it easier to
move to a different framework in the future.

Tests should make use of the built-in unittest framework's features where
possible, turning to this module only for those features that are not.

This module should only abstract features that are likely to be supported
by multiple mainstream test frameworks, such as pytest and nose.
"""


# Our current test framework is pytest
import numbers
import numpy
import pytest


def tagTest(tag, comment=None):
  """ A decorator for tagging a test class or test method with the given tag
  string

  tag: test tag string
  comment: reason for the tag; string; optional

  Examples:

  @tagTest("slowTests", "takes a long time to execute")
  class ClusterTests(TestCase):
    def testSwarmWithAggregation(self):
      pass

    def testSwarmWithoutAggregation(self):
      pass

  or

  class MiscTests(TestCase):
    def testOnePlusOne(self):
      pass

    @tagTest("slowTests")
    def testSwarm(self):
      pass
  """
  return getattr(pytest.mark, tag)


def assertInstancesAlmostEqual(testCase, name, obj1, obj2,
                               classesToCompare=[],
                               classesToIgnore=[],
                               membersToIgnore=[]):
  """Check that two instances have the very similar members"""

  if type(obj1) in classesToIgnore or name in membersToIgnore:
    pass
  elif type(obj1) in classesToCompare:
    # Here we update the list of which class instances that should not be
    # parsed again in order to avoid an infinite recursion
    newClassesToIgnore = list(classesToIgnore)
    newClassesToIgnore.append(type(obj1))

    keys1 = set(obj1.__dict__.keys()).copy()
    keys2 = set(obj1.__dict__.keys()).copy()
    for k in membersToIgnore:
      if k in keys1:
        keys1.remove(k)
      if k in keys2:
        keys2.remove(k)

    testCase.assertSetEqual(keys1, keys2)
    for k, v1 in obj1.__dict__.iteritems():
      v2 = getattr(obj2, k)
      assertInstancesAlmostEqual(testCase, k, v1, v2,
                                 classesToCompare,
                                 newClassesToIgnore,
                                 membersToIgnore)
  elif isinstance(obj1, float) or isinstance(obj1, numpy.float32):
    #testCase.assertEqual(type(obj1), type(obj2), name)
    testCase.assertAlmostEqual(float(obj1), float(obj2), 4, name)
  elif isinstance(obj1, numbers.Integral):
    testCase.assertEqual(long(obj1), long(obj2), name)
  elif isinstance(obj1, numpy.ndarray):
    testCase.assertEqual(type(obj1), type(obj2), name)
    testCase.assertEqual(obj1.dtype, obj2.dtype,
                         "Key %s has differing dtypes: %s vs %s" % (
                         name, obj1.dtype, obj2.dtype))
    testCase.assertTrue(numpy.isclose(obj1, obj2).all(), name)
  elif isinstance(obj1, list) or isinstance(obj1, tuple):
    testCase.assertEqual(len(obj1), len(obj2), name)
    for i in xrange(len(obj1)):
      assertInstancesAlmostEqual(testCase, name, obj1[i], obj2[i],
                                 classesToCompare,
                                 classesToIgnore,
                                 membersToIgnore)
  elif isinstance(obj1, dict):
    testCase.assertEqual(obj1.keys().sort(), obj2.keys().sort(), name)
    for i in obj1.keys():
      assertInstancesAlmostEqual(testCase, i, obj1[i], obj2[i],
                                 classesToCompare,
                                 classesToIgnore,
                                 membersToIgnore)
  else:
    testCase.assertEqual(type(obj1), type(obj2), name)
    testCase.assertEqual(obj1, obj2, name)
