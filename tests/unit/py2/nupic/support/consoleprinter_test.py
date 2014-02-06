#! /usr/bin/env python
# ----------------------------------------------------------------------
#  Copyright (C) 2010 Numenta Inc. All rights reserved.
#
#  The information and source code contained herein is the
#  exclusive property of Numenta Inc. No part of this software
#  may be used, reproduced, stored or distributed in any form,
#  without explicit written authorization from Numenta Inc.
# ----------------------------------------------------------------------

from __future__ import with_statement
import os
from nupic.support.consoleprinter import ConsolePrinterMixin, Tee

class MyClass(ConsolePrinterMixin):
  def __init__(self):
    ConsolePrinterMixin.__init__(self)

  def run(self):
    for i in xrange(0, 4):
      self.cPrint(i, "message at level %d", i)



if __name__ == "__main__":
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
    c1.cPrint(0, "Message with %s and %s", "no newline", "args", newline=False)
    c1.cPrint(0, " Message with %s and %s", "newline", "args")


    print "Done"

  caughtException = False
  try:
    c1.cPrint(0, "Message", badkw="badvalue")
  except KeyError, e:
    caughtException = True
  if not caughtException:
    raise Exception("Bad keyword for cPrint should have been caught")



  referenceFilename = os.path.join(mydir, "testconsoleprinter_output.txt")
  expected = open(referenceFilename).readlines()
  actual = open(filename).readlines()

  print ("Comparing files '%s'" % referenceFilename)
  print ("and             '%s'" % filename)


  if len(expected) != len(actual):
    raise Exception("Expected %d lines of output got %d lines" % (len(expected), len(actual)))

  for i in xrange(len(expected)):
    if expected[i].strip() != actual[i].strip():
      raise Exception("Line %d of output differs from expected" % i)

  print "Output is correct"
