# ----------------------------------------------------------------------
#  Copyright (C) 2012 Numenta Inc. All rights reserved.
#
#  The information and source code contained herein is the
#  exclusive property of Numenta Inc. No part of this software
#  may be used, reproduced, stored or distributed in any form,
#  without explicit written authorization from Numenta Inc.
# ----------------------------------------------------------------------

## This file defines parameters for a prediction experiment.

import os
from nupic.frameworks.opf.expdescriptionhelpers import importBaseDescription

# the sub-experiment configuration
config = \
{ 
  'dataSource': 'file://' + os.path.join(os.path.dirname(__file__), 
                                         '../datasets/scalar_0.csv'),
  'modelParams': { 
    'sensorParams': { 
      'verbosity': 0,
      'encoders': { 
        'field1': { 
          'clipInput': True,
          'fieldname': u'field1',
          'maxval': 0.1,
          'minval': 0.0,
          'n': 11,
          'name': u'field1',
          'type': 'ScalarEncoder',
          'w': 7
          },
       },
    },
    'clParams': { 
      'clVerbosity': 0,
      'implementation': 'py'
    },
  }
}

mod = importBaseDescription('../base/description.py', config)
locals().update(mod.__dict__)
