# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
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


# This module implements a light-weight event loop. TODO: Eventually, this
# should be replaced by a more sophisticaled event loop implementation, such as
# the one in python's Twisted framework, which also supports comminution
# primitives.
#
# IMPORTANT: This API is NOT thread-safe
#

from abc import ABCMeta, abstractmethod
import logging
import time


MODULE_NAME = "nupic.support.SimpleEventLoop"


###############################################################################
class EventMonitorIface(object):
  """ Event monitor interface; to be used as base class for event monitor
  implementations.  Additional event monitors may be created by subclassing
  this class and implementing its interface.
  """

  __metaclass__ = ABCMeta


  @abstractmethod
  def peekLoop(self):
    """ May be called by anyone to get reference to the EventLoop
    instance that this EventMonitor is registered with.

    Parameters:
    ---------------------------------------------------------------------
    retval:         EventLoop instance that was passed in via _joinLoop; None
                    is returned before EventLoop registration or after
                    _leaveLoop() is handled by this EventMonitor intance.
    """


  @abstractmethod
  def _joinLoop(self, eventLoop):
    """ Called by EventLoop from the scope of registerEventMonitors before
    EventLoop calls any other EventMonitor interface method. The implementation
    of this inteface is expected to save the given eventLoop reference and make
    it subsequently avaiable via EventMonitorIface.peekLoop()

    Parameters:
    ---------------------------------------------------------------------
    eventLoop:      EventLoop instance that this EventMonitor instance is
                    registered with.

    retval:         nothing
    """


  @abstractmethod
  def _leaveLoop(self):
    """ Called by EventLoop to inform the EventMonitor instance that it is
    being disassociated from the EventLoop.  The EventMonitor instance
    is expected to clear its reference to the EventLoop that was previously
    saved by _joinLoop().

    Parameters:
    ---------------------------------------------------------------------
    retval:         nothing
    """


  @abstractmethod
  def _check(self):
    """ Called by EventLoop; checks if the event being monitored is ready for
    dispatch.

    Parameters:
    ---------------------------------------------------------------------
    retval:         True if ready; False if not ready for dispatch
    """

  @abstractmethod
  def _prepareForSleep(self):
    """ Called by EventLoop before event loop goes to sleep;

    Parameters:
    ---------------------------------------------------------------------
    retval:         Maximum time interval that EvenLoop may sleep before
                    the next series of _check() calls (>= 0 sec).
                    Returning None means that this EventMonitor does not
                    wish to impose a limit (i.e., sleep as much as you like)
    """

  @abstractmethod
  def _dispatch(self):
    """ Called by EventLoop; dispatches the handler that is associated with this
    event monitor instance.

    Parameters:
    ---------------------------------------------------------------------
    retval:         True: keep this event monitor in EventLoop; False:
                    disassociate this event monitor from EventLoop
    """




###############################################################################
class _EventMonitorHelper(EventMonitorIface):
  """ Private helper base class for SimpleEventLoop's EventMonitor
  implementations.
  """

  def __init__(self, handler, logger):
    """
    Parameters:
    ---------------------------------------------------------------------
    handler:        handler to be called when timer becomes ready;
                    the handler MUST have the following signature:
                      bool handler(monitor)
                      monitor: The dispatching EventMonitor instance
                      Returns: True to keep the dispatching EventMonitor in the
                                EventLoop; False to disassociate the dispatching
                                EventMonitor from the EventLoop, so that the handler
                                would not be called again (e.g., for single-shot
                                timer)
    logger:         python logger instance for logging info associated with this
                    timer instance.
    """

    # _handler may be accessed by subclass (e.g., by __repr__())
    self._handler = handler

    # _logger may be accessed by subclasses
    self._logger = logger

    self.__loop = None
    return


  def peekLoop(self):
    """ [EventMonitorIface override] May be called by anyone to get reference to
    the EventLoop instance that this EventMonitor is registered with.

    Parameters:
    ---------------------------------------------------------------------
    retval:         EventLoop instance that was passed in via _joinLoop; None
                    is returned before EventLoop registration or after
                    _leaveLoop() is handled by this EventMonitor intance.
    """

    return self.__loop


  def _joinLoop(self, eventLoop):
    """ [EventMonitorIface override] Called by EventLoop from the scope of
    registerEventMonitors before EventLoop calls any other EventMonitor interface
    method. The implementation of this inteface is expected to save the given
    eventLoop reference and make it subsequently avaiable via
    EventMonitorIface.peekLoop()

    Parameters:
    ---------------------------------------------------------------------
    eventLoop:      EventLoop instance that this EventMonitor instance is
                    registered with.

    retval:         nothing
    """

    assert self.__loop is None, "self.__loop is not None: %r" % (self.__loop,)

    self.__loop = eventLoop

    return


  def _leaveLoop(self):
    """ [EventMonitorIface override] Called by EventLoop to inform the
    EventMonitor instance that it is being disassociated from the EventLoop. The
    EventMonitor instance is expected to clear its reference to the EventLoop
    that was previously saved by _joinLoop().

    Parameters:
    ---------------------------------------------------------------------
    retval:         nothing
    """

    assert self.__loop is not None

    self.__loop = None

    return


  def _dispatch(self):
    """ [EventMonitorIface override] Called by EventLoop; dispatches the handler
    that is associated with this event monitor instance.

    Parameters:
    ---------------------------------------------------------------------
    retval:         True: keep this event monitor in EventLoop; False:
                    disassociate this event monitor from EventLoop
    """

    try:
      keepMe = self._handler(monitor=self)
    except Exception:
      self._logger.exception("Exception during EventMonitor dispatch to user.")
      raise

    return keepMe




