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

import os

from PIL import Image
from nupic.image import imageExtensions


imageDir = os.path.join(os.path.dirname(__file__), 'images')
allImageFiles = [f for f in os.listdir(imageDir)
                 if os.path.splitext(f)[1].lower() in imageExtensions
                 or os.path.splitext(f)[1].lower() == '.ico']
allImageNames = [os.path.splitext(f)[0] for f in allImageFiles]

def getNTAImage(name):
  """Return the path to an image resource."""

  if name in allImageNames:
    return os.path.join(imageDir, allImageFiles[allImageNames.index(name)])
  else:
    return ""

def createDropTargetImage(width, height):
  """Load and prepare a drop target image for the specified size."""

  labelImage = Image.open(getNTAImage('drag_target'))
  dropImage = Image.new('RGBA', (width, height), (128, 128, 128, 255))
  dropImageInterior = Image.new('LA', (width - 5, height - 5), (128, 0))
  dropImage.paste(dropImageInterior, (3, 3))
  dropImage.paste(labelImage, ((width - labelImage.size[0]) / 2,
                               (height - labelImage.size[1]) / 2))
  return dropImage
