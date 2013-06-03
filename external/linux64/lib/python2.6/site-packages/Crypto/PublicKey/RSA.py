# -*- coding: utf-8 -*-
#
#  PublicKey/RSA.py : RSA public key primitive
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

"""RSA public-key cryptography algorithm."""

__revision__ = "$Id$"

__all__ = ['generate', 'construct', 'error', 'importKey' ]

from Crypto.Util.python_compat import *

from Crypto.PublicKey import _RSA, _slowmath, pubkey
from Crypto import Random

from Crypto.Util.asn1 import DerObject, DerSequence
import binascii

try:
    from Crypto.PublicKey import _fastmath
except ImportError:
    _fastmath = None

class _RSAobj(pubkey.pubkey):
    keydata = ['n', 'e', 'd', 'p', 'q', 'u']

    def __init__(self, implementation, key):
        self.implementation = implementation
        self.key = key

    def __getattr__(self, attrname):
        if attrname in self.keydata:
            # For backward compatibility, allow the user to get (not set) the
            # RSA key parameters directly from this object.
            return getattr(self.key, attrname)
        else:
            raise AttributeError("%s object has no %r attribute" % (self.__class__.__name__, attrname,))

    def _encrypt(self, c, K):
        return (self.key._encrypt(c),)

    def _decrypt(self, c):
        #(ciphertext,) = c
        (ciphertext,) = c[:1]  # HACK - We should use the previous line
                               # instead, but this is more compatible and we're
                               # going to replace the Crypto.PublicKey API soon
                               # anyway.
        return self.key._decrypt(ciphertext)

    def _blind(self, m, r):
        return self.key._blind(m, r)

    def _unblind(self, m, r):
        return self.key._unblind(m, r)

    def _sign(self, m, K=None):
        return (self.key._sign(m),)

    def _verify(self, m, sig):
        #(s,) = sig
        (s,) = sig[:1]  # HACK - We should use the previous line instead, but
                        # this is more compatible and we're going to replace
                        # the Crypto.PublicKey API soon anyway.
        return self.key._verify(m, s)

    def has_private(self):
        return self.key.has_private()

    def size(self):
        return self.key.size()

    def can_blind(self):
        return True

    def can_encrypt(self):
        return True

    def can_sign(self):
        return True

    def publickey(self):
        return self.implementation.construct((self.key.n, self.key.e))

    def __getstate__(self):
        d = {}
        for k in self.keydata:
            try:
                d[k] = getattr(self.key, k)
            except AttributeError:
                pass
        return d

    def __setstate__(self, d):
        if not hasattr(self, 'implementation'):
            self.implementation = RSAImplementation()
        t = []
        for k in self.keydata:
            if not d.has_key(k):
                break
            t.append(d[k])
        self.key = self.implementation._math.rsa_construct(*tuple(t))

    def __repr__(self):
        attrs = []
        for k in self.keydata:
            if k == 'n':
                attrs.append("n(%d)" % (self.size()+1,))
            elif hasattr(self.key, k):
                attrs.append(k)
        if self.has_private():
            attrs.append("private")
        return "<%s @0x%x %s>" % (self.__class__.__name__, id(self), ",".join(attrs))

    def exportKey(self, format='PEM'):
	"""Export the RSA key. A string is returned
	with the encoded public or the private half
	under the selected format.

	format:		'DER' (PKCS#1) or 'PEM' (RFC1421)
	"""
	der = DerSequence()
	if self.has_private():
		keyType = "RSA PRIVATE"
		der[:] = [ 0, self.n, self.e, self.d, self.p, self.q,
			   self.d % (self.p-1), self.d % (self.q-1),
			   self.u ]
	else:
		keyType = "PUBLIC"
		der.append('\x30\x0D\x06\x09\x2A\x86\x48\x86\xF7\x0D\x01\x01\x01\x05\x00')
		bitmap = DerObject('BIT STRING')
		derPK = DerSequence()
		derPK[:] = [ self.n, self.e ]
		bitmap.payload = '\x00' + derPK.encode()
		der.append(bitmap.encode())
	if format=='DER':
		return der.encode()
	if format=='PEM':
		pem = "-----BEGIN %s KEY-----\n" % keyType
		binaryKey = der.encode()
		# Each BASE64 line can take up to 64 characters (=48 bytes of data)
		chunks = [ binascii.b2a_base64(binaryKey[i:i+48]) for i in range(0, len(binaryKey), 48) ]
		pem += ''.join(chunks)
		pem += "-----END %s KEY-----" % keyType
		return pem
	return ValueError("")

