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

import os
import imp

from nupic.data.dict_utils import rUpdate


# This file contains utility functions that are used
# internally by the prediction framework and may be imported
# by description files. Functions that are used only by
# the prediction framework should be in utils.py
#
# This file provides support for the following experiment description features:
#
# 1. Sub-experiment support
# 2. Lazy evaluators (e.g., DeferredDictLookup, applyValueGettersToContainer)


###############################################################################
# Sub-experiment support
###############################################################################


# Utility methods for description files  are organized as a base description
#  and an experiment based on that base description.
# The base description calls getConfig to get the configuration from the
# specific experiment, and the specific experiment calls importBaseDescription

# empty initial config allows base experiment to run by itself
_config = dict()

# Save the path to the current sub-experiment here during importBaseDescription()
subExpDir = None


# We will load the description file as a module, which allows us to
# use the debugger and see source code. But description files are frequently
# modified and we want to be able to easily reload them. To facilitate this,
# we reload with a unique module name ("pf_description%d") each time.
baseDescriptionImportCount = 0



def importBaseDescription(path, config):
  global baseDescriptionImportCount, _config, subExpDir
  if not os.path.isabs(path):
    # grab the path to the file doing the import
    import inspect
    callingFrame = inspect.stack()[1][0]
    callingFile = callingFrame.f_globals['__file__']
    subExpDir = os.path.dirname(callingFile)
    path = os.path.normpath(os.path.join(subExpDir, path))

  #print "Importing from: %s" % path

  # stash the config in a place where the loading module can find it.
  _config = config
  mod = imp.load_source("pf_base_description%d" % baseDescriptionImportCount,
                        path)
  # don't want to override __file__ in our caller
  mod.__base_file__ = mod.__file__
  del mod.__file__
  baseDescriptionImportCount += 1
  return mod



def updateConfigFromSubConfig(config):
  # Newer method just updates from sub-experiment
  # _config is the configuration provided by the sub-experiment
  global _config
  rUpdate(config, _config)
  _config = dict()



def getSubExpDir():
  global subExpDir
  return subExpDir





###############################################################################
# Lazy evaluators (DeferredDictLookup, applyValueGettersToContainer, and friends)
###############################################################################



class ValueGetterBase(object):
  """ Base class for "value getters" (e.g., class DictValueGetter) that are used
  to resolve values of sub-fields after the experiment's config dictionary (in
  description.py) is defined and possibly updated from a sub-experiment.

  This solves the problem of referencing the config dictionary's field from within
  the definition of the dictionary itself (before the dictionary's own defintion
  is complete).

  NOTE: its possible that the referenced value does not yet exist at the
        time of instantiation of a given value-getter future. It will be
        resolved when the base description.py calls
        applyValueGettersToContainer().

  NOTE: The constructor of the derived classes MUST call our constructor.
  NOTE: The derived classes MUST override handleGetValue(self).

  NOTE: may be used by base and sub-experiments to derive their own custom value
    getters; however, their use is applicapble only where permitted, as
    described in comments within descriptionTemplate.tpl. See class
    DictValueGetter for implementation example.
  """

  class __NoResult(object):
    """ A private class that we use as a special unique value to indicate that
    our result cache instance variable does not hold a valid result.
    """
    pass


  def __init__(self):
    #print("NOTE: ValueGetterBase INITIALIZING")
    self.__inLookup = False
    self.__cachedResult = self.__NoResult


  def __call__(self, topContainer):
    """ Resolves the referenced value.  If the result is already cached,
    returns it to caller. Otherwise, invokes the pure virtual method
    handleGetValue.  If handleGetValue() returns another value-getter, calls
    that value-getter to resolve the value.  This may result in a chain of calls
    that terminates once the value is fully resolved to a non-value-getter value.
    Upon return, the value is fully resolved and cached, so subsequent calls will
    always return the cached value reference.

    topContainer: The top-level container (dict, tuple, or list [sub-]instance)
                  within whose context the value-getter is applied.

    Returns:  The fully-resolved value that was referenced by the value-getter
              instance
    """

    #print("IN ValueGetterBase.__CAll__()")

    assert(not self.__inLookup)

    if self.__cachedResult is not self.__NoResult:
      return self.__cachedResult

    self.__cachedResult = self.handleGetValue(topContainer)

    if isinstance(self.__cachedResult, ValueGetterBase):
      valueGetter = self.__cachedResult
      self.__inLookup = True
      self.__cachedResult = valueGetter(topContainer)
      self.__inLookup = False

    # The value should be full resolved at this point
    assert(self.__cachedResult is not self.__NoResult)
    assert(not isinstance(self.__cachedResult, ValueGetterBase))

    return self.__cachedResult


  def handleGetValue(self, topContainer):
    """ A "pure virtual" method.  The derived class MUST override this method
    and return the referenced value.  The derived class is NOT responsible for
    fully resolving the reference'd value in the event the value resolves to
    another ValueGetterBase-based instance -- this is handled automatically
    within ValueGetterBase implementation.

    topContainer: The top-level container (dict, tuple, or list [sub-]instance)
                  within whose context the value-getter is applied.

    Returns:      The value referenced by this instance (which may be another
                  value-getter instance)
    """
    raise NotImplementedError("ERROR: ValueGetterBase is an abstract " + \
                              "class; base class MUST override handleGetValue()")



