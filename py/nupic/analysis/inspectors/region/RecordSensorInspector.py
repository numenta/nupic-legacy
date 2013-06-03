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
from nupic.data.filesource import FileSource

def _getParameters(Region):
  return dict((k, v) for (k,v) in Region.spec.parameters.items()
           if (not k.startswith('dense') and k != 'self'))


class _FileTabHandler(RegionInspectorTabHandler):
  """
  """
  def __init__(self, *args, **kw):
    Handler.__init__(self, *args, **kw)

  def setattr(self, info, object, name, value):
    """Update the inspector when the selected region changes."""
    ss = object.region.getSelf()
    ds = ss.dataSource
    #from dbgp.client import brk; brk(port=9011)
    if name == 'filePath':
      assert False
      from dbgp.client import brk; brk(port=9011)
    elif name == 'loadFile':
      ds.open(value)
      object.filePath = value
    else:
      RegionInspectorTabHandler.setattr(self, info, object, name, value)

class _FileTab(RegionInspectorTab):
  def __init__(self, Region):
    RegionInspectorTab.__init__(self, Region)

    self.filePath = None

    self._addTraits()
    self._createView()

  def update(self, methodName=None, elementName=None, args=None, kwargs=None):

    s = self.region.getSelf()
    ds = s.dataSource
    self.filePath = ds.filename
    #print '_FileTab.update(), self.filePath=', self.filePath

  def _addTraits(self):
    """Add additional traits for the full tab."""

    self.add_trait('loadFile', File)
    self.add_trait('filePath', CStr)
    self.add_trait('category', Str)

  def _createView(self):
    """Set up a view for the traits."""

    loadGroup = Group(
      Group(
        Item('loadFile',
          editor=FileOrDirectoryEditor(buttonLabel="Load file...")),
        Item('filePath', style='readonly'),
        show_labels=False,
        orientation='horizontal'
        ),
      label='Load file',
      show_border=True,
      show_labels=False
    )

    self.traits_view = View(
      Group(loadGroup),
      title='File',
      handler=_FileTabHandler
    )

class _OutputTab(RegionInspectorTab):

  """
  The RecordTab shows just the output record and recent history.
  """

  def __init__(self, Region):
    RegionInspectorTab.__init__(self, Region)


    # Cache the output buffers in local numpy arrays
    ## self.categoryOutBuffer = self.region.getOutputData("categoryOut")
    ## assert self.categoryOutBuffer.shape == (1,)

    self.resetOutBuffer = self.region.getOutputData("resetOut")
    assert self.resetOutBuffer.shape == (1,)

    self.sequenceIdOutBuffer = self.region.getOutputData("sequenceIdOut")
    assert self.sequenceIdOutBuffer.shape == (1,)


    self.dataOutBuffer = self.region.getOutputData("dataOut")

    # Cache the encoder because we will need it at each update
    self.encoder = self.region.getSelf().encoder

    # Allocate this array once, instead of at each update
    self.formattedDataWidth= self.encoder.getDisplayWidth()

    # Encode an empty array to get just the separator bits
    # We'll use the separator bits to construct the image.
    z = numpy.zeros((self.encoder.getWidth(),), dtype='uint8')
    self.separatorBits = numpy.zeros((self.formattedDataWidth,), dtype='uint8')
    self.encoder.formatBits(z, self.separatorBits, scale=255, blank=255)

    self.historyCount = 4;
    black = Image.fromarray(numpy.zeros((5,self.formattedDataWidth, 3), dtype='uint8'),'RGB')
    self.history = [black] * self.historyCount

    self._addTraits()
    self._createView()

  def _addTraits(self):
    """Add additional traits for the full tab."""
    # self.add_trait('loadSingleImage', File)
    # self.add_trait('loadMultipleImages', Directory)
    # self.add_trait('numImagesString', Str)
    # self.add_trait('imagePath', CStr)
    ## self.add_trait('category', Str)
    self.add_trait('input', Str)
    self.add_trait('reset', Str)
    self.add_trait('sequenceId', Str)
    for i in range(self.historyCount +1):
      self.add_trait('dataOutImage%d' % i, Instance(Image.Image))
    self.add_trait('field', Str)
    self.add_trait('fieldOffset', Int)
    # self.add_trait('resetOut', Str)
    # self.add_trait('bboxOut', Str)
    # self.add_trait('locationImage', CStr)
    # self.add_trait('outputImage', CStr)


  def onMotion(self, x, y, mouseDown):
    if x == -1:
      return

    # print "%d %d %s" % (x, y, mouseDown)
    # ignore the y value -- only the x position matters
    (self.field, self.fieldOffset) =  self.encoder.encodedBitDescription(x, formatted=True)


  def _createView(self):
    """Set up a view for the traits."""


    outputGroup = Group(
      Group(
        Item('input', style='readonly', label='input'),
        # Item('imagePath', style='readonly', label='image'),
        # Item('category', style='readonly', label='category'),
        Item('reset', style='readonly', label='reset'),
        Item('sequenceId', style='readonly', label='sequenceId'),
      ),
      Group(
        Item('field', style='readonly', label='field'),
        Item('fieldOffset', style='readonly', label='offset')
      ),
      Group(
        Item('dataOutImage0',
             editor=ImageEditor(caption='Output', height=20, width=self.formattedDataWidth*5,
                                wantMagnifier=True, interpolate=False, onMotion=self.onMotion),
             style='custom'),
        Item('dataOutImage1',
             editor=ImageEditor(caption='Output @ t-1', height=20, width=self.formattedDataWidth*5,
                                wantMagnifier=True, interpolate=False, onMotion=self.onMotion),
             style='custom'),
        Item('dataOutImage2',
             editor=ImageEditor(caption='Output @ t-2', height=20, width=self.formattedDataWidth*5,
                                wantMagnifier=True, interpolate=False, onMotion=self.onMotion),
             style='custom'),
        Item('dataOutImage3',
             editor=ImageEditor(caption='Output @ t-3', height=20, width=self.formattedDataWidth*5,
                                wantMagnifier=True, interpolate=False, onMotion=self.onMotion),
             style='custom'),
        Item('dataOutImage4',
             editor=ImageEditor(caption='Output @ t-4', height=20, width=self.formattedDataWidth*5,
                                wantMagnifier=True, interpolate=False, onMotion=self.onMotion),
             style='custom'),

        show_labels=False,
        orientation='vertical'
      ),
      label='Previous compute',
      show_labels=False,
      show_border=True
    )

    self.traits_view = View(
      outputGroup,
      title='Output'
    )

  def updateHistory(self):
    for i in range(self.historyCount, 0, -1):
      setattr(self, 'dataOutImage%d' % i, getattr(self, 'dataOutImage%d' % (i-1)))

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

    # Make these values available to the inspector
    ## self.category = self.categoryOutBuffer[0]
    s = self.region.getSelf()
    self.input = s.encoder.decodedToStr(s.encoder.decode(self.dataOutBuffer))
    self.sequenceId = str(self.sequenceIdOutBuffer[0])
    self.reset = str(self.resetOutBuffer[0])

    # Convert dataOut to an image for the ImageEditor

    # Create an image from the formatter bits
    # onColor = 0x00FFFFFF # white
    # separatorColor = 0x00FF00FF # red + blue = purple


    # Array from which we form the image
    # Image is 5 pixels high to make it easier to position the mouse
    formattedDataOut = numpy.zeros((5,self.formattedDataWidth, 3), dtype='uint8')

    # 1D array for individual colors
    fdata = numpy.zeros((self.formattedDataWidth,), dtype='uint8')

    # "on" bits are green. Separator bits are red-blue (purple)
    self.encoder.formatBits(self.dataOutBuffer, fdata, scale=255, blank=0)
    formattedDataOut[:,:,0] = self.separatorBits # R
    formattedDataOut[:,:,1] = fdata              # G
    formattedDataOut[:,:,2] = self.separatorBits # B

    self.updateHistory()
    self.dataOutImage0 = Image.fromarray(formattedDataOut,'RGB')

