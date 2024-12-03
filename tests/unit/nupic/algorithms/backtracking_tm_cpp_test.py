# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""Tests for the C++ implementation of the temporal memory."""

import unittest2 as unittest

from nupic.algorithms.backtracking_tm_cpp import BacktrackingTMCPP
from tests.unit.nupic.algorithms import backtracking_tm_test

# Run the Python TM test against the BacktrackingTMCPP.
backtracking_tm_test.BacktrackingTM = BacktrackingTMCPP
BacktrackingTMTest = backtracking_tm_test.BacktrackingTMTest



if __name__ == '__main__':
  unittest.main()
