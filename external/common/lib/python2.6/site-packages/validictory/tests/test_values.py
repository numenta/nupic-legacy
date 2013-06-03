"""
    Tests that test the value of individual items
"""

from unittest import TestCase

import validictory


class TestEnum(TestCase):
    schema = {"enum": ["test", True, 123, ["???"]]}
    schema2 = {"enum": ("test", True, 123, ["???"])}

    def test_enum_pass(self):
        data = ["test", True, 123, ["???"]]
        try:
            for item in data:
                validictory.validate(item, self.schema)
                validictory.validate(item, self.schema2)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_enum_fail(self):
        data = "unknown"

        self.assertRaises(ValueError, validictory.validate, data, self.schema)


class TestPattern(TestCase):

    # match simplified regular expression for an e-mail address
    schema = {"pattern":
              "^[A-Za-z0-9][A-Za-z0-9\.]*@([A-Za-z0-9]+\.)+[A-Za-z0-9]+$"}

    def test_pattern_pass(self):
        data = "my.email01@gmail.com"

        try:
            validictory.validate(data, self.schema)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_pattern_pass_nonstring(self):
        data = 123

        try:
            validictory.validate(data, self.schema)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_pattern_fail(self):
        data = "whatever"

        self.assertRaises(ValueError, validictory.validate, data, self.schema)


def validate_format_contains_spaces(validator, fieldname, value,
                                    format_option):
    if ' ' in value:
        return

    raise validictory.FieldValidationError(
        "Value %(value)r of field '%(fieldname)s' does not contain any spaces,"
        "but it should" % locals(), fieldname, value)


class TestFormat(TestCase):

    schema_datetime = {"format": "date-time"}
    schema_date = {"format": "date"}
    schema_time = {"format": "time"}
    schema_utcmillisec = {"format": "utc-millisec"}
    schema_ip = {"format": "ip-address"}
    schema_spaces = {"format": "spaces"}

    def test_format_datetime_pass(self):
        data = "2011-01-13T10:56:53Z"

        try:
            validictory.validate(data, self.schema_datetime)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_format_date_pass(self):
        data = "2011-01-13"

        try:
            validictory.validate(data, self.schema_date)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_format_time_pass(self):
        data = "10:56:53"

        try:
            validictory.validate(data, self.schema_time)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_format_utcmillisec_pass(self):
        try:
            validictory.validate(1294915735, self.schema_utcmillisec)
            validictory.validate(1294915735.0, self.schema_utcmillisec)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_format_datetime_nonexisting_day_fail(self):
        data = "2013-13-13T00:00:00Z"

        self.assertRaises(ValueError, validictory.validate, data,
                          self.schema_datetime)

    def test_format_datetime_feb29_fail(self):
        data = "2011-02-29T00:00:00Z"

        self.assertRaises(ValueError, validictory.validate, data,
                          self.schema_datetime)

    def test_format_datetime_notutc_fail(self):
        data = "2011-01-13T10:56:53+01: 00"

        self.assertRaises(ValueError, validictory.validate, data,
                          self.schema_datetime)

    def test_format_datetime_fail(self):
        data = "whatever"
        self.assertRaises(ValueError, validictory.validate, data,
                          self.schema_datetime)

    def test_format_date_fail(self):
        data = "whatever"
        self.assertRaises(ValueError, validictory.validate, data,
                          self.schema_date)

    def test_format_time_fail(self):
        data = "whatever"
        self.assertRaises(ValueError, validictory.validate, data,
                          self.schema_time)

    def test_format_utcmillisec_fail(self):
        data = "whatever"
        self.assertRaises(ValueError, validictory.validate, data,
                          self.schema_utcmillisec)

    def test_format_utcmillisec_negative_fail(self):
        data = -1
        self.assertRaises(ValueError, validictory.validate, data,
                          self.schema_utcmillisec)

    def test_format_ip_pass(self):
        valids = ["0.0.0.0", "255.255.255.255"]
        for ip in valids:
            try:
                validictory.validate(ip, self.schema_ip)
            except ValueError as e:
                self.fail("Unexpected failure: %s" % e)

    def test_format_ip_fail(self):
        invalids = [1.2, "bad", {"test": "blah"}, [32, 49], 1284, True,
                    "-0.-0.-0.-0", "-1.-1.-1.-1", "256.256.256.256"]
        for ip in invalids:
            self.assertRaises(ValueError, validictory.validate, ip,
                              self.schema_ip)

    def test_format_required_false(self):
        schema = {
            'type': 'object',
            'properties': {
                'startdate': {'type': 'string', 'format': 'date-time',
                              'required': False}
            }
        }
        try:
            validictory.validate({}, schema, required_by_default=False)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_format_custom_unregistered_pass(self):
        data = 'No-spaces-here'

        try:
            # no custom validator installed, so no error
            validictory.validate(data, self.schema_spaces)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_format_custom_instantiated_pass(self):
        data = 'Here are spaces'

        validator = validictory.SchemaValidator(
            {'spaces': validate_format_contains_spaces})

        try:
            # validator installed, but data validates
            validator.validate(data, self.schema_spaces)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_format_custom_registered_pass(self):
        data = 'Here are spaces'

        validator = validictory.SchemaValidator()
        validator.register_format_validator('spaces',
                                            validate_format_contains_spaces)

        try:
            # validator registered, but data validates
            validator.validate(data, self.schema_spaces)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_format_custom_registered_fail(self):
        data = 'No-spaces-here'

        validator = validictory.SchemaValidator(
            {'spaces': validate_format_contains_spaces})

        # validator registered, but data does not conform
        self.assertRaises(ValueError, validator.validate, data,
                          self.schema_spaces)


