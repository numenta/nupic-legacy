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

import wx
from enthought.traits.api import HasTraits, Str
from enthought.traits.ui.api import Handler
from enthought.traits.ui.menu import NoButtons

import nupic

from nupic.analysis.runtimelistener import RuntimeListener
from nupic.ui.enthought import patchEnthoughtClasses

class NetworkInspector(HasTraits, RuntimeListener):

  """
  NetworkInspector is the base class for inspectors which analyze the network
  as a whole, rather than a particular region.

  Example subclasses:
  RuntimeInspector -- run the network
  ResultsInspector -- show inference results, with images if available

  In the creation of the view, the handler is automatically set to
  NetworkInspectorHandler, and the buttons are automatically set to NoButtons,
  so these parameters only need to be specified when using custom values.
  """

  @staticmethod
  def isNetworkSupported(network):
    """
    Return True if the inspector is appropriate for this network. Otherwise,
    return a string specifying why the inspector is not supported.
    """

    return True

  @staticmethod
  def getNames():
    """
    Return the short and long names for this inspector. The short name appears
    in the dropdown menu, and the long name is used as the window title.
    """

    raise NotImplementedError("NetworkInspectors must implement getNames")

  # Traits
  spacer = Str

  def __init__(self, parent, network):

    RuntimeListener.__init__(self)

    self.parent = parent
    self.network = network

    patchEnthoughtClasses()

  def edit_traits(self, *args, **kwargs):
    """Extend to set the current view."""

    if self.parent:
      # Allow the inspector to handle key events
      self.parent.Bind(wx.EVT_CHAR, self.handleKeyEvent)

    # Set the view to the traits_view attribute if it is not specified
    # Necessary because traits_view is created as an instance attribute
    # at runtime, rather than as part of the class definition
    if not kwargs.get('view', None):
      kwargs['view'] = self.traits_view

    # Set handler and buttons if they are not specified
    if not kwargs['view'].handler:
      kwargs['view'].handler = NetworkInspectorHandler
    if not kwargs['view'].buttons:
      kwargs['view'].buttons = NoButtons

    # Remove the title if the inspector is being embedded
    if self.parent:
      self.traits_view.title = ""

    return HasTraits.edit_traits(self, *args, **kwargs)

  def update(self, methodName=None, elementName=None, args=None, kwargs=None):
    """
    Called automatically in response to runtime engine activity.

    Extra arguments (optional) are passed by the wrapped methods,
    and they can be used to avoid unnecessary updating.

    @param methodName -- RuntimeElement class method that was called.
    @param elementName -- RuntimeElement name.
    @param args -- Positional arguments passed to the method.
    @param kwargs -- Keyword arguments passed to the method.
    """

    pass

  def handleKeyEvent(self, evt):
    """
    Handle a key event.

    If an event is not handled, call the parent class to handle it.
    """

    evt.Skip()

  def close(self):
    """Called by MultiInspector upon closing."""

    pass


class NetworkInspectorHandler(Handler):

  def setattr(self, info, object, name, value):
    """Clear the automatic undo history."""

    Handler.setattr(self, info, object, name, value)
    if info.ui.history:
      info.ui.history.clear()