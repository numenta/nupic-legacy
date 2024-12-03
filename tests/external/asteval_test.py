# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""Test asteval module is installed."""

import unittest2 as unittest



class TestCase(unittest.TestCase):


  def testImportAndVersions(self):
    import asteval
    from pkg_resources import parse_version
    self.assertGreater(parse_version(asteval.__version__), parse_version("0.9"))



if __name__ == "__main__":
  unittest.main()
