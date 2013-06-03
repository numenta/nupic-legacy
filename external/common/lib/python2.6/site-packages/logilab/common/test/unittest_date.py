# copyright 2003-2012 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This file is part of logilab-common.
#
# logilab-common is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option) any
# later version.
#
# logilab-common is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with logilab-common.  If not, see <http://www.gnu.org/licenses/>.
"""
Unittests for date helpers
"""
from logilab.common.testlib import TestCase, unittest_main, tag

from logilab.common.date import date_range, endOfMonth
from logilab.common.date import add_days_worked, nb_open_days, \
         get_national_holidays, ustrftime, ticks2datetime

from datetime import date, datetime, timedelta

try:
    from mx.DateTime import Date as mxDate, DateTime as mxDateTime, \
         now as mxNow, RelativeDateTime, RelativeDate
except ImportError:
    mxDate = mxDateTime = RelativeDateTime = mxNow = None

class DateTC(TestCase):
    datecls = date
    datetimecls = datetime
    timedeltacls = timedelta
    now = datetime.now

    def test_day(self):
        """enumerate days"""
        r = list(date_range(self.datecls(2000, 1, 1), self.datecls(2000, 1, 4)))
        expected = [self.datecls(2000, 1, 1), self.datecls(2000, 1, 2), self.datecls(2000, 1, 3)]
        self.assertListEqual(r, expected)
        r = list(date_range(self.datecls(2000, 1, 31), self.datecls(2000, 2, 3)))
        expected = [self.datecls(2000, 1, 31), self.datecls(2000, 2, 1), self.datecls(2000, 2, 2)]
        self.assertListEqual(r, expected)
        r = list(date_range(self.datecls(2000, 1, 1), self.datecls(2000, 1, 6), 2))
        expected = [self.datecls(2000, 1, 1), self.datecls(2000, 1, 3), self.datecls(2000, 1, 5)]
        self.assertListEqual(r, expected)

    def test_add_days_worked(self):
        add = add_days_worked
        # normal
        self.assertEqual(add(self.datecls(2008, 1, 3), 1), self.datecls(2008, 1, 4))
        # skip week-end
        self.assertEqual(add(self.datecls(2008, 1, 3), 2), self.datecls(2008, 1, 7))
        # skip 2 week-ends
        self.assertEqual(add(self.datecls(2008, 1, 3), 8), self.datecls(2008, 1, 15))
        # skip holiday + week-end
        self.assertEqual(add(self.datecls(2008, 4, 30), 2), self.datecls(2008, 5, 5))

    def test_get_national_holidays(self):
        holidays = get_national_holidays
        yield self.assertEqual, holidays(self.datecls(2008, 4, 29), self.datecls(2008, 5, 2)), \
              [self.datecls(2008, 5, 1)]
        yield self.assertEqual, holidays(self.datecls(2008, 5, 7), self.datecls(2008, 5, 8)), []
        x = self.datetimecls(2008, 5, 7, 12, 12, 12)
        yield self.assertEqual, holidays(x, x + self.timedeltacls(days=1)), []

    def test_open_days_now_and_before(self):
        nb = nb_open_days
        x = self.now()
        y = x - self.timedeltacls(seconds=1)
        self.assertRaises(AssertionError, nb, x, y)

    def assertOpenDays(self, start, stop, expected):
        got = nb_open_days(start, stop)
        self.assertEqual(got, expected)

    def test_open_days_tuesday_friday(self):
        self.assertOpenDays(self.datecls(2008, 3, 4), self.datecls(2008, 3, 7), 3)

    def test_open_days_day_nextday(self):
        self.assertOpenDays(self.datecls(2008, 3, 4), self.datecls(2008, 3, 5), 1)

    def test_open_days_friday_monday(self):
        self.assertOpenDays(self.datecls(2008, 3, 7), self.datecls(2008, 3, 10), 1)

    def test_open_days_friday_monday_with_two_weekends(self):
        self.assertOpenDays(self.datecls(2008, 3, 7), self.datecls(2008, 3, 17), 6)

    def test_open_days_tuesday_wednesday(self):
        """week-end + easter monday"""
        self.assertOpenDays(self.datecls(2008, 3, 18), self.datecls(2008, 3, 26), 5)

    def test_open_days_friday_saturday(self):
        self.assertOpenDays(self.datecls(2008, 3, 7), self.datecls(2008, 3, 8), 1)

    def test_open_days_friday_sunday(self):
        self.assertOpenDays(self.datecls(2008, 3, 7), self.datecls(2008, 3, 9), 1)

    def test_open_days_saturday_sunday(self):
        self.assertOpenDays(self.datecls(2008, 3, 8), self.datecls(2008, 3, 9), 0)

    def test_open_days_saturday_monday(self):
        self.assertOpenDays(self.datecls(2008, 3, 8), self.datecls(2008, 3, 10), 0)

    def test_open_days_saturday_tuesday(self):
        self.assertOpenDays(self.datecls(2008, 3, 8), self.datecls(2008, 3, 11), 1)

    def test_open_days_now_now(self):
        x = self.now()
        self.assertOpenDays(x, x, 0)

    def test_open_days_now_now2(self):
        x = self.datetimecls(2010, 5, 24)
        self.assertOpenDays(x, x, 0)

    def test_open_days_afternoon_before_holiday(self):
        self.assertOpenDays(self.datetimecls(2008, 5, 7, 14), self.datetimecls(2008, 5, 8, 0), 1)

    def test_open_days_afternoon_before_saturday(self):
        self.assertOpenDays(self.datetimecls(2008, 5, 9, 14), self.datetimecls(2008, 5, 10, 14), 1)

    def test_open_days_afternoon(self):
        self.assertOpenDays(self.datetimecls(2008, 5, 6, 14), self.datetimecls(2008, 5, 7, 14), 1)

    @tag('posix', '1900')
    def test_ustrftime_before_1900(self):
        date = self.datetimecls(1328, 3, 12, 6, 30)
        self.assertEqual(ustrftime(date, '%Y-%m-%d %H:%M:%S'), u'1328-03-12 06:30:00')

    @tag('posix', '1900')
    def test_ticks2datetime_before_1900(self):
        ticks = -2209075200000
        date = ticks2datetime(ticks)
        self.assertEqual(ustrftime(date, '%Y-%m-%d'), u'1899-12-31')


class MxDateTC(DateTC):
    datecls = mxDate
    datetimecls = mxDateTime
    timedeltacls = RelativeDateTime
    now = mxNow

    def check_mx(self):
        if mxDate is None:
            self.skipTest('mx.DateTime is not installed')

    def setUp(self):
        self.check_mx()

    def test_month(self):
        """enumerate months"""
        r = list(date_range(self.datecls(2000, 1, 2), self.datecls(2000, 4, 4), endOfMonth))
        expected = [self.datecls(2000, 1, 2), self.datecls(2000, 2, 29), self.datecls(2000, 3, 31)]
        self.assertListEqual(r, expected)
        r = list(date_range(self.datecls(2000, 11, 30), self.datecls(2001, 2, 3), endOfMonth))
        expected = [self.datecls(2000, 11, 30), self.datecls(2000, 12, 31), self.datecls(2001, 1, 31)]
        self.assertListEqual(r, expected)

if __name__ == '__main__':
    unittest_main()
