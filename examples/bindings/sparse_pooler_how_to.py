#!/usr/bin/env python

# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
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

from nupic.bindings.math import *
from nupic.bindings.algorithms import *

import numpy
import cPickle

#--------------------------------------------------------------------------------
# SparsePooler learning and inference
#--------------------------------------------------------------------------------
def sparse_pooler_use_case():

    segment_size = 4
    norm = 2
    kWinners = 0
    threshold = .25
    sparsification_mode = 2
    inference_mode = 0
    min_accept_distance = 1e-5
    min_accept_norm = .5
    min_proto_sum = 3
    sigma = .1

    # Create a SparsePooler
    sp = SparsePooler(SparsePoolerInputMasks(segment_size, [[(0,8)]]),
                      1, norm,
                      sparsification_mode,
                      inference_mode,
                      kWinners,
                      threshold,
                      min_accept_distance,
                      min_accept_norm,
                      min_proto_sum,
                      sigma)

    # Change its parameters
    sp.setSparsificationMode(1)
    sp.setDoNormalization(1)
    sp.setNorm(1.5)
    sp.setKWinners(2)
    sp.setMinAcceptDistance(.001)
    sp.setMinAcceptNorm(.001)
    sp.setSigma(.414)

    # Learn
    for _ in range(0, 10):
        x = numpy.random.random((8))
        sp.learn(x)

    # Infer
    for _ in range(0, 10):
        x = numpy.random.random((8))
        sp.infer(x)

    # Access the stored prototypes
    print '\nNumber of prototypes\n', sp.getNPrototypes(0)
    print '\nPrototypes\n', sp.prototypes(0)

    # Persist the SparsePooler
    cPickle.dump(sp, open('test.txt', 'w'))
    sp2 = cPickle.load(open('test.txt', 'r'))

#--------------------------------------------------------------------------------
sparse_pooler_use_case()
