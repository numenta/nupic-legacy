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

from enthought.traits.api import *
from enthought.traits.ui.api import *
import os
import PIL
import numpy

from nupic.engine import Network
from nupic.analysis.inspectors.network import NetworkInspector
from nupic.ui.enthought import alignLeft, FileOrDirectoryEditor, ImageEditor

from nupic.frameworks.vision2 import VisionUtils
from nupic.frameworks.vision2.VisionUtils import getTierName

# ----------------------------------------------------------------------
# NearestNeighbor Inspector
# ----------------------------------------------------------------------

def _getElement(network, name):
  return network.regions[name]

def _findClassifier(network):
  for r in network.regions.values():
    if 'categoriesOut' in r.spec.outputs:
      return r

  return None

def _getRegionType(network, name):
    return network.regions[name].type

def _getGaborProxy(g):
  return g.getSelf()

def _getCategoryInfo(sensor):
  s = sensor.getSelf()

  return s.getParameter('categoryInfo')

def _getSelf(region):
  return region.getSelf()

class NearestNeighborInspector(NetworkInspector):

  @staticmethod
  def isNetworkSupported(network):
    """
    Return True if the inspector is appropriate for this network. Otherwise,
    return a string specifying why the inspector is not supported.
    """
    if not isinstance(network, Network):
      return False
    # Look for a region named level1SP
    if not 'level1SP' in network.regions:
      return "This inspector requires a region named 'level1SP'."
    # Look for a classifier
    for r in network.regions.values():
      if not 'categoriesOut' in r.spec.outputs:
        continue

      if not _classifierComplies(r):
        return "This classifier is not supported."
      return True

    return "No classifier found."

  @staticmethod
  def getNames():
    """
    Return the short and long names for this inspector. The short name appears
    in the dropdown menu, and the long name is used as the window title.
    """

    return ('neighbors', 'Nearest Neighbors')

  # ----------------------------------------------------------------------
  # Class attributes
  # ----------------------------------------------------------------------

  _numNeighbors = 5
  spacer = Str

  # Traits
  mode = Enum("unfiltered", "filteredByCat", "singleProtoPerCat", label="Mode", desc="mode")
  numPrototypes  = Str
  filterOnCategory = Bool

  # Stub
  category = Enum("stubCategory0", "stubCategory1", label="Category", desc="category")
  orientation = Enum("stubOrient0", "stubOrient1", label="Gabor Orientation", desc="orientation")

  # Std image display size
  _stdDisplayWidth  = 204
  _stdDisplayHeight = 204

  # ----------------------------------------------------------------------
  # Constructor
  # ----------------------------------------------------------------------

  def __init__(self, parent, network):

    NetworkInspector.__init__(self, parent, network)

    # Find the classifier
    self.classifier = _findClassifier(network)
    if not self.classifier:
      raise RuntimeError("No classifier found (no region with 'categoriesOut')")

    # Get the categoryInfo from the sensor
    sensor = _getElement(network, 'sensor')
    self.categoryInfo = _getCategoryInfo(sensor)
    self.catNames = [cat[0] for cat in self.categoryInfo]

    # Acquire reference to the gabor region
    if 'GaborRegion' in _getRegionType(network, 'level1SP'):
      self._hasGabor = True
      self._gaborRegion = None
      self._gaborProxy = None
      gaborRegion = _getElement(network, VisionUtils.getTierName(1, network=network))
      if gaborRegion:
        self._gaborProxy = _getGaborProxy(gaborRegion)

      # Obtain gabor scales
      gaborInputDims = self._gaborProxy._inputDims
      baseWidth = float(gaborInputDims[0][1])
      self.scales = [float(dims[1])/baseWidth for dims in gaborInputDims]

      # Used to store cached gabor responses
      self._cachedResponses = {}
    else:
      self._gaborRegion = None
      self._hasGabor = False

    self.showTitle = False
    self.mode = 'unfiltered'
    self.filterOnCategory = False
    self.logDir = ""
    self._bboxes = None
    self._imageFilenames = None


    # Check if our classifier complies with the required API:
    self._compliantClassifier = _classifierComplies(self.classifier)
    if self._compliantClassifier:
      # Convert category labels to numpy
      c = _getSelf(self.classifier)
      categoryList = c.getCategoryList()
      if categoryList is None:
        categoryList = []
      self._catLabels = numpy.array(categoryList)
      self.numPrototypes = "Total Prototypes: %d" % len(self._catLabels)

    # Parameters that need to be handled with custom code in updateParameters
    customParameters = {
      'numPresentationsInLog': Str,
      'logDir': Str,
      # Used for displaying "Distance:"
      'dummy': Str
    }

    for name, trait in customParameters.iteritems():
      self.add_trait(name, trait(label=name))

    self._createDefaultImages()

    # Add traits
    if not self._hasGabor:
      availableSpaces = ['pixel']
    else:
      availableSpaces = ['pixel', 'gabor']

    for k in xrange(self._numNeighbors):
      for spaceType in availableSpaces:
        traitName = '%s%03d' % (spaceType, k)
        self.add_trait(traitName, Instance(PIL.Image.Image))
        exec "self.%s = self._missingImage" % traitName

      traitName = 'score%03d' % k
      self.add_trait(traitName, Str)
      protoScoreStr = self._makeScoreString()
      exec "self.%s = protoScoreStr" % traitName

      traitName = 'imagename%03d' % k
      self.add_trait(traitName, Str)
      imagename = ""
      exec "self.%s = imagename" % traitName

    self.createView()

  # ----------------------------------------------------------------------

  def forceUpdate(self, refreshCache=False):
    """
    Allow handler to force an update of our display
    """
    self._doUpdate(refreshCache)

  # ----------------------------------------------------------------------

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
    if methodName != 'run':
      return

    # If we haven't loaded a log directory, then there's nothing we can do
    if not self.logDir:
      return

    self._doUpdate()

  # ----------------------------------------------------------------------

  #def createViews(self, displayWidth=204, displayHeight=204):
  def createView(self, displayWidth=None, displayHeight=None):
    """
    Set up a view for the traits.
    """

    if displayWidth is None:
      displayWidth = self._stdDisplayWidth
    if displayHeight is None:
      displayHeight = self._stdDisplayHeight

    # Build category dict
    catValues = {}
    for k, catName in enumerate(self.catNames):
      catValues["cat%04d" % k] = "%d: %s" % (k, catName)
    self.catIndex = 0

    # Gabor related traits
    if self._hasGabor:
      # Get response properties
      phaseMode = self._gaborProxy._phaseMode
      if phaseMode == 'dual':
        numPhases = 2
      else:
        assert phaseMode == 'single'
        numPhases = 1
      centerSurround = self._gaborP_centerSurround
      numOrientations = self._gaborP._numOrientations

      # Build orientation dict
      numGaborOrients = self._gaborProxy.getNumPlanes()
      orientValues = {"all": "00: Composite"}
      for k in xrange(numOrientations):
        orientValues["orient%04d" % k] = "%02d: %d Degrees" % (k+1, k * 180.0/numOrientations)
      if centerSurround:
        orientValues["centerSurround"] = "%02d: Center Surround" % (numOrientations + 1)
      self._gaborOrient = 'all'

      # Build phase dict
      phaseValues = {}
      for k, phaseName in enumerate(['Positive', 'Negative'][:numPhases]):
        phaseValues[phaseName] = "%d: Phase %s" % (k+1, phaseName)
      self._gaborPhase = 0
      self._numGaborPhases = numPhases

      # Build scale dict
      scaleValues = {}
      for k, scale in enumerate(self.scales):
        scaleValues["scale%04d" % k] = "%d: Scale %.2f%%" % (k+1, 100.0 * scale)
      #self._gaborScale = scaleValues["scale0000"]
      self._gaborScale = 0
      self._numGaborScales = len(scaleValues)

    # @todo -- much of this can/should be commonized

    loadLogGroupPixel = Group(
      alignLeft(
        Item('mode', style='custom', show_label=False,
            editor=EnumEditor(cols=1, values={
              'filteredByCat':     '1: Single-category matches',
              'singleProtoPerCat': '2: Single best match per category',
              'unfiltered':        '3: Raw best matches',
            }))
      ),
      alignLeft(
        Item('category', show_label=False,
            editor=EnumEditor(values=catValues))
      ),
      alignLeft(
        Item('loadLogFile',
             show_label=False,
             editor=FileOrDirectoryEditor(buttonLabel="Load log directory...",
                                          directory=True))
      ),
      Item('numPrototypes', style='readonly'),
      label='Display Settings',
      show_border=True,
      show_labels=False,
      orientation='horizontal',
    )

    if self._hasGabor:
      if self._numGaborPhases > 1:
        if self._numGaborScales > 1:
          # Multi-phase/Multi-scale
          gaborItems = Group(Item('orientation', show_label=False,
                             editor=EnumEditor(values=orientValues)),
                             Item('phase', show_label=False,
                             editor=EnumEditor(values=phaseValues)),
                             Item('scale', show_label=False,
                             editor=EnumEditor(values=scaleValues)),
                              )
        else:
          # Multi-phase/single-scale
          gaborItems = Group(Item('orientation', show_label=False,
                             editor=EnumEditor(values=orientValues)),
                             Item('phase', show_label=False,
                             editor=EnumEditor(values=phaseValues)),
                              )
      else:
        if self._numGaborScales > 1:
          # Single-phase/Multi-scale
          gaborItems = Group(Item('orientation', show_label=False,
                             editor=EnumEditor(values=orientValues)),
                             Item('scale', show_label=False,
                             editor=EnumEditor(values=scaleValues)),
                          )
        else:
          # Single-phase/Single-scale
          gaborItems = Item('orientation', show_label=False,
                            editor=EnumEditor(values=orientValues))

      loadLogGroupGabor = Group(
        alignLeft(
          Item('mode', style='custom', show_label=False,
              editor=EnumEditor(cols=1, values={
                'filteredByCat':     '1: Single-category matches',
                'singleProtoPerCat': '2: Single best match per category',
                'unfiltered':        '3: Raw best matches',
              }))
        ),
        alignLeft(
          Item('category', show_label=False,
              editor=EnumEditor(values=catValues))
        ),
        alignLeft(
          Item('loadLogFile',
               show_label=False,
               editor=FileOrDirectoryEditor(buttonLabel="Load log directory...",
                                            directory=True))
        ),
        Item('numPrototypes', style='readonly'),
        alignLeft(
          gaborItems
          #Item('orientation', show_label=False,
          #    editor=EnumEditor(values=orientValues))
        ),
        label='Display Settings',
        show_border=True,
        show_labels=False,
        orientation='horizontal',
      )


    # Create image panes
    pixelItems = self._createImagePane('pixel', displayWidth, displayHeight)
    if self._hasGabor:
      gaborItems = self._createImagePane('gabor', displayWidth, displayHeight)

    neighborsPixelGroup = Group(pixelItems[0], pixelItems[1], pixelItems[2], pixelItems[3], pixelItems[4],
                                label="Neighbors in Pixel Space",
                                show_border=True,
                                orientation='horizontal')
    if self._hasGabor:
      neighborsGaborGroup = Group(gaborItems[0], gaborItems[1], gaborItems[2], gaborItems[3], gaborItems[4],
                                label="Neighbors in Gabor Space",
                                show_border=True,
                                orientation='horizontal')

    tabPixel = Group(loadLogGroupPixel,
                     neighborsPixelGroup,
                     label='Pixel Space')
    if self._hasGabor:
      tabGabor = Group(loadLogGroupGabor,
                     neighborsGaborGroup,
                     label='Gabor Space')

      self.traits_view = View(
        tabPixel,
        tabGabor,
        handler=NearestNeighborHandler,
      )
    else:
      self.traits_view = View(
        tabPixel,
        handler=NearestNeighborHandler,
      )


  # ----------------------------------------------------------------------
  # Private helper methods
  # ----------------------------------------------------------------------

  def _createDefaultImages(self, width=64, height=64, horzPadding=40, vertSpacing=5):

    if not self._compliantClassifier:
      warningMesg = "NON SUPPORTED CLASSIFIER"
    else:
      warningMesg = "NO LOG DIRECTORY LOADED"
    words = warningMesg.split()

    # Add up vertical height of words, and find maximum width
    w = 0
    h = 0
    self._blankImage = PIL.Image.new('L', (width, height))
    dc = PIL.ImageDraw.Draw(self._blankImage)
    for word in words:
      textSize = dc.textsize(word)
      w = max(w, textSize[0])
      h += textSize[1]

    h += vertSpacing * (len(words) + 1)
    w += 2 * horzPadding
    d = max(w, h)

    # Create blank image
    self._missingImage = PIL.Image.new('L', (d, d))
    dc = PIL.ImageDraw.Draw(self._missingImage)
    dc.rectangle([0, 0, d, d], 255)

    y = vertSpacing

    # Create image
    for word in words:
      textSize = dc.textsize(word)
      x = (d - textSize[0]) / 2
      dc.text((x, y), word)
      y += vertSpacing + textSize[1]

  # ----------------------------------------------------------------------

  def _getBestPrototypes(self,
                         numBestProtos=5,
                         mode='unfiltered', # 'filteredByCat', 'singleProtoPerCat'
                         bestProtoCategory=0):
    """
    Get 'numBestProtos' indices
    """
    c = _getSelf(self.classifier)
    # Obtain the latest full scores from the classifier
    fullScores = c.getLatestDistances()

    # HACK: RTE <===> tools bridge deserialization seems to be broken;
    #       does not return numpy array (only string) so we have
    #       to do it ourselves.
    if type(fullScores) == type(""):
      fullScores = numpy.array([float(token) for token in fullScores.split()], dtype=float)

    # Force our scores to be numpy arrays
    if type(fullScores) == type(()):
      fullScores = numpy.array(list(fullScores))

    # Convert category labels to numpy if we haven't
    # done so already
    if not hasattr(self, '_catLabels'):
      self._catLabels = numpy.array(c.getCategoryList())

    # Generate a list of non-empty category indices, if we have not done so already
    if not hasattr(self, '_nonEmptyCats'):
      self._nonEmptyCats = set(list(self._catLabels))

    # Filter on a single category
    if mode == 'filteredByCat':
      # Suppress all non-category-of-interest scores
      dummyScore = fullScores.max() + 1.0
      catScores = fullScores.copy()
      catScores[numpy.where(self._catLabels != bestProtoCategory)] = dummyScore

    elif mode == 'unfiltered':
      # Reference is good enough (not copy) since we won't modify anything
      catScores = fullScores

    # For each category, find the single best matching prototype
    if mode == 'singleProtoPerCat':
      catProtos = []
      dummyScore = fullScores.max() + 1.0
      for cat in self._nonEmptyCats:
        catScores = fullScores.copy()
        assert catScores is not None
        catScores[numpy.where(self._catLabels != cat)] = dummyScore
        protoIndex = catScores.argsort()[0]
        protoScore = catScores[protoIndex]
        catProtos += [(protoIndex, protoScore)]
      # Now sort by score
      catProtos.sort(lambda x1,x2: cmp(x1[1], x2[1]))
      bestProtos = [k for (k,v) in catProtos]
      bestProtos = numpy.array(bestProtos)

    else:
      # Ignore category labels; just find the 'numBestProtos' best matching prototypes.
      bestProtos = catScores.argsort()[:numBestProtos]

    # Pull raw scores
    protoScores = fullScores[bestProtos]

    return list(bestProtos), list(protoScores)

  # ----------------------------------------------------------------------

  def _doUpdate(self, refreshCache=True):

    # If our classifier does not support the required API then we do nothing
    if not self._compliantClassifier:
      return

    # If we haven't loaded the bbox log yet, do so now
    if not self._bboxes:
      self._bboxes = [[int(i) for i in line.split()] for line in \
                      file(os.path.join(self.logDir, "imagesensor_bbox_log.txt"), 'r').readlines()]

    # If we haven't looked up the image filenames that correspond to each training image,
    #  do that now.
    if self._imageFilenames is None:
      self._imageFilenames = self._lookupImageFilenames()

    bestProtos, protoScores = self._getBestPrototypes(numBestProtos=self._numNeighbors,
                                                      mode=self.mode,
                                                      bestProtoCategory=self.catIndex)

    numNeighbors = min(len(bestProtos), self._numNeighbors)
    for k in xrange(numNeighbors):

      # Load log image
      if self._hasGabor and self._numGaborScales > 1:
        imagePath = os.path.join(self.logDir, "output_to_network", "%09d_%02d.png" % (bestProtos[k], self._gaborScale))
      else:
        imagePath = os.path.join(self.logDir, "output_to_network", "%09d.png" % bestProtos[k])

      f = open(imagePath, 'rb')
      neighborImage = PIL.Image.open(f)
      neighborImage.load()
      f.close()
      neighborSize = neighborImage.size

      # @todo -- Cache for efficiency

      # @todo -- Relax this constraint
      #assert neighborSize[0] == neighborSize[1]

      validRegion = self._bboxes[bestProtos[k]]

      # "lazy load" of gabor region
      if self._hasGabor and not self._gaborRegion and self._gaborProxy:
        self._gaborRegion = self._gaborProxy
        self._gaborRegion._prepare()

      # Assign
      exec 'self.pixel%03d = neighborImage' % k

      # @todo -- need way of detecting if we are in "gabor tab"
      if self._gaborRegion:
        cachedResponse = None
        if not refreshCache:
          cachedResponse = self._cachedResponses[k]
        neighborGabor, self._cachedResponses[k] = \
                    self._gaborRegion.filter(neighborImage, validRegion,
                                           self._gaborOrient,
                                           self._gaborPhase,
                                           scaleIndex=self._gaborScale,
                                           cachedResponse=cachedResponse)
        exec 'self.gabor%03d = neighborGabor' % k

      # Set value of scores
      protoScoreStr = self._makeScoreString(protoScores[k])
      exec "self.score%03d = protoScoreStr" % k
      if len(self._imageFilenames) > 0:
        imagename = self._imageFilenames[bestProtos[k]]
        # keep only the filename, and 2 directories right above it
        parts = os.path.split(imagename)
        fname = parts[1]
        parts = os.path.split(parts[0])
        dir2 = parts[1]
        dir1 = os.path.split(parts[0])[1]
        imagename = "%d: " % bestProtos[k] + os.path.join(dir1, dir2, fname)
      else:
        imagename = 'Train with the "-d" option to see the filename here.'
      exec "self.imagename%03d = imagename" % k

    # Blank out leftover slots
    if numNeighbors < self._numNeighbors:
      blankImage = PIL.Image.new(mode="L", size=(self._stdDisplayWidth, self._stdDisplayHeight))
      for k in xrange(numNeighbors, self._numNeighbors):
        exec 'self.pixel%03d = blankImage' % k
        exec 'self.gabor%03d = blankImage' % k
        exec "self.score%03d = 'N/A'" % k
        exec "self.imagename%03d = 'N/A'" % k

  # ----------------------------------------------------------------------

  def _makeScoreString(self, protoScore=None):
    if protoScore:
      protoScoreStr = '%.3f' % protoScore
    else:
      protoScoreStr = 'N/A'
    return protoScoreStr

  # ----------------------------------------------------------------------

  def _createImagePane(self, spaceType, displayWidth, displayHeight):
    return [Group(Item(name='%s%03d' % (spaceType, k),
                       show_label=False,
                       editor=ImageEditor(width=displayWidth,
                                          height=displayHeight,
                                          caption='Neighbor %d' % (k+1),
                                          interpolate=False)),
                  Group(Item('dummy', style='readonly', label='Distance:'),
                        Item(name='score%03d' % k, show_label=False),
                        orientation='horizontal'),
                  Item(name='imagename%03d' % k, show_label=False),
                  orientation='vertical'
                  ) for k in xrange(self._numNeighbors)]

  # -------------------------------------------------------------------------
  def _lookupImageFilenames(self, verbose = False):
    """
    Try to find the imagesensor_log.txt file in the most recent training session directory.
    This file is generated when you train with the -d option to log the image sensor
    images. We use the information in this file to map each training image (known only by
    index) to an actual filename. This filename is displayed below the image in the
    inspector (if known).
    """

    #verbose = True

    # Get the mod date/time on the nearest neighbor log
    stats = os.stat(os.path.join(self.logDir, "imagesensor_bbox_log.txt"))
    neighborsTime = stats.st_mtime


    # Look for the most recent imagesensor_log.txt file in training session directories
    prefix = os.path.join(self.logDir, "..")
    if not os.path.exists(os.path.join(prefix, 'sessions')):
      return []

    sessions = os.listdir(os.path.join(prefix, 'sessions'))
    mostRecentLog = None
    mostRecentSessionDir = None
    mostRecentDate = 0
    for sessionDir in sessions:
      if sessionDir.startswith('.'):
        continue

      # See if there's an imagesensor log here
      logFilename = os.path.join(prefix, 'sessions', sessionDir, 'imagesensor_log',
                          'imagesensor_log.txt')
      if os.path.exists(logFilename):
        modTime = os.stat(logFilename).st_mtime
        if verbose:
          print "log file", logFilename, "has mod date", modTime
        if modTime >= mostRecentDate:
          if verbose:
            print "-> most recent is now", sessionDir
          mostRecentDate = modTime
          mostRecentLog = logFilename
          mostRecentSessionDir = os.path.join(prefix, 'sessions', sessionDir)

    # Return now if no training session found
    if mostRecentLog is None:
      return []

    # Make sure the date is close to when the nearest neighbor was generated
    diff = abs(mostRecentDate - neighborsTime)
    if diff > 15*60:   # 15 minutes "slop"
      print "The most recent imagesensor log (generated by -d) appears to be from a",
      print "different training run than the nearest neighbors log because their",
      print "modification dates differ by %d seconds." % diff
      print "In order to see the training image filenames, you must train with both -d ",
      print "and --nearest at the same time."
      return []

    # Open up the log
    if verbose:
      print "Using imagesensor log file found at:", mostRecentLog
    rawSensorLines = file(mostRecentLog, "r").readlines()
    sensorEvents = [eval(line.strip()) for line in rawSensorLines if line.strip()]

    # Read in the image path for each image that was used by the sensor to train
    #  the classifier. The general structure of the log is:
    #
    #  # Level X
    #   'loadMultipleImages'
    #   'loadSingleImage'+
    #   'seek'+
    #   'compute'+
    #   'seek'
    #  # Classifier
    #   'loadMultipleImages'
    #   'loadSingleImage'+
    #   'seek'+
    #   'compute'+
    #
    #  In general, it contains a clump of commands for each tier. Each clump contains
    #  a 'loadMultipleImages' at the start. We must find the last clump, which is the
    #  classifier.
    #
    #  Also note that when running with octopus, we will have one log for each process,
    #  but every log has the same set of 'loadSingleImages' in it - only the computes are
    #  different. Because we're only looking at the 'loadSingleImages' commands, it doesn't
    #  matter which process log we end up looking at.
    startIdx = 0
    state = None
    idx = 0
    for event in sensorEvents:
      if event[0] == 'loadMultipleImages':
        startIdx = idx
      idx += 1
    imageLoads = [event for event in sensorEvents[startIdx:] if event[0] == "loadSingleImage"]
    imageData = [image[1]['imagePath'] for image in imageLoads]

    return imageData


