#!/usr/bin/env python

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
## @file
This is a (WIP) utility class for creating various visualizations. It is largely a wrapper around the PIL, but contains other useful methods.
One VisualizationEngine should be instantiated per desired output image.
Constructor accepts a size in pixels. Once instantiated, this size cannot change.
Once instantiated, images can be drawn to using the various methods contained here.
Save your image to disk using save(outfile), display using display() or get the underlying Image object using getImage()

Coordinates may be supplied in either pixel space (0,0 top left) or normalized space relative to the width and height of the image.
Note that this implies that you may not specify a pixel value < 1, as it will be interpreted as a normalized coordinate.

Coordinates and sizes are supplied as 2-tuples
Color can be a 3- or 4-tuple (where the 4th entry is alpha)


"""

from PIL import Image, ImageDraw, ImageFont

import matplotlib
matplotlib.use('Agg') # rendering backend for most image types
import pylab
import random
import StringIO
from numpy import *

##########################################################################
class VisualizationEngine(object):

    def __init__(self, width=500, height=500, color=(255, 255, 255, 255)):
        self.mImg = Image.new("RGBA", (width, height), color)
        self.mDraw = ImageDraw.Draw(self.mImg)
        print "matplotlib version: %s  location: %s  backend: %s" % (matplotlib.__version__, matplotlib.__file__, matplotlib.get_backend())

    def display(self):
        self.mImg.show()

    def save(self, filename):
        self.mImg.save(filename)

    def getImage(self):
        return self.mImg



##########################################################################
##           BASIC DRAWING METHODS
##########################################################################

    def drawCircle(self, center, radius, color):
        ccoords = self._convertCoords(center[0], center[1])
        bbox = (ccoords[0] - radius, ccoords[1] - radius, ccoords[0] + radius, ccoords[1] + radius)
        self.mDraw.ellipse(bbox, fill=color, outline=None)


    def drawString(self, bottomleft, str, color, fontsize=12):
        ccoords = self._convertCoords(bottomleft[0], bottomleft[1])
        font = ImageFont.truetype("/Library/Fonts/Arial Black.ttf", fontsize)
        self.mDraw.text(ccoords, str, fill=color, font=font)


    def drawBox(self, topleft, size, color):
        ccoords = self._convertCoords(topleft[0], topleft[1])
        csize = self._convertCoords(size[0], size[1])
        bbox = (ccoords[0], ccoords[1], ccoords[0] + csize[0], ccoords[1] + csize[1])
        self.mDraw.rectangle(bbox, fill=color, outline=None)



    def drawLine(self, points, stroke, color):
        cpoints = []
        for p in points:
            cpoints.append(self._convertCoords(p[0], p[1]))
        self.mDraw.line(cpoints, fill=color, width=stroke)




##########################################################################
##           WRAPPERS FOR PLOTTING
##########################################################################

    def plotOneVector(self, vec, name=None):
        vec = self._normalize(vec)
        pylab.plot(vec, label=name)
        pylab.ylim((-0.1, 1.1))
        if name is not None:
            pylab.legend([name])

        imgdata = StringIO.StringIO()
        pylab.savefig(imgdata, format='png', transparent=False)
        imgdata.seek(0)
        img = Image.open(imgdata)

        ## scale the output figure to fit our image
        scaleX = self.mImg.size[0] / float(img.size[0])
        scaleY = self.mImg.size[1] / float(img.size[1])
        scale = min(scaleX,scaleY)
        newW = int(img.size[0] * scale)
        newH = int(img.size[1] * scale)
        img2 = img.resize((newW,newH))
        box = (0,0,newW,newH)
        self.mImg.paste(img2, box)
        #print "scale: %f  w: %f  h: %f imgsize: %s\r" % (scale,newW, newH, img.size)


    def plotVectors(self, vecs, normalize=True, names=None):
        i = 0
        for v in vecs:
            if normalize:
                v = self._normalize(v)
            if names is None:
                lab = ''
            else:
                lab = names[i]
            pylab.plot(v, label=lab)
            pylab.hold(True)
            i += 1
        if names is not None:
            pylab.legend(names)
        pylab.ylim((0, 1.1))

        imgdata = StringIO.StringIO()
        pylab.savefig(imgdata, format='png', transparent=False)
        imgdata.seek(0)
        img = Image.open(imgdata)

        ## scale the output figure to fit our image
        scaleX = self.mImg.size[0] / float(img.size[0])
        scaleY = self.mImg.size[1] / float(img.size[1])
        scale = min(scaleX,scaleY)
        newW = int(img.size[0] * scale)
        newH = int(img.size[1] * scale)
        img2 = img.resize((newW,newH))
        box = (0,0,newW,newH)
        self.mImg.paste(img2, box)



##########################################################################
##           HIGH LEVEL DRAWING METHODS
##########################################################################

    def drawBitMatrix(self, M, offset=0, w=0, h=0):
        # figure out the size and shape of the cells
        if w == 0:
            cellwidth = self.mImg.size[0] / M.shape[1]
        else:
            cellwidth = w / M.shape[1]

        if h == 0:
            cellheight = self.mImg.size[1] / M.shape[0]
        else:
            cellheight = h / M.shape[0]

        #print 'cell width: %f  cell height: %f\r' % (cellwidth,cellheight)

        i = 0
        for row in M:
            j = 0
            y = i * cellheight
            for bitval in row:
                x = j*cellwidth + offset
                if bitval == 1:
                    c = 0
                else:
                    c = 255
                self.drawBox((x,y),(cellwidth,cellheight),(c,c,c))
                #print 'x: %f y: %f    ' % (x,y)
                j += 1
            i += 1


















##########################################################################
##           (private) UTILS
##########################################################################

    """ if x,y are in pixel space just return them. otherwise convert to px """
    def _convertCoords(self, x, y):
        if x < 1 and y < 1:
            x = self.mImg.size[0] * x
            y = self.mImg.size[1] * y

        return (x, y)

    """  min = 0 and max = 1 """
    def _normalize(self, v):
        vv = [ x - min(v) for x in v]
        vMax = max(vv)
        if min(vv) == max(vv):
            return v
        return [ x / (vMax) for x in vv]

    """ mean = 0 std = 1 """
    def _normalizeGauss(self, v):
        vv = [ x - mean(v) for x in v]
        if min(vv) == max(vv):
            return v
        stddev = std(vv)
        return [ x / (stddev) for x in vv]





##########################################################################
##           TEST CASES
##########################################################################

def testPlots():
    viz = VisualizationEngine(400, 600, (255,0,0,255))
    v = []
    for i in xrange(100):
        v.append(random.random())
    viz.plotOneVector(v)
    viz.display()


def testDrawTools():
    viz = VisualizationEngine(1000, 300)
    viz.drawCircle((500, 150), 50, (255, 0, 0))
    viz.drawBox((10, 10), (20, 20), (0, 255, 0))
    viz.drawBox((970, 270), (20, 20), (0, 255, 0))
    line = [(500, 0), (500, 300)]
    viz.drawLine(line, 2, (0, 0, 255))
    viz.display()











if __name__ == '__main__':
    #testDrawTools()
    testPlots()