class DictValueGetter(ValueGetterBase):
  """
    Creates a "future" reference to a value within a top-level or a nested
    dictionary.  See also class DeferredDictLookup.
  """
  def __init__(self, referenceDict, *dictKeyChain):
    """
      referenceDict: Explicit reference dictionary that contains the field
                    corresonding to the first key name in dictKeyChain.  This may
                    be the result returned by the built-in globals() function,
                    when we desire to look up a dictionary value from a dictionary
                    referenced by a global variable within the calling module.
                    If None is passed for referenceDict, then the topContainer
                    parameter supplied to handleGetValue() will be used as the
                    reference dictionary instead (this allows the desired module
                    to designate the appropriate reference dictionary for the
                    value-getters when it calls applyValueGettersToContainer())

      dictKeyChain: One or more strings; the first string is a key (that will
                    eventually be defined) in the reference dictionary. If
                    additional strings are supplied, then the values
                    correspnding to prior key strings must be dictionaries, and
                    each additionl string references a sub-dictionary of the
                    former. The final string is the key of the field whose value
                    will be returned by handleGetValue().

      NOTE: Its possible that the referenced value does not yet exist at the
            time of instantiation of this class.  It will be resolved when the
            base description.py calls applyValueGettersToContainer().


    Example:
      config = dict(
        _dsEncoderFieldName2_N = 70,
        _dsEncoderFieldName2_W = 5,

        dsEncoderSchema = [
          dict(
            base=dict(
              fieldname='Name2', type='ScalarEncoder',
              name='Name2', minval=0, maxval=270, clipInput=True,
              n=DictValueGetter(None, '_dsEncoderFieldName2_N'),
              w=DictValueGetter(None, '_dsEncoderFieldName2_W')),
            ),
          ],
      )

      updateConfigFromSubConfig(config)
      applyValueGettersToContainer(config)
    """

    # First, invoke base constructor
    ValueGetterBase.__init__(self)

    assert(referenceDict is None or isinstance(referenceDict, dict))
    assert(len(dictKeyChain) >= 1)

    self.__referenceDict = referenceDict
    self.__dictKeyChain = dictKeyChain


  def handleGetValue(self, topContainer):
    """ This method overrides ValueGetterBase's "pure virtual" method.  It
    returns the referenced value.  The derived class is NOT responsible for
    fully resolving the reference'd value in the event the value resolves to
    another ValueGetterBase-based instance -- this is handled automatically
    within ValueGetterBase implementation.

    topContainer: The top-level container (dict, tuple, or list [sub-]instance)
                  within whose context the value-getter is applied.  If
                  self.__referenceDict is None, then topContainer will be used
                  as the reference dictionary for resolving our dictionary key
                  chain.

    Returns:      The value referenced by this instance (which may be another
                  value-getter instance)
    """
    value = self.__referenceDict if self.__referenceDict is not None else topContainer
    for key in self.__dictKeyChain:
      value = value[key]

    return value



class DeferredDictLookup(DictValueGetter):
  """
    Creates a "future" reference to a value within an implicit dictionary that
    will be passed to applyValueGettersToContainer() in the future (typically
    called by description.py after its config dictionary has been updated from
    the sub-experiment). The reference is relative to the dictionary that will
    be passed to applyValueGettersToContainer()
  """
  def __init__(self, *dictKeyChain):
    """
      dictKeyChain: One or more strings; the first string is a key (that will
                    eventually be defined) in the dictionary that will be passed
                    to applyValueGettersToContainer(). If additional strings are
                    supplied, then the values correspnding to prior key strings
                    must be dictionaries, and each additionl string references a
                    sub-dictionary of the former. The final string is the key of
                    the field whose value will be returned by this value-getter

      NOTE: its possible that the referenced value does not yet exist at the
            time of instantiation of this class.  It will be resolved when the
            base description.py calls applyValueGettersToContainer().


    Example:
      config = dict(
        _dsEncoderFieldName2_N = 70,
        _dsEncoderFieldName2_W = 5,

        dsEncoderSchema = [
          dict(
            base=dict(
              fieldname='Name2', type='ScalarEncoder',
              name='Name2', minval=0, maxval=270, clipInput=True,
              n=DeferredDictLookup('_dsEncoderFieldName2_N'),
              w=DeferredDictLookup('_dsEncoderFieldName2_W')),
            ),
          ],
      )

      updateConfigFromSubConfig(config)
      applyValueGettersToContainer(config)
    """

    # Invoke base (DictValueGetter constructor), passing None for referenceDict,
    # which will force it use the dictionary passed via
    # applyValueGettersToContainer(), instead.
    DictValueGetter.__init__(self, None, *dictKeyChain)



def applyValueGettersToContainer(container):
  """
  """
  _applyValueGettersImpl(container=container, currentObj=container,
                         recursionStack=[])



def _applyValueGettersImpl(container, currentObj, recursionStack):
  """
  """

  # Detect cycles
  if currentObj in recursionStack:
    return

  # Sanity-check of our cycle-detection logic
  assert(len(recursionStack) < 1000)

  # Push the current object on our cycle-detection stack
  recursionStack.append(currentObj)

  # Resolve value-getters within dictionaries, tuples and lists

  if isinstance(currentObj, dict):
    for (key, value) in currentObj.items():
      if isinstance(value, ValueGetterBase):
        currentObj[key] = value(container)

      _applyValueGettersImpl(container, currentObj[key], recursionStack)


  elif isinstance(currentObj, tuple) or isinstance(currentObj, list):
    for (i, value) in enumerate(currentObj):
      # NOTE: values within a tuple should never be value-getters, since
      #       the top-level elements within a tuple are immutable. However,
      #       if any nested sub-elements might be mutable
      if isinstance(value, ValueGetterBase):
        currentObj[i] = value(container)

      _applyValueGettersImpl(container, currentObj[i], recursionStack)

  else:
    pass

  recursionStack.pop()
  return
