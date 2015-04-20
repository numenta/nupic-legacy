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

"""
Unit tests for functionsource.
"""

import unittest2 as unittest
import pickle

from nupic.data import FunctionSource

def dataFunction(stat):
  ret = {"reset": 0, "sequence": 0, "data": 0}
  if stat is not None:
    val = stat.get('val', 0) + 1
    ret["val"] = stat["val"] = val
  return ret

class FunctionSourceTest(unittest.TestCase):
  def testFunctionSource(self):
    fs = FunctionSource(dataFunction, state=None, resetFieldName=None, sequenceIdFieldName=None)
    self.assertIsNotNone(fs)
    r = fs.getNextRecordDict()
    self.assertIsNotNone(r)

  def testFunctionSourceReset(self):
    fs = FunctionSource(dataFunction, state=None, resetFieldName="reset", sequenceIdFieldName=None)
    self.assertIsNotNone(fs)
    r = fs.getNextRecordDict()
    self.assertIsNotNone(r)
      
  def testFunctionSourceSequence(self):
    fs = FunctionSource(dataFunction, state=None, resetFieldName=None, sequenceIdFieldName="sequence")
    self.assertIsNotNone(fs)
    r = fs.getNextRecordDict()
    self.assertIsNotNone(r)
      
  def testFunctionSourceResetAndSequence(self):
    fs = FunctionSource(dataFunction, state=None, resetFieldName="reset", sequenceIdFieldName="sequence")
    self.assertIsNotNone(fs)
    r = fs.getNextRecordDict()
    self.assertIsNotNone(r)
      
  def testFunctionSourceState(self):
    state = dict(val=100)
    fs = FunctionSource(dataFunction, state=state, resetFieldName="reset", sequenceIdFieldName="sequence")
    self.assertIsNotNone(fs)
    r = fs.getNextRecordDict()
    self.assertIsNotNone(r)
    r = fs.getNextRecordDict()
    r = fs.getNextRecordDict()
    self.assertEqual(103, state["val"])

  def testFunctionSourcePickle(self):
    state = dict(val=100)
    fs = FunctionSource(dataFunction, state=state, resetFieldName="reset", sequenceIdFieldName="sequence")
    self.assertIsNotNone(fs)
    r = fs.getNextRecordDict()    
    self.assertIsNotNone(r)
    
    pkl = pickle.dumps(fs)
    
    fs2 = pickle.loads(pkl)
    
    r = fs2.getNextRecordDict()
    r = fs2.getNextRecordDict()
    self.assertEqual(103, fs2.state["val"])

if __name__ == "__main__":
  unittest.main()
