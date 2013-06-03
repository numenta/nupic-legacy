from unittest import TestCase

import validictory


class TestSchemaErrors(TestCase):

    def setUp(self):
        self.valid_desc = {"description": "My Description for My Schema"}
        self.invalid_desc = {"description": 1233}
        self.valid_title = {"title": "My Title for My Schema"}
        self.invalid_title = {"title": 1233}
        # doesn't matter what this is
        self.data = "whatever"

    def test_description_pass(self):
        try:
            validictory.validate(self.data, self.valid_desc)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_description_fail(self):
        self.assertRaises(ValueError, validictory.validate, self.data,
                          self.invalid_desc)

    def test_title_pass(self):
        try:
            validictory.validate(self.data, self.valid_title)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_title_fail(self):
        self.assertRaises(ValueError, validictory.validate, self.data,
                          self.invalid_title)

    def test_invalid_type(self):
        expected = "Type for field 'bar' must be 'dict', got: 'str'"
        data = {'bar': False}
        schema = {"type": "object", "required": True,
                  "properties": {"bar": "foo"}}
        try:
            validictory.validate(data, schema)
            result = None
        except Exception as e:
            result = e.__str__()
        self.assertEqual(expected, result)


class TestFieldValidationErrors(TestCase):
    def setUp(self):
        self.schema = {"type": "object", "required": True,
                       "properties": {"bar": {"type": "integer"}}}

        self.data = {"bar": "faz"}

    def test(self):
        try:
            validictory.validate(self.data, self.schema)
        except validictory.FieldValidationError as e:
            self.assertEqual(e.fieldname, "bar")
            self.assertEqual(e.value, "faz")
        else:
            self.fail("No Exception")
