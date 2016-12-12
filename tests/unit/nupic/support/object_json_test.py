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

"""Unit tests for object_json module."""

import datetime
import StringIO

from nupic.data.inference_shifter import InferenceShifter
from nupic.swarming.hypersearch import object_json as json
from nupic.support.unittesthelpers.testcasebase import (TestCaseBase,
                                                        unittest)


class TestObjectJson(TestCaseBase):
  """Unit tests for object_json module."""

  def testPrimitives(self):
    self.assertEqual(json.loads(json.dumps(None)), None)
    self.assertEqual(json.loads(json.dumps(True)), True)
    self.assertEqual(json.loads(json.dumps(False)), False)
    self.assertEqual(json.loads(json.dumps(-5)), -5)
    self.assertEqual(json.loads(json.dumps(0)), 0)
    self.assertEqual(json.loads(json.dumps(5)), 5)
    self.assertEqual(json.loads(json.dumps(7.7)), 7.7)
    self.assertEqual(json.loads(json.dumps('hello')), 'hello')
    self.assertEqual(json.loads(json.dumps(5L)), 5L)
    self.assertEqual(json.loads(json.dumps(u'hello')), u'hello')
    self.assertEqual(json.loads(json.dumps([5, 6, 7])), [5, 6, 7])
    self.assertEqual(json.loads(json.dumps({'5': 6, '7': 8})), {'5': 6, '7': 8})

  def testDates(self):
    d = datetime.date(year=2012, month=9, day=25)
    serialized = json.dumps(d)
    self.assertEqual(serialized,
                     '{"py/object": "datetime.date", '
                     '"py/repr": "datetime.date(2012, 9, 25)"}')
    deserialized = json.loads(serialized)
    self.assertEqual(type(deserialized), datetime.date)
    self.assertEqual(deserialized.isoformat(), d.isoformat())

  def testDatetimes(self):
    d = datetime.datetime(year=2012, month=9, day=25, hour=14, minute=33,
                          second=8, microsecond=455969)
    serialized = json.dumps(d)
    self.assertEqual(serialized,
                     '{"py/object": "datetime.datetime", "py/repr": '
                     '"datetime.datetime(2012, 9, 25, 14, 33, 8, 455969)"}')
    deserialized = json.loads(serialized)
    self.assertEqual(type(deserialized), datetime.datetime)
    self.assertEqual(deserialized.isoformat(), d.isoformat())

  def testDumpsTuple(self):
    self.assertEqual(json.dumps((5, 6, 7)), '{"py/tuple": [5, 6, 7]}')

  def testTuple(self):
    self.assertTupleEqual(json.loads(json.dumps((5, 6, 7))), (5, 6, 7))

  def testComplex(self):
    self.assertEqual(json.loads(json.dumps(2 + 1j)), 2 + 1j)

  def testBasicDumps(self):
    d = {'a': 1, 'b': {'c': 2}}
    s = json.dumps(d, sort_keys=True)
    self.assertEqual(s, '{"a": 1, "b": {"c": 2}}')

  def testDumpsWithIndent(self):
    d = {'a': 1, 'b': {'c': 2}}
    s = json.dumps(d, indent=2, sort_keys=True)
    self.assertEqual(s, '{\n  "a": 1,\n  "b": {\n    "c": 2\n  }\n}')

  def testDump(self):
    d = {'a': 1, 'b': {'c': 2}}
    f = StringIO.StringIO()
    json.dump(d, f)
    self.assertEqual(f.getvalue(), '{"a": 1, "b": {"c": 2}}')

  def testLoads(self):
    s = '{"a": 1, "b": {"c": 2}}'
    d = json.loads(s)
    self.assertDictEqual(d, {'a': 1, 'b': {'c': 2}})

  def testLoadsWithIndent(self):
    s = '{\n  "a": 1,\n  "b": {\n    "c": 2\n  }\n}'
    d = json.loads(s)
    self.assertDictEqual(d, {'a': 1, 'b': {'c': 2}})

  def testLoad(self):
    f = StringIO.StringIO('{"a": 1, "b": {"c": 2}}')
    d = json.load(f)
    self.assertDictEqual(d, {'a': 1, 'b': {'c': 2}})

  def testNonStringKeys(self):
    original = {1.1: 1, 5: {(7, 8, 9): {1.1: 5}}}
    result = json.loads(json.dumps(original))
    self.assertEqual(original, result)

  def testDumpsObject(self):
    testClass = InferenceShifter()
    testClass.a = 5
    testClass.b = {'b': (17,)}
    encoded = json.dumps(testClass, sort_keys=True)
    self.assertEqual(
        encoded,
        '{"_inferenceBuffer": null, "a": 5, "b": {"b": {"py/tuple": [17]}}, '
        '"py/object": "nupic.data.inference_shifter.InferenceShifter"}')

  def testObjectWithNonStringKeys(self):
    testClass = InferenceShifter()
    testClass.a = 5
    testClass.b = {(4, 5): (17,)}
    encoded = json.dumps(testClass, sort_keys=True)
    self.assertEqual(
        encoded,
        '{"_inferenceBuffer": null, "a": 5, "b": {"py/dict/keys": '
        '["{\\"py/tuple\\": [4, 5]}"], "{\\"py/tuple\\": [4, 5]}": '
        '{"py/tuple": [17]}}, "py/object": '
        '"nupic.data.inference_shifter.InferenceShifter"}')
    decoded = json.loads(encoded)
    self.assertEqual(decoded.a, 5)
    self.assertEqual(type(decoded.b), dict)
    self.assertEqual(len(decoded.b.keys()), 1)
    self.assertTupleEqual(decoded.b.keys()[0], (4, 5))
    self.assertTupleEqual(decoded.b[(4, 5)], (17,))


if __name__ == '__main__':
  unittest.main()
