import struct

class ByteWriter:
    def __init__(self):
        self.buf = bytearray()

    def clear(self):
        self.buf *= 0

    def write_u8(self, v: int) -> 'ByteWriter':
        self.buf.append(v & 0xFF)
        return self

    def write_u16(self, v: int) -> 'ByteWriter':
        self.buf.extend(struct.pack("<H", v & 0xFFFF))
        return self
    
    def write_s24(self, v: int) -> 'ByteWriter':
        self.buf.extend((v & 0xFFFFFF).to_bytes(3, "little"))
        return self

    def write_u32(self, v: int) -> 'ByteWriter':
        self.buf.extend(struct.pack("<I", v & 0xFFFFFFFF))
        return self

    def write_d(self, v: int) -> 'ByteWriter':
        self.buf.extend(struct.pack("<d", v))
        return self

    def write_bytes(self, b: bytes) -> 'ByteWriter':
        self.buf.extend(b)
        return self
    
    def write_leb128(self, v: int) -> 'ByteWriter':
        while True:
            byte = v & 0x7F
            v >>= 7
            if (v == 0):
                self.buf.append(byte)
                break
            self.buf.append(byte | 0x80)
        return self
    
    def write_sleb128(self, v: int) -> 'ByteWriter': # S32
        if v & (1 << 31):
            v -= 1 << 32
        return self.write_leb128(v)
        
    def write_string(self, s: str) -> 'ByteWriter':
        return self.write_leb128(len(s.encode())).write_bytes(s.encode())
    
    def write_sstring(self, s: str) -> 'ByteWriter':
        self.buf.extend(s.encode() + b"\x00")
        return self