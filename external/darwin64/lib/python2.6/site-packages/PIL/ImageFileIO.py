#
# The Python Imaging Library.
# $Id: ImageFileIO.py 2134 2004-10-06 08:55:20Z fredrik $
#
# kludge to get basic ImageFileIO functionality
#
# History:
# 1998-08-06 fl   Recreated
#
# Copyright (c) Secret Labs AB 1998-2002.
#
# See the README file for information on usage and redistribution.
#

from StringIO import StringIO

##
# The <b>ImageFileIO</b> module can be used to read an image from a
# socket, or any other stream device.
# <p>
# This module is deprecated. New code should use the <b>Parser</b>
# class in the <a href="imagefile">ImageFile</a> module instead.
#
# @see ImageFile#Parser

class ImageFileIO(StringIO):

    ##
    # Adds buffering to a stream file object, in order to
    # provide <b>seek</b> and <b>tell</b> methods required
    # by the <b>Image.open</b> method. The stream object must
    # implement <b>read</b> and <b>close</b> methods.
    #
    # @param fp Stream file handle.
    # @see Image#open

    def __init__(self, fp):
        data = fp.read()
        StringIO.__init__(self, data)

if __name__ == "__main__":

    import Image
    fp = open("/images/clenna.im", "rb")
    im = Image.open(ImageFileIO(fp))
    im.load() # make sure we can read the raster data
    print im.mode, im.size
