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
from binascii import a2b_hex, b2a_hex

# For compatibility with Python 2.1 and Python 2.2
if sys.hexversion < 0x02030000:
    # Python 2.1 doesn't have a dict() function
    # Python 2.2 dict() function raises TypeError if you do dict(MD5='blah')
    def dict(**kwargs):
        return kwargs.copy()
else:
    dict = __builtins__['dict']

class _NoDefault: pass        # sentinel object
def _extract(d, k, default=_NoDefault):
    """Get an item from a dictionary, and remove it from the dictionary."""
    try:
        retval = d[k]
    except KeyError:
        if default is _NoDefault:
            raise
        return default
    del d[k]
    return retval

# Generic cipher test case
class CipherSelfTest(unittest.TestCase):

    def __init__(self, module, params):
        unittest.TestCase.__init__(self)
        self.module = module

        # Extract the parameters
        params = params.copy()
        self.description = _extract(params, 'description')
        self.key = _extract(params, 'key')
        self.plaintext = _extract(params, 'plaintext')
        self.ciphertext = _extract(params, 'ciphertext')
        self.module_name = _extract(params, 'module_name', None)

        mode = _extract(params, 'mode', None)
        self.mode_name = str(mode)
        if mode is not None:
            # Block cipher
            self.mode = getattr(self.module, "MODE_" + mode)
            self.iv = _extract(params, 'iv', None)
        else:
            # Stream cipher
            self.mode = None
            self.iv = None

        self.extra_params = params

    def shortDescription(self):
        return self.description

    def _new(self):
        params = self.extra_params.copy()

        # Handle CTR mode parameters.  By default, we use Counter.new(self.module.block_size)
        if hasattr(self.module, "MODE_CTR") and self.mode == self.module.MODE_CTR:
            from Crypto.Util import Counter
            ctr_class = _extract(params, 'ctr_class', Counter.new)
            ctr_params = _extract(params, 'ctr_params', {}).copy()
            if ctr_params.has_key('prefix'): ctr_params['prefix'] = a2b_hex(ctr_params['prefix'])
            if ctr_params.has_key('suffix'): ctr_params['suffix'] = a2b_hex(ctr_params['suffix'])
            if not ctr_params.has_key('nbits'):
                ctr_params['nbits'] = 8*(self.module.block_size - len(ctr_params.get('prefix', '')) - len(ctr_params.get('suffix', '')))
            params['counter'] = ctr_class(**ctr_params)

        if self.mode is None:
            # Stream cipher
            return self.module.new(a2b_hex(self.key), **params)
        elif self.iv is None:
            # Block cipher without iv
            return self.module.new(a2b_hex(self.key), self.mode, **params)
        else:
            # Block cipher with iv
            return self.module.new(a2b_hex(self.key), self.mode, a2b_hex(self.iv), **params)

    def runTest(self):
        plaintext = a2b_hex(self.plaintext)
        ciphertext = a2b_hex(self.ciphertext)

        ct1 = b2a_hex(self._new().encrypt(plaintext))
        pt1 = b2a_hex(self._new().decrypt(ciphertext))
        ct2 = b2a_hex(self._new().encrypt(plaintext))
        pt2 = b2a_hex(self._new().decrypt(ciphertext))

        self.assertEqual(self.ciphertext, ct1)  # encrypt
        self.assertEqual(self.ciphertext, ct2)  # encrypt (second time)
        self.assertEqual(self.plaintext, pt1)   # decrypt
        self.assertEqual(self.plaintext, pt2)   # decrypt (second time)

class CipherStreamingSelfTest(CipherSelfTest):

    def shortDescription(self):
        desc = self.module_name
        if self.mode is not None:
            desc += " in %s mode" % (self.mode_name,)
        return "%s should behave like a stream cipher" % (desc,)

    def runTest(self):
        plaintext = a2b_hex(self.plaintext)
        ciphertext = a2b_hex(self.ciphertext)

        # The cipher should work like a stream cipher

        # Test counter mode encryption, 3 bytes at a time
        ct3 = []
        cipher = self._new()
        for i in range(0, len(plaintext), 3):
            ct3.append(cipher.encrypt(plaintext[i:i+3]))
        ct3 = b2a_hex("".join(ct3))
        self.assertEqual(self.ciphertext, ct3)  # encryption (3 bytes at a time)

        # Test counter mode decryption, 3 bytes at a time
        pt3 = []
        cipher = self._new()
        for i in range(0, len(ciphertext), 3):
            pt3.append(cipher.encrypt(ciphertext[i:i+3]))
        pt3 = b2a_hex("".join(pt3))
        self.assertEqual(self.plaintext, pt3)  # decryption (3 bytes at a time)

class CTRSegfaultTest(unittest.TestCase):

    def __init__(self, module, params):
        unittest.TestCase.__init__(self)
        self.module = module
        self.key = params['key']
        self.module_name = params.get('module_name', None)

    def shortDescription(self):
        return """Regression test: %s.new(key, %s.MODE_CTR) should raise TypeError, not segfault""" % (self.module_name, self.module_name)

    def runTest(self):
        self.assertRaises(TypeError, self.module.new, a2b_hex(self.key), self.module.MODE_CTR)

