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

from enthought.traits.api import CStr
from enthought.traits.ui.api import Item, Group, View

from nupic.analysis.inspectors.region.RegionInspector import RegionInspector
from nupic.analysis.inspectors.region.tabs import *
from nupic.ui.enthought import ImageEditor

import nupic

def _getParameter(region, name):
  return region.getSelf().getParameter(name)

class _MiniImagesTab(RegionInspectorTab):

  """
  The MiniImagesTab shows just the output image. It's used in the vision GUIs.
  The full ImagesTab subclasses from it and adds all the other traits for
  the standalone PictureSensorInspector. However, the update method in this
  class handles the updating for all the extra traits too (if they're present).
  """

  # Parameters
  largeSize = 224

  def __init__(self, region):
    RegionInspectorTab.__init__(self, region)

    self._addTraits()
    self._createView()

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

    self.outputImage = _getParameter(self.region, 'outputImage')

  def _addTraits(self):
    """Add traits for the mini tab."""

    self.add_trait('outputImage', CStr)

  def _createView(self):
    """Set up a view for the traits."""

    self.traits_view = View(
      Item('outputImage', show_label=False,
        editor=ImageEditor(width=self.largeSize,
                           height=self.largeSize)),
      title='Images'
    )


class _ImagesTab(_MiniImagesTab):

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

    _MiniImagesTab.update(self)
    self.locationImage = _getParameter(self.region, 'locationImage')

  def _addTraits(self):
    """Add traits for the mini tab."""

    _MiniImagesTab._addTraits(self)
    self.add_trait('locationImage', CStr)

  def _createView(self):
    """Set up a view for the traits."""

    self.traits_view = View(
      Group(
        Item('outputImage', show_label=False,
          editor=ImageEditor(width=self.largeSize,
                             height=self.largeSize,
                             caption='Output Image'),
          style='custom'),
        Item('locationImage', show_label=False,
          editor=ImageEditor(width=self.largeSize,
                             height=self.largeSize,
                             caption='Location Image'),
          style='custom'),
        orientation='horizontal'
      ),
      title='Images'
    )


class _PictureSensorParametersTab(ParametersTab):
  """ParametersTab subclass that allows us to remove nonsense parameters."""
  def __init__(self, *args, **kwargs):
    # These don't make sense to show generically...
    self.disallowedParameters = [
      'locationImage',
      'outputImage',
    ]
    super(_PictureSensorParametersTab, self).__init__(*args, **kwargs)


class PictureSensorInspector(RegionInspector):
  def __init__(self, parent, region, tabChangeCallback=None):
    tabs = [_ImagesTab, _PictureSensorParametersTab, HelpTab]
    RegionInspector.__init__(self, parent, region, tabChangeCallback, tabs)