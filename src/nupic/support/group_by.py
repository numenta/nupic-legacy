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

''' A utility function wrapper based on groupby in itertools. Allows to
    walk across n sorted lists with respect to their key functions
    and yields a tuple of n lists of the members of the next *smallest*
    group.

    @param args (list) a list of arguments alternating between sorted lists and
                       their respective key functions. The lists should be
                       sorted with respect to their key function.

    @return (tuple) a n + 1 dimensional tuple, where the first element is the
                    key of the group and the other n entries are lists of
                    objects that are a member of the current group that is being
                    iterated over in the nth list passed in.

    Notes: Read up on groupby here:
           https://docs.python.org/dev/library/itertools.html#itertools.groupby
'''

class GroupByGenerator(object):

  def __init__(self, iterable, length):
    self.iterable = iterable
    self.length = length
    self.index = 0


  def __iter__(self):
    for i in xrange(self.length):
      self.index = i
      yield self.iterable[i]


  def __len__(self):
    return self.length - self.index


def groupby(lis, fn):
  length = 1
  begining = 0

  for i in xrange(len(lis)):
    val = fn(lis[i])
    if i == 0:
      key = val
      continue
    if val != key:
      yield (key, GroupByGenerator(lis[begining : i], length))
      length = 1
      begining = i
      key = val
    else:
      length += 1
  if len(lis):
    yield (key, GroupByGenerator(lis[begining:], length))



def groupByN(*args):
  groupsList = [] # list of each list's (k, group) tuples
  indexList = [] # list of [currentIndex, endIndex] pairs

  if len(args) % 2 == 1:
    raise ValueError("Must have a key function for every list.")

  # populate above lists
  for i in xrange(0, len(args), 2):
    listn = args[i]
    fn = args[i + 1]
    groupsListEntry = [(k, g) for k, g in groupby(listn, fn)]
    groupsList.append(groupsListEntry)
    indexList.append([0, len(groupsListEntry)])

  # while all lists aren't exhausted walk through each group in order
  while any([pair[0] != pair[1] for pair in indexList]):
    # find the smallest next group and all lists that have an element in it
    argIndices = [] # array of indices corresponding to the lists that have at
                    # least one element that is a member of the minKeyVal group
    minKeyVal = float("inf")
    for i, groupTupleList in enumerate(groupsList):
      if indexList[i][0] < indexList[i][1]: # still groups left in the list
        groupVal = groupTupleList[indexList[i][0]][0]
        if groupVal < minKeyVal:
          argIndices = [i]
          minKeyVal = groupVal
        elif groupVal == minKeyVal:
          argIndices.append(i)

    # populate the tuple to return
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
        retGroups.append(GroupByGenerator([], 0))

    yield tuple(retGroups)
