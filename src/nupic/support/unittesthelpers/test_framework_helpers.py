# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""
Abstraction around some test framework features to make it easier to
move to a different framework in the future.

Tests should make use of the built-in unittest framework's features where
possible, turning to this module only for those features that are not.

This module should only abstract features that are likely to be supported
by multiple mainstream test frameworks, such as pytest and nose.
"""


# Our current test framework is pytest
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