class _ParametersTab(ParametersTab):

  def _addTraits(self):
    """Use the Spec to add parameters as traits."""

    parameters = {
      # wcs -- from imagesensor
      # 'width': Int,
      # 'height': Int,
      # 'depth': Int,
      # 'enabledWidth': Int,
      # 'enabledHeight': Int,
      # 'memoryLimit': Int,
      # 'logText': CBool,
      # 'logOutputImages': CBool,
      # 'logLocationImages': CBool,
      # 'logOriginalImages': CBool,
      # 'logFilteredImages': CBool,
    }
    self.parameters = {}
    #Regionspec = getSpec(self.region)
    #for name, trait in parameters.iteritems():
    #  description = Regionspec['parameters'][name]['description']
    #  self.add_trait(name, trait(label=name, desc=description))
    #  self.parameters[name] = Regionspec['parameters'][name]

    specs = _getParameters(self.region)
    for name, trait in parameters.iteritems():
      spec = specs[name]
      self.add_trait(name, trait(label=name, desc=spec.description))
      self.parameters[name] = spec

  def _createView(self):
    """Set up the view for the traits."""

    self.traits_view = View(
      Group(
        Group(
          # wcs - from imagesensor
          # Item('width', style='readonly'),
          # Item('height', style='readonly'),
          # Item('depth', style='readonly'),
          # Item('enabledWidth', width=-40),
          # Item('enabledHeight', width=-40),
          # label='Dimensions',
          show_border=True
        ),
        Group(
          #Item('memoryLimit', width=-50),
          label='Miscellaneous',
          show_border=True
        ),
        Group(
          Group(
            Group(
           #   Item('logOriginalImages', label='Original images'),
           #   Item('logLocationImages', label='Location images'),
           #   Item('logText', label='Text log')
            ),
            Group(
           #   Item('logOutputImages', label='Output images'),
           #   Item('logFilteredImages', label='Filtered images')
            ),
            orientation='horizontal'
          ),
          label='Logging',
          show_border=True
        ),
      ),
      title='Parameters'
    )

class RecordSensorInspector(RegionInspector):
  def __init__(self, parent, region, tabChangeCallback=None):
    ss = region.getSelf()
    if isinstance(ss.dataSource, FileSource):
      tabs = [_OutputTab, _FileTab, _ParametersTab, HelpTab]
    else:
      tabs = [_OutputTab, _ParametersTab, HelpTab]
    RegionInspector.__init__(self, parent, region, tabChangeCallback, tabs)