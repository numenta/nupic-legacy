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
  """ Like itertools.groupby, with the following additions:

  - Supports multiple sequences. Instead of returning (k, g), each iteration
    returns (k, g0, g1, ...), with one `g` for each input sequence. The value of
    each `g` is either a non-empty iterator or `None`.
  - It treats the value `None` as an empty sequence. So you can make subsequent
    calls to groupby2 on any `g` value.

  .. note:: Read up on groupby here:
         https://docs.python.org/dev/library/itertools.html#itertools.groupby

  :param args: (list) Parameters alternating between sorted lists and their
                      respective key functions. The lists should be sorted with
                      respect to their key function.

  :returns: (tuple) A n + 1 dimensional tuple, where the first element is the
                  key of the iteration, and the other n entries are groups of
                  objects that share this key. Each group corresponds to the an
                  input sequence. `groupby2` is a generator that returns a tuple
                  for every iteration. If an input sequence has no members with
                  the current key, None is returned in place of a generator.
  """
  generatorList = [] # list of each list's (k, group) tuples

  if len(args) % 2 == 1:
    raise ValueError("Must have a key function for every list.")

  advanceList = []

  # populate above lists
  for i in xrange(0, len(args), 2):
    listn = args[i]
    fn = args[i + 1]
    if listn is not None:
      generatorList.append(groupby(listn, fn))
      advanceList.append(True) # start by advancing everyone.
    else:
      generatorList.append(None)
      advanceList.append(False)

  n = len(generatorList)

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
