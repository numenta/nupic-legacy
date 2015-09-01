# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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

"""
utils.py are a collection of methods that can be reused by different classes
in our codebase.
"""

import numbers



class MovingAverage(object):
  """Helper class for computing moving average and sliding window"""


  def __init__(self, windowSize, existingHistoricalValues=None):
    """
    new instance of MovingAverage, so method .next() can be used
    @param windowSize - length of sliding window
    @param existingHistoricalValues - construct the object with already
        some values in it.
    """
    if not isinstance(windowSize, numbers.Integral):
      raise TypeError("MovingAverage - windowSize must be integer type")
    if  windowSize <= 0:
      raise ValueError("MovingAverage - windowSize must be >0")

    self.windowSize = windowSize
    if existingHistoricalValues is not None:
      self.slidingWindow = existingHistoricalValues[
                              len(existingHistoricalValues)-windowSize:]
    else:
      self.slidingWindow = []
    self.total = float(sum(self.slidingWindow))


  @staticmethod
  def compute(slidingWindow, total, newVal, windowSize):
    """Routine for computing a moving average.

    @param slidingWindow a list of previous values to use in computation that
        will be modified and returned
    @param total the sum of the values in slidingWindow to be used in the
        calculation of the moving average
    @param newVal a new number compute the new windowed average
    @param windowSize how many values to use in the moving window

    @returns an updated windowed average, the modified input slidingWindow list,
        and the new total sum of the sliding window
    """
    if len(slidingWindow) == windowSize:
      total -= slidingWindow.pop(0)

    slidingWindow.append(newVal)
    total += newVal
    return float(total) / len(slidingWindow), slidingWindow, total


  def next(self, newValue):
    """Instance method wrapper around compute."""
    newAverage, self.slidingWindow, self.total = self.compute(
        self.slidingWindow, self.total, newValue, self.windowSize)
    return newAverage


  def getSlidingWindow(self):
    return self.slidingWindow


  def getCurrentAvg(self):
    """get current average"""
    return float(self.total) / len(self.slidingWindow)

  # TODO obsoleted by capnp, will be removed in future
  def __setstate__(self, state):
    """ for loading this object"""
    self.__dict__.update(state)

    if not hasattr(self, "slidingWindow"):
      self.slidingWindow = []

    if not hasattr(self, "total"):
      self.total = 0
      self.slidingWindow = sum(self.slidingWindow)


  def __eq__(self, o):
    return (isinstance(o, MovingAverage) and
            o.slidingWindow == self.slidingWindow and
            o.total == self.total and
            o.windowSize == self.windowSize)


  def __call__(self, value):
    return self.next(value)


  @classmethod
  def read(cls, proto):
    movingAverage = object.__new__(cls)
    movingAverage.windowSize = proto.windowSize
    movingAverage.slidingWindow = list(proto.slidingWindow)
    movingAverage.total = proto.total
    return movingAverage


  def write(self, proto):
    proto.windowSize = self.windowSize
    proto.slidingWindow = self.slidingWindow
    proto.total = self.total



#######################################################
# code from functools.lru_cache for Python 3.3, backports from ActiveState:
# https://code.activestate.com/recipes/578078/
# my modifications under '#mmm:' for runtime evaluation of cachesize argument
# which is needed for use in a library
from collections import namedtuple
from functools import update_wrapper
from threading import RLock

_CacheInfo = namedtuple("CacheInfo", ["hits", "misses", "maxsize", "currsize"])

class _HashedSeq(list):
    __slots__ = 'hashvalue'

    def __init__(self, tup, hash=hash):
        self[:] = tup
        self.hashvalue = hash(tup)

    def __hash__(self):
        return self.hashvalue

def _make_key(args, kwds, typed,
             kwd_mark = (object(),),
             fasttypes = {int, str, frozenset, type(None)},
             sorted=sorted, tuple=tuple, type=type, len=len):
    'Make a cache key from optionally typed positional and keyword arguments'
    key = args
    if kwds:
        sorted_items = sorted(kwds.items())
        key += kwd_mark
        for item in sorted_items:
            key += item
    if typed:
        key += tuple(type(v) for v in args)
        if kwds:
            key += tuple(type(v) for k, v in sorted_items)
    elif len(key) == 1 and type(key[0]) in fasttypes:
        return key[0]
    return _HashedSeq(key)

def _setSize(sizeref, properties, *args, **kwds):
  """
  set size for the cache
  from parsing method's arguments or object's member variable
  specified by sizeref value.
  @param sizeref - string, name of variable which holds the size
                   If sizeref is None, the call is ignored.
  @param properties - dict with 'maxsize' and 'init' keys, 
                   passed from the wrapper function.
  @except ValueError if specified sizeref was not retrieved
  """
  if not properties['init']: # already initiated
    return
  properties['init'] = False
  if not isinstance(sizeref, str): # no sizeref
    return

  mxArg = -1
  mxRef = -1

  # 1st from the method's arguments:
  mxArg = int(kwds.pop(sizeref, -1))
  # 2nd from caller object's member of name as sizeref's value:
  # try to get attribute of value sizeref from methods parent object, if it is called from an object
  # otherwise just ignore
  try:
    caller = args[0]
    mxRef = int(caller.__dict__.get(sizeref, -1))
  except AttributeError:
    # ignore missing attribute of the object
    pass

  if mxArg >= 0:
    print "setting maxsize to methods arg %s = %i" % (sizeref, mxArg)
    properties['maxsize'] = mxArg
  elif mxRef >= 0:
    print "setting maxsize to object's member %s = %i" % (sizeref, mxRef)
    properties['maxsize'] = mxRef
  else:
    raise ValueError("lru_cache: No arg or object's member of name %s, as specified in 'sizeref'" % (sizeref))


