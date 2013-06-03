from unittest import TestCase

import validictory


class TestDisallowUnknownProperties(TestCase):

    def setUp(self):
        self.data_simple = {"name": "john doe", "age": 42}
        self.schema_simple = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
        }

        self.data_complex = {
            "inv_number": "123",
            "rows": [
                {
                    "sku": "ab-456",
                    "desc": "a description",
                    "price": 100.45
                },
                {
                    "sku": "xy-123",
                    "desc": "another description",
                    "price": 999.00
                }
            ]
        }
        self.schema_complex = {
            "type": "object",
            "properties": {
                "inv_number": {"type": "string"},
                "rows": {
                    "type": "array",
                    "items": {
                        "sku": {"type": "string"},
                        "desc": {"type": "string"},
                        "price": {"type": "number"}
                    },
                }
            }
        }

    def test_disallow_unknown_properties_pass(self):
        try:
            validictory.validate(self.data_simple, self.schema_simple,
                                 disallow_unknown_properties=True)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_disallow_unknown_properties_fail(self):
        self.data_simple["sex"] = "male"
        self.assertRaises(validictory.SchemaError, validictory.validate,
                          self.data_simple, self.schema_simple,
                          disallow_unknown_properties=True)

    def test_disallow_unknown_properties_complex_pass(self):
        try:
            validictory.validate(self.data_complex, self.schema_complex,
                                 disallow_unknown_properties=True)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_disallow_unknown_properties_complex_fail(self):
        newrow = {"sku": "789", "desc": "catch me if you can", "price": 1,
                  "rice": 666}
        self.data_complex["rows"].append(newrow)
        self.assertRaises(validictory.SchemaError, validictory.validate,
                          self.data_complex, self.schema_complex,
                          disallow_unknown_properties=True)
