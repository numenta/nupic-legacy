#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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

import unittest2 as unittest

from nupic.regions.PyRegion import PyRegion
from nupic.engine import *

class PCANodeTest(unittest.TestCase):


  def testPCANode(self):
    rgen = numpy.random.RandomState(37)

    inputSize = 8

    net = Network()
    sensor = net.addRegion('sensor', 'py.ImageSensor' ,
          '{ width: %d, height: %d }' % (inputSize, inputSize))

    params = """{bottomUpCount: %d,
                SVDSampleCount: 5,
                SVDDimCount: 2}""" % inputSize

    pca = net.addRegion('pca', 'py.PCANode', params)

    #nodeAbove = CreateNode("py.ImageSensor", phase=0, categoryOut=1, dataOut=3,
    #                       width=3, height=1)
    #net.addElement('nodeAbove', nodeAbove)

    linkParams = '{ mapping: in, rfSize: [%d, %d] }' % (inputSize, inputSize)
    net.link('sensor', 'pca', 'UniformLink', linkParams, 'dataOut', 'bottomUpIn')

    net.initialize()

    for i in range(10):
      pca.getSelf()._testInputs = numpy.random.random([inputSize])
      net.run(1)
      #print s.sendRequest('nodeOPrint pca_node')



if __name__ == "__main__":
  unittest.main()
