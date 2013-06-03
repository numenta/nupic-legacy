# -*- coding: ascii -*-
#
#  Util/asn1.py : Minimal support for ASN.1 DER binary encoding.
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

from Crypto.Util.number import long_to_bytes, bytes_to_long

__all__ = [ 'DerObject', 'DerInteger', 'DerSequence' ]

class DerObject:
	typeTags = { 'SEQUENCE':'\x30', 'BIT STRING':'\x03', 'INTEGER':'\x02' }

	def __init__(self, ASN1Type=None):
		self.typeTag = self.typeTags.get(ASN1Type, ASN1Type)
		self.payload = ''

	def _lengthOctets(self, payloadLen):
		'''
		Return an octet string that is suitable for the BER/DER
		length element if the relevant payload is of the given
		size (in bytes).
		'''
		if payloadLen>127:
			encoding = long_to_bytes(payloadLen)
			return chr(len(encoding)+128) + encoding
		return chr(payloadLen)

	def encode(self):
		return self.typeTag + self._lengthOctets(len(self.payload)) + self.payload	

	def _decodeLen(self, idx, str):
		'''
		Given a string and an index to a DER LV,
		this function returns a tuple with the length of V
		and an index to the first byte of it.
		'''
		length = ord(str[idx])
		if length<=127:
			return (length,idx+1)
		else:
			payloadLength = bytes_to_long(str[idx+1:idx+1+(length & 0x7F)])
			if payloadLength<=127:
				raise ValueError("Not a DER length tag.")
			return (payloadLength, idx+1+(length & 0x7F))

	def decode(self, input, noLeftOvers=0):
		try:
			self.typeTag = input[0]
			if (ord(self.typeTag) & 0x1F)==0x1F:
				raise ValueError("Unsupported DER tag")
			(length,idx) = self._decodeLen(1,input)
			if noLeftOvers and len(input) != (idx+length):
				raise ValueError("Not a DER structure")
			self.payload = input[idx:idx+length]
		except IndexError:
			raise ValueError("Not a valid DER SEQUENCE.")
		return idx+length

class DerInteger(DerObject):
	def __init__(self, value = 0):
		DerObject.__init__(self, 'INTEGER')
		self.value = value

	def encode(self):
		self.payload = long_to_bytes(self.value)
		if ord(self.payload[0])>127:
			self.payload = '\x00' + self.payload
		return DerObject.encode(self)

	def decode(self, input, noLeftOvers=0):
		tlvLength = DerObject.decode(self, input,noLeftOvers)
		if ord(self.payload[0])>127:
			raise ValueError ("Negative INTEGER.")
		self.value = bytes_to_long(self.payload)
		return tlvLength
				
class DerSequence(DerObject):
	def __init__(self):
		DerObject.__init__(self, 'SEQUENCE')
		self._seq = []
	def __delitem__(self, n):
		del self._seq[n]
	def __getitem__(self, n):
		return self._seq[n]
	def __setitem__(self, key, value):
		self._seq[key] = value	
	def __setslice__(self,i,j,sequence):
		self._seq[i:j] = sequence
	def __delslice__(self,i,j):
		del self._seq[i:j]
	def __getslice__(self, i, j):
		return self._seq[max(0, i):max(0, j)]
	def __len__(self):
		return len(self._seq)
	def append(self, item):
		return self._seq.append(item)

	def hasOnlyInts(self):
		if not self._seq: return 0
		test = 0
		for item in self._seq:
			try:
				test += item
			except TypeError:
				return 0
		return 1

	def encode(self):
		'''
		Return the DER encoding for the ASN.1 SEQUENCE containing
		the non-negative integers and longs added to this object.
		'''
		self.payload = ''
		for item in self._seq:
			try:
				self.payload += item
			except:
				try:
					self.payload += DerInteger(item).encode()
				except:
					raise ValueError("Trying to DER encode an unknown object")
		return DerObject.encode(self)

	def decode(self, input,noLeftOvers=0):
		'''
		This function decodes the given string into a sequence of
		ASN.1 objects. Yet, we only know about unsigned INTEGERs.
		Any other type is stored as its rough TLV. In the latter
		case, the correctectness of the TLV is not checked.
		'''
		self._seq = []
		try:
			tlvLength = DerObject.decode(self, input,noLeftOvers)
			if self.typeTag!=self.typeTags['SEQUENCE']:
				raise ValueError("Not a DER SEQUENCE.")
			# Scan one TLV at once
			idx = 0
			while idx<len(self.payload):
				typeTag = self.payload[idx]
				if typeTag==self.typeTags['INTEGER']:
					newInteger = DerInteger()
					idx += newInteger.decode(self.payload[idx:])
					self._seq.append(newInteger.value)
				else:
					itemLen,itemIdx = self._decodeLen(idx+1,self.payload)
					self._seq.append(self.payload[idx:itemIdx+itemLen])
					idx = itemIdx + itemLen
		except IndexError:
			raise ValueError("Not a valid DER SEQUENCE.")
		return tlvLength

