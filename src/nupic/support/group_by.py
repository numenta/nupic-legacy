# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2016, Numenta, Inc.  Unless you have an agreement
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

from itertools import groupby

''' A utility function wrapper around groupby in itertools. Allows to 
    walk across n sorted lists with respect to their key functions
    and yields a tuple of n lists of the members of the next *smallest*
    group.

    @param args (list) a list of (sortedlist, keyfunction) tuples to perform
                       the groupby on.

    @return (tuple) a n dimensional tuple, where n is the number of tuples
                    in args, of lists of objects that are a member of the 
                    next group

    Notes: Read up on groupby here:
           https://docs.python.org/dev/library/itertools.html#itertools.groupby
'''

def groupByN(*args):
  groupsList = [] #list  (k, group) tuples
  indexList = []

  for listn, fn in args:
    if sorted(listn, cmp=lambda a,b: fn(a) - fn(b)) != listn:
      raise ValueError("iterables must be sorted with respect to their key function")
    groupsListEntry = [(k, list(g)) for k, g in groupby(listn, fn)]
    groupsList.append(groupsListEntry)
    indexList.append([0, len(groupsListEntry)])

  while (any([pair[0] != pair[1] for pair in indexList])):
    argIndices = []
    minKeyVal = float("inf")

    for i, groupTupleList in enumerate(groupsList):
      if indexList[i][0] < indexList[i][1]: #still groups left to process
        groupVal = groupTupleList[indexList[i][0]][0]
        if groupVal < minKeyVal:
          argIndices = [i]
          minKeyVal = groupVal
        elif groupVal == minKeyVal:
          argIndices.append(i)

    retGroups = [minKeyVal]
    argIndicesIndex = 0
    argIndicesLen = len(argIndices)

    for i in xrange(len(indexList)):
      index = indexList[i][0]
      if argIndicesIndex != argIndicesLen and argIndices[argIndicesIndex] == i: 
        retGroups.append(groupsList[i][index][1])
        indexList[i][0] += 1 
        argIndicesIndex += 1
      else:
        retGroups.append([]) 

    yield tuple(retGroups)
