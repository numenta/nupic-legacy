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

import numpy

def similar(a, b, eps=0.001):
  return (numpy.abs(a - b) < eps).all()


def lscsum(lx, epsilon=None):
  """
  Accepts log-values as input, exponentiates them, computes the sum,
  then converts the sum back to log-space and returns the result.
  Handles underflow by rescaling so that the largest values is exactly 1.0.
  """
  lx = numpy.asarray(lx)
  base = lx.max()

  # If the input is the log of 0's, catch this condition before we generate
  #  an exception, and return the log(0)
  if numpy.isinf(base):
    return base

  # If the user specified an epsilon and we are below it, return epsilon
  if (epsilon is not None) and (base < epsilon):
    return epsilon

  x = numpy.exp(lx - base)
  ssum = x.sum()

  result = numpy.log(ssum) + base
  # try:
  #   conventional = numpy.log(numpy.exp(lx).sum())
  #   if not similar(result, conventional):
  #     if numpy.isinf(conventional).any() and not numpy.isinf(result).any():
  #       # print "Scaled log sum avoided underflow or overflow."
  #       pass
  #     else:
  #       import sys
  #       print >>sys.stderr, "Warning: scaled log sum did not match."
  #       print >>sys.stderr, "Scaled log result:"
  #       print >>sys.stderr, result
  #       print >>sys.stderr, "Conventional result:"
  #       print >>sys.stderr, conventional
  # except FloatingPointError, e:
  #   # print "Scaled log sum avoided underflow or overflow."
  #   pass

  return result


def lscsum0(lx):
  """
  Accepts log-values as input, exponentiates them, sums down the rows
  (first dimension), then converts the sum back to log-space and returns the result.
  Handles underflow by rescaling so that the largest values is exactly 1.0.
  """
  # rows = lx.shape[0]
  # columns = numpy.prod(lx.shape[1:])
  # lx = lx.reshape(rows, columns)
  # bases = lx.max(1).reshape(rows, 1)
  # bases = lx.max(0).reshape((1,) + lx.shape[1:])
  lx = numpy.asarray(lx)
  bases = lx.max(0) # Don't need to reshape in the case of 0.
  x = numpy.exp(lx - bases)
  ssum = x.sum(0)

  result = numpy.log(ssum) + bases
  try:
    conventional = numpy.log(numpy.exp(lx).sum(0))

    if not similar(result, conventional):
      if numpy.isinf(conventional).any() and not numpy.isinf(result).any():
        # print "Scaled log sum down axis 0 avoided underflow or overflow."
        pass
      else:
        import sys
        print >>sys.stderr, "Warning: scaled log sum down axis 0 did not match."
        print >>sys.stderr, "Scaled log result:"
        print >>sys.stderr, result
        print >>sys.stderr, "Conventional result:"
        print >>sys.stderr, conventional
  except FloatingPointError, e:
    # print "Scaled log sum down axis 0 avoided underflow or overflow."
    pass


  return result


def normalize(lx):
  """
  Accepts log-values as input, exponentiates them,
  normalizes and returns the result.
  Handles underflow by rescaling so that the largest values is exactly 1.0.
  """
  lx = numpy.asarray(lx)
  base = lx.max()
  x = numpy.exp(lx - base)
  result = x / x.sum()

  conventional = (numpy.exp(lx) / numpy.exp(lx).sum())
  assert similar(result, conventional)

  return result


def nsum0(lx):
  """
  Accepts log-values as input, exponentiates them, sums down the rows
  (first dimension), normalizes and returns the result.
  Handles underflow by rescaling so that the largest values is exactly 1.0.
  """
  lx = numpy.asarray(lx)
  base = lx.max()
  x = numpy.exp(lx - base)
  ssum = x.sum(0)
  result = ssum / ssum.sum()

  conventional = (numpy.exp(lx).sum(0) / numpy.exp(lx).sum())
  assert similar(result, conventional)

  return result


def lnsum0(lx):
  """
  Accepts log-values as input, exponentiates them, sums down the rows
  (first dimension), normalizes, then converts the sum back to
  log-space and returns the result.
  Handles underflow by rescaling so that the largest values is exactly 1.0.
  """
  lx = numpy.asarray(lx)
  base = lx.max()
  x = numpy.exp(lx - base)
  ssum = x.sum(0)
  normalized = nsum0(lx)

  result = numpy.log(normalized)
  conventional = numpy.log(numpy.exp(lx).sum(0) / numpy.exp(lx).sum())
  assert similar(result, conventional)

  return result


def logSumExp(A, B, out=None):
  """ returns log(exp(A) + exp(B)). A and B are numpy arrays"""

  if out is None:
    out = numpy.zeros(A.shape)

  indicator1 = A >= B
  indicator2 = numpy.logical_not(indicator1)
  out[indicator1] = A[indicator1] + numpy.log1p(numpy.exp(B[indicator1]-A[indicator1]))
  out[indicator2]  = B[indicator2] + numpy.log1p(numpy.exp(A[indicator2]-B[indicator2]))

  return out

def logDiffExp(A, B, out=None):
  """ returns log(exp(A) - exp(B)). A and B are numpy arrays. values in A should be
  greater than or equal to corresponding values in B"""

  if out is None:
    out = numpy.zeros(A.shape)

  indicator1 = A >= B
  assert indicator1.all(), "Values in the first array should be greater than the values in the second"
  out[indicator1] = A[indicator1] + numpy.log(1 - numpy.exp(B[indicator1]-A[indicator1]))

  return out
