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
This file defines PictureSensor.
"""

# Standard imports
import sys
import math
import random
import inspect
import os
import glob
import copy

# Third-party imports
import numpy
from PIL import (Image,
                 ImageDraw,
                 PngImagePlugin)
try:
  import opencv.cvtypes as cvtypes
except:
  cvtypes = None

# Local imports
import nupic.regions
from nupic.regions.PyRegion import PyRegion, RealNumpyDType
from nupic.regions.Spec import *

#from nupic.support.getsetstate import (GetSomeVars,
#                                  CallReader,
#                                  UpdateMembers)
from nupic.research.PicturesGenerator import PicturesGenerator
from nupic.image import serializeImage

class PictureSensor(PyRegion):
  """
  PictureSensor is a companion sensor node to ImageSensor.
  Whereas ImageSensor is bitmap-centric and specializes in presenting
  large numbers of static images (already stored as files on disk) using
  various filtering operations, PictureSensor is based on vector
  graphics and dynamically generates images on the fly based on a
  small number of generative parameters.  These generative parameters
  include such generic characteristics as pattern size, line
  thickness, rotation, etc., as well as category-specific parameters
  that are associated with the details of a particular category
  (e.g., "cat head height".)

  In general, PictureSensor is designed to generate images that
  sample a fairly large number of degrees of freedom, where each
  degree of freedom is associated with a particular generative
  parameter.  Since densely and exhaustively sampling a parameter
  space of even four or five parameters is impractical, we take the
  approach of randomly exploring this parameter space; i.e., we
  slowly "morph" the generated images by varying all of the degrees
  by a small amount on each iteration.

  The precise mechanism by which PictureSensor explores ("travels through")
  this parameter space is governed by a particular "Explorer Plugin",
  which is a sub-class of the PictureSensor.PictureExplorer base class.
  Each such explorer uses a custom algorithm for generating sequences
  of generative parameter vectors; these generative parameters are then
  turned into sequences of actual bitmaps using the underlying
  PictureGenerator engine.
  """

  def _init(self,
            # Outputs
            dataOut=None,
            categoryOut=None,
            resetOut=None,
            distanceOut=None,
            # Generic parameters
            width=256, height=256,
            logPrefix='',
            replayMode=False,
            configPath=None,
            emitResets=True,
            seed=42,
            # Controls pattern generation
            mode="random",
            sequenceLength=32,
            minThickness=1, maxThickness=4,
            minPatternSize=32, maxPatternSize=128,
            minVelocity=1, maxVelocity=3,
            minAngularPosn=0.0, maxAngularPosn=0.0,
            minAngularVelocity=0.0, maxAngularVelocity=0.0,
            lockCategories=False,
            numRepetitions=1,
            noiseLevel=0.0,
            noiseWhere='fb',
            noiseThickness=1,
            radialLength=8,
            radialStep=1,
            spaceShape=None,
            spreadShape=None,
            stepSize=1,
            sweepOffMode=False,
            cropToBox=True,
            maxOffset=-1,
            **kwargs):
    """
    @param width: Specifies the width, in pixels, of each image that is to
                  be generated.
    @param height: Specifies the height, in pixels, of each image that is
                  to be generated.

    @param logPrefix: Specifies the prefix to use for logging images (including
                  directory(s) if desired); if evaluates to boolean False, then
                  no logging of generated images will be performed.

    @param replayMode:  If True (and if logPrefix is non-None), then logPrefix will
                        be treated as specifying the prefix of files to read from
                        and inject into the network, instead of the default
                        behavior of logging.

    @param configPath:  the PicturesGenerator configuration path to use for
                        non-novel categories; if None (the default), then use
                        the default PicturesGenerator configuration file.

    @param emitResets:  If True (default) sets the 'resetOut' output on the first
                        pattern of each sequence and clears it for all subsequent
                        patterns in the sequence.  If False, then never sets the
                        'resetOut' output.

    @param seed: Integer specifying a value to be used for seeding the pseudo
                 random number generated used (exclusively) by PictureSensor
                 as a source of randomness; the same value is used for seeding
                 each explorer's private/internal PRNG.

    @param mode:    Controls the translational positioning of generated patterns;
                    selects a named explorer that is expected to be found and
                    loaded from the explorer plugin directory.

    @param sequenceLength: Specifies the number presentations that is to constitute
                    a single sequence (which will typically include a 'reset' signal
                    at the beginning.)

    @param minThickness, maxThickness: Controls the range (in pixels) of line thickness;
                    Each generated image will be rendered with a fixed line thickness,
                    which will be chosen randomly from within the specified range.

    @param minPatternSize, maxPatternSize: Controls the size (in pixels) of each
                    generated pattern (or "object"); in general, this may be either
                    larger or smaller than the (width, height) of the output image.
                    Currently, there exists a single generative parameter (pattern size)
                    which forces all generated patterns to be drawn within a
                    square drawing zone (although the category's specific
                    aspect ratio will then further reduce this drawing zone and
                    allow for non-square patterns.)

    @param minVelocity, maxVelocity: Controls the range (in pixels/iteration) of
                    sweep velocity (for those explorers that support the concept
                    of sweeps, such as "random").  Each sequence will be
                    initialized with a velocity chosen from this range.  The
                    velocity applies to both horizontal and vertical motion.

    @param minAngularPosn, maxAngularPosn: Controls the range (in degrees) in
                    which patterns are initially rotated at the beginning of
                    each sequence, where a value of 0 implies no rotation with
                    respect to the raw pattern produced by PictureGenerator.

    @param minAngularVelocity, maxAngularVelocity: Controls the range (in
                    degrees/iteration) in which patterns will rotate throughout
                    the course of a sequence.

    @param lockCategories: a boolean which if True forces a single instance of
                    each category to be used, as opposed to randomly generating
                    new instances (specimens) of a category for each sequence.

    @param numRepetitions: the number of times that each sequence should be
                    repeated verbatim; the convention is that a value of 1
                    will correspond to a single presentation of each unique
                    sequence (e.g., ABCDE), a value of 2 will correspond to
                    a pair of identical sequences (AABBCCDDEE), etc.

    @param noiseLevel: specifies the probability of flipping each bit in order
                    to simulate shot noise on the output images.

    @param noiseThickness: Specifies the thickness (in number of pixels) of bit flips.
                    For example, noiseThickness = 2 means that blocks of 2x2 pixels are
                    flipped when adding noise to an image.

    @param noiseWhere: where to apply noise, can be 'f' (foreground), 'b' (background),
                    or 'fb' (foreground and background)

    @param radialLength: The number of presentations per radial (minus one).

    @param radialStep:  The number of pixels to advance per radial presentation.
                        Thus, the total "length" (in pixels) of a radial in
                        image space is 1 + radialLength * radialStep

    @param spaceShape:  The (height, width) of the 2-D space to explore for the
                        blockSpread explorer. This sets the number of center-points

    @param spreadShape:  The (height, width) of the area around each center
                        point to explore for the blockSpread explorer.

    @param stepSize:    The step size in pixels. This controls the spacing of
                        both the spaceShape points and the spreadShape points

    @param sweepOffMode:  If True, causes the position of objects within random
                        sweep sequences (i.e., sequences generated in mode 'random')
                        to sweep off the edge of the canvas; if False (default),
                        objects will "bounce" off the edge of the image.

    @param cropToBox:   If True, generated pattern is cropped to its bounding
                        box before being centered.

    @param maxOffset:   If set, the object won't be shifted more than this many
                        pixels from center. Only has an effect when mode=='random'.
    """

    PyRegion.__init__(self, **kwargs)

    # Make sure dataOut is correct size for the canvas
    reqdDataOut = height * width
    if dataOut is not None:
      if hasattr(dataOut, '__iter__'):
        # dataOut is a 2- or 3-dimensional vector (3 if coming from the VF)
        # Compute the product
        lenDataOut = reduce(lambda x, y: x*y, dataOut)
      else:
        lenDataOut = dataOut
      if lenDataOut != reqdDataOut:
        raise RuntimeError("The 'dataOut' output element count must be equal"
                           " to height (%d) * width (%d), or %d" \
                           % (height, width, reqdDataOut))
    if categoryOut is not None and categoryOut and categoryOut != 1:
      raise RuntimeError("The 'categoryOut' output element count must be 1.")
    if resetOut is not None and resetOut and resetOut != 1:
      raise RuntimeError("The 'resetOut' output element count must be 1.")
    if distanceOut is not None and distanceOut and distanceOut != 1:
      raise RuntimeError("The 'distanceOut' output element count must be 1.")
    # If running in replay mode, must have a valid logPrefix
    if replayMode and not logPrefix:
      raise RuntimeError("Replay mode requires a valid logPrefix be specified.")

    self.width = width
    self.height = height
    self.sequenceLength = sequenceLength
    self.minThickness = minThickness
    self.maxThickness = maxThickness
    self.minPatternSize = minPatternSize
    self.maxPatternSize = maxPatternSize
    self.minVelocity = minVelocity
    self.maxVelocity = maxVelocity
    self.minAngularPosn = minAngularPosn
    self.maxAngularPosn = maxAngularPosn
    self.minAngularVelocity = minAngularVelocity
    self.maxAngularVelocity = maxAngularVelocity
    self.noiseLevel = noiseLevel
    self.noiseWhere = noiseWhere
    self.noiseThickness = noiseThickness
    self.mode = mode
    self.radialLength = radialLength
    self.radialStep = radialStep
    self.spaceShape = spaceShape
    self.spreadShape = spreadShape
    self.stepSize = stepSize
    self.lockCategories = lockCategories
    self.numRepetitions = numRepetitions
    self.logPrefix = logPrefix
    self.replayMode = replayMode
    self.seed = seed
    self.configPath = configPath
    self.emitResets = emitResets
    self.sweepOffMode = sweepOffMode
    self.cropToBox = cropToBox
    self.maxOffset = maxOffset

    self.lockedCatMap = {}

    # Internal state
    self._initEphemerals()


  #+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=
  # PictureExplorer

  class PictureExplorer(object):
    """
    A base plugin class that implements "explorer" functionality for
    specific categories; this functionality controls the manner in
    which pictures are swept.

    To add support for a new type of explorer to the PictureSensor,
    perform the following:

    1. Derive a sub-class from this PictureExplorer base class;

    2. Implement the following mandatory methods:

       initialize() - perform one-time initialization of the explorer;

       initSequence() - create initial state for a new sequence

       updateSequence()  - update state of an existing sequence

       queryRelevantParams() - returns a sequence of names
                      of PictureSensor parameters that are relevant
                      to the operation of the explorer; a dict containing
                      these parameters' values will be passed to each
                      invocation of initialize(), initSequence(),
                      updateSequence(), and notifyParamUpdate().

       notifyParamUpdate() - a callback that will be invoked if/when
                      any of the explorer's relevant parameters have
                      their values changed.
    """

    def __init__(self, sensor):
      """
      Constructor that should never be overridden.
      """
      # Initialize a private source of pseudo-random-ness
      # to be available exclusively for use by this explorer
      self._rng = random.Random()
      self._rng.seed(sensor.seed)
      # Store a private reference to the owning sensor.
      self.__sensor = sensor


    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # External Plugin API

    def initialize(self, params):
      """
      Initialize the explorer.

      Perform any and all one-time explorer-specific initialization.
      This will often involve querying the 'sensor' reference to obtain
      values of parameters that are pertinent to the operation of
      the explorer, and saving these values as attributes of the
      explorer object.

      @param params: a dict containing the values of all parameters
                     that are relevant to the explorer's operation
                     (as specified by a call to queryRelevantParams()).

      May be extended by sub-classes, but they must invoke this base
      class method.
      """
      pass

    def initSequence(self, defaultState, params):
      """
      Create the state associated with a new sequence.

      @param defaultState: a dict containing the default values for new
             sequence state.  This dict will contain the following keys
             (additional keys may be added by the method implementation):
               catIndex - the 0-based index of the category
                          that will be used for the sequence;
               posnX - the initial X position of the pattern's reference
                          point for the new sequence;
               posnY - the initial Y position of the pattern's reference
                          point for the new sequence;
               velocityX - the initial horizontal velocity of the
                          pattern's reference point for the new sequence;
               velocityY - the initial vertical velocity of the
                          pattern's reference point for the new sequence;
               angularPosn - the initial angular position (in degrees) of
                          the pattern for the new sequence;
               angularVelocity - the initial angular velocity (in degrees
                          per iteration) of the pattern for the new sequence;

      @param params: a dict containing the values of all parameters
                     that are relevant to the explorer's operation
                     (as specified by a call to queryRelevantParams()).

      Must be overridden by sub-classes, and must not invoke this base class method.
      """
      raise NotImplementedError(
            "%s-derived classes must implement initSequence()" \
            % self.__class__.__name__)

    def updateSequence(self, state, params):
      """
      Update the state associated with an existing sequence.

      @param state: dict containing the
      @param params: a dict containing the values of all parameters
                     that are relevant to the explorer's operation
                     (as specified by a call to queryRelevantParams()).
      @returns: None

      Must be overridden by sub-classes, and must not invoke this base class method.
      """
      raise NotImplementedError(
            "%s-derived classes must implement updateSequence()" \
            % self.__class__.__name__)

    def notifyParamUpdate(self, params):
      """
      A callback that will be invoked if/when any of the explorer's
      relevant parameters have their values changed.

      @param params: a dict containing the new values of all parameters
                     that are relevant to the explorer's operation
                     (as specified by a call to queryRelevantParams()).
      """
      # Default behavior: save local explorer attribute values for each
      # relevant parameter
      for paramName, paramValue in params.items():
        setattr(self, '_%s' % paramName, paramValue)

    @classmethod
    def queryRelevantParams(klass):
      """
      Returns a sequence of parameter names that are relevant to
      the operation of the explorer.

      May be extended or overridden by sub-classes as appropriate.
      """
      return ()


    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Internal Helper Method API

    def _getAllCategories(self):
      return self.__sensor._categories

    def _getIterCount(self):
      return self.__sensor._iterCount

    def _getNumCategories(self):
      return len(self._getAllCategories())

    def _getNumRepetitions(self):
      return self.__sensor.numRepetitions

    def _chooseCategory(self, categories=None):
      """
      Helper function that randomly selects a category by consulting
      the PictureGenerator to use the relative frequency counts of
      each category.

      @return: 0-based integer of the chosen category.
      """
      if categories is None:
        categories = self._getAllCategories()
      chosenCat = self.__sensor._generator.chooseCategory(categories)
      return categories.index(chosenCat)

  # End of PictureExplorer inner class
  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


  @classmethod
  def queryNumCategories(self, configPath):
    """
    Public utility API that accepts a config path, parses it,
    and returns the number of categories it exports.
    """
    return PicturesGenerator.queryNumCategories(configPath)


  # Directory to be searched by default for plugin
  # modules, relative to directory associated withi
  # nupic.regions.extra module.
  _defExplorerDir = "PictureSensorExplorers"


  def _initExplorers(self):
    """
    Initialize explorer plugins.
    """
    for explorer in self._explorers.values():
      explorer.initialize(self._formExplorerParams(explorer))

  def _formExplorerParams(self, explorer):
    """
    Populate and return a dict containing the names and
    values of all PictureSensor parameters that are
    relevant to the specific explorer.
    """
    return dict([(paramName, self.getParameter(paramName)) \
           for paramName in explorer.queryRelevantParams()])

  def _loadExplorers(self):
    """
    Detect and load explorer plugins.
    """
    # Locate all ".py" modules in the explorers directory
    explorerDir = os.path.join(nupic.regions.__path__[0], self._defExplorerDir)
    explorerModulePaths = glob.glob(os.path.join(explorerDir, "*.py"))

    # Add explorer dir to our python path
    sys.path = [explorerDir] + sys.path

    # Load each explorer and introspect it for categories
    explorers = {}
    for explorerModulePath in explorerModulePaths:
      preState = {}
      execfile(explorerModulePath, preState)
      explorerName = os.path.splitext(os.path.split(explorerModulePath)[1])[0]
      candidates = []
      baseClassNames = []
      for itemName, item in preState.items():
        if explorerName not in explorers and type(item) == type(self.PictureExplorer) \
                                         and issubclass(item, self.PictureExplorer):
          # Keep track of substantive base classes (i.e., base classes
          # that are actually real parental plugins)
          baseClassNames += [mroType.__name__ for mroType in inspect.getmro(item) \
                             if mroType not in (self.PictureExplorer, item, object)]
          candidates += [item]

      # Instantiate an explorer
      nonBaseClasses = [candidate for candidate in candidates if candidate.__name__ not in baseClassNames]
      if len(nonBaseClasses) > 1:
        raise RuntimeError("A PictureSensor explorer module may only define a single Explorer")
      elif nonBaseClasses:
        ExplorerClass = nonBaseClasses[0]
        explorer = ExplorerClass(sensor=self)
        explorers[explorerName] = explorer

    # Store dict of explorers
    self._explorers = explorers
    # Initialize each explorer
    self._initExplorers()


  def _initEphemerals(self):

    # Scan directory(s) looking for explorer plugins
    self._loadExplorers()

    self._iterCount = 0  # number of compute() iterations completed
    self._seqIndex = 0   # index of next pattern in sequence
    self._repIndex = 0
    self._repMemory = []
    self._canvas = None
    self._seqState = {}  # parameter state of sequence
    self._lastMetadata = {}  # metadata from most recent pattern

    self._categoryOutputFile = None
    self.categoryOutputFile = ''
    self._fullImage = None
    self._locationBox = None

    # Initialize private PRNG
    self._rng = random.Random()
    self._rng.seed(self.seed)

    self._resetCategories()


  def _resetCategories(self):
    self._generator = PicturesGenerator(seed=self.seed, configPath=self.configPath)
    self._categories = self._generator.getCategories()


  def __init__(self, *args, **kw):
    self._init(*args, **kw)


  def _initSequence(self, state):
    # Prepare default state
    state['catIndex'] = 0
    state['posnX'] = 0
    state['posnY'] = 0
    state['velocityX'] = 0
    state['velocityY'] = 0
    state['angularPosn'] = 0.0
    state['angularVelocity'] = 0.0
    # Invoke the appropriate explorer
    explorer = self._getCurrentExplorer()
    explorer.initSequence(state, self._formExplorerParams(explorer))


  def _updateSequence(self, state):
    # Invoke the appropriate explorer
    explorer = self._getCurrentExplorer()
    explorer.updateSequence(state, self._formExplorerParams(explorer))


  def _genPattern(self):

    # In most cases, 'distance' is zero; it is only actually computed
    # if we are in "radial" mode.
    distance = 0.0

    # Time for new sequence
    if self._seqIndex == 0:
      state = dict(
        patternSize = self._rng.choice(xrange(self.minPatternSize, self.maxPatternSize + 1)),
        thickness = self._rng.choice(xrange(self.minThickness, self.maxThickness + 1)),
        )
      self._initSequence(state)
      if self.lockCategories:
        catIndex = state['catIndex']
        cat = self._categories[catIndex]
        catParams = self.lockedCatMap.get(cat, {})
        self.lockedCatMap[cat] = catParams
      else:
        # Empty dict causes new (random) set of category-specific # parameters to be chosen.
        catParams = {}
      # Choose change directions
      state.update(dict(
        patternSizeDelta = self._rng.choice([-1, +1]),
        thicknessDelta = self._rng.choice([-1, +1]),
        catParams = catParams,
        ))

    else:
      state = self._seqState
      # Choose new pattern size
      state['patternSize'] += state['patternSizeDelta']
      if state['patternSize'] <= self.minPatternSize or state['patternSize'] >= self.maxPatternSize:
        state['patternSize'] = max(min(state['patternSize'], self.maxPatternSize), self.minPatternSize)
        state['patternSizeDelta'] *= -1
      # Choose new thickness
      state['thickness'] += state['thicknessDelta']
      if state['thickness'] <= self.minThickness or state['thickness'] >= self.maxThickness:
        state['thickness'] = max(min(state['thickness'], self.maxThickness), self.minThickness)
        state['thicknessDelta'] *= -1
      self._updateSequence(state)

    # Save state
    self._seqState = state

    metadata = {}
    pattern = self._generator.generate(self._categories[state['catIndex']],
                                 patternSize=state['patternSize'],
                                 thickness=state['thickness'],
                                 paramState=state['catParams'],
                                 allowMirroring=False,
                                 lockParams=self.lockCategories,
                                 metadata=metadata,
                                ).astype(RealNumpyDType)
    # Extract optional center of gravity location for rotation
    # (defaulting to centroid)
    centerOfGravity = metadata.get('centerOfGravity', (0.5, 0.5))

    pilImage = Image.fromarray(numpy.uint8(pattern * 255), "L")

    # Rotation
    if state['angularPosn'] != 0.0:

      # OpenCV rotation
      if cvtypes and False:

        # Expand original pattern by 3X to make room for worst-case rotation
        origPatHeight, origPatWidth = pattern.shape
        bigPatHeight = origPatHeight * 3
        bigPatWidth = origPatWidth * 3
        bigPattern = numpy.zeros((bigPatHeight, bigPatWidth), dtype=numpy.uint8)
        patternInt = (255.0 * pattern).astype(numpy.uint8)
        bigPattern[origPatHeight:origPatHeight<<1, origPatWidth:origPatWidth<<1] = patternInt[:,:]

        # Allocate OpenCV (IPL) images
        imgBigSrc = cvtypes.cvCreateImageHeader(cvtypes.CvSize(bigPatWidth, bigPatHeight), 8, 1)
        imgBigSrc.contents.imageData = bigPattern.ctypes.data
        imgBigDst = cvtypes.cvCreateImage(cvtypes.CvSize(bigPatWidth, bigPatHeight), 8, 1)
        imgBigSize = cvtypes.cvGetSize(imgBigSrc)

        imgBigSrcBuf = cvtypes.cvImageAsBuffer(imgBigSrc)
        pilBigSrc = Image.frombuffer("L", (imgBigSize.width, imgBigSize.height), imgBigSrcBuf, 'raw', 'L', imgBigSrc.contents.widthStep, imgBigSrc.contents.nChannels)

        # Determine center of rotation
        (boxLeft, boxTop, boxRight, boxBottom) = pilBigSrc.getbbox()
        boxWidth = boxRight - boxLeft
        boxHeight = boxBottom - boxTop
        centerX = boxLeft + int(round(float(boxWidth)  * centerOfGravity[0]))
        centerY = boxTop  + int(round(float(boxHeight) * centerOfGravity[1]))

        # Perform rotation
        translate = cvtypes.cvCreateMat(2, 3, cvtypes.CV_32FC1)
        cvtypes.cvSetZero(translate)

        scale = 1.0
        center = cvtypes.CvPoint2D32f(centerX, centerY)
        cvtypes.cv2DRotationMatrix(center, state['angularPosn'], scale, translate)
        cvtypes.cvWarpAffine(imgBigSrc, imgBigDst, translate, cvtypes.CV_INTER_LINEAR + cvtypes.CV_WARP_FILL_OUTLIERS, cvtypes.CvScalar(0,0,0,0))
        cvtypes.cvReleaseMat(translate)

        imgBigDstBuf = cvtypes.cvImageAsBuffer(imgBigDst)
        pilBigDst = Image.frombuffer("L", (imgBigSize.width, imgBigSize.height), imgBigDstBuf, 'raw', 'L', imgBigDst.contents.widthStep, imgBigDst.contents.nChannels)

        # @TODO: allocate once and cache???
        cvtypes.cvReleaseImage(imgBigDst)
        cvtypes.cvReleaseImageHeader(imgBigSrc)

        # Force binarized image
        pilImage = pilBigDst.convert('1').convert('L')

      # PIL rotation
      else:
        pilImage = pilImage.rotate(state['angularPosn'], Image.BICUBIC, expand=True).convert('1').convert('L')
        # Optional: NEAREST filtering
        #rotImage = pilImage.rotate(rotDegrees, Image.NEAREST, expand=True)

    # Save the image to draw the location image if requested
    self._fullImage = pilImage

    # Convert to numpy
    pattern = numpy.asarray(pilImage, 'B').astype(pattern.dtype) / 255.0

    if self.cropToBox:
      # Clip to bounding box of actual pixels
      (boxLeft, boxTop, boxRight, boxBottom) = pilImage.getbbox()
      pattern = pattern[boxTop:boxBottom, boxLeft:boxRight]

    patternHeight, patternWidth = pattern.shape
    canvas = numpy.zeros((self.height, self.width), dtype=RealNumpyDType)

    # Handle collisions with canvas edge
    self._handleCollision(state, patternHeight, patternWidth)

    # Object position will be relative to center of canvas, so that
    # a position (0,0) will cause the center of the object pattern to be
    # placed at the center of the canvas.  Likewise, a position of (-4, 8)
    # will place the center of the object pattern at an offset
    # position of (-4, 8) relative to the canvas center.

    halfPatternHeight = patternHeight // 2
    halfPatternWidth  = patternWidth // 2
    halfCanvasWidth = self.width // 2
    halfCanvasHeight = self.height // 2
    offsetX = halfCanvasWidth - halfPatternWidth + state['posnX']
    offsetY = halfCanvasHeight - halfPatternHeight + state['posnY']

    # Clip the pattern (possibly partially or even wholly swept off
    # the canvas) onto the canvas.
    canvasStartX = max(offsetX, 0)
    canvasStopX = max(canvasStartX, min(offsetX + patternWidth, self.width))
    canvasStartX = min(canvasStartX, canvasStopX)
    canvasStartY = max(offsetY, 0)
    canvasStopY = max(canvasStartY, min(offsetY + patternHeight, self.height))
    canvasStartY = min(canvasStartY, canvasStopY)
    patternStartX = min(max(0, canvasStartX - offsetX), patternWidth)
    patternStopX  = min(max(0, patternStartX + canvasStopX - canvasStartX), patternWidth)
    patternStartY = min(max(0, canvasStartY - offsetY), patternHeight)
    patternStopY  = min(max(0, patternStartY + canvasStopY - canvasStartY), patternHeight)
    assert patternStartX >= 0
    assert patternStartY >= 0
    assert patternStopX <= patternWidth
    assert patternStopY <= patternHeight

    # Compute box for location image if requested
    if not self.cropToBox:
      boxLeft = boxTop = 0
    # Enlarge box by one pixel in each direction to draw the rectangle _around_
    #  the pixels that are seen
    self._locationBox = (patternStartX + boxLeft - canvasStartX - 1,
                         patternStartY + boxTop - canvasStartY - 1,
                         patternStopX + boxLeft + (self.width - canvasStopX),
                         patternStopY + boxTop + (self.height - canvasStopY))

    # "Blit" visible portion of pattern onto canvas
    canvas[canvasStartY:canvasStopY, canvasStartX:canvasStopX] = \
          pattern[patternStartY:patternStopY, patternStartX:patternStopX]

    # Apply noise
    if self.noiseLevel:
      self._generator.applyNoise(canvas,
                                 noise=self.noiseLevel,
                                 noiseThickness=self.noiseThickness,
                                 where=self.noiseWhere,
                                 rng=self._generator.getRNG())

    reset = 1 if self._seqIndex == 0 else 0

    # Store decoded metadata
    lastMetadata = copy.deepcopy(state)
    # Get rid of internal housekeeping state
    for internalParam in ('thicknessDelta', 'patternSizeDelta'):
      del lastMetadata[internalParam]
    catParams = lastMetadata['catParams']
    if catParams:
      category = self._categories[lastMetadata['catIndex']]
      catParams = self._generator.mapGenericParams(category, catParams['curKeyPt'])
      lastMetadata['catName'] = category
    lastMetadata['catParams'] = catParams
    self._lastMetadata = lastMetadata

    # Compute distance from center
    posnX = state['posnX']
    posnY = state['posnY']
    distance = math.sqrt(posnX * posnX + posnY * posnY)
    category = state['catIndex']

    return canvas, reset, category, distance

  def _handleCollision(self, state, clippedHeight, clippedWidth):
    """
    Handle collisions with canvas edge
    """
    if not self.sweepOffMode:
      slopX = (self.width  - clippedWidth) // 2
      slopY = (self.height - clippedHeight) // 2
      if self.maxOffset != -1:
        slopX = min(abs(slopX), self.maxOffset)
        slopY = min(abs(slopY), self.maxOffset)
      if state['posnX'] <= -slopX or state['posnX'] >= slopX:
        state['posnX'] = max(min(state['posnX'], slopX), -slopX)
        state['velocityX'] *= -1
      if state['posnY'] <= -slopY or state['posnY'] >= slopY:
        state['posnY'] = max(min(state['posnY'], slopY), -slopY)
        state['velocityY'] *= -1

  def _genImagePath(self):
    """
    Utility method for computing the path for a particualar image iteration
    """
    basePath = os.path.split(self.logPrefix)[0] if os.path.isabs(self.logPrefix) else os.getcwd()
    if not os.path.exists(basePath):
      print "Creating log directory: %s" % basePath
      os.makedirs(basePath)
    return os.path.join(basePath, "%s.%06d.png" % (self.logPrefix, self._iterCount))


  # Wrapper around PIL 1.1.6 Image.save to preserve PNG metadata
  # Public domain, Nick Galbreath
  # http://blog.modp.com/2007/08/python-pil-and-png-metadata-take-2.html
  def _saveWithMetadata(self, img, file):
      # These can be automatically added to Image.info dict
      # They are not user-added metadata
      reserved = ('interlace', 'gamma', 'dpi', 'transparency', 'aspect')
      # Undocumented class
      meta = PngImagePlugin.PngInfo()
      # Copy metadata into new object
      for k,v in img.info.iteritems():
        if k in reserved:
          continue
        meta.add_text(k, v, 0)
      # Save
      img.save(file, "PNG", pnginfo=meta)

  def _createLocationImage(self):
    """
    Draw a red box on the full image (before cropped to canvas) and return it.
    """

    if not self._fullImage:
      return

    # Draw red box onto location image
    locationImage = Image.new('RGB', self._fullImage.size)
    locationImage.paste(self._fullImage, (0, 0))
    draw = ImageDraw.Draw(locationImage)
    draw.rectangle(self._locationBox, outline='red')
    return locationImage

  def compute(self, inputs=None, outputs=None):
    """
    Generate the next sensor output and send it out.
    This method is called by the runtime engine.
    """

    # If this is the first iteration since a mode change
    # occurred, then we need to re-initialize explorers
    # and reseed _generator's RNG
    if self._iterCount == 0:
      self._initExplorers()
      self._generator.reSeed()

    # Replay images
    if self.replayMode:
      pilImage = Image.open(self._genImagePath())
      canvas = numpy.asarray(pilImage, 'B') / 255.0
      # Pull meta data
      category = int(pilImage.info['category'])
      reset = int(pilImage.info['reset'])
      distance = float(pilImage.info['distance'])

    # Produce new images
    else:
      if not self._repIndex:
        # Start new pattern to be repeated
        if self._seqIndex == 0:
          self._repMemory = []
        canvas, reset, category, distance = self._genPattern()
        self._repMemory += [(canvas, reset, category, distance)]
      else:
        canvas, reset, category, distance = self._repMemory[self._seqIndex]

    # Log if needed
    if self.logPrefix and not self.replayMode:
      numpyImg = numpy.uint8(canvas * 255)
      pilImage = Image.fromarray(numpyImg, "L")
      # Stuff with metadata
      pilImage.info['reset'] = str(reset)
      pilImage.info['category'] = str(category)
      pilImage.info['distance'] = str(distance)
      self._saveWithMetadata(pilImage, self._genImagePath())

    if self.categoryOutputFile:  # Only write if we have a valid filename
      if not self._categoryOutputFile:
        # Open the file
        self._categoryOutputFile = open(self.categoryOutputFile, 'w')
        # Write a 1 to the first line to specify one entry per line
        self._categoryOutputFile.write('1' + os.linesep)
      self._categoryOutputFile.write(str(category) + os.linesep)
      self._categoryOutputFile.flush()

    self._seqIndex += 1
    if self._seqIndex == self.sequenceLength:
      self._seqIndex = 0
      self._repIndex = (self._repIndex + 1) % self.numRepetitions

    # dataOut - main output
    outputs['dataOut'][:] = canvas.flatten()
    # print "PS OUTPUT: %s" % [i for i in xrange(len(outputs['dataOut'])) if outputs['dataOut'][i] != 0]

    # categoryOut - category index
    if 'categoryOut' in outputs:
      outputs['categoryOut'][:] = \
        numpy.array([float(category)], RealNumpyDType)

    # resetOut - reset flag
    if 'resetOut' in outputs:
      outputs['resetOut'][:] = \
        numpy.array([float(self.emitResets and reset)], RealNumpyDType)

    # distanceOut - reset flag
    if 'distanceOut' in outputs:
      outputs['distanceOut'][:] = \
        numpy.array([float(distance)], RealNumpyDType)

    self._iterCount += 1

    # Save canvas to calculate outputImage if requested
    self._canvas = canvas


  def getParameter(self, parameterName, nodeSet=""):
    if parameterName == 'numCategories':
      return len(self._categories)
    elif parameterName == 'categoryList':
      return self._categories
    elif parameterName == "numBlockPresentations":
      # Compute total number of block presentations
      edgeLen = 2 * self.radialLength + 1
      return 0 if self.mode != "block" else len(self._categories) * edgeLen * edgeLen
    elif parameterName == 'outputImage':
      if self._canvas is None:
        return ''  # Can't just do "return" because it shows up as "None"!
      outputArray = self._canvas.astype(numpy.uint8) * 255
      outputArray = outputArray.reshape((self.height, self.width))
      outputImage = Image.fromarray(outputArray)
      return serializeImage(outputImage)
    elif parameterName == 'locationImage':
      if self._fullImage is None:
        return ''  # Can't just do "return" because it shows up as "None"!
      return serializeImage(self._createLocationImage())
    elif parameterName == 'metadata':
      return str(self._lastMetadata)
    else:
      return PyRegion.getParameter(self, parameterName, nodeSet)


  def _getCurrentExplorer(self):
    explorer = self._explorers.get(self.mode, None)
    if not explorer:
      raise RuntimeError("Non-existent explorer requested: %s" % self.mode)
    return explorer


  def setParameter(self, parameterName, index, parameterValue="THISISNOTAVALUE"):

    # kludge for nupic 2 GP
    if parameterValue == "THISISNOTAVALUE":
      parameterValue = index

    if parameterName == "sequenceLength":
      self.sequenceLength = parameterValue
      self._seqIndex = 0

    elif parameterName == "mode":
      self.mode = parameterValue
      self._seqIndex = 0
      self._iterCount = 0

    elif parameterName == "numRepetitions":
      self.numRepetitions = parameterValue
      self._repIndex = 0
      self._seqIndex = 0
      self._repMemory = []
    elif parameterName == 'logPrefix':
      self.logPrefix = parameterValue
      self._iterCount = 0

    # Requires re-initializing internal state
    elif parameterName == "configPath":
      if parameterValue != self.configPath:
        self.configPath = parameterValue
        self._resetCategories()

    elif parameterName == 'categoryOutputFile':
      if self._categoryOutputFile:
        self._categoryOutputFile.close()
        self._categoryOutputFile = None
      self.categoryOutputFile = parameterValue
    else:
      if hasattr(self, parameterName):
        setattr(self, parameterName, parameterValue)

    # If the changed parameter is relevant to the particular
    # explorer, then notify that explorer.
    explorer = self._getCurrentExplorer()
    if parameterName in explorer.queryRelevantParams():
      explorer.notifyParamUpdate(self._formExplorerParams(explorer))


  def __getstate__(self):
    state = dict()
    for name in ['width', 'height', 'sequenceLength', 'minThickness',
                 'maxThickness', 'minPatternSize', 'maxPatternSize',
                 'minVelocity', 'maxVelocity', 'minAngularVelocity',
                 'maxAngularVelocity', 'minAngularPosn', 'maxAngularPosn',
                 'lockCategories', 'lockedCatMap', 'numRepetitions',
                 'noiseLevel', 'noiseWhere', 'noiseThickness', 'mode',
                 'radialLength', 'radialStep', 'spaceShape', 'spreadShape',
                 'stepSize', 'logPrefix', 'seed', 'configPath', 'replayMode',
                 'emitResets', 'sweepOffMode', 'cropToBox', 'maxOffset']:
      state[name] = getattr(self, name)
    return state

  def __setstate__(self, state):
    if '_canvasWidth' in state:
      # Handle _canvasWidth->width and _canvasHeight->height
      state['width'] = state.pop('_canvasWidth')
      state['height'] = state.pop('_canvasHeight')

    # Apply state
    for name in state:
      setattr(self, name, state[name])

    self._initEphemerals()


  @classmethod
  def getSpec(cls):
    ns = Spec(description = cls.__doc__,
                  singleNodeOnly=False)

    ns.outputs = dict(
      dataOut=OutputSpec(
        description="""Pixels of the image.""",
        dataType='float',
        count=1,
        regionLevel=False,
        isDefaultOutput=True
      ),

      categoryOut=OutputSpec(
        description="""Index of the current image's category.""",
        dataType='float',
        count=1,
        regionLevel=True,
        isDefaultOutput=False
      ),

      resetOut=OutputSpec(
        description="""Boolean reset output.""",
        dataType='float',
        count=1,
        regionLevel=True,
        isDefaultOutput=False
      ),

      distanceOut=OutputSpec(
        description="""Distance of object from image center.""",
        dataType='float',
        count=1,
        regionLevel=True,
        isDefaultOutput=False
      ),
    )

    ns.parameters=dict(
      width=ParameterSpec(dataType="uint", accessMode='Create',
        constraints="interval: [1, ...]", defaultValue=1,
        description="""Width of the output canvas, in pixels."""),

      height=ParameterSpec(dataType="uint", accessMode='Create',
        constraints="interval: [1, ...]", defaultValue=1,
        description="""Height of the output canvas, in pixels."""),

      sequenceLength=ParameterSpec(dataType="uint", accessMode='ReadWrite',
        constraints="interval: [1, ...]",
        description="""Length of temporal sequences."""),

      numRepetitions=ParameterSpec(dataType="uint", accessMode='ReadWrite',
        constraints="interval: [1, ...]",
        description="""Total number of repetitions of each sequences."""),

      numCategories=ParameterSpec(dataType="uint", accessMode='Read',
        constraints="interval: [1, ...]",
        description="""Number of categories."""),

      categoryList=ParameterSpec(dataType="Handle", constraints="string", accessMode='Read',
        description="""The categories that were last read in."""),

      logPrefix=ParameterSpec(dataType="str", accessMode='ReadWrite',
        description="""Name of the logging directory."""),

      noiseLevel=ParameterSpec(dataType="float", accessMode='ReadWrite',
        description="""Fraction of bits to flip randomly"""),

      noiseWhere=ParameterSpec(dataType="str", accessMode='ReadWrite',
        description="""Where to flip bits, can be either 'f' (foreground),
          'b' (background), or 'fb' (foreground and background)."""),

      noiseThickness=ParameterSpec(dataType="uint", accessMode='ReadWrite',
        description="""Width and height of a bit of noise in pixels."""),

      mode=ParameterSpec(dataType="str", accessMode='ReadWrite',
        description="""Controls the translational positioning of objects."""),

      minVelocity=ParameterSpec(dataType="uint", accessMode='ReadWrite',
        constraints="interval: [0, ...]",
        description="""Minimum speed at which pattern may be sweeped."""),

      maxVelocity=ParameterSpec(dataType="uint", accessMode='ReadWrite',
        constraints="interval: [0, ...]",
        description="""Maximum speed at which pattern may be sweeped."""),

      minAngularVelocity=ParameterSpec(dataType="float", accessMode='ReadWrite',
        description="""Minimum angular speed at which pattern may be rotated."""),

      maxAngularVelocity=ParameterSpec(dataType="float", accessMode='ReadWrite',
        description="""Maximum angular speed at which pattern may be rotated."""),

      minAngularPosn=ParameterSpec(dataType="float", accessMode='ReadWrite',
        description="""Minimum initial angular position at which pattern may be presented."""),

      maxAngularPosn=ParameterSpec(dataType="float", accessMode='ReadWrite',
        description="""Maximum initial angular position at which pattern may be presented."""),

      configPath=ParameterSpec(dataType="str", accessMode='ReadWrite',
        description="""SuperPictures configuration file to use when not in 'novel' mode."""),

      outputImage=ParameterSpec(dataType="str", accessMode='Read',
        description="""The image sent out during the last compute (serialized)."""),

      locationImage=ParameterSpec(dataType="str", accessMode='Read',
        description="""The full image with the crop box of the sensor (serialized)."""),

      categoryOutputFile=ParameterSpec(dataType="str", accessMode="ReadWrite",
       description="""Name of file to which to write category number on each compute."""),

      emitResets=ParameterSpec(dataType="bool", constraints="bool", accessMode='ReadWrite',
        description="""Whether to emit reset flag for the first pattern of each sequence."""),

      sweepOffMode=ParameterSpec(dataType="bool", constraints="bool", accessMode='ReadWrite',
        description="""Whether to allow objects to sweep off the edge of the image."""),

      cropToBox=ParameterSpec(dataType="bool", constraints="bool", accessMode='Read',
        description="""Whether generated pattern is cropped to its bounding box before being centered"""),

      minThickness=ParameterSpec(dataType="uint", accessMode='ReadWrite',
        constraints="interval: [1, ...]",
        description="""Minimum thickness with which to draw patterns."""),

      maxThickness=ParameterSpec(dataType="uint", accessMode='ReadWrite',
        constraints="interval: [1, ...]",
        description="""Maximum thickness with which to draw patterns."""),

      minPatternSize=ParameterSpec(dataType="uint", accessMode='ReadWrite',
        constraints="interval: [1, ...]",
        description="""Minimum size (in pixels) of generated patterns."""),

      maxPatternSize=ParameterSpec(dataType="uint", accessMode='ReadWrite',
        constraints="interval: [1, ...]",
        description="""Maximum size (in pixels) of generated patterns."""),

      lockCategories=ParameterSpec(dataType="bool", constraints="bool", accessMode='Create',
        description="""If True, disallows any parametric intra-category variation."""),

      radialLength=ParameterSpec(dataType="uint", accessMode='ReadWrite',
        constraints="interval: [1, ...]",
        description="""Length of radial onion curve 'spokes' in pixels (minus one.)"""),

      radialStep=ParameterSpec(dataType="uint", accessMode='ReadWrite',
        constraints="interval: [1, ...]",
        description="""Number of pixels to step during onion curve testing."""),

      spaceShape=ParameterSpec(dataType="Handle", accessMode='ReadWrite',
        description="""The (height, width) of the 2-D block to explore for the
        blockSpread explorer. This defines the center-points to spread around."""),

      spreadShape=ParameterSpec(dataType="Handle", accessMode='ReadWrite',
        description="""The (height, width) of the area around each center-point
        to explore for the blockSpread exlorer."""),

      stepSize=ParameterSpec(dataType="uint", accessMode='ReadWrite',
        description="""The step-size ot use for the blockSpread explorer. This
        controls the spacing between the center points as well as the spacing
        between the points in the spread around each center-point."""),

      replayMode=ParameterSpec(dataType="bool", constraints="bool", accessMode='Create',
        description="""Controls whether previously logged images should be replayed."""),

      seed=ParameterSpec(dataType="uint", accessMode='Create',
        description="""The value used to seed the internal pseudo RNG."""),

      maxOffset=ParameterSpec(dataType="int", accessMode='ReadWrite',
        description="""Maximum amount the object can be offset from the center."""),

      lockedCatMap=ParameterSpec(dataType='Handle', constraints='string', accessMode='Read',
        description="""Parameter that contains a dict of locked categories."""),

      metadata=ParameterSpec(dataType="str", accessMode='Read',
        description="""Parameter that contains a dict of metadata for the most
                       recently generated output image."""),

    )

    return ns.toDict()


  def initialize(self, dims, splitterMaps):
    assert dims[0] == self.width
    assert dims[1] == self.height