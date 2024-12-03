# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""
This module contains file-system helper functions.
"""

import os



def makeDirectoryFromAbsolutePath(absDirPath):
  """ Makes directory for the given directory path with default permissions.
  If the directory already exists, it is treated as success.

  :param absDirPath: (string) absolute path of the directory to create.
  :raises: OSError if directory creation fails
  :returns: (string) absolute path provided
  """

  assert os.path.isabs(absDirPath)

  try:
    os.makedirs(absDirPath)
  except OSError, e:
    if e.errno != os.errno.EEXIST:
      raise

  return absDirPath
