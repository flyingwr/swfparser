import struct

class ByteReader:
	def __init__(self, data: bytes):
		self.buf = bytearray(data)
		self.pos = 0

	def read_u8(self) -> int:
		val = self.buf[self.pos]
		self.pos += 1
		return val

	def read_u16(self) -> int:
		val = struct.unpack_from('<H', self.buf, self.pos)[0]
		self.pos += 2
		return val
	
	def read_s24(self) -> int:
		return int.from_bytes(self.read_bytes(3), "little")

	def read_u32(self) -> int:
		val = struct.unpack_from('<I', self.buf, self.pos)[0]
		self.pos += 4
		return val

	def read_d(self) -> float:
		val = struct.unpack_from('<d', self.buf, self.pos)[0]
		self.pos += 8
		return val

	def read_bytes(self, n: int) -> bytes:
		b = self.buf[self.pos:self.pos + n]
		self.pos += n
		return b

	def read_leb128(self) -> int:
		result = 0
		shift = 0

		while True:
			byte = self.read_u8()
			result |= (byte & 0x7F) << shift

			shift += 7
			
			if not (byte & 0x80) or shift == 35:
				break
			
		return result

	def read_sleb128(self) -> int: # S32
		result = self.read_leb128()
		if result & (1 << 31):
			result -= 1 << 32
		return result
	
	def read_string(self) -> str:
		length = self.read_leb128()
		raw = self.read_bytes(length)
		return raw.decode()

	def read_sstring(self) -> str:
		start = self.pos
		while self.buf[self.pos] != 0:
			self.pos += 1
		self.pos += 1
		return self.buf[start:self.pos].decode().rstrip("\x00")