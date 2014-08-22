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

class PatrolSweep(SpiralSweep):

  """
  This explorer generates multiple presentations for each image in a patrol-like
  path around the original image. For example, if the patrol radius is 2 then
  instead of the image being centered at (0,0) multiple presentations will be
  generated at the following offsets :


  (-2, -2) (-2, 0) (-2, 2)

  (-2, 0)    I     (2, 0)

  (-2, 2)  (0, 2)  (2, 2)


  PatrolSweep sub-classes SpiralSweep, which is provides general-purpose logic
  for explorers that generate multiple translated presentations of each image.
  It overrides the __init__ method where it generates the particular "patrol"
  list of offsets (where SpiralSweep generates a spiral-like list of offsets)
  """

  def __init__(self, radius=1, *args, **kwargs):
    """
    radius - the radius of the Patrol sweep
    """

    assert(radius >= 1)
    SpiralSweep.__init__(self, radius, *args, **kwargs)
    r = radius
    self.offsets = [(r, 0),  (r, r),   (0, r),  (-r, r),
                    (-r, 0), (-r, -r), (0, -r), (r, -r)]
    self.index = 0
