# Copyright 2015 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.



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
