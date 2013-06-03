#! /usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
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

import fcntl
import os


class FileLockAcquireException(Exception):
    pass

class FileLockReleaseException(Exception):
    pass


class FileLock(object):
  """ This class implements a global file lock that can be used as a
  a mutex between cooperating processes.

  NOTE: the present implementation's behavior is undefined when multiple
        threads may try ackquire a lock on the same file.
  """

  def __init__(self, filePath):
    """
    Parameters:
    ------------------------------------------------------------------------
    filePath:   Path to a file to be used for locking; The file MUST already exist.
    """

    assert os.path.isabs(filePath), "not absolute path: %r" % filePath

    assert os.path.isfile(filePath), (
            "not a file or doesn't exist: %r" % filePath)

    self.__filePath = filePath

    self.__fp = open(self.__filePath, "r")

    self.__fd = self.__fp.fileno()

    return

  def __enter__(self):
    """ Context Manager protocol method. Allows a FileLock instance to be
    used in a "with" statement for automatic acquire/release

    Parameters:
    ------------------------------------------------------------------------
    retval:     self.
    """
    self.acquire()
    return self


  def __exit__(self, exc_type, exc_val, exc_tb):
    """ Context Manager protocol method. Allows a FileLock instance to be
    used in a "with" statement for automatic acquire/release
    """
    self.release()
    return False


  def acquire(self):
    """ Acquire global lock

    exception: FileLockAcquireException on failure
    """
    try:
      fcntl.flock(self.__fd, fcntl.LOCK_EX)
    except Exception, e:
      e = FileLockAcquireException(
        "FileLock acquire failed on %r" % (self.__filePath), e)
      raise e, None, sys.exc_info()[2]

    return


  def release(self):
    """ Release global lock
    """
    try:
      fcntl.flock(self.__fd, fcntl.LOCK_UN)
    except Exception, e:
      e = FileLockReleaseException(
        "FileLock release failed on %r" % (self.__filePath), e)
      raise e, None, sys.exc_info()[2]

    return