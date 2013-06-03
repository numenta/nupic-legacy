from unittest import TestCase

import validictory


class TestItems(TestCase):
    schema1 = {
        "type": "array",
        "items": {"type": "string"}
    }

    schema2 = {
        "type": "array",
        "items": [{"type": "integer"}, {"type": "string"}, {"type": "boolean"}]
    }

    schema3 = {
        "type": "array",
        "items": ({"type": "integer"}, {"type": "string"}, {"type": "boolean"})
    }

    def test_items_single_pass(self):
        data = ["string", "another string", "mystring"]
        data2 = ["JSON Schema is cool", "yet another string"]

        try:
            validictory.validate(data, self.schema1)
            validictory.validate(data2, self.schema1)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_items_single_fail(self):
        data = ["string", "another string", 1]
        self.assertRaises(ValueError, validictory.validate, data, self.schema1)

    def test_items_multiple_pass(self):
        data = [1, "More strings?", True]
        data2 = [12482, "Yes, more strings", False]

        try:
            validictory.validate(data, self.schema2)
            validictory.validate(data2, self.schema2)
            validictory.validate(tuple(data), self.schema3)
            validictory.validate(tuple(data2), self.schema3)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_items_multiple_fail(self):
        data = [1294, "Ok. I give up"]
        data2 = [1294, "Ok. I give up", "Not a boolean"]
        self.assertRaises(ValueError, validictory.validate, data, self.schema2)
        self.assertRaises(ValueError, validictory.validate, data2,
                          self.schema2)

    def test_items_descriptive_fail(self):
        data = [1294]
        try:
            validictory.validate(data, self.schema1)
        except ValueError as e:
            # warning should mention list item, not _data
            assert 'list item' in str(e)


class TestAdditionalItems(TestCase):

    schema1 = {
        "type": "array",
        "items": [{"type": "integer"}, {"type": "string"},
                  {"type": "boolean"}],
        "additionalItems": False
    }

    schema2 = {
        "type": "array",
        "items": [{"type": "integer"}, {"type": "string"},
                  {"type": "boolean"}],
        "additionalItems": True
    }

    schema3 = {
        "type": "array",
        "items": [{"type": "integer"}, {"type": "string"},
                  {"type": "boolean"}],
        "additionalItems": {"type": "number"}
    }

    schema4 = {
        "type": "array",
        "items": [{"type": "integer"}, {"type": "string"},
                  {"type": "boolean"}],
        "additionalItems": {"type": ["number", "boolean"]}
    }

    def test_additionalItems_false_no_additional_items_pass(self):
        data = [12482, "Yes, more strings", False]

        try:
            validictory.validate(data, self.schema1)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_additionalItems_false_additional_items_fail(self):
        data = [12482, "Yes, more strings", False, "I don't belong here"]
        self.assertRaises(ValueError, validictory.validate, data, self.schema1)

    def test_additionalItems_pass(self):
        data = [12482, "Yes, more strings", False, ["I'm"],
                {"also": "allowed!"}]
        try:
            validictory.validate(data, self.schema2)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_additionalItems_schema_pass(self):
        data = [12482, "Yes, more strings", False, 13.37, 47.11]
        try:
            validictory.validate(data, self.schema3)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_additionalItems_schema_fail(self):
        data = [12482, "Yes, more strings", False, 13.37, "I'm not allowed"]
        self.assertRaises(ValueError, validictory.validate, data, self.schema3)

    def test_additionalItems_multischema_pass(self):
        data = [12482, "Yes, more strings", False, 13.37, 47.11, True, False]
        try:
            validictory.validate(data, self.schema4)
        except ValueError as e:
            self.fail("Unexpected failure: %s" % e)

    def test_additionalItems_multischema_fail(self):
        data = [12482, "Yes, more strings", False, 13.37, True,
                "I'm not allowed"]
        self.assertRaises(ValueError, validictory.validate, data, self.schema4)
