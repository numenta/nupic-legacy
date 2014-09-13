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

import numpy

#=============================================================================
class ObjectDiff(object):
  """
  A class representing the differences between two generic python objects.
  """
  #---------------------------------------------------------------------------
  def __init__(self,
               obj0,
               obj1):

    # Initializations
    self._ignoreList = set(['__dict__'])
    self._customDiffOperators = {}
    self._customDiffMembers = set([])

    # Get all the member functions and variables of both TFDR objects
    members0 = dir(obj0)
    members1 = dir(obj1)
    self.obj0 = obj0
    self.obj1 = obj1

    # Separate by types, names
    types = set([])
    names = set([])
    for m in members0:
      types.update([type(eval("obj0."+m))])
      names.update([m])
    for m in members1:
      types.update([type(eval("obj1."+m))])
      names.update([m])


    # Hash table to find the members using their type as the key
    membersByType = {}
    for memberType in types:
      membersByType[memberType] = {}
      membersByType[memberType][0] = {}
      membersByType[memberType][1] = {}
    for m in members0:
      membersByType[type(eval("obj0."+m))][0][m] = eval("obj0."+m)
    for m in members1:
      membersByType[type(eval("obj1."+m))][1][m] = eval("obj1."+m)


    # Hash table to find the members using their name as the key
    membersByName = {}
    for memberName in names:
      membersByName[memberName] = {}
      if memberName in members0:
        membersByName[memberName][0] = eval("obj0."+memberName)
      else:
        membersByName[memberName][0] = None
      if memberName in members1:
        membersByName[memberName][1] = eval("obj1."+memberName)
      else:
        membersByName[memberName][1] = None



    self.types = types
    self.names = names
    self.membersByName = membersByName
    self.membersByType = membersByType
    self._hashKeys = {}
    for key in membersByType.keys():
      self._hashKeys[key.__name__] = key
  #---------------------------------------------------------------------------
  def _rawDiff(self, memberName):
    """
    Returns the raw difference between two members of the objects.
    """
    exist0 = hasattr(self.obj0, memberName)
    exist1 = hasattr(self.obj1, memberName)

    if (not (exist0 and exist1)) or numpy.array(numpy.array(eval("self.obj0."+memberName)) != numpy.array(eval("self.obj1."+memberName))).all():
      isDiff = True
      try:
        val0 = eval("self.obj0."+memberName)
      except:
        val0 = 'N/A'
      try:
        val1 = eval("self.obj1."+memberName)
      except:
        val1 = 'N/A'
      if memberName in self._customDiffMembers:
        try:
          diff = self._customDiffOperators[memberName](val0, val1)
          if hasattr(diff,'__iter__'):
            val0 = diff[1]
            val1 = diff[2]
            diff = diff[0]
        except:
          diff = 'Custom Diff Failed!'
      else:
        try:
          diff = val0 - val1
        except:
          diff = "N/A"
    else:
      isDiff = False
      diff = None
      val0 = None
      val1 = None

    return isDiff, diff, [val0, val1]
  #---------------------------------------------------------------------------
  def _getAllRawDiffs(self):
    """
    Goes through all the members and returns their raw differences.
    """
    diffs = []
    for m in self.names:
      if m not in self._ignoreList:
        _isDiff, _diff, _vals = self._rawDiff(m)
        if _isDiff:
          diffs.append((m, _diff, _vals))

    return diffs
  #---------------------------------------------------------------------------
  def addToIgnoreList(self, memberName):
    """
    Adds a member name to the ignore list so that it is not considered when
    computing differneces.
    """
    if memberName not in self.names:
      raise ValueError ("%s is not in the members list!" %memberName)

    self._ignoreList.update([memberName])
  #---------------------------------------------------------------------------
  def addToIgnoreListByType(self, memberType):
    """
    Adds all the members of a certain type to the ignore list.
    """
    members = self.membersByType[memberType][0].keys()
    for m in members:
      self.addToIgnoreList(m)
  #---------------------------------------------------------------------------
  def addAllToIgnoreList(self):
    """
    Adds all the members to the ignore list. This is useful when the user wants
    only a few members to be considered. In this case everything is first added
    to the ignore list, and then those important members are popped out.
    """
    for m in self.names:
      self.addToIgnoreList(m)
  #---------------------------------------------------------------------------
  def removeFromIgnoreList(self, memberName):
    """
    Removes a member from the ignore list.
    """
    try:
      self._ignoreList.remove(memberName)
    except:
      raise ValueError ("%s is not in the ignore list!" %memberName)
  #---------------------------------------------------------------------------
  def getTypeKeyFromName(self, typeName):
    """
    Returns the hash key of the type from its name.
    """
    return self._hashKeys[typeName]
  #---------------------------------------------------------------------------

  #---------------------------------------------------------------------------
  def defineCustomOperation(self, memberName, function):
    """
    Defines a custom operation to be performed in place of the standard
    subtraction operation for a given member.

    function is assumed to be of format:
        def function(member0, member1):
          ...
          return diff
    """
    if memberName not in self.names:
      raise ValueError ("%s is not in the members list!" %memberName)

    self._customDiffOperators[memberName] = function
    self._customDiffMembers.update([memberName])

    return
  #---------------------------------------------------------------------------
