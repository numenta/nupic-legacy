# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
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

raise Exception("XERROR mcmc not available")


import copy
import time
import numpy
from nupic.support.pythonics import Accessor
from nupic.bindings.math import CMultiArgMax, GetNumpyDataType
realDType = GetNumpyDataType("NTA_Real")

class MCMCState(object):
  def __init__(self, values, logPrior, logLikelihood, postTime, **keywds):
    self.values = values
    self.logPrior = logPrior
    self.logLikelihood = logLikelihood
    self.info = keywds
    self.time = postTime

  def __str__(self):
    return ("<state logPrior='%f' logLikelihood='%f'>" %
      (self.logPrior, self.logLikelihood)) + str(self.values) + "</state>"
  def __repr__(self):
    return ("<state logPrior='%f' logLikelihood='%f'>" %
      (self.logPrior, self.logLikelihood)) + repr(self.values) + "</state>"

class MCMCSample(object):
  def __init__(self, previous, proposal, logForward, logBackward, alpha, ra, current):
    self.previous = previous
    self.proposal = proposal
    self.logForward = logForward
    self.logBackward = logBackward
    self.alpha = alpha
    self.ra = ra
    self.current = current
  def __str__(self):
    return ("<sample accepted='%s'>" % (self.ra < self.alpha)) + \
      str(self.current) + "</sample>"
  def __repr__(self):
    return ("<sample accepted='%s'>" % (self.ra < self.alpha)) + \
      repr(self.current) + "</sample>"

class ProposalAccessor(Accessor):
  def __init__(self, key, dist):
    Accessor.__init__(self, key)
    self.dist = dist

