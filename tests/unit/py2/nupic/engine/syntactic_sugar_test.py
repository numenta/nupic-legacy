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

import nupic.engine as net



class NetworkSugarTest(unittest.TestCase):


  def testPhases(self):
    n = net.Network()
    assert n.minPhase == 0
    assert n.maxPhase == 0
    assert n.minEnabledPhase == 0
    assert n.maxEnabledPhase == 0

    r1 = n.addRegion('r1', 'TestNode', '')
    r2 = n.addRegion('r2', 'TestNode', '')

    assert n.minPhase == 0
    assert n.maxPhase == 1
    assert n.minEnabledPhase == 0
    assert n.maxEnabledPhase == 1

    n.setPhases('r1', (1, 4))
    n.setPhases('r2', (2, 3))
    assert n.minPhase == 1
    assert n.maxPhase == 4
    assert n.minEnabledPhase == 1
    assert n.maxEnabledPhase == 4

    n.minEnabledPhase = 2
    n.maxEnabledPhase = 3
    assert n.minPhase == 1
    assert n.maxPhase == 4
    assert n.minEnabledPhase == 2
    assert n.maxEnabledPhase == 3


  def testRegionCollection(self):
    n = net.Network()

    regions = n.regions
    assert len(regions) == 0

    r1 = n.addRegion('r1', 'TestNode', '')
    r2 = n.addRegion('r2', 'TestNode', '')
    assert r1 is not None

    assert len(regions) == 2

    # test the 'in' operator
    assert 'r1' in regions
    assert 'r2' in regions
    assert not 'r3' in regions

    # test [] operator
    assert regions['r1'] == r1
    assert regions['r2'] == r2
    try:
      regions['r3']
      assert False
    except KeyError:
      pass

    # for iteration
    for i, r in enumerate(regions):
      if i == 0:
        assert r == 'r1'
      elif i == 1:
        assert r == 'r2'
      else:
        assert False

    # test .keys()
    keys = regions.keys()
    assert keys == set(['r1', 'r2'])

    # test .values()
    values = regions.values()
    assert len(values) == 2
    v1 = values.pop()
    v2 = values.pop()
    assert (v1, v2) == (r1, r2) or (v1, v2) == (r2, r1)

    # test .items()
    items = regions.items()
    assert len(items) == 2
    i1 = items.pop()
    i2 = items.pop()
    assert (i1, i2) == (('r1', r1), ('r2',r2)) or (('r2',r2), ('r1', r1))


  def testRegion(self):
    r = net.Network().addRegion('r', 'py.TestNode', '')

    print r.spec
    assert r.type == 'py.TestNode'
    assert r.name == 'r'
    assert r.dimensions.isUnspecified()


  def testSpec(self):
    ns = net.Region.getSpecFromType('py.TestNode')
    assert ns.description == 'The node spec of the NuPIC 2 Python TestNode'

    n = net.Network()
    r = n.addRegion('r', 'py.TestNode', '')

    ns2 = r.spec
    assert ns.singleNodeOnly == ns2.singleNodeOnly
    assert ns.description == ns2.description
    assert ns.inputs == ns2.inputs
    assert ns.outputs == ns2.outputs
    assert ns.parameters == ns2.parameters
    assert ns.commands == ns2.commands


  def testTimer(self):
    t = net.Timer()
    assert t.elapsed == 0
    assert t.startCount == 0
    assert str(t) == "[Elapsed: 0 Starts: 0]"
    t.start()
    # Dummy time
    j = 0
    for i in xrange(0, 1000):
      j = i
    t.stop()
    assert t.elapsed > 0
    assert t.startCount == 1



if __name__ == "__main__":
  unittest.main()
