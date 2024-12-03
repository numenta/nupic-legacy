# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import unittest2 as unittest
from nupic.bindings.algorithms import SpatialPooler as CPPSpatialPooler

import spatial_pooler_py_api_test

spatial_pooler_py_api_test.SpatialPooler = CPPSpatialPooler
SpatialPoolerCPPAPITest = spatial_pooler_py_api_test.SpatialPoolerAPITest



if __name__ == "__main__":
  unittest.main()
