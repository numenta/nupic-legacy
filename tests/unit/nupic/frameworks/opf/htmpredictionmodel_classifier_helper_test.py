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

"""Unit tests for the htm_prediction_model module."""

import sys
import copy
from datetime import datetime
import numpy
from mock import Mock, patch, ANY, call

from nupic.support.unittesthelpers.testcasebase import (unittest,
                                                        TestOptionParser)

from nupic.frameworks.opf.htm_prediction_model import HTMPredictionModel
from nupic.frameworks.opf.htm_prediction_model_classifier_helper import \
  HTMPredictionModelClassifierHelper, _CLAClassificationRecord, Configuration

from nupic.frameworks.opf.opf_utils import InferenceType

from nupic.frameworks.opf.exceptions import HTMPredictionModelInvalidRangeError

experimentDesc = {
    "inferenceType": InferenceType.TemporalAnomaly,
    "environment": "nupic",
    "inferenceArgs": {
        "predictionSteps": [1],
        "predictedField": "value1"
    },
    "streamDef": dict(
      version = 1,
      info = "checkpoint_test_dummy",
      streams = [
        dict(source="file://joined_mosman_2011.csv",
             info="checkpoint_test_dummy",
             columns=["*"],
             ),
        ],
      ),
    "includedFields": [
        {
            "fieldName": "TimeStamp",
            "fieldType": "datetime"
        },
        {
            "fieldName": "value1",
            "fieldType": "float"
        },
        {
            "fieldName": "value2",
            "fieldType": "string"
        }
    ]
}

records= [
  {"TimeStamp":datetime(year=2012, month=4, day=4, hour=1),
   "value1": 8.3,
   "value2": "BLUE"},

   {"TimeStamp":datetime(year=2012, month=4, day=4, hour=2),
   "value1": -8.3,
   "value2": "GREEN"},

   {"TimeStamp":datetime(year=2012, month=4, day=4, hour=3),
   "value1": 1.3,
   "value2": "RED"},

   {"TimeStamp":datetime(year=2012, month=4, day=4, hour=4),
   "value1": -0.9,
   "value2": "GREEN"},

   {"TimeStamp":datetime(year=2012, month=4, day=4, hour=5),
   "value1": 4.2,
   "value2": "GREEN"},

   {"TimeStamp":datetime(year=2012, month=4, day=4, hour=6),
   "value1": 100.1,
   "value2": "BLUE"},

   {"TimeStamp":datetime(year=2012, month=4, day=4, hour=7),
   "value1": 8.3,
   "value2": "BLUE"},

   {"TimeStamp":datetime(year=2012, month=4, day=4, hour=8),
   "value1": 8.3,
   "value2": "GREEN"},

   {"TimeStamp":datetime(year=2012, month=4, day=4, hour=9),
   "value1": 8.3,
   "value2": "GREEN"},

   {"TimeStamp":datetime(year=2012, month=4, day=4, hour=10),
   "value1": 8.3,
   "value2": "GREEN"},

   {"TimeStamp":datetime(year=2012, month=4, day=4, hour=10),
   "value1": 8.3,
   "value2": "GREEN"},

   {"TimeStamp":datetime(year=2012, month=4, day=4, hour=10),
   "value1": 8.3,
   "value2": "GREEN"},

   {"TimeStamp":datetime(year=2012, month=4, day=4, hour=10),
   "value1": 8.3,
   "value2": "GREEN"},

   {"TimeStamp":datetime(year=2012, month=4, day=4, hour=10),
   "value1": 8.3,
   "value2": "BLUE"},

   {"TimeStamp":datetime(year=2012, month=4, day=4, hour=10),
   "value1": 8.3,
   "value2": "GREEN"},

   {"TimeStamp":datetime(year=2012, month=4, day=4, hour=10),
   "value1": 8.3,
   "value2": "GREEN"},

   {"TimeStamp":datetime(year=2012, month=4, day=4, hour=10),
   "value1": 8.3,
   "value2": "GREEN"},

]




