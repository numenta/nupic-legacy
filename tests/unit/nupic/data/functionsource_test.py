# Copyright 2015 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""
Unit tests for functionsource.
"""

import pickle
import unittest

from nupic.data import FunctionSource



def dataFunction(stat):
  ret = {"reset": 0, "sequence": 0, "data": 0}
  if stat is not None:
    val = stat.get("val", 0) + 1
    ret["val"] = stat["val"] = val
  return ret

class FunctionSourceTest(unittest.TestCase):


  def testDefaultArgs(self):
    fs = FunctionSource(dataFunction, state=None, resetFieldName=None,
                        sequenceIdFieldName=None)
    self.assertIsNotNone(fs)
    r = fs.getNextRecordDict()
    self.assertIsNotNone(r)


  def testResetField(self):
    fs = FunctionSource(dataFunction, state=None, resetFieldName="reset",
                        sequenceIdFieldName=None)
    self.assertIsNotNone(fs)
    r = fs.getNextRecordDict()
    self.assertIsNotNone(r)


  def testSequenceField(self):
    fs = FunctionSource(dataFunction, state=None, resetFieldName=None,
                        sequenceIdFieldName="sequence")
    self.assertIsNotNone(fs)
    r = fs.getNextRecordDict()
    self.assertIsNotNone(r)


  def testResetAndSequenceFields(self):
    fs = FunctionSource(dataFunction, state=None, resetFieldName="reset",
                        sequenceIdFieldName="sequence")
    self.assertIsNotNone(fs)
    r = fs.getNextRecordDict()
    self.assertIsNotNone(r)


  def testState(self):
    state = dict(val=100)
    fs = FunctionSource(dataFunction, state=state, resetFieldName="reset",
                        sequenceIdFieldName="sequence")
    self.assertIsNotNone(fs)
    r = fs.getNextRecordDict()
    self.assertIsNotNone(r)
    r = fs.getNextRecordDict()
    r = fs.getNextRecordDict()
    self.assertEqual(103, state["val"])


  def testPickle(self):
    state = dict(val=100)
    fs = FunctionSource(dataFunction, state=state, resetFieldName="reset",
                        sequenceIdFieldName="sequence")
    self.assertIsNotNone(fs)
    r = fs.getNextRecordDict()
    self.assertIsNotNone(r)

    pkl = pickle.dumps(fs)
    self.assertIsNotNone(pkl)

    fs2 = pickle.loads(pkl)
    self.assertIsNotNone(fs2)

    r = fs2.getNextRecordDict()
    r = fs2.getNextRecordDict()
    self.assertEqual(103, fs2.state["val"])



if __name__ == "__main__":
  unittest.main()
