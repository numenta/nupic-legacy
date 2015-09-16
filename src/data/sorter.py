#! /usr/bin/env python
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

import os
import sys
from operator import itemgetter

import psutil

from nupic.support import title
from nupic.data.file_record_stream import FileRecordStream


"""The sorter sorts PF datasets in the standard File format

- It supports sorting by multiple fields
- It allows sorting of datasets that don't fit in memory
- It allows selecting a subset of the original fields

The sorter uses merge sort ()

"""
def sort(filename, key, outputFile, fields=None, watermark=1024 * 1024 * 100):
  """Sort a potentially big file

  filename - the input file (standard File format)
  key - a list of field names to sort by
  outputFile - the name of the output file
  fields - a list of fields that should be included (all fields if None)
  watermark - when available memory goes bellow the watermark create a new chunk

  sort() works by reading as records from the file into memory
  and calling _sortChunk() on each chunk. In the process it gets
  rid of unneeded fields if any. Once all the chunks have been sorted and
  written to chunk files it calls _merge() to merge all the chunks into a
  single sorted file.

  Note, that sort() gets a key that contains field names, which it converts
  into field indices for _sortChunk() becuase _sortChunk() doesn't need to know
  the field name.

  sort() figures out by itself how many chunk files to use by reading records
  from the file until the low watermark value of availabel memory is hit and
  then it sorts the current records, generates a chunk file, clears the sorted
  records and starts on a new chunk.

  The key field names are turned into indices
  """
  if fields is not None:
    assert set(key).issubset(set([f[0] for f in fields]))

  with FileRecordStream(filename) as f:


    # Find the indices of the requested fields
    if fields:
      fieldNames = [ff[0] for ff in fields]
      indices = [f.getFieldNames().index(name) for name in fieldNames]
      assert len(indices) == len(fields)
    else:
      fileds = f.getFields()
      fieldNames = f.getFieldNames()
      indices = None

    # turn key fields to key indices
    key = [fieldNames.index(name) for name in key]

    chunk = 0
    records = []
    for i, r in enumerate(f):
      # Select requested fields only
      if indices:
        temp = []
        for i in indices:
          temp.append(r[i])
        r = temp
      # Store processed record
      records.append(r)

      # Check memory
      available_memory = psutil.avail_phymem()

      # If bellow the watermark create a new chunk, reset and keep going
      if available_memory < watermark:
        _sortChunk(records, key, chunk, fields)
        records = []
        chunk += 1

    # Sort and write the remainder
    if len(records) > 0:
      _sortChunk(records, key, chunk, fields)
      chunk += 1

    # Marge all the files
    _mergeFiles(key, chunk, outputFile, fields)

def _sortChunk(records, key, chunkIndex, fields):
  """Sort in memory chunk of records

  records - a list of records read from the original dataset
  key - a list of indices to sort the records by
  chunkIndex - the index of the current chunk

  The records contain only the fields requested by the user.

  _sortChunk() will write the sorted records to a standard File
  named "chunk_<chunk index>.csv" (chunk_0.csv, chunk_1.csv,...).
  """
  title(additional='(key=%s, chunkIndex=%d)' % (str(key), chunkIndex))

  assert len(records) > 0

  # Sort the current records
  records.sort(key=itemgetter(*key))

  # Write to a chunk file
  if chunkIndex is not None:
    filename = 'chunk_%d.csv' % chunkIndex
    with FileRecordStream(filename, write=True, fields=fields) as o:
      for r in records:
        o.appendRecord(r)

    assert os.path.getsize(filename) > 0

  return records

def _mergeFiles(key, chunkCount, outputFile, fields):
  """Merge sorted chunk files into a sorted output file

  chunkCount - the number of available chunk files
  outputFile the name of the sorted output file

  _mergeFiles()

  """
  title()

  # Open all chun files
  files = [FileRecordStream('chunk_%d.csv' % i) for i in range(chunkCount)]

  # Open output file
  with FileRecordStream(outputFile, write=True, fields=fields) as o:
    # Open all chunk files
    files = [FileRecordStream('chunk_%d.csv' % i) for i in range(chunkCount)]
    records = [f.getNextRecord() for f in files]

    # This loop will run until all files are exhausted
    while not all(r is None for r in records):
      # Cleanup None values (files that were exhausted)
      indices = [i for i,r in enumerate(records) if r is not None]
      records = [records[i] for i in indices]
      files = [files[i] for i in indices]

      # Find the current record
      r = min(records, key=itemgetter(*key))
      # Write it to the file
      o.appendRecord(r)

      # Find the index of file that produced the current record
      index = records.index(r)
      # Read a new record from the file
      records[index] = files[index].getNextRecord()

  # Cleanup chunk files
  for i, f in enumerate(files):
    f.close()
    os.remove('chunk_%d.csv' % i)

