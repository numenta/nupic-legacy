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

"""
## @file
This file defines the k Nearest Neighbor classifier region.
"""
import copy

import numpy
from PyRegion import PyRegion
from KNNClassifierRegion import KNNClassifierRegion
from nupic.algorithms.anomaly import computeRawAnomalyScore
from nupic.bindings.math import Random
from nupic.frameworks.opf.exceptions import (CLAModelInvalidRangeError,
                                             CLAModelInvalidArgument)



class KNNAnomalyClassifierRegion(PyRegion):
  """
  KNNAnomalyClassifierRegion wraps the KNNClassifierRegion to classify clamodel
  state.  It allows for individual records to be classified as anomalies and
  supports anomaly detection even after the model has learned the anomalous
  sequence.

  Methods:
    compute() - called by clamodel during record processing
    getLabels() - return points with classification records
    addLabel() - add a set label to a given set of points
    removeLabels() - remove labels from a given set of points

  Parameters:
    trainRecords - number of records to skip before classification
    anomalyThreshold - threshold on anomaly score to automatically classify
                       record as an anomaly
    cacheSize - number of records to keep in cache. Can only recalculate
                records kept in cache when setting the trainRecords.

  """

  @classmethod
  def getSpec(cls):
    ns = dict(
        description=KNNAnomalyClassifierRegion.__doc__,
        singleNodeOnly=True,
        inputs=dict(
          spBottomUpOut=dict(
            description="""The output signal generated from the bottom-up inputs
                            from lower levels.""",
            dataType='Real32',
            count=0,
            required=True,
            regionLevel=False,
            isDefaultInput=True,
            requireSplitterMap=False),

          tpTopDownOut=dict(
            description="""The top-down inputsignal, generated from
                          feedback from upper levels""",
            dataType='Real32',
            count=0,
            required=True,
            regionLevel=False,
            isDefaultInput=True,
            requireSplitterMap=False),

          tpLrnActiveStateT=dict(
            description="""Active cells in the learn state at time T from TP.
                        This is used to classify on.""",
            dataType='Real32',
            count=0,
            required=True,
            regionLevel=False,
            isDefaultInput=True,
            requireSplitterMap=False)
        ),

        outputs=dict(
        ),

        parameters=dict(
          trainRecords=dict(
            description='Number of records to wait for training',
            dataType='UInt32',
            count=1,
            constraints='',
            defaultValue=0,
            accessMode='Create'),

          anomalyThreshold=dict(
            description='Threshold used to classify anomalies.',
            dataType='Real32',
            count=1,
            constraints='',
            defaultValue=0,
            accessMode='Create'),

          cacheSize=dict(
            description='Number of records to store in cache.',
            dataType='UInt32',
            count=1,
            constraints='',
            defaultValue=0,
            accessMode='Create'),

          classificationVectorType=dict(
            description="""Vector type to use when classifying.
              1 - Vector Column with Difference (TP and SP)
            """,
            dataType='UInt32',
            count=1,
            constraints='',
            defaultValue=1,
            accessMode='ReadWrite'),

          activeColumnCount=dict(
            description="""Number of active columns in a given step. Typically
            equivalent to SP.numActiveColumnsPerInhArea""",
            dataType='UInt32',
            count=1,
            constraints='',
            defaultValue=40,
            accessMode='ReadWrite'),

          classificationMaxDist=dict(
            description="""Maximum distance a sample can be from an anomaly
            in the classifier to be labeled as an anomaly.

            Ex: With rawOverlap distance, a value of 0.65 means that the points
            must be at most a distance 0.65 apart from each other. This
            translates to they must be at least 35% similar.""",
            dataType='Real32',
            count=1,
            constraints='',
            defaultValue=0.65,
            accessMode='Create'
            )
        ),
        commands=dict(
          getLabels=dict(description=
            "Returns a list of label dicts with properties ROWID and labels."
            "ROWID corresponds to the records id and labels is a list of "
            "strings representing the records labels.  Takes additional "
            "integer properties start and end representing the range that "
            "will be returned."),

          addLabel=dict(description=
            "Takes parameters start, end and labelName. Adds the label "
            "labelName to the records from start to end. This will recalculate "
            "labels from end to the most recent record."),

          removeLabels=dict(description=
            "Takes additional parameters start, end, labelFilter.  Start and "
            "end correspond to range to remove the label. Remove labels from "
            "each record with record ROWID in range from start to end, "
            "noninclusive of end. Removes all records if labelFilter is None, "
            "otherwise only removes the labels eqaul to labelFilter.")
        )
      )

    ns['parameters'].update(KNNClassifierRegion.getSpec()['parameters'])

    return ns

  __VERSION__ = 1

  AUTO_THRESHOLD_CLASSIFIED_LABEL = "Auto Threshold Classification"

  AUTO_TAG = " (auto)"


  def __init__(self,
               trainRecords,
               anomalyThreshold,
               cacheSize,
               classificationVectorType=1,
               activeColumnCount=40,
               classificationMaxDist=0.30,
               **classifierArgs):

    # Internal Region Values
    self._maxLabelOutputs = 16
    self._activeColumnCount = activeColumnCount
    self._prevPredictedColumns = numpy.array([])
    self._anomalyVectorLength = None
    self._classificationMaxDist = classificationMaxDist
    self._iteration = 0

    # Set to create deterministic classifier
    classifierArgs['SVDDimCount'] = None

    # Parameters
    self.trainRecords = trainRecords
    self.anomalyThreshold = anomalyThreshold
    self.cacheSize = cacheSize
    self.classificationVectorType = classificationVectorType

    self._knnclassifierArgs = classifierArgs
    self._knnclassifier = KNNClassifierRegion(**self._knnclassifierArgs)
    self.labelResults = []
    self.saved_categories = []
    self._recordsCache = []

    self._version = KNNAnomalyClassifierRegion.__VERSION__


  def initialize(self, dims, splitterMaps):
    assert tuple(dims) == (1,) * len(dims)


  def getParameter(self, name, index=-1):
    """
    Get the value of the parameter.

    @param name -- the name of the parameter to retrieve, as defined
            by the Node Spec.
    """
    if name == "trainRecords":
      return self.trainRecords
    elif name == "anomalyThreshold":
      return self.anomalyThreshold
    elif name == "activeColumnCount":
      return self._activeColumnCount
    elif name == "classificationMaxDist":
      return self._classificationMaxDist
    else:
      # If any spec parameter name is the same as an attribute, this call
      # will get it automatically, e.g. self.learningMode
      return PyRegion.getParameter(self, name, index)


  def setParameter(self, name, index, value):
    """
    Set the value of the parameter.

    @param name -- the name of the parameter to update, as defined
            by the Node Spec.
    @param value -- the value to which the parameter is to be set.
    """
    if name == "trainRecords":
      # Ensure that the trainRecords can only be set to minimum of the ROWID in
      # the saved states
      if not (isinstance(value, float) or isinstance(value, int)):
        raise CLAModelInvalidArgument("Invalid argument type \'%s\'. threshold "
          "must be a number." % (type(value)))

      if len(self._recordsCache) > 0 and value < self._recordsCache[0].ROWID:
        raise CLAModelInvalidArgument("Invalid value. autoDetectWaitRecord "
          "value must be valid record within output stream. Current minimum "
          " ROWID in output stream is %d." % (self._recordsCache[0].ROWID))

      self.trainRecords = value
      # Remove any labels before the first cached record (wont be used anymore)
      self._deleteRangeFromKNN(0, self._recordsCache[0].ROWID)
      # Reclassify all states
      self.classifyStates()
    elif name == "anomalyThreshold":
      if not (isinstance(value, float) or isinstance(value, int)):
        raise CLAModelInvalidArgument("Invalid argument type \'%s\'. threshold "
          "must be a number." % (type(value)))
      self.anomalyThreshold = value
      self.classifyStates()
    elif name == "classificationMaxDist":
      if not (isinstance(value, float) or isinstance(value, int)):
        raise CLAModelInvalidArgument("Invalid argument type \'%s\'. "
          "classificationMaxDist must be a number." % (type(value)))
      self._classificationMaxDist = value
      self.classifyStates()
    elif name == "activeColumnCount":
      self._activeColumnCount = value
    else:
      return PyRegion.setParameter(self, name, index, value)


  def compute(self, inputs, outputs):
    """
    Process one input sample.
    This method is called by the runtime engine.
    """
    record = self.constructClassificationRecord(inputs)

    #Classify this point after waiting the classification delay
    if record.ROWID >= self.getParameter('trainRecords'):
      self.classifyState(record)

    #Save new classification record and keep history as moving window
    self._recordsCache.append(record)
    while len(self._recordsCache) > self.cacheSize:
      self._recordsCache.pop(0)

    self.labelResults = record.anomalyLabel

    self._iteration += 1


  def getLabelResults(self):
    """
    Get the labels of the previously computed record.

    ----------------
    retval - array of strings representing the classification labels
    """
    return self.labelResults


  def classifyStates(self):
    """
    Reclassifies all internal state
    """
    for state in self._recordsCache:
      self.classifyState(state)


  def classifyState(self, state):
    """
    Reclassifies given state.
    """
    # Record is before wait period do not classifiy
    if state.ROWID < self.getParameter('trainRecords'):
      if not state.setByUser:
        state.anomalyLabel = []
        self._deleteRecordsFromKNN([state])
      return

    label = KNNAnomalyClassifierRegion.AUTO_THRESHOLD_CLASSIFIED_LABEL
    autoLabel = label + KNNAnomalyClassifierRegion.AUTO_TAG

    # Update the label based on classifications
    newCategory = self._recomputeRecordFromKNN(state)
    labelList = self._categoryToLabelList(newCategory)

    if state.setByUser:
      if label in state.anomalyLabel:
        state.anomalyLabel.remove(label)
      if autoLabel in state.anomalyLabel:
        state.anomalyLabel.remove(autoLabel)
      labelList.extend(state.anomalyLabel)

    # Add threshold classification label if above threshold, else if
    # classified to add the auto threshold classification.
    if state.anomalyScore >= self.getParameter('anomalyThreshold'):
      labelList.append(label)
    elif label in labelList:
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


  def constructClassificationRecord(self, inputs):
    """
    Construct a _CLAClassificationRecord based on the state of the model
    passed in through the inputs.

    Types for self.classificationVectorType:
      1 - TP active cells in learn state
      2 - SP columns concatenated with error from TP column predictions and SP
    """
    # Count the number of unpredicted columns
    allSPColumns = inputs["spBottomUpOut"]
    activeSPColumns = allSPColumns.nonzero()[0]

    score = computeRawAnomalyScore(activeSPColumns, self._prevPredictedColumns)

    spSize = len(allSPColumns)


    allTPCells = inputs['tpTopDownOut']
    tpSize = len(inputs['tpLrnActiveStateT'])

    classificationVector = numpy.array([])

    if self.classificationVectorType == 1:
      # Classification Vector: [---TP Cells---]
      classificationVector = numpy.zeros(tpSize)
      activeCellMatrix = inputs["tpLrnActiveStateT"].reshape(tpSize, 1)
      activeCellIdx = numpy.where(activeCellMatrix > 0)[0]
      if activeCellIdx.shape[0] > 0:
        classificationVector[numpy.array(activeCellIdx, dtype=numpy.uint16)] = 1
    elif self.classificationVectorType == 2:
      # Classification Vecotr: [---SP---|---(TP-SP)----]
      classificationVector = numpy.zeros(spSize+spSize)
      if activeSPColumns.shape[0] > 0:
        classificationVector[activeSPColumns] = 1.0

      errorColumns = numpy.setdiff1d(self._prevPredictedColumns,
          activeSPColumns)
      if errorColumns.shape[0] > 0:
        errorColumnIndexes = ( numpy.array(errorColumns, dtype=numpy.uint16) +
          spSize )
        classificationVector[errorColumnIndexes] = 1.0
    else:
      raise TypeError("Classification vector type must be either 'tpc' or"
        " 'sp_tpe', current value is %s" % (self.classificationVectorType))

    # Store the state for next time step
    numPredictedCols = len(self._prevPredictedColumns)
    predictedColumns = allTPCells.nonzero()[0]
    self._prevPredictedColumns = copy.deepcopy(predictedColumns)

    if self._anomalyVectorLength is None:
      self._anomalyVectorLength = len(classificationVector)

    result = _CLAClassificationRecord(
      ROWID=self._iteration, #__numRunCalls called
        #at beginning of model.run
      anomalyScore=score,
      anomalyVector=classificationVector.nonzero()[0].tolist(),
      anomalyLabel=[]
    )
    return result


  def _addRecordToKNN(self, record):
    """
    Adds the record to the KNN classifier.
    """
    knn = self._knnclassifier._knn

    prototype_idx = self._knnclassifier.getParameter('categoryRecencyList')
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
    Removes the given records from the classifier.

    parameters
    ------------
    recordsToDelete - list of records to delete from the classififier
    """
    prototype_idx = self._knnclassifier.getParameter('categoryRecencyList')

    idsToDelete = ([r.ROWID for r in recordsToDelete if
      not r.setByUser and r.ROWID in prototype_idx])

    nProtos = self._knnclassifier._knn._numPatterns
    self._knnclassifier._knn.removeIds(idsToDelete)
    assert self._knnclassifier._knn._numPatterns == nProtos - len(idsToDelete)


  def _deleteRangeFromKNN(self, start=0, end=None):
    """
    Removes any stored records within the range from start to
    end. Noninclusive of end.

    parameters
    ------------
    start - integer representing the ROWID of the start of the deletion range,
    end - integer representing the ROWID of the end of the deletion range,
      if None, it will default to end.
    """
    prototype_idx = numpy.array(
      self._knnclassifier.getParameter('categoryRecencyList'))

    if end is None:
      end = prototype_idx.max() + 1

    idsIdxToDelete = numpy.logical_and(prototype_idx >= start,
                                       prototype_idx < end)
    idsToDelete = prototype_idx[idsIdxToDelete]

    nProtos = self._knnclassifier._knn._numPatterns
    self._knnclassifier._knn.removeIds(idsToDelete.tolist())
    assert self._knnclassifier._knn._numPatterns == nProtos - len(idsToDelete)


  def _recomputeRecordFromKNN(self, record):
    """
    returns the classified labeling of record
    """
    inputs = {
      "categoryIn": [None],
      "bottomUpIn": self._getStateAnomalyVector(record),
    }

    outputs = {"categoriesOut": numpy.zeros((1,)),
               "bestPrototypeIndices":numpy.zeros((1,)),
               "categoryProbabilitiesOut":numpy.zeros((1,))}

    # Only use points before record to classify and after the wait period.
    classifier_indexes = numpy.array(
        self._knnclassifier.getParameter('categoryRecencyList'))
    valid_idx = numpy.where(
        (classifier_indexes >= self.getParameter('trainRecords')) &
        (classifier_indexes < record.ROWID)
      )[0].tolist()

    if len(valid_idx) == 0:
      return None

    self._knnclassifier.setParameter('inferenceMode', None, True)
    self._knnclassifier.setParameter('learningMode', None, False)
    self._knnclassifier.compute(inputs, outputs)
    self._knnclassifier.setParameter('learningMode', None, True)

    classifier_distances = self._knnclassifier.getLatestDistances()
    valid_distances = classifier_distances[valid_idx]
    if valid_distances.min() <= self._classificationMaxDist:
      classifier_indexes_prev = classifier_indexes[valid_idx]
      rowID = classifier_indexes_prev[valid_distances.argmin()]
      indexID = numpy.where(classifier_indexes == rowID)[0][0]
      category = self._knnclassifier.getCategoryList()[indexID]
      return category
    return None


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


  def getLabels(self, start=None, end=None):
    """
    Get the labels on classified points within range start to end. Not inclusive
    of end.

    reval - dict of format:

      {
        'isProcessing': boolean,
        'recordLabels': list of results
      }

      isProcessing - currently always false as recalculation blocks; used if
        reprocessing of records is still being performed;

      Each item in recordLabels is of format:
      {
        'ROWID': id of the row,
        'labels': list of strings
      }

    """
    if len(self._recordsCache) == 0:
      return {
        'isProcessing': False,
        'recordLabels': []
      }
    try:
      start = int(start)
    except Exception:
      start = 0

    try:
      end = int(end)
    except Exception:
      end = self._recordsCache[-1].ROWID

    if end <= start:
      raise CLAModelInvalidRangeError("Invalid supplied range for 'getLabels'.",
        debugInfo={
          'requestRange': {
            'startRecordID': start,
            'endRecordID': end
          },
          'numRecordsStored': len(self._recordsCache)
        })

    results = {
      'isProcessing': False,
      'recordLabels': []
    }

    ROWIDX = numpy.array(
        self._knnclassifier.getParameter('categoryRecencyList'))
    validIdx = numpy.where((ROWIDX >= start) & (ROWIDX < end))[0].tolist()
    categories = self._knnclassifier.getCategoryList()
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
    if len(self._recordsCache) == 0:
      raise CLAModelInvalidRangeError("Invalid supplied range for 'addLabel'. "
        "Model has no saved records.")

    try:
      start = int(start)
    except Exception:
      start = 0

    try:
      end = int(end)
    except Exception:
      end = int(self._recordsCache[-1].ROWID)

    startID = self._recordsCache[0].ROWID

    clippedStart = max(0, start - startID)
    clippedEnd = max(0, min( len( self._recordsCache) , end - startID))

    if clippedEnd <= clippedStart:
      raise CLAModelInvalidRangeError("Invalid supplied range for 'addLabel'.",
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
            'endRecordID': self._recordsCache[len(self._recordsCache)-1].ROWID
          },
          'numRecordsStored': len(self._recordsCache)
        })

    # Add label to range [clippedStart, clippedEnd)
    for state in self._recordsCache[clippedStart:clippedEnd]:
      if labelName not in state.anomalyLabel:
        state.anomalyLabel.append(labelName)
        state.setByUser = True
        self._addRecordToKNN(state)

    assert len(self.saved_categories) > 0

    # Recompute [end, ...)
    for state in self._recordsCache[clippedEnd:]:
      self.classifyState(state)


  def removeLabels(self, start=None, end=None, labelFilter=None):
    """
    Remove labels from each record with record ROWID in range from
    start to end, noninclusive of end. Removes all records if labelFilter is
    None, otherwise only removes the labels eqaul to labelFilter.

    This will recalculate all points from end to the last record stored in the
    internal cache of this classifier.
    """
    if len(self._recordsCache) == 0:
      raise CLAModelInvalidRangeError("Invalid supplied range for "
        "'removeLabels'. Model has no saved records.")

    try:
      start = int(start)
    except Exception:
      start = 0

    try:
      end = int(end)
    except Exception:
      end = self._recordsCache[-1].ROWID

    startID = self._recordsCache[0].ROWID

    clippedStart = 0 if start is None else max(0, start - startID)
    clippedEnd = len(self._recordsCache) if end is None else \
      max(0, min( len( self._recordsCache) , end - startID))

    if clippedEnd <= clippedStart:
      raise CLAModelInvalidRangeError("Invalid supplied range for "
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
            'endRecordID': self._recordsCache[len(self._recordsCache)-1].ROWID
          },
          'numRecordsStored': len(self._recordsCache)
        })

    # Remove records within the cache
    recordsToDelete = []
    for state in self._recordsCache[clippedStart:clippedEnd]:
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
    for state in self._recordsCache[clippedEnd:]:
      self.classifyState(state)


  #############################################################################
  #
  # Methods to support serialization
  #
  #############################################################################


  def __getstate__(self):
    """
    Return serializable state.  This function will return a version of the
    __dict__ with all "ephemeral" members stripped out.  "Ephemeral" members
    are defined as those that do not need to be (nor should be) stored
    in any kind of persistent file (e.g., NuPIC network XML file.)
    """
    state = self.__dict__.copy()

    # Save knnclassifier properties
    state['_knnclassifierProps'] = state['_knnclassifier'].__getstate__()
    state.pop('_knnclassifier')
    return state


  def __setstate__(self, state):
    """
    Set the state of ourself from a serialized state.
    """
    if '_version' not in state or state['_version'] == 1:

      knnclassifierProps = state.pop('_knnclassifierProps')

      self.__dict__.update(state)
      self._knnclassifier = KNNClassifierRegion(**self._knnclassifierArgs)
      self._knnclassifier.__setstate__(knnclassifierProps)

      self._version = KNNAnomalyClassifierRegion.__VERSION__
    else:
      raise Exception("Invalid KNNAnomalyClassifierRegion version. Current "
          "version: %s" % (KNNAnomalyClassifierRegion.__VERSION__))


  def diff(self, knnRegion2):
    diff = []
    toCheck = [((), self.__getstate__(), knnRegion2.__getstate__())]
    while toCheck:
      keys, a, b = toCheck.pop()
      if type(a) != type(b):
        diff.append((keys, a, b))
      elif 'saved_categories' in keys:
        cats1 = set(a)
        cats2 = set(b)
        if cats1 != cats2:
          for k in cats1 - cats2:
            diff.append((keys + (k,), a[k], None))
          for k in cats1 - cats2:
            diff.append((keys + (k,), None, b[k]))
      elif '_recordsCache' in keys:
        if len(a) != len(b):
          diff.append((keys + ('len', ), len(a), len(b)))
        for i, v in enumerate(a):
          if not (a[i] == b[i]):
            diff.append((keys + ('_' + str(i), ), a[i].__getstate__(),
                b[i].__getstate__()))
      elif isinstance(a, dict):
        keys1 = set(a.keys())
        keys2 = set(b.keys())
        # If there are missing keys, add them to the diff.
        if keys1 != keys2:
          for k in keys1 - keys2:
            diff.append((keys + (k,), [k], None))
          for k in keys2 - keys1:
            diff.append((keys + (k,), None, b[k]))
        # For matching keys, add the values to the list of things to check.
        for k in keys1.union(keys2):
          toCheck.append((keys + (k,), a[k], b[k]))
      elif (isinstance(a, numpy.ndarray) or isinstance(a, list) or
            isinstance(a, tuple)):
        if len(a) != len(b):
          diff.append((keys + ('len', ), len(a), len(b)))
        elif not numpy.array_equal(a, b):
          diff.append((keys, a, b))
        #for i in xrange(len(a)):
        #  toCheck.append((keys + (k, i), a[i], b[i]))
      elif isinstance(a, Random):
        for i, v in enumerate(a.get_state()):
          toCheck.append((keys + (i,), v, b.get_state()[i]))
      else:
        try:
          _ = a != b
        except ValueError:
          raise ValueError(type(a))
        if a != b:
          diff.append((keys, a, b))
    return diff


  #############################################################################
  #
  # NuPIC 2 Support
  #    These methods are required by NuPIC 2
  #
  #############################################################################


  def getOutputElementCount(self, name):
    if name == 'labels':
      return self._maxLabelOutputs
    else:
      raise Exception("Invalid output name specified")



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


  def __eq__(self, other):
    return (self.ROWID == other.ROWID and
            self.anomalyScore == other.anomalyScore and
            self.anomalyLabel == other.anomalyLabel and
            self.setByUser == other.setByUser and
            numpy.array_equal(self.anomalyVector, other.anomalyVector))