###############################################################################
class Timer(_EventMonitorHelper):
  def __init__(self, handler, logger, hours=0, minutes=0, sec=0):
    """ Constructs a repeating timer

    Parameters:
    ---------------------------------------------------------------------
    interval:       timer interval in hours and/or minutes and/or sec (ints
                      or floats)
    handler:        handler to be called when timer becomes ready;
                    the handler MUST have the following signature:
                      bool handler(monitor)
                      monitor: The dispatching Timer instance
                      Returns: True to keep the dispatching Timer in the
                                EventLoop; False to disassociate the dispatching
                                Timer from the EventLoop, so that the handler
                                would not be called again (e.g., for single-shot
                                timer)
    logger:         python logger instance for logging info associated with this
                    timer instance.
    """

    super(Timer, self).__init__(handler=handler, logger=logger)

    self.__interval = (3600.0 * hours) + (60.0 * minutes) + sec
    self.__lastFired = time.time()
    return


  def __repr__(self):
    return ("%s<interval=%r, lastFired=%r, handler=%r>" % (
            self.__class__.__name__, self.__interval,
            self.__lastFired, self._handler))


  def _check(self):
    """ [EventMonitorIface override] Called by EventLoop; checks if the event
    being monitored is ready for dispatch.

    Parameters:
    ---------------------------------------------------------------------
    retval:         True if ready; False if not ready for dispatch
    """

    timeRemaining = self.__getRemainingTime()

    isReady = (timeRemaining <= 0)

    return isReady


  def _prepareForSleep(self):
    """ [EventMonitorIface override] Called by EventLoop before event loop goes
    to sleep;

    Parameters:
    ---------------------------------------------------------------------
    retval:         Maximum time interval that EvenLoop may sleep before
                    the next series of _check() calls (>= 0 sec).
                    Returning None means that this EventMonitor does not
                    wish to impose a limit (i.e., sleep as much as you like)
    """
    return self.__getRemainingTime()


  def _dispatch(self):
    """ [EventMonitorIface override] Called by EventLoop; dispatches the handler
    that is associated with this event monitor instance.

    Parameters:
    ---------------------------------------------------------------------
    retval:         True: keep this event monitor in EventLoop; False:
                    disassociate this event monitor from EventLoop
    """

    self.__lastFired = time.time()

    return super(Timer, self)._dispatch()


  def __getRemainingTime(self):
    """ Computes how much time remains until the next dispatch of the timer

    Parameters:
    ---------------------------------------------------------------------
    retval:         Amount of time that remains (>= 0); in seconds as a
                    floating point value
    """
    now = time.time()

    # Handle backwards clock adjustment (built-in python API didn't provide
    # access to monotonic time when this method was written)
    if now < self.__lastFired:
      self.__lastFired = now

    timeRemaining = self.__interval - (now - self.__lastFired)
    if timeRemaining < 0:
      timeRemaining = 0

    return timeRemaining




