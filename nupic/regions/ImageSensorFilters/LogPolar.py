# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
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
## @file
This file defines the LogPolar filter, an ImageSensor filter that distorts
incoming images in a "fish-eye" manner.
"""

from PIL import Image
import numpy

from nupic.regions.ImageSensorFilters.BaseFilter import BaseFilter


class LogPolar(BaseFilter):

  """
  Apply a LogPolar transformation to the original image
  """

  def __init__(self, xsize, ysize, c, preserveCenterResolution=False, Debug=False):
    """
    Initializes the kernel matrices, a one-time cost, which are then applied to
    each image.

    @param xsize -- The x-dimension size of the desired output
    @param ysize -- The y-dimension size of the desired output
    @param c     -- Paramaterizes how much the image bends (ie. how steep the
                    fish-eye.  c=0 is no distortion.  c=3 is severe.
    @param preserveCenterResolution -- if True, the resolution of the center of the
                    image will be preserved and the edges will be sub-sampled.
                    If False, the center pixels will be blown up to keep the
                    outside corners at the original resolution.
    @param Debug -- Determines whether to compute and save some intermediate
                    data structures for debugging (deltaxmat, deltaymat, scales).
    """

    BaseFilter.__init__(self)

    # Init params
    self._lastOutputImage = None
    self._xsize = xsize
    self._ysize = ysize
    self._c = c
    self._pcr = preserveCenterResolution
    self._debug = Debug
    self._kernelx = None
    self._kernely = None
    self._kernel = None
    self._imgSize = (-1,-1)

  def process(self, image):
    """
    Perform LogPolar filtering on the input image and return the response

    @param image -- The image to process
    """

    #image.save("logPolarDebugInput.png")
    BaseFilter.process(self, image)
    #image.save("logPolarDebugPostBase.png")

    out = self._applyKernel(image, 0)
    outImg = Image.fromarray(out.astype(numpy.int8))
    #outImg.save("logPolarDebug.png")
    maskOut = self._applyKernel(image, 1)
    maskOutImg = Image.fromarray(maskOut.astype(numpy.int8))
    outImg.putalpha(maskOutImg)
    #outImg.save("logPolarDebugMask.png")
    self._lastOutputImage = outImg
    return outImg

  def _applyKernel(self, img, channel=0, Mirror=False):
    """
    The "guts" of the filter.  Takes an input PIL image and returns a numpy
    array containing the output image data

    @param img     -- The image to process
    @param channel -- Which part of the image to process
                          0: The image
                          1: The mask
    @param Mirror  -- If the image is smaller than the output, whether to mirror
                       the image (or to fill with zeros)
    """


    # Create the kernel if we haven't done so already
    if self._kernelx is None:
      self._makeKernel(self._xsize, self._ysize, self._c, Debug=self._debug, Save=False)

    # Get the input image into a flattened array
    data = numpy.array(img.split()[channel].getdata())

    # Add a sentinel pixel at the end which is set to the background color
    data = numpy.resize(data, data.size+1)
    data[-1] = self.background

    # See if we need to re-compute our clipped, flattened kernel, which depends on the
    #  image size
    if img.size != self._imgSize:
      # Convert our kernel matrix center to the center of the input image, and mark indicies
      #  that are outside the bounds of the input image with a sentinel
      sentinel = -1 * img.size[0] * img.size[1]
      kxBig = self._ceilFoor(self._kernelx, img.size[1], None, Mirror).astype('int')
      kyBig = self._ceilFoor(self._kernely, img.size[0], None, Mirror).astype('int')

      # When preserving the resolution at the edges, we make the output image size the
      #  same as the input image size. So, when the input image size is smaller than our
      #  kernel, we have to clip the outside edges of our kernel
      if not self._pcr:
        kx = self._cropMatCenter(kxBig, (img.size[1],img.size[0]))
        ky = self._cropMatCenter(kyBig, (img.size[1],img.size[0]))
        matSize = (img.size[1],img.size[0])
      else:
        kx = kxBig
        ky = kyBig
        matSize = (self._ysize, self._xsize)

      # Convert our kernel to indices into the flattened array of the input image.
      kernel = (kx + ky*img.size[0]).flatten()

      # Convert all negative indices (sentinels) to reference the last element of the data
      kernel[kernel < 0] = -1
      self._kernel = kernel
      self._imgSize = img.size
      self._matSize = matSize

    # Map the output from the kernel
    output = data[self._kernel].reshape(self._matSize)
    return output


  def _ceilFoor(self, mat, width, sentinel, Mirror=False):
    """
    Center our kernel matrix around the center of the given input image and ensure that
    the kernel matrix does not try to access pixels outside the input data array.
    """
    out = mat.copy()

    # Re-center around the image center
    maxIdx = width-1
    out += maxIdx / 2.0

    # Mark the indices that go outside the source image with a sentinel, we will use these as
    #  indicators to plug-in the background pixel value
    if Mirror:
      out[out < 0] = -out[out < 0]
      out[out > maxIdx] = 2 * maxIdx-out[out > maxIdx]
    else:
      if sentinel is not None:
        out[out < 0] = sentinel
        out[out > maxIdx] = sentinel
      else:
        out[out < 0] = 0
        out[out > maxIdx] = maxIdx

    return out

  def _cropMatCenter(self, mat, outSize):
    """
    Crops mat to be outSize, maintaining the original center.
    """
    (xsize, ysize) = outSize
    if mat.shape[0] < xsize or mat.shape[1] < ysize:
      raise ValueError("Mat shape %s must be >= (xsize=%i,ysize=%i)" %(str(mat.shape), xsize,ysize))
    mcenterx = mat.shape[0]/2.
    mcentery = mat.shape[1]/2.
    x0 = int(mcenterx - xsize/2.)
    y0 = int(mcentery - ysize/2.)
    return mat[x0:x0+xsize, y0:y0+ysize]

  def _makeKernel(self, xsize, ysize, c, Debug=False, Save=True):
    """
    Make the original kernel matrices, of size (xsize,ysize) and with bending
    parameter c.  Debug determines whether to compute and store data structures
    useful for debugging (deltaxmat, deltaymat, scales).  Save determines whether
    to save the kernel matrices to disk, eg. to be loaded later instead of
    recomputed.
    """

    # Numeric errors if c is exactly zero:
    if c == 0:
      c = 0.001
    centerx = (xsize-1)/2.;
    centery = (ysize-1)/2.;
    self._kernelx = numpy.zeros((ysize,xsize))
    self._kernely = numpy.zeros((ysize,xsize))
    if Debug:
      self._deltaxmat = numpy.zeros((ysize,xsize))
      self._deltaymat = numpy.zeros((ysize,xsize))
      self._scales = numpy.zeros((ysize,xsize))

    hypotmax = numpy.sqrt(numpy.power(xsize-1-centerx,2) + \
                          numpy.power(ysize-1-centery,2))
    k = 1 / (numpy.exp(c) - 1)

    # Are we preserving the center resolution? If so, compute the factor required
    #  to give a scale of 1 to the center pixels
    if self._pcr:
      scaleInCenter = k * (numpy.exp(c*1.0/hypotmax)-1) / (1.0/hypotmax)
      scaleFactor = 1.0/scaleInCenter
    else:
      scaleFactor = 1.0

    for row in range(ysize):
      for col in range(xsize):
        if (col != centerx) or (row != centery):
          deltax = col-centerx
          deltay = row-centery
          hypot = numpy.sqrt(numpy.power(deltax,2) + numpy.power(deltay,2))
          scale = scaleFactor * k * (numpy.exp(c*hypot/hypotmax)-1) / (hypot/hypotmax)
          # scale = numpy.power(hypot/centerx, 1.1) / hypot
          self._kernelx[row,col] = scale*deltax
          self._kernely[row,col] = scale*deltay
          if Debug:
            self._deltaxmat[row,col] = deltax
            self._deltaymat[row,col] = deltay
            self._scales[row,col] = scale

    # Compute the optimim input image size so that the output image fills the self._xsize,
    #  self._ysize destination image
    if self._pcr:
      optSrcWidth = self._kernelx[centery][-1] * 2
      optSrcHeight = self._kernely[-1][centerx] * 2
      print "LogPolar Filter: Optimum input image size for this value of c (%f)" % (c), \
            "is %d x %d (width x height)" % (optSrcWidth, optSrcHeight)

    if Save:
      import cPickle
      f = open('kernelx%ix%ic%.2f.dat' %(xsize,ysize,c),'w')
      cPickle.dump(self._kernelx, f)
      f.close()
      f = open('kernely%ix%ic%.2f.dat' %(xsize,ysize,c),'w')
      cPickle.dump(self._kernely, f)
      f.close()
      if Debug:
        f = open('deltax%ix%i.dat' %(xsize,ysize),'w')
        cPickle.dump(self._deltaxmat, f)
        f.close()
        f = open('deltay%ix%i.dat' %(xsize,ysize),'w')
        cPickle.dump(self._deltaymat, f)
        f.close()
        f = open('scales%ix%ic%.2f.dat' %(xsize,ysize,c),'w')
        cPickle.dump(self._scales, f)
        f.close()
