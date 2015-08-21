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
## @file
Internal package.

Package containing modules that are used internally by Numenta Python
tools and plugins to extend standard library functionality.
These modules should NOT be used by client applications.

The following modules are included:

nupic.support.paths
Module containing filesystem path manipulation utilities.

nupic.support.serialization
Module containing Python object serialization (pickling and unpickling) and
versioning utilities.

nupic.support.compress
Module containing Python object encoding and compression utilities.

nupic.support.processes
Module containing operating system process management utilities and wrappers.

nupic.support.output
Module containing operating system interprocess communication utilities and
wrappers.

nupic.support.diff
Module containing file difference calculation wrappers.

nupic.support.vision
Temporary location for vision framework before the move to nupic.vision.

nupic.support.deprecate
Contains the deprecate decorator used for automatic handling of deprecated
methods.

nupic.support.memchecker
Contains the MemChecker class, for checking physical memory and monitoring
memory usage.

nupic.support.imagesearch
Contains functions for searching for images on the web and downloading them.
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
from nupic.support.fshelpers import makeDirectoryFromAbsolutePath


# Local imports



def getCallerInfo(depth=2):
  """Utility function to get information about function callers

  The information is the tuple (function/method name, filename, class)
  The class will be None if the caller is just a function and not an object
  method.

  depth: how far back in the callstack to go to extract the caller info

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



def title(s=None, additional='', stream=sys.stdout, frame='-'):
  """Utility function to display nice titles

  It automatically extracts the name of the function/method it is called from
  and you can add additional text. title() will then print the name
  of the function/method and the additional text surrounded by tow lines
  of dashes. If you don't want the name of the function, you can provide
  alternative text (regardless of the additional text)

  @param s - text to display, uses the function name and arguments by default
  @param additional - extra text to display (not needed if s is not None)
  @param stream - the stream to print to. Ny default goes to standard output
  @param frame - the character used for the over and under line. Default is '-'

  Examples:

  def foo():
    title()

  will display:

  ---
  foo
  ---

  def foo():
    title(additional='(), this is cool!!!')

  will display:

  ----------------------
  foo(), this is cool!!!
  ----------------------


  def foo():
    title('No function name here!')

  will display:

  ----------------------
  No function name here!
  ----------------------
  """
  if s is None:
    callable_name, file_name, class_name = getCallerInfo(2)
    s = callable_name
    if class_name is not None:
      method_name = s
      s = class_name + '.' + callable_name
  lines = (s + additional).split('\n')
  length = max(len(line) for line in lines)
  print >> stream, '-' * length
  print >> stream, s + additional
  print >> stream, '-' * length



def bringToFront(title):
  """Bring a top-level window with a given title
     to the front on Windows"""
  if sys.platform != 'win32':
    return

  import ctypes
  find_window = ctypes.windll.user32.FindWindowA
  set_foreground_window = ctypes.windll.user32.SetForegroundWindow
  hwnd = find_window(None, title)
  if hwnd == 0:
    raise Exception('There is no window titled: "%s"' % title)
  set_foreground_window(hwnd)



def getUserDocumentsPath():
  """
  Find the user's "Documents" directory (OS X), "My Documents" directory
  (Windows), or home directory (Unix).
  """

  # OS X and Windows code from:
  # http://www.blueskyonmars.com/2005/08/05
  # /finding-a-users-my-documents-folder-on-windows/
  # Alternate Windows code from:
  # http://bugs.python.org/issue1763
  if sys.platform.startswith('win'):
    if sys.platform.startswith('win32'):
      # Try the primary method on 32-bit windows
      try:
        from win32com.shell import shell
        alt = False
      except ImportError:
        try:
          import ctypes
          dll = ctypes.windll.shell32
          alt = True
        except:
          raise Exception("Could not find 'My Documents'")
    else:
      # Use the alternate method on 64-bit Windows
      alt = True
    if not alt:
      # Primary method using win32com
      df = shell.SHGetDesktopFolder()
      pidl = df.ParseDisplayName(0, None,
               "::{450d8fba-ad25-11d0-98a8-0800361b1103}")[1]
      path = shell.SHGetPathFromIDList(pidl)
    else:
      # Alternate method using ctypes rather than win32com
      buf = ctypes.create_string_buffer(300)
      dll.SHGetSpecialFolderPathA(None, buf, 0x0005, False)
      path = buf.value
  elif sys.platform.startswith('darwin'):
    from Carbon import Folder, Folders
    folderref = Folder.FSFindFolder(Folders.kUserDomain,
                                    Folders.kDocumentsFolderType,
                                    False)
    path = folderref.as_pathname()
  else:
    path = os.getenv('HOME')
  return path



def getArgumentDescriptions(f):
  """
  Get the arguments, default values, and argument descriptions for a function.

  Returns a list of tuples: (argName, argDescription, defaultValue). If an
    argument has no default value, the tuple is only two elements long (as None
    cannot be used, since it could be a default value itself).

  Parses the argument descriptions out of the function docstring, using a
  format something lke this:

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



