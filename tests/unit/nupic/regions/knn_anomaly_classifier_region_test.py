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

"""Unit tests for the clamodel module."""

import sys
import copy
from datetime import datetime
import unittest2 as unittest
import numpy
from mock import Mock, patch, ANY, call

from nupic.support.unittesthelpers.testcasebase import (unittest,
                                                        TestOptionParser)
from nupic.frameworks.opf.opfutils import InferenceType

from nupic.regions.KNNAnomalyClassifierRegion import (
    KNNAnomalyClassifierRegion,
    _CLAClassificationRecord)

from nupic.frameworks.opf.opfutils import InferenceType

from nupic.frameworks.opf.exceptions import (CLAModelInvalidRangeError)



class KNNAnomalyClassifierRegionTest(unittest.TestCase):
  """KNNAnomalyClassifierRegion unit tests."""
  def setUp(self):

    self.params = dict(
                  trainRecords=10,
                  anomalyThreshold=1.1,
                  cacheSize=10000,
                  k=1,
                  distanceMethod='rawOverlap',
                  distanceNorm=1,
                  doBinarization=1,
                  replaceDuplicates=0,
                  maxStoredPatterns=1000)

    self.helper = KNNAnomalyClassifierRegion(**self.params)


  def testInit(self):

    params = dict(
                  trainRecords=100,
                  anomalyThreshold=101,
                  cacheSize=102,
                  classificationVectorType=1,
                  k=1,
                  distanceMethod='rawOverlap',
                  distanceNorm=1,
                  doBinarization=1,
                  replaceDuplicates=0,
                  maxStoredPatterns=1000)
    
    helper = KNNAnomalyClassifierRegion(**params)

    self.assertEqual(helper.trainRecords, params['trainRecords'])
    self.assertEqual(helper.anomalyThreshold, params['anomalyThreshold'])
    self.assertEqual(helper.cacheSize, params['cacheSize'])
    self.assertEqual(helper.classificationVectorType,
        params['classificationVectorType'])


  @patch.object(KNNAnomalyClassifierRegion, 'classifyState')
  @patch.object(KNNAnomalyClassifierRegion, 'getParameter')
  @patch.object(KNNAnomalyClassifierRegion, 'constructClassificationRecord')
  def testCompute(self, constructRecord, getParam, classifyState):
    params = {
      'trainRecords': 0
    }
    getParam.side_effect = params.get
    state = {
      "ROWID": 0,
      "anomalyScore": 1.0,
      "anomalyVector": [1,4,5],
      "anomalyLabel": "Label"
    }
    record = _CLAClassificationRecord(**state)
    constructRecord.return_value = record
    self.helper.compute(dict(), dict())
    classifyState.assert_called_once_with(record)
    self.assertEqual(self.helper.labelResults, state['anomalyLabel'])
    

  def testGetLabels(self):
    # No _recordsCache
    self.helper._recordsCache = []
    self.assertEqual(self.helper.getLabels(), \
      {'isProcessing': False, 'recordLabels': []})

    # Invalid ranges
    self.helper._recordsCache = [Mock(ROWID=10)]
    self.assertRaises(CLAModelInvalidRangeError,
      self.helper.getLabels, start=100, end=100)

    self.helper._recordsCache = [Mock(ROWID=10)]
    self.assertRaises(CLAModelInvalidRangeError,
      self.helper.getLabels, start=-100, end=-100)

    self.helper._recordsCache = [Mock(ROWID=10)]
    self.assertRaises(CLAModelInvalidRangeError,
      self.helper.getLabels, start=100, end=-100)

    # Valid no threshold labels
    values = {
      'categoryRecencyList': [4, 5, 7],
    }
    self.helper.saved_categories = ['TestCategory']
    categoryList = [1, 1, 1]
    classifier = self.helper._knnclassifier
    classifier.getParameter = Mock(side_effect=values.get)
    classifier._knn._categoryList = categoryList

    results = self.helper.getLabels()
    self.assertTrue('isProcessing' in results)
    self.assertTrue('recordLabels' in results)
    self.assertEqual(len(results['recordLabels']),
      len(values['categoryRecencyList']))
    for record in results['recordLabels']:
      self.assertTrue(record['ROWID'] in values['categoryRecencyList'])
      self.assertEqual(record['labels'], self.helper.saved_categories)



  @patch.object(KNNAnomalyClassifierRegion, '_getStateAnomalyVector')
  @patch.object(KNNAnomalyClassifierRegion, 'constructClassificationRecord')
  @patch.object(KNNAnomalyClassifierRegion, 'classifyState')
  def testAddLabel(self, classifyState, constructVector, getVector):
    # Setup Mocks
    getVector.return_value = numpy.array([0, 0, 0, 1, 0, 0, 1])
    knn = self.helper._knnclassifier._knn
    knn.learn = Mock()

    # Invalid ranges
    self.helper._recordsCache = []
    self.assertRaises(CLAModelInvalidRangeError,
      self.helper.addLabel, start=100, end=100, labelName="test")
    
    self.helper._recordsCache = [Mock(ROWID=10)]
    self.assertRaises(CLAModelInvalidRangeError,
      self.helper.addLabel, start=100, end=100, labelName="test")

    self.helper._recordsCache = [Mock(ROWID=10)]
    self.assertRaises(CLAModelInvalidRangeError,
      self.helper.addLabel, start=-100, end=-100, labelName="test")

    self.helper._recordsCache = [Mock(ROWID=10)]
    self.assertRaises(CLAModelInvalidRangeError,
      self.helper.addLabel, start=100, end=-100, labelName="test")

    # Valid no threshold labels
    self.helper._recordsCache = [
      Mock(ROWID=10, anomalyLabel=["Test"], setByUser=False),
      Mock(ROWID=11, anomalyLabel=[], setByUser=False),
      Mock(ROWID=12, anomalyLabel=["Test"], setByUser=True)]
    results = self.helper.addLabel(11, 12, "Added")

    # Verifies records were updated
    self.assertEqual(results, None)
    self.assertTrue('Added' in self.helper._recordsCache[1].anomalyLabel)
    self.assertTrue(self.helper._recordsCache[1].setByUser)
    
    # Verifies record added to KNN classifier
    knn.learn.assert_called_once_with(ANY, ANY, rowID=11)
    
    # Verifies records after added label is recomputed
    classifyState.assert_called_once_with(self.helper._recordsCache[2])


  @patch.object(KNNAnomalyClassifierRegion, 'constructClassificationRecord')
  @patch.object(KNNAnomalyClassifierRegion, 'classifyState')
  def testRemoveLabel(self, classifyState, constructClassificationRecord):
    knn = self.helper._knnclassifier._knn
    knn._numPatterns = 3
    knn._categoryRecencyList = [10, 11, 12]
    knn.removeIds = Mock(side_effect = self.mockRemoveIds)
      
    self.helper._recordsCache = []
    self.assertRaises(CLAModelInvalidRangeError,
      self.helper.removeLabels,)

    # Invalid ranges
    self.helper._recordsCache = [Mock(ROWID=10)]
    self.assertRaises(CLAModelInvalidRangeError,
      self.helper.removeLabels, start=100, end=100)

    self.helper._recordsCache = [Mock(ROWID=10)]
    self.assertRaises(CLAModelInvalidRangeError,
      self.helper.removeLabels, start=-100, end=-100)

    self.helper._recordsCache = [Mock(ROWID=10)]
    self.assertRaises(CLAModelInvalidRangeError,
      self.helper.removeLabels, start=100, end=-100)

    # Valid no threshold labels
    self.helper._recordsCache = [
      Mock(ROWID=10, anomalyLabel=["Test"], setByUser=False),
      Mock(ROWID=11, anomalyLabel=["Test"], setByUser=False),
      Mock(ROWID=12, anomalyLabel=["Test"], setByUser=True)]
    results = self.helper.removeLabels(11, 12, "Test")

    self.assertEqual(results, None)
    self.assertTrue('Test' not in self.helper._recordsCache[1].anomalyLabel)
    
    # Verifies records removed from KNN classifier
    self.assertEqual(knn.removeIds.mock_calls, [call([11]), call([])])

    # Verifies records after removed record are updated
    classifyState.assert_called_once_with(self.helper._recordsCache[2])


  @patch.object(KNNAnomalyClassifierRegion, 'constructClassificationRecord')
  @patch.object(KNNAnomalyClassifierRegion, 'classifyState')
  def testRemoveLabelNoFilter(self, classifyState,
      constructClassificationRecord):
    knn = self.helper._knnclassifier._knn
    knn._numPatterns = 3
    knn._categoryRecencyList = [10, 11, 12]
    knn.removeIds = Mock(side_effect=self.mockRemoveIds)

    # Valid no threshold labels
    self.helper._recordsCache = [
      Mock(ROWID=10, anomalyLabel=["Test"], setByUser=False),
      Mock(ROWID=11, anomalyLabel=["Test"], setByUser=False),
      Mock(ROWID=12, anomalyLabel=["Test"], setByUser=True)]
    results = self.helper.removeLabels(11, 12)

    self.assertEqual(results, None)
    self.assertTrue('Test' not in self.helper._recordsCache[1].anomalyLabel)
    
    # Verifies records removed from KNN classifier
    self.assertEqual(knn.removeIds.mock_calls, [call([11]), call([])])

    # Verifies records after removed record are updated
    classifyState.assert_called_once_with(self.helper._recordsCache[2])


  @patch.object(KNNAnomalyClassifierRegion, 'classifyState')
  def testSetGetThreshold(self, classifyState):
    self.helper._recordsCache = [Mock(), Mock(), Mock()]
    
    self.helper.setParameter('anomalyThreshold', None, 1.0)
    
    self.assertAlmostEqual(self.helper.anomalyThreshold, 1.0)
    self.assertEqual(len(classifyState.mock_calls),
        len(self.helper._recordsCache))

    self.assertAlmostEqual(self.helper.getParameter('anomalyThreshold'), 1.0)

    self.assertRaises(Exception, self.helper.setParameter,
        'anomalyThreshold', None, 'invalid')


  @patch.object(KNNAnomalyClassifierRegion, 'classifyState')
  def testSetGetWaitRecords(self, classifyState):
    self.helper._recordsCache = [
      Mock(ROWID=10, anomalyLabel=["Test"], setByUser=False),
      Mock(ROWID=11, anomalyLabel=["Test"], setByUser=False),
      Mock(ROWID=12, anomalyLabel=["Test"], setByUser=True)]
    
    self.helper.setParameter('trainRecords', None, 20)
    
    self.assertEqual(self.helper.trainRecords, 20)
    self.assertEqual(len(classifyState.mock_calls),
        len(self.helper._recordsCache))

    self.assertEqual(self.helper.getParameter('trainRecords'), 20)

    # Test invalid parameter type
    self.assertRaises(Exception, self.helper.setParameter,
      'trainRecords', None, 'invalid')

    # Test invalid value before first record ROWID in cache
    state = {
      "ROWID": 1000,
      "anomalyScore": 1.0,
      "anomalyVector": [1,4,5],
      "anomalyLabel": "Label"
    }
    record = _CLAClassificationRecord(**state)
    self.helper._recordsCache = [state]
    self.assertRaises(Exception, self.helper.setParameter,
      'trainRecords', None, 0)


  @patch.object(KNNAnomalyClassifierRegion, 'constructClassificationRecord')
  def testSetGetWaitRecordsRecalculate(self, getRecord):
    """
    This test ensures that records in classifier are removed when they are no
    longer being used when the trainRecords is set.
    """
    self.helper.cacheSize = 5
    self.helper.anomalyThreshold = 0.8

    self.helper._anomalyVectorLength = 20
    records = [
      Mock(ROWID=10, anomalyLabel=["Test"], anomalyScore=1, setByUser=False, anomalyVector=numpy.array([1,4])),
      Mock(ROWID=11, anomalyLabel=["Test"], anomalyScore=0, setByUser=False, anomalyVector=numpy.array([1,2])),
      Mock(ROWID=12, anomalyLabel=["Test"], anomalyScore=0, setByUser=False, anomalyVector=numpy.array([1,4])),
      Mock(ROWID=13, anomalyLabel=["Test"], anomalyScore=0, setByUser=False, anomalyVector=numpy.array([1,2,6,7])),
      Mock(ROWID=14, anomalyLabel=["Test"], anomalyScore=1, setByUser=False, anomalyVector=numpy.array([1,10])),
      Mock(ROWID=15, anomalyLabel=["Test"], anomalyScore=0, setByUser=False, anomalyVector=numpy.array([1,3])),
      Mock(ROWID=16, anomalyLabel=["Test"], anomalyScore=0, setByUser=False, anomalyVector=numpy.array([1,4])),
      Mock(ROWID=17, anomalyLabel=["Test"], anomalyScore=0, setByUser=False, anomalyVector=numpy.array([10])),
      Mock(ROWID=18, anomalyLabel=["Test"], anomalyScore=0, setByUser=False, anomalyVector=numpy.array([1,4]))]

    getRecord.side_effect = records

    for i in records:
      self.helper.compute(dict(), dict())


    self.assertEqual(self.helper._knnclassifier._knn._numPatterns, 6)
    self.assertEqual(
        self.helper._knnclassifier.getParameter('categoryRecencyList'),
        [10, 12, 14, 16, 17, 18],
        "Classifier incorrectly classified test records."
    )
    
    # Now set trainRecords and should remove the labels outside of cache
    # and relabel points.
    self.helper.setParameter('trainRecords', None, 14)

    self.assertEqual(self.helper._knnclassifier._knn._numPatterns, 2)
    self.assertEqual(
        self.helper._knnclassifier.getParameter('categoryRecencyList'),
        [14, 17],
        "Classifier incorrectly reclassified test records after setting "
        "trainRecords")


  @patch.object(KNNAnomalyClassifierRegion, '_addRecordToKNN')
  @patch.object(KNNAnomalyClassifierRegion, '_deleteRecordsFromKNN')
  @patch.object(KNNAnomalyClassifierRegion, '_recomputeRecordFromKNN')
  @patch.object(KNNAnomalyClassifierRegion, '_categoryToLabelList')
  def testUpdateState(self, toLabelList, recompute, deleteRecord, addRecord):
    record = {
      "ROWID": 0,
      "anomalyScore": 1.0,
      "anomalyVector": "",
      "anomalyLabel": ["Label"],
      "setByUser": False
    }

    # Test record not labeled and not above threshold
    deleteRecord.reset_mock()
    addRecord.reset_mock()
    self.helper.trainRecords = 0
    self.helper.anomalyThreshold = 1.1
    toLabelList.return_value = []
    state = _CLAClassificationRecord(**record)
    self.helper.classifyState(state)
    self.assertEqual(state.anomalyLabel, [])
    deleteRecord.assert_called_once_with([state])

    # Test record not labeled and above threshold
    deleteRecord.reset_mock()
    addRecord.reset_mock()
    self.helper.anomalyThreshold = 0.5
    toLabelList.return_value = []
    state = _CLAClassificationRecord(**record)
    self.helper.classifyState(state)
    
    self.assertEqual(state.anomalyLabel, \
      [KNNAnomalyClassifierRegion.AUTO_THRESHOLD_CLASSIFIED_LABEL])
    addRecord.assert_called_once_with(state)

    # Test record not labeled and above threshold during wait period
    deleteRecord.reset_mock()
    addRecord.reset_mock()
    self.helper.trainRecords = 10
    self.helper.anomalyThreshold = 0.5
    toLabelList.return_value = []
    state = _CLAClassificationRecord(**record)
    self.helper.classifyState(state)
    
    self.assertEqual(state.anomalyLabel, [])
    self.assertTrue(not addRecord.called)

    # Test record labeled and not above threshold
    deleteRecord.reset_mock()
    addRecord.reset_mock()
    self.helper.trainRecords = 0
    self.helper.anomalyThreshold = 1.1
    toLabelList.return_value = ["Label"]
    state = _CLAClassificationRecord(**record)
    self.helper.classifyState(state)
    self.assertEqual(state.anomalyLabel, ["Label"])
    self.assertTrue(not addRecord.called)

    # Test setByUser
    deleteRecord.reset_mock()
    addRecord.reset_mock()
    self.helper.anomalyThreshold = 1.1
    toLabelList.return_value = ["Label 2"]
    recordCopy = copy.deepcopy(record)
    recordCopy['setByUser'] = True
    state = _CLAClassificationRecord(**recordCopy)
    self.helper.classifyState(state)
    self.assertEqual(state.anomalyLabel,
      [recordCopy["anomalyLabel"][0], toLabelList.return_value[0]])
    addRecord.assert_called_once_with(state)

    # Test removal of above threshold
    deleteRecord.reset_mock()
    addRecord.reset_mock()
    self.helper.anomalyThreshold = 1.1
    toLabelList.return_value = []
    recordCopy = copy.deepcopy(record)
    recordCopy['setByUser'] = True
    recordCopy['anomalyLabel'] = \
      [KNNAnomalyClassifierRegion.AUTO_THRESHOLD_CLASSIFIED_LABEL,
       KNNAnomalyClassifierRegion.AUTO_THRESHOLD_CLASSIFIED_LABEL + \
        KNNAnomalyClassifierRegion.AUTO_TAG]
    state = _CLAClassificationRecord(**recordCopy)
    self.helper.classifyState(state)
    self.assertEqual(state.anomalyLabel, [])

    # Auto classified threshold
    deleteRecord.reset_mock()
    addRecord.reset_mock()
    self.helper.anomalyThreshold = 1.1
    toLabelList.return_value = \
      [KNNAnomalyClassifierRegion.AUTO_THRESHOLD_CLASSIFIED_LABEL]
    recordCopy = copy.deepcopy(record)
    recordCopy['setByUser'] = True
    recordCopy['anomalyLabel'] = \
      [KNNAnomalyClassifierRegion.AUTO_THRESHOLD_CLASSIFIED_LABEL]
    state = _CLAClassificationRecord(**recordCopy)
    self.helper.classifyState(state)
    self.assertEqual(state.anomalyLabel,
      [KNNAnomalyClassifierRegion.AUTO_THRESHOLD_CLASSIFIED_LABEL + \
        KNNAnomalyClassifierRegion.AUTO_TAG])
    addRecord.assert_called_once_with(state)

    # Test precedence of threshold label above auto threshold label
    deleteRecord.reset_mock()
    addRecord.reset_mock()
    self.helper.anomalyThreshold = 0.8
    toLabelList.return_value = \
      [KNNAnomalyClassifierRegion.AUTO_THRESHOLD_CLASSIFIED_LABEL,
        KNNAnomalyClassifierRegion.AUTO_THRESHOLD_CLASSIFIED_LABEL + \
        KNNAnomalyClassifierRegion.AUTO_TAG]
    recordCopy = copy.deepcopy(record)
    recordCopy['setByUser'] = True
    recordCopy['anomalyLabel'] = \
      [KNNAnomalyClassifierRegion.AUTO_THRESHOLD_CLASSIFIED_LABEL]
    state = _CLAClassificationRecord(**recordCopy)
    self.helper.classifyState(state)
    self.assertEqual(state.anomalyLabel,
      [KNNAnomalyClassifierRegion.AUTO_THRESHOLD_CLASSIFIED_LABEL])
    addRecord.assert_called_once_with(state)


  @patch.object(KNNAnomalyClassifierRegion, '_getStateAnomalyVector')
  def testAddRecordToKNN(self, getAnomalyVector):
    getAnomalyVector.return_value = numpy.array([0, 1, 0, 0, 1, 0, 1, 1])
    values = {
      'categoryRecencyList': [1, 2, 3]
    }
    classifier = self.helper._knnclassifier
    classifier.getParameter = Mock(side_effect=values.get)
    classifier._knn.learn = Mock()
    classifier._knn.prototypeSetCategory = Mock()
    state = {
      "ROWID": 5,
      "anomalyScore": 1.0,
      "anomalyVector": numpy.array([1, 5, 7, 8]),
      "anomalyLabel": ["Label"],
      "setByUser": False
    }
    record = _CLAClassificationRecord(**state)

    # Test with record not already in KNN
    self.helper._addRecordToKNN(record)
    classifier._knn.learn.assert_called_once_with(getAnomalyVector.return_value,
        ANY, rowID=state['ROWID'])
    self.assertTrue(not classifier._knn.prototypeSetCategory.called)
    classifier._knn.learn.reset_mock()

    # Test with record already in KNN
    values = {
      'categoryRecencyList': [1, 2, 3, 5]
    }
    classifier.getParameter.side_effect = values.get
    self.helper._addRecordToKNN(record)
    classifier._knn.prototypeSetCategory.assert_called_once_with(
        state['ROWID'], ANY)
    self.assertTrue(not classifier._knn.learn.called)


  @patch.object(KNNAnomalyClassifierRegion, '_getStateAnomalyVector')
  def testDeleteRangeFromKNN(self, getAnomalyVector):
    getAnomalyVector.return_value = "Vector"
    values = {
      'categoryRecencyList': [1, 2, 3]
    }
    classifier = self.helper._knnclassifier
    classifier.getParameter = Mock(side_effect=values.get)
    classifier._knn._numPatterns = len(values['categoryRecencyList'])
    classifier._knn.removeIds = Mock(side_effect=self.mockRemoveIds)

    # Test with record not already in KNN
    self.helper._deleteRangeFromKNN(start=1, end=3)
    classifier._knn.removeIds.assert_called_once_with([1, 2])
    classifier._knn.removeIds.reset_mock()

    # Test with record already in KNN
    values = {
      'categoryRecencyList': [1, 2, 3, 5]
    }
    classifier.getParameter.side_effect = values.get
    self.helper._deleteRangeFromKNN(start=1)
    classifier._knn.removeIds.assert_called_once_with([1, 2, 3, 5])
    

  @patch.object(KNNAnomalyClassifierRegion, '_getStateAnomalyVector')
  def testRecomputeRecordFromKNN(self, getAnomalyVector):
    getAnomalyVector.return_value = "Vector"
    self.helper.trainRecords = 0
    values = {
      'categoryRecencyList': [1, 2, 3, 5, 6, 7, 8, 9],
      'latestDists': numpy.array([0.7, 0.2, 0.5, 1, 0.3, 0.2, 0.1]),
      'categories': ['A','B','C','D','E','F','G']
    }
    classifier = self.helper._knnclassifier
    classifier.getLatestDistances = Mock(return_value=values['latestDists'])
    classifier.getCategoryList = Mock(return_value=values['categories'])
    classifier.getParameter = Mock(side_effect=values.get)
    classifier.setParameter = Mock()
    classifier.compute = Mock()
    state = {
      "ROWID": 5,
      "anomalyScore": 1.0,
      "anomalyVector": "",
      "anomalyLabel": ["Label"],
      "setByUser": False
    }
    record = _CLAClassificationRecord(**state)

    # Test finding best category before record - exists
    self.helper._classificationMaxDist = 0.4
    self.helper._autoDetectWaitRecords = 0
    result = self.helper._recomputeRecordFromKNN(record)
    self.assertEqual(result, 'B')

    # Test finding best category before record - does not exists
    self.helper._classificationMaxDist = 0.1
    result = self.helper._recomputeRecordFromKNN(record)
    self.assertEqual(result, None)

    # Test finding best category before record - not record before
    record.ROWID = 0
    self.helper._classificationMaxDist = 0.1
    result = self.helper._recomputeRecordFromKNN(record)
    self.assertEqual(result, None)


  def testConstructClassificationVector(self):
    modelParams = {
      '__numRunCalls': 0
    }
    spVals = {
      'params': {
        'activeOutputCount': 5
      },
      'output': {
        'bottomUpOut': numpy.array([1, 1, 0, 0, 1])
      }
    }
    tpVals = {
      'params': {
        'cellsPerColumn': 2,
        'columnCount': 2
      },
      'output': {
        'lrnActive': numpy.array([1, 0, 0, 1]),
        'topDownOut': numpy.array([1, 0, 0, 0, 1])
      }
    }
    inputs = dict(
      spBottomUpOut=spVals['output']['bottomUpOut'],
      tpTopDownOut=tpVals['output']['topDownOut'],
      tpLrnActiveStateT=tpVals['output']['lrnActive']
    )

    self.helper._activeColumnCount = 5
    
    # Test TP Cell vector
    self.helper.classificationVectorType = 1
    vector = self.helper.constructClassificationRecord(inputs)
    self.assertEqual(vector.anomalyVector,
        tpVals['output']['lrnActive'].nonzero()[0].tolist())

    # Test SP and TP Column Error vector
    self.helper.classificationVectorType = 2
    self.helper._prevPredictedColumns = numpy.array(
        [1, 0, 0, 0, 1]).nonzero()[0]
    vector = self.helper.constructClassificationRecord(inputs)
    self.assertEqual(vector.anomalyVector, [0, 1, 4])

    self.helper._prevPredictedColumns = numpy.array(
        [1, 0, 1, 0, 0]).nonzero()[0]
    vector = self.helper.constructClassificationRecord(inputs)
    self.assertEqual(vector.anomalyVector, [0, 1, 4, 7])

    self.helper.classificationVectorType = 3
    self.assertRaises(TypeError, self.helper.constructClassificationRecord,
        inputs)


  @patch.object(KNNAnomalyClassifierRegion ,'classifyState')
  @patch.object(KNNAnomalyClassifierRegion, 'constructClassificationRecord')
  def testCompute(self, createRecord, updateState):
    state = {
      "ROWID": 0,
      "anomalyScore": 1.0,
      "anomalyVector": numpy.array([1, 0, 0, 0, 1]),
      "anomalyLabel": "Label"
    }
    record = _CLAClassificationRecord(**state)
    createRecord.return_value = record

    inputs = dict()
    outputs=  dict()

    # Test add first record
    self.helper.cacheSize = 10
    self.helper.trainRecords = 0
    self.helper._recordsCache = []
    self.helper.compute(inputs, outputs)
    self.assertEqual(self.helper._recordsCache[-1], record)
    self.assertEqual(len(self.helper._recordsCache), 1)
    updateState.assert_called_once_with(self.helper._recordsCache[-1])

    # Test add record before wait records
    updateState.reset_mock()
    self.helper.cacheSize = 10
    self.helper.trainRecords = 10
    self.helper._recordsCache = []
    self.helper.compute(inputs, outputs)
    self.assertEqual(self.helper._recordsCache[-1], record)
    self.assertEqual(len(self.helper._recordsCache), 1)
    self.helper.compute(inputs, outputs)
    self.assertEqual(self.helper._recordsCache[-1], record)
    self.assertEqual(len(self.helper._recordsCache), 2)
    self.assertTrue(not updateState.called)

    # Test exceeded cache length
    updateState.reset_mock()
    self.helper.cacheSize = 1
    self.helper._recordsCache = []
    self.helper.compute(inputs, outputs)
    self.assertEqual(self.helper._recordsCache[-1], record)
    self.assertEqual(len(self.helper._recordsCache), 1)
    self.helper.compute(inputs, outputs)
    self.assertEqual(self.helper._recordsCache[-1], record)
    self.assertEqual(len(self.helper._recordsCache), 1)
    self.assertTrue(not updateState.called)


  def testCategoryToList(self):
    result = self.helper._categoryToLabelList(None)
    self.assertEqual(result, [])

    self.helper.saved_categories = ['A', 'B', 'C']
    result = self.helper._categoryToLabelList(1)
    self.assertEqual(result, ['A'])

    result = self.helper._categoryToLabelList(4)
    self.assertEqual(result, ['C'])

    result = self.helper._categoryToLabelList(5)
    self.assertEqual(result, ['A','C'])


  def testGetAnomalyVector(self):
    state = {
      "ROWID": 0,
      "anomalyScore": 1.0,
      "anomalyVector": [1,4,5],
      "anomalyLabel": "Label"
    }
    record = _CLAClassificationRecord(**state)
    self.helper._anomalyVectorLength = 10
    vector = self.helper._getStateAnomalyVector(record)

    self.assertEqual(len(vector), self.helper._anomalyVectorLength)
    self.assertEqual(vector.nonzero()[0].tolist(), record.anomalyVector)


  # Tests for configuration
  # ===========================================================================

  def testSetState(self):
    # No Version set
    state = dict(_classificationDelay=100)
    state['_knnclassifierProps'] = self.params
    self.helper._vectorType = None
    self.helper.__setstate__(state)
    self.assertEqual(self.helper.classificationVectorType, 1)
    self.assertEqual(self.helper._version,
        KNNAnomalyClassifierRegion.__VERSION__)

    # Version 1
    state = dict(_version=1, _classificationDelay=100)
    state['_knnclassifierProps'] = self.params
    self.helper.__setstate__(state)
    self.assertEqual(self.helper._version,
        KNNAnomalyClassifierRegion.__VERSION__)

    # Invalid Version
    state = dict(_version="invalid")
    state['_knnclassifierProps'] = self.params
    self.assertRaises(Exception, self.helper.__setstate__, state)


  # Tests for _CLAClassificationRecord class
  # ===========================================================================

  def testCLAClassificationRecord(self):
    record = {
      "ROWID": 0,
      "anomalyScore": 1.0,
      "anomalyVector": "Vector",
      "anomalyLabel": "Label"
    }

    state = _CLAClassificationRecord(**record)
    self.assertEqual(state.ROWID, record['ROWID'])
    self.assertEqual(state.anomalyScore, record['anomalyScore'])
    self.assertEqual(state.anomalyVector, record['anomalyVector'])
    self.assertEqual(state.anomalyLabel, record['anomalyLabel'])
    self.assertEqual(state.setByUser, False)

    record = {
      "ROWID": 0,
      "anomalyScore": 1.0,
      "anomalyVector": "Vector",
      "anomalyLabel": "Label",
      "setByUser": True
    }

    state = _CLAClassificationRecord(**record)
    self.assertEqual(state.ROWID, record['ROWID'])
    self.assertEqual(state.anomalyScore, record['anomalyScore'])
    self.assertEqual(state.anomalyVector, record['anomalyVector'])
    self.assertEqual(state.anomalyLabel, record['anomalyLabel'])
    self.assertEqual(state.setByUser, record['setByUser'])


  def testCLAClassificationRecordGetState(self):
    record = {
      "ROWID": 0,
      "anomalyScore": 1.0,
      "anomalyVector": "Vector",
      "anomalyLabel": "Label",
      "setByUser": False
    }

    state = _CLAClassificationRecord(**record)

    self.assertEqual(state.__getstate__(), record)


  def testCLAClassificationRecordSetState(self):
    record = {
      "ROWID": None,
      "anomalyScore": None,
      "anomalyVector": None,
      "anomalyLabel": None,
      "setByUser": None
    }

    state = _CLAClassificationRecord(**record)

    record = {
      "ROWID": 0,
      "anomalyScore": 1.0,
      "anomalyVector": "Vector",
      "anomalyLabel": "Label",
      "setByUser": False
    }

    state.__setstate__(record)

    self.assertEqual(state.ROWID, record['ROWID'])
    self.assertEqual(state.anomalyScore, record['anomalyScore'])
    self.assertEqual(state.anomalyVector, record['anomalyVector'])
    self.assertEqual(state.anomalyLabel, record['anomalyLabel'])
    self.assertEqual(state.setByUser, record['setByUser'])




  def mockRemoveIds(self, ids):
    self.helper._knnclassifier._knn._numPatterns -= len(ids)
    knnClassifier = self.helper._knnclassifier
    for idx in ids:
      if idx in self.helper._knnclassifier.getParameter('categoryRecencyList'):
        knnClassifier.getParameter('categoryRecencyList').remove(idx)




if __name__ == '__main__':
  parser = TestOptionParser()
  options, args = parser.parse_args()

  # Form the command line for the unit test framework
  args = [sys.argv[0]] + args
  unittest.main(argv=args)

