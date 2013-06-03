#
# The Python Imaging Library.
# $Id: TgaImagePlugin.py 2134 2004-10-06 08:55:20Z fredrik $
#
# TGA file handling
#
# History:
# 95-09-01 fl   created (reads 24-bit files only)
# 97-01-04 fl   support more TGA versions, including compressed images
# 98-07-04 fl   fixed orientation and alpha layer bugs
# 98-09-11 fl   fixed orientation for runlength decoder
#
# Copyright (c) Secret Labs AB 1997-98.
# Copyright (c) Fredrik Lundh 1995-97.
#
# See the README file for information on usage and redistribution.
#


__version__ = "0.3"

import Image, ImageFile, ImagePalette


def i16(c):
    return ord(c[0]) + (ord(c[1])<<8)

def i32(c):
    return ord(c[0]) + (ord(c[1])<<8) + (ord(c[2])<<16) + (ord(c[3])<<24)


MODES = {
    # map imagetype/depth to rawmode
    (1, 8):  "P",
    (3, 1):  "1",
    (3, 8):  "L",
    (2, 16): "BGR;5",
    (2, 24): "BGR",
    (2, 32): "BGRA",
}


def _accept(prefix):
    return prefix[0] == "\0"

##
# Image plugin for Targa files.

class TgaImageFile(ImageFile.ImageFile):

    format = "TGA"
    format_description = "Targa"

    def _open(self):

        # process header
        s = self.fp.read(18)

        id = ord(s[0])

        colormaptype = ord(s[1])
        imagetype = ord(s[2])

        depth = ord(s[16])

        flags = ord(s[17])

        self.size = i16(s[12:]), i16(s[14:])

        # validate header fields
        if id != 0 or colormaptype not in (0, 1) or\
           self.size[0] <= 0 or self.size[1] <= 0 or\
           depth not in (8, 16, 24, 32):
            raise SyntaxError, "not a TGA file"

        # image mode
        if imagetype in (3, 11):
            self.mode = "L"
            if depth == 1:
                self.mode = "1" # ???
        elif imagetype in (1, 9):
            self.mode = "P"
        elif imagetype in (2, 10):
            self.mode = "RGB"
            if depth == 32:
                self.mode = "RGBA"
        else:
            raise SyntaxError, "unknown TGA mode"

        # orientation
        orientation = flags & 0x30
        if orientation == 0x20:
            orientation = 1
        elif not orientation:
            orientation = -1
        else:
            raise SyntaxError, "unknown TGA orientation"

        if imagetype & 8:
            self.info["compression"] = "tga_rle"

        if colormaptype:
            # read palette
            start, size, mapdepth = i16(s[3:]), i16(s[5:]), i16(s[7:])
            if mapdepth == 16:
                self.palette = ImagePalette.raw("BGR;16",
                    "\0"*2*start + self.fp.read(2*size))
            elif mapdepth == 24:
                self.palette = ImagePalette.raw("BGR",
                    "\0"*3*start + self.fp.read(3*size))
            elif mapdepth == 32:
                self.palette = ImagePalette.raw("BGRA",
                    "\0"*4*start + self.fp.read(4*size))

        # setup tile descriptor
        try:
            rawmode = MODES[(imagetype&7, depth)]
            if imagetype & 8:
                # compressed
                self.tile = [("tga_rle", (0, 0)+self.size,
                              self.fp.tell(), (rawmode, orientation, depth))]
            else:
                self.tile = [("raw", (0, 0)+self.size,
                              self.fp.tell(), (rawmode, 0, orientation))]
        except KeyError:
            pass # cannot decode

#
# registry

Image.register_open("TGA", TgaImageFile, _accept)

Image.register_extension("TGA", ".tga")
