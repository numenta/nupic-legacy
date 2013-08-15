# -*- coding: utf-8 -*-
#
#  SelfTest/PublicKey/test_importKey.py: Self-test for importing RSA keys
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

__revision__ = "$Id$"

import unittest

from Crypto.PublicKey import RSA
from Crypto.SelfTest.st_common import *
from Crypto.SelfTest.st_common import list_test_cases, a2b_hex, b2a_hex

class ImportKeyTests(unittest.TestCase):

	# 512-bit RSA key generated with openssl
	rsaKeyPEM = '''-----BEGIN RSA PRIVATE KEY-----
MIIBOwIBAAJBAL8eJ5AKoIsjURpcEoGubZMxLD7+kT+TLr7UkvEtFrRhDDKMtuII
q19FrL4pUIMymPMSLBn3hJLe30Dw48GQM4UCAwEAAQJACUSDEp8RTe32ftq8IwG8
Wojl5mAd1wFiIOrZ/Uv8b963WJOJiuQcVN29vxU5+My9GPZ7RA3hrDBEAoHUDPrI
OQIhAPIPLz4dphiD9imAkivY31Rc5AfHJiQRA7XixTcjEkojAiEAyh/pJHks/Mlr
+rdPNEpotBjfV4M4BkgGAA/ipcmaAjcCIQCHvhwwKVBLzzTscT2HeUdEeBMoiXXK
JACAr3sJQJGxIQIgarRp+m1WSKV1MciwMaTOnbU7wxFs9DP1pva76lYBzgUCIQC9
n0CnZCJ6IZYqSt0H5N7+Q+2Ro64nuwV/OSQfM6sBwQ==
-----END RSA PRIVATE KEY-----'''

	rsaPublicKeyPEM = '''-----BEGIN PUBLIC KEY-----
MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAL8eJ5AKoIsjURpcEoGubZMxLD7+kT+T
Lr7UkvEtFrRhDDKMtuIIq19FrL4pUIMymPMSLBn3hJLe30Dw48GQM4UCAwEAAQ==
-----END PUBLIC KEY-----'''

	rsaKeyDER = a2b_hex(
	'''3082013b020100024100bf1e27900aa08b23511a5c1281ae6d93312c3efe
	913f932ebed492f12d16b4610c328cb6e208ab5f45acbe2950833298f312
	2c19f78492dedf40f0e3c190338502030100010240094483129f114dedf6
	7edabc2301bc5a88e5e6601dd7016220ead9fd4bfc6fdeb75893898ae41c
	54ddbdbf1539f8ccbd18f67b440de1ac30440281d40cfac839022100f20f
	2f3e1da61883f62980922bd8df545ce407c726241103b5e2c53723124a23
	022100ca1fe924792cfcc96bfab74f344a68b418df578338064806000fe2
	a5c99a023702210087be1c3029504bcf34ec713d877947447813288975ca
	240080af7b094091b12102206ab469fa6d5648a57531c8b031a4ce9db53b
	c3116cf433f5a6f6bbea5601ce05022100bd9f40a764227a21962a4add07
	e4defe43ed91a3ae27bb057f39241f33ab01c1
	'''.replace(" ",""))

	rsaPublicKeyDER = a2b_hex(
	'''305c300d06092a864886f70d0101010500034b003048024100bf1e27900a
	a08b23511a5c1281ae6d93312c3efe913f932ebed492f12d16b4610c328c
	b6e208ab5f45acbe2950833298f3122c19f78492dedf40f0e3c190338502
	03010001
	'''.replace(" ",""))

	n = long('BF 1E 27 90 0A A0 8B 23 51 1A 5C 12 81 AE 6D 93 31 2C 3E FE 91 3F 93 2E BE D4 92 F1 2D 16 B4 61 0C 32 8C B6 E2 08 AB 5F 45 AC BE 29 50 83 32 98 F3 12 2C 19 F7 84 92 DE DF 40 F0 E3 C1 90 33 85'.replace(" ",""),16)
	e = 65537L
	d = long('09 44 83 12 9F 11 4D ED F6 7E DA BC 23 01 BC 5A 88 E5 E6 60 1D D7 01 62 20 EA D9 FD 4B FC 6F DE B7 58 93 89 8A E4 1C 54 DD BD BF 15 39 F8 CC BD 18 F6 7B 44 0D E1 AC 30 44 02 81 D4 0C FA C8 39'.replace(" ",""),16)
	p = long('00 F2 0F 2F 3E 1D A6 18 83 F6 29 80 92 2B D8 DF 54 5C E4 07 C7 26 24 11 03 B5 E2 C5 37 23 12 4A 23'.replace(" ",""),16)
	q = long('00 CA 1F E9 24 79 2C FC C9 6B FA B7 4F 34 4A 68 B4 18 DF 57 83 38 06 48 06 00 0F E2 A5 C9 9A 02 37'.replace(" ",""),16)
	coeff = long('00 BD 9F 40 A7 64 22 7A 21 96 2A 4A DD 07 E4 DE FE 43 ED 91 A3 AE 27 BB 05 7F 39 24 1F 33 AB 01 C1'.replace(" ",""),16)

	def testImportKey1(self):
		key = RSA.importKey(self.rsaKeyDER)
		self.failUnless(key.has_private())
		self.assertEqual(key.n, self.n)
		self.assertEqual(key.e, self.e)
		self.assertEqual(key.d, self.d)
		self.assertEqual(key.p, self.p)
		self.assertEqual(key.q, self.q)
		self.assertEqual(key.u, self.coeff)

	def testImportKey2(self):
		key = RSA.importKey(self.rsaPublicKeyDER)
		self.failIf(key.has_private())
		self.assertEqual(key.n, self.n)
		self.assertEqual(key.e, self.e)

	def testImportKey3(self):
		key = RSA.importKey(self.rsaKeyPEM)
		self.failUnless(key.has_private())
		self.assertEqual(key.n, self.n)
		self.assertEqual(key.e, self.e)
		self.assertEqual(key.d, self.d)
		self.assertEqual(key.p, self.p)
		self.assertEqual(key.q, self.q)
		self.assertEqual(key.u, self.coeff)

	def testImportKey4(self):
		key = RSA.importKey(self.rsaPublicKeyPEM)
		self.failIf(key.has_private())
		self.assertEqual(key.n, self.n)
		self.assertEqual(key.e, self.e)

	###
	def testExportKey1(self):
		key = RSA.construct([self.n, self.e, self.d, self.p, self.q, self.coeff])
		derKey = key.exportKey("DER")
		self.assertEqual(derKey, self.rsaKeyDER)

	def testExportKey2(self):
		key = RSA.construct([self.n, self.e])
		derKey = key.exportKey("DER")
		self.assertEqual(derKey, self.rsaPublicKeyDER)

	def testExportKey3(self):
		key = RSA.construct([self.n, self.e, self.d, self.p, self.q, self.coeff])
		pemKey = key.exportKey("PEM")
		self.assertEqual(pemKey, self.rsaKeyPEM)

	def testExportKey4(self):
		key = RSA.construct([self.n, self.e])
		pemKey = key.exportKey("PEM")
		self.assertEqual(pemKey, self.rsaPublicKeyPEM)

if __name__ == '__main__':
    unittest.main()

def get_tests(config={}):
    tests = []
    tests += list_test_cases(ImportKeyTests)
    return tests

if __name__ == '__main__':
    suite = lambda: unittest.TestSuite(get_tests())
    unittest.main(defaultTest='suite')

# vim:set ts=4 sw=4 sts=4 expandtab:
