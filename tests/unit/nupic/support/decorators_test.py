#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

"""Unit tests for the nupic.support.decorators module.

TODO: add tests for logEntryExit and retry decorators
"""



from mock import patch, Mock


from nupic.support.unittesthelpers.testcasebase import unittest


from nupic.support import decorators


class LogExceptionsTestCase(unittest.TestCase):
  """Unit tests for the nupic.support.decorators module."""
  
  def testLogExceptionsWithoutException(self):
    @decorators.logExceptions()
    def doSomething(*args, **kwargs):
      return args, kwargs
    
    
    inputArgs = (1, 2, 3)
    inputKwargs = dict(a="A", b="B", c="C")
    
    outputArgs, outputKwargs = doSomething(*inputArgs, **inputKwargs)
    
    # Validate that doSomething got the right inputs
    self.assertEqual(outputArgs, inputArgs)
    self.assertEqual(outputKwargs, inputKwargs)
  
  
  def testLogExceptionsWithRuntimeErrorExceptionAndDefaultLogger(self):
    @decorators.logExceptions()
    def doSomething(*args, **kwargs):
      self.assertEqual(args, inputArgs)
      self.assertEqual(kwargs, inputKwargs)
      
      raise RuntimeError()
    
    
    loggerMock = Mock(spec_set=decorators.logging.getLogger())
    with patch.object(decorators.logging, "getLogger", autospec=True,
                      return_value=loggerMock):
      inputArgs = (1, 2, 3)
      inputKwargs = dict(a="A", b="B", c="C")
      
      with self.assertRaises(RuntimeError):
        doSomething(*inputArgs, **inputKwargs)
      
      self.assertEqual(loggerMock.exception.call_count, 1)
      self.assertIn("Unhandled exception %r from %r. Caller stack:\n%s",
                    loggerMock.exception.call_args[0][0])
  
  
  def testLogExceptionsWithRuntimeErrorExceptionAndCustomLogger(self):
    loggerMock = Mock(spec_set=decorators.logging.getLogger())
    
    @decorators.logExceptions(lambda: loggerMock)
    def doSomething(*args, **kwargs):
      self.assertEqual(args, inputArgs)
      self.assertEqual(kwargs, inputKwargs)
      
      raise RuntimeError()
    
    
    inputArgs = (1, 2, 3)
    inputKwargs = dict(a="A", b="B", c="C")
    
    with self.assertRaises(RuntimeError):
      doSomething(*inputArgs, **inputKwargs)
    
    self.assertEqual(loggerMock.exception.call_count, 1)
    self.assertIn("Unhandled exception %r from %r. Caller stack:\n%s",
                  loggerMock.exception.call_args[0][0])
  
  
  def testLogExceptionsWithSystemExitExceptionAndDefaultLogger(self):
    # SystemExit is based on BaseException, so we want to make sure that
    # those are handled properly, too
    inputArgs = (1, 2, 3)
    inputKwargs = dict(a="A", b="B", c="C")
    
    @decorators.logExceptions()
    def doSomething(*args, **kwargs):
      self.assertEqual(args, inputArgs)
      self.assertEqual(kwargs, inputKwargs)
      
      raise SystemExit()
    
    
    loggerMock = Mock(spec_set=decorators.logging.getLogger())
    with patch.object(decorators.logging, "getLogger", autospec=True,
                      return_value=loggerMock):
      
      with self.assertRaises(SystemExit):
        doSomething(*inputArgs, **inputKwargs)
      
      self.assertEqual(loggerMock.exception.call_count, 1)
      self.assertIn("Unhandled exception %r from %r. Caller stack:\n%s",
                    loggerMock.exception.call_args[0][0])



if __name__ == '__main__':
  unittest.main()
