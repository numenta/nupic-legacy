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

import random as rand

from nupic.encoders import adaptive_scalar, sdr_category, date
from nupic.bindings.math import GetNTAReal
from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
from nupic.data.generators.distributions import *


realDType = GetNTAReal()

class DataGenerator():
  """The DataGenerator provides a framework for generating, encoding, saving
  and exporting records. Each column of the output contains records with a
  specific set of parameters such as encoderType, n, w, etc. This interface
  is intended to be used for testing the spatial pooler, temporal memory and
  for generating artificial datasets.
  """


  def __init__(self, name='testDataset', seed=42, verbosity=0):
    """Initialize the dataset generator with a random seed and a name"""

    self.name=name
    self.verbosity=verbosity
    self.setSeed(seed)
    self.fields=[]


  def getDescription(self):
    """Returns a description of the dataset"""

    description = {'name':self.name, 'fields':[f.name for f in self.fields], \
      'numRecords by field':[f.numRecords for f in self.fields]}

    return description


  def setSeed(self, seed):
    """Set the random seed and the numpy seed
    Parameters:
    --------------------------------------------------------------------
    seed:             random seed
    """

    rand.seed(seed)
    np.random.seed(seed)


  def addField(self, name, fieldParams, encoderParams):
    """Add a single field to the dataset.
    Parameters:
    -------------------------------------------------------------------
    name:             The user-specified name of the field
    fieldSpec:        A list of one or more dictionaries specifying parameters
                      to be used for dataClass initialization. Each dict must
                      contain the key 'type' that specifies a distribution for
                      the values in this field
    encoderParams:    Parameters for the field encoder
    """

    assert fieldParams is not None and'type' in fieldParams

    dataClassName = fieldParams.pop('type')
    try:
      dataClass=eval(dataClassName)(fieldParams)

    except TypeError, e:
      print ("#### Error in constructing %s class object. Possibly missing "
              "some required constructor parameters. Parameters "
              "that were provided are: %s" % (dataClass, fieldParams))
      raise

    encoderParams['dataClass']=dataClass
    encoderParams['dataClassName']=dataClassName

    fieldIndex = self.defineField(name, encoderParams)


  def addMultipleFields(self, fieldsInfo):
    """Add multiple fields to the dataset.
    Parameters:
    -------------------------------------------------------------------
    fieldsInfo:       A list of dictionaries, containing a field name, specs for
                      the data classes and encoder params for the corresponding
                      field.
    """
    assert all(x in field for x in ['name', 'fieldSpec', 'encoderParams'] for field \
               in fieldsInfo)

    for spec in fieldsInfo:
      self.addField(spec.pop('name'), spec.pop('fieldSpec'), spec.pop('encoderParams'))


  def defineField(self, name, encoderParams=None):
    """Initialize field using relevant encoder parameters.
    Parameters:
    -------------------------------------------------------------------
    name:                 Field name
    encoderParams:        Parameters for the encoder.

    Returns the index of the field
    """
    self.fields.append(_field(name, encoderParams))

    return len(self.fields)-1


  def setFlag(self, index, flag):
    """Set flag for field at index. Flags are special characters such as 'S' for
    sequence or 'T' for timestamp.
    Parameters:
    --------------------------------------------------------------------
    index:            index of field whose flag is being set
    flag:             special character
    """
    assert len(self.fields)>index
    self.fields[index].flag=flag


  def generateRecord(self, record):
    """Generate a record. Each value is stored in its respective field.
    Parameters:
    --------------------------------------------------------------------
    record:       A 1-D array containing as many values as the number of fields
    fields:       An object of the class field that specifies the characteristics
                  of each value in the record
    Assertion:
    --------------------------------------------------------------------
    len(record)==len(fields):   A value for each field must be specified.
                                Replace missing values of any type by
                                SENTINEL_VALUE_FOR_MISSING_DATA

    This method supports external classes but not combination of classes.
    """
    assert(len(record)==len(self.fields))
    if record is not None:
      for x in range(len(self.fields)):
        self.fields[x].addValue(record[x])

    else:
      for field in self.fields:
        field.addValue(field.dataClass.getNext())


  def generateRecords(self, records):
    """Generate multiple records. Refer to definition for generateRecord"""

    if self.verbosity>0: print 'Generating', len(records), 'records...'
    for record in records:
      self.generateRecord(record)


  def getRecord(self, n=None):
    """Returns the nth record"""

    if n is None:
      assert len(self.fields)>0
      n = self.fields[0].numRecords-1

    assert (all(field.numRecords>n for field in self.fields))

    record = [field.values[n] for field in self.fields]

    return record


  def getAllRecords(self):
    """Returns all the records"""
    values=[]
    numRecords = self.fields[0].numRecords
    assert (all(field.numRecords==numRecords for field in self.fields))

    for x in range(numRecords):
      values.append(self.getRecord(x))

    return values


  def encodeRecord(self, record, toBeAdded=True):
    """Encode a record as a sparse distributed representation
    Parameters:
    --------------------------------------------------------------------
    record:        Record to be encoded
    toBeAdded:     Whether the encodings corresponding to the record are added to
                   the corresponding fields
    """
    encoding=[self.fields[i].encodeValue(record[i], toBeAdded) for i in \
              xrange(len(self.fields))]

    return encoding


  def encodeAllRecords(self, records=None, toBeAdded=True):
    """Encodes a list of records.
    Parameters:
    --------------------------------------------------------------------
    records:      One or more records. (i,j)th element of this 2D array
                  specifies the value at field j of record i.
                  If unspecified, records previously generated and stored are
                  used.
    toBeAdded:    Whether the encodings corresponding to the record are added to
                  the corresponding fields
    """
    if records is None:
      records = self.getAllRecords()
    if self.verbosity>0: print 'Encoding', len(records), 'records.'
    encodings = [self.encodeRecord(record, toBeAdded) for record in records]

    return encodings


  def addValueToField(self, i, value=None):
    """Add 'value' to the field i.
    Parameters:
    --------------------------------------------------------------------
    value:       value to be added
    i:           value is added to field i
    """

    assert(len(self.fields)>i)
    if value is None:
      value = self.fields[i].dataClass.getNext()
      self.fields[i].addValue(value)
      return value

    else: self.fields[i].addValue(value)


  def addValuesToField(self, i, numValues):
    """Add values to the field i."""

    assert(len(self.fields)>i)
    values = [self.addValueToField(i) for n in range(numValues)]
    return values


  def getSDRforValue(self, i, j):
    """Returns the sdr for jth value at column i"""
    assert len(self.fields)>i
    assert self.fields[i].numRecords>j
    encoding = self.fields[i].encodings[j]

    return encoding


  def getZeroedOutEncoding(self, n):
    """Returns the nth encoding with the predictedField zeroed out"""

    assert all(field.numRecords>n for field in self.fields)

    encoding = np.concatenate([field.encoder.encode(SENTINEL_VALUE_FOR_MISSING_DATA)\
        if field.isPredictedField else field.encodings[n] for field in self.fields])

    return encoding


  def getTotaln(self):
    """Returns the cumulative n for all the fields in the dataset"""

    n = sum([field.n for field in self.fields])
    return n


  def getTotalw(self):
    """Returns the cumulative w for all the fields in the dataset"""

    w = sum([field.w for field in self.fields])
    return w


  def getEncoding(self, n):
    """Returns the nth encoding"""

    assert (all(field.numEncodings>n for field in self.fields))
    encoding = np.concatenate([field.encodings[n] for field in self.fields])

    return encoding


  def getAllEncodings(self):
    """Returns encodings for all the records"""

    numEncodings=self.fields[0].numEncodings
    assert (all(field.numEncodings==numEncodings for field in self.fields))
    encodings = [self.getEncoding(index) for index in range(numEncodings)]

    return encodings


  def getAllFieldNames(self):
    """Returns all field names"""
    names = [field.name for field in self.fields]
    return names


  def getAllFlags(self):
    """Returns flags for all fields"""

    flags = [field.flag for field in self.fields]
    return flags


  def getAllDataTypes(self):
    """Returns data types for all fields"""

    dataTypes = [field.dataType for field in self.fields]
    return dataTypes


  def getFieldDescriptions(self):
    """Returns descriptions for all fields"""

    descriptions = [field.getDescription() for field in self.fields]

    return descriptions


  def saveRecords(self, path='myOutput'):
    """Export all the records into a csv file in numenta format.

    Example header format:
    fieldName1    fieldName2    fieldName3
    date          string        float
    T             S

    Parameters:
    --------------------------------------------------------------------
    path:      Relative path of the file to which the records are to be exported
    """
    numRecords = self.fields[0].numRecords
    assert (all(field.numRecords==numRecords for field in self.fields))

    import csv
    with open(path+'.csv', 'wb') as f:
      writer = csv.writer(f)
      writer.writerow(self.getAllFieldNames())
      writer.writerow(self.getAllDataTypes())
      writer.writerow(self.getAllFlags())
      writer.writerows(self.getAllRecords())
    if self.verbosity>0:
      print '******', numRecords,'records exported in numenta format to file:',\
                path,'******\n'


  def removeAllRecords(self):
    """Deletes all the values in the dataset"""

    for field in self.fields:
      field.encodings, field.values=[], []
      field.numRecords, field.numEncodings= (0, 0)



