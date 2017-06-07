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

"""
Module of statistical data structures and functions used in learning algorithms
and for analysis of HTM network inputs and outputs.
"""

import random

import numpy

from nupic.bindings.math import GetNTAReal, SparseMatrix


dtype = GetNTAReal()

def pickByDistribution(distribution, r=None):
  """
  Pick a value according to the provided distribution.

  Example:

  ::

    pickByDistribution([.2, .1])

  Returns 0 two thirds of the time and 1 one third of the time.

  :param distribution: Probability distribution. Need not be normalized.
  :param r: Instance of random.Random. Uses the system instance if one is
         not provided.
  """

  if r is None:
    r = random

  x = r.uniform(0, sum(distribution))
  for i, d in enumerate(distribution):
    if x <= d:
      return i
    x -= d



def Indicator(pos, size, dtype):
  """
  Returns an array of length size and type dtype that is everywhere 0,
  except in the index in pos.

  :param pos: (int) specifies the position of the one entry that will be set.
  :param size: (int) The total size of the array to be returned.
  :param dtype: The element type (compatible with NumPy array())
         of the array to be returned.
  :returns: (list) of length ``size`` and element type ``dtype``.
  """
  x = numpy.zeros(size, dtype=dtype)
  x[pos] = 1
  return x



def MultiArgMax(x):
  """
  Get tuple (actually a generator) of indices where the max value of
  array x occurs. Requires that x have a max() method, as x.max()
  (in the case of NumPy) is much faster than max(x).
  For a simpler, faster argmax when there is only a single maximum entry,
  or when knowing only the first index where the maximum occurs,
  call argmax() on a NumPy array.

  :param x: Any sequence that has a max() method.
  :returns: Generator with the indices where the max value occurs.
  """
  m = x.max()
  return (i for i, v in enumerate(x) if v == m)



def Any(sequence):
  """
  Tests much faster (30%) than bool(sum(bool(x) for x in sequence)).

  :returns: (bool) true if any element of the sequence satisfies True. 

  :param sequence: Any sequence whose elements can be evaluated as booleans.
  """
  return bool(reduce(lambda x, y: x or y, sequence, False))



def All(sequence):
  """
  :param sequence: Any sequence whose elements can be evaluated as booleans.
  :returns: true if all elements of the sequence satisfy True and x.
  """
  return bool(reduce(lambda x, y: x and y, sequence, True))



def Product(sequence):
  """
  Returns the product of the elements of the sequence.
  Use numpy.prod() if the sequence is an array, as it will be faster.
  Remember that the product of many numbers may rapidly overflow or
  underflow the numeric precision of the computer.
  Use a sum of the logs of the sequence elements instead when precision
  should be maintained.

  :param sequence: Any sequence whose elements can be multiplied by their
            neighbors.
  :returns: A single value that is the product of all the sequence elements.
  """
  return reduce(lambda x, y: x * y, sequence)



def MultiIndicator(pos, size, dtype):
  """
  Returns an array of length size and type dtype that is everywhere 0,
  except in the indices listed in sequence pos.

  :param pos:   A single integer or sequence of integers that specify
         the position of ones to be set.
  :param size:  The total size of the array to be returned.
  :param dtype: The element type (compatible with NumPy array())
         of the array to be returned.
  :returns: An array of length size and element type dtype.
  """
  x = numpy.zeros(size, dtype=dtype)
  if hasattr(pos, '__iter__'):
    for i in pos: x[i] = 1
  else: x[pos] = 1
  return x



def Distribution(pos, size, counts, dtype):
  """
  Returns an array of length size and type dtype that is everywhere 0,
  except in the indices listed in sequence pos.  The non-zero indices
  contain a normalized distribution based on the counts.


  :param pos:    A single integer or sequence of integers that specify
          the position of ones to be set.
  :param size:   The total size of the array to be returned.
  :param counts: The number of times we have observed each index.
  :param dtype:  The element type (compatible with NumPy array())
          of the array to be returned.
  :returns: An array of length size and element type dtype.
  """
  x = numpy.zeros(size, dtype=dtype)
  if hasattr(pos, '__iter__'):
    # calculate normalization constant
    total = 0
    for i in pos:
      total += counts[i]
    total = float(total)
    # set included positions to normalized probability
    for i in pos:
      x[i] = counts[i]/total
  # If we don't have a set of positions, assume there's only one position
  else: x[pos] = 1
  return x


