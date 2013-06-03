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

import logging

from enthought.traits.api import HasTraits
from enthought.traits.ui.api import *
from enthought.traits.ui.menu import NoButtons
import wx

import nupic

from nupic.analysis.runtimelistener import RuntimeListener
from nupic.ui.enthought import patchEnthoughtClasses
from nupic.analysis.inspectors.region.tabs import *

class RegionInspector(HasTraits, RuntimeListener):
  """
  RegionInspector sets up an Inspector GUI from a RuntimeRegion in the tools.

  By default, RegionInspector checks all tabs in the inspectors/tabs directory,
  and uses all the ones which are compatible with the specified region.

  To create a custom inspector for a particular region type, subclass
  RegionInspector and name it after the region type (e.g. RegionTypeInspector) in
  a file of the same name. in __init__() pass your your desired list of tabs
  to RegionInspector.__init__(). It is unlikely that you will need to override
  or extend any methods, but you may wish to create custom tabs in the same file
  and include them in your tabs list.
  """
  def __init__(self, parent, region, tabChangeCallback=None, tabs=defaultTabs):

    RuntimeListener.__init__(self)

    self.parent = parent
    self.region = region
    self.tabChangeCallback = tabChangeCallback

    patchEnthoughtClasses()

    # Remove incompatible tabs
    self.tabs = [tab for tab in tabs if tab.isRegionSupported(region)]

    # Create tab instances
    self.tabs = [tab(region) for tab in self.tabs]

    # Strip titles from tab views, but save them for use as tab labels
    self.titles = []
    for tab in self.tabs:
      self.titles.append(tab.traits_view.title)
      tab.traits_view.title = ""

    # Add a trait for each tab
    for i, tab in enumerate(self.tabs):
      self.add_trait('tab%d' % i, tab)

    # Set the handler for each tab if it is not specified
    for tab in self.tabs:
      if not tab.traits_view.handler:
        tab.traits_view.handler = RegionInspectorTabHandler

    # Create the view
    items = [Item('tab%d' % i,
                  editor=InstanceEditor(view=tab.traits_view),
                  style='custom',
                  show_label=False,
                  springy=True)
             for i, tab in enumerate(self.tabs)]
    if len(self.tabs) == 1:
      args = [items[0]]
    else:
      args = [Group(item, label=self.titles[i]) for i, item in enumerate(items)]
    self.handler = RegionInspectorHandler()
    kwargs = dict(handler=self.handler,
                  buttons=NoButtons,
                  title=self.region.getName())
    self.traits_view = View(*args, **kwargs)

    self.activeTabIndex = 0
    self.tabNeedsUpdate = [True] * len(self.tabs)
    self.tabNeedsSwitch = [False] * len(self.tabs)
    self.initCompleted = True

  def edit_traits(self, *args, **kwargs):
    """Extend to set up the view and bind key events."""

    if self.parent:
      # Allow the inspector to handle key events
      self.parent.Bind(wx.EVT_CHAR, self.handleKeyEvent)
      self.parent.SetFocusFromKbd()

    # Set the view to the traits_view attribute if it is not specified
    # Necessary because traits_view is created as an instance attribute
    # at runtime, rather than as part of the class definition
    if not kwargs.get('view', None):
      kwargs['view'] = self.traits_view

    # Set handler and buttons if they are not specified
    if not kwargs['view'].handler:
      kwargs['view'].handler = RegionInspectorHandler
    if not kwargs['view'].buttons:
      kwargs['view'].buttons = NoButtons

    if self.parent:
      # Inspector is being embedded - don't show the title
      self.traits_view.title = ""

    #if 'level1' in self.region.getName():
    #  from dbgp.client import brk; brk(port=9011)

    return HasTraits.edit_traits(self, *args, **kwargs)

  def update(self, methodName=None, elementName=None, args=None, kwargs=None):
    """
    Called automatically in response to runtime engine activity.

    Extra arguments (optional) are passed by the wrapped methods,
    and they can be used to avoid unnecessary updating.

    @param methodName -- Class method that was called.
    @param elementName -- Name of RuntimeElement.
    @param args -- Positional arguments passed to the method.
    @param kwargs -- Keyword arguments passed to the method.
    """
    # If we haven't finished initialization, skip this. This update method can be
    #  called as a result of doing an execute method on a region during an
    #  isRegionSupported() call while setting up the tabs for example, and we're not
    #  ready to do anthing regarding updates at this point yet.
    if not hasattr(self, 'initCompleted'):
      return

    # Update only the active tab
    logging.debug("Updating tab %d" % self.activeTabIndex)
    #if 'level1' in self.region.getName():
    #  from dbgp.client import brk; brk(port=9011)
    self.tabs[self.activeTabIndex].update(methodName=methodName,
                                          elementName=elementName,
                                          args=args,
                                          kwargs=kwargs)

    if methodName:
      # Method was called by the runtime engine, so all other tabs need updates
      self.tabNeedsUpdate = [True] * len(self.tabNeedsUpdate)
    self.tabNeedsUpdate[self.activeTabIndex] = False

  def switchRegion(self, region=None):
    """Switch to a different RuntimeRegion of the same type."""

    if region:
      self.region = region

    # Switch only the active tab
    logging.debug("Switching tab %d to region %s" % (self.activeTabIndex,
                                                   self.region.getName()))
    self.tabs[self.activeTabIndex].switchRegion(self.region)

    if region:
      # User is switching regions, so all other tabs need to switch
      self.tabNeedsSwitch = [True] * len(self.tabNeedsSwitch)
    self.tabNeedsSwitch[self.activeTabIndex] = False
    self.tabNeedsUpdate[self.activeTabIndex] = False

  def tabChanged(self, index):
    """Handle the user selecting a new tab."""

    logging.debug("Switching to tab %d" % index)
    self.tabs[self.activeTabIndex].setVisible(False)
    self.activeTabIndex = index
    self.tabs[self.activeTabIndex].setVisible(True)

    if self.tabNeedsSwitch[self.activeTabIndex]:
      # Region needs to switch regions (which also updates)
      self.switchRegion()
    else:
      if self.tabNeedsUpdate[self.activeTabIndex]:
        # Region needs to update (but not switch regions)
        self.update()

    if self.tabChangeCallback:
      self.tabChangeCallback(self.getTabName())

  def handleKeyEvent(self, evt):
    """Handle a key event."""

    self.tabs[self.activeTabIndex].handleKeyEvent(evt)

  def getTabName(self):
    """Get the name of the selected tab."""

    return self.titles[self.activeTabIndex]


class RegionInspectorHandler(Handler):

  def tabChanged(self, info, index):
    """Handle the user selecting the tab with the specified index."""

    info.object.tabChanged(index)