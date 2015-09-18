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

# Helper utilities for python scripts that use pymysql

import inspect
import logging
from socket import error as socket_error

import pymysql
from pymysql.constants import ER
from nupic.support.decorators import retry as make_retry_decorator



# Client mysql error codes of interest; pymysql didn't have constants for these
# at the time of this writing.
# (per https://dev.mysql.com/doc/refman/5.5/en/error-messages-client.html)
CR_CONNECTION_ERROR = 2002
""" Can't connect to local MySQL server through socket '%s' (%d) """

CR_CONN_HOST_ERROR = 2003
""" Can't connect to MySQL server on '%s' (%d) """

CR_UNKNOWN_HOST = 2005
""" Unknown MySQL server host '%s' (%d) """

CR_SERVER_GONE_ERROR = 2006
""" MySQL server has gone away """

CR_TCP_CONNECTION = 2011
"""  %s via TCP/IP """

CR_SERVER_HANDSHAKE_ERR = 2012
""" Error in server handshake """

CR_SERVER_LOST = 2013
""" Lost connection to MySQL server during query """

CR_SERVER_LOST_EXTENDED = 2055
""" Lost connection to MySQL server at '%s', system error: %d """


_RETRIABLE_CLIENT_ERROR_CODES = (
  CR_CONNECTION_ERROR,
  CR_CONN_HOST_ERROR,
  CR_UNKNOWN_HOST,
  CR_SERVER_GONE_ERROR,
  CR_TCP_CONNECTION,
  CR_SERVER_HANDSHAKE_ERR,
  CR_SERVER_LOST,
  CR_SERVER_LOST_EXTENDED,
)


_RETRIABLE_SERVER_ERROR_CODES = (
  ER.TABLE_DEF_CHANGED,
  ER.LOCK_WAIT_TIMEOUT,
  ER.LOCK_DEADLOCK,

  #Maybe these also?
  #  ER_TOO_MANY_DELAYED_THREADS
  #  ER_BINLOG_PURGE_EMFILE
  #  ER_TOO_MANY_CONCURRENT_TRXS
  #  ER_CON_COUNT_ERROR
  #  ER_OUTOFMEMORY
)


_ALL_RETRIABLE_ERROR_CODES = set(_RETRIABLE_CLIENT_ERROR_CODES +
                              _RETRIABLE_SERVER_ERROR_CODES)



def retrySQL(timeoutSec=60*5, getLoggerCallback=logging.getLogger):
  """ Return a closure suitable for use as a decorator for
  retrying a pymysql DAO function on certain failures that warrant retries (
  e.g., RDS/MySQL server down temporarily, transaction deadlock, etc.).
  We share this function across multiple scripts (e.g., ClientJobsDAO,
  StreamMgr) for consitent behavior.
  
  NOTE: please ensure that the operation being retried is idempotent.
  
  timeoutSec:       How many seconds from time of initial call to stop retrying
                     (floating point)
  getLoggerCallback:
                    user-supplied callback function that takes no args and
                     returns the logger instance to use for logging.

  Usage Example:
    NOTE: logging must be initialized *before* any loggers are created, else
      there will be no output; see nupic.support.initLogging()

    @retrySQL()
    def jobInfo(self, jobID):
        ...
  """
  
  def retryFilter(e, args, kwargs):
    
    if isinstance(e, (pymysql.InternalError, pymysql.OperationalError)):
      if e.args and e.args[0] in _ALL_RETRIABLE_ERROR_CODES:
        return True
      
    elif isinstance(e, pymysql.Error):
      if (e.args and
          inspect.isclass(e.args[0]) and issubclass(e.args[0], socket_error)):
        return True
      
    return False
  
  
  retryExceptions = tuple([
    pymysql.InternalError,
    pymysql.OperationalError,
    pymysql.Error,
  ])
  
  return make_retry_decorator(
    timeoutSec=timeoutSec, initialRetryDelaySec=0.1, maxRetryDelaySec=10,
    retryExceptions=retryExceptions, retryFilter=retryFilter,
    getLoggerCallback=getLoggerCallback)
