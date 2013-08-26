# ----------------------------------------------------------------------
#  Copyright (C) 2013 Numenta Inc. All rights reserved.
#
#  The information and source code contained herein is the
#  exclusive property of Numenta Inc. No part of this software
#  may be used, reproduced, stored or distributed in any form,
#  without explicit written authorization from Numenta Inc.
# ----------------------------------------------------------------------

"""
Abstraction around some test framework features to make it easier to move to
move to a different framework in the future.

Tests should make use of the built-in unittest framework's features where
possible, turning to this module only for those features that are not.

This module should only abstract features that are likely to be supported
by multiple mainstream test frameworks, such as pytest and nose.
"""


# Our current test framework is pytest
import pytest


def tagTest(tag, comment=None):
  """ A decorator for taggomg a test class or test method with the given tag
  string
  
  tag: test tag string
  comment: reason for the tag; string; optional
  
  Examples:
  
  @markTest("slowTests", "takes a long time to execute")
  class ClusterTests(TestCase):
    def testSwarmWithAggregation(self):
      pass
    
    def testSwarmWithoutAggregation(self):
      pass
  
  or
  
  class MiscTests(TestCase):
    def testOnePlusOne(self):
      pass
      
    @markTest("slowTests")
    def testSwarm(self):
      pass
  """
  return getattr(pytest.mark, tag)
