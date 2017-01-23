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

"""Tool for adding anomalies to data sets."""

import random
import sys

from nupic.data.file_record_stream import FileRecordStream

USAGE = """
Usage:
  python anomalyzer.py input output action extraArgs
Actions:
  add
    extraArgs: column start stop value
    Adds value to each element in range [start, stop].
  scale
    extraArgs: column start stop multiple
    Multiplies each element in range [start, stop] by multiple.
  copy
    extraArgs: start stop [insertLocation] [tsCol]
    Copies the values in range [start, stop] and inserts them at
    insertLocation, or following the copied section if no insertLocation
    is specified. Updates timestamps if tsCol is given.
  sample
    extraArgs: n [start] [stop] [tsCol]
    Samples rows from the specified range and writes them to the new file.
    If tsCol is specified, the timestamps of this column are updated.
  sample2
    Same as sample except the rows before and after the specified range are
    preserved.
"""



class Actions(object):
  """Enum class for actions that can be performed."""
  ADD = 'add'
  SCALE = 'scale'
  COPY = 'copy'
  SAMPLE = 'sample'
  SAMPLE2 = 'sample2'
  ACTIONS = (ADD, SCALE, COPY, SAMPLE, SAMPLE2)



def add(reader, writer, column, start, stop, value):
  """Adds a value over a range of rows.

  Args:
    reader: A FileRecordStream object with input data.
    writer: A FileRecordStream object to write output data to.
    column: The column of data to modify.
    start: The first row in the range to modify.
    end: The last row in the range to modify.
    value: The value to add.
  """
  for i, row in enumerate(reader):
    if i >= start and i <= stop:
      row[column] = type(value)(row[column]) + value
    writer.appendRecord(row)



def scale(reader, writer, column, start, stop, multiple):
  """Multiplies a value over a range of rows.

  Args:
    reader: A FileRecordStream object with input data.
    writer: A FileRecordStream  object to write output data to.
    column: The column of data to modify.
    start: The first row in the range to modify.
    end: The last row in the range to modify.
    multiple: The value to scale/multiply by.
  """
  for i, row in enumerate(reader):
    if i >= start and i <= stop:
      row[column] = type(multiple)(row[column]) * multiple
    writer.appendRecord(row)



def copy(reader, writer, start, stop, insertLocation=None, tsCol=None):
  """Copies a range of values to a new location in the data set.

  Args:
    reader: A FileRecordStream object with input data.
    writer: A FileRecordStream object to write output data to.
    start: The first row in the range to copy.
    stop: The last row in the range to copy.
    insertLocation: The location to insert the copied range. If not specified,
        the range is inserted immediately following itself.
  """
  assert stop >= start
  startRows = []
  copyRows = []
  ts = None
  inc = None
  if tsCol is None:
    tsCol = reader.getTimestampFieldIdx()
  for i, row in enumerate(reader):
    # Get the first timestamp and the increment.
    if ts is None:
      ts = row[tsCol]
    elif inc is None:
      inc = row[tsCol] - ts
    # Keep a list of all rows and a list of rows to copy.
    if i >= start and i <= stop:
      copyRows.append(row)
    startRows.append(row)
  # Insert the copied rows.
  if insertLocation is None:
    insertLocation = stop + 1
  startRows[insertLocation:insertLocation] = copyRows
  # Update the timestamps.
  for row in startRows:
    row[tsCol] = ts
    writer.appendRecord(row)
    ts += inc



def sample(reader, writer, n, start=None, stop=None, tsCol=None,
           writeSampleOnly=True):
  """Samples n rows.

  Args:
    reader: A FileRecordStream object with input data.
    writer: A FileRecordStream object to write output data to.
    n: The number of elements to sample.
    start: The first row in the range to sample from.
    stop: The last row in the range to sample from.
    tsCol: If specified, the timestamp column to update.
    writeSampleOnly: If False, the rows before start are written before the
        sample and the rows after stop are written after the sample.
  """
  rows = list(reader)
  if tsCol is not None:
    ts = rows[0][tsCol]
    inc = rows[1][tsCol] - ts
  if start is None:
    start = 0
  if stop is None:
    stop = len(rows) - 1
  initialN = stop - start + 1
  # Select random rows in the sample range to delete until the desired number
  # of rows are left.
  numDeletes =  initialN - n
  for i in xrange(numDeletes):
    delIndex = random.randint(start, stop - i)
    del rows[delIndex]
  # Remove outside rows if specified.
  if writeSampleOnly:
    rows = rows[start:start + n]
  # Rewrite columns if tsCol is given.
  if tsCol is not None:
    ts = rows[0][tsCol]
  # Write resulting rows.
  for row in rows:
    if tsCol is not None:
      row[tsCol] = ts
      ts += inc
    writer.appendRecord(row)



def main(args):
  inputPath, outputPath, action = args[:3]
  with FileRecordStream(inputPath) as reader:
    with FileRecordStream(outputPath, write=True,
                          fields=reader.fields) as writer:
      assert action in Actions.ACTIONS, USAGE
      if action == Actions.ADD:
        assert len(args) == 7, USAGE
        start = int(args[4])
        stop = int(args[5])
        column = int(args[3])
        valueType = eval(reader.fields[column][1])
        value = valueType(args[6])
        add(reader, writer, column, start, stop, value)
      elif action == Actions.SCALE:
        assert len(args) == 7, USAGE
        start = int(args[4])
        stop = int(args[5])
        column = int(args[3])
        valueType = eval(reader.fields[column][1])
        multiple = valueType(args[6])
        scale(reader, writer, column, start, stop, multiple)
      elif action == Actions.COPY:
        assert 5 <= len(args) <= 8, USAGE
        start = int(args[3])
        stop = int(args[4])
        if len(args) > 5:
          insertLocation = int(args[5])
        else:
          insertLocation = None
        if len(args) == 7:
          tsCol = int(args[6])
        else:
          tsCol = None
        copy(reader, writer, start, stop, insertLocation, tsCol)
      elif action == Actions.SAMPLE or action == Actions.SAMPLE2:
        assert 4 <= len(args) <= 7, USAGE
        n = int(args[3])
        start = None
        if len(args) > 4:
          start = int(args[4])
        stop = None
        if len(args) > 5:
          stop = int(args[5])
        tsCol = None
        if len(args) > 6:
          tsCol = int(args[6])
        writeSampleOnly = action == Actions.SAMPLE
        sample(reader, writer, n, start, stop, tsCol, writeSampleOnly)



if __name__ == "__main__":
  if len(sys.argv) <= 1:
    print USAGE
    sys.exit(1)
  main(sys.argv[1:])
