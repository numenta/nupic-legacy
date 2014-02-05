# ----------------------------------------------------------------------
#  Copyright (C) 2011 Numenta Inc. All rights reserved.
#
#  The information and source code contained herein is the
#  exclusive property of Numenta Inc. No part of this software
#  may be used, reproduced, stored or distributed in any form,
#  without explicit written authorization from Numenta Inc.
# ----------------------------------------------------------------------
import os
import sys
import datetime
import shutil
import tempfile
from nupic.support import title
from nupic.data.datasethelpers import (_getDataDirs,
                                       findDataset,
                                       uncompressAndCopyDataset)

def testGetDataDirs():
  """ """
  title()
  dd =  _getDataDirs()
  dd = zip(*dd)[0]

  # Make sure the local data is there
  assert ('data') in dd
  # Make sure there are no duplicates
  assert len(set(dd)) == len(dd)

  nta_data_path = os.environ.get('NTA_DATA_PATH', None)
  os.environ['NTA_DATA_PATH'] = 'XXX:YYY'

  dd =  _getDataDirs()
  dd = zip(*dd)[0]

  assert 'XXX' in dd and 'YYY' in dd

  if nta_data_path is None:
    del os.environ['NTA_DATA_PATH']
  else:
    os.environ['NTA_DATA_PATH'] = nta_data_path

def testFindDataset():
  title()
  # Test non-existing dataset (relative path)
  try:
    findDataset('no_such_dataset.csv')
    assert False
  except:
    pass
  # Test non-existing dataset (absolute path)
  try:
    findDataset('/no_such_dataset.csv')
    assert False
  except:
    pass
  # Test existing dataset (relative path)
  if not os.path.isdir('data'):
    os.makedirs('data')
  datasetPath = 'test_find_dataset.csv'
  filename = 'data/test_find_dataset.csv'
  # This is the uncompressed name.
  fullPath = os.path.abspath(filename)
  if os.path.exists(fullPath):
    os.remove(fullPath)
  fullPathCompressed = fullPath + ".gz"
  if os.path.exists(fullPathCompressed):
    os.remove(fullPathCompressed)

  # Create the "dataset"
  open(filename, 'w').write('123')
  path = findDataset(datasetPath)
  assert path == fullPath
  assert os.path.exists(path)

  # This should do nothing, since it is already compressed
  path = uncompressAndCopyDataset(path)
  assert path == fullPath

  # Test existing dataset (absolute path)
  assert findDataset(fullPath) == fullPath

  # Test existing dataset (compressed path)

  # Create the compressed file
  import gzip
  f = gzip.GzipFile(fullPathCompressed, 'w')
  f.write('1,2,3\n')
  f.close()
  assert os.path.isfile(fullPathCompressed)

  # Remove the original file
  os.remove(fullPath)

  assert findDataset(datasetPath) == fullPathCompressed
  # This should put the uncompressed file in the same directory
  path = uncompressAndCopyDataset(fullPathCompressed)
  assert path == fullPath
  assert os.path.isfile(path)

  os.remove(fullPath)
  os.remove(fullPathCompressed)

def test():
  testFindDataset()
  testGetDataDirs()

if __name__=='__main__':
  test()