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

"""
Package containing modules that are used internally by Numenta Python
tools and plugins to extend standard library functionality.
These modules should NOT be used by client applications.
"""

from __future__ import with_statement

# Standard imports
import os
import sys
import inspect
import logging
import logging.config
import logging.handlers
from platform import python_version
import struct
from StringIO import StringIO
import time
import traceback

from pkg_resources import resource_string, resource_filename

from configuration import Configuration
from nupic.support.fs_helpers import makeDirectoryFromAbsolutePath


# Local imports



def getCallerInfo(depth=2):
  """Utility function to get information about function callers

  The information is the tuple (function/method name, filename, class)
  The class will be None if the caller is just a function and not an object
  method.

  :param depth: (int) how far back in the callstack to go to extract the caller
         info

  """
  f = sys._getframe(depth)
  method_name = f.f_code.co_name
  filename = f.f_code.co_filename

  arg_class = None
  args = inspect.getargvalues(f)
  if len(args[0]) > 0:
    arg_name = args[0][0] # potentially the 'self' arg if its a method
    arg_class = args[3][arg_name].__class__.__name__
  return (method_name, filename, arg_class)



def title(s=None, additional='', stream=sys.stdout):
  """Utility function to display nice titles

  It automatically extracts the name of the function/method it is called from
  and you can add additional text. title() will then print the name
  of the function/method and the additional text surrounded by tow lines
  of dashes. If you don't want the name of the function, you can provide
  alternative text (regardless of the additional text)

  :param s: (string) text to display, uses the function name and arguments by
         default
  :param additional: (string) extra text to display (not needed if s is not
         None)
  :param stream: (stream) the stream to print to. Ny default goes to standard
         output

  Examples:

  .. code-block:: python

    def foo():
      title()

  will display:

  .. code-block:: text

    ---
    foo
    ---

  .. code-block:: python

    def foo():
      title(additional='(), this is cool!!!')

  will display:

  .. code-block:: text

    ----------------------
    foo(), this is cool!!!
    ----------------------

  .. code-block:: python

    def foo():
      title('No function name here!')

  will display:

  .. code-block:: text

    ----------------------
    No function name here!
    ----------------------

  """
  if s is None:
    callable_name, file_name, class_name = getCallerInfo(2)
    s = callable_name
    if class_name is not None:
      s = class_name + '.' + callable_name
  lines = (s + additional).split('\n')
  length = max(len(line) for line in lines)
  print >> stream, '-' * length
  print >> stream, s + additional
  print >> stream, '-' * length



def getArgumentDescriptions(f):
  """
  Get the arguments, default values, and argument descriptions for a function.

  Parses the argument descriptions out of the function docstring, using a
  format something lke this:

  ::

    [junk]
    argument_name:     description...
      description...
      description...
    [junk]
    [more arguments]

  It will find an argument as long as the exact argument name starts the line.
  It will then strip a trailing colon, if present, then strip the rest of the
  line and use it to start the description. It will then strip and append any
  subsequent lines with a greater indent level than the original argument name.

  :param f: (function) to inspect
  :returns: (list of tuples) (``argName``, ``argDescription``, ``defaultValue``)
    If an argument has no default value, the tuple is only two elements long (as
    ``None`` cannot be used, since it could be a default value itself).
  """

  # Get the argument names and default values
  argspec = inspect.getargspec(f)

  # Scan through the docstring to extract documentation for each argument as
  # follows:
  #   Check the first word of the line, stripping a colon if one is present.
  #   If it matches an argument name:
  #    Take the rest of the line, stripping leading whitespeace
  #    Take each subsequent line if its indentation level is greater than the
  #      initial indentation level
  #    Once the indentation level is back to the original level, look for
  #      another argument
  docstring = f.__doc__
  descriptions = {}
  if docstring:
    lines = docstring.split('\n')
    i = 0
    while i < len(lines):
      stripped = lines[i].lstrip()
      if not stripped:
        i += 1
        continue
      # Indentation level is index of the first character
      indentLevel = lines[i].index(stripped[0])
      # Get the first word and remove the colon, if present
      firstWord = stripped.split()[0]
      if firstWord.endswith(':'):
        firstWord = firstWord[:-1]
      if firstWord in argspec.args:
        # Found an argument
        argName = firstWord
        restOfLine = stripped[len(firstWord)+1:].strip()
        argLines = [restOfLine]
        # Take the next lines as long as they are indented more
        i += 1
        while i < len(lines):
          stripped = lines[i].lstrip()
          if not stripped:
            # Empty line - stop
            break
          if lines[i].index(stripped[0]) <= indentLevel:
            # No longer indented far enough - stop
            break
          # This line counts too
          argLines.append(lines[i].strip())
          i += 1
        # Store this description
        descriptions[argName] = ' '.join(argLines)
      else:
        # Not an argument
        i += 1

  # Build the list of (argName, description, defaultValue)
  args = []
  if argspec.defaults:
    defaultCount = len(argspec.defaults)
  else:
    defaultCount = 0
  nonDefaultArgCount = len(argspec.args) - defaultCount
  for i, argName in enumerate(argspec.args):
    if i >= nonDefaultArgCount:
      defaultValue = argspec.defaults[i - nonDefaultArgCount]
      args.append((argName, descriptions.get(argName, ""), defaultValue))
    else:
      args.append((argName, descriptions.get(argName, "")))

  return args



