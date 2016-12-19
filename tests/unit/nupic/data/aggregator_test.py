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

"""Unit tests for aggregator module."""

import unittest2 as unittest

from nupic.data import aggregator


class AggregatorTest(unittest.TestCase):
  """Unit tests for misc. aggregator functions."""

  def testFixAggregationDict(self):
    # Simplest case.
    result = aggregator._aggr_weighted_mean((1.0, 1.0), (1, 1))
    self.assertAlmostEqual(result, 1.0, places=7)
    # Simple non-uniform case.
    result = aggregator._aggr_weighted_mean((1.0, 2.0), (1, 2))
    self.assertAlmostEqual(result, 5.0/3.0, places=7)
    # Make sure it handles integer values as integers.
    result = aggregator._aggr_weighted_mean((1, 2), (1, 2))
    self.assertAlmostEqual(result, 1, places=7)
    # More-than-two case.
    result = aggregator._aggr_weighted_mean((1.0, 2.0, 3.0), (1, 2, 3))
    self.assertAlmostEqual(result, 14.0/6.0, places=7)
    # Handle zeros.
    result = aggregator._aggr_weighted_mean((1.0, 0.0, 3.0), (1, 2, 3))
    self.assertAlmostEqual(result, 10.0/6.0, places=7)
    # Handle negative numbers.
    result = aggregator._aggr_weighted_mean((1.0, -2.0, 3.0), (1, 2, 3))
    self.assertAlmostEqual(result, 1.0, places=7)


if __name__ == '__main__':
  unittest.main()
