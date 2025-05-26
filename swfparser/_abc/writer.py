from ..writer import ByteWriter

from .consts import *
from .instruction import Stack

class ABCWriter:
	def __init__(self):
		self.writer: ByteWriter = ByteWriter()

	def write(self) -> 'ByteWriter':
		self.writer.write_u32(self.flags)
		self.writer.write_sstring(self.name)

		self.writer.write_u16(self.minor_version)
		self.writer.write_u16(self.major_version)

		self._write_constant_pool()
		self._write_method_info()

		# ignore metadata: their entries are not used by AVM2
		self.writer.write_leb128(0)

		self._write_instances_and_classes()
		self._write_scripts()
		self._write_method_bodies()

		return self.writer

	def _write_constant_pool(self):
		self.writer.write_leb128(len(self.int_pool))
		for i in range(1, len(self.int_pool)):
			self.writer.write_sleb128(self.int_pool[i])
		
		self.writer.write_leb128(len(self.uint_pool))
		for i in range(1, len(self.uint_pool)):
			self.writer.write_leb128(self.uint_pool[i])

		self.writer.write_leb128(len(self.double_pool))
		for i in range(1, len(self.double_pool)):
			self.writer.write_d(self.double_pool[i])

		self.writer.write_leb128(len(self.string_pool))
		for i in range(1, len(self.string_pool)):
			self.writer.write_string(self.string_pool[i])

		self.writer.write_leb128(len(self.namespace_pool))
		for i in range(1, len(self.namespace_pool)):
			namespace = self.namespace_pool[i]
			self.writer.write_u8(namespace["kind"])
			self.writer.write_leb128(namespace["name_index"])

		self.writer.write_leb128(len(self.ns_set_pool))
		for i in range(1, len(self.ns_set_pool)):
			ns_set = self.ns_set_pool[i]
			self.writer.write_leb128(len(ns_set))
			for indice in ns_set:
				self.writer.write_leb128(indice)

		self.writer.write_leb128(len(self.multiname_pool))
		for i in range(1, len(self.multiname_pool)):
			multiname = self.multiname_pool[i]
			kind = multiname["kind"]
			self.writer.write_u8(kind)
			if kind in (CONSTANT_QName, CONSTANT_QNameA):
				self.writer.write_leb128(multiname["ns_index"])
				self.writer.write_leb128(multiname["name_index"])
			elif kind in (CONSTANT_RTQName, CONSTANT_RTQNameA):
				self.writer.write_leb128(multiname["name_index"])
			elif kind in (CONSTANT_RTQNameL, CONSTANT_RTQNameLA):
				# no additional data
				pass
			elif kind in (CONSTANT_Multiname, CONSTANT_MultinameA):
				self.writer.write_leb128(multiname["name_index"])
				self.writer.write_leb128(multiname["ns_set_index"])
			elif kind in (CONSTANT_MultinameL, CONSTANT_MultinameLA):
				self.writer.write_leb128(multiname["ns_set_index"])
			elif kind == CONSTANT_TypeName:
				self.writer.write_leb128(multiname["name_index"])
				self.writer.write_leb128(len(multiname["param_types"]))
				for param_type in multiname["param_types"]:
					self.writer.write_leb128(param_type)
			else:
				raise ValueError(f"Unknown multiname kind: {kind}")

	def _write_method_info(self):
		self.writer.write_leb128(len(self.method_info))
		for method in self.method_info:
			self.writer.write_leb128(len(method["params"]))
			self.writer.write_leb128(self.multiname_pool.index(method["return_type"]))

			for param in method["params"]:
				self.writer.write_leb128(self.multiname_pool.index(param))

			self.writer.write_leb128(self.string_pool.index(method["name"], 1))
			self.writer.write_u8(method["flags"])

			if method["flags"] & HAS_OPTIONAL:
				self.writer.write_leb128(len(method["optional_params"]))
				for param in method["optional_params"]:
					value, kind = param
					self.writer.write_leb128(value)
					self.writer.write_u8(kind)

	def _write_instances_and_classes(self):
		self.writer.write_leb128(len(self.class_pool))
		for instance in self.instance_pool:
			self.writer.write_leb128(self.multiname_pool.index(instance["name"]))
			self.writer.write_leb128(self.multiname_pool.index(instance["super"]))

			self.writer.write_u8(instance["flags"])
			if instance["protected_ns"] is not None:
				self.writer.write_leb128(instance["protected_ns"])

			self.writer.write_leb128(len(instance["interfaces"]))
			for interface in instance["interfaces"]:
				self.writer.write_leb128(self.multiname_pool.index(interface))

			self.writer.write_leb128(instance["iinit"])
			self._write_traits(instance["traits"])

		# ClassInfo (static side)
		for klass in self.class_pool:
			self.writer.write_leb128(klass["cinit"])
			self._write_traits(klass["traits"])
		
	def _write_scripts(self):
		self.writer.write_leb128(len(self.script_pool))
		for script in self.script_pool:
			self.writer.write_leb128(script["init"])
			self._write_traits(script["traits"])

	def _write_method_bodies(self):
		self.writer.write_leb128(len(self.method_bodies))
		for body in self.method_bodies:
			self.writer.write_leb128(body["method_index"])
			self.writer.write_leb128(body["max_stack"])
			self.writer.write_leb128(body["local_count"])
			self.writer.write_leb128(body["init_scope"])
			self.writer.write_leb128(body["max_scope"])
			self.writer.write_leb128(len(body["code"]))
			self.writer.write_bytes(body["code"])

			self.writer.write_leb128(len(body["exceptions"]))			
			for exception in body["exceptions"]:
				self.writer.write_leb128(exception["from"])
				self.writer.write_leb128(exception["to"])
				self.writer.write_leb128(exception["target"])
				self.writer.write_leb128(exception["exc_type"])
				self.writer.write_leb128(exception["var_name"])
			
			self._write_traits(body["traits"])
	
	def _write_traits(self, traits: list[dict[str, int]]):
		self.writer.write_leb128(len(traits))
		for trait in traits:
			self._write_trait(trait)

	def _write_trait(self, trait: dict[str, int]):
		self.writer.write_leb128(self.multiname_pool.index(trait["name"]))
		self.writer.write_u8(trait["kind"])
		
		kind_tag = trait["kind"] & 0x0F
		if kind_tag in (TRAIT_SLOT, TRAIT_CONST):
			self.writer.write_leb128(trait["slot_id"])
			self.writer.write_leb128(self.multiname_pool.index(trait["type_name"]))
			self.writer.write_leb128(trait["vindex"])
			if trait['vindex'] != 0:
				self.writer.write_u8(trait["vkind"])
		elif kind_tag in (TRAIT_METHOD, TRAIT_GETTER, TRAIT_SETTER, TRAIT_CLASS):
			self.writer.write_leb128(trait["disp_id"])
			self.writer.write_leb128(trait["index"])
		elif kind_tag == TRAIT_FUNCTION:
			self.writer.write_leb128(trait["disp_id"])
			self.writer.write_leb128(trait["index"])
	
	@staticmethod
	def assemble_instructions(stack: Stack) -> bytes:
		writer = ByteWriter()

		while True:
			instr = stack.next()
			if instr is None:
				break
			
			opcode_val = instr.opcode.value
			writer.write_u8(opcode_val[0])

			arg_types = []
			if len(opcode_val) > 1:
				arg_types.extend(opcode_val[1:])

			for arg, t in zip(instr.args, arg_types):
				match t:
					case "u30":
						writer.write_leb128(arg)
					case "u8":
						writer.write_u8(arg)
					case "u16":
						writer.write_u16(arg)
					case "s24":
						writer.write_s24(arg)
					case "s24arr":
						case_count = len(arg) + 1
						writer.write_leb128(case_count)

						for case_offset in arg:
							writer.write_s24(case_offset)
					case "u32":
						writer.write_u32(arg)
					case "s32":
						writer.write_sleb128(arg)
					case "u32":
						writer.write_u32(arg)
					
					case _:
						raise ValueError(f"Unknwon arg type for assembly: {t}")
					
		return bytes(writer.buf)