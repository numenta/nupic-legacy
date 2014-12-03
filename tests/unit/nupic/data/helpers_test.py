#! /usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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
import unittest2 as unittest

from nupic.data.datasethelpers import (_getDataDirs,
                                       findDataset,
                                       uncompressAndCopyDataset)



class HelpersTest(unittest.TestCase):


  def testGetDataDirs(self):
    dd =  _getDataDirs()
    dd = zip(*dd)[0]

    # Make sure the local data is there
    self.assertTrue(("data") in dd)

    ntaDataPath = os.environ.get('NTA_DATA_PATH', None)
    os.environ['NTA_DATA_PATH'] = 'XXX:YYY'

    dd =  _getDataDirs()
    dd = zip(*dd)[0]

    self.assertTrue('XXX' in dd and 'YYY' in dd)

    if ntaDataPath is None:
      del os.environ['NTA_DATA_PATH']
    else:
      os.environ['NTA_DATA_PATH'] = ntaDataPath


  def testFindDataset(self):
    # Test non-existing dataset (relative path)
    with self.assertRaises(Exception):
      findDataset('no_such_dataset.csv')

    # Test non-existing dataset (absolute path)
    with self.assertRaises(Exception):
      findDataset('/no_such_dataset.csv')

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
    self.assertEqual(path, fullPath)
    self.assertTrue(os.path.exists(path))

    # This should do nothing, since it is already compressed
    path = uncompressAndCopyDataset(path)
    self.assertEqual(path, fullPath)

    # Test existing dataset (absolute path)
    self.assertEqual(findDataset(fullPath), fullPath)

    # Test existing dataset (compressed path)

    # Create the compressed file
    import gzip
    f = gzip.GzipFile(fullPathCompressed, 'w')
    f.write("1,2,3\n")
    f.close()
    self.assertTrue(os.path.isfile(fullPathCompressed))

    # Remove the original file
    os.remove(fullPath)

    self.assertEqual(findDataset(datasetPath), fullPathCompressed)
    # This should put the uncompressed file in the same directory
    path = uncompressAndCopyDataset(fullPathCompressed)
    self.assertEqual(path, fullPath)
    self.assertTrue(os.path.isfile(path))

    os.remove(fullPath)
    os.remove(fullPathCompressed)



if __name__ == "__main__":
  unittest.main()