class _field():

  def __init__(self, name, encoderSpec):
    """Initialize a field with various parameters such as n, w, flag, dataType,
    encoderType, and tag predicted field."""

    self.name=name

    #Default values
    self.n, self.w = (100, 15)
    self.encoderType,self.dataType,self.dataClassName  = (None, None, None)
    self.flag=''
    self.isPredictedField=False

    if encoderSpec is not None:
      if 'n' in encoderSpec: self.n = encoderSpec.pop('n')
      if 'w' in encoderSpec: self.w = encoderSpec.pop('w')
      if 'flag' in encoderSpec: self.flag = encoderSpec.pop('flag')
      if 'isPredictedField' in encoderSpec: self.isPredictedField\
                          = encoderSpec.pop('isPredictedField')
      if 'dataClass' in encoderSpec: self.dataClass \
                          = encoderSpec.pop('dataClass')
      if 'dataClassName' in encoderSpec: self.dataClassName \
                          = encoderSpec.pop('dataClassName')
      if 'dataType' in encoderSpec: self.dataType = encoderSpec.pop('dataType')
      if 'encoderType' in encoderSpec: self.encoderType \
                          = encoderSpec.pop('encoderType')

    # ==========================================================================
    # Setting up the encoders
    if self.dataType is None and self.encoderType is None:
      raise RuntimeError('At least one of dataType and encoderType must be specified')

    assert(self.dataType is not None or self.encoderType is not None)

    if self.dataType is None or self.encoderType is None:
      self._setTypes(encoderSpec)

    self._initializeEncoders(encoderSpec)

    self.encodings=[]
    self.values=[]
    self.numRecords=0
    self.numEncodings=0


  def getDescription(self):

    description = dict(n=self.n, w=self.w, flag=self.flag, isPredictedField=\
      self.isPredictedField, dataClass=self.dataClassName, encoderType= \
      self.encoderType, numRecords=self.numRecords, numEncodings=self.numEncodings)

    return description


  def addValues(self, values):
    """Add values to the field"""

    for v in values:
      self.addValue(v)


  def addValue(self, value):
    """Add value to the field"""

    self.values.append(value)
    self.numRecords+=1


  def encodeValue(self, value, toBeAdded=True):
    """Value is encoded as a sdr using the encoding parameters of the Field"""

    encodedValue = np.array(self.encoder.encode(value), dtype=realDType)

    if toBeAdded:
      self.encodings.append(encodedValue)
      self.numEncodings+=1

    return encodedValue


  def _setTypes(self, encoderSpec):
    """Set up the dataTypes and initialize encoders"""

    if self.encoderType is None:
      if self.dataType in ['int','float']:
        self.encoderType='adaptiveScalar'
      elif self.dataType=='string':
        self.encoderType='category'
      elif self.dataType in ['date', 'datetime']:
        self.encoderType='date'

    if self.dataType is None:
      if self.encoderType in ['scalar','adaptiveScalar']:
        self.dataType='float'
      elif self.encoderType in ['category', 'enumeration']:
        self.dataType='string'
      elif self.encoderType in ['date', 'datetime']:
        self.dataType='datetime'


  def _initializeEncoders(self, encoderSpec):
    """ Initialize the encoders"""

    #Initializing scalar encoder
    if self.encoderType in ['adaptiveScalar', 'scalar']:
      if 'minval' in encoderSpec:
        self.minval = encoderSpec.pop('minval')
      else: self.minval=None
      if 'maxval' in encoderSpec:
        self.maxval = encoderSpec.pop('maxval')
      else: self.maxval = None
      self.encoder=adaptive_scalar.AdaptiveScalarEncoder(name='AdaptiveScalarEncoder', \
                                                         w=self.w, n=self.n, minval=self.minval, maxval=self.maxval, periodic=False, forced=True)

    #Initializing category encoder
    elif self.encoderType=='category':
      self.encoder=sdr_category.SDRCategoryEncoder(name='categoryEncoder', \
                                                   w=self.w, n=self.n)

    #Initializing date encoder
    elif self.encoderType in ['date', 'datetime']:
      self.encoder=date.DateEncoder(name='dateEncoder')
    else:
      raise RuntimeError('Error in constructing class object. Either encoder type'
          'or dataType must be specified')
