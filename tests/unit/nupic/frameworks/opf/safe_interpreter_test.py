# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""Unit tests for safe_interpreter module."""

import ast
import io
import types

import unittest2 as unittest

from nupic.frameworks.opf.safe_interpreter import SafeInterpreter

class TestSafeInterpreter(unittest.TestCase):


  # AWS tests attribute required for tagging via automatic test discovery via
  # nosetests
  engineAWSClusterTest = 1


  def setUp(self):
    """Set up an interpreter directing output to a BytesIO stream."""
    self.interpreter = SafeInterpreter(writer=io.BytesIO())


  def testPrimitives(self):
    """Verify basic primitives"""
    self.assertTrue(self.interpreter("True"))
    self.assertFalse(self.interpreter("False"))
    self.assertTrue(self.interpreter("None") is None)


  def testConditionals(self):
    """Verify basic if statements"""
    self.assertTrue(self.interpreter("True if True else False"))
    self.assertTrue(self.interpreter("""
foo = False
if not foo:
 foo = True
foo
"""))


  def testBlacklist(self):
    """Verify that src with blacklisted nodes fail"""
    self.interpreter("for x in []: pass")
    self.assertIn("NotImplementedError",
                  (error.get_error()[0] for error in self.interpreter.error))
    self.interpreter("while True: pass")
    self.assertIn("NotImplementedError",
                  (error.get_error()[0] for error in self.interpreter.error))


  def testParse(self):
    """Verify that parse() returns an AST instance"""
    tree = self.interpreter.parse("True")
    self.assertTrue(isinstance(tree, ast.AST))


  def testCompile(self):
    """Verify that parse() returns a compile()-able AST"""
    tree = self.interpreter.parse("True")
    codeObj = compile(tree, "<string>", mode="exec")
    self.assertTrue(isinstance(codeObj, types.CodeType))


  def testSum(self):
    """Verify that sum() works and is correct"""
    result = self.interpreter("sum([x*p for x,p in {1:2}.items()])")
    self.assertEqual(result, 2)


  def testRecursive(self):
    """Verify that a recursive function raises a runtime error"""
    self.interpreter("""
def foo():
  foo()

foo()
""")

    self.assertIn("RuntimeError",
                  (error.get_error()[0] for error in self.interpreter.error))


  def testOpen(self):
    """Verify that an attempt to open a file raises a runtime error"""
    self.interpreter("open('foo')")
    self.assertIn("RuntimeError",
                  (error.get_error()[0] for error in self.interpreter.error))



if __name__ == "__main__":
  unittest.main()