class MHSampler(object):
  def __init__(self, logPosteriorFunc, lpArgs=None, lpKeywds=None,
      seed=0x7654321):

    self.logPosteriorFunc = logPosteriorFunc
    if lpArgs is None: self.lpArgs = []
    else: self.lpArgs = lpArgs
    if lpKeywds is None: self.lpKeywds = {}
    else: self.lpKeywds = lpKeywds

    self.rgen = numpy.random.RandomState(seed)

    self.catchInterrupt = False
    self.proposals = {}

    self.samples = []

    self.nRejected = 0
    self.burnin = None

  def __getstate__(self):
    return {"version": (1, 0),
        "rgen": self.rgen,
        "catchInterrupt": self.catchInterrupt,
        "samples": self.samples,
        "nRejected": self.nRejected,
        "burnin": self.burnin,
      }

  def __setstate__(self, state):
    assert state["version"] == (1, 0)
    self.rgen = state["rgen"]
    self.catchInterrupt = state["catchInterrupt"]
    self.samples = state["samples"]
    self.nRejected = state["nRejected"]
    self.burnin = state["burnin"]

    # Must be set again after unpickling.
    self.logPosteriorFunc = None
    self.lpArgs = []
    self.lpKeywds = {}

  def setProposal(self, key, dist):
    accessor = ProposalAccessor(key, dist)
    self.proposals[key] = accessor

  def propose(self, currentValues):
    logForwardSum = 0
    logBackwardSum = 0
    proposed = copy.deepcopy(currentValues)
    changes = {}
    for key, accessor in self.proposals.iteritems():
      currentValue = accessor.getValue(proposed)
      newValue, logForward, logBackward = \
        accessor.dist.propose(currentValue, self.rgen)
      if currentValue != newValue:
        changes[key] = (currentValue, newValue)
      accessor.setValue(proposed, newValue)
      # print base, key, logForward, logBackward
      logForwardSum += logForward
      logBackwardSum += logBackward
    return proposed, logForwardSum, logBackwardSum, changes

  def getCurrentValues(self):
    if self.samples: return self.samples[-1].current.values
    else: raise RuntimeError("No current values.")

  def getAcceptanceStats(self):
    # Skip burn-in.
    samples = self.getSamples()
    nSampled = len(samples)
    nAccepted = sum(1 for sample in samples if sample.ra < sample.alpha)
    return nAccepted, nSampled

  def getBurnin(self):
    if self.burnin is not None: return self.burnin
    else: return len(self.samples) / 2

  def getSamples(self):
    return self.samples[self.getBurnin():]

  def _getMaximumLikelihoodSamples(self):
    indices = CMultiArgMax(numpy.array(
      [sample.proposal.logLikelihood for sample in self.samples], dtype=realDType))
    return indices

  def getMaximumLikelihoods(self):
    return [self.samples[i].proposal for i in self._getMaximumLikelihoodSamples()]

  def _getMAPSamples(self):
    indices = CMultiArgMax(numpy.array(
        [(sample.proposal.logLikelihood + sample.proposal.logPrior)
          for sample in self.samples],
        dtype=realDType
      ))
    return indices

  def getMAPs(self):
    return [self.samples[i].proposal for i in self._getMAPSamples()]

  def getParameterNames(self):
    fields = set()
    for key in self.proposals.keys():
      if hasattr(key, "__iter__"): fields.update(key)
      else: fields.add(key)
    return sorted(fields)

  def _getTableFields(self, params=None, info=None, remainder=None):
    if remainder is None:
      remainder = ["log prior", "log likelihood",
        "log posterior", "compute time", "accepted", "forward", "backward"]
    # ma = len(remainder)

    if params is None:
      params = self.getParameterNames()
    else:
      params = list(params) # Shallow copy.
      # if params[-ma:] == remainder: params = params[:-ma]

    if info is None:
      if self.samples:
        info = set()
        for sample in self.samples:
          info.update(key for key in sample.current.info.iterkeys()
            if not key.startswith("_"))
        info = sorted(info)
      else:
        info = []

    return params, info, remainder

  def _convertStatesToTable(self, states, accepted=None, params=None, info=None):
    params, info, remainder = self._getTableFields(params=params, info=info)
    n = len(states)
    m0 = len(params)
    m1 = len(info)
    m2 = len(remainder)
    rows = numpy.ndarray((n, (m0 + m1 + m2)), dtype=object)

    for i, state in enumerate(states):
      offset = 0
      for param in params:
        rows[i, offset] = self.proposals[param].getValue(state.values)
        offset += 1
      for key in info:
        rows[i, offset] = state.info[key]
        offset += 1
      rows[i, offset] = state.logPrior
      offset += 1
      rows[i, offset] = state.logLikelihood
      offset += 1
      rows[i, offset] = state.logPrior + state.logLikelihood
      offset += 1
      rows[i, offset] = state.time
      offset += 1
      if accepted is not None:
        rows[i, offset] = accepted[i][0]
        offset += 1
        rows[i, offset] = accepted[i][1]
        offset += 1
        rows[i, offset] = accepted[i][2]
        offset += 1
      else:
        rows[i, offset] = ""
        offset += 1
        rows[i, offset] = ""
        offset += 1
        rows[i, offset] = ""
        offset += 1

    return (params + info + remainder), rows


  def getSampleTable(self):
    return self._convertStatesToTable(
      [sample.current for sample in self.getSamples()])

  def getProposalTable(self):
    return self._convertStatesToTable(
      [sample.proposal for sample in self.getSamples()])

  def getMaximumLikelihoodTable(self):
    return self._convertStatesToTable(self.getMaximumLikelihoods())

  def getMAPTable(self):
    return self._convertStatesToTable(self.getMAPs())

  def _writeHeader(self, output, fields):
    print >>output, ",".join(("\"%s\"" % field) for field in fields)
    output.flush()

  def _writeRows(self, output, table):
    # header = table[0]
    body = table[1]
    n = len(body)
    for i in xrange(n):
      print >>output, ",".join(("\"%s\"" % field) for field in body[i])
    output.flush()

  def run(self, n, initialParams=None, printIterations=True,
      output=None, outputInfo=None, proposalOutput=None):

    startTime = time.time()

    if initialParams is None: # Continue.
      if not self.samples: raise RuntimeError("No chain to continue.")
      current = self.samples[-1].current
      # Don't store the sample again.
      # Don't write a header on the sample file.
      # Don't output the sample to the sample file.
      outputParams, outputInfo, outputRemainder = \
        self._getTableFields(info=outputInfo)

    else: # Start from the initial values.
      postStart = time.time()
      validated, initialLogPrior, initialLogLikelihood, initialInfo = \
        self.logPosteriorFunc(initialParams, *self.lpArgs, **self.lpKeywds)
      postTime = time.time() - postStart

      if not validated:
        raise RuntimeError("Initial configuration was not valid.")

      current = MCMCState(initialParams, initialLogPrior, initialLogLikelihood,
        postTime, **initialInfo)

      self.samples.append(MCMCSample(current, current, 0.0, 0.0, 1.0, 0.0, current))

      outputParams, outputInfo, outputRemainder = \
        self._getTableFields(info=outputInfo)

      if output is not None:
        self._writeHeader(output, outputParams + outputInfo + outputRemainder)
        self._writeRows(output, self._convertStatesToTable([current],
          params=outputParams, info=outputInfo))

      if proposalOutput is not None:
        self._writeHeader(proposalOutput,
          outputParams + outputInfo + outputRemainder)
        self._writeRows(proposalOutput, self._convertStatesToTable([current],
          params=outputParams, info=outputInfo))

    nAccepted = 0

    for i in xrange(1, n):
      try: # Allow a graceful keyboard interrupt.

        if printIterations:
          print "========================="
          print "Iteration", i
          print "========================="


        while True:
          proposed, logForwardSum, logBackwardSum, changes = \
            self.propose(current.values)

          if printIterations:
            print "----------------------------------------------------------------------------------"
            print "Changes:"
            for changedKey in sorted(changes):
              value = changes[changedKey]
              print changedKey, ":", value[0], "->", value[1]
            print "----------------------------------------------------------------------------------"

          postStart = time.time()
          validated, logPrior, logLikelihood, info = \
            self.logPosteriorFunc(proposed, *self.lpArgs, **self.lpKeywds)
          postTime = time.time() - postStart

          if validated: break
          # Log invalid samples?
          else: self.nRejected += 1

        logPosterior = logPrior + logLikelihood

        # print info
        # print "Accuracy:", info["trainingAccuracy"], info["testAccuracy"], logPosterior

        curPosterior = current.logPrior + current.logLikelihood

        logPosteriorRatio = logPosterior - curPosterior
        logProposalRatio = logForwardSum - logBackwardSum

        alpha = numpy.exp(min(0.0, logPosteriorRatio - logProposalRatio))

        ra = self.rgen.uniform()
        accepted = (ra < alpha)

        if printIterations:
          print "----------------------------------------------------------------------------------"
          print "Changes:"
          for changedKey in sorted(changes):
            value = changes[changedKey]
            print changedKey, ":", value[0], "->", value[1]

          # print logPosterior, current.logPosterior, logBackwardSum, logForwardSum, \
          #   logPosteriorRatio, logProposalRatio, logPosteriorRatio - logProposalRatio, \
          #   alpha

          print "----------------------------------------------------------------------------------"
          print "Accept   Draw  Prob      PLP      CLP       LB       LF  Accepted  Proposed   Rate"
          print "----------------------------------------------------------------------------------"
          print "     %d  %.3f %.3f % 8.2f % 8.2f % 8.2f % 8.2f  %8d  %8d  %.3f" % \
            (accepted, ra, alpha,
              logPosterior, curPosterior, logBackwardSum, logForwardSum,
              (nAccepted+accepted), (i+1),
              float(nAccepted+accepted) / (i+1)
            )

        previous = current
        proposal = MCMCState(proposed, logPrior, logLikelihood,
          postTime, **info)

        if accepted:
          current = proposal
          nAccepted += 1

        # Adapt all of the proposal distributions, if they are adaptive.
        for propDist in self.proposals.itervalues():
          propDist.dist.adapt(accepted)


        self.samples.append(MCMCSample(previous, proposal,
          logForwardSum, logBackwardSum, alpha, ra, current))


        if output is not None:
          self._writeRows(output, self._convertStatesToTable([current],
              accepted=[(accepted, logForwardSum, logBackwardSum)],
              params=outputParams, info=outputInfo
            ))

        if proposalOutput is not None:
          self._writeRows(proposalOutput, self._convertStatesToTable([proposal],
              accepted=[(accepted, logForwardSum, logBackwardSum)],
              params=outputParams, info=outputInfo
            ))


      except KeyboardInterrupt:
        if self.catchInterrupt: break
        else: raise # Re-raise.

    endTime = time.time()

    print "% .2fs elapsed" % (endTime - startTime)

