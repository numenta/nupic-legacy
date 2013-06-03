#
# The Python Imaging Library.
# $Id: SgiImagePlugin.py 2134 2004-10-06 08:55:20Z fredrik $
#
# SGI image file handling
#
# See "The SGI Image File Format (Draft version 0.97)", Paul Haeberli.
# <ftp://ftp.sgi.com/graphics/SGIIMAGESPEC>
#
# History:
# 1995-09-10 fl     Created
#
# Copyright (c) Secret Labs AB 1997.
# Copyright (c) Fredrik Lundh 1995.
#
# See the README file for information on usage and redistribution.
#


__version__ = "0.1"


import string
import Image, ImageFile


def i16(c):
    return ord(c[1]) + (ord(c[0])<<8)

def i32(c):
    return ord(c[3]) + (ord(c[2])<<8) + (ord(c[1])<<16) + (ord(c[0])<<24)


def _accept(prefix):
    return i16(prefix) == 474

##
# Image plugin for SGI images.

class SgiImageFile(ImageFile.ImageFile):

    format = "SGI"
    format_description = "SGI Image File Format"

    def _open(self):

        # HEAD
        s = self.fp.read(512)
        if i16(s) != 474:
            raise SyntaxError, "not an SGI image file"

        # relevant header entries
        compression = ord(s[2])

        # bytes, dimension, zsize
        layout = ord(s[3]), i16(s[4:]), i16(s[10:])

        # determine mode from bytes/zsize
        if layout == (1, 2, 1):
            self.mode = "L"
        elif layout == (1, 3, 3):
            self.mode = "RGB"
        else:
            raise SyntaxError, "unsupported SGI image mode"

        # size
        self.size = i16(s[6:]), i16(s[8:])

        # decoder info
        if compression == 0:
            if self.mode == "RGB":
                # RGB images are band interleaved
                size = self.size[0]*self.size[1]
                self.tile = [("raw", (0,0)+self.size, 512, ("R",0,1)),
                             ("raw", (0,0)+self.size, 512+size, ("G",0,1)),
                             ("raw", (0,0)+self.size, 512+2*size, ("B",0,1))]
            else:
                self.tile = [("raw", (0,0)+self.size, 512, (self.mode, 0, 1))]
        if compression == 1:
            self.tile = [("sgi_rle", (0,0)+self.size, 512, (self.mode, 0, 1))]

#
# registry

Image.register_open("SGI", SgiImageFile, _accept)

Image.register_extension("SGI", ".bw")
Image.register_extension("SGI", ".rgb")
Image.register_extension("SGI", ".rgba")

Image.register_extension("SGI", ".sgi") # really?
