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

raise Exception("XERROR -- removing for NuPIC 2")


import numpy
from numpy.linalg import svd

log2pi = numpy.log(2.0 * numpy.pi)

def cov(data, mean=None, prior=None, dfOffset=-1):
  x = numpy.asmatrix(data)
  if mean is None: mean = x.mean()
  xc = x - mean
  xxt = xc.T * xc
  n = x.shape[0]
  if prior is not None:
    assert len(prior) == 2, "Must be of the form (n, SS)"
    n += prior[0]
    print prior[1].shape
    xxt += prior[1]
  n += dfOffset
  assert n > 0
  return (1.0 / n) * xxt

def getRank(d, s):
  if numpy.min(s) > 0: return d
  else: return max(numpy.argmin(s > 0), 1)

class mvn(object):
  def __init__(self, mean, varcov):
    if mean is not None: self.mean = numpy.asarray(mean)
    else: self.mean = None
    varcov = numpy.asmatrix(varcov)
    self.d = varcov.shape[1]
    self.varcov = varcov
    self.u, self.s, self.vt = svd(varcov, full_matrices=0, compute_uv=1)
    self.rank = getRank(self.d, self.s)

  def __str__(self):
    return "Mean:\n" + str(self.mean) + "\nCovariance:\n" + str(self.varcov)

  def __repr__(self):
    return "Mean:\n" + repr(self.mean) + "\nCovariance:\n" + repr(self.varcov)

  def limitRank(self, minvar):
    if numpy.min(self.s) > minvar: self.rank = self.d
    else:
      self.rank = max(numpy.argmin(self.s > minvar), 1)

  def setRank(self, rank):
    assert rank <= self.d
    assert rank >= 1
    self.rank = rank

  def s0(self):
    s = numpy.zeros(len(self.s))
    s[0:self.rank] = self.s[0:self.rank]
    s[self.rank:] = 0
    return s

  def si(self):
    si = numpy.zeros(len(self.s))
    si[0:self.rank] = 1.0 / self.s[0:self.rank]
    si[self.rank:] = 0
    return si

  def sigma(self):
    return self.u * numpy.asmatrix(numpy.diag(self.s0())) * self.vt

  def sigmai(self):
    # return self.vt.T * numpy.asmatrix(numpy.diag(self.si())) * self.u.T
    return self.u * numpy.asmatrix(numpy.diag(self.si())) * self.vt

  def rightRoot(self):
    return numpy.asmatrix(numpy.diag(numpy.sqrt(self.s0()))) * self.vt

  def leftRoot(self):
    return self.u * numpy.asmatrix(numpy.diag(numpy.sqrt(self.s0())))

  def leftInvRoot(self):
    # return self.vt.T * numpy.asmatrix(numpy.diag(numpy.sqrt(self.si())))
    return self.u * numpy.asmatrix(numpy.diag(numpy.sqrt(self.si())))

  def rightInvRoot(self):
    # return numpy.asmatrix(numpy.diag(numpy.sqrt(self.si()))) * self.u.T
    return numpy.asmatrix(numpy.diag(numpy.sqrt(self.si()))) * self.vt

  def sample(self, r=None, n=1):
    if r is None: r = numpy.random
    z = r.normal(0, 1, (n, self.d))
    return z * self.rightRoot() + self.mean

  def center(self, x):
    x = numpy.asmatrix(x)
    assert x.shape[1] == self.d
    if self.mean is not None: return (x - self.mean)
    else: return x

  def whiten(self, x):
    xc = self.center(x)
    # Whiten.
    z = xc * self.leftInvRoot()
    return z

  def z2(self, x):
    z = self.whiten(x)
    # Avoid matrix multiplication, just square the rows.
    z = numpy.asarray(z)
    z2 = z * z
    return numpy.sum(z2, axis=1)

  def logDetSigma(self):
    return numpy.sum(numpy.log(self.s[0:self.rank]))

  def logDetInvRoot(self):
    return -0.5 * self.logDetSigma()

  def logK(self):
    return -0.5 * self.rank * log2pi

  def logLikelihood(self, x):
    z = numpy.asarray(self.whiten(x))
    # z2 = numpy.sum(z * z, axis=1)
    n = len(z)
    return -0.5 * ( n*(self.rank * log2pi + self.logDetSigma()) + numpy.sum(z*z) )

  def logLikelihoods(self, x):
    z2 = self.z2(x)
    return self.logK() + self.logDetInvRoot() - 0.5 * z2

  def logDensity(self, x):
    return self.logLikelihood(x)

class MaskBuilder(object):
  def __init__(self, d):
    self.indices = numpy.arange(d)

  def __getitem__(self, *args):
    return bits

class ConditionalMVN(object):
  def __init__(self, mvn):
    self.mvn = mvn

  class Impl(object):
    def __init__(self, mean1, mean2, Sigma11, Sigma12, Sigma22):
      Sigma11 = numpy.asmatrix(Sigma11)
      Sigma12 = numpy.asmatrix(Sigma12)
      Sigma22 = numpy.asmatrix(Sigma22)
      u22, s22, vt22 = svd(Sigma22, full_matrices=0, compute_uv=1)

      rank22 = getRank(Sigma22.shape[1], s22)
      s22i = numpy.zeros(len(s22))
      s22i[0:rank22] = 1.0 / s22[0:rank22]
      # Rest are zeroes.
      Sigma22i = u22 * numpy.asmatrix(numpy.diag(s22i)) * vt22

      self.mean1 = mean1
      self.mean2 = mean2
      self.Sigma11 = Sigma11
      self.Sigma12 = Sigma12
      self.Sigma22i = Sigma22i

    def getDistribution(self, given):
      given_from_mean = given - self.mean2

      # Keep means in row form.
      # mean = self.mean1 + self.Sigma12 * self.Sigma22i * given_from_mean
      mean = self.mean1 + given_from_mean * self.Sigma22i * self.Sigma12.transpose()
      varcov = self.Sigma11 - (self.Sigma12 * self.Sigma22i * (self.Sigma12.transpose()))

      return mvn(mean, varcov)

    def logDensity(self, x, given):
      return getDistribution(given).logDensity(x)

  def __getitem__(self, *args):
    d = self.mvn.d
    indices = numpy.arange(d).__getitem__(*args)
    bits = numpy.repeat(False, d)
    bits[indices] = True
    givenMask = bits # Should it be this way, or the other way around?
    varMask = ~givenMask
    C22 = self.mvn.varcov[givenMask, ...][..., givenMask]
    C12 = self.mvn.varcov[varMask, ...][..., givenMask]
    C11 = self.mvn.varcov[varMask, ...][..., varMask]
    return ConditionalMVN.Impl(self.mvn.mean[varMask], self.mvn.mean[givenMask],
      C11, C12, C22)
