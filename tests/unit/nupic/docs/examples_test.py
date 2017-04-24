# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2017, Numenta, Inc.  Unless you have an agreement
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

"""Unit tests for all quick-start examples in the NuPIC docs."""

import os
import sys
import unittest2 as unittest



def _runExample():
  """Import and run main function runHotgym() in complete-example.py"""
  mod = __import__("complete-example", fromlist=["runHotgym"])
  runHotgym = getattr(mod, 'runHotgym')
  runHotgym()



class ExamplesTest(unittest.TestCase):
  """Unit tests for all quick-start examples."""


  def setUp(self):
    docsTestsPath = os.path.dirname(os.path.abspath(__file__))
    self.examplesDir = os.path.join(docsTestsPath, os.path.pardir,
                                    os.path.pardir, os.path.pardir,
                                    os.path.pardir, "docs", "examples")


  def testExamplesDirExists(self):
    """Make sure the ``examples`` directory is in the correct location"""
    self.assertTrue(os.path.exists(self.examplesDir),
                    "Path to examples does not exist: %s" % self.examplesDir)


  def testOPFExample(self):
    """Make sure the OPF example does not throw any exception"""
    sys.path.insert(0, os.path.join(self.examplesDir, "opf"))  # Add to path
    _runExample()


  def testNetworkAPIExample(self):
    """Make sure the network API example does not throw any exception"""
    sys.path.insert(0, os.path.join(self.examplesDir, "network"))  # Add to path
    _runExample()


  def testAlgoExample(self):
    """Make sure the algorithm API example does not throw any exception"""
    sys.path.insert(0, os.path.join(self.examplesDir, "algo"))  # Add to path
    _runExample()



if __name__ == '__main__':
  unittest.main()
