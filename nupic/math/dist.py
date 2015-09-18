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

raise Exception("XERROR dist not available")

import bisect

from nupic.math import lgamma, logChoose, choose, erf
import numpy

log2pi = numpy.log(2.0 * numpy.pi)

def logFactorial(x):
  """Approximation to the log of the factorial function."""
  return lgamma(x + 1.0)

class Distribution(object):
  pass

class Binomial(Distribution):
  def __init__(self, n, p):
    self.n = n
    self.p = p
  def logProbability(self, x):
    return logChoose(self.n, x) + x * numpy.log(self.p) + \
      (self.n - x) * numpy.log(1.0 - self.p)
  def probability(self, x):
    return choose(self.n, x) * (self.p ** x) * \
      (1.0 - self.p) ** (self.n - x)
  def sample(self, rgen):
    x = rgen.binomial(self.n, self.p)
    return x, self.logProbability(x)

class DiscreteDistribution(Distribution):
  def __init__(self, pmfIn, normalize=True):
    # Convert PMF to a CDF.
    # Use iteritems() repeatedly here (instead of iterkeys()) to
    # make sure the order is preserved.
    n = len(pmfIn)
    keyMap = dict((item[0], i) for i, item in enumerate(pmfIn.iteritems()))
    keys = [item[0] for item in pmfIn.iteritems()]
    pmf = numpy.array([item[1] for item in pmfIn.iteritems()], dtype=float)
    if normalize:
      pmf *= (1.0 / pmf.sum())
    # Is there a faster way to accumulate?
    cdf = pmf.copy()
    for i in xrange(1, n): cdf[i] += cdf[i-1]
    self.keys = keys
    self.keyMap = keyMap
    self.pmf = pmf
    self.cdf = cdf
    self.sum = self.cdf[-1]
    self.scale = 1.0 / self.sum

  def sample(self, rgen):
    """Generates a random sample from the discrete probability distribution
    and returns its value and the log of the probability of sampling that value.
    """
    rf = rgen.uniform(0, self.sum)
    index = bisect.bisect(self.cdf, rf)
    return self.keys[index], numpy.log(self.pmf[index])

  def probability(self, key):
    if key in self.keyMap: return self.pmf[self.keyMap[key]] * self.scale
    else: return 0

  density = probability

  def logDensity(self, key):
    if key in self.keyMap: return numpy.log(self.pmf[self.keyMap[key]] * self.scale)
    else: return -numpy.inf

class MultinomialDistribution(Distribution):
  def __init__(self, pmf):
    self.dist = DiscreteDistribution(pmf, normalize=True)

  def mean(self, n=1):
    return n * self.dist.pmf

  def var(self, n=1):
    return n * self.dist.pmf * (1.0 - self.dist.pmf)

  def cov(self, n=1):
    cov = - numpy.outer(self.dist.pmf, self.dist.pmf)
    diag = self.dist.pmf
    return n * (numpy.diag(diag) + cov)

  def logProbability(self, distn):
    """Form of distribution must be an array of counts in order of self.keys."""
    x = numpy.asarray(distn)
    n = x.sum()
    return (logFactorial(n) - numpy.sum([logFactorial(k) for k in x]) +
      numpy.sum(x * numpy.log(self.dist.pmf)))

  def probability(self, distn):
    return numpy.exp(self.logProbability(distn))

  def density(self, distn):
    return numpy.exp(self.logProbability(distn))

  def logDensity(self, distn):
    return self.logProbability(distn)

  def sample(self, rgen, n=1):
    return rgen.multinomial(n, self.dist.pmf)



class PoissonDistribution(Distribution):
  def __init__(self, lambdaParameter):
    self.lambdaParameter = lambdaParameter
    self.logLambda = numpy.log(self.lambdaParameter)

  def sample(self, rgen):
    """Generates a random sample from the Poisson probability distribution and
    returns its value and the log of the probability of sampling that value.
    """
    x = rgen.poisson(self.lambdaParameter)
    return x, self.logDensity(x)

  def probability(self, x):
    return numpy.exp( - self.lambdaParameter + self.logLambda * x - logFactorial(x) )

  def logProbability(self, x):
    return ( - self.lambdaParameter + self.logLambda * x - logFactorial(x) )

  def logDensity(self, x):
    return ( - self.lambdaParameter + self.logLambda * x - logFactorial(x) )

  def cdf(self, x):
    if x == numpy.inf: return 1.0
    else: # Inefficient sum.
      if x != int(x): raise RuntimeError("Invalid value.")
      c = 0.0
      for i in xrange(x+1):
        c += self.probability(i)
      return c