class SDRClassifierHelperTest(unittest.TestCase):
  """HTMPredictionModelClassifierHelper unit tests."""
  def setUp(self):
    self.helper = HTMPredictionModelClassifierHelper(Mock(spec=HTMPredictionModel))

  @patch.object(Configuration, 'get')
  @patch.object(HTMPredictionModelClassifierHelper, 'compute')
  def testInit(self, compute, configurationGet):
    anomalyParams = {
      'autoDetectWaitRecords': 100,
      'autoDetectThreshold': 101,
      'anomalyCacheRecords': 102,
      'anomalyVectorType': 'tpc'
    }
    conf = {
      'nupic.model.temporalAnomaly.wait_records': 160,
      'nupic.model.temporalAnomaly.auto_detect_threshold': 2.0,
      'nupic.model.temporalAnomaly.window_length': 1111,
      'nupic.model.temporalAnomaly.anomaly_vector': 'tpc',
    }
    configurationGet.side_effect = conf.get
    helper = HTMPredictionModelClassifierHelper(Mock(spec=HTMPredictionModel), anomalyParams)

    self.assertEqual(helper._autoDetectWaitRecords,
                     anomalyParams['autoDetectWaitRecords'])
    self.assertEqual(helper._autoDetectThreshold,
                     anomalyParams['autoDetectThreshold'])
    self.assertEqual(helper._history_length,
                     anomalyParams['anomalyCacheRecords'])
    self.assertEqual(helper._vectorType,
                     anomalyParams['anomalyVectorType'])

    helper = HTMPredictionModelClassifierHelper(Mock(spec=HTMPredictionModel), None)
    self.assertEqual(helper._autoDetectWaitRecords,
                     conf['nupic.model.temporalAnomaly.wait_records'])
    self.assertEqual(helper._autoDetectThreshold,
                     conf['nupic.model.temporalAnomaly.auto_detect_threshold'])
    self.assertEqual(helper._history_length,
                     conf['nupic.model.temporalAnomaly.window_length'])
    self.assertEqual(helper._vectorType,
                     conf['nupic.model.temporalAnomaly.anomaly_vector'])



  @patch.object(HTMPredictionModelClassifierHelper, 'compute')
  def testRun(self,compute):
    state = {
      "ROWID": 0,
      "anomalyScore": 1.0,
      "anomalyVector": [1,4,5],
      "anomalyLabel": "Label"
    }
    compute.return_value = _CLAClassificationRecord(**state)
    result = self.helper.run()
    compute.assert_called_once_with()
    self.assertEqual(result, state['anomalyLabel'])


  def testGetLabels(self):
    # No saved_states
    self.helper.saved_states = []
    self.assertEqual(self.helper.getLabels(), \
      {'isProcessing': False, 'recordLabels': []})

    # Invalid ranges
    self.helper.saved_states = [Mock(ROWID=10)]
    self.assertRaises(HTMPredictionModelInvalidRangeError,
                      self.helper.getLabels, start=100, end=100)

    self.helper.saved_states = [Mock(ROWID=10)]
    self.assertRaises(HTMPredictionModelInvalidRangeError,
                      self.helper.getLabels, start=-100, end=-100)

    self.helper.saved_states = [Mock(ROWID=10)]
    self.assertRaises(HTMPredictionModelInvalidRangeError,
                      self.helper.getLabels, start=100, end=-100)

    # Valid no threshold labels
    values = {
      'categoryRecencyList': [4, 5, 7],
    }
    self.helper.saved_categories = ['TestCategory']
    categoryList = [1,1,1]
    classifier = self.helper.htm_prediction_model._getAnomalyClassifier().getSelf()
    classifier.getParameter.side_effect = values.get
    classifier._knn._categoryList = categoryList

    results = self.helper.getLabels()
    self.assertTrue('isProcessing' in results)
    self.assertTrue('recordLabels' in results)
    self.assertEqual(len(results['recordLabels']),
      len(values['categoryRecencyList']))
    for record in results['recordLabels']:
      self.assertTrue(record['ROWID'] in values['categoryRecencyList'])
      self.assertEqual(record['labels'], self.helper.saved_categories)

  @patch.object(HTMPredictionModelClassifierHelper, '_getStateAnomalyVector')
  @patch.object(HTMPredictionModelClassifierHelper, '_updateState')
  def testAddLabel(self, _updateState, _getStateAnomalyVector):
    self.helper.htm_prediction_model._getAnomalyClassifier().getSelf().getParameter.return_value = [1,2,3]
    self.helper.saved_states = []
    self.assertRaises(HTMPredictionModelInvalidRangeError,
                      self.helper.addLabel, start=100, end=100, labelName="test")

    # Invalid ranges
    self.helper.saved_states = [Mock(ROWID=10)]
    self.assertRaises(HTMPredictionModelInvalidRangeError,
                      self.helper.addLabel, start=100, end=100, labelName="test")

    self.helper.saved_states = [Mock(ROWID=10)]
    self.assertRaises(HTMPredictionModelInvalidRangeError,
                      self.helper.addLabel, start=-100, end=-100, labelName="test")

    self.helper.saved_states = [Mock(ROWID=10)]
    self.assertRaises(HTMPredictionModelInvalidRangeError,
                      self.helper.addLabel, start=100, end=-100, labelName="test")

    # Valid no threshold labels
    self.helper.saved_states = [
      Mock(ROWID=10, anomalyLabel=["Test"], setByUser=False),
      Mock(ROWID=11, anomalyLabel=[], setByUser=False),
      Mock(ROWID=12, anomalyLabel=["Test"], setByUser=True)]
    results = self.helper.addLabel(11, 12, "Added")

    # Verifies records were updated
    self.assertEqual(results, None)
    self.assertTrue('Added' in self.helper.saved_states[1].anomalyLabel)
    self.assertTrue(self.helper.saved_states[1].setByUser)

    # Verifies record added to KNN classifier
    knn = self.helper.htm_prediction_model._getAnomalyClassifier().getSelf()._knn
    knn.learn.assert_called_once_with(ANY, ANY, rowID=11)

    # Verifies records after added label is recomputed
    _updateState.assert_called_once_with(self.helper.saved_states[2])


  @patch.object(HTMPredictionModelClassifierHelper, '_getStateAnomalyVector')
  @patch.object(HTMPredictionModelClassifierHelper, '_updateState')
  def testRemoveLabel(self, _updateState, _getStateAnomalyVector):
    classifier = self.helper.htm_prediction_model._getAnomalyClassifier().getSelf()
    classifier.getParameter.return_value = [10,11,12]
    classifier._knn._numPatterns = 3
    classifier._knn.removeIds.side_effect = self.mockRemoveIds


    self.helper.saved_states = []
    self.assertRaises(HTMPredictionModelInvalidRangeError,
                      self.helper.removeLabels, )

    # Invalid ranges
    self.helper.saved_states = [Mock(ROWID=10)]
    self.assertRaises(HTMPredictionModelInvalidRangeError,
                      self.helper.removeLabels, start=100, end=100)

    self.helper.saved_states = [Mock(ROWID=10)]
    self.assertRaises(HTMPredictionModelInvalidRangeError,
                      self.helper.removeLabels, start=-100, end=-100)

    self.helper.saved_states = [Mock(ROWID=10)]
    self.assertRaises(HTMPredictionModelInvalidRangeError,
                      self.helper.removeLabels, start=100, end=-100)

    # Valid no threshold labels
    self.helper.saved_states = [
      Mock(ROWID=10, anomalyLabel=["Test"], setByUser=False),
      Mock(ROWID=11, anomalyLabel=["Test"], setByUser=False),
      Mock(ROWID=12, anomalyLabel=["Test"], setByUser=True)]
    results = self.helper.removeLabels(11, 12, "Test")

    self.assertEqual(results, {'status': 'success'})
    self.assertTrue('Test' not in self.helper.saved_states[1].anomalyLabel)

    # Verifies records removed from KNN classifier
    knn = self.helper.htm_prediction_model._getAnomalyClassifier().getSelf()._knn
    self.assertEqual(knn.removeIds.mock_calls, [call([11]), call([])])

    # Verifies records after removed record are updated
    _updateState.assert_called_once_with(self.helper.saved_states[2])


  @patch.object(HTMPredictionModelClassifierHelper, '_getStateAnomalyVector')
  @patch.object(HTMPredictionModelClassifierHelper, '_updateState')
  def testRemoveLabelNoFilter(self, _updateState, _getStateAnomalyVector):
    classifier = self.helper.htm_prediction_model._getAnomalyClassifier().getSelf()
    values = {
      'categoryRecencyList': [10, 11, 12]
    }
    classifier.getParameter.side_effect = values.get
    classifier._knn._numPatterns = 3
    classifier._knn.removeIds.side_effect = self.mockRemoveIds

    # Valid no threshold labels
    self.helper.saved_states = [
      Mock(ROWID=10, anomalyLabel=["Test"], setByUser=False),
      Mock(ROWID=11, anomalyLabel=["Test"], setByUser=False),
      Mock(ROWID=12, anomalyLabel=["Test"], setByUser=True)]
    results = self.helper.removeLabels(11, 12)

    self.assertEqual(results, {'status': 'success'})
    self.assertTrue('Test' not in self.helper.saved_states[1].anomalyLabel)

    # Verifies records removed from KNN classifier
    knn = self.helper.htm_prediction_model._getAnomalyClassifier().getSelf()._knn
    self.assertEqual(knn.removeIds.mock_calls, [call([11]), call([])])

    # Verifies records after removed record are updated
    _updateState.assert_called_once_with(self.helper.saved_states[2])


  @patch.object(HTMPredictionModelClassifierHelper, '_updateState')
  def testSetGetThreshold(self, updateState):
    self.helper.saved_states = [Mock(), Mock(), Mock()]

    self.helper.setAutoDetectThreshold(1.0)

    self.assertAlmostEqual(self.helper._autoDetectThreshold, 1.0)
    self.assertEqual(len(updateState.mock_calls), len(self.helper.saved_states))

    self.assertAlmostEqual(self.helper.getAutoDetectThreshold(), 1.0)

    self.assertRaises(Exception, self.helper.setAutoDetectThreshold, 'invalid')

  @patch.object(HTMPredictionModelClassifierHelper, '_updateState')
  def testSetGetWaitRecords(self, updateState):
    self.helper.saved_states = [
      Mock(ROWID=10, anomalyLabel=["Test"], setByUser=False),
      Mock(ROWID=11, anomalyLabel=["Test"], setByUser=False),
      Mock(ROWID=12, anomalyLabel=["Test"], setByUser=True)]

    self.helper.setAutoDetectWaitRecords(20)

    self.assertEqual(self.helper._autoDetectWaitRecords, 20)
    self.assertEqual(len(updateState.mock_calls), len(self.helper.saved_states))

    self.assertEqual(self.helper.getAutoDetectWaitRecords(), 20)

    # Test invalid parameter type
    self.assertRaises(Exception, self.helper.setAutoDetectWaitRecords,
      'invalid')

    # Test invalid value before first record ROWID in cache
    self.assertRaises(Exception, self.helper.setAutoDetectWaitRecords, 0)


  @patch.object(HTMPredictionModelClassifierHelper, '_addRecordToKNN')
  @patch.object(HTMPredictionModelClassifierHelper, '_deleteRecordsFromKNN')
  @patch.object(HTMPredictionModelClassifierHelper, '_recomputeRecordFromKNN')
  @patch.object(HTMPredictionModelClassifierHelper, '_categoryToLabelList')
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
    self.helper._autoDetectWaitRecords = 0
    self.helper._autoDetectThreshold = 1.1
    toLabelList.return_value = []
    state = _CLAClassificationRecord(**record)
    self.helper._updateState(state)
    self.assertEqual(state.anomalyLabel, [])
    deleteRecord.assert_called_once_with([state])

    # Test record not labeled and above threshold
    deleteRecord.reset_mock()
    addRecord.reset_mock()
    self.helper._autoDetectThreshold = 0.5
    toLabelList.return_value = []
    state = _CLAClassificationRecord(**record)
    self.helper._updateState(state)

    self.assertEqual(state.anomalyLabel, \
      [HTMPredictionModelClassifierHelper.AUTO_THRESHOLD_CLASSIFIED_LABEL])
    addRecord.assert_called_once_with(state)

    # Test record not labeled and above threshold during wait period
    deleteRecord.reset_mock()
    addRecord.reset_mock()
    self.helper._autoDetectWaitRecords = 10
    self.helper._autoDetectThreshold = 0.5
    toLabelList.return_value = []
    state = _CLAClassificationRecord(**record)
    self.helper._updateState(state)

    self.assertEqual(state.anomalyLabel, [])
    self.assertTrue(not addRecord.called)

    # Test record labeled and not above threshold
    deleteRecord.reset_mock()
    addRecord.reset_mock()
    self.helper._autoDetectWaitRecords = 0
    self.helper._autoDetectThreshold = 1.1
    toLabelList.return_value = ["Label"]
    state = _CLAClassificationRecord(**record)
    self.helper._updateState(state)
    self.assertEqual(state.anomalyLabel, ["Label"])
    self.assertTrue(not addRecord.called)

    # Test setByUser
    deleteRecord.reset_mock()
    addRecord.reset_mock()
    self.helper._autoDetectThreshold = 1.1
    toLabelList.return_value = ["Label 2"]
    recordCopy = copy.deepcopy(record)
    recordCopy['setByUser'] = True
    state = _CLAClassificationRecord(**recordCopy)
    self.helper._updateState(state)
    self.assertEqual(state.anomalyLabel,
      [recordCopy["anomalyLabel"][0], toLabelList.return_value[0]])
    addRecord.assert_called_once_with(state)

    # Test removal of above threshold
    deleteRecord.reset_mock()
    addRecord.reset_mock()
    self.helper._autoDetectThreshold = 1.1
    toLabelList.return_value = []
    recordCopy = copy.deepcopy(record)
    recordCopy['setByUser'] = True
    recordCopy['anomalyLabel'] = \
      [HTMPredictionModelClassifierHelper.AUTO_THRESHOLD_CLASSIFIED_LABEL,
       HTMPredictionModelClassifierHelper.AUTO_THRESHOLD_CLASSIFIED_LABEL + \
        HTMPredictionModelClassifierHelper.AUTO_TAG]
    state = _CLAClassificationRecord(**recordCopy)
    self.helper._updateState(state)
    self.assertEqual(state.anomalyLabel, [])

    # Auto classified threshold
    deleteRecord.reset_mock()
    addRecord.reset_mock()
    self.helper._autoDetectThreshold = 1.1
    toLabelList.return_value = \
      [HTMPredictionModelClassifierHelper.AUTO_THRESHOLD_CLASSIFIED_LABEL]
    recordCopy = copy.deepcopy(record)
    recordCopy['setByUser'] = True
    recordCopy['anomalyLabel'] = \
      [HTMPredictionModelClassifierHelper.AUTO_THRESHOLD_CLASSIFIED_LABEL]
    state = _CLAClassificationRecord(**recordCopy)
    self.helper._updateState(state)
    self.assertEqual(state.anomalyLabel,
      [HTMPredictionModelClassifierHelper.AUTO_THRESHOLD_CLASSIFIED_LABEL + \
        HTMPredictionModelClassifierHelper.AUTO_TAG])
    addRecord.assert_called_once_with(state)

    # Test precedence of threshold label above auto threshold label
    deleteRecord.reset_mock()
    addRecord.reset_mock()
    self.helper._autoDetectThreshold = 0.8
    toLabelList.return_value = \
      [HTMPredictionModelClassifierHelper.AUTO_THRESHOLD_CLASSIFIED_LABEL,
        HTMPredictionModelClassifierHelper.AUTO_THRESHOLD_CLASSIFIED_LABEL + \
        HTMPredictionModelClassifierHelper.AUTO_TAG]
    recordCopy = copy.deepcopy(record)
    recordCopy['setByUser'] = True
    recordCopy['anomalyLabel'] = \
      [HTMPredictionModelClassifierHelper.AUTO_THRESHOLD_CLASSIFIED_LABEL]
    state = _CLAClassificationRecord(**recordCopy)
    self.helper._updateState(state)
    self.assertEqual(state.anomalyLabel,
      [HTMPredictionModelClassifierHelper.AUTO_THRESHOLD_CLASSIFIED_LABEL])
    addRecord.assert_called_once_with(state)


  @patch.object(HTMPredictionModelClassifierHelper, '_getStateAnomalyVector')
  def testAddRecordToKNN(self, getAnomalyVector):
    getAnomalyVector.return_value = "Vector"
    values = {
      'categoryRecencyList': [1, 2, 3]
    }
    classifier = self.helper.htm_prediction_model._getAnomalyClassifier().getSelf()
    classifier.getParameter.side_effect = values.get
    state = {
      "ROWID": 5,
      "anomalyScore": 1.0,
      "anomalyVector": "",
      "anomalyLabel": ["Label"],
      "setByUser": False
    }
    record = _CLAClassificationRecord(**state)

    # Test with record not already in KNN
    self.helper._addRecordToKNN(record)
    classifier._knn.learn.assert_called_once_with("Vector", ANY, rowID=state['ROWID'])
    self.assertTrue(not classifier._knn.prototypeSetCategory.called)
    classifier._knn.learn.reset_mock()

    # Test with record already in KNN
    values = {
      'categoryRecencyList': [1, 2, 3, 5]
    }
    classifier.getParameter.side_effect = values.get
    self.helper._addRecordToKNN(record)
    classifier._knn.prototypeSetCategory.assert_called_once_with(\
      state['ROWID'], ANY)
    self.assertTrue(not classifier._knn.learn.called)


  @patch.object(HTMPredictionModelClassifierHelper, '_getStateAnomalyVector')
  def testDeleteRangeFromKNN(self, getAnomalyVector):
    getAnomalyVector.return_value = "Vector"
    values = {
      'categoryRecencyList': [1, 2, 3]
    }
    classifier = self.helper.htm_prediction_model._getAnomalyClassifier().getSelf()
    classifier.getParameter.side_effect = values.get
    classifier._knn._numPatterns = len(values['categoryRecencyList'])
    classifier._knn.removeIds.side_effect = self.mockRemoveIds

    # Test with record not already in KNN
    self.helper._deleteRangeFromKNN(start=1,end=3)
    classifier._knn.removeIds.assert_called_once_with([1,2])
    classifier._knn.removeIds.reset_mock()

    # Test with record already in KNN
    values = {
      'categoryRecencyList': [1, 2, 3, 5]
    }
    classifier.getParameter.side_effect = values.get
    self.helper._deleteRangeFromKNN(start=1)
    classifier._knn.removeIds.assert_called_once_with([1,2,3,5])


  @patch.object(HTMPredictionModelClassifierHelper, '_getStateAnomalyVector')
  def testRecomputeRecordFromKNN(self, getAnomalyVector):
    getAnomalyVector.return_value = "Vector"
    values = {
      'categoryRecencyList': [1, 2, 3, 5, 6, 7, 8, 9],
      'latestDists': numpy.array([0.7, 0.2, 0.5, 1, 0.3, 0.2, 0.1]),
      'categories': ['A','B','C','D','E','F','G']
    }
    classifier = self.helper.htm_prediction_model._getAnomalyClassifier().getSelf()
    classifier.getLatestDistances.return_value = values['latestDists']
    classifier.getCategoryList.return_value = values['categories']
    classifier.getParameter.side_effect = values.get
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
        'bottomUpOut': numpy.array([1,1,0,0,1])
      }
    }
    tpVals = {
      'params': {
        'cellsPerColumn': 2,
        'columnCount': 2
      },
      'output': {
        'lrnActive': numpy.array([1,0,0,1]),
        'topDownOut': numpy.array([1,0,0,0,1])
      }
    }
    self.helper.htm_prediction_model.getParameter.side_effect = modelParams.get
    sp = self.helper.htm_prediction_model._getSPRegion()
    tm = self.helper.htm_prediction_model._getTPRegion()
    tpImp = tm.getSelf()._tfdr

    sp.getParameter.side_effect = spVals['params'].get
    sp.getOutputData.side_effect = spVals['output'].get

    self.helper._activeColumnCount = 5

    tm.getParameter.side_effect = tpVals['params'].get
    tm.getOutputData.side_effect = tpVals['output'].get

    tpImp.getLearnActiveStateT.return_value = tpVals['output']['lrnActive']

    # Test TM Cell vector
    self.helper._vectorType = 'tpc'
    vector = self.helper._constructClassificationRecord()
    self.assertEqual(vector.anomalyVector, tpImp.getLearnActiveStateT().nonzero()[0].tolist())

    # Test SP and TM Column Error vector
    self.helper._vectorType = 'sp_tpe'
    self.helper._prevPredictedColumns = numpy.array([1,0,0,0,1]).nonzero()[0]
    vector = self.helper._constructClassificationRecord()
    self.assertEqual(vector.anomalyVector, [0, 1, 4])

    self.helper._prevPredictedColumns = numpy.array([1,0,1,0,0]).nonzero()[0]
    vector = self.helper._constructClassificationRecord()
    self.assertEqual(vector.anomalyVector, [0, 1, 4, 7])

    self.helper._vectorType = 'invalidType'
    self.assertRaises(TypeError, self.helper._constructClassificationRecord)


  @patch.object(HTMPredictionModelClassifierHelper ,'_updateState')
  @patch.object(HTMPredictionModelClassifierHelper, '_constructClassificationRecord')
  def testCompute(self, createRecord, updateState):
    state = {
      "ROWID": 0,
      "anomalyScore": 1.0,
      "anomalyVector": "Vector",
      "anomalyLabel": "Label"
    }
    record = _CLAClassificationRecord(**state)
    createRecord.return_value = record

    # Test add first record
    self.helper._history_length = 10
    self.helper._autoDetectWaitRecords = 0
    self.helper.saved_states = []
    result = self.helper.compute()
    self.assertEqual(result, record)
    self.assertEqual(len(self.helper.saved_states), 1)
    updateState.assert_called_once_with(result)

    # Test add record before wait records
    updateState.reset_mock()
    self.helper._history_length = 10
    self.helper._autoDetectWaitRecords = 10
    self.helper.saved_states = []
    result = self.helper.compute()
    self.assertEqual(result, record)
    self.assertEqual(len(self.helper.saved_states), 1)
    result = self.helper.compute()
    self.assertEqual(result, record)
    self.assertEqual(len(self.helper.saved_states), 2)
    self.assertTrue(not updateState.called)

    # Test exceeded cache length
    updateState.reset_mock()
    self.helper._history_length = 1
    self.helper.saved_states = []
    result = self.helper.compute()
    self.assertEqual(result, record)
    self.assertEqual(len(self.helper.saved_states), 1)
    result = self.helper.compute()
    self.assertEqual(result, record)
    self.assertEqual(len(self.helper.saved_states), 1)
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

  @patch.object(Configuration, 'get')
  def testConfiguration(self, configurationGet):
    conf = {
      'nupic.model.temporalAnomaly.wait_records': 160,
      'nupic.model.temporalAnomaly.auto_detect_threshold': 2.0,
      'nupic.model.temporalAnomaly.window_length': 1111,
      'nupic.model.temporalAnomaly.anomaly_vector': 'tpc'
    }
    configurationGet.side_effect = conf.get
    helper = HTMPredictionModelClassifierHelper(Mock(spec=HTMPredictionModel))

    self.assertEqual(helper._autoDetectWaitRecords,
      conf['nupic.model.temporalAnomaly.wait_records'])
    self.assertTrue(helper._autoDetectThreshold,
      conf['nupic.model.temporalAnomaly.auto_detect_threshold'])
    self.assertTrue(helper._history_length,
      conf['nupic.model.temporalAnomaly.window_length'])
    self.assertTrue(helper._vectorType,
      conf['nupic.model.temporalAnomaly.anomaly_vector'])


  @patch.object(Configuration, 'get')
  def testConfigurationFail(self, configurationGet):
    conf = {
      'nupic.model.temporalAnomaly.wait_records': 160,
      'nupic.model.temporalAnomaly.anomaly_vector': 'tpc'
    }
    configurationGet.side_effect = conf.get
    self.assertRaises(TypeError, HTMPredictionModelClassifierHelper, Mock(spec=HTMPredictionModel))

  @patch.object(Configuration, 'get')
  def testSetState(self, configurationGet):
    conf = {
      'nupic.model.temporalAnomaly.wait_records': 160,
      'nupic.model.temporalAnomaly.anomaly_vector': 'tpc'
    }
    configurationGet.side_effect = conf.get

    state = dict(_version=1,_classificationDelay=100)

    self.helper._vectorType = None
    state = self.helper.__setstate__(state)
    self.assertEqual(self.helper._vectorType,
      conf['nupic.model.temporalAnomaly.anomaly_vector'])
    self.assertEqual(self.helper._version, HTMPredictionModelClassifierHelper.__VERSION__)

    state = dict(_version=2, _classificationDelay=100)
    state = self.helper.__setstate__(state)
    self.assertEqual(self.helper._version, HTMPredictionModelClassifierHelper.__VERSION__)

    state = dict(_version="invalid")
    self.assertRaises(Exception, self.helper.__setstate__, state)


  # Tests for _HTMClassificationRecord class
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
    self.helper.htm_prediction_model._getAnomalyClassifier().getSelf()._knn._numPatterns -= len(ids)
    for idx in ids:
      if idx in self.helper.htm_prediction_model._getAnomalyClassifier().getSelf().getParameter('categoryRecencyList'):
        self.helper.htm_prediction_model._getAnomalyClassifier().getSelf().getParameter('categoryRecencyList').remove(idx)




if __name__ == '__main__':
  parser = TestOptionParser()
  options, args = parser.parse_args()

  # Form the command line for the unit test framework
  args = [sys.argv[0]] + args
  unittest.main(argv=args)

