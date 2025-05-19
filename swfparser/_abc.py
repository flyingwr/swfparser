from .consts import *
from .instruction import Instruction, Opcode, Stack
from .reader import ByteReader
from .writer import ByteWriter

import struct

class ABCParser:
	def __init__(self, data: bytes):
		self.reader = ByteReader(data)

		self.method_info = []
		self.metadata = []
		self.instance_pool = []
		self.class_pool = []
		self.script_pool = []
		self.method_bodies = []

	def parse(self):
		self.reader.read_u16() # minor
		self.reader.read_u16() # major

		self._parse_constant_pool()
		self._parse_method_info()
		self._parse_metadata()
		self._parse_instances_and_classes()
		self._parse_scripts()
		self._parse_method_bodies()

	def __repr__(self) -> str:
		return (
			f"ABCParser constantpool: ints={len(self.int_pool)}, uints={len(self.uint_pool)}, \
"
			f"doubles={len(self.double_pool)}, strings={len(self.string_pool)}, \
"
			f"namespaces={len(self.namespace_pool)}, ns_sets={len(self.ns_set_pool)}, \
"
			f"multinames={len(self.multiname_pool)}, methods={len(self.method_info)}, \
"
			f"metadata={len(self.metadata)}, instances={len(self.instance_pool)}, \
"
			f"classes={len(self.class_pool)}, scripts={len(self.script_pool)}, \
"
			f"method_bodies={len(self.method_bodies)}"
		)

	def _parse_constant_pool(self):		
		int_count = self.reader.read_leb128()
		self.int_pool = [0]
		for _ in range(int_count - 1):
			self.int_pool.append(self.reader.read_sleb128())

		print(self.reader.buf[self.reader.pos:self.reader.pos + 256])

		uint_count = self.reader.read_leb128()
		self.uint_pool = [0]
		for _ in range(uint_count - 1):
			self.uint_pool.append(self.reader.read_leb128())

		double_count = self.reader.read_leb128()
		self.double_pool = [0.0]
		for _ in range(double_count - 1):
			raw = self.reader.read_bytes(8)
			self.double_pool.append(struct.unpack('<d', raw)[0])

		string_count = self.reader.read_leb128()
		self.string_pool = [""]
		for _ in range(string_count - 1):
			self.string_pool.append(self.reader.read_string())

		ns_count = self.reader.read_leb128()
		self.namespace_pool = [None]
		for _ in range(ns_count - 1):
			kind = self.reader.read_u8()
			name_index = self.reader.read_leb128()
			self.namespace_pool.append({
				'kind': kind,
				'name_index': name_index
			})

		ns_set_count = self.reader.read_leb128()
		self.ns_set_pool = [None]
		for _ in range(ns_set_count - 1):
			count = self.reader.read_leb128()
			indices = [self.reader.read_leb128() for _ in range(count)]
			self.ns_set_pool.append(indices)

		multiname_count = self.reader.read_leb128()
		self.multiname_pool = [None]
		for _ in range(multiname_count - 1):
			kind = self.reader.read_u8()
			entry = {'kind': kind}
			if kind in (CONSTANT_QName, CONSTANT_QNameA):
				entry['ns_index'] = self.reader.read_leb128()
				entry['name_index'] = self.reader.read_leb128()
			elif kind in (CONSTANT_RTQName, CONSTANT_RTQNameA):
				entry['name_index'] = self.reader.read_leb128()
			elif kind in (CONSTANT_RTQNameL, CONSTANT_RTQNameLA):
				# no additional data
				pass
			elif kind in (CONSTANT_Multiname, CONSTANT_MultinameA):
				entry['name_index'] = self.reader.read_leb128()
				entry['ns_set_index'] = self.reader.read_leb128()
			elif kind in (CONSTANT_MultinameL, CONSTANT_MultinameLA):
				entry['ns_set_index'] = self.reader.read_leb128()
			elif kind == CONSTANT_TypeName:
				entry['name_index'] = self.reader.read_leb128()
				param_count = self.reader.read_leb128()
				entry['param_types'] = [self.reader.read_leb128() for _ in range(param_count)]
			else:
				raise ValueError(f"Unknown multiname kind: {kind}")
			self.multiname_pool.append(entry)

	def _parse_method_info(self):
		count = self.reader.read_leb128()
		for _ in range(count):
			param_count = self.reader.read_leb128()
			return_type = self.multiname_pool[self.reader.read_leb128()]

			params = [self.multiname_pool[self.reader.read_leb128()] for _ in range(param_count)]

			name = self.string_pool[self.reader.read_leb128()]
			flags = self.reader.read_u8()

			entry = {
				"name": name,
				"flags": flags,
				"params": params,
				"return_type": return_type
			}

			if flags & HAS_OPTIONAL:
				option_count = self.reader.read_leb128()

				optional_params = []
				for _ in range(option_count):
					value = self.reader.read_leb128()
					kind = self.reader.read_u8()
					optional_params.append((value, kind))

				entry["optional_params"] = optional_params

			if flags & HAS_PARAM_NAMES:
				# ignore param names, their entries are not used by AVM2
				for _ in range(param_count):
					self.reader.read_leb128()

				flags &= ~HAS_PARAM_NAMES

			self.method_info.append(entry)

	def _parse_metadata(self):
		count = self.reader.read_leb128()
		for _ in range(count):
			name_idx = self.reader.read_leb128()
			item_count = self.reader.read_leb128()

			entries = {}

			for _ in range(item_count):
				key_idx = self.reader.read_leb128()
				val_idx = self.reader.read_leb128()
				key = self.string_pool[key_idx]
				val = self.string_pool[val_idx]
				entries[key] = val

			self.metadata.append({
				'name': self.string_pool[name_idx],
				'entries': entries
			})

	def _parse_instances_and_classes(self):
		count = self.reader.read_leb128()
		for _ in range(count):
			name_idx = self.reader.read_leb128()
			super_idx = self.reader.read_leb128()

			flags = self.reader.read_u8()
			protected_ns = None
			if flags & 0x08: # ProtectedNS flag
				protected_ns = self.reader.read_leb128()
			
			intf_count = self.reader.read_leb128()
			interfaces = [self.reader.read_leb128() for _ in range(intf_count)]
			iinit = self.reader.read_leb128()
			
			trait_count = self.reader.read_leb128()
			traits = [self._parse_trait() for _ in range(trait_count)]
			self.instance_pool.append({
				'name':   self.multiname_pool[name_idx],
				'super':  self.multiname_pool[super_idx],
				'flags':  flags,
				'protected_ns': protected_ns,
				'interfaces': [self.multiname_pool[i] for i in interfaces],
				'iinit': iinit,
				'traits': traits
			})

		# ClassInfo (static side)
		for _ in range(count):
			cinit = self.reader.read_leb128()
			trait_count = self.reader.read_leb128()
			traits = [self._parse_trait() for _ in range(trait_count)]
			self.class_pool.append({
				'cinit': cinit,
				'traits': traits
			})

	def _parse_scripts(self):
		script_count = self.reader.read_leb128()
		for _ in range(script_count):
			init = self.method_info[self.reader.read_leb128()]
			trait_count = self.reader.read_leb128()
			traits = [self._parse_trait() for _ in range(trait_count)]
			self.script_pool.append({
				'init': init,
				'traits': traits
			})

	def _parse_method_bodies(self):
		body_count = self.reader.read_leb128()
		for _ in range(body_count):
			method_idx  = self.reader.read_leb128()
			max_stack   = self.reader.read_leb128()
			local_count = self.reader.read_leb128()
			init_scope  = self.reader.read_leb128()
			max_scope   = self.reader.read_leb128()
			code_len    = self.reader.read_leb128()
			code_bytes  = self.reader.read_bytes(code_len)
			
			ex_count = self.reader.read_leb128()
			exceptions = []
			for _ in range(ex_count):
				exceptions.append({
					'from':     self.reader.read_leb128(),
					'to':       self.reader.read_leb128(),
					'target':   self.reader.read_leb128(),
					'exc_type': self.reader.read_leb128(),
					'var_name': self.reader.read_leb128()
				})
			
			trait_count = self.reader.read_leb128()
			traits = [self._parse_trait() for _ in range(trait_count)]

			self.method_bodies.append({
				'method_index': method_idx,
				'max_stack':    max_stack,
				'local_count':  local_count,
				'init_scope':   init_scope,
				'max_scope':    max_scope,
				'code':         code_bytes,
				'exceptions':   exceptions,
				'traits':       traits
			})

	def _parse_trait(self):
		name_idx = self.reader.read_leb128()
		kind     = self.reader.read_u8()
		trait = {'name': self.multiname_pool[name_idx], 'kind': kind}
		
		kind_tag = kind & 0x0F
		if kind_tag in (TRAIT_SLOT, TRAIT_CONST):
			trait['slot_id']     = self.reader.read_leb128()
			trait['type_name']   = self.multiname_pool[self.reader.read_leb128()]
			trait['vindex']      = self.reader.read_leb128()
			if trait['vindex'] != 0:
				trait['vkind']   = self.reader.read_u8()
		elif kind_tag in (TRAIT_METHOD, TRAIT_GETTER, TRAIT_SETTER, TRAIT_CLASS):
			trait['disp_id']     = self.reader.read_leb128()
			trait['index']       = self.reader.read_leb128()
		elif kind_tag == TRAIT_FUNCTION:  # Function
			trait['disp_id']     = self.reader.read_leb128()
			trait['index']       = self.reader.read_leb128()
		
		if (kind >> 4) & 0x04:
			meta_count = self.reader.read_leb128()
			trait['metadata'] = [self.reader.read_leb128() for _ in range(meta_count)]
		return trait
	
	def _assemble_instructions(instrs: list[Instruction]) -> bytes:
		writer = ByteWriter()
		for ins in instrs:
			_opcode = Opcode(ins.opcode)
			if _opcode is None:
				raise ValueError(f"Unknwon Opcode on assembly: 0x{ins.opcode:02x}")
			
			writer.write_ui8(ins.opcode)

			arg_types = []

			opcode_val = _opcode.value
			if len(opcode_val) > 1:
				arg_types.extend(opcode_val[1:])

			for arg, t in zip(ins.args, arg_types):
				match t:
					case "u30":
						writer.write_leb128(arg)
					case "u8":
						writer.write_ui8(arg)
					case "u16":
						writer.write_ui16(arg)
					case "u32":
						writer.write_ui32(arg)
					case "s24":
						writer.write_s24(arg)
					case "s24arr":
						default_offset, case_offsets = arg
						writer.write_s24(default_offset)

						case_count = len(case_offsets)
						writer.write_leb128(case_count)

						for offset in case_offsets:
							writer.write_s24(offset)
					case _:
						raise ValueError(f"Unknwon arg type for assembly: {t}")
		return bytes(writer.buf)

	@staticmethod	
	def _read_instructions(code: bytes) -> Stack:
		reader = ByteReader(code)
		stack = Stack()
		while reader.pos < len(code):
			opcode = reader.read_u8()
			_opcode = Opcode(opcode)
			if _opcode is None:
				raise ValueError(f"Unknown opcode on parse: 0x{opcode:02x}")
			
			arg_types = []

			opcode_val = _opcode.value
			if len(opcode_val) > 1:
				arg_types.extend(opcode_val[1:])

			args = []
			for t in arg_types:
				match t:
					case "u30":
						args.append(reader.read_leb128())
					case "u8":
						args.append(reader.read_u8())
					case "u16":
						args.append(reader.read_u16())
					case "u32":
						args.append(reader.read_u32())
					case "s24":
						args.append(reader.read_s24())
					case "s24arr":
						default_offset = reader.reads24()

						case_count = reader.read_leb128()
						case_offsets = [reader.read_s24() for _ in range(case_count)]
						args.append((default_offset, case_offsets))
					case _:
						raise ValueError(f"Unknown arg type: {t}")
				
			stack.add(Instruction(_opcode.name, opcode, args))
		return stack