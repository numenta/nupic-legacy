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

"""Test for serializing NuPIC networks."""

import filecmp
import json
import logging
import os

import unittest2 as unittest

from nupic.engine import Network, Dimensions

_LOGGER = logging.getLogger(__name__)



class NetworkSerializationTest(unittest.TestCase):


  def testSerialization(self):
    n = Network()

    imageDims = (42, 38)
    params = dict(
      width=imageDims[0],
      height=imageDims[1],
      mode="bw",
      background=1,
      invertOutput=1)

    sensor = n.addRegion("sensor", "py.ImageSensor", json.dumps(params))
    sensor.setDimensions(Dimensions(imageDims[0], imageDims[1]))

    params = dict(
      inputShape=imageDims,
      coincidencesShape=imageDims,
      disableTemporal=1,
      tpSeed=43,
      spSeed=42,
      nCellsPerCol=1)

    l1 = n.addRegion("l1", "py.CLARegion", json.dumps(params))

    params = dict(
      maxCategoryCount=48,
      SVDSampleCount=400,
      SVDDimCount=5,
      distanceNorm=0.6)

    _classifier = n.addRegion("classifier", "py.KNNClassifierRegion",
                              json.dumps(params))

    # TODO: link params should not be required. Dest region dimensions are
    # already specified as [1]
    params = dict(
      mapping="in",
      rfSize=imageDims)

    n.link("sensor", "l1", "UniformLink", json.dumps(params))
    n.link("l1", "classifier", "UniformLink", "", "bottomUpOut", "bottomUpIn")
    n.link("sensor", "classifier", "UniformLink", "", "categoryOut",
           "categoryIn")
    n.initialize()

    n.save("fdr.nta")

    # Make sure the network bundle has all the expected files
    self.assertTrue(os.path.exists("fdr.nta/network.yaml"))
    self.assertTrue(os.path.exists("fdr.nta/R0-pkl"))
    self.assertTrue(os.path.exists("fdr.nta/R1-pkl"))
    self.assertTrue(os.path.exists("fdr.nta/R2-pkl"))

    n2 = Network("fdr.nta")
    n2.initialize()  # should not fail

    # Make sure the network is actually the same
    sensor = n2.regions['sensor']
    self.assertEqual(sensor.type, "py.ImageSensor")
    # would like to directly compare, but can't -- NPC-6
    self.assertEqual(str(sensor.dimensions), str(Dimensions(42, 38)))
    self.assertEqual(sensor.getParameter("width"), 42)
    self.assertEqual(sensor.getParameter("height"), 38)
    self.assertEqual(sensor.getParameter("mode"), "bw")
    self.assertEqual(sensor.getParameter("background"), 1)
    self.assertEqual(sensor.getParameter("invertOutput"), 1)

    l1 = n2.regions['l1']
    self.assertEqual(l1.type, "py.CLARegion")
    self.assertEqual(str(l1.dimensions), str(Dimensions(1)))
    a = l1.getParameter("inputShape")
    self.assertEqual(len(a), 2)
    self.assertEqual(a[0], 42)
    self.assertEqual(a[1], 38)

    a = l1.getParameter("coincidencesShape")
    self.assertEqual(len(a), 2)
    self.assertEqual(a[0], 42)
    self.assertEqual(a[1], 38)

    self.assertEqual(l1.getParameter("disableTemporal"), 1)
    self.assertEqual(l1.getParameter("spSeed"), 42)
    self.assertEqual(l1.getParameter("tpSeed"), 43)

    cl = n2.regions['classifier']
    self.assertEqual(cl.type, "py.KNNClassifierRegion")
    self.assertEqual(cl.getParameter("maxCategoryCount"), 48)
    self.assertEqual(cl.getParameter("SVDSampleCount"), 400)
    self.assertEqual(cl.getParameter("SVDDimCount"), 5)
    self.assertLess((cl.getParameter("distanceNorm") - 0.6), 0.0001)
    self.assertEqual(str(cl.dimensions), str(Dimensions(1)))

    n2.save("fdr2.nta")

    # now compare the two network bundles -- should be the same
    c = filecmp.dircmp("fdr.nta", "fdr2.nta")
    self.assertEqual(len(c.left_only), 0,
                     "fdr.nta has extra files: %s" % c.left_only)

    self.assertEqual(len(c.right_only), 0,
                     "fdr2.nta has extra files: %s" % c.right_only)

    if len(c.diff_files) > 0:
      _LOGGER.warn("Some bundle files differ: %s\n"
                   "This is expected, as pickle.load() followed by "
                   "pickle.dump() doesn't produce the same file", c.diff_files)



if __name__ == "__main__":
  logging.basicConfig()
  unittest.main()
