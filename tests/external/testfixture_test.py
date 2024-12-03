# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""
Unit tests for our dependencies in the pytest package; at the time of this
writing, we were using an unreleased version of pytest that added support for
the unittest setUpModule fixture and friends. Some of our tests rely on
setUpModule. Once, there was a conflict with pytest installation in our build
system, and an older version of pytest was installed that didn't support
setUpModule, which resulted in subtle side-effects in some of these tests.
"""

import unittest2 as unittest


g_setUpModuleCalled = False



def setUpModule():
  global g_setUpModuleCalled
  g_setUpModuleCalled = True



class TestPytest(unittest.TestCase):

  
  def testSetUpModuleCalled(self):
    self.assertTrue(g_setUpModuleCalled)



if __name__ == "__main__":
  unittest.main()
