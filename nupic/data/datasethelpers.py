#! /usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

import os
import sys
import shutil
import gzip


#########################################################
debug = "NTA_DATA_DEBUG" in os.environ




#########################################################
def findDataset(datasetPath):
  """Returns the absolute path to a dataset (if not found, rasises Exception)
  The search rules for the dataset are:
    1. NTA_DATA_PATH  (":" separated value similar to PATH)
    2. ./data
    3. ./
    4. NTA
    5. ~/nupic/current/examples/prediction/data (unix)

  If the dataset is compressed (ends in .gz) returns the name of the compressed
  file.
  """

  if os.path.isabs(datasetPath) and os.path.isfile(datasetPath):
    if debug:
      print "Data found at absolute path '%s'" % datasetPath
    return datasetPath

  dataDirs = _getDataDirs()
  for d, location in dataDirs:
    fullPath = os.path.abspath(os.path.join(d, datasetPath))
    if os.path.isfile(fullPath):
      if debug:
        print "Data '%s' found at '%s' %s" % (datasetPath, fullPath, location)
      return fullPath

  # Not found. Look for a compressed dataset but don't uncompress is
  for d, location in dataDirs:
    fullPath = os.path.abspath(os.path.join(d, datasetPath))
    gzPath = fullPath + '.gz'
    if os.path.isfile(gzPath):
      return gzPath

  # Not found
  if debug:
    print "Data '%s' not found. " % datasetPath,
    print "dataDirs: %s" % dataDirs
    if "NTA_DATA_PATH" in os.environ:
      print "NTA_DATA_PATH: %s" % os.environ["NTA_DATA_PATH"]
    else:
      print "NTA_DATA_PATH is not set."

  raise Exception('Unable to locate: %s using NTA_DATA_PATH of %s' % \
                  (datasetPath, os.environ.get('NTA_DATA_PATH', '')))



def prependDatasetSearchPath(datasetDir):
  """ Prepend a dataset search path to the locations that findDataset() will
  search.  This is useful for test code that needs to
  copy the desired datasets to a temporary directory in order to avoid
  leaving generated results (e.g. from aggregation) in the source tree.
  """
  oldNtaDataPaths =  os.environ.get('NTA_DATA_PATH')
  if oldNtaDataPaths is None:
    newNtaDataPaths = datasetDir
  else:
    if oldNtaDataPaths.startswith(datasetDir):
      return

    newNtaDataPaths = datasetDir + ":" + oldNtaDataPaths

  os.environ['NTA_DATA_PATH'] = newNtaDataPaths

  return


def _getDataDirs():
  """Return all possible data directories in order

  1. NTA_DATA_PATH  (":" separated value similar to PATH)
  2. ./data
  3. ./
  4. NTA
  5. ~/nupic/current/examples/prediction/data (unix)

  """
  dataDirs = []
  if "NTA_DATA_PATH" in os.environ:
    dirs = os.environ["NTA_DATA_PATH"].split(":")
    for d in dirs:
      dataDirs.append((d, 'via NTA_DATA_PATH'))

  #  Local data dir
  dataDirs.append(('data', "in local directory 'data'"))
  dataDirs.append((".", "in current working directory"))

  if "NUPIC" in os.environ:
    d = os.path.join(os.environ['NUPIC'], 'examples/prediction/data')
    if os.path.isdir(d):
      if d not in zip(*dataDirs)[0]:
        dataDirs.append((d, 'in $NUPIC/examples/prediction/data'))

  if sys.platform != 'win32' and 'HOME' in os.environ:
    d = os.path.join(os.environ['HOME'], 'nupic/current/examples/prediction/data')
    if os.path.isdir(d):
      if d not in zip(*dataDirs)[0]:
        dataDirs.append((d, 'in $NUPIC/examples/prediction/data'))

  return dataDirs



#########################################################
def uncompressAndCopyDataset(path, destDir=None, overwrite=True):
  """Uncompress a data file. If destDir is specified, uncompressed it
  into this directory. Otherwise uncompress it into the original directory.

  If the file is not compressed (does not end in .gz) copy it to the
  destination directory if needed.

  If overwrite is True, we overwrite any existing file. Otherwise,
  we just return without copying

  The uncompress and copy operations are combined to minimize
  the work, since we can uncompress directly into the destination
  directory.

  """
  if not os.path.isfile(path):
    raise RuntimeError("Dataset '%s' not found" % dataset)

  if destDir is not None and not os.path.isdir(destDir):
        raise RuntimeError("Destination directory '%s' not found" % destDir)

  if not path.endswith(".gz"):
    # File is not compressed. Copy it if requested
    currentDir = os.path.dirname(path)
    if destDir is None or currentDir == destDir:
      uncompressedPath = path
    else:
      uncompressedPath = os.path.join(destDir, os.path.basename(path))
      if not os.path.exists(uncompressedPath) or overwrite:
        shutil.copy2(path, uncompressedPath)

  else:
    # File is compressed. Uncompress it.
    uncompressedPath = path[:-3]
    if destDir is not None:
      basename = os.path.basename(uncompressedPath)
      uncompressedPath = os.path.join(destDir, basename)
    if not os.path.exists(uncompressedPath) or overwrite:
      f = gzip.GzipFile(path)
      o = open(uncompressedPath, 'w')
      for line in f.readlines():
        o.write(line)
      o.close()
    assert os.path.isfile(uncompressedPath)
  return uncompressedPath
