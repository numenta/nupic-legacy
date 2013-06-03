# -*- coding: utf-8 -*-
#
#  SelfTest/Hash/common.py: Common code for Crypto.SelfTest.Hash
#
# Written in 2008 by Dwayne C. Litzenberger <dlitz@dlitz.net>
#
# ===================================================================
# The contents of this file are dedicated to the public domain.  To
# the extent that dedication to the public domain is not available,
# everyone is granted a worldwide, perpetual, royalty-free,
# non-exclusive license to exercise all rights associated with the
# contents of this file for any purpose whatsoever.
# No rights are reserved.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ===================================================================

"""Self-testing for PyCrypto hash modules"""

__revision__ = "$Id$"

import sys
import unittest
import binascii
import string

# For compatibility with Python 2.1 and Python 2.2
if sys.hexversion < 0x02030000:
    # Python 2.1 doesn't have a dict() function
    # Python 2.2 dict() function raises TypeError if you do dict(MD5='blah')
    def dict(**kwargs):
        return kwargs.copy()
else:
    dict = __builtins__['dict']


class HashSelfTest(unittest.TestCase):

    def __init__(self, hashmod, description, expected, input):
        unittest.TestCase.__init__(self)
        self.hashmod = hashmod
        self.expected = expected
        self.input = input
        self.description = description

    def shortDescription(self):
        return self.description

    def runTest(self):
        h = self.hashmod.new()
        h.update(self.input)

        out1 = binascii.b2a_hex(h.digest())
        out2 = h.hexdigest()

        h = self.hashmod.new(self.input)

        out3 = h.hexdigest()
        out4 = binascii.b2a_hex(h.digest())

        self.assertEqual(self.expected, out1)   # h = .new(); h.update(data); h.digest()
        self.assertEqual(self.expected, out2)   # h = .new(); h.update(data); h.hexdigest()
        self.assertEqual(self.expected, out3)   # h = .new(data); h.hexdigest()
        self.assertEqual(self.expected, out4)   # h = .new(data); h.digest()

class MACSelfTest(unittest.TestCase):

    def __init__(self, hashmod, description, expected_dict, input, key, hashmods):
        unittest.TestCase.__init__(self)
        self.hashmod = hashmod
        self.expected_dict = expected_dict
        self.input = input
        self.key = key
        self.hashmods = hashmods
        self.description = description

    def shortDescription(self):
        return self.description

    def runTest(self):
        for hashname in self.expected_dict.keys():
            hashmod = self.hashmods[hashname]
            key = binascii.a2b_hex(self.key)
            data = binascii.a2b_hex(self.input)

            # Strip whitespace from the expected string (which should be in lowercase-hex)
            expected = self.expected_dict[hashname]
            for ch in string.whitespace:
                expected = expected.replace(ch, "")

            h = self.hashmod.new(key, digestmod=hashmod)
            h.update(data)
            out1 = binascii.b2a_hex(h.digest())
            out2 = h.hexdigest()

            h = self.hashmod.new(key, data, hashmod)

            out3 = h.hexdigest()
            out4 = binascii.b2a_hex(h.digest())

            # Test .copy()
            h2 = h.copy()
            h.update("blah blah blah")  # Corrupt the original hash object
            out5 = binascii.b2a_hex(h2.digest())    # The copied hash object should return the correct result

            self.assertEqual(expected, out1)
            self.assertEqual(expected, out2)
            self.assertEqual(expected, out3)
            self.assertEqual(expected, out4)
            self.assertEqual(expected, out5)

def make_hash_tests(module, module_name, test_data):
    tests = []
    for i in range(len(test_data)):
        row = test_data[i]
        if len(row) < 3:
            (expected, input) = row
            description = repr(input)
        else:
            (expected, input, description) = row
        name = "%s #%d: %s" % (module_name, i+1, description)
        tests.append(HashSelfTest(module, name, expected, input))
    return tests

def make_mac_tests(module, module_name, test_data, hashmods):
    tests = []
    for i in range(len(test_data)):
        row = test_data[i]
        (key, data, results, description) = row
        name = "%s #%d: %s" % (module_name, i+1, description)
        tests.append(MACSelfTest(module, name, results, data, key, hashmods))
    return tests

# vim:set ts=4 sw=4 sts=4 expandtab:
