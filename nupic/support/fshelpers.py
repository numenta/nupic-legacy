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


# This script contains file-system helper functions


import os



def makeDirectoryFromAbsolutePath(absDirPath):
  """ Makes directory for the given directory path with default permissions.
  If the directory already exists, it is treated as success.

  absDirPath:   absolute path of the directory to create.

  Returns:      absDirPath arg

  Exceptions:         OSError if directory creation fails
  """

  assert os.path.isabs(absDirPath)

  try:
    os.makedirs(absDirPath)
  except OSError, e:
    if e.errno != os.errno.EEXIST:
      raise

  return absDirPath
