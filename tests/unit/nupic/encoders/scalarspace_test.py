# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""Unit tests for scalar space encoder"""

import unittest2 as unittest

from nupic.encoders.scalar_space import ScalarSpaceEncoder, DeltaEncoder



class ScalarSpaceEncoderTest(unittest.TestCase):
  '''Unit tests for ScalarSpaceEncoder class'''


  def testScalarSpaceEncoder(self):
    """scalar space encoder"""
    # use of forced=True is not recommended, but used in the example for readibility, see scalar.py
    sse = ScalarSpaceEncoder(1,1,2,False,2,1,1,None,0,False,"delta",
                             forced=True)
    self.assertTrue(isinstance(sse, DeltaEncoder))
    sse = ScalarSpaceEncoder(1,1,2,False,2,1,1,None,0,False,"absolute",
                             forced=True)
    self.assertFalse(isinstance(sse, DeltaEncoder))



if __name__ == '__main__':
  unittest.main()