def combine(samplers):
  # # Save the maximum likelihood.
  # ml = numpy.inf
  # mls = []
  # for sampler in samplers:
  #   samples = sampler._getMaximumLikelihoodSamples()
  #   firstSample = sampler.samples[samples[0]]
  #   ll = firstSample.proposal.logLikelihood
  #   if ll < ml:
  #     ml = ll
  #     mls = [sampler.samples[i] for i in samples]
  #   elif ll == ml:
  #     mls.extend([sampler.samples[i] for i in samples])

  # # Save the MAP.
  # ml = numpy.inf
  # maps = []
  # for sampler in samplers:
  #   samples = sampler._getMAPSamples()
  #   firstSample = sampler.samples[samples[0]]
  #   ll = firstSample.proposal.logLikelihood + firstSample.proposal.logPrior
  #   if ll < ml:
  #     ml = ll
  #     maps = [sampler.samples[i] for i in samples]
  #   elif ll == ml:
  #     maps.extend([sampler.samples[i] for i in samples])

  out = copy.copy(samplers[0]) # Shallow copy.
  bi = samplers[0].getBurnin()
  out.samples = samplers[0].samples[:bi]
  out.burnin = bi
  for sampler in samplers[1:]:
    bi = sampler.getBurnin()
    out.samples.extend(sampler.samples[:bi])
    out.burnin += bi

  for sampler in samplers:
    out.samples.extend(sampler.getSamples())

  # # Re-insert the maximum likelihood and MAP samples,
  # # but mark them as burn-in.
  # for i in maps: out.samples.insert(0, i)
  # for i in mls: out.samples.insert(0, i)
  # out.burnin = len(mls) + len(maps)

  # Will start from the last sample of the last chain.
  return out