def lru_cache(maxsize=100, typed=False, sizeref=None):
    """Least-recently-used cache decorator.

    If *maxsize* is set to None, the LRU features are disabled and the cache
    can grow without bound.

    If *typed* is True, arguments of different types will be cached separately.
    For example, f(3.0) and f(3) will be treated as distinct calls with
    distinct results.

    If *sizeref* string is defined, it overrides maxsize value and will attempt
    to read it from a decorated method's argument of the same name as its value,
    or from the decorated method's object instance member of that name. In this
    order. Raises exception of no such variables exist. 

    Arguments to the cached function must be hashable.

    View the cache statistics named tuple (hits, misses, maxsize, currsize) with
    f.cache_info().  Clear the cache and statistics with f.cache_clear().
    Access the underlying function with f.__wrapped__.

    See:  http://en.wikipedia.org/wiki/Cache_algorithms#Least_Recently_Used

    """

    # Users should only access the lru_cache through its public API:
    #       cache_info, cache_clear, and f.__wrapped__
    # The internals of the lru_cache are encapsulated for thread safety and
    # to allow the implementation to change (including a possible C version).

    def decorating_function(user_function):

        cache = dict()
        stats = [0, 0]                  # make statistics updateable non-locally
        HITS, MISSES = 0, 1             # names for the stats fields
        make_key = _make_key
        cache_get = cache.get           # bound method to lookup key or return None
        _len = len                      # localize the global len() function
        lock = RLock()                  # because linkedlist updates aren't threadsafe
        root = []                       # root of the circular doubly linked list
        root[:] = [root, root, None, None]      # initialize by pointing to self
        nonlocal_root = [root]                  # make updateable non-locally
        PREV, NEXT, KEY, RESULT = 0, 1, 2, 3    # names for the link fields
        #mmm: replaced maxsize with properties['maxsize'] is it can be overriden from inner functions
        properties = dict()
        properties['maxsize'] = maxsize         # make maxsize updatable non-locally
        properties['init'] = True               # do _setSize
                  
        if properties['maxsize'] == 0:

            def wrapper(*args, **kwds):
                # no caching, just do a statistics update after a successful call
                result = user_function(*args, **kwds)
                stats[MISSES] += 1
                return result

        elif properties['maxsize'] is None:

            def wrapper(*args, **kwds):
                # simple caching without ordering or size limit
                key = make_key(args, kwds, typed)
                result = cache_get(key, root)   # root used here as a unique not-found sentinel
                if result is not root:
                    stats[HITS] += 1
                    return result
                result = user_function(*args, **kwds)
                cache[key] = result
                stats[MISSES] += 1
                return result

        else:

            def wrapper(*args, **kwds):
                # size limited caching that tracks accesses by recency
                _setSize(sizeref, properties, *args, **kwds)
                key = make_key(args, kwds, typed) if kwds or typed else args
                
                with lock:
                    link = cache_get(key)
                    if link is not None:
                        # record recent use of the key by moving it to the front of the list
                        root, = nonlocal_root
                        link_prev, link_next, key, result = link
                        link_prev[NEXT] = link_next
                        link_next[PREV] = link_prev
                        last = root[PREV]
                        last[NEXT] = root[PREV] = link
                        link[PREV] = last
                        link[NEXT] = root
                        stats[HITS] += 1
                        return result
                result = user_function(*args, **kwds)
                with lock:
                    root, = nonlocal_root
                    if key in cache:
                        # getting here means that this same key was added to the
                        # cache while the lock was released.  since the link
                        # update is already done, we need only return the
                        # computed result and update the count of misses.
                        pass
                    elif _len(cache) >= properties['maxsize']:
                        # use the old root to store the new key and result
                        oldroot = root
                        oldroot[KEY] = key
                        oldroot[RESULT] = result
                        # empty the oldest link and make it the new root
                        root = nonlocal_root[0] = oldroot[NEXT]
                        oldkey = root[KEY]
                        oldvalue = root[RESULT]
                        root[KEY] = root[RESULT] = None
                        # now update the cache dictionary for the new links
                        del cache[oldkey]
                        cache[key] = oldroot
                    else:
                        # put result in a new link at the front of the list
                        last = root[PREV]
                        link = [last, root, key, result]
                        last[NEXT] = root[PREV] = cache[key] = link
                    stats[MISSES] += 1
                return result

        def cache_info():
            """Report cache statistics"""
            with lock:
                return _CacheInfo(stats[HITS], stats[MISSES], properties['maxsize'], len(cache))

        def cache_clear():
            """Clear the cache and cache statistics"""
            with lock:
                cache.clear()
                root = nonlocal_root[0]
                root[:] = [root, root, None, None]
                stats[:] = [0, 0]
                properties['init'] = True

        wrapper.__wrapped__ = user_function
        wrapper.cache_info = cache_info
        wrapper.cache_clear = cache_clear
        return update_wrapper(wrapper, user_function)

    return decorating_function

