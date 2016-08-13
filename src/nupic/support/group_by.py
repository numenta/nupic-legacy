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



class GroupByGenerator(object):
  """ A custom generator used by groupby to allow for len() calls on the
      generator returned.
  """

  __slots__ = ['iterable', 'beginning', 'length', 'end', 'index']

  def __init__(self, iterable, beginning, length):
    self.iterable = iterable
    self.beginning = beginning
    self.length = length
    self.end = self.beginning + self.length
    self.index = 0


  def __iter__(self):
    for i in xrange(self.beginning, self.end):
      self.index = i
      yield self.iterable[i]


  def __len__(self):
    return self.length - self.index


def groupby(lis, fn):
  """ A custom implementation of itertools.groupby that doesn't reuse the
      generator objects, allowing for groupByN to not have to capture the
      group in a list.

  @param lis (list) the list to perform the groupby on
  @param fn  (function) the key function to perform the groupings

  @return (tuple) A (key, GroupByGenerator) tuple where the first value is the
                  key of the group, and second value is the generator that
                  generates the values in the group.
  """
  length = 1
  beginning = 0

  for i in xrange(len(lis)):
    val = fn(lis[i])

    if i == 0:
      key = val
      continue

    if val != key:
      yield (key, GroupByGenerator(lis, beginning, length))
      length = 1
      beginning = i
      key = val
    else:
      length += 1

  l = len(lis)
  if l > 0: # yield last group
    yield (key, GroupByGenerator(lis, beginning, l - beginning))


def groupByN(*args):
  """ A utility function wrapper based on groupby in itertools. Allows to
      walk across n sorted lists with respect to their key functions
      and yields a tuple of n lists of the members of the next *smallest*
      group.

  @param args (list) a list of arguments alternating between sorted lists and
                       their respective key functions. The lists should be
                       sorted with respect to their key function.

  @return (tuple) a n + 1 dimensional tuple, where the first element is the
                    key of the group and the other n entries are lists of
                    objects that are a member of the current group that is being
                    iterated over in the nth list passed in. Note that this
                    is a generator and a n+1 dimensional tuple is yielded for
                    every group.

  Notes: Read up on groupby here:
         https://docs.python.org/dev/library/itertools.html#itertools.groupby

         itertools.groupby was not used and the justification can be seen
         here https://github.com/numenta/nupic/pull/3254#discussion_r74164564

"""
  generatorList = [] # list of each list's (k, group) tuples

  if len(args) % 2 == 1:
    raise ValueError("Must have a key function for every list.")

  # populate above lists
  for i in xrange(0, len(args), 2):
    listn = args[i]
    fn = args[i + 1]
    generatorList.append(groupby(listn, fn))

  n = len(generatorList)

  advanceList = [True] * n # start by advancing everyone.
  nextList = [None] * n
  # while all lists aren't exhausted walk through each group in order
  while True:
    for i in xrange(n):
      if advanceList[i]:
        try:
          nextList[i] = generatorList[i].next()
        except StopIteration:
          nextList[i] = None

    # no more values to process in any of the generators
    if all([entry is None for entry in nextList]):
      break

    # find the smallest next group and all lists that have an element in it
    argIndices = [] # array of indices corresponding to the lists that have at
                    # least one element that is a member of the minKeyVal group
    minKeyVal = float("inf")
    for i, nextVal in enumerate(nextList):
      if nextVal != None: # still groups left in the list
        key = nextVal[0]
        if key < minKeyVal:
          argIndices = [i]
          minKeyVal = key
        elif key == minKeyVal:
          argIndices.append(i)

    # populate the tuple to return
    retGroups = [minKeyVal]
    argIndicesIndex = 0
    argIndicesLen = len(argIndices)
    for i in xrange(n):
      if argIndicesIndex != argIndicesLen and argIndices[argIndicesIndex] == i:
        retGroups.append(nextList[i][1])
        advanceList[i] = True
        argIndicesIndex += 1
      else:
        advanceList[i] = False
        retGroups.append(GroupByGenerator([], 0, 0))

    yield tuple(retGroups)