###############################################################################
class Poll(_EventMonitorHelper):
  """ This Event Monitor class is always ready for dispatch, and may be used
  for continuous polling.

  WARNING: as long as a Poll EventMonitor instance is active, EventLoop will
  never sleep and may consume 100% CPU time.
  """

  def __init__(self, handler, logger):
    """ Constructs a repeating timer

    Parameters:
    ---------------------------------------------------------------------
    handler:        handler to be called
                    the handler MUST have the following signature:
                      bool handler(monitor)
                      monitor: The dispatching Event Monitor instance
                      Returns: True to keep the dispatching monitor in the
                                EventLoop; False to disassociate the dispatching
                                monitor from the EventLoop, so that the handler
                                would not be called again

    logger:         python logger instance for logging info associated with this
                    monitor instance.
    """
    super(Poll, self).__init__(handler=handler, logger=logger)

    return


  def __repr__(self):
    return ("%s<handler=%r>" % (self.__class__.__name__, self._handler,))


  def _check(self):
    """ Called by EventLoop; checks if the event being monitored is ready for
    dispatch.

    Parameters:
    ---------------------------------------------------------------------
    retval:         True if ready; False if not ready for dispatch
    """
    return True


  def _prepareForSleep(self):
    """ Called by EventLoop before event loop goes to sleep;

    Parameters:
    ---------------------------------------------------------------------
    retval:         Maximum time interval that EvenLoop may sleep before
                    the next series of _check() calls (>= 0 sec).
                    Returning None means that this EventMonitor does not
                    wish to impose a limit (i.e., sleep as much as you like)
    """
    return 0


  ##def _dispatch(self): NOTE: Our superclass does what we need for _dispatch()



