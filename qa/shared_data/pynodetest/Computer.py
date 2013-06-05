#
# This script should be loaded in PyNode::initScript().setFromFile("...")
# Also, PyNode::computeScript().setFunction("computer.compute")
#
# This init script, with the compute function
# Implement a reference node.
#

#
# Import is necessary to bring the names into this space.
#
import pdb
#import warnings
import numpy
from numpy.core import array
from nupic.foundation import LogInfo
import inspect
import sys
import linecache

def traceeveryline(frame, event, arg):
  if event == "line":
#    print dir(frame)
#    print dir(event)
#    print dir(arg)
    lineno = frame.f_lineno
    filename = "unknown"
    name = "unknown"
    try:
      filename = frame.f_globals["__file__"]
      name = frame.f_globals["__name__"]
    except:
      pass
    if(filename.endswith(".pyc") or filename.endswith(".pyo")):
      filename = filename[:-1]
    line = linecache.getline(filename, lineno).rstrip()
#    print "%s ... %s:%d: %s" % (name, filename, lineno, line)
    LogInfo(name, filename, lineno, line)
  return traceeveryline

#sys.settrace(traceeveryline)

def rdirichlet(alpha):
  n = len(alpha)
  g = array(0.0).repeat(n)
  for i in xrange(n):
    g[i] = numpy.random.gamma(alpha[i], 1.0)
  return g / numpy.sum(g)

#
# This class has no meaning to PyNode, its design is at the whims
# of its author.
# Note that __init__ is the class constructor, and will be called
# when this class is instantiated (see below).
#
class Computer:
  def __init__(self, inc):
#    pdb.set_trace()
    self.lastUsedNumpy = 1 # Start out toggling to slow call
    self.increment = inc
    self.seed = 37
    rstate = numpy.random.get_state() # Backup the generator state.
    numpy.random.seed(37) # Set the generator state.
    alpha = array([1.0, 2.0, 1.0, 5.0, 7.0, 9.0, 3.0, 1.0])
    self.x = rdirichlet(alpha / numpy.sum(alpha))
    numpy.random.set_state(rstate) # Restore the backup state.

  def test(self):
    if 5 < 7:
      print 'comparison good'
    if 7 > 5:
      print "comparison good"

  def fastCompute(self, inputs, outputs, allOutputs):
    vecs = []
    n = len(inputs)
    for i in inputs:
      a = i.array()
      a += self.increment
      vecs.append(a)
    all = numpy.concatenate(vecs)
    allOutputs[:] = all

  def slowCompute(self, inputs, outputs, allOutputs):
    if 1:
      updated = numpy.zeros(len(allOutputs))
      k = 0
      for i in inputs:
        for j in xrange(len(i)):
          doPrint = False
          if doPrint:
            print 'Printing ========================'
            print i
            print i[j]
            print self.increment
            print updated
            print updated[k]
            print 'Done ============================'
          updated[k] = i[j] + self.increment
          k+=1
      for i,j in zip(xrange(len(allOutputs)), updated):
        allOutputs[i] = j

  def compute(self, inputs, outputs, allOutputs):
# Toggle between numpy and naive versions
    if self.lastUsedNumpy:
      self.slowCompute(inputs, outputs, allOutputs)
      self.lastUsedNumpy = 0
    else:
      self.fastCompute(inputs, outputs, allOutputs)
      self.lastUsedNumpy = 1