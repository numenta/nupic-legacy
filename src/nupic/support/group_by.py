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


def groupby2(*args):
  """ An extension to groupby in itertools. Allows to walk across n sorted lists
      with respect to their key functions and yields a tuple of n lists of the
      members of the next *smallest* group.

  @param args (list) a list of arguments alternating between sorted lists and
                       their respective key functions. The lists should be
                       sorted with respect to their key function.

  @return (tuple) a n + 1 dimensional tuple, where the first element is the
                    key of the group and the other n entries are lists of
                    objects that are a member of the current group that is being
                    iterated over in the nth list passed in. Note that this
                    is a generator and a n+1 dimensional tuple is yielded for
                    every group. If a list has no members in the current
                    group, None is returned in place of a generator.

  Notes: Read up on groupby here:
         https://docs.python.org/dev/library/itertools.html#itertools.groupby

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
    if all(entry is None for entry in nextList):
      break

    # the minimum key value in the nextList
    minKeyVal = min(nextVal[0] for nextVal in nextList
                    if nextVal is not None)

    # populate the tuple to return based on minKeyVal
    retGroups = [minKeyVal]
    for i in xrange(n):
      if nextList[i] is not None and nextList[i][0] == minKeyVal:
        retGroups.append(nextList[i][1])
        advanceList[i] = True
      else:
        advanceList[i] = False
        retGroups.append(None)

    yield tuple(retGroups)
