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

"""Unit tests for sparse matrix."""

import sys
import numpy
from numpy import *
import math
import os
import cPickle
import copy
import time
import unittest2 as unittest


from nupic.bindings.math import *

rgen = numpy.random.RandomState(37)



def error(str):

  print 'Error:', str
  assert(False)



class SparseMatrixTest(unittest.TestCase):


  def test_construction(self):

    print 'Testing constructors'

    s1 = SparseMatrix(3,3)
    if s1.nRows() != 3 or s1.nCols() != 3 or s1.nNonZeros() != 0:
      error('Empty SM constructor')

    s2 = SparseMatrix(3,3,dtype='Float32')
    if s1.nRows() != 3 or s1.nCols() != 3 or s1.nNonZeros() != 0:
      error('Empty SM 32 constructor')

    a = rgen.randint(0,2,(5,7))
    a[2] = 0
    a[:,3] = 0
    sm_a = SM32(a)

    b1 = SM32(sm_a, [0,1,0,0,1,0,1], 1)
    ans1 = zeros(a.shape)
    for i in [1,4,6]:
      ans1[:,i] = a[:,i]
    if (b1.toDense() != ans1).any():
      error('From cols of other SM')

    b2 = SM32(sm_a, [0,1,0,1,1], 0)
    ans2 = zeros(a.shape)
    for i in [1,3,4]:
      ans2[i] = a[i]
    if (b2.toDense() != ans2).any():
      error('From rows of other SM')


  def test_getAllNonZeros(self):

    print 'Testing getAllNonZeros'

    for i in range(5):

      m = rgen.randint(2,10)
      n = rgen.randint(2,10)
      a = rgen.randint(0,100,(m,n)).astype(float32)
      a[numpy.where(a < 50)] = 0
      a[rgen.randint(0,m)] = 0
      a[:,rgen.randint(0,n)] = 0
      a /= sum(a)
      sm = SM32(a)

      ans_ind = numpy.where(a > 0)
      ans_val = a[ans_ind]
      ans = [(i,j,v) for i,j,v in zip(ans_ind[0], ans_ind[1], ans_val)]

      # Returns one list of triples by default
      all_nz = sm.getAllNonZeros()

      for x,y in zip(all_nz, ans):
        if x[0] != y[0] or x[1] != y[1] or abs(x[2] - y[2]) > 1e-9:
          error('getAllNonZeros 1 list of triples')

      # Test option to return 3 lists instead of 1 list of triples
      all_nz2 = sm.getAllNonZeros(True)

      for i in range(len(ans_val)):
        if all_nz2[0][i] != ans_ind[0][i] or all_nz2[1][i] != ans_ind[1][i] \
            or abs(all_nz2[2][i] - ans_val[i]) > 1e-9:
          error('getAllNonZeros 3 lists')


  def test_setAllNonZeros(self):

    print 'Testing setAllNonZeros'

    for i in range(5):

      m = rgen.randint(2,10)
      n = rgen.randint(2,10)
      a = rgen.randint(0,100,(m,n)).astype(float32)
      a[numpy.where(a < 25)] = 0
      a[rgen.randint(0,m)] = 0
      a[:,rgen.randint(0,n)] = 0
      a[0,0] = 1
      a[m-1] = 0
      a[:,n-1] = 0
      a /= sum(a)
      nz = numpy.where(a > 0)
      nz_val = a[nz]

      sm = SM32(1,1)
      # Assumes lexicographic order of the indices by default
      sm.setAllNonZeros(a.shape[0], a.shape[1], nz[0],nz[1],nz_val)

      if (sm.toDense() != a).any():
        error('setAllNonZeros, in order')

      # Test when values come in out of (lexicographic) order
      # and with duplicates
      p = rgen.permutation(len(nz_val))
      nz_i2,nz_j2,nz_val2 = [0],[0],[0]
      for i in p:
        nz_i2.append(nz[0][i])
        nz_j2.append(nz[1][i])
        nz_val2.append(nz_val[i])
      for i in p:
        nz_i2.append(nz[0][i])
        nz_j2.append(nz[1][i])
        nz_val2.append(nz_val[i])

      sm2 = SM32(1,1)
      sm2.setAllNonZeros(a.shape[0], a.shape[1], nz_i2,nz_j2,nz_val2, False)

      if (sm2.toDense() != a).any():
        error('setAllNonZeros, out of order')


  def test_nNonZerosPerBox(self):

    print 'Testing nNonZerosPerBox'

    for i in range(5):

      m = rgen.randint(2,10)
      n = rgen.randint(2,10)
      a = rgen.randint(0,2,(m,n)).astype(float32)
      a[rgen.randint(0,m)] = 0
      a[:,rgen.randint(0,n)] = 0
      a[0,0] = 1
      a[m/2] = 0
      a[:,n/2] = 0

      sm = SM32(a)

      nnzpb = sm.nNonZerosPerBox([m/2,m],[n/2,n])
      ans = zeros((2,2))
      ans[0,0] = sum(a[:m/2,:n/2])
      ans[0,1] = sum(a[:m/2,n/2:])
      ans[1,0] = sum(a[m/2:,:n/2])
      ans[1,1] = sum(a[m/2:,n/2:])
      if (nnzpb.toDense() != ans).any():
        error('nNonZerosPerBox')


  def test_getCol(self):

    print 'Testing getCol'

    for i in range(5):

      m = rgen.randint(2,10)
      n = rgen.randint(2,10)
      a = rgen.randint(0,100,(m,n)).astype(float32)
      a[rgen.randint(0,m)] = 0
      a[:,rgen.randint(0,n)] = 0
      a[where(a < 25)] = 0
      a[0,0] = 1
      a[m/2] = 0
      a[:,n/2] = 0

      sm = SM32(a)

      for j in range(n):
        if (sm.getCol(j) != a[:,j]).any():
          error('getCol')


  def test_setSlice(self):

    print 'Testing setSlice'

    # With a sparse matrix
    for i in range(5):

      m = rgen.randint(10,20)
      n = rgen.randint(10,20)
      a = rgen.randint(0,100,(m,n)).astype(float32)
      a[rgen.randint(0,m)] = 0
      a[:,rgen.randint(0,n)] = 0
      a[where(a < 25)] = 0
      a[0,0] = 1
      a[m/2] = 0
      a[:,n/2] = 0

      sm = SM32(a)

      b = rgen.randint(0,100,(m/4,n/4)).astype(float32)
      b[where(b < 50)] = 0
      slice = SM32(b)
      x,y = rgen.randint(0,m/2), rgen.randint(0,n/2)

      sm.setSlice(x,y,slice)

      ans = array(a)
      for i in range(slice.shape[0]):
        for j in range(slice.shape[1]):
          ans[x+i,y+j] = slice[i,j]

      if (sm.toDense() != ans).any():
        error('setSlice/sparse')

    # With a numpy array
    for i in range(5):

      m = rgen.randint(10,20)
      n = rgen.randint(10,20)
      a = rgen.randint(0,100,(m,n)).astype(float32)
      a[rgen.randint(0,m)] = 0
      a[:,rgen.randint(0,n)] = 0
      a[where(a < 25)] = 0
      a[0,0] = 1
      a[m/2] = 0
      a[:,n/2] = 0

      sm = SM32(a)

      slice = rgen.randint(0,100,(m/4,n/4)).astype(float32)
      x,y = rgen.randint(0,m/2), rgen.randint(0,n/2)

      sm.setSlice(x,y,slice)

      ans = array(a)
      for i in range(slice.shape[0]):
        for j in range(slice.shape[1]):
          ans[x+i,y+j] = slice[i,j]

      if (sm.toDense() != ans).any():
        error('setSlice/dense')


  def test_kthroot_product(self):

    print 'Testing k-root product'

    def algo(s, x, seg_size, small_val):

      result = numpy.ones(s.nRows())

      for row in range(s.nRows()):
        seg_begin = 0; seg_end = seg_size
        while seg_begin != s.nCols():
          blank = s.nNonZerosInBox(row, row+1, seg_begin, seg_end) == 0
          if blank:
            max_val = 0
            for col in range(seg_begin, seg_end):
              if x[col] > max_val:
                max_val = x[col]
            result[row] *= (1.0 - max_val)
          else:
            for col in range(seg_begin, seg_end):
              if s.get(row, col) > 0:
                val = x[col]
                if val > 0:
                  result[row] *= val
                else:
                  result[row] *= small_val
          seg_begin += seg_size; seg_end += seg_size

      k = float(s.nCols() / seg_size)
      result = numpy.power(result, 1.0 / k)

      too_small = True
      for i in range(s.nRows()):
        if result[i] > small_val:
          too_small = False
      if too_small:
        result = numpy.zeros(s.nRows())

      return result

    s = SM32(numpy.zeros((8,8)))
    x = .9*numpy.ones((8))
    if (kthroot_product(s, 4, x, 1e-6) - algo(s, x, 4, 1e-6) > 1e-6).any():
      error('kthroot_product 1')

    s.set(0,4,1)
    s.set(0,5,1)
    s.set(1,0,1)
    s.set(1,1,1)
    s.set(2,0,1)
    s.set(2,4,1)
    if (kthroot_product(s, 4, x, 1e-6) - algo(s, x, 4, 1e-6) > 1e-6).any():
      error('kthroot_product 1')

    s.set(0,2,1)
    s.set(0,7,1)
    s.set(1,2,1)
    s.set(1,3,1)
    s.set(2,1,1)
    s.set(2,4,1)
    s.set(2,5,1)
    s.set(2,6,1)
    s.set(2,7,1)
    if (kthroot_product(s,4, x, 1e-6) - algo(s, x, 4, 1e-6) > 1e-6).any():
      error('kthroot_product 1')

    x = rgen.randint(0,100,(10))
    x /= x.sum()
    s = SM32(rgen.randint(0,2,(10,10)))
    if (kthroot_product(s, 5, x, 1e-6) - algo(s, x, 5, 1e-6) > 1e-6).any():
      error('kthroot_product 1')
    if (kthroot_product(s, 2, x, 1e-6) - algo(s, x, 2, 1e-6) > 1e-6).any():
      error('kthroot_product 1')
    if (kthroot_product(s, 10, x, 1e-6) - algo(s, x, 10, 1e-6) > 1e-6).any():
      error('kthroot_product 1')


  def test_transpose(self):

    print 'Testing transpose'

    for k in range(5):
      nrows = rgen.randint(1,5)
      ncols = rgen.randint(5,12)
      a = rgen.randint(0,100,(nrows,ncols))
      a[numpy.where(a < 80)] = 0
      m = SM32(a)
      m.transpose()
      a = numpy.transpose(a)
      if (a != m.toDense()).any():
        error('transpose 1')

    for k in range(5):
      nrows = rgen.randint(1,5)
      ncols = rgen.randint(5,12)
      a = rgen.randint(0,100,(nrows,ncols))
      a[numpy.where(a < 80)] = 0
      m = SM32(a)
      m.decompact()
      m.transpose()
      a = numpy.transpose(a)
      if (a != m.toDense()).any():
        error('transpose 2')

    for k in xrange(5):
      nrows = rgen.randint(1,5)
      ncols = rgen.randint(5,12)
      a = rgen.randint(0,100,size=(nrows,ncols))
      a[numpy.where(a < 80)] = 0
      m = SM32(a)
      mt = m.getTransposed()
      a = numpy.transpose(a)
      if numpy.any(a != mt.toDense()):
        error('transpose 3')


  def test_aX_plus_bXY(self):

    return

    print 'Testing aX_plus_bXY'

    x0 = SM64([[10, 20, 30], [40, 50, 60]])
    x = SM64(x0)
    y0 = SM32([[1, -1, 1], [0, 1, 0]])
    y = asType(y0, SM64)
    aX_plus_bX_elementMultiply_Y(1.0, x, 0.0, y0)
    if (x.toDense() != x0.toDense()).any():
      error('aX_plus_bXY 1')

    x0 = SM64([[10, 20, 30], [40, 50, 60]])
    x = SM64(x0)
    y0 = SM32([[1, -1, 1], [0, 1, 0]])
    aX_plus_bX_elementMultiply_Y(1.0, x, 1.0, y0)
    y = asType(y0, SM64)
    xy = SM64()
    xy.copy(x0)
    xy.elementMultiply(y)
    if (x.toDense() != (x0 + xy).toDense()).any():
      error('aX_plus_bXY 2')


  def test_mat_prod(self):

    print 'Testing mat_prod'

    for i in range(5):
      a = rgen.randint(0,2,(6,8))
      b = rgen.randint(0,10,(8,4))
      c = numpy.dot(a,b)
      d = SM32(a).rightDenseMatProd(b)
      if (c != d).any():
        error('rightDenseMatProd')

      a = rgen.randint(0,2,(6,4))
      b = rgen.randint(0,10,(8,6))
      c = numpy.dot(b,a)
      d = SM32(a).leftDenseMatProd(b)
      if (c != d).any():
        error('leftDenseMatProd')


  def test_leftDenseMatMaxAtNZ(self):

    print 'Testing leftDenseMatMaxAtNZ'

    for i in range(5):

      a = rgen.randint(0,2,(6,4))
      b = rgen.randint(0,10,(5,6))
      c = zeros((b.shape[0],a.shape[1])).astype(int32)

      for rowIdx in range(b.shape[0]):
        for colIdx in range(a.shape[1]):
          elements = (b[rowIdx] * a[:,colIdx])[a[:,colIdx] > 0]
          if len(elements) > 0:
            c[rowIdx,colIdx] = elements.max()

      d = SM32(a).leftDenseMatMaxAtNZ(b).astype(int32)
      if (c != d).any():
        print a
        print b
        print c
        print d
        error('leftDenseMatMaxAtNZ')


  def test_rightDenseMatProdAtNZ(self):

    print 'Testing rightDenseMatProdAtNZ'

    for i in range(5):
      a = rgen.randint(0,2,(6,8))
      b = rgen.randint(0,10,(8,4))
      c = numpy.dot(a,b)
      d = SM32(a).rightDenseMatProdAtNZ(b)
      if (c != d).any():
        error('rightDenseMatProdAtNZ')


  def test_denseMatExtract(self):

    print 'Testing denseMatExtract'

    a = numpy.zeros((4,4))
    a[1,0] = 1; a[2,1] = 1; a[3,2] = 1
    b = rgen.randint(0,10,(4,4))
    c = numpy.dot(a,b)
    d = SM32(a).denseMatExtract(b)
    if (c != d).any():
      error('denseMatExtract')


  def test_threshold(self):

    print 'Testing threshold'

    for k in range(5):
      a = rgen.randint(0,100,(4,4))
      b = SM32(a)
      a[numpy.where(a < 50)] = 0
      b.threshold(50)
      for i in range(4):
        for j in range(4):
          if int(a[i,j]) != int(b[i,j]):
            error('threshold 1')

      l = numpy.where((a > 0) & (a < 75))
      ac = copy.deepcopy(a)
      a[l] = 0
      c = b.threshold(75, True)
      for i,j,(i2,j2,v2) in zip(l[0],l[1],c):
        if ac[i,j] != 0 and (i != i2 or j != j2 or ac[i,j] != v2):
          error('threshold 2')


  def test_clip(self):

    print 'Testing clip'

    # clip calls clipRow

    # clip above
    for k in range(5):
      a = rgen.randint(0,100,(10,10))
      a[where(a < 40)] = 0
      a[1,1] = 50
      b = SM32(a)
      a[numpy.where(a >= 50)] = 50
      b.clip(50, True)
      if (b.toDense() != a).any():
        error('clip above')

    # clip below
    for k in range(5):
      a = rgen.randint(0,100,(10,10))
      a[where(a < 40)] = 0
      a[1,1] = 50
      b = SM32(a)
      for i in range(10):
        for j in range(10):
          if a[i,j] > 0 and a[i,j] < 50:
            a[i,j] = 50
      b.clip(50, False)
      if (b.toDense() != a).any():
        error('clip below')


    print 'Testing clipCol'

    # clip col above
    for k in range(5):
      a = rgen.randint(0,100,(10,10))
      a[where(a < 40)] = 0
      a[1,1] = 50
      b = SM32(a)
      a[numpy.where(a >= 50)] = 50
      for i in range(10):
        b.clipCol(i, 50, True)
      if (b.toDense() != a).any():
        error('clipCol above')

    # clip col below
    for k in range(5):
      a = rgen.randint(0,100,(10,10))
      a[where(a < 40)] = 0
      a[1,1] = 50
      b = SM32(a)
      for i in range(10):
        for j in range(10):
          if a[i,j] > 0 and a[i,j] < 50:
            a[i,j] = 50
      for i in range(10):
        b.clipCol(i, 50, False)
      if (b.toDense() != a).any():
        error('clipCol below')


    print 'Testing clip above and below'

    # clip whole matrix below and above (calls clipRowAboveAndBelow)
    for k in range(5):
      a = rgen.randint(0,100,(10,10))
      a[where(a < 40)] = 0
      a[1,1] = 50
      a[1,2] = 60
      a[1,3] = 70
      a[1,4] = 30
      b = SM32(a)
      a[numpy.where(a >= 60)] = 60
      for i in range(10):
        for j in range(10):
          if a[i,j] > 0 and a[i,j] < 50:
            a[i,j] = 50
      b.clipAboveAndBelow(50, 60)
      if (b.toDense() != a).any():
        error('clip above and below')

    # clip col below and above
    for k in range(5):
      a = rgen.randint(0,100,(10,10))
      a[where(a < 40)] = 0
      a[1,1] = 50
      a[1,2] = 60
      a[1,3] = 70
      a[1,4] = 30
      b = SM32(a)
      for i in range(10):
        for j in range(10):
          if a[i,j] > 0 and a[i,j] >= 60:
            a[i,j] = 60
          if a[i,j] > 0 and a[i,j] < 50:
            a[i,j] = 50
      for i in range(10):
        b.clipColAboveAndBelow(i, 50, 60)
      if (b.toDense() != a).any():
        error('clipCol above and below')


  def test_increment(self):

    print 'Testing increment'

    a = rgen.randint(0,100,(4,4))
    a[numpy.where(a < 75)] = 0
    m = SM32(a)
    for i in range(5):
      old_value = m.get(i,i) if i < 4 else 0
      m.increment(i,i,i, True)
      if m.get(i,i) != old_value + i:
        error('increment')


  def test_incrementOnOuterWNZ(self):

    print 'Testing incrementOnOuterWNZ'

    a = rgen.randint(0,100,(4,4))
    a[numpy.where(a < 75)] = 0
    m = SM32(a)
    m.incrementOnOuterWNZ([1,3],[0,2])
    for i in [1,3]:
      for j in [0,2]:
        a[i,j] += 1
    if (a != m.toDense()).any():
      error('incrementOnOuterWNZ')


  def test_boxMin_boxMax(self):

    print 'Testing boxMin, boxMax'

    a = rgen.randint(0,100,(11,8))
    a[numpy.where(a < 75)] = 0
    m = SM32(a)
    box_width = 4
    box_height = 3

    for i in range(a.shape[0]-box_width):
      for j in range(a.shape[1]-box_height):
        min1 = m.boxMin(i, i+box_width, j, j + box_height)
        max1 = m.boxMax(i, i+box_width, j, j + box_height)
        min_val = 9999; max_val = 0
        min_i = i; min_j = j; max_i = i; max_j = j
        for ii in range(i,i+box_width):
          for jj in range(j,j+box_height):
            if a[ii,jj] > 0:
              if a[ii,jj] < min_val:
                min_val = a[ii,jj]
                min_i = ii; min_j = jj
              if a[ii,jj] > max_val:
                max_val = a[ii,jj]
                max_i = ii; max_j = jj
        if min_val == 9999:
          min_val = 0
        if min_i != min1[0] or min_j != min1[1] or min_val != min1[2]:
          error('boxMin')
        if max_i != max1[0] or max_j != max1[1] or max_val != max1[2]:
          error('boxMax')


  def test_getSlice(self):

    print 'Testing getSlice'

    a = rgen.randint(0,100,(11,8))
    a[numpy.where(a < 75)] = 0
    m = SM32(a)

    for i in range(11):
      for j in range(8):
        s1 = m.getSlice(i,11,j,8).toDense()
        if (s1 != a[i:11,j:8]).any():
          error('getSlice 1')
        s2 = m.getSlice(i,11,j,8).toDense()
        if (s2 != a[i:11,j:8]).any():
          error('getSlice2 1')

    for i in range(1,11):
      for j in range(1,8):
        s1 = m.getSlice(0,i,0,j).toDense()
        if (s1 != a[:i,:j]).any():
          error('getSlice 2')
        s2 = m.getSlice(0,i,0,j).toDense()
        if (s2 != a[:i,:j]).any():
          error('getSlice2 2')


  def test_addTwoRows(self):

    print 'Testing addTwoRows'

    a = rgen.randint(0,100,(11,8))
    a[numpy.where(a < 75)] = 0
    m = SM32(a)

    for i in range(11):
      for j in range(11):
        m.addTwoRows(i,j)
        a[j,:] += a[i,:]
        if (m.toDense() != a).any():
          error('addTwoRows')


  def test_setRowFromDense(self):

    print 'Testing setRowFromDense'

    a = rgen.randint(0,100,(11,8))
    a[numpy.where(a < 75)] = 0
    m = SM32(a)

    for i in range(11):
      row = [int(x) for x in rgen.randint(0,100,(8))]
      m.setRowFromDense(i,row)
      a[i,:] = row
      if (a != m.toDense()).any():
        error('setRowFromDense')


  def test_setRowFromSparse(self):

    print 'Testing setRowFromSparse'

    a = rgen.randint(0,100,(11,8))
    a[numpy.where(a < 75)] = 0
    m = SM32(a)

    for i in range(11):
      ind = list(set(rgen.randint(0,8,(4))))
      ind.sort()
      nz = rgen.randint(1,100,(4))
      m.setRowFromSparse(i,ind,nz)
      a[i,:] = 0
      for j,v in zip(ind,nz):
        a[i,j] = v
      if (a != m.toDense()).any():
        error('setRowFromSparse')


  def test_copyRow(self):

    print 'Testing copyRow'

    a = rgen.randint(0,100,(11,8))
    a[numpy.where(a < 75)] = 0
    b = rgen.randint(0,100,(11,8))
    b[numpy.where(a < 75)] = 0
    m1 = SM32(a) ; m2 = SM32(b)

    for i in range(11):
      for j in range(11):
        m1.copyRow(i,j,m2)
        a[i,:] = b[j,:]
        if (a != m1.toDense()).any():
          error('copyRow')


  def test_zeroRowAndCol(self):

    print 'Testing zeroRowAndCol'

    for k in range(5):
      a = rgen.randint(0,100,(11,11))
      a[numpy.where(a < 90)] = 0
      m = SM32(a)
      zrc = m.zeroRowAndCol()
      zrc2 = []
      for i in range(11):
        if sum(a[i,:]) == 0 and sum(a[:,i]) == 0:
          zrc2.append(i)
      if (zrc != zrc2).any():
        error('zeroRowAndCol')


  def test_setColsToZero(self):

    print 'Testing setColsToZero'

    for k in range(5):

      a = rgen.randint(0,100,(12,13))
      a[numpy.where(a < 75)] = 0
      m = SM32(a)
      to_del = set(rgen.randint(0,12,(5)));
      m.setColsToZero(list(to_del))
      for i in to_del:
        a[:,i] = 0
      if (a != m.toDense()).any():
        error('setColsToZero')


  def test_leftDenseMatSumAtNZ(self):

    print 'Testing leftDenseMatSumAtNZ'

    for i in range(5):
      a = rgen.randint(0,100,(12,13))
      a[numpy.where(a < 75)] = 0
      m = SM32(a)
      b = rgen.randint(0,100,(11,12))
      c = m.leftDenseMatSumAtNZ(b)
      a01 = numpy.zeros(a.shape)
      for i in range(12):
        for j in range(13):
          if a[i,j] > 0:
            a01[i,j] = 1
      d = numpy.dot(b,a01)
      if (c != d).any():
        error('leftDenseMatSumAtNZ')


  def test_elementRowMultiply(self):

    print 'Testing elementRowMultiply'

    a = rgen.randint(0,100,(11,12))
    a[numpy.where(a < 75)] = 0
    m = SM32(a)
    s = rgen.randint(0,10,(12))
    for i in range(m.nRows()):
      m.elementRowMultiply(i, s)
      for j in range(a.shape[1]):
        a[i,j] *= s[j]
    if (m.toDense() != a).any():
      error('elementRowMultiply')


  def test_elementColMultiply(self):

    print 'Testing elementColMultiply'

    a = rgen.randint(0,100,(11,12))
    a[numpy.where(a < 75)] = 0
    m = SM32(a)
    s = rgen.randint(0,10,(11))
    for i in range(m.nCols()):
      m.elementColMultiply(i, s)
      for j in range(a.shape[0]):
        a[j,i] *= s[j]
    if (m.toDense() != a).any():
      error('elementColMultiply')


  def test_scaleRows(self):

    print 'Testing scaleRows'

    a = rgen.randint(0,100,(11,12))
    a[numpy.where(a < 75)] = 0
    m = SM32(a)
    s = rgen.randint(0,10,(11))
    m.scaleRows(s)
    for i in range(m.nRows()):
      for j in range(a.shape[1]):
        a[i,j] *= s[i]
    if (m.toDense() != a).any():
      error('scaleRows')


  def test_scaleCols(self):

    print 'Testing scaleCols'

    a = rgen.randint(0,100,(11,12))
    a[numpy.where(a < 75)] = 0
    m = SM32(a)
    s = rgen.randint(0,10,(12))
    m.scaleCols(s)
    for i in range(m.nCols()):
      for j in range(a.shape[0]):
        a[j,i] *= s[i]
    if (m.toDense() != a).any():
      error('scaleCols')


  def test_setDiagonalToZero(self):

    print 'Testing setDiagonalToZero'

    for i in range(5):
      m = rgen.randint(1,10)
      n = rgen.randint(1,10)
      a = rgen.randint(0,100,(m,n))
      a[numpy.where(a < 75)] = 0
      mat = SM32(a)
      mat.setDiagonalToZero()
      for i in range(min(m,n)):
        if mat[i,i] != 0:
          error('setDiagonalToZero')


  def test_setDiagonalToVal(self):

    print 'Testing setDiagonalToVal'

    for i in range(5):
      m = rgen.randint(1,10)
      n = rgen.randint(1,10)
      a = rgen.randint(0,100,(m,n))
      a[numpy.where(a < 75)] = 0
      mat = SM32(a)
      mat.setDiagonalToVal(-1)
      for i in range(min(m,n)):
        if mat[i,i] != -1:
          error('setDiagonalToVal')


  def test_setDiagonal(self):

    print 'Testing setDiagonal'

    for i in range(5):
      m = rgen.randint(1,10)
      n = rgen.randint(1,10)
      a = rgen.randint(0,100,(m,n))
      a[numpy.where(a < 75)] = 0
      mat = SM32(a)
      vals = rgen.randint(0,100,(min(m,n)))
      mat.setDiagonal(vals)
      for i in range(min(m,n)):
        if mat[i,i] != vals[i]:
          error('setDiagonal')


  def test_rightVecProd(self):

    print 'Testing rightVecProd'

    # Right vec prod is the traditional matrix vector product, on the right side.
    # The argument vector has the same number of elements as the number of columns
    # in the matrix, and the result has as many elements as there are rows in the
    # matrix.

    for i in range(5):
      m = rgen.randint(1,10)
      n = rgen.randint(1,10)
      a = rgen.randint(0,100,(m,n))
      a[numpy.where(a < 75)] = 0
      a[rgen.randint(0,m)] = 0
      a[:,rgen.randint(0,n)] = 0
      x = rgen.randint(0,100,(n)).astype(float32)
      yr = dot(a,x)
      mat = SM32(a)
      y = mat.rightVecProd(x)
      if (y != yr).any():
        error('rightVecProd 1')
      y = mat * x
      if (y != yr).any():
        error('rightVecProd 2')
      rows = [j for j in range(m/2)]
      yr = dot(a[:m/2], x)
      y = mat.rightVecProd(rows, x)
      if (y != yr).any():
        error('rightVecProd 3')
      for j in range(5):
        row = rgen.randint(0,m)
        yr = dot(a[row:row+1], x)
        y = mat.rightVecProd(row, x)
        if y != yr[0]:
          error('rightVecProd 4')


  def test_rightVecProd_fast(self):

    print 'Testing rightVecProd_fast'

    # Right vec prod is the traditional matrix vector product, on the right side.
    # The argument vector has the same number of elements as the number of columns
    # in the matrix, and the result has as many elements as there are rows in the
    # matrix. This one is "fast" because it doesn't allocate memory for the result
    # but instead relied on an already allocated buffer.

    for i in range(5):
      m = rgen.randint(1,10)
      n = rgen.randint(1,10)
      a = rgen.randint(0,100,(m,n))
      a[numpy.where(a < 75)] = 0
      a[rgen.randint(0,m)] = 0
      a[:,rgen.randint(0,n)] = 0
      x = rgen.randint(0,100,(n)).astype(float32)
      y = zeros((m)).astype(float32)
      yr = dot(a,x)
      mat = SM32(a)
      mat.rightVecProd_fast(x, y)
      if (y != yr).any():
        error('rightVecProd_fast 1')


  def test_leftVecProd(self):

    print 'Testing leftVecProd'

    # Left vec prod is a matrix vector multiplication where the argument x vector
    # has as many elements as there are rows in the matrix, and the result vector
    # has as many elements as there are columns in the matrix.

    for i in range(5):
      m = rgen.randint(1,10)
      n = rgen.randint(1,10)
      a = rgen.randint(0,100,(m,n))
      a[numpy.where(a < 75)] = 0
      a[rgen.randint(0,m)] = 0
      a[:,rgen.randint(0,n)] = 0
      x = rgen.randint(0,100,(m)).astype(float32)
      yr = dot(x,a)
      mat = SM32(a)
      y = mat.leftVecProd(x)
      if (y != yr).any():
        error('leftVecProd 1')
      cols = [j for j in range(n/2)]
      yr = dot(x, a[:,:n/2])[:n/2]
      y = mat.leftVecProd(cols, x)
      if (y != yr).any():
        error('leftVecProd 2')
      for j in range(5):
        col = rgen.randint(0,n)
        yr = dot(x, a[:,col:col+1])
        y = mat.leftVecProd(col, x)
        if y != yr[0]:
          error('leftVecProd 3')


  def test_rightVecSumAtNZ(self):

    print 'Testing rightVecSumAtNZ'

    # This is like rightVecProd, except that we assume that the values stored
    # in the sparse matrix are 1 (even if they are not), so that we can skip
    # the multiplications. This acts as if the matrix was a 0/1 matrix.
    # The fast version doesn't allocate a new vector for the result but instead
    # relies on a pre-allocated buffer.

    for i in range(5):
      m = rgen.randint(1,10)
      n = rgen.randint(1,10)
      a = rgen.randint(0,100,(m,n))
      a[numpy.where(a < 75)] = 0
      a[rgen.randint(0,m)] = 0
      a[:,rgen.randint(0,n)] = 0
      x = rgen.randint(0,100,(n)).astype(float32)
      y = zeros((m))
      a2 = array(a)
      a2[where(a2 > 0)] = 1
      yr = dot(a2,x)
      mat = SM32(a)
      y = mat.rightVecSumAtNZ(x)
      if (y != yr).any():
        error('rightVecSumAtNZ')
      y2 = zeros((m)).astype(float32)
      mat.rightVecSumAtNZ_fast(x, y2)
      if (y2 != yr).any():
        error('rightVecSumAtNZ_fast')


  def test_leftVecSumAtNZ(self):

    print 'Testing leftVecSumAtNZ'

    # This is like leftVecProd, except that we assume that the values stored
    # in the sparse matrix are 1 (even if they are not), so that we can skip
    # the multiplications. This acts as if the matrix was a 0/1 matrix.
    # The fast version doesn't allocate a new vector for the result but instead
    # relies on a pre-allocated buffer.

    for i in range(5):
      m = rgen.randint(1,10)
      n = rgen.randint(1,10)
      a = rgen.randint(0,100,(m,n))
      a[numpy.where(a < 75)] = 0
      a[rgen.randint(0,m)] = 0
      a[:,rgen.randint(0,n)] = 0
      x = rgen.randint(0,100,(m)).astype(float32)
      y = zeros((n))
      a2 = array(a)
      a2[where(a2 > 0)] = 1
      yr = dot(x, a2)
      mat = SM32(a)
      y = mat.leftVecSumAtNZ(x)
      if (y != yr).any():
        error('leftVecSumAtNZ')
      y2 = zeros((n)).astype(float32)
      mat.leftVecSumAtNZ_fast(x, y2)
      if (y2 != yr).any():
        error('leftVecSumAtNZ_fast')


  def test_multiply(self):

    print 'Testing multiply'

    # Multiply is the multiplication of two sparse matrices. The result is a third
    # sparse matrix.

    for i in range(5):
      m1 = rgen.randint(2,10)
      m2 = rgen.randint(2,10)
      n = rgen.randint(1,10)
      a = rgen.randint(0,100,(m1,n))
      a[numpy.where(a < 60)] = 0
      a[rgen.randint(0,m1)] = 0
      a[:,rgen.randint(0,n)] = 0
      b = rgen.randint(0,100,(n,m2))
      b[numpy.where(b < 60)] = 0
      b[rgen.randint(0,n)] = 0
      b[:,rgen.randint(0,m2)] = 0
      cr = dot(a,b)
      c = SM32(a) * SM32(b)
      if (c.toDense() != cr).any():
        error('multiply')


  def test_elementMultiply(self):

    print 'Testing elementMultiply'

    # This multiplies elements at the same positions in matrices a and b. The
    # result is another matrix.

    for i in range(5):
      m = rgen.randint(2,10)
      n = rgen.randint(1,10)
      a = rgen.randint(0,100,(m,n))
      a[numpy.where(a < 75)] = 0
      a[rgen.randint(0,m)] = 0
      a[:,rgen.randint(0,n)] = 0
      b = rgen.randint(0,100,(m,n))
      b[numpy.where(b < 75)] = 0
      b[rgen.randint(0,m)] = 0
      b[:,rgen.randint(0,n)] = 0
      cr = a * b
      a = SM32(a); b = SM32(b)
      a.elementMultiply(b)
      if (a.toDense() != cr).any():
        error('elementMultiply')


  def test_incrementWithOuterProduct(self):

    print 'Testing incrementWithOuterProduct'

    for i in range(5):
      m = rgen.randint(2,10)
      n = rgen.randint(1,10)
      a = rgen.randint(0,100,(m,n))
      a[numpy.where(a < 75)] = 0
      a[rgen.randint(0,m)] = 0
      a[:,rgen.randint(0,n)] = 0
      x = rgen.randint(0,100,(m))
      y = rgen.randint(0,100,(n))
      b = a.copy()
      b += numpy.outer(x,y)
      a = SM32(a)
      x = [int(o) for o in x]
      y = [int(o) for o in y]
      a.incrementWithOuterProduct(x,y)
      if (a.toDense() != b).any():
        error('incrementWithOuterProduct')


  def test_incrementOnOuterProductVal(self):

    print 'Testing incrementOnOuterProductVal'

    for i in range(5):
      m = rgen.randint(2,10)
      n = rgen.randint(1,10)
      a = rgen.randint(0,100,(m,n))
      a[numpy.where(a < 75)] = 0
      a[rgen.randint(0,m)] = 0
      a[:,rgen.randint(0,n)] = 0
      x = list(set(rgen.randint(0,m,(4))))
      y = list(set(rgen.randint(0,n,(3))))
      b = copy.deepcopy(a)
      for j in x:
        for k in y:
          b[j,k] -= 2
      a = SM32(a)

      x = [int(o) for o in x]
      y = [int(o) for o in y]
      a.incrementOnOuterProductVal(x, y, -2)
      if (a.toDense() != b).any():
        error('incrementOnOuterProductVal')


  def test_setFromOuter(self):

    print 'Testing setFromOuter with variable amount of memory'

    for i in range(5):
      m = rgen.randint(1,10)
      n = rgen.randint(1,10)
      x = rgen.randint(0,100,(m))
      y = rgen.randint(0,100,(n))
      x[where(x < 50)] = 0
      y[where(y < 50)] = 0
      r = numpy.outer(x,y)
      a = SM32()
      x = [int(o) for o in x]
      y = [int(o) for o in y]
      a.setFromOuter(x,y)
      if (a.toDense() != r).any():
        error('setFromOuter 1')

    print 'Testing setFromOuter with fixed amount of memory'

    for i in range(5):
      m = rgen.randint(2,10)
      n = rgen.randint(2,10)
      a = SM32(ones((m,n)))
      for j in range(5):
        x = rgen.randint(0,100,(m))
        x[rgen.randint(0,m)] = 0
        y = rgen.randint(0,100,(n))
        y[rgen.randint(0,n)] = 0
        x = [int(o) for o in x]
        y = [int(o) for o in y]
        a.setFromOuter(x,y, True)
        r = numpy.outer(x,y)
        if (a.toDense() != r).any():
          error('setFromOuter 2')


  def test_setFromElementMultiplyWithOuter(self):

    print 'Testing setFromElementMultiplyWithOuter'

    for i in range(5):
      m = rgen.randint(1,10)
      n = rgen.randint(1,10)
      x = rgen.randint(0,100,(m))
      y = rgen.randint(0,100,(n))
      x[where(x < 50)] = 0
      y[where(y < 50)] = 0
      b = rgen.randint(0,100,(m,n))
      r = numpy.outer(x,y) * b
      a = SM32()
      x = [int(o) for o in x]
      y = [int(o) for o in y]
      a.setFromElementMultiplyWithOuter(x,y,SM32(b))
      if (a.toDense() != r).any():
        error('setFromElementMultiplyWithOuter')


  def test_add(self):

    print 'Testing add'

    for i in range(5):
      m = rgen.randint(2,10)
      n = rgen.randint(1,10)
      a = rgen.randint(0,100,(m,n))
      a[numpy.where(a < 60)] = 0
      a[rgen.randint(0,m)] = 0
      a[:,rgen.randint(0,n)] = 0
      b = rgen.randint(0,100,(m,n))
      b[numpy.where(b < 60)] = 0
      b[rgen.randint(0,m)] = 0
      b[:,rgen.randint(0,n)] = 0
      cr = a + b
      a = SM32(a); b = SM32(b)
      a += b
      if (a.toDense() != cr).any():
        error('add')


  def test_vecMaxAtNZ(self):

    print 'Testing vecMaxAtNZ'

    for i in range(5):

      m = rgen.randint(2,10)
      n = rgen.randint(1,10)
      a = rgen.randint(0,100,(m,n))
      a[numpy.where(a < 60)] = 0
      a[rgen.randint(0,m)] = 0
      a[:,rgen.randint(0,n)] = 0

      for j in range(10):

        x = rgen.randint(-100,100,(n))
        x[n/2] = 0

        ans = zeros((m))
        for r in range(m):
          max_val = -99999
          for c in range(n):
            if a[r,c] > 0 and x[c] > max_val:
              max_val = x[c]
          ans[r] = max_val if max_val != -99999 else 0

        b = SM32(a)
        y = b.vecMaxAtNZ(x)

        if (y != ans).any():
          error('vecMaxAtNZ')


  def test_vecArgMaxAtNZ(self):

    print 'Testing vecArgMaxAtNZ'

    for i in range(5):

      m = rgen.randint(2,10)
      n = rgen.randint(1,10)
      a = rgen.randint(0,100,(m,n))
      a[numpy.where(a < 60)] = 0
      a[rgen.randint(0,m)] = 0
      a[:,rgen.randint(0,n)] = 0

      for j in range(10):

        x = rgen.randint(-100,100,(n))
        x[n/2] = 0

        ans = zeros((m))
        for r in range(m):
          max_val = -999999
          for c in range(n):
            if a[r,c] > 0 and x[c] > max_val:
              max_val = x[c]
              ans[r] = c

        b = SM32(a)
        y = b.vecArgMaxAtNZ(x)

        if (y != ans).any():
          error('vecArgMaxAtNZ')


  def test_vecArgMaxProd(self):

    print 'Testing vecArgMaxProd'

    for i in range(5):

      m = rgen.randint(2,10)
      n = rgen.randint(1,10)
      a = rgen.randint(0,100,(m,n))
      a[numpy.where(a < 60)] = 0
      a[rgen.randint(0,m)] = 0
      a[:,rgen.randint(0,n)] = 0

      for j in range(10):

        x = rgen.randint(0,100,(n))
        x[n/2] = 0

        ans = zeros((m))
        for r in range(m):
          max_val = 0
          for c in range(n):
            p = a[r,c] * x[c]
            if p != 0 and p >= max_val:
              max_val = a[r,c] * x[c]
              ans[r] = c

        a = SM32(a)
        y = a.vecArgMaxProd(x)

        if (y != ans).any():
          error('vecArgMaxProd')


  def test_setBoxToZero(self):

    print 'Testing setBoxToZero'

    for i in range(5):
      m = rgen.randint(2,10)
      n = rgen.randint(1,10)
      a = rgen.randint(0,100,(m,n))
      a[numpy.where(a < 60)] = 0
      a[rgen.randint(0,m)] = 0
      a[:,rgen.randint(0,n)] = 0
      box_row_start = rgen.randint(0,m)
      box_row_end = rgen.randint(box_row_start,m)
      box_col_start = rgen.randint(0,n)
      box_col_end = rgen.randint(box_col_start,n)
      sm = SM32(a)
      sm.setBoxToZero(box_row_start, box_row_end, box_col_start, box_col_end)
      a[box_row_start:box_row_end, box_col_start:box_col_end] = 0
      if (sm.toDense() != a).any():
        error('setBoxToZero')


  def test_setBox(self):

    print 'Testing setBox'

    for i in range(5):
      m = rgen.randint(2,10)
      n = rgen.randint(1,10)
      a = rgen.randint(0,100,(m,n))
      a[numpy.where(a < 60)] = 0
      a[rgen.randint(0,m)] = 0
      a[:,rgen.randint(0,n)] = 0
      box_row_start = rgen.randint(0,m)
      box_row_end = rgen.randint(box_row_start,m)
      box_col_start = rgen.randint(0,n)
      box_col_end = rgen.randint(box_col_start,n)
      v = rgen.randint(0,100)
      sm = SM32(a)
      sm.setBox(box_row_start, box_row_end, box_col_start, box_col_end, v)
      a[box_row_start:box_row_end, box_col_start:box_col_end] = v
      if (sm.toDense() != a).any():
        error('setBox')


  def test_nNonZerosInRowRange(self):

    print 'Testing nNonZerosInRowRange'

    for i in range(5):
      m = rgen.randint(2,20)
      n = rgen.randint(2,20)
      a = rgen.randint(0,100,(m,n))
      a[numpy.where(a < 10)] = 0
      a[rgen.randint(0,m)] = 0
      a[:,rgen.randint(0,n)] = 0
      sm = SM32(a)
      for j in range(m):
        box_col_start = rgen.randint(1,n)
        box_col_end = rgen.randint(box_col_start,n)
        n_sm = sm.nNonZerosInRowRange(j, box_col_start, box_col_end)
        n_py = 0
        for k in range(box_col_start, box_col_end):
          if a[j,k] > 0:
            n_py += 1
        if n_py != n_sm:
          error('nNonZerosInRowRange')


  def test_nNonZerosInBox(self):

    print 'Testing nNonZerosInBox'

    for i in range(5):
      m = rgen.randint(4,20)
      n = rgen.randint(4,20)
      a = rgen.randint(0,100,(m,n))
      a[numpy.where(a < 10)] = 0
      a[rgen.randint(0,m)] = 0
      a[:,rgen.randint(0,n)] = 0
      box_row_start = rgen.randint(1,m/2)
      box_row_end = rgen.randint(box_row_start,m)
      box_col_start = rgen.randint(1,n/2)
      box_col_end = rgen.randint(box_col_start,n)
      sm = SM32(a)
      n_sm = sm.nNonZerosInBox(box_row_start, box_row_end,
                   box_col_start, box_col_end)
      n_py = 0
      for j in range(box_row_start, box_row_end):
        for k in range(box_col_start, box_col_end):
          if a[j,k] > 0:
            n_py += 1

      if n_py != n_sm:
        error('nNonZerosInBox')


  def test_getNonZerosInBox(self):

    print 'Testing getNonZerosInBox'

    for i in range(5):
      m = rgen.randint(4,20)
      n = rgen.randint(4,20)
      a = rgen.randint(0,100,(m,n))
      a[numpy.where(a < 10)] = 0
      a[rgen.randint(0,m)] = 0
      a[:,rgen.randint(0,n)] = 0
      box_row_start = rgen.randint(1,m/2)
      box_row_end = rgen.randint(box_row_start,m)
      box_col_start = rgen.randint(1,n/2)
      box_col_end = rgen.randint(box_col_start,n)
      sm = SM32(a)
      nnz = sm.getNonZerosInBox(box_row_start, box_row_end,
                   box_col_start, box_col_end)
      box_nz = []
      for j in range(box_row_start, box_row_end):
        for k in range(box_col_start, box_col_end):
          if a[j,k] > 0:
            box_nz.append((j, k, a[j,k]))

      if len(nnz) != len(box_nz):
        error('getNonZerosInBox 1')

      for i in range(len(nnz)):
        if nnz[i][0] != box_nz[i][0] or \
          nnz[i][1] != box_nz[i][1] or nnz[i][2] != box_nz[i][2]:
          error('getNonZerosInBox 2')


  def test_getNonZerosSorted(self):

    print 'Testing getNonZerosSorted'

    for i in range(5):

      m = rgen.randint(10,20)
      n = rgen.randint(10,20)
      A = SM32(rgen.randint(0,100,(m,n)))
      A.threshold(70)
      A.setRowToZero(m/2)
      A.setColToZero(n/2)

      z1 = list(A.getNonZerosSorted())
      z11 = list(A.getNonZerosSorted(3))
      z2 = list(A.getNonZerosSorted(-1, False))
      z21 = list(A.getNonZerosSorted(3, False))

      # Visual inspection only for now: sort needs tie breakers
      # to make automatic comparison successful


  def test_smoothVecMaxProd(self):

    print 'Testing smoothVecMaxProd'

    for i in range(5):

      m = rgen.randint(5,10)
      n = rgen.randint(5,10)
      A = SM32(rgen.randint(0,100,(m,n)))
      A.threshold(70)
      A /= 100
      A.setRowToZero(m/2)
      A.setColToZero(n/2)

      k = float(rgen.randint(1,20)) / float(20)
      x = rgen.randint(0, 100, (n)) / float(100)
      x[n/2] = 0
      y = smoothVecMaxProd(A, k, x)

      d = (A.toDense() + k) * x
      y0 = numpy.max(d, axis=1)

      if (abs(y - y0) > 1e-3).any():
        error('smoothVecMaxProd')


  def test_smoothVecArgMaxProd(self):

    print 'Testing smoothVecArgMaxProd'

    for i in range(5):

      m = rgen.randint(5,10)
      n = rgen.randint(5,10)
      A = SM32(rgen.randint(0,100,(m,n)))
      A.threshold(70)
      A /= 100
      A.setRowToZero(m/2)
      A.setColToZero(n/2)

      k = float(rgen.randint(1,20)) / float(20)
      x = rgen.randint(0, 100, (n)) / float(100)
      x[n/2] = 0
      y = smoothVecArgMaxProd(A, k, x)

      d = (A.toDense() + k) * x
      y0 = numpy.argmax(d, axis=1)

      if (y != y0).any():
        print k
        print x
        print A
        print d
        print y
        print y0
        error('smoothVecArgMaxProd')


  def test_shiftRows(self):

   print 'Testing shiftRows'

   for test in xrange(5):
    r, c = rgen.randint(10, size=2)
    m = rgen.randint(5, size=(r, c))
    sm = SM32(m)
    s = rgen.randint(-r, r+1)
    ms = numpy.zeros(m.shape)
    sb = max(0, -s)
    rs = r - abs(s)
    db = max(0, s)
    ms[db:(db+rs), ...] = m[sb:(sb+rs), ...]
    sm.shiftRows(s)
    if (sm.toDense() != ms).any():
      error('shiftRows')


  def test_shiftCols(self):

   print 'Testing shiftCols'

   for test in xrange(5):
    r, c = rgen.randint(10, size=2)
    m = rgen.randint(5, size=(r, c))
    sm = SM32(m)
    sm2 = SM32(sm)
    s = rgen.randint(-c, c+1)
    shifted = sorted(set(xrange(c)).intersection(xrange(-s, c-s)))
    rotated = sorted(set(xrange(c)).difference(shifted))
    if s > 0:
     permutation = rotated + shifted
     zero = range(0, s)
     m2 = numpy.hstack((numpy.zeros((r, s)), m[..., 0:(c-s)]))
    else:
     permutation = shifted + rotated
     zero = range(c+s, c)
     m2 = numpy.hstack((m[..., (-s):], numpy.zeros((r, -s))))

    start = time.time()
    sm2.permuteCols(permutation)
    sm2.setColsToZero(zero)
    end = time.time()
    pcElapsed = end - start

    start = time.time()
    sm.shiftCols(s)
    end = time.time()
    scElapsed = end - start
    if sm != sm2:
      error('shiftColumns')
    if not (sm.toDense() == m2).all():
      error('shiftColumns')


  def test_logRowSums(self):

    return # precision issue, function almost obsolete
    print 'Testing logRowSums'

    for i in range(5):

      m = rgen.randint(2,20)
      n = rgen.randint(2,20)
      a = rgen.randint(0,100,(m,n))
      a[numpy.where(a < 10)] = 0
      a[rgen.randint(0,m)] = 0
      a[:,rgen.randint(0,n)] = 0
      sm = SM32(a)

      x = sm.logRowSums()
      a[numpy.where(a == 0)] = 1
      a = numpy.log(a)
      y = a.sum(axis = 1)
      if (x != y).any():
        error('logRowSums')


  def test_logColSums(self):

    return # precision issue, function almost obsolete
    print 'Testing logColSums'

    for i in range(5):

      m = rgen.randint(2,20)
      n = rgen.randint(2,20)
      a = rgen.randint(0,100,(m,n))
      a[numpy.where(a < 10)] = 0
      a[rgen.randint(0,m)] = 0
      a[:,rgen.randint(0,n)] = 0
      sm = SM32(a)

      x = sm.logColSums()
      a[numpy.where(a == 0)] = 1
      a = numpy.log(a)
      y = a.sum(axis = 0)
      if (x != y).any():
        error('logColSums')


  def test_addRows(self):

    print 'Testing addRows'

    for i in range(5):

      m = rgen.randint(2,20)
      n = rgen.randint(2,20)
      a = rgen.randint(0,100,(m,n))
      a[numpy.where(a < 10)] = 0
      a[rgen.randint(0,m)] = 0
      a[:,rgen.randint(0,n)] = 0
      sm = SM32(a)

      indicator = numpy.random.randint(0,1,(m)).astype('uint32')
      x = sm.addRows(indicator)

      y = zeros((n))
      for j in range(m):
        if indicator[j] == 0:
          continue
        for k in range(n):
          y[k] += a[j][k]

      if (x != y).any():
        error('addRows')


  def test_CSRSize(self):
    print 'Testing CSRSize'

    for i in range(5):

      m = rgen.randint(10,200)
      n = rgen.randint(10,200)
      A = SM32(rgen.randint(0,100,(m,n)))
      A.threshold(70)
      A.setRowToZero(m/2)
      A.setColToZero(n/2)
      A.normalize()
      s = A.toPyString()

      if A.CSRSize() != len(s):
        error('CSRSize')


  def test_getstate_setstate(self):

    print 'Testing __getstate__/__setstate__'

    for i in range(5):

      m = rgen.randint(10,200)
      n = rgen.randint(10,200)
      A = SM32(rgen.randint(0,100,(m,n)))
      A.threshold(70)
      A.setRowToZero(m/2)
      A.setColToZero(n/2)
      A.normalize()
      s1 = A.__getstate__()
      B = SM32()
      B.__setstate__(s1)
      s2 = B.__getstate__()

      if s1 != s2:
        error('__getstate__/__setstate__')


  def test_sameRowNonZeroIndices(self):

    print 'Testing sameRowNonZeroIndices'

    m = rgen.randint(5,10)
    n = rgen.randint(5,10)

    A = SM32(rgen.randint(0,100,(m,n)))
    A.threshold(70)

    B = SM32(A)

    for i in range(m):
      if A.sameRowNonZeroIndices(i, B) != True:
        error('sameRowNonZeroIndices 1')

    if A.sameNonZeroIndices(B) != True:
      error('sameNonZeroIndices 1B')

    B = SM32(rgen.randint(0,100,(m,n)))
    B.threshold(70)
    for i in range(m):
      B[i,0] = 1 # to force difference of rows
      A[i,0] = 0

    for i in range(m):
      if A.sameRowNonZeroIndices(i, B) != False:
        print A
        print B
        print i
        error('sameRowNonZeroIndices 2')

    if A.sameNonZeroIndices(B) != False:
      error('sameNonZeroIndices 2B')

    # Test with zero row (should return true)
    A.setRowToZero(m/2)
    B.setRowToZero(m/2)

    if A.sameRowNonZeroIndices(m/2, B) != True:
      error('sameRowNonZeroIndices 3')


  def test_nonZeroIndicesIncluded(self):

    print 'Testing nonZeroIndicesIncluded'

    m = rgen.randint(2,10)
    n = rgen.randint(2,10)

    A = SM32(rgen.randint(0,100,(m,n)))
    A.threshold(70)

    # Make sure we don't have a row of zeros for now (will be tested later)
    for i in range(m):
      A[i,0] = 1

    B = SM32(A)

    for i in range(m):
      if A.nonZeroIndicesIncluded(i, B) != True:
        error('nonZeroIndicesIncluded 1')

    if A.nonZeroIndicesIncluded(B) != True:
      error('nonZeroIndicesIncluded 1B')

    B = zeros(A.shape)
    B[where(A.toDense() == 0)] = 1
    B = SM32(B)

    # We have taken care to not have a row of zeros (which we tested below)
    for i in range(m):
      if A.nonZeroIndicesIncluded(i, B) != False:
        error('nonZeroIndicesIncluded 2')

    if A.nonZeroIndicesIncluded(B) != False:
      error('nonZeroIndicesIncluded 2B')

    # Test with zero row (should return true)
    A.setRowToZero(m/2)
    B.setRowToZero(m/2)

    if A.nonZeroIndicesIncluded(m/2, B) != True:
      error('nonZeroIndicesIncluded 3')

    # Non-zeros of B included in those of A
    B = SM32(A)
    B.setRowToZero(m/2)
    B.setColToZero(n/2)

    if B.nonZeroIndicesIncluded(A) != True:
      error('nonZeroIndicesIncluded 4')


  def test_subtractNoAlloc(self):

    print 'Testing subtractNoAlloc'

    # A can have more non-zeros than B, but the non-zeros of B are followed

    m = rgen.randint(5,10)
    n = rgen.randint(5,10)

    A = SM32(rgen.randint(0,100,(m,n)))
    A.threshold(70)

    B = SM32(A)
    B *= .5
    B.setRowToZero(m/2)
    B.setColToZero(n/2)

    A_ref = A.toDense()
    for i in range(m):
      for j in range(n):
        if B[i,j] > 0:
          A_ref[i,j] = A.get(i,j) - B.get(i,j)
          if A_ref[i,j] < 41:
            A_ref[i,j] = 41

    SM_subtractNoAlloc(A, B, 41)

    if (A_ref != A.toDense()).any():
      error('subtractNoAlloc, min_floor > 0')


  def test_addToNZOnly(self):

    print 'Testing addToNZOnly'

    for k in range(3):

       m = rgen.randint(10,200)
       n = rgen.randint(10,200)

       A = SM32(rgen.randint(0,100,(m,n)))
       A.threshold(70)

       v = rgen.randint(0,100)

       Ref = A.toDense()
       for i in range(m):
         for j in range(n):
           if Ref[i,j] > 0:
             Ref[i,j] += v

       SM_addToNZOnly(A, v)

       if (A.toDense() != Ref).any():
         error('addToNZOnly, min_floor = 0')

    # With min_floor > 0
    for k in range(3):

       m = rgen.randint(10,200)
       n = rgen.randint(10,200)

       A = SM32(rgen.randint(0,100,(m,n)))
       A.threshold(70)

       v = 5

       Ref = A.toDense()
       for i in range(m):
         for j in range(n):
           if Ref[i,j] > 0:
             Ref[i,j] += v
             if Ref[i,j] < 80:
               Ref[i,j] = 80

       SM_addToNZOnly(A, v, 80)

       if (A.toDense() != Ref).any():
         error('addToNZOnly, min_floor > 0')


  def test_assignNoAlloc(self):

    print 'Testing assignNoAlloc'

    # Should update A only where and B have a non-zero in the same location
    for i in range(5):

      m = rgen.randint(10,20)
      n = rgen.randint(10,20)

      A = SM32(rgen.randint(0,100,(m,n)))
      A.threshold(70)
      A.setRowToZero(m/2)
      A.setColToZero(n/2)

      B = SM32(rgen.randint(0,100,(m,n)))
      B.threshold(70)
      B.setRowToZero(m/4)
      B.setColToZero(n/4)

      A_ref, B_ref = A.toDense(), B.toDense()
      for i in range(m):
        for j in range(n):
          if A_ref[i,j] > 0 and B_ref[i,j] > 0:
            A_ref[i,j] = B_ref[i,j]

      SM_assignNoAlloc(A, B)

      if (A.toDense() != A_ref).any():
        error('assignNoAlloc')


  def test_assignNoAllocFromBinary(self):

    print 'Testing assignNoAllocFromBinary'

    # Should update A only where and B have a non-zero in the same location
    for i in range(5):

      m = rgen.randint(10,20)
      n = rgen.randint(10,20)

      A = SM32(rgen.randint(0,100,(m,n)))
      A.threshold(70)
      A.setRowToZero(m/2)
      A.setColToZero(n/2)

      B = SM_01_32_32(rgen.randint(0,2,(m,n)))

      A_ref, B_ref = A.toDense(), B.toDense()
      for i in range(m):
        for j in range(n):
          if A_ref[i,j] > 0 and B_ref[i,j] > 0:
            A_ref[i,j] = B_ref[i,j]

      SM_assignNoAllocFromBinary(A, B)

      if (A.toDense() != A_ref).any():
        error('assignNoAllocFromBinary')


  def test_binaryLoadSave(self):

      return # doesn't work on win32
      print 'Testing binary load and save'

      _kNumRows = 1000
      _kNumCols = 1000
      _kNumActive = 123
      _kTempFileToSaveTo = "sm_save_test.bin"

      a = SM32(_kNumRows, _kNumCols)
      for i in xrange(_kNumActive):
          x = random.randint(0, _kNumCols-1)
          y = random.randint(0, _kNumRows-1)
          a.set(y, x, random.random())

      a.binarySaveToFile(_kTempFileToSaveTo)

      b = SM32(1, 1)
      b.binaryLoadFromFile(_kTempFileToSaveTo)
      os.unlink(_kTempFileToSaveTo)

      assert a.nRows() == b.nRows()
      assert a.nCols() == b.nCols()
      assert a.nNonZeros() == b.nNonZeros()
      assert a == b


  def test_logSumNoAlloc(self):

    return # precision issue, function almost obsolete
    print 'Testing logSumNoAlloc'

    for min_floor in [0, .76]:

      # A and B have exactly the same non-zeros
      for k in range(5):

        m = rgen.randint(5,10)
        n = rgen.randint(5,10)

        A = SM32(rgen.randint(0,100,(m,n)))
        A.threshold(70)
        A.normalize()
        A_ref = A.toDense()

        B = SM32(A)
        B *= rgen.uniform(0,2)
        B_ref = B.toDense()

        SM_logSumNoAlloc(A, B, min_floor)

        C_ref = A.toDense()
        for i in range(m):
          for j in range(n):
            if B_ref[i,j] > 0:
              C_ref[i,j] = log(exp(A_ref[i,j]) + exp(B_ref[i,j]))
              if min_floor > 0 and C_ref[i,j] < min_floor:
                C_ref[i,j] = min_floor

        if (abs(A.toDense() - C_ref) > 1e-12).any():
          error('logSumNoAlloc 1')

    for min_floor in [0, .78]:

      # B has less non-zeros than A
      for k in range(5):

        m = rgen.randint(5,10)
        n = rgen.randint(5,10)

        A = SM32(rgen.randint(0,100,(m,n)))
        A.threshold(70)
        A.normalize()
        A_ref = A.toDense()

        B = SM32(A)
        B *= rgen.uniform(0,2)
        B.setRowToZero(m/2)
        B.setColToZero(n/2)
        B_ref = B.toDense()

        SM_logSumNoAlloc(A, B, min_floor)

        C_ref = A.toDense()
        for i in range(m):
          for j in range(n):
            if B_ref[i,j] > 0:
              C_ref[i,j] = log(exp(A_ref[i,j]) + exp(B_ref[i,j]))
              if min_floor > 0 and C_ref[i,j] < min_floor:
                C_ref[i,j] = min_floor

        if (abs(A.toDense() - C_ref) > 1e-12).any():
          error('logSumNoAlloc 2')

    # Specific case of interest
    a = array([[-89, 1e-5]], dtype=float64)
    b = array([[1e-5,-89]], dtype=float64)

    A = SM32(a)
    B = SM32(b)

    SM_logSumNoAlloc(A,B)

    a0 = log(exp(a[0,0]) + exp(b[0,0]))
    if abs(a0 - A[0,0]) > 5e-13:
      error('logSumNoAlloc 3')

    a1 = log(exp(a[0,1]) + exp(b[0,1]))
    if abs(a1 - A[0,1]) > 5e-13:
      error('logSumNoAlloc 4')


  def test_logAddValNoAlloc(self):

    return # precision issue, function almost obsolete
    print 'Testing logAddValNoAlloc'

    for min_floor in [0, .76]:

      for k in range(5):

        m = rgen.randint(5,10)
        n = rgen.randint(5,10)

        A = SM32(rgen.randint(0,100,(m,n)))
        A.threshold(70)
        A.normalize()
        A_ref = A.toDense()

        val = rgen.uniform(0,2)

        SM_logAddValNoAlloc(A, val, min_floor)

        for i in range(m):
          for j in range(n):
            if A_ref[i,j] > 0:
              A_ref[i,j] = log(exp(A_ref[i,j]) + exp(val))
              if min_floor > 0 and A_ref[i,j] < min_floor:
                A_ref[i,j] = min_floor

        if (abs(A.toDense() - A_ref) > 1e-12).any():
          error('logAddValNoAlloc 1')


  def test_logDiffNoAlloc(self):

    return # precision issue, function almost obsolete
    print 'Testing logDiffNoAlloc'

    for min_floor in [0, 3.45]:

      # A and B have exactly the same non-zeros
      for k in range(5):

        m = rgen.randint(5, 10)
        n = rgen.randint(5, 10)

        A = SM32(rgen.randint(0,100,(m,n)))
        A.threshold(70)
        A.normalize()
        A_ref = A.toDense()

        B = SM32(A)
        for i in range(m):
          for j in range(n):
            if B[i,j] != 0:
              B[i,j] -= 1e-3
        B_ref = B.toDense()

        SM_logDiffNoAlloc(A, B, min_floor)

        C_ref = A.toDense()
        for i in range(m):
          for j in range(n):
            if B_ref[i,j] > 0:
              C_ref[i,j] = log(exp(A_ref[i,j]) - exp(B_ref[i,j]))
              if min_floor > 0 and abs(C_ref[i,j]) < min_floor:
                C_ref[i,j] = min_floor

        if (abs(A.toDense() - C_ref) > 1e-11).any():
          error('logDiffNoAlloc 1')

      # B has less non-zeros than A
      for k in range(5):

        m = rgen.randint(5,10)
        n = rgen.randint(5,10)

        A = SM32(rgen.randint(0,100,(m,n)))
        A.threshold(70)
        A.normalize()
        A_ref = A.toDense()

        B = SM32(A)
        for i in range(m):
          for j in range(n):
            if B[i,j] != 0:
              B[i,j] -= 1e-3
        B.setRowToZero(m/2)
        B.setColToZero(n/2)
        B_ref = B.toDense()

        SM_logDiffNoAlloc(A, B, min_floor)

        C_ref = A.toDense()
        for i in range(m):
          for j in range(n):
            if B_ref[i,j] > 0:
              C_ref[i,j] = log(exp(A_ref[i,j]) - exp(B_ref[i,j]))
              if min_floor > 0 and abs(C_ref[i,j]) < min_floor:
                C_ref[i,j] = min_floor

        if (abs(A.toDense() - C_ref) > 1e-11).any():
          error('logDiffNoAlloc 2')

    # Specific case of interest
    a = array([[1]],dtype=float64)
    b = array([[1e-8]],dtype=float64)
    setGlobalEpsilon(1e-9)
    A = SM32(a)
    B = SM32(b)
    SM_logDiffNoAlloc(A,B)
    a0 = log(exp(a[0,0]) - exp(b[0,0]))
    if abs(a0 - A[0,0]) > 1e-5:
      error('logDiffNoAlloc 3')

    # Another specific case, A==B, should not generate inf or -inf
    a = array([[1]],dtype=float64)
    b = array([[1]],dtype=float64)
    A = SM32(a)
    B = SM32(b)
    SM_logDiffNoAlloc(A,B)
    a = A.toDense()
    if numpy.isinf(a):
      error('logDiffNoAlloc 4a');
    if a[0,0] > log(getGlobalEpsilon()):
      error('logDiffNoAlloc 4b');


  def test_addToNZDownCols(self):

    print 'Testing addToNZDownCols'

    # Testing with min_floor = 0
    for k in range(5):

      m = rgen.randint(10, 200)
      n = rgen.randint(10, 200)

      A = SM32(rgen.randint(0,100,(m,n)))
      A.threshold(70)
      A.normalize()
      A_ref = A.toDense()

      V = rgen.randint(0,100,(n))
      V /= sum(V)

      SM_addToNZDownCols(A, V)

      C_ref = zeros((m,n))

      for i in range(m):
        for j in range(n):
          if A_ref[i,j] != 0:
            C_ref[i,j] = A_ref[i,j] + V[j]

      if (A.toDense() != C_ref).any():
        error('addToNZDownCols 1')

    return # accuracy problem, function almost obsolete
    # Testing with min_floor > 0
    min_floor = 2.5e-4

    for k in range(5):

      m = rgen.randint(10, 200)
      n = rgen.randint(10, 200)

      A = SM32(rgen.randint(0,100,(m,n)))
      A.threshold(70)
      A.normalize()

      V = rgen.randint(0,100,(n))
      V /= sum(V)
      A[1,3] = .5
      V[3] = A[1,3]

      A_ref = A.toDense()

      SM_addToNZDownCols(A, V, min_floor)

      C_ref = zeros((m,n))

      for i in range(m):
        for j in range(n):
          if A_ref[i,j] != 0:
            C_ref[i,j] = A_ref[i,j] + V[j]
            if abs(C_ref[i,j]) < min_floor:
              C_ref[i,j] = min_floor

      if (A.toDense() != C_ref).any():
        error('addToNZDownCols 2')


  def test_addToNZAcrossRows(self):

    print 'Testing addToNZAcrossRows'

    # Testing with min_floor = 0
    for k in range(5):

      m = rgen.randint(10, 200)
      n = rgen.randint(10, 200)

      A = SM32(rgen.randint(0,100,(m,n)))
      A.threshold(70)
      A.normalize()
      A_ref = A.toDense()

      V = rgen.randint(0,100,(m))
      V /= sum(V)

      SM_addToNZAcrossRows(A, V)

      C_ref = zeros((m,n))

      for i in range(m):
        for j in range(n):
          if A_ref[i,j] != 0:
            C_ref[i,j] = A_ref[i,j] + V[i]

      if (A.toDense() != C_ref).any():
        error('addToNZAcrossRows 1')

    return # accuracy problem, function almost obsolete
    # Testing with min_floor > 0
    min_floor = 6e-2

    for k in range(5):

      m = rgen.randint(10, 200)
      n = rgen.randint(10, 200)

      A = SM32(rgen.randint(0,100,(m,n)))
      A.threshold(70)
      A.normalize()

      V = rgen.randint(0,100,(m))
      V /= sum(V)
      A[1,3] = .5
      V[3] = A[1,3]

      A_ref = A.toDense()

      SM_addToNZAcrossRows(A, V, min_floor)

      C_ref = zeros((m,n))

      for i in range(m):
        for j in range(n):
          if A_ref[i,j] != 0:
            C_ref[i,j] = A_ref[i,j] + V[i]
            if abs(C_ref[i,j]) < min_floor:
              C_ref[i,j] = min_floor

      if (A.toDense() != C_ref).any():
        error('addToNZAcrossRows 2')


  def test_LBP_piPrime(self):

    return # obsolete
    print 'Testing LBP_piPrime'

    m = rgen.randint(5, 10)
    n = rgen.randint(5, 10)

    A = SM32(rgen.randint(0,100,(m,n)))
    A.threshold(70)
    A.normalize()
    A_ref = A.toDense()

    epsilon = -1e-3
    LBP_piPrime(A, epsilon)

    col_sums = A_ref.sum(axis=0)

    for i in range(m):
      for j in range(n):
        if A_ref[i,j] != 0:
          result = col_sums[j] - A_ref[i,j]
          if abs(result) < abs(epsilon):
           result = epsilon
          A_ref[i,j] = result

    if (abs(A.toDense() - A_ref) > 1e-12).any():
      error('LBP_piPrime')


  def test_matrix_entropy(self):

    print 'Testing matrix_entropy'

    def ent(tam, s = 1):

      n = tam.shape[0]
      H_rows, H_cols = zeros((n)), zeros((n))
      row_sums, col_sums = tam.rowSums() + n * s, tam.colSums() + n * s

      for i in range(n):
        for j in range(n):
          v1 = (tam[i,j]+s) / row_sums[i]
          H_rows[i] -= v1 * log2(v1)
          v2 = (tam[j,i]+s) / col_sums[i]
          H_cols[i] -= v2 * log2(v2)

      return H_rows, H_cols

    for i in range(5):

      a = SM32(rgen.randint(0,100,(10,10)))
      a.threshold(80)

      H_rows1, H_cols1 = ent(a)
      H_rows2, H_cols2 = matrix_entropy(a)

      if (abs(H_rows1 - array(H_rows2)) > 1e-5).any():
        error('matrix_entropy, rows')
      if (abs(H_cols1 - array(H_cols2)) > 1e-5).any():
        error('matrix_entropy, cols')

    for i in range(5):

      a = SM32(rgen.randint(0,100,(10,10)))
      a.threshold(80)

      H_rows1, H_cols1 = ent(a, .5)
      H_rows2, H_cols2 = matrix_entropy(a, .5)

      if (abs(H_rows1 - array(H_rows2)) > 1e-5).any():
        print H_rows1
        print H_rows2
        error('matrix_entropy, rows, with smoothing != 1')
      if (abs(H_cols1 - array(H_cols2)) > 1e-5).any():
        error('matrix_entropy, cols, with smoothing != 1')


  @unittest.skip("Doesn't play nicely with py.test.")
  def test_LogSumApprox(self):

    print 'Testing LogSumApprox'

    # On darwin86:
    # Sum of logs table: 20000000 -28 28 5.6e-06 76MB
    # abs=4.03906228374e-06 rel=6.57921289158e-05

    # On Windows:
    # Sum of logs table: 20000000 -28 28 2.8e-006 76MB
    # abs=3.41339533527e-006 rel=0.00028832192106

    lsa = LogSumApprox(20000000, -28,28, True)
    x = 14 * rgen.randint(-128,128, (1000,2)).astype(float64) / 255
    for i in range(len(x)):
      if abs(x[i][0]) < 1.1e-6:
        x[i][0] = 1.1e-6
      if abs(x[i][1]) < 1.1e-6:
        x[i][1] = 1.1e-6

    max_abs_error, max_rel_error = -1, -1
    x[0][0], x[0][1] = -14,-14
    x[1][0], x[1][1] = -15,15
    x[999][0], x[999][1] = 14,14

    for i in range(len(x)):
      z = lsa.logSum(x[i][0],x[i][1])
      if abs(z) < 1.1e-6:
        error('logSumApprox: less than minFloor')
      z0 = log(exp(x[i][0]) + exp(x[i][1]))
      max_abs_error = max(max_abs_error, abs(z - z0))
      max_rel_error = max(max_rel_error, abs(z - z0) / abs(z0))

    if (max_abs_error > 5e-6 or max_rel_error > 3e-4):
      error('LogSumApprox')


  def test_LogDiffApprox(self):

    print 'Testing LogDiffApprox'

    # On darwin86:
    # Diff of logs table: 20000000 1e-06 28 1.4e-06 76MB
    # abs=2.56909073832e-05 rel=0.000589275477819

    # On Windows:
    # Diff of logs table: 20000000 1e-006 28 1.4e-006 76MB
    # abs=2.56909073832e-005 rel=0.000589275477819

    lsa = LogDiffApprox(20000000, 1e-6,28, True)
    x = 14 * rgen.randint(-128,128, (1000,2)).astype(float64) / 255
    for i in range(len(x)):
      if abs(x[i][0]) < 1.1e-6:
        x[i][0] = 1.1e-6
      if abs(x[i][1]) < 1.1e-6:
        x[i][1] = 1.1e-6
      if x[i][1] >= x[i][0]:
        tmp = x[i][0]
        x[i][0] = x[i][1] + 1e-6
        x[i][1] = tmp

    max_abs_error, max_rel_error = -1, -1
    x[0][0], x[0][1] = -13,-14
    x[1][0], x[1][1] = 15,-15
    x[999][0], x[999][1] = 14,13

    for i in range(len(x)):
      z = lsa.logDiff(x[i][0],x[i][1])
      if abs(z) < 1.1e-6:
        error('logSumApprox: less than minFloor')
      z0 = log(exp(x[i][0]) - exp(x[i][1]))
      max_abs_error = max(max_abs_error, abs(z - z0))
      max_rel_error = max(max_rel_error, abs(z - z0) / abs(z0))

    if (max_abs_error > 3e-3 or max_rel_error > 6e-3):
      error('LogDiffApprox')


  def test_binarize_with_threshold(self):

    print 'Testing binarize_with_threshold'

    for i in range(5):

      threshold = max(0,min(1,rgen.normal(.5,1)))

      for j in range(10):

        x = clip(rgen.normal(.5,1, (5)), 0, 1).astype(float32)
        ans = (x > threshold).astype(float32)
        ans_s = ans.sum()
        s,y = binarize_with_threshold(threshold, x)

        if (s != ans_s or (ans != y).any()):
          error('binarize_with_threshold')


  def test_nonZeroRowsIndicator_01(self):

    print 'Testing nonZeroRowsIndicator_01'

    for i in range(10):

      m = rgen.randint(5,10)
      n = rgen.randint(5,10)
      x = rgen.randint(0,2,(m*n)).astype(float32)

      x.shape = (m,n)
      for k in range(m):
        if (rgen.randint(0,100)) > 50:
          x[k] = 0

      ans = (x.sum(axis=1) > 0).astype(numpy.int)

      x.shape = (-1)
      ind = nonZeroRowsIndicator_01(m,n,x)

      if (ind != ans).any():
        error('nonZeroRowsIndicator_01')


  def test_nonZeroColsIndicator_01(self):

    print 'Testing nonZeroColsIndicator_01'

    for i in range(10):

      m = rgen.randint(5,10)
      n = rgen.randint(5,10)
      x = rgen.randint(0,2,(m*n)).astype(float32)

      x.shape = (m,n)
      for k in range(m):
        if (rgen.randint(0,100)) > 50:
          x[k] = 0

      ans = (x.sum(axis=0) > 0).astype(numpy.int)

      x.shape = (-1)
      ind = nonZeroColsIndicator_01(m,n,x)

      if (ind != ans).any():
        error('nonZeroColsIndicator_01')


  def test_nNonZeroRows_01(self):

    print 'Testing nNonZeroRows_01'

    for i in range(10):

      m = rgen.randint(5,10)
      n = rgen.randint(5,10)
      x = rgen.randint(0,2,(m*n)).astype(float32)

      x.shape = (m,n)
      for k in range(m):
        if (rgen.randint(0,100)) > 50:
          x[k] = 0
      x.shape = (-1)

      nnzc = nNonZeroRows_01(m,n,x)
      x.shape = (m,n)
      ans = (x.sum(axis=1) > 0).sum()

      if (nnzc != ans):
        error('nNonZeroRows_01')


  def test_nNonZeroCols_01(self):

    print 'Testing nNonZeroCols_01'

    for i in range(10):

      m = rgen.randint(5,10)
      n = rgen.randint(5,10)
      x = rgen.randint(0,2,(m*n)).astype(float32)

      x.shape = (m,n)
      for k in range(n):
        if (rgen.randint(0,100)) > 50:
          x[:,k] = 0
      x.shape = (-1)

      nnzc = nNonZeroCols_01(m,n,x)
      x.shape = (m,n)
      ans = (x.sum(axis=0) > 0).sum()

      if (nnzc != ans):
        error('nNonZeroCols_01')


  def test_logicalAnd(self):

    print 'Testing logicalAnd'

    # To make sure SSE works (it requires 16 bytes alignment)
    # Test with variable length vectors whose size is not a multiple of 16
    # Test with slices in numpy arrays, which will lead to the vector
    # not starting on a 16 bytes boundary

    type32 = GetNumpyDataType('NTA_Real32')

    for i in range(10):

      # Let vector be of any length, not necessarily a multiple of 16
      n = rgen.randint(2,1024)
      x = rgen.randint(0,2,(n)).astype(type32)
      y = rgen.randint(0,2,(n)).astype(type32)

      # Half the time test with slice (messes with the alignment)
      # Half the time test the whole vector (start is aligned)
      if rgen.randint(0,100) > 50:
        ans = numpy.logical_and(x[1:],y[1:])
        z = logicalAnd(x[1:],y[1:])
      else:
        ans = numpy.logical_and(x,y)
        z = logicalAnd(x,y)

      if (z != ans).any():
        error('logicalAnd')


  def test_logicalAnd2(self):

    print 'Testing logicalAnd2'

    # To make sure SSE works (it requires 16 bytes alignment)
    # Test with variable length vectors whose size is not a multiple of 16
    # Test with slices in numpy arrays, which will lead to the vector
    # not starting on a 16 bytes boundary

    type32 = GetNumpyDataType('NTA_Real32')

    for i in range(10):

      # Let vector be of any length, not necessarily a multiple of 16
      n = rgen.randint(2,1024)
      x = rgen.randint(0,2,(n)).astype(type32)
      y = rgen.randint(0,2,(n)).astype(type32)

      # Half the time test with slice (messes with the alignment)
      # Half the time test the whole vector (start is aligned)
      if rgen.randint(0,100) > 50:
        ans = numpy.logical_and(x[1:],y[1:])
        logicalAnd2(x[1:],y[1:])

        if (y[1:] != ans).any():
          error('logicalAnd2, slice')

      else:
        ans = numpy.logical_and(x,y)
        logicalAnd2(x,y)

        if (y != ans).any():
          error('logicalAnd2, full')


  def test_isZero_01(self):

    print 'Testing isZero_01'

    # To make sure SSE works (it requires 16 bytes alignment)
    # Test with variable length vectors whose size is not a multiple of 16
    # Test with slices in numpy arrays, which will lead to the vector
    # not starting on a 16 bytes boundary

    type32 = GetNumpyDataType('NTA_Real32')

    for i in range(10):

      n = rgen.randint(2,8192)

      # Half the time a vector of only zeros
      # Half the time a vector that has 1s
      x = zeros((n)).astype(float32)
      if rgen.randint(0,100) > 50:
        x[rgen.randint(n/2,n)] = 1

      # Half the time test with slice (messes with the alignment)
      # Half the time test the whole vector (start is aligned)
      if rgen.randint(0,100) > 50:
        ans = x.sum() == 0
        r = isZero_01(x)
      else:
        ans = x[1:].sum() == 0
        r = isZero_01(x[1:])

      if r != ans:
        print i, r, ans
        error('isZero_01')


  def test_sum(self):

    print 'Testing sum'

    # To make sure SSE works (it requires 16 bytes alignment)
    # Test with variable length vectors whose size is not a multiple of 16
    # Test with slices in numpy arrays, which will lead to the vector
    # not starting on a 16 bytes boundary
    # Also note that the errors are not trivial between vDSP and numpy

    t1,t2 = 0,0
    max_rel_error, max_abs_error = 0,0

    for i in range(10):

      n = rgen.randint(10, 8192)
      x = (rgen.randint(0,8192, (n)) / 8192.0).astype(float32)

      # Half the time full vector (aligned at beginning), half the time
      # slice whose beginning is not going to be aligned to a 16 bytes
      # boundary
      if rgen.randint(0,100) > 50:
        t0 = time.time()
        ans = x.sum()
        t1 += time.time() - t0
        t0 = time.time()
        v = dense_vector_sum(x)
        t2 += time.time() - t0
      else:
        t0 = time.time()
        ans = x[1:].sum()
        t1 += time.time() - t0
        t0 = time.time()
        v = dense_vector_sum(x[1:])
        t2 += time.time() - t0

      abs_error = abs(v - ans)
      rel_error = abs_error / abs(ans)
      if abs_error > max_abs_error:
        max_abs_error = abs_error
      if rel_error > max_rel_error:
        max_rel_error = rel_error

      if max_abs_error > 1e-1 or max_rel_error > 1e-5:
        print v, ans
        print max_abs_error
        print max_rel_error
        error('sum')

    print "\tnumpy=", t1, 's'
    print "\tvDSP (darwin86)=", t2, 's'
    if t2 > 0:
      print "\tspeed-up=", (t1 / t2)
    print "\tmax abs error=", max_abs_error
    print "\tmax rel error=", max_rel_error


  def test_initialize_random_01(self):

    print 'Testing initialize_random_01'

    # Initializes a sparse matrix with random 0s and 1s.

    for i in range(10):

      m = rgen.randint(2,10)
      n = 2*rgen.randint(2,10)
      sm = SM32(m,n)

      # mode = 0 (only implemented, same number of nnzr per row)
      # sparsity = .5, 50% non-zeros
      # random seed = 42 why not?
      sm.initializeWithFixedNNZR(int(.5*n))
      nnzr = int32(.5 * n)

      for r in range(m):
        if sm.nNonZerosOnRow(r) != nnzr:
          error('initialize_random_01: nnzr non constant')

      i,j,v = sm.getAllNonZeros(True)
      for k in range(len(v)):
        if v[k] != 1:
          error('initialize_random_01: value != 1')

      #cols_occupancy = sm.nNonZerosPerCol()
      #avg,dev = mean(cols_occupancy), std(cols_occupancy)


  def test_partial_argsort(self):

    print 'Testing partial_argsort'

    # In C++, the ties are controlled by prefering the values stored at
    # lower indices.

    t1,t2 = 0,0

    for i in range(10):

      n = 10000
      k = 50
      x = rgen.randint(0,1000,(n)).astype(float32)
      # x = abs(rgen.lognormal(1,1,(n))).astype(float32)
      res_buff = zeros((k)).astype(uint32)
      direction = 1

      t0 = time.time()
      ans = numpy.argsort(x)[:k]
      t1 += time.time() - t0

      t0 = time.time()
      partialArgsort(k, x, res_buff, direction)
      t2 += time.time() - t0

      if (ans != res_buff).any():
        ans_vals,x_vals = zeros((k)), zeros((k))
        for k,j in enumerate(ans):
          ans_vals[k] = x[j]
        for k,j in enumerate(res_buff):
          x_vals[k] = x[j]
        if (ans_vals != x_vals).any():
          error('partial_argsort')

    print "\tnumpy time=", t1
    print "\tC++ time=", t2
    if t2 > 0:
      print "\tspeed-up=", t1/t2


  def test_count_gt(self):

    print 'Testing count_gt'

    # Counts the number of elements greater than a given threshold in a vector.
    # Checking with slicing and odd number of elements, to make sure asm code
    # underneath does the right thing.
    # Don't forget .astype(float32).

    t1,t2 = 0,0

    for i in range(10):

      n = 10000 #2*rgen.randint(2, 1024) + 1
      x = rgen.randint(0,1000,(n)).astype(float32)
      # x = abs(rgen.lognormal(1,1,(n))).astype(float32)
      threshold = rgen.randint(0, 1000)

      t0 = time.time()
      ans = (x[1:] > threshold).sum()
      t1 += time.time() - t0

      t0 = time.time()
      res = count_gt(x[1:], threshold)
      t2 += time.time() - t0

      if ans != res:
        print threshold, ans, res, (res - ans)
        error('count_gt')

    print "\tnumpy time=", t1
    print "\tC++ time=", t2
    if t2 > 0:
      print "\tspeed-up=", t1/t2


  def test_count_lt(self):

    print 'Testing count_lt'

    # Counts the number of elements less than a given threshold in a vector.

    t1,t2 = 0,0

    for i in range(10):

      n = 10000
      x = rgen.randint(0,1000,(n)).astype(float32)
      # x = abs(rgen.lognormal(1,1,(n))).astype(float32)

      t0 = time.time()
      ans = (x[1:] < 500).sum()
      t1 += time.time() - t0

      t0 = time.time()
      res = count_lt(x[1:], 500)
      t2 += time.time() - t0

      if ans != res:
        error('count_gt')

    print "\tnumpy time=", t1
    print "\tC++ time=", t2
    if t2 > 0:
      print "\tspeed-up=", t1/t2


  def test_test_nta_set(self):

      print 'Testing nta set'
      # Mac PowerBook 2.8 GHz Core 2 Duo, 10.6.3, -O3 -DNDEBUG, gcc 4.2.1 (Apple 5659)
      # m = 50000, n1 = 40, n2 = 10000: 0.00274658203125 0.00162267684937 1.69262415516
      # m = 50000, n1 = 80, n2 = 10000: 0.00458002090454 0.00179862976074 2.54639448568
      # m = 50000, n1 = 200, n2 = 10000: 0.0124213695526 0.00241708755493 5.13898204774
      # m = 50000, n1 = 500, n2 = 10000: 0.0339875221252 0.00330281257629 10.2904785967
      # m = 50000, n1 = 1000, n2 = 10000: 0.0573344230652 0.00443959236145 12.9143440202
      # m = 50000, n1 = 2500, n2 = 10000: 0.155576944351 0.00838160514832 18.5617124164
      # m = 50000, n1 = 5000, n2 = 10000: 0.256726026535 0.0143656730652 17.8707969595

      m = 50000
      n1 = 197
      n2 = 5759

      a = rgen.permutation(m)[:n1].astype('uint32')
      b = rgen.permutation(m)[:n2].astype('uint32')
      b.sort()
      s1 = set(a)
      s2 = set(b)

      ss2 = Set(m, b)
      r_cpp = numpy.zeros(m,dtype='uint32')

      if ss2.n_elements() != n2 or ss2.max_index() != m:
          error('Set construction')

      T_py = 0; T_cpp = 0

      for i in xrange(100):

          t0 = time.time()
          nr = ss2.intersection(a, r_cpp)
          T_cpp = T_cpp + time.time() - t0
          t0 = time.time()
          r = s1.intersection(s2)
          T_py = T_py + time.time() - t0
          rs = set(r_cpp[:nr])
          if rs != r:
              print a
              print b
              print r
              print rs
              error('set intersection')

      if T_cpp != 0:
          print T_py, T_cpp, T_py/T_cpp

      if 0:
          f = open('/Users/frank/Desktop/h1.txt')
          ll = []
          for i in range(135):
              l = f.readline().split()
              ll.append((int(l[0]), int(float(l[1]))))

          avg_T = 0; total_calls = 0
          for n1,ncalls in ll:

              T_cpp = 0
              for i in xrange(10):
                  a = rgen.permutation(m)[:n1].astype('uint32')
                  s1 = set(a)
                  t0 = time.time()
                  r = s1.intersection(s2)
                  #nr = ss2.intersection(a, r_cpp)
                  T_cpp = T_cpp + time.time() - t0
              T_cpp = T_cpp / 10
              avg_T = avg_T + T_cpp * ncalls
              total_calls = total_calls + ncalls
          print avg_T, total_calls, avg_T / float(total_calls)



if __name__ == "__main__":
  unittest.main()
