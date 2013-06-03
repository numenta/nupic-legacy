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

from PIL import Image
from enthought.traits.api import *
from enthought.traits.ui.api import *

from nupic.analysis.inspectors.region.RegionInspector import RegionInspector
from nupic.analysis.inspectors.region.tabs import *
from nupic.ui.enthought import ImageEditor, FileOrDirectoryEditor, alignCenter

def _getSelf(region):
  return region.getSelf()

def _getOutput(region, name):
  a = region.getOutputData(name)
  return [float(x) for x in a]

def _getDescription(spec):
  return spec.description

def _getParameters(region):
  return dict((k, v) for (k,v) in region.spec.parameters.items()
           if (not k.startswith('dense') and k != 'self'))

class _MiniImagesTab(RegionInspectorTab):

  """
  The MiniImagesTab shows just the output image. It's used in the vision GUIs.
  The full ImagesTab subclasses from it and adds all the other traits for
  the standalone ImageSensorInspector. However, the update method in this
  class handles the updating for all the extra traits too (if they're present).
  """

  # Parameters
  smallSize = 128
  largeSize = 224
  maxPathLength = 24

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
    region = _getSelf(self.region)
    if hasattr(self, 'locationImage'):
      # Full inspector
      prevImageInfo = region.getParameter('prevImageInfo')
      if prevImageInfo:
        # Update imagePath
        if prevImageInfo['imagePath']:
          self.imagePath = self._truncatePath(prevImageInfo['imagePath'])
        # Update category
        self.category = '%d ("%s")' % (prevImageInfo['categoryIndex'],
                                       prevImageInfo['categoryName'])
        # Update resetOut
        resetOut = _getOutput(self.region, 'resetOut')
        self.resetOut = str(bool(resetOut[0]))
        # Update bboxOut
        bboxOut = _getOutput(self.region, 'bboxOut')
        self.bboxOut = str(tuple([int(x) for x in bboxOut]))

      # Create the numImages string
      numImages = region.getParameter('numImages')
      if not numImages:
        self.numImagesString = "No images loaded"
      elif numImages == 1:
        self.numImagesString = "1 image loaded"
      else:
        self.numImagesString = "%d images loaded" % numImages

      # locationImage is always a single image
      self.locationImage = region.getParameter('locationImage')

    # Skip the output image if there is no location image
    if not hasattr(self, 'locationImage') or self.locationImage != 'None':
      # outputImage could be a list of strings when using multiple scales
      outputImage = region.getParameter('outputImage')
      if isinstance(outputImage, list):
        self.outputImage = outputImage[0]
      else:
        self.outputImage = outputImage
    else:
      self.outputImage = None

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

  def _truncatePath(self, path):
    """Truncate the beginning of the path so that it is under maxPathLength."""

    if len(path) <= self.maxPathLength:
      return path
    path, newPath = os.path.split(path)
    while True:
      path, directory = os.path.split(path)
      testPath = os.path.join(directory, newPath)
      if len(testPath) > self.maxPathLength:
        if newPath > self.maxPathLength and not '/' in newPath:
          newPath = newPath[-self.maxPathLength-3:]
          return "...%s" % newPath
        return os.path.join("...", newPath)
      newPath = testPath

class _ImagesTab(_MiniImagesTab):

  def _addTraits(self):
    """Add additional traits for the full tab."""

    _MiniImagesTab._addTraits(self)

    self.add_trait('loadSingleImage', File)
    self.add_trait('loadMultipleImages', Directory)
    self.add_trait('numImagesString', Str)
    self.add_trait('imagePath', CStr)
    self.add_trait('category', Str)
    self.add_trait('resetOut', Str)
    self.add_trait('bboxOut', Str)
    self.add_trait('locationImage', CStr)

  def _createView(self):
    """Set up a view for the traits."""

    loadGroup = Group(
      Group(
        Item('loadSingleImage',
          editor=FileOrDirectoryEditor(buttonLabel="Load single...")),
        Item('loadMultipleImages',
          editor=FileOrDirectoryEditor(directory=True,
            buttonLabel="Load multiple...")),
        show_labels=False,
        orientation='horizontal'
      ),
      Item('numImagesString', style='readonly'),
      label='Load images',
      show_border=True,
      show_labels=False
    )

    imagesGroup = Group(
      Group(
        Item('imagePath', style='readonly', label='image'),
        Item('category', style='readonly', label='category'),
        Item('resetOut', style='readonly', label='reset'),
        Item('bboxOut', style='readonly', label='bbox')
      ),
      Group(
        Item('locationImage',
          editor=ImageEditor(width=self.smallSize, height=self.smallSize,
          caption='Location Image'), style='custom'),
        Item('outputImage',
          editor=ImageEditor(width=self.smallSize, height=self.smallSize,
          caption='Output Image'), style='custom'),
        show_labels=False,
        orientation='horizontal'
      ),
      label='Previous compute',
      show_labels=False,
      show_border=True
    )

    self.traits_view = View(
      Group(loadGroup, imagesGroup),
      title='Images'
    )


