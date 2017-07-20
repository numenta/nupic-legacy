# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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

import os
import unittest2 as unittest

from nupic.support.console_printer import ConsolePrinterMixin, Tee



# Class used for testing

class MyClass(ConsolePrinterMixin):


  def __init__(self):
    ConsolePrinterMixin.__init__(self)


  def run(self):
    for i in xrange(0, 4):
      self.cPrint(i, "message at level %d", i)



class ConsolePrinterTest(unittest.TestCase):


  def testPrint(self):
    mydir = os.path.dirname(os.path.abspath(__file__))

    filename = os.path.abspath("console_output.txt")
    if os.path.exists(filename):
      os.remove(filename)

    # Capture output to a file so that we can compare it
    with Tee(filename):
      c1 = MyClass()
      print "Running with default verbosity"
      c1.run()
      print

      print "Running with verbosity 2"
      c1.consolePrinterVerbosity = 2
      c1.run()
      print

      print "Running with verbosity 0"
      c1.consolePrinterVerbosity = 0
      c1.run()
      print

      c1.cPrint(0, "Message %s two %s", "with", "args")
      c1.cPrint(0, "Message with no newline", newline=False)
      c1.cPrint(0, " Message with newline")
      c1.cPrint(0, "Message with %s and %s",
                "no newline", "args", newline=False)
      c1.cPrint(0, " Message with %s and %s", "newline", "args")

      print "Done"

    with self.assertRaises(KeyError):
      c1.cPrint(0, "Message", badkw="badvalue")

    referenceFilename = os.path.join(mydir, "consoleprinter_output.txt")
    expected = open(referenceFilename).readlines()
    actual = open(filename).readlines()

    print ("Comparing files '%s'" % referenceFilename)
    print ("and             '%s'" % filename)

    self.assertEqual(len(expected), len(actual))

    for i in xrange(len(expected)):
      self.assertEqual(expected[i].strip(), actual[i].strip())

    # Clean up
    os.remove(filename)



if __name__ == "__main__":
  unittest.main()
