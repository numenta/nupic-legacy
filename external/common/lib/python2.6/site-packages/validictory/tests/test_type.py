from unittest import TestCase
from decimal import Decimal
import datetime
import sys

if sys.version_info[0] == 3:
    unicode_str = '\u2603'
else:
    unicode_str = unicode('snowman')


import validictory


class TestType(TestCase):
    def test_schema(self):
        schema = {
            "type": [
                {"type": "array", "minItems": 10},
                {"type": "string", "pattern": "^0+$"}
            ]
        }

        data1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        data2 = "0"
        data3 = 1203

        for x in [data1, data2]:
            try:
                validictory.validate(x, schema)
            except ValueError as e:
                self.fail("Unexpected failure: %s" % e)

        self.assertRaises(ValueError, validictory.validate, data3, schema)

    def _test_type(self, typename, valids, invalids):
        for x in valids:
            try:
                validictory.validate(x, {"type": typename})
            except ValueError as e:
                self.fail("Unexpected failure: %s" % e)

        for x in invalids:
            self.assertRaises(ValueError, validictory.validate, x,
                              {"type": typename})

    def test_integer(self):
        valid_ints = [1, -89, 420000]
        invalid_ints = [1.2, "bad", {"test": "blah"}, [32, 49], None, True]
        self._test_type('integer', valid_ints, invalid_ints)

    def test_string(self):
        valids = ["abc", unicode_str]
        invalids = [1.2, 1, {"test": "blah"}, [32, 49], None, True]
        self._test_type('string', valids, invalids)

    def test_number(self):
        valids = [1.2, -89.42, 48, -32, Decimal('25.25')]
        invalids = ["bad", {"test": "blah"}, [32.42, 494242], None, True]
        self._test_type('number', valids, invalids)

    def test_boolean(self):
        valids = [True, False]
        invalids = [1.2, "False", {"test": "blah"}, [32, 49], None, 1, 0]
        self._test_type('boolean', valids, invalids)

    def test_object(self):
        valids = [{"blah": "test"}, {"this": {"blah": "test"}}, {1: 2, 10: 20}]
        invalids = [1.2, "bad", 123, [32, 49], None, True]
        self._test_type('object', valids, invalids)

    def test_array(self):
        valids = [[1, 89], [48, {"test": "blah"}, "49", 42], (47, 11)]
        invalids = [1.2, "bad", {"test": "blah"}, 1234, None, True]
        self._test_type('array', valids, invalids)

    def test_null(self):
        valids = [None]
        invalids = [1.2, "bad", {"test": "blah"}, [32, 49], 1284, True]
        self._test_type('null', valids, invalids)

    def test_any(self):
        valids = [1.2, "bad", {"test": "blah"}, [32, 49], None, 1284, True]
        self._test_type('any', valids, [])

    def test_default(self):
        # test default value (same as any really)
        valids = [1.2, "bad", {"test": "blah"}, [32, 49], None, 1284, True]
        for x in valids:
            try:
                validictory.validate(x, {})
            except ValueError as e:
                self.fail("Unexpected failure: %s" % e)

    def test_multi(self):
        types = ["null", "integer", "string"]
        valids = [None, 42, "string"]
        invalids = [1.2, {"test": "blah"}, [32, 49], True]
        self._test_type(types, valids, invalids)
        self._test_type(tuple(types), valids, invalids)


class TestDisallow(TestType):
    def _test_type(self, typename, valids, invalids):
        for x in invalids:
            try:
                validictory.validate(x, {"disallow": typename})
            except ValueError as e:
                self.fail("Unexpected failure: %s" % e)

        for x in valids:
            self.assertRaises(ValueError, validictory.validate, x,
                              {"disallow": typename})


class DateValidator(validictory.validator.SchemaValidator):

    def validate_type_date(self, value):
        return isinstance(value, datetime.date)

    def validate_type_datetime(self, value):
        return isinstance(value, datetime.datetime)


class TestCustomType(TestCase):
    def test_date(self):
        self._test_type('date', [datetime.date.today()],
                        [2010, '2010'])

    def test_datetime(self):
        self._test_type('datetime', [datetime.datetime.now()],
                        [2010, '2010', datetime.date.today()])

    def test_either(self):
        self._test_type(['datetime', 'date'],
                        [datetime.date.today(), datetime.datetime.now()],
                        [2010, '2010'])

    def _test_type(self, typename, valids, invalids):
        validator = DateValidator()
        for x in valids:
            try:
                validator.validate(x, {"type": typename})
            except ValueError as e:
                self.fail("Unexpected failure: %s" % e)

        for x in invalids:
            self.assertRaises(ValueError, validator.validate, x,
                              {"type": typename})