gLoggingInitialized = False
def initLogging(verbose=False, console='stdout', consoleLevel='DEBUG'):
  """
  Initilize NuPic logging by reading in from the logging configuration file. The
  logging configuration file is named ``nupic-logging.conf`` and is expected to
  be in the format defined by the python logging module.

  If the environment variable ``NTA_CONF_PATH`` is defined, then the logging
  configuration file is expected to be in the ``NTA_CONF_PATH`` directory. If
  ``NTA_CONF_PATH`` is not defined, then it is found in the 'conf/default'
  subdirectory of the NuPic installation directory (typically
  ~/nupic/current/conf/default)

  The logging configuration file can use the environment variable
  ``NTA_LOG_DIR`` to set the locations of log files. If this variable is not
  defined, logging to files will be disabled.

  :param console: Defines console output for the default "root" logging
              configuration; this may be one of 'stdout', 'stderr', or None;
              Use None to suppress console logging output
  :param consoleLevel:
              Logging-level filter string for console output corresponding to
              logging levels in the logging module; may be one of:
              'DEBUG', 'INFO', 'WARNING', 'ERROR', or 'CRITICAL'.
              E.g.,  a value of'WARNING' suppresses DEBUG and INFO level output
              to console, but allows WARNING, ERROR, and CRITICAL
  """

  # NOTE: If you call this twice from the same process there seems to be a
  # bug - logged messages don't show up for loggers that you do another
  # logging.getLogger() on.
  global gLoggingInitialized
  if gLoggingInitialized:
    if verbose:
      print >> sys.stderr, "Logging already initialized, doing nothing."
    return

  consoleStreamMappings = {
    'stdout'  : 'stdoutConsoleHandler',
    'stderr'  : 'stderrConsoleHandler',
  }

  consoleLogLevels = ['DEBUG', 'INFO', 'WARNING', 'WARN', 'ERROR', 'CRITICAL',
                      'FATAL']

  assert console is None or console in consoleStreamMappings.keys(), (
    'Unexpected console arg value: %r') % (console,)

  assert consoleLevel in consoleLogLevels, (
    'Unexpected consoleLevel arg value: %r') % (consoleLevel)

  # -----------------------------------------------------------------------
  # Setup logging. Look for the nupic-logging.conf file, first in the
  #   NTA_CONFIG_DIR path (if defined), then in a subdirectory of the nupic
  #   module
  configFilename = 'nupic-logging.conf'
  configFilePath = resource_filename("nupic.support", configFilename)

  configLogDir = os.environ.get('NTA_LOG_DIR', None)

  # Load in the logging configuration file
  if verbose:
    print >> sys.stderr, (
      "Using logging configuration file: %s") % (configFilePath)

  # This dict will hold our replacement strings for logging configuration
  replacements = dict()

  def makeKey(name):
    """ Makes replacement key """
    return "$$%s$$" % (name)

  platform = sys.platform.lower()
  if platform.startswith('java'):
    # Jython
    import java.lang
    platform = java.lang.System.getProperty("os.name").lower()
    if platform.startswith('mac os x'):
      platform = 'darwin'

  if platform.startswith('darwin'):
    replacements[makeKey('SYSLOG_HANDLER_ADDRESS')] = '"/var/run/syslog"'
  elif platform.startswith('linux'):
    replacements[makeKey('SYSLOG_HANDLER_ADDRESS')] = '"/dev/log"'
  elif platform.startswith('win'):
    replacements[makeKey('SYSLOG_HANDLER_ADDRESS')] = '"log"'
  else:
    raise RuntimeError("This platform is neither darwin, win32, nor linux: %s" % (
      sys.platform,))

  # Nupic logs go to file
  replacements[makeKey('PERSISTENT_LOG_HANDLER')] = 'fileHandler'
  if platform.startswith('win'):
    replacements[makeKey('FILE_HANDLER_LOG_FILENAME')] = '"NUL"'
  else:
    replacements[makeKey('FILE_HANDLER_LOG_FILENAME')] = '"/dev/null"'

  # Set up log file path for the default file handler and configure handlers
  handlers = list()

  if configLogDir is not None:
    logFilePath = _genLoggingFilePath()
    makeDirectoryFromAbsolutePath(os.path.dirname(logFilePath))
    replacements[makeKey('FILE_HANDLER_LOG_FILENAME')] = repr(logFilePath)

    handlers.append(replacements[makeKey('PERSISTENT_LOG_HANDLER')])

  if console is not None:
    handlers.append(consoleStreamMappings[console])

  replacements[makeKey('ROOT_LOGGER_HANDLERS')] = ", ".join(handlers)

  # Set up log level for console handlers
  replacements[makeKey('CONSOLE_LOG_LEVEL')] = consoleLevel

  customConfig = StringIO()

  # Using pkg_resources to get the logging file, which should be packaged and
  # associated with this source file name.
  loggingFileContents = resource_string(__name__, configFilename)

  for lineNum, line in enumerate(loggingFileContents.splitlines()):
    if "$$" in line:
      for (key, value) in replacements.items():
        line = line.replace(key, value)

    # If there is still a replacement string in the line, we're missing it
    #  from our replacements dict
    if "$$" in line and "$$<key>$$" not in line:
      raise RuntimeError(("The text %r, found at line #%d of file %r, "
                          "contains a string not found in our replacement "
                          "dict.") % (line, lineNum, configFilePath))

    customConfig.write("%s\n" % line)

  customConfig.seek(0)
  if python_version()[:3] >= '2.6':
    logging.config.fileConfig(customConfig, disable_existing_loggers=False)
  else:
    logging.config.fileConfig(customConfig)

  gLoggingInitialized = True



