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
