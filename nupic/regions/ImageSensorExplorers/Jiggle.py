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


DEBUG = 0

class Jiggle(SpiralSweep):

  """
  This explorer jiggles the image around each possible location within a specified
  radius, being careful not to repeat movements already performed between any
  two locations for maximum efficiency.

  This explorer can be an efficient means of training a first order temporal
  learner for translation shifts within a certain radius from center.
  """

  def __init__(self, shift=1, radius=1, *args, **kwargs):
    """
    @param shift -- Number of pixels to shift each time.
    @param radius -- maximum amount to move away from center. Must be a multiple
                      of 'shift'

    """
    assert(radius >= 1)
    SpiralSweep.__init__(self, radius, *args, **kwargs)

    if (radius % shift) != 0:
      raise RuntimeError("radius must be a multiple of shift")

    # Generate the location offsets that we will move to for each image
    self.offsets = self._generateOffsets(shift, radius)
    self.index = 0


  ##################################################################################
  def _generateOffsets(self, shift, radius):
    """
    Generate the list of offsets we will visit for each image/filter combination

    @param shift - how much each location is separated by
    @param radius - maximum radius away from center to move
    """

    # Table mapping a jiggle index to the relative location
    gJiggleOffsets = [ \
                        # direction   jiggleIndex's
      ( 0,     shift),  # up           (1,2)
      (-shift, shift),  # up-right     (3,4)
      (-shift, 0),      # right        (5,6)
      (-shift,-shift),  # down-right   (7,8)
      ( 0,    -shift),  # down         (9,10)
      ( shift,-shift),  # down-left    (11,12)
      ( shift, 0),      # left         (13,14)
      ( shift, shift),  # up-left      (15,16)
      ]

    gJigglesPerformed = []

    # ------------------------------------------------------------------------
    # Find the next "jiggle" for the current offset
    def nextJiggle(location, jiggleIndex, jiggleOffsets, jigglesPerformed):
      """
      Find the next jiggle around the current location

      @param location    - current location
      @param jiggleIndex - current jiggle index
      @param jiggleOffsets - table of jiggle offsets for each location
      @param jigglesPerformed - which jiggles we've performed already between
                                   all possible locations
      @retval (jiggleIndex, jiggleTo)
              or None if we've already visited all neighbors from this location
      """

      #global jigglesPerformed, jiggleOffsets
      while True:
        jiggleIndex += 1
        if jiggleIndex > 16:
          return (None, None)
        src = tuple(location)
        dst = (src[0] + jiggleOffsets[(jiggleIndex-1)/2][0],
               src[1] + jiggleOffsets[(jiggleIndex-1)/2][1])

        # If the dst is outside our radius, skip it
        if max(abs(dst[0]), abs(dst[1])) > radius:
          continue

        # Going away or coming back?
        if (jiggleIndex & 1) == 0:
          (src, dst) = (dst, src)

        # If we've already peformed this transition between src and dst, skip it
        if (jiggleIndex & 1):
          awayJiggle = (src, dst)
          backJiggle = (dst, src)
          if awayJiggle in jigglesPerformed  and \
             backJiggle in jigglesPerformed:
             if DEBUG >= 2: print "already performed jiggle", jiggleIndex, ", skipping"
             jiggleIndex += 1
             continue
          # Add these jiggles to those performed
          jigglesPerformed += [awayJiggle, backJiggle]


        # Move to dst
        if DEBUG >= 2:
          print "jiggleIndex:", jiggleIndex, "location:", location,
          print "relPosition:", dst
        return (jiggleIndex, dst)

    # --------------------------------------------------------------------------
    # Loop through each loation within the radius and find all the jiggles

    # Locations are encoded (x, y) and higher values move towards the top-left
    location = [radius, radius]   # top-left corner
    offsets = [tuple(location)]

    while True:

      jiggleIndex = 0
      # ...............................
      # Next jiggle at this location
      while True:
        (jiggleIndex, offset) = nextJiggle(location, jiggleIndex, gJiggleOffsets,
                                  gJigglesPerformed)
        if offset is None:
          break
        offsets += [offset]

      # ...............................
      # Next location
      # Next location to the right
      location[0] -= shift
      if location[0] >= -radius:
        offsets += [tuple(location)]
        continue

      # Next row down, on the left
      location[0] = radius
      location[1] -= shift
      if location[1] >= -radius:
        offsets += [tuple(location)]
        continue

      # Exhausted all locations, break out
      break

    return offsets