class ConditionalProbabilityTable2D(object):
  """
  Holds frequencies in a 2D grid of bins.
  Binning is not performed automatically by this class.
  Bin updates must be done one row at a time.
  Based on nupic::SparseMatrix which is a compressed sparse row matrix.
  Number of columns cannot be changed once set.
  Number of rows may be increased.
  Also maintains the row and column sumProp distributions.
  
  Constructor constructs a new empty histogram with no rows or columns. 
  
  :param rowHint: if specified, ncols must be specified (though not vice versa)
  :param ncols: if speicified, number of columns cannot be changed thereafter.
  """
  def __init__(self, rowHint=None, ncols=None):
    self.hist_ = None
    self.rowSums_ = None
    self.colSums_ = None
    if ncols:
      if not rowHint: rowHint = 1
      assert dtype
      self.grow(rowHint, ncols)
    else: assert not rowHint
    self.hack_ = None

  def numRows(self):
    """Gets the number of rows in the histogram.
    
    :returns: Integer number of rows.
    """
    if self.hist_: return self.hist_.nRows()
    else: return 0

  def numColumns(self):
    """
    :return: (int) number of columns 
    """
    if self.hist_: return self.hist_.nCols()
    else: return 0

  def grow(self, rows, cols):
    """
    Grows the histogram to have rows rows and cols columns.
    Must not have been initialized before, or already have the same
    number of columns.
    If rows is smaller than the current number of rows,
    does not shrink.
    Also updates the sizes of the row and column sums.

    :param rows: Integer number of rows.
    :param cols: Integer number of columns.
    """
    if not self.hist_:
      self.hist_ = SparseMatrix(rows, cols)
      self.rowSums_ = numpy.zeros(rows, dtype=dtype)
      self.colSums_ = numpy.zeros(cols, dtype=dtype)
      self.hack_ = None
    else:
      oldRows = self.hist_.nRows()
      oldCols = self.hist_.nCols()
      nextRows = max(oldRows, rows)
      nextCols = max(oldCols, cols)
      if (oldRows < nextRows) or (oldCols < nextCols):
        self.hist_.resize(nextRows, nextCols)
        if oldRows < nextRows:
          oldSums = self.rowSums_
          self.rowSums_ = numpy.zeros(nextRows, dtype=dtype)
          self.rowSums_[0:len(oldSums)] = oldSums
          self.hack_ = None
        if oldCols < nextCols:
          oldSums = self.colSums_
          self.colSums_ = numpy.zeros(nextCols, dtype=dtype)
          self.colSums_[0:len(oldSums)] = oldSums
          self.hack_ = None

  def updateRow(self, row, distribution):
    """
    Add distribution to row row.
    Distribution should be an array of probabilities or counts.

    :param row:   Integer index of the row to add to.
                  May be larger than the current number of rows, in which case
                  the histogram grows.
    :param distribution: Array of length equal to the number of columns.
    """
    self.grow(row+1, len(distribution))
    self.hist_.axby(row, 1, 1, distribution)
    self.rowSums_[row] += distribution.sum()
    self.colSums_ += distribution
    self.hack_ = None # Clear out the cached inference.

  def inferRow(self, distribution):
    """
    Computes the sumProp probability of each row given the input probability
    of each column. Normalizes the distribution in each column on the fly.

    The semantics are as follows: If the distribution is P(col|e) where e is
    the evidence is col is the column, and the CPD represents P(row|col), then
    this calculates sum(P(col|e) P(row|col)) = P(row|e).

    :param distribution: Array of length equal to the number of columns.
    :returns: array of length equal to the number of rows.
    """
    # normalize over colSums_ because P(row|col) = P(col,row)/P(col)
    return self.hist_ * (distribution / self.colSums_)

  def inferRowEvidence(self, distribution):
    """
    Computes the probability of evidence given each row from the probability
    of evidence given each column.  Essentially, this just means that it sums
    probabilities over (normalized) rows.  Normalizes the distribution over
    each row on the fly.

    The semantics are as follows:  If the distribution is P(e|col) where e is
    evidence and col is the column, and the CPD is of P(col|row), then this
    calculates sum(P(e|col) P(col|row)) = P(e|row).

    :param distribution: Array of length equal to the number of columns.
    :returns: array of length equal to the number of rows.
    """
    # normalize over rowSums_ because P(col|row) = P(col,row)/P(row).
    return (self.hist_ * distribution) / self.rowSums_

  def inferRowMaxProd(self, distribution):
    return self.hist_.vecMaxProd(distribution)

  def inferRowCompat(self, distribution):
    """
    Equivalent to the category inference of zeta1.TopLevel.
    Computes the max_prod (maximum component of a component-wise multiply)
    between the rows of the histogram and the incoming distribution.
    May be slow if the result of clean_outcpd() is not valid.

    :param distribution: Array of length equal to the number of columns.
    :returns: array of length equal to the number of rows.
    """
    if self.hack_ is None:
      self.clean_outcpd()
    return self.hack_.vecMaxProd(distribution)

  def clean_outcpd(self):
    """Hack to act like clean_outcpd on zeta1.TopLevelNode.
    Take the max element in each to column, set it to 1, and set all the
    other elements to 0.
    Only called by inferRowMaxProd() and only needed if an updateRow()
    has been called since the last clean_outcpd().
    """
    m = self.hist_.toDense()
    for j in xrange(m.shape[1]): # For each column.
      cmax = m[:,j].max()
      if cmax:
        m[:,j] = numpy.array(m[:,j] == cmax, dtype=dtype)
    self.hack_ = SparseMatrix(0, self.hist_.nCols())
    for i in xrange(m.shape[0]):
      self.hack_.addRow(m[i,:])