class TestUniqueItems(TestCase):

    schema = {"uniqueItems": True}
    schema_false = {"uniqueItems": False}

    def test_uniqueitems_pass(self):
        data = [1, 2, 3]

        try:
            validictory.validate(data, self.schema)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_uniqueitems_pass_string(self):
        data = ['1', '2', '3']

        try:
            validictory.validate(data, self.schema)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_uniqueitems_pass_nested_array(self):
        '''
        uniqueItems only applies for the array it was specified on and not to
        all datastructures nested within.
        '''
        data = [[1, [5, 5]], [2, [5, 5]]]

        try:
            validictory.validate(data, self.schema)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_uniqueitems_pass_not_an_array(self):
        data = 13  # it's pretty unique

        try:
            validictory.validate(data, self.schema)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_uniqueitems_pass_different_types(self):
        data = [1, "1"]

        try:
            validictory.validate(data, self.schema)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_uniqueitems_false_pass(self):
        data = [1, 1, 1]

        try:
            validictory.validate(data, self.schema_false)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_uniqueitems_fail(self):
        data = [1, 1, 1]

        self.assertRaises(ValueError, validictory.validate, data, self.schema)

    def test_uniqueitems_fail_nested_arrays(self):
        data = [[1, 2, 3], [1, 2, 3]]

        self.assertRaises(ValueError, validictory.validate, data, self.schema)

    def test_uniqueitems_fail_nested_objects(self):
        data = [{'one': 1, 'two': 2}, {'one': 1, 'two': 2}]

        self.assertRaises(ValueError, validictory.validate, data, self.schema)

    def test_uniqueitems_fail_null(self):
        data = [None, None]

        self.assertRaises(ValueError, validictory.validate, data, self.schema)


class TestMaximum(TestCase):
    props = {
        "prop01": {"type": "number", "maximum": 10},
        "prop02": {"type": "integer", "maximum": 20}
    }
    props_exclusive = {
        "prop": {"type": "integer", "maximum": 20, "exclusiveMaximum": True},
    }
    schema = {"type": "object", "properties": props}
    schema_exclusive = {"type": "object", "properties": props_exclusive}

    def test_maximum_pass(self):
        #Test less than
        data1 = {"prop01": 5, "prop02": 10}
        #Test equal
        data2 = {"prop01": 10, "prop02": 20}

        try:
            validictory.validate(data1, self.schema)
            validictory.validate(data2, self.schema)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_maximum_exclusive_pass(self):
        #Test less than
        data = {"prop": 19}

        try:
            validictory.validate(data, self.schema_exclusive)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_maximum_fail(self):
        #Test number
        data1 = {"prop01": 11, "prop02": 19}
        #Test integer
        data2 = {"prop01": 9, "prop02": 21}

        self.assertRaises(ValueError, validictory.validate, data1, self.schema)
        self.assertRaises(ValueError, validictory.validate, data2, self.schema)

    def test_maximum_exclusive_fail(self):
        #Test equal
        data = {"prop": 20}

        self.assertRaises(ValueError, validictory.validate, data,
                          self.schema_exclusive)