def _genLoggingFilePath():
  """ Generate a filepath for the calling app """
  appName = os.path.splitext(os.path.basename(sys.argv[0]))[0] or 'UnknownApp'
  appLogDir = os.path.abspath(os.path.join(
    os.environ['NTA_LOG_DIR'],
    'numenta-logs-%s' % (os.environ['USER'],),
    appName))
  appLogFileName = '%s-%s-%s.log' % (
    appName, long(time.mktime(time.gmtime())), os.getpid())
  return os.path.join(appLogDir, appLogFileName)



def aggregationToMonthsSeconds(interval):
  """
  Return the number of months and seconds from an aggregation dict that
  represents a date and time.

  Interval is a dict that contain one or more of the following keys: 'years',
  'months', 'weeks', 'days', 'hours', 'minutes', seconds', 'milliseconds',
  'microseconds'.

  For example:

  ::

    aggregationMicroseconds({'years': 1, 'hours': 4, 'microseconds':42}) ==
        {'months':12, 'seconds':14400.000042}

  :param interval: (dict) The aggregation interval representing a date and time
  :returns: (dict) number of months and seconds in the interval:
            ``{months': XX, 'seconds': XX}``. The seconds is
            a floating point that can represent resolutions down to a
            microsecond.

  """

  seconds = interval.get('microseconds', 0) * 0.000001
  seconds += interval.get('milliseconds', 0) * 0.001
  seconds += interval.get('seconds', 0)
  seconds += interval.get('minutes', 0) * 60
  seconds += interval.get('hours', 0) * 60 * 60
  seconds += interval.get('days', 0) * 24 * 60 * 60
  seconds += interval.get('weeks', 0) * 7 * 24 * 60 * 60

  months = interval.get('months', 0)
  months += 12 * interval.get('years', 0)

  return {'months': months, 'seconds': seconds}



def aggregationDivide(dividend, divisor):
  """
  Return the result from dividing two dicts that represent date and time.

  Both dividend and divisor are dicts that contain one or more of the following
  keys: 'years', 'months', 'weeks', 'days', 'hours', 'minutes', seconds',
  'milliseconds', 'microseconds'.

  For example:

  ::

    aggregationDivide({'hours': 4}, {'minutes': 15}) == 16

  :param dividend: (dict) The numerator, as a dict representing a date and time
  :param divisor: (dict) the denominator, as a dict representing a date and time
  :returns: (float) number of times divisor goes into dividend

  """

  # Convert each into microseconds
  dividendMonthSec = aggregationToMonthsSeconds(dividend)
  divisorMonthSec = aggregationToMonthsSeconds(divisor)

  # It is a usage error to mix both months and seconds in the same operation
  if (dividendMonthSec['months'] != 0 and divisorMonthSec['seconds'] != 0) \
    or (dividendMonthSec['seconds'] != 0 and divisorMonthSec['months'] != 0):
    raise RuntimeError("Aggregation dicts with months/years can only be "
      "inter-operated with other aggregation dicts that contain "
      "months/years")


  if dividendMonthSec['months'] > 0:
    return float(dividendMonthSec['months']) / divisor['months']

  else:
    return float(dividendMonthSec['seconds']) / divisorMonthSec['seconds']
