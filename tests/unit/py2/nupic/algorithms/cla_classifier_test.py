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

"""Unit tests for CLAClassifier module."""

CL_VERBOSITY = 0

import cPickle as pickle
import unittest2 as unittest

import numpy

from nupic.algorithms.CLAClassifier import CLAClassifier



class CLAClassifierTest(unittest.TestCase):
  """Unit tests for CLAClassifier class."""


  def setUp(self):
    self._classifier = CLAClassifier


  def testInitialization(self):
    c = self._classifier([1], 0.1, 0.1, 0)
    self.assertEqual(type(c), self._classifier)


  def testSingleValue(self):
    """Send same value 10 times and expect 100% likelihood for prediction."""
    classifier = self._classifier()

    # Enough times to perform Inference and learn associations
    retval = []
    for recordNum in xrange(10):
      retval = self._compute(classifier, recordNum, [1, 5], 0, 10)

    self._checkValue(retval, 0, 10, 1.)


  def testSingleValue0Steps(self):
    """Send same value 10 times and expect 100% likelihood for prediction 
    using 0-step ahead prediction"""
    classifier = self._classifier([0])

    # Enough times to perform Inference and learn associations
    retval = []
    for recordNum in xrange(10):
      retval = self._compute(classifier, recordNum, [1, 5], 0, 10)

    self.assertEqual(retval['actualValues'][0], 10)
    self.assertEqual(retval[0][0], 1.0)


  def testComputeResultTypes(self):
    c = self._classifier([1], 0.1, 0.1, 0)
    result = c.compute(recordNum=0,
                       patternNZ=[1, 5, 9],
                       classification= {'bucketIdx': 4, 'actValue': 34.7},
                       learn=True,
                       infer=True)
    self.assertSetEqual(set(result.keys()), set(('actualValues', 1)))
    self.assertEqual(type(result['actualValues']), list)
    self.assertEqual(len(result['actualValues']), 1)
    self.assertEqual(type(result['actualValues'][0]), float)
    self.assertEqual(type(result[1]), numpy.ndarray)
    self.assertEqual(result[1].itemsize, 8)
    self.assertAlmostEqual(result['actualValues'][0], 34.7, places=5)


  def testBucketIdxNumpyInt64Input(self):
    c = self._classifier([1], 0.1, 0.1, 0)
    result = c.compute(0, [1, 5, 9],
                       {'bucketIdx': numpy.int64(4), 'actValue': 34.7}, True,
                       True)
    self.assertSetEqual(set(result.keys()), set(('actualValues', 1)))
    self.assertEqual(len(result['actualValues']), 1)
    self.assertAlmostEqual(result['actualValues'][0], 34.7, places=5)


  def testCompute1(self):
    c = self._classifier([1], 0.1, 0.1, 0)
    result = c.compute(recordNum=0,
                       patternNZ=[1, 5, 9],
                       classification={'bucketIdx': 4, 'actValue': 34.7},
                       learn=True,
                       infer=True)
    self.assertSetEqual(set(result.keys()), set(('actualValues', 1)))
    self.assertEqual(len(result['actualValues']), 1)
    self.assertAlmostEqual(result['actualValues'][0], 34.7, places=5)


  def testCompute2(self):
    c = self._classifier([1], 0.1, 0.1, 0)
    c.compute(recordNum=0, patternNZ=[1, 5, 9],
              classification={'bucketIdx': 4, 'actValue': 34.7},
              learn=True, infer=True)
    result = c.compute(recordNum=1, patternNZ=[1, 5, 9],
                       classification={'bucketIdx': 4, 'actValue': 34.7},
                       learn=True, infer=True)
    self.assertSetEqual(set(result.keys()), set(('actualValues', 1)))
    self.assertAlmostEqual(result['actualValues'][4], 34.7, places=5)


  def testComputeComplex(self):
    c = self._classifier([1], 0.1, 0.1, 0)
    recordNum=0
    c.compute(recordNum=recordNum, patternNZ=[1, 5, 9],
              classification={'bucketIdx': 4, 'actValue': 34.7},
              learn=True, infer=True)
    recordNum += 1

    c.compute(recordNum=recordNum, patternNZ=[0, 6, 9, 11],
              classification={'bucketIdx': 5, 'actValue': 41.7},
              learn=True, infer=True)
    recordNum += 1

    c.compute(recordNum=recordNum, patternNZ=[6, 9],
              classification={'bucketIdx': 5, 'actValue': 44.9},
              learn=True, infer=True)
    recordNum += 1

    c.compute(recordNum=recordNum, patternNZ=[1, 5, 9],
              classification={'bucketIdx': 4, 'actValue': 42.9},
              learn=True, infer=True)
    recordNum += 1

    result = c.compute(recordNum=recordNum, patternNZ=[1, 5, 9],
              classification={'bucketIdx': 4, 'actValue': 34.7},
              learn=True, infer=True)
    recordNum += 1

    self.assertSetEqual(set(result.keys()), set(('actualValues', 1)))
    self.assertAlmostEqual(result['actualValues'][4], 35.520000457763672,
                           places=5)
    self.assertAlmostEqual(result['actualValues'][5], 42.020000457763672,
                           places=5)
    self.assertEqual(len(result[1]), 6)
    self.assertAlmostEqual(result[1][0], 0.0, places=5)
    self.assertAlmostEqual(result[1][1], 0.0, places=5)
    self.assertAlmostEqual(result[1][2], 0.0, places=5)
    self.assertAlmostEqual(result[1][3], 0.0, places=5)
    self.assertAlmostEqual(result[1][4], 0.12300123, places=5)
    self.assertAlmostEqual(result[1][5], 0.87699877, places=5)


  def testComputeWithMissingValue(self):
    c = self._classifier([1], 0.1, 0.1, 0)
    result = c.compute(
        recordNum=0, patternNZ=[1, 5, 9],
        classification={'bucketIdx': None, 'actValue': None}, learn=True,
        infer=True)

    self.assertSetEqual(set(result.keys()), set(('actualValues', 1)))
    self.assertEqual(len(result['actualValues']), 1)
    self.assertEqual(result['actualValues'][0], None)


  def testComputeCategory(self):
    c = self._classifier([1], 0.1, 0.1, 0)
    c.compute(recordNum=0, patternNZ=[1, 5, 9],
              classification={'bucketIdx': 4, 'actValue': 'D'},
              learn=True, infer=True)
    result = c.compute(recordNum=1, patternNZ=[1, 5, 9],
                       classification={'bucketIdx': 4, 'actValue': 'D'},
                       learn=True, infer=True)
    self.assertSetEqual(set(result.keys()), set(('actualValues', 1)))
    self.assertEqual(result['actualValues'][4], 'D')


  def testComputeCategory2(self):
    c = self._classifier([1], 0.1, 0.1, 0)
    c.compute(recordNum=0, patternNZ=[1, 5, 9],
              classification={'bucketIdx': 4, 'actValue': 'D'},
              learn=True, infer=True)
    result = c.compute(recordNum=1, patternNZ=[1, 5, 9],
                       classification={'bucketIdx': 4, 'actValue': 'E'},
                       learn=True, infer=True)
    self.assertSetEqual(set(result.keys()), set(('actualValues', 1)))
    self.assertEqual(result['actualValues'][4], 'D')


  def testSerialization(self):
    c = self._classifier([1], 0.1, 0.1, 0)
    c.compute(recordNum=0,
              patternNZ=[1, 5, 9],
              classification={'bucketIdx': 4, 'actValue': 34.7},
              learn=True, infer=True)
    c.compute(recordNum=1,
              patternNZ=[0, 6, 9, 11],
              classification={'bucketIdx': 5, 'actValue': 41.7},
              learn=True, infer=True)
    c.compute(recordNum=2,
              patternNZ=[6, 9],
              classification={'bucketIdx': 5, 'actValue': 44.9},
              learn=True, infer=True)
    c.compute(recordNum=3,
              patternNZ=[1, 5, 9],
              classification={'bucketIdx': 4, 'actValue': 42.9},
              learn=True, infer=True)
    serialized = pickle.dumps(c)
    c = pickle.loads(serialized)
    result = c.compute(recordNum=4,
              patternNZ=[1, 5, 9],
              classification={'bucketIdx': 4, 'actValue': 34.7},
              learn=True, infer=True)
    self.assertSetEqual(set(result.keys()), set(('actualValues', 1)))
    self.assertAlmostEqual(result['actualValues'][4], 35.520000457763672,
                           places=5)
    self.assertAlmostEqual(result['actualValues'][5], 42.020000457763672,
                           places=5)
    self.assertEqual(len(result[1]), 6)
    self.assertAlmostEqual(result[1][0], 0.0, places=5)
    self.assertAlmostEqual(result[1][1], 0.0, places=5)
    self.assertAlmostEqual(result[1][2], 0.0, places=5)
    self.assertAlmostEqual(result[1][3], 0.0, places=5)
    self.assertAlmostEqual(result[1][4], 0.12300123, places=5)
    self.assertAlmostEqual(result[1][5], 0.87699877, places=5)


  # Temporarily disabled until David's classifier change is submitted.
  def _testUnknownValues(self):
    classifier = self._classifier()

    # Single Unknown Value
    retval = self._compute(classifier, recordNum=0, pattern=[1, 5], bucket=9,
                           value=9)

    # Test with single value of 9->9 (should be 9 with 100%)
    self._checkValue(retval, 9, 9, 1.0)

    # Second Unknown Value
    retval = self._compute(classifier, recordNum=1, pattern=[2, 3], bucket=2,
                           value=2)

    # Should be both options with 50%
    self._checkValue(retval, 9, 9, 0.5)
    self._checkValue(retval, 2, 2, 0.5)


  def testOverlapPattern(self):
    classifier = self._classifier()

    _ = self._compute(classifier, recordNum=0, pattern=[1, 5], bucket=9,
                      value=9)
    _ = self._compute(classifier, recordNum=1, pattern=[1, 5], bucket=9,
                      value=9)
    retval = self._compute(classifier, recordNum=2, pattern=[3, 5], bucket=2,
                           value=2)

    # Since overlap - should be previous with 100%
    self._checkValue(retval, 9, 9, 1.0)

    retval = self._compute(classifier, recordNum=3, pattern=[3, 5], bucket=2,
                           value=2)
    # Second example: now new value should be more probable than old
    self.assertGreater(retval[1][2], retval[1][9])


  # TODO: Disabled because there are no assertions.
  def _testScaling(self):
    classifier = self._classifier()
    recordNum = 0
    for _ in range(100):
      _ = self._compute(classifier, recordNum=recordNum, pattern=[1],
                        bucket=5, value=5)
      recordNum += 1

    for _ in range(1000):
      _ = self._compute(classifier, recordNum=recordNum, pattern=[2],
                        bucket=9, value=9)
      recordNum += 1

    for _ in range(3):
      _retval = self._compute(classifier, recordNum=recordNum, pattern=[1, 5],
                              bucket=6, value=6)
      recordNum += 1

    #print retval


  def testMultistepSingleValue(self):
    classifier = self._classifier(steps=[1, 2])

    retval = []
    recordNum = 0
    for _ in range(10):
      retval = self._compute(classifier, recordNum=recordNum, pattern=[1, 5],
                             bucket=0, value=10)
      recordNum += 1

    # Only should return one actual value bucket.
    self.assertEqual(retval['actualValues'], [10])
    # Should have a probability of 100% for that bucket.
    self.assertEqual(retval[1], [1.])
    self.assertEqual(retval[2], [1.])


  def testMultistepSimple(self):
    classifier = self._classifier(steps=[1, 2])

    retval = []
    recordNum = 0
    for i in range(100):
      retval = self._compute(classifier, recordNum=recordNum, pattern=[i % 10],
                             bucket=i % 10, value=(i % 10) * 10)
      recordNum += 1

    # Only should return one actual value bucket.
    self.assertEqual(retval['actualValues'],
                     [0, 10, 20, 30, 40, 50, 60, 70, 80, 90])
    self.assertAlmostEqual(retval[1][0], 1.0)
    for i in xrange(1, 10):
      self.assertAlmostEqual(retval[1][i], 0.0)
    self.assertAlmostEqual(retval[2][1], 1.0)
    for i in [0] + range(2, 10):
      self.assertAlmostEqual(retval[2][i], 0.0)


  def testMissingRecords(self):
    """ Test missing record support.

    Here, we intend the classifier to learn the associations:
      [1,3,5] => bucketIdx 1
      [2,4,6] => bucketIdx 2
      [7,8,9] => don't care

    If it doesn't pay attention to the recordNums in this test, it will learn the
    wrong associations.
    """

    c = self._classifier([1], 0.1, 0.1, 0)
    recordNum = 0
    c.compute(recordNum=recordNum, patternNZ=[1, 3, 5],
              classification={'bucketIdx': 0, 'actValue': 0},
              learn=True, infer=True)
    recordNum += 1

    c.compute(recordNum=recordNum, patternNZ=[2, 4, 6],
              classification={'bucketIdx': 1, 'actValue': 1},
              learn=True, infer=True)
    recordNum += 1

    c.compute(recordNum=recordNum, patternNZ=[1, 3, 5],
              classification={'bucketIdx': 2, 'actValue': 2},
              learn=True, infer=True)
    recordNum += 1

    c.compute(recordNum=recordNum, patternNZ=[2, 4, 6],
              classification={'bucketIdx': 1, 'actValue': 1},
              learn=True, infer=True)
    recordNum += 1


    # -----------------------------------------------------------------------
    # At this point, we should have learned [1,3,5] => bucket 1
    #                                       [2,4,6] => bucket 2
    result = c.compute(recordNum=recordNum, patternNZ=[1, 3, 5],
              classification={'bucketIdx': 2, 'actValue': 2},
              learn=True, infer=True)
    recordNum += 1
    self.assertAlmostEqual(result[1][0], 0.0, places=5)
    self.assertAlmostEqual(result[1][1], 1.0, places=5)
    self.assertAlmostEqual(result[1][2], 0.0, places=5)

    result = c.compute(recordNum=recordNum, patternNZ=[2, 4, 6],
              classification={'bucketIdx': 1, 'actValue': 1},
              learn=True, infer=True)
    recordNum += 1
    self.assertAlmostEqual(result[1][0], 0.0, places=5)
    self.assertAlmostEqual(result[1][1], 0.0, places=5)
    self.assertAlmostEqual(result[1][2], 1.0, places=5)



    # -----------------------------------------------------------------------
    # Feed in records that skip and make sure they don't mess up what we
    #  learned
    # If we skip a record, the CLA should NOT learn that [2,4,6] from
    #  the previous learn associates with bucket 0
    recordNum += 1
    result = c.compute(recordNum=recordNum, patternNZ=[1, 3, 5],
              classification={'bucketIdx': 0, 'actValue': 0},
              learn=True, infer=True)
    recordNum += 1
    self.assertAlmostEqual(result[1][0], 0.0, places=5)
    self.assertAlmostEqual(result[1][1], 1.0, places=5)
    self.assertAlmostEqual(result[1][2], 0.0, places=5)

    # If we skip a record, the CLA should NOT learn that [1,3,5] from
    #  the previous learn associates with bucket 0
    recordNum += 1
    result = c.compute(recordNum=recordNum, patternNZ=[2, 4, 6],
              classification={'bucketIdx': 0, 'actValue': 0},
              learn=True, infer=True)
    recordNum += 1
    self.assertAlmostEqual(result[1][0], 0.0, places=5)
    self.assertAlmostEqual(result[1][1], 0.0, places=5)
    self.assertAlmostEqual(result[1][2], 1.0, places=5)

    # If we skip a record, the CLA should NOT learn that [2,4,6] from
    #  the previous learn associates with bucket 0
    recordNum += 1
    result = c.compute(recordNum=recordNum, patternNZ=[1, 3, 5],
              classification={'bucketIdx': 0, 'actValue': 0},
              learn=True, infer=True)
    recordNum += 1
    self.assertAlmostEqual(result[1][0], 0.0, places=5)
    self.assertAlmostEqual(result[1][1], 1.0, places=5)
    self.assertAlmostEqual(result[1][2], 0.0, places=5)


  def testMissingRecordInitialization(self):
    """
    Test missing record edge TestCase
    Test an edge case in the classifier initialization when there is a missing
    record in the first n records, where n is the # of prediction steps.
    """
    c = self._classifier([2], 0.1, 0.1, 0)
    result = c.compute(
        recordNum=0, patternNZ=[1, 5, 9],
        classification={'bucketIdx': 0, 'actValue': 34.7},
        learn=True, infer=True)

    result = c.compute(
        recordNum=2, patternNZ=[1, 5, 9],
        classification={'bucketIdx': 0, 'actValue': 34.7},
        learn=True, infer=True)

    self.assertSetEqual(set(result.keys()), set(('actualValues', 2)))
    self.assertEqual(len(result['actualValues']), 1)
    self.assertAlmostEqual(result['actualValues'][0], 34.7)


  def test_pFormatArray(self):
    from nupic.algorithms.CLAClassifier import _pFormatArray
    pretty = _pFormatArray(range(10))
    self.assertIsInstance(pretty, basestring)
    self.assertEqual(pretty[0], "[")
    self.assertEqual(pretty[-1], "]")
    self.assertEqual(len(pretty.split(" ")), 12)


  def _checkValue(self, retval, index, value, probability):
    self.assertEqual(retval['actualValues'][index], value)
    self.assertEqual(retval[1][index], probability)


  @staticmethod
  def _compute(classifier, recordNum, pattern, bucket, value):
    classification = {'bucketIdx': bucket, 'actValue': value}
    return classifier.compute(recordNum, pattern, classification, True, True)



if __name__ == '__main__':
  unittest.main()
