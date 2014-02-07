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
{ 'modelParams': { 'clParams': { },
                   'sensorParams': { 'encoders': { }},
                   'spParams': { },
                   'tpParams': { 'activationThreshold': 12}}}

mod = importBaseDescription('./base.py', config)
locals().update(mod.__dict__)