def ShannonEntropy(x):
  x = numpy.asarray(x, dtype=float)
  s = x.sum()
  if s: p = x / s
  else: p = x
  assert (p >= 0).all()
  p = p[p != 0] # Get rid of 0s.
  return - numpy.dot(p, numpy.log(p))

def ShannonEntropyLog(lx):
  lx = numpy.asarray(lx)
  lx = lx - lx.max()
  x = numpy.exp(lx)
  s = x.sum()
  return - ( ( numpy.dot(x, lx) / s ) - numpy.log(s) )

def DifferentialEntropy(mass, areas=1.0):
  x = numpy.asarray(mass, dtype=float)
  p = x / x.sum()
  return -numpy.dot(p, numpy.log(p)) + numpy.dot(p, numpy.log(areas))


#----------------------------------------
#Fuzzy k-means

def fuzzyKmeans(samples,fixCenter=None,iter=5,fuzzParam=1.5):

    #Not actually k means yet just 3 means

    if fixCenter is not None:
       dMeans = [min(samples)+0.01 , fixCenter ,max(samples)-0.01]
    else:
       dMeans = [min(samples)+0.01 , mean(samples) ,max(samples)-0.01]
    begDeg = map(None,numpy.zeros(len(samples)))
    midDeg = map(None,numpy.zeros(len(samples)))
    endDeg = map(None,numpy.zeros(len(samples)))

    for j in range(iter):
       for k in range(len(samples)):
          pBeg = (1.0/(samples[k] - dMeans[2])**2)**(1.0/(fuzzParam-1))
          pMid = (1.0/(samples[k] - dMeans[1])**2)**(1.0/(fuzzParam-1))
          pEnd = (1.0/(samples[k] - dMeans[0])**2)**(1.0/(fuzzParam-1))
          nmlz = pBeg + pMid + pEnd
          begDeg[k] = pBeg/nmlz; midDeg[k] = pMid/nmlz; endDeg[k] = pEnd/nmlz
       #Update means 0 and 2, the other should stay at zero! (Change this for general purpose k-means)
       dMeans[0] = numpy.nansum((numpy.array(endDeg)**fuzzParam)*numpy.array(samples))/numpy.nansum(numpy.array(endDeg)**fuzzParam)
       if fixCenter is None:
          dMeans[1] = numpy.nansum((numpy.array(midDeg)**fuzzParam)*numpy.array(samples))/numpy.nansum(numpy.array(midDeg)**fuzzParam)
       dMeans[2] = numpy.nansum((numpy.array(begDeg)**fuzzParam)*numpy.array(samples))/numpy.nansum(numpy.array(begDeg)**fuzzParam)

    return dMeans
