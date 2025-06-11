import struct

_DOUBLE = struct.Struct("<d")
_U16 = struct.Struct("<H")
_U32 = struct.Struct("<I")

class ByteReader:
	def __init__(self, data: bytes | bytearray | memoryview):
		self.buf = memoryview(data)
		self.pos = 0

	def __len__(self):
		return len(self.buf)

	def read_u8(self) -> int:
		val = self.buf[self.pos]
		self.pos += 1
		return val

	def read_u16(self) -> int:
		val = _U16.unpack_from(self.buf, self.pos)[0]
		self.pos += 2
		return val
	
	def read_s24(self) -> int:
		return int.from_bytes(self.read_bytes(3), "little", signed=True)

	def read_u32(self) -> int:
		val = _U32.unpack_from(self.buf, self.pos)[0]
		self.pos += 4
		return val

	def read_d(self) -> float:
		val = _DOUBLE.unpack_from(self.buf, self.pos)[0]
		self.pos += 8
		return val

	def read_bytes(self, n: int) -> memoryview:
		mv = self.buf[self.pos:self.pos + n]
		self.pos += n
		return mv

	def read_leb128(self) -> int:
		buf = self.buf
		pos = self.pos

		result = 0
		shift = 0

		while True:
			byte = buf[pos]
			pos += 1

			result |= (byte & 0x7F) << shift

			shift += 7
			
			if not (byte & 0x80) or shift == 35:
				break
		
		self.pos = pos
		return result

	def read_sleb128(self) -> int: # S32
		result = self.read_leb128()
		if result & (1 << 31):
			result -= 1 << 32
		return result
	
	def read_string(self) -> str:
		length = self.read_leb128()
		raw = self.read_bytes(length)
		return raw.tobytes().decode()

	def read_sstring(self) -> str:
		start = self.pos
		while self.buf[self.pos] != 0:
			self.pos += 1
		self.pos += 1
		return self.buf[start:self.pos].tobytes().decode().rstrip("\x00")