class NormalDistribution(Distribution):
  def __init__(self, mean, sd):
    self.mean = mean
    self.sd = sd
    self.var = sd * sd
    self.logVar = numpy.log(self.var)
    self.precision = 1.0 / self.var

  def density(self, x): return numpy.exp(self.logDensity(x))

  def logDensity(self, x):
    dx = x - self.mean
    return -0.5 * (log2pi + self.logVar + (dx*dx) * self.precision)

  def sample(self, rgen):
    x = rgen.normal(self.mean, self.sd)
    return x, self.logDensity(x)

  def cdf(self, x):
    return 0.5 * (1.0 + erf((x - self.mean) / (self.sd * numpy.sqrt(2.0))))

class LogNormalDistribution(Distribution):
  def __init__(self, normalMean, normalSD):
    self.mean = normalMean
    self.sd = normalSD
    self.var = normalSD * normalSD
    self.logVar = numpy.log(self.var)
    self.precision = 1.0 / self.var

  def setNormalMean(self, normalMean):
    self.mean = normalMean

  def logDensity(self, x):
    logx = numpy.log(x)
    dx = logx - self.mean
    return -0.5 * (log2pi + self.logVar + (dx*dx) * self.precision) - logx

  def sample(self, rgen):
    x = numpy.exp(rgen.normal(self.mean, self.sd))
    return x, self.logDensity(x)

class GammaDistribution(Distribution):
  def __init__(self, shape, scale=None, beta=None):
    self.alpha = shape
    if scale is not None:
      self.scale = scale
      self.beta = 1.0 / scale
      assert beta is None, "Specify exactly one of 'scale' or 'beta'."
    elif beta is not None:
      self.scale = 1.0 / beta
      self.beta = beta
    else:
      assert beta is None, "Specify exactly one of 'scale' or 'beta'."

    self.lgammaAlpha = lgamma(shape)
    self.logBeta = -numpy.log(scale)

  def logDensity(self, x):
    return ((self.alpha - 1.0) * numpy.log(x) + self.alpha * self.logBeta
              - self.beta * x - self.lgammaAlpha)

  def sample(self, rgen):
    x = rgen.gamma(self.alpha, self.scale)
    return x, self.logDensity(x)

def logBeta(alpha):
  alpha = numpy.asarray(alpha)
  return numpy.sum([lgamma(a) for a in alpha]) - lgamma(alpha.sum())

class DirichletDistribution(Distribution):
  def __init__(self, alpha):
    self.alpha = numpy.asarray(alpha).astype(float)
    self.alpha_1 = self.alpha - 1
    self.logZ = - logBeta(self.alpha)
    sum = self.alpha.sum()
    self.sum = sum

  def mean(self):
    return self.alpha / self.sum

  def var(self):
    alpha = self.alpha
    sum = self.sum
    k = sum * sum * (sum + 1)
    return alpha * (sum - alpha) / k

  def cov(self):
    cov = - numpy.outer(self.alpha, self.alpha)
    sum = self.sum
    k = sum * sum * (sum + 1)
    diag = self.alpha * self.sum
    return (numpy.diag(diag) + cov) / k

  def logDensity(self, x):
    logx = self.logZ + (self.alpha_1 * numpy.log(x)).sum()
    return logx

  def sample(self, rgen):
    y = rgen.gamma(self.alpha, 1.0, size=len(self.alpha))
    return y / y.sum()

class BetaDistribution(Distribution):
  def __init__(self, alpha, beta):
    self.distn = DirichletDistribution((alpha, beta))
  def mean(self):
    return self.distn.mean()[0]
  def var(self):
    return self.distn.var()[0]
  def logDensity(self, x):
    return self.distn.logDensity((x, 1.0 - x))
