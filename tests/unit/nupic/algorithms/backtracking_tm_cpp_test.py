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

"""Tests for the C++ implementation of the temporal memory."""

import unittest2 as unittest

from nupic.algorithms.backtracking_tm_cpp import BacktrackingTMCPP
from tests.unit.nupic.algorithms import backtracking_tm_test

# Run the Python TM test against the BacktrackingTMCPP.
backtracking_tm_test.BacktrackingTM = BacktrackingTMCPP
BacktrackingTMTest = backtracking_tm_test.BacktrackingTMTest



if __name__ == '__main__':
  unittest.main()
