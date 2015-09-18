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

# This script implements an extension of the unittest2.TestCase class to be
# used as a base class unit tests

import copy
import optparse
import sys
from datetime import datetime

import unittest2 as unittest



class TestCaseBase(unittest.TestCase):
  """ Here, we wrap the various unittest.TestCase assert methods (that
  our base classes use) in order to add extra info to their msg args from our
  log buffer.
  """

  def __init__(self, testMethodName, *args, **kwargs):
    #_debugOut(("Constructing=%s") % (testMethodName,))

    # Construct the base-class instance
    #unittest.TestCase.__init__(self, testMethodName, *args, **kwargs)
    super(TestCaseBase, self).__init__(testMethodName, *args, **kwargs)

    # Extra log items to be added to msg strings in our self.myAssertXXXXXX
    # wrappers.  Items may be added here during a given test run by calling
    # self.addExtraLogItem(item)
    self.__logItems = []
    return


  def printTestHeader(self):
    """ Print out what test we are running """

    print
    print "###############################################################"
    print "Running %s..." % (self,)
    print "[%s UTC]" % (datetime.utcnow())
    print "###############################################################"
    sys.stdout.flush()
    return


  def printBanner(self, msg, *args):
    """ Print out a banner """

    print
    print "==============================================================="
    print msg % args
    print >> sys.stdout, "[%s UTC; %s]" % (datetime.utcnow(), self,)
    print "==============================================================="
    sys.stdout.flush()
    return

  #========================
  def addExtraLogItem(self, item):
    """ Add an item to the log items list for the currently running session.
    Our self.myAssertXXXXXX wrappers add the current items to the msg that is
    passed to the unittest's assertXXXXX methods.  The extra info will show up
    in test results if the test fails.
    """
    self.__logItems.append(item)
    return

  #========================
  def resetExtraLogItems(self):
    self.__logItems = []
    return

  #========================
  def __wrapMsg(self, msg):
    """ Called by our unittest.TestCase.assertXXXXXX overrides to construct a
    message from the given message plus self.__logItems, if any. If
    self.__logItems is non-empty, returns a dictionary containing the given
    message value as the "msg" property and self.__logItems as the "extra"
    property. If self.__logItems is empy, returns the given msg arg.
    """
    msg = msg \
            if not self.__logItems \
            else {"msg":msg, "extra":copy.copy(self.__logItems)}

    # Honor line feeds in the message for when it gets printed out
    msg = str(msg)
    msg = msg.replace('\\n', '\n')
    return msg

  #========================
  def assertEqual(self, first, second, msg=None):
    """unittest.TestCase.assertEqual override; adds extra log items to msg"""
    unittest.TestCase.assertEqual(self, first, second, self.__wrapMsg(msg))
    return

  #========================
  def assertNotEqual(self, first, second, msg=None):
    """unittest.TestCase.assertNotEqual override; adds extra log items to msg"""
    unittest.TestCase.assertNotEqual(self, first, second, self.__wrapMsg(msg))
    return

  #========================
  def assertTrue(self, expr, msg=None):
    """unittest.TestCase.assertTrue override; adds extra log items to msg"""
    unittest.TestCase.assertTrue(self, expr, self.__wrapMsg(msg))
    return

  #========================
  def assertFalse(self, expr, msg=None):
    """unittest.TestCase.assertFalse override; adds extra log items to msg"""
    unittest.TestCase.assertFalse(self, expr, self.__wrapMsg(msg))
    return



class TestOptionParser(optparse.OptionParser, object):
  """Option parser with predefined test options."""

  __long__ = None

  standard_option_list = [
      optparse.Option('--verbosity', default=0, type='int',
                      help='Verbosity level from least verbose, 0, to most, '
                           '3 [default=%default].'),
      optparse.Option('--seed', default=42, type='int',
                      help='Seed to use for random number generators '
                           '[default: %default].'),
      optparse.Option('--short', action='store_false', dest='long',
                      default=True, help='Run only short tests.'),
      optparse.Option('--long', action='store_true', dest='long',
                      default=False, help='Run all short and long tests.'),
      optparse.Option('--installDir', dest='installDir',
                      help='Installation directory used for this test run.'),
      ]

  def parse_args(self, args=None, values=None, consumeArgv=True):
    options, remainingArgs = super(TestOptionParser, self).parse_args(args, values)
    TestOptionParser.__long__ = options.long
    if consumeArgv:
      sys.argv = [sys.argv[0]] + remainingArgs
    return options, remainingArgs


def longTest(testMethod):
  """Decorator for specifying tests that only run when --long is specified."""
  def newTestMethod(*args, **kwargs):
    if TestOptionParser.__long__ is None:
      raise Exception('TestOptionParser must be used in order to use @longTest'
                      'decorator.')
    if TestOptionParser.__long__:
      return testMethod(*args, **kwargs)
    else:
      msg = 'Skipping long test: %s' % testMethod.__name__
      return unittest.skip(msg)(testMethod)(*args, **kwargs)
  return newTestMethod