def _classifierComplies(classifier):
  """
  Check if our classifier supports the required nearest neighbor API.
  @returns -- True or False.
  """
  c = _getSelf(classifier)
  for requiredAPI in ['getCategoryList', 'getLatestDistances']:
    if not hasattr(c, requiredAPI):
      return False
  return True

# ----------------------------------------------------------------------
# Custom handler class for NearestNeighborInspector
# ----------------------------------------------------------------------
class NearestNeighborHandler(Handler):
  """
  A handler that updates the RuntimeRegion when the traits are updated.
  """

  # ----------------------------------------------------------------------

  def setattr(self, info, object, name, value):
    """
    Update parameters on the RuntimeRegion when they change.
    """

    if name == 'category':
      object.catIndex = int(value[3:])
      if object.mode == 'filteredByCat':
        object.forceUpdate(refreshCache=True)
      return

    if name == 'orientation':
      if value == 'all':
        object._gaborOrient = 'all'
      elif value == 'centerSurround':
        object._gaborOrient = 'centerSurround'
      else:
        object._gaborOrient = int(value[6:])
      object.forceUpdate(refreshCache=False)
      return

    elif name == 'phase':
      if value == 'Positive':
        object._gaborPhase = 0
      else:
        assert value == 'Negative'
        object._gaborPhase = 1
      object.forceUpdate(refreshCache=False)
      return

    elif name == 'scale':
      object._gaborScale = int(value[5:])
      object.forceUpdate(refreshCache=True)
      return

    Handler.setattr(self, info, object, name, value)

    if info.ui.history:
      info.ui.history.clear()

    if name == 'loadLogFile':
      object.logDir = value
      object._imageFilenames = None
      # Set blank image (if we have a compliant classifier)
      if object._compliantClassifier:
        for k in xrange(object._numNeighbors):
          for spaceType in ['pixel', 'gabor']:
            traitName = '%s%03d' % (spaceType, k)
            exec "object.%s = object._blankImage" % traitName

    if name == 'mode':
      object.forceUpdate(refreshCache=True)