# TODO queryNumInwardIters appears to be unused and should probably be deleted
#  from here altogether; it's likely an artifact of the legacy vision support.
#def queryNumInwardIters(configPath, radialLength, numRepetitions=1):
#  """
#  Public utility API that accepts a config path and
#  radial length, and determines the proper number of
#  training iterations with which to invoke net.run()
#  when running a PictureSensor in 'inward' mode.
#  """
#  numCats = queryNumCategories(configPath)
#  sequenceLen = radialLength + 1
#  numItersPerCat = (8 * radialLength) * sequenceLen
#  numTrainingItersTP = numItersPerCat * numCats
#  return numTrainingItersTP * numRepetitions



gLoggingInitialized = False
def initLogging(verbose=False, console='stdout', consoleLevel='DEBUG'):
  """
  Initilize NuPic logging by reading in from the logging configuration file. The
  logging configuration file is named 'nupic-logging.conf' and is expected to be
  in the format defined by the python logging module.

  If the environment variable 'NTA_CONF_PATH' is defined, then the logging
  configuration file is expected to be in the NTA_CONF_PATH directory. If
  NTA_CONF_PATH is not defined, then it is found in the 'conf/default'
  subdirectory of the NuPic installation directory (typically
  ~/nupic/current/conf/default)

  The logging configuration file can use the environment variable 'NTA_LOG_DIR'
  to set the locations of log files. If this variable is not defined, logging to
  files will be disabled.
  
  console:    Defines console output for the default "root" logging
              configuration; this may be one of 'stdout', 'stderr', or None;
              Use None to suppress console logging output
  consoleLevel:
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
  else:
    raise RuntimeError("This platform is neither darwin nor linux: %s" % (
      sys.platform,))

  # Nupic logs go to file
  replacements[makeKey('PERSISTENT_LOG_HANDLER')] = 'fileHandler'
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



def reinitLoggingDir():
  """ (Re-)Initialize the loging directory for the calling application that
  uses initLogging() for logging configuration
  
  NOTE: It's typially unnecessary to call this function directly since
   initLogging takes care of it for you. This function is exposed primarily for
   the benefit of nupic-services.py to allow it to restore its logging directory
   after the hard-reset operation.
  """
  if gLoggingInitialized and 'NTA_LOG_DIR' in os.environ:
    makeDirectoryFromAbsolutePath(os.path.dirname(_genLoggingFilePath()))



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
  
  

def enableLoggingErrorDebugging():
  """ Overrides the python logging facility's Handler.handleError function to
  raise an exception instead of print and suppressing it.  This allows a deeper
  stacktrace to be emitted that is very helpful for quickly finding the
  file/line that initiated the invalidly-formatted logging operation.
  
  NOTE: This is for debugging only - be sure to remove the call to this function
   *before* checking in your changes to the source code repository, as it will
   cause the application to fail if some invalidly-formatted logging statement
   still exists in your code.
  
  Example usage: enableLoggingErrorDebugging must be called *after*
   initLogging()
   
    import nupic.support
    nupic.support.initLogging()
    nupic.support.enableLoggingErrorDebugging()
  
  "TypeError: not all arguments converted during string formatting" is an
  example exception that might be output by the built-in handlers with the
  following very shallow traceback that doesn't go deep enough to show the
  source of the problem:
  
  File ".../python2.6/logging/__init__.py", line 776, in emit
    msg = self.format(record)
  File ".../python2.6/logging/__init__.py", line 654, in format
    return fmt.format(record)
  File ".../python2.6/logging/__init__.py", line 436, in format
    record.message = record.getMessage()
  File ".../python2.6/logging/__init__.py", line 306, in getMessage
    msg = msg % self.args
  TypeError: not all arguments converted during string formatting
  """
  
  print >> sys.stderr, ("WARNING")
  print >> sys.stderr, ("WARNING: "
    "nupic.support.enableLoggingErrorDebugging() was "
    "called to install a debugging patch into all logging handlers that "
    "will cause the program to fail if a logging exception occurrs; this "
    "call is for debugging only and MUST be removed before checking in code "
    "into production system. Caller: %s") % (
    traceback.format_stack(),)
  print >> sys.stderr, ("WARNING")
  
  def handleErrorPatch(*args, **kwargs):
    if logging.raiseExceptions:
      raise
  
  for handler in logging._handlerList:
    handler.handleError = handleErrorPatch
  
  return



def intTo8ByteArray(inValue):
  """
  Converts an int to a packed byte array, with left most significant byte
  """

  values = (
    (inValue >> 56 ) & 0xff,
    (inValue >> 48 ) & 0xff,
    (inValue >> 40 ) & 0xff,
    (inValue >> 32 ) & 0xff,
    (inValue >> 24 ) & 0xff,
    (inValue >> 16 ) & 0xff,
    (inValue >> 8 ) & 0xff,
    inValue & 0xff
  )

  s = struct.Struct('B B B B B B B B')
  packed_data = s.pack(*values)

  return packed_data



def byteArrayToInt(packed_data):
  """
  Converts a byte array into an integer
  """
  value = struct.unpack('B B B B B B B B', packed_data)
  return value[0] << 56 | \
         value[1] << 48 | \
         value[2] << 40 | \
         value[3] << 32 | \
         value[4] << 24 | \
         value[5] << 16 | \
         value[6] << 8 | \
         value[7]



def getSpecialRowID():
  """
  Special row id is 0xFF FFFF FFFF FFFF FFFF (9 bytes of 0xFF)
  """
  values = (0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF)
  s = struct.Struct('B B B B B B B B B')
  packed_data = s.pack(*values)

  return packed_data



_FLOAT_SECONDS_IN_A_DAY = 24.0 * 60.0 * 60.0
def floatSecondsFromTimedelta(td):
  """ Convert datetime.timedelta to seconds in floating point """
  sec = (td.days * _FLOAT_SECONDS_IN_A_DAY + td.seconds * 1.0 +
         td.microseconds / 1E6)

  return sec



def aggregationToMonthsSeconds(interval):
  """
  Return the number of months and seconds from an aggregation dict that 
  represents a date and time. 
  
  Interval is a dict that contain one or more of the following keys: 'years',
  'months', 'weeks', 'days', 'hours', 'minutes', seconds', 'milliseconds', 
  'microseconds'.

  Parameters:
  ---------------------------------------------------------------------
  interval:  The aggregation interval, as a dict representing a date and time
  retval:    number of months and seconds in the interval, as a dict:
                {months': XX, 'seconds': XX}. The seconds is
                a floating point that can represent resolutions down to a
                microsecond. 
  
  For example:
  aggregationMicroseconds({'years': 1, 'hours': 4, 'microseconds':42}) == 
      {'months':12, 'seconds':14400.000042}
  
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
  
  Parameters:
  ---------------------------------------------------------------------
  dividend:  The numerator, as a dict representing a date and time
  divisor:   the denominator, as a dict representing a date and time
  retval:    number of times divisor goes into dividend, as a floating point
                number. 
  
  For example:
  aggregationDivide({'hours': 4}, {'minutes': 15}) == 16
  
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
