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
This file contains the MultiInspector class, a GUI that contains an
inspector and a controls for switching among inspectors and among regions.
"""

from __future__ import with_statement

import os
import sys
import traceback
import math
import re
from functools import partial

import wx
from enthought.traits.api import HasTraits, Any, Instance, Enum, CStr, Tuple
from enthought.traits.ui.api import View, Item, Group, Handler, EnumEditor
from enthought.traits.ui.menu import NoButtons
import PIL
import numpy

from nupic.analysis.runtimelistener import RuntimeListener, listenersDisabled
from nupic.ui.enthought import ImageEditor, GridSelectorEditor
from nupic.ui.wx import createMenu
from nupic.analysis.inspectors.region.RegionInspector import RegionInspector
from nupic.analysis.inspectors.network import *
from nupic.image import deserializeImage
from nupic.support.resources import getNTAImage
from nupic.analysis import _inspect

from nupic.engine import Network, Region

class MultiInspectorPanel(wx.Panel):

  """
  MultiInspectorPanel is a simple wx container for a region selector and a region
  inspector. When the user picks a region, the inspector is updated to reflect
  it.

  To create a standalone inspector window, create a MultiInspector. To embed
  the inspector in an existing window, create a MultiInspectorPanel.
  """

  def __init__(self, element, parent=None, embed=True, showRun=True,
               mode='mini', lockedMode=False, networkInspectorName=None,
               tabIndex=None):
    """
    element -- A RuntimeElement.
    parent -- Parent for this wx.Panel.
    embed -- Whether this panel is embedded in another window (besides the
      NetworkInspector window).
    showRun -- Whether to show the RuntimeInspector in the dropdown.
    mode -- Initial mode for selecting inspectors, either 'mini' or 'grid'.
    lockedMode -- Whether the mode can be changed.
    networkInspectorName -- Stirng representation of a NetworkInspector
      subclass, used as the initial inspector.
    tabIndex -- Which tab to show initially (RegionInspectors only).
    """

    if not isinstance(element, Network) and not isinstance(element, Region):
      raise TypeError("'element' must be a Network")

    # Try to retrieve the NetworkInspector subclass from the provided name
    networkInspector = None
    if networkInspectorName:
      for n in networkInspectors:
        if str(n) == networkInspectorName:
          networkInspector = n
          break
      else:
        raise ValueError("Invalid networkInspectorName -- not found")

    if isinstance(element, Network):
      self.root = element
    else:
      self.root = element.network
    assert isinstance(self.root, Network)
    self.element = element
    self.parent = parent
    self.embed = embed
    self.showRun = showRun
    self.mode = mode
    self.lockedMode = lockedMode

    wx.Panel.__init__(self, parent)

    self.miniSelector = self.miniSelectorControl = None
    self.gridSelector = self.gridSelectorControl = None
    self.inspector = self.inspectorControl = None

    # Create the widgets
    if not self.lockedMode:
      # Expand and contract bitmaps
      self.expandBitmap = wx.Bitmap(getNTAImage('left_arrow_22_21'))
      self.contractBitmap = wx.Bitmap(getNTAImage('right_arrow_22_21'))
      self.switchControl = wx.StaticBitmap(self, bitmap=self.expandBitmap)
    # Inspector button
    inspectorBitmap = wx.Bitmap(getNTAImage('magnifying_glass_24_24'))
    self.inspectorBitmap = wx.StaticBitmap(self, bitmap=inspectorBitmap)
    wx.EVT_LEFT_DOWN(self.inspectorBitmap, self.launchInspector)
    # Region type
    self.regionTypeText = wx.StaticText(self)
    font = self.GetFont()
    font.SetWeight(wx.FONTWEIGHT_BOLD)
    font.SetPointSize(font.GetPointSize() + 2)
    self.regionTypeText.SetFont(font)

    # Create the mini selector (optionally telling it to load a particular
    #  inspector, if a NetworkInspector was specified)
    item = None
    if networkInspector:
      shortName, longName = networkInspector.getNames()
      item = shortName
    self.miniSelector = MiniSelector(parent=self, element=self.element,
      replaceInspector=self.replaceInspector, replaceRegion=self.replaceRegion,
      showRun=self.showRun, item=item)
    self.miniSelectorControl = self.miniSelector.edit_traits(parent=self,
      view=self.miniSelector.view, kind='panel').control

    # Create the inspector
    self.createInspector()

    # Set up sizers
    self.mainSizer = wx.BoxSizer(wx.VERTICAL)
    self.headerSizer = wx.BoxSizer(wx.HORIZONTAL)
    self.mainSizer.AddSpacer(3)
    if not self.lockedMode:
      # Add the expand button
      self.headerSizer.Add(self.switchControl,
        flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT, border=6)
    else:
      # Add a spacer in place of the expand button
      self.headerSizer.AddSpacer(28)
    self.headerSizer.AddStretchSpacer()
    # Add the region type
    self.headerSizer.Add(self.regionTypeText, flag=wx.ALIGN_CENTER_VERTICAL)
    self.headerSizer.AddStretchSpacer()
    # Add the inspector button
    self.headerSizer.Add(self.inspectorBitmap,
      flag=wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, border=6)
    # Add the horizontal sizer
    self.mainSizer.Add(self.headerSizer, flag=wx.EXPAND)
    self.mainSizer.AddSpacer(3)
    # Add the selector
    self.mainSizer.Add(self.miniSelectorControl, flag=wx.ALIGN_CENTER)
    # Add the inspector
    self.mainSizer.Add(self.inspectorControl, flag=wx.EXPAND)

    if self.mode == 'grid' or not self.lockedMode:
      # Create the grid selector
      self.gridSelector = GridSelector(parent=self, element=self.element,
        replaceInspector=self.replaceInspector, replaceRegion=self.replaceRegion,
        showRun=self.showRun)
      self.gridSelectorControl = self.gridSelector.edit_traits(parent=self,
        view=self.gridSelector.view, kind='panel').control
      # Create the grid sizer
      self.gridSizer = wx.BoxSizer(wx.HORIZONTAL)
      self.gridSizer.Add(self.gridSelectorControl, flag=wx.LEFT|wx.TOP,
        border=3)
      self.gridSizer.Add(self.mainSizer)
      # Tell the selectors about each other
      self.miniSelector.companion = self.gridSelector
      self.gridSelector.companion = self.miniSelector

    # Set the sizer
    if self.mode == 'mini':
      self.switchToMini()
    elif self.mode == 'grid':
      self.switchToGrid(register=False)
    else:
      raise ValueError("mode must be 'mini' or 'grid'")

    if tabIndex:
      # Change the initial tab in the inspector, but wait until the window is
      #  showing or it won't work
      wx.CallAfter(partial(self.setTab, tabIndex))

  def setTab(self, index):
    """
    Call _setTab on the handler to switch the tab programmatically.

    Must be done after the window is showing, because the _setTab method is
    not available until then (see nupic.ui.enthought.patches).
    """

    self.inspector.handler._setTab(index)

  def createInspector(self, icon=None):
    """Create the inspector for this region."""

    self.inspector = self.miniSelector.createInspector(self.setTitle)
    self.inspectorControl = \
      self.inspector.edit_traits(parent=self, kind='panel').control
    self.setTitle()
    name = self.miniSelector.getName()
    if isinstance(self.inspector, RegionInspector):
      region = self.root.regions[name]
      regionType = region.type
      if '.' in regionType:
        regionType = 'py.' + regionType.split('.')[-1]
      self.regionTypeText.SetLabel(regionType)
    else:
      self.regionTypeText.SetLabel(name)
    self.unregister = self.inspector.unregister

  def replaceInspector(self):
    """Replace the existing inspector with a new one for this region."""

    self.inspector.unregister()
    oldInspectorControl = self.inspectorControl
    self.mainSizer.Hide(oldInspectorControl)
    #from dbgp.client import brk; brk(port=9011)
    self.createInspector()
    self.mainSizer.Replace(oldInspectorControl, self.inspectorControl)
    self.mainSizer.Layout()

    #if not self.embed:
    #  self.GetParent().SetClientSize(self.GetBestSize())

  def replaceRegion(self):
    """Keep the same inspector but switch regions."""

    if isinstance(self.inspector, RegionInspector):
      self.inspector.switchRegion(self.miniSelector.getRegion())
    self.setTitle()

  def setTitle(self, tabName=None):
    """Set the window title (if the window is not embedded)."""

    if not self.embed:
      name = self.miniSelector.getName()
      if isinstance(self.inspector, RegionInspector):
        if not tabName:
          tabName = self.inspector.getTabName()
        name += " - " + tabName
      self.parent.SetTitle(name)

  def getRegion(self):
    """Get the current region, or return None if the item is not a region."""
    if not isinstance(self.inspector, RegionInspector):
      return None
    name = self.miniSelector.getName()
    return self.root.regions[name]

  def enterPrompt(self):
    """Enter the interactive prompt."""

    _inspect.enterPrompt(self.root, self.getRegion(), self.inspector)

  def launchInspector(self, evt=None):
    """Launch another inspector."""

    # Launch a new inspector
    element = self.getRegion()
    if not element:
      element = self.root
    #if isinstance(element, Region):
    #  container = element.getContainer()
    #  if container.getTypeName() == 'Region':
    #    # Get the 0th element in this region
    #    element = container.getElement(0)
    # Create the inspector
    MultiInspector(element=element, showRun=self.showRun)

  def switchToMini(self, evt=None):
    """Switch to the mini selector."""

    self.mode = 'mini'

    if not self.lockedMode:
      self.switchControl.SetBitmap(self.expandBitmap)
      wx.EVT_LEFT_DOWN(self.switchControl, self.switchToGrid)

    if self.gridSelector:
      # Hide the grid selector
      self.gridSelectorControl.Hide()
      # Unregister the grid selector
      self.gridSelector.unregister()
      # Tell the mini selector not to update the grid selector
      self.miniSelector.companion = None

    # Set the sizer
    self.SetSizer(self.mainSizer, deleteOld=False)
    self.mainSizer.Layout()
    if not self.embed:
      self.GetParent().SetClientSize(self.GetBestSize())

  def switchToGrid(self, evt=None, register=True):
    """Switch to the grid selector."""

    self.mode = 'grid'

    if not self.lockedMode:
      self.switchControl.SetBitmap(self.contractBitmap)
      wx.EVT_LEFT_DOWN(self.switchControl, self.switchToMini)

    # Show the grid selector
    self.gridSelectorControl.Show()

    if register:
      # Register the grid selector
      self.gridSelector.register()
      # Tell the mini selector to update the grid selector
      self.miniSelector.companion = self.gridSelector

    # Set the grid selector item and indices from the mini selector
    self.gridSelector.switchFromCompanion(item=self.miniSelector.item,
      indices=self.miniSelector.getIndices())

    # Set the sizer
    self.SetSizer(self.gridSizer, deleteOld=False)
    self.gridSizer.Layout()
    if not self.embed:
      self.GetParent().SetClientSize(self.GetBestSize())


class MultiInspector(wx.Frame):

  """
  MultiInspector wraps a MultiInspectorPanel into a wx.Frame.

  To create a standalone inspector window, create a MultiInspector. To embed
  the inspector in an existing window, create a MultiInspectorPanel.
  """

  def __init__(self, element, showRun=True, mode='mini', icon=None,
               networkInspectorName=None, tabIndex=None):
    """
    element -- A RuntimeElement.
    showRun -- Whether to show the RuntimeInspector in the dropdown.
    mode -- Initial mode for selecting inspectors, either 'mini' or 'grid'.
    networkInspectorName -- Stirng representation of a NetworkInspector
      subclass, used as the initial inspector.
    tabIndex -- Which tab to show initially (RegionInspectors only).
    """

    focused = wx.Window.FindFocus()

    wx.Frame.__init__(self, None,
      style=wx.DEFAULT_FRAME_STYLE - wx.MAXIMIZE_BOX - wx.RESIZE_BORDER)

    if icon:
      self.SetIcon(icon)

    self.panel = MultiInspectorPanel(element=element, parent=self,
                                     embed=False, showRun=showRun, mode=mode,
                                     networkInspectorName=networkInspectorName,
                                     tabIndex=tabIndex)

    self.SetClientSize(self.panel.GetBestSize())

    menuBar, self.menuItemIDs = _inspect.createInspectorMenus()
    self.SetMenuBar(menuBar)
    self.Bind(wx.EVT_MENU, self.onMenu)

    if not focused:
      # This is the first window - center it
      self.Center()
    else:
      # Stagger the window
      while focused.GetParent():
        focused = focused.GetParent()
      self.MoveXY(*[p + 15 for p in focused.GetPositionTuple()])
    self.Show(True)

    self.Bind(wx.EVT_CLOSE, self.close)

  def close(self, evt):
    """Unregister the inspector from the global list of listeners."""

    self.panel.inspector.unregister()
    if hasattr(self.panel.inspector, 'close'):
      self.panel.inspector.close()
    if isinstance(self.panel.inspector, VisionRuntimeInspector):
      globals().pop('runtimeInspectorActive')
    if self.panel.gridSelector and self.panel.gridSelectorControl.IsShown():
      # Unregister the grid selector
      self.panel.gridSelector.unregister()
    evt.Skip()

  def onMenu(self, event):
    """Handle custom menu events for inspectors, such as saving the config."""

    menuItemID = event.GetId()
    name = self.menuItemIDs.get(menuItemID, None)
    if name:
      if name == 'loadConfig':
        _inspect.loadInspectors(self.panel.root)
      elif name == 'saveConfig':
        _inspect.saveInspectors()
      elif name == 'enterPrompt':
        self.panel.enterPrompt()
      elif name == 'enableLogging':
        _inspect.enableLogging()
      else:
        raise RuntimeError('Unknown command name: %s' % name)
    else:
      event.Skip()

class Selector(HasTraits):

  """
  Base class for objects that allow the user to pick an inspector.

  Currently does not support nested networks, nested regions, or regions with
  more than three dimensions.
  """

  excludedRegionTypes = ['PassThroughRegion']

  def __init__(self, parent, element, replaceInspector, replaceRegion,
               showRun=True, item=None):
    """
    item -- Name of the inspector or element to show initially.
    """

    self.parent = parent
    if isinstance(element, Network):
      self.root = element
    else:
      self.root = element.network

    assert isinstance(self.root, Network)

    self.replaceInspector = replaceInspector
    self.replaceRegion = replaceRegion
    self.showRun = showRun
    self.companion = None

    itemName = indices = None

    #if element.getTypeName() != 'Network':
    #  # Get the region and indices from the element name
    #  schema = element.getSchema()
    #  if element.getTypeName() == 'Region':
    #    itemName = element.getName()
    #  else:
    #    if '[' not in element.getName():
    #      itemName = element.getName()
    #    else:
    #      itemName = schema.getContainer().getName()
    #      indices = map(int, schema.getRelativeName()[1:-1].split(','))
    #else:
    #  # Start with the sensor
    #  for e in self.root:
    #    if e.getPhase().startswith('0') and e.getTypeName() == 'Region':
    #      itemName = e.getName()
    #      break
    #  else:
    #    raise RuntimeError("Could not find phase 0 region to use as initial region")

    if isinstance(element, Network):
      regions = element.regions
      for name in regions:
        if element.getPhases(name) == (0,):
          itemName = name
          break
    elif isinstance(element, Region):
      itemName = element.name
    else:
      raise Exception('Unknown element type: ' + str(type(element)))

    # Filter out unwanted elements
    allowedNames = []
    regions = self.root.regions
    for name, region in regions.items():
      if region.type not in self.excludedRegionTypes:
        allowedNames.append(name)

    # Sort regions by phase
    def phaseCompare(net, r1, r2):
      return net.getPhases(r1)[0] - net.getPhases(r2)[0]

    allowedNames = sorted(allowedNames, cmp=partial(phaseCompare, self.root))

    # Add a divider
    allowedNames.append('-----')

    # Add all network inspectors, marking incompatible ones with an asterisk
    self.networkInspectors = []
    for networkInspector in networkInspectors:
      shortName, longName = networkInspector.getNames()
      if shortName == 'run' and not self.showRun:
        continue
      if not networkInspector.isNetworkSupported(element):
        shortName += ' *'
      self.networkInspectors.append((networkInspector, shortName, longName))
      allowedNames.append(shortName)

    # Add the allowed elements to the enum
    self.add_trait('item', Enum(*allowedNames))
    if itemName:
      self.item = itemName

    r = regions[self.item]
    dimensions = self.getDimensions(r)
    for i in xrange(3):
      indexName = 'index%d' % i
      self.add_trait(indexName + '_enum', Any)
      self.add_trait(indexName, CStr)
      setattr(self, indexName, '0')
      if len(dimensions) > i:
        setattr(self, indexName + '_enum', Enum(*range(dimensions[i])))
        if indices and len(indices) > i:
          setattr(self, indexName, str(indices[i]))
      else:
        setattr(self, indexName + '_enum', Enum(['0']))

    # Create conditions used in the view
    self.numDimensionsString = \
      'len(object.getDimensions())'
    self.runtimeElementCondition = \
      'object.item in object.root.getElementNames() and '

    self.createView()

    if item:
      self.item = item

  def createInspector(self, setTitle):
    """
    Create an inspector for the selected item.

    setTitle -- Called with the tab name when the tab changes (for region
      inspectors only, not network inspectors).
    """
    region = self.getRegion()
    if region:
      # Region inspector
      inspectorClass = getInspectorClass(region)
      inspector = inspectorClass(parent=self.parent, region=region,
                                          tabChangeCallback=setTitle)
    else:
      # Network inspector
      i = [n[1] for n in self.networkInspectors].index(self.item)
      inspector = \
        self.networkInspectors[i][0](parent=self.parent, network=self.root)

    inspector.update()
    return inspector

  def getDimensions(self, element=None):
    """
    Get the dimensions of the selected region.

    In MRG networks, the first two dimensions vary based on the third.
    """
    if not element:
      if not self.isRegionInspector():
        return []

      element = self.root.regions[self.item]

    if element.spec.singleNodeOnly:
      return []
    else:
      return element.dimensions

    #
    #if element.getTypeName() == 'Region':
    #  return tuple()
    #layoutInfo = element.getLayoutInfo()
    #dimensions = eval(layoutInfo['dimensions'])
    #layoutType = layoutInfo['layoutType']
    #if layoutType == 'Multi-resolution Grid Layout':
    #  if type(dimensions[0]) is not tuple:
    #    dimensions = (dimensions,)
    #  # Latter two dimensions are set by first (scale)
    #  if hasattr(self, 'index0'):
    #    scale = min(int(self.index0), len(dimensions)-1)
    #  else:
    #    scale = 0
    #  dimensions = (len(dimensions),) + dimensions[scale]
    #elif layoutType == 'Multi-dimensional Layout':
    #  pass
    #else:
    #  raise RuntimeError("Unknown layout type: %s" % layoutType)
    #if type(dimensions) is int:
    #  dimensions = (dimensions,)
    #return dimensions

  def getRegion(self):
    """Retrieve the selected region."""

    if not self.isRegionInspector():
      return None

    name = self.getName()
    return self.root.regions[name]

  def getName(self):
    """Get the name of the selected item."""

    return self.item
    #if self.isRegionInspector():
    #  # Region inspector
    #  dimensions = self.getDimensions()
    #  if not dimensions:
    #    name = self.item
    #  else:
    #    indices = []
    #    for i in xrange(len(dimensions)):
    #      indices.append(getattr(self, 'index%d' % i))
    #    indicesName = '[%s]' % ','.join([str(x) for x in indices])
    #    name = self.item + indicesName
    #  return name
    #else:
    #  # Network inspector
    #  i = [n[1] for n in self.networkInspectors].index(self.item)
    #  return self.networkInspectors[i][2]

  def getIndices(self):
    """Get the current indices."""

    if not self.isRegionInspector():
      return []
    indices = []
    dimensions = self.getDimensions()
    for i, dimension in enumerate(dimensions):
      index = getattr(self, 'index%d' % i)
      indices.append(index)
    return indices

  def switchItem(self):
    """Update the selector to reflect the newly-selected item."""

    if self.isRegionInspector():
      self.switchDimensions()
    if self.companion:
      self.companion.switchFromCompanion(item=self.item,
                                         indices=self.getIndices())
    self.replaceInspector()

  def switchDimensions(self, updateScale=True):
    """Update the selector when the region's dimensions change."""

    dimensions = self.getDimensions()
    for i, dimension in enumerate(dimensions):
      if not updateScale and i == 0:
        continue
      indexName = 'index%d' % i
      oldIndex = int(getattr(self, indexName))
      setattr(self, indexName + '_enum',
        Enum(*[str(d) for d in range(dimension)]))
      index = min(oldIndex, dimension - 1)
      setattr(self, indexName, str(index))

  def switchRegion(self):
    """Update the selector to reflect the newly-selected region."""

    if self.companion:
      self.companion.switchFromCompanion(indices=self.getIndices())
    self.replaceRegion()

  def switchFromCompanion(self, item=None, indices=None):
    """Update the selector to reflect the item in the companion selector."""

    if item:
      self.item = item
    if indices:
      for i, index in enumerate(indices):
        if getattr(self, 'index%d' % i) != index:
          setattr(self, 'index%d' % i, str(index))

  def isRegionInspector(self):
    return self.item not in [i[1] for i in self.networkInspectors]

  def isMRG(self):
    return False

  def getMaxDimensions(self):
    """Return the maximum number of dimensions for all region in the network."""

    maxDimensions = 0

    regions = self.root.regions
    for r in regions.values():
      dimCount = len(r.getDimensions())
      if dimCount > maxDimensions:
        maxDimensions = dimCount

    #iterator = self.root.getElementIterator()
    #while True:
    #  try:
    #    element = iterator.next()
    #  except StopIteration:
    #    break
    #  maxDimensions = max(maxDimensions, len(self.getDimensions(element)))
    return maxDimensions


