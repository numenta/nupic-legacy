
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

import cPickle

# SparseMatrix is a versatile class that offers a wide range of functionality.
# This tutorial will introduce you to the main features of SparseMatrix.

# SparseMatrix is located in nupic.bindings.math, and here is the import you need:

from nupic.bindings.math import *


# 1. Types of sparse matrices:
# ===========================

# There are three types of SparseMatrix, depending on the precision you need 
# in your application: 32 and 32 bits. To create a SparseMatrix holding 
# floating point values of the desired precision, simply specify it as the 
# 'dtype' parameter in the constructor:

s = SparseMatrix(dtype='Float32')


# 2. Global Epsilon:
# =================

# By default, NuPIC is compiled to handle only 32 bits of precision at max,
# and sparse matrices consider a floating point value to be zero if it's less than 
# 1e-6 (the best precision possible with 32 bits floats). This value of 1e-6 is 
# called "epsilon", and it is a global value used throughout NuPIC to deal with
# near-zero floating point numbers. 

# If this is not enough, NuPIC can be recompiled to access more precision.
# With NTA_DOUBLE_PRECISION or NTA_QUAD_PRECISION set at compile time, NuPIC can 
# use 32 bits to represent floating point values. The global epsilon can 
# then be set to smaller values via the variable nupic::Epsilon in nupic/math/math.hpp
print '\nGlobal epsilon :', getGlobalEpsilon()


# 3. Creation of sparse matrices:
# ==============================

# There are several convenient ways to create sparse matrices. 
# You can create a SparseMatrix by passing it a 2D array:

s = SparseMatrix([[1,2],[3,4]], dtype='Float32')
print '\nFrom array 32\n', s

# ... or by passing it a numpy.array:

s = SparseMatrix(numpy.array([[1,2],[3,4]]),dtype='Float32')
print '\nFrom numpy array 32\n', s

# ... or by using one of the shortcuts: SM32, SM32:

s = SM32([[1,2],[3,4]])
print '\nWith shortcut 32\n', s

# It is also possible to create an empty SparseMatrix, or a copy of another
# SparseMatrix, or a SparseMatrix from a string in CSR format:

s_empty = SM32()
print '\nEmpty sparse matrix\n', s_empty

s_string = SM32('sm_csr_1.5 26 2 2 4 2 0 1 1 2 2 0 3 1 4')
print '\nSparse matrix from string\n', s_string

# A sparse matrix can be converted to a dense one via toDense:

a = numpy.array(s_string.toDense())
print '\ntoDense\n', a

# To set a sparse matrix from a dense one, one can use fromDense:

s = SM32()
s.fromDense(numpy.random.random((4,4)))
print '\nfromDense\n', s

# A sparse matrix can be pickled:
cPickle.dump(s, open('sm.txt', 'wb'))
s2 = cPickle.load(open('sm.txt', 'rb'))
print '\nPickling\n', s2

# 4. Simple queries:
# =================

# You can print a SparseMatrix, and query it for its number of rows, columns, 
# non-zeros per row or column... There are many query methods available.
# All row operations are mirrored by the equivalent column operations
# Most operations are available either for a given row, or a given col, or
# all rows or all cols simultaneously. All col operations can be pretty efficient,
# even if the internal storage is CSR.

s = SM32(numpy.random.random((4,4)))
s.threshold(.5)

print '\nPrint\n', s
print '\nNumber of rows ', s.nRows()
print 'Number of columns ', s.nCols()
print 'Is matrix zero? ', s.isZero()
print 'Total number of non zeros ', s.nNonZeros()
print 'Sum of all values ', s.sum()
print 'Prod of non-zeros ', s.prod()
print 'Maximum value and its location ', s.max()
print 'Minimum value and its location ', s.min()

print 'Number of non-zeros on row 0 ', s.nNonZerosOnRow(0)
print 'If first row zero? ', s.isRowZero(0)
print 'Number of non-zeros on each row ', s.nNonZerosPerRow() 
print 'Minimum on row 0 ', s.rowMin(0)
print 'Minimum values and locations for all rows', s.rowMin() 
print 'Maximum on row 0 ', s.rowMax(0)
print 'Maximum values and locations for all rows', s.rowMax() 
print 'Sum of values on row 0 ', s.rowSum(0)
print 'Sum of each row ', s.rowSums()
print 'Product of non-zeros on row 1', s.rowProd(1)
print 'Product of each row ', s.rowProds()

