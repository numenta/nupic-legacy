# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

from array import array



def bitsToString(arr):
  """Returns a string representing a numpy array of 0's and 1's"""
  s = array('c','.'*len(arr))
  for i in xrange(len(arr)):
    if arr[i] == 1:
      s[i]='*'
  return s

