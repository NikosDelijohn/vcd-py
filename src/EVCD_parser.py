from dataclasses import dataclass
from VCD_Parser import VCD_Parser 
from utils import Section 

import re
import multiprocessing as mp

from _Var        import _Var   as Var
from _Scope      import _Scope as Scope
from typing      import Tuple, List, Dict

__VAR_REGEXP__   = "^\$var\s+(port)\s+(1|\[[0-9]+:[0-9]+\])\s+(<[0-9]+)\s(.*)\s\$end"
__SCOPE_REGEXP__  = "^\$scope\s+(.*)\s+(.*)\s+\$end"



class EVCD_Parser(VCD_Parser):

    def __init__(self,vcd_filename : str, sig_file : str = None):
        super().__init__(vcd_filename, sig_file=sig_file, mode="extended")


    def parse(self) -> None:
            
        """
        Generates a Tree data structure where every node is a $scope 
        and holds as data nested $scopes and $vars
        """

        super().fill_VCD_sections()

        nesting_level = 0
        node_id  = 0

        s_regex  = re.compile(__SCOPE_REGEXP__)
        v_regex  = re.compile(__VAR_REGEXP__)

        current_cell = None

        for raw_str in self.raw_sections[Section.Variable_Definition]:           

            is_scope = re.match(s_regex, raw_str)
            is_var   = re.match(v_regex, raw_str)

            if is_scope:

                scope = Scope(*is_scope.groups())
                
                self.tree_metadata[scope.cell_name] = node_id

                if nesting_level == 0:
                    # this is the root node
                    self.tree.create_node(tag=scope.cell_name, identifier=node_id, data=scope)
                    current_cell = self.tree.get_node(node_id)

                else:
                    
                    # update the predecessor's nesting modules
                    predecessor = self.tree.get_node(nesting_level-1)
                    predecessor.data.append_scope(scope)
                    self.tree.update_node(nid=predecessor.identifier, data=predecessor.data)
                    # add the new node as a child to the previous one
                    self.tree.create_node(tag=scope.cell_name, identifier=node_id, data=scope, parent=nesting_level-1)
                    current_cell = self.tree.get_node(node_id)

                nesting_level += 1
                node_id       += 1

            if is_var:
                # get the current node (module) and update the wire's list                   
                var = Var(*is_var.groups())
                current_cell.data.append_var(var)
                self.tree.update_node(nid=current_cell.identifier, data=current_cell.data)

            # closing statement for module in VCD syntax
            if "upscope" in raw_str: nesting_level -= 1

    def find_all_signal_values(self, signal_name: str) -> List[str]:
        raise NotImplementedError("Soon...")

    def find_signal_values_at(self, start : int, end : int, signal_name : str) -> List[str]:
        raise NotImplementedError("Soon...")


def main():

    TestObj = EVCD_Parser("../misc/XXX_decode.vcd", sig_file=None)
    TestObj.parse()

    r = TestObj.find_all_signal_values("tb_top_level/uGPGPU/uStreamingMultiProcessor/uPipelineDecode/U1211/A")
    for ret in r: print(ret)  


if __name__ == "__main__":
    main()