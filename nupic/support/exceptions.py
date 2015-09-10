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

import sys
import traceback



class TimeoutError(Exception):
  """ The requested operation timed out """
  pass



class NupicJobFailException(Exception):
  """ This exception signals that the Nupic job (e.g., Hypersearch, Production,
  etc.) should be aborted due to the given error.
  """

  def __init__(self, errorCode, msg):
    """
    Parameters:
    ---------------------------------------------------------------------
    errorCode:      An error code from the support.errorcodes.ErrorCodes
                    enumeration
    msg:            Error message string
    """

    self.__errorCode = errorCode
    self.__msg = msg

    super(JobFatalException, self).__init__(errorCode, msg)

    return


  def getWorkerCompletionMessage(self):
    """ Generates a worker completion message that is suitable for the
    worker_completion_message field in jobs table

    Parameters:
    ---------------------------------------------------------------------
    retval:         The worker completion message appropriate for the
                    "worker_completion_message" field in jobs table
    """

    msg = "%s: %s\n%s" % (self.__errorCode, self.__msg, traceback.format_exc())

    return msg


  @classmethod
  def mapCurrentException(cls, e, errorCode, msg):
    """ Raises NupicJobFailException by mapping from another exception that
    is being handled in the caller's scope and preserves the current exception's
    traceback.

    Parameters:
    ---------------------------------------------------------------------
    e:              The source exception
    errorCode:      An error code from the support.errorcodes.ErrorCodes
                    enumeration
    msg:            Error message string
    """

    traceback = sys.exc_info()[2]
    assert traceback is not None

    newMsg = "%s: %r" % (msg, e)

    e = NupicJobFailException(errorCode=errorCode, msg=newMsg)

    raise e, None, traceback
