# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
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


from nupic.frameworks.prediction.helpers import importBaseDescription

config = dict(
      #sensorVerbosity=3,
      iterationCount = 1000,

      numAValues = 10,
      numBValues = 10,

      #encodingFieldStyleA = 'contiguous',    
      encodingFieldWidthA = 50,
      #encodingOnBitsA =     5,

      #encodingFieldStyleB = 'contiguous',    
      encodingFieldWidthB = 50,       
      #encodingOnBitsB =     5,        

      b0Likelihood = None,
    )
              
mod = importBaseDescription('../base/description.py', config)
locals().update(mod.__dict__)

