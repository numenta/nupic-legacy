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



def importAndRunFunction(
    path,
    moduleName,
    funcName,
    **keywords
  ):
  """
  Run a named function specified by a filesystem path, module name
  and function name.

  Returns the value returned by the imported function.

  Use this when access is needed to code that has
  not been added to a package accessible from the ordinary Python
  path. Encapsulates the multiple lines usually needed to
  safely manipulate and restore the Python path.

  Parameters
  ----------
  path: filesystem path
  Path to the directory where the desired module is stored.
  This will be used to temporarily augment the Python path.

  moduleName: basestring
  Name of the module, without trailing extension, where the desired
  function is stored. This module should be in the directory specified
  with path.

  funcName: basestring
  Name of the function to import and call.

  keywords:
  Keyword arguments to be passed to the imported function.
  """
  import sys
  originalPath = sys.path
  try:
    augmentedPath = [path] + sys.path
    sys.path = augmentedPath
    func = getattr(__import__(moduleName, fromlist=[funcName]), funcName)
    sys.path = originalPath
  except:
    # Restore the original path in case of an exception.
    sys.path = originalPath
    raise
  return func(**keywords)



def getLockedHandle(runtimeElement, expression):
  """
  Calls runtimeElement.interpret(expression) and wraps the result
  in a call to nupic.bindings.research.lockHandle().
  """
  fullExpression = '__import__("nupic.bindings.research", ' \
      'fromlist=["lockHandle"]).lockHandle( ' + expression + ' )'
  return runtimeElement.interpret(fullExpression)



def transferCoincidences(network, fromElementName, toElementName):
  """
  Gets the coincidence matrix from one element and sets it on
  another element
  (using locked handles, a la nupic.bindings.research.lockHandle).

  TODO: Generalize to more node types, parameter name pairs, etc.

  Does not work across processes.
  """
  coincidenceHandle = getLockedHandle(
      runtimeElement=network.getElement(fromElementName),
      # TODO: Re-purpose for use with nodes other than PMXClassifierNode.
      expression="self._cd._W"
    )

  network.getElement(toElementName).setParameter("coincidencesAbove",
      coincidenceHandle)

  # print network.getElement(toElementName).interpret(
  #     "self._inferenceEngines[0]._coincidences")


####################################################################
# Support code for matching named algorithms with code.            #
####################################################################


class DynamicImport(object):
  def __init__(self, moduleName, className):
    self.moduleName = moduleName
    self.className = className
  def __call__(self, **keywords):
    module = __import__(self.moduleName, fromlist=[self.className])
    factory = getattr(module, self.className)
    return factory(**keywords)



class DynamicGroupingFunction(object):
  def __init__(self,
      moduleName,
      funcName,
      learningKeys=None,
    ):
    self.moduleName = moduleName
    self.funcName = funcName
    self.learningKeys = learningKeys if learningKeys is not None else []

  def __call__(self,
      learning,
      **keywords
    ):
    module = __import__(self.moduleName, fromlist=[self.funcName])
    function = getattr(module, self.funcName)
    # Re-map names.
    if isinstance(self.learningKeys, dict): # Safer check?
      remapped = dict((k, learning[j]) for j, k in self.learningKeys.iteritems()
          if j in learning)
    else: # Just collect arguments.
      remapped = dict((j, learning[j]) for j in self.learningKeys
          if j in learning)
    return GroupingFunction(function, learning=remapped, grouping=keywords)



class GroupingFunction(object):
  def __init__(self, function, learning, grouping):
    self.function = function
    args = dict(grouping)
    for k in learning:
      assert k not in args
    args.update(learning)
    self.args = args
  def group(self, model):
    # combined = dict(self.args) # Shallow copy.
    # for k in keywords:
    #   assert k not in combined
    # combined.update(keywords)
    # return self.function(**combined)
    return self.function(model=model, **self.args)


####################################################################
# Printing and visualization.                                      #
####################################################################



def nz(x):
  from nupic.network import NodeSetStream
  y = NodeSetStream()
  for i in x.nonzero()[0]: y.insert(i)
  return y.getSet()



def printStatesWithTitles(ts):
  lw = numpy.get_printoptions()["linewidth"]
  numpy.set_printoptions(linewidth=100000)
  titles = [t for t, s in ts]
  ml = max(len(t) for t in titles)
  titles = [((" " * (ml-len(t))) + t) for t in titles]
  combined = numpy.vstack([s for t, s in ts])
  maxes = combined.max(1)
  s = str(combined)
  numpy.set_printoptions(linewidth=lw)
  print "\n".join(("%s %s %f" % (t, l, m)) for t, l, m in
      zip(titles, s.splitlines(), maxes))



def _viewTAM(tam, nsp):
  from nupic.support.learning import printTAM
  if 0:
    printTAM(tam, nsp=nsp, precision=2)
  else:
    tamView = tam.__class__()
    tamView.copy(tam)
    tamView.threshold(0.1 * tam.max()[2])
    printTAM(tamView, childBoundary=nsp, precision=1)