class SelectorHandler(Handler):

  """
  A handler that switches the inspector and updates the name and indices in
  the selector when the selection changes. It also ensures that there are
  never multiple RuntimeInspectors active simultaneously.
  """

  def setattr(self, info, object, name, value):
    """Update the inspector when the selected region changes."""

    if name == 'item':
      if value.startswith('-'):
        # Divider
        return
      elif value == 'run':
        # Check that no other RuntimeInspectors are registered
        if 'runtimeInspectorActive' in globals():
          print "Only one RuntimeInspector may be active at a time"
          return
        else:
          globals()['runtimeInspectorActive'] = True
      elif value != 'run' and object.item == 'run':
        globals().pop('runtimeInspectorActive')
      else:
        # Check if it is a NetworkInspector
        for inspector, shortName, longName in object.networkInspectors:
          if value == shortName:
            supported = inspector.isNetworkSupported(object.root)
            if supported is not True:
              if supported and isinstance(supported, basestring):
                # Show a dialog explaining why the inspector is not supported
                dialog = wx.MessageDialog(None,
                                          supported,
                                          '"%s" not supported' % longName,
                                          wx.OK | wx.ICON_ERROR)
                dialog.ShowModal()
                dialog.Destroy()
              return
            break

    Handler.setattr(self, info, object, name, value)
    if info.ui.history:
      info.ui.history.clear()
    try:
      if name == 'item':
        # Switch inspectors
        object.switchItem()
      elif name == 'index0':
        # Switch dimensions if MRG
        object.switchDimensions(updateScale=False)
      if name != 'item':
        # Switch region with existing inspector
        object.switchRegion()
    except:
      traceback.print_exc()
      os._exit(1)


