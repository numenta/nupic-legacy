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

from collections import namedtuple



# Passed as parameter to ActivityMgr
#
# repeating: True if the activity is a repeating activite, False if one-shot
# period: period of activity's execution (number of "ticks")
# cb: a callable to call upon expiration of period; will be called
#     as cb()
PeriodicActivityRequest = namedtuple("PeriodicActivityRequest",
                                     ("repeating", "period", "cb"))



class PeriodicActivityMgr(object):
  """
  TODO: move to shared script so that we can share it with run_opf_experiment
  """

  # iteratorHolder: a list holding one iterator; we use a list so that we can
  #           replace the iterator for repeating activities (a tuple would not
  #           allow it if the field was an imutable value)
  Activity = namedtuple("Activity", ("repeating",
                                     "period",
                                     "cb",
                                     "iteratorHolder"))

  def __init__(self, requestedActivities=[]):
    """
    requestedActivities: a sequence of PeriodicActivityRequest elements
    """

    self.__activities = []
    self.__appendActivities(requestedActivities)

    return


  def addActivities(self, periodicActivities):
    """ Adds activities

    periodicActivities: A sequence of PeriodicActivityRequest elements
    """

    self.__appendActivities(periodicActivities)

    return


  def tick(self):
    """ Activity tick handler; services all activities

    Returns:      True if controlling iterator says it's okay to keep going;
                  False to stop
    """

    # Run activities whose time has come
    for act in self.__activities:
      if not act.iteratorHolder[0]:
        continue

      try:
        next(act.iteratorHolder[0])
      except StopIteration:
        act.cb()
        if act.repeating:
          act.iteratorHolder[0] = iter(xrange(act.period-1))
        else:
          act.iteratorHolder[0] = None

    return True


  def __appendActivities(self, periodicActivities):
    """
    periodicActivities: A sequence of PeriodicActivityRequest elements
    """

    for req in periodicActivities:
      act =   self.Activity(repeating=req.repeating,
                            period=req.period,
                            cb=req.cb,
                            iteratorHolder=[iter(xrange(req.period-1))])
      self.__activities.append(act)

    return