###############################################################################
class EventLoop(object):
  """ This class manages our main "event" loop. It allows us to schedule periodic
  tasks and run an event loop that waits for either stdin or one or more
  tasks to be ready to run.
  """

  eventMonitorInterfaceClass = EventMonitorIface

  timerMonitorClass = Timer

  pollMonitorClass = Poll


  ############################################################################
  def __init__(self, logLevel=None):
    """
    Parameters:
    ---------------------------------------------------------------------
    logLevel:       Pass None for default log level; otherwise, one of the
                    python logging levels to override the default log level
                    (e.g., logging.DEBUG)
    """
    global MODULE_NAME

    self.__logger = logging.getLogger(".".join(
      ['com.numenta', MODULE_NAME, self.__class__.__name__]))

    if logLevel is not None:
      self.__logger.setLevel(logLevel)


    self.__monitors = []    # List of EventMonitorIface-based objects
    self.__readyMonitorIndexes = []
    self.__removeMonitorIndexes = []

    self.__inRunLoop = False
    self.__stopRequested = False

    self.__logger.info("EventLoop instance created: %r", self)

    return



  ############################################################################
  def registerEventMonitors(self, *monitors):
    """ Register one or more EventMonitorIface-based monitor instances. May be
    called either before running the loop or while the loop is running from
    user's handler function that was dispatched from a monitor that is run by
    the same EventLoop.

    Parameters:
    ---------------------------------------------------------------------
    *monitors:      one or more comma-separated EventMonitorIface-based monitor
                    instances

    retval:         nothing
    """

    for m in monitors:
      # Make sure it wasn't added already (user error)
      assert m not in self.__monitors, "already registered: %r" % (m,)

      self.__logger.info("Registering EventMonitor: %r", m)

      self.__monitors.append(m)

      m._joinLoop(eventLoop=self)

      self.__logger.info("Finished registering EventMonitor: %r", m)

    return


  def stopLoop(self):
    """ Request the loop to stop running, causing run() to return eventually.

    Parameters:
    ---------------------------------------------------------------------
    monitor:        an EventMonitorIface-based monitor instance

    retval:         nothing
    """

    self.__stopRequested = True

    self.__logger.info("stopLoop requested by user")

    return


  ############################################################################
  def close(self):
    """ Unregister all Event Monitors from the loop, thus eliminating circular
    references between registered EventMonitor instances and this EventLoop
    instance.

    NOTE: this object may be used in a Context Manager (i.e., "with")
    expression, which guarantees that it will be closed under all
    circumstances.

    WARNING: DO NOT call while run() is executing, or bad things will happen.
    """

    self.__logger.info("Closing EventLoop")

    assert not self.__inRunLoop

    if len(self.__monitors) > 0:
      for i in xrange(len(self.__monitors) - 1, -1, -1):
        self.__monitors[i]._leaveLoop()
        self.__monitors.pop(i)

      assert len(self.__monitors) == 0, \
             "len(self.__monitors): %s" % (len(self.__monitors),)


    self.__logger.info("Finished closing EventLoop")

    return


  ############################################################################
  def run(self):
    """ Run the event loop until stopLoop() is called.

    WARNING: caller must maintain at least one EventMonitor in the running
    EventLoop instance.  A running EventLoop without EventMonitors is
    considered an error that will trigger an exception if loop-stop is
    not pending at the same time.

    Parameters:
    ---------------------------------------------------------------------
    retval:         nothing
    """

    self.__logger.info("Entering run-loop")


    try:
      self.__inRunLoop = True
      self.__run()
    finally:
      self.__inRunLoop = False
      self.__stopRequested = False


    self.__logger.info("Exiting run-loop")

    return


  ############################################################################
  def __run(self):
    """ Implementation of EventLoop's inner run() logic.

    Parameters:
    ---------------------------------------------------------------------
    retval:         nothing
    """

    # A run-loop without any monitors is useless, and is most likely user
    # error
    assert self.__monitors or self.__stopRequested, \
           "User error: running an EventLoop w/o EventMonitors"

    while not self.__stopRequested:

      # ------------------------------------------------------------------
      # Prepare monitors for sleep and derermine sleep timeout (in seconds)
      self.__logger.debug("Preparing EventMonitors for sleep")

      timeout = 3600
      for monitor in self.__monitors:

        self.__logger.debug("Preparing EventMonitor for sleep: %r", monitor)

        timeTillDue = monitor._prepareForSleep()

        self.__logger.debug("Finished preparing EventMonitor for sleep; "
                            "monitor returned timeTillDue=%r sec: %r",
                            timeTillDue, monitor)


        if timeTillDue is None:
          continue

        assert timeTillDue >= 0, "unexected negative interval: %r" % (timeTillDue,)

        timeout = min(timeout, timeTillDue)


      # ------------------------------------------------------------------
      # Sleep
      #
      # NOTE: the _sleep method may be overridden by a subclass to implement
      # different sleep behavior/semantics (that's why we call it
      # unconditionally)
      #
      self._sleep(timeout)


      # --------------------------------------------------------------
      # Check for readiness
      self.__logger.debug("Performing EventMonitor readiness check")

      assert len(self.__readyMonitorIndexes) == 0, \
             "Unexpected ready monitors: %r" % (self.__readyMonitorIndexes,)

      for (i, monitor) in enumerate(self.__monitors):

        self.__logger.debug("Checking EventMonitor: %r", monitor)

        isReady = monitor._check()

        self.__logger.debug("EventMonitor ready=%r: %r", isReady, monitor)

        if isReady:
          self.__readyMonitorIndexes.append(i)


      # --------------------------------------------------------------
      # Dispatch
      if self.__readyMonitorIndexes:
        self.__logger.debug("Dispatching ready EventMonitors")

        assert len(self.__removeMonitorIndexes) == 0, \
               "Unexpected remove monitors: %r" % (self.__removeMonitorIndexes,)

        for i in self.__readyMonitorIndexes:
          readyMonitor = self.__monitors[i]

          self.__logger.debug("Dispatching: %r", readyMonitor)

          keep = readyMonitor._dispatch()

          self.__logger.debug("EventMonitor completed dispatch; keep=%r: %r",
                              keep, readyMonitor,)

          if not keep:
            self.__removeMonitorIndexes.append(i)


        # Prepare for next cycle
        del self.__readyMonitorIndexes[:]


        # Handle monitors on the remove list
        if self.__removeMonitorIndexes:
          # NOTE: we pop in reverse order to maintain validity of indexes
          for i in reversed(self.__removeMonitorIndexes):
            departingMonitor = self.__monitors[i]

            self.__logger.info("Removing from EventLoop: %r", departingMonitor)

            departingMonitor._leaveLoop()
            self.__monitors.pop(i)

            self.__logger.info("Finished removing from EventLoop: %r",
                               departingMonitor)

          # Prepare for next cycle
          del self.__removeMonitorIndexes[:]

          assert self.__monitors or self.__stopRequested, \
                 "User error: running an EventLoop w/o EventMonitors"

      else:
        self.__logger.debug("There were no ready EventMonitors")

    # ^^^^ end of: while not self.__stopRequested


    return


  def _sleep(self, timeoutSec):
    """ Called internally by the EventLoop implementation to sleep the loop for
    the given amount of time.  This method may be overridden by subclasses to
    implement different sleep behavior/semantics.

    Parameters:
    ---------------------------------------------------------------------
    timeoutSec:     The amount of time, in seconds, to sleep (floating point
                    or integer).  This generally represents the amount of
                    time until the next timer is due to fire.
                    NOTE: _sleep() may return sooner than this (e.g., if
                    interrupted by a signal) or later (e.g., due to process
                    scheduling constraints)

    retval:         nothing
    """
    if timeoutSec > 0:
      self.__logger.debug("Going to sleep for %r seconds", timeoutSec)

      time.sleep(timeoutSec)

      self.__logger.debug("Woke up from sleep")

    else:
      self.__logger.debug("Skipping sleep: timeoutSec=%r seconds", timeoutSec)

    return


  def __enter__(self):
    """ [Context Manager protocol method] Allows an EventLoop instance to be
    used in a "with" statement for automatic closing regardless of exceptions

    Parameters:
    ------------------------------------------------------------------------
    retval:     self.
    """
    return self


  def __exit__(self, exc_type, exc_val, exc_tb):
    """ [Context Manager protocol method] Allows an EventLoop instance to be
    used in a "with" statement for automatic closing regardless of exceptions
    """
    self.close()

    # return False so that exception, if any, will not be suppressed
    return False




