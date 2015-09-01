#!/usr/bin/env python
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

"""Unit tests for sparse binary matrix."""

import cPickle
import os

import numpy
import unittest2 as unittest

from nupic.bindings.math import SM32, SM_01_32_32

_RGEN = numpy.random.RandomState(37)



def error(str):
  print 'Error:', str



class UnitTests(unittest.TestCase):


  def setUp(self):
    self.Matrix = SM_01_32_32(1)


  def test_construction(self):
    a = self.Matrix.__class__(4)

    if a.nRows() != 0 or a.nCols() != 4:
      error('constructor 1')

    b = self.Matrix.__class__(a)
    if b.nRows() != 0 or b.nCols() != 4:
      error('constructor 2A')

    if (a.toDense() != b.toDense()).any():
      error('constructor 2B')

    m = _RGEN.randint(1,10)
    n = _RGEN.randint(5,10)
    a = self.Matrix.__class__(n)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = numpy.zeros((n))

    for i in range(m):
      a.appendSparseRow(numpy.where(x[i] > 0)[0].tolist())

    b = self.Matrix.__class__(a)
    if (a.toDense() != b.toDense()).any():
      error('copy constructor')

    c = self.Matrix.__class__(x)
    if (c.toDense() != x).any():
      error('constructor from numpy array')

    s = c.toCSR()
    d = self.Matrix.__class__(s)
    if (d.toDense() != x).any():
      error('constructor from csr string')

    # Test construction from a SM
    a = _RGEN.randint(0,10,(3,4))
    a[2] = 0
    a[:,3] = 0
    a = SM32(a)
    b = SM_01_32_32(a)
    a = a.toDense()
    w = numpy.where(a > 0)
    a[w] = 1
    if (a != b.toDense()).any():
      error('construction from SM')


  def testAccessors(self):
    m = _RGEN.randint(1,10)
    n = _RGEN.randint(5,10)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = 0
    a = self.Matrix.__class__(n)

    print a.getVersion(), a.getVersion(True)

    if a.nRows() != 0:
      error('nRows 1')

    if a.nCols() != n:
      error('nCols 1')

    for i in range(m):
      a.appendSparseRow(numpy.where(x[i] > 0)[0].tolist())

    if a.nRows() != m:
      error('nRows 2')

    if a.nCols() != n:
      error('nCols 2')

    if a.nNonZeros() != len(numpy.where(x > 0)[0]):
      error('nNonZeros')

    for i in range(m):
      if a.nNonZerosOnRow(i) != x.sum(axis=1)[i]:
        error('nNonZerosOnRow')

    if (a.nNonZerosPerRow() != x.sum(axis=1)).any():
      error('nNonZerosPerRow')

    if (a.nNonZerosPerCol() != x.sum(axis=0)).any():
      error('nNonZerosPerCol')

    for i in range(m):
      y = numpy.zeros((n))
      for j in a.getRowSparse(i):
        y[j] = 1
      if (y != x[i]).any():
        error('getRowSparse')

    if a.capacity() < a.nNonZeros():
      error('capacity')

    m = _RGEN.randint(100,200)
    n = _RGEN.randint(100,200)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = 0
    a = self.Matrix.__class__(x)

    m1 = a.nBytes()
    a.compact()
    m2 = a.nBytes()
    if (m2 > m1):
      error('compact')


  def testCopy(self):
    m = _RGEN.randint(1,10)
    n = _RGEN.randint(5,10)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = numpy.zeros((n))

    a = self.Matrix.__class__(x)
    b = self.Matrix.__class__(1)
    b.copy(a)

    if a != b:
      error('copy')


  def testClear(self):
    m = _RGEN.randint(1,10)
    n = _RGEN.randint(5,10)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = 0

    a = self.Matrix.__class__(x)

    a.clear()

    if a.capacity() != 0:
      error('clear /capacity')

    if a.nRows() != 0:
      error('clear /nRows')

    if a.nCols() != 0:
      error('clear /nCols')

    if a.nNonZeros() != 0:
      error('clear /nNonZeros')


  def testResize(self):
    # 1. Resize to 0,0 (equivalent to clear)

    m = _RGEN.randint(4,10)
    n = _RGEN.randint(6,10)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = 0
    a = self.Matrix.__class__(x)

    a.resize(0,0)

    if a.capacity() != 0:
      error('resize to 0,0 /capacity')

    if a.nRows() != 0:
      error('resize to 0,0 /nRows')

    if a.nCols() != 0:
      error('resize to 0,0 /nCols')

    if a.nNonZeros() != 0:
      error('resize to 0,0 /nNonZeros')

    # 2. Resize to larger size

    m = _RGEN.randint(4,10)
    n = _RGEN.randint(6,10)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = 0
    a = self.Matrix.__class__(x)

    # 2.1 More rows only

    old_nrows = a.nRows()
    old_ncols = a.nCols()
    old_nnzr = a.nNonZeros()
    a.resize(2*a.nRows(),a.nCols())

    if a.nRows() != 2*old_nrows or a.nCols() != old_ncols:
      error('resize to more rows, 1')

    if a.nNonZeros() != old_nnzr:
      error('resize to more rows, 2')

    # 2.2 More cols only

    old_nrows = a.nRows()
    a.resize(a.nRows(), 2*a.nCols())

    if a.nRows() != old_nrows or a.nCols() != 2*old_ncols:
      error('resize to more cols, 1')

    if a.nNonZeros() != old_nnzr:
      error('resize to more cols, 2')

    # 2.3 More rows and cols

    m = _RGEN.randint(4,10)
    n = _RGEN.randint(6,10)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = 0
    a = self.Matrix.__class__(x)
    old_nrows = a.nRows()
    old_ncols = a.nCols()
    old_nnzr = a.nNonZeros()
    a.resize(2*a.nRows(),2*a.nCols())

    if a.nRows() != 2*old_nrows or a.nCols() != 2*old_ncols:
      error('resize to more rows and cols, 1')

    if a.nNonZeros() != old_nnzr:
      error('resize to more rows and cols, 2')

    # 3. Resize to smaller size
    m = _RGEN.randint(10,20)
    n = _RGEN.randint(10,20)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = 0
    a = self.Matrix.__class__(x)

    # 3.1 Less rows only

    old_nrows = a.nRows()
    old_ncols = a.nCols()
    old_nnzr = a.nNonZeros()
    a.resize(a.nRows()/2,a.nCols())

    if a.nRows() != old_nrows/2 or a.nCols() != old_ncols:
      error('resize to less rows, 1')

    if a.nNonZeros() != numpy.sum(x[:old_nrows/2]):
      error('resize to less rows, 2')

    # 2.2 Less cols only

    old_nrows = a.nRows()
    a.resize(a.nRows(), a.nCols()/2)

    if a.nRows() != old_nrows or a.nCols() != old_ncols/2:
      error('resize to less cols, 1')

    if a.nNonZeros() != numpy.sum(x[:a.nRows(),:old_ncols/2]):
      error('resize to less cols, 2')

    # 2.3 Less rows and cols

    m = _RGEN.randint(10,20)
    n = _RGEN.randint(10,20)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = 0
    a = self.Matrix.__class__(x)
    old_nrows = a.nRows()
    old_ncols = a.nCols()
    old_nnzr = a.nNonZeros()
    a.resize(a.nRows()/2,a.nCols()/2)

    if a.nRows() != old_nrows/2 or a.nCols() != old_ncols/2:
      error('resize to less rows and cols, 1')

    if a.nNonZeros() != numpy.sum(x[:old_nrows/2,:old_ncols/2]):
      error('resize to less rows and cols, 2')


  def testEquals(self):
    m = _RGEN.randint(1,10)
    n = _RGEN.randint(5,10)
    a = self.Matrix.__class__(n)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = numpy.zeros((n))

    a = self.Matrix.__class__(x)
    b = self.Matrix.__class__(x)

    if a != b:
      error('equals 1')

    b.set(m/2, n/2, 1)

    if a == b:
      error('equals 2')


  def testSet(self):
    m = _RGEN.randint(1,10)
    n = _RGEN.randint(5,10)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = numpy.zeros((n))

    a = self.Matrix.__class__(x)

    a.set(m/2, [0, 2, 4], 1)
    x[m/2,0] = 1
    x[m/2,2] = 1
    x[m/2,4] = 1
    if (a != x).any():
      error('set on row 1')

    a.set(m/2, [0,2,4], 0)
    x[m/2,0] = 0
    x[m/2,2] = 0
    x[m/2,4] = 0
    if (a != x).any():
      error('set on row 1')

    m = _RGEN.randint(1,10)
    n = _RGEN.randint(5,10)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = numpy.zeros((n))

    a = self.Matrix.__class__(x)

    a.setForAllRows([0,2,4], 1)
    for i in range(m):
      x[i,0] = 1
      x[i,2] = 1
      x[i,4] = 1
    if (a != x).any():
      error('set for all rows')


  def testGetAllNonZeros(self):
    for i in range(10):
      m = _RGEN.randint(2,10)
      n = _RGEN.randint(2,10)
      a = _RGEN.randint(0,2,(m,n))
      a[_RGEN.randint(0,m)] = 0
      a[:,_RGEN.randint(0,n)] = 0
      sm = self.Matrix.__class__(a)

      ans_ind = numpy.where(a > 0)
      ans_val = a[ans_ind]
      ans = [(i,j,v) for i,j,v in zip(ans_ind[0], ans_ind[1], ans_val)]

      # Returns one list of pairs by default
      all_nz = sm.getAllNonZeros()

      for x,y in zip(all_nz, ans):
        if x[0] != y[0] or x[1] != y[1]:
          error('getAllNonZeros 1 list of pairs')

      # Test option to return 2 lists instead of 1 list of pairs
      all_nz2 = sm.getAllNonZeros(True)

      for i in range(len(ans_val)):
        if all_nz2[0][i] != ans_ind[0][i] or all_nz2[1][i] != ans_ind[1][i]:
          error('getAllNonZeros 2 lists')


  def testSetAllNonZeros(self):
    for i in range(10):

      m = _RGEN.randint(2,10)
      n = _RGEN.randint(2,10)
      a = _RGEN.randint(0,2,(m,n))
      a[_RGEN.randint(0,m)] = 0
      a[:,_RGEN.randint(0,n)] = 0
      a[0,0] = 1
      a[m-1] = 0
      a[:,n-1] = 0

      nz = numpy.where(a > 0)
      sm = self.Matrix.__class__(1)

      # Assumes lexicographic order of the indices by default
      sm.setAllNonZeros(a.shape[0], a.shape[1], nz[0],nz[1])

      if (sm.toDense() != a).any():
        error('setAllNonZeros, in order')

      # Test when values come in out of (lexicographic) order
      # and with duplicates
      p = _RGEN.permutation(len(nz[0]))
      nz_i2,nz_j2 = [],[]
      for i in p:
        nz_i2.append(nz[0][i])
        nz_j2.append(nz[1][i])
      for i in p:
        nz_i2.append(nz[0][i])
        nz_j2.append(nz[1][i])

      sm2 = self.Matrix.__class__(1)
      sm2.setAllNonZeros(a.shape[0], a.shape[1], nz_i2,nz_j2, False)

      if (sm2.toDense() != a).any():
        error('setAllNonZeros, out of order')


  def testGetCol(self):
    for i in range(10):

      m = _RGEN.randint(2,10)
      n = _RGEN.randint(2,10)
      a = _RGEN.randint(0,2,(m,n)).astype(numpy.float32)
      a[_RGEN.randint(0,m)] = 0
      a[:,_RGEN.randint(0,n)] = 0
      a[0,0] = 1
      a[m/2] = 0
      a[:,n/2] = 0

      sm = self.Matrix.__class__(a)

      for j in range(n):
        if (sm.getCol(j) != a[:,j]).any():
          error('getCol')


  def testSetSlice(self):
    # With a sparse matrix
    for i in range(10):

      m = _RGEN.randint(10,20)
      n = _RGEN.randint(10,20)
      a = _RGEN.randint(0,2,(m,n)).astype(numpy.float32)
      a[_RGEN.randint(0,m)] = 0
      a[:,_RGEN.randint(0,n)] = 0
      a[0,0] = 1
      a[m/2] = 0
      a[:,n/2] = 0

      sm = self.Matrix.__class__(a)

      b = _RGEN.randint(0,2,(m/4,n/4)).astype(numpy.float32)
      slice = self.Matrix.__class__(b)
      x,y = _RGEN.randint(0,m/2), _RGEN.randint(0,n/2)

      sm.setSlice(x,y,slice)

      ans = numpy.array(a)
      for i in range(b.shape[0]):
        for j in range(b.shape[1]):
          ans[x+i,y+j] = slice.get(i,j)

      if (sm.toDense() != ans).any():
        error('setSlice')

    # With a numpy array
    for i in range(10):

      m = _RGEN.randint(10,20)
      n = _RGEN.randint(10,20)
      a = _RGEN.randint(0,2,(m,n)).astype(numpy.float32)
      a[_RGEN.randint(0,m)] = 0
      a[:,_RGEN.randint(0,n)] = 0
      a[numpy.where(a < 25)] = 0
      a[0,0] = 1
      a[m/2] = 0
      a[:,n/2] = 0

      sm = self.Matrix.__class__(a)

      slice = _RGEN.randint(0,2,(m/4,n/4)).astype(numpy.float32)
      x,y = _RGEN.randint(0,m/2), _RGEN.randint(0,n/2)

      sm.setSlice(x,y,slice)

      ans = numpy.array(a)
      for i in range(slice.shape[0]):
        for j in range(slice.shape[1]):
          ans[x+i,y+j] = slice[i,j]

      if (sm.toDense() != ans).any():
        error('setSlice/dense')


  def testNNonZerosPerBox(self):
    for i in range(10):
      m = _RGEN.randint(2,10)
      n = _RGEN.randint(2,10)
      a = _RGEN.randint(0,2,(m,n)).astype(numpy.float32)
      a[_RGEN.randint(0,m)] = 0
      a[:,_RGEN.randint(0,n)] = 0
      a[0,0] = 1
      a[m/2] = 0
      a[:,n/2] = 0

      sm = self.Matrix.__class__(a)

      nnzpb = sm.nNonZerosPerBox([m/2, m], [n/2, n])
      ans = numpy.zeros((2,2))
      ans[0,0] = numpy.sum(a[:m/2,:n/2])
      ans[0,1] = numpy.sum(a[:m/2,n/2:])
      ans[1,0] = numpy.sum(a[m/2:,:n/2])
      ans[1,1] = numpy.sum(a[m/2:,n/2:])
      if (nnzpb.toDense() != ans).any():
        error('nNonZerosPerBox')


  def testAppendSparseRow(self):
    m = _RGEN.randint(1,10)
    n = _RGEN.randint(5,10)
    a = self.Matrix.__class__(n)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = numpy.zeros((n))

    for i in range(m):
      a.appendSparseRow(numpy.where(x[i] > 0)[0].tolist())

    if (a.toDense() != x).any():
      error('appendSparseRow')

    if a.nRows() != m:
      error('appendSparseRow nRows')

    if (numpy.array(a.nNonZerosPerRow()) != x.sum(axis=1)).any():
      error('appendSparseRow nNonZerosPerRow')

    if a.nNonZeros() != len(numpy.where(x > 0)[0]):
      error('appendSparseRow nNonZeros')


  def testAppendDenseRow(self):
    m = _RGEN.randint(1,10)
    n = _RGEN.randint(5,10)
    a = self.Matrix.__class__(n)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = numpy.zeros((n))

    for i in range(m):
      a.appendDenseRow(x[i])

    if (a.toDense() != x).any():
      error('appendDenseRow')

    if a.nRows() != m:
      error('appendDenseRow nRows')

    if (numpy.array(a.nNonZerosPerRow()) != x.sum(axis=1)).any():
      error('appendDenseRow nNonZerosPerRow')

    if a.nNonZeros() != len(numpy.where(x > 0)[0]):
      error('appendDenseRow nNonZeros')


  def testReplaceSparseRow(self):
    m = _RGEN.randint(1,10)
    n = _RGEN.randint(5,10)
    a = self.Matrix.__class__(n)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = numpy.zeros((n))

    for i in range(m):
      a.appendSparseRow(numpy.where(x[i] > 0)[0].tolist())

    for i in range(m):
      x[i] = _RGEN.randint(0,2,(n))
      a.replaceSparseRow(i, numpy.where(x[i] > 0)[0].tolist())

      if (a.toDense() != x).any():
        error('replaceSparseRow')

      if (numpy.array(a.nNonZerosPerRow()) != x.sum(axis=1)).any():
        error('replaceSparseRow nNonZerosPerRow')

    if a.nNonZeros() != len(numpy.where(x > 0)[0]):
      error('replaceSparseRow nNonZeros')

    if a.nRows() != m:
      error('replaceSparseRow nRows')


  def testFindRowSparse(self):
    m = _RGEN.randint(1,10)
    n = _RGEN.randint(5,10)
    a = self.Matrix.__class__(n)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = numpy.zeros((n))

    for i in range(m):
      a.appendSparseRow(numpy.where(x[i] > 0)[0].tolist())

    for i in range(m):
      w = a.findRowSparse(numpy.where(x[i] > 0)[0].tolist())
      if (x[w] != x[i]).any():
        error('findRowSparse')


  def testFindRowDense(self):
    m = _RGEN.randint(1,10)
    n = _RGEN.randint(5,10)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = numpy.zeros((n))
    a = self.Matrix.__class__(x)

    for i in range(m):
      w = a.findRowDense(x[i])
      if (x[w] != x[i]).any():
        error('findRowDense')


  def testGet(self):
    m = _RGEN.randint(1,10)
    n = _RGEN.randint(5,10)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = numpy.zeros((n))

    a = self.Matrix.__class__(n)
    a.fromDense(x)

    for i in range(m):
      for j in range(n):
        if a.get(i,j) != x[i,j]:
          error('get')


  def testSet(self):
    m = _RGEN.randint(1,10)
    n = _RGEN.randint(5,10)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = 0

    a = self.Matrix.__class__(x)

    for i in range(m):
      for j in range(n):
        v = _RGEN.randint(0,2)
        a.set(i,j,v)
        x[i,j] = v

    if (a.toDense() != x).any():
      error('set')

    a.set(0,n-1,2)
    x[0,n-1] = 1
    if (a.toDense() != x).any():
      error('set 2')

    x[m/2] = 0
    a.fromDense(x)
    for j in range(n):
      a.set(m/2,j,1)
    x[m/2] = 1
    if (a.toDense() != x).any():
      error('set 3')


  def testSetRangeToZero(self):
    m = _RGEN.randint(1,10)
    n = _RGEN.randint(5,10)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = 0

    a = self.Matrix.__class__(n)
    a.fromDense(x)

    for i in range(m):

      begin = _RGEN.randint(0,n)
      end = _RGEN.randint(begin, n+1)
      a.setRangeToZero(i, begin, end)
      x[i][begin:end] = 0

      if (a.toDense() != x).any():
        error('setRangeToZero 1')

    a.setRangeToZero(0, 0, 0)
    if (a.toDense() != x).any():
      error('setRangeToZero 2')

    a.setRangeToZero(0, n, n)
    if (a.toDense() != x).any():
      error('setRangeToZero 3')

    a.setRangeToZero(0, 3, 3)
    if (a.toDense() != x).any():
      error('setRangeToZero 4')

    a.setRangeToZero(0, 0, n)
    x[0] = 0
    if (a.toDense() != x).any():
      error('setRangeToZero 5')


  def testSetRangeToOne(self):
    m = _RGEN.randint(1,10)
    n = _RGEN.randint(5,10)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = numpy.zeros((n))

    a = self.Matrix.__class__(n)
    a.fromDense(x)

    for i in range(m):

      begin = _RGEN.randint(0,n)
      end = _RGEN.randint(begin, n+1)
      a.setRangeToOne(i, begin, end)
      x[i][begin:end] = 1

      if (a.toDense() != x).any():
        error('setRangeToOne 1')

    a.setRangeToOne(0, 0, 0)
    if (a.toDense() != x).any():
      error('setRangeToOne 2')

    a.setRangeToOne(0, n, n)
    if (a.toDense() != x).any():
      error('setRangeToOne 3')

    a.setRangeToOne(0, 3, 3)
    if (a.toDense() != x).any():
      error('setRangeToOne 4')

    a.setRangeToOne(0, 0, n)
    x[0] = 1
    if (a.toDense() != x).any():
      error('setRangeToOne 5')


  def testTranspose(self):
    for k in range(10):

      m = _RGEN.randint(4,10)
      n = _RGEN.randint(5,10)
      a = self.Matrix.__class__(n)
      x = _RGEN.randint(0,2,(m,n))
      x[m/2] = 0
      x[:n/2] = 0

      for i in range(m):
        a.appendDenseRow(x[i])

      a.transpose()

      if (a.toDense() != numpy.transpose(x)).any():
        error('numpy.transpose')

      if (numpy.array(a.nNonZerosPerRow()) != x.sum(axis=0)).any():
        error('numpy.transpose nNonZerosPerRow')

      if a.nNonZeros() != len(numpy.where(x > 0)[0]):
        error('numpy.transpose nNonZeros')

      a.transpose()

      if (a.toDense() != x).any():
        error('numpy.transpose 2')

      if (numpy.array(a.nNonZerosPerRow()) != x.sum(axis=1)).any():
        error('numpy.transpose nNonZerosPerRow 2')

      if a.nNonZeros() != len(numpy.where(x > 0)[0]):
        error('numpy.transpose nNonZeros 2')

  def testCSR(self):
    m = _RGEN.randint(10,20)
    n = _RGEN.randint(10,20)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = 0
    x[:,n/2] = 0
    a = self.Matrix.__class__(x)

    csr = a.toCSR()
    b = self.Matrix.__class__(1)
    b.fromCSR(csr)

    if (a.toDense() != b.toDense()).any():
      error('toCSR/fromCSR')

    if (numpy.array(a.nNonZerosPerRow()) != numpy.array(b.nNonZerosPerRow())).any():
      error('toCSR/fromCSR nNonZerosPerRow')

    if b.nNonZeros() != len(numpy.where(x > 0)[0]):
      error('toCSR/fromCSR nNonZeros')


  def testGetstateSetstate(self):
    m = _RGEN.randint(10,20)
    n = _RGEN.randint(10,20)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = 0
    x[:,n/2] = 0
    a = self.Matrix.__class__(x)

    s = a.__getstate__()
    b = self.Matrix.__class__(1)
    b.__setstate__(s)

    if a != b:
      error('__geststate__/__setstate__')


  def testCSRToFromFile(self):
    m = _RGEN.randint(10,20)
    n = _RGEN.randint(10,20)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = 0
    x[:,n/2] = 0
    a = self.Matrix.__class__(x)

    a.CSRSaveToFile('test_csr2.txt')
    b = self.Matrix.__class__(1)
    b.CSRLoadFromFile('test_csr2.txt')

    if a != b:
      error('CSRSaveToFile/CSRLoadFromFile')

    os.unlink('test_csr2.txt')


  def testCSRSize(self):
    for k in range(5):
      m = _RGEN.randint(10,100)
      n = _RGEN.randint(10,100)
      x = _RGEN.randint(0,100,(m,n))
      x[m/2] = 0
      a = self.Matrix.__class__(x)

      for i in range(10):

        s_estimated = a.CSRSize()
        a.CSRSaveToFile('test_csr.txt')
        s_real = os.path.getsize('test_csr.txt')
        if s_estimated != s_real:
          error('CSRSize')

        for j in range(1000):
          a.set(_RGEN.randint(0,m),_RGEN.randint(0,n), 0)

    os.unlink('test_csr.txt')


  def testBinary(self):
    m = _RGEN.randint(10,20)
    n = _RGEN.randint(10,20)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = 0
    x[:,n/2] = 0
    a = self.Matrix.__class__(x)

    a.binarySaveToFile('test_binary.bin')

    b = self.Matrix.__class__(1)
    b.binaryLoadFromFile('test_binary.bin')

    if a != b:
      error('binarySaveToFile/binaryLoadFromFile')

    os.unlink('test_binary.bin')


  def testToFromSparseVector(self):
    m = _RGEN.randint(1,10)
    n = _RGEN.randint(5,10)
    a = self.Matrix.__class__(1)

    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = numpy.zeros((n))

    x = x.reshape((m*n))
    indices = numpy.where(x > 0)[0].tolist()
    a.fromSparseVector(m, n, indices)

    x = x.reshape((m,n))

    if (a.toDense() != x).any():
      error('fromSparseVector')

    if (numpy.array(a.nNonZerosPerRow()) != x.sum(axis=1)).any():
      error('fromSparseVector nNonZerosPerRow')

    if a.nNonZeros() != len(numpy.where(x > 0)[0]):
      error('fromSparseVector nNonZeros')

    x = x.reshape(m*n)
    y = a.toSparseVector()

    if (y != numpy.where(x > 0)[0].tolist()).any():
      error('toSparseVector')

    if a.nNonZeros() != len(numpy.where(x > 0)[0]):
      error('toSparseVector nNonZeros 2')

    # Need to make the same matrix can go through
    # fromSparseVector again with a different x
    x = _RGEN.randint(0,2,(n,m))

    x = x.reshape((m*n))
    indices = numpy.where(x > 0)[0].tolist()
    a.fromSparseVector(n, m, indices)

    x = x.reshape((n, m))

    if (a.toDense() != x).any():
      error('fromSparseVector 2')

    if (numpy.array(a.nNonZerosPerRow()) != x.sum(axis=1)).any():
      error('fromSparseVector nNonZerosPerRow 2')

    if a.nNonZeros() != len(numpy.where(x > 0)[0]):
      error('fromSparseVector nNonZeros 2')

    x = x.reshape(m*n)
    y = a.toSparseVector()

    if (y != numpy.where(x > 0)[0].tolist()).any():
      error('toSparseVector 2')

    if a.nNonZeros() != len(numpy.where(x > 0)[0]):
      error('toSparseVector nNonZeros 2')


  def testToFromDense(self):
    m = _RGEN.randint(1,10)
    n = _RGEN.randint(5,10)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = numpy.zeros((n))

    a = self.Matrix.__class__(1)
    a.fromDense(x)

    if (a.toDense() != x).any():
      error('fromDense')

    if (numpy.array(a.nNonZerosPerRow()) != x.sum(axis=1)).any():
      error('fromDense nNonZerosPerRow')

    if a.nNonZeros() != len(numpy.where(x > 0)[0]):
      error('fromDense nNonZeros')

    # Need to make sure the same matrix can go
    # through another fromDense with a different x
    x = _RGEN.randint(0,2,(n,m))
    a.fromDense(x)

    if (a.toDense() != x).any():
      error('fromDense 2')

    if (numpy.array(a.nNonZerosPerRow()) != x.sum(axis=1)).any():
      error('fromDense nNonZerosPerRow 2')

    if a.nNonZeros() != len(numpy.where(x > 0)[0]):
      error('fromDense nNonZeros 2')


  def testRowToFromDense(self):
    m = _RGEN.randint(1,10)
    n = _RGEN.randint(5,10)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = numpy.zeros((n))
    b = numpy.zeros((m,n))

    a = self.Matrix.__class__(n)

    for i in range(m):
      a.appendDenseRow(numpy.zeros((n)))
      a.rowFromDense(i, x[i])

    if (a.toDense() != x).any():
      error('rowFromDense')

    for i in range(m):
      b[i] = a.rowToDense(i)

    if (b != x).any():
      error('rowToDense')


  def testLogicalNot(self):
    m = _RGEN.randint(1,10)
    n = _RGEN.randint(5,10)
    a = self.Matrix.__class__(n)
    x = _RGEN.randint(0,2,(m,n))
    x[m/2] = numpy.zeros((n))

    for i in range(m):
      a.appendSparseRow(numpy.where(x[i] > 0)[0].tolist())

    a.logicalNot()
    y = 1 - x

    if (a.toDense() != y).any():
      error('logicalNot')


  def testLogicalOr(self):
    show = False

    a = self.Matrix.__class__(1)
    a.fromDense([[0,0,1,1,1,0,0],
           [0,1,0,0,0,1,0],
           [0,1,0,0,0,1,0],
           [0,0,1,1,1,0,0]])

    b = self.Matrix.__class__(1)
    b.fromDense([[0,0,0,0,0,0,0],
           [0,0,1,1,1,0,0],
           [0,0,1,1,1,0,0],
           [0,0,0,0,0,0,0]])

    a.logicalOr(b)
    if show: print a
    a.logicalOr(a)
    if show: print a

    a = self.Matrix.__class__(1)
    a.fromDense([[0,0,1,1,1,0,0],
           [0,1,0,0,0,1,0],
           [0,1,0,0,0,1,0],
           [0,0,1,1,1,0,0]])

    b = self.Matrix.__class__(1)
    b.fromDense([[0,0,0,0,0,0,0],
           [0,0,1,1,1,0,0],
           [0,0,1,1,1,0,0],
           [0,0,0,0,0,0,0]])

    b.logicalNot()
    if show: print b
    b.logicalOr(a)
    if show: print b

    a = self.Matrix.__class__([[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
                ,[1,1,1,1,1,0,0,0,0,0,0,0,0,0,1]
                ,[1,1,1,1,0,0,0,0,0,0,0,0,0,0,1]
                ,[1,0,0,0,0,0,0,0,0,0,0,0,0,0,1]
                ,[1,0,0,0,0,0,0,0,0,0,0,0,0,0,1]
                ,[1,0,0,0,0,0,0,0,0,0,0,0,0,0,1]
                ,[1,0,0,0,0,0,0,0,0,0,0,0,0,0,1]
                ,[1,0,0,0,0,0,0,0,0,0,0,0,0,0,1]
                ,[1,0,0,0,0,0,0,0,0,0,0,0,0,0,1]
                ,[1,0,0,0,0,0,0,1,1,1,1,1,0,0,1]
                ,[1,0,0,0,1,1,1,1,1,1,1,1,0,0,1]
                ,[1,0,0,0,0,1,1,1,1,1,1,0,0,0,1]
                ,[1,0,0,0,0,0,0,1,1,1,0,0,0,0,1]
                ,[1,0,0,0,0,0,0,1,1,1,0,0,0,0,1]
                ,[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]])
    a.logicalNot()
    if show: print a
    b = self.Matrix.__class__(a)
    b.inside()
    if show: print b
    a.logicalOr(b)
    if show: print a


  def testLogicalAnd(self):
    show = False

    a = self.Matrix.__class__(1)
    a.fromDense([[0,0,1,1,1,0,0],
           [0,1,0,0,0,1,0],
           [0,1,0,0,0,1,0],
           [0,0,1,1,1,0,0]])

    b = self.Matrix.__class__(1)
    b.fromDense([[0,0,0,0,0,0,0],
           [0,0,1,1,1,0,0],
           [0,0,1,1,1,0,0],
           [0,0,0,0,0,0,0]])

    a.logicalAnd(b)
    if show: print a
    a.logicalAnd(a)
    if show: print a

    a = self.Matrix.__class__(1)
    a.fromDense([[0,0,1,1,1,0,0],
           [0,1,0,0,0,1,0],
           [0,1,0,0,0,1,0],
           [0,0,1,1,1,0,0]])

    b = self.Matrix.__class__(1)
    b.fromDense([[0,0,0,0,0,0,0],
           [0,0,1,1,1,0,0],
           [0,0,1,1,1,0,0],
           [0,0,0,0,0,0,0]])

    b.logicalNot()
    if show: print b
    b.logicalAnd(a)
    if show: print b


  def testOverlap(self):
    x = [[0,1,1,0,0,1],
       [1,1,1,1,1,1],
       [0,0,0,0,0,0],
       [1,0,1,0,1,0],
       [1,1,1,0,0,0],
       [0,0,0,1,1,1],
       [1,1,0,0,1,1]]

    ans = [[3,3,0,1,2,1,2],
         [3,6,0,3,3,3,4],
         [0,0,0,0,0,0,0],
         [1,3,0,3,2,1,2],
         [2,3,0,2,3,0,2],
         [1,3,0,1,0,3,2],
         [2,4,0,2,2,2,4]]

    a = self.Matrix.__class__(1)
    a.fromDense(x)

    for xv,yv in zip(x,ans):
      y = a.overlap(xv)
      if (y != yv).any():
        error('overlap')


  def testMaxAllowedOverlap(self):
    for i in range(10):

      m = _RGEN.randint(5,10)
      maxDistance = .5
      n = _RGEN.randint(10,20)
      x = _RGEN.randint(0,2,(m,n))
      a = self.Matrix.__class__(1)
      a.fromDense(x)

      for i in range(10):

        coinc = _RGEN.randint(0,2,(n))
        overlaps = a.overlap(coinc)
        longSums = numpy.maximum(a.rowSums(), coinc.sum())
        maxAllowedOverlaps = (1.0 - maxDistance) * longSums
        py_accepted = True
        if (overlaps > maxAllowedOverlaps).any():
          py_accepted = False

        if a.maxAllowedOverlap(maxDistance, coinc) != py_accepted:
          error('maxAllowedOverlap')


  def testSubtract(self):
    a = numpy.array([[0,1,0],
                     [1,0,1],
                     [0,1,0]])

    b = numpy.array([[1,1,1],
                     [1,0,1],
                     [1,1,1]])

    c = b - a
    a = self.Matrix.__class__(a)
    b = self.Matrix.__class__(b)
    a.logicalNot()
    b.logicalAnd(a)

    if (c != b.toDense()).any():
      error('subtract')


  def testInsideAndEdges(self):
    show = False

    def printSideBySide(before, after):

      for i in range(before.nRows()):
        line = ''
        for j in range(before.nCols()):
          line += '#' if before.get(i,j) == 1 else '.'
        line += ' -> '
        for j in range(before.nCols()):
          line += '#' if after.get(i,j) == 1 else '.'
        print line
      print


    def sideBySide(a, edges=False):
      a = self.Matrix.__class__(a)
      orig = self.Matrix.__class__(a)
      if edges:
        a.edges(2)
      else:
        a.inside()
      if show:
        printSideBySide(orig, a)

    for edges in [False, True]:

      sideBySide([[0,0,0,0,0,0],
              [0,0,0,0,0,0],
              [0,0,0,0,0,0]], edges)

      sideBySide([[1,1,1,1,1,1],
              [1,0,0,0,0,1],
              [1,1,1,1,1,1]], edges)

      sideBySide([[1,1,1,1,1,1],
              [1,1,0,0,0,1],
              [1,1,1,1,1,1]], edges)

      sideBySide([[1,1,1,1,1,1],
              [1,1,0,0,1,1],
              [1,1,1,1,1,1]], edges)

      sideBySide([[1,1,1,1,1,1],
              [1,1,1,0,0,1],
              [1,1,1,1,1,1]], edges)

      sideBySide([[1,1,1,1,1,1],
              [1,1,1,0,1,1],
              [1,1,1,1,1,1]], edges)

      sideBySide([[1,1,1,1,1,1],
              [1,1,1,1,1,1],
              [1,1,1,1,1,1]], edges)

      sideBySide([[0,0,0,0,0,0,0,0],
              [0,1,1,1,1,1,1,0],
              [0,1,0,0,0,0,1,0],
              [0,1,1,1,1,1,1,0],
              [0,0,0,0,0,0,0,0]], edges)

      sideBySide([[0,0,0,0,0,0,0,0],
              [0,1,1,1,1,1,1,0],
              [0,1,0,0,0,0,1,0],
              [0,1,0,0,0,0,1,0],
              [0,1,1,1,1,1,1,0],
              [0,0,0,0,0,0,0,0]], edges)

      sideBySide([[0,0,0,0,0,0,0,0],
              [0,1,1,1,1,1,1,0],
              [0,1,1,0,0,0,1,0],
              [0,1,1,0,0,0,1,0],
              [0,1,1,1,1,1,1,0],
              [0,0,0,0,0,0,0,0]], edges)

      sideBySide([[0,0,0,0,0,0,0,0],
              [0,1,1,1,1,1,1,0],
              [0,1,1,1,0,0,1,0],
              [0,1,1,1,0,0,1,0],
              [0,1,1,1,1,1,1,0],
              [0,0,0,0,0,0,0,0]], edges)

      sideBySide([[1,1,1,1,1,1,0],
              [1,1,1,1,0,0,1],
              [1,1,0,0,0,0,1],
              [0,1,1,1,1,1,0]], edges)

      sideBySide([[0,0,1,1,1,0,0],
              [0,1,0,0,0,1,0],
              [0,1,0,0,0,1,0],
              [0,0,1,1,1,0,0]], edges)

      sideBySide([[0,0,1,1,1,0,0],
              [0,1,0,1,0,1,0],
              [0,1,0,1,0,1,0],
              [0,0,1,1,1,0,0]], edges)

      sideBySide([[0,0,1,1,1,0,0],
              [0,1,0,0,0,0,0],
              [0,1,0,0,0,0,0],
              [0,0,1,1,1,0,0]], edges)

      sideBySide([[0,0,1,1,1,1,0],
              [0,1,0,1,0,0,0],
              [0,1,0,1,0,0,0],
              [0,0,1,1,1,1,0]], edges)

      sideBySide([[1,1,1,1,1,1,0],
              [1,1,0,0,0,1,1],
              [1,0,0,0,0,0,1],
              [0,1,0,0,1,1,0]], edges)

      sideBySide([[1,1,1,1,1,1,0],
              [1,1,1,0,0,1,1],
              [1,1,0,0,0,0,1],
              [0,1,1,1,1,1,0]], edges)

      sideBySide([[ 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
              [ 0,0,0,1,1,1,1,1,1,1,1,1,0,0,0],
              [ 0,0,0,1,1,1,1,1,1,1,1,1,1,0,0],
              [ 0,0,0,1,1,1,1,1,1,1,1,1,1,0,0],
              [ 0,0,0,1,1,1,1,1,1,1,1,1,1,0,0],
              [ 0,0,0,0,1,1,1,1,1,1,1,1,1,0,0],
              [ 0,0,0,0,1,1,1,1,1,1,1,1,1,0,0],
              [ 0,0,0,0,1,1,1,1,1,1,1,1,1,0,0],
              [ 0,0,0,1,1,1,1,1,1,1,1,1,0,0,0],
              [ 0,0,0,1,1,1,1,1,1,1,1,1,0,0,0],
              [ 0,0,0,1,1,1,1,1,1,1,1,1,0,0,0],
              [ 0,0,0,1,1,1,1,1,1,1,1,1,0,0,0],
              [ 0,0,0,1,1,1,1,1,1,1,1,1,0,0,0],
              [ 0,0,0,1,1,1,1,1,1,1,1,1,0,0,0],
              [ 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]], edges)


      sideBySide([[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
              ,[1,1,1,1,1,0,0,0,0,0,0,0,0,0,1]
              ,[1,1,1,1,0,0,0,0,0,0,0,0,0,0,1]
              ,[1,0,0,0,0,0,0,0,0,0,0,0,0,0,1]
              ,[1,0,0,0,0,0,0,0,0,0,0,0,0,0,1]
              ,[1,0,0,0,0,0,0,0,0,0,0,0,0,0,1]
              ,[1,0,0,0,0,0,0,0,0,0,0,0,0,0,1]
              ,[1,0,0,0,0,0,0,0,0,0,0,0,0,0,1]
              ,[1,0,0,0,0,0,0,0,0,0,0,0,0,0,1]
              ,[1,0,0,0,0,0,0,1,1,1,1,1,0,0,1]
              ,[1,0,0,0,1,1,1,1,1,1,1,1,0,0,1]
              ,[1,0,0,0,0,1,1,1,1,1,1,0,0,0,1]
              ,[1,0,0,0,0,0,0,1,1,1,0,0,0,0,1]
              ,[1,0,0,0,0,0,0,1,1,1,0,0,0,0,1]
              ,[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]], edges)

      a = self.Matrix.__class__([[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
                  ,[1,1,1,1,1,0,0,0,0,0,0,0,0,0,1]
                  ,[1,1,1,1,0,0,0,0,0,0,0,0,0,0,1]
                  ,[1,0,0,0,0,0,0,0,0,0,0,0,0,0,1]
                  ,[1,0,0,0,0,0,0,0,0,0,0,0,0,0,1]
                  ,[1,0,0,0,0,0,0,0,0,0,0,0,0,0,1]
                  ,[1,0,0,0,0,0,0,0,0,0,0,0,0,0,1]
                  ,[1,0,0,0,0,0,0,0,0,0,0,0,0,0,1]
                  ,[1,0,0,0,0,0,0,0,0,0,0,0,0,0,1]
                  ,[1,0,0,0,0,0,0,1,1,1,1,1,0,0,1]
                  ,[1,0,0,0,1,1,1,1,1,1,1,1,0,0,1]
                  ,[1,0,0,0,0,1,1,1,1,1,1,0,0,0,1]
                  ,[1,0,0,0,0,0,0,1,1,1,0,0,0,0,1]
                  ,[1,0,0,0,0,0,0,1,1,1,0,0,0,0,1]
                  ,[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]])
      a.logicalNot()
      sideBySide(a, edges)

      sideBySide([[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
              ,[1,1,1,1,1,0,0,0,0,0,0,0,0,0,1]
              ,[1,1,1,1,0,0,0,0,0,0,0,0,0,0,1]
              ,[1,0,0,0,0,0,0,0,1,1,1,0,0,0,1]
              ,[1,0,0,0,0,0,1,1,1,0,1,0,0,0,1]
              ,[1,0,0,0,0,0,1,0,0,0,0,0,0,0,1]
              ,[1,0,0,0,0,0,1,1,1,0,0,0,0,0,1]
              ,[1,0,0,0,0,0,0,0,0,0,0,0,0,0,1]
              ,[1,0,0,0,0,0,0,0,0,0,0,0,0,0,1]
              ,[1,0,0,0,0,0,0,1,1,1,1,1,0,0,1]
              ,[1,0,0,0,1,1,1,1,1,1,1,1,0,0,1]
              ,[1,0,0,0,0,1,1,1,1,1,1,0,0,0,1]
              ,[1,0,0,0,0,0,0,1,1,1,0,0,0,0,1]
              ,[1,0,0,0,0,0,0,1,1,1,0,0,0,0,1]
              ,[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]], edges)

      sideBySide([[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
              [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
              [1,1,1,1,1,0,0,0,0,0,0,0,1,1,1],
              [1,1,1,1,0,0,0,0,0,0,0,0,0,0,1],
              [1,1,1,0,0,0,0,0,0,0,0,0,0,0,1],
              [1,1,0,0,0,0,0,0,0,0,0,0,0,0,1],
              [1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
              [1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
              [1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
              [1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
              [1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
              [1,1,0,0,0,0,0,0,0,0,0,0,0,1,1],
              [1,1,1,1,1,1,0,0,0,0,0,0,1,1,1],
              [1,1,1,1,1,1,0,0,0,0,0,0,1,1,1],
              [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]], edges)

      a = self.Matrix.__class__([[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
                  [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
                  [1,1,1,1,1,0,0,0,0,0,0,0,1,1,1],
                  [1,1,1,1,0,0,0,0,0,0,0,0,0,0,1],
                  [1,1,1,0,0,0,0,0,0,0,0,0,0,0,1],
                  [1,1,0,0,0,0,0,0,0,0,0,0,0,0,1],
                  [1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                  [1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                  [1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                  [1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                  [1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                  [1,1,0,0,0,0,0,0,0,0,0,0,0,1,1],
                  [1,1,1,1,1,1,0,0,0,0,0,0,1,1,1],
                  [1,1,1,1,1,1,0,0,0,0,0,0,1,1,1],
                  [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]])
      a.logicalNot()
      sideBySide(a, edges)


  def testRightVecSumAtNZ(self):
    # Regular matrix vector product, on the right side, all the values in the
    # matrix being 1. The fast version doesn't allocate memory for the result
    # and uses a pre-allocated buffer instead.

    for i in range(10):

      m = _RGEN.randint(1,10)
      n = _RGEN.randint(5,10)
      mat = _RGEN.randint(0,2,(m,n))
      mat[m/2] = numpy.zeros((n))

      a = self.Matrix.__class__(1)
      a.fromDense(mat)

      x = _RGEN.lognormal(size=n).astype(numpy.float32)
      y = a.rightVecSumAtNZ(x)
      answer = numpy.dot(mat, x)

      if (max(y - answer) > 1e-5).any():
        error('rightVecSumAtNZ')

      y2 = numpy.zeros((m)).astype(numpy.float32)
      a.rightVecSumAtNZ_fast(x, y2)

      if (y != y2).any():
        error('rightVecSumAtNZ_fast')


  def testRightVecArgMaxAtNZ(self):
    for k in range(10):

      m = _RGEN.randint(1,10)
      n = _RGEN.randint(5,10)
      mat = _RGEN.randint(0,2,(m,n))
      mat[m/2] = numpy.zeros((n))

      a = self.Matrix.__class__(1)
      a.fromDense(mat)

      x = _RGEN.lognormal(size=n).astype(numpy.float32)
      y = a.rightVecArgMaxAtNZ(x)

      answer = numpy.zeros(m)
      for i in xrange(m):
        a = 0
        for j in xrange(n):
          if mat[i,j] > 0:
            if x[j] > a:
              a = x[j]
              answer[i] = j

      if (y != answer).any():
        error('rightVecArgMaxAtNZ')


  def testLeftVecSumAtNZ(self):
    # Regular vector matrix product, on the left side, with all the values in the
    # matrix being 1. The fast version doesn't allocate memory for the result
    # and uses a pre-allocated buffer instead.

    for i in range(10):

      m = _RGEN.randint(1,10)
      n = _RGEN.randint(5,10)
      mat = _RGEN.randint(0,2,(m,n))
      mat[m/2] = numpy.zeros((n))

      a = self.Matrix.__class__(1)
      a.fromDense(mat)

      x = _RGEN.lognormal(size=m).astype(numpy.float32)
      y = a.leftVecSumAtNZ(x)
      answer = numpy.dot(x, mat)

      if (max(y - answer) > 1e-5).any():
        error('leftVecSumAtNZ')

      y2 = numpy.zeros((n)).astype(numpy.float32)
      a.leftVecSumAtNZ_fast(x, y2)

      if (y != y2).any():
        error('rightVecSumAtNZ_fast')


  def testCompact(self):
    m = _RGEN.randint(1,100)
    n = _RGEN.randint(5,100)
    mat = _RGEN.randint(0,2,(m,n))
    mat[m/2] = numpy.zeros((n))

    a = self.Matrix.__class__(1)
    a.fromDense(mat)
    needed = a.nNonZeros()
    a.compact()

    if a.capacity() != needed:
      error('compact')


  def testPickling(self):
    m = _RGEN.randint(1,100)
    n = _RGEN.randint(5,100)
    mat = _RGEN.randint(0,2,(m,n))
    mat[m/2] = numpy.zeros((n))

    a = self.Matrix.__class__(1)
    a.fromDense(mat)

    cPickle.dump(a, open('test.bin', 'wb'))
    b = cPickle.load(open('test.bin'))

    if (a.toDense() != b.toDense()).any():
      error('pickling')

    os.unlink('test.bin')


  def testMinHammingDistance(self):
    m = _RGEN.randint(5,10)
    n = _RGEN.randint(5,10)
    mat = _RGEN.randint(0,2,(m,n))
    mat[m/2] = numpy.zeros((n))

    a = self.Matrix.__class__(mat)

    for i in range(10):

      x = _RGEN.randint(0,2,(n))

      sparse_x = []
      for i in range(n):
        if x[i] == 1:
          sparse_x.append(i)

      min_row, min_d = 0, 9999
      for i in range(m):
        d = 0
        for j in range(n):
          if (x[j] == 1 and mat[i,j] == 0) \
              or (x[j] == 0 and mat[i,j] == 1):
            d += 1
        if d < min_d:
          min_d = d
          min_row = i

      r = a.minHammingDistance(sparse_x)
      if r[0] != min_row or r[1] != min_d:
        error('minHammingDistance')


  def testFirstRowCloserThan(self):
    m = _RGEN.randint(5,10)
    n = _RGEN.randint(5,10)
    mat = _RGEN.randint(0,2,(m,n))
    mat[m/2] = numpy.zeros((n))

    a = self.Matrix.__class__(mat)

    for i in range(10):

      x = _RGEN.randint(0,2,(n))

      sparse_x = []
      for i in range(n):
        if x[i] == 1:
          sparse_x.append(i)

      min_row = m
      for i in range(m):
        d = 0
        for j in range(n):
          if (x[j] == 1 and mat[i,j] == 0) \
              or (x[j] == 0 and mat[i,j] == 1):
            d += 1
        if d < 4:
          min_row = i
          break

      r = a.firstRowCloserThan(sparse_x, 4)
      if r != min_row:
        error('firstRowCloserThan')


  def testVecMaxProd(self):
    m = _RGEN.randint(5,10)
    n = _RGEN.randint(5,10)
    mat = _RGEN.randint(0,2,(m,n))
    mat[m/2] = numpy.zeros((n))

    a = self.Matrix.__class__(mat)

    for i in range(10):

      x = _RGEN.lognormal(1,2,(n))
      y = a.vecMaxProd(x)

      truth = numpy.zeros((m))
      for j in range(m):
        max_v = 0
        for k in range(n):
          if mat[j,k] > 0 and x[k] > max_v:
            max_v = x[k]
        truth[j] = max_v

      if max(y - truth) > 1e-4:
        error('vecMaxProd')


  def testLeftDenseMatSumAtNZ(self):
    for i in range(10):
      a = _RGEN.randint(0,2,(12,13))
      m = self.Matrix.__class__(a)
      b = _RGEN.randint(0,10,(11,12))
      c = m.leftDenseMatSumAtNZ(b)
      d = numpy.dot(b,a)
      if (c != d).any():
        print m
        print a
        print c
        print d
        error('leftDenseMatSumAtNZ')


  def testLeftDenseMatMaxAtNZ(self):
    for i in range(10):
      a = _RGEN.randint(0,2,(6,4))
      b = _RGEN.randint(0,10,(5,6))
      c = numpy.zeros((b.shape[0],a.shape[1])).astype(numpy.int32)

      for rowIdx in range(b.shape[0]):
        for colIdx in range(a.shape[1]):
          elements = (b[rowIdx] * a[:,colIdx])[a[:,colIdx] > 0]
          if len(elements) > 0:
            c[rowIdx,colIdx] = elements.max()

      d = self.Matrix.__class__(a).leftDenseMatMaxAtNZ(b).astype(numpy.int32)
      if (c != d).any():
        error('leftDenseMatMaxAtNZ')


  def testZeroRowsIndicator(self):
    for i in range(10):
      m = _RGEN.randint(10, 20)
      n = _RGEN.randint(10, 20)
      a = _RGEN.randint(0,100,(m,n))
      a[numpy.where(a < 80)] = 0

      if _RGEN.randint(0,100) > 50:
        a[_RGEN.randint(0,m)] = 0
      elif _RGEN.randint(0,100) > 50:
        for k in range(m):
          a[k,0] = 1

      b = self.Matrix.__class__(a)

      ans_v = a.sum(axis=1) == 0
      ans_c = ans_v.sum()

      c,v = b.zeroRowsIndicator()

      if c != ans_c or (ans_v != v).any():
        error('zeroRowsIndicator 1')

      c2,v2 = b.nonZeroRowsIndicator()
      if c + c2 != m:
        error('zeroRowsIndicator 2')
      for j in range(m):
        if v[j] == v2[j]:
          error('zeroRowsIndicator 3')


  def testNonZeroRowsIndicator(self):
    for i in range(10):
      m = _RGEN.randint(10, 20)
      n = _RGEN.randint(10, 20)
      a = _RGEN.randint(0,100,(m,n))
      a[numpy.where(a < 80)] = 0

      if _RGEN.randint(0,100) > 50:
        a[_RGEN.randint(0,m)] = 0
      elif _RGEN.randint(0,100) > 50:
        for k in range(m):
          a[k,0] = 1

      b = self.Matrix.__class__(a)

      ans_v = a.sum(axis=1) != 0
      ans_c = ans_v.sum()

      c,v = b.nonZeroRowsIndicator()

      if c != ans_c or (ans_v != v).any():
        error('nonZeroRowsIndicator 1')

      c2,v2 = b.zeroRowsIndicator()
      if c + c2 != m:
        error('nonZeroRowsIndicator 2')
      for j in range(m):
        if v[j] == v2[j]:
          error('nonZeroRowsIndicator 3')


  def testAppendSparseCol(self):
    m = _RGEN.randint(10,20)
    n = _RGEN.randint(10,20)
    x = _RGEN.randint(0,2,(m,n))
    a = self.Matrix.__class__(x)
    a.appendEmptyCols(3)
    if a.nRows() != m or a.nCols() != n + 3:
      error('appendEmptyCols 1')

    x = _RGEN.permutation(m)[:m/2].astype('int32')
    a.appendSparseCol(x)
    if a.nRows() != m or a.nCols() != n + 4:
      error('appendSparseCol 1')


  @unittest.skip("Not currently using...")
  def testScalability(self):
    # Make sure we can create a long matrix
    a = self.Matrix.__class__(2)
    for i in range(200000):
      a.appendDenseRow([1,1])
    a.CSRSaveToFile('test.txt')
    b = self.Matrix.__class__(1)
    b.CSRLoadFromFile('test.txt')
    if (a.toDense() != b.toDense()).any():
      error('scalability 1')

    print 'Preparing'
    n = 10000
    a = self.Matrix.__class__(n)
    mat = _RGEN.randint(0,100,(20000,n))
    x = []
    for row in mat:
      x += [numpy.where(row > 90)[0]]

    print 'Evaluating'
    for i in range(len(x)):
      if i % 100 == 0:
        print i
      if a.findRowSparse(x[i]) == a.nRows():
        a.appendSparseRow(x[i])



if __name__ == "__main__":
  unittest.main()
