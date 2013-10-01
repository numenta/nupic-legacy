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

"""Unit tests for sparse tensor."""

from time import time
import numpy
import cPickle
import unittest2 as unittest
import sys

from nupic.bindings.math import *


class TestSparseTensor(unittest.TestCase):

  def setUp(self):
    self.dtype = GetNTAReal()

  def test_Construction(self):
    x = SparseTensor((3, 4, 5))
    assert x.getBounds() == (3, 4, 5)
    print 'Construction tests passed.'

    assert x.get((2, 1, 0)) == 0
    x.set((2, 1, 0), 5)
    assert x.get((2, 1, 0)) == 5
    print 'Get and set tests passed.'

  def test_Timing(self):

    x = SparseTensor((3, 4, 5))
    start = time()

    for iter in xrange(1000):
      l = 0
      for i in xrange(3):
        for j in xrange(4):
          for k in xrange(5):
            x.set((i, j, k), l)
            l += 1

    end = time()
    print 'set:', (end - start), 's elapsed'

    start = time()
    for iter in xrange(1000):
      l = 0
      for i in xrange(3):
        for j in xrange(4):
          for k in xrange(5):
            assert l == x.get((i, j, k))
            l += 1

    end = time()
    print 'get:', (end - start), 's elapsed'

    start = time()
    for iter in xrange(1000):
      l = 0
      idx = TensorIndex(0, 0, 0)
      for i in xrange(3):
        idx[0] = i
        for j in xrange(4):
          idx[1] = j
          for k in xrange(5):
            idx[2] = k
            x.set(idx, l)
            l += 1

    end = time()
    print 'set-fixed:', (end - start), 's elapsed'

    start = time()
    for iter in xrange(1000):
      l = 0
      idx = TensorIndex(0, 0, 0)
      for i in xrange(3):
        idx[0] = i
        for j in xrange(4):
          idx[1] = j
          for k in xrange(5):
            idx[2] = k
            assert l == x.get(idx)
            l += 1

    end = time()
    print 'get-fixed:', (end - start), 's elapsed'

    print 'Timing tests passed.'

  def test_Slicing(self):

    x = SparseTensor((3, 4, 5))
    z = x.getSlice(Domain((0, 3, 0), (3, 3, 2)))
    print z
    print 'Slicing tests passed.'


    w = z.reshape((2, 3))
    print w
    print 'Reshaping tests passed.'


    w = z.reshape((2, 3))
    print z.marginalize((1, ))
    print z.max((1, ))

    print x.marginalize((0, 2))
    print x.max((0, 2))
    print 'Dimension reduction (marginalize and max) tests passed.'


  def test_BracketOperator(self):

    x = SparseTensor((3, 4, 5))

    assert x[2, 2, 1] == 0
    x[2, 2, 1] = 16.5
    assert x[2, 2, 1] == 16.5
    print 'Bracket operator tests passed.'

  def test_Pickling(self):

    x = SparseTensor((3, 4, 5))
    s = cPickle.dumps(x)
    print s
    print 'Pickling test passed.'

    y = cPickle.loads(s)
    print 'Unpickling test passed.'

    assert x == y
    print 'Equality test passed.'


    z = x.copy()
    assert z is not x
    assert z == x
    print 'Copy tests passed.'


    assert x[:,:,:].getBounds() == (3, 4, 5)
    assert x[2,:,:].getBounds() == (4, 5)
    assert x[:,2,:].getBounds() == (3, 5)
    assert x[:,:,2].getBounds() == (3, 4)
    assert x[:,0,2].getBounds() == (3,)
    assert x[2,:,0].getBounds() == (4,)
    assert x[2:3, 0:1, 1:2].getBounds() == (1, 1, 1)
    assert x[1:-1, 1:-2, 1:-3].getBounds() == (1, 1, 1)
    assert x[:-1, :-2, :-3].getBounds() == (2, 2, 2)
    assert x[-2:-1, -3:-2, -4:-3].getBounds() == (1, 1, 1)
    assert x[-2:-1, ..., -4:-3].getBounds() == (1, 4, 1)
    assert x[..., -4:-3].getBounds() == (3, 4, 1)
    assert x[-2:-1, ...].getBounds() == (1, 4, 5)
    assert x[...].getBounds() == (3, 4, 5)
    print 'Slicing tests passed.'

    x.resize((4, 5, 6))
    assert x.getBounds() == (4, 5, 6)
    print 'Resize tests passed.'

    x = SparseTensor((3, 3))
    y = SparseTensor((3, 3))

    x[0, 0] = 1
    y[0, 0] = 1

    z1 = x.factorMultiply((0, 1), y)

    z2 = x.factorAdd((0, 1), y)

    # Operations tests.
    x = SparseTensor((2, 3))
    x[0, 0] = 2
    x[1, 2] = 4
    y1 = x + x
    y2 = x * 2
    assert y1 == y2
    assert (x - x) == SparseTensor((2, 3))
    assert (x * 0) == SparseTensor((2, 3))
    assert ((x * 2.5) == (x + x + (x*0.5)))
    z = SparseTensor((2, 3))
    z[0, 0] = 4
    z[1, 2] = 16
    #assert ((x * x) == z)
    assert (x.factorMultiply(range(x.getRank()), x) == z)
    print 'Operations tests passed.'

    # Interaction with numpy arrays:
    y = numpy.array(((3, 4, 5), (6, 7, 8)))
    x = SparseTensor(y.astype(self.dtype))
    assert x.getBounds() == y.shape
    x.set((1, 1), y[1, 1])
    x[0, 0] = y[0, 0]
    assert (x.toDense() == y).all()

    y = numpy.array(((3.0, 4.0, 5.0), (6.0, 7.0, 8.0)), dtype=self.dtype)
    x = SparseTensor(y.astype(self.dtype))
    assert x.getBounds() == y.shape
    x.set((1, 1), y[1, 1])
    x[0, 0] = y[0, 0]
    assert (x.toDense() == y).all()

    y = numpy.array(((3.0, 4.0, 5.0), (6.0, 7.0, 8.0)))
    x = SparseTensor(y.astype(self.dtype))
    assert x.getBounds() == y.shape
    x.set((1, 1), y[1, 1])
    x[0, 0] = y[0, 0]
    assert (x.toDense() == y).all()
    print 'numpy tests passed.'


    # setSlice tests.
    x = SparseTensor((2, 3, 4))

    ones = SparseTensor(numpy.ones((2, 3, 4), dtype=self.dtype))

    x[...] = ones

    print 'x after setSlice:', x

    twos = SparseTensor(2*numpy.ones((2, 2, 2), dtype=self.dtype))

    x[:2,:2,:2] = twos

    print 'x (partially twos):', x

    x = SparseTensor((3, 4, 5))
    x[1:3, 1:3, 1:3] = SparseTensor(numpy.ones((2, 2, 2), dtype=self.dtype))
    assert x[0, 0, 0] == 0
    assert x[1, 1, 1] == 1

    print 'setSlice tests passed.'



if __name__ == "__main__":
  unittest.main()
