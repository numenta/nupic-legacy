
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013-15, Numenta, Inc.  Unless you have an agreement
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
import numpy
from nupic.bindings.regions.PyRegion import PyRegion
from nupic.data.field_meta import FieldMetaType
from nupic.encoders.multi import MultiEncoder

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.encoders.record_sensor_capnp import RecordSensorProto



class RecordSensor(PyRegion):
  """
  A Record Sensor (RS) retrieves an information "record" and encodes
  it to be suitable as input to an HTM.

  An information record is analogous database record -- it is just a
  collection of typed values: date, amount, category, location, etc.

  The RS may obtain information from one of two sources:
    . a file (e.g. csv or tsv)
    . a data generator (for artificial data)

  The RS encodes a record using an encoding scheme that can be specified
  programmatically.

  An RS is essentially a shell containing two objects:

  1. `dataSource` object gets one record at a time. This record is returned
     either as a dictionary or a user-defined object. The fields within a record
     correspond to entries in the dictionary or attributes of the object. For
     example, a `dataSource` might return:

     .. code-block:: python
    
        dict(date="02-01-2010 23:12:23", amount=4.95, country="US",
             _reset=0, _sequenceId=0)
    
     or an object with attributes `date`, `amount` and `country`.
    
     A data source is typically a 
     :class:`nupic.data.file_record_stream.FileRecordStream`: or an artificial 
     data generator.

  2. An `encoder` object encodes one record into a fixed-sparsity
     distributed representation. Usually 
     :class:`nupic.encoders.multi.MultiEncoder`.

     Example usage in NuPIC:
  
     .. code-block:: python
   
       from nupic.net import Network
       from nupic.encoders import MultiEncoder
       from nupic.data.file.file_record_stream import FileRecordStream
     
       n = Network()
       s = n.addRegion("sensor", "py.RecordSensor", "")
       mysource = FileRecordStream("mydata.txt")
       myencoder = MultiEncoder()
       ... set up myencoder ...
       s.getSelf().dataSource = mysource
       s.getSelf().encoder = myencoder
     
       l1 = n.addRegion("l1", "py.TestRegion", "[create params]")
       n.initialize()
     
       n.run(100)


  :param verbosity: (int) verbosity, default 0 
  :param numCategories: (int) number of categories, default 1 
  """

  @classmethod
  def getSpec(cls):
    ns = dict(
      singleNodeOnly=True,
      description="Sensor that reads data records and encodes them for an HTM",
      outputs=dict(
        actValueOut=dict(
          description="Actual value of the field to predict. The index of the "
                      "field to predict must be specified via the parameter "
                      "predictedField. If this parameter is not set, then "
                      "actValueOut won't be populated.",
          dataType="Real32",
          count=0,
          regionLevel=True,
          isDefaultOutput=False),
        bucketIdxOut=dict(
          description="Active index of the encoder bucket for the "
                      "actual value of the field to predict. The index of the "
                      "field to predict must be specified via the parameter "
                      "predictedField. If this parameter is not set, then "
                      "actValueOut won't be populated.",
          dataType="UInt64",
          count=0,
          regionLevel=True,
          isDefaultOutput=False),
        dataOut=dict(
          description="Encoded data",
          dataType="Real32",  # inefficient for bits, but that's what we use now
          count=0,
          regionLevel=True,
          isDefaultOutput=True),
        resetOut=dict(
          description="Reset signal",
          dataType="Real32",
          count=1,
          regionLevel=True,
          isDefaultOutput=False),
        sequenceIdOut=dict(
          description="Sequence ID",
          dataType='UInt64',
          count=1,
          regionLevel=True,
          isDefaultOutput=False),
        categoryOut=dict(
          description="Category",
          dataType='Real32',
          count=0,
          regionLevel=True,
          isDefaultOutput=False),
        sourceOut=dict(
          description="Unencoded data from the source, input to the encoder",
          dataType="Real32",
          count=0,
          regionLevel=True,
          isDefaultOutput=False),
        spatialTopDownOut=dict(
          description="The top-down output signal, generated from "
                      "feedback from SP",
          dataType='Real32',
          count=0,
          regionLevel=True,
          isDefaultOutput=False),
        temporalTopDownOut=dict(
          description="The top-down output signal, generated from "
                      "feedback from TM through SP",
          dataType='Real32',
          count=0,
          regionLevel=True,
          isDefaultOutput=False),
      ),
      inputs=dict(
        spatialTopDownIn=dict(
          description="The top-down input signal, generated from "
                      "feedback from SP",
          dataType='Real32',
          count=0,
          required=False,
          regionLevel=True,
          isDefaultInput=False,
          requireSplitterMap=False),
        temporalTopDownIn=dict(
          description="The top-down input signal, generated from "
                      "feedback from TM through SP",
          dataType='Real32',
          count=0,
          required=False,
          regionLevel=True,
          isDefaultInput=False,
          requireSplitterMap=False),
      ),
      parameters=dict(
        verbosity=dict(
          description="Verbosity level",
          dataType="UInt32",
          accessMode="ReadWrite",
          count=1,
          constraints=""),
        numCategories=dict(
          description="Total number of categories to expect from the "
                      "FileRecordStream",
          dataType="UInt32",
          accessMode="ReadWrite",
          count=1,
          constraints=""),
        predictedField=dict(
          description="The name of the field to be predicted. This will result "
                      "in the outputs actValueOut and bucketIdxOut not being "
                      "populated.",
          dataType="Byte",
          accessMode="ReadWrite",
          count=0,
          defaultValue=-1,
          constraints=""),
        topDownMode=dict(
          description="1 if the node should do top down compute on the next "
                      "call to compute into topDownOut (default 0).",
          accessMode="ReadWrite",
          dataType="UInt32",
          count=1,
          constraints="bool"),
      ),
      commands=dict())

    return ns


  def __init__(self, verbosity=0, numCategories=1):
    self.encoder = None
    self.disabledEncoder = None
    self.dataSource = None
    self._outputValues = {}

    self.preEncodingFilters = []
    self.postEncodingFilters = []
    self.topDownMode = False
    self.verbosity = verbosity
    self.numCategories = numCategories
    self._iterNum = 0

    # Optional field for which we want to populate bucketIdxOut
    # and actValueOut. If predictedField is None, then bucketIdxOut and
    # actValueOut won't be populated.
    self.predictedField = None

    # lastRecord is the last record returned. Used for debugging only
    self.lastRecord = None


  def __setstate__(self, state):
    # Default value for older versions being deserialized.
    self.disabledEncoder = None
    self.__dict__.update(state)
    if not hasattr(self, "numCategories"):
      self.numCategories = 1


  def initialize(self):
    if self.encoder is None:
      raise Exception("Unable to initialize RecordSensor "
                      "-- encoder has not been set")
    if self.dataSource is None:
      raise Exception("Unable to initialize RecordSensor "
                      "-- dataSource has not been set")


  def rewind(self):
    """ Reset the sensor to beginning of data.
    """
    self._iterNum = 0
    if self.dataSource is not None:
      self.dataSource.rewind()


  def getNextRecord(self):
    """
    Get the next record to encode. Includes getting a record from the 
    `dataSource` and applying filters. If the filters request more data from the 
    `dataSource` continue to get data from the `dataSource` until all filters 
    are satisfied. This method is separate from :meth:`.RecordSensor.compute` so that we can 
    use a standalone :class:`.RecordSensor` to get filtered data.
    """

    allFiltersHaveEnoughData = False
    while not allFiltersHaveEnoughData:
      # Get the data from the dataSource
      data = self.dataSource.getNextRecordDict()

      if not data:
        raise StopIteration("Datasource has no more data")

      # temporary check
      if "_reset" not in data:
        data["_reset"] = 0
      if "_sequenceId" not in data:
        data["_sequenceId"] = 0
      if "_category" not in data:
        data["_category"] = [None]

      data, allFiltersHaveEnoughData = self.applyFilters(data)

    self.lastRecord = data

    return data


  def applyFilters(self, data):
    """
    Apply pre-encoding filters. These filters may modify or add data. If a 
    filter needs another record (e.g. a delta filter) it will request another 
    record by returning False and the current record will be skipped (but will 
    still be given to all filters).

    We have to be very careful about resets. A filter may add a reset,
    but other filters should not see the added reset, each filter sees
    the original reset value, and we keep track of whether any filter
    adds a reset.

    :param data: (dict) The data that will be processed by the filter.
    :returns: (tuple) with the data processed by the filter and a boolean to
              know whether or not the filter needs mode data.
    """

    if self.verbosity > 0:
      print "RecordSensor got data: %s" % data

    allFiltersHaveEnoughData = True
    if len(self.preEncodingFilters) > 0:
      originalReset = data['_reset']
      actualReset = originalReset
      for f in self.preEncodingFilters:
        # if filter needs more data, it returns False
        filterHasEnoughData = f.process(data)
        allFiltersHaveEnoughData = (allFiltersHaveEnoughData
                                    and filterHasEnoughData)
        actualReset = actualReset or data['_reset']
        data['_reset'] = originalReset
      data['_reset'] = actualReset

    return data, allFiltersHaveEnoughData


  def populateCategoriesOut(self, categories, output):
    """
    Populate the output array with the category indices.
    
    .. note:: Non-categories are represented with ``-1``.

    :param categories: (list) of category strings
    :param output: (list) category output, will be overwritten
    """
    if categories[0] is None:
      # The record has no entry in category field.
      output[:] = -1
    else:
      # Populate category output array by looping over the smaller of the
      # output array (size specified by numCategories) and the record's number
      # of categories.
      for i, cat in enumerate(categories[:len(output)]):
        output[i] = cat
      output[len(categories):] = -1


  def compute(self, inputs, outputs):
    """
    Get a record from the dataSource and encode it.
    
    Overrides :meth:`nupic.bindings.regions.PyRegion.PyRegion.compute`.
    """
    if not self.topDownMode:
      data = self.getNextRecord()

      # The private keys in data are standard of RecordStreamIface objects. Any
      # add'l keys are column headers from the data source.
      reset = data["_reset"]
      sequenceId = data["_sequenceId"]
      categories = data["_category"]

      # Encode the processed records; populate outputs["dataOut"] in place
      self.encoder.encodeIntoArray(data, outputs["dataOut"])

      # If there is a field to predict, set bucketIdxOut and actValueOut.
      # There is a special case where a predicted field might be a vector, as in
      # the CoordinateEncoder. Since this encoder does not provide bucket
      # indices for prediction, we will ignore it.
      if self.predictedField is not None and self.predictedField != "vector":
        allEncoders = list(self.encoder.encoders)
        if self.disabledEncoder is not None:
          allEncoders.extend(self.disabledEncoder.encoders)
        encoders = [e for e in allEncoders
                    if e[0] == self.predictedField]
        if len(encoders) == 0:
          raise ValueError("There is no encoder for set for the predicted "
                           "field: %s" % self.predictedField)
        # TODO: Figure out why there are sometimes multiple encoders with the
        # same name.
        #elif len(encoders) > 1:
        #  raise ValueError("There cant' be more than 1 encoder for the "
        #                   "predicted field: %s" % self.predictedField)
        else:
          encoder = encoders[0][1]

        actualValue = data[self.predictedField]
        outputs["bucketIdxOut"][:] = encoder.getBucketIndices(actualValue)
        if isinstance(actualValue, str):
          outputs["actValueOut"][:] = encoder.getBucketIndices(actualValue)
        else:
          outputs["actValueOut"][:] = actualValue

      # Write out the scalar values obtained from they data source.
      outputs["sourceOut"][:] = self.encoder.getScalars(data)
      self._outputValues["sourceOut"] = self.encoder.getEncodedValues(data)

      # -----------------------------------------------------------------------
      # Get the encoded bit arrays for each field
      encoders = self.encoder.getEncoderList()
      prevOffset = 0
      sourceEncodings = []
      bitData = outputs["dataOut"]
      for encoder in encoders:
        nextOffset = prevOffset + encoder.getWidth()
        sourceEncodings.append(bitData[prevOffset:nextOffset])
        prevOffset = nextOffset
      self._outputValues['sourceEncodings'] = sourceEncodings

      # Execute post-encoding filters, if any
      for filter in self.postEncodingFilters:
        filter.process(encoder=self.encoder, data=outputs['dataOut'])

      # Populate the output numpy arrays; must assign by index.
      outputs['resetOut'][0] = reset
      outputs['sequenceIdOut'][0] = sequenceId
      self.populateCategoriesOut(categories, outputs['categoryOut'])

      # ------------------------------------------------------------------------
      # Verbose print?
      if self.verbosity >= 1:
        if self._iterNum == 0:
          self.encoder.pprintHeader(prefix="sensor:")
        if reset:
          print "RESET - sequenceID:%d" % sequenceId
        if self.verbosity >= 2:
          print

      # If verbosity >=2, print the record fields
      if self.verbosity >= 1:
        self.encoder.pprint(outputs["dataOut"], prefix="%7d:" % (self._iterNum))
        scalarValues = self.encoder.getScalars(data)
        nz = outputs["dataOut"].nonzero()[0]
        print "     nz: (%d)" % (len(nz)), nz
        print "  encIn:", self.encoder.scalarsToStr(scalarValues)
      if self.verbosity >= 2:
        # if hasattr(data, 'header'):
        #  header = data.header()
        # else:
        #  header = '     '.join(self.dataSource.names)
        # print "        ", header
        print "   data:", str(data)
      if self.verbosity >= 3:
        decoded = self.encoder.decode(outputs["dataOut"])
        print "decoded:", self.encoder.decodedToStr(decoded)

      self._iterNum += 1

    else:

      # ========================================================================
      # Spatial
      # ========================================================================
      # This is the top down compute in sensor

      # We get the spatial pooler's topDownOut as spatialTopDownIn
      spatialTopDownIn = inputs['spatialTopDownIn']
      spatialTopDownOut = self.encoder.topDownCompute(spatialTopDownIn)

      # -----------------------------------------------------------------------
      # Split topDownOutput into seperate outputs
      values = [elem.value for elem in spatialTopDownOut]
      scalars = [elem.scalar for elem in spatialTopDownOut]
      encodings = [elem.encoding for elem in spatialTopDownOut]
      self._outputValues['spatialTopDownOut'] = values
      outputs['spatialTopDownOut'][:] = numpy.array(scalars)
      self._outputValues['spatialTopDownEncodings'] = encodings

      # ========================================================================
      # Temporal
      # ========================================================================

      ## TODO: Add temporal top-down loop
      # We get the temporal memory's topDownOut passed through the spatial
      # pooler as temporalTopDownIn
      temporalTopDownIn = inputs['temporalTopDownIn']
      temporalTopDownOut = self.encoder.topDownCompute(temporalTopDownIn)

      # -----------------------------------------------------------------------
      # Split topDownOutput into separate outputs

      values = [elem.value for elem in temporalTopDownOut]
      scalars = [elem.scalar for elem in temporalTopDownOut]
      encodings = [elem.encoding for elem in temporalTopDownOut]
      self._outputValues['temporalTopDownOut'] = values
      outputs['temporalTopDownOut'][:] = numpy.array(scalars)
      self._outputValues['temporalTopDownEncodings'] = encodings

      assert len(spatialTopDownOut) == len(temporalTopDownOut), (
        "Error: spatialTopDownOut and temporalTopDownOut should be the same "
        "size")


  def _convertNonNumericData(self, spatialOutput, temporalOutput, output):
    """
    Converts all of the non-numeric fields from spatialOutput and temporalOutput
    into their scalar equivalents and records them in the output dictionary.

    :param spatialOutput: The results of topDownCompute() for the spatial input.
    :param temporalOutput: The results of topDownCompute() for the temporal
      input.
    :param output: The main dictionary of outputs passed to compute(). It is
      expected to have keys 'spatialTopDownOut' and 'temporalTopDownOut' that
      are mapped to numpy arrays.
    """
    encoders = self.encoder.getEncoderList()
    types = self.encoder.getDecoderOutputFieldTypes()
    for i, (encoder, type) in enumerate(zip(encoders, types)):
      spatialData = spatialOutput[i]
      temporalData = temporalOutput[i]

      if type != FieldMetaType.integer and type != FieldMetaType.float:
        # TODO: Make sure that this doesn't modify any state
        spatialData = encoder.getScalars(spatialData)[0]
        temporalData = encoder.getScalars(temporalData)[0]

      assert isinstance(spatialData, (float, int))
      assert isinstance(temporalData, (float, int))
      output['spatialTopDownOut'][i] = spatialData
      output['temporalTopDownOut'][i] = temporalData


  def getOutputValues(self, outputName):
    """
    .. note:: These are normal Python lists, rather than numpy arrays. This is 
              to support lists with mixed scalars and strings, as in the case of 
              records with categorical variables.
    
    :returns: (dict) output values. 
    """
    return self._outputValues[outputName]


  def getOutputElementCount(self, name):
    """
    Computes the width of dataOut.

    Overrides 
    :meth:`nupic.bindings.regions.PyRegion.PyRegion.getOutputElementCount`.
    """

    if name == "resetOut":
      print ("WARNING: getOutputElementCount should not have been called with "
             "resetOut")
      return 1

    elif name == "sequenceIdOut":
      print ("WARNING: getOutputElementCount should not have been called with "
             "sequenceIdOut")
      return 1

    elif name == "dataOut":
      if self.encoder is None:
        raise Exception("NuPIC requested output element count for 'dataOut' "
                        "on a RecordSensor node, but the encoder has not "
                        "been set")
      return self.encoder.getWidth()

    elif name == "sourceOut":
      if self.encoder is None:
        raise Exception("NuPIC requested output element count for 'sourceOut' "
                        "on a RecordSensor node, "
                        "but the encoder has not been set")
      return len(self.encoder.getDescription())

    elif name == "bucketIdxOut":
      return 1

    elif name == "actValueOut":
      return 1

    elif name == "categoryOut":
      return self.numCategories

    elif name == 'spatialTopDownOut' or name == 'temporalTopDownOut':
      if self.encoder is None:
        raise Exception("NuPIC requested output element count for 'sourceOut' "
                        "on a RecordSensor node, "
                        "but the encoder has not been set")
      return len(self.encoder.getDescription())
    else:
      raise Exception("Unknown output %s" % name)


  def setParameter(self, parameterName, index, parameterValue):
    """
      Set the value of a Spec parameter. Most parameters are handled
      automatically by PyRegion's parameter set mechanism. The ones that need
      special treatment are explicitly handled here.
    """
    if parameterName == 'topDownMode':
      self.topDownMode = parameterValue
    elif parameterName == 'predictedField':
      self.predictedField = parameterValue
    else:
      raise Exception('Unknown parameter: ' + parameterName)


  @staticmethod
  def getSchema():
    """
    Overrides :meth:`nupic.bindings.regions.PyRegion.PyRegion.getSchema`.
    """
    return RecordSensorProto


  def writeToProto(self, proto):
    """
    Overrides :meth:`nupic.bindings.regions.PyRegion.PyRegion.writeToProto`.
    """
    self.encoder.write(proto.encoder)
    if self.disabledEncoder is not None:
      self.disabledEncoder.write(proto.disabledEncoder)
    proto.topDownMode = int(self.topDownMode)
    proto.verbosity = self.verbosity
    proto.numCategories = self.numCategories


  @classmethod
  def readFromProto(cls, proto):
    """    
    Overrides :meth:`nupic.bindings.regions.PyRegion.PyRegion.readFromProto`.
    """
    instance = cls()

    instance.encoder = MultiEncoder.read(proto.encoder)
    if proto.disabledEncoder is not None:
      instance.disabledEncoder = MultiEncoder.read(proto.disabledEncoder)
    instance.topDownMode = bool(proto.topDownMode)
    instance.verbosity = proto.verbosity
    instance.numCategories = proto.numCategories

    return instance
