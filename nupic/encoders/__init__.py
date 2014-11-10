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

from scalar import ScalarEncoder
from adaptivescalar import AdaptiveScalarEncoder
from date import DateEncoder
from logenc import LogEncoder
from category import CategoryEncoder
from sdrcategory import SDRCategoryEncoder
from delta import DeltaEncoder
from scalarspace import ScalarSpaceEncoder
from coordinate import CoordinateEncoder
from geospatial_coordinate import GeospatialCoordinateEncoder
from nupic.encoders.pass_through_encoder import PassThroughEncoder
# multiencoder must be imported last because it imports * from this module!
from multi import MultiEncoder
from utils import bitsToString
