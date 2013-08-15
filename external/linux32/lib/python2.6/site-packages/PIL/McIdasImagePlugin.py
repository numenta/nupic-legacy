#
# The Python Imaging Library.
# $Id: McIdasImagePlugin.py 2134 2004-10-06 08:55:20Z fredrik $
#
# Basic McIdas support for PIL
#
# History:
#       97-05-05 fl     Created (8-bit images only)
#
# Thanks to Richard Jones <richard.jones@bom.gov.au> for specs
# and samples.
#
# Copyright (c) Secret Labs AB 1997.
# Copyright (c) Fredrik Lundh 1997.
#
# See the README file for information on usage and redistribution.
#

__version__ = "0.1"

import string

import Image, ImageFile

def i16(c,i=0):
    return ord(c[1+i])+(ord(c[i])<<8)

def i32(c,i=0):
    return ord(c[3+i])+(ord(c[2+i])<<8)+(ord(c[1+i])<<16)+(ord(c[i])<<24)

def _accept(s):
    return i32(s) == 0 and i32(s, 4) == 4

##
# Image plugin for McIdas area images.

class McIdasImageFile(ImageFile.ImageFile):

    format = "MCIDAS"
    format_description = "McIdas area file"

    def _open(self):

        # parse area file directory
        s = self.fp.read(256)
        if not _accept(s):
            raise SyntaxError, "not an McIdas area file"

        # get mode
        if i32(s, 40) != 1 or i32(s, 52) != 1:
            raise SyntaxError, "unsupported McIdas format"

        self.mode = "L"

        # get size
        self.size = i32(s, 36), i32(s, 32)

        # setup image descriptor
        prefix = i32(s, 56)
        offset = i32(s, 132)

        self.tile = [("raw", (0, 0) + self.size, offset,
                     ("L", prefix + self.size[0], 1))]

        # FIXME: should store the navigation and calibration blocks
        # somewhere (or perhaps extract some basic information from
        # them...)

# --------------------------------------------------------------------
# registry

Image.register_open("MCIDAS", McIdasImageFile, _accept)

# no default extension
