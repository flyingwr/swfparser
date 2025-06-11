from ..reader import ByteReader

from .consts import *
from .instruction import Instruction, Opcode, Stack

class ABCReader:
	def __init__(self, data: bytes):
		self.reader: ByteReader = ByteReader(data)

	def read(self):
		self.minor_version = self.reader.read_u16()
		self.major_version = self.reader.read_u16()

		self._read_constant_pool()
		self._read_method_info()
		self._read_metadata()
		self._read_instances_and_classes()
		self._read_scripts()
		self._read_method_bodies()

	def _read_constant_pool(self):
		int_count = self.reader.read_leb128()
		self.int_pool = [0]
		for _ in range(int_count - 1):
			self.int_pool.append(self.reader.read_sleb128())
		
		uint_count = self.reader.read_leb128()
		self.uint_pool = [0]
		for _ in range(uint_count - 1):
			self.uint_pool.append(self.reader.read_leb128())

		double_count = self.reader.read_leb128()
		self.double_pool = [0.0]
		for _ in range(double_count - 1):
			self.double_pool.append(self.reader.read_d())

		string_count = self.reader.read_leb128()
		self.string_pool = [""]
		for _ in range(string_count - 1):
			s = self.reader.read_string()
			self._str_index[s] = len(self.string_pool)
			self.string_pool.append(s)

		ns_count = self.reader.read_leb128()
		self.namespace_pool = [{
			"kind": 0,
			"name_index": 0
		}]
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
		st_entry = {
			"kind": CONSTANT_QName,
			"name_index": 0,
		}
		self.multiname_pool = [st_entry]
		self._multiname_id_index[id(st_entry)] = 0
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
			
			self._multiname_id_index[id(entry)] = len(self.multiname_pool)
			self.multiname_pool.append(entry)

	def _read_method_info(self):
		count = self.reader.read_leb128()
		for _ in range(count):
			param_count = self.reader.read_leb128()
			return_type = self.multiname_pool[self.reader.read_leb128()]

			params = [self.multiname_pool[self.reader.read_leb128()] for _ in range(param_count)]

			name = self.string_pool[self.reader.read_leb128()]
			flags = self.reader.read_u8()

			entry = {
				"name": name,
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
				# ignore param names: their entries are not used by AVM2
				for _ in range(param_count):
					self.reader.read_leb128()

				flags &= ~HAS_PARAM_NAMES
			entry["flags"] = flags
			self.method_info.append(entry)

	def _read_metadata(self):
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

	def _read_instances_and_classes(self):
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
			traits = [self._read_trait() for _ in range(trait_count)]
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
			traits = [self._read_trait() for _ in range(trait_count)]
			self.class_pool.append({
				'cinit': cinit,
				'traits': traits
			})

	def _read_scripts(self):
		script_count = self.reader.read_leb128()
		for _ in range(script_count):
			init = self.reader.read_leb128()
			trait_count = self.reader.read_leb128()
			traits = [self._read_trait() for _ in range(trait_count)]
			self.script_pool.append({
				'init': init,
				'traits': traits
			})

	def _read_method_bodies(self):
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
			traits = [self._read_trait() for _ in range(trait_count)]

			self.method_bodies.append({
				'method_index': method_idx,
				'max_stack':    max_stack,
				'local_count':  local_count,
				'init_scope':   init_scope,
				'max_scope':    max_scope,
				'code':         code_bytes.tobytes(),
				'exceptions':   exceptions,
				'traits':       traits
			})

	def _read_trait(self):
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
		elif kind_tag == TRAIT_FUNCTION:
			trait['disp_id']     = self.reader.read_leb128()
			trait['index']       = self.reader.read_leb128()
		
		if (kind >> 4) & 0x04:
			# ignore metadata
			meta_count = self.reader.read_leb128()
			for _ in range(meta_count):
				self.reader.read_leb128()

		return trait
	
	@staticmethod	
	def read_instructions(code: bytes) -> Stack:
		reader = ByteReader(code)
		stack = Stack(code_len=len(code))

		get_op = Opcode.from_code
		while reader.pos < len(code):
			address = reader.pos

			opcode = get_op(reader.read_u8())
			if opcode is None:
				raise ValueError(f"Unknown opcode on read: 0x{opcode.name:02x}")
			
			arg_types = []
			if len(opcode.value) > 1:
				arg_types.extend(opcode.value[1:])

			args, targets = [], []
			for t in arg_types:
				match t:
					case "u30":
						args.append(reader.read_leb128())
					case "u8":
						args.append(reader.read_u8())
					case "u16":
						args.append(reader.read_u16())
					case "s24":
						op_off = reader.pos
						target = reader.read_s24()

						if opcode.name == "lookupswitch":
							targets.append(op_off + target)
						else:
							targets.append(target + reader.pos)

						args.append(target)
					case "s24arr":
						op_off = reader.pos

						case_count = reader.read_leb128() + 1
						case_offsets = [reader.read_s24() for _ in range(case_count)]

						targets.extend([op_off + offset for offset in case_offsets])

						args.append(case_offsets)
					case "u32":
						args.append(reader.read_u32())
					case "s32":
						args.append(reader.read_sleb128())
					case _:
						raise ValueError(f"Unknown arg type: {t}")
				
			stack.add(Instruction(opcode, address, args, targets))
		return stack