print 'Number of non-zeros on col 0 ', s.nNonZerosOnCol(0)
print 'If first col zero? ', s.isColZero(0)
print 'Number of non-zeros on each col ', s.nNonZerosPerCol() 
print 'Minimum on col 0 ', s.colMin(0)
print 'Minimum values and locations for all cols', s.colMin() 
print 'Maximum on col 0 ', s.colMax(0)
print 'Maximum values and locations for all cols', s.colMax() 
print 'Sum of values on col 0 ', s.colSum(0)
print 'Sum of each col ', s.colSums()
print 'Product of non-zeros on col 1', s.colProd(1)
print 'Product of each col ', s.colProds()


# 5. Element access and slicing:
# =============================

# It is very easy to access individual elements:

print '\n', s
print '\ns[0,0] = ', s[0,0], 's[1,1] = ', s[1,1]

s[0,0] = 3.5
print 'Set [0,0] to 3.5 ', s[0,0]

# There are powerful slicing operations:

print '\ngetOuter\n', s.getOuter([0,2],[0,2])
s.setOuter([0,2],[0,2],[[1,2],[3,4]])
print '\nsetOuter\n', s 

s.setElements([0,1,2],[0,1,2],[1,1,1])
print '\nsetElements\n', s
print '\ngetElements\n', s.getElements([0,1,2],[0,1,2])

s2 = s.getSlice(0,2,0,3)
print '\ngetSlice\n', s2
s.setSlice(1,1, s2)
print '\nsetSlice\n', s

# A whole row or col can be set to zero with one call:

s.setRowToZero(1)
print '\nsetRowToZero\n', s

s.setColToZero(1)
print '\nsetColToZero\n', s

# Individual rows and cols can be retrieved as sparse or dense vectors:

print '\nrowNonZeros ', s.rowNonZeros(0)
print 'colNonZeros ', s.colNonZeros(0)
print 'getRow ', s.getRow(0)
print 'getCol ', s.getCol(0)


# 6. Dynamic features:
# ===================

# SparseMatrix is very dynamic. Rows and columns can be added and deleted. 
# A sparse matrix can also be resized and reshaped.

print '\n', s
s.reshape(2,8)
print '\nreshape 2 8\n', s
s.reshape(8,2)
print '\nreshape 8 2\n', s
s.reshape(1,16)
print '\nreshape 1 16\n', s
s.reshape(4,4)
print '\nreshape 4 4\n', s

s.resize(5,5)
print '\nresize 5 5\n', s
s.resize(3,3)
print '\nresize 3 3\n', s
s.resize(4,4)
print '\nresize 4 4\n', s

s.deleteRows([3])
print '\ndelete row 3\n', s
s.deleteCols([1])
print '\ndelete col 1\n', s

s.addRow([1,2,3])
print '\nadd row 1 2 3\n', s
s.addCol([1,2,3,4])
print '\nadd col 1 2 3 4\n', s

s.deleteRows([0,3])
print '\ndelete rows 0 and 3\n', s
s.deleteCols([1,2])
print '\ndelete cols 1 and 2\n', s

# It is also possible to threshold a row, column or whole sparse matrix.
# This operation usually introduces zeros.

s.normalize()
print '\n', s
s.thresholdRow(0, .1)
print '\nthreshold row 0 .1\n', s
s.thresholdCol(1, .1)
print '\nthreshold col 1 .1\n', s
s.threshold(.1)
print '\nthreshold .1\n', s


# 7. Element wise operations:
# ==========================

# Element wise operations are prefixed with 'element'. There are row-oriented
# column-oriented and whole matrix element-wise operations.

s = SM32(numpy.random.random((4,4)))
print '\n', s

s.elementNZInverse()
print '\nelementNZInverse\n', s

s.elementNZLog()
print '\nelementNZLog\n', s

s = abs(s)
print '\nabs\n', s

s.elementSqrt()
print '\nelementSqrt\n', s

s.add(4)
print '\nadd 4\n', s

s.normalizeRow(1, 10)
print '\nnormalizeRow 1 10\n', s
print 'sum row 1 = ', s.rowSum(1)

s.normalizeCol(0, 3)
print '\nnormalizeCol 0 3\n', s
print 'sum col 0 = ', s.colSum(0)

s.normalize(5)
print '\nnormalize to 5\n', s
print 'sum = ', s.sum()

s.normalize()
print '\nnormalize\n', s
print 'sum = ', s.sum()

s.transpose()
print '\ntranspose\n', s

