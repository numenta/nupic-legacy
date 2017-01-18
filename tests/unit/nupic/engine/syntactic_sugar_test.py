# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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


import sys
import unittest2 as unittest
import nupic.engine as net



class NetworkSugarTest(unittest.TestCase):


  def testPhases(self):
    n = net.Network()
    self.assertEqual(n.minPhase, 0)
    self.assertEqual(n.maxPhase, 0)
    self.assertEqual(n.minEnabledPhase, 0)
    self.assertEqual(n.maxEnabledPhase, 0)

    _r1 = n.addRegion('r1', 'TestNode', '')
    _r2 = n.addRegion('r2', 'TestNode', '')

    self.assertEqual(n.minPhase, 0)
    self.assertEqual(n.maxPhase, 1)
    self.assertEqual(n.minEnabledPhase, 0)
    self.assertEqual(n.maxEnabledPhase, 1)

    n.setPhases('r1', (1, 4))
    n.setPhases('r2', (2, 3))
    self.assertEqual(n.minPhase, 1)
    self.assertEqual(n.maxPhase, 4)
    self.assertEqual(n.minEnabledPhase, 1)
    self.assertEqual(n.maxEnabledPhase, 4)

    n.minEnabledPhase = 2
    n.maxEnabledPhase = 3
    self.assertEqual(n.minPhase, 1)
    self.assertEqual(n.maxPhase, 4)
    self.assertEqual(n.minEnabledPhase, 2)
    self.assertEqual(n.maxEnabledPhase, 3)


  def testRegionCollection(self):
    n = net.Network()

    regions = n.regions
    self.assertEqual(len(regions), 0)

    r1 = n.addRegion('r1', 'TestNode', '')
    r2 = n.addRegion('r2', 'TestNode', '')
    self.assertTrue(r1 is not None)

    self.assertEqual(len(regions), 2)

    # test the 'in' operator
    self.assertTrue('r1' in regions)
    self.assertTrue('r2' in regions)
    self.assertFalse('r3' in regions)

    # test [] operator
    self.assertEqual(regions['r1'], r1)
    self.assertEqual(regions['r2'], r2)
    with self.assertRaises(KeyError):
      _ = regions['r3']

    # for iteration
    for i, r in enumerate(regions):
      if i == 0:
        self.assertEqual(r[0], 'r1')
      elif i == 1:
        self.assertEqual(r[0], 'r2')
      else:
        self.fail("Expected i == 0 or i == 1")

    # test .keys()
    keys = regions.keys()
    self.assertEqual(keys, set(['r1', 'r2']))

    # test .values()
    values = regions.values()
    self.assertEqual(len(values), 2)
    v1 = values.pop()
    v2 = values.pop()
    self.assertTrue((v1, v2) == (r1, r2) or (v1, v2) == (r2, r1))

    # test .items()
    items = regions.items()
    self.assertEqual(len(items), 2)
    i1 = items.pop()
    i2 = items.pop()
    self.assertTrue((i1, i2) == (('r1', r1), ('r2', r2)) or
                                 (('r2', r2), ('r1', r1)))


  @unittest.skipIf(sys.platform.lower().startswith("win"),
                   "Not supported on Windows, yet!")
  def testRegion(self):
    r = net.Network().addRegion('r', 'py.TestNode', '')

    print r.spec
    self.assertEqual(r.type, 'py.TestNode')
    self.assertEqual(r.name, 'r')
    self.assertTrue(r.dimensions.isUnspecified())


  @unittest.skipIf(sys.platform.lower().startswith("win"),
                   "Not supported on Windows, yet!")
  def testSpec(self):
    ns = net.Region.getSpecFromType('py.TestNode')
    self.assertEqual(ns.description,
                     'The node spec of the NuPIC 2 Python TestNode')

    n = net.Network()
    r = n.addRegion('r', 'py.TestNode', '')

    ns2 = r.spec
    self.assertEqual(ns.singleNodeOnly, ns2.singleNodeOnly)
    self.assertEqual(ns.description, ns2.description)
    self.assertEqual(ns.inputs, ns2.inputs)
    self.assertEqual(ns.outputs, ns2.outputs)
    self.assertEqual(ns.parameters, ns2.parameters)
    self.assertEqual(ns.commands, ns2.commands)


  def testTimer(self):
    t = net.Timer()
    self.assertEqual(t.elapsed, 0)
    self.assertEqual(t.startCount, 0)
    self.assertEqual(str(t), "[Elapsed: 0 Starts: 0]")
    t.start()
    # Dummy time
    _j = 0
    for i in xrange(0, 1000):
      _j = i
    t.stop()
    self.assertTrue(t.elapsed > 0)
    self.assertEqual(t.startCount, 1)



if __name__ == "__main__":
  unittest.main()