class _ParametersTab(ParametersTab):

  def _addTraits(self):
    """Use the Spec to add parameters as traits."""

    parameters = {
      'width': Int,
      'height': Int,
      'depth': Int,
      'enabledWidth': Int,
      'enabledHeight': Int,
      'memoryLimit': Int,
      'logText': CBool,
      'logOutputImages': CBool,
      'logLocationImages': CBool,
      'logOriginalImages': CBool,
      'logFilteredImages': CBool,
    }
    self.parameters = {}
    #regionspec = getSpec(self.region)
    #for name, trait in parameters.iteritems():
    #  description = regionspec['parameters'][name]['description']
    #  self.add_trait(name, trait(label=name, desc=description))
    #  self.parameters[name] = regionspec['parameters'][name]

    specs = _getParameters(self.region)
    for name, trait in parameters.iteritems():
      spec = specs[name]
      description = _getDescription(spec)
      self.add_trait(name, trait(label=name, desc=description))
      self.parameters[name] = spec

  def _createView(self):
    """Set up the view for the traits."""

    self.traits_view = View(
      Group(
        Group(
          Item('width', style='readonly'),
          Item('height', style='readonly'),
          Item('depth', style='readonly'),
          Item('enabledWidth', width=-40),
          Item('enabledHeight', width=-40),
          label='Dimensions',
          show_border=True
        ),
        Group(
          Item('memoryLimit', width=-50),
          label='Miscellaneous',
          show_border=True
        ),
        Group(
          Group(
            Group(
              Item('logOriginalImages', label='Original images'),
              Item('logLocationImages', label='Location images'),
              Item('logText', label='Text log')
            ),
            Group(
              Item('logOutputImages', label='Output images'),
              Item('logFilteredImages', label='Filtered images')
            ),
            orientation='horizontal'
          ),
          label='Logging',
          show_border=True
        ),
      ),
      title='Parameters'
    )


class _AlphaTab(RegionInspectorTab):

  def __init__(self, region):
    RegionInspectorTab.__init__(self, region)

    self.width = self.region.getParameter('width')
    self.height = self.region.getParameter('height')

    self.add_trait('image', Instance(Image.Image))
    self.add_trait('mode', Str('erode'))

    self.traits_view = View(
      Group(alignCenter(Item('mode', style='readonly')),
            alignCenter(Item('image',
                             editor=ImageEditor(width=self.width,
                                                height=self.height,
                                                caption='Alpha Image'),
                             show_label=False))),
      title='Alpha'
    )

  def update(self, methodName=None, elementName=None, args=None, kwargs=None):
    """
    Passed through by RegionInspector only if this tab is visible.

    Extra arguments (optional) are passed by the wrapped methods,
    and they can be used to avoid unnecessary updating.

    @param methodName -- Class method that was called.
    @param elementName -- Name of RuntimeElement.
    @param args -- Positional arguments passed to the method.
    @param kwargs -- Keyword arguments passed to the method.
    """

    # Get the alpha output from the sensor
    alpha = _getOutput(self.region, 'alphaOut')
    if len(alpha) == 1:
      # No alpha output hooked up
      return

    # Fix top-left indicator if present
    if alpha[0] < 0:
      self.mode = 'dilate'
      alpha[0] = -alpha[0] - 1
    else:
      self.mode = 'erode'

    # Convert to numpy, then to PIL
    alphaNumpy = numpy.array(alpha, dtype=numpy.uint8)
    image = Image.new('L', (self.width, self.height))
    image.putdata(alphaNumpy)
    self.image = image

class ImageSensorInspector(RegionInspector):
  def __init__(self, parent, region, tabChangeCallback=None):
    tabs = [_ImagesTab, _ParametersTab, _AlphaTab, HelpTab]
    RegionInspector.__init__(self, parent, region, tabChangeCallback, tabs)