class RSAImplementation(object):
    def __init__(self, **kwargs):
        # 'use_fast_math' parameter:
        #   None (default) - Use fast math if available; Use slow math if not.
        #   True - Use fast math, and raise RuntimeError if it's not available.
        #   False - Use slow math.
        use_fast_math = kwargs.get('use_fast_math', None)
        if use_fast_math is None:   # Automatic
            if _fastmath is not None:
                self._math = _fastmath
            else:
                self._math = _slowmath

        elif use_fast_math:     # Explicitly select fast math
            if _fastmath is not None:
                self._math = _fastmath
            else:
                raise RuntimeError("fast math module not available")

        else:   # Explicitly select slow math
            self._math = _slowmath

        self.error = self._math.error

        # 'default_randfunc' parameter:
        #   None (default) - use Random.new().read
        #   not None       - use the specified function
        self._default_randfunc = kwargs.get('default_randfunc', None)
        self._current_randfunc = None

    def _get_randfunc(self, randfunc):
        if randfunc is not None:
            return randfunc
        elif self._current_randfunc is None:
            self._current_randfunc = Random.new().read
        return self._current_randfunc

    def generate(self, bits, randfunc=None, progress_func=None):
        if bits < 1024 or (bits & 0xff) != 0:
            # pubkey.getStrongPrime doesn't like anything that's not a multiple of 128 and > 512
            raise ValueError("RSA modulus length must be a multiple of 256 and > 1024")
        rf = self._get_randfunc(randfunc)
        obj = _RSA.generate_py(bits, rf, progress_func)    # TODO: Don't use legacy _RSA module
        key = self._math.rsa_construct(obj.n, obj.e, obj.d, obj.p, obj.q, obj.u)
        return _RSAobj(self, key)

    def construct(self, tup):
        key = self._math.rsa_construct(*tup)
        return _RSAobj(self, key)

    def _importKeyDER(self, externKey):
	der = DerSequence()
	der.decode(externKey, True)
	if len(der)==9 and der.hasOnlyInts() and der[0]==0:
		# ASN.1 RSAPrivateKey element
		del der[6:8]	# Remove d mod (p-1) and d mod (q-1)
		del der[0]	# Remove version
		return self.construct(der[:])
	if len(der)==2:
		# ASN.1 SubjectPublicKeyInfo element
		if der[0]=='\x30\x0D\x06\x09\x2A\x86\x48\x86\xF7\x0D\x01\x01\x01\x05\x00':
			bitmap = DerObject()
			bitmap.decode(der[1], True)
			if bitmap.typeTag=='\x03' and bitmap.payload[0]=='\x00':
				der.decode(bitmap.payload[1:], True)
				if len(der)==2 and der.hasOnlyInts():
					return self.construct(der[:])
	raise ValueError("RSA key format is not supported")

    def importKey(self, externKey):
	"""Import an RSA key (public or private half).

	externKey:	the RSA key to import, encoded as a string.
			The key can be in DER (PKCS#1) or in unencrypted
			PEM format (RFC1421).
	"""
	if externKey.startswith('-----'):
		# This is probably a PEM encoded key
		lines = externKey.replace(" ",'').split()
		der = binascii.a2b_base64(''.join(lines[1:-1]))
		return self._importKeyDER(der)
	if externKey[0]=='\x30':
		# This is probably a DER encoded key
		return self._importKeyDER(externKey)
	raise ValueError("RSA key format is not supported")

_impl = RSAImplementation()
generate = _impl.generate
construct = _impl.construct
importKey = _impl.importKey
error = _impl.error

# vim:set ts=4 sw=4 sts=4 expandtab:

