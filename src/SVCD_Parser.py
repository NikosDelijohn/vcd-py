from VCD_Parser import VCD_Parser 
from utils import Section 

import re
import multiprocessing as mp

from os          import cpu_count
from _Var        import _Var   as Var
from _Scope      import _Scope as Scope
from typing      import Tuple, List, Dict

__VAR_REGEXP__    = "^\$var\s+([a-z]+)\s+([0-9]+)\s+(.*)\s+([a-zA-Z0-9_]+)\s+\$end"
__SCOPE_REGEXP__  = "^\$scope\s+(.*)\s+(.*)\s+\$end"

class SVCD_Parser(VCD_Parser):

    def __init__(self,vcd_filename : str, sig_file : str = None):
        super().__init__(vcd_filename, sig_file=sig_file, mode="standard")

    
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

        retvals = list()

        value_change = '\n'.join(self.raw_sections[Section.Value_Change])
        timestamp_regex = r"\#[0-9]+\n"

        signal = self.get_signal(signal_name)
        signal_ascii_id = signal.get_id()
        signal_size = signal.get_size()

        # can also be done with re.finditer
        sections = re.split(timestamp_regex, value_change, maxsplit=0, flags=re.DOTALL|re.MULTILINE)

        previous_value = None 

        for n, section in enumerate(sections): 
            
            in_section = section.find(signal_ascii_id)

            if n == 0: 
                # that's the $dumpvars section i.e., initial value
                previous_value = section[in_section-signal_size:in_section]
            
            if in_section == -1:
                # signal's value didn't change in current section 
                retvals.append(previous_value)
                continue
            
            # search for multiple signal changes occuring in the section
            while(in_section != -1):
                previous_value = section[in_section-signal_size:in_section]
                retvals.append(section[in_section-signal_size:in_section])
                in_section = section.find(signal_ascii_id, in_section + 1)

        return retvals 

    def find_signal_values_at(self, start : int, end : int, signal_name : str) -> List[str]:
      
        retvals = list()

        search_space = '\n'.join(self.raw_sections[Section.Value_Change])
        search_regex = f"#{start}(.*)^#{end}"

        # Extract the ]start,end[ segment
        regex_results = re.search(search_regex, search_space, flags=re.DOTALL|re.MULTILINE)

        if not regex_results: 
            raise ValueError("Provided timestamp(s) do not exist in the VCD file.")

        period = regex_results[1]

        # Find the signal attributes in the Tree.
        signal = self.get_signal(signal_name)
        signal_ascii_id = signal.get_id()
        signal_size = signal.get_size()

        # Record every value change of the signal
        found_symbol = period.find(signal_ascii_id)
        while(found_symbol != -1):
            
            if period[found_symbol+1].isdigit():  # special case for the '#' char only
                found_symbol = period.find(signal_ascii_id,found_symbol+1)
                continue;

            retvals.append(period[found_symbol-signal_size:found_symbol])

            found_symbol = period.find(signal_ascii_id,found_symbol+1)

        return retvals


def main():

    TestObj = SVCD_Parser("../misc/wikipedia.vcd", sig_file=None)
    TestObj.parse()

    #r = TestObj.find_all_signal_values2("tb_top_level/uGPGPU/uStreamingMultiProcessor/uPipelineDecode/U1211/A")
    r = TestObj.find_all_signal_values("logic/tx_en")
    for ret in r: print(ret)  


if __name__ == "__main__":
    main()