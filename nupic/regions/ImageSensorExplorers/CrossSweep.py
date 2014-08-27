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

from nupic.regions.ImageSensorExplorers.SpiralSweep import SpiralSweep

class CrossSweep(SpiralSweep):

  """
  This explorer generates multiple presentations for each image in cross
  around the original image. For example, if the cross size is 2 then
  instead of the image being centered at (0,0) multiple presentations will be
  generated at the following locations :


           x
           x
     x  x  x  x  x
           x
           x


  CrossSweep sub-classes SpiralSweep, which is provides general-purpose logic
  for explorers that generate multiple translated presentations of each image.
  It overrides the __init__ method where it generates the particular "cross"
  list of offsets (where SpiralSweep generates a spiral-like list of offsets)

  The image is first swept horizontally left to right, and then vertically top to
  bottom. This order of sweeping makes it easier to debug translation effects in the
  inspectors.
  """

  def __init__(self, radius=1, stepsize=1, minradius=None, *args, **kwargs):
    """
    radius - the distance from the center to the outer x's
    stepsize - the distance between the x's
    minradius - distance from the center to the first x

    If the stepsize is greater than 1, then each 'x' in the diagrams above will be
    separated by 'stepsize' pixels. The 'radius' must always be a multiple of 'stepsize'

    By default, the inner circle starts at a radius of stepsize. If minradius is set,
    it defines the smallest circle radius. 'minradius' must also be a multiple of 'stepsize'

    If includeCenter is True, the center location will be included. By default it is not.
    """

    assert(radius >= 1)
    SpiralSweep.__init__(self, radius=radius, stepsize=stepsize, minradius=minradius,
                          *args, **kwargs)

    # Generate a list of possible offsets for this stepsize and radius
    self.offsets = []

    # First, generate the horizontal sweep
    for i in range(-radius, radius+1, stepsize):
      self.offsets += [(-i, 0)]

    # Now, the vertical sweep
    for i in range(-radius, radius+1, stepsize):
      self.offsets += [(0, -i)]
