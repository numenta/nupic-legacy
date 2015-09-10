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

raise Exception("XERROR proposal not available")

from nupic.math.dist import *


class Proposal(object):
  # Must support the following methods:
  # sample, logForward, logBackward = propose(currentValue, randomNumberGenerator)
  # None = adapt(accepted)
  def adapt(self, accepted):
    pass

class RangeWrapper(Proposal):
  def __init__(self, prop, min=None, max=None, offset=0, maxIterations=1000):
    self.prop = prop
    self.offset = offset
    self.min = min
    self.max = max
    self.maxIterations = 1000
  def propose(self, inCurrent, r):
    iterations = 0
    maxIterations = 10
    done = False
    prop = None
    value = None
    while not done:
      if self.offset is not None: current = inCurrent - self.offset
      else: current = inCurrent
      prop = self.prop.propose(current, r)
      value = prop[0]
      if self.offset is not None: value = value + self.offset
      done = True
      if (self.min is not None) and (value < self.min): done = False
      if (self.max is not None) and (value > self.max): done = False
      if iterations >= self.maxIterations:
        raise RuntimeError("Failed to sample in %d iterations." % self.maxIterations)
    prop = tuple([value] + list(prop[1:]))
    return prop

def toOdds(p): return p / (1.0 - p)
def toProbability(o): return o / (1.0 + o)
def logit(p): return numpy.log(p / (1.0 - p))
def invlogit(lo):
  o = numpy.exp(lo)
  return o / (1.0 + o)

def estimateProportion(x, n, prior=0.5):
  prop = (x + prior) / (n + 2.0 * prior)
  return prop

class CircularQueue(object):
  def __init__(self, n):
    self.queue = [None] * n
    self.max = n
    self.n = 0
  def add(self, x):
    self.queue[self.n % self.max] = x
    self.n += 1
  def clear(self):
    self.n = 0
  def getEarliest(self):
    if self.n > self.max: return self.queue[(self.n+1) % self.max]
    else:
      assert self.n
      return self.queue[0]

class MovingAverage(CircularQueue):
  def __init__(self, n, prior=None):
    CircularQueue.__init__(self, n)
    if prior is not None:
      self.pn = prior
      self.pd = 1.0
    else:
      self.pn = 0.0
      self.pd = 0.0
    self.sum = 0.0
  def add(self, x):
    rem = 0
    if self.n >= self.max: rem = self.queue[(self.n+1) % self.max]
    CircularQueue.add(self, x)
    self.sum += (x - rem)
  def clear(self):
    self.sum = 0
    CircularQueue.clear(self)
  def get(self):
    return (self.sum + self.pn) / (min(self.n, self.max) + self.pd)
  def getSum(self):
    return (self.sum + self.pn), (min(self.n, self.max) + self.pd)


class TransitionKernel(Proposal):
  def __init__(self, proposal, kernel, adaptiveWindow=None, target=0.5):
    self.prop = proposal
    if hasattr(kernel, "__iter__"):
      assert len(kernel) in [2, 3]
      if len(kernel) == 2:
        self.minKernel, self.maxKernel = kernel
        self.kernel = (kernel[0] + kernel[1]) / 2.0
      elif len(kernel) == 3:
        self.minKernel, self.kernel, self.maxKernel = kernel
      else:
        raise RuntimeError("Specify kernel as 1 number, a range, or a 3-tuple "
          "with (min, start, max)")
    else:
      self.kernel = kernel
      self.minKernel = min(0.01, kernel) # Assume a default bounds.
      self.maxKernel = max(0.99, kernel) # Assume a default bounds.

    self.target = target
    self.accepted = None
    if adaptiveWindow:
      self.accepted = MovingAverage(adaptiveWindow, prior=0.5)

  def propose(self, current, r):
    # Adapt if have sufficient data.
    willAdaptForward = False
    willAdaptBackward = False
    if self.accepted:
      minAdapt = self.accepted.max
      willAdaptForward = ((self.accepted.n+0) >= minAdapt)
      willAdaptBackward = ((self.accepted.n+1) >= minAdapt)

    kernelForward = self.kernel
    kernelBackward = kernelForward

    targetOdds = logit(self.target)
    if willAdaptForward:
      obsOdds = logit(self.accepted.get())
      weight = 0.1
      logOR = weight * (targetOdds - obsOdds)
      kernelForward = invlogit(logit(self.kernel) + logOR)
      kernelForward = max(self.minKernel, min(self.maxKernel, kernelForward))

    if willAdaptBackward:
      # Now consider the backward direction.
      a, b = self.accepted.getSum()
      if (self.accepted.n >= self.accepted.max):
        nextOdds = logit(estimateProportion(a + 1 - self.accepted.getEarliest(), b))
      else:
        nextOdds = logit(estimateProportion(a + 1, b + 1))
      nextWeight = 0.1
      nextLogOR = nextWeight * (targetOdds - nextOdds)
      kernelBackward = invlogit(logit(kernelForward) + nextLogOR)
      kernelBackward = max(self.minKernel, min(self.maxKernel, kernelBackward))

    if willAdaptForward or willAdaptBackward:
      if not "obsOdds" in locals():
        obsOdds = logit(self.accepted.get())
      print " Adapting:", obsOdds, "->", targetOdds
      print "  Adapted:", self.kernel, kernelForward, kernelBackward
      self.kernel = kernelForward

    # Perform the proposal.
    stay = (r.uniform(0, 1) < kernelForward)
    if stay:
      # print "stay"
      return (current, numpy.log(kernelForward), numpy.log(kernelBackward))
    else:
      # print "propose"
      while True: # Rejection sample to avoid the case of staying in one place.
        # Otherwise, our 'stay' probability will be wrong.
        proposed, logForward, logBackward = self.prop.propose(current, r)
        if proposed != current: break

      return (proposed, (logForward + numpy.log(1.0 - kernelForward)),
        (logBackward + numpy.log(1.0 - kernelBackward)))

  def adapt(self, accepted):
    if self.accepted: self.accepted.add(int(accepted))

