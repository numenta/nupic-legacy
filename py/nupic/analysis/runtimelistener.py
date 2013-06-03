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

"""
This file contains RuntimeListener, a class which registers for automatic
updates from the runtime engine.
"""

import time
import logging
import traceback
from warnings import warn
from functools import update_wrapper

from nupic.engine import Network, Region

# Methods which should trigger updates
updateMethods = ('run', 'executeCommand', 'setParameter')

# Methods which should be monitored but which should not trigger updates
monitorMethods = ('getParameter', 'getInputData', 'getOutputData')

# Methods that should not be logged, even though they may trigger updates
ignoredMethods = ('run',)

# Arguments/values for these commands/parameters won't be printed
suppressedNames = ('loadSerializedImage', 'categoryInfo')


# Allows RuntimeElement methods to be called without triggering updates
# Example usage:
# from nupic.analysis import listenersDisabled
# with listenersDisabled:
#   node.execute(...)
listenersEnabled = True
class ListenersDisabled(object):
  def __enter__(self):
    globals()['listenersEnabled'] = False
  def __exit__(self, exc_type, exc_val, exc_tb):
    globals()['listenersEnabled'] = True
listenersDisabled = ListenersDisabled()


# Can be called manually to force an update
def updateListeners(methodName=None, elementName=None, args=None, kwargs=None):
  """Update all RuntimeListeners."""

  if 'listeners' in globals() and globals()['listenersEnabled']:
    for listener in globals()['listeners']:
      try:
        listener.update(methodName, elementName, args, kwargs)
      except Exception, e:
        if 'PyDeadObjectError' in str(type(e)):
          # Listener has been closed
          warn("Listener is dead but has not yet been unregistered")
          listeners.remove(listener)
        else:
          traceback.print_exc()


class RuntimeListener(object):

  """Class that registers for automatic updates from the runtime engine."""

  # RuntimeElement classes to wrap for automatic updates
  wrappedClasses = (Network, Region)

  def __init__(self):

    self.register()

  def register(self):
    """Register this listener in the global list of listeners."""

    logging.debug("Registering listener: " + str(self))
    # Add this listener to the global dictionary
    if 'listeners' in globals():
      if self in globals()['listeners']:
        warn("Tried to register listener which is already registered")
      else:
        globals()['listeners'].append(self)
    else:
      globals()['listeners'] = [self]
      # Wrap the RuntimeElement class methods to update the listeners
      self._wrapMethods()
    logging.debug("Listeners: " + str(globals().get('listeners', [])))

  def unregister(self):
    """Unregister this listener from the global list of listeners."""

    logging.debug("Unregistering listener: " + str(self))
    try:
      globals().get('listeners', []).remove(self)
    except ValueError:
      warn("Tried to unregister listener which has already been removed")
      return
    logging.debug("Listeners: " + str(globals().get('listeners', [])))
    if not globals()['listeners']:
      # No listeners remain - unwrap the methods
      globals().pop('listeners')
      self._unwrapMethods()

  def update(self, methodName=None, elementName=None, args=None, kwargs=None):
    """
    Called automatically in response to runtime engine activity.

    Extra arguments (optional) are passed by the wrapped methods,
    and they can be used to avoid unnecessary updating.

    methodName -- Name of the RuntimeElement method that was called.
    elementName -- Name of the target RuntimeElement.
    args -- Positional arguments passed to the method.
    kwargs -- Keyword arguments passed to the method.
    """

    raise NotImplementedError("RuntimeListeners must override update()")

  def _wrapMethods(self):
    """Wrap all class methods to automatically update the listeners."""

    for elementType in self.wrappedClasses:
      for methodName in updateMethods + monitorMethods:
        if hasattr(elementType, methodName):
          #print elementType, methodName
          method = getattr(elementType, methodName)
          setattr(elementType, methodName, self._wrapMethod(method))
          # Store the original method as _method
          setattr(elementType, '_' + methodName, method)


  def _unwrapMethods(self):
    """Revert to the original versions of all the class methods."""

    for elementType in self.wrappedClasses:
      for methodName in updateMethods + monitorMethods:
        if hasattr(elementType, '_' + methodName):
          method = getattr(elementType, '_' + methodName)
          setattr(elementType, methodName, method)

  def _wrapMethod(self, method):
    """Wrap a class method to automatically update the listeners."""

    def wrappedMethod(*args, **kwargs):
      methodName = str(method).split('.')[-1][:-1]
      element = args[0]
      if isinstance(element, Network):
        elementName = 'Network'
      else:
        elementName = element.name

      if methodName not in ignoredMethods:
        # Log a string representation of this method
        if len(args) == 1 or args[1] not in suppressedNames:
          argsStrs = map(repr, args[1:])
          kwargsStrs = ['%s=%s' for key, value in kwargs.iteritems()]
          methodStr = '%s.%s(%s)' % (elementName, methodName,
                                     ', '.join(argsStrs + kwargsStrs))
        else:
          methodStr = '%s.%s(%s, [other arguments/values suppressed])' \
                    % (elementName, methodName, repr(args[1]))
        logging.debug(methodStr)
        # Start the timer
        t = time.time()

      # Call the method
      returnVal = method(*args, **kwargs)
      #try:
      #  returnVal = method(*args, **kwargs)
      #except Exception, e:
      #  print e
      #  from dbgp.client import brk; brk(port=9011)
      #  print

      if methodName not in ignoredMethods:
        # Report the run time
        logging.debug('  Completed in %dms' % int((time.time() - t) * 1000))

      # If the method is one which should trigger updates, update the listeners
      if methodName in globals()['updateMethods']:
        updateListeners(methodName, elementName, args[1:], kwargs)

      return returnVal

    return update_wrapper(wrappedMethod, method)