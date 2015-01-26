#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

"""Unit tests for the FastCLAClassifier.

This test extends the test for the Python CLAClassifier to ensure that both
classifiers and their tests stay in sync.
"""

import unittest2 as unittest

from nupic.bindings.algorithms import FastCLAClassifier

# Don't import the CLAClassifierTest directly or the unittest.main() will pick
# it up and run it.
import cla_classifier_test



class FastCLAClassifierTest(cla_classifier_test.CLAClassifierTest):
  """Unit tests for FastCLAClassifier class."""


  def setUp(self):
    self._classifier = FastCLAClassifier



if __name__ == '__main__':
  unittest.main()
