#!/usr/bin/env python
# ----------------------------------------------------------------------
# Copyright (C) 2013 Numenta Inc. All rights reserved.
#
# The information and source code contained herein is the
# exclusive property of Numenta Inc. No part of this software
# may be used, reproduced, stored or distributed in any form,
# without explicit written authorization from Numenta Inc.
# ----------------------------------------------------------------------

"""
Unit tests for our dependencies in the pytest package; at the time of this
writing, we were using an unreleased version of pytest that added support for
the unittest setUpModule fixture and friends. Some of our tests rely on
setUpModule. Once, there was a conflict with pytest installation in our build
system, and an older version of pytest was installed that didn't support
setUpModule, which resulted in suble side-effects in some of these tests.
"""

import unittest2 as unittest


g_setUpModuleCalled = False



def setUpModule():
  global g_setUpModuleCalled
  g_setUpModuleCalled = True



class TestPytest(unittest.TestCase):

  
  def testSetUpModuleCalled(self):
    self.assertTrue(g_setUpModuleCalled)



if __name__ == '__main__':
  unittest.main()
