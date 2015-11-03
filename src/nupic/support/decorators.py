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

import functools
import logging
import sys
import time
import traceback


# TODO Need unit tests



def logExceptions(logger=None):
  """ Returns a closure suitable for use as function/method decorator for
  logging exceptions that leave the scope of the decorated function. Exceptions
  are logged at ERROR level.

  logger:    user-supplied logger instance. Defaults to logging.getLogger.

  Usage Example:
    NOTE: logging must be initialized *before* any loggers are created, else
      there will be no output; see nupic.support.initLogging()

    @logExceptions()
    def myFunctionFoo():
        ...
        raise RuntimeError("something bad happened")
        ...
  """
  logger = (logger if logger is not None else logging.getLogger(__name__))

  def exceptionLoggingDecorator(func):
    @functools.wraps(func)
    def exceptionLoggingWrap(*args, **kwargs):
      try:
        return func(*args, **kwargs)
      except:
        logger.exception(
          "Unhandled exception %r from %r. Caller stack:\n%s",
          sys.exc_info()[1], func, ''.join(traceback.format_stack()), )
        raise

    return exceptionLoggingWrap

  return exceptionLoggingDecorator



def logEntryExit(getLoggerCallback=logging.getLogger,
                 entryExitLogLevel=logging.DEBUG, logArgs=False,
                 logTraceback=False):
  """ Returns a closure suitable for use as function/method decorator for
  logging entry/exit of function/method.

  getLoggerCallback:    user-supplied callback function that takes no args and
                          returns the logger instance to use for logging.
  entryExitLogLevel:    Log level for logging entry/exit of decorated function;
                          e.g., logging.DEBUG; pass None to disable entry/exit
                          logging.
  logArgs:              If True, also log args
  logTraceback:         If True, also log Traceback information

  Usage Examples:
    NOTE: logging must be initialized *before* any loggers are created, else
      there will be no output; see nupic.support.initLogging()

    @logEntryExit()
    def myFunctionBar():
        ...


    @logEntryExit(logTraceback=True)
    @logExceptions()
    def myFunctionGamma():
        ...
        raise RuntimeError("something bad happened")
        ...
  """

  def entryExitLoggingDecorator(func):

    @functools.wraps(func)
    def entryExitLoggingWrap(*args, **kwargs):

      if entryExitLogLevel is None:
        enabled = False
      else:
        logger = getLoggerCallback()
        enabled = logger.isEnabledFor(entryExitLogLevel)

      if not enabled:
        return func(*args, **kwargs)

      funcName = str(func)

      if logArgs:
        argsRepr = ', '.join(
          [repr(a) for a in args] +
          ['%s=%r' % (k,v,) for k,v in kwargs.iteritems()])
      else:
        argsRepr = ''

      logger.log(
        entryExitLogLevel, "ENTERING: %s(%s)%s", funcName, argsRepr,
        '' if not logTraceback else '; ' + repr(traceback.format_stack()))

      try:
        return func(*args, **kwargs)
      finally:
        logger.log(
          entryExitLogLevel, "LEAVING: %s(%s)%s", funcName, argsRepr,
          '' if not logTraceback else '; ' + repr(traceback.format_stack()))


    return entryExitLoggingWrap

  return entryExitLoggingDecorator



def retry(timeoutSec, initialRetryDelaySec, maxRetryDelaySec,
          retryExceptions=(Exception,),
          retryFilter=lambda e, args, kwargs: True,
          logger=None, clientLabel=""):
  """ Returns a closure suitable for use as function/method decorator for
  retrying a function being decorated.

  timeoutSec:           How many seconds from time of initial call to stop
                        retrying (floating point); 0 = no retries
  initialRetryDelaySec: Number of seconds to wait for first retry.
                        Subsequent retries will occur at geometrically
                        doubling intervals up to a maximum interval of
                        maxRetryDelaySec (floating point)
  maxRetryDelaySec:     Maximum amount of seconds to wait between retries
                        (floating point)
  retryExceptions:      A tuple (must be a tuple) of exception classes that,
                        including their subclasses, should trigger retries;
                        Default: any Exception-based exception will trigger
                        retries
  retryFilter:          Optional filter function used to further filter the
                        exceptions in the retryExceptions tuple; called if the
                        current exception meets the retryExceptions criteria:
                        takes the current exception instance, args, and kwargs
                        that were passed to the decorated function, and returns
                        True to retry, False to allow the exception to be
                        re-raised without retrying. Default: permits any
                        exception that matches retryExceptions to be retried.
  logger:               User-supplied logger instance to use for logging.
                        None=defaults to logging.getLogger(__name__).

  Usage Example:
    NOTE: logging must be initialized *before* any loggers are created, else
      there will be no output; see nupic.support.initLogging()

    _retry = retry(timeoutSec=300, initialRetryDelaySec=0.2,
                   maxRetryDelaySec=10, retryExceptions=[socket.error])
    @_retry
    def myFunctionFoo():
        ...
        raise RuntimeError("something bad happened")
        ...
  """

  assert initialRetryDelaySec > 0, str(initialRetryDelaySec)

  assert timeoutSec >= 0, str(timeoutSec)

  assert maxRetryDelaySec >= initialRetryDelaySec, \
      "%r < %r" % (maxRetryDelaySec, initialRetryDelaySec)

  assert isinstance(retryExceptions, tuple), (
    "retryExceptions must be tuple, but got %r") % (type(retryExceptions),)

  if logger is None:
    logger = logging.getLogger(__name__)

  def retryDecorator(func):
    @functools.wraps(func)
    def retryWrap(*args, **kwargs):
      numAttempts = 0
      delaySec = initialRetryDelaySec
      startTime = time.time()

      # Make sure it gets called at least once
      while True:
        numAttempts += 1
        try:
          result = func(*args, **kwargs)
        except retryExceptions, e:
          if not retryFilter(e, args, kwargs):
            if logger.isEnabledFor(logging.DEBUG):
              logger.debug(
                '[%s] Failure in %r; retries aborted by custom retryFilter. '
                'Caller stack:\n%s', clientLabel, func,
                ''.join(traceback.format_stack()), exc_info=True)
            raise

          now = time.time()
          # Compensate for negative time adjustment so we don't get stuck
          # waiting way too long (python doesn't provide monotonic time yet)
          if now < startTime:
            startTime = now
          if (now - startTime) >= timeoutSec:
            logger.exception(
              '[%s] Exhausted retry timeout (%s sec.; %s attempts) for %r. '
              'Caller stack:\n%s', clientLabel, timeoutSec, numAttempts, func,
              ''.join(traceback.format_stack()))
            raise

          if numAttempts == 1:
            logger.warning(
              '[%s] First failure in %r; initial retry in %s sec.; '
              'timeoutSec=%s. Caller stack:\n%s', clientLabel, func, delaySec,
              timeoutSec, ''.join(traceback.format_stack()), exc_info=True)
          else:
            logger.debug(
              '[%s] %r failed %s times; retrying in %s sec.; timeoutSec=%s. '
              'Caller stack:\n%s',
              clientLabel, func, numAttempts, delaySec, timeoutSec,
              ''.join(traceback.format_stack()), exc_info=True)
          time.sleep(delaySec)

          delaySec = min(delaySec*2, maxRetryDelaySec)
        else:
          if numAttempts > 1:
            logger.info('[%s] %r succeeded on attempt # %d',
                        clientLabel, func, numAttempts)

          return result

    return retryWrap

  return retryDecorator
