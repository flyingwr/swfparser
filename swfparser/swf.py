from ._abc import ABC
from .reader import ByteReader
from .writer import ByteWriter

from concurrent.futures import ProcessPoolExecutor

import struct
import zlib

class SWFParser:
	def __init__(self, path: str):
		self.raw: bytes
		with open(path, "rb") as f:
			self.raw = f.read()

		self.abcs: dict[str, ABC] = {}
		self.binary_data: dict[int, bytes] = {}
		self.symbols: dict[int, str] = {}

		self.tags: list[tuple[int, bytes]] = []

		self.reader: ByteReader = ByteReader(self._maybe_decompress(self.raw))
		self.writer: ByteWriter = None

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
		self.signature = self.reader.read_bytes(3)
		self.version = self.reader.read_u8()
		self.reader.read_u32() # length

		self.rect_data = self._read_rect()
		self.frame_rate = self.reader.read_u16()
		self.frame_count = self.reader.read_u16()

		# SWF tags
		while True:
			record = self.reader.read_u16()
			tag_code = record >> 6
			tag_len  = record & 0x3f
			if tag_len == 0x3f:
				tag_len = self.reader.read_u32()

			data = self.reader.read_bytes(tag_len)

			if tag_code == 0x52: # DoABC tag
				data = self._handle_doabc(data)
			elif tag_code == 0x57: # DefineBinaryData tag
				data = self._handle_binary_data(data)
			elif tag_code == 0x4C: # SymbolClass tag
				data = self._handle_symbol(data)

			self.tags.append((tag_code, data))

			if tag_code == 0: # END tag
				break

	def write(self, path: str, compress: bool | None = None):
		self.writer = ByteWriter()

		_compress = (self.signature == b"CWS") if compress is None else bool(compress)
		signature = b"CWS" if _compress else b"FWS"

		self.writer.write_bytes(signature)
		self.writer.write_u8(self.version)
		self.writer.write_u32(0) # swf length will be updated later
		self.writer.write_u8(self.rect_data[0]).write_bytes(self.rect_data[1])
		self.writer.write_u16(self.frame_rate).write_u16(self.frame_count)

		# SWF tags
		for tag_code, data in self.tags:
			if isinstance(data, ABC):
				data = bytes(data.write().buf)

			record  = tag_code << 6
			tag_len = len(data)
			if tag_len < 0x3f:
				record |= tag_len
				self.writer.write_u16(record)
			else:
				record |= 0x3f
				self.writer.write_u16(record)
				self.writer.write_u32(tag_len)
			self.writer.write_bytes(data)

		# fix swf length
		swf_len = len(self.writer.buf)
		struct.pack_into("<I", self.writer.buf, 4, swf_len)

		if _compress:
			header = self.writer.buf[:8]
			header[:3].replace(b"F", b"C")

			body = self.writer.buf[8:]
			comp = zlib.compress(body)
			
			self.writer.clear()
			self.writer.write_bytes(header + comp)

		with open(path, "wb") as f:
			f.write(self.writer.buf)
	
	def _read_rect(self) -> tuple[int, bytes]:
		first = self.reader.read_u8()
		nbits = first >> 3
		total_bits = 5 + nbits * 4
		total_bytes = (total_bits + 7) // 8 - 1
		return first, self.reader.read_bytes(total_bytes)

	def _handle_binary_data(self, data: bytes) -> bytearray:
		r = ByteReader(data)
		tag = r.read_u16() # tag
		r.read_u32() # reserved bytes
		data = r.read_bytes(len(data) - r.pos)

		self.binary_data[tag] = data

		return r.buf

	def _handle_symbol(self, data: bytes) -> bytearray:
		r = ByteReader(data)
		count = r.read_u16()
		for _ in range(count):
			tag = r.read_u16()
			name = r.read_sstring()
			self.symbols[tag] = name

		return r.buf

	def _handle_doabc(self, data: bytes) -> ABC:
		r     = ByteReader(data)
		flags = r.read_u32() # flags
		name  = r.read_sstring()

		abc_data = r.read_bytes(len(data) - r.pos)
		self.abcs[name] = abc = ABC(name, flags, abc_data)
		abc.read()

		return abc