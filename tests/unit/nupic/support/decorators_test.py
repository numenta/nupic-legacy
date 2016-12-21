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

"""Unit tests for the nupic.support.decorators module.

TODO: add tests for logEntryExit
"""


from mock import patch, call, Mock

from nupic.support.unittesthelpers.testcasebase import unittest
from nupic.support import decorators



class TestParentException(Exception):
  pass



class TestChildException(TestParentException):
  pass



class RetryDecoratorTest(unittest.TestCase):
  """Unit tests specific to retry decorator."""


  def mockSleepTime(self, mockTime, mockSleep):
    """Configures mocks for time.time and time.sleep such that every call
    to time.sleep(x) increments the return value of time.time() by x.

    mockTime:     time.time mock
    mockSleep:    time.sleep mock
    """

    class _TimeContainer(object):
      accumulatedTime = 0

    def testTime():
      return _TimeContainer.accumulatedTime

    def testSleep(duration):
      _TimeContainer.accumulatedTime += duration

    mockTime.side_effect = testTime
    mockSleep.side_effect = testSleep


  @patch("time.sleep", autospec=True)
  @patch("time.time", autospec=True)
  def testRetryNoTimeForRetries(self, mockTime, mockSleep):
    """Test that when timeoutSec == 0, function is executed exactly once
    with no retries, and raises an exception on failure.
    """

    self.mockSleepTime(mockTime, mockSleep)

    retryDecorator = decorators.retry(
      timeoutSec=0, initialRetryDelaySec=0.2,
      maxRetryDelaySec=10)

    testFunction = Mock(side_effect=TestParentException("Test exception"),
                        __name__="testFunction", autospec=True)

    with self.assertRaises(TestParentException):
      retryDecorator(testFunction)()

    self.assertFalse(mockSleep.called)
    testFunction.assert_called_once_with()


  @patch("time.sleep", autospec=True)
  @patch("time.time", autospec=True)
  def testRetryWaitsInitialRetryDelaySec(self, mockTime, mockSleep):
    """Test that delay times are correct."""

    self.mockSleepTime(mockTime, mockSleep)

    retryDecorator = decorators.retry(
      timeoutSec=30, initialRetryDelaySec=2,
      maxRetryDelaySec=10)

    testFunction = Mock(side_effect=TestParentException("Test exception"),
                        __name__="testFunction", autospec=True)

    with self.assertRaises(TestParentException):
      retryDecorator(testFunction)()

    self.assertEqual(mockSleep.mock_calls, [call(2), call(4), call(8),
                                            call(10), call(10)])

    self.assertEqual(testFunction.call_count, 6)


  @patch("time.sleep", autospec=True)
  @patch("time.time", autospec=True)
  def testRetryRetryExceptionIncluded(self, mockTime, mockSleep):
    """Test that retry is triggered if raised exception is in
    retryExceptions."""

    self.mockSleepTime(mockTime, mockSleep)

    retryDecorator = decorators.retry(
      timeoutSec=1, initialRetryDelaySec=1,
      maxRetryDelaySec=10, retryExceptions=(TestParentException,))

    @retryDecorator
    def testFunction():
      raise TestChildException("Test exception")

    with self.assertRaises(TestChildException):
      testFunction()

    self.assertEqual(mockSleep.call_count, 1)


  @patch("time.sleep", autospec=True)
  @patch("time.time", autospec=True)
  def testRetryRetryExceptionExcluded(self, mockTime, mockSleep):
    """ Test that retry is not triggered if raised exception is not in
    retryExceptions """

    self.mockSleepTime(mockTime, mockSleep)

    class TestExceptionA(Exception):
      pass

    class TestExceptionB(Exception):
      pass

    retryDecorator = decorators.retry(
      timeoutSec=1, initialRetryDelaySec=1,
      maxRetryDelaySec=10, retryExceptions=(TestExceptionA,))

    @retryDecorator
    def testFunction():
      raise TestExceptionB("Test exception")

    with self.assertRaises(TestExceptionB):
      testFunction()

    self.assertEqual(mockSleep.call_count, 0)


  @patch("time.sleep", autospec=True)
  @patch("time.time", autospec=True)
  def testRetryRetryFilter(self, mockTime, mockSleep):
    """Test that if retryFilter is specified and exception is in
    retryExceptions, retries iff retryFilter returns true."""

    self.mockSleepTime(mockTime, mockSleep)

    # Test with retryFilter returning True

    retryDecoratorTrueFilter = decorators.retry(
      timeoutSec=1, initialRetryDelaySec=1,
      maxRetryDelaySec=10, retryExceptions=(TestParentException,),
      retryFilter=lambda _1, _2, _3: True)

    @retryDecoratorTrueFilter
    def testFunctionTrue():
      raise TestChildException("Test exception")

    with self.assertRaises(TestChildException):
      testFunctionTrue()

    self.assertEqual(mockSleep.call_count, 1)

    # Test with retryFilter returning False

    mockSleep.reset_mock()

    retryDecoratorFalseFilter = decorators.retry(
      timeoutSec=1, initialRetryDelaySec=1,
      maxRetryDelaySec=10, retryExceptions=(TestParentException,),
      retryFilter=lambda _1, _2, _3: False)

    @retryDecoratorFalseFilter
    def testFunctionFalse():
      raise TestChildException("Test exception")

    with self.assertRaises(TestChildException):
      testFunctionFalse()

    self.assertEqual(mockSleep.call_count, 0)


  @patch("time.sleep", autospec=True)
  @patch("time.time", autospec=True)
  def testReturnsExpectedWithExpectedArgs(self, mockTime, mockSleep):
    """Test that docorated function receives only expected args and
    that it returns the expected value on success."""

    self.mockSleepTime(mockTime, mockSleep)

    retryDecorator = decorators.retry(
      timeoutSec=30, initialRetryDelaySec=2,
      maxRetryDelaySec=10)

    testFunction = Mock(return_value=321,
                        __name__="testFunction", autospec=True)

    returnValue = retryDecorator(testFunction)(1, 2, a=3, b=4)

    self.assertEqual(returnValue, 321)
    testFunction.assert_called_once_with(1, 2, a=3, b=4)


  @patch("time.sleep", autospec=True)
  @patch("time.time", autospec=True)
  def testNoRetryIfCallSucceeds(self, mockTime, mockSleep):
    """If the initial call succeeds, test that no retries are performed."""

    self.mockSleepTime(mockTime, mockSleep)

    retryDecorator = decorators.retry(
      timeoutSec=30, initialRetryDelaySec=2,
      maxRetryDelaySec=10)

    testFunction = Mock(__name__="testFunction", autospec=True)

    retryDecorator(testFunction)()

    testFunction.assert_called_once_with()


  @patch("time.sleep", autospec=True)
  @patch("time.time", autospec=True)
  def testFailsFirstSucceedsLater(self, mockTime, mockSleep):
    """If initial attempts fail but subsequent attempt succeeds, ensure that
    expected number of retries is performed and expected value is returned."""

    self.mockSleepTime(mockTime, mockSleep)

    retryDecorator = decorators.retry(
      timeoutSec=30, initialRetryDelaySec=2,
      maxRetryDelaySec=10)

    testFunction = Mock(
      side_effect=[
        TestParentException("Test exception 1"),
        TestParentException("Test exception 2"),
        321
      ],
      __name__="testFunction", autospec=True)

    returnValue = retryDecorator(testFunction)()

    self.assertEqual(returnValue, 321)
    self.assertEqual(testFunction.call_count, 3)


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
    loggerMock = Mock(spec_set=decorators.logging.getLogger())
    with patch.object(decorators.logging, "getLogger", autospec=True,
                      return_value=loggerMock):

      @decorators.logExceptions()
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


  def testLogExceptionsWithRuntimeErrorExceptionAndCustomLogger(self):
    loggerMock = Mock(spec_set=decorators.logging.getLogger())

    @decorators.logExceptions(loggerMock)
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
    loggerMock = Mock(spec_set=decorators.logging.getLogger())
    with patch.object(decorators.logging, "getLogger", autospec=True,
                      return_value=loggerMock):

      # SystemExit is based on BaseException, so we want to make sure that
      # those are handled properly, too
      inputArgs = (1, 2, 3)
      inputKwargs = dict(a="A", b="B", c="C")

      @decorators.logExceptions()
      def doSomething(*args, **kwargs):
        self.assertEqual(args, inputArgs)
        self.assertEqual(kwargs, inputKwargs)

        raise SystemExit()

      with self.assertRaises(SystemExit):
        doSomething(*inputArgs, **inputKwargs)

      self.assertEqual(loggerMock.exception.call_count, 1)
      self.assertIn("Unhandled exception %r from %r. Caller stack:\n%s",
                    loggerMock.exception.call_args[0][0])


if __name__ == '__main__':
  unittest.main()
