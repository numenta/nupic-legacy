#!/usr/bin/env python
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
This module contains the inspect function and other tools for wx windows that
use inspectors.
"""

import sys
import cPickle as pickle

from nupic.engine import Network

def inspect(element, showRun=True, icon=None):
  """
  Launch an Inspector for the provided element.

  element -- A network, region or a path to a network directory.
  showRun -- Whether to show the RuntimeInspector in the dropdown, which lets
             the user run the network.
  """
  if isinstance(element, basestring):
    element = Network(element)
  else:
    assert isinstance(element, Network)

  if len(element.regions) == 0:
    raise Exception('Unable to inspect an empty network')

  # Network must be initialized before it can be inspected
  element.initialize()

  from wx import GetApp, PySimpleApp

  if GetApp():
    useApp = True
  else:
    useApp = False

  from nupic.analysis.inspectors.MultiInspector import MultiInspector

  if not useApp:
    app = PySimpleApp()

  inspector = MultiInspector(element=element, showRun=showRun, icon=icon)

  if not useApp:
    app.MainLoop()
    app.Destroy()
  else:
    return inspector


def createInspectorMenus():
  """
  Create the menus that are useful for any frame that uses inspectors.

  Returns the wx.MenuBar and a dictionary mapping menu item IDs to the names
  used below (e.g. 'loadConfig').

  To use with your frame that wraps and launches inspectors, call this function
  in your constructor. Take the menu bar returned and use self.SetMenuBar.
  Store the menu item ID dictionary and save it for your event handler.

  Bind EVT_MENU. In your menu event handler, check if the event ID is in the
  dictionary. If so, call the appropriate function from this file.
  """

  import wx
  from nupic.ui.wx import createMenu

  # Menus to create for inspectors, used by MultiInspector and GUIs (as they
  #  are the two outer frames that can contain inspector panels)
  menus = [
    ('File',
      dict(text='Load Configuration', name='loadConfig', keys='Ctrl-O'),
      dict(text='Save Configuration', name='saveConfig', keys='Ctrl-S'),
    ),
    ('Options',
      dict(text='Enter Interactive Prompt', name='enterPrompt', keys='Ctrl-I'),
      dict(text='Enable Debug Logging', name='enableLogging', keys='Ctrl-L'),
    )
  ]

  menuBar = wx.MenuBar()
  allMenuItemIDs = {}
  for menuData in menus:
    menuName = menuData[0]
    menuData = menuData[1:]
    menu, menuItemIDs = createMenu(menuData)
    menuBar.Append(menu, menuName)
    allMenuItemIDs.update(menuItemIDs)

  return menuBar, allMenuItemIDs


def loadInspectors(root, path=None, showRun=True):
  """
  Load configuration of inspector windows from a file and recreate.

  root -- RuntimeNetwork (used as the base for launching new inspectors).
  path -- Path to .pkl file (if not present, user will be prompted).
  showRun -- Whether to show the RuntimeInspector in the dropdown, which lets
             the user run the network.
  """

  import wx
  from nupic.analysis.inspectors.MultiInspector import MultiInspector

  if not path:
    dialog = wx.FileDialog(None,
                           wildcard="Inspector config files (*.pkl)|*.pkl")
    ret = dialog.ShowModal()
    path = dialog.GetPath()
    dialog.Destroy()
    if ret != wx.ID_OK:
      return

  data = pickle.load(open(path))
  missingCount = 0
  # Filter out any elements that aren't in this network
  # ???????
  #for d in data[:]:
  #  if d['element'] and not root.hasElement(d['element']):
  #    data.remove(d)
  #    missingCount += 1
  # Create all the other inspectors
  for d in data:
    # Create the inspector
    if d['element']:
      # ???????????
      ## Region inspector
      #element = root.getElement(d['element'])
      pass
    else:
      # Network inspector
      element = root
    i = MultiInspector(element=element,
                       mode=d['mode'],
                       showRun=showRun,
                       networkInspectorName=d['networkInspectorName'],
                       tabIndex=d['tabIndex'])
    # Set the window position
    i.SetPosition(d['position'])
  # Alert the user if some inspectors weren't regenerated
  if missingCount:
    wx.MessageBox("%d inspectors weren't opened because their element names "
                  "aren't in this network." % missingCount)


def saveInspectors(path=None):
  """
  Save configuration of inspector windows to a file.

  path -- Path to .pkl file (if not present, user will be prompted).
  """

  import wx
  from nupic.analysis.inspectors.MultiInspector import MultiInspector

  if not path:
    dialog = wx.FileDialog(None,
                           wildcard="Inspector config files (*.pkl)|*.pkl",
                           style=wx.FD_SAVE)
    ret = dialog.ShowModal()
    path = dialog.GetPath()
    dialog.Destroy()
    if ret != wx.ID_OK:
      return
    path = dialog.GetPath()
    if not path.endswith('.pkl'):
      path += '.pkl'

  data = []
  for w in wx.GetTopLevelWindows():
    if not isinstance(w, MultiInspector):
      continue  # Ignore IPython windows and the Vision GUIs
    if w.panel.miniSelector.isRegionInspector():
      # Region inspector
      element = w.panel.getRegion().getName()
      tabIndex = w.panel.inspector.activeTabIndex
      networkInspectorName = None
    else:
      # Network inspector
      element = None
      tabIndex = None
      networkInspectorName = str(w.panel.inspector.__class__)
    data.append(dict(element=element,
                     tabIndex=tabIndex,
                     networkInspectorName=networkInspectorName,
                     position=w.GetPosition(),
                     mode=w.panel.mode))
  pickle.dump(data, open(path, 'w'))


def enterPrompt(net, region=None, insp=None):
  """Enter the interactive prompt."""

  # TODO: handle case where only one of region and insp are provided (although
  #  no one is using this function that way yet)
  if (not region and not insp):
    sys.stdout.write("\nLaunching interactive shell prompt..."
                     "\nThe variable 'net' contains the network object.")
  else:
    sys.stdout.write("\nLaunching interactive shell prompt..."
                     "\nThe variable 'net', 'region', and 'insp' contain the "
                     "network, region, and inspector objects.")

  argv = sys.argv[:]
  sys.argv = []
  from IPython.Shell import IPShellEmbed; IPShellEmbed()()
  sys.argv = argv


def enableLogging():
  """Turn on debug-level logging."""

  import logging
  logging.getLogger().setLevel(logging.DEBUG)