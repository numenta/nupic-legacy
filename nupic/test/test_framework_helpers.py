#! /usr/bin/env python
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
