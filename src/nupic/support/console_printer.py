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
This module defines :class:`ConsolePrinterMixin` and :class:`Tee`.

The :class:`ConsolePrinterMixin` is used by objects that need to print to the
screen under the control of a verbosity level.

The :class:`Tee` class is used to redirect standard output to a file in addition
to sending it to the console.
"""

import sys

class ConsolePrinterMixin(object):
  """Mixin class for printing to the console with different verbosity levels.

    :param verbosity: (int)
        0: don't print anything to stdout
        1: normal (production-level) printing
        2: extra debug information
        3: lots of debug information
  """

  def __init__(self, verbosity=1):
    # The internal attribute is consolePrinterVerbosity to make it
    # more clear where it comes from (without having to trace back
    # through the class hierarchy). This attribute is normally
    # not accessed directly, but it is fine to read or write it
    # directly if you know what you're doing.
    self.consolePrinterVerbosity = verbosity

  def cPrint(self, level, message, *args, **kw):
    """Print a message to the console.

    Prints only if level <= self.consolePrinterVerbosity
    Printing with level 0 is equivalent to using a print statement,
    and should normally be avoided.

    :param level: (int) indicating the urgency of the message with
           lower values meaning more urgent (messages at level 0  are the most
           urgent and are always printed)

    :param message: (string) possibly with format specifiers

    :param args: specifies the values for any format specifiers in message

    :param kw: newline is the only keyword argument. True (default) if a newline
           should be printed
    """

    if level > self.consolePrinterVerbosity:
      return

    if len(kw) > 1:
      raise KeyError("Invalid keywords for cPrint: %s" % str(kw.keys()))

    newline = kw.get("newline", True)
    if len(kw) == 1 and 'newline' not in kw:
      raise KeyError("Invalid keyword for cPrint: %s" % kw.keys()[0])

    if len(args) == 0:
      if newline:
        print message
      else:
        print message,
    else:
      if newline:
        print message % args
      else:
        print message % args,

class Tee(object):
  """This class captures standard output and writes it to a file
  in addition to sending it to the console
  """
  def __init__(self, outputFile):
    self.outputFile = open(outputFile, 'w', buffering=False)
    self.stdout = sys.stdout
    sys.stdout = self

  def write(self, s):
    self.outputFile.write(s)
    self.stdout.write(s)

  def flush(self):
    self.stdout.flush()
    self.outputFile.flush()

  def fileno(self):
    return self.outputFile.fileno()

  def close(self):
    self.outputFile.close()
    sys.stdout = self.stdout

  def __enter__(self):
    pass

  def __exit__(self, exc_type, exc_value, traceback):
    self.close()
