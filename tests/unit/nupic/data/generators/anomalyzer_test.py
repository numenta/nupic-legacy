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

"""Tests for the anomalyzer."""

import csv
from mock import MagicMock, patch
from StringIO import StringIO

import unittest2 as unittest

from nupic.data.file_record_stream import FileRecordStream
from nupic.data.generators import anomalyzer


class AnomalyzerTest(unittest.TestCase):
  """Tests for the anomalyzer."""


  def setUp(self):
    self.sampleInput = ("Timestamp,Value\n"
                        "datetime,int\n"
                        "T,\n"
                        "2011-09-04 2:00:00.0,1\n"
                        "2011-09-04 2:05:00.0,2\n"
                        "2011-09-04 2:10:00.0,3\n"
                        "2011-09-04 2:15:00.0,4\n"
                        "2011-09-04 2:20:00.0,5\n"
                        "2011-09-04 2:25:00.0,6")


  def testAddBeginning(self):
    expectedOutput = ("Timestamp,Value\n"
                      "datetime,int\n"
                      "T,\n"
                      "2011-09-04 02:00:00.000000,9\n"
                      "2011-09-04 02:05:00.000000,10\n"
                      "2011-09-04 02:10:00.000000,3\n"
                      "2011-09-04 02:15:00.000000,4\n"
                      "2011-09-04 02:20:00.000000,5\n"
                      "2011-09-04 02:25:00.000000,6\n")
    mockInput = MagicMock(return_value=StringIO(self.sampleInput))
    output = StringIO()
    mockOutput = MagicMock(return_value=output)
    with patch("__builtin__.open", mockInput):
      inputFile = FileRecordStream("input_path")
      with patch("__builtin__.open", mockOutput):
        outputFile = FileRecordStream("output_path",
                                      fields=inputFile.getFields(),
                                      write=True)
        anomalyzer.add(inputFile, outputFile, 1, 0, 1, 8)
    result = output.getvalue()
    result = result.replace("\r\n", "\n")
    result = result.replace("\r", "\n")
    self.assertSequenceEqual(expectedOutput, result)


  def testAddMiddle(self):
    expectedOutput = ("Timestamp,Value\n"
                      "datetime,int\n"
                      "T,\n"
                      "2011-09-04 02:00:00.000000,1\n"
                      "2011-09-04 02:05:00.000000,10\n"
                      "2011-09-04 02:10:00.000000,11\n"
                      "2011-09-04 02:15:00.000000,4\n"
                      "2011-09-04 02:20:00.000000,5\n"
                      "2011-09-04 02:25:00.000000,6\n")
    mockInput = MagicMock(return_value=StringIO(self.sampleInput))
    output = StringIO()
    mockOutput = MagicMock(return_value=output)
    with patch("__builtin__.open", mockInput):
      inputFile = FileRecordStream("input_path")
      with patch("__builtin__.open", mockOutput):
        outputFile = FileRecordStream("output_path",
                                      fields=inputFile.getFields(),
                                      write=True)
        anomalyzer.add(inputFile, outputFile, 1, 1, 2, 8)
    result = output.getvalue()
    result = result.replace("\r\n", "\n")
    result = result.replace("\r", "\n")
    self.assertSequenceEqual(expectedOutput, result)


  def testAddEnd(self):
    expectedOutput = ("Timestamp,Value\n"
                      "datetime,int\n"
                      "T,\n"
                      "2011-09-04 02:00:00.000000,1\n"
                      "2011-09-04 02:05:00.000000,2\n"
                      "2011-09-04 02:10:00.000000,3\n"
                      "2011-09-04 02:15:00.000000,4\n"
                      "2011-09-04 02:20:00.000000,13\n"
                      "2011-09-04 02:25:00.000000,14\n")
    mockInput = MagicMock(return_value=StringIO(self.sampleInput))
    output = StringIO()
    mockOutput = MagicMock(return_value=output)
    with patch("__builtin__.open", mockInput):
      inputFile = FileRecordStream("input_path")
      with patch("__builtin__.open", mockOutput):
        outputFile = FileRecordStream("output_path",
                                      fields=inputFile.getFields(),
                                      write=True)
        anomalyzer.add(inputFile, outputFile, 1, 4, 5, 8)
    result = output.getvalue()
    result = result.replace("\r\n", "\n")
    result = result.replace("\r", "\n")
    self.assertSequenceEqual(expectedOutput, result)


  def testAddSingle(self):
    expectedOutput = ("Timestamp,Value\n"
                      "datetime,int\n"
                      "T,\n"
                      "2011-09-04 02:00:00.000000,1\n"
                      "2011-09-04 02:05:00.000000,10\n"
                      "2011-09-04 02:10:00.000000,3\n"
                      "2011-09-04 02:15:00.000000,4\n"
                      "2011-09-04 02:20:00.000000,5\n"
                      "2011-09-04 02:25:00.000000,6\n")
    mockInput = MagicMock(return_value=StringIO(self.sampleInput))
    output = StringIO()
    mockOutput = MagicMock(return_value=output)
    with patch("__builtin__.open", mockInput):
      inputFile = FileRecordStream("input_path")
      with patch("__builtin__.open", mockOutput):
        outputFile = FileRecordStream("output_path",
                                      fields=inputFile.getFields(),
                                      write=True)
        anomalyzer.add(inputFile, outputFile, 1, 1, 1, 8)
    result = output.getvalue()
    result = result.replace("\r\n", "\n")
    result = result.replace("\r", "\n")
    self.assertSequenceEqual(expectedOutput, result)


  def testAddAll(self):
    expectedOutput = ("Timestamp,Value\n"
                      "datetime,int\n"
                      "T,\n"
                      "2011-09-04 02:00:00.000000,9\n"
                      "2011-09-04 02:05:00.000000,10\n"
                      "2011-09-04 02:10:00.000000,11\n"
                      "2011-09-04 02:15:00.000000,12\n"
                      "2011-09-04 02:20:00.000000,13\n"
                      "2011-09-04 02:25:00.000000,14\n")
    mockInput = MagicMock(return_value=StringIO(self.sampleInput))
    output = StringIO()
    mockOutput = MagicMock(return_value=output)
    with patch("__builtin__.open", mockInput):
      inputFile = FileRecordStream("input_path")
      with patch("__builtin__.open", mockOutput):
        outputFile = FileRecordStream("output_path",
                                      fields=inputFile.getFields(),
                                      write=True)
        anomalyzer.add(inputFile, outputFile, 1, 0, 5, 8)
    result = output.getvalue()
    result = result.replace("\r\n", "\n")
    result = result.replace("\r", "\n")
    self.assertSequenceEqual(expectedOutput, result)


  def testScale(self):
    expectedOutput = ("Timestamp,Value\n"
                      "datetime,int\n"
                      "T,\n"
                      "2011-09-04 02:00:00.000000,1\n"
                      "2011-09-04 02:05:00.000000,16\n"
                      "2011-09-04 02:10:00.000000,24\n"
                      "2011-09-04 02:15:00.000000,4\n"
                      "2011-09-04 02:20:00.000000,5\n"
                      "2011-09-04 02:25:00.000000,6\n")
    mockInput = MagicMock(return_value=StringIO(self.sampleInput))
    output = StringIO()
    mockOutput = MagicMock(return_value=output)
    with patch("__builtin__.open", mockInput):
      inputFile = FileRecordStream("input_path")
      with patch("__builtin__.open", mockOutput):
        outputFile = FileRecordStream("output_path",
                                      fields=inputFile.getFields(),
                                      write=True)
        anomalyzer.scale(inputFile, outputFile, 1, 1, 2, 8)
    result = output.getvalue()
    result = result.replace("\r\n", "\n")
    result = result.replace("\r", "\n")
    self.assertSequenceEqual(expectedOutput, result)


  def testCopyAllImplicit(self):
    expectedOutput = ("Timestamp,Value\n"
                      "datetime,int\n"
                      "T,\n"
                      "2011-09-04 02:00:00.000000,1\n"
                      "2011-09-04 02:05:00.000000,2\n"
                      "2011-09-04 02:10:00.000000,3\n"
                      "2011-09-04 02:15:00.000000,4\n"
                      "2011-09-04 02:20:00.000000,5\n"
                      "2011-09-04 02:25:00.000000,6\n"
                      "2011-09-04 02:30:00.000000,1\n"
                      "2011-09-04 02:35:00.000000,2\n"
                      "2011-09-04 02:40:00.000000,3\n"
                      "2011-09-04 02:45:00.000000,4\n"
                      "2011-09-04 02:50:00.000000,5\n"
                      "2011-09-04 02:55:00.000000,6\n")
    mockInput = MagicMock(return_value=StringIO(self.sampleInput))
    output = StringIO()
    mockOutput = MagicMock(return_value=output)
    with patch("__builtin__.open", mockInput):
      inputFile = FileRecordStream("input_path")
      with patch("__builtin__.open", mockOutput):
        outputFile = FileRecordStream("output_path",
                                      fields=inputFile.getFields(),
                                      write=True)
        anomalyzer.copy(inputFile, outputFile, 0, 5)
    result = output.getvalue()
    result = result.replace("\r\n", "\n")
    result = result.replace("\r", "\n")
    self.assertSequenceEqual(expectedOutput, result)


  def testCopyAllExplicit(self):
    expectedOutput = ("Timestamp,Value\n"
                      "datetime,int\n"
                      "T,\n"
                      "2011-09-04 02:00:00.000000,1\n"
                      "2011-09-04 02:05:00.000000,2\n"
                      "2011-09-04 02:10:00.000000,3\n"
                      "2011-09-04 02:15:00.000000,4\n"
                      "2011-09-04 02:20:00.000000,5\n"
                      "2011-09-04 02:25:00.000000,6\n"
                      "2011-09-04 02:30:00.000000,1\n"
                      "2011-09-04 02:35:00.000000,2\n"
                      "2011-09-04 02:40:00.000000,3\n"
                      "2011-09-04 02:45:00.000000,4\n"
                      "2011-09-04 02:50:00.000000,5\n"
                      "2011-09-04 02:55:00.000000,6\n")
    mockInput = MagicMock(return_value=StringIO(self.sampleInput))
    output = StringIO()
    mockOutput = MagicMock(return_value=output)
    with patch("__builtin__.open", mockInput):
      inputFile = FileRecordStream("input_path")
      with patch("__builtin__.open", mockOutput):
        outputFile = FileRecordStream("output_path",
                                      fields=inputFile.getFields(),
                                      write=True)
        anomalyzer.copy(inputFile, outputFile, 0, 5, 6)
    result = output.getvalue()
    result = result.replace("\r\n", "\n")
    result = result.replace("\r", "\n")
    self.assertSequenceEqual(expectedOutput, result)


  def testCopyBeginning(self):
    expectedOutput = ("Timestamp,Value\n"
                      "datetime,int\n"
                      "T,\n"
                      "2011-09-04 02:00:00.000000,1\n"
                      "2011-09-04 02:05:00.000000,2\n"
                      "2011-09-04 02:10:00.000000,1\n"
                      "2011-09-04 02:15:00.000000,2\n"
                      "2011-09-04 02:20:00.000000,3\n"
                      "2011-09-04 02:25:00.000000,4\n"
                      "2011-09-04 02:30:00.000000,5\n"
                      "2011-09-04 02:35:00.000000,6\n")
    mockInput = MagicMock(return_value=StringIO(self.sampleInput))
    output = StringIO()
    mockOutput = MagicMock(return_value=output)
    with patch("__builtin__.open", mockInput):
      inputFile = FileRecordStream("input_path")
      with patch("__builtin__.open", mockOutput):
        outputFile = FileRecordStream("output_path",
                                      fields=inputFile.getFields(),
                                      write=True)
        anomalyzer.copy(inputFile, outputFile, 0, 1, 0)
    result = output.getvalue()
    result = result.replace("\r\n", "\n")
    result = result.replace("\r", "\n")
    self.assertSequenceEqual(expectedOutput, result)


  def testCopyOneRow(self):
    expectedOutput = ("Timestamp,Value\n"
                      "datetime,int\n"
                      "T,\n"
                      "2011-09-04 02:00:00.000000,1\n"
                      "2011-09-04 02:05:00.000000,2\n"
                      "2011-09-04 02:10:00.000000,2\n"
                      "2011-09-04 02:15:00.000000,3\n"
                      "2011-09-04 02:20:00.000000,4\n"
                      "2011-09-04 02:25:00.000000,5\n"
                      "2011-09-04 02:30:00.000000,6\n")
    mockInput = MagicMock(return_value=StringIO(self.sampleInput))
    output = StringIO()
    mockOutput = MagicMock(return_value=output)
    with patch("__builtin__.open", mockInput):
      inputFile = FileRecordStream("input_path")
      with patch("__builtin__.open", mockOutput):
        outputFile = FileRecordStream("output_path",
                                      fields=inputFile.getFields(),
                                      write=True)
        anomalyzer.copy(inputFile, outputFile, 1, 1, 1)
    result = output.getvalue()
    result = result.replace("\r\n", "\n")
    result = result.replace("\r", "\n")
    self.assertSequenceEqual(expectedOutput, result)


  def testSample(self):
    mockInput = MagicMock(return_value=StringIO(self.sampleInput))
    output = StringIO()
    mockOutput = MagicMock(return_value=output)
    with patch("__builtin__.open", mockInput):
      inputFile = FileRecordStream("input_path")
      with patch("__builtin__.open", mockOutput):
        outputFile = FileRecordStream("output_path",
                                      fields=inputFile.getFields(),
                                      write=True)
        anomalyzer.sample(inputFile, outputFile, 1)
    result = StringIO(output.getvalue())
    result.next()
    result.next()
    result.next()
    reader = csv.reader(result)
    _, value = reader.next()
    self.assertIn(int(value), (1, 2, 3, 4, 5, 6))
    self.assertRaises(StopIteration, result.next)



if __name__ == "__main__":
  unittest.main()