def writeTestFile(testFile, fields, big):
  if big:
    print 'Creating big test file (763MB)...'
    payload = 'x' * 10 ** 8
  else:
    print 'Creating a small big test file...'
    payload = 'x' * 3
  with FileRecordStream(testFile, write=True, fields=fields) as o:
    print '.'; o.appendRecord([1,3,6, payload])
    print '.'; o.appendRecord([2,3,6, payload])
    print '.'; o.appendRecord([1,4,6, payload])
    print '.'; o.appendRecord([2,4,6, payload])
    print '.'; o.appendRecord([1,3,5, payload])
    print '.'; o.appendRecord([2,3,5, payload])
    print '.'; o.appendRecord([1,4,5, payload])
    print '.'; o.appendRecord([2,4,5, payload])

def test(long):
  import shutil
  from tempfile import gettempdir

  print 'Running sorter self-test...'

  # Switch to a temp dir in order to create files freely
  workDir = os.path.join(gettempdir(), 'sorter_test')
  if os.path.exists(workDir):
    shutil.rmtree(workDir)
  os.makedirs(workDir)
  os.chdir(workDir)
  print 'cwd:', os.getcwd()

  # The fields definition used by all tests
  fields = [
   ('f1', 'int', ''),
   ('f2', 'int', ''),
   ('f3', 'int', ''),
   ('payload', 'string', '')
  ]

  # Create a test file
  testFile = '1.csv'
  if not os.path.isfile(testFile):
    writeTestFile(testFile, fields, big=long)

  # Set watermark here to 300MB bellow current available memory. That ensures
  # multiple chunk files in the big testcase

  mem = psutil.avail_phymem()
  watermark = mem - 300 * 1024 * 1024

  print 'Test sorting by f1 and f2, watermak:', watermark
  results = []
  sort(testFile,
       key=['f1', 'f2'],
       fields=fields,
       outputFile='f1_f2.csv',
       watermark=watermark)
  with FileRecordStream('f1_f2.csv') as f:
    for r in f:
      results.append(r[:3])

  assert results == [
    [1, 3, 6],
    [1, 3, 5],
    [1, 4, 6],
    [1, 4, 5],
    [2, 3, 6],
    [2, 3, 5],
    [2, 4, 6],
    [2, 4, 5],
  ]

  mem = psutil.avail_phymem()
  watermark = mem - 300 * 1024 * 1024
  print 'Test sorting by f2 and f1, watermark:', watermark
  results = []
  sort(testFile,
       key=['f2', 'f1'],
       fields=fields,
       outputFile='f2_f1.csv',
       watermark=watermark)
  with FileRecordStream('f2_f1.csv') as f:
    for r in f:
      results.append(r[:3])
  assert results == [
    [1, 3, 6],
    [1, 3, 5],
    [2, 3, 6],
    [2, 3, 5],
    [1, 4, 6],
    [1, 4, 5],
    [2, 4, 6],
    [2, 4, 5],
  ]

  mem = psutil.avail_phymem()
  watermark = mem - 300 * 1024 * 1024
  print 'Test sorting by f3 and f2, watermark:', watermark
  results = []
  sort(testFile,
       key=['f3', 'f2'],
       fields=fields,
       outputFile='f3_f2.csv',
       watermark=watermark)
  with FileRecordStream('f3_f2.csv') as f:
    for r in f:
      results.append(r[:3])

  assert results == [
    [1, 3, 5],
    [2, 3, 5],
    [1, 4, 5],
    [2, 4, 5],
    [1, 3, 6],
    [2, 3, 6],
    [1, 4, 6],
    [2, 4, 6],
  ]

  # Cleanup the work dir
  os.chdir('..')
  shutil.rmtree(workDir)

  print 'done'

if __name__=='__main__':
  print 'Starting tests...'
  test('--long' in sys.argv)
  print 'All tests pass'
