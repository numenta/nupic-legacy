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
This script provides a file-based implementation of the ``opf_environment``
interfaces (OPF).

This "basic" implementation of the interface (need a better name
instead of "basic") uses files (.csv, etc.) versus Nupic's implementation
that would use databases.

This implementation is used by research tools, such as
``scripts/run_opf_experiment.py``.

The ``opf_environment`` interfaces encapsulate external specifics, such as
data source (e.g., .csv file or database, etc.), prediction sink (.csv file or
databse, etc.), report and serialization destination,  etc.
"""

from abc import ABCMeta, abstractmethod
import copy
import csv
import json
import logging
import logging.handlers
import os
import shutil
import StringIO

import opf_utils
import opf_environment as opfenv
from nupic.data.file_record_stream import FileRecordStream
from nupic.data.stream_reader import StreamReader
from nupic.data.field_meta import (FieldMetaInfo,
                                   FieldMetaType,
                                   FieldMetaSpecial)
from nupic.data.inference_shifter import InferenceShifter
from opf_utils import InferenceType, InferenceElement



class PredictionMetricsLoggerIface(object):
  """ This is the interface for output of prediction metrics.
  """
  __metaclass__ = ABCMeta


  @abstractmethod
  def emitPeriodicMetrics(self, metrics):
    """ Emits periodic metrics to stdout in JSON.

    :param metrics: A list of metrics as returned by
          :meth:`nupic.frameworks.opf.opf_task_driver.OPFTaskDriver.getMetrics`.
    """


  @abstractmethod
  def emitFinalMetrics(self, metrics):
    """ Emits final metrics.

    .. note:: the intention is that the final metrics may go to a different
              place (e.g., csv file) versus :meth:`emitPeriodicMetrics`
              (e.g., stdout)

    :param metrics: A list of metrics as returned by
          :meth:`nupic.frameworks.opf.opf_task_driver.OPFTaskDriver.getMetrics`.
    """



class DatasetReaderIface(object):
  """ This is the interface class for a dataset readers
  """
  __metaclass__ = ABCMeta


  @abstractmethod
  def getDatasetFieldMetaData(self):
    """
    :returns:     a tuple of dataset field metadata descriptors that are
                  arranged in the same order as the columns in the dataset.
                  Each field metadata descriptor is of type
                  :class:`nupic.data.field_meta.FieldMetaInfo`
    """


  @abstractmethod
  def next(self):
    """
    :returns:     The next record from the dataset.  The returned record object
                  is of the same structure as returned by
                  :meth:`nupic.data.record_stream.RecordStreamIface.getNextRecord`.
                  Returns ``None`` if the next record is not available yet.

    :raises: (StopIteration) if a hard "end of file" has been reached
                  and no more records will be forthcoming.
    """



class PredictionWriterIface(object):
  """ This class defines the interface for prediction writer implementation
  returned by an object factory conforming to PredictionWriterFactoryIface
  """
  __metaclass__ = ABCMeta


  @abstractmethod
  def close(self):
    """ Closes the writer (e.g., close the underlying file)
    """

  @abstractmethod
  def append(self, inputRow, predictionRow, sequenceReset, metrics=None):
    """ Emits a single prediction as input versus predicted.

    inputRow:       A tuple or list of fields comprising the input data row.
    predictionRow:  A tuple or list of fields comprising the prediction, or None
                    if prediction is not available.  The None use case is
                    intended for temporal inference where there is no matching
                    prediction for the same timestep as the given ground truth,
                    such as the case with the very first input record.
    sequenceReset:  A value that tests True if the input row was
                    accompanied by a sequence reset signal; False if not
                    accompanied by a sequence reset signal.

    metrics:        OPTIONAL -A dictionary of metrics that will be written out
                    with every prediction. The keys are the automatically
                    generated metric labels (see MetricSpec in
                    prediction_metrics_manager.py), and the value is the real
                    number value of the metric.
    """

  @abstractmethod
  def checkpoint(self, checkpointSink, maxRows):
    """ Save a checkpoint of the prediction output stream. The checkpoint
    comprises up to maxRows of the most recent inference records.

    Parameters:
    ----------------------------------------------------------------------
    checkpointSink:     A File-like object where predictions checkpoint data, if
                        any, will be stored.
    maxRows:            Maximum number of most recent inference rows
                        to checkpoint.
    """



class BasicPredictionMetricsLogger(PredictionMetricsLoggerIface):
  """ This is the file-based implementation of the interface for output of
  prediction metrics

  TODO: where should periodic and final predictions go (versus stdout)

  :param experimentDir: (string) path to directory for experiment to run.

  :param label: (string) used to distinguish the output's container (e.g.,
         filename, directory name, property key, etc.).
  """

  def __init__(self, experimentDir, label):
    self.__experimentDir = experimentDir
    self.__label = label
    return


  def __repr__(self):
    return ("%s(experimentDir=%r,label=%r)" % (self.__class__.__name__,
                                               self.__experimentDir,
                                               self.__label))


  def emitPeriodicMetrics(self, metrics):
    jsonString = self._translateMetricsToJSON(metrics, label="PERIODIC")

    self._emitJSONStringToStdout(jsonString)
    return


  def emitFinalMetrics(self, metrics):
    jsonString = self._translateMetricsToJSON(metrics, label="FINAL")
    self._emitJSONStringToStdout(jsonString)
    return


  def _translateMetricsToJSON(self, metrics, label):
    """ Translates the given metrics value to JSON string

    metrics:        A list of dictionaries per OPFTaskDriver.getMetrics():

    Returns:        JSON string representing the given metrics object.
    """

    # Transcode the MetricValueElement values into JSON-compatible
    # structure
    metricsDict = metrics

    # Convert the structure to a display-friendly JSON string
    def _mapNumpyValues(obj):
      """
      """
      import numpy

      if isinstance(obj, numpy.float32):
        return float(obj)

      elif isinstance(obj, numpy.bool_):
        return bool(obj)

      elif isinstance(obj, numpy.ndarray):
        return obj.tolist()

      else:
        raise TypeError("UNEXPECTED OBJ: %s; class=%s" % (obj, obj.__class__))


    jsonString = json.dumps(metricsDict, indent=4, default=_mapNumpyValues)

    return jsonString


  def _emitJSONStringToStdout(self, jsonString):
    print '<JSON>'
    print jsonString
    print '</JSON>'



class BasicDatasetReader(DatasetReaderIface):
  """ This is a CSV file-based implementation of :class:`DatasetReaderIface`.

  :param streamDefDict: stream definition, as defined `here <stream-def.html>`_.
  """

  def __init__(self, streamDefDict):
    # Create the object to read from
    self._reader = StreamReader(streamDefDict, saveOutput=True)
    return


  def __iter__(self):
    return self


  def next(self):
    row = self._reader.getNextRecordDict()
    if row == None:
      raise StopIteration

    return row


  def getDatasetFieldMetaData(self):
    return FieldMetaInfo.createListFromFileFieldList(self._reader.getFields())



class _BasicPredictionWriter(PredictionWriterIface):
  """ This class defines the basic (file-based) implementation of
  PredictionWriterIface, whose instances are returned by
  BasicPredictionWriterFactory
  """
  def __init__(self, experimentDir, label, inferenceType,
               fields, metricNames=None, checkpointSource=None):
    """ Constructor

    experimentDir:
                  experiment directory path that contains description.py

    label:        A label string to incorporate into the filename.


    inferenceElements:


    inferenceType:
                  An constant from opf_utils.InferenceType for the
                  requested prediction writer

    fields:       a non-empty sequence of nupic.data.fieldmeta.FieldMetaInfo
                  representing fields that will be emitted to this prediction
                  writer

    metricNames:  OPTIONAL - A list of metric names that well be emiited by this
                  prediction writer

    checkpointSource:
                  If not None, a File-like object containing the
                  previously-checkpointed predictions for setting the initial
                  contents of this PredictionOutputStream.  Will be copied
                  before returning, if needed.
    """
    #assert len(fields) > 0

    self.__experimentDir = experimentDir

    # opf_utils.InferenceType kind value
    self.__inferenceType = inferenceType

    # A tuple of nupic.data.fieldmeta.FieldMetaInfo
    self.__inputFieldsMeta = tuple(copy.deepcopy(fields))
    self.__numInputFields = len(self.__inputFieldsMeta)
    self.__label = label
    if metricNames is not None:
      metricNames.sort()
    self.__metricNames = metricNames

    # Define our output field meta info
    self.__outputFieldsMeta = []

    # The list of inputs that we include in the prediction output
    self._rawInputNames = []

    # Output dataset
    self.__datasetPath = None
    self.__dataset = None

    # Save checkpoint data until we're ready to create the output dataset
    self.__checkpointCache = None
    if checkpointSource is not None:
      checkpointSource.seek(0)
      self.__checkpointCache = StringIO.StringIO()
      shutil.copyfileobj(checkpointSource, self.__checkpointCache)

    return


  def __openDatafile(self, modelResult):
    """Open the data file and write the header row"""

    # Write reset bit
    resetFieldMeta = FieldMetaInfo(
      name="reset",
      type=FieldMetaType.integer,
      special = FieldMetaSpecial.reset)

    self.__outputFieldsMeta.append(resetFieldMeta)


    # -----------------------------------------------------------------------
    # Write each of the raw inputs that go into the encoders
    rawInput = modelResult.rawInput
    rawFields = rawInput.keys()
    rawFields.sort()
    for field in rawFields:
      if field.startswith('_') or field == 'reset':
        continue
      value = rawInput[field]
      meta = FieldMetaInfo(name=field, type=FieldMetaType.string,
                           special=FieldMetaSpecial.none)
      self.__outputFieldsMeta.append(meta)
      self._rawInputNames.append(field)


    # -----------------------------------------------------------------------
    # Handle each of the inference elements
    for inferenceElement, value in modelResult.inferences.iteritems():
      inferenceLabel = InferenceElement.getLabel(inferenceElement)

      # TODO: Right now we assume list inferences are associated with
      # The input field metadata
      if type(value) in (list, tuple):
        # Append input and prediction field meta-info
        self.__outputFieldsMeta.extend(self.__getListMetaInfo(inferenceElement))

      elif isinstance(value, dict):
          self.__outputFieldsMeta.extend(self.__getDictMetaInfo(inferenceElement,
                                                                value))
      else:

        if InferenceElement.getInputElement(inferenceElement):
          self.__outputFieldsMeta.append(FieldMetaInfo(name=inferenceLabel+".actual",
                type=FieldMetaType.string, special = ''))
        self.__outputFieldsMeta.append(FieldMetaInfo(name=inferenceLabel,
                type=FieldMetaType.string, special = ''))

    if self.__metricNames:
      for metricName in self.__metricNames:
        metricField = FieldMetaInfo(
          name = metricName,
          type = FieldMetaType.float,
          special = FieldMetaSpecial.none)

        self.__outputFieldsMeta.append(metricField)

    # Create the inference directory for our experiment
    inferenceDir = _FileUtils.createExperimentInferenceDir(self.__experimentDir)

    # Consctruct the prediction dataset file path
    filename = (self.__label + "." +
                opf_utils.InferenceType.getLabel(self.__inferenceType) +
               ".predictionLog.csv")
    self.__datasetPath = os.path.join(inferenceDir, filename)

    # Create the output dataset
    print "OPENING OUTPUT FOR PREDICTION WRITER AT: %r" % self.__datasetPath
    print "Prediction field-meta: %r" % ([tuple(i) for i in self.__outputFieldsMeta],)
    self.__dataset = FileRecordStream(streamID=self.__datasetPath, write=True,
                                     fields=self.__outputFieldsMeta)

    # Copy data from checkpoint cache
    if self.__checkpointCache is not None:
      self.__checkpointCache.seek(0)

      reader = csv.reader(self.__checkpointCache, dialect='excel')

      # Skip header row
      try:
        header = reader.next()
      except StopIteration:
        print "Empty record checkpoint initializer for %r" % (self.__datasetPath,)
      else:
        assert tuple(self.__dataset.getFieldNames()) == tuple(header), \
          "dataset.getFieldNames(): %r; predictionCheckpointFieldNames: %r" % (
          tuple(self.__dataset.getFieldNames()), tuple(header))

      # Copy the rows from checkpoint
      numRowsCopied = 0
      while True:
        try:
          row = reader.next()
        except StopIteration:
          break

        #print "DEBUG: restoring row from checkpoint: %r" % (row,)

        self.__dataset.appendRecord(row)
        numRowsCopied += 1

      self.__dataset.flush()

      print "Restored %d rows from checkpoint for %r" % (
        numRowsCopied, self.__datasetPath)

      # Dispose of our checkpoint cache
      self.__checkpointCache.close()
      self.__checkpointCache = None

    return


  def setLoggedMetrics(self, metricNames):
    """ Tell the writer which metrics should be written

    Parameters:
    -----------------------------------------------------------------------
    metricsNames: A list of metric lables to be written
    """
    if metricNames is None:
      self.__metricNames = set([])
    else:
      self.__metricNames = set(metricNames)


  def close(self):
    """ [virtual method override] Closes the writer (e.g., close the underlying
    file)
    """

    if self.__dataset:
      self.__dataset.close()
    self.__dataset = None

    return


  def __getListMetaInfo(self, inferenceElement):
    """ Get field metadata information for inferences that are of list type
    TODO: Right now we assume list inferences are associated with the input field
    metadata
    """
    fieldMetaInfo = []
    inferenceLabel = InferenceElement.getLabel(inferenceElement)

    for inputFieldMeta in self.__inputFieldsMeta:
      if InferenceElement.getInputElement(inferenceElement):
        outputFieldMeta = FieldMetaInfo(
          name=inputFieldMeta.name + ".actual",
          type=inputFieldMeta.type,
          special=inputFieldMeta.special
        )

      predictionField = FieldMetaInfo(
        name=inputFieldMeta.name + "." + inferenceLabel,
        type=inputFieldMeta.type,
        special=inputFieldMeta.special
      )

      fieldMetaInfo.append(outputFieldMeta)
      fieldMetaInfo.append(predictionField)

    return fieldMetaInfo


  def __getDictMetaInfo(self, inferenceElement, inferenceDict):
    """Get field metadate information for inferences that are of dict type"""
    fieldMetaInfo = []
    inferenceLabel = InferenceElement.getLabel(inferenceElement)

    if InferenceElement.getInputElement(inferenceElement):
      fieldMetaInfo.append(FieldMetaInfo(name=inferenceLabel+".actual",
                                         type=FieldMetaType.string,
                                         special = ''))

    keys = sorted(inferenceDict.keys())
    for key in keys:
      fieldMetaInfo.append(FieldMetaInfo(name=inferenceLabel+"."+str(key),
                                         type=FieldMetaType.string,
                                         special=''))


    return fieldMetaInfo


  def append(self, modelResult):
    """ [virtual method override] Emits a single prediction as input versus
    predicted.

    modelResult:    An opf_utils.ModelResult object that contains the model input
                    and output for the current timestep.
    """

    #print "DEBUG: _BasicPredictionWriter: writing modelResult: %r" % (modelResult,)

    # If there are no inferences, don't write anything
    inferences = modelResult.inferences
    hasInferences = False
    if inferences is not None:
      for value in inferences.itervalues():
        hasInferences = hasInferences or (value is not None)

    if not hasInferences:
      return

    if self.__dataset is None:
      self.__openDatafile(modelResult)

    inputData = modelResult.sensorInput

    sequenceReset = int(bool(inputData.sequenceReset))
    outputRow = [sequenceReset]


    # -----------------------------------------------------------------------
    # Write out the raw inputs
    rawInput = modelResult.rawInput
    for field in self._rawInputNames:
      outputRow.append(str(rawInput[field]))

    # -----------------------------------------------------------------------
    # Write out the inference element info
    for inferenceElement, outputVal in inferences.iteritems():
      inputElement = InferenceElement.getInputElement(inferenceElement)
      if inputElement:
        inputVal = getattr(inputData, inputElement)
      else:
        inputVal = None

      if type(outputVal) in (list, tuple):
        assert type(inputVal) in (list, tuple, None)

        for iv, ov in zip(inputVal, outputVal):
          # Write actual
          outputRow.append(str(iv))

          # Write inferred
          outputRow.append(str(ov))
      elif isinstance(outputVal, dict):
        if inputVal is not None:
          # If we have a predicted field, include only that in the actuals
          if modelResult.predictedFieldName is not None:
            outputRow.append(str(inputVal[modelResult.predictedFieldName]))
          else:
            outputRow.append(str(inputVal))
        for key in sorted(outputVal.keys()):
          outputRow.append(str(outputVal[key]))
      else:
        if inputVal is not None:
          outputRow.append(str(inputVal))
        outputRow.append(str(outputVal))

    metrics = modelResult.metrics
    for metricName in self.__metricNames:
      outputRow.append(metrics.get(metricName, 0.0))

    #print "DEBUG: _BasicPredictionWriter: writing outputRow: %r" % (outputRow,)

    self.__dataset.appendRecord(outputRow)

    self.__dataset.flush()

    return

  def checkpoint(self, checkpointSink, maxRows):
    """ [virtual method override] Save a checkpoint of the prediction output
    stream. The checkpoint comprises up to maxRows of the most recent inference
    records.

    Parameters:
    ----------------------------------------------------------------------
    checkpointSink:     A File-like object where predictions checkpoint data, if
                        any, will be stored.
    maxRows:            Maximum number of most recent inference rows
                        to checkpoint.
    """

    checkpointSink.truncate()

    if self.__dataset is None:
      if self.__checkpointCache is not None:
        self.__checkpointCache.seek(0)
        shutil.copyfileobj(self.__checkpointCache, checkpointSink)
        checkpointSink.flush()
        return
      else:
        # Nothing to checkpoint
        return

    self.__dataset.flush()
    totalDataRows = self.__dataset.getDataRowCount()

    if totalDataRows == 0:
      # Nothing to checkpoint
      return

    # Open reader of prediction file (suppress missingValues conversion)
    reader = FileRecordStream(self.__datasetPath, missingValues=[])

    # Create CSV writer for writing checkpoint rows
    writer = csv.writer(checkpointSink)

    # Write the header row to checkpoint sink -- just field names
    writer.writerow(reader.getFieldNames())

    # Determine number of rows to checkpoint
    numToWrite = min(maxRows, totalDataRows)

    # Skip initial rows to get to the rows that we actually need to checkpoint
    numRowsToSkip = totalDataRows - numToWrite
    for i in xrange(numRowsToSkip):
      reader.next()

    # Write the data rows to checkpoint sink
    numWritten = 0
    while True:
      row = reader.getNextRecord()
      if row is None:
        break;

      row =  [str(element) for element in row]

      #print "DEBUG: _BasicPredictionWriter: checkpointing row: %r" % (row,)

      writer.writerow(row)

      numWritten +=1

    assert numWritten == numToWrite, \
      "numWritten (%s) != numToWrite (%s)" % (numWritten, numToWrite)


    checkpointSink.flush()

    return



###############################################################################
# Prediction Log adapters
###############################################################################



class NonTemporalPredictionLogAdapter(object):
  """ This class serves as an adapter for a client-instantiated Non-temporal log
  writer.

  :param writer: (:class:`PredictionWriterIface`) Non-temporal prediction log
         writer
  """
  def __init__(self, writer):
    self.__writer = writer
    return


  def close(self):
    self.__writer.close()
    self.__writer = None
    return


  def update(self, modelResult):
    """ Emit a input/prediction pair, if possible.

    modelResult:    An opf_utils.ModelResult object that contains the model input
                    and output for the current timestep.
    """
    self.__writer.append(modelResult)
    return



class TemporalPredictionLogAdapter(object):
  """This class serves as an adapter for a client-instantiated Temporal log
  writer.  It maintains a prediction FIFO for matching T(i+1) input record
  with T(i=1) prediction for outputting to the log writer.

  TODO: Right now this is broken
  """
  def __init__(self, writer):
    """
    writer:       Non-temporal prediction log writer conforming to
                  PredictionWriterIface interface.
    """

    self.__logger = logging.getLogger(".".join(
      ['com.numenta', self.__class__.__module__, self.__class__.__name__]))

    self.__writer = writer
    self.__inferenceShifter = InferenceShifter()
    return


  def close(self):
    self.__writer.close()
    self.__writer = None
    return


  def update(self, modelResult):
    """ Queue up the T(i+1) prediction value and emit a T(i)
    input/prediction pair, if possible.  E.g., if the previous T(i-1)
    iteration was learn-only, then we would not have a T(i) prediction in our
    FIFO and would not be able to emit a meaningful input/prediction
    pair.

    modelResult:    An opf_utils.ModelResult object that contains the model input
                    and output for the current timestep.
    """
    self.__writer.append(self.__inferenceShifter.shift(modelResult))



class BasicPredictionLogger(opfenv.PredictionLoggerIface):
  """ This class implements logging of predictions to files as actual vs
  predicted values.

  :param fields: (list) of :class:`nupic.data.field_meta.FieldMetaInfo` objects
         representing the encoder-mapped data row field value sequences that
         will be emitted to this prediction logger.

  :param experimentDir: (string) experiment directory path that contains
         description.py

  :param label: (string) to incorporate into the filename.

  :param checkpointSource: If not None, a File-like object containing the
         previously-checkpointed predictions for setting the initial contents of
         this output stream.  Will be copied before returning, if
         needed.
  """

  def __init__(self, fields, experimentDir, label, inferenceType,
               checkpointSource=None):
    #assert len(fields) > 0

    self.__reprString = (
      "%s(fields=%r)" % (
        self.__class__.__name__, fields))


    self.__inputFieldsMeta = tuple(copy.deepcopy(fields))
    self.__experimentDir = experimentDir
    self.__label = label
    self.__inferenceType = inferenceType
    self.__writer = None

    self.__logAdapter = None
    self.__loggedMetricNames = None

    # Save checkpoint data until we're ready to create the output writer
    self.__checkpointCache = None
    if checkpointSource is not None:
      checkpointSource.seek(0)
      self.__checkpointCache = StringIO.StringIO()
      shutil.copyfileobj(checkpointSource, self.__checkpointCache)

    return


  def __repr__(self):
    return self.__reprString


  def close(self):
    if self.__logAdapter:
      self.__logAdapter.close()
    self.__logAdapter = None
    return


  def writeRecord(self, modelResult):
    self.writeRecords([modelResult])
    return


  def writeRecords(self, modelResults, progressCB=None):
    # Instantiate the logger if it doesn't exist yet
    if self.__logAdapter is None and modelResults:
      self.__writer = _BasicPredictionWriter(
                                      experimentDir=self.__experimentDir,
                                      label=self.__label,
                                      inferenceType=self.__inferenceType,
                                      fields=self.__inputFieldsMeta,
                                      metricNames=self.__loggedMetricNames,
                                      checkpointSource=self.__checkpointCache)

      # Dispose of our checkpoint cache now
      if self.__checkpointCache is not None:
        self.__checkpointCache.close()
        self.__checkpointCache = None

      if InferenceType.isTemporal(self.__inferenceType):
        logAdapterClass = TemporalPredictionLogAdapter
      else:
        logAdapterClass = NonTemporalPredictionLogAdapter

      self.__logAdapter = logAdapterClass(self.__writer)
      self.__writer.setLoggedMetrics(self.__loggedMetricNames)


    for modelResult in modelResults:
      if modelResult.inferences is not None:
        # -----------------------------------------------------------------------
        # Update the prediction log
        self.__logAdapter.update(modelResult)

      else:
        # Handle the learn-only scenario: pass input to existing logAdapters
        self.__logAdapter.update(modelResult)

    return

  def setLoggedMetrics(self, metricNames):
    self.__loggedMetricNames = metricNames
    if self.__writer is not None:
      self.__writer.setLoggedMetrics(metricNames)

  def checkpoint(self, checkpointSink, maxRows):
    checkpointSink.truncate()

    if self.__writer is None:
      if self.__checkpointCache is not None:
        self.__checkpointCache.seek(0)
        shutil.copyfileobj(self.__checkpointCache, checkpointSink)
        checkpointSink.flush()
        return
      else:
        # Nothing to checkpoint
        return

    self.__writer.checkpoint(checkpointSink, maxRows)
    return



class _FileUtils(object):
  @staticmethod
  def getExperimentInferenceDirPath(experimentDir):
    """
    experimentDir:  experiment directory path that contains description.py

    Returns: experiment inference directory path string (the path may not
              yet exist - see createExperimentInferenceDir())
    """
    return os.path.abspath(os.path.join(experimentDir, "inference"))


  @classmethod
  def createExperimentInferenceDir(cls, experimentDir):
    """ Creates the inference output directory for the given experiment

    experimentDir:  experiment directory path that contains description.py

    Returns:  path of the inference output directory
    """
    path = cls.getExperimentInferenceDirPath(experimentDir)

    cls.makeDirectory(path)

    return path


  @staticmethod
  def makeDirectory(path):
    """ Makes directory for the given directory path if it doesn't already exist
    in the filesystem.  Creates all requested directory segments as needed.

    path:   path of the directory to create.

    Returns:      nothing
    """
    # Create the experiment directory
    # TODO Is default mode (0777) appropriate?
    try:
      os.makedirs(path)
    except OSError as e:
      if e.errno == os.errno.EEXIST:
        #print "Experiment directory already exists (that's okay)."
        pass
      else:
        raise

    return



def test():
  #testLogging()
  return



#def testLogging():
#  dir = os.path.expanduser('~/nupic/trunk/examples/opf/experiments/opfrunexperiment_test/base')
#  outfile = "test.log"
#  message = "This is a test message."
#  filepath = "%s/%s" % (dir,outfile)
#
#  if os.path.exists(filepath):
#    os.remove(filepath)
#
#  logOutputDesc = dict(
#      outputDestination = [outfile],
#      level = "DEBUG",
#      format = '%(levelname)10s: %(asctime)s - %(name)s. %(message)s'
#  )
#  logHandlerFactory = BasicLoggingHandlerFactory(dir)
#  logHandlerList = logHandlerFactory(logOutputDesc)
#  for handler in logHandlerList:
#    logging.root.addHandler(handler)
#
#  logger = logging.getLogger("test.logger")
#  logger.setLevel(logging.DEBUG)
#
#  logger.debug(message)
#  logger.info(message)
#
#  f = open(filepath)
#  fcontents = f.read()
#  import string
#  c = string.count(fcontents, message)
#  assert(c == 2)
#  os.remove(filepath)
#
#  print "Logging test passed."
#  return



if __name__ == "__main__":
  test()
