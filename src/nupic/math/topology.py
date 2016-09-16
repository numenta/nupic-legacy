# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2016, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------


import itertools
import numpy


def coordinatesFromIndex(index, dimensions):
  """
  Translate an index into coordinates, using the given coordinate system.

  Similar to numpy.unravel_index.

  @param index (int)
  The index of the point. The coordinates are expressed as a single index by
  using the dimensions as a mixed radix definition. For example, in dimensions
  42x10, the point [1, 4] is index 1*420 + 4*10 = 460.

  @param dimensions (list of ints)
  The coordinate system.

  @returns
  A list of coordinates of length len(dimensions).
  """
  coordinates = [0] * len(dimensions)

  shifted = index
  for i in xrange(len(dimensions) - 1, 0, -1):
    coordinates[i] = shifted % dimensions[i]
    shifted = shifted / dimensions[i]

  coordinates[0] = shifted

  return coordinates


def indexFromCoordinates(coordinates, dimensions):
  """
  Translate coordinates into an index, using the given coordinate system.

  Similar to numpy.ravel_multi_index.

  @param coordinates (list of ints)
  A list of coordinates of length dimensions.size().

  @param dimensions (list of ints
  The coordinate system.

  @returns
  The index of the point. The coordinates are expressed as a single index by
  using the dimensions as a mixed radix definition. For example, in dimensions
  42x10, the point [1, 4] is index 1*420 + 4*10 = 460.
  """
  index = 0
  for i, dimension in enumerate(dimensions):
    index *= dimension
    index += coordinates[i]

  return index


def neighborhood(centerIndex, radius, dimensions):
  """
  Get the points in the neighborhood of a point.

  A point's neighborhood is the n-dimensional hypercube with sides ranging
  [center - radius, center + radius], inclusive. For example, if there are two
  dimensions and the radius is 3, the neighborhood is 6x6. Neighborhoods are
  truncated when they are near an edge.

  This is designed to be fast. In C++ it's fastest to iterate through neighbors
  one by one, calculating them on-demand rather than creating a list of them.
  But in Python it's faster to build up the whole list in batch via a few calls
  to C code rather than calculating them on-demand with lots of calls to Python
  code.

  @param centerIndex (int)
  The index of the point. The coordinates are expressed as a single index by
  using the dimensions as a mixed radix definition. For example, in dimensions
  42x10, the point [1, 4] is index 1*420 + 4*10 = 460.

  @param radius (int)
  The radius of this neighborhood about the centerIndex.

  @param dimensions (indexable sequence)
  The dimensions of the world outside this neighborhood.

  @returns (numpy array)
  The points in the neighborhood, including centerIndex.
  """
  centerPosition = coordinatesFromIndex(centerIndex, dimensions)

  intervals = []
  for i, dimension in enumerate(dimensions):
    left = max(0, centerPosition[i] - radius)
    right = min(dimension - 1, centerPosition[i] + radius)
    intervals.append(xrange(left, right + 1))

  coords = numpy.array(list(itertools.product(*intervals)))
  return numpy.ravel_multi_index(coords.T, dimensions)


def wrappingNeighborhood(centerIndex, radius, dimensions):
  """
  Like 'neighborhood', except that the neighborhood isn't truncated when it's
  near an edge. It wraps around to the other side.

  @param centerIndex (int)
  The index of the point. The coordinates are expressed as a single index by
  using the dimensions as a mixed radix definition. For example, in dimensions
  42x10, the point [1, 4] is index 1*420 + 4*10 = 460.

  @param radius (int)
  The radius of this neighborhood about the centerIndex.

  @param dimensions (indexable sequence)
  The dimensions of the world outside this neighborhood.

  @returns (numpy array)
  The points in the neighborhood, including centerIndex.
  """
  centerPosition = coordinatesFromIndex(centerIndex, dimensions)

  intervals = []
  for i, dimension in enumerate(dimensions):
    left = centerPosition[i] - radius
    right = min(centerPosition[i] + radius,
                left + dimensions[i] - 1)
    interval = [v % dimension for v in xrange(left, right + 1)]
    intervals.append(interval)

  coords = numpy.array(list(itertools.product(*intervals)))
  return numpy.ravel_multi_index(coords.T, dimensions)
