# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.


from nupic.frameworks.prediction.helpers import importBaseDescription

config = dict(
      #sensorVerbosity=1,
      iterationCount = 25000,
      spPeriodicStats = 0,

      #numAValues = 25,
      #numBValues = 25,

      #encodingFieldStyleA = 'contiguous',    
      #encodingFieldWidthA = 50,
      #encodingOnBitsA =     5,

      #encodingFieldStyleB = 'contiguous',    
      #encodingFieldWidthB = 25,       
      #encodingOnBitsB =     5,        

      b0Likelihood = 0.90,
    )
              
mod = importBaseDescription('../base/description.py', config)
locals().update(mod.__dict__)