s2 = SM32(numpy.random.random((3,4)))
print '\n', s2
s2.transpose()
print '\ntranspose rectangular\n', s2
s2.transpose()
print '\ntranspose rectangular again\n', s2


# 8. Matrix vector and matrix matrix operations:
# =============================================

# SparseMatrix provides matrix vector multiplication on the right and left,
# as well as specialized operations between the a vector and the rows
# of the SparseMatrix.

x = numpy.array([1,2,3,4])
print '\nx = ', x
print 'Product on the right:\n', s.rightVecProd(x)
print 'Product on the left:\n', s.leftVecProd(x)
print 'Product of x elements corresponding to nz on each row:\n', s.rightVecProdAtNZ(x)
print 'Product of x elements and nz:\n', s.rowVecProd(x)
print 'Max of x elements corresponding to nz:\n', s.vecMaxAtNZ(x)
print 'Max of products of x elements and nz:\n', s.vecMaxProd(x)
print 'Max of elements of x corresponding to nz:\n', s.vecMaxAtNZ(x)

# axby computes linear combinations of rows and vectors

s.axby(0, 1.5, 1.5, x)
print '\naxby 0 1.5 1.5\n', s
s.axby(1.5, 1.5, x)
print '\naxby 1.5 1.5\n', s

# The multiplication operator can be used both for inner and outer product,
# depending on the shape of its operands, when using SparseMatrix instances:

s_row = SM32([[1,2,3,4]])
s_col = SM32([[1],[2],[3],[4]])
print '\nInner product: ', s_row * s_col
print '\nOuter product:\n', s_col * s_row

# SparseMatrix supports matrix matrix multiplication:
s1 = SM32(numpy.random.random((4,4)))
s2 = SM32(numpy.random.random((4,4)))

print '\nmatrix matrix multiplication\n', s1 * s2

# The block matrix vector multiplication treats the matrix as if it were
# a collection of narrower matrices. The following multiplies a1 by x and then a2 by x,
# where a1 is the sub-matrix of size (4,2) obtained by considering 
# only the first two columns of a, and a2 the sub-matrix obtained by considering only
# the last two columns of x.

a = SM32([[1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16]])
x = [1,2,3,4]
print a.blockRightVecProd(2, x)

# To do an element multiplication of two matrices, do:

print a
b = SM32(numpy.random.randint(0,2,(4,4)))
print b
a.elementNZMultiply(b)
print a

# In general, the "element..." operations implement element by element operations.


# 9. Arithmetic operators:
# =======================

# It is possible to use all 4 arithmetic operators, with scalars or matrices:

print '\ns + 3\n', s + 3
print '\n3 + s\n', 3 + s
print '\ns - 1\n', s - 1
print '\n1 - s\n', 1 - s
print '\ns + s\n', s + s
print '\ns * 3\n', s * 3
print '\n3 * s\n', 3 * s
print '\ns * s\n', s * s
print '\ns / 3.1\n', s / 3.1

# ... and to write arbitrarily linear combinations of sparse matrices:

print '\ns1 + 2 * s - s2 / 3.1\n', s1 + 2 * s - s2 / 3.1

# In place operators are supported:

s += 3.5
print '\n+= 3.5\n', s
s -= 3.2
print '\n-= 3.2\n', s
s *= 3.1
print '\n*= 3.1\n', s
s /= -1.5
print '\n/= -1.5\n', s


# 10. Count/find:
# ==============

# Use countWhereEqual and whereEqual to count or find the elements that have 
# a specific value. The first four parameters define a box in which to look:
# [begin_row, end_row) X [begin_col, end _col). The indices returned by whereEqual
# are relative to the orignal matrix. countWhereEqual is faster than using len()
# on the list returned by whereEqual.

s = SM32(numpy.random.randint(0,3,(5,5)))

print '\nThe matrix is now:\n', s
print '\nNumber of elements equal to 0=', s.countWhereEqual(0,5,0,5,0)
print 'Number of elements equal to 1=', s.countWhereEqual(0,5,0,5,1)
print 'Number of elements equal to 2=', s.countWhereEqual(0,5,0,5,2)
print '\nIndices of the elements == 0:', s.whereEqual(0,5,0,5,0)
print '\nIndices of the elements == 1:', s.whereEqual(0,5,0,5,1)
print '\nIndices of the elements == 2:', s.whereEqual(0,5,0,5,2)


# ... and there is even more:
print '\nAll ' + str(len(dir(s))) + ' methods:\n', dir(s)
