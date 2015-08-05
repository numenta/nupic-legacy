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


__all__ = ["cross_list", "cross", "combinations"]

def cross_list(*sequences):
  """
  From: http://book.opensourceproject.org.cn/lamp/python/pythoncook2/opensource/0596007973/pythoncook2-chp-19-sect-9.html
  """
  result = [[ ]]
  for seq in sequences:
    result = [sublist+[item] for sublist in result for item in seq]
  return result

def cross(*sequences):
  """
  From: http://book.opensourceproject.org.cn/lamp/python/pythoncook2/opensource/0596007973/pythoncook2-chp-19-sect-9.html
  """
  # visualize an odometer, with "wheels" displaying "digits"...:
  wheels = list(map(iter, sequences))
  digits = [next(it) for it in wheels]
  while True:
    yield tuple(digits)
    for i in range(len(digits)-1, -1, -1):
      try:
        digits[i] = next(wheels[i])
        break
      except StopIteration:
        wheels[i] = iter(sequences[i])
        digits[i] = next(wheels[i])
    else:
      break

def dcross(**keywords):
  """
  Similar to cross(), but generates output dictionaries instead of tuples.
  """
  keys = list(keywords.keys())
  # Could use keywords.values(), but unsure whether the order
  # the values come out in is guaranteed to be the same as that of keys
  # (appears to be anecdotally true).
  sequences = [keywords[key] for key in keys]

  wheels = list(map(iter, sequences))
  digits = [next(it) for it in wheels]
  while True:
    yield dict(list(zip(keys, digits)))
    for i in range(len(digits)-1, -1, -1):
      try:
        digits[i] = next(wheels[i])
        break
      except StopIteration:
        wheels[i] = iter(sequences[i])
        digits[i] = next(wheels[i])
    else:
      break

def combinations(n, c):
  m = n - 1
  positions = list(range(c))
  while True:
    yield tuple(positions)
    success = False
    lastPi = m
    for i in range(c-1, -1, -1):
      pi = positions[i]
      if pi < lastPi:
        pi += 1
        for j in range(i, c):
          positions[j] = pi
          pi += 1
        success = True
        break
      lastPi = pi-1
    if not success: break # Done.

def permutations(x):
  if len(x) > 1:
    for permutation in permutations(x[1:]):
      # Stick the first digit in every position.
      for i in range(len(permutation)+1):
        yield permutation[:i] + x[0:1] + permutation[i:]
  else: yield x