class MiniSelector(Selector):

  """
  This selector has dropdown lists for the item and indices.
  """

  def createView(self):
    """Set up a view for the traits."""
    indexItems = [
      Item('index0', editor=EnumEditor(name='index0_enum'),
        visible_when=self.runtimeElementCondition
        + self.numDimensionsString + '>=1'),
      Item('index1', editor=EnumEditor(name='index1_enum'),
        visible_when=self.runtimeElementCondition
        + self.numDimensionsString + '>=2'),
      Item('index2', editor=EnumEditor(name='index2_enum'),
        visible_when=self.runtimeElementCondition
        + self.numDimensionsString + '>=3'),
    ]

    items = [Item('item')]
    #items = [Item('item')] + indexItems[:self.getMaxDimensions()]

    self.view = View(
      Group(*items, **dict(orientation='horizontal', show_labels=False)),
      buttons=NoButtons,
      handler=SelectorHandler
    )


class GridSelector(Selector, RuntimeListener):

  """
  This selector has a grid for selecting indices from two dimensions.
  It also shows a view of the sensor output and highlights the current
  region's receptive field, if there is an ImageSensor in the network.
  """

  # Parameters
  largestSide = 160

  # Traits
  grid = Tuple((0, 0, 1, 1))  # (row, col, nRows, nCols)
  sensorLocationImage = Instance(PIL.Image.Image)
  gaborLocationImage = Instance(PIL.Image.Image)

  def __init__(self, *args, **kwargs):

    Selector.__init__(self, *args, **kwargs)
    RuntimeListener.__init__(self)

    self.outputImage = None
    self.setDimensions()
    self.update()

  def findRegions(self):
    """Look for an ImageSensor and GaborRegion."""

    self.sensor = self.gabor = None
    for e in self.root.regions.values():
      if 'ImageSensor' in e.type or 'PictureSensor' in e.type:
        self.sensor = e
      elif 'GaborRegion' in e.type:
        self.gabor = e
      if self.sensor and self.gabor:
        break

  def _getSensor(self):
    try:
      return self.sensor.getSelf()
    except:
      return self.sensor

  def createView(self):
    """Set up a view for the traits."""

    # Look for an ImageSensor/PictureSensor and a GaborRegion
    self.findRegions()

    # Calculate the height of the grid and images
    if self.sensor:
      ss = self._getSensor()
      ratio = ss.width / ss.height
      if ratio > 1:
        # Image is wider than it is tall
        self.width = self.largestSide
        self.height = int(round(self.largestSide / ratio))
      else:
        # Image is taller than it is wide
        self.height = self.largestSide
        self.width = int(round(self.largestSide * ratio))
    else:
      self.height = self.width = self.largestSide

    items = [Item('grid',
                  editor=GridSelectorEditor(width=self.width,
                                            height=self.height),
                  visible_when=self.runtimeElementCondition)]
    if self.sensor:
      items.append(Item('sensorLocationImage',
                        editor=ImageEditor(width=self.width,
                                           height=self.height),
                        visible_when=self.runtimeElementCondition))
      if self.gabor:
        items.append(Item('gaborLocationImage',
                          editor=ImageEditor(width=self.width,
                                             height=self.height),
                          visible_when=self.runtimeElementCondition))

    self.view = View(
      Group(*items, **dict(show_labels=False)),
      buttons=NoButtons,
      handler=SelectorHandler
    )

  def setDimensions(self):
    """Set the grid dimensions."""

    if self.isRegionInspector():
      dimensions = self.getDimensions()
      if dimensions:
        if len(dimensions) == 1:
          # MD layout (1 dimension)
          self.grid = (0, 0, dimensions[0], 1)
        elif len(dimensions) == 2:
          # MD layout (2 dimensions)
          self.grid = (0, 0, dimensions[0], dimensions[1])
        else:
          # MRG layout (3 dimensions)
          self.grid = (0, 0, dimensions[1], dimensions[2])
      else:
        self.grid = (0, 0, 1, 1)
    else:
      self.grid = (0, 0, 1, 1)

  def update(self, methodName=None, elementName=None, args=None, kwargs=None):
    """
    Called automatically in response to runtime engine activity.

    Extra arguments (optional) are passed by the wrapped methods,
    and they can be used to avoid unnecessary updating.

    methodName -- RuntimeElement class method that was called.
    elementName -- RuntimeElement name.
    args -- Positional arguments passed to the method.
    kwargs -- Keyword arguments passed to the method.
    """
    ss = self._getSensor()
    if not ss:  # If there is only a grid, no updates are necessary
      return

    ns = self.sensor.spec

    # Try to get the output image
    if 'outputImage' in ns.parameters:
      if hasattr(ss, 'outputImage'):
        # Image sensor takes this branch.
        outputImage = ss.outputImage
      else:
        # Picture sensor takes this branch.
        outputImage = ss.getParameter('outputImage')
      if outputImage:
        if isinstance(outputImage, str):
          self.outputImage = deserializeImage(outputImage)
        if isinstance(outputImage, PIL.Image._ImageCrop):
          self.outputImage = outputImage
        else:
          # If the output image is multi-scale, pick the first image (largest)
          if hasattr(outputImage, '__iter__'):
            imgStr = ss.getParameter('outputImage')[0]
          else:
            imgStr = ss.getParameter('outputImage')
          if imgStr:
            # Valid image
            self.outputImage = deserializeImage(imgStr)

    if self.gabor:
      # Retrieve the largest composite Gabor image
      with listenersDisabled:
        g = self.gabor.getSelf()
        s = g.getResponseImages(whichScale=0)
        self.gaborImage = deserializeImage(s)

    self.drawLocationImages()

  def drawLocationImages(self):
    """Draw the location on the sensor and gabor images."""

    ss = self._getSensor()
    scale = self.width / float(ss.width)

    if not self.outputImage:
      # Create blank images
      sensorLocationImage = PIL.Image.new('RGB', (self.width, self.height),
                                          (255, 255, 255))
      gaborLocationImage = sensorLocationImage.copy()
    else:
      # Copy the output image to the sensor location image
      sensorLocationImage = self.outputImage.convert('RGB')
      if self.gabor:
        # Copy the composite gabor image to the gabor location image
        gaborLocationImage = self.gaborImage.copy()
      if self.gabor:
        if sensorLocationImage.size != gaborLocationImage.size:
          # Gabor image is constrained
          # Compute offsets
          offsetX = \
            (sensorLocationImage.size[0] - gaborLocationImage.size[0]) / 2
          offsetY = \
            (sensorLocationImage.size[1] - gaborLocationImage.size[1]) / 2
          gaborWidth  = int(round(scale * gaborLocationImage.size[0]))
          gaborHeight = int(round(scale * gaborLocationImage.size[1]))
        else:
          gaborWidth, gaborHeight = self.width, self.height
      # Scale the images
      sensorLocationImage = sensorLocationImage.resize((self.width,
                                                        self.height))
      if self.gabor:
        gaborLocationImage = \
          gaborLocationImage.resize((gaborWidth, gaborHeight))

    if self.grid != (0, 0, 1, 1):
      # ??????????? Ignore getReceptiveFields for now
      #unscaledRF = getReceptiveFields(self.getRegion(), gui=True)[0]
      unscaledRF = False
      if unscaledRF:
        rf = [int(round(scale * r)) for r in unscaledRF]
        sensorLocationImageDraw = PIL.ImageDraw.Draw(sensorLocationImage)
        # Draw a 3-pixel-wide rectangle
        sensorLocationImageDraw.rectangle((rf[0]-1, rf[1]-1, rf[2], rf[3]),
          outline='blue')
        sensorLocationImageDraw.rectangle((rf[0]-2, rf[1]-2, rf[2]+1, rf[3]+1),
          outline='blue')
        sensorLocationImageDraw.rectangle((rf[0]-3, rf[1]-3, rf[2]+2, rf[3]+2),
          outline='blue')
        if self.gabor:
          if sensorLocationImage.size != gaborLocationImage.size:
            unscaledGaborRF = (unscaledRF[0] - offsetX,
                               unscaledRF[1] - offsetY,
                               unscaledRF[2] - offsetX,
                               unscaledRF[3] - offsetY)
          else:
            unscaledGaborRF = unscaledRF
          rf = [int(round(scale * r)) for r in unscaledGaborRF]
          gaborLocationImageDraw = PIL.ImageDraw.Draw(gaborLocationImage)
          # Draw a 3-pixel-wide rectangle
          gaborLocationImageDraw.rectangle((rf[0]-1, rf[1]-1, rf[2], rf[3]),
            outline='blue')
          gaborLocationImageDraw.rectangle((rf[0]-2, rf[1]-2, rf[2]+1, rf[3]+1),
            outline='blue')
          gaborLocationImageDraw.rectangle((rf[0]-3, rf[1]-3, rf[2]+2, rf[3]+2),
            outline='blue')
    self.sensorLocationImage = sensorLocationImage
    if self.gabor:
      if sensorLocationImage.size != gaborLocationImage.size:
        # Scale the offset
        offsetX = int(round(scale * offsetX))
        offsetY = int(round(scale * offsetY))
        # Pad to the full size
        newImage = PIL.Image.new('RGB',
                                 sensorLocationImage.size,
                                 (255, 255, 255))
        newImage.paste(gaborLocationImage, (offsetX, offsetY))
        gaborLocationImage = newImage
      self.gaborLocationImage = gaborLocationImage

  def switchItem(self):
    """Update the selector to reflect the newly-selected item."""

    Selector.switchItem(self)
    self.setDimensions()

  def switchFromCompanion(self, item=None, indices=None):
    """Update the selector to reflect the item in the companion selector."""

    if item:
      self.item = item
      self.setDimensions()
    if indices:
      grid = list(self.grid)
      if not self.isMRG():
        # MD layout (1 or 2 dimensions)
        for i, index in enumerate(indices):
          if getattr(self, 'index%d' % i) != index:
            grid[i] = index
      else:
        # MRG layout (3 dimensions)
        if indices[0] != self.index0:
          # Scale has changed - updated the grid
          self.index0 = indices[0]
          dimensions = self.getDimensions()
          grid[2:] = dimensions[1:]
        if self.index1 != indices[1]:
          grid[0] = indices[1]
        if self.index2 != indices[2]:
          grid[1] = indices[2]
      self.grid = tuple(grid)

  def _grid_changed(self):
    """Update the indices when the grid selection changes."""

    if not self.grid:
      return
    dimensions = self.getDimensions()
    if not self.isMRG():
      # MD layout (1 or 2 dimensions)
      if self.grid[0] != self.index0:
        self.index0 = self.grid[0]
      if self.grid[1] != self.index1:
        self.index1 = self.grid[1]
    else:
      # MRG layout (3 dimensions)
      if self.grid[0] != self.index1:
        self.index1 = self.grid[0]
      if self.grid[1] != self.index2:
        self.index2 = self.grid[1]
    if self.sensor:
      self.drawLocationImages()

def getInspectorClass(region, format='%sInspector'):
  """Find and import the appropriate region inspector for this region."""

  regionType = region.type.split('.')[-1]
  if regionType[-1] == '2':
    regionType = regionType[:-1]
  base = os.path.join(os.path.split(__file__)[0], 'region')
  moduleName = format % regionType
  className = moduleName

  modulePath = os.path.join(base, moduleName +  '.py')
  modulePath2 = os.path.join(base, moduleName + '2.py')

  # Module path 3 is for the special case of MiniPictureSensorInspector
  modulePath3 = os.path.join(base, format % (regionType + '2') + '.py')

  if os.path.exists(modulePath2):
    moduleName += '2'
  elif os.path.exists(modulePath3):
    moduleName = format % (regionType + '2')
  elif not os.path.exists(modulePath):
    # Use the default inspector
    return RegionInspector

  # Import the custom inspector
  module = __import__('nupic.analysis.inspectors.region.%s' % className,
                      fromlist=moduleName)
  return getattr(module, className)