#####################################################################################
def test():

  import time
  import logging

  logger = logging.getLogger("test")

  with EventLoop() as loop:

    # First, try running the loop w/o any EventMonitors - this should
    # trigger an AssertionError exception
    gotAssertionError = False
    try:
      loop.run()
    except AssertionError:
      gotAssertionError = True

    assert gotAssertionError


    # Now, do the normal stuff...

    def quarterSecHandler(monitor):
      print "QUARTER-SEC HANDLER: ", time.time()
      return True

    def oneSecHandler(monitor):
      print "ONE-SEC HANDLER: ", time.time()
      return True

    def tenSecHandler(monitor):
      print "TEN-SEC HANDLER: ", time.time()
      return True

    def twentySecOneShotHandler(monitor):
      print "TWENTY-SEC ONE-SHOT HANDLER: ", time.time()
      return False

    def halfMinQuitHandler(monitor):
      print "HALF-MIN-QUIT-HANDLER: STOPPING EVENT LOOP..."
      monitor.peekLoop().stopLoop()
      return False

    def oneShotBootstrapHandler(monitor):
      print "ONE-SHOT-BOOTSTRAP-HANDLER: registering halfMinQuitTimer"
      monitor.peekLoop().registerEventMonitors(halfMinQuitTimer)
      return

    halfMinQuitTimer = Timer(minutes=0.5, handler=halfMinQuitHandler, logger=logger)

    bootstrapMonitor = Poll(handler=oneShotBootstrapHandler, logger=logger)
    loop.registerEventMonitors(bootstrapMonitor)

    quarterSecTimer = Timer(sec=0.25, handler=quarterSecHandler, logger=logger)
    loop.registerEventMonitors(quarterSecTimer)

    oneSecTimer = Timer(sec=1, handler=oneSecHandler, logger=logger)
    loop.registerEventMonitors(oneSecTimer)

    anotherOneSecTimer = Timer(sec=1, handler=oneSecHandler, logger=logger)
    loop.registerEventMonitors(anotherOneSecTimer)

    tenSecTimer = Timer(sec=10, handler=tenSecHandler, logger=logger)
    loop.registerEventMonitors(tenSecTimer)

    twentySecOneShotTimer = Timer(sec=20, handler=twentySecOneShotHandler, logger=logger)
    loop.registerEventMonitors(twentySecOneShotTimer)

    loop.run()


  print "\nPASSED"

  return




#####################################################################################
if __name__ == "__main__":
  test()