class TestMinimum(TestCase):
    props = {
        "prop01": {"type": "number", "minimum": 10},
        "prop02": {"type": "integer", "minimum": 20}
    }
    props_exclusive = {
        "prop": {"type": "integer", "minimum": 20, "exclusiveMinimum": True},
    }
    schema = {"type": "object", "properties": props}
    schema_exclusive = {"type": "object", "properties": props_exclusive}

    def test_minimum_pass(self):
        #Test greater than
        data1 = {"prop01": 21, "prop02": 21}
        #Test equal
        data2 = {"prop01": 10, "prop02": 20}

        try:
            validictory.validate(data1, self.schema)
            validictory.validate(data2, self.schema)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_minimum_exclusive_pass(self):
        #Test greater than
        data = {"prop": 21}

        try:
            validictory.validate(data, self.schema_exclusive)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_minimum_fail(self):
        #Test number
        data1 = {"prop01": 9, "prop02": 21}
        #Test integer
        data2 = {"prop01": 10, "prop02": 19}

        self.assertRaises(ValueError, validictory.validate, data1, self.schema)
        self.assertRaises(ValueError, validictory.validate, data2, self.schema)

    def test_minimum_exclusive_fail(self):
        #Test equal
        data = {"prop": 20}

        self.assertRaises(ValueError, validictory.validate, data,
                          self.schema_exclusive)


class TestMinLength(TestCase):
    schema = {"minLength": 4}

    def test_minLength_pass(self):
        # str-equal, str-gt, list-equal, list-gt
        data = ['test', 'string', [1, 2, 3, 4], [0, 0, 0, 0, 0]]

        try:
            for item in data:
                validictory.validate(item, self.schema)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_minLength_pass_nonstring(self):
        #test when data is not a string
        data1 = 123

        try:
            validictory.validate(data1, self.schema)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_minLength_fail(self):
        #test equal
        data = ["car", [1, 2, 3]]

        for item in data:
            self.assertRaises(ValueError, validictory.validate, data,
                              self.schema)


class TestMaxLength(TestCase):
    schema = {"maxLength": 4}

    def test_maxLength_pass(self):
        # str-equal, str-lt, list-equal, list-lt
        data = ["test", "car", [1, 2, 3, 4], [0, 0, 0]]
        try:
            for item in data:
                validictory.validate(item, self.schema)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_maxLength_pass_nonstring(self):
        # test when data is not a string
        data1 = 12345

        try:
            validictory.validate(data1, self.schema)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_maxLength_fail(self):
        data = ["string", [1, 2, 3, 4, 5]]
        for item in data:
            self.assertRaises(ValueError, validictory.validate, item,
                              self.schema)


class TestBlank(TestCase):

    def test_blank_default_false(self):
        schema = {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "required": True,
                }
            }
        }
        try:
            validictory.validate({"key": "value"}, {}, blank_by_default=False)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

        self.assertRaises(ValueError, validictory.validate, {"key": ""},
                          schema)

    def test_blank_default_true(self):
        schema = {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "required": True,
                }
            }
        }
        try:
            validictory.validate({"key": ""}, schema, blank_by_default=True)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_blank_false(self):
        schema = {"blank": False}
        try:
            validictory.validate("test", schema, blank_by_default=True)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

        self.assertRaises(ValueError, validictory.validate, "", schema)

    def test_blank_true(self):
        try:
            validictory.validate("", {"blank": True}, blank_by_default=False)
            validictory.validate("test", {"blank": True},
                                 blank_by_default=False)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)


class TestDivisibleBy(TestCase):
    schema = {'type': 'number', 'divisibleBy': 12}
    schema0 = {'type': 'number', 'divisibleBy': 0}

    def test_divisibleBy_pass(self):
        data = 60
        try:
            validictory.validate(data, self.schema)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_divisibleBy_fail(self):
        data = 13
        self.assertRaises(ValueError, validictory.validate, data, self.schema)

    def test_divisibleBy_ZeroDivisionError_fail(self):
        data = 60
        self.assertRaises(ValueError, validictory.validate, data, self.schema0)
