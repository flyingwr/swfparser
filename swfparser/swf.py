from .reader import ByteReader
from ._abc import ABCParser, TRAIT_METHOD, NEED_REST

import zlib

class SWFParser:
	def __init__(self, path: str):
		self.raw: bytes
		with open(path, "rb") as f:
			self.raw = f.read()

		self.abcs: dict[str, ABCParser] = {}
		self.binary_data: dict[int, bytes] = {}
		self.symbols: dict[int, str] = {}

		self.reader: ByteReader = ByteReader(self._maybe_decompress(self.raw))

		self.hash_script: str = ""

	def _maybe_decompress(self, data: bytes) -> bytes:
		sig = data[:3]
		if sig == b'CWS':
			# SWF compressed with zlib from 8th byte
			header = data[:8]
			comp = data[8:]
			return header[:3].replace(b'C', b'F') + header[3:] + zlib.decompress(comp)
		elif sig == b'FWS':
			return data
		else:
			raise ValueError("Unsupported SWF signature: %s" % sig)

	def parse(self):
		self.reader.read_bytes(3) # sig
		self.reader.read_u8() # version
		self.reader.read_u32() # length

		self._skip_rect()
		self.reader.read_u16()  # FrameRate
		self.reader.read_u16()  # FrameCount

		# SWF tags
		while True:
			record = self.reader.read_u16()
			tag_code = record >> 6
			tag_len  = record & 0x3f
			if tag_len == 0x3f:
				tag_len = self.reader.read_u32()

			data = self.reader.read_bytes(tag_len)

			if tag_code == 0x52: # DoABC tag
				self._handle_doabc(data)
			elif tag_code == 0x57: # DefineBinaryData tag
				self._handle_binary_data(data)
			elif tag_code == 0x4C: # SymbolClass tag
				self._handle_symbol(data)

			if tag_code == 0: # END tag
				break
		
	def _skip_rect(self):
		first = self.reader.read_u8()
		nbits = first >> 3
		total_bits = 5 + nbits * 4
		total_bytes = (total_bits + 7) // 8 - 1
		self.reader.read_bytes(total_bytes)

	def _handle_binary_data(self, data: bytes):
		r = ByteReader(data)
		tag = r.read_u16() # tag
		r.read_u32() # reserved bytes
		data = r.read_bytes(len(data) - r.pos)

		self.binary_data[tag] = data

	def _handle_symbol(self, data: bytes):
		r = ByteReader(data)
		count = r.read_u16()
		for _ in range(count):
			tag = r.read_u16()
			name = r.read_sstring()
			self.symbols[tag] = name

	def _handle_doabc(self, data: bytes):
		r = ByteReader(data)
		flags = r.read_u32()
		name  = r.read_sstring()
		abc_data = r.read_bytes(len(data) - r.pos)
		# print(f"DoABC name={name}, flags={flags}, size={len(abc_data)}")
		abc = ABCParser(abc_data)
		abc.parse()

		self.abcs[name] = abc