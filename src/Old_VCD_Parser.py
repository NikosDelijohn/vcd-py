#!/usr/bin/python3

from subprocess import check_output
import re
import treelib
import tqdm

__WIRE_REGEXP__   = "^\$var\s+([a-z]+)\s+([0-9]+)\s+(.*)\s+([a-zA-Z0-9_]+)\s+\$end"
__MODULE_REGEXP__ = "^\$scope\s+module\s+(.*)\s+\$end"
__VCD_FPTR__      = 0

VCD_FILE = "XXX_decode.vcd"
STROBE_PERIOD = (0,95)
SIGNAL_LIST = "SI.txt"

class Wire():
	#$var wire 1 7* D $end
	def __init__(self, wire_type : str, wire_size : str, vcd_alias : str, port_name : str ):

		self.wire_type = wire_type
		self.wire_size = wire_size
		self.vcd_alias = vcd_alias
		self.port_name = port_name

	def __repr__(self) -> str:
		return f"<{self.vcd_alias},{self.port_name},{self.wire_type},{self.wire_size}>"

	def __str__(self) -> str:
		return self.__repr__()

class Module():

	def __init__(self, cell_name : str):

		self.cell_name = cell_name
		self.wires     = list()
		self.modules   = list()

	def __repr__(self) -> str:
		return f"<{self.cell_name}, {len(self.wires)} wires, {len(self.modules)} modules>"

	def __str__(self) ->str:
		return self.__repr__()

	def append_wire(self, wire : Wire) -> None:

		self.wires.append(wire)

	def append_module(self, module) -> None:

		self.modules.append(module)


def _generate_tree(vcd : str) -> tuple:

	global __VCD_FPTR__

	nesting_level = 0

	id_map = []

	m_regex = re.compile(__MODULE_REGEXP__)
	w_regex = re.compile(__WIRE_REGEXP__)

	tree   = treelib.Tree()
	nodeid = 0

	with open(vcd) as f:


		current_cell = None

		for line in f:

			__VCD_FPTR__ += len(line)

			if "$enddefinitions $end" in line: break; # VCD PARSING ENDED

			is_cell = re.match(m_regex,line)
			is_wire = re.match(w_regex,line)

			if is_cell:

				cell = Module(is_cell.group(1))

				id_map.append((cell.cell_name,nodeid))

				if nesting_level == 0:
					# this is the root node
					tree.create_node(tag=cell.cell_name,identifier=nodeid,data=cell)
					current_cell = tree.get_node(nodeid)

				else:
					# update the predecessor's nesting modules
					predecessor = tree.get_node(nesting_level-1)
					predecessor.data.append_module(cell)
					tree.update_node(nid=predecessor.identifier,data=predecessor.data)
					# add the new node as a child to the previous one
					tree.create_node(tag=cell.cell_name,identifier=nodeid,data=cell,parent=nesting_level-1)
					current_cell = tree.get_node(nodeid)

				nesting_level += 1
				nodeid        += 1

			if is_wire:

				# get the current node (module) and update the wire's list
				wire = Wire(*is_wire.groups())
				current_cell.data.append_wire(wire)
				tree.update_node(nid=current_cell.identifier,data=current_cell.data)

			# closing statement for module in VCD syntax
			if "upscope" in line: nesting_level -= 1

	return (tree,id_map)

def get_signals(infile : str, VCD_tree : treelib.Tree, idmap : tuple) -> list:

	"""
	Read a signal list and try to map it with the VCD signals that are
	parsed into a tree structure. Then extract the requested signals from
	the tree
	"""

	sigs =  [x.rstrip() for x in open(infile) ]

	nodes = list()

	for signal in sigs:

		for cell_name, cell_nodeid in idmap:

			if cell_name == signal:

				nodes.append(VCD_tree.get_node(cell_nodeid))
				break

			assert(True), f"Signal '{signal}' not found in VCD file"

	return nodes

# This can be paralellized
def get_values_at_time(sigs : list) -> dict:

	def _extract(segment : str, alias : str) -> str:

		for line in segment.splitlines():
			# vcd syntax is [LOGIC][ALIAS]
			if line[1:] == alias:
				return line[0]

		assert(True), f"VCD alias '{alias}' not found in current VCD segment"


	chunk = check_output(f"sed -n \"/^#{STROBE_PERIOD[0]}/,/#{STROBE_PERIOD[1]}/p\" {VCD_FILE}", shell=True).decode(encoding='utf-8')
	retval = dict()

	for signal in sigs:

		for wire in signal.data.wires:

			if wire.port_name == "D":
				retval[f"{signal.data.cell_name}/D"] = _extract(chunk,wire.vcd_alias)

	#LEXICOGRAPHICAL SORTING

	#keys = sorted(retval.items(),key=lambda pair : pair[0])

	for pair in retval.items():
		print(pair[0],pair[1])



	exit(0)




def main():

	VCD_tree, id_map = _generate_tree(VCD_FILE)
	sigs             = get_signals(SIGNAL_LIST,VCD_tree,id_map)

	values = get_values_at_time(sigs)


	for sig,val in values.items():

		print(f"{sig} has initial value {val}")


if __name__ == "__main__":
	main()
