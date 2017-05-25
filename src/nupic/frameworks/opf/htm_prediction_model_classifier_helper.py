import copy

import numpy

from nupic.support.configuration import Configuration
from nupic.frameworks.opf.exceptions import (HTMPredictionModelInvalidRangeError,
                                             HTMPredictionModelInvalidArgument)


class _CLAClassificationRecord(object):
  """
  A single record to store data associated with a single prediction for the
  anomaly classifier.

  ROWID - prediction stream ROWID record number
  setByUser - if true, a delete must be called explicitly on this point to
    remove its label

  """
  __slots__ = ["ROWID", "anomalyScore", "anomalyVector", "anomalyLabel",
    "setByUser"]

  def __init__(self, ROWID, anomalyScore, anomalyVector, anomalyLabel,
      setByUser=False):
    self.ROWID = ROWID
    self.anomalyScore = anomalyScore
    self.anomalyVector = anomalyVector
    self.anomalyLabel = anomalyLabel
    self.setByUser = setByUser

  def __getstate__(self):
    obj_slot_values = dict((k, getattr(self, k)) for k in self.__slots__)
    return obj_slot_values

  def __setstate__(self, data_dict):
    for (name, value) in data_dict.iteritems():
      setattr(self, name, value)



class HTMPredictionModelClassifierHelper(object):
  """
  This class implements a record classifier used to classify prediction
  records. It currently depends on the KNN classifier within the parent model.

  Currently it is classifying based on SP / TM properties and has a sliding
  window of 1000 records.

  The model should call the compute() method for each iteration that will be
  classified.

  This model also exposes methods to classify records after they have been
  processed.
  """

  AUTO_THRESHOLD_CLASSIFIED_LABEL = "Auto Threshold Classification"

  AUTO_TAG = " (auto)"

  __VERSION__ = 3

  def __init__(self, htm_prediction_model, anomalyParams={}):
    if anomalyParams is None:
      anomalyParams = {}
    self.htm_prediction_model = htm_prediction_model

    self._version = HTMPredictionModelClassifierHelper.__VERSION__

    self._classificationMaxDist = 0.1

    if 'autoDetectWaitRecords' not in anomalyParams or \
        anomalyParams['autoDetectWaitRecords'] is None:
      self._autoDetectWaitRecords = int(Configuration.get(
        'nupic.model.temporalAnomaly.wait_records'))
    else:
      self._autoDetectWaitRecords = anomalyParams['autoDetectWaitRecords']

    if 'autoDetectThreshold' not in anomalyParams or \
        anomalyParams['autoDetectThreshold'] is None:
      self._autoDetectThreshold = float(Configuration.get(
        'nupic.model.temporalAnomaly.auto_detect_threshold'))
    else:
      self._autoDetectThreshold = anomalyParams['autoDetectThreshold']

    if 'anomalyCacheRecords' not in anomalyParams or \
        anomalyParams['anomalyCacheRecords'] is None:
      self._history_length = int(Configuration.get(
        'nupic.model.temporalAnomaly.window_length'))
    else:
      self._history_length = anomalyParams['anomalyCacheRecords']

    if 'anomalyVectorType' not in anomalyParams or \
        anomalyParams['anomalyVectorType'] is None:
      self._vectorType = str(Configuration.get(
        'nupic.model.temporalAnomaly.anomaly_vector'))
    else:
      self._vectorType = anomalyParams['anomalyVectorType']

    self._activeColumnCount = \
      self.htm_prediction_model._getSPRegion().getSelf().getParameter('numActiveColumnsPerInhArea')

    # Storage for last run
    self._anomalyVectorLength = None
    self._classificationVector = numpy.array([])
    self._prevPredictedColumns = numpy.array([])
    self._prevTPCells = numpy.array([])

    # Array of CLAClassificationRecord's used to recompute and get history
    self.saved_states = []
    self.saved_categories = []


  def run(self):
    # Compute an iteration of this classifier
    result = self.compute()

    # return the label to assign to this point
    return result.anomalyLabel


  def getLabels(self, start=None, end=None):
    if len(self.saved_states) == 0:
      return {
        'isProcessing': False,
        'recordLabels': []
      }

    if start is None:
      start = 0

    if end is None:
      end = self.saved_states[-1].ROWID

    if end <= start:
      raise HTMPredictionModelInvalidRangeError("Invalid supplied range for 'getLabels'.",
                                                debugInfo={
          'requestRange': {
            'startRecordID': start,
            'endRecordID': end
          },
          'numRecordsStored': len(self.saved_states)
        })

    results = {
      'isProcessing': False,
      'recordLabels': []
    }

    classifier = self.htm_prediction_model._getAnomalyClassifier()
    knn = classifier.getSelf()._knn

    ROWIDX = numpy.array(
      classifier.getSelf().getParameter('categoryRecencyList'))
    validIdx = numpy.where((ROWIDX >= start) & (ROWIDX < end))[0].tolist()
    categories = knn._categoryList
    for idx in validIdx:
      row = dict(
        ROWID=int(ROWIDX[idx]),
        labels=self._categoryToLabelList(categories[idx]))
      results['recordLabels'].append(row)

    return results


  def addLabel(self, start, end, labelName):
    """
    Add the label labelName to each record with record ROWID in range from
    start to end, noninclusive of end.

    This will recalculate all points from end to the last record stored in the
    internal cache of this classifier.
    """
    if len(self.saved_states) == 0:
      raise HTMPredictionModelInvalidRangeError("Invalid supplied range for 'addLabel'. "
        "Model has no saved records.")

    startID = self.saved_states[0].ROWID

    clippedStart = max(0, start - startID)
    clippedEnd = max(0, min( len( self.saved_states) , end - startID))

    if clippedEnd <= clippedStart:
      raise HTMPredictionModelInvalidRangeError("Invalid supplied range for 'addLabel'.",
                                                debugInfo={
          'requestRange': {
            'startRecordID': start,
            'endRecordID': end
          },
          'clippedRequestRange': {
            'startRecordID': clippedStart,
            'endRecordID': clippedEnd
          },
          'validRange': {
            'startRecordID': startID,
            'endRecordID': self.saved_states[len(self.saved_states)-1].ROWID
          },
          'numRecordsStored': len(self.saved_states)
        })

    # Add label to range [clippedStart, clippedEnd)
    for state in self.saved_states[clippedStart:clippedEnd]:
      if labelName not in state.anomalyLabel:
        state.anomalyLabel.append(labelName)
        state.setByUser = True
        self._addRecordToKNN(state)

    assert len(self.saved_categories) > 0

    # Recompute [end, ...)
    for state in self.saved_states[clippedEnd:]:
      self._updateState(state)


  def removeLabels(self, start=None, end=None, labelFilter=None):
    """
    Remove labels from each record with record ROWID in range from
    start to end, noninclusive of end. Removes all records if labelFilter is
    None, otherwise only removes the labels eqaul to labelFilter.

    This will recalculate all points from end to the last record stored in the
    internal cache of this classifier.
    """

    if len(self.saved_states) == 0:
      raise HTMPredictionModelInvalidRangeError("Invalid supplied range for "
        "'removeLabels'. Model has no saved records.")

    startID = self.saved_states[0].ROWID

    clippedStart = 0 if start is None else max(0, start - startID)
    clippedEnd = len(self.saved_states) if end is None else \
      max(0, min( len( self.saved_states) , end - startID))

    if clippedEnd <= clippedStart:
      raise HTMPredictionModelInvalidRangeError("Invalid supplied range for "
        "'removeLabels'.", debugInfo={
          'requestRange': {
            'startRecordID': start,
            'endRecordID': end
          },
          'clippedRequestRange': {
            'startRecordID': clippedStart,
            'endRecordID': clippedEnd
          },
          'validRange': {
            'startRecordID': startID,
            'endRecordID': self.saved_states[len(self.saved_states)-1].ROWID
          },
          'numRecordsStored': len(self.saved_states)
        })

    # Remove records within the cache
    recordsToDelete = []
    for state in self.saved_states[clippedStart:clippedEnd]:
      if labelFilter is not None:
        if labelFilter in state.anomalyLabel:
          state.anomalyLabel.remove(labelFilter)
      else:
        state.anomalyLabel = []
      state.setByUser = False
      recordsToDelete.append(state)
    self._deleteRecordsFromKNN(recordsToDelete)

    # Remove records not in cache
    self._deleteRangeFromKNN(start, end)

    # Recompute [clippedEnd, ...)
    for state in self.saved_states[clippedEnd:]:
      self._updateState(state)

    return {'status': 'success'}


  def _updateState(self, state):

    # Record is before wait period do not classifiy
    if state.ROWID < self._autoDetectWaitRecords:
      if not state.setByUser:
        state.anomalyLabel = []
        self._deleteRecordsFromKNN([state])
      return

    label = HTMPredictionModelClassifierHelper.AUTO_THRESHOLD_CLASSIFIED_LABEL
    autoLabel = label + HTMPredictionModelClassifierHelper.AUTO_TAG

    # Update the label based on classifications
    newCategory = self._recomputeRecordFromKNN(state)
    labelList = self._categoryToLabelList(newCategory)

    if state.setByUser:
      if label in state.anomalyLabel:
        state.anomalyLabel.remove(label)
      if autoLabel in state.anomalyLabel:
        state.anomalyLabel.remove(autoLabel)
      labelList.extend(state.anomalyLabel)

    if state.anomalyScore >= self._autoDetectThreshold:
      labelList.append(label)
    elif label in labelList:
      # If not above threshold but classified - set to auto threshold label
      ind = labelList.index(label)
      labelList[ind] = autoLabel

    # Make all entries unique
    labelList = list(set(labelList))

    # If both above threshold and auto classified above - remove auto label
    if label in labelList and autoLabel in labelList:
      labelList.remove(autoLabel)

    if state.anomalyLabel == labelList:
      return

    # Update state's labeling
    state.anomalyLabel = labelList

    # Update KNN Classifier with new labeling
    if state.anomalyLabel == []:
      self._deleteRecordsFromKNN([state])
    else:
      self._addRecordToKNN(state)


  def _addRecordToKNN(self, record):
    """
    This method will add the record to the KNN classifier.
    """
    classifier = self.htm_prediction_model._getAnomalyClassifier()
    knn = classifier.getSelf()._knn

    prototype_idx = classifier.getSelf().getParameter('categoryRecencyList')
    category = self._labelListToCategoryNumber(record.anomalyLabel)

    # If record is already in the classifier, overwrite its labeling
    if record.ROWID in prototype_idx:
      knn.prototypeSetCategory(record.ROWID, category)
      return

    # Learn this pattern in the knn
    pattern = self._getStateAnomalyVector(record)
    rowID = record.ROWID
    knn.learn(pattern, category, rowID=rowID)


  def _deleteRecordsFromKNN(self, recordsToDelete):
    """
    This method will remove the given records from the classifier.

    parameters
    ------------
    recordsToDelete - list of records to delete from the classififier
    """
    classifier = self.htm_prediction_model._getAnomalyClassifier()
    knn = classifier.getSelf()._knn

    prototype_idx = classifier.getSelf().getParameter('categoryRecencyList')

    idsToDelete = [r.ROWID for r in recordsToDelete if \
      not r.setByUser and r.ROWID in prototype_idx]

    nProtos = knn._numPatterns
    knn.removeIds(idsToDelete)
    assert knn._numPatterns == nProtos - len(idsToDelete)

  def _deleteRangeFromKNN(self, start=0, end=None):
    """
    This method will remove any stored records within the range from start to
    end. Noninclusive of end.

    parameters
    ------------
    start - integer representing the ROWID of the start of the deletion range,
    end - integer representing the ROWID of the end of the deletion range,
      if None, it will default to end.
    """
    classifier = self.htm_prediction_model._getAnomalyClassifier()
    knn = classifier.getSelf()._knn

    prototype_idx = numpy.array(
      classifier.getSelf().getParameter('categoryRecencyList'))

    if end is None:
      end = prototype_idx.max() + 1

    idsIdxToDelete = numpy.logical_and(prototype_idx >= start,
                                       prototype_idx < end)
    idsToDelete = prototype_idx[idsIdxToDelete]

    nProtos = knn._numPatterns
    knn.removeIds(idsToDelete.tolist())
    assert knn._numPatterns == nProtos - len(idsToDelete)


  def _recomputeRecordFromKNN(self, record):
    """
    return the classified labeling of record
    """
    inputs = {
      "categoryIn": [None],
      "bottomUpIn": self._getStateAnomalyVector(record),
    }

    outputs = {"categoriesOut": numpy.zeros((1,)),
               "bestPrototypeIndices":numpy.zeros((1,)),
               "categoryProbabilitiesOut":numpy.zeros((1,))}

    # Run inference only to capture state before learning
    classifier = self.htm_prediction_model._getAnomalyClassifier()
    knn = classifier.getSelf()._knn

    # Only use points before record to classify and after the wait period.
    classifier_indexes = \
      numpy.array(classifier.getSelf().getParameter('categoryRecencyList'))
    valid_idx = numpy.where(
        (classifier_indexes >= self._autoDetectWaitRecords) &
        (classifier_indexes < record.ROWID)
      )[0].tolist()

    if len(valid_idx) == 0:
      return None

    classifier.setParameter('inferenceMode', True)
    classifier.setParameter('learningMode', False)
    classifier.getSelf().compute(inputs, outputs)
    classifier.setParameter('learningMode', True)

    classifier_distances = classifier.getSelf().getLatestDistances()
    valid_distances = classifier_distances[valid_idx]
    if valid_distances.min() <= self._classificationMaxDist:
      classifier_indexes_prev = classifier_indexes[valid_idx]
      rowID = classifier_indexes_prev[valid_distances.argmin()]
      indexID = numpy.where(classifier_indexes == rowID)[0][0]
      category = classifier.getSelf().getCategoryList()[indexID]
      return category
    return None



  def _constructClassificationRecord(self):
    """
    Construct a _HTMClassificationRecord based on the current state of the
    htm_prediction_model of this classifier.

    ***This will look into the internals of the model and may depend on the
    SP, TM, and KNNClassifier***
    """
    model = self.htm_prediction_model
    sp = model._getSPRegion()
    tm = model._getTPRegion()
    tpImp = tm.getSelf()._tfdr

    # Count the number of unpredicted columns
    activeColumns = sp.getOutputData("bottomUpOut").nonzero()[0]
    score = numpy.in1d(activeColumns, self._prevPredictedColumns).sum()
    score = (self._activeColumnCount - score)/float(self._activeColumnCount)

    spSize = sp.getParameter('activeOutputCount')
    tpSize = tm.getParameter('cellsPerColumn') * tm.getParameter('columnCount')

    classificationVector = numpy.array([])

    if self._vectorType == 'tpc':
      # Classification Vector: [---TM Cells---]
      classificationVector = numpy.zeros(tpSize)
      activeCellMatrix = tpImp.getLearnActiveStateT().reshape(tpSize, 1)
      activeCellIdx = numpy.where(activeCellMatrix > 0)[0]
      if activeCellIdx.shape[0] > 0:
        classificationVector[numpy.array(activeCellIdx, dtype=numpy.uint16)] = 1
    elif self._vectorType == 'sp_tpe':
      # Classification Vecotr: [---SP---|---(TM-SP)----]
      classificationVector = numpy.zeros(spSize+spSize)
      if activeColumns.shape[0] > 0:
        classificationVector[activeColumns] = 1.0

      errorColumns = numpy.setdiff1d(self._prevPredictedColumns, activeColumns)
      if errorColumns.shape[0] > 0:
        errorColumnIndexes = ( numpy.array(errorColumns, dtype=numpy.uint16) +
          spSize )
        classificationVector[errorColumnIndexes] = 1.0
    else:
      raise TypeError("Classification vector type must be either 'tpc' or"
        " 'sp_tpe', current value is %s" % (self._vectorType))

    # Store the state for next time step
    numPredictedCols = len(self._prevPredictedColumns)
    predictedColumns = tm.getOutputData("topDownOut").nonzero()[0]
    self._prevPredictedColumns = copy.deepcopy(predictedColumns)

    if self._anomalyVectorLength is None:
      self._anomalyVectorLength = len(classificationVector)

    result = _CLAClassificationRecord(
      ROWID=int(model.getParameter('__numRunCalls') - 1), #__numRunCalls called
        #at beginning of model.run
      anomalyScore=score,
      anomalyVector=classificationVector.nonzero()[0].tolist(),
      anomalyLabel=[]
    )
    return result


  def compute(self):
    """
    Run an iteration of this anomaly classifier
    """
    result = self._constructClassificationRecord()

    # Classify this point after waiting the classification delay
    if result.ROWID >= self._autoDetectWaitRecords:
      self._updateState(result)

    # Save new classification record and keep history as moving window
    self.saved_states.append(result)
    if len(self.saved_states) > self._history_length:
      self.saved_states.pop(0)

    return result


  def setAutoDetectWaitRecords(self, waitRecords):
    """
    Sets the autoDetectWaitRecords.
    """
    if not isinstance(waitRecords, int):
      raise HTMPredictionModelInvalidArgument("Invalid argument type \'%s\'. WaitRecord "
        "must be a number." % (type(waitRecords)))

    if len(self.saved_states) > 0 and waitRecords < self.saved_states[0].ROWID:
      raise HTMPredictionModelInvalidArgument("Invalid value. autoDetectWaitRecord value "
        "must be valid record within output stream. Current minimum ROWID in "
        "output stream is %d." % (self.saved_states[0].ROWID))

    self._autoDetectWaitRecords = waitRecords

    # Update all the states in the classifier's cache
    for state in self.saved_states:
      self._updateState(state)


  def getAutoDetectWaitRecords(self):
    """
    Return the autoDetectWaitRecords.
    """
    return self._autoDetectWaitRecords


  def setAutoDetectThreshold(self, threshold):
    """
    Sets the autoDetectThreshold.
    TODO: Ensure previously classified points outside of classifier are valid.
    """
    if not (isinstance(threshold, float) or isinstance(threshold, int)):
      raise HTMPredictionModelInvalidArgument("Invalid argument type \'%s\'. threshold "
        "must be a number." % (type(threshold)))

    self._autoDetectThreshold = threshold

    # Update all the states in the classifier's cache
    for state in self.saved_states:
      self._updateState(state)


  def getAutoDetectThreshold(self):
    """
    Return the autoDetectThreshold.
    """
    return self._autoDetectThreshold


  def _labelToCategoryNumber(self, label):
    """
    Since the KNN Classifier stores categories as numbers, we must store each
    label as a number. This method converts from a label to a unique number.
    Each label is assigned a unique bit so multiple labels may be assigned to
    a single record.
    """
    if label not in self.saved_categories:
      self.saved_categories.append(label)
    return pow(2, self.saved_categories.index(label))


  def _labelListToCategoryNumber(self, labelList):
    """
    This method takes a list of labels and returns a unique category number.
    This enables this class to store a list of categories for each point since
    the KNN classifier only stores a single number category for each record.
    """
    categoryNumber = 0
    for label in labelList:
      categoryNumber += self._labelToCategoryNumber(label)
    return categoryNumber


  def _categoryToLabelList(self, category):
    """
    Converts a category number into a list of labels
    """
    if category is None:
      return []

    labelList = []
    labelNum = 0
    while category > 0:
      if category % 2 == 1:
        labelList.append(self.saved_categories[labelNum])
      labelNum += 1
      category = category >> 1
    return labelList


  def _getStateAnomalyVector(self, state):
    """
    Returns a state's anomaly vertor converting it from spare to dense
    """
    vector = numpy.zeros(self._anomalyVectorLength)
    vector[state.anomalyVector] = 1
    return vector


  def __setstate__(self, state):
    version = 1
    if "_version" in state:
      version = state["_version"]

    # Migrate from version 1 to version 2
    if version == 1:
      self._vectorType = str(Configuration.get(
        'nupic.model.temporalAnomaly.anomaly_vector'))
      self._autoDetectWaitRecords = state['_classificationDelay']
    elif version == 2:
      self._autoDetectWaitRecords = state['_classificationDelay']
    elif version == 3:
      pass
    else:
      raise Exception("Error while deserializing %s: Invalid version %s"
                      %(self.__class__, version))

    if '_autoDetectThreshold' not in state:
      self._autoDetectThreshold = 1.1

    for attr, value in state.iteritems():
      setattr(self, attr, value)

    self._version = HTMPredictionModelClassifierHelper.__VERSION__

