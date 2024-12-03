# Copyright 2016 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import unittest

import nupic.bindings.algorithms
from extensive_tm_test_base import ExtensiveTemporalMemoryTest



class ExtensiveTemporalMemoryTestCPP(ExtensiveTemporalMemoryTest, unittest.TestCase):
  def getTMClass(self):
    return nupic.bindings.algorithms.TemporalMemory


if __name__ == "__main__":
  unittest.main()