class CTRWraparoundTest(unittest.TestCase):

    def __init__(self, module, params):
        unittest.TestCase.__init__(self)
        self.module = module
        self.key = params['key']
        self.module_name = params.get('module_name', None)

    def shortDescription(self):
        return """Regression test: %s with MODE_CTR should raise OverflowError on wraparound when shortcut used""" % (self.module_name,)

    def runTest(self):
        from Crypto.Util import Counter

        for disable_shortcut in (0, 1): # (False, True) Test CTR-mode shortcut and PyObject_CallObject code paths
            for little_endian in (0, 1): # (False, True) Test both endiannesses
                ctr = Counter.new(8*self.module.block_size, initial_value=2L**(8*self.module.block_size)-1, little_endian=little_endian, disable_shortcut=disable_shortcut)
                cipher = self.module.new(a2b_hex(self.key), self.module.MODE_CTR, counter=ctr)
                block = "\x00" * self.module.block_size
                cipher.encrypt(block)
                self.assertRaises(OverflowError, cipher.encrypt, block)

class CFBSegmentSizeTest(unittest.TestCase):

    def __init__(self, module, params):
        unittest.TestCase.__init__(self)
        self.module = module
        self.key = params['key']
        self.description = params['description']

    def shortDescription(self):
        return self.description

    def runTest(self):
        """Regression test: m.new(key, m.MODE_CFB, segment_size=N) should require segment_size to be a multiple of 8 bits"""
        for i in range(1, 8):
            self.assertRaises(ValueError, self.module.new, a2b_hex(self.key), self.module.MODE_CFB, segment_size=i)
        self.module.new(a2b_hex(self.key), self.module.MODE_CFB, segment_size=8) # should succeed

def make_block_tests(module, module_name, test_data):
    tests = []
    extra_tests_added = 0
    for i in range(len(test_data)):
        row = test_data[i]

        # Build the "params" dictionary
        params = {'mode': 'ECB'}
        if len(row) == 3:
            (params['plaintext'], params['ciphertext'], params['key']) = row
        elif len(row) == 4:
            (params['plaintext'], params['ciphertext'], params['key'], params['description']) = row
        elif len(row) == 5:
            (params['plaintext'], params['ciphertext'], params['key'], params['description'], extra_params) = row
            params.update(extra_params)
        else:
            raise AssertionError("Unsupported tuple size %d" % (len(row),))

        # Build the display-name for the test
        p2 = params.copy()
        p_key = _extract(p2, 'key')
        p_plaintext = _extract(p2, 'plaintext')
        p_ciphertext = _extract(p2, 'ciphertext')
        p_description = _extract(p2, 'description', None)
        p_mode = p2.get('mode', 'ECB')
        if p_mode == 'ECB':
            _extract(p2, 'mode', 'ECB')

        if p_description is not None:
            description = p_description
        elif p_mode == 'ECB' and not p2:
            description = "p=%s, k=%s" % (p_plaintext, p_key)
        else:
            description = "p=%s, k=%s, %r" % (p_plaintext, p_key, p2)
        name = "%s #%d: %s" % (module_name, i+1, description)
        params['description'] = name
        params['module_name'] = module_name

        # Add extra test(s) to the test suite before the current test
        if not extra_tests_added:
            tests += [
                CTRSegfaultTest(module, params),
                CTRWraparoundTest(module, params),
                CFBSegmentSizeTest(module, params),
            ]
            extra_tests_added = 1

        # Add the current test to the test suite
        tests.append(CipherSelfTest(module, params))

        # When using CTR mode, test that the interface behaves like a stream cipher
        if p_mode == 'CTR':
            tests.append(CipherStreamingSelfTest(module, params))

        # When using CTR mode, test the non-shortcut code path.
        if p_mode == 'CTR' and not params.has_key('ctr_class'):
            params2 = params.copy()
            params2['description'] += " (shortcut disabled)"
            ctr_params2 = params.get('ctr_params', {}).copy()
            params2['ctr_params'] = ctr_params2
            if not params2['ctr_params'].has_key('disable_shortcut'):
                params2['ctr_params']['disable_shortcut'] = 1
            tests.append(CipherSelfTest(module, params2))
    return tests

def make_stream_tests(module, module_name, test_data):
    tests = []
    for i in range(len(test_data)):
        row = test_data[i]

        # Build the "params" dictionary
        params = {}
        if len(row) == 3:
            (params['plaintext'], params['ciphertext'], params['key']) = row
        elif len(row) == 4:
            (params['plaintext'], params['ciphertext'], params['key'], params['description']) = row
        elif len(row) == 5:
            (params['plaintext'], params['ciphertext'], params['key'], params['description'], extra_params) = row
            params.update(extra_params)
        else:
            raise AssertionError("Unsupported tuple size %d" % (len(row),))

        # Build the display-name for the test
        p2 = params.copy()
        p_key = _extract(p2, 'key')
        p_plaintext = _extract(p2, 'plaintext')
        p_ciphertext = _extract(p2, 'ciphertext')
        p_description = _extract(p2, 'description', None)

        if p_description is not None:
            description = p_description
        elif not p2:
            description = "p=%s, k=%s" % (p_plaintext, p_key)
        else:
            description = "p=%s, k=%s, %r" % (p_plaintext, p_key, p2)
        name = "%s #%d: %s" % (module_name, i+1, description)
        params['description'] = name
        params['module_name'] = module_name

        # Add the test to the test suite
        tests.append(CipherSelfTest(module, params))
        tests.append(CipherStreamingSelfTest(module, params))
    return tests

# vim:set ts=4 sw=4 sts=4 expandtab:
