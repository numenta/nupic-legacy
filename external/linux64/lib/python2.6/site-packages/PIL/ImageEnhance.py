#
# The Python Imaging Library.
# $Id: ImageEnhance.py 2134 2004-10-06 08:55:20Z fredrik $
#
# image enhancement classes
#
# For a background, see "Image Processing By Interpolation and
# Extrapolation", Paul Haeberli and Douglas Voorhies.  Available
# at http://www.sgi.com/grafica/interp/index.html
#
# History:
#       96-03-23 fl     Created
#
# Copyright (c) Secret Labs AB 1997.
# Copyright (c) Fredrik Lundh 1996.
#
# See the README file for information on usage and redistribution.
#

import Image, ImageFilter

class _Enhance:

    ##
    # Returns an enhanced image. The enhancement factor is a floating
    # point value controlling the enhancement. Factor 1.0 always
    # returns a copy of the original image, lower factors mean less
    # colour (brightness, contrast, etc), and higher values more.
    # There are no restrictions on this value.
    #
    # @param factor Enhancement factor.
    # @return An enhanced image.

    def enhance(self, factor):
        return Image.blend(self.degenerate, self.image, factor)

##
# Color enhancement object.
# <p>
# This class can be used to adjust the colour balance of an image, in
# a manner similar to the controls on a colour TV set.  An enhancement
# factor of 0.0 gives a black and white image, a factor of 1.0 gives
# the original image.

class Color(_Enhance):
    "Adjust image colour balance"
    def __init__(self, image):
        self.image = image
        self.degenerate = image.convert("L").convert(image.mode)

##
# Contrast enhancement object.
# <p>
# This class can be used to control the contrast of an image, similar
# to the contrast control on a TV set.  An enhancement factor of 0.0
# gives an solid grey image, factor 1.0 gives the original image.

class Contrast(_Enhance):
    "Adjust image contrast"
    def __init__(self, image):
        self.image = image
        mean = reduce(lambda a,b: a+b, image.convert("L").histogram())/256.0
        self.degenerate = Image.new("L", image.size, mean).convert(image.mode)

##
# Brightness enhancement object.
# <p>
# This class can be used to control the brighntess of an image.  An
# enhancement factor of 0.0 gives a black image, factor 1.0 gives the
# original image.

class Brightness(_Enhance):
    "Adjust image brightness"
    def __init__(self, image):
        self.image = image
        self.degenerate = Image.new(image.mode, image.size, 0)

##
# Sharpness enhancement object.
# <p>
# This class can be used to adjust the sharpness of an image.  The
# enhancement factor 0.0 gives a blurred image, 1.0 gives the original
# image, and a factor of 2.0 gives a sharpened image.

class Sharpness(_Enhance):
    "Adjust image sharpness"
    def __init__(self, image):
        self.image = image
        self.degenerate = image.filter(ImageFilter.SMOOTH)
