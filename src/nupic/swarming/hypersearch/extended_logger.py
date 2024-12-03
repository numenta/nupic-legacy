# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
import logging
import copy



class ExtendedLogger(logging.Logger):
  """ Extends the log message by appending custom parameters
  """

  __logPrefix = ''

  def __init__(self, level):
    self._baseLogger = logging.Logger
    self._baseLogger.__init__(self, level)


  @staticmethod
  def setLogPrefix(logPrefix):
    ExtendedLogger.__logPrefix = copy.deepcopy(logPrefix)


  def getExtendedMsg(self, msg):
    extendedMsg = '%s' % (ExtendedLogger.__logPrefix) + msg
    return extendedMsg


  def debug(self, msg, *args, **kwargs):
    """
    Log 'msg % args' with severity 'DEBUG'.

    To pass exception information, use the keyword argument exc_info with
    a true value, e.g.

    logger.debug("Houston, we have a %s", "thorny problem", exc_info=1)
    """
    self._baseLogger.debug(self, self.getExtendedMsg(msg), *args, **kwargs)


  def info(self, msg, *args, **kwargs):
    """
    Log 'msg % args' with severity 'INFO'.

    To pass exception information, use the keyword argument exc_info with
    a true value, e.g.

    logger.info("Houston, we have a %s", "interesting problem", exc_info=1)
    """
    self._baseLogger.info(self, self.getExtendedMsg(msg), *args, **kwargs)


  def warning(self, msg, *args, **kwargs):
    """
    Log 'msg % args' with severity 'WARNING'.

    To pass exception information, use the keyword argument exc_info with
    a true value, e.g.

    logger.warning("Houston, we have a %s", "bit of a problem", exc_info=1)
    """
    self._baseLogger.warning(self, self.getExtendedMsg(msg), *args, **kwargs)

  warn = warning


  def error(self, msg, *args, **kwargs):
    """
    Log 'msg % args' with severity 'ERROR'.

    To pass exception information, use the keyword argument exc_info with
    a true value, e.g.

    logger.error("Houston, we have a %s", "major problem", exc_info=1)
    """
    self._baseLogger.error(self, self.getExtendedMsg(msg), *args, **kwargs)


  def critical(self, msg, *args, **kwargs):
    """
    Log 'msg % args' with severity 'CRITICAL'.

    To pass exception information, use the keyword argument exc_info with
    a true value, e.g.

    logger.critical("Houston, we have a %s", "major disaster", exc_info=1)
    """
    self._baseLogger.critical(self, self.getExtendedMsg(msg), *args, **kwargs)

  fatal = critical


  def log(self, level, msg, *args, **kwargs):
      """
      Log 'msg % args' with the integer severity 'level'.

      To pass exception information, use the keyword argument exc_info with
      a true value, e.g.

      logger.log(level, "We have a %s", "mysterious problem", exc_info=1)
      """
      self._baseLogger.log(self, level, self.getExtendedMsg(msg), *args,
                           **kwargs)



def test():
  pass



if __name__ == "__main__":
  test()
