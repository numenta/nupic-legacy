# -*- coding: utf-8 -*-
# copyright 2003-2011 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
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

from logilab.common.testlib import TestCase, unittest_main
from logilab.common.xmlutils import parse_pi_data


class ProcessingInstructionDataParsingTest(TestCase):
    def test_empty_pi(self):
        """
        Tests the parsing of the data of an empty processing instruction.
        """
        pi_data = u" \t \n "
        data = parse_pi_data(pi_data)
        self.assertEqual(data, {})

    def test_simple_pi_with_double_quotes(self):
        """
        Tests the parsing of the data of a simple processing instruction using
        double quotes for embedding the value.
        """
        pi_data = u""" \t att="value"\n """
        data = parse_pi_data(pi_data)
        self.assertEqual(data, {u"att": u"value"})

    def test_simple_pi_with_simple_quotes(self):
        """
        Tests the parsing of the data of a simple processing instruction using
        simple quotes for embedding the value.
        """
        pi_data = u""" \t att='value'\n """
        data = parse_pi_data(pi_data)
        self.assertEqual(data, {u"att": u"value"})

    def test_complex_pi_with_different_quotes(self):
        """
        Tests the parsing of the data of a complex processing instruction using
        simple quotes or double quotes for embedding the values.
        """
        pi_data = u""" \t att='value'\n att2="value2" att3='value3'"""
        data = parse_pi_data(pi_data)
        self.assertEqual(data, {u"att": u"value", u"att2": u"value2",
                                 u"att3": u"value3"})

    def test_pi_with_non_attribute_data(self):
        """
        Tests the parsing of the data of a complex processing instruction
        containing non-attribute data.
        """
        pi_data = u""" \t keyword att1="value1" """
        data = parse_pi_data(pi_data)
        self.assertEqual(data, {u"keyword": None, u"att1": u"value1"})


# definitions for automatic unit testing

if __name__ == '__main__':
    unittest_main()

