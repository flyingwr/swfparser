from .consts import *
from .reader import ABCReader
from .writer import ABCWriter

from .consts import *
from .instruction import Instruction, Opcode, Stack

class ABC(ABCReader, ABCWriter):
	def __init__(self, name: str, flags: int, data: bytes):
		self.name: str = name
		self.flags:int = flags
		
		self.minor_version: int = 0
		self.major_version: int = 0

		self.double_pool = []
		self.method_info = []
		self.metadata = []
		self.instance_pool = []
		self.int_pool = []
		self.uint_pool = []
		self.class_pool = []
		self.multiname_pool = []
		self.namespace_pool = []
		self.ns_set_pool = []
		self.script_pool = []
		self.string_pool = []
		self.method_bodies = []

		self._multiname_index: dict[tuple[int, int], int] = {}
		self._multiname_id_index: dict[dict[str, int], int] = {}
		self._str_index: dict[str, int] = {}

		ABCReader.__init__(self, data)
		ABCWriter.__init__(self)

	def __repr__(self) -> str:
		return (
			f"ABC constantpool: ints={len(self.int_pool)}, uints={len(self.uint_pool)}, \
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

	def ensure_string(self, s: str) -> int:
		if s not in self.string_pool:
			self._str_index[s] = len(self.string_pool)
			self.string_pool.append(s)
		return self._str_index[s]
	
	def ensure_namespace(self, name: str) -> int:
		s_index = self.ensure_string(name)

		for index, namespace in enumerate(self.namespace_pool):
			if namespace["name_index"] == s_index:
				return index
		
		self.namespace_pool.append({
			"kind": 0x08,
			"name_index": len(self.namespace_pool)
		})
		return len(self.namespace_pool) - 1
	
	def ensure_multiname(self, name_index: int, ns_index: int) -> int:
		key = (name_index, ns_index)
		try:
			return self._multiname_index[key]
		except KeyError:
			idx = len(self.multiname_pool)
			self.multiname_pool.append({
				"kind": CONSTANT_QName,
				"name_index": name_index,
				"ns_index": ns_index
			})
			self._multiname_index[key] = idx
			return idx
	
	def find_multiname(self, prop_name: str, namespace: str = "") -> int | None:
		prop_s_index = self._str_index[prop_name]
		ns_s_index = self._str_index[namespace]

		for index, multiname in enumerate(self.multiname_pool):
			if multiname is not None:
				name_index = multiname.get("name_index")
				if name_index == prop_s_index:
					namespace_index = multiname["ns_index"]
					namespace = self.namespace_pool[namespace_index]
					if namespace["name_index"] == ns_s_index:
						return index
		return None