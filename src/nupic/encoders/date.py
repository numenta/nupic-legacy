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

import datetime

import numpy

from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
from nupic.encoders.base import Encoder
from nupic.encoders.scalar import ScalarEncoder



class DateEncoder(Encoder):
  """
  A date encoder encodes a date according to encoding parameters specified in
  its constructor. The input to a date encoder is a datetime.datetime object.
  The output is the concatenation of several sub-encodings, each of which
  encodes a different aspect of the date. Which sub-encodings are present, and
  details of those sub-encodings, are specified in the DateEncoder constructor.

  Each parameter describes one attribute to encode. By default, the attribute
  is not encoded.

  :param season: (int | tuple) Season of the year, where units = day.

      - (int) width of attribute; default radius = 91.5 days (1 season)
      - (tuple)  season[0] = width; season[1] = radius

  :param dayOfWeek: (int | tuple) Day of week, where monday = 0, units = 1 day.

      - (int) width of attribute; default radius = 1 day
      - (tuple) dayOfWeek[0] = width; dayOfWeek[1] = radius

  :param weekend: (int) Is a weekend or not. A block of bits either 0s or 1s.

      - (int) width of attribute

  :param holiday: (int) Is a holiday or not, boolean: 0, 1

      - (int) width of attribute

  :param timeOfday: (int | tuple) Time of day, where midnight = 0, units = hour.

      - (int) width of attribute: default radius = 4 hours
      - (tuple) timeOfDay[0] = width; timeOfDay[1] = radius

  :param customDays: (tuple) A way to custom encode specific days of the week.

      - [0] (int) Width of attribute
      - [1] (str | list) Either a string representing a day of the week like
        "Monday" or "mon", or a list of these strings.

  :param forced: (default True) if True, skip checks for parameters' settings.
         See :class:`~.nupic.encoders.scalar.ScalarEncoder` for details.

  """


  def __init__(self, season=0, dayOfWeek=0, weekend=0, holiday=0, timeOfDay=0, customDays=0,
                name = '', forced=True):

    self.width = 0
    self.description = []
    self.name = name

    # This will contain a list of (name, encoder, offset) tuples for use by
    #  the decode() method
    self.encoders = []

    self.seasonEncoder = None
    if season != 0:
      # Ignore leapyear differences -- assume 366 days in a year
      # Radius = 91.5 days = length of season
      # Value is number of days since beginning of year (0 - 355)
      if hasattr(season, "__getitem__"):
        w = season[0]
        radius = season[1]
      else:
        w = season
        radius = 91.5

      self.seasonEncoder = ScalarEncoder(w = w, minval=0, maxval=366,
                                         radius=radius, periodic=True,
                                         name="season", forced=forced)
      self.seasonOffset = self.width
      self.width += self.seasonEncoder.getWidth()
      self.description.append(("season", self.seasonOffset))
      self.encoders.append(("season", self.seasonEncoder, self.seasonOffset))


    self.dayOfWeekEncoder = None
    if dayOfWeek != 0:
      # Value is day of week (floating point)
      # Radius is 1 day
      if hasattr(dayOfWeek, "__getitem__"):
        w = dayOfWeek[0]
        radius = dayOfWeek[1]
      else:
        w = dayOfWeek
        radius = 1
      self.dayOfWeekEncoder = ScalarEncoder(w = w, minval=0, maxval=7,
                                            radius=radius, periodic=True,
                                            name="day of week", forced=forced)
      self.dayOfWeekOffset = self.width
      self.width += self.dayOfWeekEncoder.getWidth()
      self.description.append(("day of week", self.dayOfWeekOffset))
      self.encoders.append(
        ("day of week", self.dayOfWeekEncoder, self.dayOfWeekOffset))

    self.weekendEncoder = None
    if weekend != 0:
      # Binary value. Not sure if this makes sense. Also is somewhat redundant
      #  with dayOfWeek
      #Append radius if it was not provided
      if not hasattr(weekend, "__getitem__"):
        weekend = (weekend, 1)
      self.weekendEncoder = ScalarEncoder(w=weekend[0], minval=0, maxval=1,
                                          periodic=False, radius=weekend[1],
                                          name="weekend", forced=forced)
      self.weekendOffset = self.width
      self.width += self.weekendEncoder.getWidth()
      self.description.append(("weekend", self.weekendOffset))
      self.encoders.append(("weekend", self.weekendEncoder, self.weekendOffset))

    #Set up custom days encoder, first argument in tuple is width
    #second is either a single day of the week or a list of the days
    #you want encoded as ones.
    self.customDaysEncoder = None
    if customDays !=0:
      customDayEncoderName = ""
      daysToParse = []
      assert len(customDays)==2, "Please provide a w and the desired days"
      if isinstance(customDays[1], list):
        for day in customDays[1]:
          customDayEncoderName+=str(day)+" "
        daysToParse=customDays[1]
      elif isinstance(customDays[1], str):
        customDayEncoderName+=customDays[1]
        daysToParse = [customDays[1]]
      else:
        assert False, "You must provide either a list of days or a single day"
      #Parse days
      self.customDays = []
      for day in daysToParse:
        if(day.lower() in ["mon","monday"]):
          self.customDays+=[0]
        elif day.lower() in ["tue","tuesday"]:
          self.customDays+=[1]
        elif day.lower() in ["wed","wednesday"]:
          self.customDays+=[2]
        elif day.lower() in ["thu","thursday"]:
          self.customDays+=[3]
        elif day.lower() in ["fri","friday"]:
          self.customDays+=[4]
        elif day.lower() in ["sat","saturday"]:
          self.customDays+=[5]
        elif day.lower() in ["sun","sunday"]:
          self.customDays+=[6]
        else:
          assert False, "Unable to understand %s as a day of week" % str(day)
      self.customDaysEncoder = ScalarEncoder(w=customDays[0], minval = 0, maxval=1,
                                            periodic=False, radius=1,
                                            name=customDayEncoderName, forced=forced)
      self.customDaysOffset = self.width
      self.width += self.customDaysEncoder.getWidth()
      self.description.append(("customdays", self.customDaysOffset))
      self.encoders.append(("customdays", self.customDaysEncoder, self.customDaysOffset))

    self.holidayEncoder = None
    if holiday != 0:
      # A "continuous" binary value. = 1 on the holiday itself and smooth ramp
      #  0->1 on the day before the holiday and 1->0 on the day after the holiday.
      self.holidayEncoder = ScalarEncoder(w = holiday, minval = 0, maxval=1,
                                          periodic=False, radius=1,
                                          name="holiday", forced=forced)
      self.holidayOffset = self.width
      self.width += self.holidayEncoder.getWidth()
      self.description.append(("holiday", self.holidayOffset))
      self.encoders.append(("holiday", self.holidayEncoder, self.holidayOffset))

    self.timeOfDayEncoder = None
    if timeOfDay != 0:
      # Value is time of day in hours
      # Radius = 4 hours, e.g. morning, afternoon, evening, early night,
      #  late night, etc.
      if hasattr(timeOfDay, "__getitem__"):
        w = timeOfDay[0]
        radius = timeOfDay[1]
      else:
        w = timeOfDay
        radius = 4
      self.timeOfDayEncoder = ScalarEncoder(w = w, minval=0, maxval=24,
                              periodic=True, radius=radius, name="time of day", forced=forced)
      self.timeOfDayOffset = self.width
      self.width += self.timeOfDayEncoder.getWidth()
      self.description.append(("time of day", self.timeOfDayOffset))
      self.encoders.append(("time of day", self.timeOfDayEncoder, self.timeOfDayOffset))


  def getWidth(self):
    return self.width


  def getScalarNames(self, parentFieldName=''):
    """ See method description in base.py """

    names = []

    # This forms a name which is the concatenation of the parentFieldName
    #   passed in and the encoder's own name.
    def _formFieldName(encoder):
      if parentFieldName == '':
        return encoder.name
      else:
        return '%s.%s' % (parentFieldName, encoder.name)

    # -------------------------------------------------------------------------
    # Get the scalar values for each sub-field
    if self.seasonEncoder is not None:
      names.append(_formFieldName(self.seasonEncoder))

    if self.dayOfWeekEncoder is not None:
      names.append(_formFieldName(self.dayOfWeekEncoder))

    if self.customDaysEncoder is not None:
      names.append(_formFieldName(self.customDaysEncoder))

    if self.weekendEncoder is not None:
      names.append(_formFieldName(self.weekendEncoder))

    if self.holidayEncoder is not None:
      names.append(_formFieldName(self.holidayEncoder))

    if self.timeOfDayEncoder is not None:
      names.append(_formFieldName(self.timeOfDayEncoder))

    return names


  def getEncodedValues(self, input):
    """ See method description in base.py """

    if input == SENTINEL_VALUE_FOR_MISSING_DATA:
      return numpy.array([None])

    assert isinstance(input, datetime.datetime)
    values = []

    # -------------------------------------------------------------------------
    # Get the scalar values for each sub-field
    timetuple = input.timetuple()
    timeOfDay = timetuple.tm_hour + float(timetuple.tm_min)/60.0

    if self.seasonEncoder is not None:
      dayOfYear = timetuple.tm_yday
      # input.timetuple() computes the day of year 1 based, so convert to 0 based
      values.append(dayOfYear-1)

    if self.dayOfWeekEncoder is not None:
      dayOfWeek = timetuple.tm_wday + timeOfDay / 24.0
      values.append(dayOfWeek)

    if self.weekendEncoder is not None:
      # saturday, sunday or friday evening
      if timetuple.tm_wday == 6 or timetuple.tm_wday == 5 \
          or (timetuple.tm_wday == 4 and timeOfDay > 18):
        weekend = 1
      else:
        weekend = 0
      values.append(weekend)

    if self.customDaysEncoder is not None:
      if timetuple.tm_wday in self.customDays:
        customDay = 1
      else:
        customDay = 0
      values.append(customDay)
    if self.holidayEncoder is not None:
      # A "continuous" binary value. = 1 on the holiday itself and smooth ramp
      #  0->1 on the day before the holiday and 1->0 on the day after the holiday.
      # Currently the only holiday we know about is December 25
      # holidays is a list of holidays that occur on a fixed date every year
      holidays = [(12, 25)]
      val = 0
      for h in holidays:
        # hdate is midnight on the holiday
        hdate = datetime.datetime(timetuple.tm_year, h[0], h[1], 0, 0, 0)
        if input > hdate:
          diff = input - hdate
          if diff.days == 0:
            # return 1 on the holiday itself
            val = 1
            break
          elif diff.days == 1:
            # ramp smoothly from 1 -> 0 on the next day
            val = 1.0 - (float(diff.seconds) / (86400))
            break
        else:
          diff = hdate - input
          if diff.days == 0:
            # ramp smoothly from 0 -> 1 on the previous day
            val = 1.0 - (float(diff.seconds) / 86400)

      values.append(val)

    if self.timeOfDayEncoder is not None:
      values.append(timeOfDay)

    return values


  def getScalars(self, input):
    """
    See method description in :meth:`~.nupic.encoders.base.Encoder.getScalars`.

    :param input: (datetime) representing the time being encoded

    :returns: A numpy array of the corresponding scalar values in the following
              order: season, dayOfWeek, weekend, holiday, timeOfDay. Some of
              these fields might be omitted if they were not specified in the
              encoder.
    """
    return numpy.array(self.getEncodedValues(input))


  def getBucketIndices(self, input):
    """ See method description in base.py """

    if input == SENTINEL_VALUE_FOR_MISSING_DATA:
      # Encoder each sub-field
      return [None] * len(self.encoders)

    else:
      assert isinstance(input, datetime.datetime)

      # Get the scalar values for each sub-field
      scalars = self.getScalars(input)

      # Encoder each sub-field
      result = []
      for i in xrange(len(self.encoders)):
        (name, encoder, offset) = self.encoders[i]
        result.extend(encoder.getBucketIndices(scalars[i]))
      return result


  def encodeIntoArray(self, input, output):
    """ See method description in base.py """

    if input == SENTINEL_VALUE_FOR_MISSING_DATA:
      output[0:] = 0
    else:
      if not isinstance(input, datetime.datetime):
        raise ValueError("Input is type %s, expected datetime. Value: %s" % (
            type(input), str(input)))

      # Get the scalar values for each sub-field
      scalars = self.getScalars(input)
      # Encoder each sub-field
      for i in xrange(len(self.encoders)):
        (name, encoder, offset) = self.encoders[i]
        encoder.encodeIntoArray(scalars[i], output[offset:])


  def getDescription(self):
    return self.description


  @classmethod
  def read(cls, proto):
    encoder = object.__new__(cls)
    encoder.encoders = []
    encoder.description = []
    encoder.width = 0
    encoder.name = proto.name

    def addEncoder(encoderAttr, offsetAttr):
      protoVal = getattr(proto, encoderAttr)
      if protoVal.n:
        setattr(encoder, encoderAttr, ScalarEncoder.read(protoVal))
        innerEncoder = getattr(encoder, encoderAttr)
        setattr(encoder, offsetAttr, encoder.width)
        innerOffset = getattr(encoder, offsetAttr)
        encoder.width += innerEncoder.getWidth()
        encoder.description.append((innerEncoder.name, innerOffset))
        encoder.encoders.append((innerEncoder.name, innerEncoder, innerOffset))
      else:
        setattr(encoder, encoderAttr, None)

    addEncoder("seasonEncoder", "seasonOffset")
    addEncoder("dayOfWeekEncoder", "dayOfWeekOffset")
    addEncoder("weekendEncoder", "weekendOffset")
    addEncoder("customDaysEncoder", "customDaysOffset")
    addEncoder("holidayEncoder", "holidayOffset")
    addEncoder("timeOfDayEncoder", "timeOfDayOffset")

    return encoder


  def write(self, proto):
    for name in ("seasonEncoder",
                 "dayOfWeekEncoder",
                 "weekendEncoder",
                 "customDaysEncoder",
                 "holidayEncoder",
                 "timeOfDayEncoder"):
      encoder = getattr(self, name)
      if encoder:
        encoder.write(getattr(proto, name))
