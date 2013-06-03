# HMAC.py - Implements the HMAC algorithm as described by RFC 2104.
#
# ===================================================================
# Portions Copyright (c) 2001, 2002, 2003 Python Software Foundation;
# All Rights Reserved
#
# This file contains code from the Python 2.2 hmac.py module (the
# "Original Code"), with modifications made after it was incorporated
# into PyCrypto (the "Modifications").
#
# To the best of our knowledge, the Python Software Foundation is the
# copyright holder of the Original Code, and has licensed it under the
# Python 2.2 license.  See the file LEGAL/copy/LICENSE.python-2.2 for
# details.
#
# The Modifications to this file are dedicated to the public domain.
# To the extent that dedication to the public domain is not available,
# everyone is granted a worldwide, perpetual, royalty-free,
# non-exclusive license to exercise all rights associated with the
# contents of this file for any purpose whatsoever.  No rights are
# reserved.
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


"""HMAC (Keyed-Hashing for Message Authentication) Python module.

Implements the HMAC algorithm as described by RFC 2104.

This is just a copy of the Python 2.2 HMAC module, modified to work when
used on versions of Python before 2.2.
"""

__revision__ = "$Id$"

__all__ = ['new', 'digest_size']

import string

from Crypto.Util.strxor import strxor_c

# The size of the digests returned by HMAC depends on the underlying
# hashing module used.
digest_size = None

class HMAC:
    """RFC2104 HMAC class.

    This supports the API for Cryptographic Hash Functions (PEP 247).
    """

    def __init__(self, key, msg = None, digestmod = None):
        """Create a new HMAC object.

        key:       key for the keyed hash object.
        msg:       Initial input for the hash, if provided.
        digestmod: A module supporting PEP 247. Defaults to the md5 module.
        """
        if digestmod == None:
            import MD5
            digestmod = MD5

        self.digestmod = digestmod
        self.outer = digestmod.new()
        self.inner = digestmod.new()
        try:
            self.digest_size = digestmod.digest_size
        except AttributeError:
            self.digest_size = len(self.outer.digest())

        blocksize = 64
        ipad = 0x36
        opad = 0x5C

        if len(key) > blocksize:
            key = digestmod.new(key).digest()

        key = key + chr(0) * (blocksize - len(key))
        self.outer.update(strxor_c(key, opad))
        self.inner.update(strxor_c(key, ipad))
        if (msg):
            self.update(msg)

##    def clear(self):
##        raise NotImplementedError, "clear() method not available in HMAC."

    def update(self, msg):
        """Update this hashing object with the string msg.
        """
        self.inner.update(msg)

    def copy(self):
        """Return a separate copy of this hashing object.

        An update to this copy won't affect the original object.
        """
        other = HMAC("")
        other.digestmod = self.digestmod
        other.inner = self.inner.copy()
        other.outer = self.outer.copy()
        return other

    def digest(self):
        """Return the hash value of this hashing object.

        This returns a string containing 8-bit data.  The object is
        not altered in any way by this function; you can continue
        updating the object after calling this function.
        """
        h = self.outer.copy()
        h.update(self.inner.digest())
        return h.digest()

    def hexdigest(self):
        """Like digest(), but returns a string of hexadecimal digits instead.
        """
        return "".join([string.zfill(hex(ord(x))[2:], 2)
                        for x in tuple(self.digest())])

def new(key, msg = None, digestmod = None):
    """Create a new hashing object and return it.

    key: The starting key for the hash.
    msg: if available, will immediately be hashed into the object's starting
    state.

    You can now feed arbitrary strings into the object using its update()
    method, and can ask for the hash value at any time by calling its digest()
    method.
    """
    return HMAC(key, msg, digestmod)

