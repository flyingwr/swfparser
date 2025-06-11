from dataclasses import dataclass, field
from enum import Enum

@dataclass
class Instruction:
    opcode: "Opcode"
    
    address: int = -1

    args: list[int] = field(default_factory=lambda: [])
    targets: list[int] = field(default_factory=lambda: [])

    def __repr__(self):
        return f"Instruction(name='{self.opcode.name}', opcode=0x{self.opcode.value[0]:02x}, args={self.args})"
    
@dataclass
class Stack:
    current_instruction: Instruction = None

    code_len: int = 0
    index: int = -1

    instructions: list[Instruction] = field(default_factory=lambda: [])

    def add(self, instr: Instruction):
        self.instructions.append(instr)

    def back(self, i : int = 1) -> Instruction | None:
        if self.index - i < 0:
            return None
        
        self.index -= i
        self.current_instruction = self.instructions[self.index]
        return self.current_instruction

    def next(self, i: int = 1) -> Instruction | None:
        if self.index + i > len(self.instructions) - 1:
            return None
        
        self.index += i
        self.current_instruction = self.instructions[self.index]
        return self.current_instruction
    
    def reset(self) -> "Stack":
        self.index = -1
        self.current_instruction = None
        return self
    
class Opcode(Enum):
    # instruction name = opcode[, args]
    add = 0xa0,
    add_d = 0x9B,
    add_i = 0xC5,
    applytype = 0x53, "u30",
    astype = 0x86, "u30",
    astypelate = 0x87,
    bitand = 0xa8,
    bitnot = 0x97,
    bitor = 0xa9,
    bitxor = 0xAA,
    bkpt = 0x01,
    bkptline = 0xF2, "u30",
    call = 0x41, "u30",
    callinterface = 0x4D, "u30", "u30",
    callmethod = 0x43, "u30", "u30",
    callproperty = 0x46, "u30", "u30",
    callproplex = 0x4C, "u30", "u30",
    callpropvoid = 0x4f, "u30", "u30",
    callstatic = 0x44, "u30", "u30",
    callsuper = 0x45, "u30", "u30",
    callsuperid = 0x4B,
    callsupervoid = 0x4e, "u30", "u30",
    checkfilter = 0x78,
    coerce = 0x80, "u30",
    coerce_a = 0x82,
    coerce_b = 0x81,
    coerce_d = 0x84,
    coerce_i = 0x83,
    coerce_o = 0x89,
    coerce_s = 0x85,
    coerce_u = 0x88,
    concat = 0x9A,
    construct = 0x42, "u30",
    constructprop = 0x4a, "u30", "u30",
    constructsuper = 0x49, "u30",
    convert_b = 0x76,
    convert_d = 0x75,
    convert_i = 0x73,
    convert_o = 0x77,
    convert_s = 0x70,
    convert_u = 0x74,
    debug = 0xEF, "u8", "u30", "u8", "u30",
    debugfile = 0xF1, "u30",
    debugline = 0xF0, "u30",
    declocal = 0x94, "u30",
    declocal_i = 0xC3, "u30",
    decrement = 0x93,
    decrement_i = 0xc1,
    deleteproperty = 0x6a, "u30",
    deletepropertylate = 0x6B,
    divide = 0xa3,
    dup = 0x2a,
    dxns = 0x06, "u30",
    dxnslate = 0x07,
    equals = 0xab,
    esc_xattr = 0x72,
    esc_xelem = 0x71,
    finddef = 0x5F, "u30",
    findproperty = 0x5e, "u30",
    findpropglobal = 0x5c, "u30",
    findpropglobalstrict = 0x5b, "u30",
    findpropstrict = 0x5d, "u30",
    getdescendants = 0x59, "u30",
    getglobalscope = 0x64,
    getglobalslot = 0x6E, "u30",
    getlex = 0x60, "u30",
    getlocal = 0x62, "u30",
    getlocal_0 = 0xd0,
    getlocal_1 = 0xd1,
    getlocal_2 = 0xd2,
    getlocal_3 = 0xd3,
    getouterscope = 0x67, "u30",
    getproperty = 0x66, "u30",
    getscopeobject = 0x65, "u8",
    getslot = 0x6c, "u30",
    getsuper = 0x04, "u30",
    greaterequals = 0xb0,
    greaterthan = 0xaf,
    hasnext = 0x1F,
    hasnext2 = 0x32, "u30", "u30",
    ifeq = 0x13, "s24",
    iffalse = 0x12, "s24",
    ifge = 0x18, "s24",
    ifgt = 0x17, "s24",
    ifle = 0x16, "s24",
    iflt = 0x15, "s24",
    ifne = 0x14, "s24",
    ifnge = 0x0f, "s24",
    ifngt = 0x0e, "s24",
    ifnle = 0x0d, "s24",
    ifnlt = 0x0c, "s24",
    ifstricteq = 0x19, "s24",
    ifstrictne = 0x1a, "s24",
    iftrue = 0x11, "s24",
    _in = 0xb4,
    inclocal = 0x92, "u30",
    inclocal_i = 0xc2, "u30",
    increment = 0x91,
    increment_i = 0xc0,
    initproperty = 0x68, "u30",
    instance_of = 0xB1,
    istype = 0xB2, "u30",
    istypelate = 0xb3,
    jump = 0x10, "s24",
    kill = 0x08, "u30",
    label = 0x09,
    lessequals = 0xae,
    lessthan = 0xad,
    lf32 = 0x38,
    lf64 = 0x39,
    li16 = 0x36,
    li32 = 0x37,
    li8 = 0x35,
    lookupswitch = 0x1b, "s24", "s24arr",
    lshift = 0xa5,
    modulo = 0xa4,
    multiply = 0xa2,
    multiply_i = 0xC7,
    negate = 0x90,
    negate_i = 0xC4,
    newactivation = 0x57,
    newarray = 0x56, "u30",
    newcatch = 0x5a, "u30",
    newclass = 0x58, "u30",
    newfunction = 0x40, "u30",
    newobject = 0x55, "u30",
    nextname = 0x1e,
    nextvalue = 0x23,
    nop = 0x02,
    _not = 0x96,
    pop = 0x29,
    popscope = 0x1d,
    pushbyte = 0x24, "u8",
    pushconstant = 0x22, "u30",
    pushdecimal = 0x33, "u30",
    pushdnan = 0x34,
    pushdouble = 0x2f, "u30",
    pushfalse = 0x27,
    pushint = 0x2d, "u30",
    pushnamespace = 0x31, "u30",
    pushnan = 0x28,
    pushnull = 0x20,
    pushscope = 0x30,
    pushshort = 0x25, "s32",
    pushstring = 0x2c, "u30",
    pushtrue = 0x26,
    pushuint = 0x2E, "u30",
    pushundefined = 0x21,
    pushwith = 0x1c,
    returnvalue = 0x48,
    returnvoid = 0x47,
    rshift = 0xa6,
    setglobalslot = 0x6F, "u30",
    setlocal = 0x63, "u30",
    setlocal_0 = 0xD4,
    setlocal_1 = 0xD5,
    setlocal_2 = 0xD6,
    setlocal_3 = 0xD7,
    setproperty = 0x61, "u30",
    setpropertylate = 0x69,
    setslot = 0x6d, "u30",
    setsuper = 0x05, "u30",
    sf32 = 0x3d,
    sf64 = 0x3e,
    si16 = 0x3b,
    si32 = 0x3c,
    si8 = 0x3a,
    strictequals = 0xac,
    subtract = 0xa1,
    subtract_i = 0xC6,
    swap = 0x2b,
    sxi1 = 0x50,
    sxi16 = 0x52,
    sxi8 = 0x51,
    throw = 0x03,
    typeof = 0x95,
    urshift = 0xa7,
    unknown_7d = 0x7d,

    @classmethod
    def _missing_(cls, key) -> "Opcode":
        if isinstance(key, int):
            for member in cls:
                if member.value[0] == key:
                    return member
            return None
                
        for member in cls:
            if member.name == key:
                return member
        return None
    
    @classmethod
    def from_code(cls, code: int) -> "Opcode":
        try:
            return CODE_TO_OPCODE[code]
        except KeyError:
            CODE_TO_OPCODE[code] = member = cls._missing_(code)
            return member
    
CODE_TO_OPCODE = {m.value[0]: m for m in Opcode}