# Copyright 2016 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import unittest

import nupic.algorithms.temporal_memory
from extensive_tm_test_base import ExtensiveTemporalMemoryTest



class ExtensiveTemporalMemoryTestPY(ExtensiveTemporalMemoryTest, unittest.TestCase):
  def getTMClass(self):
    return nupic.algorithms.temporal_memory.TemporalMemory


if __name__ == "__main__":
  unittest.main()
