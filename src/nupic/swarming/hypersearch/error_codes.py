# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have an agreement
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



class ErrorCodes(object):
  streamReading         = "E10001"
  tooManyModelErrs      = "E10002"
  hypersearchLogicErr   = "E10003"
  productionModelErr    = "E10004"      # General PM error
  modelCommandFormatErr = "E10005"      # Invalid model command request object
  tooManyFailedWorkers  = "E10006"
  unspecifiedErr        = "E10007"
  modelInputLostErr     = "E10008"      # Input stream was garbage-collected
  requestOutOfRange     = "E10009"      # If a request range is invalid
  invalidType           = "E10010"      # Invalid 