class DiscreteProposal(Proposal):
  def __init__(self, keys, kernel):
    self.keys = [i for i in keys]
    self.keyMap = dict((key, i) for (i, key) in enumerate(self.keys))
    nKeys = len(keys)
    assert nKeys > 0
    self.nKeys = nKeys
    if nKeys == 1:
      kernel = 1.0
      self.logp = 0
    else:
      self.logp = -numpy.log(nKeys-1)
    assert (kernel >= 0) and (kernel <= 1.0)
    self.kernel = kernel

  def propose(self, current, r):
    """Generates a random sample from the discrete probability distribution and
    returns its value, the log of the probability of sampling that value and the
    log of the probability of sampling the current value (passed in).
    """
    stay = (r.uniform(0, 1) < self.kernel)
    if stay:
      logKernel = numpy.log(self.kernel)
      return current, logKernel, logKernel
    else: # Choose uniformly, not according to the pmf.
      curIndex = self.keyMap[current]
      ri = r.randint(0, self.nKeys-1)
      logKernel = numpy.log(1.0 - self.kernel)
      lp = logKernel + self.logp
      if ri < curIndex: return self.keys[ri], lp, lp
      else: return self.keys[ri+1], lp, lp

class TwoFishProposal(Proposal):
  def __init__(self, scale, minVal=-numpy.inf, maxVal=numpy.inf):
    self.dist = PoissonDistribution(scale)
    self.minVal = minVal
    self.maxVal = maxVal

  @staticmethod
  def proposePositive(dist, minVal, maxVal, r):
    if minVal > 0: raise RuntimeError("Current value is outside legal range.")
    elif maxVal < 0: raise RuntimeError("Current value is outside legal range.")
    cdf = dist.cdf(maxVal)
    while 1:
      diff, logProb = dist.sample(r)
      if diff <= maxVal: break
    rrange = diff - minVal
    rcdf = dist.cdf(rrange)
    rlp = dist.logProbability(diff)
    log2 = numpy.log(2) # The half chance we went up, rather than down.
    logForward = logProb - numpy.log(cdf) - log2
    logBackward = rlp - numpy.log(rcdf) - log2
    return diff, logForward, logBackward

  def propose(self, current, r):
    up = r.randint(2)
    if up:
      diff, logForward, logBackward = TwoFishProposal.proposePositive(
          self.dist, self.minVal - current, self.maxVal - current, r)
      return current + diff, logForward, logBackward
    else:
      diff, logForward, logBackward = TwoFishProposal.proposePositive(
          self.dist, current - self.maxVal, current - self.minVal, r)
      return current - diff, logForward, logBackward


class PoissonProposal(Proposal):
  def __init__(self, offset=0.1):
    self.offset = offset

  def propose(self, current, r):
    """Generates a random sample from the Poisson probability distribution with
    with location and scale parameter equal to the current value (passed in).
    Returns the value of the random sample, the log of the probability of
    sampling that value, and the log of the probability of sampling the current
    value if the roles of the new sample and the current sample were reversed
    (the log of the backward proposal probability).
    """
    curLambda = current + self.offset
    x, logProb = PoissonDistribution(curLambda).sample(r)
    logBackward = PoissonDistribution(x+self.offset).logDensity(current)
    return x, logProb, logBackward

class NormalProposal(Proposal):
  def __init__(self, sd):
    self.dist = NormalDistribution(0, sd)

  def propose(self, current, r):
    x, logProb = self.dist.sample(r)
    return x + current, logProb, logProb

class LogNormalProposal(Proposal):
  def __init__(self, normalSD):
    self.sd = normalSD

  def propose(self, current, r):
    dist = LogNormalDistribution(numpy.log(current), self.sd)
    x, logDensity = dist.sample(r)
    # Switch to new center, look at backward density.
    dist.setNormalMean(numpy.log(x))
    return x, logDensity, dist.logDensity(current)

class GammaProposal(Proposal):
  def __init__(self, shape, offset=0.001):
    self.shape = float(shape)
    self.offset = offset

  def propose(self, current, r):
    forwardScale = max((current + self.offset) / self.shape, 0)
    fdist = GammaDistribution(self.shape, forwardScale)
    x, logForward = fdist.sample(r)
    # backwardScale = max((x + self.offset) / self.shape, 0)
    backwardScale = (x + self.offset) / self.shape
    bdist = GammaDistribution(self.shape, backwardScale)
    return x, logForward, bdist.logDensity(current)
